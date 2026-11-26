"""Append close-up comparisons of the saved drafts to the four build passes."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CASE = Path(__file__).resolve().parents[1]
REVISIONS = CASE / "build" / "revisions"
FINAL = CASE / "build" / "steps" / "04_cleanup.png"
TIMELAPSE = CASE / "deliver" / f"{CASE.name}_timelapse.gif"
BACKGROUND = "#211725"
TEXT = "#fff5e6"
PINK = "#f987a2"
AMBER = "#ffb153"
BORDER = "#6a3b73"


def chapter_card(size):
    card = Image.new("RGB", size, BACKGROUND)
    pen = ImageDraw.Draw(card)
    x = size[0] // 2
    y = size[1] // 2
    pen.text((x, y - 34), "Revisions", font=ImageFont.load_default(size=78),
             fill=TEXT, anchor="mm")
    pen.text((x, y + 54), "Smoke details  /  Shorter smile  /  Third tooth",
             font=ImageFont.load_default(size=34), fill=AMBER, anchor="mm")
    return card


def comparison(size, number, title, before_path, after_path, bounds):
    frame = Image.new("RGB", size, BACKGROUND)
    half = size[0] // 2
    text = ImageDraw.Draw(frame)
    heading = ImageFont.load_default(size=36)
    label = ImageFont.load_default(size=24)
    text.text((34, 16), f"REVISION {number} / 3", font=label, fill=PINK)
    text.text((278, 8), title, font=heading, fill=TEXT)
    text.line((32, 62, size[0]-32, 62), fill=BORDER, width=2)

    for index, (caption, path) in enumerate([("Before", before_path), ("After", after_path)]):
        midpoint = index * half + half // 2
        with Image.open(path) as artwork:
            crop = artwork.crop(bounds).convert("RGB")
        top, bottom = 116, size[1] - 24
        scale = min((half - 84) // crop.width, (bottom - top) // crop.height)
        zoomed = crop.resize((crop.width * scale, crop.height * scale), Image.Resampling.NEAREST)
        x = midpoint - zoomed.width // 2
        y = (top + bottom - zoomed.height) // 2
        text.text((midpoint, 88), caption, font=label, fill=AMBER, anchor="mm")
        frame.paste(zoomed, (x, y))
        text.rectangle((x-2, y-2, x+zoomed.width+1, y+zoomed.height+1), outline=BORDER, width=2)
    return frame


def main():
    durations = []
    frames = []
    with Image.open(TIMELAPSE) as animation:
        loop = animation.info.get("loop", 0)
        for index in range(4):
            animation.seek(index)
            durations.append(animation.info.get("duration", 650))
            frames.append(animation.convert("RGB"))

    size = frames[0].size
    firelight = REVISIONS / "01_firelight_draft.png"
    smoke = REVISIONS / "02_smoke_refinement.png"
    smile = REVISIONS / "03_shorter_smile.png"
    frames.append(chapter_card(size))
    durations.append(1100)
    for number, (title, before, after, crop) in enumerate([
        ("Shaped the smoke into uneven billows", firelight, smoke, (3, 5, 141, 50)),
        ("Shortened the wide-shot smile", smoke, smile, (48, 60, 103, 93)),
        ("Added the third tooth", smile, FINAL, (193, 96, 251, 128)),
    ], start=1):
        frames.append(comparison(size, number, title, before, after, crop))
        durations.append(2300)

    temporary = TIMELAPSE.with_suffix(".gif.tmp")
    frames[0].save(temporary, format="GIF", save_all=True, append_images=frames[1:],
                   duration=durations, loop=loop, optimize=False, disposal=2)
    temporary.replace(TIMELAPSE)


if __name__ == "__main__":
    main()
