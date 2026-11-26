"""Draw three periodic, fractured rock faces on a 128-pixel grid."""
from pathlib import Path
import numpy as np
from PIL import Image

N = 128
ROOT = Path(__file__).resolve().parents[2]
palettes = {
 'rose': ['#202221','#303330','#414440','#525550','#666863','#7b7d76','#91928a','#aaa9a0','#c1bfb3'],
 'lavender': ['#2b211e','#3f3029','#554036','#6c4e3e','#83604b','#99755a','#b08c6e','#c4a68a','#dbc3a8'],
 'sand': ['#262525','#393735','#4c4946','#5f5b57','#74706b','#89847e','#9e9992','#b4afa7','#cbc5bc'],
}

def make(name, seed, tilt):
 rng = np.random.default_rng(seed)
 y,x = np.mgrid[:N,:N]
 def smooth_noise(size):
  a=rng.normal(0,1,(size,size))
  fx=x*size/N; fy=y*size/N
  ix=fx.astype(int); iy=fy.astype(int); tx=fx-ix; ty=fy-iy
  return ((1-ty)*((1-tx)*a[iy,ix]+tx*a[iy,(ix+1)%size])
          +ty*((1-tx)*a[(iy+1)%size,ix]+tx*a[(iy+1)%size,(ix+1)%size]))
 wx=x+4.2*smooth_noise(8)+1.5*smooth_noise(16)
 wy=y+4.2*smooth_noise(8)+1.5*smooth_noise(16)
 # Long irregular rock masses. The metric shears the cells into slanted facets.
 points = rng.uniform(0,N,(37,2))
 distances=[]
 for px,py in points:
  options=[]
  for dx in (-N,0,N):
   for dy in (-N,0,N):
    vx=wx-(px+dx); vy=wy-(py+dy)
    u=vx + tilt*vy
    options.append((u/12)**2 + (vy/23)**2)
  distances.append(np.minimum.reduce(options))
 dist=np.array(distances)
 order=np.argsort(dist,axis=0)
 first=order[0]; second=order[1]
 d1=np.take_along_axis(dist,first[None],axis=0)[0]
 d2=np.take_along_axis(dist,second[None],axis=0)[0]
 gap=d2-d1
 # Interpolate periodic fields to avoid visible square noise cells.
 broad=smooth_noise(8); medium=smooth_noise(16)
 fine=smooth_noise(32); grit=smooth_noise(64)
 cell=rng.uniform(-1.05,1.05,len(points))[first]
 # A lit side and a shadowed side within each diagonal slab.
 dx=((x-points[first,0]+N/2)%N)-N/2
 dy=((y-points[first,1]+N/2)%N)-N/2
 plane=np.clip((dx+tilt*dy)/13,-1,1)
 value=4.4+cell+0.7*plane+0.50*broad+0.46*medium+0.29*fine+0.17*grit
 value-=np.where(gap<0.09,2.1,np.where(gap<0.21,0.9,0))
 # Discontinuous angular fractures across the grain, with thin lit edges.
 fracture=((np.mod(wx+2*wy,51)<1.3)&(medium<-.25)&(gap>.14))
 value-=fracture*1.5
 value+=((gap>.20)&(gap<.31)&(plane<-.2))*0.7
 pal=np.array([tuple(bytes.fromhex(c[1:])) for c in palettes[name]],dtype=np.uint8)
 steps=ROOT/f'pastel-cliffs-{name}'/'build'/'steps'; steps.mkdir(parents=True,exist_ok=True)
 def save(v,file): Image.fromarray(pal[np.clip(np.rint(v),0,8).astype(int)]).save(steps/file)
 save(4+cell-(gap<.15)*2,'01_silhouette.png')
 save(4+cell+plane-(gap<.15)*2,'02_blockin.png')
 save(value-0.17*grit,'03_shading.png')
 save(value,'04_cleanup.png')

if __name__=='__main__':
 make('rose',19,.50)
 make('lavender',47,.65)
 make('sand',83,-.40)
