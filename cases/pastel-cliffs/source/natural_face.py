"""Seamless pixel cliff: irregular warped planes with sparse fissures."""
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
N=256
PALETTES={
 'rose':['#292e39','#383d4b','#484d5a','#595e69','#6d7179','#848589','#a09d98'],
 'lavender':['#302a2b','#403635','#51443f','#645148','#796154','#907568','#aa9380'],
 'sand':['#302f30','#403f3e','#52504e','#64615e','#797572','#8e8a83','#aaa49a'],
}

def make(name,seed):
 rng=np.random.default_rng(seed); y,x=np.mgrid[:N,:N]
 def field(size):
  a=rng.normal(size=(size,size)); fx=x*size/N; fy=y*size/N
  ix=fx.astype(int); iy=fy.astype(int); u=fx-ix; v=fy-iy
  u=u*u*(3-2*u); v=v*v*(3-2*v)
  return ((1-v)*((1-u)*a[iy,ix]+u*a[iy,(ix+1)%size])+
          v*((1-u)*a[(iy+1)%size,ix]+u*a[(iy+1)%size,(ix+1)%size]))
 # These fields only displace and reshape broad planes; no grain is added.
 wx=x+5*field(6)+2*field(14); wy=y+5*field(6)+2*field(14)
 pts=rng.uniform(0,N,(54,2)); distances=[]; vectors=[]
 for px,py in pts:
  options=[]; vxlist=[]; vylist=[]
  for ox in (-N,0,N):
   for oy in (-N,0,N):
    vx=wx-(px+ox); vy=wy-(py+oy)
    options.append(((vx+.44*vy)/20)**2+(vy/35)**2); vxlist.append(vx); vylist.append(vy)
  options=np.array(options); choice=options.argmin(axis=0)
  distances.append(np.take_along_axis(options,choice[None],axis=0)[0])
  vectors.append(np.take_along_axis(np.array(vxlist),choice[None],axis=0)[0]+.44*np.take_along_axis(np.array(vylist),choice[None],axis=0)[0])
 dist=np.array(distances); order=np.argsort(dist,axis=0); nearest=order[0]; second=order[1]
 first=np.take_along_axis(dist,nearest[None],axis=0)[0]
 gap=np.take_along_axis(dist,second[None],axis=0)[0]-first
 vec=np.take_along_axis(np.array(vectors),nearest[None],axis=0)[0]
 cell=rng.choice([-1,0,0,0,1],len(pts))[nearest]
 face=3+cell+np.where(vec < -6,1,0)-np.where(vec>13,1,0)
 # A broken subset of cell edges becomes shadow, instead of an outline mesh.
 fracture_mask=field(7)+.45*field(13)
 shaded=face-np.where((gap<.17)&(fracture_mask>.0),1,0)
 shaded-=np.where((gap<.055)&(fracture_mask>.4),1,0)
 pal=np.array([tuple(bytes.fromhex(c[1:])) for c in PALETTES[name]],dtype=np.uint8)
 steps=ROOT/f'pastel-cliffs-{name}'/'build'/'steps'
 for values,file in [(3+cell,'01_silhouette.png'),(face,'02_blockin.png'),(shaded,'03_shading.png'),(shaded,'04_cleanup.png')]:
  Image.fromarray(pal[np.clip(values,0,len(pal)-1).astype(int)]).save(steps/file)

if __name__=='__main__':
 for n,s in [('rose',9),('lavender',21),('sand',44)]: make(n,s)
