#!/usr/bin/env python3
"""Hand-crafted seamless Studio Ghibli pixel-art paving stones tile (128x128)."""

from pathlib import Path
import math
import numpy as np
from PIL import Image

CASE_DIR = Path(__file__).resolve().parents[1]
STEPS_DIR = CASE_DIR / "build" / "steps"
N = 128
U = 16  # 8x8 herringbone unit cells on 128x128 grid

# Curated 22-color Ghibli daylight stonework & moss palette
PALETTE_HEX = {
    # Crevices & Earth Mortar
    "crevice_deep": "#233336",
    "crevice_soil": "#344446",
    "earth_dark": "#4c544b",
    "earth_mid": "#6b6959",
    # Primary Warm Limestone Ramp
    "stone_sh2": "#3e4d52",
    "stone_sh1": "#57666b",
    "stone_mid2": "#7c8786",
    "stone_mid1": "#a4a599",
    "stone_base": "#c7bfb0",
    "stone_lit": "#ddd4c0",
    "stone_hi": "#eee7d2",
    # Warm Golden-Ochre Variation
    "warm_sh": "#857865",
    "warm_mid": "#bda982",
    "warm_lit": "#dcc996",
    "warm_hi": "#efe4b4",
    # Cool Weathered Sage-Mineral Variation
    "sage_mid": "#91a198",
    "sage_lit": "#b8c4b6",
    # Sunlit Moss & Crevice Foliage
    "moss_deep": "#2c4d39",
    "moss_dark": "#466f3b",
    "moss_mid": "#6f9940",
    "moss_lit": "#9ec04e",
    "moss_hi": "#cdd86b",
}

NAMES = list(PALETTE_HEX.keys())
IDX = {name: i for i, name in enumerate(NAMES)}
PAL_RGB = np.array(
    [tuple(bytes.fromhex(PALETTE_HEX[name][1:])) for name in NAMES],
    dtype=np.uint8,
)

# Mathematically verified staggered temperaments across the 32 bricks:
# 17 neutral ('N'), 8 warm ('W'), 7 cool ('C'); zero W-W or C-C adjacency on torus,
# balanced across all four 4x4 quadrants with zero 4x4 sub-period collisions.
BRICK_TEMPS = [
    "N", "N", "C", "W",  # r = 0
    "N", "W", "W", "C",  # r = 1
    "N", "N", "C", "N",  # r = 2
    "N", "N", "W", "N",  # r = 3
    "W", "C", "N", "N",  # r = 4
    "C", "N", "N", "N",  # r = 5
    "C", "W", "N", "W",  # r = 6
    "W", "C", "N", "N",  # r = 7
]


def torus_delta(coord: np.ndarray, center: float, size: int = N) -> np.ndarray:
    """Signed shortest distance on a periodic torus of length `size`."""
    return (coord - center + size / 2.0) % size - size / 2.0


def build_bricks() -> list[dict]:
    """Build the 32 herringbone bricks matching the 8x8 reference partition."""
    # (corner_radii (TL,TR,BR,BL), center_shift (sx,sy), edge_fracture)
    geom_specs = [
        ((2.4, 2.0, 2.7, 2.2), (0.25, -0.15), None),             # 0: H (0,2..3)
        ((2.1, 2.6, 2.2, 2.5), (-0.20, 0.25), "top_edge_chip"),  # 1: H (0,6..7) wraps X
        ((2.5, 2.1, 2.3, 2.4), (0.15, 0.20), None),              # 2: V (0..1,1)
        ((2.2, 2.5, 2.7, 2.0), (-0.25, -0.15), None),            # 3: V (0..1,5)
        ((2.4, 2.2, 2.3, 2.6), (0.25, 0.10), None),              # 4: H (1,3..4)
        ((2.0, 2.5, 2.2, 2.3), (-0.15, -0.25), "bottom_crack"),  # 5: H (1,7..0) wraps X
        ((2.3, 2.1, 2.6, 2.7), (0.10, -0.25), None),             # 6: V (1..2,2)
        ((2.5, 2.6, 2.1, 2.2), (-0.20, 0.15), None),             # 7: V (1..2,6)
        ((2.2, 2.3, 2.6, 2.1), (0.15, 0.25), None),              # 8: H (2,0..1)
        ((2.6, 2.0, 2.2, 2.5), (-0.25, 0.10), None),             # 9: H (2,4..5)
        ((2.1, 2.5, 2.4, 2.2), (0.20, -0.15), "left_seam_split"),# 10: V (2..3,3)
        ((2.4, 2.2, 2.1, 2.6), (-0.10, 0.25), None),             # 11: V (2..3,7)
        ((2.3, 2.6, 2.1, 2.3), (-0.15, 0.20), None),             # 12: H (3,1..2)
        ((2.5, 2.1, 2.4, 2.6), (0.20, -0.20), None),             # 13: H (3,5..6)
        ((2.2, 2.4, 2.6, 2.0), (-0.20, -0.10), None),            # 14: V (3..4,0)
        ((2.7, 2.1, 2.3, 2.4), (0.15, 0.15), None),              # 15: V (3..4,4)
        ((2.1, 2.6, 2.3, 2.4), (-0.20, 0.15), None),             # 16: H (4,2..3)
        ((2.5, 2.2, 2.4, 2.0), (0.20, -0.15), None),             # 17: H (4,6..7) wraps X
        ((2.2, 2.4, 2.1, 2.6), (-0.15, 0.20), "right_edge_notch"),# 18: V (4..5,1)
        ((2.4, 2.0, 2.7, 2.3), (0.15, -0.20), None),             # 19: V (4..5,5)
        ((2.6, 2.3, 2.1, 2.1), (-0.15, 0.25), None),             # 20: H (5,3..4)
        ((2.2, 2.1, 2.6, 2.4), (0.25, 0.10), None),              # 21: H (5,7..0) wraps X
        ((2.4, 2.5, 2.1, 2.3), (-0.20, -0.15), None),            # 22: V (5..6,2)
        ((2.0, 2.3, 2.5, 2.7), (0.10, 0.20), "top_corner_split"),# 23: V (5..6,6)
        ((2.5, 2.2, 2.3, 2.6), (-0.25, -0.15), None),            # 24: H (6,0..1)
        ((2.1, 2.7, 2.4, 2.2), (0.15, 0.20), None),              # 25: H (6,4..5)
        ((2.3, 2.1, 2.6, 2.3), (-0.10, 0.25), None),             # 26: V (6..7,3)
        ((2.6, 2.4, 2.2, 2.0), (0.20, -0.20), None),             # 27: V (6..7,7)
        ((2.2, 2.5, 2.1, 2.4), (0.15, -0.15), None),             # 28: H (7,1..2)
        ((2.4, 2.0, 2.7, 2.2), (-0.20, 0.20), "bottom_chip"),    # 29: H (7,5..6)
        ((2.6, 2.3, 2.2, 2.5), (0.20, 0.15), None),              # 30: V (7..0,0) wraps Y
        ((2.1, 2.6, 2.4, 2.2), (-0.15, -0.20), None),            # 31: V (7..0,4) wraps Y
    ]

    bricks = []
    si = 0
    for r in range(8):
        for c in ((r + 2) % 4, (r + 2) % 4 + 4):
            radii, shift, frac = geom_specs[si]
            bricks.append({
                "id": si,
                "orient": "H",
                "r": r,
                "c": c,
                "cx": (c * U + 16.0) % N,
                "cy": (r * U + 8.0) % N,
                "w": 32.0,
                "h": 16.0,
                "temp": BRICK_TEMPS[si],
                "radii": radii,
                "shift": shift,
                "fracture": frac,
            })
            si += 1
        for c in ((r + 1) % 4, (r + 1) % 4 + 4):
            radii, shift, frac = geom_specs[si]
            bricks.append({
                "id": si,
                "orient": "V",
                "r": r,
                "c": c,
                "cx": (c * U + 8.0) % N,
                "cy": (r * U + 16.0) % N,
                "w": 16.0,
                "h": 32.0,
                "temp": BRICK_TEMPS[si],
                "radii": radii,
                "shift": shift,
                "fracture": frac,
            })
            si += 1
    return bricks


def compute_brick_geometry(bricks: list[dict]):
    """Evaluate clean rounded-box SDF with gentle low-freq taper and silhouette polish."""
    yy, xx = np.mgrid[:N, :N].astype(np.float32)
    px = xx + 0.5
    py = yy + 0.5

    n_bricks = len(bricks)
    sdfs = np.empty((n_bricks, N, N), dtype=np.float32)
    local_dx = np.empty((n_bricks, N, N), dtype=np.float32)
    local_dy = np.empty((n_bricks, N, N), dtype=np.float32)

    for i, b in enumerate(bricks):
        sx, sy = b["shift"]
        dx = torus_delta(px, b["cx"] + sx * 0.35)
        dy = torus_delta(py, b["cy"] + sy * 0.35)
        local_dx[i] = dx
        local_dy[i] = dy

        # Subtle broad organic camber (low frequency so edges stay clean and gently bowed)
        nx_u = dx / (b["w"] * 0.5)
        ny_u = dy / (b["h"] * 0.5)
        phase = i * 1.43
        camber = 0.15 * np.sin(nx_u * 2.1 + phase) + 0.14 * np.cos(ny_u * 2.0 - phase)

        rtl, rtr, rbr, rbl = b["radii"]
        rad = np.where(
            dx < 0,
            np.where(dy < 0, rtl, rbl),
            np.where(dy < 0, rtr, rbr),
        )

        # Leaves clean ~2px mortar joints, widening smoothly at rounded corners
        hx = b["w"] * 0.5 - 1.15
        hy = b["h"] * 0.5 - 1.15

        qx = np.abs(dx) - (hx - rad)
        qy = np.abs(dy) - (hy - rad)
        outside = np.hypot(np.maximum(qx, 0.0), np.maximum(qy, 0.0))
        inside = np.minimum(np.maximum(qx, qy), 0.0)
        sdfs[i] = outside + inside - rad + camber

    order = np.argsort(sdfs, axis=0)
    best_id = order[0]
    second_id = order[1]
    d1 = np.take_along_axis(sdfs, best_id[None], axis=0)[0]
    d2 = np.take_along_axis(sdfs, second_id[None], axis=0)[0]

    brick_mask = (d1 <= 0.0) & ((d2 - d1) >= 1.15)
    owner = np.where(brick_mask, best_id, -1)

    # Enforce strict 4-connected separation between distinct bricks
    for dy_r, dx_r in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nb = np.roll(owner, shift=(dy_r, dx_r), axis=(0, 1))
        collision = (owner >= 0) & (nb >= 0) & (owner != nb)
        if collision.any():
            nb_d1 = np.roll(d1, shift=(dy_r, dx_r), axis=(0, 1))
            owner[collision & (d1 >= nb_d1)] = -1

    # Silhouette polish: remove stray 1px spurs, then fill harmless 1px edge pinholes
    for _ in range(2):
        same_n = np.zeros((N, N), dtype=np.int32)
        for dy_r, dx_r in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            same_n += (np.roll(owner, shift=(dy_r, dx_r), axis=(0, 1)) == owner) & (owner >= 0)
        owner[(owner >= 0) & (same_n <= 1)] = -1

    # Fill 1px concave edge pinholes when all adjacent bricks are >= 2px away
    n_up = np.roll(owner, 1, axis=0)
    n_dn = np.roll(owner, -1, axis=0)
    n_lf = np.roll(owner, 1, axis=1)
    n_rt = np.roll(owner, -1, axis=1)
    empty = owner < 0
    for b_idx in range(n_bricks):
        cnt = (
            (n_up == b_idx).astype(np.int32)
            + (n_dn == b_idx).astype(np.int32)
            + (n_lf == b_idx).astype(np.int32)
            + (n_rt == b_idx).astype(np.int32)
        )
        # Safe if no neighbor belongs to a DIFFERENT brick
        other = (
            ((n_up >= 0) & (n_up != b_idx))
            | ((n_dn >= 0) & (n_dn != b_idx))
            | ((n_lf >= 0) & (n_lf != b_idx))
            | ((n_rt >= 0) & (n_rt != b_idx))
        )
        owner[empty & (cnt >= 3) & (~other)] = b_idx

    brick_mask = owner >= 0
    dx_own = np.take_along_axis(local_dx, best_id[None], axis=0)[0]
    dy_own = np.take_along_axis(local_dy, best_id[None], axis=0)[0]
    depth = -d1

    grad_x = (np.roll(d1, -1, axis=1) - np.roll(d1, 1, axis=1)) * 0.5
    grad_y = (np.roll(d1, -1, axis=0) - np.roll(d1, 1, axis=0)) * 0.5
    gnorm = np.hypot(grad_x, grad_y) + 1e-6
    inx = -grad_x / gnorm
    iny = -grad_y / gnorm

    return {
        "owner": owner,
        "mask": brick_mask,
        "d1": d1,
        "depth": depth,
        "dx": dx_own,
        "dy": dy_own,
        "inx": inx,
        "iny": iny,
        "px": px,
        "py": py,
    }


def make_moss_pockets(geom: dict) -> tuple[np.ndarray, np.ndarray]:
    """Build organic irregular moss cushions tucked into corner pockets and narrow joints."""
    px, py = geom["px"], geom["py"]
    mask = geom["mask"]
    depth = geom["depth"]

    # Irregular slanted lobes tucked tightly into mortar intersections & joints
    # (cx, cy, rx, ry, angle_rad, weight) -- kept away from brick fractures!
    lobes = [
        # Q00: organic dual-lobe corner cushion at (16, 16)
        (16.0, 15.8, 2.5, 2.2, 0.45, 1.05),
        (16.2, 19.2, 1.7, 2.1, -0.25, 0.90),
        # Q00: tiny subtle joint sprout near (64, 32)
        (63.6, 32.0, 2.5, 1.5, 0.25, 0.90),
        # Q01: corner tuft at (96, 16) trailing lightly along joint
        (96.0, 15.6, 2.3, 2.0, -0.40, 1.00),
        (93.0, 16.0, 1.8, 1.3, 0.15, 0.82),
        # Wraps X=0 seamlessly at (0/128, 56..60) vertical joint
        (0.0, 56.5, 1.6, 2.8, 0.22, 0.95),
        (1.4, 54.0, 1.3, 1.5, -0.35, 0.78),
        # Q10: natural skewed corner pillow at (32, 96) (no rigid 90-deg bar)
        (31.5, 96.2, 2.3, 2.1, 0.55, 1.02),
        (29.0, 96.2, 1.8, 1.4, -0.20, 0.84),
        # Q11: small crevice moss wisp at (80, 80)
        (80.0, 79.8, 2.1, 1.7, -0.45, 0.92),
        # Q11: slender vertical crevice moss wisp at (112, 96)
        (112.0, 96.0, 1.5, 2.8, 0.15, 0.92),
        (112.0, 99.0, 1.3, 1.6, -0.30, 0.82),
        # Wraps Y=0 seamlessly at (64, 0/128) horizontal joint
        (63.8, 0.0, 2.8, 1.7, -0.25, 0.98),
        (61.5, 0.6, 1.6, 1.3, 0.35, 0.80),
    ]

    moss_score = np.full((N, N), -1.0, dtype=np.float32)
    for k, (mx, my, rx, ry, ang, wt) in enumerate(lobes):
        dx = torus_delta(px, mx)
        dy = torus_delta(py, my)
        ca, sa = math.cos(ang), math.sin(ang)
        ux = dx * ca + dy * sa
        uy = -dx * sa + dy * ca
        undul = 0.22 * np.sin(px * 0.65 + py * 0.55 + k * 1.7) + 0.16 * np.cos(px * 0.45 - py * 0.75)
        raw = (1.0 - np.hypot(ux / rx, uy / ry)) * wt + undul * 0.45
        moss_score = np.maximum(moss_score, raw)

    # Moss stays rooted in crevices (~mask) and feathers softly onto stone rims (depth < 1.15)
    stone_block = np.where(mask, np.maximum(0.0, depth - 0.10) * 0.95, 0.0)
    effective = moss_score - stone_block
    moss_mask = effective > 0.12
    # Clean stray 1px detached moss dots on torus
    same_m = (
        np.roll(moss_mask, 1, axis=0).astype(int)
        + np.roll(moss_mask, -1, axis=0).astype(int)
        + np.roll(moss_mask, 1, axis=1).astype(int)
        + np.roll(moss_mask, -1, axis=1).astype(int)
    )
    moss_mask &= same_m >= 1
    return moss_mask, effective


def draw_edge_fractures(canvas: np.ndarray, bricks: list[dict], geom: dict) -> None:
    """Add sparse edge-anchored hairline fractures (Ref 2 boulder style)."""
    owner = geom["owner"]
    depth = geom["depth"]

    for b in bricks:
        frac = b["fracture"]
        if frac is None:
            continue
        bid = b["id"]
        sel = owner == bid
        temp = b["temp"]
        dark_c = IDX["stone_sh2"] if temp != "W" else IDX["warm_sh"]
        lit_c = IDX["warm_hi"] if temp == "W" else IDX["stone_hi"]

        # Edge-anchored polylines entering from stone bevels & tapering inward
        if frac == "top_edge_chip":
            # Enters from top bevel near x=-5 and curves slightly down-right
            pts = [(-5, -6), (-5, -5), (-4, -4), (-3, -3), (-3, -2)]
            lit_off = (1, 0)
        elif frac == "bottom_crack":
            # Enters from bottom shadow edge near x=4 and tapers upward
            pts = [(4, 6), (4, 5), (3, 4), (3, 3), (2, 2)]
            lit_off = (-1, 0)
        elif frac == "left_seam_split":
            # Enters from left sunlit bevel near y=-4
            pts = [(-6, -4), (-5, -4), (-4, -3), (-3, -3), (-2, -2)]
            lit_off = (0, -1)
        elif frac == "right_edge_notch":
            # Enters from right shadow bevel near y=3
            pts = [(6, 3), (5, 3), (4, 2), (3, 2), (2, 1)]
            lit_off = (0, -1)
        elif frac == "top_corner_split":
            # Small subtle corner hairline from upper-right edge
            pts = [(5, -10), (4, -9), (3, -8), (3, -7)]
            lit_off = (-1, 0)
        elif frac == "bottom_chip":
            # Small chip notch entering bottom-left bevel
            pts = [(-7, 6), (-6, 5), (-5, 4), (-4, 4)]
            lit_off = (0, -1)
        else:
            continue

        cx_i = int(round(b["cx"]))
        cy_i = int(round(b["cy"]))
        for k, (lx, ly) in enumerate(pts):
            gx = (cx_i + lx) % N
            gy = (cy_i + ly) % N
            if sel[gy, gx]:
                canvas[gy, gx] = dark_c
            # Only highlight the inner/sunlit lip of the crack on mid steps
            if 1 <= k <= len(pts) - 2:
                lx2, ly2 = lx + lit_off[0], ly + lit_off[1]
                gx2 = (cx_i + lx2) % N
                gy2 = (cy_i + ly2) % N
                if sel[gy2, gx2] and depth[gy2, gx2] >= 0.8 and (lx2, ly2) not in pts:
                    canvas[gy2, gx2] = lit_c


def render_passes() -> None:
    STEPS_DIR.mkdir(parents=True, exist_ok=True)
    bricks = build_bricks()
    geom = compute_brick_geometry(bricks)
    owner = geom["owner"]
    mask = geom["mask"]
    depth = geom["depth"]
    dx = geom["dx"]
    dy = geom["dy"]
    inx = geom["inx"]
    iny = geom["iny"]
    px = geom["px"]
    py = geom["py"]

    moss_mask, moss_score = make_moss_pockets(geom)
    sun_bevel = (inx + iny) * 0.7071

    # ------------------------------------------------------------------
    # PASS 1: 01_silhouette.png
    # ------------------------------------------------------------------
    p1 = np.full((N, N), IDX["crevice_deep"], dtype=np.uint8)
    for b in bricks:
        p1[owner == b["id"]] = IDX["stone_mid2"] if b["orient"] == "H" else IDX["stone_sh1"]
    Image.fromarray(PAL_RGB[p1]).save(STEPS_DIR / "01_silhouette.png")

    # ------------------------------------------------------------------
    # PASS 2: 02_blockin.png (Crisp flat-topped stones & 1px directional bevel)
    # ------------------------------------------------------------------
    p2 = np.full((N, N), IDX["earth_dark"], dtype=np.uint8)
    cast_ao = (~mask) & (np.roll(mask, 1, axis=0) | np.roll(mask, 1, axis=1))
    p2[(~mask) & (~cast_ao)] = IDX["crevice_soil"]
    p2[cast_ao] = IDX["crevice_deep"]

    # Deterministic per-brick flat top tone (high-key sunlit balance, zero dark outliers)
    flat_tones: dict[int, int] = {}
    n_idx = 0
    for b in bricks:
        bid = b["id"]
        temp = b["temp"]
        if temp == "W":
            flat_tones[bid] = IDX["warm_lit"]
        elif temp == "C":
            flat_tones[bid] = IDX["sage_lit"]
        else:
            flat_tones[bid] = IDX["stone_base"] if (n_idx % 2 == 1) else IDX["stone_lit"]
            n_idx += 1

    for b in bricks:
        bid = b["id"]
        bm = owner == bid
        temp = b["temp"]
        c_top = flat_tones[bid]
        c_hi = IDX["warm_hi"] if temp == "W" else IDX["stone_hi"]

        is_bevel = bm & (depth < 1.25)
        p2[bm] = c_top
        p2[is_bevel & (sun_bevel > 0.25)] = c_hi
        p2[is_bevel & (sun_bevel < -0.20)] = IDX["stone_sh1"]

    p2[moss_mask] = IDX["moss_dark"]
    p2[moss_mask & (moss_score > 0.42)] = IDX["moss_mid"]
    Image.fromarray(PAL_RGB[p2]).save(STEPS_DIR / "02_blockin.png")

    # ------------------------------------------------------------------
    # PASS 3: 03_shading.png (Flat-topped Ghibli stones + crisp 1px bevels)
    # ------------------------------------------------------------------
    p3 = np.full((N, N), IDX["earth_dark"], dtype=np.uint8)

    # Textured sunlit earth-and-slate mortar bed
    mortar_wave = np.sin(px * 0.23 + py * 0.17) + 0.65 * np.cos(px * 0.39 - py * 0.29)
    p3[(~mask) & (mortar_wave < -0.15)] = IDX["crevice_soil"]
    p3[(~mask) & (mortar_wave > 0.72)] = IDX["earth_mid"]
    # Crisp 1px ambient drop shadow ONLY under bottom and right brick edges
    p3[cast_ao] = IDX["crevice_deep"]

    for b in bricks:
        bid = b["id"]
        bm = owner == bid
        temp = b["temp"]
        c_top = flat_tones[bid]
        c_hi = IDX["warm_hi"] if temp == "W" else IDX["stone_hi"]

        nx_f = dx / (b["w"] * 0.5)
        ny_f = dy / (b["h"] * 0.5)

        # Fill entire top plateau with ONE clean flat base plane
        face = bm & (depth >= 1.25)
        p3[face] = c_top

        # Keep ~30% of bricks purely flat-topped; on others paint AT MOST ONE crisp
        # edge-anchored painterly facet (1 palette step, never floating spots or gradients)
        if bid % 3 != 0:
            mode = (bid * 7) % 4
            if mode == 0:
                # Upper-left sunlit corner wash anchored cleanly to TL rim
                ox, oy, rx, ry = -0.82, -0.78, 1.05, 1.02
            elif mode == 1:
                # Lower-right subtle bounce/weathering facet anchored to BR corner
                ox, oy, rx, ry = 0.85, 0.75, 0.98, 0.96
            elif mode == 2:
                # Lower-left worn slab facet anchored to BL rim
                ox, oy, rx, ry = -0.78, 0.82, 1.02, 0.95
            else:
                # Upper-right sunlit glaze anchored to TR edge
                ox, oy, rx, ry = 0.80, -0.80, 0.96, 1.02

            patch_dist = (
                ((nx_f - ox) / rx) ** 2
                + ((ny_f - oy) / ry) ** 2
                + 0.22 * np.sin(nx_f * 2.3 + ny_f * 2.0 + bid * 1.6)
            )
            patch_mask = face & (patch_dist < 0.92)

            # Shift strictly 1 palette step based on the brick's flat top color
            if c_top == IDX["stone_lit"]:
                c_patch = IDX["warm_lit"] if (mode in (0, 3) and bid % 2 == 0) else IDX["stone_base"]
            elif c_top == IDX["stone_base"]:
                c_patch = IDX["stone_lit"] if mode in (0, 3) else IDX["stone_mid1"]
            elif c_top == IDX["warm_lit"]:
                c_patch = IDX["stone_lit"] if mode in (0, 3) else IDX["warm_mid"]
            else:  # sage_lit
                c_patch = IDX["stone_lit"] if mode in (0, 3) else IDX["stone_mid1"]

            p3[patch_mask] = c_patch

        # Crisp 1px chamfered bevels (decisive 2-tone edge, no soft roll-off)
        bevel = bm & (depth < 1.25)
        bevel_break = np.sin(dx * 0.28 + dy * 0.26 + bid * 1.7)
        p3[bevel] = c_top

        # Top & left sunlit chamfer broken naturally into clean sunlit segments
        lit_edge = bevel & (sun_bevel > 0.25) & (bevel_break > -0.30)
        p3[lit_edge] = c_hi

        # Subtle midtone corner turn pixel on sunlit-to-shadow transitions
        turn_edge = bevel & (sun_bevel >= -0.20) & (sun_bevel <= 0.25)
        if c_top in (IDX["stone_lit"], IDX["warm_lit"], IDX["sage_lit"]):
            p3[turn_edge & (sun_bevel < 0.0)] = IDX["stone_mid1"]

        # Bottom & right cool slate shadow chamfer, deepening on tight bottom-right corner
        p3[bevel & (sun_bevel < -0.20)] = IDX["stone_sh1"]
        p3[bevel & (sun_bevel < -0.68)] = IDX["stone_sh2"]

    draw_edge_fractures(p3, bricks, geom)

    # Organic crevice-hugging moss cushions with tight contact shadow
    moss_dr = (
        np.roll(moss_mask, 1, axis=0)
        | np.roll(moss_mask, 1, axis=1)
        | np.roll(np.roll(moss_mask, 1, axis=0), 1, axis=1)
    )
    p3[(~moss_mask) & moss_dr & mask] = IDX["moss_deep"]

    mgx = (np.roll(moss_score, -1, axis=1) - np.roll(moss_score, 1, axis=1)) * 0.5
    mgy = (np.roll(moss_score, -1, axis=0) - np.roll(moss_score, 1, axis=0)) * 0.5
    moss_sun = moss_score + (mgx + mgy) * 0.70

    # Punchy 2-3 tone cel-clustered moss inside crevices
    p3[moss_mask] = IDX["moss_dark"]
    p3[moss_mask & (moss_sun > 0.22)] = IDX["moss_mid"]
    p3[moss_mask & (moss_sun > 0.56)] = IDX["moss_lit"]
    sunlit_moss_tips = moss_mask & (moss_sun > 0.85) & ((np.sin(px * 0.19 + py * 0.23)) > 0.1)
    p3[sunlit_moss_tips] = IDX["moss_hi"]

    Image.fromarray(PAL_RGB[p3]).save(STEPS_DIR / "03_shading.png")

    # ------------------------------------------------------------------
    # PASS 4: 04_cleanup.png (Toroidal orphan cleanup)
    # ------------------------------------------------------------------
    p4 = p3.copy()
    protected = {
        IDX["stone_hi"], IDX["warm_hi"], IDX["moss_hi"],
        IDX["crevice_deep"], IDX["moss_deep"],
    }
    n_up = np.roll(p4, 1, axis=0)
    n_dn = np.roll(p4, -1, axis=0)
    n_lf = np.roll(p4, 1, axis=1)
    n_rt = np.roll(p4, -1, axis=1)
    n_ul = np.roll(n_up, 1, axis=1)
    n_ur = np.roll(n_up, -1, axis=1)
    n_dl = np.roll(n_dn, 1, axis=1)
    n_dr = np.roll(n_dn, -1, axis=1)

    same_any = (
        (p4 == n_up) | (p4 == n_dn) | (p4 == n_lf) | (p4 == n_rt)
        | (p4 == n_ul) | (p4 == n_ur) | (p4 == n_dl) | (p4 == n_dr)
    )
    for y in range(N):
        for x in range(N):
            if not same_any[y, x] and int(p4[y, x]) not in protected:
                nbrs = [int(n_up[y, x]), int(n_dn[y, x]), int(n_lf[y, x]), int(n_rt[y, x])]
                p4[y, x] = max(set(nbrs), key=nbrs.count)

    Image.fromarray(PAL_RGB[p4]).save(STEPS_DIR / "04_cleanup.png")
    print(f"[draw] Wrote 4 native {N}x{N} passes to {STEPS_DIR}")


if __name__ == "__main__":
    render_passes()
