"""Complete frozen public rim diagnostics. No fitting, shifting or new ROI."""
from pathlib import Path
import csv, hashlib, io, json
import numpy as np
from PIL import Image, ImageCms

O=Path(__file__).resolve().parent; P=O.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def clean(v):
    if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple,np.ndarray)):return [clean(x) for x in v]
    if isinstance(v,np.generic):return clean(v.item())
    if isinstance(v,float) and not np.isfinite(v):return None
    return v
def write(name,v):(O/name).write_text(json.dumps(clean(v),indent=2,allow_nan=False)+'\n')
def writecsv(name,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with (O/name).open('w',newline='') as f:
        w=csv.DictWriter(f,keys);w.writeheader();w.writerows(clean(rows))
def readcsv(p):return list(csv.DictReader(p.open()))
def number(s):return float(s) if s else float('nan')
PLAN=json.loads((P/'panel-probes-preparation/analysis-plan.json').read_text())
assert sha(O/'rim-next-frozen-plan.md')=='179c6679b5400d5fd8551279b4ad99fc82eb456c8fa01203d62d0cf235ca10ac'
G=json.loads((P/'analysis-native-probes/geometry-and-mask.json').read_text())
N=P/'native-panel-feasibility-preparation'; ATT=json.loads((N/'attachments/manifest.json').read_text())[0]['attachments']
native={}
for a in ATT:
    for sid in PLAN['selected_ids']:
        for car in ['alert','sheet']:
            if sid+'-light-'+car+'-rest_0_' in a['suggestedHumanReadableName'] and a['exportedFileName'].endswith('.png'):
                native[(sid,car)]=N/'attachments'/a['exportedFileName']
B=P/'panels-alert-body8-20261115'; C=P/'panels-alert-rim-bounded-20261115'
caps={}
for platform,d in [('baseline',B),('candidate',C)]:
    caps[platform]={(r['background'],'sheet' if r['carrier']=='share_sheet' else r['carrier']):r for r in json.loads((d/'matrix.json').read_text())['captures']}
cache={}; dec=[]
def load(p):
    if p in cache:return cache[p]
    im=Image.open(p); raw=np.asarray(im.convert('RGB')); ic=im.info.get('icc_profile')
    if ic:
        norm=np.asarray(ImageCms.profileToProfile(im.convert('RGB'),ImageCms.ImageCmsProfile(io.BytesIO(ic)),ImageCms.createProfile('sRGB'),outputMode='RGB'))
    else:
        assert 'srgb' in im.info,(p,'undeclared color space');norm=raw.copy()
    assert np.array_equal(raw,norm)
    dec.append({'path':str(p),'sha256':sha(p),'raw_icc_identical':True});cache[p]=raw;return raw
Y,X=np.mgrid[0:1334,0:750];X=(X+.5)/2;Y=(Y+.5)/2;masks={}
for g in G['union_foreground_boxes']:
    m=np.zeros((1334,750),bool)
    for x0,y0,x1,y1 in g['native_ax']+g['android_actual_layout']:m|=(X>=x0-2)&(X<x1+2)&(Y>=y0-2)&(Y<y1+2)
    masks[(g['input'],g['carrier'])]=m
segments=PLAN['straight']+[{'carrier':'alert','segment':'neutral_'+s,'axis':ax,'boundary_pt':bd,'inward_sign':sg,'tangent_half_open_pt':[lo,hi],'last_inward_pt_exclusive':12} for s,lo,hi,bd,sg,ax in [('top',140,235,257.5,1,'y'),('bottom',140,235,429.5,-1,'y'),('left',353,359,27.5,1,'x'),('right',353,359,347.5,-1,'x')]]
cliprows=[]; pointrows=[]
def clip_stats(a):
    return {'pixel_count':len(a),'channel255':(a==255).sum(0),'channel0':(a==0).sum(0),'any255':int(np.any(a==255,1).sum()),'RGB255':int(np.all(a==255,1).sum()),'any0':int(np.any(a==0,1).sum()),'RGB0':int(np.all(a==0,1).sum())}
def addclip(meta,vals):
    for plat,a in vals.items():
        cliprows.append({**meta,'platform':plat,**clip_stats(a)})
    b=vals['baseline'];c=vals['candidate'];n=vals['native']
    q={**meta,'pixel_count':len(c)}
    for val,label in [(255,'255'),(0,'0')]:
        for other,ref in [(b,'baseline'),(n,'native')]:
            newly=(c==val)&(other!=val)
            q['candidate_new_'+label+'_vs_'+ref+'_channels']=newly.sum(0)
            q['candidate_new_'+label+'_vs_'+ref+'_any_pixels']=int(newly.any(1).sum())
    pointrows.append(q)
for key,cc in caps['candidate'].items():
    sid,car=key;bc=caps['baseline'][key];ims={'baseline':load(B/bc['screen_png']),'candidate':load(C/cc['screen_png']),'native':load(native[key])};m=masks[key]
    for s in [x for x in segments if x['carrier']==car]:
        ds=np.arange(-5.75,s['last_inward_pt_exclusive'],.5);ts=np.arange(s['tangent_half_open_pt'][0]+.25,s['tangent_half_open_pt'][1],.5)
        nn=np.floor(2*(s['boundary_pt']+s['inward_sign']*ds)).astype(int);tt=np.floor(2*ts).astype(int)
        for di,ni in zip(ds,nn):
            yy,xx=(tt,np.full_like(tt,ni)) if s['axis']=='x' else (np.full_like(tt,ni),tt);good=~m[yy,xx]
            addclip({'input':sid,'carrier':car,'track':'straight','segment':s['segment'],'distance_pt':di,'masked_pixels':int((~good).sum())},{plat:a[yy,xx][good] for plat,a in ims.items()})
    for top in [True,False]:
        for left in [True,False]:
            bx=(27.5 if left else 347.5) if car=='alert' else (8 if left else 367)
            by=(257.5 if top else 429.5) if car=='alert' else (317.5 if top else 659)
            deps=[4.25,8.25,12.25,16.25,20.25,24.25] if car=='alert' else ([4.25,8.25,12.25,16.25,20.25,24.25,28.25,32.25] if top else [4.25,8.25,12.25,16.25])
            last=28 if car=='alert' else (40 if top else 24)
            for dep in deps:
                ds=np.arange(-5.75,last,.5);xx=np.floor(2*(bx+(1 if left else -1)*ds)).astype(int);yy=int(2*(by+(1 if top else -1)*dep))
                for di,xi in zip(ds,xx):
                    good=not m[yy,xi]
                    addclip({'input':sid,'carrier':car,'track':'corner','corner':('top' if top else 'bottom')+'_'+('left' if left else 'right'),'depth_pt':dep,'distance_pt':di,'masked_pixels':int(not good)},{plat:a[yy,xi][None,:] if good else np.empty((0,3),np.uint8) for plat,a in ims.items()})
write('rim-bounded-clipping-all-fixed.json',cliprows)
write('rim-bounded-clipping-pointwise.json',pointrows)
write('rim-bounded-completion-decode.json',dec)
clip_summary=[]
for sid,car,track in sorted({(r['input'],r['carrier'],r['track']) for r in pointrows}):
    rr=[r for r in pointrows if r['input']==sid and r['carrier']==car and r['track']==track and r['distance_pt']>=0]
    clip_summary.append({'input':sid,'carrier':car,'track':track,'scope':'original inward-only fixed samples; overlaps retained, not unique pixel total','new255_channels_vs_body8':sum(sum(r['candidate_new_255_vs_baseline_channels']) for r in rr),'new0_channels_vs_body8':sum(sum(r['candidate_new_0_vs_baseline_channels']) for r in rr),'rows_with_new255_vs_body8':[r for r in rr if sum(r['candidate_new_255_vs_baseline_channels'])]})
write('rim-bounded-clipping-summary.json',clip_summary)

# The frozen neutral peak/shoulder calculation, retaining unresolved crossings.
groups={}
for r in readcsv(O/'rim-bounded-straight-tracks.csv'):
    if r['input']=='panel_probe_shapes' and r['carrier']=='alert' and r['segment'].startswith('neutral_'):
        groups.setdefault((r['segment'],r['platform']),[]).append(r)
peaks=[];luma=np.array([.2126,.7152,.0722])
for (seg,plat),rr in groups.items():
    ds=np.array([float(r['distance_pt']) for r in rr]);vs=np.array([[float(r['raw_'+ch]) for ch in 'rgb'] for r in rr]);ok=np.isfinite(vs).all(1);ys=vs@luma
    rim=(ds>=0)&(ds<4)&ok;sh=(ds>=8)&(ds<12)&ok
    if not rim.any() or not sh.any():continue
    shoulder=ys[sh].mean();pi=np.flatnonzero(rim)[np.argmax(ys[rim])];peak=ys[pi];ex=peak-shoulder;half=shoulder+.5*ex;high=(ys>=half)&ok if ex>0 else np.zeros(len(ds),bool);le=ri=pi
    while le>0 and high[le-1]:le-=1
    while ri+1<len(ds) and high[ri+1]:ri+=1
    br=le>0 and ri+1<len(ds) and ok[le-1] and ok[ri+1] and ex>0
    lc=rc=None
    if br:
        lc=ds[le-1]+(half-ys[le-1])/(ys[le]-ys[le-1])*.5;rc=ds[ri]+(half-ys[ri])/(ys[ri+1]-ys[ri])*.5
    support=ri-le+1;resolved=br and support>=3
    peaks.append({'segment':seg,'platform':plat,'diagnostic_only':seg=='neutral_bottom','peak_location_pt':ds[pi],'minimum_sampling_uncertainty_pt_per_platform':.25,'peak_rgb':vs[pi],'peak_luma':peak,'shoulder_8_12_mean_luma':shoulder,'peak_minus_shoulder_luma':ex,'half_height_luma':half,'halfheight_support_pixels':support,'bracketed':br,'linear_crossings_pt_diagnostic':[lc,rc],'FWHM_pt':rc-lc if resolved else None,'FWHM_status':'identified_raster_diagnostic' if resolved else 'unresolved_fewer_than_3_pixels_or_missing_crossing','first4_raw_rows':[{'distance_pt':ds[i],'rgb':vs[i],'luma':ys[i]} for i in np.flatnonzero(rim)]})
write('rim-bounded-neutral-peaks.json',peaks)

# Preserve every corner and separately score RGB, smoothed RGB, D1 and D2.
# Derivatives require the plan's 16 contiguous clear original samples.
z=np.arange(-3,4);kernel=np.exp(-.5*(z/1.5)**2);kernel/=kernel.sum()
def derivatives(a,minimum):
    result=[np.full_like(a,np.nan) for _ in range(3)];ok=np.isfinite(a).all(1)
    runs=np.flatnonzero(np.diff(np.r_[False,ok,False])).reshape(-1,2)
    for st,en in runs:
        if en-st<minimum:continue
        sm=np.stack([np.convolve(np.pad(a[st:en,j],3,mode='reflect'),kernel,'valid') for j in range(3)],1)
        d1=np.gradient(sm,.5,axis=0);d2=np.gradient(d1,.5,axis=0)
        for dst,src in zip(result,[sm,d1,d2]):dst[st:en]=src
    return [a]+result
cg={}
for r in readcsv(O/'rim-bounded-corner-tracks.csv'):
    key=(r['input'],r['carrier'],r['corner'],float(r['depth_pt']));cg.setdefault(key,{}).setdefault(r['platform'],[]).append(r)
cm=[]
for key,plats in cg.items():
    ds=np.array([float(r['distance_pt']) for r in plats['native']]);vv={p:derivatives(np.array([[number(r['raw_'+ch]) for ch in 'rgb'] for r in rr]),16) for p,rr in plats.items()}
    for scope,inside in [('whole_fixed_scan',np.ones(len(ds),bool)),('inward_only',ds>=0)]:
        for ii,field in enumerate(['raw','smooth','d1','d2']):
            n,b,c=[vv[p][ii] for p in ['native','baseline','candidate']];valid=inside&np.isfinite(n).all(1)&np.isfinite(b).all(1)&np.isfinite(c).all(1)
            if not valid.any():continue
            e1=np.abs(b[valid]-n[valid]);e2=np.abs(c[valid]-n[valid]);a=e1.mean();q=e2.mean()
            cm.append({'input':key[0],'carrier':key[1],'corner':key[2],'depth_pt':key[3],'scope':scope,'field':field,'valid_original_pixels':int(valid.sum()),'minimum_contiguous_clear_original_pixels_for_derivatives':16,'baseline_native_rgb_mae':e1.mean(0),'candidate_native_rgb_mae':e2.mean(0),'baseline_native_mean_mae':a,'candidate_native_mean_mae':q,'direction':'improved' if q<a-1e-9 else ('regressed' if q>a+1e-9 else 'unchanged')})
write('rim-bounded-corner-complete-metrics.json',cm)

# Historical four-source light combination; exact original analysis metrics.
old=json.loads((O/'history-reference/analysis.json').read_text());new=json.loads((O/'history-rim-bounded/analysis.json').read_text())
os={s['scene']:s for s in old['scenes']};changes=[];summaries=[]
for ns in new['scenes']:
    sid=ns['scene'];bs=os[sid];assert bs['files']['native']['sha256']==ns['files']['native']['sha256']
    for mode in ['raw','icc_srgb']:
        aa=bs['tracks'][mode];bb=ns['tracks'][mode]
        for name in aa['body']:
            a=aa['body'][name]['rgb_rmse'];b=bb['body'][name]['rgb_rmse'];changes.append({'scene':sid,'mode':mode,'region':'body','name':name,'field':'rgb_rmse','baseline':a,'candidate':b})
        for name in aa['straight']:
            for field in ['rgb_rmse_inward_0_20','d1_rgb_rmse_inward_0_20','d2_rgb_rmse_inward_0_20']:
                changes.append({'scene':sid,'mode':mode,'region':'straight','name':name,'field':field,'baseline':aa['straight'][name][field],'candidate':bb['straight'][name][field]})
        for name in aa['corner']:
            for a,b in zip(aa['corner'][name],bb['corner'][name]):
                assert a['depth_pt']==b['depth_pt'] and a['sample_count']==b['sample_count']
                for field in ['rgb_rmse','d1_rgb_rmse','d2_rgb_rmse']:
                    if a[field] is not None and b[field] is not None:changes.append({'scene':sid,'mode':mode,'region':'corner','name':name,'depth_pt':a['depth_pt'],'field':field,'baseline':a[field],'candidate':b[field]})
for r in changes:
    r['delta']=r['candidate']-r['baseline'];r['direction']='improved' if r['delta']< -1e-9 else ('regressed' if r['delta']>1e-9 else 'unchanged')
for sid in os:
    rr=[r for r in changes if r['scene']==sid and r['mode']=='raw']
    summaries.append({'scene':sid,'attribution':'blur+rim combination vs original factory, not rim alone' if sid.endswith('-light') else 'strict unchanged control','body_rgb':{d:sum(r['region']=='body' and r['direction']==d for r in rr) for d in ['improved','regressed','unchanged']},'straight_rgb':{d:sum(r['region']=='straight' and r['field']=='rgb_rmse_inward_0_20' and r['direction']==d for r in rr) for d in ['improved','regressed','unchanged']},'corner_rgb':{d:sum(r['region']=='corner' and r['field']=='rgb_rmse' and r['direction']==d for r in rr) for d in ['improved','regressed','unchanged']}})
write('rim-bounded-history-metric-changes.json',changes);write('rim-bounded-history-summary.json',summaries)

summary={'schema':1,'frozen_plan_sha256':sha(O/'rim-next-frozen-plan.md'),'coordinates':'original 750x1334; no warp/resize/registration or ROI movement','color':'all independently decoded raw/ICC results identical','neutral_peaks':peaks,'clipping':clip_summary,'new_probe_corner_raw_whole_scan':{d:sum(r['carrier']=='alert' and r['field']=='raw' and r['scope']=='whole_fixed_scan' and r['direction']==d for r in cm) for d in ['improved','regressed','unchanged']},'history':summaries,'limits':['Public calibration only; no independent heldout or motion proof.','Native peak FWHM stays unresolved under original minimum3px rule.','Any corner/source regression blocks an all-rim/all-background improvement claim.','Sheet top neutral samples remain excluded by original conservative grabber mask.']}
write('rim-bounded-completion-summary.json',summary)
print(json.dumps(clean({'clip_rows':len(cliprows),'pointwise_rows':len(pointrows),'corner_metrics':len(cm),'new_probe_corners':summary['new_probe_corner_raw_whole_scan'],'history':summaries,'peaks':[{k:r[k] for k in ['segment','platform','peak_location_pt','halfheight_support_pixels','FWHM_pt']} for r in peaks]}),indent=2))
