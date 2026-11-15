"""Score fixed historical corner raw data with frozen16-clear-pixel support."""
from pathlib import Path
import csv,json
import numpy as np
O=Path(__file__).resolve().parent
def clean(v):
    if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple,np.ndarray)):return [clean(x) for x in v]
    if isinstance(v,np.generic):return clean(v.item())
    if isinstance(v,float) and not np.isfinite(v):return None
    return v
groups={}
for label,d in [('candidate','history-screen-increment'),('additive','history-rim-bounded'),('original','history-reference')]:
    for r in csv.DictReader((O/d/'corner-profiles.csv').open()):
        assert r['mode']=='raw';key=(r['scene'],r['corner'],float(r['depth_pt']));p='native' if r['platform']=='native' else label
        if p=='native' and label!='candidate':continue
        groups.setdefault(key,{}).setdefault(p,[]).append(r)
z=np.arange(-3,4);k=np.exp(-.5*(z/1.5)**2);k/=k.sum()
def curve(a):
    dst=[np.full_like(a,np.nan) for _ in range(3)];ok=np.isfinite(a).all(1);runs=np.flatnonzero(np.diff(np.r_[False,ok,False])).reshape(-1,2)
    for st,en in runs:
        if en-st<16:continue
        sm=np.stack([np.convolve(np.pad(a[st:en,j],3,mode='reflect'),k,'valid') for j in range(3)],1);d1=np.gradient(sm,.5,axis=0);d2=np.gradient(d1,.5,axis=0)
        for d,s in zip(dst,[sm,d1,d2]):d[st:en]=s
    return [a]+dst
metrics=[]
for key,plat in groups.items():
    ds=np.array([float(r['horizontal_inward_pt']) for r in plat['native']]);v={p:curve(np.array([[float(r['raw_'+ch]) if r['raw_'+ch] else np.nan for ch in 'rgb'] for r in rr])) for p,rr in plat.items()}
    for scope,inside in [('whole_fixed_scan',np.ones(len(ds),bool)),('inward_only',ds>=0)]:
        for idx,field in enumerate(['raw','smooth','d1','d2']):
            for ref in ['additive','original']:
                n,b,c=[v[p][idx] for p in ['native',ref,'candidate']];valid=inside&np.isfinite(n).all(1)&np.isfinite(b).all(1)&np.isfinite(c).all(1)
                if not valid.any():continue
                before=np.abs(b[valid]-n[valid]);after=np.abs(c[valid]-n[valid]);x=before.mean();y=after.mean()
                metrics.append({'scene':key[0],'corner':key[1],'depth_pt':key[2],'reference':ref,'scope':scope,'field':field,'valid_original_pixels':int(valid.sum()),'minimum_contiguous_clear_pixels_for_derivatives':16,'baseline_native_rgb_mae':before.mean(0),'candidate_native_rgb_mae':after.mean(0),'baseline_native_mean_mae':x,'candidate_native_mean_mae':y,'direction':'improved' if y<x-1e-9 else ('regressed' if y>x+1e-9 else 'unchanged')})
record={'color_policy':'All decoded raw and ICC data independently verified identical; one raw curve per pixel retained.','minimum_contiguous_clear_pixels_for_derivatives':16,'legacy_export_note':'Original historical CSV exports also retain legacy7-support derivative columns. This report recomputes smooth/D1/D2 exclusively from their original raw RGB with the frozen16-support gate; the legacy derivative columns are not used in these final corner interpretation metrics.','metrics':metrics}
(O/'rim-screen-history-corner16-metrics.json').write_text(json.dumps(clean(record),indent=2,allow_nan=False)+'\n')
print(json.dumps({'corner_metrics':len(metrics),'support':16}))
