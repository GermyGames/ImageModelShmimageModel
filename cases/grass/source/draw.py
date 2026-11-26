#!/usr/bin/env python3
"""Procedural painterly Ghibli pixel-art seamless grass texture (128x128)."""

from pathlib import Path
import math
import sys
import numpy as np
from PIL import Image

CASE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = CASE_DIR.parents[1]
STEPS_DIR = CASE_DIR / "build" / "steps"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import tile_tools  # noqa: E402

N = 128

# Curated 16-color Ghibli lush meadow grass palette
# Cool tones stay rich cool forest emerald so shaded turf integrates cleanly with warm greens.
PALETTE_HEX = {
    # Deep Root Shadows & Tucked Crevices
    "shadow_deep": "#152d24",
    "shadow_mid": "#1f412f",
    "shadow_soft": "#2c5736",
    # Cool Forest Emerald Shaded Turf Tints
    "cool_dark": "#1d4636",
    "cool_mid": "#2c6042",
    "cool_lit": "#3f7b4c",
    # Core Lush Ghibli Emerald Grass Ramp
    "grass_dark": "#376b36",
    "grass_mid2": "#477f3a",
    "grass_mid1": "#5c963f",
    "grass_lit": "#76ae46",
    # Warm Olive / Sun-Drenched Meadow Glaze
    "warm_dark": "#527932",
    "warm_mid": "#6d953b",
    "warm_lit": "#8bb046",
    # Crisp Sunlit Chartreuse Blade Tips
    "tip_mid": "#99c44e",
    "tip_hi": "#b9d85d",
    "tip_glint": "#d7e578",
}

NAMES = list(PALETTE_HEX.keys())
IDX = {name: i for i, name in enumerate(NAMES)}
PAL_RGB = np.array(
    [tuple(bytes.fromhex(PALETTE_HEX[name][1:])) for name in NAMES],
    dtype=np.uint8,
)


def periodic_fbm(
    n: int,
    freq_min: float,
    freq_max: float,
    falloff: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Synthesize a smooth zero-mean unit-std periodic scalar field on an N x N torus."""
    noise = rng.normal(0.0, 1.0, size=(n, n))
    fy = np.fft.fftfreq(n)[:, None] * n
    fx = np.fft.fftfreq(n)[None, :] * n
    kmag = np.hypot(fy, fx)
    weights = np.where(
        (kmag >= freq_min) & (kmag <= freq_max),
        np.where(kmag > 0.0, kmag, 1.0) ** (-falloff),
        0.0,
    )
    field = np.fft.ifft2(np.fft.fft2(noise) * weights).real.astype(np.float32)
    std = float(field.std())
    return (field - float(field.mean())) / (std if std > 1e-6 else 1.0)


def toroidal_blue_noise(
    count: int,
    min_dist: float,
    rng: np.random.Generator,
    candidates_per_step: int = 24,
    score_field: np.ndarray | None = None,
    min_score: float = -10.0,
) -> list[tuple[float, float]]:
    """Sample evenly spaced anchors on the N x N torus with optional subtle height preference."""
    pts: list[tuple[float, float]] = []
    min_d2 = min_dist * min_dist
    max_attempts = count * 14

    for _ in range(max_attempts):
        if len(pts) >= count:
            break
        best_pt: tuple[float, float] | None = None
        best_dist2 = -1.0

        for _ in range(candidates_per_step):
            cx = float(rng.uniform(0.0, N))
            cy = float(rng.uniform(0.0, N))
            if score_field is not None:
                val = float(score_field[int(cy) % N, int(cx) % N])
                if val < min_score and rng.random() > 0.25:
                    continue
            if not pts:
                best_pt = (cx, cy)
                best_dist2 = float(N * N)
                break
            arr = np.asarray(pts, dtype=np.float32)
            dx = tile_tools.torus_delta(arr[:, 0], cx, N)
            dy = tile_tools.torus_delta(arr[:, 1], cy, N)
            d2 = float(np.min(dx * dx + dy * dy))
            if d2 > best_dist2:
                best_dist2 = d2
                best_pt = (cx, cy)

        if best_pt is not None and (best_dist2 >= min_d2 or len(pts) < count // 2):
            pts.append(best_pt)
            if best_dist2 < min_d2 * 0.65:
                min_d2 *= 0.96
    return pts


def blade_point(
    x0: float, y0: float, angle: float, length: float, bend: float, t: float
) -> tuple[float, float, float]:
    """Return curved sweeping grass blade coordinates and tangent angle for t in [0, 1]."""
    dx0, dy0 = math.cos(angle), math.sin(angle)
    nx0, ny0 = -dy0, dx0
    dist = length * t
    arc = bend * (t * t) * length * 0.42
    bx = x0 + dx0 * dist + nx0 * arc
    by = y0 + dy0 * dist + ny0 * arc
    tx = dx0 + nx0 * (bend * t * 0.84)
    ty = dy0 + ny0 * (bend * t * 0.84)
    return bx, by, math.atan2(ty, tx)


def draw_tapered_blade(
    grid: np.ndarray,
    x0: float,
    y0: float,
    angle: float,
    length: float,
    bend: float,
    root_col: int,
    body_col: int,
    tip_col: int | None = None,
) -> None:
    """Rasterize one slender curved grass blade modulo N (2px base t < 0.28, 1px tip ribbon)."""
    steps = max(24, int(round(length * 3.5)))
    for t in np.linspace(0.0, 1.0, steps):
        tf = float(t)
        bx, by, tang = blade_point(x0, y0, angle, length, bend, tf)
        px = int(round(bx)) % N
        py = int(round(by)) % N

        if tf < 0.30:
            col = root_col
        elif tip_col is not None and tf >= 0.65:
            col = tip_col
        else:
            col = body_col

        grid[py, px] = col
        if tf < 0.28:
            nx, ny = -math.sin(tang), math.cos(tang)
            grid[int(round(by + ny)) % N, int(round(bx + nx)) % N] = col


def draw_grass_whorl(
    grid: np.ndarray,
    cx: float,
    cy: float,
    base_angle: float,
    whorl_bend: float,
    rng: np.random.Generator,
    blade_specs: list[tuple[float, float, float, int, int, int | None]],
    shadow_col: int | None = None,
) -> None:
    """Draw a 2-3 blade whorl radiating from one tight root point with optional tucked shadow."""
    geom: list[tuple[float, float, float, float, float, int, int, int | None]] = []
    for ang_off, length, bend_factor, root_col, body_col, tip_col in blade_specs:
        jx = float(rng.uniform(-0.85, 0.85))
        jy = float(rng.uniform(-0.85, 0.85))
        ang = base_angle + ang_off
        bend = whorl_bend * bend_factor
        geom.append((cx + jx, cy + jy, ang, length, bend, root_col, body_col, tip_col))

    # 1. Stamp tight shadow wedge (+1, +1) under lower base BEFORE drawing blades
    if shadow_col is not None:
        rx, ry = int(round(cx)) % N, int(round(cy)) % N
        grid[(ry + 1) % N, (rx + 1) % N] = shadow_col
        grid[(ry + 1) % N, (rx + 2) % N] = shadow_col
        for x0, y0, ang, length, bend, _, _, _ in geom:
            steps = max(8, int(round(length * 1.4)))
            for t in np.linspace(0.0, 0.32, steps):
                bx, by, _ = blade_point(x0, y0, ang, length, bend, float(t))
                grid[int(round(by + 1.0)) % N, int(round(bx + 1.0)) % N] = shadow_col

    # 2. Draw secondary/companion blades behind hero blade so leading blade reads cleanly
    for x0, y0, ang, length, bend, root_col, body_col, tip_col in reversed(geom):
        draw_tapered_blade(grid, x0, y0, ang, length, bend, root_col, body_col, tip_col)


def render_passes() -> None:
    STEPS_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20261127)

    # 1. Toroidal equalized height & temperature fields + multi-directional swirling curl flow
    raw_height = periodic_fbm(N, freq_min=2.0, freq_max=5.0, falloff=1.35, rng=rng)
    eq_height = tile_tools.equalize_toroidal_luma(raw_height, sigma=16.0, strength=0.85)
    height_field = (eq_height - float(eq_height.mean())) / (float(eq_height.std()) + 1e-6)

    raw_temp = periodic_fbm(N, freq_min=2.0, freq_max=5.0, falloff=1.4, rng=rng)
    eq_temp = tile_tools.equalize_toroidal_luma(raw_temp, sigma=16.0, strength=0.85)
    smooth_temp = tile_tools.periodic_gaussian(eq_temp, sigma=4.0)
    temp_field = (smooth_temp - float(smooth_temp.mean())) / (float(smooth_temp.std()) + 1e-6)

    # Stream function curl + gentle SW->NE bias for authentic multi-whorl turf (freq >= 2 prevents 1-tile vortex eye)
    psi = periodic_fbm(N, freq_min=2.0, freq_max=4.0, falloff=1.55, rng=rng)
    vx = (np.roll(psi, -1, axis=0) - np.roll(psi, 1, axis=0)) * 0.5
    vy = -(np.roll(psi, -1, axis=1) - np.roll(psi, 1, axis=1)) * 0.5
    mag = np.hypot(vx, vy) + 1e-6
    vx_blend = vx / mag + 0.42
    vy_blend = vy / mag - 0.42
    flow_angle = np.arctan2(vy_blend, vx_blend)

    bend_noise = periodic_fbm(N, freq_min=2.0, freq_max=5.0, falloff=1.5, rng=rng)
    whorl_bend_field = np.where(bend_noise >= 0.0, 1.0, -1.0) * (
        0.35 + 0.43 * np.abs(np.tanh(bend_noise * 1.1))
    )

    # Evenly spaced toroidal blue-noise whorl anchors across 3 canopy tiers
    whorls_1 = toroidal_blue_noise(295, min_dist=5.8, rng=rng)
    whorls_2 = toroidal_blue_noise(265, min_dist=6.1, rng=rng)
    whorls_3 = toroidal_blue_noise(
        170, min_dist=7.5, rng=rng, score_field=height_field, min_score=-0.45
    )

    # ------------------------------------------------------------------
    # PASS 1: 01_silhouette.png (Lush shadowed turf mattress & swirling under-blades)
    # ------------------------------------------------------------------
    p1 = np.full((N, N), IDX["shadow_mid"], dtype=np.uint8)
    p1[height_field < -0.95] = IDX["shadow_deep"]
    p1[(height_field >= 0.35)] = IDX["shadow_soft"]
    p1[(height_field >= -0.95) & (height_field < 0.15) & (temp_field < -0.55)] = IDX["cool_dark"]

    for cx, cy in whorls_1:
        ix, iy = int(cx) % N, int(cy) % N
        ang = float(flow_angle[iy, ix]) + float(rng.uniform(-0.22, 0.22))
        wb = float(whorl_bend_field[iy, ix])
        tval = float(temp_field[iy, ix])
        hval = float(height_field[iy, ix])

        if tval < -0.35:
            root_c = IDX["cool_dark"]
            body_c = IDX["cool_mid"] if hval > -0.2 else IDX["shadow_soft"]
        else:
            root_c = IDX["shadow_soft"] if hval > 0.0 else IDX["cool_dark"]
            body_c = IDX["grass_dark"] if hval > -0.3 else IDX["shadow_soft"]

        hero_len = float(rng.uniform(9.2, 12.8))
        comp_len = float(rng.uniform(6.4, 9.2))
        div = float(rng.uniform(0.32, 0.52)) * (1.0 if rng.random() < 0.5 else -1.0)
        specs = [
            (0.0, hero_len, 1.0, root_c, body_c, None),
            (div, comp_len, 0.88, root_c, body_c, None),
        ]
        if rng.random() < 0.45:
            specs.append((-div * 0.9, float(rng.uniform(4.5, 6.4)), -0.7, IDX["cool_dark"], IDX["shadow_soft"], None))
        draw_grass_whorl(p1, cx, cy, ang, wb, rng, specs, shadow_col=None)
    Image.fromarray(PAL_RGB[p1]).save(STEPS_DIR / "01_silhouette.png")

    # ------------------------------------------------------------------
    # PASS 2: 02_blockin.png (Lush emerald midtone carpet with tucked base accents)
    # ------------------------------------------------------------------
    p2 = p1.copy()
    for cx, cy in whorls_2:
        ix, iy = int(cx) % N, int(cy) % N
        ang = float(flow_angle[iy, ix]) + float(rng.uniform(-0.24, 0.24))
        wb = float(whorl_bend_field[iy, ix])
        tval = float(temp_field[iy, ix])
        hval = float(height_field[iy, ix])

        if tval < -0.55 and hval < 0.2:
            root_c = IDX["cool_mid"]
            body_h = IDX["cool_lit"]
            body_s = IDX["cool_mid"]
        elif tval > 0.55:
            root_c = IDX["warm_dark"]
            body_h = IDX["warm_mid"]
            body_s = IDX["grass_mid2"]
        elif hval > 0.2:
            root_c = IDX["grass_dark"]
            body_h = IDX["grass_mid1"]
            body_s = IDX["grass_mid2"]
        else:
            root_c = IDX["shadow_soft"]
            body_h = IDX["grass_mid2"]
            body_s = IDX["grass_dark"]

        hero_len = float(rng.uniform(9.5, 13.5))
        comp_len = float(rng.uniform(6.5, 9.5))
        div = float(rng.uniform(0.32, 0.55)) * (1.0 if wb >= 0.0 else -1.0)
        specs = [
            (0.0, hero_len, 1.0, root_c, body_h, None),
            (div, comp_len, 0.9, root_c, body_s, None),
        ]
        if rng.random() < 0.45:
            specs.append((-div * 0.95, float(rng.uniform(4.5, 6.5)), -0.75, IDX["grass_dark"], body_s, None))

        sh_col = IDX["shadow_deep"] if (hval < -0.1 and rng.random() < 0.45) else IDX["shadow_mid"]
        draw_grass_whorl(p2, cx, cy, ang, wb, rng, specs, shadow_col=sh_col)
    Image.fromarray(PAL_RGB[p2]).save(STEPS_DIR / "02_blockin.png")

    # ------------------------------------------------------------------
    # PASS 3: 03_shading.png (Sunlit curving hero blades & connected chartreuse tips)
    # ------------------------------------------------------------------
    p3 = p2.copy()
    for cx, cy in whorls_3:
        ix, iy = int(cx) % N, int(cy) % N
        ang = float(flow_angle[iy, ix]) + float(rng.uniform(-0.22, 0.22))
        wb = float(whorl_bend_field[iy, ix])
        tval = float(temp_field[iy, ix])
        hval = float(height_field[iy, ix])

        # Hero blades curving slightly up/left catch brighter top-left sun glints
        catches_sun = (math.cos(ang + 2.35) > -0.25) or (hval > 0.25)

        if tval > 0.45:
            root_c = IDX["warm_dark"]
            body_h = IDX["warm_lit"]
            body_c = IDX["warm_mid"]
            tip_h = IDX["tip_glint"] if (catches_sun and hval > 0.2 and rng.random() < 0.65) else IDX["tip_hi"]
            tip_c = IDX["tip_mid"]
        elif tval < -0.55:
            root_c = IDX["cool_mid"]
            body_h = IDX["grass_lit"]
            body_c = IDX["cool_lit"]
            tip_h = IDX["tip_hi"] if catches_sun else IDX["tip_mid"]
            tip_c = IDX["grass_lit"]
        else:
            root_c = IDX["grass_dark"]
            body_h = IDX["grass_lit"] if (hval > -0.15 or catches_sun) else IDX["grass_mid1"]
            body_c = IDX["grass_mid1"]
            tip_h = IDX["tip_glint"] if (catches_sun and hval > 0.35 and rng.random() < 0.55) else IDX["tip_hi"]
            tip_c = IDX["tip_mid"]

        hero_len = float(rng.uniform(9.8, 13.5))
        comp_len = float(rng.uniform(6.6, 9.5))
        div = float(rng.uniform(0.32, 0.55)) * (1.0 if wb >= 0.0 else -1.0)
        specs = [
            (0.0, hero_len, 1.0, root_c, body_h, tip_h),
            (div, comp_len, 0.9, root_c, body_c, tip_c),
        ]
        if rng.random() < 0.35:
            specs.append((-div * 0.9, float(rng.uniform(4.8, 6.5)), -0.75, IDX["grass_dark"], IDX["grass_mid2"], None))

        sh_col = IDX["shadow_deep"] if rng.random() < 0.35 else IDX["shadow_mid"]
        draw_grass_whorl(p3, cx, cy, ang, wb, rng, specs, shadow_col=sh_col)
    Image.fromarray(PAL_RGB[p3]).save(STEPS_DIR / "03_shading.png")

    # ------------------------------------------------------------------
    # PASS 4: 04_cleanup.png (Clean isolated 1px midtone dots; protect razor tips & deep roots)
    # ------------------------------------------------------------------
    protected = {
        IDX["tip_glint"],
        IDX["tip_hi"],
        IDX["tip_mid"],
        IDX["shadow_deep"],
        IDX["shadow_mid"],
    }
    p4 = tile_tools.absorb_small_components(p3, max_size=1, protected=protected)
    Image.fromarray(PAL_RGB[p4]).save(STEPS_DIR / "04_cleanup.png")
    print(f"[draw] Wrote 4 native {N}x{N} passes to {STEPS_DIR}")


if __name__ == "__main__":
    render_passes()
