"""Hand-authored native pixels for the Germy Games logo (256 x 192)."""
from pathlib import Path
import numpy as np
from PIL import Image


WIDTH, HEIGHT = 256, 192
SIZE = (WIDTH, HEIGHT)

# Curated 29-color palette (strictly palette-locked; no alpha blending or blur).
COLORS = {
    # Backdrop & stepped halo / sticker contour
    "bg_deep": "#210351",
    "halo_edge": "#3d1380",
    "halo_outer": "#5e29b5",
    "halo_mid": "#7738d9",
    "halo_bright": "#8c47f0",
    # Germ jelly body ramp (hue-shifted deep violet -> warm lavender)
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
    # Typography accents
    "text_glow": "#b482ff",
    "text_shade": "#e3d4ff",
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
        xs = 128.0 + 52.0 * t
        ys = 84.0 + 12.0 * (t * t)
        r = 27.5 - 3.5 * (t * t)
        dist = np.hypot(X - xs, Y - ys)
        sdf = dist - r
        best_sdf = np.minimum(best_sdf, sdf)

    # Smooth analytic parabola across full bean width (zero kinks at endcaps)
    tx = (X - 128.0) / 60.0
    spine_y = 85.0 + 10.5 * (tx * tx)
    spine_r = 26.0 - 2.0 * np.minimum(tx * tx, 1.4)
    norm_y = (Y - spine_y) / spine_r
    norm_x = (X - 128.0) / 76.0
    return best_sdf, norm_x, norm_y


def segment_sdf(X: np.ndarray, Y: np.ndarray, p0: tuple[float, float], p1: tuple[float, float]):
    """Return distance to segment and signed perpendicular offset (for directional lighting)."""
    x0, y0 = p0
    x1, y1 = p1
    vx, vy = x1 - x0, y1 - y0
    len_sq = vx * vx + vy * vy
    wx = X - x0
    wy = Y - y0
    proj = np.clip((wx * vx + wy * vy) / len_sq, 0.0, 1.0)
    cx = x0 + proj * vx
    cy = y0 + proj * vy
    dx = X - cx
    dy = Y - cy
    dist = np.hypot(dx, dy)
    # Light from top-left (-0.707, -0.707)
    light_dot = (-0.707 * dx - 0.707 * dy) / np.maximum(dist, 1e-4)
    return dist, proj, light_dot


def build_cilia(X: np.ndarray, Y: np.ndarray):
    """Build all 10 grouped pairs (20 total) of rounded cilia."""
    # Each entry: (root_x, root_y, tip_x, tip_y, radius)
    # Root points sit cleanly inside the [-6, 0] membrane band.
    cilia_specs = [
        # 1. Bottom-left pair
        (60.0, 108.0, 34.0, 117.0, 2.7),
        (57.0, 101.0, 35.0, 105.0, 2.7),
        # 2. Upper-left pair
        (64.0, 86.0, 42.0, 76.0, 2.7),
        (69.0, 80.0, 48.0, 67.0, 2.7),
        # 3. Left-shoulder pair
        (76.0, 74.0, 61.0, 56.0, 2.7),
        (83.0, 70.0, 69.0, 52.0, 2.7),
        # 4. Top-left crown pair
        (93.0, 65.0, 86.0, 44.0, 2.7),
        (101.0, 62.0, 96.0, 41.0, 2.7),
        # 5. Top-center-left pair
        (113.0, 60.0, 109.0, 39.0, 2.7),
        (121.0, 60.0, 118.0, 38.0, 2.7),
        # 6. Top-center pair (left cilium intentionally slightly shorter)
        (132.0, 60.0, 132.0, 43.0, 2.7),
        (140.0, 60.0, 142.0, 39.0, 2.7),
        # 7. Top-center-right pair (right cilium slightly shorter)
        (151.0, 61.0, 157.0, 40.0, 2.7),
        (159.0, 63.0, 167.0, 47.0, 2.7),
        # 8. Right-shoulder pair
        (171.0, 69.0, 183.0, 52.0, 2.7),
        (178.0, 73.0, 192.0, 56.0, 2.7),
        # 9. Upper-right pair
        (186.0, 80.0, 207.0, 67.0, 2.7),
        (191.0, 86.0, 213.0, 75.0, 2.7),
        # 10. Bottom-right pair
        (198.0, 101.0, 221.0, 102.0, 2.7),
        (196.0, 108.0, 220.0, 116.0, 2.7),
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


def capsule_dist(u: np.ndarray, v: np.ndarray, p0: tuple[float, float], p1: tuple[float, float]) -> np.ndarray:
    x0, y0 = p0
    x1, y1 = p1
    vx, vy = x1 - x0, y1 - y0
    len_sq = max(vx * vx + vy * vy, 1e-6)
    t = np.clip(((u - x0) * vx + (v - y0) * vy) / len_sq, 0.0, 1.0)
    return np.hypot(u - (x0 + t * vx), v - (y0 + t * vy))


def glyph_sdf(ch: str, u: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Clean capsule/arc SDF in local glyph coords: u centered around 0, v in [0, 22]."""
    r = 1.42
    d = np.full(u.shape, 1e4, dtype=np.float32)

    def add_seg(p0, p1):
        nonlocal d
        d = np.minimum(d, capsule_dist(u, v, p0, p1) - r)

    def add_poly(pts):
        for a, b in zip(pts, pts[1:]):
            add_seg(a, b)

    if ch == "G":
        add_poly([
            (4.0, 4.5), (2.2, 2.0), (-0.8, 1.6), (-3.5, 3.2),
            (-4.5, 7.0), (-4.5, 15.0), (-3.5, 18.8), (-0.6, 20.4),
            (2.4, 19.6), (4.2, 16.5), (4.2, 11.8), (0.6, 11.8),
        ])
    elif ch == "E":
        add_seg((-3.8, 1.8), (-3.8, 20.2))
        add_seg((-3.8, 1.8), (3.8, 1.8))
        add_seg((-3.8, 10.6), (2.6, 10.6))
        add_seg((-3.8, 20.2), (4.0, 20.2))
    elif ch == "R":
        add_seg((-4.0, 1.8), (-4.0, 20.2))
        add_poly([
            (-4.0, 1.8), (1.4, 1.8), (3.8, 3.6), (4.1, 6.4),
            (3.6, 9.2), (1.2, 10.8), (-4.0, 10.8),
        ])
        add_seg((0.4, 10.8), (4.2, 20.2))
    elif ch == "M":
        add_seg((-5.0, 20.2), (-4.7, 2.0))
        add_seg((-4.4, 2.0), (0.0, 14.5))
        add_seg((0.0, 14.5), (4.4, 2.0))
        add_seg((4.7, 2.0), (5.0, 20.2))
    elif ch == "Y":
        add_seg((-4.4, 1.8), (0.0, 11.2))
        add_seg((4.4, 1.8), (0.0, 11.2))
        add_seg((0.0, 11.2), (0.0, 20.2))
    elif ch == "A":
        add_seg((-4.4, 20.2), (-0.5, 1.8))
        add_seg((-0.5, 1.8), (0.5, 1.8))
        add_seg((0.5, 1.8), (4.4, 20.2))
        add_seg((-2.9, 14.3), (2.9, 14.3))
    elif ch == "S":
        add_poly([
            (3.6, 4.4), (2.0, 2.0), (-0.8, 1.6), (-3.3, 3.0),
            (-3.8, 5.6), (-2.5, 8.2), (0.2, 10.2), (2.9, 12.2),
            (4.0, 15.2), (3.4, 18.4), (0.8, 20.4), (-2.2, 20.0),
            (-3.8, 17.6),
        ])
    return d


def build_text_mask(X: np.ndarray, Y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Place condensed quirky 'GERMY GAMES' along the rainbow arch hugging the belly."""
    # Letter specs centered symmetrically around x=128
    letters = [
        ("G", 60.5),
        ("E", 74.0),
        ("R", 87.5),
        ("M", 102.5),
        ("Y", 117.0),
        ("G", 137.5),
        ("A", 152.0),
        ("M", 167.0),
        ("E", 182.0),
        ("S", 196.0),
    ]

    mask = np.zeros(X.shape, dtype=bool)
    baseline_mask = np.zeros(X.shape, dtype=bool)
    for ch, cx in letters:
        dx = cx - 128.0
        # Smooth arch peaking near center y=121 and curving down at sides
        y_top = 121.0 + 0.00235 * (dx * dx)
        # Slope dy/dx = 0.0047 * dx -> gentle arch rotation angle
        theta = np.arctan(0.0038 * dx)
        cos_t = np.cos(theta)
        sin_t = np.sin(theta)

        # Rotate into glyph frame centered horizontally at cx, vertically anchored at y_top
        px = X - cx
        py = Y - y_top
        u = cos_t * px + sin_t * py
        v = -sin_t * px + cos_t * py

        d = glyph_sdf(ch, u, v)
        g_mask = d <= 0.0
        mask |= g_mask
        baseline_mask |= g_mask & (v >= 19.6)

    return mask, baseline_mask


def build_distance_field(mask: np.ndarray, max_radius: float = 17.0) -> np.ndarray:
    """Exact Euclidean distance in pixels from `mask` up to `max_radius`."""
    dist = np.full(mask.shape, max_radius + 1.0, dtype=np.float32)
    dist[mask] = 0.0
    h, w = mask.shape
    rmax = int(np.ceil(max_radius))
    # Pre-sort circular integer offsets within max_radius
    offsets = []
    for dy in range(-rmax, rmax + 1):
        for dx in range(-rmax, rmax + 1):
            r = np.hypot(dx, dy)
            if 0.0 < r <= max_radius:
                offsets.append((r, dy, dx))
    offsets.sort(key=lambda item: item[0])

    # Expand per offset where source mask is True
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
    # Eyes
    eye_cy = 94.5
    eye_l_d = np.hypot(X - 81.5, Y - eye_cy)
    eye_r_d = np.hypot(X - 174.5, Y - eye_cy)
    eye_r = 9.8
    eyes = (eye_l_d <= eye_r) | (eye_r_d <= eye_r)

    # Subtle eye cheek occlusion (bottom-right rim)
    eye_cheek_shadow = (
        ((np.hypot(X - 83.0, Y - (eye_cy + 1.5)) <= 11.4) | (np.hypot(X - 176.0, Y - (eye_cy + 1.5)) <= 11.4))
        & (~eyes)
    )

    # Eye specular glints (upper-left crescent) and lower-right sheen
    def eye_details(cx, cy):
        d = np.hypot(X - cx, Y - cy)
        inside = d <= eye_r
        # Smooth curved crescent along upper-left rim
        glint_outer = inside & (d >= 4.2) & (d <= 8.2) & (
            (X - cx) * 0.72 + (Y - cy) * 0.69 <= -4.4
        )
        glint_core = inside & (d >= 5.0) & (d <= 7.4) & (
            (X - cx) * 0.72 + (Y - cy) * 0.69 <= -5.5
        )
        sheen = inside & (d >= 7.2) & ((X - cx) * 0.6 + (Y - cy) * 0.8 > 4.6)
        return glint_outer, glint_core, sheen

    gl_soft_l, gl_hi_l, sh_l = eye_details(81.5, eye_cy)
    gl_soft_r, gl_hi_r, sh_r = eye_details(174.5, eye_cy)
    eye_glint_soft = gl_soft_l | gl_soft_r
    eye_glint_hi = gl_hi_l | gl_hi_r
    eye_sheen = sh_l | sh_r

    # Mouth geometry (centered at x=128)
    dx = X - 128.0
    in_mouth_x = np.abs(dx) <= 29.0
    t_m = np.clip(dx / 29.0, -1.0, 1.0)
    # Upper arch peaks at y=81.5, curves to 90.0 at corners
    y_upper = 81.5 + 8.5 * (t_m ** 2)
    # Lower lip dips to y=99.5 at center, curves up to 90.0 at corners
    y_lower = 99.5 - 9.5 * (np.abs(t_m) ** 2.4)

    mouth_cavity = in_mouth_x & (Y >= y_upper) & (Y <= y_lower)

    # Bold ink outline around mouth + tapered upturned whisker flicks at corners
    mouth_outline = dilate_mask(mouth_cavity, 2.2) & (~mouth_cavity)
    flick_l, fproj_l, _ = segment_sdf(X, Y, (99.5, 89.5), (92.0, 86.2))
    flick_r, fproj_r, _ = segment_sdf(X, Y, (156.5, 89.5), (164.0, 86.2))
    mouth_outline |= (flick_l <= (1.3 - 0.75 * fproj_l)) | (flick_r <= (1.3 - 0.75 * fproj_r))

    # 4 upper teeth (2 outer corner teeth tucked cleanly inside mouth + 2 central buck teeth)
    tooth_outer_l = (
        mouth_cavity
        & (X >= 103.0) & (X <= 115.0)
        & (Y <= 94.0 - 0.14 * np.maximum(0.0, X - 108.5) ** 2)
    )
    tooth_outer_r = (
        mouth_cavity
        & (X >= 141.0) & (X <= 153.0)
        & (Y <= 94.0 - 0.14 * np.maximum(0.0, 147.5 - X) ** 2)
    )
    # Central buck teeth with rounded bottoms and 2 px center gap (x=127..129)
    tooth_mid_l = (
        mouth_cavity
        & (X >= 117.0) & (X <= 126.5)
        & (Y <= 89.8 - 0.11 * (X - 121.8) ** 2)
    )
    tooth_mid_r = (
        mouth_cavity
        & (X >= 129.5) & (X <= 139.0)
        & (Y <= 89.8 - 0.11 * (X - 134.2) ** 2)
    )
    teeth = tooth_outer_l | tooth_outer_r | tooth_mid_l | tooth_mid_r

    # Subtle tooth shading along upper roots / edges
    teeth_shade = teeth & ((Y <= y_upper + 1.8) | (np.abs(dx) <= 1.8) & (Y >= 86.5))

    # Fiery orange-red tongue filling lower mouth cavity
    tongue_top = 92.2 + 0.008 * (dx * dx)
    tongue = mouth_cavity & (np.abs(dx) <= 17.5) & (Y >= tongue_top) & (~teeth)
    tongue_deep = tongue & ((Y >= y_lower - 1.6) | (np.abs(dx) >= 15.2))
    tongue_bright = tongue & (Y <= tongue_top + 2.2) & (np.abs(dx) <= 13.5)
    tongue_spec = tongue & (np.hypot(X - 120.5, Y - 93.8) <= 2.2)

    # Mouth interior depth (deep throat behind teeth vs mid maroon)
    mouth_deep = mouth_cavity & (~teeth) & (~tongue) & (Y <= 88.5)

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
            # Check all 8 neighbors
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
                # Replace with majority of 4-connected neighbors
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
    # Keep cilia out of the inner purple jelly body so they fuse seamlessly into the outer membrane
    cilia_outer = cilia_mask & (~body_inner)

    germ_outer = membrane_outer | cilia_outer
    text_mask, text_baseline = build_text_mask(X, Y)

    # Combined logo silhouette for the unified puffy sticker halo
    logo_fg = germ_outer | text_mask
    halo_dist = build_distance_field(logo_fg, max_radius=14.5)

    halo_bright = (halo_dist <= 2.4) & (~logo_fg)
    halo_mid = (halo_dist > 2.4) & (halo_dist <= 6.2)
    halo_outer = (halo_dist > 6.2) & (halo_dist <= 11.4)
    halo_edge = (halo_dist > 11.4) & (halo_dist <= 13.0)

    face = build_face(X, Y)

    # Text accents (crisp neon outline + subtle soft underglow on halo, uniform bottom rim tint)
    text_dist = build_distance_field(text_mask, max_radius=2.5)
    text_glow = (text_dist > 0.0) & (text_dist <= 1.45)
    text_shifted = np.zeros_like(text_mask)
    text_shifted[2:, :] = text_mask[:-2, :]
    text_shadow = text_shifted & (~text_mask) & (~text_glow) & (Y >= 134.0)
    text_shade = text_baseline & (~np.roll(text_mask, -1, axis=0))

    # Internal jelly body shading (smooth continuous lighting from top-left)
    light_score = -0.20 * norm_x - 0.90 * norm_y
    body_deep = body_inner & (light_score < -0.52)
    body_shadow = body_inner & (light_score >= -0.52) & (light_score < -0.18)
    body_lit = body_inner & (light_score >= 0.36) & (light_score < 0.72)
    body_gloss = body_inner & (light_score >= 0.72)

    # Membrane & cilia lighting (draw continuous membrane cleanly on top of cilia roots)
    membrane_bright = membrane_ring & (light_score >= 0.16)
    membrane_shade = membrane_ring & (light_score < -0.45)
    membrane_spec = membrane_ring & (light_score >= 0.78) & (bean_sdf >= -4.2) & (bean_sdf <= -1.2)

    cilia_ext = cilia_outer & (~membrane_ring)
    cilia_lit = cilia_ext & (cilia_light >= 0.15)
    cilia_shaded = cilia_ext & (cilia_light < -0.35)
    cilia_tip_spec = cilia_ext & (cilia_proj >= 0.80) & (cilia_light >= 0.12) & (cilia_sdf >= -1.6)

    # Translucent internal jelly bubbles/vacuoles from reference
    bubble_tl = body_inner & (np.hypot(X - 91.5, Y - 76.0) <= 3.4)
    bubble_tl_core = body_inner & (np.hypot(X - 91.0, Y - 75.5) <= 1.8)
    bubble_tr_dot = body_inner & (np.hypot(X - 142.0, Y - 75.5) <= 1.6)
    bubble_br = body_inner & (np.hypot(X - 157.5, Y - 104.5) <= 5.4)
    bubble_br_rim = body_inner & (np.hypot(X - 157.5, Y - 104.5) <= 5.4) & (
        np.hypot(X - 159.0, Y - 106.0) > 4.2
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
    paint(p1, halo_dist <= 13.0, "halo_outer")
    paint(p1, germ_outer | text_mask, "body_shadow")

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
    paint(p2, text_mask, "tooth_white")

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

    # Body 3D jelly shading
    paint(p3, body_inner, "body_base")
    paint(p3, body_shadow, "body_shadow")
    paint(p3, body_deep | face["eye_cheek_shadow"], "body_deep")
    paint(p3, body_lit, "body_lit")
    paint(p3, body_gloss, "body_gloss")

    # Translucent bubbles (subtle soft vacuole lower-right, bright sparkle upper-left)
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

    # Text glow, gentle shadow & crisp white fill
    paint(p3, text_shadow, "halo_mid")
    paint(p3, text_glow, "text_glow")
    paint(p3, text_mask, "tooth_white")

    # --- Pass 04: Cleanup & Specular Glints ---
    p4 = p3.copy()
    paint(p4, membrane_spec | cilia_tip_spec, "membrane_spec")
    paint(p4, bubble_tl_core | bubble_tr_dot, "membrane_spec")
    paint(p4, face["eye_glint_hi"], "eye_glint_hi")
    paint(p4, face["tongue_spec"], "tongue_spec")
    paint(p4, text_shade, "text_shade")

    # Protect meaningful small highlights/details from cleanup
    protected = (
        bubble_tl_core
        | bubble_tr_dot
        | face["eye_glint_hi"]
        | face["tongue_spec"]
        | face["teeth_shade"]
        | face["mouth_outline"]
        | text_mask
    )
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
