"""Hand-authored native pixels for Germy wearing studio monitor headphones (256 x 192)."""
from pathlib import Path
import numpy as np
from PIL import Image


WIDTH, HEIGHT = 256, 192
SIZE = (WIDTH, HEIGHT)

# Curated 39-color palette (strictly palette-locked; zero blur or anti-aliasing).
COLORS = {
    # Backdrop & stepped halo / sticker contour
    "bg_deep": "#210351",
    "halo_edge": "#3d1380",
    "halo_outer": "#5e29b5",
    "halo_mid": "#7738d9",
    "halo_bright": "#8c47f0",
    # Germ jelly body ramp
    "body_deep": "#5d24c2",
    "body_shadow": "#7435dc",
    "body_base": "#9251f6",
    "body_lit": "#a86dfa",
    "body_gloss": "#bc8aff",
    # Membrane, cilia & specular bubbles
    "cilia_shade": "#9f6cf5",
    "membrane_mid": "#ba8eff",
    "membrane_bright": "#d4b5ff",
    "membrane_spec": "#ede0ff",
    # Eyes & bold ink outline
    "ink_black": "#0d0517",
    "eye_core": "#05020a",
    "eye_sheen": "#2a1b42",
    "eye_glint_soft": "#8d7da8",
    "eye_glint_hi": "#dfd4f2",
    # Mouth, teeth & tongue
    "mouth_deep": "#24040a",
    "mouth_dark": "#470e18",
    "tooth_shade": "#cfc3e6",
    "tooth_white": "#ffffff",
    "tongue_deep": "#a82400",
    "tongue_base": "#e84601",
    "tongue_bright": "#ff671a",
    "tongue_spec": "#ffa05c",
    # Studio monitor headphones (matte charcoal / leatherette)
    "hp_ink": "#140e24",
    "hp_dark": "#221b38",
    "hp_base": "#342c4f",
    "hp_mid": "#4a416b",
    "hp_lit": "#655c8a",
    "hp_bounce": "#7d4ce0",
    # Brushed steel hardware
    "metal_dark": "#555b78",
    "metal_mid": "#8790b0",
    "metal_light": "#bcc6e0",
    "metal_spec": "#eef3ff",
    # Studio L / R indicators
    "studio_blue": "#29b6ff",
    "studio_red": "#ff3b5c",
}


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


PALETTE_RGB = {k: np.array(hex_to_rgb(v), dtype=np.uint8) for k, v in COLORS.items()}


def make_grid():
    xs = np.arange(WIDTH, dtype=np.float32)[None, :] + 0.5
    ys = np.arange(HEIGHT, dtype=np.float32)[:, None] + 0.5
    return np.broadcast_to(xs, (HEIGHT, WIDTH)), np.broadcast_to(ys, (HEIGHT, WIDTH))


def compute_bean_sdf(X: np.ndarray, Y: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return signed distance to outer membrane and C-infinity smooth interior shading fields."""
    ts = np.linspace(-1.0, 1.0, 201, dtype=np.float32)
    best_sdf = np.full(X.shape, 1e6, dtype=np.float32)

    for t in ts:
        xs = 128.0 + 50.0 * t
        ys = 108.0 + 12.0 * (t * t)
        r = 27.5 - 3.5 * (t * t)
        dist = np.hypot(X - xs, Y - ys)
        best_sdf = np.minimum(best_sdf, dist - r)

    tx = (X - 128.0) / 58.0
    spine_y = 109.0 + 10.5 * (tx * tx)
    spine_r = 26.0 - 2.0 * np.minimum(tx * tx, 1.4)
    norm_y = (Y - spine_y) / spine_r
    norm_x = (X - 128.0) / 74.0
    return best_sdf, norm_x, norm_y


def segment_sdf(X: np.ndarray, Y: np.ndarray, p0: tuple[float, float], p1: tuple[float, float]):
    """Return distance to segment, projection [0, 1], and top-left directional lighting score."""
    x0, y0 = p0
    x1, y1 = p1
    vx, vy = x1 - x0, y1 - y0
    len_sq = max(vx * vx + vy * vy, 1e-6)
    proj = np.clip(((X - x0) * vx + (Y - y0) * vy) / len_sq, 0.0, 1.0)
    cx = x0 + proj * vx
    cy = y0 + proj * vy
    dx = X - cx
    dy = Y - cy
    dist = np.hypot(dx, dy)
    light_dot = (-0.707 * dx - 0.707 * dy) / np.maximum(dist, 1e-4)
    return dist, proj, light_dot


def build_cilia(X: np.ndarray, Y: np.ndarray):
    """Build all 10 grouped pairs (20 total) of rounded cilia."""
    cilia_specs = [
        # 1. Bottom-left pair (peeking out behind left earcup)
        (58.0, 132.0, 26.0, 139.0, 2.7),
        (56.0, 125.0, 25.0, 127.0, 2.7),
        # 2. Upper-left pair (visible inside left yoke window)
        (65.0, 108.0, 46.0, 95.0, 2.7),
        (70.0, 102.0, 52.0, 86.0, 2.7),
        # 3. Left-shoulder pair
        (76.0, 97.0, 62.0, 79.0, 2.7),
        (83.0, 93.0, 70.0, 75.0, 2.7),
        # 4. Top-left crown pair
        (93.0, 88.0, 87.0, 67.0, 2.7),
        (101.0, 85.0, 97.0, 64.0, 2.7),
        # 5. Top-center-left pair
        (113.0, 83.0, 110.0, 63.0, 2.7),
        (121.0, 83.0, 119.0, 62.0, 2.7),
        # 6. Top-center pair (left cilium slightly shorter)
        (132.0, 83.0, 132.0, 67.0, 2.7),
        (140.0, 83.0, 142.0, 63.0, 2.7),
        # 7. Top-center-right pair (right cilium slightly shorter)
        (151.0, 84.0, 156.0, 64.0, 2.7),
        (159.0, 86.0, 166.0, 70.0, 2.7),
        # 8. Right-shoulder pair
        (171.0, 93.0, 183.0, 75.0, 2.7),
        (178.0, 97.0, 192.0, 79.0, 2.7),
        # 9. Upper-right pair (visible inside right yoke window)
        (186.0, 102.0, 204.0, 86.0, 2.7),
        (191.0, 108.0, 210.0, 95.0, 2.7),
        # 10. Bottom-right pair (peeking out behind right earcup)
        (200.0, 125.0, 231.0, 127.0, 2.7),
        (198.0, 132.0, 230.0, 139.0, 2.7),
    ]

    mask = np.zeros(X.shape, dtype=bool)
    best_sdf = np.full(X.shape, 1e6, dtype=np.float32)
    best_proj = np.zeros(X.shape, dtype=np.float32)
    best_light = np.zeros(X.shape, dtype=np.float32)

    for x0, y0, x1, y1, r in cilia_specs:
        dist, proj, light_dot = segment_sdf(X, Y, (x0, y0), (x1, y1))
        sdf = dist - r
        better = sdf < best_sdf
        best_sdf = np.where(better, sdf, best_sdf)
        best_proj = np.where(better, proj, best_proj)
        best_light = np.where(better, light_dot, best_light)
        mask |= sdf <= 0.0

    return mask, best_sdf, best_proj, best_light


def build_distance_field(mask: np.ndarray, max_radius: float = 15.0) -> np.ndarray:
    """Exact Euclidean distance in pixels from `mask` up to `max_radius`."""
    dist = np.full(mask.shape, max_radius + 1.0, dtype=np.float32)
    dist[mask] = 0.0
    h, w = mask.shape
    rmax = int(np.ceil(max_radius))
    offsets = []
    for dy in range(-rmax, rmax + 1):
        for dx in range(-rmax, rmax + 1):
            r = np.hypot(dx, dy)
            if 0.0 < r <= max_radius:
                offsets.append((r, dy, dx))
    offsets.sort(key=lambda item: item[0])

    for r, dy, dx in offsets:
        y_src_start = max(0, -dy)
        y_src_end = min(h, h - dy)
        x_src_start = max(0, -dx)
        x_src_end = min(w, w - dx)

        y_dst_start = max(0, dy)
        y_dst_end = min(h, h + dy)
        x_dst_start = max(0, dx)
        x_dst_end = min(w, w + dx)

        src_slice = mask[y_src_start:y_src_end, x_src_start:x_src_end]
        dst_view = dist[y_dst_start:y_dst_end, x_dst_start:x_dst_end]
        update = src_slice & (r < dst_view)
        if np.any(update):
            dst_view[update] = r

    return dist


def dilate_mask(mask: np.ndarray, radius: float) -> np.ndarray:
    return build_distance_field(mask, max_radius=radius + 0.5) <= radius


def build_face(X: np.ndarray, Y: np.ndarray):
    """Build eyes, mouth outline, cavity, 4 upper teeth, and tongue."""
    eye_cy = 118.5
    eye_l_d = np.hypot(X - 82.5, Y - eye_cy)
    eye_r_d = np.hypot(X - 173.5, Y - eye_cy)
    eye_r = 9.8
    eyes = (eye_l_d <= eye_r) | (eye_r_d <= eye_r)

    eye_cheek_shadow = (
        ((np.hypot(X - 84.0, Y - (eye_cy + 1.5)) <= 11.4) | (np.hypot(X - 175.0, Y - (eye_cy + 1.5)) <= 11.4))
        & (~eyes)
    )

    def eye_details(cx: float, cy: float):
        d = np.hypot(X - cx, Y - cy)
        inside = d <= eye_r
        glint_outer = inside & (d >= 4.2) & (d <= 8.2) & (
            (X - cx) * 0.72 + (Y - cy) * 0.69 <= -4.4
        )
        glint_core = inside & (d >= 5.0) & (d <= 7.4) & (
            (X - cx) * 0.72 + (Y - cy) * 0.69 <= -5.5
        )
        sheen = inside & (d >= 7.2) & ((X - cx) * 0.6 + (Y - cy) * 0.8 > 4.6)
        return glint_outer, glint_core, sheen

    gl_soft_l, gl_hi_l, sh_l = eye_details(82.5, eye_cy)
    gl_soft_r, gl_hi_r, sh_r = eye_details(173.5, eye_cy)
    eye_glint_soft = gl_soft_l | gl_soft_r
    eye_glint_hi = gl_hi_l | gl_hi_r
    eye_sheen = sh_l | sh_r

    dx = X - 128.0
    in_mouth_x = np.abs(dx) <= 29.0
    t_m = np.clip(dx / 29.0, -1.0, 1.0)
    y_upper = 105.5 + 8.5 * (t_m ** 2)
    y_lower = 123.5 - 9.5 * (np.abs(t_m) ** 2.4)

    mouth_cavity = in_mouth_x & (Y >= y_upper) & (Y <= y_lower)

    mouth_outline = dilate_mask(mouth_cavity, 2.2) & (~mouth_cavity)
    flick_l, fproj_l, _ = segment_sdf(X, Y, (99.5, 113.5), (92.0, 110.2))
    flick_r, fproj_r, _ = segment_sdf(X, Y, (156.5, 113.5), (164.0, 110.2))
    mouth_outline |= (flick_l <= (1.3 - 0.75 * fproj_l)) | (flick_r <= (1.3 - 0.75 * fproj_r))

    tooth_outer_l = (
        mouth_cavity
        & (X >= 103.0) & (X <= 115.0)
        & (Y <= 118.0 - 0.14 * np.maximum(0.0, X - 108.5) ** 2)
    )
    tooth_outer_r = (
        mouth_cavity
        & (X >= 141.0) & (X <= 153.0)
        & (Y <= 118.0 - 0.14 * np.maximum(0.0, 147.5 - X) ** 2)
    )
    tooth_mid_l = (
        mouth_cavity
        & (X >= 117.0) & (X <= 126.5)
        & (Y <= 113.8 - 0.11 * (X - 121.8) ** 2)
    )
    tooth_mid_r = (
        mouth_cavity
        & (X >= 129.5) & (X <= 139.0)
        & (Y <= 113.8 - 0.11 * (X - 134.2) ** 2)
    )
    teeth = tooth_outer_l | tooth_outer_r | tooth_mid_l | tooth_mid_r
    teeth_shade = teeth & ((Y <= y_upper + 1.8) | ((np.abs(dx) <= 1.8) & (Y >= 110.5)))

    tongue_top = 116.2 + 0.008 * (dx * dx)
    tongue = mouth_cavity & (np.abs(dx) <= 17.5) & (Y >= tongue_top) & (~teeth)
    tongue_deep = tongue & ((Y >= y_lower - 1.6) | (np.abs(dx) >= 15.2))
    tongue_bright = tongue & (Y <= tongue_top + 2.2) & (np.abs(dx) <= 13.5)
    tongue_spec = tongue & (np.hypot(X - 120.5, Y - 117.8) <= 2.2)

    mouth_deep = mouth_cavity & (~teeth) & (~tongue) & (Y <= 112.5)

    return {
        "eyes": eyes,
        "eye_cheek_shadow": eye_cheek_shadow,
        "eye_glint_soft": eye_glint_soft,
        "eye_glint_hi": eye_glint_hi,
        "eye_sheen": eye_sheen,
        "mouth_cavity": mouth_cavity,
        "mouth_outline": mouth_outline,
        "mouth_deep": mouth_deep,
        "teeth": teeth,
        "teeth_shade": teeth_shade,
        "tongue": tongue,
        "tongue_deep": tongue_deep,
        "tongue_bright": tongue_bright,
        "tongue_spec": tongue_spec,
    }


def poly_sdf(sx: np.ndarray, Y: np.ndarray, pts: list[tuple[float, float]]):
    """Distance to piecewise polyline in symmetric (sx, Y) coordinates."""
    best_d = np.full(sx.shape, 1e6, dtype=np.float32)
    best_nx = np.zeros(sx.shape, dtype=np.float32)
    best_ny = np.zeros(sx.shape, dtype=np.float32)
    best_t = np.zeros(sx.shape, dtype=np.float32)
    n_seg = len(pts) - 1
    for i, ((x0, y0), (x1, y1)) in enumerate(zip(pts, pts[1:])):
        vx, vy = x1 - x0, y1 - y0
        len_sq = max(vx * vx + vy * vy, 1e-6)
        proj = np.clip(((sx - x0) * vx + (Y - y0) * vy) / len_sq, 0.0, 1.0)
        cx = x0 + proj * vx
        cy = y0 + proj * vy
        dx = sx - cx
        dy = Y - cy
        d = np.hypot(dx, dy)
        better = d < best_d
        best_d = np.where(better, d, best_d)
        safe_d = np.maximum(d, 1e-4)
        best_nx = np.where(better, dx / safe_d, best_nx)
        best_ny = np.where(better, dy / safe_d, best_ny)
        best_t = np.where(better, (i + proj) / n_seg, best_t)
    return best_d, best_nx, best_ny, best_t


def build_headphones(X: np.ndarray, Y: np.ndarray):
    """Build symmetric studio monitor earpads, closed-back cups, steel yokes, and headband."""
    sx = np.abs(X - 128.0)
    is_left = X < 128.0

    # 1. Plush circumaural earpads clamping snugly onto Germy's cheeks
    pad_pts = [(75.5 - 0.08 * (y - 119.0), float(y)) for y in range(103, 136, 2)]
    pad_d, pad_nx, pad_ny, _ = poly_sdf(sx, Y, pad_pts)
    pad_sdf = pad_d - 7.3
    pad_fill = pad_sdf <= 0.0
    pad_ink = (pad_sdf > -1.4) & pad_fill
    # Inner face (sx < 75) gets violet bounce light from Germy; outer ridge gets mid cushion tone
    pad_crease = pad_fill & (~pad_ink) & (pad_d <= 2.3)
    pad_lit = pad_fill & (~pad_ink) & (pad_ny < -0.25) & (pad_d >= 2.2)
    pad_bounce = pad_fill & (~pad_ink) & (pad_nx < -0.45) & (pad_sdf >= -3.0)

    # Contact shadow cast onto Germy's cheek right inside the earpad
    pad_contact_shadow = (pad_sdf > 0.0) & (pad_sdf <= 3.2) & (pad_nx < -0.15)

    # 2. Stepped closed-back studio monitor driver housing (curved bezel + recessed backplate)
    cup_pts = [(84.5 - 0.06 * (y - 119.0), float(y)) for y in range(105, 134, 2)]
    cup_d, cup_nx, cup_ny, _ = poly_sdf(sx, Y, cup_pts)
    back_plane = sx - (93.0 - 0.04 * (Y - 119.0))
    cup_sdf = np.maximum(cup_d - 9.8, back_plane)
    cup_fill = (cup_sdf <= 0.0) & (~pad_fill)
    cup_ink = cup_fill & ((cup_sdf > -1.4) | (pad_sdf <= 1.3))

    # Recessed matte driver backplate following the curved monitor shell
    cup_backplate = cup_fill & (~cup_ink) & (cup_d <= 6.5) & (sx >= 86.4)
    # Brushed steel curved trim ring framing the recessed backplate
    cup_ring = (
        cup_fill
        & (~cup_ink)
        & (~cup_backplate)
        & (cup_d <= 8.5)
        & (sx >= 82.8)
        & (sx <= 88.2)
    )
    # Acoustic rib grooves on the recessed backplate
    cup_grooves = cup_backplate & (
        ((Y >= 111.5) & (Y <= 113.0))
        | ((Y >= 118.2) & (Y <= 119.8))
        | ((Y >= 125.0) & (Y <= 126.5))
    )
    cup_top_bevel = cup_fill & (~cup_ink) & (~cup_backplate) & (~cup_ring) & (cup_ny < -0.25)

    # 3. Left-cup studio cable strain-relief jack boot
    jack_d, _, _, jack_t = poly_sdf(X, Y, [(41.0, 138.0), (41.0, 145.5)])
    jack_sdf = jack_d - 2.6
    jack_fill = (jack_sdf <= 0.0) & (~cup_fill) & (~pad_fill)
    jack_ink = jack_fill & (jack_sdf > -1.1)
    jack_collar = jack_fill & (~jack_ink) & (jack_t <= 0.35)
    jack_spec = jack_collar & (X <= 41.2) & (Y <= 140.5)

    # 4. Brushed steel telescoping C-yoke & slider arm
    yoke_pts = [
        (92.2, 121.0),
        (92.5, 112.0),
        (91.0, 102.0),
        (88.2, 92.0),
        (85.2, 82.0),
        (82.0, 72.5),
    ]
    yoke_d, yoke_nx, yoke_ny, _ = poly_sdf(sx, Y, yoke_pts)
    yoke_sdf = yoke_d - 2.5
    yoke_fill = yoke_sdf <= 0.0
    yoke_ink = yoke_fill & (yoke_sdf > -1.05)

    pivot_d = np.hypot(sx - 91.5, Y - 119.0)
    pivot_fill = pivot_d <= 3.8
    pivot_ink = pivot_fill & (pivot_d > 2.6)
    pivot_screw = pivot_d <= 1.3

    slider_all = yoke_fill | pivot_fill
    slider_ink = (yoke_ink & (~pivot_fill)) | (pivot_ink & (~yoke_fill)) | (yoke_ink & pivot_ink)

    slider_notches = (
        yoke_fill
        & (~yoke_ink)
        & (
            ((Y >= 81.5) & (Y <= 82.6))
            | ((Y >= 86.5) & (Y <= 87.6))
            | ((Y >= 91.5) & (Y <= 92.6))
        )
    )

    signed_nx = np.where(is_left, -yoke_nx, yoke_nx)
    metal_light_score = -0.65 * signed_nx - 0.75 * yoke_ny
    yoke_lit = slider_all & (~slider_ink) & (metal_light_score >= 0.15)
    yoke_dark = slider_all & (~slider_ink) & (metal_light_score < -0.35)
    yoke_spec = (
        (yoke_fill & (~yoke_ink) & (~slider_notches) & is_left & (yoke_nx <= -0.15) & (Y >= 77.0) & (Y <= 80.5))
        | pivot_screw
    )

    # 5. Contoured padded studio headband arching cleanly over top cilia
    band_pts = []
    for k in range(81):
        s = 80.8 * (k / 80.0)
        yb = 47.5 + 25.5 * ((s / 80.8) ** 2.05)
        band_pts.append((s, yb))
    band_d, band_nx, band_ny, band_t = poly_sdf(sx, Y, band_pts)
    band_sdf = band_d - 6.3
    band_fill = band_sdf <= 0.0
    band_ink = band_fill & (band_sdf > -1.35)

    # Metal end-clamps aligned cleanly to the headband curve tangent
    clamp_fill = band_fill & (band_t >= 0.855)
    clamp_ink = clamp_fill & ((band_sdf > -1.35) | (band_t < 0.872))
    clamp_lit = clamp_fill & (~clamp_ink) & ((band_ny < -0.05) | (is_left & (band_t >= 0.89)))
    clamp_dark = clamp_fill & (~clamp_ink) & (band_ny > 0.35)
    clamp_spec = clamp_fill & (~clamp_ink) & (band_ny < -0.42) & (band_t >= 0.88) & (band_t <= 0.94)

    # Studio L (blue) / R (red) indicator bars on the clamp mount
    lr_bar = (
        (band_t >= 0.90) & (band_t <= 0.96)
        & (Y >= 70.0) & (Y <= 72.3)
        & clamp_fill & (~clamp_ink)
    )
    studio_left = lr_bar & is_left
    studio_right = lr_bar & (~is_left)

    # Headband cushion & top leatherette arch shading (smoothly tapered top highlight)
    band_body = band_fill & (~band_ink) & (~clamp_fill)
    band_top_lit = band_body & (band_ny < -0.20)
    taper = ((X - 114.0) / 56.0) ** 2
    band_top_spec = band_body & (band_ny < (-0.54 - 0.30 * taper))
    band_cushion = band_body & (band_ny > 0.10)
    band_stitches = (
        band_cushion
        & (band_ny < 0.45)
        & (
            (np.abs(sx - 18.0) <= 0.65)
            | (np.abs(sx - 38.0) <= 0.65)
            | (np.abs(sx - 58.0) <= 0.65)
        )
    )
    band_bounce = band_body & (band_ny >= 0.48) & (band_sdf >= -2.6)

    # Cup ring lighting
    ring_lit = cup_ring & ((cup_ny < -0.10) | (is_left & (Y <= 122.0)))
    ring_dark = cup_ring & (cup_ny > 0.35)
    ring_spec = cup_ring & (Y >= 106.0) & (Y <= 110.0) & is_left & (~ring_dark)

    all_hp = pad_fill | cup_fill | jack_fill | slider_all | band_fill

    return {
        "all": all_hp,
        "pad_fill": pad_fill,
        "pad_ink": pad_ink,
        "pad_crease": pad_crease,
        "pad_lit": pad_lit,
        "pad_bounce": pad_bounce,
        "pad_contact_shadow": pad_contact_shadow,
        "cup_fill": cup_fill,
        "cup_ink": cup_ink,
        "cup_ring": cup_ring,
        "ring_lit": ring_lit,
        "ring_dark": ring_dark,
        "ring_spec": ring_spec,
        "cup_backplate": cup_backplate,
        "cup_grooves": cup_grooves,
        "cup_top_bevel": cup_top_bevel,
        "jack_fill": jack_fill,
        "jack_ink": jack_ink,
        "jack_collar": jack_collar,
        "jack_spec": jack_spec,
        "slider_all": slider_all,
        "slider_ink": slider_ink,
        "slider_notches": slider_notches,
        "yoke_lit": yoke_lit,
        "yoke_dark": yoke_dark,
        "yoke_spec": yoke_spec,
        "band_fill": band_fill,
        "band_ink": band_ink,
        "band_body": band_body,
        "band_top_lit": band_top_lit,
        "band_top_spec": band_top_spec,
        "band_cushion": band_cushion,
        "band_stitches": band_stitches,
        "band_bounce": band_bounce,
        "clamp_fill": clamp_fill,
        "clamp_ink": clamp_ink,
        "clamp_lit": clamp_lit,
        "clamp_dark": clamp_dark,
        "clamp_spec": clamp_spec,
        "studio_left": studio_left,
        "studio_right": studio_right,
    }


def cleanup_isolated_pixels(canvas: np.ndarray, protected_mask: np.ndarray) -> np.ndarray:
    """Remove stray 1-pixel 8-connected islands on non-protected regions in Pass 4."""
    out = canvas.copy()
    rgb = canvas[:, :, :3]
    h, w, _ = rgb.shape
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if protected_mask[y, x]:
                continue
            center = rgb[y, x]
            same8 = False
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dy == 0 and dx == 0:
                        continue
                    if np.array_equal(rgb[y + dy, x + dx], center):
                        same8 = True
                        break
                if same8:
                    break
            if not same8:
                n4 = [tuple(int(v) for v in rgb[y + dy, x + dx]) for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1))]
                best = max(set(n4), key=n4.count)
                out[y, x, :3] = best
    return out


def render_passes():
    X, Y = make_grid()

    bean_sdf, norm_x, norm_y = compute_bean_sdf(X, Y)
    membrane_outer = bean_sdf <= 0.0
    body_inner = bean_sdf <= -6.0
    membrane_ring = membrane_outer & (~body_inner)

    cilia_mask, cilia_sdf, cilia_proj, cilia_light = build_cilia(X, Y)
    cilia_outer = cilia_mask & (~body_inner)

    germ_outer = membrane_outer | cilia_outer
    hp = build_headphones(X, Y)
    face = build_face(X, Y)

    # Combined logo silhouette (germ + cilia + headphones, no text)
    logo_fg = germ_outer | hp["all"]
    halo_dist = build_distance_field(logo_fg, max_radius=14.5)

    halo_bright = (halo_dist <= 2.5) & (~logo_fg)
    halo_mid = (halo_dist > 2.5) & (halo_dist <= 6.8)
    halo_outer = (halo_dist > 6.8) & (halo_dist <= 11.8)
    halo_edge = (halo_dist > 11.8) & (halo_dist <= 13.4)

    # Internal jelly body shading
    light_score = -0.20 * norm_x - 0.90 * norm_y
    body_deep = body_inner & (light_score < -0.52)
    body_shadow = body_inner & (light_score >= -0.52) & (light_score < -0.18)
    body_lit = body_inner & (light_score >= 0.36) & (light_score < 0.72)
    body_gloss = body_inner & (light_score >= 0.72)

    # Membrane & cilia lighting
    membrane_bright = membrane_ring & (light_score >= 0.16)
    membrane_shade = membrane_ring & (light_score < -0.45)
    membrane_spec = membrane_ring & (light_score >= 0.78) & (bean_sdf >= -4.2) & (bean_sdf <= -1.2)

    cilia_ext = cilia_outer & (~membrane_ring)
    cilia_lit = cilia_ext & (cilia_light >= 0.15)
    cilia_shaded = cilia_ext & (cilia_light < -0.35)
    cilia_tip_spec = cilia_ext & (cilia_proj >= 0.80) & (cilia_light >= 0.12) & (cilia_sdf >= -1.6)

    # Translucent internal jelly bubbles
    bubble_tl = body_inner & (np.hypot(X - 91.5, Y - 99.5) <= 3.4)
    bubble_tl_core = body_inner & (np.hypot(X - 91.0, Y - 99.0) <= 1.8)
    bubble_tr_dot = body_inner & (np.hypot(X - 142.0, Y - 99.5) <= 1.6)
    bubble_br = body_inner & (np.hypot(X - 157.5, Y - 128.5) <= 5.4)
    bubble_br_rim = body_inner & (np.hypot(X - 157.5, Y - 128.5) <= 5.4) & (
        np.hypot(X - 159.0, Y - 130.0) > 4.2
    )

    def blank_canvas():
        canvas = np.empty((HEIGHT, WIDTH, 4), dtype=np.uint8)
        canvas[:, :, :3] = PALETTE_RGB["bg_deep"]
        canvas[:, :, 3] = 255
        return canvas

    def paint(canvas, mask, color_name):
        canvas[mask, :3] = PALETTE_RGB[color_name]

    # --- Pass 01: Silhouette ---
    p1 = blank_canvas()
    paint(p1, halo_dist <= 13.4, "halo_outer")
    paint(p1, germ_outer, "body_shadow")
    paint(p1, hp["all"], "hp_base")

    # --- Pass 02: Block-In ---
    p2 = blank_canvas()
    paint(p2, halo_edge | halo_outer, "halo_outer")
    paint(p2, halo_mid | halo_bright, "halo_mid")
    paint(p2, cilia_outer | membrane_ring, "membrane_mid")
    paint(p2, body_inner, "body_base")
    paint(p2, face["mouth_outline"], "ink_black")
    paint(p2, face["mouth_cavity"], "mouth_dark")
    paint(p2, face["teeth"], "tooth_white")
    paint(p2, face["tongue"], "tongue_base")
    paint(p2, face["eyes"], "ink_black")

    # Headphones flat block-in (drawn over side cilia & outer cheeks)
    paint(p2, hp["jack_fill"], "hp_dark")
    paint(p2, hp["cup_fill"], "hp_base")
    paint(p2, hp["cup_ring"], "metal_mid")
    paint(p2, hp["pad_fill"], "hp_dark")
    paint(p2, hp["slider_all"], "metal_mid")
    paint(p2, hp["band_fill"], "hp_base")
    paint(p2, hp["clamp_fill"], "metal_mid")
    paint(p2, hp["studio_left"], "studio_blue")
    paint(p2, hp["studio_right"], "studio_red")

    # --- Pass 03: Shading ---
    p3 = blank_canvas()
    paint(p3, halo_edge, "halo_edge")
    paint(p3, halo_outer, "halo_outer")
    paint(p3, halo_mid, "halo_mid")
    paint(p3, halo_bright, "halo_bright")

    # Cilia & membrane shaded
    paint(p3, cilia_outer | membrane_ring, "membrane_mid")
    paint(p3, cilia_shaded | membrane_shade, "cilia_shade")
    paint(p3, cilia_lit | membrane_bright, "membrane_bright")

    # Body 3D jelly shading + earpad cheek contact shadow
    paint(p3, body_inner, "body_base")
    paint(p3, body_shadow, "body_shadow")
    paint(p3, body_deep | face["eye_cheek_shadow"] | (body_inner & hp["pad_contact_shadow"]), "body_deep")
    paint(p3, membrane_ring & hp["pad_contact_shadow"], "cilia_shade")
    paint(p3, body_lit, "body_lit")
    paint(p3, body_gloss, "body_gloss")

    # Translucent bubbles
    paint(p3, bubble_br, "body_base")
    paint(p3, bubble_br_rim, "body_lit")
    paint(p3, bubble_tl, "membrane_bright")

    # Eyes & mouth shaded
    paint(p3, face["mouth_outline"], "ink_black")
    paint(p3, face["mouth_cavity"], "mouth_dark")
    paint(p3, face["mouth_deep"], "mouth_deep")
    paint(p3, face["teeth"], "tooth_white")
    paint(p3, face["teeth_shade"], "tooth_shade")
    paint(p3, face["tongue"], "tongue_base")
    paint(p3, face["tongue_deep"], "tongue_deep")
    paint(p3, face["tongue_bright"], "tongue_bright")

    paint(p3, face["eyes"], "eye_core")
    paint(p3, face["eye_sheen"], "eye_sheen")
    paint(p3, face["eye_glint_soft"], "eye_glint_soft")

    # Studio monitor headphones (shaded layer order: jack -> cup -> pad -> steel yoke -> headband)
    paint(p3, hp["jack_fill"], "hp_dark")
    paint(p3, hp["jack_collar"], "metal_mid")
    paint(p3, hp["jack_ink"], "hp_ink")

    paint(p3, hp["cup_fill"], "hp_base")
    paint(p3, hp["cup_top_bevel"], "hp_mid")
    paint(p3, hp["cup_backplate"], "hp_dark")
    paint(p3, hp["cup_grooves"], "hp_base")
    paint(p3, hp["cup_ring"], "metal_mid")
    paint(p3, hp["ring_dark"], "metal_dark")
    paint(p3, hp["ring_lit"], "metal_light")
    paint(p3, hp["cup_ink"], "hp_ink")

    paint(p3, hp["pad_fill"], "hp_base")
    paint(p3, hp["pad_crease"], "hp_dark")
    paint(p3, hp["pad_lit"], "hp_mid")
    paint(p3, hp["pad_bounce"], "hp_bounce")
    paint(p3, hp["pad_ink"], "hp_ink")

    paint(p3, hp["slider_all"], "metal_mid")
    paint(p3, hp["yoke_dark"], "metal_dark")
    paint(p3, hp["yoke_lit"], "metal_light")
    paint(p3, hp["slider_notches"], "hp_dark")
    paint(p3, hp["slider_ink"], "hp_ink")

    paint(p3, hp["band_fill"], "hp_base")
    paint(p3, hp["band_top_lit"], "hp_mid")
    paint(p3, hp["band_cushion"], "hp_dark")
    paint(p3, hp["band_stitches"], "hp_base")
    paint(p3, hp["band_bounce"], "hp_bounce")
    paint(p3, hp["band_ink"], "hp_ink")

    paint(p3, hp["clamp_fill"], "metal_mid")
    paint(p3, hp["clamp_dark"], "metal_dark")
    paint(p3, hp["clamp_lit"], "metal_light")
    paint(p3, hp["clamp_ink"], "hp_ink")
    paint(p3, hp["studio_left"], "studio_blue")
    paint(p3, hp["studio_right"], "studio_red")

    # --- Pass 04: Cleanup & Specular Glints ---
    p4 = p3.copy()
    paint(p4, (membrane_spec | cilia_tip_spec) & (~hp["all"]), "membrane_spec")
    paint(p4, bubble_tl_core | bubble_tr_dot, "membrane_spec")
    paint(p4, face["eye_glint_hi"], "eye_glint_hi")
    paint(p4, face["tongue_spec"], "tongue_spec")
    paint(p4, hp["band_top_spec"], "hp_lit")
    paint(p4, hp["ring_spec"] | hp["yoke_spec"] | hp["clamp_spec"] | hp["jack_spec"], "metal_spec")

    protected = (
        bubble_tl_core
        | bubble_tr_dot
        | face["eye_glint_hi"]
        | face["tongue_spec"]
        | face["teeth_shade"]
        | face["mouth_outline"]
        | hp["studio_left"]
        | hp["studio_right"]
        | hp["yoke_spec"]
        | hp["clamp_spec"]
        | hp["ring_spec"]
        | hp["jack_spec"]
        | hp["slider_ink"]
        | hp["band_ink"]
        | hp["cup_ink"]
        | hp["pad_ink"]
        | hp["jack_ink"]
    )
    p4 = cleanup_isolated_pixels(p4, protected)
    p4 = cleanup_isolated_pixels(p4, protected)

    return {
        "01_silhouette.png": Image.fromarray(p1, mode="RGBA"),
        "02_blockin.png": Image.fromarray(p2, mode="RGBA"),
        "03_shading.png": Image.fromarray(p3, mode="RGBA"),
        "04_cleanup.png": Image.fromarray(p4, mode="RGBA"),
    }


def main():
    steps_dir = Path(__file__).resolve().parents[1] / "build" / "steps"
    steps_dir.mkdir(parents=True, exist_ok=True)
    passes = render_passes()
    for name, img in passes.items():
        out_path = steps_dir / name
        img.save(out_path)
        print(f"Saved {out_path} ({img.width}x{img.height})")

    final = np.array(passes["04_cleanup.png"])[:, :, :3].reshape(-1, 3)
    unique_colors = np.unique(final, axis=0)
    print(f"Unique colors in 04_cleanup.png: {len(unique_colors)} (palette defines {len(COLORS)})")


if __name__ == "__main__":
    main()
