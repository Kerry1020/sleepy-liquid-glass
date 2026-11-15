"""Frozen all-reference probe scoring from original raw tracks; no fit."""
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
def write(n,v):(O/n).write_text(json.dumps(clean(v),indent=2,allow_nan=False)+'\n')
z=np.arange(-3,4);kernel=np.exp(-.5*(z/1.5)**2);kernel/=kernel.sum()
def curves(a,minimum):
    out=[np.full_like(a,np.nan) for _ in range(3)];ok=np.isfinite(a).all(1);runs=np.flatnonzero(np.diff(np.r_[False,ok,False])).reshape(-1,2)
    for st,en in runs:
        if en-st<minimum:continue
        sm=np.stack([np.convolve(np.pad(a[st:en,j],3,mode='reflect'),kernel,'valid') for j in range(3)],1);d1=np.gradient(sm,.5,axis=0);d2=np.gradient(d1,.5,axis=0)
        for d,s in zip(out,[sm,d1,d2]):d[st:en]=s
    return [a]+out
allgroups={};metrics=[];peaks=[];luma=np.array([.2126,.7152,.0722])
for track in ['straight','corner']:
    groups={}
    for label,prefix,platform in [('candidate','budget','candidate'),('native','budget','native'),('body8','body8','candidate'),('additive','rim-bounded','candidate'),('screen','rim-screen','candidate')]:
        for r in csv.DictReader((O/f'{prefix}-{track}-tracks.csv').open()):
            if r['platform']!=platform:continue
            key=(r['input'],r['carrier'],r['segment']) if track=='straight' else (r['input'],r['carrier'],r['corner'],float(r['depth_pt']))
            groups.setdefault(key,{}).setdefault(label,[]).append(r)
    allgroups[track]=groups
    for key,plats in groups.items():
        assert set(plats)=={'candidate','native','body8','additive','screen'},(track,key,plats.keys())
        ds=np.array([float(r['distance_pt']) for r in plats['native']]);vals={}
        for label,rr in plats.items():
            assert np.array_equal(ds,np.array([float(r['distance_pt']) for r in rr])),(track,key,label)
            a=np.array([[float(r['raw_'+ch]) if r['raw_'+ch] else np.nan for ch in 'rgb'] for r in rr]);vals[label]=curves(a,16 if track=='corner' else 3)
        scopes=[('whole_fixed_scan',np.ones(len(ds),bool)),('inward_only',ds>=0)] if track=='corner' else [(f'bin_{lo}_{hi}',(ds>=lo)&(ds<hi)) for lo,hi in [(-6,0),(0,2),(2,4),(4,12),(12,20),(20,24)]]
        for scope,inside in scopes:
            for ii,field in enumerate(['raw','smooth','d1','d2']):
                for ref in ['body8','additive','screen']:
                    n,b,c=[vals[p][ii] for p in ['native',ref,'candidate']];valid=inside&np.isfinite(n).all(1)&np.isfinite(b).all(1)&np.isfinite(c).all(1)
                    if not valid.any():continue
                    before=np.abs(b[valid]-n[valid]);after=np.abs(c[valid]-n[valid]);x=before.mean();y=after.mean()
                    q={'input':key[0],'carrier':key[1],'track':track,'reference':ref,'scope':scope,'field':field,'valid_original_normal_samples':int(valid.sum()),'baseline_native_rgb_mae':before.mean(0),'candidate_native_rgb_mae':after.mean(0),'baseline_native_mean_mae':x,'candidate_native_mean_mae':y,'candidate_vs_reference_max_abs':np.abs(c[valid]-b[valid]).max(),'direction':'improved' if y<x-1e-9 else ('regressed' if y>x+1e-9 else 'unchanged'),'reference_scope':'combined Sheet12to10 response' if key[1]=='sheet' and ref in ['body8','additive'] else 'same radius/material; declared floor-composition comparison'}
                    if track=='straight':q['segment']=key[2]
                    else:q['corner']=key[2];q['depth_pt']=key[3]
                    metrics.append(q)
        if track=='straight' and key[0]=='panel_probe_shapes' and key[1]=='alert' and key[2].startswith('neutral_'):
            for label,v in vals.items():
                a=v[0];ok=np.isfinite(a).all(1);ys=a@luma;rim=(ds>=0)&(ds<4)&ok;sh=(ds>=8)&(ds<12)&ok
                if not rim.any() or not sh.any():continue
                shoulder=ys[sh].mean();pi=np.flatnonzero(rim)[np.argmax(ys[rim])];peak=ys[pi];ex=peak-shoulder;half=shoulder+.5*ex;high=(ys>=half)&ok if ex>0 else np.zeros(len(ds),bool);le=ri=pi
                while le>0 and high[le-1]:le-=1
                while ri+1<len(ds) and high[ri+1]:ri+=1
                br=le>0 and ri+1<len(ds) and ok[le-1] and ok[ri+1] and ex>0;lc=rc=None
                if br:lc=ds[le-1]+(half-ys[le-1])/(ys[le]-ys[le-1])*.5;rc=ds[ri]+(half-ys[ri])/(ys[ri+1]-ys[ri])*.5
                support=ri-le+1;resolved=br and support>=3
                peaks.append({'segment':key[2],'platform':label,'diagnostic_only':key[2]=='neutral_bottom','raw_argmax_inset_pt':ds[pi],'minimum_sampling_uncertainty_pt':.25,'peak_rgb':a[pi],'peak_luma':peak,'shoulder_8_12_luma':shoulder,'peak_minus_shoulder_luma':ex,'minimum8_count_contrast_gate':bool(ex>=8),'halfheight_support_pixels':support,'bracketed':br,'linear_crossings_pt_diagnostic':[lc,rc],'FWHM_pt':rc-lc if resolved else None,'FWHM_status':'identified_raster_diagnostic' if resolved else 'unresolved_fewer_than3pixels_or_missing_crossing'})
write('budget-all-reference-probe-metrics.json',metrics);write('budget-all-reference-neutral-peaks.json',peaks)
summary=[]
for ref in ['body8','additive','screen']:
    rr=[r for r in metrics if r['reference']==ref and r['carrier']=='alert' and r['track']=='corner' and r['scope']=='whole_fixed_scan' and r['field']=='raw']
    summary.append({'reference':ref,'alert_corner_raw_whole_scan':{d:sum(r['direction']==d for r in rr) for d in ['improved','regressed','unchanged']}})
write('budget-all-reference-probe-summary.json',summary);print(json.dumps(clean({'comparison_counts':summary,'neutral':peaks}),indent=2))
