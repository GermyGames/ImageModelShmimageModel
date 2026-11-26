#!/usr/bin/env python3
"""
shmimage.py - Image Model Shmimage Model pixel-art pipeline CLI.

Commands:
  init     Initialize a case directory with CONTRACT.md and acceptance.json
  prep     Segment subject, crop/pad, and optimize sub-pixel grid phase alignment
  extract  Infer line art and protected detail masks for a prepared case
  style    Sample palette and outline settings from a style reference
  fit      Run 4 recorded passes: silhouette -> block-in -> shading -> cleanup
  check    Measure Silhouette IoU, Edge F1, Delta E, Orphans, and Jaggies
  tile-preview  Show the repeat or bring the tile joins to the center
  tile-stats    Report luminance balance, palette coverage, and seam continuity
  record-revision  Save a labeled native draft for the build timelapse
  deliver  Export 1x/Nx PNGs, palette sheet, build timelapse GIF, and .aseprite
"""

import argparse
import json
import shutil
import subprocess
import sys
from collections import Counter, deque
from pathlib import Path
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from guides import extract_guides, guide_overlay, load_mask, mask_image, widen_lines, write_review
from image_grid import pad_for_phase, resample_phase
from revision_history import (
    Revision, read_revision, record_revision, revision_paths, timelapse_with_revisions,
)
from style_reference import analyze_style, load_style
from tile_tools import tonal_report

PALETTES = {
    "gameboy": [
        (15, 56, 15),
        (48, 98, 48),
        (139, 172, 15),
        (155, 188, 15),
    ],
    "pico8": [
        (0, 0, 0), (29, 43, 83), (126, 37, 83), (0, 135, 81),
        (171, 82, 54), (95, 87, 79), (194, 195, 199), (255, 241, 232),
        (255, 0, 77), (255, 163, 0), (255, 236, 39), (0, 228, 54),
        (41, 173, 255), (131, 118, 156), (255, 119, 168), (255, 204, 170),
    ],
    "sweetie16": [
        (26, 28, 44), (93, 39, 93), (177, 62, 83), (239, 125, 87),
        (255, 205, 117), (167, 240, 112), (56, 183, 100), (37, 113, 121),
        (41, 54, 111), (59, 93, 201), (65, 166, 246), (115, 239, 247),
        (244, 244, 244), (148, 176, 194), (86, 108, 134), (51, 60, 87),
    ],
    "nes": [
        (124, 124, 124), (0, 0, 252), (0, 0, 188), (68, 40, 188),
        (148, 0, 132), (168, 0, 32), (168, 16, 0), (136, 20, 0),
        (80, 48, 0), (0, 120, 0), (0, 104, 0), (0, 88, 0),
        (0, 64, 88), (0, 0, 0), (188, 188, 188), (0, 120, 248),
        (0, 88, 248), (104, 68, 252), (216, 0, 204), (228, 0, 88),
        (248, 56, 0), (228, 92, 16), (172, 124, 0), (0, 184, 0),
        (0, 168, 0), (0, 168, 68), (0, 136, 136), (248, 248, 248),
        (60, 188, 252), (104, 136, 252), (152, 120, 248), (248, 120, 248),
        (248, 88, 152), (248, 120, 88), (252, 160, 68), (248, 184, 0),
        (184, 248, 24), (88, 216, 84), (88, 248, 152), (0, 232, 216),
        (120, 120, 120), (252, 252, 252), (164, 228, 252), (184, 184, 248),
        (216, 184, 248), (248, 184, 248), (248, 164, 192), (240, 208, 176),
        (252, 224, 168), (248, 216, 120), (216, 248, 120), (184, 248, 184),
        (184, 248, 216), (0, 252, 252), (248, 216, 248),
    ],
    "endesga32": [
        (190, 74, 47), (215, 118, 67), (234, 212, 170), (228, 166, 114),
        (184, 111, 80), (115, 62, 57), (62, 39, 49), (162, 38, 51),
        (228, 59, 68), (247, 118, 34), (254, 174, 52), (254, 231, 97),
        (99, 199, 77), (62, 137, 72), (38, 92, 66), (25, 60, 62),
        (18, 78, 137), (0, 153, 219), (44, 232, 245), (255, 255, 255),
        (192, 203, 220), (139, 155, 180), (90, 105, 136), (58, 68, 102),
        (38, 43, 68), (24, 20, 37), (255, 0, 68), (104, 56, 108),
        (181, 80, 136), (246, 117, 122), (232, 183, 150), (194, 133, 105),
    ],
}

BAYER2 = (np.array([[0, 2], [3, 1]], dtype=np.float32) + 0.5) / 4.0 - 0.5
BAYER4 = (
    np.array(
        [
            [0, 8, 2, 10],
            [12, 4, 14, 6],
            [3, 11, 1, 9],
            [15, 7, 13, 5],
        ],
        dtype=np.float32,
    )
    + 0.5
) / 16.0 - 0.5


def srgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    arr = np.asarray(rgb, dtype=np.float32) / 255.0
    mask = arr > 0.04045
    linear = np.where(mask, np.power((arr + 0.055) / 1.055, 2.4), arr / 12.92)

    x = linear[..., 0] * 0.4124564 + linear[..., 1] * 0.3575761 + linear[..., 2] * 0.1804375
    y = linear[..., 0] * 0.2126729 + linear[..., 1] * 0.7151522 + linear[..., 2] * 0.0721750
    z = linear[..., 0] * 0.0193339 + linear[..., 1] * 0.1191920 + linear[..., 2] * 0.9503041

    xyz = np.stack([x / 0.95047, y / 1.00000, z / 1.08883], axis=-1)
    eps = 0.008856
    kappa = 903.3
    f = np.where(xyz > eps, np.cbrt(xyz), (kappa * xyz + 16.0) / 116.0)

    L = 116.0 * f[..., 1] - 16.0
    a = 500.0 * (f[..., 0] - f[..., 1])
    b = 200.0 * (f[..., 1] - f[..., 2])
    return np.stack([L, a, b], axis=-1)


def lab_to_srgb(lab: np.ndarray) -> np.ndarray:
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    fy = (L + 16.0) / 116.0
    fx = a / 500.0 + fy
    fz = fy - b / 200.0

    eps = 0.008856
    kappa = 903.3
    xr = np.where(fx ** 3 > eps, fx ** 3, (116.0 * fx - 16.0) / kappa)
    yr = np.where(L > kappa * eps, ((L + 16.0) / 116.0) ** 3, L / kappa)
    zr = np.where(fz ** 3 > eps, fz ** 3, (116.0 * fz - 16.0) / kappa)

    X = xr * 0.95047
    Y = yr * 1.00000
    Z = zr * 1.08883

    r_lin = X * 3.2404542 - Y * 1.5371385 - Z * 0.4985314
    g_lin = -X * 0.9692660 + Y * 1.8760108 + Z * 0.0415560
    b_lin = X * 0.0556434 - Y * 0.2040259 + Z * 1.0572252

    lin = np.clip(np.stack([r_lin, g_lin, b_lin], axis=-1), 0.0, 1.0)
    srgb = np.where(lin > 0.0031308, 1.055 * np.power(lin, 1.0 / 2.4) - 0.055, 12.92 * lin)
    return np.clip(np.round(srgb * 255.0), 0, 255).astype(np.uint8)


def kmeans_lab(pixels_lab: np.ndarray, k: int, max_iter: int = 25, seed: int = 42) -> np.ndarray:
    n = len(pixels_lab)
    if n == 0:
        return np.zeros((k, 3), dtype=np.float32)
    unique = np.unique(np.round(pixels_lab, 2), axis=0)
    if len(unique) <= k:
        return unique.astype(np.float32)

    rng = np.random.default_rng(seed)
    centers = np.empty((k, 3), dtype=np.float32)
    centers[0] = pixels_lab[rng.integers(0, n)]

    dist_sq = np.sum((pixels_lab - centers[0]) ** 2, axis=1)
    for i in range(1, k):
        total = float(dist_sq.sum())
        if total <= 1e-8:
            centers[i] = pixels_lab[rng.integers(0, n)]
        else:
            probs = dist_sq / total
            centers[i] = pixels_lab[rng.choice(n, p=probs)]
        new_dist = np.sum((pixels_lab - centers[i]) ** 2, axis=1)
        dist_sq = np.minimum(dist_sq, new_dist)

    for _ in range(max_iter):
        dists = np.sum((pixels_lab[:, None, :] - centers[None, :, :]) ** 2, axis=2)
        labels = np.argmin(dists, axis=1)
        new_centers = np.copy(centers)
        for j in range(k):
            mask = labels == j
            if np.any(mask):
                new_centers[j] = pixels_lab[mask].mean(axis=0)
        if np.allclose(centers, new_centers, atol=0.05):
            centers = new_centers
            break
        centers = new_centers

    return centers


def skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_meta(case_dir: Path) -> dict:
    meta_file = case_dir / "build" / "case.json"
    if not meta_file.exists():
        raise FileNotFoundError(f"Case not initialized: missing {meta_file}")
    return json.loads(meta_file.read_text(encoding="utf-8"))


def save_meta(case_dir: Path, meta: dict) -> None:
    meta_file = case_dir / "build" / "case.json"
    meta_file.parent.mkdir(parents=True, exist_ok=True)
    meta_file.write_text(json.dumps(meta, indent=2), encoding="utf-8")


def cmd_init(args: argparse.Namespace) -> None:
    case_dir = Path(args.case_dir).resolve()
    if not args.input and not args.tile:
        sys.exit("Error: provide --input or use --tile to start a tile without a reference.")
    src = Path(args.input).resolve() if args.input else None
    if src is not None and not src.is_file():
        sys.exit(f"Error: input image not found: {src}")

    for sub in ["source", "build/prep", "build/steps", "build/check", "deliver"]:
        (case_dir / sub).mkdir(parents=True, exist_ok=True)

    ref_copy = None
    if src is not None:
        ref_copy = case_dir / "source" / f"reference{src.suffix.lower()}"
        if ref_copy != src:
            shutil.copy2(src, ref_copy)

    root = skill_root()
    contract_tpl = (root / "templates" / "CONTRACT.md").read_text(encoding="utf-8")
    contract_txt = (
        contract_tpl.replace("{{CASE_NAME}}", case_dir.name)
        .replace("{{INPUT_PATH}}", str(ref_copy) if ref_copy else "None (original tile)")
        .replace("{{SIZE}}", str(args.size))
        .replace("{{PALETTE}}", args.palette)
        .replace("{{COLORS}}", str(args.colors))
    )
    if args.tile:
        contract_txt += (
            "\n## Seamless tile\n\n"
            "Record the native width and height, wrap axes, material references, "
            "and style choices. Inspect the offset joins and repeated field "
            "as described in the skill’s seamless tile guide.\n"
        )
    (case_dir / "CONTRACT.md").write_text(contract_txt, encoding="utf-8")

    acc_tpl = root / "templates" / "acceptance.json"
    shutil.copy2(acc_tpl, case_dir / "acceptance.json")

    meta = {
        "case_name": case_dir.name,
        "reference_path": str(ref_copy) if ref_copy else None,
        "size": args.size,
        "palette": args.palette,
        "colors": args.colors,
    }
    save_meta(case_dir, meta)
    print(f"[init] Initialized case at {case_dir}")


def segment_subject(img: Image.Image, bg_mode: str, tolerance: float) -> Image.Image:
    rgba = img.convert("RGBA")
    arr = np.array(rgba, dtype=np.uint8)
    alpha = arr[..., 3]

    if bg_mode == "none":
        arr[..., 3] = 255
        return Image.fromarray(arr, mode="RGBA")

    if bg_mode == "auto" and int(alpha.min()) < 250:
        return rgba

    h, w = arr.shape[:2]
    lab = srgb_to_lab(arr[..., :3])

    border_samples = np.concatenate(
        [lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]], axis=0
    )
    bg_lab = np.median(border_samples, axis=0)

    visited = np.zeros((h, w), dtype=bool)
    bg_mask = np.zeros((h, w), dtype=bool)
    q: deque[tuple[int, int]] = deque()

    for cy, cx in [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]:
        if np.linalg.norm(lab[cy, cx] - bg_lab) <= tolerance * 1.25:
            visited[cy, cx] = True
            bg_mask[cy, cx] = True
            q.append((cy, cx))

    while q:
        y, x = q.popleft()
        cur = lab[y, x]
        for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx]:
                visited[ny, nx] = True
                pix = lab[ny, nx]
                if (
                    np.linalg.norm(pix - bg_lab) <= tolerance
                    and np.linalg.norm(pix - cur) <= tolerance * 0.6
                ):
                    bg_mask[ny, nx] = True
                    q.append((ny, nx))

    fg_alpha = np.where(bg_mask, 0, 255).astype(np.uint8)
    alpha_img = Image.fromarray(fg_alpha, mode="L").filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3))
    arr[..., 3] = np.array(alpha_img, dtype=np.uint8)
    return Image.fromarray(arr, mode="RGBA")


def compute_sobel_edges(gray: np.ndarray) -> np.ndarray:
    padded = np.pad(gray.astype(np.float32), 1, mode="edge")
    gx = (
        -padded[:-2, :-2] + padded[:-2, 2:]
        - 2.0 * padded[1:-1, :-2] + 2.0 * padded[1:-1, 2:]
        - padded[2:, :-2] + padded[2:, 2:]
    )
    gy = (
        -padded[:-2, :-2] - 2.0 * padded[:-2, 1:-1] - padded[:-2, 2:]
        + padded[2:, :-2] + 2.0 * padded[2:, 1:-1] + padded[2:, 2:]
    )
    return np.hypot(gx, gy)


def cmd_prep(args: argparse.Namespace) -> None:
    case_dir = Path(args.case_dir).resolve()
    meta = load_meta(case_dir)
    if not meta.get("reference_path"):
        sys.exit("Error: prep requires a source image. Draw original tile passes on the native grid.")
    ref_img = Image.open(meta["reference_path"])

    subj = segment_subject(ref_img, bg_mode=args.bg_mode, tolerance=args.bg_tolerance)
    alpha_np = np.array(subj.getchannel("A"))
    ys, xs = np.where(alpha_np >= 128)
    if len(xs) > 0 and len(ys) > 0:
        pad = max(2, int(round(max(subj.size) * 0.02)))
        x0 = max(0, int(xs.min()) - pad)
        y0 = max(0, int(ys.min()) - pad)
        x1 = min(subj.width, int(xs.max()) + 1 + pad)
        y1 = min(subj.height, int(ys.max()) + 1 + pad)
        subj = subj.crop((x0, y0, x1, y1))

    max_size = int(meta["size"])
    if subj.width >= subj.height:
        target_w = max_size
        target_h = max(1, round(subj.height * (max_size / subj.width)))
    else:
        target_h = max_size
        target_w = max(1, round(subj.width * (max_size / subj.height)))

    target_size = (target_w, target_h)
    phases = (0.0, 0.25, 0.5, 0.75)
    phase_source = pad_for_phase(subj, target_size, (phases[-1], phases[-1]))
    best_score = -1.0
    best_phase = (0.0, 0.0)
    best_aligned = None

    for dy in phases:
        for dx in phases:
            candidate = resample_phase(phase_source, subj.size, target_size, (dx, dy))
            lum = np.array(candidate.convert("L"), dtype=np.float32)
            grad = compute_sobel_edges(lum)
            score = float(grad.mean())
            if score > best_score:
                best_score = score
                best_phase = (dx, dy)
                best_aligned = candidate

    assert best_aligned is not None

    ref_gray = np.array(best_aligned.convert("L"), dtype=np.float32)
    edge_mag = compute_sobel_edges(ref_gray)
    edge_norm = np.clip((edge_mag / (edge_mag.max() + 1e-6)) * 255.0, 0, 255).astype(np.uint8)

    prep_dir = case_dir / "build" / "prep"
    subj.save(prep_dir / "subject_rgba.png")
    best_aligned.save(prep_dir / "phase_aligned.png")
    Image.fromarray(edge_norm, mode="L").save(prep_dir / "edge_target.png")

    meta["target_w"] = target_w
    meta["target_h"] = target_h
    meta["best_phase"] = list(best_phase)
    meta["bg_mode"] = args.bg_mode
    save_meta(case_dir, meta)
    print(f"[prep] Target grid: {target_w}x{target_h}, optimal sub-pixel phase: {best_phase}")


def cmd_extract(args: argparse.Namespace) -> None:
    case_dir = Path(args.case_dir).resolve()
    meta = load_meta(case_dir)
    build = case_dir / "build"
    prep = build / "prep"
    if "best_phase" not in meta or not (prep / "phase_aligned.png").is_file() or not (prep / "subject_rgba.png").is_file():
        sys.exit("Error: run prep for this case before extracting guides.")
    if not 0 < args.line_threshold <= 1 or not 0 < args.detail_threshold <= 1:
        sys.exit("Error: guide thresholds must be greater than 0 and at most 1.")
    if not 2 <= args.region_colors <= 64:
        sys.exit("Error: region colors must be between 2 and 64.")

    with Image.open(prep / "subject_rgba.png") as source, Image.open(prep / "phase_aligned.png") as grid:
        subject = source.convert("RGBA")
        aligned = grid.convert("RGBA")
    phase = tuple(meta["best_phase"])
    lines, details = extract_guides(
        subject, aligned, phase, args.method,
        args.line_threshold, args.detail_threshold, args.region_colors,
    )
    blockin = None
    blockin_path = build / "steps" / "02_blockin.png"
    if blockin_path.is_file():
        with Image.open(blockin_path) as preview:
            if preview.size == aligned.size:
                blockin = preview.convert("RGBA")

    guides_dir = build / "guides"
    guides_dir.mkdir(parents=True, exist_ok=True)
    mask_image(lines).save(guides_dir / "lineart.png")
    mask_image(details).save(guides_dir / "detail_mask.png")
    overlay = guide_overlay(blockin if blockin is not None else aligned, lines, details)
    overlay.save(guides_dir / "overlay.png")
    write_review(guides_dir / "review.html", subject, aligned, blockin, lines, details, overlay)
    print(f"[extract] {args.method}: {lines.sum()} line pixels, {details.sum()} detail pixels on a {aligned.width}x{aligned.height} grid")
    print(f"[extract] Open {guides_dir / 'review.html'} to edit and download the masks.")


def cmd_style(args: argparse.Namespace) -> None:
    if not 2 <= args.colors <= 64:
        sys.exit("Error: style colors must be between 2 and 64.")
    destination = Path(args.output)
    if destination.resolve() == Path(args.input).resolve():
        sys.exit("Error: use a different path for the style JSON and the reference image.")
    try:
        with Image.open(args.input) as image:
            style = analyze_style(image, args.colors, args.pixel_scale)
    except (ValueError, OSError) as error:
        sys.exit(f"Error: {error}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(style, indent=2) + "\n", encoding="utf-8")
    print(f"[style] Saved {len(style['palette'])} colors and outline settings to {destination}")


def edge_preserving_majority(idx_map: np.ndarray, alpha_mask: np.ndarray, edge_map: np.ndarray) -> np.ndarray:
    h, w = idx_map.shape
    out = idx_map.copy()
    edge_thresh = np.percentile(edge_map, 75)
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if not alpha_mask[y, x] or edge_map[y, x] >= edge_thresh:
                continue
            patch = idx_map[y - 1 : y + 2, x - 1 : x + 2]
            amask = alpha_mask[y - 1 : y + 2, x - 1 : x + 2]
            vals = patch[amask]
            if len(vals) >= 5:
                most_common, count = Counter(vals.tolist()).most_common(1)[0]
                if count >= 5:
                    out[y, x] = most_common
    return out


def remove_orphans(
    idx_map: np.ndarray, alpha_mask: np.ndarray, protected: np.ndarray | None = None
) -> np.ndarray:
    h, w = idx_map.shape
    out = idx_map.copy()
    editable = alpha_mask if protected is None else alpha_mask & ~protected
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if not editable[y, x]:
                continue
            c = out[y, x]
            nb8 = []
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dy == 0 and dx == 0:
                        continue
                    if alpha_mask[y + dy, x + dx]:
                        nb8.append(int(out[y + dy, x + dx]))
            if nb8 and c not in nb8:
                cardinal = [
                    int(out[y + dy, x + dx])
                    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1))
                    if alpha_mask[y + dy, x + dx]
                ]
                pool = cardinal if cardinal else nb8
                out[y, x] = Counter(pool).most_common(1)[0][0]
    return out


def smooth_jaggies(
    idx_map: np.ndarray, alpha_mask: np.ndarray, protected: np.ndarray | None = None
) -> np.ndarray:
    h, w = idx_map.shape
    out = idx_map.copy()
    editable = alpha_mask if protected is None else alpha_mask & ~protected
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if not editable[y, x]:
                continue
            c = out[y, x]
            up = out[y - 1, x] if alpha_mask[y - 1, x] else -1
            dn = out[y + 1, x] if alpha_mask[y + 1, x] else -1
            lt = out[y, x - 1] if alpha_mask[y, x - 1] else -1
            rt = out[y, x + 1] if alpha_mask[y, x + 1] else -1
            if up != -1 and up == dn and up != c and lt != c and rt != c:
                out[y, x] = up
            elif lt != -1 and lt == rt and lt != c and up != c and dn != c:
                out[y, x] = lt
    return out


def apply_selective_outline(
    idx_map: np.ndarray, alpha_mask: np.ndarray, palette_lab: np.ndarray,
    protected: np.ndarray | None = None,
) -> np.ndarray:
    h, w = idx_map.shape
    out = idx_map.copy()
    darkest_overall = int(np.argmin(palette_lab[:, 0]))
    editable = alpha_mask if protected is None else alpha_mask & ~protected

    for y in range(h):
        for x in range(w):
            if not editable[y, x]:
                continue
            touches_bg = False
            interior_neighbors = []
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ny, nx = y + dy, x + dx
                if ny < 0 or ny >= h or nx < 0 or nx >= w or not alpha_mask[ny, nx]:
                    touches_bg = True
                else:
                    interior_neighbors.append(int(idx_map[ny, nx]))
            if touches_bg and interior_neighbors:
                dom_idx = Counter(interior_neighbors).most_common(1)[0][0]
                dom_lab = palette_lab[dom_idx]
                darker = np.where(palette_lab[:, 0] < dom_lab[0] - 12.0)[0]
                if len(darker) > 0:
                    chroma_dist = np.linalg.norm(
                        palette_lab[darker, 1:3] - dom_lab[1:3], axis=1
                    )
                    best = darker[int(np.argmin(chroma_dist))]
                    out[y, x] = int(best)
                else:
                    out[y, x] = darkest_overall
    return out


def render_indexed(idx_map: np.ndarray, alpha_mask: np.ndarray, palette_rgb: np.ndarray) -> Image.Image:
    h, w = idx_map.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    rgba[..., :3] = palette_rgb[idx_map]
    rgba[..., 3] = np.where(alpha_mask, 255, 0).astype(np.uint8)
    return Image.fromarray(rgba, mode="RGBA")


def cmd_fit(args: argparse.Namespace) -> None:
    case_dir = Path(args.case_dir).resolve()
    meta = load_meta(case_dir)
    prep_dir = case_dir / "build" / "prep"
    steps_dir = case_dir / "build" / "steps"
    steps_dir.mkdir(parents=True, exist_ok=True)

    aligned = Image.open(prep_dir / "phase_aligned.png").convert("RGBA")
    edge_target = np.array(Image.open(prep_dir / "edge_target.png"), dtype=np.float32)

    arr = np.array(aligned, dtype=np.uint8)
    h, w = arr.shape[:2]

    alpha_mask = arr[..., 3] >= 128
    protected = None
    ink_index = None
    ink_width = 1
    try:
        details = load_mask(args.detail_mask, aligned.size) & alpha_mask
        lines = load_mask(args.lineart, aligned.size)
        if args.style:
            palette_rgb, ink_index, ink_width = load_style(args.style)
    except (ValueError, OSError) as error:
        sys.exit(f"Error: {error}")
    if args.lineart or args.detail_mask:
        lines = widen_lines(lines, ink_width) & alpha_mask & ~details
        protected = lines | details
    sil_rgba = np.zeros((h, w, 4), dtype=np.uint8)
    sil_rgba[alpha_mask] = [235, 240, 245, 255]
    Image.fromarray(sil_rgba, mode="RGBA").save(steps_dir / "01_silhouette.png")

    lab_img = srgb_to_lab(arr[..., :3])

    pal_name = meta["palette"]
    if args.style:
        palette_lab = srgb_to_lab(palette_rgb)
    elif pal_name != "auto" and pal_name in PALETTES:
        palette_rgb = np.array(PALETTES[pal_name], dtype=np.uint8)
        palette_lab = srgb_to_lab(palette_rgb)
    else:
        color_count = int(meta["colors"])
        if color_count > 1 and details.any() and (alpha_mask & ~details).any():
            detail_colors = kmeans_lab(lab_img[details], k=max(1, color_count // 4))
            base_colors = kmeans_lab(lab_img[alpha_mask & ~details], k=color_count - len(detail_colors))
            centers_lab = np.concatenate((base_colors, detail_colors))
        else:
            centers_lab = kmeans_lab(lab_img[alpha_mask], k=color_count)
        palette_rgb = lab_to_srgb(centers_lab[np.argsort(centers_lab[:, 0])])
        palette_lab = srgb_to_lab(palette_rgb)

    dists = np.sum((lab_img[:, :, None, :] - palette_lab[None, None, :, :]) ** 2, axis=3)
    idx_source = np.argmin(dists, axis=2)
    idx_blockin = edge_preserving_majority(idx_source, alpha_mask, edge_target)
    if protected is not None:
        if ink_index is None:
            ink_index = int(np.argmin(palette_lab[:, 0]))
        idx_blockin[details] = idx_source[details]
        idx_blockin[lines] = ink_index
    render_indexed(idx_blockin, alpha_mask, palette_rgb).save(steps_dir / "02_blockin.png")

    shaded_lab = lab_img.copy()
    if args.hue_shift > 0:
        l_norm = (shaded_lab[..., 0] - 50.0) / 50.0
        shaded_lab[..., 2] += l_norm * (args.hue_shift * 18.0)
        shaded_lab[..., 1] += np.maximum(0.0, -l_norm) * (args.hue_shift * 8.0)

    if args.dither in ("bayer2", "bayer4"):
        mat = BAYER2 if args.dither == "bayer2" else BAYER4
        mh, mw = mat.shape
        tiled = np.tile(mat, (h // mh + 1, w // mw + 1))[:h, :w]
        shaded_lab[..., 0] += tiled * 14.0

    dists_shaded = np.sum(
        (shaded_lab[:, :, None, :] - palette_lab[None, None, :, :]) ** 2, axis=3
    )
    idx_shaded = np.argmin(dists_shaded, axis=2)
    if protected is not None:
        idx_shaded[protected] = idx_blockin[protected]
    render_indexed(idx_shaded, alpha_mask, palette_rgb).save(steps_dir / "03_shading.png")

    idx_clean = idx_shaded.copy()
    for _ in range(args.cleanup_passes):
        idx_clean = remove_orphans(idx_clean, alpha_mask, protected)
        idx_clean = smooth_jaggies(idx_clean, alpha_mask, protected)

    if args.sel_out:
        idx_clean = apply_selective_outline(idx_clean, alpha_mask, palette_lab, protected)

    render_indexed(idx_clean, alpha_mask, palette_rgb).save(steps_dir / "04_cleanup.png")

    np.save(case_dir / "build" / "palette_rgb.npy", palette_rgb)
    np.save(case_dir / "build" / "final_indices.npy", idx_clean)
    meta["fit_params"] = {
        "dither": args.dither,
        "hue_shift": args.hue_shift,
        "sel_out": args.sel_out,
        "cleanup_passes": args.cleanup_passes,
    }
    for option in ("lineart", "detail_mask", "style"):
        if path := getattr(args, option):
            meta["fit_params"][option] = str(Path(path).resolve())
    save_meta(case_dir, meta)
    print(f"[fit] Recorded 4 passes in {steps_dir}")


def detect_defects(idx_map: np.ndarray, alpha_mask: np.ndarray) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    h, w = idx_map.shape
    orphans: list[tuple[int, int]] = []
    jaggies: list[tuple[int, int]] = []

    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if not alpha_mask[y, x]:
                continue
            c = idx_map[y, x]
            nb8 = [
                idx_map[y + dy, x + dx]
                for dy in (-1, 0, 1)
                for dx in (-1, 0, 1)
                if (dy != 0 or dx != 0) and alpha_mask[y + dy, x + dx]
            ]
            if nb8 and c not in nb8:
                orphans.append((x, y))

            up = idx_map[y - 1, x] if alpha_mask[y - 1, x] else -1
            dn = idx_map[y + 1, x] if alpha_mask[y + 1, x] else -1
            lt = idx_map[y, x - 1] if alpha_mask[y, x - 1] else -1
            rt = idx_map[y, x + 1] if alpha_mask[y, x + 1] else -1
            if (up != -1 and up == dn and up != c and lt != c and rt != c) or (
                lt != -1 and lt == rt and lt != c and up != c and dn != c
            ):
                jaggies.append((x, y))

    return orphans, jaggies


def cmd_check(args: argparse.Namespace) -> None:
    case_dir = Path(args.case_dir).resolve()
    meta = load_meta(case_dir)
    prep_dir = case_dir / "build" / "prep"
    steps_dir = case_dir / "build" / "steps"
    check_dir = case_dir / "build" / "check"
    check_dir.mkdir(parents=True, exist_ok=True)

    ref_aligned = Image.open(prep_dir / "phase_aligned.png").convert("RGBA")
    edge_target = np.array(Image.open(prep_dir / "edge_target.png"), dtype=np.float32)
    final_img = Image.open(steps_dir / "04_cleanup.png").convert("RGBA")
    idx_clean = np.load(case_dir / "build" / "final_indices.npy")
    palette_rgb = np.load(case_dir / "build" / "palette_rgb.npy")

    ref_arr = np.array(ref_aligned)
    fin_arr = np.array(final_img)

    ref_mask = ref_arr[..., 3] >= 128
    fin_mask = fin_arr[..., 3] >= 128

    inter = np.logical_and(ref_mask, fin_mask).sum()
    union = np.logical_or(ref_mask, fin_mask).sum()
    sil_iou = float(inter / max(1, union))

    ref_edges = edge_target >= np.percentile(edge_target, 75)
    fin_edges = compute_sobel_edges(np.array(final_img.convert("L"), dtype=np.float32))
    fin_edge_bin = fin_edges >= np.percentile(fin_edges, 75)
    tp = np.logical_and(ref_edges, fin_edge_bin).sum()
    fp = np.logical_and(~ref_edges, fin_edge_bin).sum()
    fn = np.logical_and(ref_edges, ~fin_edge_bin).sum()
    edge_f1 = float((2 * tp) / max(1, 2 * tp + fp + fn))

    ref_lab = srgb_to_lab(ref_arr[..., :3])
    fin_lab = srgb_to_lab(fin_arr[..., :3])
    delta_e = np.linalg.norm(ref_lab[fin_mask] - fin_lab[fin_mask], axis=1)
    mean_delta_e = float(delta_e.mean()) if len(delta_e) > 0 else 0.0

    orphans, jaggies = detect_defects(idx_clean, fin_mask)
    fg_count = max(1, int(fin_mask.sum()))
    orphan_ratio = float(len(orphans) / fg_count)
    jaggie_ratio = float(len(jaggies) / fg_count)

    acc = json.loads((case_dir / "acceptance.json").read_text(encoding="utf-8"))
    checks = {
        "silhouette_iou": {"value": round(sil_iou, 4), "target": f">= {acc['silhouette_iou_min']}", "pass": sil_iou >= acc["silhouette_iou_min"]},
        "edge_alignment": {"value": round(edge_f1, 4), "target": f">= {acc['edge_alignment_min']}", "pass": edge_f1 >= acc["edge_alignment_min"]},
        "mean_delta_e": {"value": round(mean_delta_e, 2), "target": "<= 14.0", "pass": mean_delta_e <= 14.0},
        "orphan_ratio": {"value": round(orphan_ratio, 4), "target": f"<= {acc['orphan_ratio_max']}", "pass": orphan_ratio <= acc["orphan_ratio_max"]},
        "jaggie_index": {"value": round(jaggie_ratio, 4), "target": f"<= {acc['jaggie_index_max']}", "pass": jaggie_ratio <= acc["jaggie_index_max"]},
    }
    all_pass = all(c["pass"] for c in checks.values())
    metrics = {"passed": all_pass, "checks": checks}
    (check_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    scale = 8
    h, w = fin_mask.shape
    pw, ph = w * scale, h * scale

    ov = np.zeros((h, w, 3), dtype=np.uint8)
    ov[ref_mask] += np.array([220, 40, 180], dtype=np.uint8)
    ov[fin_mask] += np.array([35, 215, 75], dtype=np.uint8)
    p1 = Image.fromarray(ov, mode="RGB").resize((pw, ph), Image.Resampling.NEAREST)

    ed = np.zeros((h, w, 3), dtype=np.uint8)
    ed[ref_edges] = [220, 50, 50]
    ed[np.logical_and(ref_edges, fin_edge_bin)] = [50, 230, 90]
    p2 = Image.fromarray(ed, mode="RGB").resize((pw, ph), Image.Resampling.NEAREST)

    bg = Image.new("RGBA", (pw, ph), (28, 30, 38, 255))
    fin_up = final_img.resize((pw, ph), Image.Resampling.NEAREST)
    p3 = Image.alpha_composite(bg, fin_up).convert("RGB")
    draw3 = ImageDraw.Draw(p3)
    for ox, oy in orphans:
        draw3.rectangle([ox * scale, oy * scale, (ox + 1) * scale - 1, (oy + 1) * scale - 1], outline=(255, 40, 40), width=2)
    for jx, jy in jaggies:
        draw3.rectangle([jx * scale, jy * scale, (jx + 1) * scale - 1, (jy + 1) * scale - 1], outline=(255, 210, 40), width=2)

    p4 = Image.new("RGB", (pw, ph), (24, 26, 33))
    draw4 = ImageDraw.Draw(p4)
    used_indices = sorted(set(idx_clean[fin_mask].tolist()))
    swatch_w = max(8, pw // max(1, len(used_indices)))
    for i, cidx in enumerate(used_indices):
        rgb = tuple(int(v) for v in palette_rgb[cidx])
        draw4.rectangle([i * swatch_w, 8, (i + 1) * swatch_w - 2, 36], fill=rgb)

    y_txt = 48
    for k, v in checks.items():
        status = "PASS" if v["pass"] else "FAIL"
        color = (90, 230, 120) if v["pass"] else (255, 90, 90)
        draw4.text((8, y_txt), f"[{status}] {k}: {v['value']} ({v['target']})", fill=color)
        y_txt += 16

    sheet = Image.new("RGB", (pw * 2 + 12, ph * 2 + 12), (16, 17, 22))
    sheet.paste(p1, (4, 4))
    sheet.paste(p2, (pw + 8, 4))
    sheet.paste(p3, (4, ph + 8))
    sheet.paste(p4, (pw + 8, ph + 8))
    sheet.save(check_dir / "check_sheet.png")

    print(json.dumps(metrics, indent=2))


def cmd_tile_preview(args: argparse.Namespace) -> None:
    if min(args.columns, args.rows, args.scale) < 1:
        sys.exit("Error: columns, rows, and scale must be positive integers.")
    source = Path(args.input)
    destination = Path(args.output)
    if source.resolve() == destination.resolve():
        sys.exit("Error: the tile preview needs a different path from its input.")

    with Image.open(source) as image:
        tile = image.convert("RGBA")
    if args.center_seams:
        tile = ImageChops.offset(tile, tile.width // 2, tile.height // 2)
    width, height = tile.size
    preview = Image.new("RGBA", (width * args.columns, height * args.rows))
    for row in range(args.rows):
        for column in range(args.columns):
            preview.paste(tile, (width * column, height * row))
    if args.scale != 1:
        preview = preview.resize(
            (preview.width * args.scale, preview.height * args.scale),
            Image.Resampling.NEAREST,
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    preview.save(destination)
    print(f"[tile-preview] Saved {preview.width} × {preview.height} preview to {destination}")


def cmd_tile_stats(args: argparse.Namespace) -> None:
    if args.top_colors < 1:
        sys.exit("Error: top-colors must be a positive integer.")

    ref_image = None
    try:
        with Image.open(args.input) as image:
            if args.reference:
                with Image.open(args.reference) as ref:
                    ref_image = ref.convert("RGBA")
            report = tonal_report(image, reference=ref_image, top_colors=args.top_colors)
    except ValueError as error:
        sys.exit(f"Error: {error}")

    payload = json.dumps(report, indent=2)
    if args.output:
        destination = Path(args.output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(payload + "\n", encoding="utf-8")
    print(payload)


def cmd_record_revision(args: argparse.Namespace) -> None:
    case_dir = Path(args.case_dir).resolve()
    load_meta(case_dir)
    label = args.label.strip()
    if not label:
        sys.exit("Error: a revision label must contain text.")
    source = Path(args.image) if args.image else case_dir / "build" / "steps" / "04_cleanup.png"
    with Image.open(source) as draft:
        snapshot = record_revision(case_dir, Revision(label, draft.convert("RGBA")))
    if snapshot:
        print(f"[record-revision] Saved {snapshot.name}: {label}")
    else:
        print("[record-revision] The pixels match the latest saved revision.")


def cmd_deliver(args: argparse.Namespace) -> None:
    case_dir = Path(args.case_dir).resolve()
    meta = load_meta(case_dir)
    case_name = meta["case_name"]
    scale = int(args.scale)
    if not args.manual and not meta.get("reference_path"):
        sys.exit("Error: use deliver --manual for an original tile without a source image.")

    prep_dir = case_dir / "build" / "prep"
    steps_dir = case_dir / "build" / "steps"
    deliver_dir = case_dir / "deliver"

    step_files = [
        ("01: Silhouette", steps_dir / "01_silhouette.png"),
        ("02: Block-In", steps_dir / "02_blockin.png"),
        ("03: Shading", steps_dir / "03_shading.png"),
        ("04: Cleanup (Final)", steps_dir / "04_cleanup.png"),
    ]
    steps = []
    for label, path in step_files:
        with Image.open(path) as step:
            steps.append((label, step.convert("RGBA")))
    final_1x = steps[-1][1]
    if args.manual and any(step.size != final_1x.size for _, step in steps):
        sys.exit("Error: all four hand-drawn passes must have the same native canvas size.")

    native_path = deliver_dir / f"{case_name}_1x.png"
    if not revision_paths(case_dir) and native_path.is_file():
        with Image.open(native_path) as previous:
            record_revision(case_dir, Revision("Previous export", previous.convert("RGBA")))
    label = "Latest export" if revision_paths(case_dir) else "First export"
    record_revision(case_dir, Revision(label, final_1x))

    deliver_dir.mkdir(parents=True, exist_ok=True)
    final_1x.save(native_path)

    final_nx = final_1x.resize((final_1x.width * scale, final_1x.height * scale), Image.Resampling.NEAREST)
    final_nx.save(deliver_dir / f"{case_name}_{scale}x.png")

    fin_mask = np.array(final_1x.getchannel("A")) >= 128
    if args.manual:
        pixels = np.asarray(final_1x)[..., :3][fin_mask]
        palette_rgb, frequencies = np.unique(pixels, axis=0, return_counts=True)
        counts = dict(enumerate(frequencies.tolist()))
    else:
        idx_clean = np.load(case_dir / "build" / "final_indices.npy")
        palette_rgb = np.load(case_dir / "build" / "palette_rgb.npy")
        counts = Counter(idx_clean[fin_mask].tolist())
    total_fg = max(1, sum(counts.values()))

    used = sorted(counts.keys())
    card_w = max(360, len(used) * 56)
    card = Image.new("RGB", (card_w, 96), (24, 26, 33))
    draw = ImageDraw.Draw(card)
    hex_lines = []
    for i, cidx in enumerate(used):
        r, g, b = [int(v) for v in palette_rgb[cidx]]
        hex_lines.append(f"{r:02x}{g:02x}{b:02x}")
        x0 = 12 + i * 54
        draw.rectangle([x0, 12, x0 + 44, 52], fill=(r, g, b), outline=(200, 200, 200))
        pct = round(100.0 * counts[cidx] / total_fg, 1)
        draw.text((x0, 58), f"#{r:02X}{g:02X}{b:02X}", fill=(220, 225, 235))
        draw.text((x0, 72), f"{pct}%", fill=(150, 160, 175))
    card.save(deliver_dir / f"{case_name}_palette.png")
    (deliver_dir / f"{case_name}_palette.hex").write_text("\n".join(hex_lines) + "\n", encoding="utf-8")

    pw, ph = final_1x.width * scale, final_1x.height * scale
    bg_tile = Image.new("RGBA", (pw, ph), (30, 32, 40, 255))
    reference_path = meta.get("reference_path") if args.manual else prep_dir / "subject_rgba.png"
    ref_comp = None
    if reference_path is not None:
        with Image.open(reference_path) as reference:
            ref_rgba = reference.convert("RGBA")
        ref_size = (pw, ph)
        if args.manual:
            ref_scale = min(pw / ref_rgba.width, ph / ref_rgba.height)
            ref_size = (max(1, round(ref_rgba.width * ref_scale)), max(1, round(ref_rgba.height * ref_scale)))
        ref_panel = ref_rgba.resize(ref_size, Image.Resampling.BILINEAR)
        ref_background = bg_tile.copy()
        ref_background.alpha_composite(ref_panel, ((pw - ref_panel.width) // 2, (ph - ref_panel.height) // 2))
        ref_comp = ref_background.convert("RGB")

    frames: list[Image.Image] = []
    step_x = pw + 12 if ref_comp is not None else 4
    frame_width = 2 * pw + 16 if ref_comp is not None else max(112, pw + 8)
    for label, step in steps:
        step_up = step.resize((pw, ph), Image.Resampling.NEAREST)
        step_comp = Image.alpha_composite(bg_tile, step_up).convert("RGB")
        frame = Image.new("RGB", (frame_width, ph + 32), (18, 20, 26))
        frame.paste(step_comp, (step_x, 26))
        fdraw = ImageDraw.Draw(frame)
        if ref_comp is not None:
            frame.paste(ref_comp, (4, 26))
            fdraw.text((8, 6), "Reference Subject", fill=(180, 190, 205))
        fdraw.text((step_x + 4, 6), label, fill=(110, 235, 145))
        frames.append(frame)

    history = [read_revision(path) for path in revision_paths(case_dir)]
    frames, durations = timelapse_with_revisions(frames, history)
    frames[0].save(
        deliver_dir / f"{case_name}_timelapse.gif",
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
    )

    aseprite_bin = args.aseprite_bin or shutil.which("aseprite")
    lua_script = skill_root() / "scripts" / "aseprite" / "build.lua"
    if aseprite_bin and lua_script.exists():
        subprocess.run(
            [
                aseprite_bin,
                "-b",
                "--script-param",
                f"steps_dir={steps_dir}",
                "--script-param",
                f"out_file={deliver_dir / f'{case_name}.aseprite'}",
                "--script",
                str(lua_script),
            ],
            check=False,
        )

    print(f"[deliver] Exported artifacts to {deliver_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="shmimage.py", description="Image Model Shmimage Model: multi-pass pixel-art pipeline.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Initialize a new pixel art case")
    p_init.add_argument("case_dir")
    p_init.add_argument("--input", help="Subject or material reference image")
    p_init.add_argument("--tile", action="store_true", help="Start a seamless tile case; the input image is optional")
    p_init.add_argument("--size", type=int, default=64)
    p_init.add_argument("--palette", choices=["auto", "gameboy", "pico8", "sweetie16", "nes", "endesga32"], default="auto")
    p_init.add_argument("--colors", type=int, default=16)
    p_init.set_defaults(func=cmd_init)

    p_prep = sub.add_parser("prep", help="Segment subject and align sub-pixel phase")
    p_prep.add_argument("case_dir")
    p_prep.add_argument("--bg-mode", choices=["auto", "none"], default="auto")
    p_prep.add_argument("--bg-tolerance", type=float, default=18.0)
    p_prep.set_defaults(func=cmd_prep)

    p_extract = sub.add_parser("extract", help="Infer editable line-art and detail guides from the prepared reference")
    p_extract.add_argument("case_dir")
    p_extract.add_argument("--method", choices=["ink", "xdog", "regions"], default="xdog")
    p_extract.add_argument("--line-threshold", type=float, default=0.24)
    p_extract.add_argument("--detail-threshold", type=float, default=0.42)
    p_extract.add_argument("--region-colors", type=int, default=12)
    p_extract.set_defaults(func=cmd_extract)

    p_style = sub.add_parser("style", help="Sample a palette and likely outline settings from a style image")
    p_style.add_argument("--input", required=True)
    p_style.add_argument("--output", required=True)
    p_style.add_argument("--colors", type=int, default=16)
    p_style.add_argument("--pixel-scale", type=int, help="Known integer enlargement of the reference")
    p_style.set_defaults(func=cmd_style)

    p_fit = sub.add_parser("fit", help="Run 4-pass synthesis and cleanup")
    p_fit.add_argument("case_dir")
    p_fit.add_argument("--dither", choices=["none", "bayer2", "bayer4"], default="none")
    p_fit.add_argument("--hue-shift", type=float, default=0.15)
    p_fit.add_argument("--sel-out", action="store_true")
    p_fit.add_argument("--cleanup-passes", type=int, default=1)
    p_fit.add_argument("--lineart", help="Native PNG mask with white pixels marking ink")
    p_fit.add_argument("--detail-mask", help="Native PNG mask with white pixels marking protected detail")
    p_fit.add_argument("--style", help="Palette and outline JSON from the style command")
    p_fit.set_defaults(func=cmd_fit)

    p_check = sub.add_parser("check", help="Evaluate quantitative metrics and generate check_sheet.png")
    p_check.add_argument("case_dir")
    p_check.set_defaults(func=cmd_check)

    p_tile = sub.add_parser("tile-preview", help="Inspect repeated tiles or centered wrap joins")
    p_tile.add_argument("--input", required=True, help="Native tile PNG")
    p_tile.add_argument("--output", required=True, help="Preview PNG")
    p_tile.add_argument("--columns", type=int, default=3)
    p_tile.add_argument("--rows", type=int, default=3)
    p_tile.add_argument("--scale", type=int, default=1, help="Integer nearest-neighbor enlargement")
    p_tile.add_argument("--center-seams", action="store_true", help="Wrap the image by half its width and height")
    p_tile.set_defaults(func=cmd_tile_preview)

    p_tile_stats = sub.add_parser("tile-stats", help="Report luminance balance, palette coverage, and seam continuity")
    p_tile_stats.add_argument("--input", required=True, help="Tile or pass PNG")
    p_tile_stats.add_argument("--reference", help="Optional material reference image for comparison")
    p_tile_stats.add_argument("--top-colors", type=int, default=24, help="Maximum palette colors to list")
    p_tile_stats.add_argument("--output", help="Optional JSON output path")
    p_tile_stats.set_defaults(func=cmd_tile_stats)

    p_record = sub.add_parser("record-revision", help="Save a native draft for the timelapse revision chapter")
    p_record.add_argument("case_dir")
    p_record.add_argument("--label", required=True, help="Short description of the draft or edit")
    p_record.add_argument("--image", help="Path to the draft PNG (defaults to build/steps/04_cleanup.png)")
    p_record.set_defaults(func=cmd_record_revision)

    p_del = sub.add_parser("deliver", help="Package 1x/Nx PNGs, palette card, timelapse GIF, and .aseprite")
    p_del.add_argument("case_dir")
    p_del.add_argument("--scale", type=int, default=8)
    p_del.add_argument("--manual", action="store_true", help="Package hand-drawn passes and read the palette from the final PNG")
    p_del.add_argument("--aseprite-bin", default=None)
    p_del.set_defaults(func=cmd_deliver)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
