from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
N = 64
palettes = {
    'rose': ['#e7b9b4', '#f4d6c7', '#d49d9f', '#bd8993', '#fbe8d1', '#d9ada9'],
    'lavender': ['#c4bddb', '#ded7e8', '#aaa5ca', '#918fb9', '#eee8ed', '#b9b4d0'],
    'sand': ['#ddc8ab', '#f2e1c1', '#cbb093', '#b69989', '#fbefd7', '#ddc5aa'],
}

def wrap(draw, shape, coords, fill, width=1):
    for dx in (-N, 0, N):
        for dy in (-N, 0, N):
            pts = [(x+dx, y+dy) for x, y in coords]
            if shape == 'polygon': draw.polygon(pts, fill=fill)
            else: draw.line(pts, fill=fill, width=width, joint='curve')

def build(name, p):
    base, light, shade, dark, glint, mid = p
    steps = ROOT / 'build' / 'steps'
    steps.mkdir(parents=True, exist_ok=True)
    img = Image.new('RGB', (N, N), base)
    d = ImageDraw.Draw(img)
    # Broad, irregular horizontal strata: all shapes wrap on the 64px torus.
    bands = [
      [(-8, 3), (3, 3), (3, 5), (15, 5), (15, 3), (26, 3), (26, 5), (39, 5), (39, 3), (53, 3), (53, 4), (68, 4), (68, 10), (55, 10), (55, 11), (41, 11), (41, 9), (27, 9), (27, 11), (10, 11), (10, 10), (-8, 10)],
      [(-6, 25), (8, 25), (8, 23), (21, 23), (21, 25), (34, 25), (34, 23), (47, 23), (47, 25), (59, 25), (59, 23), (69, 23), (69, 30), (53, 30), (53, 31), (36, 31), (36, 29), (20, 29), (20, 31), (5, 31), (5, 30), (-6, 30)],
      [(-5, 45), (6, 45), (6, 43), (20, 43), (20, 45), (34, 45), (34, 44), (49, 44), (49, 42), (60, 42), (60, 44), (69, 44), (69, 50), (55, 50), (55, 51), (39, 51), (39, 49), (23, 49), (23, 51), (8, 51), (8, 50), (-5, 50)],
    ]
    for poly in bands: wrap(d, 'polygon', poly, shade)
    img.save(steps / '01_silhouette.png')
    for poly in bands:
        wrap(d, 'line', poly[:8], light, 2)
        wrap(d, 'line', poly[8:16], dark, 1)
    # Chunky faces between ledges.
    faces = [[(3,11),(14,11),(14,14),(12,14),(12,20),(8,22),(2,21)],
             [(26,10),(36,10),(36,13),(39,13),(39,20),(34,23),(27,21)],
             [(49,11),(59,10),(62,12),(62,20),(57,23),(50,21)],
             [(11,31),(20,30),(23,32),(23,40),(19,43),(12,41)],
             [(34,30),(44,31),(46,33),(46,40),(42,43),(35,42)],
             [(56,31),(67,30),(68,40),(63,43),(57,41)],
             [(-4,51),(7,51),(9,54),(9,61),(4,64),(-3,62)],
             [(20,51),(29,50),(32,53),(32,61),(28,64),(21,62)],
             [(43,50),(53,51),(55,54),(55,61),(51,64),(44,62)]]
    for poly in faces: wrap(d, 'polygon', poly, mid)
    img.save(steps / '02_blockin.png')
    for poly in faces:
        x,y=poly[0]
        wrap(d,'line',[(x,y+2),(x,y+7),(x+2,y+9)],light)
        wrap(d,'line',[(x+10,y+2),(x+10,y+7),(x+8,y+10)],shade)
    cracks = [[(19,12),(19,15),(21,15),(21,18),(20,18),(20,20)],
              [(44,13),(44,16),(42,16),(42,19)], [(1,33),(1,36),(-1,36),(-1,39)],
              [(27,33),(27,36),(29,36),(29,39)], [(50,34),(50,38),(48,38),(48,40)],
              [(14,53),(14,56),(16,56),(16,59)], [(38,53),(38,56),(36,56),(36,59)],
              [(59,54),(59,57),(61,57),(61,60)]]
    for c in cracks: wrap(d,'line',c,dark)
    img.save(steps / '03_shading.png')
    for x,y,w in [(5,4,5),(29,4,6),(43,4,5),(10,24,6),(36,24,7),(54,24,5),(7,44,5),(25,44,5),(50,43,5),(-2,44,4)]:
        wrap(d,'line',[(x,y),(x+w,y)],glint)
    for x,y in [(16,17),(24,20),(46,20),(6,38),(31,40),(53,39),(12,59),(34,59),(57,61)]:
        wrap(d,'line',[(x,y),(x+2,y)],shade)
    img.save(steps / '04_cleanup.png')

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 2:
        ROOT = Path(sys.argv[2]).resolve()
    build(sys.argv[1], palettes[sys.argv[1]])
