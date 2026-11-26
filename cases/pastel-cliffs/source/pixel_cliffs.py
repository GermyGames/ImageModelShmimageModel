"""Hand-placed facets for seamless pixel-art cliff faces."""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
N = 96
PALETTES = {
    'rose': ['#292d3e','#34394e','#41445b','#505267','#626273','#777480','#908a8e','#a8a199'],
    'lavender': ['#332b36','#41343f','#51404a','#62505a','#75626a','#887579','#a08d88','#b4a397'],
    'sand': ['#30323b','#3a3e49','#484c57','#595c66','#6c6d76','#807f86','#99958f','#ada79b'],
}
# Interlocking slabs, intentionally varied in size and lean. Coordinates cross
# the canvas boundary, so the exact same shapes continue on the opposite edge.
SLABS = [
 [(-9,-8),(8,-12),(19,-5),(22,7),(15,19),(3,23),(-8,14),(-14,3)],
 [(18,-10),(34,-14),(46,-7),(44,5),(38,12),(40,22),(27,27),(15,19),(22,7)],
 [(45,-9),(62,-12),(71,-3),(69,8),(75,17),(63,25),(51,22),(39,14),(44,4)],
 [(71,-8),(86,-13),(101,-6),(106,4),(101,17),(91,23),(75,17),(69,8)],
 [(-13,16),(3,22),(13,20),(21,29),(18,43),(9,51),(-5,48),(-13,39)],
 [(18,22),(28,26),(40,21),(51,26),(54,38),(48,49),(34,52),(22,47),(18,42),(21,30)],
 [(51,21),(63,25),(75,18),(84,26),(87,39),(80,48),(68,51),(54,40),(54,31)],
 [(83,22),(94,22),(103,17),(111,26),(110,40),(102,48),(87,43),(86,31)],
 [(-10,46),(9,51),(18,44),(25,51),(23,64),(16,76),(3,78),(-8,70),(-13,58)],
 [(24,49),(35,52),(48,49),(56,57),(55,69),(45,79),(30,78),(20,70),(23,60)],
 [(54,45),(68,51),(80,47),(87,53),(88,67),(78,78),(64,77),(55,69),(56,57)],
 [(86,44),(100,48),(109,42),(113,56),(107,70),(97,77),(87,71),(88,57)],
 [(-9,73),(3,78),(15,75),(25,82),(22,95),(13,102),(-1,101),(-10,93)],
 [(23,75),(31,78),(45,78),(51,88),(45,101),(34,108),(20,98),(23,88)],
 [(46,76),(62,77),(78,76),(80,87),(70,99),(58,104),(46,98),(50,88)],
 [(79,75),(96,77),(106,72),(111,86),(104,99),(90,104),(79,96),(80,87)],
]

def shifted(points, dx, dy): return [(x+dx,y+dy) for x,y in points]
def polygon(d, pts, color):
 for dx in (-N,0,N):
  for dy in (-N,0,N): d.polygon(shifted(pts,dx,dy),fill=color)
def line(d,pts,color):
 for dx in (-N,0,N):
  for dy in (-N,0,N): d.line(shifted(pts,dx,dy),fill=color,width=1)

def build(name):
 p=PALETTES[name]; steps=ROOT/f'pastel-cliffs-{name}'/'build'/'steps'
 for stage,filename in enumerate(('01_silhouette.png','02_blockin.png','03_shading.png','04_cleanup.png')):
  img=Image.new('RGB',(N,N),p[0])
  for i,pts in enumerate(SLABS):
   mask=Image.new('L',(N,N)); polygon(ImageDraw.Draw(mask),pts,255)
   rock=Image.new('RGB',(N,N),p[1+(i*7%2)]); d=ImageDraw.Draw(rock)
   a,b,c=pts[0],pts[1],pts[2]
   cx=sum(x for x,y in pts)//len(pts); cy=sum(y for x,y in pts)//len(pts)
   if stage >= 1:
    polygon(d,[a,b,c,(cx+3,cy-3),(cx-3,cy+3),pts[-1]],p[3+i%2])
   if stage >= 2:
    if i%4==0:
     polygon(d,[b,c,((c[0]+cx)//2,(c[1]+cy)//2),(cx,cy-2)],p[5])
    elif i%4==1:
     polygon(d,[b,((b[0]+c[0])//2,(b[1]+c[1])//2),(cx+2,cy-3),(cx-1,cy+2),(cx-4,cy-2)],p[5])
    elif i%4==2:
     polygon(d,[c,(c[0]+1,c[1]+5),(cx+4,cy+5),(cx+1,cy),(cx+2,cy-4)],p[5])
    polygon(d,[pts[-1],(cx-3,cy+3),(cx,cy+8),pts[-2]],p[2])
    if i%3 != 1:
     line(d,[(cx-4,cy+2),(cx-1,cy+4),(cx,cy+8),(cx+4,cy+10)],p[1])
     line(d,[(cx-1,cy+4),(cx+2,cy+3),(cx+4,cy+1)],p[2])
   if stage >= 3 and i%4==0:
    x,y=pts[1]; line(d,[(x-2,y+2),(x+2,y+1),(x+5,y+3)],p[7])
   if stage >= 3 and i%4==2:
    x,y=pts[2]; line(d,[(x-3,y+3),(x-1,y+5),(x-1,y+8)],p[6])
   img.paste(rock,(0,0),mask)
  img.save(steps/filename)

if __name__=='__main__':
 for name in PALETTES: build(name)
