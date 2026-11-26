"""Extract local line and detail guides from a prepared reference."""

import base64
from io import BytesIO
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from image_grid import pad_for_phase, resample_phase


def blur_luma(image: Image.Image, radius: float) -> np.ndarray:
    return np.asarray(image.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32)


def region_boundaries(image: Image.Image, stride: float, color_count: int) -> np.ndarray:
    smoothed = image.filter(ImageFilter.GaussianBlur(max(0.8, stride * 0.85)))
    colors = smoothed.quantize(colors=color_count, dither=Image.Dither.NONE)
    regions = np.asarray(colors.convert("RGB"), dtype=np.float32)
    strengths = np.zeros(regions.shape[:2], dtype=np.float32)
    for a, b in [
        (np.s_[:, :-1], np.s_[:, 1:]),
        (np.s_[:-1, :], np.s_[1:, :]),
    ]:
        contrast = np.linalg.norm(regions[a] - regions[b], axis=2)
        # Put each boundary on its darker side so it yields one contour.
        a_is_darker = regions[a].sum(axis=2) <= regions[b].sum(axis=2)
        strengths[a] = np.maximum(strengths[a], np.where(a_is_darker, contrast, 0))
        strengths[b] = np.maximum(strengths[b], np.where(a_is_darker, 0, contrast))
    # Weight boundaries by the underlying local color change. A quantization step
    # in a smooth gradient should contribute less than a stable object boundary.
    continuous = np.asarray(smoothed, dtype=np.float32)
    radius = max(1, round(stride * 0.65))
    expanded = np.pad(continuous, ((radius, radius), (radius, radius), (0, 0)), mode="edge")
    h, w = strengths.shape
    dx = expanded[radius:radius+h, 2*radius:2*radius+w] - expanded[radius:radius+h, :w]
    dy = expanded[2*radius:2*radius+h, radius:radius+w] - expanded[:h, radius:radius+w]
    evidence = np.maximum(np.linalg.norm(dx, axis=2), np.linalg.norm(dy, axis=2))
    strength = np.clip(strengths / 55, 0, 1) * np.clip(evidence / 34, 0, 1)
    ridges = Image.fromarray(np.uint8(strength * 255))
    # Keep a one-source-pixel region boundary visible when sampling onto a coarse grid.
    width = max(3, (round(stride * 0.34) // 2) * 2 + 1)
    return np.asarray(ridges.filter(ImageFilter.MaxFilter(width)), dtype=np.float32) / 255


def extract_guides(
    subject: Image.Image,
    aligned: Image.Image,
    phase: tuple[float, float],
    method: str,
    line_threshold: float,
    detail_threshold: float,
    color_count: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Return white-selects masks on the same grid as the prepared subject."""
    target_size = aligned.size
    visible = np.asarray(aligned.getchannel("A")) >= 128
    stride = max(1.0, min(subject.width / target_size[0], subject.height / target_size[1]))

    # Give filtering a stable backing at transparent edges. The silhouette comes from
    # the aligned alpha channel, independently of the source colors.
    background = Image.new("RGBA", subject.size, (240, 240, 240, 255))
    background.alpha_composite(subject)
    rgb = background.convert("RGB")
    luma = rgb.convert("L")
    fine = blur_luma(luma, max(0.4, stride * 0.16))
    local = blur_luma(luma, max(1.1, stride * 0.65))

    if method == "ink":
        neighborhood = blur_luma(luma, max(1.6, stride * 1.25))
        line_strength = np.clip((neighborhood - fine) / 65, 0, 1)
    elif method == "regions":
        line_strength = region_boundaries(rgb, stride, color_count)
    else:
        line_strength = np.zeros(fine.shape, dtype=np.float32)
        for sigma in (max(0.55, stride * 0.23), max(1.0, stride * 0.58)):
            narrow = blur_luma(luma, sigma)
            wide = blur_luma(luma, sigma * 1.65)
            # Soft-threshold dark ridges over two scales, as in DoG-based stylization.
            response = np.tanh(np.maximum(0, wide - narrow - 1.5) / 18)
            np.maximum(line_strength, response, out=line_strength)

    fine_rgb = np.asarray(rgb.filter(ImageFilter.GaussianBlur(max(0.4, stride * 0.16))), dtype=np.float32)
    local_rgb = np.asarray(rgb.filter(ImageFilter.GaussianBlur(max(1.1, stride * 0.65))), dtype=np.float32)
    chroma_detail = np.max(np.abs(fine_rgb - local_rgb), axis=2)
    detail_strength = np.clip(np.maximum(np.abs(fine - local), chroma_detail * 0.7) / 45, 0, 1)

    def project(strength: np.ndarray, threshold: float) -> np.ndarray:
        response = Image.fromarray(strength.astype(np.float32))
        padded = pad_for_phase(response, target_size, phase)
        sampled = resample_phase(padded, response.size, target_size, phase)
        return (np.asarray(sampled) >= threshold) & visible

    lines = project(line_strength, line_threshold)
    # Add the inner silhouette border only for a case with an actual cutout.
    if visible.any() and not visible.all():
        foreground = Image.fromarray(np.uint8(visible) * 255)
        inner = np.asarray(foreground.filter(ImageFilter.MinFilter(3))) > 0
        lines |= visible & ~inner
    highlights = project(np.clip((fine - local) / 45, 0, 1), detail_threshold)
    details = project(detail_strength, detail_threshold) & (~lines | highlights)
    lines &= ~details
    return lines, details


def mask_image(mask: np.ndarray) -> Image.Image:
    return Image.fromarray(np.uint8(mask) * 255)


def load_mask(path: str | None, size: tuple[int, int]) -> np.ndarray:
    if path is None:
        return np.zeros((size[1], size[0]), dtype=bool)
    with Image.open(path) as image:
        if image.size != size:
            raise ValueError(f"{path} is {image.width}×{image.height}; the current case grid is {size[0]}×{size[1]}.")
        return (np.asarray(image.convert("L")) >= 128) & (np.asarray(image.convert("RGBA").getchannel("A")) >= 128)


def widen_lines(mask: np.ndarray, width: int) -> np.ndarray:
    if width == 1:
        return mask
    padding = (width // 2, (width - 1) // 2)
    neighborhoods = np.lib.stride_tricks.sliding_window_view(np.pad(mask, (padding, padding)), (width, width))
    return neighborhoods.any(axis=(-2, -1))


def guide_overlay(base: Image.Image, lines: np.ndarray, details: np.ndarray) -> Image.Image:
    result = base.convert("RGBA")
    for mask, color in [(lines, (52, 224, 234, 190)), (details, (255, 144, 86, 200))]:
        layer = np.zeros((*mask.shape, 4), dtype=np.uint8)
        layer[mask] = color
        result.alpha_composite(Image.fromarray(layer))
    return result


def write_review(
    destination: Path, source: Image.Image, aligned: Image.Image,
    blockin: Image.Image | None, lines: np.ndarray, details: np.ndarray, overlay: Image.Image,
) -> None:
    def data_url(image: Image.Image) -> str:
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")

    source_preview = source.copy()
    source_preview.thumbnail((1280, 1280), Image.Resampling.LANCZOS)
    data = {
        "width": aligned.width,
        "height": aligned.height,
        "aligned": data_url(aligned),
        "blockin": data_url(blockin) if blockin is not None else None,
        "lines": data_url(mask_image(lines)),
        "details": data_url(mask_image(details)),
    }
    template = Path(__file__).with_name("guide_review.html").read_text(encoding="utf-8")
    page = (
        template.replace('<body data-review="template">', '<body data-review="generated">', 1)
        .replace('id="source"', f'id="source" src="{data_url(source_preview)}"', 1)
        .replace('id="static-grid"', f'id="static-grid" src="{data_url(overlay)}"', 1)
        .replace('type="application/json">{}</script>', f'type="application/json">{json.dumps(data)}</script>', 1)
    )
    destination.write_text(page, encoding="utf-8")
