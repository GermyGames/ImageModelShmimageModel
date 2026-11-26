"""Draw the cathedral and its figures directly on a 256 × 320 pixel grid."""
from math import atan2, cos, hypot, pi, sin
from pathlib import Path
from random import Random
import sys

from PIL import Image, ImageColor, ImageDraw

W, H = 256, 320
CX = 127
CASE = Path(__file__).resolve().parents[1]
PALETTE = {
    "black": "#090a16", "ink": "#10101f", "soot": "#16162a", "vault": "#202039",
    "stone0": "#282744", "stone1": "#34334e", "stone2": "#45405b", "stone3": "#595168",
    "steel": "#1d354c", "teal0": "#264a64", "teal1": "#34677b", "teal2": "#428997",
    "glass": "#60afaf", "ice": "#96d6c9", "pale": "#c4eadd",
    "plum": "#341b34", "wine": "#50203b", "red0": "#702646", "red1": "#97314f",
    "red2": "#bb4255", "rose": "#e15b62", "pink": "#f98273",
    "brown": "#57313a", "copper": "#83463e", "clay": "#ab5945", "orange": "#d47a46",
    "amber": "#ee9f4c", "gold": "#f8bf61", "light": "#ffdc8a", "flame": "#fff2bf",
    "violet": "#777089", "linen0": "#8d8396", "linen1": "#b4a5a9", "linen2": "#e0c8b8",
    "skin0": "#814854", "skin1": "#a45e56", "skin2": "#cc826b", "skin3": "#e6a384",
    "skin4": "#f5c49e", "green0": "#1d403e", "green1": "#32614c", "green2": "#508653",
    "green3": "#8eaf52", "green4": "#c9d974",
    "blue1": "#344c78", "blue2": "#4979a2", "yellow0": "#9b703b",
    "mortar": "#2c293e", "slate": "#383750", "haze": "#243e55", "mist": "#2e566c",
    "ember0": "#48243a", "ember1": "#612940", "ember2": "#89354a",
    "fabric": "#65253e", "wool": "#522139",
    "linen_warm": "#bea6a0", "linen_shadow": "#8e7686", "linen_edge": "#d5ada1",
    "glass_dark": "#142321", "glass_haze": "#273830", "moss": "#37482c",
    "fern": "#45643b", "glass_muted": "#62823b", "dew_green": "#87a83f",
    "dew_lime": "#bcdc53", "dew_light": "#e2f58f",
    "oxblood": "#341727", "char_red": "#581e31", "ritual_red": "#92263b",
    "hot_red": "#d23b39", "nacho": "#ff812d", "nacho_light": "#ffb34d",
}


RGB = {name: ImageColor.getrgb(color) for name, color in PALETTE.items()}


class Canvas:
    def __init__(self, stage):
        self.stage = stage
        self.im = Image.new("RGB", (W, H), PALETTE["ink"])
        self.pen = ImageDraw.Draw(self.im)

    def poly(self, color, pts, outline=None):
        self.pen.polygon(pts, fill=PALETTE[color], outline=PALETTE[outline] if outline else None)

    def line(self, color, pts, width=1):
        self.pen.line(pts, fill=PALETTE[color], width=width)

    def rect(self, color, box):
        self.pen.rectangle(box, fill=PALETTE[color])

    def dot(self, color, x, y):
        self.pen.point((x, y), fill=PALETTE[color])

    def glaze(self, pts, ramp):
        """Shift selected stone or fabric colors inside a native-pixel lighting shape."""
        mask = Image.new("1", (W, H))
        ImageDraw.Draw(mask).polygon(pts, fill=1)
        palette = {RGB[base]: RGB[lit] for base, lit in ramp.items()}
        pixels, matte = self.im.load(), mask.load()
        left, top, right, bottom = mask.getbbox()
        for y in range(top, bottom):
            for x in range(left, right):
                if matte[x, y] and pixels[x, y] in palette:
                    pixels[x, y] = palette[pixels[x, y]]

    def oval(self, color, box, outline=None):
        self.pen.ellipse(box, fill=PALETTE[color], outline=PALETTE[outline] if outline else None)


def arch(x, y, w, h, foot):
    """Trace both ribs from the spring line into the pointed crown."""
    half = [(0, 0), (w*.24, h*.15), (w*.45, h*.31), (w*.65, h*.49),
            (w*.82, h*.68), (w*.94, h*.86), (w, h)]
    return [(x-w, foot)] + [(round(x-d), round(y+dy)) for d, dy in half[::-1]] + [
        (round(x+d), round(y+dy)) for d, dy in half[1:]] + [(x+w, foot)]


def mirror(points, side):
    return [(CX + side * (x - CX), y) for x, y in points]


def recess(c, x, y, w, h, foot):
    c.poly("soot", arch(x, y, w, h, foot))
    c.line("stone1", arch(x, y, w, h, foot), 2)
    c.line("stone0", arch(x, y+4, w-3, h, foot), 2)
    c.poly("steel", arch(x, y+8, w-6, h, foot))
    if c.stage < 2:
        return
    for dx in (-4, 4):
        c.poly("teal0", arch(x+dx, y+27, 3, 11, foot-7))
        for yy in range(y+40, foot-5, 11):
            c.rect("teal1", (x+dx-2, yy, x+dx+1, yy+6))
            c.dot("glass", x+dx-1, yy+1)
            c.line("teal0", [(x+dx-2, yy+5), (x+dx+1, yy+1)])
    c.oval("teal1", (x-4, y+15, x+4, y+23), "ink")
    c.poly("teal2", [(x, y+16), (x+2, y+19), (x, y+22), (x-2, y+19)])
    c.line("stone2", [(x-w-1, foot), (x+w+1, foot)])
    c.line("soot", [(x-w-4, foot+2), (x+w+4, foot+2)], 2)


def rose_window(c):
    r, cy = 38, 90
    c.oval("stone1", (CX-44, cy-44, CX+44, cy+44), "soot")
    c.oval("stone2", (CX-42, cy-42, CX+42, cy+42), "stone0")
    c.oval("soot", (CX-40, cy-40, CX+40, cy+40))
    c.oval("moss", (CX-r, cy-r, CX+r, cy+r), "steel")
    if c.stage < 2:
        for n in range(12):
            a = n*pi/6
            c.line("steel", [(CX, cy), (CX+int(37*cos(a)), cy+int(37*sin(a)))], 2)
        return
    rng = Random(207)
    colors = {(x, y): rng.random() for y in range(-15, 16) for x in range(-15, 16)}
    for dy in range(-r, r+1):
        for dx in range(-r, r+1):
            dist = hypot(dx, dy)
            if dist > r:
                continue
            angle = atan2(dy, dx) + pi/2
            t = abs((angle + pi/12) % (pi/6) - pi/12) * dist
            pr = 29 - ((dist - 23) * .60) ** 2
            grain = colors[(round((dx+(dy % 3)*.45)/3), round(dy/3))]
            led = abs(dist - 26.7) < .52 and t < max(0, pr/7) and abs(dx) > 3
            inner = 11.4 + 2.5*cos(angle*6)
            if dist > 36.2 or abs(dist - 33.8) < .65 or abs(dist - inner) < .95:
                color = "steel"
            elif dist > 33.8:
                color = "fern" if grain > .26 else "glass_muted"
                if t < 1.4:
                    color = "stone2"
            elif dist < inner:
                color = "moss" if dist > 9 else "plum"
            elif t < .78 or abs(t - max(0, pr/7)) < .68 or led:
                color = "steel"
            elif t < max(0, pr/7):
                color = ("glass_muted", "dew_green", "dew_lime", "dew_light")[min(3, int((1.7 if dy-dx*.25 < 5 else 0.6) + grain*2))]
                if dy > 3 and dist > 28 and abs(dx) > 10:
                    color = "ritual_red" if grain < .6 else "hot_red"
            else:
                color = ("glass_dark", "moss", "fern")[int(grain*2.4)]
                if dist > 29 and t > 4.8 and dy > -18:
                    color = ("moss", "ritual_red", "char_red")[int(grain*2.4)]
            c.dot(color, CX+dx, cy+dy)
    c.poly("hot_red", [(CX, 81), (CX+8, 96), (CX-8, 96)], "plum")
    c.line("nacho_light", [(CX-7, 95), (CX, 83), (CX+7, 95), (CX-7, 95)])
    for n in range(24):
        angle = n*pi/12
        x, y = CX+round(42*cos(angle)), cy+round(42*sin(angle))
        c.dot("stone3" if y < cy+17 else "stone2", x, y)


def sanctuary(c):
    c.rect("black", (0, 0, 255, 252))
    c.poly("vault", arch(CX, -9, 111, 96, 244))
    c.poly("stone0", arch(CX, 4, 92, 98, 238))
    c.poly("steel", arch(CX, 24, 71, 73, 235))
    c.poly("teal0", arch(CX, 40, 53, 61, 226))
    c.poly("steel", [(77, 106), (179, 106), (175, 147), (167, 174), (167, 224),
                     (88, 224), (88, 176), (79, 154)])
    c.poly("teal0", arch(CX, 98, 35, 41, 228))
    c.poly("teal1", arch(CX, 114, 24, 32, 220))
    for side, x in [(1, 25), (-1, 229)]:
        c.poly("soot", mirror([(0, 23), (21, 31), (45, 49), (56, 73), (60, 214), (0, 244)], side))
        recess(c, x, 48, 14, 32, 191)
        c.poly("ink", mirror([(0, 89), (8, 99), (10, 202), (30, 234), (0, 248)], side))
        c.poly("soot", mirror([(49, 66), (62, 57), (71, 78), (76, 214), (44, 224)], side))
        recess(c, CX-side*57, 113, 9, 23, 209)
    if c.stage >= 2:
        rng = Random(108)
        for y in range(19, 212, 7):
            for x in range(-12 + (y % 2)*7, 256, 13):
                px = x + rng.randint(0, 5)
                if not 0 <= px < W:
                    continue
                color = c.im.getpixel((px, y))
                from_color = {
                    (40, 39, 68): ("vault", "stone1"),
                    (29, 53, 76): ("steel", "teal0"),
                    (38, 74, 100): ("steel", "teal1"),
                    (32, 32, 57): ("soot", "stone0"),
                }.get(color)
                if from_color:
                    for dx in range(rng.randint(2, 9)):
                        if px+dx < W and c.im.getpixel((px+dx, y)) == color:
                            c.dot(from_color[0], px+dx, y)
                            if dx < 4 and y+1 < 211 and c.im.getpixel((px+dx, y+1)) == color:
                                c.dot(from_color[1], px+dx, y+1)
        for apex, width, height, base, shade in [
            (-11, 111, 96, "black", "stone0"),
            (0, 98, 95, "soot", "stone2"),
            (11, 85, 92, "vault", "stone3"),
            (23, 74, 76, "steel", "teal1"),
            (37, 56, 65, "steel", "teal1"),
        ]:
            vertices = arch(CX, apex, width, height, 216)
            c.line(base, vertices, 5)
            c.line(shade, arch(CX, apex+1, width-2, height, 217))
            for a, b in zip(vertices[1:-2], vertices[2:-1]):
                for frac in (.37, .76):
                    x = round(a[0]+(b[0]-a[0])*frac)
                    y = round(a[1]+(b[1]-a[1])*frac)
                    s = -1 if x < CX else 1
                    c.line(base, [(x-s*2, y+2), (x+s*2, y-2)])
        for side in (-1, 1):
            c.line("stone1", mirror([(4, 31), (23, 34), (39, 44), (49, 58)], side), 2)
            c.line("stone0", mirror([(2, 73), (16, 74), (34, 82), (44, 91)], side))
            c.line("stone2", mirror([(30, 11), (46, 19), (61, 29), (72, 41)], side))
            c.line("vault", mirror([(30, 13), (46, 21), (61, 31), (72, 43)], side), 2)
            for n in range(3):
                x = 91+n*10
                pts = mirror(arch(x, 133-4*n, 4, 13, 219), side)
                c.line("steel", pts, 2)
                c.line("teal1", mirror(arch(x+2, 134-4*n, 3, 12, 218), side))

    if c.stage >= 2:
        upper_masonry(c)
    rose_window(c)
    if c.stage >= 3:
        window_light(c)


def upper_masonry(c):
    for side in (-1, 1):
        def p(color, pts):
            c.poly(color, mirror(pts, side))

        def l(color, pts, width=1):
            c.line(color, mirror(pts, side), width)

        p("soot", [(16, 0), (49, 0), (57, 14), (67, 24), (75, 29), (67, 36),
                   (56, 29), (44, 19), (30, 13), (16, 24)])
        l("stone0", [(16, 23), (30, 12), (42, 17), (55, 27), (64, 34)])
        l("stone1", [(18, 23), (30, 14), (40, 19), (52, 28), (63, 36)])
        l("vault", [(48, 0), (53, 12), (62, 22), (73, 30)], 3)
        p("vault", [(13, 38), (20, 36), (32, 41), (42, 49), (48, 61),
                    (48, 70), (40, 68), (39, 56), (33, 49), (23, 44), (13, 47)])
        l("stone1", [(13, 39), (20, 37), (32, 42), (41, 50), (47, 61), (47, 68)])
        l("stone0", [(13, 45), (22, 42), (32, 47), (40, 55), (40, 65)])
        for y, x in [(4, 21), (13, 22), (22, 26), (30, 21), (51, 14),
                     (58, 14), (65, 14), (81, 13), (88, 15), (97, 16)]:
            l("stone0", [(x, y), (x+5, y), (x+6, y+1)])
        if side == 1:
            l("stone0", [(36, 29), (36, 43), (37, 44), (37, 87), (38, 88), (38, 92)])
            for y in range(35, 90, 4):
                l("stone2" if y % 8 == 3 else "soot", [(36, y), (37, y)])
        else:
            l("stone0", [(20, 43), (20, 68), (21, 69), (21, 102)])
            for y in range(53, 101, 5):
                l("stone2", [(20, y), (21, y)])


def window_light(c):
    # The center aisle catches lime light. Recesses and side windows keep their blue stone.
    wall = {"steel": "glass_dark", "haze": "glass_dark", "teal0": "moss",
            "teal1": "glass_dark", "teal2": "fern", "glass": "fern"}
    c.glaze([(85, 111), (104, 127), (151, 127), (169, 109),
             (185, 208), (166, 234), (91, 231), (77, 202)], wall)
    outer = {"steel": "haze", "glass_dark": "glass_haze", "moss": "glass_haze",
             "teal0": "glass_haze", "teal1": "moss", "stone0": "vault"}
    c.glaze([(100, 122), (110, 129), (108, 151), (101, 176), (93, 198),
             (72, 229), (62, 232), (73, 201), (86, 155)], outer)
    c.glaze([(155, 125), (165, 118), (171, 143), (182, 177),
             (194, 203), (204, 231), (179, 229), (164, 189), (153, 143)], outer)
    core = {"glass_haze": "moss", "glass_dark": "glass_haze", "moss": "fern",
            "teal1": "moss", "fern": "glass_muted"}
    c.glaze([(105, 125), (115, 128), (111, 152), (102, 180), (92, 202),
             (79, 222), (84, 203), (92, 171), (101, 139)], core)
    c.glaze([(154, 126), (159, 123), (168, 155), (177, 181), (190, 217),
             (177, 209), (168, 183), (161, 157)], core)
    c.glaze([(117, 127), (142, 127), (143, 143), (149, 169), (155, 202),
             (154, 227), (101, 227), (103, 209), (113, 158)],
            {"glass_dark": "glass_haze", "moss": "glass_haze"})
    c.glaze([(116, 133), (137, 131), (139, 160), (142, 181),
             (149, 222), (111, 222), (113, 194), (117, 161)],
            {"glass_haze": "glass_dark", "moss": "glass_dark"})
    c.glaze([(91, 208), (115, 205), (139, 204), (164, 208), (175, 222),
             (162, 231), (92, 231), (79, 223)],
            {"glass_dark": "oxblood", "glass_haze": "oxblood", "moss": "ember0",
             "fern": "char_red"})

    # Sparse grains of dust mark the beams without raising the black level around them.
    rng = Random(40)
    for _ in range(150):
        y = rng.randrange(127, 222)
        side = rng.choice((-1, 1))
        x = round(CX + side*(20 + (y-127)*.40 + rng.randrange(-5, 6)))
        color = "glass_muted" if rng.random() < .14 and y < 181 else "fern"
        c.dot(color, x, y)


def fire_light(c):
    # Red light catches the stone by each brazier and the steps around the altar.
    ramp = {"plum": "oxblood", "vault": "oxblood", "stone0": "oxblood",
            "soot": "ember0", "stone1": "char_red", "stone2": "ember2",
            "stone3": "red1", "wine": "char_red", "red0": "ritual_red", "copper": "hot_red"}
    for side in (1, -1):
        c.glaze(mirror([(20, 180), (37, 177), (47, 183), (53, 203), (62, 218),
                        (82, 233), (70, 246), (52, 242), (27, 238), (14, 216)], side), ramp)
    c.glaze([(99, 222), (143, 220), (163, 233), (171, 251), (164, 260),
             (146, 273), (121, 270), (99, 255), (86, 235)], ramp)


def ritual_banners(c):
    for side in (1, -1):
        def p(color, pts):
            c.poly(color, mirror(pts, side))

        def l(color, pts):
            c.line(color, mirror(pts, side))

        l("stone2", [(66, 142), (85, 142)])
        p("oxblood", [(69, 143), (82, 143), (81, 176), (83, 189),
                       (77, 186), (75, 191), (70, 186), (69, 173)])
        p("char_red", [(70, 144), (74, 144), (73, 172), (74, 183),
                        (71, 184), (70, 177)])
        l("ritual_red", [(81, 145), (80, 172), (81, 185)])
        l("hot_red", [(70, 145), (70, 154)])
        l("copper", [(72, 167), (76, 156), (80, 168), (72, 167)])
        l("nacho", [(74, 166), (76, 159), (78, 166), (74, 166)])
        if c.stage >= 3:
            l("orange", [(73, 173), (76, 173)])
            l("glass_muted", [(80, 144), (81, 144)])
            l("char_red", [(75, 179), (75, 185)])


def ritual_marks(c):
    # The inlaid design follows the horizontal surfaces of the stairs.
    c.line("hot_red", [(126, 250), (128, 250), (136, 259)])
    c.line("hot_red", [(126, 250), (118, 259)])
    c.line("hot_red", [(118, 260), (137, 260)])
    c.line("clay", [(120, 260), (125, 255), (128, 255), (134, 260)])
    c.line("orange", [(125, 259), (127, 257), (129, 259)])
    c.line("copper", [(110, 260), (106, 263), (117, 266), (137, 266), (149, 263), (145, 260)])
    for x, y in [(107, 263), (114, 265), (124, 266), (138, 266), (146, 263), (142, 260)]:
        c.dot("nacho", x, y)


def column(c, x, top, bottom, w, side):
    c.poly("soot", [(x-w-4, top), (x+w+3, top), (x+w+3, top+17),
                    (x+w, top+23), (x+w, bottom-16), (x+w+5, bottom),
                    (x-w-6, bottom), (x-w, bottom-13), (x-w, top+22)])
    c.rect("stone0", (x-w+2, top+22, x+w-2, bottom-13))
    c.rect("stone1", (x-4, top+24, x+4, bottom-16))
    if c.stage < 2:
        return
    for dx, color in [(-w, "ink"), (-w+2, "stone1"), (-5, "vault"), (-3, "stone2"),
                      (3, "stone0"), (5, "stone2"), (w-2, "vault")]:
        c.line(color, [(x+dx*side, top+24), (x+dx*side, bottom-13)])
    for i, y in enumerate(range(top+33, bottom-15, 14)):
        c.line("soot", [(x-w, y), (x+w, y)])
        c.line("stone2", [(x-2, y+1), (x+4, y+1)])
        c.line("vault", [(x-4*side, y+4), (x-4*side, y+10)])
        c.line("slate", [(x+side*3, y+2), (x+side*3, y+5+(i*3)%6)])
        if i % 3 != 1:
            p = x+side*(5+i%3)
            c.line("soot", [(p, y+1), (p, y+3), (p-side, y+4), (p-side, y+6)])
        if c.stage >= 3:
            c.line("teal0" if i < 5 else "copper", [(x-side*5, y+2), (x-side*5, y+4)])
            c.dot("stone3", x+side*(i%4-1), y+2)
    for y, extend, color in [(top+13, 4, "stone2"), (top+16, 4, "vault"),
                             (top+19, 3, "stone3"), (top+22, 1, "stone1"),
                             (bottom-14, 1, "stone2"), (bottom-9, 4, "stone1"),
                             (bottom-4, 5, "stone2")]:
        c.line(color, [(x-w-extend, y), (x+w+extend, y)])


def gargoyle(c, side):
    def p(color, pts, outline=None):
        c.poly(color, mirror(pts, side), outline)

    def l(color, pts):
        c.line(color, mirror(pts, side))

    p("soot", [(50, 128), (43, 116), (34, 111), (25, 110), (18, 104), (19, 119),
                (24, 120), (22, 129), (31, 127), (30, 138), (40, 132), (48, 150),
                (48, 159), (63, 161), (67, 156), (62, 145), (67, 139), (69, 128),
                (63, 124), (61, 116), (56, 110), (52, 109), (57, 116), (56, 124)])
    p("stone0", [(55, 126), (59, 122), (58, 118), (56, 114), (61, 117), (63, 124),
                  (65, 126), (71, 126), (71, 131), (66, 136), (66, 142), (59, 143),
                  (62, 151), (64, 155), (58, 157), (52, 154), (50, 144), (47, 135)])
    if c.stage >= 2:
        p("vault", [(20, 109), (27, 115), (35, 116), (44, 121), (48, 136),
                    (40, 130), (33, 132), (36, 124), (25, 126), (27, 118), (22, 118)])
        l("stone2", [(21, 111), (28, 115), (35, 115), (42, 119), (47, 126)])
        l("stone1", [(27, 118), (35, 120), (42, 125), (45, 132)])
        l("stone1", [(33, 127), (39, 126), (43, 129)])
        p("stone2", [(51, 134), (54, 127), (58, 125), (63, 126), (66, 129),
                      (71, 129), (68, 132), (59, 134), (56, 144), (52, 149)])
        l("glass_muted", [(55, 113), (59, 115), (61, 119), (62, 123)])
        l("soot", [(57, 134), (62, 137), (66, 135), (68, 135)])
        l("stone3", [(57, 153), (60, 152), (64, 154), (61, 155)])
        l("red2", [(61, 128), (64, 129)])
    if c.stage >= 3:
        l("hot_red", [(62, 128), (64, 129)])
        l("nacho", [(63, 129), (64, 129)])
        l("fern", [(65, 130), (69, 129)])
        l("red0", [(59, 150), (61, 151), (63, 152)])
        l("stone2", [(44, 151), (68, 151)])
        l("soot", [(43, 157), (67, 157)])


def altar_floor(c):
    c.poly("soot", [(0, 236), (74, 226), (181, 226), (255, 236), (255, 319), (0, 319)])
    c.poly("plum", [(76, 235), (177, 235), (238, 319), (16, 319)])
    c.poly("wine", [(101, 242), (154, 242), (185, 319), (70, 319)])
    for y, left, right, depth in [(240, 68, 188, 7), (249, 55, 201, 8),
                                   (260, 42, 213, 9), (273, 27, 228, 10),
                                   (288, 11, 245, 11)]:
        c.poly("stone1", [(left+8, y-depth//2), (right-8, y-depth//2), (right, y),
                           (right, y+depth), (left, y+depth), (left, y)])
        c.rect("vault", (left, y+1, right, y+depth))
        c.poly("red0", [(CX-round((y-180)*.49), y-depth//2), (CX+round((y-180)*.49), y-depth//2),
                         (CX+round((y-180)*.56), y+depth), (CX-round((y-180)*.56), y+depth)])
        if c.stage >= 2:
            c.line("stone3", [(left+1, y), (right-1, y)])
            c.line("soot", [(left, y+depth), (right, y+depth)])
            c.line("red1", [(CX-(y-180)//2, y), (CX+(y-180)//2, y)])
            c.line("wine", [(CX-(y-180)//2, y+depth-1), (CX+(y-180)//2, y+depth-1)])
            for x in range(left+11+y%7, right-4, 19):
                if abs(x-CX) > (y-180)*.57:
                    c.line("soot", [(x, y+1), (x-2, y+4), (x-2, y+depth-1)])
                    c.line("stone2", [(x+2, y+1), (x+1, y+5), (x+1, y+depth-2)])
    if c.stage >= 2:
        c.poly("red0", [(72, 300), (181, 300), (195, 319), (58, 319)])
        for side in (-1, 1):
            c.line("red1", mirror([(77, 300), (63, 319)], side), 2)
            c.line("copper", mirror([(82, 301), (71, 319)], side))
        c.poly("wine", [(127, 302), (157, 316), (127, 317), (97, 316)], "red1")
        c.poly("copper", [(127, 305), (146, 314), (108, 314)])
        c.poly("wine", [(127, 308), (137, 313), (117, 313)])


def floor_detail(c):
    ramp = {"vault": "plum", "stone1": "brown", "stone2": "copper", "stone3": "clay",
            "red0": "ember2", "red1": "red2"}
    c.glaze([(111, 229), (147, 229), (150, 242), (171, 245), (176, 252),
             (170, 263), (157, 267), (138, 269), (130, 278), (109, 277),
             (90, 270), (81, 262), (83, 251), (104, 246)], ramp)
    for side in (-1, 1):
        c.glaze(mirror([(25, 225), (44, 224), (58, 230), (68, 237), (67, 251),
                        (57, 255), (42, 253), (33, 247), (21, 246)], side), ramp)

    rng = Random(137)
    tones = {RGB["red0"]: ("fabric", "ember2", "wool"),
             RGB["ember2"]: ("red0", "red1", "fabric"), RGB["wine"]: ("fabric", "plum", "wool"),
             RGB["vault"]: ("mortar", "stone1", "soot"), RGB["stone1"]: ("mortar", "stone2", "vault"),
             RGB["plum"]: ("ember0", "vault", "wine"), RGB["brown"]: ("copper", "brown", "wine")}
    for y in range(239, H):
        for x in range(5, W-5):
            pair = tones.get(c.im.getpixel((x, y)))
            if pair and rng.random() < .038:
                color = rng.choice(pair)
                c.dot(color, x, y)
                if rng.random() > .30 and c.im.getpixel((x+1, y)) in tones:
                    c.dot(color, x+1, y)
    for y, left, right, depth in [(240, 68, 188, 7), (249, 55, 201, 8),
                                   (260, 42, 213, 9), (273, 27, 228, 10),
                                   (288, 11, 245, 11)]:
        edge = (y-180)*.53
        for side in (-1, 1):
            x = CX+int(side*edge)
            c.line("copper", [(x, y+1), (x-side, y+4), (x+side, y+depth-2)])
            c.line("ember2", [(x+side*4, y+1), (x+side*5, y+depth-1)])
            for dx in (14, 27, 49):
                joint = (left+dx) if side == -1 else (right-dx-4)
                if abs(joint-CX) > edge+4:
                    c.line("vault", [(joint, y), (joint+3, y)])
                    c.line("slate", [(joint-2, y+4), (joint+3, y+4), (joint+4, y+5)])
        pitch = 11 + depth
        for x in range(CX-int(edge)+pitch//2, CX+int(edge)-6, pitch):
            c.line("copper", [(x-3, y+4), (x, y+2), (x+3, y+4), (x, y+6), (x-3, y+4)])
            c.dot("red1", x, y+4)


POPE_FACE = (
    ".bbbbbbb..",
    "bbbaaaaah.",
    "bbaaaahhh.",
    "baiaaiaah.",
    "baaamaash.",
    ".bammasss.",
    ".baaasass.",
    "..baaash..",
    "...bbbb...",
)


def priest(c):
    # One continuous cassock falls from the shoulder line to the landing.
    c.poly("plum", [(118, 188), (123, 185), (132, 185), (138, 189),
                    (139, 207), (137, 218), (143, 241), (139, 244),
                    (115, 244), (113, 242), (118, 218), (117, 207)], "soot")
    c.poly("wine", [(122, 187), (129, 187), (135, 190), (135, 210), (133, 222),
                    (137, 242), (119, 242), (122, 221), (121, 199)])
    # The upper arm rises out from the shoulder. The forearm lifts at the elbow.
    c.poly("stone3", [(121, 186), (119, 191), (116, 192),
                      (105, 184), (97, 171), (101, 169), (109, 180)], "soot")
    c.poly("violet", [(136, 189), (140, 191), (143, 203), (142, 208),
                      (138, 212), (133, 212), (132, 208), (136, 205)], "soot")
    c.poly("soot", [(97, 174), (95, 170), (100, 167), (102, 170), (101, 172)])
    c.poly("skin1", [(96, 170), (94, 167), (94, 164), (97, 162),
                     (101, 162), (103, 165), (102, 168), (99, 171)], "brown")
    dew_bottle(c, 97, 151)
    c.line("skin2", [(101, 164), (100, 166), (100, 168)])
    c.dot("skin2", 95, 165)
    c.poly("skin1", [(139, 208), (141, 209), (140, 211), (137, 213),
                     (133, 213), (132, 212), (134, 210)], "brown")

    # A split, tapered mitre seats across the forehead on an embroidered band.
    c.rect("skin0", (125, 182, 130, 187))
    face_colors = {"b": "brown", "a": "skin0", "i": "black",
                   "m": "skin1", "s": "skin2", "h": "oxblood"}
    for dy, row in enumerate(POPE_FACE):
        for dx, mark in enumerate(row):
            if mark != ".":
                c.dot(face_colors[mark], 122+dx, 176+dy)
    c.poly("amber", [(120, 176), (120, 170), (122, 165), (126, 157),
                      (127, 157), (131, 163), (135, 168), (136, 175),
                      (133, 178), (123, 177)], "brown")
    c.poly("brown", [(120, 174), (124, 175), (132, 174), (135, 173),
                      (135, 176), (133, 178), (124, 177), (120, 176)])
    if c.stage < 2:
        return

    # The lime window rims the upper folds. The altar lights the fabric from below.
    c.poly("oxblood", [(127, 190), (133, 191), (135, 204), (131, 220),
                    (134, 239), (129, 242), (123, 241), (125, 220)])
    c.poly("char_red", [(118, 194), (124, 192), (123, 210), (120, 224),
                    (118, 240), (114, 241), (118, 218)])
    c.line("hot_red", [(116, 236), (122, 209), (123, 201)])
    c.line("moss", [(136, 218), (137, 226), (141, 240)])
    c.line("copper", [(118, 240), (123, 242), (134, 242)])
    c.poly("char_red", [(118, 189), (120, 187), (124, 185), (132, 185),
                    (137, 188), (141, 192), (137, 197), (133, 193),
                    (128, 191), (123, 192), (119, 196), (116, 195)])
    c.line("dew_green", [(130, 185), (135, 187), (138, 190)])
    c.line("hot_red", [(117, 195), (120, 194), (124, 191)])
    c.rect("clay", (125, 186, 130, 187))
    c.line("brown", [(122, 190), (122, 207), (120, 237)], 3)
    c.line("nacho", [(122, 191), (121, 209), (119, 238)])
    c.line("brown", [(133, 190), (132, 205), (136, 239)], 3)
    c.line("orange", [(133, 191), (132, 207), (136, 238)])
    c.poly("plum", [(128, 192), (132, 198), (124, 198)])
    c.line("nacho_light", [(125, 197), (128, 193), (131, 197), (125, 197)])
    c.dot("dew_lime", 128, 196)

    c.line("glass_muted", [(101, 172), (108, 182), (116, 186)])
    c.line("copper", [(99, 176), (105, 184), (115, 191)])
    c.dot("linen_shadow", 105, 182)
    c.poly("stone3", [(137, 194), (140, 193), (142, 203), (141, 206), (138, 204)])
    c.line("fern", [(140, 194), (142, 202)])
    c.line("clay", [(141, 205), (139, 208), (136, 209)])
    c.line("skin2", [(134, 212), (137, 211), (139, 210)])

    c.poly("clay", [(121, 172), (124, 167), (127, 159), (131, 164),
                      (134, 168), (134, 174), (131, 176), (123, 175)])
    c.poly("nacho_light", [(122, 171), (124, 165), (126, 159), (128, 161),
                    (128, 165), (125, 169), (124, 173), (122, 174)])
    c.poly("nacho", [(126, 173), (130, 167), (131, 164), (134, 169),
                      (134, 172), (131, 174)])
    c.line("clay", [(124, 174), (127, 170), (130, 165)])
    c.line("yellow0", [(121, 175), (125, 176), (130, 176), (134, 174)])
    c.line("dew_lime", [(127, 158), (129, 161)])
    c.line("dew_green", [(134, 169), (135, 171), (135, 174)])
    c.dot("dew_green", 132, 180)
    c.line("clay", [(124, 181), (125, 183), (127, 183)])
    c.dot("copper", 129, 181)
    c.line("brown", [(123, 181), (124, 183)])
    if c.stage >= 3:
        for x, y, tone in [(123, 170, "clay"), (125, 165, "orange"), (132, 170, "orange"),
                           (122, 173, "amber"), (127, 172, "clay"), (130, 173, "light")]:
            c.dot(tone, x, y)
        for x, y in [(121, 198), (121, 205), (133, 198), (132, 205)]:
            c.line("amber", [(x, y), (x, y+1)])
        c.dot("nacho_light", 128, 193)
        c.dot("skin3", 135, 211)
        c.dot("dew_green", 101, 170)
        c.line("ritual_red", [(125, 184), (128, 185), (130, 184)])


def dew_bottle(c, x, y):
    c.rect("linen0", (x-1, y, x+1, y+1))
    c.poly("green0", [(x-1, y+2), (x+1, y+2), (x+1, y+4), (x+3, y+6),
                      (x+3, y+12), (x+2, y+14), (x-2, y+14),
                      (x-3, y+12), (x-3, y+6), (x-1, y+4)])
    c.rect("dew_green", (x-2, y+6, x+2, y+12))
    c.line("hot_red", [(x-2, y+11), (x+2, y+8)], 2)
    if c.stage >= 2:
        c.line("dew_lime", [(x-1, y+5), (x-2, y+7)])
        c.line("linen2", [(x-2, y+10), (x+1, y+8)])
        c.dot("dew_lime", x, y+13)
        c.dot("dew_light", x+1, y)


def canopy(c):
    sanctuary(c)
    for x, side in [(46, -1), (208, 1)]:
        column(c, x, 73, 233, 10, side)
    if c.stage >= 2:
        ritual_banners(c)
    for side in (1, -1):
        gargoyle(c, side)
    for side in (-1, 1):
        c.poly("ink", mirror([(0, 0), (18, 0), (14, 23), (10, 34), (8, 170),
                              (11, 215), (22, 239), (0, 252)], side))
        if c.stage >= 2:
            c.line("stone0", mirror([(19, 0), (15, 23), (10, 36), (9, 171),
                                      (12, 214), (23, 238)], side), 2)
            c.line("vault", mirror([(11, 42), (12, 132), (12, 177), (15, 211)], side))


def candle(c, x, y, height, style=0):
    c.rect("brown", (x-2, y+height-1, x+2, y+height+1))
    c.line("copper", [(x, y), (x, y+height)], 2)
    c.poly("orange", [(x-2, y-2), (x-1, y-5), (x+style, y-8),
                      (x+2, y-4), (x+1, y-2)])
    if c.stage >= 2:
        c.line("amber", [(x, y+1), (x, y+height-2)])
        c.line("light", [(x, y-2), (x+style, y-5)])
    if c.stage >= 3:
        c.dot("flame", x, y-3)


def incense(c):
    for side in (-1, 1):
        def p(color, pts, outline=None):
            c.poly(color, mirror(pts, side), outline)

        def l(color, pts):
            c.line(color, mirror(pts, side))

        p("plum", [(16, 204), (50, 204), (47, 209), (39, 211), (36, 220),
                   (36, 240), (41, 245), (24, 245), (30, 240), (30, 218),
                   (27, 212), (22, 211)], "ink")
        p("ritual_red", [(20, 204), (23, 200), (21, 198), (25, 196), (25, 190),
                   (28, 194), (32, 186), (33, 181), (37, 190), (37, 194),
                   (41, 190), (40, 196), (45, 200), (44, 204)])
        if c.stage >= 2:
            p("hot_red", [(24, 204), (27, 199), (29, 200), (31, 195), (33, 194),
                       (34, 188), (36, 193), (35, 199), (41, 197), (39, 203)])
            p("nacho_light", [(29, 204), (32, 200), (35, 196), (36, 201), (38, 199), (39, 204)])
            p("copper", [(19, 205), (22, 207), (28, 208), (29, 212), (34, 214),
                         (32, 219), (32, 241), (29, 243), (26, 243), (30, 238),
                         (30, 217), (27, 212), (21, 210)])
            l("orange", [(22, 208), (31, 209), (39, 207), (46, 206)])
            l("wine", [(33, 239), (34, 220), (36, 214), (40, 212)])
            l("red0", [(28, 245), (37, 245)])
        if c.stage >= 3:
            l("flame", [(31, 202), (34, 201), (34, 199)])
            l("hot_red", [(20, 205), (27, 205), (34, 206), (44, 204)])
            for x, y in [(24, 186), (28, 178), (40, 183), (43, 174), (32, 175),
                         (34, 163), (48, 167), (18, 191), (39, 188)]:
                c.dot("red2" if y > 178 else "red0", *mirror([(x, y)], side)[0])


def offering(c, x, y, base="red0", face="red1"):
    c.rect(base, (x-3, y, x+3, y+7))
    c.rect(face, (x-2, y+1, x+2, y+6))
    c.line("plum", [(x-2, y+4), (x+2, y+3)])
    if c.stage >= 2:
        c.line("linen1", [(x-1, y+3), (x+1, y+3)])
        c.dot("orange", x+1, y+5)


def lectern(c):
    c.oval("soot", (108, 241, 147, 246))
    c.poly("plum", [(116, 240), (139, 240), (143, 243), (140, 245),
                    (115, 245), (112, 243)], "ink")
    c.poly("brown", [(118, 222), (137, 222), (137, 232), (136, 241),
                     (117, 241), (116, 230)], "ink")
    c.poly("brown", [(113, 212), (142, 212), (148, 218), (146, 223),
                     (109, 223), (107, 218)], "ink")
    if c.stage >= 2:
        c.poly("copper", [(113, 213), (141, 213), (145, 217), (142, 220),
                          (112, 220), (109, 217)])
        c.line("hot_red", [(110, 219), (113, 221), (143, 221), (146, 219)])
        c.line("copper", [(118, 224), (119, 240), (116, 242)])
        c.line("plum", [(136, 224), (134, 240), (137, 242)], 2)
        c.line("copper", [(115, 243), (140, 243)])
        c.poly("ritual_red", [(123, 224), (132, 224), (132, 236), (128, 240), (123, 237)])
        c.poly("nacho", [(127, 226), (132, 235), (122, 235)], "brown")
        c.line("gold", [(124, 234), (127, 227), (130, 232)])
    offering(c, 117, 207)
    offering(c, 126, 205, "blue1", "blue2")
    if c.stage >= 3:
        c.line("orange", [(111, 219), (116, 220), (123, 220)])
        c.poly("gold", [(134, 215), (139, 215), (136, 218)])
        c.dot("dew_lime", 127, 232)
        c.dot("nacho_light", 124, 236)
        c.dot("nacho_light", 130, 236)


def votives(c):
    for x, y, count in [(86, 232, 4), (165, 236, 3)]:
        c.poly("brown", [(x-7, y+2), (x+7, y+2), (x+5, y+5), (x-7, y+5)], "plum")
        for i in range(count):
            candle(c, x-6+4*i, y-2-(i*3)%8, 5+(i*3)%8, (i % 3)-1)
    for x, y, h in [(67, 230, 9), (183, 228, 6), (187, 235, 10)]:
        candle(c, x, y, h)


def standing_cultist(c, x, y, side, carrying_censer):
    def pose(points):
        return [(x+side*px, y+py) for px, py in points]

    def p(color, points, outline=None):
        c.poly(color, pose(points), outline)

    def l(color, points):
        c.line(color, pose(points))

    p("black", [(-13, 79), (9, 77), (17, 80), (13, 82), (-15, 82), (-19, 80)])
    p("black", [(-8, 55), (1, 55), (0, 77), (-2, 80), (-10, 80),
                (-12, 78), (-9, 75)], "ink")
    p("black", [(1, 55), (8, 54), (8, 74), (11, 76), (11, 79), (3, 79),
                (0, 77), (2, 71)], "ink")
    p("soot", [(-4, 15), (3, 15), (10, 21), (11, 33), (8, 43),
               (9, 54), (12, 67), (6, 72), (0, 69), (-7, 73), (-14, 71),
               (-10, 57), (-10, 46), (-13, 29), (-12, 22)], "black")
    p("plum", [(-8, 20), (-3, 17), (4, 19), (9, 23), (8, 34), (5, 44),
               (6, 54), (9, 65), (5, 68), (1, 64), (-8, 70), (-11, 68),
               (-8, 52), (-8, 43), (-11, 28)])
    p("oxblood", [(-8, 16), (-9, 10), (-7, 5), (-1, 0), (3, 1), (8, 5),
                  (10, 10), (8, 13), (8, 18), (5, 21), (-3, 20)], "black")
    if carrying_censer:
        p("wine", [(4, 23), (9, 22), (12, 27), (10, 40), (16, 45),
                   (14, 49), (6, 44), (4, 39)], "ink")
        p("skin0", [(14, 44), (17, 44), (19, 46), (18, 49), (15, 49), (13, 47)])
        l("copper", [(17, 48), (18, 54), (21, 58)])
        l("brown", [(17, 48), (14, 55), (15, 58)])
        p("brown", [(13, 58), (23, 58), (21, 62), (17, 64), (15, 62)])
        l("orange", [(14, 58), (22, 58)])
    else:
        p("wine", [(4, 22), (9, 23), (12, 28), (10, 38), (15, 36),
                   (19, 30), (21, 33), (18, 40), (12, 44), (7, 43),
                   (5, 38)], "ink")
        p("skin0", [(18, 32), (18, 28), (20, 25), (21, 26), (22, 30),
                    (21, 33), (19, 34)])
    if c.stage < 2:
        return

    p("stone0", [(-9, 25), (-5, 23), (-2, 26), (-2, 36), (-5, 46),
                 (-4, 52), (-6, 64), (-10, 68), (-8, 56), (-9, 44)])
    p("wine", [(-5, 22), (-1, 23), (4, 21), (6, 24), (4, 30), (0, 29), (-6, 28)])
    p("char_red", [(-3, 1), (3, 2), (7, 6), (8, 10), (6, 13), (5, 18),
                   (2, 19), (0, 16), (3, 10), (2, 5)])
    p("soot", [(7, 8), (9, 10), (7, 13), (7, 16), (4, 17), (5, 13)])
    l("ritual_red", [(3, 2), (7, 6), (9, 10)])
    l("ember2", [(3, 20), (6, 19), (9, 23)])
    l("ember1", [(0, 28), (0, 38), (-2, 46), (0, 55), (2, 63)])
    l("red0", [(-8, 51), (-9, 59), (-12, 66)])
    l("stone2", [(-11, 70), (-7, 71), (0, 67), (5, 70), (10, 67)])
    l("stone1", [(-9, 77), (-7, 76), (-3, 77)])
    l("stone1", [(2, 76), (6, 75), (9, 76)])
    if carrying_censer:
        l("ember2", [(9, 25), (10, 33), (8, 39), (14, 45)])
        l("clay", [(16, 46), (18, 47)])
    else:
        l("ember2", [(10, 27), (10, 33), (9, 39), (12, 40)])
        l("copper", [(14, 38), (17, 36), (19, 33)])
        l("skin1", [(20, 28), (20, 31)])
    if c.stage >= 3:
        l("copper", [(6, 5), (8, 7)])
        l("stone1", [(-7, 32), (-8, 42), (-6, 46)])
        l("copper", [(7, 23), (8, 25)])
        l("brown", [(-6, 29), (-2, 31), (1, 30)])
        l("orange", [(-4, 27), (-1, 24), (2, 27), (-4, 27)])
        if carrying_censer:
            l("ember2", [(18, 55), (17, 52), (18, 50)])
            l("nacho_light", [(17, 58), (20, 58)])
            l("clay", [(18, 51), (19, 54)])
            l("ember2", [(10, 60), (11, 62)])


def kneeling_cultist(c, x, y, side, raised_hands):
    def pose(points):
        return [(x+side*px, y+py) for px, py in points]

    def p(color, points, outline=None):
        c.poly(color, pose(points), outline)

    def l(color, points):
        c.line(color, pose(points))

    p("black", [(-14, 43), (-4, 42), (13, 42), (18, 44), (12, 46), (-12, 46)])
    # The lower leg lies on the landing and the forward knee supports the lifted torso.
    p("soot", [(-6, 32), (3, 32), (6, 37), (3, 42), (-8, 43),
               (-12, 45), (-15, 43), (-13, 40), (-7, 39)], "ink")
    p("plum", [(-2, 30), (6, 29), (12, 31), (15, 35), (14, 39), (11, 42),
               (5, 44), (2, 43), (5, 39), (6, 35), (0, 39), (-5, 37)], "ink")
    p("soot", [(-4, 12), (3, 12), (8, 16), (9, 24), (7, 30),
               (5, 34), (-1, 36), (-6, 36), (-9, 33), (-7, 25),
               (-7, 18)], "ink")
    p("oxblood", [(-5, 11), (-5, 5), (0, 0), (3, 0), (8, 5),
                  (9, 8), (6, 10), (6, 13), (1, 16), (-3, 14)], "ink")
    if raised_hands:
        p("wine", [(4, 16), (8, 16), (10, 22), (13, 19), (16, 14),
                   (19, 15), (18, 20), (15, 26), (10, 28), (6, 25)], "ink")
        p("skin0", [(16, 15), (16, 12), (18, 9), (20, 10), (20, 13), (18, 16)])
    else:
        p("wine", [(4, 16), (8, 16), (9, 23), (12, 27), (15, 28),
                   (14, 31), (9, 29), (5, 24)], "ink")
        p("skin0", [(13, 28), (17, 28), (18, 30), (15, 32), (12, 31)])
    if c.stage < 2:
        return

    p("plum", [(-5, 18), (0, 16), (4, 18), (4, 25), (2, 29),
               (3, 32), (-2, 34), (-6, 33), (-4, 25)])
    l("ember2", [(1, 1), (5, 3), (8, 7)])
    l("red0", [(1, 15), (6, 13), (8, 17)])
    l("stone2", [(-6, 33), (-3, 35), (2, 35), (6, 33)])
    l("ember1", [(7, 32), (11, 32), (14, 35), (13, 38)])
    l("stone2", [(-13, 43), (-8, 41), (-3, 41)])
    l("ember0", [(-5, 38), (0, 37), (3, 35)])
    l("stone2", [(5, 42), (9, 41), (11, 40)])
    if c.stage >= 3:
        l("copper", [(5, 4), (7, 6)])
        l("copper", [(11, 33), (13, 35)])
        l("stone1", [(-11, 44), (-7, 43)])
        if raised_hands:
            l("ember2", [(11, 27), (15, 24), (17, 20)])
            l("skin1", [(17, 13), (18, 11)])
        else:
            l("ember2", [(7, 20), (9, 25), (12, 27)])
            l("skin1", [(14, 29), (16, 29)])


def congregation(c):
    kneeling_cultist(c, 75, 238, 1, True)
    kneeling_cultist(c, 181, 241, -1, False)
    standing_cultist(c, 42, 225, 1, False)
    standing_cultist(c, 215, 228, -1, True)


def motes(c):
    for x, y, color in [(19, 160, "teal1"), (34, 185, "orange"), (43, 190, "rose"),
                        (23, 179, "rose"), (53, 181, "red2"), (56, 211, "red1"),
                        (65, 219, "orange"), (70, 229, "red1"), (77, 238, "rose"),
                        (80, 205, "gold"), (87, 187, "teal2"), (93, 179, "teal2"),
                        (115, 207, "amber"), (146, 191, "red2"), (156, 210, "rose"),
                        (164, 220, "gold"), (185, 237, "rose"), (191, 215, "orange"),
                        (215, 180, "red2"), (219, 195, "gold"), (231, 189, "rose"),
                        (241, 176, "red0"), (226, 178, "red1"), (224, 169, "red0"),
                        (149, 141, "teal2"), (80, 155, "teal2"), (180, 111, "teal2")]:
        c.dot(color, x, y)


def draw(stage):
    c = Canvas(stage)
    canopy(c)
    altar_floor(c)
    if stage >= 3:
        floor_detail(c)
        shadow = {"ember2": "red0", "red2": "red0", "red1": "wine",
                  "red0": "wine", "copper": "red0", "fabric": "wool"}
        c.glaze([(114, 241), (139, 241), (134, 252), (129, 257),
                 (111, 260), (105, 257)], shadow)
    if stage >= 3:
        fire_light(c)
        ritual_marks(c)
    incense(c)
    votives(c)
    priest(c)
    lectern(c)
    if stage >= 3:
        motes(c)
    congregation(c)
    return c.im


def silhouette():
    c = Canvas(0)
    c.poly("vault", arch(CX, 4, 92, 98, 238))
    c.poly("stone1", arch(CX, 24, 71, 73, 235))
    c.oval("stone3", (87, 50, 167, 130))
    altar_floor(c)
    for x, side in [(46, -1), (208, 1)]:
        column(c, x, 73, 233, 10, side)
    for side in (1, -1):
        gargoyle(c, side)
    incense(c)
    figure = Canvas(0)
    priest(figure)
    for y in range(151, 245):
        for x in range(91, 144):
            if figure.im.getpixel((x, y)) != RGB["ink"]:
                c.dot("linen0", x, y)
    lectern(c)
    votives(c)
    congregation(c)
    return c.im


def main():
    steps = CASE / "build" / "steps"
    steps.mkdir(parents=True, exist_ok=True)
    passes = [(silhouette(), "01_silhouette.png"), (draw(1), "02_blockin.png")]
    if "--layout" not in sys.argv:
        passes.extend([(draw(2), "03_shading.png"), (draw(3), "04_cleanup.png")])
    for art, name in passes:
        art.save(steps / name)


if __name__ == "__main__":
    main()
