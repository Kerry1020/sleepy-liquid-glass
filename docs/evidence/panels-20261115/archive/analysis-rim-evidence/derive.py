from pathlib import Path
import csv
import numpy as np
O=Path(__file__).resolve().parent
rows=list(csv.DictReader((O/'tracks.csv').open()));groups={}
for r in rows:groups.setdefault((r['carrier'],r['segment']),[]).append(r)
kernel=np.exp(-np.arange(-3,4)**2/(2*1.5**2));kernel/=kernel.sum();out=[]
for (c,s),rr in groups.items():
 for plat in ['source',c+'_before',c+'_native',c+'_android']:
  a=np.array([[float(r[plat+'_'+ch]) for ch in 'rgb'] for r in rr]);good=np.isfinite(a).all(1);sm=np.full(a.shape,np.nan);d1=sm.copy();d2=sm.copy();ix=np.flatnonzero(np.diff(np.r_[False,good,False])).reshape(-1,2)
  for st,en in ix:
   v=a[st:en]
   if len(v)>1:
    pad=np.pad(v,((3,3),(0,0)),mode='reflect');sm[st:en]=np.stack([np.convolve(pad[:,j],kernel,'valid') for j in range(3)],axis=1)
   else:sm[st:en]=v
   if en-st>=3:d1[st:en]=np.gradient(sm[st:en],.5,axis=0);d2[st:en]=np.gradient(d1[st:en],.5,axis=0)
  for i,r in enumerate(rr):
   v={'carrier':c,'segment':s,'platform':plat,'distance_pt':r['distance_pt'],'retained_pixels':r['retained_pixels']}
   for label,aa in [('raw',a),('smoothed',sm),('d1',d1),('d2',d2)]:
    for j,ch in enumerate('rgb'):v[label+'_'+ch]=aa[i,j] if np.isfinite(aa[i,j]) else ''
   out.append(v)
with (O/'curves-and-derivatives.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
