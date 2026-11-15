from pathlib import Path
import json,hashlib,csv,io
import numpy as np
from PIL import Image,ImageCms
P=Path(__file__).resolve().parent.parent; O=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
M=json.loads((P/'native-panel-feasibility-preparation/attachments/manifest.json').read_text())[0]['attachments'];N={}
for t in M:
 s=t['suggestedHumanReadableName']
 if 'panel_probe_shapes-light-' in s and t['exportedFileName'].endswith('.png'):N[s.split('panel_probe_shapes-light-')[1].split('_0_')[0]]=P/'native-panel-feasibility-preparation/attachments'/t['exportedFileName']
G=json.loads((P/'analysis-native-probes/geometry-and-mask.json').read_text())
paths={'source':P/'panel-probes-preparation/inputs/panel_probe_shapes.png'}
for c in ['alert','sheet']:
 paths[c+'_native']=N[c+'-rest'];paths[c+'_before']=N['before-alert-context' if c=='alert' else 'after-alert-before-sheet-context'];paths[c+'_android']=P/'panels-nonperiodic-baseline-20261115'/('panel_probe_shapes-light-'+('share_sheet' if c=='sheet' else c)+'-rest-screen.png')
ims={};dec=[]
for k,p in paths.items():
 im=Image.open(p);a=np.asarray(im.convert('RGB'));ic=im.info.get('icc_profile');norm=np.asarray(ImageCms.profileToProfile(im.convert('RGB'),ImageCms.ImageCmsProfile(io.BytesIO(ic)),ImageCms.createProfile('sRGB'),outputMode='RGB')) if ic else a.copy();assert np.array_equal(a,norm);ims[k]=a.astype(float);dec.append({'key':k,'path':str(p),'sha256':sha(p),'size':im.size,'raw_icc_identical':True})
yy,xx=np.mgrid[0:1334,0:750];xx=(xx+.5)/2;yy=(yy+.5)/2;masks={}
for g in G['union_foreground_boxes']:
 if g['input']!='panel_probe_shapes':continue
 m=np.zeros((1334,750),bool)
 for x0,y0,x1,y1 in g['native_ax']+g['android_actual_layout']:m|=(xx>=x0-2)&(xx<x1+2)&(yy>=y0-2)&(yy<y1+2)
 masks[g['carrier']]=m
segments=[('alert','top',140,235,257.5,1,'y'),('alert','bottom',140,235,429.5,-1,'y'),('alert','left',353,359,27.5,1,'x'),('alert','right',353,359,347.5,-1,'x'),('sheet','top_left_neutral',140,160,317.5,1,'y'),('sheet','top_right_neutral',215,235,317.5,1,'y'),('sheet','bottom',140,235,659,-1,'y')]
rows=[];summ=[];lum=np.array([.2126,.7152,.0722]);ds=np.arange(-1.75,12,.5)
for c,s,lo,hi,b,sgn,axis in segments:
 ti=np.arange(round(lo*2),round(hi*2));ni=np.floor((b+sgn*ds)*2).astype(int); profiles={}; ranges={}; retained=[]
 for idx,d in enumerate(ds):
  ys,xs=(ni[idx]*np.ones_like(ti),ti) if axis=='y' else (ti,ni[idx]*np.ones_like(ti));good=~masks[c][ys,xs];retained.append(int(good.sum()))
  r={'carrier':c,'segment':s,'distance_pt':d,'retained_pixels':int(good.sum()),'excluded_pixels':int((~good).sum())}
  for k in ['source',c+'_before',c+'_native',c+'_android']:
   v=ims[k][ys,xs][good];mean=v.mean(0) if len(v) else np.full(3,np.nan);ran=np.ptp(v,axis=0) if len(v) else np.full(3,np.nan);profiles.setdefault(k,[]).append(mean);ranges.setdefault(k,[]).append(ran)
   for j,ch in enumerate('rgb'):r[k+'_'+ch]=mean[j];r[k+'_range_'+ch]=ran[j]
  rows.append(r)
 profiles={k:np.array(v) for k,v in profiles.items()};ranges={k:np.array(v) for k,v in ranges.items()};q={'carrier':c,'segment':s,'retained_min':min(retained),'tangent_count':len(ti),'direct_foreground_all_clear':min(retained)==len(ti),'profiles':{}}
 for k,v in profiles.items():
  valid=np.isfinite(v).all(1);q['profiles'][k]={'max_tangent_rgb_range':np.nanmax(ranges[k],axis=0).tolist() if valid.any() else None}
  if k not in [c+'_native',c+'_android'] or not valid.any():continue
  ys=v@lum; rim=(ds>=0)&(ds<4)&valid;shoulder=(ds>=8)&(ds<12)&valid
  if not rim.any() or not shoulder.any():continue
  body=float(ys[shoulder].mean());ii=np.where(rim)[0];peakidx=ii[np.argmax(ys[rim])];peak=float(ys[peakidx]);ex=peak-body;half=body+.5*ex
  # A bounded local peak needs clear bracketing samples; don't invent FWHM from an edge step.
  high=(ys>=half)&valid if ex>0 else np.zeros(len(ds),bool);left=peakidx;right=peakidx
  while left>0 and high[left-1]:left-=1
  while right+1<len(ds) and high[right+1]:right+=1
  brack=left>0 and right+1<len(ds) and valid[left-1] and valid[right+1] and ex>0
  w=None
  if brack and right-left+1>=3:
   a=ds[left-1]+(.5*(ys[left]-ys[left-1]) if False else (half-ys[left-1])/(ys[left]-ys[left-1])*.5)
   z=ds[right]+(half-ys[right])/(ys[right+1]-ys[right])*.5;w=float(z-a)
  q['profiles'][k].update({'shoulder_8_12_mean_luma':body,'rim_peak_luma':peak,'peak_location_pt':float(ds[peakidx]),'peak_minus_shoulder_luma':ex,'halfheight_support_pixels':int(right-left+1),'bracketed':bool(brack),'FWHM_pt':w,'FWHM_status':'identified_raster_diagnostic' if w is not None else 'unresolved_fewer_than_3_pixels_or_missing_crossing'})
 summ.append(q)
with (O/'tracks.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in rows for k in r)));w.writeheader();w.writerows(rows)
(O/'inputs.json').write_text(json.dumps(dec,indent=2)+'\n');(O/'summary.json').write_text(json.dumps(summ,indent=2,allow_nan=False)+'\n')
print(json.dumps(summ,indent=2))
