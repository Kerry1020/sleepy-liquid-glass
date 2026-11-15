from pathlib import Path
import csv,hashlib,json,io
import numpy as np
from PIL import Image,ImageCms
P=Path(__file__).resolve().parent.parent;O=Path(__file__).resolve().parent
B=P/'panels-alert-outline-zero-20261115';C=P/'panels-alert-body8-20261115';N=P/'native-panel-feasibility-preparation'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
PLAN=json.loads((P/'panel-probes-preparation/analysis-plan.json').read_text());G=json.loads((P/'analysis-native-probes/geometry-and-mask.json').read_text())
bm=json.loads((B/'matrix.json').read_text());cm=json.loads((C/'matrix.json').read_text());captures={p:{(r['background'],'sheet' if r['carrier']=='share_sheet' else r['carrier']):r for r in m['captures']} for p,m in [('baseline',bm),('candidate',cm)]}
ATT=json.loads((N/'attachments/manifest.json').read_text())[0]['attachments'];native={}
for t in ATT:
 s=t['suggestedHumanReadableName']
 for sid in PLAN['selected_ids']:
  for car in ['alert','sheet']:
   if sid+'-light-'+car+'-rest_0_' in s and t['exportedFileName'].endswith('.png'):native[(sid,car)]=N/'attachments'/t['exportedFileName']
cache={};dec=[]
def load(p):
 if p in cache:return cache[p]
 im=Image.open(p);raw=np.asarray(im.convert('RGBA'));ic=im.info.get('icc_profile');rgb=im.convert('RGB');n=np.asarray(ImageCms.profileToProfile(rgb,ImageCms.ImageCmsProfile(io.BytesIO(ic)),ImageCms.createProfile('sRGB'),outputMode='RGB')) if ic else raw[:,:,:3];nr=np.dstack([n,raw[:,:,3]]);assert np.array_equal(raw,nr)
 dec.append({'path':str(p),'sha256':sha(p),'size':list(im.size),'raw_icc_identical':True});cache[p]=raw.astype(float);return cache[p]
Y,X=np.mgrid[0:1334,0:750];X=(X+.5)/2;Y=(Y+.5)/2;masks={}
for g in G['union_foreground_boxes']:
 m=np.zeros((1334,750),bool)
 for x0,y0,x1,y1 in g['native_ax']+g['android_actual_layout']:m|=(X>=x0-2)&(X<x1+2)&(Y>=y0-2)&(Y<y1+2)
 masks[(g['input'],g['carrier'])]=m

def diff(a,b):
 assert a.shape==b.shape and a.size>0
 d=np.abs(a-b);return {'samples':int(d.size),'changed_channels':int(np.count_nonzero(d)),'max_abs':float(d.max()),'mean_abs':float(d.mean())}
def roi(a,r,origin=(0,0)):
 x0,y0,x1,y1=r;x0-=origin[0];x1-=origin[0];y0-=origin[1];y1-=origin[1];assert 0<=x0<x1<=a.shape[1] and 0<=y0<y1<=a.shape[0];return a[y0:y1,x0:x1]
def clean(x):
 if isinstance(x,dict):return {k:clean(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [clean(v) for v in x]
 if isinstance(x,np.ndarray):return clean(x.tolist())
 if isinstance(x,(float,np.floating)):return float(x) if np.isfinite(x) else None
 if isinstance(x,np.integer):return int(x)
 return x
def write(name,v):(O/name).write_text(json.dumps(clean(v),indent=2,allow_nan=False)+'\n')
def csvwrite(name,rr):
 keys=list(dict.fromkeys(k for r in rr for k in r))
 with (O/name).open('w') as f:w=csv.DictWriter(f,keys);w.writeheader();w.writerows(clean(rr))
controls=[];images={}
for key,cc in captures['candidate'].items():
 sid,car=key;bc=captures['baseline'][key]
 assert bc['window_geometry']['captured_surface_screen_rect_px']==cc['window_geometry']['captured_surface_screen_rect_px']
 assert bc['actual_alert_layout']==cc['actual_alert_layout']
 bw=load(B/bc['window_png']);cw=load(C/cc['window_png']);bs=load(B/bc['screen_png']);cs=load(C/cc['screen_png']);images[key]={'baseline':bs[:,:,:3],'candidate':cs[:,:,:3],'native':load(native[key])[:,:,:3]}
 origin=cc['window_geometry']['captured_surface_screen_rect_px'][:2];r=[55,515,695,859] if car=='alert' else [16,635,734,1318];deep=[r[0]+80,r[1]+80,r[2]-80,r[3]-80];near=[r[0]+8,r[1]+8,r[2]-8,r[3]-8]
 bodies={}
 for name,b in PLAN['body_rois_pt'][car].items():
  box=[round(v*2) for v in b];m=roi(masks[key],box);bb=roi(bs,box)[~m];qq=roi(cs,box)[~m];bodies[name]=diff(bb,qq) if bb.size else {'no_unmasked_samples':True}
 controls.append({'input':sid,'carrier':car,'actual_window':diff(bw,cw),'full_screen':diff(bs,cs),'visible_app_screen':diff(bs[80:1302],cs[80:1302]),'deep80_rect_px':deep,'deep80_rgba':diff(roi(bw,deep,origin),roi(cw,deep,origin)),'eroded8_bounding_diagnostic':diff(roi(bw,near,origin),roi(cw,near,origin)),'original_body_rois':bodies})

kernel=np.exp(-np.arange(-3,4)**2/(2*1.5**2));kernel/=kernel.sum()
def curve(v):
 sm=np.full(v.shape,np.nan);d1=sm.copy();d2=sm.copy();ok=np.isfinite(v).all(1);runs=np.flatnonzero(np.diff(np.r_[False,ok,False])).reshape(-1,2)
 for st,en in runs:
  if en-st<2:continue
  pad=np.pad(v[st:en],((3,3),(0,0)),mode='reflect');sm[st:en]=np.stack([np.convolve(pad[:,j],kernel,'valid') for j in range(3)],axis=1)
  if en-st>=3:d1[st:en]=np.gradient(sm[st:en],.5,axis=0);d2[st:en]=np.gradient(d1[st:en],.5,axis=0)
 return sm,d1,d2
rows=[];metrics=[];bins=[(-6,0),(0,2),(2,4),(4,12),(12,20),(20,24)]
segments=PLAN['straight']+[{'carrier':'alert','segment':'neutral_'+s,'axis':axis,'boundary_pt':b,'inward_sign':sgn,'tangent_half_open_pt':[lo,hi],'last_inward_pt_exclusive':12,'status':'fixed_neutral_followup'} for s,lo,hi,b,sgn,axis in [('top',140,235,257.5,1,'y'),('bottom',140,235,429.5,-1,'y'),('left',353,359,27.5,1,'x'),('right',353,359,347.5,-1,'x')]]
for key,sets in images.items():
 sid,car=key;mask=masks[key]
 for seg in [s for s in segments if s['carrier']==car]:
  d=np.arange(-5.75,seg['last_inward_pt_exclusive'],.5);t=np.arange(seg['tangent_half_open_pt'][0]+.25,seg['tangent_half_open_pt'][1],.5);ni=np.floor(2*(seg['boundary_pt']+seg['inward_sign']*d)).astype(int);ti=np.floor(2*t).astype(int);yy,xx=(ti[:,None],ni[None,:]) if seg['axis']=='x' else (ni[None,:],ti[:,None]);m=mask[yy,xx];raws={}
  for plat,a in sets.items():
   v=a[yy,xx];raw=np.array([v[:,i][~m[:,i]].mean(0) if (~m[:,i]).any() else [np.nan]*3 for i in range(len(d))]);raws[plat]=raw;sm,d1,d2=curve(raw)
   for i,di in enumerate(d):rows.append({'input':sid,'carrier':car,'segment':seg['segment'],'platform':plat,'distance_pt':di,'clear_pixels':int((~m[:,i]).sum()),**{label+'_'+ch:ar[i,j] for label,ar in [('raw',raw),('smooth',sm),('d1',d1),('d2',d2)] for j,ch in enumerate('rgb')}})
  for lo,hi in bins:
   good=(d>=lo)&(d<hi)&np.isfinite(raws['native']).all(1)
   if not good.any():continue
   n=raws['native'][good];b=raws['baseline'][good];c=raws['candidate'][good];metrics.append({'input':sid,'carrier':car,'segment':seg['segment'],'bin_pt':[lo,hi],'baseline_native_rgb_mae':np.abs(b-n).mean(0),'candidate_native_rgb_mae':np.abs(c-n).mean(0),'baseline_native_mean_mae':float(np.abs(b-n).mean()),'candidate_native_mean_mae':float(np.abs(c-n).mean()),'baseline_candidate':diff(b,c)})

corners=[];corner_metrics=[]
for key,sets in images.items():
 sid,car=key;mask=masks[key]
 for top in [True,False]:
  for left in [True,False]:
   bx=(27.5 if left else 347.5) if car=='alert' else (8 if left else 367);by=(257.5 if top else 429.5) if car=='alert' else (317.5 if top else 659)
   depths=[4.25,8.25,12.25,16.25,20.25,24.25] if car=='alert' else ([4.25,8.25,12.25,16.25,20.25,24.25,28.25,32.25] if top else [4.25,8.25,12.25,16.25]);last=28 if car=='alert' else (40 if top else 24)
   for dep in depths:
    ds=np.arange(-5.75,last,.5);xx=np.floor(2*(bx+(1 if left else -1)*ds)).astype(int);yy=int(2*(by+(1 if top else -1)*dep));mm=mask[yy,xx];vals={}
    for plat,a in sets.items():
     v=a[yy,xx].copy();v[mm]=np.nan;vals[plat]=v;sm,d1,d2=curve(v)
     for i,di in enumerate(ds):corners.append({'input':sid,'carrier':car,'corner':('top' if top else 'bottom')+'_'+('left' if left else 'right'),'depth_pt':dep,'distance_pt':di,'masked':bool(mm[i]),'platform':plat,**{label+'_'+ch:ar[i,j] for label,ar in [('raw',v),('smooth',sm),('d1',d1),('d2',d2)] for j,ch in enumerate('rgb')}})
    valid=~mm;n=vals['native'][valid];b=vals['baseline'][valid];c=vals['candidate'][valid]
    if valid.any():corner_metrics.append({'input':sid,'carrier':car,'corner':('top' if top else 'bottom')+'_'+('left' if left else 'right'),'depth_pt':dep,'samples':int(valid.sum()),'baseline_native_mean_mae':float(np.abs(b-n).mean()),'candidate_native_mean_mae':float(np.abs(c-n).mean()),'baseline_candidate':diff(b,c)})
write('body8-controls.json',controls);write('body8-straight-metrics.json',metrics);write('body8-corner-metrics.json',corner_metrics);write('body8-decode.json',dec);csvwrite('body8-straight-tracks.csv',rows);csvwrite('body8-corner-tracks.csv',corners)
print('controls')
for r in controls:print(r['input'],r['carrier'],'actualwindow',r['actual_window'],'deep',r['deep80_rgba'])
print('neutral first4pt')
for r in metrics:
 if r['input']=='panel_probe_shapes' and r['segment'].startswith('neutral_') and r['bin_pt'] in [[0,2],[2,4]]:print(r['segment'],r['bin_pt'],round(r['baseline_native_mean_mae'],4),'->',round(r['candidate_native_mean_mae'],4))
print('corner changed')
for r in corner_metrics:
 if r['carrier']=='alert' and r['baseline_candidate']['max_abs']>0:print(r['input'],r['corner'],r['depth_pt'],round(r['baseline_native_mean_mae'],4),'->',round(r['candidate_native_mean_mae'],4))
