#!/usr/bin/env python3
"""Procedural Ghibli pixel-art seamless medieval castle bricks texture (128x128)."""

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

# Curated 20-color Ghibli weathered castle stone, iron rust, and moss palette
PALETTE_HEX = {
    # Deep Recessed Mortar & Overhang Shadows
    "mortar_deep": "#1a252a",
    "mortar_mid": "#2a383e",
    "stone_sh2": "#3f4d52",
    "stone_sh1": "#596566",
    # Core Weathered Castle Limestone / Granite Ramp
    "stone_mid2": "#747d78",
    "stone_mid1": "#91958b",
    "stone_base": "#aea998",
    "stone_lit": "#cac2ad",
    "stone_hi": "#e2dac4",
    # Warm Ochre / Sandstone Weathered Blocks
    "warm_sh": "#786c57",
    "warm_mid": "#9c8b6e",
    "warm_lit": "#bda986",
    # Cool Slate-Gray Weathered Blocks
    "cool_mid": "#6d7b7a",
    "cool_lit": "#8f9d99",
    # Subtle Medieval Iron / Rust Weathering Streaks
    "rust_dark": "#6b4731",
    "rust_mid": "#91613f",
    # Lush Ghibli Crevice Moss (harmonized with grass & cliff-rock)
    "moss_deep": "#1d3829",
    "moss_dark": "#355d30",
    "moss_mid": "#598639",
    "moss_lit": "#8eb446",
}

NAMES = list(PALETTE_HEX.keys())
IDX = {name: i for i, name in enumerate(NAMES)}
PAL_RGB = np.array(
    [tuple(bytes.fromhex(PALETTE_HEX[name][1:])) for name in NAMES],
    dtype=np.uint8,
)

# 8 irregular medieval ashlar courses wrapping 128x128 with zero aligned vertical joints
# Format: (course_height, start_x, block_widths, split_double_idx_or_None)
COURSE_SPECS = [
    (15, 10, [22, 28, 20, 30, 28], None),
    (17, 21, [26, 22, 27, 21, 32], None),
    (15, 4,  [24, 29, 25, 22, 28], None),
    (20, 14, [30, 24, 32, 20, 22], 1),     # block 1 (w=24) splits vertically into 2 narrow bricks
    (14, 28, [27, 29, 24, 24, 24], None),
    (17, 16, [25, 25, 13, 35, 30], None),  # includes slim 13px header stone
    (15, 4,  [26, 26, 34, 18, 24], None),
    (15, 19, [26, 25, 28, 24, 25], None),
]

# Temperaments carefully staggered with ZERO horizontal or vertical W-W / C-C / L-L collisions:
# 'L' = light limestone, 'N' = neutral medium limestone, 'D' = weathered darker stone,
# 'W' = warm sandstone ochre, 'C' = cool slate-gray
BLOCK_TEMPS = [
    "N", "C", "N", "W", "D",        # C0: 0..4
    "W", "D", "L", "N", "C",        # C1: 5..9  (mason mark on wide id=7 'L')
    "L", "N", "D", "C", "W",        # C2: 10..14 (id=12 is 'D' above double-brick id=16)
    "C", "W", "N", "N", "L", "D",   # C3: 15..20 (16='W', 17='N' stacked narrow bricks; 18='N')
    "L", "D", "C", "W", "N",        # C4: 21..25
    "W", "N", "D", "L", "C",        # C5: 26..30 (28 slim 13px header='D'; 29 wide 35px='L' mark)
    "N", "C", "W", "D", "N",        # C6: 31..35
    "D", "L", "N", "C", "W",        # C7: 36..40
]


def periodic_fbm(
    n: int,
    freq_min: float,
    freq_max: float,
    falloff: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Zero-mean unit-std periodic scalar field on an N x N torus."""
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


def build_blocks(rng: np.random.Generator) -> list[dict]:
    """Construct 41 ashlar stone definitions across 8 wrapping courses."""
    blocks: list[dict] = []
    # Shift courses vertically by 7px so row wraps cross inside blocks rather than on y=0 seam
    y_shift = 7.0
    y0 = 0
    bid = 0
    for c_idx, (ch, x0, widths, split_idx) in enumerate(COURSE_SPECS):
        x = x0
        for b_idx, bw in enumerate(widths):
            if split_idx is not None and b_idx == split_idx:
                h_top = ch // 2
                h_bot = ch - h_top
                for sub_i, (sy, sh) in enumerate([(y0, h_top), (y0 + h_top, h_bot)]):
                    blocks.append({
                        "id": bid,
                        "course": c_idx,
                        "cx": (x + bw * 0.5) % N,
                        "cy": (sy + sh * 0.5 + y_shift) % N,
                        "w": float(bw),
                        "h": float(sh),
                        "rad": float(rng.uniform(1.1, 1.5)),
                        "temp": BLOCK_TEMPS[bid],
                        "inset_x": float(rng.uniform(0.55, 0.72)),
                        "inset_y": float(rng.uniform(0.65, 0.88)),
                        "protrude": float(rng.uniform(-0.15, 0.35)),
                        "split_sub": sub_i,
                    })
                    bid += 1
            else:
                blocks.append({
                    "id": bid,
                    "course": c_idx,
                    "cx": (x + bw * 0.5) % N,
                    "cy": (y0 + ch * 0.5 + y_shift) % N,
                    "w": float(bw),
                    "h": float(ch),
                    "rad": float(rng.uniform(1.3, 2.0)),
                    "temp": BLOCK_TEMPS[bid],
                    "inset_x": float(rng.uniform(0.58, 0.78)),
                    "inset_y": float(rng.uniform(0.72, 0.98)),
                    "protrude": float(rng.uniform(-0.20, 0.45)),
                    "split_sub": None,
                })
                bid += 1
            x = (x + bw) % N
        y0 += ch
    assert bid == len(BLOCK_TEMPS) and y0 == N
    return blocks


def rasterize_geometry(blocks: list[dict], rng: np.random.Generator) -> dict[str, np.ndarray]:
    """Compute toroidal SDF, block ownership, local coordinates, and directional bevel distances."""
    yy, xx = np.mgrid[:N, :N].astype(np.float32) + 0.5

    # Crisp hand-hewn limestone edge undulation (subtle chisel wobble without melted lumps)
    rough_macro = periodic_fbm(N, freq_min=6.0, freq_max=16.0, falloff=1.4, rng=rng)
    rough_micro = periodic_fbm(N, freq_min=16.0, freq_max=32.0, falloff=1.3, rng=rng)
    edge_warp = 0.28 * rough_macro + 0.14 * rough_micro

    owner = np.full((N, N), -1, dtype=np.int16)
    inward_best = np.full((N, N), -99.0, dtype=np.float32)
    second_best = np.full((N, N), -99.0, dtype=np.float32)
    norm_x = np.zeros((N, N), dtype=np.float32)
    norm_y = np.zeros((N, N), dtype=np.float32)

    for b in blocks:
        dx = tile_tools.torus_delta(xx, b["cx"], N)
        dy = tile_tools.torus_delta(yy, b["cy"], N)
        hw = b["w"] * 0.5 - b["inset_x"]
        hh = b["h"] * 0.5 - b["inset_y"]
        rad = b["rad"]

        qx = np.abs(dx) - (hw - rad)
        qy = np.abs(dy) - (hh - rad)
        sdf = np.hypot(np.maximum(qx, 0.0), np.maximum(qy, 0.0)) + np.minimum(np.maximum(qx, qy), 0.0) - rad
        inward = -sdf + edge_warp

        better = inward > inward_best
        second_best = np.where(better, inward_best, np.maximum(second_best, inward))
        inward_best = np.where(better, inward, inward_best)
        owner = np.where(better, b["id"], owner)
        norm_x = np.where(better, dx / max(hw, 1.0), norm_x)
        norm_y = np.where(better, dy / max(hh, 1.0), norm_y)

    # Guarantee crisp 1-2px mortar gap between any two neighboring blocks across torus
    seam_gap = inward_best - second_best
    is_stone = (inward_best > -0.05) & (seam_gap > 0.65)

    return {
        "owner": owner,
        "inward": inward_best,
        "is_stone": is_stone,
        "nx": norm_x,
        "ny": norm_y,
        "rough": edge_warp,
    }


def make_crevice_moss(geom: dict[str, np.ndarray], blocks: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    """Grow moss directly out of mortar T-junctions and shaded stone rims (never floating mid-face)."""
    yy, xx = np.mgrid[:N, :N].astype(np.float32) + 0.5
    is_stone = geom["is_stone"]

    # Anchor squarely ON mortar junctions ((±0.95, ±0.95) half-extents) so moss hugs real seams
    pockets_spec = [
        (blocks[8],  -0.96,  0.96, 4.8, 2.5,  0.18, 1.06),  # Upper-right mortar T-joint
        (blocks[12],  0.94, -0.92, 5.4, 2.8, -0.22, 1.10),  # Upper-mid overhanging shelf
        (blocks[31], -0.96, -0.92, 5.6, 3.0, -0.18, 1.12),  # Lower-left T-joint shelf
        (blocks[31], -0.92,  0.95, 4.4, 2.4,  0.24, 1.04),  # Secondary lower-left joint
        (blocks[24],  0.95,  0.94, 4.2, 2.3,  0.15, 1.00),  # Mid-right mortar corner
    ]

    moss_score = np.full((N, N), -1.0, dtype=np.float32)
    for k, (b, ox_f, oy_f, rx, ry, ang, wt) in enumerate(pockets_spec):
        mx = (b["cx"] + ox_f * b["w"] * 0.5) % N
        my = (b["cy"] + oy_f * b["h"] * 0.5) % N
        dx = tile_tools.torus_delta(xx, mx, N)
        dy = tile_tools.torus_delta(yy, my, N)
        ca, sa = math.cos(ang), math.sin(ang)
        ux = dx * ca + dy * sa
        uy = -dx * sa + dy * ca
        undul = (
            0.22 * np.sin(xx * 0.62 + yy * 0.52 + k * 1.7)
            + 0.14 * np.cos(xx * 0.45 - yy * 0.68)
        )
        raw = (1.0 - np.hypot(ux / rx, uy / ry)) * wt + undul
        moss_score = np.maximum(moss_score, raw)

    # Strictly keep moss tethered to mortar or the immediate 2.6px outer stone rim
    moss_raw = (moss_score > 0.24) & ((~is_stone) | (geom["inward"] < 2.6))
    moss_mask = tile_tools.prune_sparse_mask(moss_raw, min_size=5)
    return moss_mask, moss_score


def render_passes() -> None:
    STEPS_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20261125)

    blocks = build_blocks(rng)
    geom = rasterize_geometry(blocks, rng)
    owner = geom["owner"]
    inward = geom["inward"]
    is_stone = geom["is_stone"]
    nx = geom["nx"]
    ny = geom["ny"]

    plane_fbm = periodic_fbm(N, freq_min=4.0, freq_max=11.0, falloff=1.3, rng=rng)
    moss_mask, moss_score = make_crevice_moss(geom, blocks)

    # Color role lookup per temperament: (main_face, sunlit_bevel, chisel_step, shadow_bevel, top_glint)
    ROLE_MAP = {
        "L": ("stone_base", "stone_lit",  "stone_mid1", "stone_sh1", "stone_hi"),
        "N": ("stone_mid1", "stone_base", "stone_mid2", "stone_sh1", "stone_lit"),
        "D": ("stone_mid2", "stone_mid1", "stone_sh1",  "stone_sh2", "stone_base"),
        "W": ("warm_mid",   "warm_lit",   "warm_sh",    "warm_sh",   "stone_lit"),
        "C": ("cool_lit",   "stone_lit",  "cool_mid",   "stone_sh1", "stone_hi"),
    }

    # Overhang cast shadow directly beneath stone bottoms into recessed mortar
    above_is_stone = np.roll(is_stone, 1, axis=0) | np.roll(is_stone, 2, axis=0)
    under_overhang = (~is_stone) & above_is_stone

    # ------------------------------------------------------------------
    # PASS 1: 01_silhouette.png (Recessed mortar channels & 41 sturdy ashlar silhouettes)
    # ------------------------------------------------------------------
    p1 = np.full((N, N), IDX["mortar_mid"], dtype=np.uint8)
    p1[under_overhang] = IDX["mortar_deep"]
    for b in blocks:
        m = is_stone & (owner == b["id"])
        t = b["temp"]
        p1[m] = IDX["stone_mid1"] if t in ("L", "N", "W") else IDX["stone_mid2"]
    Image.fromarray(PAL_RGB[p1]).save(STEPS_DIR / "01_silhouette.png")

    # ------------------------------------------------------------------
    # PASS 2: 02_blockin.png (Flat block values, crisp TL bevels, BR undersides, flat moss)
    # ------------------------------------------------------------------
    p2 = np.full((N, N), IDX["mortar_mid"], dtype=np.uint8)
    p2[under_overhang] = IDX["mortar_deep"]

    for b in blocks:
        bid = b["id"]
        m = is_stone & (owner == bid)
        base_n, lit_n, _, sh_n, _ = ROLE_MAP[b["temp"]]
        p2[m] = IDX[base_n]

        bevel_tl = m & (inward <= 1.65) & ((ny < -0.35) | (nx < -0.50)) & (~((nx > 0.65) & (ny > 0.35)))
        bevel_br = m & (inward <= 2.15) & ((ny > 0.42) | (nx > 0.58))
        bevel_deep = m & (inward <= 1.05) & (ny > 0.68)

        p2[bevel_tl] = IDX[lit_n]
        p2[bevel_br] = IDX[sh_n]
        if b["temp"] != "W":
            p2[bevel_deep] = IDX["stone_sh2"]

    p2[moss_mask] = IDX["moss_dark"]
    p2[moss_mask & (moss_score > 0.52)] = IDX["moss_mid"]
    Image.fromarray(PAL_RGB[p2]).save(STEPS_DIR / "02_blockin.png")

    # ------------------------------------------------------------------
    # PASS 3: 03_shading.png (Edge-anchored chisel steps, cracks, rust drips, carved marks, glints, moss)
    # ------------------------------------------------------------------
    p3 = p2.copy()

    for b in blocks:
        bid = b["id"]
        m = is_stone & (owner == bid)
        if not m.any():
            continue
        base_n, lit_n, step_n, sh_n, hi_n = ROLE_MAP[b["temp"]]
        interior = m & (inward > 1.7)

        # Flat-dominant weathering: at most one crisp edge-anchored chiseled corner/shelf
        if bid % 3 != 2:
            side = -1.0 if (bid % 2 == 0) else 1.0
            corner_slope = nx * 0.6 * side + ny * 0.55 + plane_fbm * 0.30
            step_mask = interior & (inward < 5.2) & (corner_slope > 0.52)
            p3[tile_tools.prune_sparse_mask(step_mask, min_size=5)] = IDX[step_n]
        elif b["temp"] in ("N", "L", "W"):
            top_shelf = interior & (ny < -0.22) & (plane_fbm > 0.28)
            p3[tile_tools.prune_sparse_mask(top_shelf, min_size=6)] = IDX[lit_n]

        # Crisp broken 1px top-left brow glints along protruding upper-left edges
        if b["protrude"] > 0.08 or b["temp"] in ("L", "W"):
            brow = m & (inward <= 1.05) & (ny < -0.38) & (nx < 0.30) & (geom["rough"] > -0.10)
            p3[tile_tools.prune_sparse_mask(brow, min_size=2)] = IDX[hi_n]

    # Edge-anchored stone fractures strictly starting from mortar borders
    crack_seeds = [
        (blocks[1],  -0.35,  1.0,  0.85, -0.45, 5),
        (blocks[9],   1.0,  -0.1, -0.90,  0.30, 5),
        (blocks[14], -1.0,   0.2,  0.90,  0.25, 4),
        (blocks[20],  0.25, -1.0, -0.25,  0.95, 5),
        (blocks[26],  0.15,  1.0,  0.25, -0.95, 5),
        (blocks[35], -0.45, -1.0,  0.35,  0.90, 6),
    ]
    for b, sx_dir, sy_dir, step_x, step_y, c_len in crack_seeds:
        bid = b["id"]
        cur_x = b["cx"] + sx_dir * (b["w"] * 0.5 - 1.0)
        cur_y = b["cy"] + sy_dir * (b["h"] * 0.5 - 1.0)
        for s in range(c_len):
            jitter = 0.30 * math.sin(s * 1.9 + bid)
            px = int(round(cur_x + step_x * s + jitter)) % N
            py = int(round(cur_y + step_y * s)) % N
            if is_stone[py, px] and owner[py, px] == bid and not moss_mask[py, px]:
                p3[py, px] = IDX["mortar_mid"] if s < 2 else IDX["stone_sh2"]

    # 2 subtle carved medieval mason marks (quatrefoil ring & chamfered diamond seal)
    mark_coords: list[tuple[int, int]] = []
    mark_shapes = {
        7: [  # Chamfered diamond quatrefoil mark
            (-2, -1), (-2, 0), (-1, -2), (0, -2),
            (1, -2), (2, -1), (2, 0), (1, 1), (0, 2), (-1, 1),
        ],
        29: [ # Worn ringed saltire / rosette mason mark
            (-2, -2), (-1, -1), (1, -1), (2, -2),
            (0, 0), (-1, 1), (1, 1), (-2, 2), (2, 2),
        ],
    }
    for mark_bid, groove_pts in mark_shapes.items():
        b = blocks[mark_bid]
        mx = int(round(b["cx"])) % N
        my = int(round(b["cy"])) % N
        _, lit_n, _, sh_n, _ = ROLE_MAP[b["temp"]]
        groove_set = set(groove_pts)
        for dx, dy in groove_pts:
            rx, ry = (mx + dx + 1) % N, (my + dy + 1) % N
            if (dx + 1, dy + 1) not in groove_set and is_stone[ry, rx] and owner[ry, rx] == mark_bid and inward[ry, rx] > 2.2:
                p3[ry, rx] = IDX[lit_n]
                mark_coords.append((rx, ry))
        for dx, dy in groove_pts:
            px, py = (mx + dx) % N, (my + dy) % N
            if is_stone[py, px] and owner[py, px] == mark_bid and inward[py, px] > 2.2:
                p3[py, px] = IDX["stone_mid2"] if b["temp"] == "L" else IDX[sh_n]
                mark_coords.append((px, py))

    # 3 restrained tapering vertical iron/rust drips beneath top mortar edges
    rust_specs = [
        (blocks[13], -0.22, 5),
        (blocks[22],  0.15, 4),
        (blocks[32], -0.10, 5),
    ]
    for b, rx_off, drop_len in rust_specs:
        bid = b["id"]
        sx = int(round(b["cx"] + rx_off * b["w"])) % N
        start_y = int(round(b["cy"] - b["h"] * 0.5 + 1.0)) % N
        for step in range(drop_len):
            py = (start_y + step) % N
            px = (sx + (1 if step >= 3 else 0)) % N
            if is_stone[py, px] and owner[py, px] == bid and not moss_mask[py, px]:
                p3[py, px] = IDX["rust_dark"] if step < 2 else IDX["rust_mid"]

    # Velvety cel-clustered moss pockets overhanging stone & crevices
    moss_shadow = (np.roll(moss_mask, 1, axis=0) | np.roll(moss_mask, 1, axis=1)) & (~moss_mask)
    p3[moss_shadow] = IDX["moss_deep"]

    mgx = (np.roll(moss_score, -1, axis=1) - np.roll(moss_score, 1, axis=1)) * 0.5
    mgy = (np.roll(moss_score, -1, axis=0) - np.roll(moss_score, 1, axis=0)) * 0.5
    moss_sun = moss_score + (mgx + mgy) * 0.55

    p3[moss_mask] = IDX["moss_dark"]
    p3[moss_mask & (moss_sun > 0.45)] = IDX["moss_mid"]
    p3[moss_mask & (moss_sun > 0.72)] = IDX["moss_lit"]

    Image.fromarray(PAL_RGB[p3]).save(STEPS_DIR / "03_shading.png")

    # ------------------------------------------------------------------
    # PASS 4: 04_cleanup.png (Clean stray 1-2px speckles while keeping carved details crisp)
    # ------------------------------------------------------------------
    protected = {
        IDX["stone_hi"],
        IDX["moss_lit"],
        IDX["moss_deep"],
        IDX["mortar_deep"],
        IDX["rust_dark"],
        IDX["rust_mid"],
    }
    p4 = tile_tools.absorb_small_components(p3, max_size=2, protected=protected)
    # Restore intentionally carved mason cross pixels cleanly
    for px, py in mark_coords:
        p4[py, px] = p3[py, px]

    Image.fromarray(PAL_RGB[p4]).save(STEPS_DIR / "04_cleanup.png")
    print(f"[draw] Wrote 4 native {N}x{N} passes to {STEPS_DIR}")


if __name__ == "__main__":
    render_passes()
