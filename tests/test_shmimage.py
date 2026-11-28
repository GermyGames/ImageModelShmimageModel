from base64 import b64decode
from io import BytesIO
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

import numpy as np
from PIL import Image, ImageChops, ImageDraw


SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import shmimage  # noqa: E402
import tile_tools  # noqa: E402


CLI = SCRIPTS_DIR / "shmimage.py"


class PixelArtCliTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.case = self.root / "art"
        self.reference = self.root / "photo.png"

    def run_cli(self, command, *options):
        result = subprocess.run(
            [sys.executable, "-B", str(CLI), command, str(self.case), *options],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_prep_can_choose_shifted_phase_for_full_frame(self):
        source = Image.new("RGBA", (19, 11), "#151515")
        drawing = ImageDraw.Draw(source)
        drawing.rectangle((4, 1, 7, 9), fill="#ffffff")
        drawing.rectangle((14, 3, 18, 10), fill="#ffc870")
        source.save(self.reference)
        self.run_cli("init", "--input", str(self.reference), "--size", "8")
        self.run_cli("prep", "--bg-mode", "none")

        build = self.case / "build"
        metadata = json.loads((build / "case.json").read_text())
        self.assertNotEqual(metadata["best_phase"], [0.0, 0.0])
        with Image.open(build / "prep" / "subject_rgba.png") as prepared:
            self.assertEqual(prepared.tobytes(), source.tobytes())
            self.assertEqual(prepared.size, source.size)
        with Image.open(build / "prep" / "phase_aligned.png") as aligned:
            self.assertEqual(aligned.size, (8, 5))
            self.assertEqual(aligned.getchannel("A").getextrema(), (255, 255))

    def test_manual_deliver_reads_passes_and_palette_from_pngs(self):
        Image.new("RGB", (4, 12), "#3750d8").save(self.reference)
        self.run_cli("init", "--input", str(self.reference), "--size", "3")

        steps = self.case / "build" / "steps"
        final = Image.new("RGBA", (3, 2), "#e74d31")
        final.putpixel((1, 0), (58, 128, 81, 255))
        final.putpixel((2, 0), (84, 23, 57, 0))
        for filename, color in [
            ("01_silhouette.png", "#28202b"),
            ("02_blockin.png", "#074b6c"),
            ("03_shading.png", "#daf890"),
        ]:
            Image.new("RGBA", final.size, color).save(steps / filename)
        final.save(steps / "04_cleanup.png")

        self.run_cli("deliver", "--manual", "--scale", "4")

        deliver = self.case / "deliver"
        with Image.open(deliver / "art_1x.png") as native:
            self.assertEqual(native.tobytes(), final.tobytes())
        with Image.open(deliver / "art_4x.png") as preview:
            self.assertEqual(preview.size, (12, 8))
            self.assertEqual(preview.tobytes(), final.resize((12, 8), Image.Resampling.NEAREST).tobytes())
        self.assertEqual((deliver / "art_palette.hex").read_text().splitlines(), ["3a8051", "e74d31"])
        with Image.open(deliver / "art_timelapse.gif") as animation:
            self.assertEqual(animation.n_frames, 4)
            reference_panel = animation.convert("RGB")
            self.assertEqual(reference_panel.getpixel((4, 26)), (30, 32, 40))
            self.assertEqual(reference_panel.getpixel((10, 26)), (55, 80, 216))

    def test_timelapse_includes_every_saved_revision_in_order(self):
        Image.new("RGB", (4, 4), "#ebdfcc").save(self.reference)
        self.run_cli("init", "--input", str(self.reference), "--size", "4")
        steps = self.case / "build" / "steps"
        deliver = self.case / "deliver"
        colors = [(25, 35, 45), (90, 100, 110), (130, 140, 150), (180, 190, 200)]
        for name in ["01_silhouette", "02_blockin", "03_shading", "04_cleanup"]:
            Image.new("RGB", (4, 4), colors[1]).save(steps / f"{name}.png")

        # A case exported before revision history was available can still use its old artwork.
        Image.new("RGB", (4, 4), colors[0]).save(deliver / "art_1x.png")
        self.run_cli("deliver", "--manual", "--scale", "4")

        draft = self.root / "draft.png"
        Image.new("RGB", (6, 4), colors[2]).save(draft)
        self.run_cli("record-revision", "--image", str(draft), "--label", "Wider canvas")
        self.run_cli("record-revision", "--image", str(draft), "--label", "Identical retry")
        Image.new("RGB", (4, 4), colors[3]).save(steps / "04_cleanup.png")
        self.run_cli("record-revision", "--label", "Adjusted lighting")
        self.run_cli("deliver", "--manual", "--scale", "4")
        self.run_cli("deliver", "--manual", "--scale", "4")

        snapshots = sorted((self.case / "build" / "revisions").glob("revision-*.png"))
        self.assertEqual(len(snapshots), 4)
        for path, color, label in zip(snapshots, colors, [
            "Previous export", "Latest export", "Wider canvas", "Adjusted lighting",
        ]):
            with Image.open(path) as snapshot:
                self.assertEqual(snapshot.getpixel((0, 0)), (*color, 255))
                self.assertEqual(snapshot.info["revision_label"], label)

        with Image.open(deliver / "art_timelapse.gif") as animation:
            self.assertEqual(animation.n_frames, 8)
            width, height = animation.size
            for index, (before, after) in enumerate(zip(colors, colors[1:]), 5):
                animation.seek(index)
                frame = animation.convert("RGB")
                self.assertEqual(frame.getpixel((width // 4, height - 76)), before)
                self.assertEqual(frame.getpixel((3 * width // 4, height - 76)), after)

    def test_extract_writes_disjoint_native_masks_and_standalone_editor(self):
        source = Image.new("RGB", (48, 36), "#ceb980")
        draw = ImageDraw.Draw(source)
        draw.rectangle((8, 6, 41, 30), fill="#f09b4b", outline="#23172e", width=2)
        draw.rectangle((20, 14, 26, 21), fill="#23172e")
        draw.point((23, 17), fill="#fff7bf")
        source.save(self.reference)
        self.run_cli("init", "--input", str(self.reference), "--size", "24")
        self.run_cli("prep", "--bg-mode", "none")

        guides = self.case / "build" / "guides"
        for method in ["ink", "xdog", "regions"]:
            with self.subTest(method=method):
                self.run_cli("extract", "--method", method, "--line-threshold", "0.14", "--detail-threshold", "0.22")
                with Image.open(guides / "lineart.png") as lines, Image.open(guides / "detail_mask.png") as details:
                    self.assertEqual(lines.size, (24, 18))
                    self.assertEqual(details.size, lines.size)
                    self.assertEqual(lines.getextrema(), (0, 255))
                    self.assertEqual(details.getextrema(), (0, 255))
                    self.assertIsNone(ImageChops.multiply(lines, details).getbbox())
                page = (guides / "review.html").read_text()
                self.assertIn('"width": 24, "height": 18', page)
                self.assertIn('<body data-review="generated">', page)
                self.assertIn('id="editor-controls" hidden', page)
                self.assertIn("Open this file in a browser with JavaScript enabled", page)
                for image_id, dimensions in [("source", (48, 36)), ("static-grid", (24, 18))]:
                    match = re.search(fr'<img id="{image_id}" src="data:image/png;base64,([^"]+)"', page)
                    self.assertIsNotNone(match)
                    with Image.open(BytesIO(b64decode(match.group(1)))) as fallback:
                        fallback.load()
                        self.assertEqual(fallback.size, dimensions)
        with Image.open(guides / "overlay.png") as overlay:
            self.assertEqual(overlay.size, (24, 18))

    def test_style_and_masks_survive_palette_fitting_and_cleanup(self):
        paper, red, ink = (254, 240, 192), (232, 71, 92), (20, 43, 67)
        style_ref = Image.new("RGB", (9, 8), paper)
        draw = ImageDraw.Draw(style_ref)
        draw.line((1, 3, 7, 3), fill=ink)
        draw.rectangle((2, 5, 4, 6), fill=red)
        style_image_path = self.root / "style.png"
        style_ref.resize((27, 24), Image.Resampling.NEAREST).save(style_image_path)
        style_path = self.root / "style.json"
        subprocess.run([sys.executable, "-B", str(CLI), "style", "--input", str(style_image_path),
                        "--output", str(style_path), "--colors", "4"], check=True, capture_output=True)
        style = json.loads(style_path.read_text())
        self.assertEqual(style["pixel_scale"], 3)
        self.assertEqual(style["outline"], {"color": "#142b43", "width": 1})
        style["outline"]["width"] = 2
        style_path.write_text(json.dumps(style))

        source = Image.new("RGB", (12, 12), paper)
        source.putpixel((5, 5), red)
        source.save(self.reference)
        self.run_cli("init", "--input", str(self.reference), "--size", "12")
        self.run_cli("prep", "--bg-mode", "none")
        with Image.open(self.case / "build" / "prep" / "phase_aligned.png") as aligned:
            x, y = next((i, j) for j in range(12) for i in range(12) if aligned.getpixel((i, j))[:3] == red)
        mask = Image.new("L", (12, 12))
        mask.putpixel((x, y), 255)
        mask_path = self.root / "mask.png"
        mask.save(mask_path)
        self.run_cli("fit", "--style", str(style_path), "--lineart", str(mask_path), "--detail-mask", str(mask_path),
                     "--cleanup-passes", "2", "--dither", "bayer4", "--sel-out")

        for filename in ["02_blockin.png", "03_shading.png", "04_cleanup.png"]:
            with Image.open(self.case / "build" / "steps" / filename) as result:
                self.assertEqual(result.getpixel((x, y))[:3], red)
                self.assertEqual(result.getpixel((x+1, y))[:3], ink)
                self.assertEqual(result.getpixel((x, y+1))[:3], ink)

    def test_automatic_palette_reserves_room_for_rare_protected_color(self):
        source = Image.new("RGB", (16, 16), "#fef0c0")
        draw = ImageDraw.Draw(source)
        draw.rectangle((0, 0, 7, 15), fill="#142b43")
        red = (232, 71, 92)
        source.putpixel((12, 8), red)
        source.save(self.reference)
        self.run_cli("init", "--input", str(self.reference), "--size", "16", "--colors", "2")
        self.run_cli("prep", "--bg-mode", "none")
        prep = self.case / "build" / "prep" / "phase_aligned.png"
        with Image.open(prep) as aligned:
            x, y = next((i, j) for j in range(16) for i in range(16) if aligned.getpixel((i, j))[:3] == red)
        detail = Image.new("L", (16, 16))
        detail.putpixel((x, y), 255)
        mask = self.root / "detail.png"
        detail.save(mask)
        self.run_cli("fit", "--detail-mask", str(mask), "--cleanup-passes", "2")
        with Image.open(self.case / "build" / "steps" / "04_cleanup.png") as result:
            self.assertEqual(result.getpixel((x, y))[:3], red)
            self.assertEqual(len(result.getcolors()), 2)

    def test_tile_stats_reports_tonal_balance_palette_and_seams(self):
        tile = Image.new("RGB", (16, 16), "#d4c9af")
        draw = ImageDraw.Draw(tile)
        draw.rectangle((0, 4, 15, 7), fill="#162228")
        tile_path = self.root / "tile.png"
        tile.save(tile_path)

        ref = Image.new("RGB", (16, 16), "#000000")
        ImageDraw.Draw(ref).rectangle((8, 0, 15, 15), fill="#ffffff")
        ref.save(self.reference)

        report_path = self.root / "report.json"
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                str(CLI),
                "tile-stats",
                "--input",
                str(tile_path),
                "--reference",
                str(self.reference),
                "--output",
                str(report_path),
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        stdout_report = json.loads(result.stdout)
        saved_report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(stdout_report, saved_report)
        self.assertEqual(saved_report["unique_colors"], 2)
        self.assertEqual([c["pct"] for c in saved_report["colors"]], [75.0, 25.0])
        self.assertEqual(saved_report["value_bands"]["dark_pct"], 25.0)
        self.assertEqual(saved_report["value_bands"]["light_pct"], 75.0)
        self.assertEqual(saved_report["seams"]["lr_edge_diff"], 0.0)
        self.assertEqual(saved_report["seams"]["tb_edge_diff"], 0.0)
        self.assertAlmostEqual(saved_report["reference"]["luma_mean"], 127.5, places=1)
        self.assertAlmostEqual(
            saved_report["reference"]["luma_delta"],
            round(saved_report["luma_mean"] - saved_report["reference"]["luma_mean"], 1),
            places=1,
        )
        self.assertGreater(saved_report["reference"]["seams"]["lr_ratio"], 5.0)

    def test_manual_check_reports_hygiene_defects_and_passes_when_clean(self):
        Image.new("RGB", (8, 8), "#221133").save(self.reference)
        self.run_cli("init", "--input", str(self.reference), "--size", "8")

        steps = self.case / "build" / "steps"
        Image.new("RGBA", (6, 8), (34, 17, 51, 255)).save(steps / "01_silhouette.png")
        draft = Image.new("RGBA", (8, 8), (34, 17, 51, 255))
        draft.putpixel((2, 2), (255, 100, 50, 255))  # 1-px orphan
        draft.putpixel((5, 5), (90, 220, 120, 180))  # semi-transparent leak
        draft.save(steps / "04_cleanup.png")

        self.run_cli("check", "--manual", "--max-colors", "2")
        metrics_path = self.case / "build" / "check" / "metrics.json"
        sheet_path = self.case / "build" / "check" / "check_sheet.png"
        self.assertTrue(sheet_path.is_file())
        bad = json.loads(metrics_path.read_text(encoding="utf-8"))
        self.assertEqual(bad["mode"], "manual")
        self.assertFalse(bad["passed"])
        self.assertFalse(bad["checks"]["step_sizes_match"]["pass"])
        self.assertEqual(bad["checks"]["semi_transparent_pixels"]["value"], 1)
        self.assertFalse(bad["checks"]["semi_transparent_pixels"]["pass"])
        self.assertGreaterEqual(bad["orphan_count"], 1)
        self.assertIn([2, 2], bad["orphans"])
        self.assertEqual(bad["unique_colors"], 3)
        self.assertFalse(bad["checks"]["unique_colors"]["pass"])

        # Fix step size, alpha leak, orphan, and palette budget
        clean = Image.new("RGBA", (8, 8), (34, 17, 51, 255))
        draw = ImageDraw.Draw(clean)
        draw.rectangle((2, 2, 5, 5), fill=(255, 100, 50, 255))
        clean.save(steps / "01_silhouette.png")
        clean.save(steps / "04_cleanup.png")

        self.run_cli("check", "--manual", "--max-colors", "2")
        good = json.loads(metrics_path.read_text(encoding="utf-8"))
        self.assertTrue(good["passed"])
        self.assertTrue(good["checks"]["step_sizes_match"]["pass"])
        self.assertEqual(good["checks"]["semi_transparent_pixels"]["value"], 0)
        self.assertEqual(good["orphan_count"], 0)
        self.assertEqual(good["orphans"], [])
        self.assertEqual(good["unique_colors"], 2)
        self.assertTrue(good["checks"]["unique_colors"]["pass"])

    def test_review_sheet_renders_reference_and_selected_steps(self):
        ref = Image.new("RGB", (6, 6), "#102040")
        ref.save(self.reference)
        self.run_cli("init", "--input", str(self.reference), "--size", "12")

        steps = self.case / "build" / "steps"
        Image.new("RGBA", (12, 12), "#331155").save(steps / "01_silhouette.png")
        step2 = Image.new("RGBA", (12, 12), "#663399")
        step2.putpixel((4, 4), (255, 255, 255, 255))
        step2.save(steps / "02_blockin.png")

        self.run_cli("review-sheet", "--steps", "1,2", "--scale", "3")
        default_sheet = self.case / "build" / "check" / "review_sheet.png"
        self.assertTrue(default_sheet.is_file())
        with Image.open(default_sheet) as sheet:
            self.assertGreater(sheet.width, 350)
            self.assertGreater(sheet.height, 80)

        custom_out = self.root / "custom_review.png"
        self.run_cli("review-sheet", "--steps", "2", "--scale", "4", "--no-reference", "--output", str(custom_out))
        self.assertTrue(custom_out.is_file())
        with Image.open(custom_out) as solo:
            # Verify nearest-neighbor 4x block at (4, 4) -> 4x4 white square inside zoomed panel
            # Top strip has 1 tile (12px tall) + label_h (20px) + pad (12px) + 16px gap = y_zoom_start 60 + label_h 20 = 80
            white_count = sum(
                1
                for py in range(solo.height)
                for px in range(solo.width)
                if solo.getpixel((px, py)) == (255, 255, 255)
            )
            # 1 px in 1x tile + 16 px in 4x tile = 17 white pixels
            self.assertEqual(white_count, 17)

    def test_format_palette_pct_handles_tiny_nonzero_highlights(self):
        self.assertEqual(shmimage.format_palette_pct(1, 5000), "<0.1%")
        self.assertEqual(shmimage.format_palette_pct(0, 100), "0.0%")
        self.assertEqual(shmimage.format_palette_pct(25, 100), "25.0%")

    def test_icon_preview_renders_light_and_dark_size_rows(self):
        Image.new("RGB", (16, 16), "#210351").save(self.reference)
        self.run_cli("init", "--input", str(self.reference), "--size", "16")

        steps = self.case / "build" / "steps"
        icon = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        ImageDraw.Draw(icon).rectangle((2, 2, 13, 13), fill=(146, 81, 246, 255))
        icon.save(steps / "04_cleanup.png")

        self.run_cli("icon-preview")
        default_preview = self.case / "build" / "check" / "icon_preview.png"
        self.assertTrue(default_preview.is_file())
        with Image.open(default_preview) as preview:
            self.assertEqual(preview.getpixel((0, 0)), (236, 239, 244))
            self.assertEqual(preview.getpixel((0, preview.height - 1)), (24, 26, 32))

        custom_out = self.root / "dock_preview.png"
        self.run_cli("icon-preview", "--sizes", "64,32", "--output", str(custom_out))
        self.assertTrue(custom_out.is_file())
        with Image.open(custom_out) as custom:
            self.assertEqual(custom.getpixel((0, 0)), (236, 239, 244))
            self.assertEqual(custom.getpixel((0, custom.height - 1)), (24, 26, 32))

    def test_deliver_app_icon_exports_png_sizes_and_multisize_ico(self):
        Image.new("RGB", (16, 16), "#210351").save(self.reference)
        self.run_cli("init", "--input", str(self.reference), "--size", "16")

        steps = self.case / "build" / "steps"
        icon = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
        ImageDraw.Draw(icon).rectangle((2, 2, 13, 13), fill=(146, 81, 246, 255))
        for fname in ["01_silhouette.png", "02_blockin.png", "03_shading.png", "04_cleanup.png"]:
            icon.save(steps / fname)

        self.run_cli("deliver", "--manual", "--scale", "4", "--app-icon")
        deliver = self.case / "deliver"
        for sz in (256, 512, 1024):
            path = deliver / f"art_{sz}.png"
            self.assertTrue(path.is_file())
            with Image.open(path) as im:
                self.assertEqual(im.size, (sz, sz))
                self.assertEqual(im.getpixel((0, 0))[3], 0)
        ico_path = deliver / "art.ico"
        self.assertTrue(ico_path.is_file())
        with Image.open(ico_path) as ico:
            self.assertEqual(sorted(ico.info.get("sizes", [])), [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

        # Reject non-square canvas when --app-icon is requested
        nonsq = Image.new("RGBA", (8, 6), "#210351")
        for fname in ["01_silhouette.png", "02_blockin.png", "03_shading.png", "04_cleanup.png"]:
            nonsq.save(steps / fname)
        bad = subprocess.run(
            [sys.executable, "-B", str(CLI), "deliver", str(self.case), "--manual", "--scale", "4", "--app-icon"],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(bad.returncode, 0)
        self.assertIn("square", bad.stderr)


class TileToolsTests(unittest.TestCase):
    def test_periodic_gaussian_wraps_and_preserves_mean(self):
        impulse = np.zeros((16, 24), dtype=np.float32)
        impulse[0, 0] = 240.0

        blurred = tile_tools.periodic_gaussian(impulse, sigma=2.5)
        self.assertEqual(blurred.shape, (16, 24))
        self.assertAlmostEqual(float(blurred.mean()), float(impulse.mean()), places=4)
        self.assertAlmostEqual(float(blurred[0, 23]), float(blurred[0, 1]), places=5)
        self.assertAlmostEqual(float(blurred[15, 0]), float(blurred[1, 0]), places=5)
        self.assertGreater(float(blurred[0, 23]), 1.0)

        np.testing.assert_allclose(tile_tools.periodic_gaussian(impulse, sigma=0.0), impulse, atol=1e-6)

        rgb = np.stack([impulse, impulse * 0.5, impulse * 0.25], axis=-1)
        rgb_blurred = tile_tools.periodic_gaussian(rgb, sigma=2.0)
        self.assertEqual(rgb_blurred.shape, (16, 24, 3))
        np.testing.assert_allclose(rgb_blurred[..., 1], rgb_blurred[..., 0] * 0.5, atol=1e-4)

    def test_equalize_toroidal_luma_reduces_drift_and_preserves_mean(self):
        yy, xx = np.mgrid[:32, :32].astype(np.float32)
        drift = 40.0 * np.sin(2.0 * np.pi * xx / 32.0)
        ridge = 10.0 * np.sin(2.0 * np.pi * yy * 4.0 / 32.0)
        field = 110.0 + drift + ridge

        equalized = tile_tools.equalize_toroidal_luma(field, sigma=4.0, strength=0.8)
        self.assertAlmostEqual(float(equalized.mean()), float(field.mean()), places=4)
        self.assertLess(float(equalized.std()), float(field.std()) * 0.65)

    def test_toroidal_kuwahara_flattens_noise_and_is_shift_equivariant(self):
        rng = np.random.default_rng(7)
        base = np.full((24, 32), 60.0, dtype=np.float32)
        base[:, 16:] = 190.0
        noisy = base + rng.normal(0.0, 8.0, size=base.shape).astype(np.float32)

        filtered = tile_tools.toroidal_kuwahara(noisy, radius=2, passes=2)
        self.assertEqual(filtered.shape, noisy.shape)
        self.assertLess(float(filtered[:, 4:12].std()), float(noisy[:, 4:12].std()) * 0.5)
        step = float(filtered[:, 20:28].mean() - filtered[:, 4:12].mean())
        self.assertGreater(step, 115.0)

        rolled_in = np.roll(noisy, (5, 7), axis=(0, 1))
        rolled_out = tile_tools.toroidal_kuwahara(rolled_in, radius=2, passes=2)
        expected_out = np.roll(filtered, (5, 7), axis=(0, 1))
        np.testing.assert_allclose(rolled_out, expected_out, atol=1e-5)

    def test_absorb_small_components_wraps_and_respects_protected(self):
        grid = np.zeros((6, 6), dtype=np.uint8)
        # 2px component wrapping horizontally across right/left border
        grid[2, 5] = 3
        grid[2, 0] = 3
        # Isolated 1px protected component
        grid[5, 3] = 4
        # Tie test: 1px component of label 2 with two neighbors = 1 and two neighbors = 5 -> picks 1 (lowest)
        grid2 = grid.copy()
        absorbed = tile_tools.absorb_small_components(grid2, max_size=2, protected={4})
        self.assertEqual(int(absorbed[2, 5]), 0)
        self.assertEqual(int(absorbed[2, 0]), 0)
        self.assertEqual(int(absorbed[5, 3]), 4)

        preserved = tile_tools.absorb_small_components(grid2, max_size=1, protected={4})
        self.assertEqual(int(preserved[2, 5]), 3)
        self.assertEqual(int(preserved[2, 0]), 3)

        tie_grid = np.zeros((5, 5), dtype=np.uint8)
        tie_grid[2, 2] = 9
        tie_grid[1, 2] = 5
        tie_grid[3, 2] = 5
        tie_grid[2, 1] = 1
        tie_grid[2, 3] = 1
        tie_resolved = tile_tools.absorb_small_components(tie_grid, max_size=1)
        self.assertEqual(int(tie_resolved[2, 2]), 1)

    def test_prune_sparse_mask_wraps_corners_and_connectivity(self):
        mask = np.zeros((8, 8), dtype=bool)
        # 4px corner-wrapping 8-connected cluster: (0, 0), (0, 7), (7, 0), (7, 7)
        mask[0, 0] = True
        mask[0, 7] = True
        mask[7, 0] = True
        mask[7, 7] = True
        # 3px isolated cluster
        mask[3, 3] = True
        mask[3, 4] = True
        mask[4, 4] = True

        pruned8 = tile_tools.prune_sparse_mask(mask, min_size=4, connectivity=8)
        self.assertTrue(pruned8[0, 0] and pruned8[7, 7])
        self.assertFalse(pruned8[3, 3] or pruned8[4, 4])

        # Diagonal-only 4px chain kept under 8-connectivity, removed under 4-connectivity
        diag = np.zeros((8, 8), dtype=bool)
        for i in range(4):
            diag[i, i] = True
        self.assertTrue(tile_tools.prune_sparse_mask(diag, min_size=4, connectivity=8)[diag].all())
        self.assertFalse(tile_tools.prune_sparse_mask(diag, min_size=4, connectivity=4).any())

    def test_seam_continuity_distinguishes_seamless_from_ramp(self):
        yy, xx = np.mgrid[:16, :16].astype(np.float32)
        periodic = 128.0 + 40.0 * np.cos(2.0 * np.pi * (xx + yy) / 16.0)
        seamless_stats = tile_tools.seam_continuity(periodic)
        self.assertLess(seamless_stats["lr_ratio"], 1.3)
        self.assertLess(seamless_stats["tb_ratio"], 1.3)

        ramp = np.tile(np.linspace(0.0, 255.0, 16, dtype=np.float32), (16, 1))
        ramp_stats = tile_tools.seam_continuity(ramp)
        self.assertGreater(ramp_stats["lr_ratio"], 10.0)
        self.assertEqual(ramp_stats["tb_ratio"], 1.0)

    def test_torus_delta_shortest_signed_distance(self):
        coords = np.array([0.0, 15.0, 8.0], dtype=np.float32)
        deltas_from_15 = tile_tools.torus_delta(coords, 15.0, 16)
        np.testing.assert_allclose(deltas_from_15, np.array([1.0, 0.0, -7.0], dtype=np.float32))
        deltas_from_1 = tile_tools.torus_delta(np.array([15.0, 2.0], dtype=np.float32), 1.0, 16)
        np.testing.assert_allclose(deltas_from_1, np.array([-2.0, 1.0], dtype=np.float32))
