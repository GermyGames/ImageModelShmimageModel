"""Sample a palette and likely outline settings from a separate style reference."""

import json
from pathlib import Path
import re

import numpy as np
from PIL import Image


MAX_OUTLINE_WIDTH = 6


def detect_pixel_scale(pixels: np.ndarray) -> int:
    height, width = pixels.shape[:2]
    if np.all(pixels == pixels[0, 0]):
        return 1
    for scale in range(min(height, width, 16), 1, -1):
        if width % scale or height % scale:
            continue
        blocks = pixels.reshape(height // scale, scale, width // scale, scale, 4)
        if np.all(blocks == blocks[:, :1, :, :1, :]):
            return scale
    return 1


def estimate_outline(
    rgb: np.ndarray, visible: np.ndarray, luma: np.ndarray
) -> tuple[np.ndarray, int] | None:
    darkness = np.percentile(luma[visible], 35)
    dark = visible & (luma <= darkness)
    widths = np.zeros(MAX_OUTLINE_WIDTH, dtype=int)
    candidates = np.zeros_like(dark)
    for color_dark, lightness, foreground, found in [
        (dark, luma, visible, candidates),
        (dark.T, luma.T, visible.T, candidates.T),
    ]:
        span = color_dark.shape[1]
        for width in range(1, min(MAX_OUTLINE_WIDTH, span - 2) + 1):
            end = span - width - 1
            runs = np.lib.stride_tricks.sliding_window_view(color_dark[:, 1:-1], width, axis=1).all(axis=2)
            interior = np.lib.stride_tricks.sliding_window_view(lightness[:, 1:-1], width, axis=1)
            center = 1 + width // 2
            inside = lightness[:, center:center + end]
            contrast = np.minimum(lightness[:, :end], lightness[:, width + 1:]) - inside
            # Measure width on coherent dark strokes, so a ramp of different shades
            # across a filled shadow does not count as one thick line.
            runs &= foreground[:, :end] & foreground[:, width + 1:] & (contrast >= 15)
            runs &= np.ptp(interior, axis=2) <= 8
            widths[width - 1] += int(runs.sum())
            found[:, center:center + end] |= runs
    if not candidates.any():
        return None
    colors, counts = np.unique(rgb[candidates], axis=0, return_counts=True)
    return colors[np.argmax(counts)], int(np.argmax(widths)) + 1


def analyze_style(image: Image.Image, colors: int, pixel_scale: int | None) -> dict:
    rgba = image.convert("RGBA")
    source = np.asarray(rgba)
    pixel_scale = pixel_scale if pixel_scale is not None else detect_pixel_scale(source)
    if not 1 <= pixel_scale <= min(rgba.size):
        raise ValueError("Pixel scale must fit inside the reference image.")
    if pixel_scale > 1:
        rgba = rgba.resize((rgba.width // pixel_scale, rgba.height // pixel_scale), Image.Resampling.NEAREST)

    pixels = np.asarray(rgba)
    visible = pixels[..., 3] >= 128
    if not visible.any():
        raise ValueError("The style reference has no visible pixels.")
    rgb = pixels[..., :3]
    luma = np.asarray(rgba.convert("L"), dtype=np.float32)
    outline = estimate_outline(rgb, visible, luma)
    flat = rgb[visible]
    sample = flat[::max(1, len(flat) // 150_000)]
    sample_image = Image.fromarray(sample[None, ...])
    quantized = sample_image.quantize(colors=colors, dither=Image.Dither.NONE).convert("RGB")
    palette = np.unique(np.asarray(quantized)[0], axis=0)
    contrast_weights = np.array([0.2126, 0.7152, 0.0722])
    if outline is None:
        outline_color = palette[np.argmin(palette @ contrast_weights)]
        stroke_width = 1
    else:
        outline_color, stroke_width = outline
        if not (palette == outline_color).all(axis=1).any():
            nearest = np.argmin(np.sum((palette.astype(float) - outline_color) ** 2, axis=1))
            palette[nearest] = outline_color
    palette = palette[np.argsort(palette @ contrast_weights)]

    def hex_color(rgb_color: np.ndarray) -> str:
        return "#" + "".join(f"{component:02x}" for component in rgb_color)

    return {
        "pixel_scale": pixel_scale,
        "palette": [hex_color(rgb_color) for rgb_color in palette],
        "outline": {"color": hex_color(outline_color), "width": stroke_width},
    }


def load_style(path: str) -> tuple[np.ndarray, int, int]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    try:
        palette = data["palette"]
        ink = data["outline"]["color"]
        width = data["outline"]["width"]
    except (KeyError, TypeError) as error:
        raise ValueError("Style JSON needs a palette and an outline color and width.") from error
    if not isinstance(palette, list) or not 1 <= len(palette) <= 256:
        raise ValueError("The style palette must contain between 1 and 256 colors.")
    if any(not isinstance(color, str) or not re.fullmatch(r"#[\da-fA-F]{6}", color, re.ASCII) for color in palette):
        raise ValueError("Style palette colors must use #RRGGBB notation.")
    if not isinstance(ink, str) or ink.lower() not in [color.lower() for color in palette]:
        raise ValueError("The style outline color must be in its palette.")
    if type(width) is not int or not 1 <= width <= MAX_OUTLINE_WIDTH:
        raise ValueError(f"Outline width must be an integer from 1 to {MAX_OUTLINE_WIDTH}.")
    rgb = np.array([tuple(bytes.fromhex(color[1:])) for color in palette], dtype=np.uint8)
    return rgb, [color.lower() for color in palette].index(ink.lower()), width
