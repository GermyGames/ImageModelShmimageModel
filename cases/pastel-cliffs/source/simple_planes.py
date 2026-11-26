"""Low-detail, repeating cliff planes drawn on a native pixel grid."""
from pathlib import Path
from PIL import Image, ImageDraw
from pixel_cliffs import PALETTES, polygon, line, N

ROOT = Path(__file__).resolve().parents[2]
# Boundaries meet themselves at the top and bottom of the tile.
edges = [
 [(-5,0),(-2,18),(-7,33),(-4,52),(-9,70),(-6,84),(-5,96)],
 [(19,0),(23,18),(18,33),(22,52),(17,70),(20,84),(19,96)],
 [(43,0),(40,17),(45,35),(41,53),(47,68),(44,83),(43,96)],
 [(69,0),(73,16),(68,34),(72,51),(67,68),(71,83),(69,96)],
 [(91,0),(94,18),(89,33),(92,52),(87,70),(90,84),(91,96)],
]
facets = [
 ([(19,0),(23,18),(18,33),(15,42),(12,35),(16,19),(12,11)],4),
 ([(45,35),(41,53),(47,68),(43,75),(37,62),(39,47)],4),
 ([(69,0),(73,16),(68,34),(64,41),(61,32),(67,18),(61,8)],4),
 ([(92,52),(87,70),(90,84),(87,94),(82,83),(84,70),(80,62)],4),
 ([(0,51),(4,41),(8,44),(7,59),(12,69),(8,79),(3,67)],3),
 ([(20,84),(19,96),(24,105),(30,99),(27,89),(32,80),(29,74),(23,79)],4),
]
cracks = [
 [(12,11),(15,15),(14,20),(17,23)],
 [(31,7),(30,15),(33,20),(31,26)],
 [(54,29),(58,33),(57,38),(62,42)],
 [(84,45),(80,49),(82,54),(79,59)],
 [(7,43),(11,46),(10,51),(13,54)],
 [(30,63),(33,66),(38,65)],
 [(55,78),(59,81),(58,87),(62,91)],
 [(81,3),(84,7),(83,11)],
]

def build(name):
 p=PALETTES[name]; steps=ROOT/f'pastel-cliffs-{name}'/'build'/'steps'
 for stage,filename in enumerate(('01_silhouette.png','02_blockin.png','03_shading.png','04_cleanup.png')):
  im=Image.new('RGB',(N,N),p[2]); d=ImageDraw.Draw(im)
  for i in range(4):
   polygon(d,edges[i]+list(reversed(edges[i+1])),p[2+(i%2)])
  if stage>=1:
   for pts,c in facets: polygon(d,pts,p[c])
  if stage>=2:
   for edge in edges[1:4]: line(d,edge,p[1])
   for pts in cracks: line(d,pts,p[1])
  if stage>=3:
   for pts in [[(16,10),(20,17),(17,26)],[(63,8),(68,16),(65,27)],[(41,50),(39,58),(42,66)]]:
    line(d,pts,p[5])
  im.save(steps/filename)

if __name__=='__main__':
 for name in PALETTES: build(name)
