from base64 import b64decode
from io import BytesIO
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from PIL import Image, ImageChops, ImageDraw


CLI = Path(__file__).resolve().parents[1] / "scripts" / "shmimage.py"


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
