"""Hand-placed shapes and pixels for the two-panel redraw."""
import argparse
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw


PANEL = (138, 134)
SIZE = (288, 144)
COLORS = {
    "page": "#150e22", "trim": "#6a3b73",
    "ink": "#210f26", "deep": "#371637", "wine": "#572040",
    "plum": "#74264e", "berry": "#a23862", "rose": "#d0527a",
    "pink": "#f987a2", "lilac": "#d89ad1", "purple": "#5c3b79",
    "teal_dark": "#173148", "teal": "#22516a", "teal_light": "#377b84",
    "mint": "#75cba7", "mint_lit": "#d0efa6",
    "base_wall": "#393354", "wall_lit": "#4f4469", "floor": "#452b48",
    "wood_dark": "#753343", "wood": "#b85851", "wood_lit": "#e68760",
    "clay": "#a74944", "umber": "#773448", "ochre": "#cb6e45",
    "honey": "#ee984b", "gold": "#f8bc60", "gold_lit": "#ffda86",
    "shine": "#fff3bc", "white": "#fff5e6", "eye_shade": "#efbbbe",
    "iris": "#391d38", "iris_lit": "#6b3b68", "glint": "#fff8ee",
    "ember_dark": "#9f3152", "fire_red": "#ed4f52", "fire": "#fd794e",
    "fire_gold": "#ffb153", "fire_lit": "#fcdc7a", "flame_core": "#fff499",
    "hot": "#ffffd0", "tea": "#56223a", "tea_lit": "#bb555f",
    "smoke": "#311c43", "smoke_mid": "#4a2854", "smoke_lit": "#744264",
    "smoke_blue": "#293752", "carpet": "#61415f",
}


class Pixels:
    def __init__(self, stage, fill="base_wall", size=PANEL):
        self.stage = stage
        self.image = Image.new("RGB", size, COLORS[fill])
        self.pen = ImageDraw.Draw(self.image)

    def shape(self, color, points, edge=None, stage=1):
        if self.stage >= stage:
            self.pen.polygon(points, COLORS[color], COLORS[edge] if edge else None)

    def ellipse(self, color, bounds, edge=None, stage=1):
        if self.stage >= stage:
            self.pen.ellipse(bounds, COLORS[color], COLORS[edge] if edge else None)

    def box(self, color, bounds, edge=None, stage=1):
        if self.stage >= stage:
            self.pen.rectangle(bounds, COLORS[color], COLORS[edge] if edge else None)

    def line(self, color, points, stage=2):
        if self.stage >= stage:
            self.pen.line(points, COLORS[color])

    def dot(self, color, x, y, stage=3):
        if self.stage >= stage:
            self.pen.point((x, y), COLORS[color])

    def arc(self, color, bounds, start, end, stage=2):
        if self.stage >= stage:
            self.pen.arc(bounds, start, end, fill=COLORS[color])


def flame(c, x, bottom, width, height, flip=False, bank=False):
    def points(path):
        return [
            (x + round((24 - u if flip else u) * width / 24),
             bottom - round(v * height / 60))
            for u, v in path
        ]

    tips = [(0, 0), (1, 10), (4, 18), (4, 25), (6, 34), (6, 45),
            (9, 60), (11, 53), (11, 45), (9, 36), (10, 29), (12, 22),
            (14, 29), (16, 36), (19, 42), (19, 34), (18, 26), (19, 20),
            (21, 14), (23, 19), (24, 10), (24, 0)]
    c.shape("fire" if bank else "fire_gold", points(tips), "ember_dark")
    inner = [(2, 0), (3, 10), (6, 17), (7, 28), (8, 37), (9, 49),
             (10, 44), (8, 33), (8, 25), (10, 17), (12, 12),
             (15, 21), (17, 29), (17, 20), (19, 13), (21, 8), (23, 0)]
    c.shape("fire_gold" if bank else "fire_lit", points(inner), stage=2)
    seam = [(0, 0), (1, 11), (4, 19), (4, 25), (6, 36), (6, 44),
            (8, 50), (7, 38), (6, 29), (7, 24), (4, 14), (3, 3)]
    c.shape("fire_red" if bank else "fire", points(seam), stage=2)
    core = [(5, 0), (5, 8), (7, 17), (7, 23), (8, 19), (10, 12),
            (12, 5), (14, 7), (16, 14), (17, 19), (17, 12), (20, 4), (21, 0)]
    c.shape("fire_lit" if bank else "flame_core", points(core), stage=2)
    c.shape("hot", points([(8, 0), (8, 7), (8, 13), (10, 9), (12, 3),
                            (15, 1), (15, 0)]), stage=3)
    c.line("hot", points([(8, 8), (8, 13), (7, 17)]), stage=3)
    c.line("fire_red", points([(6, 37), (7, 43), (8, 48)]), stage=3)
    c.line("fire_red", points([(20, 8), (21, 12), (22, 14)]), stage=3)


def room(c, close):
    c.box("teal_dark", (0, 0, 137, 133))
    if close:
        c.shape("teal", [(0, 20), (137, 17), (137, 112), (105, 119),
                         (44, 119), (0, 124)])
        c.shape("base_wall", [(0, 19), (31, 22), (37, 77), (17, 132), (0, 133)])
        c.shape("wall_lit", [(114, 33), (137, 28), (137, 100), (108, 98)])
        c.shape("teal_light", [(29, 37), (42, 35), (67, 43), (96, 40),
                               (115, 48), (117, 72), (103, 94), (59, 109),
                               (34, 104), (32, 82)], stage=2)
        c.line("mint", [(4, 43), (17, 46), (35, 47), (55, 52), (95, 49), (129, 47)])
        c.line("teal_dark", [(1, 45), (20, 49), (36, 50), (55, 55), (98, 52), (137, 49)])
    else:
        c.shape("teal", [(0, 21), (105, 16), (103, 91), (0, 103)])
        c.shape("base_wall", [(105, 16), (137, 22), (137, 98), (103, 91)])
        c.shape("floor", [(0, 101), (102, 90), (137, 97), (137, 133), (0, 133)])
        c.shape("carpet", [(8, 111), (88, 103), (137, 116), (137, 133), (0, 133)])
        c.shape("teal_light", [(2, 34), (30, 32), (52, 29), (78, 31), (103, 26),
                               (103, 72), (79, 80), (44, 83), (13, 87), (0, 93)], stage=2)
        c.line("mint", [(0, 31), (48, 27), (102, 25)])
        c.line("purple", [(105, 36), (125, 40), (137, 43)])
        c.line("wood_lit", [(0, 102), (47, 97), (102, 91), (137, 98)])
        c.line("wood_dark", [(0, 104), (47, 99), (101, 94), (137, 101)])
        for line in [
            [(10, 115), (41, 108), (76, 105), (99, 108)],
            [(0, 122), (35, 114), (79, 110), (119, 119)],
            [(12, 131), (43, 124), (80, 117), (137, 129)],
            [(76, 107), (67, 117), (62, 133)],
            [(85, 109), (94, 121), (98, 133)],
        ]:
            c.line("wood_dark", line, stage=3)
        c.shape("wine", [(19, 39), (53, 35), (54, 97), (19, 100)], "ink")
        c.shape("teal_dark", [(23, 43), (49, 40), (50, 94), (23, 97)], "plum")
        c.line("rose", [(19, 40), (19, 96)])
        c.line("wood_lit", [(21, 39), (49, 36), (52, 36)])
        c.line("teal", [(25, 46), (47, 44), (47, 90)], stage=3)
        c.line("teal", [(28, 47), (28, 86)], stage=3)
        c.shape("wood_dark", [(79, 35), (101, 33), (100, 63), (79, 65)], "ink")
        c.shape("mint", [(83, 39), (97, 37), (96, 59), (83, 61)], "deep")
        c.line("wood_lit", [(79, 36), (100, 34), (99, 61)])
        c.shape("teal_light", [(85, 42), (96, 40), (95, 57), (85, 59)], stage=2)
        c.shape("mint", [(85, 51), (90, 49), (92, 45), (95, 47), (95, 57), (85, 59)], stage=2)
        c.line("mint_lit", [(87, 48), (93, 40), (95, 39)], stage=3)
        c.line("mint_lit", [(89, 53), (96, 43)], stage=3)
    for y in range(39, 97, 11):
        for x in range(2 + 5 * (y % 2), 138, 10):
            if not close and (18 <= x <= 55 or 78 <= x <= 102 and y <= 66):
                continue
            c.line("teal" if x < 105 else "purple", [(x, y), (x+1, y-2), (x+2, y)], stage=3)
            c.dot("mint" if x < 105 else "smoke_lit", x+1, y+2)


def smoke(c, close):
    c.box("smoke", (0, 0, 137, 16))
    billows = [(-18, 0, 29, 31), (16, 6, 48, 26), (40, -5, 77, 22),
               (65, 3, 88, 25), (83, 2, 118, 34), (107, -1, 128, 23),
               (119, 7, 147, 29)]
    for x0, y0, x1, y1 in billows:
        bump = 2 if close else 0
        c.ellipse("smoke", (x0, y0, x1, y1+bump), "ink")
        c.ellipse("smoke_mid", (x0+1, y0-3, x1-1, y1-3+bump), stage=2)

    c.shape("smoke_blue", [(0, 0), (61, 0), (54, 5), (44, 7), (33, 5),
                          (24, 7), (17, 14), (8, 19), (0, 18)], stage=2)
    c.shape("smoke_blue", [(68, 0), (123, 0), (121, 7), (111, 11),
                          (108, 19), (101, 22), (94, 20), (90, 13),
                          (82, 11), (72, 11), (65, 7)], stage=2)
    c.shape("plum", [(0, 14), (5, 16), (11, 16), (15, 14), (20, 9), (26, 8),
                     (32, 11), (32, 15), (28, 18), (24, 18), (23, 15),
                     (20, 19), (15, 23), (7, 26), (0, 25)], stage=2)
    c.shape("wine", [(80, 12), (87, 10), (95, 12), (97, 18), (103, 20),
                     (109, 18), (113, 13), (119, 12), (125, 16), (130, 17),
                     (137, 13), (137, 19), (130, 22), (123, 21), (116, 18),
                     (111, 25), (103, 28), (96, 26), (92, 19), (88, 16),
                     (84, 16), (82, 19), (78, 16)], stage=2)
    for color, bounds, start, end in [
        ("smoke_lit", (-13, 6, 20, 27), 18, 118),
        ("rose", (16, 9, 30, 21), 178, 319),
        ("purple", (28, 2, 54, 19), 22, 125),
        ("smoke_lit", (58, 1, 86, 20), 9, 118),
        ("berry", (84, 10, 99, 25), 154, 284),
        ("smoke_lit", (93, 7, 119, 30), 12, 164),
        ("purple", (111, 4, 134, 20), 65, 186),
    ]:
        c.arc(color, bounds, start, end, stage=3)
    for color, x, y in [("purple", 11, 22), ("rose", 21, 14), ("berry", 33, 17),
                        ("purple", 42, 12), ("smoke_lit", 70, 15), ("rose", 89, 17),
                        ("berry", 100, 25), ("purple", 113, 22), ("rose", 125, 20)]:
        c.dot(color, x, y)
        c.dot("smoke_lit", x+1, y+1)


def chair(c, close):
    if close:
        c.shape("wood", [(0, 97), (9, 94), (24, 97), (32, 105),
                         (30, 133), (0, 133)], "ink")
        c.shape("wood_dark", [(3, 104), (12, 100), (22, 103),
                              (25, 111), (24, 133), (3, 133)], "wine")
        c.line("wood_lit", [(2, 99), (8, 96), (17, 97), (25, 99)])
        c.line("ochre", [(3, 110), (4, 121), (4, 133)], stage=3)
        return
    c.shape("wood", [(33, 76), (41, 72), (56, 73), (61, 79), (61, 102),
                     (57, 109), (40, 109), (33, 105), (31, 96), (31, 81)], "ink")
    c.shape("wood_dark", [(36, 81), (41, 77), (54, 77), (57, 82),
                          (57, 102), (53, 105), (40, 104), (36, 100)], "wine")
    for x, y in [(42, 107), (68, 107), (74, 103)]:
        c.shape("wood_lit", [(x, y), (x+4, y), (x+4, y+18), (x+2, y+21),
                             (x, y+20)], "ink")
        c.line("wood_dark", [(x+3, y+3), (x+3, y+16)])
    c.shape("wood", [(39, 103), (55, 100), (75, 101), (79, 106),
                     (77, 111), (59, 113), (39, 111), (36, 108)], "ink")
    c.line("wood_lit", [(34, 80), (35, 93), (36, 99)])
    c.line("wood_lit", [(39, 108), (53, 110), (59, 110)], stage=3)


def table(c, close):
    if close:
        c.shape("wood", [(98, 133), (103, 127), (113, 122), (126, 120),
                         (137, 120), (137, 133)], "ink")
        c.line("wood_lit", [(101, 133), (106, 128), (115, 124), (127, 122), (137, 122)])
    else:
        c.shape("wood_dark", [(111, 98), (120, 98), (119, 121), (116, 125),
                              (111, 124)], "ink")
        c.shape("wood_dark", [(133, 99), (138, 98), (138, 120),
                              (134, 118)], "ink")
        c.ellipse("wood_dark", (86, 91, 159, 106), "ink")
        c.ellipse("wood", (86, 86, 159, 102), "ink")
        c.ellipse("wood_lit", (89, 88, 156, 98), stage=2)
        c.arc("honey", (88, 86, 158, 102), 10, 170, stage=3)
        c.line("wood_dark", [(99, 95), (109, 96), (134, 96), (147, 94)], stage=3)
        c.line("honey", [(120, 99), (131, 99), (135, 98)], stage=3)


def cup(c, x, y, scale):
    def pp(path):
        return [(x + round(u*scale), y + round(v*scale)) for u, v in path]

    def bounds(x0, y0, x1, y1):
        a, b = pp([(x0, y0), (x1, y1)])
        return (*a, *b)

    c.ellipse("shine", bounds(11, 3, 21, 13), "ink")
    c.ellipse("wood_dark", bounds(13, 5, 18, 11), "wine")
    c.shape("shine", pp([(0, 2), (15, 2), (14, 17), (11, 19), (4, 19),
                         (2, 17)]), "ink")
    c.shape("eye_shade", pp([(11, 4), (14, 4), (13, 17), (11, 18), (5, 18),
                             (3, 16), (9, 16)]), stage=2)
    c.shape("rose", pp([(12, 6), (14, 5), (13, 16), (11, 18), (6, 18),
                        (5, 17), (10, 16)]), stage=2)
    c.ellipse("shine", bounds(0, 0, 15, 5), "ink")
    c.ellipse("tea", bounds(2, 2, 13, 4), stage=2)
    c.line("tea_lit", pp([(4, 3), (9, 3), (11, 2)]), stage=3)
    c.line("white", pp([(3, 6), (4, 10), (4, 12)]), stage=3)
    c.line("mint_lit", pp([(19, 6), (20, 8), (19, 10)]), stage=3)


def eye(c, box, pupil, *, smooth_pupil=False):
    x0, y0, x1, y1 = box
    a, b, d, e = pupil
    c.ellipse("white", box, "ink")
    c.ellipse("eye_shade", (x0+1, y0+2, x1-1, y1-1), stage=2)
    c.ellipse("white", (x0+2, y0+1, x1-1, y1-3), stage=2)
    if smooth_pupil:
        c.ellipse("ink", pupil)
        highlight_x = a + (d-a)//3
        highlight_y = b + (e-b)//4
        c.box("glint", (highlight_x, highlight_y, highlight_x+1, highlight_y+1), stage=3)
        return
    c.ellipse("iris", pupil)
    c.ellipse("ink", (a+1, b+1, d-1, e-1), stage=2)
    c.line("iris_lit", [(a+1, e-2), (a+2, e-1), (d-2, e-1)], stage=3)
    c.ellipse("glint", (a+2, b+2, a+3, b+3), stage=3)


def dog_wide(c):
    c.shape("gold", [(49, 54), (55, 50), (64, 51), (70, 55), (74, 62),
                     (76, 73), (75, 81), (70, 87), (70, 93), (74, 100),
                     (71, 106), (63, 108), (53, 106), (46, 102),
                     (42, 97), (41, 87), (42, 77), (44, 66)], "ink")
    c.shape("honey", [(42, 78), (50, 70), (54, 76), (54, 85), (59, 93),
                      (68, 95), (71, 101), (70, 105), (63, 107), (53, 105),
                      (46, 101), (43, 96), (42, 88)], stage=2)
    c.shape("gold_lit", [(55, 55), (63, 53), (69, 57), (68, 64), (62, 67),
                         (55, 63)], stage=2)
    c.shape("ochre", [(43, 82), (46, 85), (45, 90), (46, 96), (51, 100),
                      (53, 104), (47, 101), (43, 95)], stage=2)
    c.shape("iris", [(47, 61), (51, 65), (51, 73), (48, 82), (44, 87),
                     (40, 86), (37, 83), (37, 77), (40, 70), (43, 65)], "ink")
    c.shape("iris_lit", [(46, 64), (49, 66), (48, 73), (45, 80), (42, 84),
                         (39, 82), (40, 76)], stage=2)
    c.line("rose", [(42, 72), (44, 68), (46, 66)], stage=3)
    c.shape("gold", [(58, 73), (62, 70), (70, 69), (77, 67), (87, 66),
                     (93, 69), (94, 74), (91, 78), (85, 81), (77, 82),
                     (72, 80), (68, 77), (60, 78)])
    c.shape("honey", [(69, 76), (75, 78), (84, 77), (91, 74), (91, 77),
                      (85, 80), (77, 81), (73, 79)], stage=2)
    c.shape("gold_lit", [(72, 71), (78, 68), (87, 67), (89, 69), (86, 72),
                         (80, 73), (75, 73)], stage=2)
    c.line("ink", [(74, 68), (77, 67), (87, 66), (93, 69), (94, 74),
                   (91, 78), (85, 81), (77, 82), (72, 80), (69, 77)], stage=1)
    c.line("umber", [(67, 77), (69, 76), (70, 76)], stage=3)
    eye(c, (67, 56, 78, 71), (72, 59, 78, 69))
    eye(c, (54, 60, 66, 75), (58, 63, 64, 73))
    c.ellipse("ink", (82, 64, 95, 73))
    c.ellipse("iris", (83, 65, 94, 70), stage=2)
    c.line("iris_lit", [(85, 66), (89, 65), (92, 66)], stage=3)
    c.dot("lilac", 87, 66)
    c.shape("honey", [(47, 84), (51, 91), (56, 96), (64, 97), (68, 101),
                      (70, 105), (67, 109), (63, 109), (61, 105),
                      (56, 104), (50, 101), (46, 96), (45, 90)], "umber")
    c.line("gold_lit", [(48, 91), (51, 96), (55, 99), (59, 100)])
    c.line("ochre", [(46, 94), (50, 100), (54, 102)], stage=3)
    c.shape("gold", [(67, 97), (70, 95), (73, 96), (74, 100), (75, 102),
                     (78, 100), (81, 101), (82, 104), (80, 107), (75, 108),
                     (70, 107), (68, 104)], "ink")
    c.shape("honey", [(69, 103), (74, 105), (79, 105), (80, 103),
                      (81, 104), (79, 106), (75, 107), (70, 106)], stage=2)
    c.shape("gold", [(55, 99), (60, 100), (63, 103), (64, 107), (67, 107),
                     (70, 109), (68, 112), (64, 113), (59, 111), (58, 107),
                     (54, 106)], "ink")
    c.line("ochre", [(56, 105), (60, 106), (61, 110), (65, 112), (68, 110)])
    c.line("gold_lit", [(63, 108), (65, 109), (67, 109)], stage=3)
    c.shape("honey", [(47, 51), (46, 46), (49, 43), (53, 42), (58, 44),
                      (61, 49), (59, 54), (51, 55)], "ink")
    c.shape("gold_lit", [(48, 46), (51, 43), (54, 43), (57, 45), (54, 47),
                         (49, 48)], stage=2)
    c.shape("tea", [(47, 50), (53, 49), (59, 46), (61, 49), (57, 53),
                    (50, 55)], "ink")
    c.shape("gold", [(44, 53), (47, 52), (51, 52), (57, 50), (62, 47),
                     (65, 48), (66, 51), (63, 55), (56, 58), (49, 59),
                     (45, 57)], "ink")
    c.line("honey", [(46, 56), (50, 57), (56, 57), (63, 54), (65, 51)])
    c.line("shine", [(49, 54), (53, 54), (59, 52), (62, 49)], stage=3)


def dog_close(c):
    c.shape("gold", [(23, 60), (30, 54), (40, 52), (53, 55), (63, 61),
                     (71, 71), (75, 84), (78, 97), (74, 109), (67, 117),
                     (66, 124), (70, 133), (10, 133), (10, 123),
                     (13, 109), (11, 98), (13, 85), (18, 71)], "ink")
    c.shape("honey", [(23, 63), (33, 55), (44, 55), (48, 60), (42, 69),
                      (37, 83), (37, 93), (43, 101), (48, 109), (53, 118),
                      (62, 124), (66, 126), (68, 133), (11, 133), (14, 109),
                      (12, 98), (14, 85), (19, 72)], stage=2)
    c.shape("ochre", [(24, 74), (30, 80), (27, 96), (27, 108), (32, 120),
                      (38, 128), (42, 133), (13, 133), (14, 113), (14, 106),
                      (15, 91)], stage=2)
    c.shape("gold_lit", [(39, 59), (49, 57), (58, 61), (64, 67), (62, 74),
                         (55, 77), (47, 75), (41, 71), (35, 69)], stage=2)
    c.shape("gold_lit", [(43, 104), (51, 108), (57, 114), (59, 120), (62, 125),
                         (63, 133), (46, 133), (41, 128), (38, 121),
                         (37, 112)], stage=2)
    c.line("clay", [(28, 108), (27, 114), (28, 122), (31, 130), (33, 133)])
    c.line("umber", [(31, 107), (30, 112), (31, 120), (33, 127), (37, 133)], stage=3)
    c.line("clay", [(40, 113), (40, 119), (43, 126), (46, 133)], stage=3)
    c.line("gold_lit", [(31, 117), (34, 125), (36, 129)], stage=3)
    c.line("shine", [(56, 119), (58, 124), (58, 129)], stage=3)
    c.shape("iris", [(24, 62), (29, 67), (30, 78), (28, 94), (25, 105),
                     (20, 111), (13, 113), (8, 110), (6, 104), (6, 97),
                     (9, 86), (15, 75), (18, 69)], "ink")
    c.shape("ink", [(22, 65), (26, 66), (28, 74), (28, 87), (25, 97),
                    (19, 106), (12, 109), (9, 104), (9, 96), (14, 87),
                    (17, 76)], stage=2)
    c.shape("iris_lit", [(21, 70), (24, 69), (26, 73), (25, 81), (23, 89),
                         (19, 96), (14, 99), (12, 99), (13, 92), (17, 83)], stage=2)
    c.shape("berry", [(20, 78), (23, 73), (24, 73), (22, 82), (18, 89),
                      (15, 91), (16, 87)], stage=3)
    c.line("lilac", [(20, 78), (22, 74), (23, 73)], stage=3)
    c.line("rose", [(8, 102), (10, 107), (13, 110), (17, 110)], stage=3)
    c.shape("gold", [(44, 88), (51, 83), (61, 81), (73, 77), (84, 74),
                     (96, 74), (102, 77), (106, 83), (106, 90), (102, 98),
                     (97, 102), (89, 106), (79, 108), (68, 109), (59, 107),
                     (53, 104), (48, 105)], "ink")
    c.shape("honey", [(47, 99), (58, 100), (68, 103), (82, 103), (94, 99),
                      (100, 94), (104, 87), (104, 93), (101, 97), (96, 101),
                      (88, 105), (78, 107), (68, 108), (59, 106), (53, 103),
                      (48, 104)], stage=2)
    c.shape("gold_lit", [(59, 87), (69, 80), (77, 77), (86, 75), (97, 75),
                         (100, 80), (94, 85), (85, 86), (75, 90), (67, 91)], stage=2)
    c.shape("shine", [(73, 82), (83, 78), (90, 77), (93, 78), (89, 81),
                      (81, 82), (75, 84)], stage=3)
    c.line("ochre", [(83, 103), (92, 100), (99, 95)], stage=3)
    for x, y in [(64, 95), (69, 97), (72, 94), (77, 97)]:
        c.dot("ochre", x, y)
        c.dot("gold_lit", x, y+1)
    c.shape("tea", [(48, 105), (52, 103), (58, 107), (67, 109), (75, 108),
                    (80, 107), (77, 114), (72, 118), (64, 120), (57, 117),
                    (52, 112)], "ink")
    c.shape("ink", [(57, 109), (65, 111), (74, 110), (78, 109), (75, 115),
                    (70, 118), (63, 119), (57, 116)], stage=2)
    c.shape("fire_red", [(53, 108), (59, 109), (63, 112), (67, 118),
                         (60, 118), (56, 115)], "wine")
    c.shape("pink", [(54, 109), (59, 110), (63, 113), (61, 115), (57, 114)], stage=2)
    c.line("rose", [(56, 110), (59, 112), (60, 114)], stage=3)
    c.shape("white", [(56, 106), (62, 107), (65, 109), (64, 111), (60, 111),
                      (57, 109)], "ink")
    c.shape("white", [(65, 109), (72, 109), (73, 112), (70, 114), (66, 112)], "ink")
    c.line("white", [(74, 110), (76, 110)], stage=1)
    c.line("white", [(74, 111), (75, 111)], stage=1)
    c.dot("eye_shade", 75, 112, stage=2)
    eye(c, (57, 65, 78, 89), (64, 68, 76, 86), smooth_pupil=True)
    eye(c, (31, 70, 57, 98), (40, 74, 55, 94), smooth_pupil=True)
    c.shape("ink", [(91, 73), (98, 72), (104, 74), (108, 78), (108, 84),
                    (105, 90), (101, 94), (94, 96), (88, 94), (85, 90),
                    (84, 84), (87, 78)], "deep")
    c.shape("iris", [(89, 78), (94, 74), (100, 74), (105, 77), (106, 82),
                     (103, 85), (97, 87), (90, 86), (87, 84)], stage=2)
    c.shape("iris_lit", [(90, 78), (94, 75), (100, 75), (102, 77), (99, 80),
                         (92, 81), (89, 81)], stage=2)
    c.shape("lilac", [(93, 77), (96, 76), (100, 76), (100, 77), (96, 78),
                      (93, 79)], stage=3)
    c.line("rose", [(87, 87), (88, 91), (92, 94), (96, 94)], stage=3)
    c.shape("honey", [(20, 54), (20, 46), (23, 39), (28, 35), (34, 34),
                      (40, 36), (45, 40), (48, 46), (47, 52), (43, 58),
                      (35, 60), (28, 59)], "ink")
    c.shape("gold", [(21, 46), (24, 40), (28, 37), (34, 36), (39, 38),
                     (42, 42), (38, 45), (31, 47), (23, 49)], stage=2)
    c.shape("gold_lit", [(24, 43), (27, 39), (32, 37), (35, 38), (33, 41),
                         (28, 43)], stage=2)
    c.line("shine", [(26, 40), (29, 38), (33, 37)], stage=3)
    c.shape("tea", [(20, 53), (27, 51), (35, 48), (43, 44), (47, 44),
                    (50, 48), (47, 55), (40, 60), (31, 63), (24, 60)], "ink")
    c.line("rose", [(23, 53), (30, 51), (36, 49), (44, 45)], stage=3)
    c.shape("gold", [(15, 58), (19, 55), (27, 55), (34, 54), (41, 51),
                     (49, 45), (54, 44), (58, 47), (59, 51), (57, 56),
                     (53, 61), (46, 65), (36, 68), (26, 67), (18, 65)], "ink")
    c.shape("honey", [(16, 59), (21, 60), (26, 62), (36, 63), (46, 61),
                      (52, 57), (57, 51), (57, 55), (52, 61), (46, 64),
                      (36, 67), (26, 66), (19, 64)], stage=2)
    c.shape("gold_lit", [(19, 57), (28, 56), (38, 54), (47, 48), (52, 45),
                         (55, 46), (54, 50), (49, 54), (41, 58), (31, 59),
                         (24, 59)], stage=2)
    c.line("shine", [(25, 57), (34, 56), (43, 53), (50, 48)], stage=3)
    c.line("ochre", [(20, 64), (25, 65), (31, 65)], stage=3)


GLYPHS = {
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "H": ("11001", "11001", "11001", "11111", "11001", "11001", "11001"),
    "I": ("111", "010", "010", "010", "010", "010", "111"),
    "S": ("01111", "11000", "11000", "01110", "00011", "00011", "11110"),
    "F": ("11111", "11000", "11000", "11110", "11000", "11000", "11000"),
    "N": ("10001", "11001", "11001", "10101", "10011", "10011", "10001"),
    "E": ("11111", "11000", "11000", "11110", "11000", "11000", "11111"),
    ".": ("00", "00", "00", "00", "00", "11", "11"),
    " ": ("000",)*7,
}


def speech(c):
    c.shape("ink", [(35, 7), (42, 3), (121, 3), (129, 6), (134, 12),
                    (135, 21), (134, 29), (130, 35), (122, 40), (100, 40),
                    (98, 47), (93, 55), (86, 61), (80, 65), (84, 55),
                    (86, 48), (86, 40), (44, 40), (36, 37), (30, 32),
                    (27, 25), (27, 17), (30, 11)])
    c.shape("white", [(36, 8), (43, 5), (121, 5), (128, 8), (132, 13),
                      (133, 21), (132, 28), (128, 34), (121, 38), (98, 38),
                      (96, 47), (92, 54), (84, 61), (87, 52), (88, 46),
                      (88, 38), (44, 38), (37, 35), (32, 31), (29, 24),
                      (29, 17), (32, 12)])
    c.shape("eye_shade", [(30, 27), (35, 30), (43, 33), (55, 35),
                          (92, 35), (92, 45), (89, 52), (86, 58), (88, 51),
                          (89, 44), (89, 37), (44, 37), (38, 34), (33, 30)], stage=2)
    c.shape("eye_shade", [(102, 35), (120, 34), (128, 30), (132, 24),
                          (131, 29), (127, 34), (121, 37), (101, 37)], stage=2)
    c.line("white", [(45, 6), (120, 6), (126, 8)], stage=3)
    x = 49
    for character in "THIS IS FINE.":
        glyph = GLYPHS[character]
        for row, bits in enumerate(glyph):
            for column, bit in enumerate(bits):
                if bit == "1":
                    c.dot("ink", x+column, 18+row, stage=1)
        x += len(glyph[0]) + 1


def embers(c, close):
    if close:
        sparks = [(4, 51), (11, 58), (15, 45), (97, 67), (104, 59),
                  (119, 53), (123, 73), (130, 61), (115, 89), (133, 94)]
    else:
        sparks = [(9, 40), (16, 52), (28, 41), (32, 65), (70, 48),
                  (77, 35), (104, 60), (110, 54), (123, 35), (132, 67),
                  (92, 82), (97, 116), (85, 124), (25, 116)]
    for index, (x, y) in enumerate(sparks):
        c.dot("fire_red", x-1, y+1)
        c.dot("fire_gold", x, y)
        if index % 3 == 1:
            c.dot("hot", x, y-1)
            c.dot("fire", x+1, y)


def panel(stage, close):
    c = Pixels(stage)
    room(c, close)
    if close:
        for placement in [(-7, 103, 39, 66, True), (82, 133, 69, 94, False),
                          (115, 124, 44, 81, True)]:
            flame(c, *placement, bank=True)
    else:
        for placement in [(4, 108, 43, 63, False), (70, 114, 42, 52, True),
                          (115, 103, 45, 63, False)]:
            flame(c, *placement, bank=True)
    smoke(c, close)
    embers(c, close)
    chair(c, close)
    if close:
        dog_close(c)
        table(c, close)
        cup(c, 106, 104, 1.42)
        flame(c, -14, 134, 23, 45, True)
        speech(c)
    else:
        dog_wide(c)
        table(c, close)
        cup(c, 104, 77, 1)
        flame(c, -10, 134, 48, 100, True)
        flame(c, 100, 134, 53, 49, False)
    return c.image


def artwork(stage):
    canvas = Pixels(stage, "page", SIZE)
    for x, close in [(3, False), (147, True)]:
        canvas.image.paste(panel(stage, close), (x, 5))
        canvas.pen.rectangle((x-1, 4, x+138, 139), outline=COLORS["trim"])
    return canvas.image


def silhouette():
    result = Image.new("RGB", SIZE, COLORS["page"])
    for x, close in [(3, False), (147, True)]:
        c = Pixels(1, "wall_lit")
        chair(c, close)
        (dog_close if close else dog_wide)(c)
        table(c, close)
        cup(c, 106 if close else 104, 104 if close else 77, 1.42 if close else 1)
        background = Image.new("RGB", PANEL, COLORS["wall_lit"])
        difference = ImageChops.difference(c.image, background).convert("L")
        mask = difference.point(lambda value: 255 if value else 0)
        background.paste(COLORS["ink"], (0, 0, *PANEL), mask)
        result.paste(background, (x, 5))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--block-in", action="store_true")
    args = parser.parse_args()
    steps = Path(__file__).resolve().parents[1] / "build" / "steps"
    steps.mkdir(parents=True, exist_ok=True)
    silhouette().save(steps / "01_silhouette.png")
    artwork(1).save(steps / "02_blockin.png")
    if not args.block_in:
        artwork(2).save(steps / "03_shading.png")
        artwork(3).save(steps / "04_cleanup.png")


if __name__ == "__main__":
    main()
