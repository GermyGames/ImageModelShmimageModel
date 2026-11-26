#!/usr/bin/env python3
"""Reference-sculpted seamless Ghibli pixel-art rocky cliff texture (128x128)."""

from collections import deque
from pathlib import Path
import math
import numpy as np
from PIL import Image

CASE_DIR = Path(__file__).resolve().parents[1]
REF_PATH = CASE_DIR / "source" / "reference.jpg"
STEPS_DIR = CASE_DIR / "build" / "steps"
N = 128

# Deep rugged 18-color Ghibli rocky cliff palette (grounded luma ~95-115, rich warm/cool contrast)
PALETTE_HEX = {
    # Deep Crevices & Overhang Shadows
    "crevice_deep": "#162228",
    "rock_sh2": "#25343c",
    "rock_sh1": "#384850",
    # Core Rugged Cliff Rock Ramp
    "rock_mid3": "#4d5a5f",
    "rock_mid2": "#636c6b",
    "rock_mid1": "#7b7f78",
    "rock_base": "#969285",
    "rock_lit": "#b4ab97",
    "rock_hi": "#d4c9af",
    # Subtle Warm Sun-Kissed Rock Tints
    "warm_mid": "#7c705d",
    "warm_lit": "#a49376",
    "warm_hi": "#cbb68e",
    # Subtle Cool Mineral / Sky-Bounce Tints
    "cool_mid": "#576968",
    "cool_lit": "#7c8d86",
    # Sparse Crevice Ledge Moss
    "moss_deep": "#1d3829",
    "moss_dark": "#33592f",
    "moss_mid": "#578238",
    "moss_lit": "#85aa43",
}

NAMES = list(PALETTE_HEX.keys())
IDX = {name: i for i, name in enumerate(NAMES)}
PAL_RGB = np.array(
    [tuple(bytes.fromhex(PALETTE_HEX[name][1:])) for name in NAMES],
    dtype=np.uint8,
)


def periodic_gaussian(arr: np.ndarray, sigma: float) -> np.ndarray:
    """Exact periodic Gaussian blur on the N x N torus via 2D FFT."""
    fy = np.fft.fftfreq(N)[:, None]
    fx = np.fft.fftfreq(N)[None, :]
    kernel_hat = np.exp(-2.0 * (np.pi ** 2) * (sigma ** 2) * (fx ** 2 + fy ** 2))
    return np.fft.ifft2(np.fft.fft2(arr) * kernel_hat).real.astype(np.float32)


def toroidal_kuwahara(img: np.ndarray, radius: int = 2) -> np.ndarray:
    """Toroidal 4-quadrant Kuwahara filter: flattens photo grain while sharpening rock planes."""
    pad = np.pad(img, radius, mode="wrap")
    h, w = img.shape
    size = radius + 1

    # 4 overlapping quadrant slices relative to center pixel
    slices = [
        (0, size, 0, size),             # Top-Left
        (0, size, radius, radius + size),  # Top-Right
        (radius, radius + size, 0, size),  # Bottom-Left
        (radius, radius + size, radius, radius + size),  # Bottom-Right
    ]

    means = np.empty((4, h, w), dtype=np.float32)
    vars_ = np.empty((4, h, w), dtype=np.float32)

    for q, (y0, y1, x0, x1) in enumerate(slices):
        acc = np.zeros((h, w), dtype=np.float32)
        acc2 = np.zeros((h, w), dtype=np.float32)
        for dy in range(y0, y1):
            for dx in range(x0, x1):
                patch = pad[dy:dy + h, dx:dx + w]
                acc += patch
                acc2 += patch * patch
        n_pix = float(size * size)
        mean = acc / n_pix
        var = acc2 / n_pix - mean * mean
        means[q] = mean
        vars_[q] = np.maximum(0.0, var)

    best_q = np.argmin(vars_, axis=0)
    return np.take_along_axis(means, best_q[None], axis=0)[0]


def absorb_small_components(grid: np.ndarray, max_size: int = 2, protected: set[int] | None = None) -> np.ndarray:
    """Absorb tiny <3px isolated clusters into their majority 4-neighbor color on the torus."""
    out = grid.copy()
    visited = np.zeros((N, N), dtype=bool)
    prot = protected or set()

    for sy in range(N):
        for sx in range(N):
            if visited[sy, sx]:
                continue
            val = int(out[sy, sx])
            comp = []
            q = deque([(sy, sx)])
            visited[sy, sx] = True
            while q:
                cy, cx = q.popleft()
                comp.append((cy, cx))
                for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    ny, nx = (cy + dy) % N, (cx + dx) % N
                    if not visited[ny, nx] and int(out[ny, nx]) == val:
                        visited[ny, nx] = True
                        q.append((ny, nx))
            if len(comp) <= max_size and val not in prot:
                # Collect surrounding 4-neighbor colors outside this component
                comp_set = set(comp)
                nbr_vals = []
                for cy, cx in comp:
                    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        ny, nx = (cy + dy) % N, (cx + dx) % N
                        if (ny, nx) not in comp_set:
                            nbr_vals.append(int(out[ny, nx]))
                if nbr_vals:
                    rep = max(set(nbr_vals), key=nbr_vals.count)
                    for cy, cx in comp:
                        out[cy, cx] = rep
    return out


def prune_sparse_mask(mask: np.ndarray, min_size: int = 4) -> np.ndarray:
    """Remove 8-connected mask islands smaller than `min_size` on the torus."""
    out = mask.copy()
    visited = np.zeros((N, N), dtype=bool)
    for sy in range(N):
        for sx in range(N):
            if out[sy, sx] and not visited[sy, sx]:
                comp = []
                q = deque([(sy, sx)])
                visited[sy, sx] = True
                while q:
                    cy, cx = q.popleft()
                    comp.append((cy, cx))
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dy == 0 and dx == 0:
                                continue
                            ny, nx = (cy + dy) % N, (cx + dx) % N
                            if out[ny, nx] and not visited[ny, nx]:
                                visited[ny, nx] = True
                                q.append((ny, nx))
                if len(comp) < min_size:
                    for cy, cx in comp:
                        out[cy, cx] = False
    return out


def torus_delta(coord: np.ndarray, center: float, size: int = N) -> np.ndarray:
    return (coord - center + size / 2.0) % size - size / 2.0


def make_crevice_moss(crevice_mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Anchor 3 small organic moss tufts directly onto real deep cliff ledges."""
    yy, xx = np.mgrid[:N, :N].astype(np.float32) + 0.5

    # Prefer solid horizontal/diagonal ledge runs of crevices across distinct quadrants
    solid_crev = crevice_mask & (
        np.roll(crevice_mask, 1, axis=1) | np.roll(crevice_mask, -1, axis=1)
    )
    coords = np.argwhere(solid_crev if solid_crev.any() else crevice_mask)

    targets = [
        (30.0, 32.0, 4.2, 1.9, 0.48, 0.96),   # Q00 NW->SE shelf
        (108.0, 60.0, 3.8, 1.8, 0.42, 0.92),  # Q01/Q11 right shelf
        (54.0, 108.0, 3.4, 1.7, 0.50, 0.88),  # Q10 lower shelf
    ]

    pockets = []
    for k, (tx, ty, rx, ry, ang, wt) in enumerate(targets):
        if len(coords) > 0:
            dy = torus_delta(coords[:, 0].astype(np.float32), ty)
            dx = torus_delta(coords[:, 1].astype(np.float32), tx)
            best = int(np.argmin(dx * dx + dy * dy))
            ay = float(coords[best, 0]) + 0.5
            ax = float(coords[best, 1]) + 0.5
        else:
            ay, ax = ty, tx
        pockets.append((ax, (ay - 0.7) % N, rx, ry, ang, wt))
        if k == 0:
            pockets.append(((ax + 2.4) % N, (ay + 0.7) % N, 2.5, 1.5, ang - 0.15, 0.86))

    moss_score = np.full((N, N), -1.0, dtype=np.float32)
    for k, (mx, my, rx, ry, ang, wt) in enumerate(pockets):
        dx = torus_delta(xx, mx)
        dy = torus_delta(yy, my)
        ca, sa = math.cos(ang), math.sin(ang)
        ux = dx * ca + dy * sa
        uy = -dx * sa + dy * ca
        undul = 0.22 * np.sin(xx * 0.75 + yy * 0.55 + k * 1.9) + 0.14 * np.cos(xx * 0.45 - yy * 0.8)
        raw = (1.0 - np.hypot(ux / rx, uy / ry)) * wt + undul
        moss_score = np.maximum(moss_score, raw)

    moss_mask = moss_score > 0.20
    moss_mask = prune_sparse_mask(moss_mask, min_size=4)
    return moss_mask, moss_score


def render_passes() -> None:
    STEPS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load 512x512 seamless cliff reference and 4x4 block-average to 128x128 torus
    with Image.open(REF_PATH) as im:
        src = np.asarray(im.convert("RGB"), dtype=np.float32)
    h, w, _ = src.shape
    if (h, w) == (512, 512):
        ds = src.reshape(N, 4, N, 4, 3).mean(axis=(1, 3))
    else:
        ds = np.asarray(
            Image.fromarray(src.astype(np.uint8)).resize((N, N), Image.Resampling.BOX),
            dtype=np.float32,
        )

    luma_raw = 0.2126 * ds[..., 0] + 0.7152 * ds[..., 1] + 0.0722 * ds[..., 2]
    warm_raw = ds[..., 0] - ds[..., 2]  # warm-cool chroma channel

    # 2. Toroidal low-frequency equalization (balances tile-wide drift while preserving sharp ledges)
    broad = periodic_gaussian(luma_raw, sigma=18.0)
    luma_eq = luma_raw - 0.55 * (broad - broad.mean())

    # 3. Edge-preserving toroidal Kuwahara planarization (radius 2 then radius 3)
    # Flattens photo speckle into broad, crisp painted rock planes with zero gradient blur
    kuw = toroidal_kuwahara(luma_eq, radius=2)
    kuw = toroidal_kuwahara(kuw, radius=3)

    # Multi-scale local relief on torus
    local_mean = periodic_gaussian(luma_eq, sigma=3.5)
    valley = local_mean - luma_eq
    ridge = luma_eq - local_mean

    # Top-left directional edge derivative on planarized rock
    gx = (np.roll(kuw, -1, axis=1) - np.roll(kuw, 1, axis=1)) * 0.5
    gy = (np.roll(kuw, -1, axis=0) - np.roll(kuw, 1, axis=0)) * 0.5
    sun_edge = -(gx + gy)

    # 4. Quantize planarized relief into crisp flat rock tiers (broad midtones, punchy highlights)
    q10, q28, q50, q72, q88, q95 = np.percentile(kuw, [10, 28, 50, 72, 88, 95])
    tier = np.zeros((N, N), dtype=np.uint8)
    tier[kuw >= q10] = 1
    tier[kuw >= q28] = 2
    tier[kuw >= q50] = 3
    tier[kuw >= q72] = 4
    tier[kuw >= q88] = 5
    tier[(kuw >= q95) & (ridge > 2.5)] = 6

    tier = absorb_small_components(tier, max_size=4)

    tier_palette = np.array([
        IDX["rock_sh2"],
        IDX["rock_sh1"],
        IDX["rock_mid3"],
        IDX["rock_mid2"],
        IDX["rock_mid1"],
        IDX["rock_base"],
        IDX["rock_lit"],
    ], dtype=np.uint8)

    # 5. Deep rocky crevices strictly along real sharp clefts & dark overhangs (~6-8% area)
    crev_raw = ((valley > 24.5) & (luma_eq < q28)) | ((luma_eq < np.percentile(luma_eq, 3.5)) & (valley > 15.0))
    crevice_mask = prune_sparse_mask(crev_raw, min_size=4)
    # Flank crevices strictly 1px directly below overhangs with rock_sh2
    crev_flank = np.roll(crevice_mask, 1, axis=0) & (~crevice_mask)

    # 6. Sparse organic ledge moss anchored onto real cliff crevices
    moss_mask, moss_score = make_crevice_moss(crevice_mask)

    # ------------------------------------------------------------------
    # PASS 1: 01_silhouette.png (Macro craggy rock masses & deep clefts)
    # ------------------------------------------------------------------
    p1 = np.full((N, N), IDX["rock_mid2"], dtype=np.uint8)
    p1[tier <= 1] = IDX["rock_sh1"]
    p1[tier >= 4] = IDX["rock_mid1"]
    p1[crev_flank] = IDX["rock_sh2"]
    p1[crevice_mask] = IDX["crevice_deep"]
    Image.fromarray(PAL_RGB[p1]).save(STEPS_DIR / "01_silhouette.png")

    # ------------------------------------------------------------------
    # PASS 2: 02_blockin.png (Flat planarized rock tiers, deep clefts, flat moss)
    # ------------------------------------------------------------------
    p2 = tier_palette[tier]
    p2[crev_flank & (tier >= 2)] = IDX["rock_sh2"]
    p2[crevice_mask] = IDX["crevice_deep"]
    p2[moss_mask] = IDX["moss_dark"]
    p2[moss_mask & (moss_score > 0.45)] = IDX["moss_mid"]
    Image.fromarray(PAL_RGB[p2]).save(STEPS_DIR / "02_blockin.png")

    # ------------------------------------------------------------------
    # PASS 3: 03_shading.png (Warm/cool rock glazes, 1px ridge crests & moss)
    # ------------------------------------------------------------------
    p3 = p2.copy()

    # Broad low-frequency warm/cool mineral shift across whole rock shelves (no mottled flecks)
    chroma_smooth = periodic_gaussian(warm_raw, sigma=7.0)
    c_hi_thresh = np.percentile(chroma_smooth, 68)
    c_lo_thresh = np.percentile(chroma_smooth, 30)

    warm_base_mask = (p3 == IDX["rock_base"]) & (chroma_smooth > c_hi_thresh) & (~crev_flank)
    warm_mid_mask = (p3 == IDX["rock_mid1"]) & (chroma_smooth > c_hi_thresh + 1.5) & (~crev_flank)
    cool_mid_mask = (p3 == IDX["rock_mid2"]) & (chroma_smooth < c_lo_thresh)
    cool_lit_mask = (p3 == IDX["rock_mid1"]) & (chroma_smooth < c_lo_thresh - 1.0)

    p3[prune_sparse_mask(warm_base_mask, min_size=10)] = IDX["warm_lit"]
    p3[prune_sparse_mask(warm_mid_mask, min_size=10)] = IDX["warm_mid"]
    p3[prune_sparse_mask(cool_mid_mask, min_size=10)] = IDX["cool_mid"]
    p3[prune_sparse_mask(cool_lit_mask, min_size=10)] = IDX["cool_lit"]

    # Crisp broken 1px sunlit ridge highlights along sharp protruding rocky edges
    dn_drop = (np.roll(tier, -1, axis=0) <= 2) | np.roll(crevice_mask, -1, axis=0) | (np.roll(tier, -1, axis=1) <= 2)
    is_sunlit_rock = (
        (p3 == IDX["rock_lit"])
        | (p3 == IDX["rock_base"])
        | (p3 == IDX["warm_lit"])
    )
    ridge_hi = (
        is_sunlit_rock
        & (~crevice_mask)
        & (~moss_mask)
        & (ridge > 4.0)
        & (sun_edge > 3.5)
        & dn_drop
    )
    warm_hi_mask = ridge_hi & (p3 == IDX["warm_lit"])
    p3[ridge_hi] = IDX["rock_hi"]
    p3[warm_hi_mask] = IDX["warm_hi"]

    # Lush cel-clustered moss tucked onto select recessed shelf pockets
    moss_below = np.roll(moss_mask, 1, axis=0) | np.roll(moss_mask, 1, axis=1)
    p3[(~moss_mask) & (~crevice_mask) & moss_below] = IDX["moss_deep"]

    mgx = (np.roll(moss_score, -1, axis=1) - np.roll(moss_score, 1, axis=1)) * 0.5
    mgy = (np.roll(moss_score, -1, axis=0) - np.roll(moss_score, 1, axis=0)) * 0.5
    moss_sun = moss_score + (mgx + mgy) * 0.65

    p3[moss_mask] = IDX["moss_dark"]
    p3[moss_mask & (moss_sun > 0.42)] = IDX["moss_mid"]
    p3[moss_mask & (moss_sun > 0.68)] = IDX["moss_lit"]

    Image.fromarray(PAL_RGB[p3]).save(STEPS_DIR / "03_shading.png")

    # ------------------------------------------------------------------
    # PASS 4: 04_cleanup.png (Toroidal orphan cleanup protecting ridges & moss)
    # ------------------------------------------------------------------
    protected = {
        IDX["rock_hi"], IDX["warm_hi"], IDX["moss_lit"],
        IDX["crevice_deep"], IDX["moss_deep"],
    }
    p4 = absorb_small_components(p3, max_size=3, protected=protected)
    Image.fromarray(PAL_RGB[p4]).save(STEPS_DIR / "04_cleanup.png")
    print(f"[draw] Wrote 4 native {N}x{N} passes to {STEPS_DIR}")


if __name__ == "__main__":
    render_passes()
