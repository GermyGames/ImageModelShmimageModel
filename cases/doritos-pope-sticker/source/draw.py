"""Hand-drawn pixel geometry for the Doritos Pope sticker."""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


SIZE = (176, 164)
PALETTE = {
    "backdrop": "#9298b0", "paper": "#fff9f5", "ink": "#281c2a",
    "aubergine": "#452334", "plum": "#65283f", "wine": "#84223e",
    "crimson": "#b92646", "rose": "#df4262", "pink": "#ff7684",
    "vest_dark": "#3f2130", "vest_red": "#7b272d", "gold_dark": "#895032",
    "gold_mid": "#b97937", "gold": "#e5ad50", "gold_light": "#ffe095",
    "orange": "#dc8233", "chip": "#f3ac45", "chip_light": "#ffd363",
    "lemon": "#ffd54b", "lemon_light": "#fff1a0",
    "sleeve_dark": "#67627f", "sleeve_mid": "#9a95b1", "sleeve_lit": "#cfcce2",
    "linen": "#f6ecf2", "cuff": "#272735", "cuff_light": "#49475f",
    "skin_dark": "#8c4c58", "skin_shade": "#bc6965", "skin_mid": "#df8d78",
    "skin": "#f5b19a", "skin_light": "#ffd7ba",
    "hair": "#512b37", "hair_light": "#75404a",
    "blue_dark": "#183251", "blue": "#245c92", "blue_mid": "#378bb2",
    "green_dark": "#194135", "green": "#286b43",
    "green_mid": "#61a73d", "green_light": "#a2d94b", "mint": "#d8ee8b",
}

# Each mark is placed directly on the native grid. Levels record the build passes.
class Canvas:
    def __init__(self, level):
        self.level = level
        self.image = Image.new("RGBA", SIZE)
        self.pen = ImageDraw.Draw(self.image)

    def shape(self, fill, points, outline=None, level=1):
        if level <= self.level:
            self.pen.polygon(points, PALETTE[fill], PALETTE[outline] if outline else None)

    def line(self, fill, points, width=1, level=2):
        if level <= self.level:
            self.pen.line(points, PALETTE[fill], width)

    def box(self, fill, coords, level=3):
        if level <= self.level:
            self.pen.rectangle(coords, PALETTE[fill])

    def finish(self):
        sticker = self.image.getchannel("A").filter(ImageFilter.MaxFilter(5))
        backing = Image.new("RGBA", SIZE, PALETTE["paper"])
        backing.putalpha(sticker)
        bg = Image.new("RGBA", SIZE, PALETTE["backdrop"])
        bg.alpha_composite(backing)
        bg.alpha_composite(self.image)
        return bg


def bottle_and_hand(c, x, y, right=False):
    def shape(fill, points, outline=None, level=1, reflect=False):
        sign = -1 if right and reflect else 1
        c.shape(fill, [(x + sign * dx, y + dy) for dx, dy in points], outline, level)

    def line(fill, points, level=3, reflect=False):
        sign = -1 if right and reflect else 1
        c.line(fill, [(x + sign * dx, y + dy) for dx, dy in points], level=level)

    shape("skin_mid", [(-8, 17), (-5, 16), (-2, 18), (0, 23), (6, 24), (9, 18),
                       (12, 17), (14, 20), (13, 25), (11, 29), (8, 34), (6, 42),
                       (-2, 43), (-6, 39), (-7, 34), (-10, 29), (-10, 23)], "ink", reflect=True)
    shape("skin_shade", [(-9, 28), (-5, 31), (1, 34), (7, 32), (6, 38), (5, 42),
                         (-2, 42), (-5, 38), (-6, 34)], level=2, reflect=True)
    shape("skin", [(-4, 31), (1, 32), (6, 30), (8, 29), (6, 33), (3, 37),
                   (1, 40), (-2, 39), (-4, 36)], level=2, reflect=True)
    shape("green", [(-3, 3), (4, 3), (4, 7), (8, 11), (9, 16), (8, 20),
                    (9, 27), (8, 32), (5, 34), (-5, 33), (-8, 31), (-8, 25),
                    (-7, 20), (-8, 15), (-7, 10), (-3, 6)], "green_dark")
    shape("green_mid", [(-2, 7), (4, 8), (6, 11), (7, 15), (4, 17), (-6, 17),
                        (-6, 12)], level=2)
    shape("green_mid", [(-6, 25), (4, 26), (7, 24), (7, 30), (3, 32), (-4, 31),
                        (-6, 29)], level=2)
    shape("green_dark", [(-7, 19), (7, 16), (8, 24), (2, 27), (-7, 28)], level=2)
    shape("paper", [(-7, 22), (7, 17), (7, 22), (-6, 28)], level=2)
    shape("crimson", [(-6, 24), (7, 18), (7, 21), (-6, 26)], level=2)
    shape("linen", [(-4, 0), (5, 0), (5, 4), (-4, 4)], "ink")
    line("sleeve_mid", [(-3, 3), (4, 3)], 2)
    line("green_light", [(-4, 12), (-5, 13), (-5, 15)], 2)
    line("mint", [(-3, 10), (0, 10)], 3)
    line("green_light", [(-4, 28), (-3, 30), (0, 30)], 3)
    line("green_dark", [(3, 29), (3, 31), (2, 32)], 3)
    shape("skin", [(-10, 21), (-8, 19), (-5, 18), (-3, 19), (-3, 20), (-6, 22),
                   (-4, 22), (-3, 23), (-4, 25), (-6, 26), (-4, 26), (-3, 28),
                   (-5, 30), (-7, 31), (-9, 29), (-10, 26)], "skin_dark", reflect=True)
    shape("skin", [(11, 17), (9, 18), (7, 21), (6, 24), (7, 26), (9, 25),
                   (10, 23), (12, 22), (13, 20)], "skin_dark", reflect=True)
    line("skin_mid", [(-9, 23), (-7, 23), (-5, 22)], reflect=True)
    line("skin_mid", [(-9, 27), (-7, 27), (-5, 26)], reflect=True)
    line("skin_light", [(-7, 20), (-5, 19)], reflect=True)
    line("skin_light", [(9, 21), (10, 19)], reflect=True)


def vestments(c):
    c.shape("wine", [(66, 86), (79, 89), (98, 89), (112, 87), (124, 96), (124, 149),
                     (51, 150), (52, 101)], "ink")
    c.shape("crimson", [(68, 90), (78, 92), (96, 93), (107, 91), (114, 103),
                        (110, 126), (105, 148), (66, 148), (62, 122)], level=2)
    c.shape("rose", [(74, 98), (96, 98), (103, 102), (99, 106), (76, 103)], level=2)
    c.shape("plum", [(69, 108), (90, 111), (103, 108), (100, 113), (91, 117),
                     (104, 120), (100, 124), (71, 120)], level=2)
    c.shape("rose", [(76, 114), (94, 117), (86, 120), (74, 119)], level=2)

    c.shape("crimson", [(62, 89), (49, 90), (40, 85), (32, 80), (24, 84),
                       (27, 94), (39, 103), (58, 113), (65, 101)], "ink")
    c.shape("crimson", [(112, 89), (126, 89), (138, 82), (150, 78), (154, 87),
                       (149, 99), (134, 106), (119, 115), (112, 102)], "ink")
    c.shape("rose", [(55, 92), (42, 88), (36, 86), (47, 96), (58, 103)], level=2)
    c.shape("rose", [(119, 92), (131, 88), (140, 85), (131, 96), (116, 104)], level=2)
    c.line("pink", [(45, 91), (53, 93), (57, 96)])
    c.line("pink", [(129, 92), (137, 87), (141, 86)])

    c.shape("cuff", [(13, 68), (20, 65), (26, 67), (33, 73), (28, 84), (19, 87),
                     (12, 81)], "ink")
    c.shape("cuff", [(146, 72), (152, 70), (158, 71), (163, 79), (160, 87),
                     (151, 90), (143, 83)], "ink")
    c.shape("cuff_light", [(14, 69), (21, 67), (26, 70), (28, 74), (20, 73), (14, 76)], level=2)
    c.shape("cuff_light", [(147, 76), (153, 72), (158, 73), (160, 78), (153, 77)], level=2)

    c.shape("linen", [(13, 76), (19, 80), (24, 78), (30, 72), (35, 80), (41, 85),
                      (47, 91), (55, 98), (62, 108), (64, 119), (57, 130), (47, 134),
                      (39, 123), (25, 116), (12, 108), (8, 102), (8, 91)], "ink")
    c.shape("linen", [(144, 75), (150, 81), (156, 82), (162, 77), (166, 89),
                      (169, 99), (167, 108), (160, 115), (142, 122), (131, 130),
                      (119, 135), (112, 124), (113, 112), (120, 102), (130, 93),
                      (138, 84)], "ink")

    c.shape("sleeve_mid", [(10, 95), (14, 100), (22, 103), (29, 102), (35, 107),
                           (46, 109), (54, 113), (59, 119), (56, 128), (47, 133),
                           (39, 122), (25, 115), (13, 107), (9, 101)], level=2)
    c.shape("sleeve_mid", [(166, 98), (163, 103), (157, 106), (148, 106), (139, 111),
                           (130, 111), (122, 115), (116, 124), (120, 134), (130, 129),
                           (142, 121), (159, 114), (166, 108)], level=2)
    c.shape("sleeve_lit", [(15, 82), (19, 84), (23, 82), (20, 89), (17, 94), (17, 100),
                           (13, 98), (11, 94)], level=2)
    c.shape("sleeve_lit", [(33, 82), (43, 91), (52, 99), (54, 106), (50, 107), (43, 98),
                           (34, 92), (27, 94), (30, 88)], level=2)
    c.shape("sleeve_lit", [(143, 81), (148, 85), (147, 89), (140, 93), (134, 102),
                           (124, 107), (128, 100), (134, 94)], level=2)
    c.shape("sleeve_lit", [(159, 83), (163, 92), (164, 99), (161, 103), (157, 104),
                           (159, 96), (155, 90), (154, 85)], level=2)
    c.shape("sleeve_dark", [(11, 92), (13, 97), (17, 101), (21, 102), (23, 105),
                            (17, 104), (12, 101), (10, 97)], level=2)
    c.shape("sleeve_dark", [(165, 94), (166, 101), (164, 107), (160, 110), (155, 111),
                            (159, 107), (162, 104), (164, 99)], level=2)
    c.line("linen", [(24, 87), (22, 92), (22, 97), (25, 99)])
    c.line("linen", [(152, 88), (154, 94), (153, 101), (150, 104)])
    c.line("sleeve_lit", [(27, 109), (35, 114), (40, 115), (45, 121)])
    c.line("sleeve_lit", [(149, 112), (142, 116), (136, 118), (131, 123)])


def stole(c):
    c.shape("vest_red", [(73, 85), (67, 84), (62, 87), (58, 94), (58, 105), (56, 120),
                         (55, 151), (73, 151), (74, 126), (77, 109), (77, 97)], "ink")
    c.shape("vest_red", [(101, 85), (107, 84), (114, 88), (119, 95), (119, 110),
                         (121, 123), (121, 152), (102, 152), (101, 129), (98, 110),
                         (97, 97)], "ink")
    c.shape("vest_dark", [(60, 107), (72, 110), (69, 125), (69, 150), (57, 150)], level=2)
    c.shape("vest_dark", [(101, 108), (116, 105), (119, 128), (119, 150), (104, 150)], level=2)
    c.line("gold_dark", [(56, 147), (58, 114), (59, 96), (64, 88), (70, 86), (76, 95),
                         (75, 112), (72, 123), (71, 147)], 2)
    c.line("gold_dark", [(104, 147), (103, 126), (100, 111), (98, 97), (102, 88), (108, 86),
                         (115, 91), (118, 99), (118, 113), (120, 127), (120, 147)], 2)
    c.line("gold", [(57, 146), (59, 115), (60, 96), (64, 89), (70, 87), (75, 95),
                    (74, 111), (71, 123), (70, 148)])
    c.line("gold", [(105, 148), (104, 126), (101, 111), (99, 97), (103, 89), (108, 87),
                    (114, 91), (117, 99), (117, 113), (119, 127), (119, 147)])
    for x, y in [(67, 99), (109, 100), (65, 118), (110, 119)]:
        c.shape("gold_dark", [(x, y-7), (x+5, y-2), (x+5, y+4), (x, y+7),
                              (x-5, y+4), (x-5, y-2)], level=2)
        c.line("gold", [(x-4, y+4), (x-4, y), (x, y-5), (x+4, y), (x+4, y+4)])
        c.line("gold_light", [(x, y-3), (x, y+4)], level=3)
        c.line("gold_light", [(x-2, y), (x+2, y)], level=3)
    c.line("gold_light", [(60, 106), (65, 108), (70, 109), (74, 109)], level=3)
    c.line("gold_light", [(102, 110), (107, 109), (112, 108), (116, 106)], level=3)


def portrait(c):
    c.shape("skin_mid", [(80, 89), (96, 89), (97, 95), (100, 98), (94, 103),
                         (86, 103), (77, 98), (80, 94)], "ink")
    c.shape("skin_shade", [(81, 90), (96, 90), (96, 97), (91, 102), (83, 99)], level=2)
    c.shape("wine", [(78, 98), (85, 100), (91, 101), (99, 98), (102, 101), (94, 106),
                     (86, 106), (76, 101)], "aubergine")
    c.line("gold", [(78, 100), (86, 104), (94, 104), (100, 101)])
    c.line("gold_light", [(89, 105), (91, 108), (95, 110), (95, 112)])
    c.line("gold", [(90, 106), (91, 110), (94, 112), (94, 115)])
    c.box("gold", (93, 114, 96, 116))

    c.shape("hair", [(70, 62), (75, 54), (84, 49), (98, 51), (105, 58), (108, 66),
                     (107, 78), (100, 87), (80, 90), (71, 82), (68, 74)], "ink")
    c.shape("hair_light", [(70, 66), (72, 60), (77, 56), (79, 58), (76, 61),
                           (73, 66), (72, 73), (70, 72)], level=2)
    c.shape("skin_mid", [(73, 73), (70, 73), (69, 76), (70, 81), (75, 83), (77, 78)], "ink")
    c.shape("skin_mid", [(101, 73), (105, 73), (106, 76), (104, 81), (100, 83), (99, 78)], "ink")
    c.line("skin_dark", [(71, 76), (73, 77), (73, 80)])
    c.line("skin_dark", [(104, 76), (102, 77), (102, 80)])

    c.shape("skin", [(75, 65), (78, 60), (82, 57), (96, 57), (101, 60), (102, 66),
                     (103, 75), (102, 82), (100, 88), (97, 94), (92, 98), (86, 98),
                     (80, 94), (76, 89), (74, 82), (73, 73)], "hair")
    c.shape("skin_mid", [(75, 64), (81, 60), (98, 59), (101, 63), (102, 69), (102, 78),
                         (101, 83), (99, 88), (96, 94), (92, 97), (86, 97), (80, 93),
                         (77, 88), (82, 92), (86, 94), (92, 94), (96, 90), (98, 84),
                         (97, 80), (99, 76), (99, 69), (96, 65), (87, 64), (80, 65),
                         (76, 70), (75, 75), (77, 80), (76, 83), (74, 79), (74, 73)], level=2)
    c.shape("skin_light", [(79, 65), (83, 63), (92, 63), (96, 65), (91, 65), (84, 66)], level=2)
    c.shape("skin_light", [(87, 75), (89, 76), (88, 80), (88, 83), (86, 85),
                           (85, 84), (86, 80)], level=2)
    c.shape("skin_mid", [(76, 82), (79, 80), (83, 81), (80, 82), (78, 85)], level=2)
    c.shape("skin_mid", [(92, 81), (98, 81), (99, 83), (96, 85), (94, 84)], level=2)
    c.line("skin_shade", [(90, 77), (90, 81), (92, 84), (90, 86), (87, 86)])
    c.line("skin_dark", [(87, 85), (89, 85)])
    c.line("skin_dark", [(84, 91), (87, 90), (91, 90), (94, 91)])
    c.line("skin_light", [(87, 92), (91, 92)], level=3)

    c.line("hair", [(76, 71), (79, 69), (83, 69), (86, 71)], 2)
    c.line("hair", [(92, 71), (95, 69), (98, 69), (100, 70)], 2)
    for x in (77, 92):
        c.shape("paper", [(x, 75), (x+2, 73), (x+6, 73), (x+7, 75), (x+5, 76),
                          (x+2, 76)], level=2)
        c.line("ink", [(x, 74), (x+2, 73), (x+5, 73), (x+7, 74)], level=3)
        c.box("hair_light", (x+2, 74, x+4, 76))
        c.box("ink", (x+3, 74, x+4, 75))
        c.line("skin_mid", [(x+1, 77), (x+5, 77)], level=3)

    # The hat sits in front of the hairline and tilts like a single corn chip.
    c.shape("chip", [(74, 62), (71, 55), (69, 45), (68, 33), (70, 22), (75, 11),
                     (79, 6), (84, 6), (91, 10), (98, 16), (104, 24), (109, 33),
                     (109, 39), (105, 46), (103, 55), (102, 61), (93, 58),
                     (82, 59)], "ink")
    c.shape("orange", [(71, 24), (75, 16), (74, 30), (76, 43), (80, 49), (84, 49),
                       (96, 43), (104, 37), (107, 33), (108, 39), (103, 47), (102, 54),
                       (101, 60), (93, 57), (82, 58), (75, 61), (72, 54), (70, 44),
                       (69, 33)], level=2)
    c.shape("chip_light", [(77, 15), (81, 9), (85, 10), (91, 14), (98, 21), (101, 28),
                           (99, 32), (91, 32), (85, 37), (79, 33), (76, 27)], level=2)
    c.shape("chip", [(83, 51), (92, 48), (101, 43), (99, 51), (99, 55), (92, 54),
                     (84, 56), (77, 58)], level=2)
    c.line("gold_dark", [(75, 59), (82, 55), (92, 51), (101, 44), (105, 41)])
    c.line("gold_light", [(80, 12), (82, 10), (86, 12), (91, 15), (94, 18)], level=3)
    for x, y, color in [(81, 18, "orange"), (87, 20, "orange"), (94, 26, "gold_mid"),
                         (78, 28, "gold_mid"), (86, 33, "orange"), (100, 33, "gold_mid"),
                         (80, 40, "orange"), (92, 38, "gold_mid"), (96, 50, "gold_mid"),
                         (75, 47, "gold_mid")]:
        c.line(color, [(x, y), (x+1, y), (x+1, y+1)], level=3)


GLYPHS = {
    "D": ("110", "101", "101", "101", "110"),
    "O": ("111", "101", "101", "101", "111"),
    "R": ("110", "101", "110", "101", "101"),
    "I": ("1", "1", "1", "1", "1"),
    "T": ("111", "010", "010", "010", "010"),
    "S": ("111", "100", "111", "001", "111"),
}


def bag(c, x, y, bottom, flavor):
    base, shade, light, logo = {
        "red": ("crimson", "wine", "rose", "blue_dark"),
        "yellow": ("lemon", "gold_mid", "lemon_light", "vest_dark"),
        "blue": ("blue", "blue_dark", "blue_mid", "blue_dark"),
    }[flavor]
    h = bottom - y

    def polygon(color, points, outline=None, level=1):
        c.shape(color, [(x + dx, y + dy) for dx, dy in points], outline, level)

    def stroke(color, points, level=2):
        c.line(color, [(x + dx, y + dy) for dx, dy in points], level=level)

    polygon(base, [(1, 0), (29, 0), (28, 4), (27, 8), (28, h-8), (30, h-3),
                   (29, h), (1, h), (0, h-3), (2, h-8), (2, 7), (0, 2)], "ink")
    polygon(shade, [(2, 4), (6, 6), (6, h-8), (9, h-5), (21, h-5), (26, h-9),
                    (28, h-7), (29, h-2), (1, h-2), (3, h-9)], level=2)
    polygon(light, [(25, 6), (27, 5), (26, 12), (27, h-7), (25, h-9), (24, 17)], level=2)
    stroke(light, [(3, 2), (24, 2), (27, 1)])
    stroke(base, [(2, h-2), (10, h-2), (13, h-3), (24, h-3), (28, h-2)])

    if flavor == "red":
        polygon("blue", [(3, 9), (27, 6), (24, 14), (15, 20), (5, 19)], level=2)
    else:
        polygon("orange", [(5, 10), (22, 4), (19, 11), (27, 10), (14, 16), (16, 10)], level=2)
        stroke("gold_light", [(10, 9), (20, 6), (17, 10)], 3)
    polygon(logo, [(3, 12), (27, 10), (28, 17), (25, 19), (3, 19)], level=2)

    if c.level >= 3:
        cursor = 3
        for letter in "DORITOS":
            glyph = GLYPHS[letter]
            for row, bits in enumerate(glyph):
                for dx, bit in enumerate(bits):
                    if bit == "1":
                        c.pen.point((x + cursor + dx, y + 13 + row), PALETTE["paper"])
            cursor += len(glyph[0]) + 1

    chip_y = max(h - 12, 23)
    polygon("orange", [(8, chip_y-3), (16, chip_y-1), (10, chip_y+4)], level=2)
    polygon("chip_light", [(8, chip_y-4), (15, chip_y-1), (10, chip_y+2)], level=2)
    polygon("gold_dark", [(15, chip_y-4), (24, chip_y+1), (13, chip_y+5)], level=2)
    polygon("chip", [(15, chip_y-5), (23, chip_y), (14, chip_y+3)], level=2)
    stroke("gold_light", [(15, chip_y-4), (16, chip_y-4), (18, chip_y-2)], 3)
    stroke("gold_mid", [(18, chip_y), (19, chip_y)], 3)


def draw(level):
    c = Canvas(level)
    bottle_and_hand(c, 23, 27)
    bottle_and_hand(c, 153, 30, right=True)
    vestments(c)
    stole(c)
    portrait(c)
    c.shape("vest_red", [(8, 149), (167, 149), (170, 152), (170, 155), (164, 158),
                         (10, 158), (6, 155), (6, 152)], "ink")
    c.shape("vest_dark", [(7, 154), (11, 155), (163, 155), (169, 153), (169, 155),
                         (164, 157), (10, 157), (7, 155)], level=2)
    c.line("rose", [(9, 152), (18, 152), (22, 151), (148, 151), (155, 152), (165, 152)])
    for placement in [(8, 119, 152, "red"), (40, 121, 152, "yellow"),
                      (73, 117, 152, "blue"), (106, 120, 152, "red"),
                      (138, 122, 152, "yellow")]:
        bag(c, *placement)
    return c


def main():
    case = Path(__file__).resolve().parents[1]
    build = case / "build"
    steps = build / "steps"
    steps.mkdir(parents=True, exist_ok=True)
    base = draw(1)
    silhouette = Image.new("RGBA", SIZE, PALETTE["ink"])
    silhouette.putalpha(base.image.getchannel("A"))
    base.image = silhouette
    base.finish().save(steps / "01_silhouette.png")
    for level, filename in [(1, "02_blockin.png"), (2, "03_shading.png")]:
        draw(level).finish().save(steps / filename)

    # The project exporter reads the native pixel indices and their palette.
    final = draw(3).finish()
    final.save(steps / "04_cleanup.png")
    pixels = np.asarray(final.convert("RGB")).reshape(-1, 3)
    colors, indices = np.unique(pixels, axis=0, return_inverse=True)
    np.save(build / "palette_rgb.npy", colors)
    np.save(build / "final_indices.npy", indices.reshape(final.height, final.width))


if __name__ == "__main__":
    main()
