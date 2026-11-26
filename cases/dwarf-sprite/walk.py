"""Draw and assemble the dwarf's eight-frame walk on the native grid."""
import argparse
import math
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw

CASE = Path(__file__).parent
ART = CASE / "build" / "walk"
STEPS = ART / "steps"
DELIVER = CASE / "deliver"
SIZE = (96, 112)
COLUMNS = 4
FRAME_MS = 90
INK = "#251d2b"


@dataclass(frozen=True)
class Foot:
    ankle_x: int
    sole_y: int
    angle: int
    lifted: bool = False


@dataclass(frozen=True)
class Pose:
    near: Foot
    far: Foot
    bob: int
    cape: int
    coat: int


@dataclass(frozen=True)
class SecondaryMotion:
    beard_swing: int
    beard_bounce: int
    cape_flick: int
    cape_lift: int
    arm_swing: int
    shoulder_dip: int
    near_forearm: tuple[int, int]


# Contact, down, passing, up. Repeat on the other leg.
POSES = (
    Pose(Foot(62, 108, -12), Foot(30, 103, 15), 0, -2, 1),
    Pose(Foot(55, 108, 0), Foot(34, 102, 22, True), 1, -1, 1),
    Pose(Foot(47, 108, 0), Foot(47, 99, 11, True), 0, 1, 0),
    Pose(Foot(38, 108, 10), Foot(56, 100, -11, True), -2, 2, -1),
    Pose(Foot(30, 108, 21), Foot(62, 103, -12), 0, 1, -1),
    Pose(Foot(34, 105, 25, True), Foot(55, 103, 0), 1, -1, -1),
    Pose(Foot(43, 100, 13, True), Foot(47, 103, 0), 0, -2, 0),
    Pose(Foot(53, 103, -9, True), Foot(38, 103, 10), -2, -1, 1),
)

# The beard and cape settle after each footfall. The free arm counters the stride.
SECONDARY = (
    SecondaryMotion(0, 0, -1, 0, -2, 0, (-4, 2)),
    SecondaryMotion(-1, 2, -2, 0, -1, 1, (-3, 2)),
    SecondaryMotion(-3, 0, -1, 1, 0, 1, (-1, 1)),
    SecondaryMotion(-1, -1, 1, 3, 1, 0, (2, -1)),
    SecondaryMotion(2, 0, 2, 2, 2, 0, (4, -2)),
    SecondaryMotion(1, 2, 0, 0, 1, -1, (3, -1)),
    SecondaryMotion(-2, 0, -2, 1, 0, -1, (0, 0)),
    SecondaryMotion(-1, -1, -2, 2, -1, 0, (-2, 1)),
)

# Relative to the ankle, with the toes pointing to the right.
BOOT = ((-5, -4), (4, -5), (5, 0), (9, 1), (12, 3), (13, 6),
        (12, 8), (8, 9), (-6, 9), (-8, 7), (-7, 4), (-5, 1))


def draw_leg(canvas, foot, near, bob, shaded):
    draw = ImageDraw.Draw(canvas)
    angle = math.radians(foot.angle)
    scale = 1.0 if near else 0.90

    def rotate(x, y):
        return (round(scale*(x*math.cos(angle) - y*math.sin(angle))),
                round(scale*(x*math.sin(angle) + y*math.cos(angle))))

    ankle_y = foot.sole_y - max(rotate(*vertex)[1] for vertex in BOOT)

    def shoe(points, color, outline=None):
        rotated = [rotate(*vertex) for vertex in points]
        draw.polygon([(foot.ankle_x+x, ankle_y+y) for x, y in rotated],
                     fill=color, outline=outline)

    hx, hy = (39 if near else 56), 78+bob
    ax, ay = foot.ankle_x, ankle_y
    kx = round((hx+ax)/2) + (5 if foot.lifted else 2)
    ky = round((hy+ay)/2)
    width = 7 if near else 6
    pants = "#513143" if near else "#382534"
    shin = "#733d48" if near else "#513143"

    draw.polygon(
        [(hx-width,hy), (hx+width,hy-2), (kx+width,ky), (ax+5,ay+2),
         (ax-6,ay+3), (kx-width,ky+2)], fill=pants, outline=INK,
    )
    draw.polygon(
        [(kx-width+1,ky+1), (kx+width-1,ky-1), (ax+5,ay+2),
         (ax-6,ay+2)], fill=shin, outline=INK,
    )
    shoe(BOOT, shin, INK)
    if not shaded:
        return

    dark = "#513143" if near else "#382534"
    mid = "#9d514d" if near else "#733d48"
    lit = "#b26752" if near else "#9d514d"
    edge = "#d48d62" if near else "#b26752"
    draw.polygon(
        [(hx-width+2,hy+2), (hx,hy+1), (kx+1,ky), (kx-4,ky+2)],
        fill=shin,
    )
    draw.polygon(
        [(kx-width+2,ky+3), (kx+2,ky+1), (ax+2,ay-1), (ax-4,ay+2)],
        fill=mid,
    )
    draw.line([(kx-width+2,ky+2), (kx+width-3,ky)], fill=lit)
    shoe(((-6,2), (4,1), (9,2), (12,5), (12,7), (7,8), (-6,8), (-7,7)), dark)
    shoe(((-4,-3), (1,-4), (3,0), (2,3), (-5,4), (-5,1)), mid)
    shoe(((2,3), (6,1), (10,3), (12,5), (10,7), (4,7), (1,6)), lit)
    shoe(((5,2), (8,2), (10,4), (8,4), (5,3)), edge)
    shoe(((-6,7), (1,8), (9,8), (11,7), (8,7), (-2,7)), mid)


def shift_rows(layer, amount, start, full, lift=0, hem_flick=0):
    """Bend a cloth edge without moving its attachment point."""
    shifted = Image.new("RGBA", SIZE)
    for y in range(SIZE[1]):
        weight = max(0, min(1, (y-start)/(full-start)))
        shift = round(amount*weight + hem_flick*weight**2)
        shifted.paste(layer.crop((0, y, SIZE[0], y+1)),
                      (shift, y-round(lift*weight)))
    return shifted


def swing_beard(head, motion):
    """Move the ends of the locks, holding the cheeks and the belt still."""
    result = head.copy()
    source = head.load()
    target = result.load()
    for y in range(44, 65):
        depth = min((y-43)/14, (66-y)/9, 1)
        for x in range(22, 74):
            taper = min((x-21)/9, (75-x)/11, 1)
            weight = taper*depth
            dx = round(motion.beard_swing*weight)
            dy = round(motion.beard_bounce*weight)
            target[x, y] = source[x-dx, y-dy]
    return result


def bend_sleeve(layer, joints):
    """Slide rows between shoulder, elbow, and wrist offsets on the pixel grid."""
    width, height = layer.size
    shifted = Image.new("RGBA", layer.size)
    keys = ((0, *joints[0][1:]), *joints, (height, *joints[-1][1:]))
    for (a, ax, ay), (b, bx, by) in zip(keys, keys[1:]):
        top, bottom = a+ay, b+by
        for y in range(max(0, top), min(height, bottom)):
            t = (y-top)/(bottom-top)
            row = min(height-1, round(a+(b-a)*t))
            dx = round(ax+(bx-ax)*t)
            shifted.paste(layer.crop((0, row, width, row+1)), (dx, y))
    return shifted


def compose(pose, motion, layers, shaded, clean=False):
    frame = Image.new("RGBA", SIZE)
    cape = shift_rows(layers["cape"], pose.cape, 54, 96,
                      lift=motion.cape_lift+int(clean), hem_flick=motion.cape_flick)
    frame.alpha_composite(cape, (0, pose.bob))
    draw_leg(frame, pose.far, False, pose.bob, shaded)
    draw_leg(frame, pose.near, True, pose.bob, shaded)
    coat = shift_rows(layers["body"], pose.coat, 76, 93, lift=2 if clean else 0)
    frame.alpha_composite(coat, (0, pose.bob))
    swing, dip = motion.arm_swing, motion.shoulder_dip
    # Anchor the near shoulder. Swing the bracer and hand together over the sleeve.
    far = bend_sleeve(layers["far_arm"], ((48, -swing/2, -dip),
                                         (62, -swing, -dip), (72, 0, 0)))
    dx, dy = motion.near_forearm
    frame.alpha_composite(far, (0, pose.bob))
    frame.alpha_composite(layers["near_shoulder"], (0, pose.bob))
    frame.alpha_composite(layers["near_forearm"], (dx, pose.bob+dy))
    frame.alpha_composite(swing_beard(layers["head"], motion), (0, pose.bob))
    # Move the axe with the gripping hand in whole pixels so the blade stays rigid.
    frame.alpha_composite(layers["axe"], (0, pose.bob-4))
    frame.alpha_composite(layers["grip"], (0, pose.bob))
    return frame


def sheet(frames):
    full = Image.new("RGBA", (SIZE[0]*COLUMNS, SIZE[1]*2))
    for index, frame in enumerate(frames):
        full.paste(frame, (index%COLUMNS*SIZE[0], index//COLUMNS*SIZE[1]))
    return full


def silhouettes(frames):
    for frame in frames:
        outline = Image.new("RGBA", SIZE, INK)
        outline.putalpha(frame.getchannel("A"))
        yield outline


def prepare():
    STEPS.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, str(CASE/"redraw.py"), "--walk-layers",
                    str(ART/"layers")], check=True)
    return {name: Image.open(ART/"layers"/f"{name}.png").convert("RGBA")
            for name in ("cape", "body", "head", "near_shoulder", "near_forearm",
                         "far_arm", "axe", "grip")}


def export(frames):
    sheet(frames).save(DELIVER/"dwarf_walk_sheet.png")
    # A solid background keeps the GIF consistent across viewers.
    previews = []
    for frame in frames:
        preview = Image.new("RGB", SIZE, "#d4cdc3")
        preview.paste(frame, mask=frame.getchannel("A"))
        previews.append(preview.resize((SIZE[0]*3,SIZE[1]*3), Image.Resampling.NEAREST))
    previews[0].save(DELIVER/"dwarf_walk_preview.gif", save_all=True,
                     append_images=previews[1:], duration=FRAME_MS, loop=0, disposal=2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--block-in", action="store_true", help="Draw the first two review passes.")
    parser.add_argument("--export", action="store_true", help="Save the native sheet and animated preview.")
    args = parser.parse_args()
    layers = prepare()
    poses_with_motion = tuple(zip(POSES, SECONDARY, strict=True))
    if args.block_in:
        frames = [compose(pose, motion, layers, shaded=False)
                  for pose, motion in poses_with_motion]
        sheet(silhouettes(frames)).save(STEPS/"01_silhouette.png")
        sheet(frames).save(STEPS/"02_blockin.png")
        return

    shading = [compose(pose, motion, layers, shaded=True)
               for pose, motion in poses_with_motion]
    sheet(shading).save(STEPS/"03_shading.png")
    frames = [compose(pose, motion, layers, shaded=True, clean=True)
              for pose, motion in poses_with_motion]
    sheet(frames).save(STEPS/"04_cleanup.png")
    if args.export:
        export(frames)


if __name__ == "__main__":
    main()
