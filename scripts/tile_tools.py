"""Toroidal planarization, cleanup, and diagnostic helpers for seamless pixel-art tiles."""

from collections import Counter, deque
from collections.abc import Iterable

import numpy as np
from PIL import Image


_OFFSETS_4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_OFFSETS_8 = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)


def rgb_luma(rgb: np.ndarray) -> np.ndarray:
    """Compute Rec. 709 luminance from an array whose last axis holds RGB channels."""
    arr = np.asarray(rgb, dtype=np.float32)
    if arr.ndim < 1 or arr.shape[-1] != 3:
        raise ValueError("Expected an RGB array with shape (..., 3).")
    return (0.2126 * arr[..., 0] + 0.7152 * arr[..., 1] + 0.0722 * arr[..., 2]).astype(np.float32)


def torus_delta(coord: np.ndarray | float, center: float, size: int) -> np.ndarray:
    """Return signed shortest displacements on a wrapping axis of length `size`."""
    if size <= 0:
        raise ValueError("Period size must be positive.")
    return ((np.asarray(coord, dtype=np.float32) - center + size / 2.0) % size) - size / 2.0


def periodic_gaussian(arr: np.ndarray, sigma: float) -> np.ndarray:
    """Apply an exact periodic Gaussian blur on an H x W torus via 2D FFT."""
    if sigma < 0:
        raise ValueError("Sigma must be non-negative.")
    data = np.asarray(arr, dtype=np.float32)
    if data.ndim not in (2, 3) or data.shape[0] == 0 or data.shape[1] == 0:
        raise ValueError("Expected a non-empty 2D or 3D spatial array.")
    if sigma == 0:
        return data.copy()

    h, w = data.shape[:2]
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    kernel_hat = np.exp(-2.0 * (np.pi ** 2) * (sigma ** 2) * (fx ** 2 + fy ** 2))
    if data.ndim == 3:
        kernel_hat = kernel_hat[..., None]
    filtered = np.fft.ifft2(np.fft.fft2(data, axes=(0, 1)) * kernel_hat, axes=(0, 1)).real
    return filtered.astype(np.float32)


def equalize_toroidal_luma(
    luma: np.ndarray, sigma: float = 18.0, strength: float = 0.55
) -> np.ndarray:
    """Suppress low-frequency brightness drift across the torus while preserving mean luminance."""
    data = np.asarray(luma, dtype=np.float32)
    if data.ndim != 2:
        raise ValueError("Expected a 2D luminance array.")
    if not 0.0 <= strength <= 1.0:
        raise ValueError("Equalization strength must be between 0.0 and 1.0.")
    broad = periodic_gaussian(data, sigma)
    return (data - strength * (broad - float(broad.mean()))).astype(np.float32)


def toroidal_kuwahara(img: np.ndarray, radius: int = 2, passes: int = 1) -> np.ndarray:
    """Flatten photo grain into crisp painted planes using a wrapping 4-quadrant Kuwahara filter."""
    cur = np.asarray(img, dtype=np.float32)
    if cur.ndim != 2 or cur.shape[0] == 0 or cur.shape[1] == 0:
        raise ValueError("Expected a non-empty 2D array.")
    if radius < 1:
        raise ValueError("Radius must be at least 1.")
    if passes < 1:
        raise ValueError("Passes must be at least 1.")

    h, w = cur.shape
    size = radius + 1
    n_pix = float(size * size)
    slices = (
        (0, size, 0, size),
        (0, size, radius, radius + size),
        (radius, radius + size, 0, size),
        (radius, radius + size, radius, radius + size),
    )

    for _ in range(passes):
        pad = np.pad(cur, radius, mode="wrap").astype(np.float64)
        means = np.empty((4, h, w), dtype=np.float64)
        vars_ = np.empty((4, h, w), dtype=np.float64)
        for q, (y0, y1, x0, x1) in enumerate(slices):
            acc = np.zeros((h, w), dtype=np.float64)
            acc2 = np.zeros((h, w), dtype=np.float64)
            for dy in range(y0, y1):
                for dx in range(x0, x1):
                    patch = pad[dy:dy + h, dx:dx + w]
                    acc += patch
                    acc2 += patch * patch
            mean = acc / n_pix
            var = np.maximum(0.0, acc2 / n_pix - mean * mean)
            means[q] = mean
            vars_[q] = var
        best_q = np.argmin(vars_, axis=0)
        cur = np.take_along_axis(means, best_q[None], axis=0)[0].astype(np.float32)
    return cur


def _collect_component(
    arr: np.ndarray,
    visited: np.ndarray,
    start_y: int,
    start_x: int,
    offsets: tuple[tuple[int, int], ...],
) -> list[tuple[int, int]]:
    """Breadth-first traversal of one equal-valued connected component on a torus."""
    h, w = arr.shape
    target = arr[start_y, start_x]
    comp: list[tuple[int, int]] = []
    queue = deque([(start_y, start_x)])
    visited[start_y, start_x] = True
    while queue:
        cy, cx = queue.popleft()
        comp.append((cy, cx))
        for dy, dx in offsets:
            ny, nx = (cy + dy) % h, (cx + dx) % w
            if not visited[ny, nx] and arr[ny, nx] == target:
                visited[ny, nx] = True
                queue.append((ny, nx))
    return comp


def absorb_small_components(
    grid: np.ndarray,
    max_size: int = 2,
    protected: Iterable[int] | None = None,
) -> np.ndarray:
    """Absorb small 4-connected label islands on the torus into their majority neighbor."""
    arr = np.asarray(grid)
    if arr.ndim != 2:
        raise ValueError("Expected a 2D label grid.")
    if max_size < 0:
        raise ValueError("max_size must be non-negative.")

    out = arr.copy()
    if max_size == 0 or arr.size == 0:
        return out

    h, w = arr.shape
    visited = np.zeros((h, w), dtype=bool)
    prot = {int(v) for v in protected} if protected is not None else set()

    for sy in range(h):
        for sx in range(w):
            if visited[sy, sx]:
                continue
            val = int(arr[sy, sx])
            comp = _collect_component(arr, visited, sy, sx, _OFFSETS_4)
            if len(comp) > max_size or val in prot:
                continue
            comp_set = set(comp)
            counts: Counter[int] = Counter()
            for cy, cx in comp:
                for dy, dx in _OFFSETS_4:
                    ny, nx = (cy + dy) % h, (cx + dx) % w
                    if (ny, nx) not in comp_set:
                        counts[int(arr[ny, nx])] += 1
            if counts:
                replacement = min(counts.items(), key=lambda item: (-item[1], item[0]))[0]
                for cy, cx in comp:
                    out[cy, cx] = replacement
    return out


def prune_sparse_mask(
    mask: np.ndarray, min_size: int = 4, connectivity: int = 8
) -> np.ndarray:
    """Remove True components smaller than `min_size` on the wrapping grid."""
    arr = np.asarray(mask, dtype=bool)
    if arr.ndim != 2:
        raise ValueError("Expected a 2D boolean mask.")
    if min_size < 1:
        raise ValueError("min_size must be at least 1.")
    if connectivity not in (4, 8):
        raise ValueError("Connectivity must be 4 or 8.")

    offsets = _OFFSETS_8 if connectivity == 8 else _OFFSETS_4
    out = arr.copy()
    h, w = arr.shape
    visited = np.zeros((h, w), dtype=bool)

    for sy in range(h):
        for sx in range(w):
            if out[sy, sx] and not visited[sy, sx]:
                comp = _collect_component(out, visited, sy, sx, offsets)
                if len(comp) < min_size:
                    for cy, cx in comp:
                        out[cy, cx] = False
    return out


def seam_continuity(image: Image.Image | np.ndarray) -> dict[str, float]:
    """Compare wrap-edge L-R and T-B steps against interior neighbor steps."""
    if isinstance(image, Image.Image):
        arr = np.asarray(image.convert("RGB"), dtype=np.float32)
    else:
        arr = np.asarray(image, dtype=np.float32)
    if arr.ndim not in (2, 3) or arr.shape[0] == 0 or arr.shape[1] == 0:
        raise ValueError("Expected a non-empty 2D or 3D image array.")

    h, w = arr.shape[:2]
    lr_edge_diff = float(np.mean(np.abs(arr[:, 0] - arr[:, -1])))
    interior_x_diff = float(np.mean(np.abs(arr[:, 1:] - arr[:, :-1]))) if w > 1 else 0.0
    tb_edge_diff = float(np.mean(np.abs(arr[0, :] - arr[-1, :])))
    interior_y_diff = float(np.mean(np.abs(arr[1:, :] - arr[:-1, :]))) if h > 1 else 0.0

    lr_ratio = 1.0 if interior_x_diff <= 1e-9 else lr_edge_diff / interior_x_diff
    tb_ratio = 1.0 if interior_y_diff <= 1e-9 else tb_edge_diff / interior_y_diff
    return {
        "lr_edge_diff": round(lr_edge_diff, 3),
        "interior_x_diff": round(interior_x_diff, 3),
        "lr_ratio": round(lr_ratio, 3),
        "tb_edge_diff": round(tb_edge_diff, 3),
        "interior_y_diff": round(interior_y_diff, 3),
        "tb_ratio": round(tb_ratio, 3),
    }


def _summarize_luma(luma_values: np.ndarray) -> dict:
    percentiles = np.percentile(luma_values, [5, 15, 30, 50, 70, 85, 95])
    keys = ("p05", "p15", "p30", "p50", "p70", "p85", "p95")
    return {
        "luma_mean": round(float(np.mean(luma_values)), 1),
        "luma_std": round(float(np.std(luma_values)), 1),
        "luma_percentiles": {k: round(float(v), 1) for k, v in zip(keys, percentiles)},
        "value_bands": {
            "dark_pct": round(100.0 * float(np.mean(luma_values < 75.0)), 1),
            "mid_pct": round(100.0 * float(np.mean((luma_values >= 75.0) & (luma_values < 165.0))), 1),
            "light_pct": round(100.0 * float(np.mean(luma_values >= 165.0)), 1),
        },
    }


def tonal_report(
    image: Image.Image,
    reference: Image.Image | None = None,
    top_colors: int = 24,
) -> dict:
    """Summarize luminance balance, palette coverage percentages, and seam continuity."""
    if top_colors < 1:
        raise ValueError("top_colors must be at least 1.")

    rgba = image.convert("RGBA")
    pixels = np.asarray(rgba)
    visible = pixels[..., 3] >= 128
    if not visible.any():
        raise ValueError("The image has no visible pixels.")

    visible_rgb = pixels[..., :3][visible]
    luma = rgb_luma(visible_rgb)
    total = int(len(visible_rgb))

    unique_rgb, counts = np.unique(visible_rgb, axis=0, return_counts=True)
    color_rows = []
    for color, count in zip(unique_rgb, counts):
        r, g, b = (int(color[0]), int(color[1]), int(color[2]))
        hex_str = f"#{r:02x}{g:02x}{b:02x}"
        color_luma = float(rgb_luma(color.astype(np.float32)))
        color_rows.append((
            -int(count),
            hex_str,
            {
                "hex": hex_str,
                "luma": round(color_luma, 1),
                "pct": round(100.0 * int(count) / total, 2),
                "pixels": int(count),
            },
        ))
    color_rows.sort(key=lambda item: (item[0], item[1]))

    report: dict = {
        "size": [rgba.width, rgba.height],
        "unique_colors": int(len(unique_rgb)),
        **_summarize_luma(luma),
        "seams": seam_continuity(rgba.convert("RGB")),
        "colors": [row[2] for row in color_rows[:top_colors]],
    }

    if reference is not None:
        ref_rgba = reference.convert("RGBA")
        ref_pixels = np.asarray(ref_rgba)
        ref_visible = ref_pixels[..., 3] >= 128
        if not ref_visible.any():
            raise ValueError("The reference image has no visible pixels.")
        ref_luma = rgb_luma(ref_pixels[..., :3][ref_visible])
        ref_summary = _summarize_luma(ref_luma)
        report["reference"] = {
            "size": [ref_rgba.width, ref_rgba.height],
            "luma_mean": ref_summary["luma_mean"],
            "luma_delta": round(float(luma.mean() - ref_luma.mean()), 1),
            "luma_std": ref_summary["luma_std"],
            "luma_percentiles": ref_summary["luma_percentiles"],
            "value_bands": ref_summary["value_bands"],
            "seams": seam_continuity(ref_rgba.convert("RGB")),
        }

    return report
