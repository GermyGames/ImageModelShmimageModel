"""Paint the campfire at native resolution and export its animation."""

import argparse
from dataclasses import dataclass
from math import pi, sin
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw


CASE = Path(__file__).resolve().parents[1]
ANIMATION = CASE / "build" / "animation" / "steps"
DELIVER = CASE / "deliver"
SIZE = (64, 64)
FRAMES = 16
COLUMNS = 4
FRAME_MS = 70
PREVIEW_SCALE = 5
PREVIEW_BG = "#19191d"

COLORS = {
    "ash": "#25242b",
    "slate": "#34313a",
    "char": "#44363e",
    "shadow": "#382329",
    "coal": "#49272c",
    "bark": "#653236",
    "rust": "#853c35",
    "wood": "#a64935",
    "split": "#ca6138",
    "cinder": "#ad3825",
    "ember": "#db4c20",
    "vermilion": "#f06d20",
    "orange": "#fa931f",
    "amber": "#ffb736",
    "gold": "#ffda57",
    "lemon": "#ffe982",
    "cream": "#fff3bd",
    "white": "#fff8de",
}


def points(path):
    return [tuple(map(int, pair.split(","))) for pair in path.split()]


class Painter:
    def __init__(self, canvas):
        self.draw = ImageDraw.Draw(canvas)

    def poly(self, color, path):
        self.draw.polygon(points(path), fill=COLORS[color])

    def line(self, color, path):
        self.draw.line(points(path), fill=COLORS[color])

    def pixels(self, color, path):
        self.draw.point(points(path), fill=COLORS[color])

    def shapes(self, shapes):
        for color, path in shapes:
            self.poly(color, path)


def ground(p, shaded):
    p.shapes((
        ("ash", "5,57 10,56 13,54 17,54 22,52 41,52 45,54 52,55 57,56 59,57 "
                "57,58 53,58 52,59 46,59 43,60 20,60 17,59 13,59 12,58 7,58"),
        ("shadow", "10,56 16,55 26,54 35,55 43,54 51,55 57,56 54,57 48,57 "
                   "45,59 35,58 30,59 21,59 19,57 12,58"),
        ("coal", "12,55 22,52 39,53 48,54 53,56 45,57 41,56 35,58 25,58 20,57 15,57"),
    ))
    if shaded:
        p.shapes((
            ("rust", "13,55 20,54 24,55 19,56 13,56"),
            ("rust", "33,55 43,54 51,55 48,56 41,56 37,57 32,57"),
            ("wood", "18,55 25,54 30,55 36,55 38,56 32,57 25,57 22,56"),
            ("bark", "8,56 10,55 13,56 11,57 7,57"),
            ("slate", "51,57 56,56 59,57 57,58 53,58"),
            ("slate", "14,58 17,57 21,58 21,59 17,59"),
        ))
        p.pixels("bark", "5,58 11,59 23,60 48,60 58,59 60,57")
        p.pixels("rust", "9,57 16,57 23,58 30,59 43,58 49,57 55,55")


def rear_wood(p, shaded):
    p.shapes((
        ("coal", "9,54 13,50 20,49 24,50 22,54 16,56 11,56"),
        ("bark", "13,51 19,49 24,49 24,52 20,54 14,54"),
        ("coal", "26,40 28,35 32,34 34,37 45,53 44,56 39,56 37,53"),
        ("rust", "27,39 30,35 33,36 43,51 39,51 32,44"),
        ("shadow", "38,52 43,49 53,51 57,53 56,56 52,57 43,56 39,55"),
        ("bark", "41,51 47,50 54,52 55,54 48,54 44,53 40,54"),
        ("coal", "45,52 48,47 50,45 51,40 53,38 53,43 52,47 50,50 51,52 49,54"),
    ))
    if shaded:
        p.shapes((
            ("wood", "14,51 18,50 23,50 22,51 17,53 13,53"),
            ("split", "28,38 30,36 32,36 40,47 36,44 34,44 31,39"),
            ("wood", "42,51 47,50 53,52 51,53 46,52"),
        ))
        p.line("split", "48,49 49,47 51,45 52,41 53,38")
        p.line("rust", "49,51 51,49 52,47")
        p.line("shadow", "11,55 15,55 18,54")


# A low, broad flame stays rooted between the logs while tongues rise through it.
BED_FLAME = (
    ("cinder", "16,52 15,49 16,45 14,42 18,44 20,40 19,37 23,39 24,36 27,38 "
               "30,34 34,36 37,33 41,36 43,42 47,42 50,38 49,45 53,45 "
               "50,50 47,54 38,56 25,56"),
    ("ember", "17,53 17,48 19,45 21,45 23,41 26,41 29,37 33,39 36,37 40,39 "
              "42,44 46,45 49,42 48,48 50,48 46,53 38,55 27,55"),
    ("vermilion", "19,53 19,49 22,46 24,44 27,43 28,41 31,40 33,42 35,40 39,41 "
                  "41,46 44,47 47,46 45,52 41,54 29,55 24,54"),
    ("orange", "21,53 22,49 25,47 27,44 30,45 33,43 36,42 38,45 39,48 43,49 44,52 "
               "39,54 29,54"),
    ("amber", "23,53 26,49 30,48 31,45 34,46 36,44 37,48 40,50 42,52 36,54 29,54"),
    ("gold", "25,53 27,51 31,50 34,47 36,48 36,50 39,51 39,53 32,55"),
    ("lemon", "28,53 30,51 33,51 34,49 35,49 37,52 36,54 33,55"),
)

HEARTH = (
    ("ember", "18,53 23,49 28,49 32,46 38,47 42,49 48,49 50,53 46,56 39,57 33,57 27,56 22,56"),
    ("vermilion", "19,53 23,51 28,51 32,48 38,48 42,50 46,50 48,53 44,55 35,57 29,56 23,55"),
    ("orange", "21,53 26,52 29,51 34,48 37,49 39,51 45,51 46,53 42,55 34,56 27,55"),
    ("amber", "24,53 28,53 31,51 35,49 37,50 40,53 44,52 43,54 38,55 30,55"),
    ("gold", "26,54 30,53 34,50 36,50 38,53 41,54 37,55 30,55"),
    ("lemon", "29,54 32,53 34,51 36,51 37,54 34,55"),
    ("cream", "32,54 34,52 35,52 36,54 34,55"),
    ("white", "34,53 35,53 35,54 34,54"),
)

HEAT_RAMP = ("cinder", "ember", "vermilion", "orange", "amber",
             "gold", "lemon", "cream", "white")
HEAT_LEVELS = {color: level for level, color in enumerate(HEAT_RAMP, 1)}

# Each row gives the leading tip, trailing edge, width and heat at the next age.
# After reaching the crest, the trailing edge rises faster and the flame pinches off.
LIFE = (
    (.32, .00, .54, 6),
    (.43, .00, .83, 8),
    (.54, .00, 1.00, 9),
    (.65, .02, 1.07, 9),
    (.76, .05, 1.00, 8),
    (.86, .11, .87, 7),
    (.95, .21, .72, 6),
    (1.03, .32, .55, 4),
    (1.10, .53, .37, 3),
    (1.17, .84, .23, 2),
    (1.23, 1.08, .13, 1),
)

# Outlines run from the leading tip around the left edge and back up the right.
# The trailing edge narrows and the broadest part creeps toward the tip with age.
LICK = (
    (0, 0), (-.28, .11), (-.18, .25), (-.55, .34), (-.51, .43),
    (-.89, .55), (-.80, .63), (-1, .76), (-.68, .90), (-.47, 1),
    (.42, 1), (.72, .93), (.86, .81), (1, .70), (.67, .62),
    (.77, .49), (.48, .37), (.51, .26), (.26, .16),
)
WISP = (
    (0, 0), (-.19, .08), (-.43, .14), (-.75, .24), (-.56, .35),
    (-1, .43), (-.65, .52), (-.56, .66), (-.31, .82), (-.04, 1),
    (.09, 1), (.26, .86), (.20, .69), (.49, .55), (.47, .46),
    (.83, .35), (.74, .26), (.68, .18), (.29, .10),
)

# Each hotter color exposes a rim of the layer beneath and starts lower in the tongue.
BANDS = (
    (0, 1, 1), (.06, .98, .88), (.14, .96, .75), (.23, .94, .63),
    (.31, .93, .53), (.41, .92, .43), (.51, .91, .35), (.63, .90, .27), (.73, .90, .19),
)


@dataclass(frozen=True)
class Pulse:
    birth: int
    x: int
    root: int
    rise: int
    width: int
    drift: int
    mirror: int
    heat: int = 0


PULSES = (
    Pulse(0, 32, 52, 39, 11, 3, 1),
    Pulse(5, 36, 51, 34, 9, 4, -1),
    Pulse(11, 33, 52, 38, 10, -4, 1),
    Pulse(2, 25, 53, 23, 7, -8, -1, -2),
    Pulse(11, 23, 51, 22, 6, -4, 1, -2),
    Pulse(0, 42, 54, 20, 7, 6, 1, -2),
    Pulse(8, 42, 52, 25, 7, 5, -1, -2),
)


def paint_pulse(mask, pulse, age, shaded):
    rise, trail, breadth, peak = LIFE[age]
    top = pulse.root - pulse.rise * rise
    bottom = pulse.root - pulse.rise * trail
    span = bottom - top
    width = pulse.width * breadth
    thinning = max(0, min(1, (age - 3) / 5))
    draw = ImageDraw.Draw(mask)
    for level, (start, stop, band_width) in enumerate(BANDS[:max(1, peak + pulse.heat)], 1):
        if not shaded and level not in (1, 5):
            continue
        band_top = top + span * start
        band_length = span * (stop - start)
        vertices = []
        for (lateral, height), (wisp_lateral, wisp_height) in zip(LICK, WISP):
            lateral += (wisp_lateral - lateral) * thinning
            height += (wisp_height - height) * thinning
            y = band_top + band_length * height
            lift = (pulse.root - y) / pulse.rise
            lean = pulse.drift * lift ** 1.3
            hook = pulse.mirror * (2 * sin(pi * height) - 3 * (1 - height) ** 4)
            x = pulse.x + lean + hook + pulse.mirror * lateral * width * band_width
            vertices.append((round(x), round(y)))
        draw.polygon(vertices, fill=level)


def flames(p, frame, shaded):
    heat = Image.new("L", SIZE)
    heat_draw = ImageDraw.Draw(heat)
    for color, path in (*BED_FLAME, *HEARTH):
        level = HEAT_LEVELS[color]
        if shaded or level in (1, 5):
            heat_draw.polygon(points(path), fill=level)
    for pulse in PULSES:
        age = (frame - pulse.birth) % FRAMES
        if age < len(LIFE):
            layer = Image.new("L", SIZE)
            paint_pulse(layer, pulse, age, shaded)
            heat = ImageChops.lighter(heat, layer)
    for y in range(SIZE[1]):
        for x in range(SIZE[0]):
            level = heat.getpixel((x, y))
            if level:
                p.draw.point((x, y), fill=COLORS[HEAT_RAMP[level - 1]])


def front_wood(p, shaded):
    p.shapes((
        # Split wood leaning in from the left.
        ("coal", "10,55 11,52 16,49 23,41 23,39 26,38 30,41 28,44 26,45 22,52 17,56 12,57"),
        ("wood", "12,53 17,49 23,42 25,39 28,40 28,42 24,46 19,53 16,55 12,56"),
        ("rust", "14,53 19,49 25,43 27,42 23,48 20,52 17,55 14,55"),
        # A thin upright branch frames the bright gap in the center.
        ("shadow", "19,55 21,51 21,46 23,43 26,43 28,46 31,54 33,57 31,59 "
                   "27,58 25,55 23,50 22,56 20,57"),
        ("rust", "21,51 22,46 24,44 26,44 28,48 29,52 31,56 30,57 28,55 26,49 24,46 23,49 22,54"),
        ("bark", "24,47 26,48 27,53 29,57 32,58 29,58 26,55 25,52"),
        # The crossed trunk has a firelit face and a dark underside.
        ("coal", "32,44 32,41 35,40 38,41 41,45 47,50 51,54 50,57 46,58 42,56 39,53 36,50"),
        ("rust", "33,42 36,41 39,44 41,47 46,50 48,53 46,55 43,53 40,50 37,47 34,46"),
        ("bark", "35,46 38,48 41,52 44,54 47,54 47,57 44,57 40,54 38,51 36,50"),
        ("split", "33,42 35,41 37,42 39,45 43,48 45,50 42,49 39,47 36,44 34,44"),
        ("rust", "45,55 47,53 50,54 51,55 50,57 47,58 45,57"),
        ("wood", "46,55 48,54 50,55 49,57 47,57"),
        # A shorter front split catches light along its exposed edge.
        ("coal", "32,56 34,54 38,52 41,52 42,54 40,57 36,59 32,59"),
        ("wood", "33,56 38,53 40,52 41,53 39,55 35,58 33,58"),
        ("rust", "33,58 37,56 39,55 41,54 39,57 36,59 33,59"),
    ))
    if not shaded:
        return
    p.shapes((
        ("split", "12,53 16,50 19,46 23,42 24,40 26,39 27,40 25,43 21,47 17,52 13,55"),
        ("shadow", "13,55 16,54 17,53 18,55 16,56 12,56"),
        ("wood", "23,45 24,44 26,44 27,46 28,49 26,48 25,46 24,46 22,49"),
        ("char", "23,48 24,47 25,49 24,51 25,54 24,55 23,53 23,51"),
        ("split", "33,56 36,54 39,53 40,53 37,56 34,57"),
        ("bark", "36,45 38,46 40,49 43,51 45,52 46,54 44,53 41,52 39,50 37,49"),
        ("char", "38,51 41,53 43,54 45,55 45,56 42,55 40,54"),
        ("split", "47,55 48,54 50,55 50,56 48,57 46,56"),
        ("rust", "47,55 48,55 49,56 48,56"),
    ))
    p.line("wood", "17,53 20,51 23,47")
    p.line("bark", "14,54 16,53 19,50")
    p.line("split", "27,48 28,51 29,53")
    p.line("shadow", "21,56 23,52 23,50")
    p.line("coal", "27,54 28,56 30,57")
    p.line("wood", "35,43 37,44 39,46 43,49 46,52")
    p.line("split", "41,48 43,49 44,50")
    p.line("coal", "38,49 40,51 42,52")
    p.line("bark", "34,58 36,58 38,57")
    p.line("char", "12,56 16,56 18,55")
    p.line("char", "52,56 54,56 55,55")
    p.pixels("bark", "11,54 16,55 24,42 32,56 47,56 49,55")


# Birth phase, lifetime, origin, rise, drift and lateral curl.
SPARKS = (
    (0, 13, 32, 38, 26, -11, 2),
    (1, 11, 39, 32, 21, 10, -2),
    (3, 15, 32, 34, 29, 1, -4),
    (5, 12, 24, 46, 26, -13, 1),
    (5, 11, 38, 40, 21, 8, -2),
    (7, 12, 34, 32, 25, 11, 2),
    (9, 10, 26, 37, 25, -5, -1),
    (10, 12, 33, 42, 26, 5, 4),
    (12, 14, 44, 44, 27, 9, 2),
    (13, 13, 27, 33, 26, -11, 2),
    (15, 11, 36, 39, 28, 0, -3),
    (2, 14, 31, 25, 23, 11, 1),
    (8, 12, 33, 29, 25, -8, -1),
    (11, 10, 21, 34, 14, -9, 1),
)


def sparks(p, frame):
    for birth, life, origin_x, origin_y, rise, drift, curl in SPARKS:
        elapsed = (frame - birth) % FRAMES
        if elapsed >= life:
            continue
        t = elapsed / (life - 1)
        x = round(origin_x + drift * t + curl * sin(pi * t))
        y = round(origin_y - rise * t)
        color = ("lemon", "gold", "orange", "ember", "cinder", "rust")[round(5 * t)]
        p.draw.point((x, y), fill=COLORS[color])
        if 2 <= elapsed <= 4 and birth % 3 == 0:
            p.draw.point((x, y + 1), fill=COLORS["vermilion"])


def glints(p, frame):
    p.line("amber", "13,53 16,51 17,49")
    p.line("gold", "23,43 24,43 25,44")
    p.line("amber", "25,45 26,46 27,49")
    p.line("amber", "33,41 35,41 36,42")
    p.line("orange", "37,43 39,45 44,49")
    p.line("gold", "34,55 37,53 39,52")
    p.pixels("amber", "20,55 33,54 42,54 51,53")
    p.pixels("ember", "10,56 17,57 23,56 30,58 44,57 52,55")
    glows = (
        ("16,50 28,51 35,41 42,48 41,55", "24,44 34,54 49,54"),
        ("14,54 23,43 36,42 45,51 20,55", "26,46 38,52 51,53"),
        ("17,49 26,48 34,42 43,48 33,55", "24,43 36,54 42,54"),
        ("15,52 24,44 29,54 37,44 47,54", "25,45 39,52 43,54"),
    )
    hot, bright = glows[(frame // 2 + frame // 8) % len(glows)]
    p.pixels("orange", hot)
    p.pixels("lemon", bright)


def compose(frame, stage):
    image = Image.new("RGBA", SIZE)
    p = Painter(image)
    shaded = stage >= 3
    ground(p, shaded)
    rear_wood(p, shaded)
    flames(p, frame, shaded)
    front_wood(p, shaded)
    if stage == 4:
        glints(p, frame)
        sparks(p, frame)
    if stage == 1:
        alpha = image.getchannel("A")
        image = Image.new("RGBA", SIZE, COLORS["shadow"])
        image.putalpha(alpha)
    return image


def sheet(frames):
    width, height = SIZE
    canvas = Image.new("RGBA", (width * COLUMNS, height * (len(frames) // COLUMNS)))
    for index, frame in enumerate(frames):
        canvas.paste(frame, (index % COLUMNS * width, index // COLUMNS * height))
    return canvas


def export(frames):
    sheet(frames).save(DELIVER / "campfire_sheet.png")
    previews = []
    for frame in frames:
        preview = Image.new("RGB", SIZE, PREVIEW_BG)
        preview.paste(frame, mask=frame.getchannel("A"))
        previews.append(preview.resize(tuple(n * PREVIEW_SCALE for n in SIZE), Image.Resampling.NEAREST))
    previews[0].save(
        DELIVER / "campfire_loop.gif", save_all=True, append_images=previews[1:],
        duration=FRAME_MS, loop=0, disposal=2, optimize=False,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--block-in", action="store_true", help="Draw only the silhouette and flat-color passes.")
    parser.add_argument("--export", action="store_true", help="Write the sheet and looping GIF to deliver/.")
    args = parser.parse_args()
    ANIMATION.mkdir(parents=True, exist_ok=True)
    stages = ("01_silhouette", "02_blockin", "03_shading", "04_cleanup")
    for stage, name in enumerate(stages, 1):
        frames = [compose(index, stage) for index in range(FRAMES)]
        sheet(frames).save(ANIMATION / f"{name}.png")
        if args.block_in and stage == 2:
            return
    if args.export:
        DELIVER.mkdir(parents=True, exist_ok=True)
        export(frames)


if __name__ == "__main__":
    main()
