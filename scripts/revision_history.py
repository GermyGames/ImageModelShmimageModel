"""Save native pixel-art snapshots and render their timelapse comparisons."""
from dataclasses import dataclass
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import fill

from PIL import Image, ImageChops, ImageDraw, ImageFont, PngImagePlugin


BACKGROUND = "#211725"
TEXT = "#fff5e6"
ACCENT = "#ffb153"
BORDER = "#6a3b73"


@dataclass(frozen=True)
class Revision:
    label: str
    artwork: Image.Image


def revision_paths(case_dir: Path) -> list[Path]:
    directory = case_dir / "build" / "revisions"
    return sorted(directory.glob("revision-*.png"), key=lambda path: int(path.stem.split("-")[-1]))


def read_revision(path: Path) -> Revision:
    with Image.open(path) as image:
        return Revision(image.info["revision_label"], image.convert("RGBA"))


def changed_region(before: Image.Image, after: Image.Image) -> tuple[int, int, int, int] | None:
    red, green, blue, alpha = ImageChops.difference(before, after).split()
    return ImageChops.lighter(ImageChops.lighter(red, green), ImageChops.lighter(blue, alpha)).getbbox()


def record_revision(case_dir: Path, revision: Revision) -> Path | None:
    """Append a snapshot without replacing an existing revision."""
    directory = case_dir / "build" / "revisions"
    directory.mkdir(parents=True, exist_ok=True)
    png_info = PngImagePlugin.PngInfo()
    png_info.add_itxt("revision_label", revision.label)
    with TemporaryDirectory(dir=directory) as scratch:
        pending = Path(scratch) / "snapshot.png"
        revision.artwork.save(pending, pnginfo=png_info)
        while True:
            paths = revision_paths(case_dir)
            if paths:
                previous = read_revision(paths[-1]).artwork
                if previous.size == revision.artwork.size and not changed_region(previous, revision.artwork):
                    return None
            number = int(paths[-1].stem.split("-")[-1]) + 1 if paths else 1
            target = directory / f"revision-{number:04d}.png"
            try:
                os.link(pending, target)
            except FileExistsError:
                continue
            return target


def comparison_crops(before: Image.Image, after: Image.Image) -> tuple[Image.Image, Image.Image]:
    if before.size != after.size:
        return before, after

    region = changed_region(before, after)
    if region is None:
        return before, after
    left, top, right, bottom = region
    w, h = before.size
    x_margin = max(6, w // 16, (right - left) // 4)
    y_margin = max(6, h // 16, (bottom - top) // 4)
    bounds = (
        max(0, left - x_margin), max(0, top - y_margin),
        min(w, right + x_margin), min(h, bottom + y_margin),
    )
    return before.crop(bounds), after.crop(bounds)


def caption_font(size: int) -> ImageFont.ImageFont | ImageFont.FreeTypeFont:
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def timelapse_with_revisions(
    build_frames: list[Image.Image], history: list[Revision]
) -> tuple[list[Image.Image], list[int]]:
    durations = [650, 650, 650, 1950]
    if len(history) < 2:
        return build_frames, durations

    build_width, build_height = build_frames[0].size
    w = max(build_width, 720, 2 * max(r.artwork.width for r in history) + 48)
    h = max(build_height, 260, max(r.artwork.height for r in history) + 140)
    size = (w, h)
    frames = []
    for frame in build_frames:
        padded = Image.new("RGB", size, BACKGROUND)
        padded.paste(frame, ((w - frame.width) // 2, (h - frame.height) // 2))
        frames.append(padded)

    label = caption_font(18)
    heading = caption_font(24)
    count = len(history) - 1
    chapter = Image.new("RGB", size, BACKGROUND)
    draw = ImageDraw.Draw(chapter)
    draw.text((w // 2, h // 2 - 14), "Revisions", font=caption_font(48),
              anchor="mm", fill=TEXT)
    draw.text((w // 2, h // 2 + 32), f"{count} saved {'edit' if count == 1 else 'edits'}",
              font=label, anchor="mm", fill=ACCENT)
    frames.append(chapter)
    durations.append(1100)

    for index, (previous, current) in enumerate(zip(history, history[1:]), 1):
        frame = Image.new("RGBA", size, BACKGROUND)
        draw = ImageDraw.Draw(frame)
        draw.text((20, 12), f"REVISION {index} / {count}", font=label, fill=ACCENT)
        wrapped = fill(current.label, width=int((w - 40) / draw.textlength("M", font=heading)), max_lines=2)
        draw.multiline_text((20, 36), wrapped, font=heading, fill=TEXT, spacing=1)
        draw.line((20, 91, w - 20, 91), fill=BORDER, width=2)
        before, after = comparison_crops(previous.artwork, current.artwork)
        scale = min((w // 2 - 24) // max(before.width, after.width),
                    (h - 140) // max(before.height, after.height))
        for col, (caption, artwork) in enumerate([("Before", before), ("After", after)]):
            center = (2 * col + 1) * w // 4
            draw.text((center, 110), caption, font=label, anchor="mm", fill=ACCENT)
            zoomed = artwork.resize((artwork.width * scale, artwork.height * scale), Image.Resampling.NEAREST)
            x, y = center - zoomed.width // 2, (124 + h - 16 - zoomed.height) // 2
            draw.rectangle((x - 1, y - 1, x + zoomed.width, y + zoomed.height), outline=BORDER)
            frame.alpha_composite(zoomed, (x, y))
        frames.append(frame.convert("RGB"))
        durations.append(2300)
    return frames, durations
