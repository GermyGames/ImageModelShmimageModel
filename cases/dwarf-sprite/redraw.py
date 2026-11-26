"""Draw the dwarf directly onto the 96 × 112 sprite grid."""
import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw

STEPS = Path(__file__).parent / "build" / "steps"
SIZE = (96, 112)
parser = argparse.ArgumentParser(description="Render the dwarf or export layers for animation.")
parser.add_argument("--walk-layers", type=Path)
walk_layers = parser.parse_args().walk_layers
if walk_layers:
    walk_layers.mkdir(parents=True, exist_ok=True)
PALETTE = dict(
    ink="#251d2b", deep="#382534", wine="#513143", rust="#733d48",
    brick="#9d514d", leather="#b26752", ochre="#d48d62",
    gold0="#765447", gold1="#aa7958", gold2="#deb487", gold3="#f5d8a6",
    hair0="#68333b", hair1="#974238", hair2="#c25d3c", hair3="#e98b4c",
    hair4="#ffbc6a", skin0="#aa5b53", skin1="#dc8764",
    skin2="#f5b47f", skin3="#ffdb9e",
    green0="#30353a", green1="#40494b", green2="#596459", green3="#7f8870",
    steel0="#454657", steel1="#666a79", steel2="#909aa1", steel3="#c4cdd0",
    steel4="#ecede0", eye="#362029",
)
sprite = Image.new("RGBA", SIZE)
draw = ImageDraw.Draw(sprite)


def points(path):
    """Sample corner and Bézier paths, rounding every point to the native grid."""
    tokens = iter(path.split())
    result = []
    cursor = (0, 0)
    for cmd in tokens:
        count = {"M": 1, "L": 1, "Q": 2, "C": 3}[cmd]
        knots = [(float(next(tokens)), float(next(tokens))) for _ in range(count)]
        if cmd in ("M", "L"):
            result.append(tuple(map(round, knots[-1])))
        else:
            controls = [cursor, *knots]
            length = sum(math.dist(a, b) for a, b in zip(controls, controls[1:]))
            steps = max(2, math.ceil(length * 1.5))
            for i in range(1, steps + 1):
                t = i / steps
                sample = controls
                while len(sample) > 1:
                    sample = [((1-t)*a[0]+t*b[0], (1-t)*a[1]+t*b[1])
                              for a, b in zip(sample, sample[1:])]
                point = tuple(map(round, sample[0]))
                if point != result[-1]:
                    result.append(point)
        cursor = knots[-1]
    return result


def fill(color, path, outline=None):
    draw.polygon(points(path), PALETTE[color], PALETTE[outline] if outline else None)


def stroke(color, path, width=1):
    draw.line(points(path), PALETTE[color], width, joint="curve")


def dot(color, *pixels):
    draw.point(pixels, PALETTE[color])


def shade_cape():
    fill("green2", "M 19 65 Q 23 69 27 69 Q 22 78 21 88 Q 19 92 17 94 L 15 95 Q 20 83 19 65")
    fill("green0", "M 26 74 L 24 85 Q 23 92 20 96 L 17 96 Q 21 89 22 82 L 26 74")
    stroke("green3", "M 17 91 Q 19 84 19 76")
    stroke("green2", "M 17 94 Q 21 94 23 92", 2)
    fill("green2", "M 78 66 L 76 73 L 73 73 L 75 66")


# Gather the cloak behind the left elbow. Its flare opens a gap behind the boots.
fill("ink", "M 28 41 Q 37 38 53 42 L 74 45 Q 80 50 78 63 Q 77 77 81 87 L 76 96 Q 61 92 49 95 Q 28 103 12 97 Q 18 86 16 72 Q 13 54 28 41")
fill("green1", "M 28 43 Q 37 39 53 44 L 73 47 Q 77 52 76 64 Q 75 80 79 87 L 75 93 Q 62 89 48 94 Q 27 100 14 96 Q 21 86 18 71 Q 15 56 28 43")
if walk_layers:
    shade_cape()
    stroke("green0", "M 18 69 L 18 77")
    sprite.save(walk_layers / "cape.png")
    sprite = Image.new("RGBA", SIZE)
    draw = ImageDraw.Draw(sprite)

if not walk_layers:
    # Weight sits over the back boot, with the other toe pointed to the right.
    fill("wine", "M 26 76 Q 38 76 50 82 L 65 77 Q 77 84 72 97 L 61 103 L 50 97 Q 48 90 44 94 L 38 103 L 23 99 Q 20 90 26 76", "ink")
    fill("rust", "M 24 89 L 40 91 Q 43 96 40 103 L 36 107 L 19 107 Q 14 106 16 102 Q 20 98 22 97 L 22 92 L 24 89", "ink")
    fill("rust", "M 55 89 Q 63 91 71 87 L 73 96 Q 80 98 81 103 Q 79 107 68 108 L 55 107 Q 51 105 52 99 L 55 89", "ink")

# Overlapping coat panels and tucked mail.
fill("steel0", "M 31 58 L 65 57 L 73 79 L 68 92 Q 56 96 42 92 L 24 91 Q 25 75 31 58", "ink")
fill("rust", "M 31 50 Q 45 45 59 52 L 70 59 Q 65 68 72 83 Q 68 88 57 89 L 49 75 Q 45 85 42 90 Q 29 93 22 88 Q 25 77 26 65 L 31 50", "ink")
fill("wine", "M 27 67 Q 42 72 64 64 L 66 70 Q 46 77 26 73 L 27 67", "ink")
# The far arm bends inward to the axe. The near arm rests on the belt.
def draw_far_arm():
    fill("steel1", "M 62 45 Q 73 43 79 50 Q 85 56 88 64 Q 89 70 85 73 L 77 71 Q 75 64 67 60 L 59 52 L 62 45", "ink")
    fill("leather", "M 86 65 Q 91 66 91 71 Q 91 77 85 79 L 79 79 Q 77 75 79 71 Q 83 69 86 65", "ink")


def draw_near_shoulder():
    fill("steel1", "M 29 43 Q 22 42 19 48 Q 14 53 15 59 Q 15 66 20 70 L 27 69 Q 34 65 36 59 L 40 53 Q 37 46 29 43", "ink")
    fill("leather", "M 27 45 Q 34 44 40 51 L 36 57 Q 29 51 20 55 Q 20 49 27 45", "deep")


def draw_near_forearm():
    fill("rust", "M 22 62 Q 25 59 28 61 L 35 65 L 34 72 Q 31 74 26 73 Q 21 73 19 69 Q 17 65 22 62", "ink")


if walk_layers:
    torso = sprite
    sprite = Image.new("RGBA", SIZE)
    draw = ImageDraw.Draw(sprite)
else:
    draw_far_arm()
    draw_near_shoulder()
    draw_near_forearm()

# Set both eyes below the helmet rim and leave room for the cheeks.
fill("hair0", "M 22 26 Q 21 19 31 15 Q 48 12 60 20 L 69 31 Q 70 38 75 44 Q 74 52 68 54 Q 67 60 61 60 Q 55 65 48 60 Q 42 63 37 58 Q 28 59 25 51 Q 19 50 20 44 Q 17 40 22 33 L 22 26", "ink")
fill("skin1", "M 36 20 Q 51 15 64 22 Q 68 25 69 30 L 69 36 Q 69 43 63 46 L 46 47 Q 36 44 32 35 L 32 25", "deep")
fill("hair2", "M 24 28 Q 29 29 34 34 Q 36 40 43 44 Q 48 44 51 42 Q 53 40 56 42 Q 60 44 65 42 Q 68 42 70 45 Q 74 48 69 52 Q 66 53 65 57 Q 61 63 55 59 Q 50 64 45 59 Q 39 60 35 55 Q 28 57 25 51 Q 20 49 22 44 Q 19 40 23 35 L 24 28", "hair0")

# Oversized dome, two cheek guards and the engraved brow band.
fill("wine", "M 19 28 Q 18 13 31 7 Q 43 1 57 7 Q 67 11 70 21 L 68 24 L 62 24 Q 46 20 35 28 L 29 36 Q 25 37 21 33 L 19 28", "ink")
fill("steel1", "M 64 18 Q 69 18 71 22 L 72 30 Q 74 33 71 36 L 69 35 L 68 29 L 65 25 L 64 18", "deep")
fill("steel2", "M 19 24 Q 27 17 44 17 Q 57 15 70 21 L 69 25 Q 55 20 40 24 Q 29 25 22 30 L 19 30 L 19 24", "deep")
fill("steel1", "M 19 25 Q 26 22 32 24 L 36 28 Q 33 32 34 37 Q 34 41 28 42 L 23 40 Q 20 35 19 30 L 19 25", "deep")
fill("gold2", "M 50 5 L 54 6 Q 56 11 57 17 L 61 21 L 59 25 L 55 27 L 52 23 L 53 19 Q 52 11 50 5", "deep")

# Construct the head and haft in one plane, then rotate the entire axe together.
AXE_ANGLE = math.radians(6)
AXE_COS = math.cos(AXE_ANGLE)
AXE_SIN = math.sin(AXE_ANGLE)


def axe_points(path, side=1):
    return [(round(79 + side*x*AXE_COS - y*AXE_SIN),
             round(49 + side*x*AXE_SIN + y*AXE_COS)) for x, y in points(path)]


def axe_fill(color, path, outline=None, side=1):
    draw.polygon(axe_points(path, side), PALETTE[color],
                 PALETTE[outline] if outline else None)


def axe_stroke(color, path, side=1):
    draw.line(axe_points(path, side), PALETTE[color])


def draw_axe_block():
    axe_fill("wine", "M -2 -5 L 2 -5 L 2 55 L 1 60 L -2 60 L -3 58 L -2 -5", "ink")
    for side in (-1, 1):
        axe_fill("steel1", "M 2 -5 Q 9 -5 12 -12 Q 15 -7 14 1 Q 14 8 11 13 Q 8 6 2 5 L 2 -5",
                 "ink", side)
    axe_fill("gold1", "M -2 -8 L 2 -8 L 3 -6 L 3 5 L 2 8 L -2 8 L -3 6 L -3 -6 L -2 -8", "deep")
    axe_fill("deep", "M -2 11 L 2 11 L 2 42 L -2 42 L -2 11", "ink")


# Two compact fists. The gripping hand wraps across the front of the haft.
def draw_rest_hand_block():
    fill("skin1", "M 32 66 L 35 65 L 38 65 L 40 67 L 42 69 L 42 72 L 40 74 L 36 75 L 33 73 L 31 70 L 32 66", "ink")


def draw_grip_block():
    fill("skin0", "M 80 72 L 77 72 L 75 70 L 73 71 L 73 73 L 71 74 L 71 77 L 73 80 L 77 81 L 79 79 L 82 78 L 82 74 L 80 72", "ink")

if walk_layers:
    head = sprite
    sprite = torso
    draw = ImageDraw.Draw(sprite)

if not walk_layers:
    draw_axe_block()
    draw_rest_hand_block()
    draw_grip_block()

    alpha = sprite.getchannel("A")
    silhouette = Image.new("RGBA", SIZE, PALETTE["ink"])
    silhouette.putalpha(alpha)
    silhouette.save(STEPS / "01_silhouette.png")
    sprite.save(STEPS / "02_blockin.png")

# Broad cloth folds and warm bounce on the boot leather.
if not walk_layers:
    shade_cape()
fill("brick", "M 29 75 Q 35 76 45 74 Q 44 81 40 85 Q 33 87 26 85 Q 29 79 29 75")
fill("leather", "M 30 76 L 37 77 Q 34 80 34 84 L 28 85 L 30 76")
fill("brick", "M 52 73 L 56 73 L 55 82 L 58 86 L 56 86 L 52 73")
stroke("gold0", "M 24 87 Q 31 90 41 86", 2)
stroke("gold1", "M 25 87 Q 32 88 39 86")
stroke("gold0", "M 28 72 Q 35 75 47 72")
fill("steel1", "M 26 90 Q 35 90 40 88 L 40 91 Q 35 93 26 91")
dot("steel2", (27,90),(30,91),(32,90),(35,91),(38,90))
if not walk_layers:
    fill("wine", "M 23 92 Q 30 95 39 93 L 39 96 Q 37 99 35 101 L 23 102 L 21 100 L 23 97")
    fill("brick", "M 25 94 L 32 95 L 30 99 L 26 100 L 23 99 L 25 94")
    fill("leather", "M 18 102 Q 23 99 28 101 Q 31 102 31 105 L 18 105 L 17 104 L 18 102")
    stroke("ochre", "M 19 102 Q 24 100 27 102")
    stroke("wine", "M 17 105 Q 26 107 36 104 L 38 102")
    stroke("gold1", "M 24 92 Q 30 94 37 93")
    stroke("gold0", "M 24 97 L 28 98 L 33 96")
    fill("brick", "M 55 94 L 63 93 L 64 98 Q 61 99 57 104 L 54 104 Q 53 101 55 94")
    fill("leather", "M 75 98 Q 79 100 79 103 Q 77 105 73 104 L 72 101 L 75 98")
    stroke("ochre", "M 76 100 L 79 102")
    stroke("wine", "M 55 105 L 65 105")

# A broad shoulder and a short bracer give each bend a clear elbow and wrist.
def shade_near_shoulder():
    fill("steel2", "M 18 51 L 20 50 L 20 55 L 26 56 L 25 60 Q 20 60 18 64 Q 15 61 16 56 L 18 51")
    stroke("steel3", "M 16 58 Q 17 54 19 52")
    for y, xs in [(55,[18]), (57,[17,20,23]), (59,[18,21]), (61,[18])]:
        dot("steel0", *((x,y) for x in xs))
        dot("steel3", *((x,y+1) for x in xs))
    fill("ochre", "M 22 51 Q 23 47 27 46 L 31 47 L 33 51 Q 26 49 22 51")
    stroke("gold2", "M 22 51 Q 24 48 27 47")


def shade_near_forearm():
    fill("brick", "M 21 65 Q 24 61 28 63 L 32 66 L 30 71 Q 24 72 21 69 L 21 65")
    stroke("ochre", "M 21 65 Q 24 62 27 63")
    stroke("wine", "M 22 67 L 24 69 L 27 66 L 29 68")
    stroke("gold1", "M 23 66 L 24 67 L 27 65 L 29 67")
    fill("wine", "M 30 64 L 34 66 L 32 69 L 34 72 L 31 73 Q 29 70 30 64")
    stroke("gold1", "M 31 65 L 30 69 L 31 71")


def shade_far_arm():
    fill("steel2", "M 80 55 Q 84 56 87 63 L 87 66 L 83 67 Q 81 61 78 59 L 80 55")
    stroke("steel3", "M 82 57 L 85 61 L 86 64")
    dot("steel0", (84,62), (86,65), (83,64))
    fill("brick", "M 86 67 Q 90 68 90 72 Q 88 77 83 77 L 82 72 Q 85 71 86 67")
    stroke("ochre", "M 86 68 L 89 70 L 88 72")
    stroke("wine", "M 84 74 L 86 75 L 88 73")
    stroke("gold1", "M 83 73 L 86 74 L 87 72")
    stroke("deep", "M 81 72 L 82 78", 2)
    stroke("gold1", "M 82 72 L 83 77")


if not walk_layers:
    shade_near_shoulder()
    shade_near_forearm()
    shade_far_arm()

# The open stance exposes the belt buckle beneath the beard.
fill("gold0", "M 46 66 L 51 65 L 53 66 L 53 71 L 50 73 L 46 72 L 45 70 L 46 66", "deep")
stroke("gold2", "M 46 70 L 47 67 L 51 66")
stroke("gold1", "M 47 71 L 50 71 L 51 69")
dot("gold2", (49,69))

if walk_layers:
    sprite.save(walk_layers / "body.png")
    sprite = head
    draw = ImageDraw.Draw(sprite)

# Helmet shell: a single warm reflection on the dome, and a cooler rim.
fill("rust", "M 21 22 Q 23 12 33 8 Q 41 5 49 6 L 51 14 Q 39 13 32 17 Q 26 18 21 22")
fill("brick", "M 25 16 Q 30 9 39 7 L 46 7 Q 41 10 37 10 Q 30 12 25 16")
stroke("leather", "M 29 11 Q 34 8 40 7")
fill("deep", "M 57 9 Q 63 12 67 18 L 58 15 L 57 9")
stroke("rust", "M 57 10 Q 62 12 64 15")
stroke("steel3", "M 20 25 Q 30 18 48 18")
stroke("steel3", "M 59 18 L 66 21")
stroke("gold0", "M 31 23 Q 40 20 50 21")
stroke("gold2", "M 32 22 L 36 21 L 39 22 L 42 20 L 45 21 L 49 20")
dot("steel4", (23,23),(27,21),(30,20),(43,18))
fill("steel0", "M 20 28 L 23 28 Q 26 31 25 36 Q 28 38 32 36 L 32 39 L 28 41 L 24 39 Q 21 34 20 28")
fill("steel2", "M 23 26 Q 30 24 33 28 Q 32 32 30 34 L 27 36 Q 26 30 23 26")
stroke("steel3", "M 22 26 Q 28 24 32 26")
stroke("gold2", "M 25 28 L 29 27 L 31 29 L 29 31 L 28 34")
stroke("gold0", "M 26 29 L 29 28 L 29 30 L 27 31")
dot("steel3", (27,38),(29,37))
stroke("steel2", "M 70 26 L 70 30 L 71 34")
dot("gold1", (70,31),(71,33))
fill("gold0", "M 54 10 Q 55 12 56 17 L 60 21 L 58 24 L 56 26 L 54 24 L 55 21 L 54 18 L 54 10")
stroke("gold3", "M 51 6 Q 54 12 54 18 L 53 22 L 55 24")
stroke("gold1", "M 56 19 L 58 21 L 56 24")
dot("steel4", (52,8),(54,18))

# Deep-set eyes, a short broad nose, and a weathered cheek.
fill("skin0", "M 35 29 Q 41 24 50 25 L 53 27 L 49 29 L 45 32 L 43 35 L 44 39 L 41 42 Q 36 40 34 34 L 35 29")
fill("skin0", "M 60 25 Q 64 24 67 26 L 69 32 L 68 37 L 66 38 L 65 34 L 65 30 L 60 30 L 60 25")
fill("skin2", "M 41 28 Q 47 25 53 27 L 52 28 L 48 28 L 44 30 L 41 28")
fill("skin2", "M 43 38 L 47 36 L 52 36 L 51 39 L 48 41 L 43 42 L 43 38")
fill("hair0", "M 42 30 L 47 28 L 50 29 L 54 31 L 53 32 L 49 31 L 45 31 L 42 30")
fill("hair0", "M 59 31 L 62 29 L 67 28 L 67 30 L 63 31 L 60 32 L 59 31")
stroke("eye", "M 45 33 L 48 32 L 50 32 L 53 33")
stroke("skin3", "M 47 33 L 49 33")
dot("skin2", (48,34))
dot("eye", (50,33))
stroke("skin0", "M 46 35 L 50 35 L 52 34")
stroke("eye", "M 60 33 L 63 32 L 66 32")
dot("skin3", (62,33),(63,33))
dot("skin2", (63,34))
dot("eye", (64,33))
stroke("skin0", "M 62 35 L 65 34")
fill("skin0", "M 55 33 L 57 33 L 58 36 Q 61 36 62 38 Q 62 41 59 42 L 54 41 Q 52 39 54 37 L 55 33")
fill("skin2", "M 56 34 L 57 36 Q 59 36 60 38 L 60 39 L 57 39 L 54 38 L 56 34")
dot("skin3", (56,37),(57,37),(58,38))
dot("hair0", (59,40))
stroke("skin0", "M 43 39 L 45 40")
dot("skin3", (47,38))

# Separate the beard into locks that hook around one another.
fill("hair1", "M 23 37 Q 24 42 31 42 Q 35 43 38 42 Q 38 45 42 46 Q 44 50 41 56 Q 38 57 35 53 Q 28 56 26 50 Q 21 48 23 44 Q 20 41 23 37")
fill("hair1", "M 48 42 Q 49 43 50 45 Q 56 43 62 43 Q 72 42 72 48 Q 69 51 66 50 Q 66 58 61 59 L 55 57 Q 51 62 46 57 Q 49 56 49 50 L 48 42")
fill("hair3", "M 24 42 Q 27 45 31 43 Q 34 43 35 46 Q 32 48 35 51 L 33 54 Q 30 53 28 50 Q 26 48 27 46 Q 24 46 24 42")
fill("hair3", "M 35 45 Q 38 45 40 49 Q 44 51 43 54 Q 43 57 47 58 Q 42 60 39 55 Q 40 51 36 49 L 35 45")
fill("hair3", "M 43 43 Q 47 45 47 50 Q 47 54 51 54 Q 54 50 51 47 Q 51 45 54 44 Q 56 46 57 50 Q 57 53 54 58 Q 51 61 48 58 Q 45 56 46 52 Q 45 49 43 47 L 43 43")
fill("hair3", "M 61 45 Q 66 47 63 51 Q 61 55 62 57 Q 57 57 58 53 Q 60 49 58 47 L 61 45")
fill("hair2", "M 65 44 Q 70 43 71 47 Q 71 49 68 50 L 65 50 Q 68 48 65 44")
# Mustache locks fall from the nose and cover the mouth.
fill("hair1", "M 51 44 Q 55 41 61 42 L 66 45 Q 61 46 58 48 Q 54 47 51 44")
fill("hair3", "M 42 45 Q 47 44 49 42 Q 53 39 56 42 L 57 43 Q 53 44 51 47 Q 48 50 44 49 L 42 45")
fill("hair2", "M 58 43 Q 62 40 66 42 Q 69 44 68 47 L 66 49 Q 64 47 62 47 L 58 43")
stroke("hair4", "M 45 46 Q 49 45 52 42")
stroke("hair3", "M 60 43 Q 64 42 66 45")

stroke("hair4", "M 28 45 Q 31 45 31 49 L 32 51")
stroke("hair4", "M 38 47 Q 41 50 41 52")
stroke("hair4", "M 53 46 Q 55 49 54 52")
stroke("hair4", "M 62 47 L 62 49 L 60 52")
stroke("hair2", "M 46 52 Q 46 56 50 58")
dot("hair2", (23,36),(22,39),(22,40))

def paint_axe():
    draw_axe_block()
    axe_stroke("brick", "M 0 42 L 0 57")
    axe_stroke("ochre", "M -1 43 L -1 56")
    axe_fill("gold0", "M -2 56 L 2 56 L 1 59 L -2 59 L -2 56")
    axe_stroke("gold2", "M -2 56 L 1 56")
    for side in (-1, 1):
        axe_fill("steel2", "M 3 -3 Q 9 -4 12 -9 Q 14 -2 12 6 Q 7 3 3 3 L 3 -3", side=side)
        axe_fill("steel3", "M 12 -10 Q 15 -2 13 5 L 11 11 Q 12 4 12 0 Q 13 -4 12 -10", side=side)
        axe_fill("steel0", "M 6 -2 L 9 -4 L 8 0 L 6 -2", side=side)
        axe_fill("steel0", "M 6 3 L 8 0 L 9 4 L 6 3", side=side)
        axe_stroke("steel1", "M 4 4 Q 8 4 11 8", side)
    axe_stroke("steel4", "M 12 -9 Q 14 -5 14 -1", -1)
    axe_stroke("steel4", "M 13 -8 Q 14 -4 14 -2")
    axe_fill("gold0", "M 1 -5 L 2 -6 L 2 5 L 1 7 L 1 -5")
    axe_stroke("gold3", "M -2 -6 L -2 5")
    axe_stroke("gold2", "M -2 -7 L 2 -7")
    axe_stroke("gold2", "M -1 6 L 1 6")
    axe_stroke("wine", "M -1 12 L -1 41")
    for y in range(12, 42, 3):
        axe_stroke("rust", f"M -1 {y} L 1 {y+1}")
    axe_stroke("brick", "M -1 24 L 0 25")
    axe_stroke("gold1", "M -1 10 L 1 10")


def paint_rest_hand():
    draw_rest_hand_block()
    fill("skin0", "M 32 70 L 35 69 L 39 70 L 41 70 L 40 73 L 37 74 L 34 73 L 32 70")
    fill("skin2", "M 33 67 Q 35 65 38 66 L 39 68 L 38 69 L 36 68 L 34 70 L 32 69 L 33 67")
    stroke("hair0", "M 36 70 L 38 72 L 40 72")
    stroke("skin1", "M 37 70 L 39 70 L 40 71")
    dot("skin3", (35,67))


def paint_grip():
    draw_grip_block()
    fill("skin1", "M 81 74 L 78 74 L 75 72 L 74 72 L 74 74 L 72 75 L 72 77 L 74 79 L 77 80 L 78 77 L 81 77 L 81 74")
    fill("skin2", "M 74 72 L 75 71 L 77 73 L 77 74 L 75 74 L 74 73")
    stroke("skin2", "M 72 75 L 74 75 L 76 76")
    stroke("hair0", "M 73 77 L 75 77 L 76 76")
    stroke("skin1", "M 74 78 L 76 79")
    dot("skin3", (73,75))


def clean_character():
    stroke("wine", "M 22 16 Q 26 9 34 7")
    stroke("ochre", "M 34 9 L 38 8 L 41 8")
    if not walk_layers:
        stroke("green0", "M 18 69 L 18 77")
    dot("hair4", (26,46),(33,52),(50,55),(60,54))
    dot("gold3", (26,48),(30,28))

if walk_layers:
    clean_character()
    sprite.save(walk_layers / "head.png")
    for name, painters in (
        ("far_arm", (draw_far_arm, shade_far_arm)),
        ("near_shoulder", (draw_near_shoulder, shade_near_shoulder)),
        ("near_forearm", (draw_near_forearm, shade_near_forearm, paint_rest_hand)),
        ("axe", (paint_axe,)),
        ("grip", (paint_grip,)),
    ):
        sprite = Image.new("RGBA", SIZE)
        draw = ImageDraw.Draw(sprite)
        for paint in painters:
            paint()
        sprite.save(walk_layers / f"{name}.png")
else:
    paint_axe()
    paint_rest_hand()
    paint_grip()
    sprite.save(STEPS / "03_shading.png")
    clean_character()
    sprite.save(STEPS / "04_cleanup.png")
