#!/usr/bin/env python3
"""Fixed-coordinate public historical Alert diagnostics; no image warp or fit.

Usage: python3 -B analyze_alert_baseline.py [--android MATRIX_DIR] [--output DIR]
       [--compare-to previous/analysis.json]
Only four declared calibration backgrounds and their light/dark REST images enter.
"""
from __future__ import annotations
import argparse, csv, hashlib, io, json
from pathlib import Path
import numpy as np
from PIL import Image, ImageCms
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
NATIVE = ROOT / 'outputs/glass-native-parity-20261112/native-alert-optics-20261113'
DEFAULT = ROOT / 'artifacts/glass-panel-thickness-20261115/panels-current-baseline-20261115'
BACKGROUNDS = ('fine_grid', 'color_stripes', 'tonal_blocks', 'synthetic_landscape')
PANE = [55, 515, 695, 859]
LUMA = np.array([.2126, .7152, .0722])
BLUE = np.array([-.5, -.5, 1.])
EXTERIOR = [32, 176, 343, 220]
BODY = {'left_gutter': [49.5,307,54.5,338], 'right_gutter': [320.5,307,325.5,338],
        'left_gap': [60,350,110,359], 'right_gap': [265,350,315,359]}
NATIVE_FOREGROUND = [[57.5,279.5,317.5,300], [57.5,307,317.5,345],
                     [43.5,365.5,183.5,413.5], [191.5,365.5,331.5,413.5]]
EDGES = {'left': ('x',27.5,1,[[307,338]],24),
         'right': ('x',347.5,-1,[[307,338]],24),
         'top': ('y',257.5,1,[[62,104],[271,313]],20),
         'bottom': ('y',429.5,-1,[[62,104],[271,313]],10)}
DEPTHS = [4.25,8.25,12.25,16.25,20.25,24.25]

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rgb_hash(a): return hashlib.sha256(np.asarray(a,dtype=np.uint8).tobytes()).hexdigest()
def load(p):
    im=Image.open(p); assert im.size == (750,1334), (p,im.size)
    raw=im.convert('RGB'); icc=im.info.get('icc_profile')
    if icc:
        profile=ImageCms.ImageCmsProfile(io.BytesIO(icc))
        managed=ImageCms.profileToProfile(raw,profile,ImageCms.createProfile('sRGB'),outputMode='RGB',renderingIntent=1)
        action='embedded ICC -> sRGB, relative colorimetric, Pillow/LittleCMS'
        profile_name=ImageCms.getProfileName(profile).strip()
    else:
        assert 'srgb' in im.info, (p,'No ICC or sRGB declaration; do not assume')
        managed=raw.copy(); action='identity: PNG sRGB chunk, no ICC'; profile_name='PNG sRGB'
    a=np.asarray(raw,dtype=float); b=np.asarray(managed,dtype=float)
    return {'raw':a,'icc_srgb':b}, {'path':str(p),'sha256':sha(p),'size_px':list(im.size),
        'icc_bytes':len(icc or b''),'profile':profile_name,'normalization':action,
        'raw_rgb_sha256':rgb_hash(a),'icc_srgb_rgb_sha256':rgb_hash(b),
        'raw_equals_icc_srgb':bool(np.array_equal(a,b))}
def crop(a,r):
    l,t,r,b=(int(round(x*2)) for x in r); return a[t:b,l:r]
def grid(r):
    l,t,r,b=(int(round(v*2)) for v in r)
    return np.meshgrid((np.arange(l,r)+.5)/2,(np.arange(t,b)+.5)/2)
def clear(x,y,boxes):
    good=np.ones(np.broadcast_shapes(np.shape(x),np.shape(y)),dtype=bool)
    for l,t,r,b in boxes: good &= ~((x>=l-2)&(x<r+2)&(y>=t-2)&(y<b+2))
    return good
def sample(a,x,y):
    # All sampling coordinates are original pixel centers. No interpolation.
    x,y=np.broadcast_arrays(x,y); ix=x*2-.5; iy=y*2-.5
    assert np.max(np.abs(ix-np.round(ix))) < 1e-8
    assert np.max(np.abs(iy-np.round(iy))) < 1e-8
    return a[np.round(iy).astype(int),np.round(ix).astype(int)]
def stats(a,b):
    assert a.shape==b.shape and len(a)>0
    return {'sample_count':len(a),'native_mean_rgb':a.mean(0).tolist(),
        'android_mean_rgb':b.mean(0).tolist(),'mean_delta_rgb':(b-a).mean(0).tolist(),
        'rgb_rmse':float(np.sqrt(np.mean((a-b)**2))),
        'native_std_rgb':a.std(0).tolist(),'android_std_rgb':b.std(0).tolist()}
def transfer(a,b):
    a=a.reshape(-1,3);b=b.reshape(-1,3)
    g=np.sum(a*b,axis=0)/np.maximum(np.sum(a*a,axis=0),1e-12)
    return {'through_origin_gain_rgb':g.tolist(),
        'through_origin_gain_all_rgb':float(np.sum(a*b)/np.sum(a*a)),
        'residual_rgb_rmse':float(np.sqrt(np.mean((b-a*g)**2)))}
def smooth(a):
    # Fixed .75pt sigma, .5pt native spacing, 7-sample support; raw also retained.
    z=np.arange(-3,4);k=np.exp(-.5*(z/1.5)**2);k/=k.sum()
    return np.stack([np.convolve(np.pad(a[:,i],3,mode='reflect'),k,mode='valid') for i in range(3)],1)
def curves(a):
    sm=smooth(a);return sm,np.gradient(sm,.5,axis=0),np.gradient(np.gradient(sm,.5,axis=0),.5,axis=0)
def corr(a,b):
    a=a-a.mean(0);b=b-b.mean(0);den=np.sqrt(np.sum(a*a)*np.sum(b*b))
    return None if den<1e-8 else float(np.sum(a*b)/den)
def phase(a,b):
    # Numerical lag of fixed 1D appearance samples; no image is translated.
    rows=[]
    for lag in range(-4,5):
        aa=a[max(lag,0):len(a)+min(lag,0)]
        bb=b[max(-lag,0):len(b)-max(lag,0)]
        rows.append({'native_sample_offset_pt':lag*.5,'correlation':corr(aa,bb)})
    finite=[r for r in rows if r['correlation'] is not None]
    if not finite:return {'curve':rows,'best_native_offsets_pt':[],'identified':False}
    best=max(r['correlation'] for r in finite)
    return {'curve':rows,'best_native_offsets_pt':[r['native_sample_offset_pt'] for r in finite if r['correlation']>=best-1e-6],
        'identified':False,'limit':'Appearance phase only: periodic/content/blur/coverage ambiguity; no unique physical displacement.'}
def finite_derivatives(a):
    # Never differentiate across a foreground-masked NaN gap.
    out=[np.full_like(a,np.nan) for _ in range(3)]
    ok=np.isfinite(a).all(1);starts=np.flatnonzero(ok & ~np.r_[False,ok[:-1]])
    ends=np.flatnonzero(ok & ~np.r_[ok[1:],False])+1
    for st,en in zip(starts,ends):
        if en-st>=7:
            for dst,src in zip(out,curves(a[st:en])):dst[st:en]=src
    return out
def write_csv(p,fields,rows):
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def load_rgba(p):
    im=Image.open(p);raw=np.asarray(im.convert('RGBA'),dtype=np.int16)
    icc=im.info.get('icc_profile')
    if icc:
        rgb=ImageCms.profileToProfile(im.convert('RGB'),ImageCms.ImageCmsProfile(io.BytesIO(icc)),ImageCms.createProfile('sRGB'),outputMode='RGB',renderingIntent=1)
        managed=np.concatenate([np.asarray(rgb,dtype=np.int16),raw[:,:,3:4]],axis=2)
    else:
        assert 'srgb' in im.info,(p,'missing color declaration');managed=raw.copy()
    return {'raw':raw,'icc_srgb':managed}
def delta_pixels(a,b,mask=None):
    assert a.shape==b.shape
    if mask is not None:a=a[mask];b=b[mask]
    delta=np.abs(b.astype(float)-a.astype(float));changed=np.any(delta>0,axis=-1)
    return {'pixels':int(changed.size),'changed_pixels':int(changed.sum()),'maximum_abs_channel':float(delta.max(initial=0)),
        'rgb_or_rgba_rmse':float(np.sqrt(np.mean(delta**2))) if delta.size else None}
def candidate_compare(current,previous,current_dir,previous_path):
    old=json.loads(previous_path.read_text());assert old['body_rois_pt']==BODY and old['fixed_exterior_roi_pt']==EXTERIOR
    assert old['curve_spacing_pt']==.5 and old['foreground_union_expansion_pt']==2
    oldsc={s['scene']:s for s in old['scenes']};changes=[];scene_summary=[]
    for s in current['scenes']:
        q=oldsc[s['scene']];assert q['files']['native']['sha256']==s['files']['native']['sha256']
        group=[]
        for mode in ('raw','icc_srgb'):
            x=q['tracks'][mode];y=s['tracks'][mode]
            for name in BODY:
                assert x['body'][name]['sample_count']==y['body'][name]['sample_count']
                group.append((mode,'body',name,'rgb_rmse',x['body'][name]['rgb_rmse'],y['body'][name]['rgb_rmse']))
            for edge in EDGES:
                for key in ('rgb_rmse_inward_0_20','d1_rgb_rmse_inward_0_20','d2_rgb_rmse_inward_0_20'):
                    group.append((mode,'straight',edge,key,x['straight'][edge][key],y['straight'][edge][key]))
            for corner in ('TL','TR','BL','BR'):
                for u,v in zip(x['corner'][corner],y['corner'][corner]):
                    assert u['depth_pt']==v['depth_pt'] and u['sample_count']==v['sample_count']
                    for key in ('rgb_rmse','d1_rgb_rmse','d2_rgb_rmse'):
                        if u[key] is not None and v[key] is not None:group.append((mode,'corner',f'{corner}@{u["depth_pt"]}',key,u[key],v[key]))
        for mode,region,name,key,before,after in group:
            changes.append({'scene':s['scene'],'mode':mode,'region':region,'name':name,'metric':key,
                'before':before,'after':after,'delta_after_minus_before':after-before,
                'direction':'improved' if after<before-1e-9 else ('regressed' if after>before+1e-9 else 'unchanged')})
        raw=[r for r in changes if r['scene']==s['scene'] and r['mode']=='raw']
        scene_summary.append({'scene':s['scene'],'groups':{region:{direction:sum(r['region']==region and r['direction']==direction for r in raw)
            for direction in ('improved','regressed','unchanged')} for region in ('body','straight','corner')}})
    oldmat=json.loads(Path(old['android_matrix']).read_text());newmat=json.loads((current_dir/'matrix.json').read_text())
    oldcaps={(c['scene'],c['phase']):c for c in oldmat['captures']};controls=[]
    for c in newmat['captures']:
        key=(c['scene'],c['phase']);p=oldcaps[key]
        # Full-window controls include decoded RGBA, preserving transparent color/alpha.
        aa=load_rgba(Path(old['android_matrix']).parent/p['window_png']);bb=load_rgba(current_dir/c['window_png'])
        origin=c['window_geometry']['captured_surface_screen_rect_px'];assert origin==p['window_geometry']['captured_surface_screen_rect_px']
        for mode in ('raw','icc_srgb'):
            a=aa[mode];b=bb[mode]
            if c['carrier']=='share_sheet':
                controls.append({'scene':c['scene'],'mode':mode,'region':'full_sheet_window_rgba',**delta_pixels(a,b)})
            elif c['carrier']=='alert':
                h,w=a.shape[:2];xx,yy=np.meshgrid((np.arange(w)+origin[0]+.5)/2,(np.arange(h)+origin[1]+.5)/2)
                outside=(xx<27.5)|(xx>=347.5)|(yy<257.5)|(yy>=429.5)
                # Conservative central rectangle lies beyond every34dp corner extent;
                # unlike rectangular20dp erosion it does not misclassify curved corners.
                core=(xx>=61.5)&(xx<313.5)&(yy>=291.5)&(yy<395.5)
                boxes=NATIVE_FOREGROUND+next(s['android_foreground_pt'] for s in current['scenes'] if s['scene']==c['scene'].removesuffix('-alert'))
                controls.append({'scene':c['scene'],'mode':mode,'region':'alert_window_outside_pane_bbox',**delta_pixels(a,b,outside)})
                controls.append({'scene':c['scene'],'mode':mode,'region':'alert_conservative_deep_core_without_foreground',**delta_pixels(a,b,core&clear(xx,yy,boxes))})
                for m in c['measurements']:
                    if m['tag'] not in ('static-alert-confirm','static-alert-cancel'):continue
                    l,t,r,bottom=np.array(m['actual_screen_rect_px'])/2
                    mask=(xx>=l+8)&(xx<r-8)&(yy>=t+8)&(yy<bottom-8)
                    controls.append({'scene':c['scene'],'mode':mode,'region':m['tag']+'_inner8pt',**delta_pixels(a,b,mask)})
    return {'previous_analysis':str(previous_path),'previous_sha256':sha(previous_path),'metric_changes':changes,'scene_summary_raw':scene_summary,
        'pixel_controls':controls,'limit':'Fixed per-scene diagnostics only; no pooled winner/acceptance. Children are listed separately because they sample their parent material.'}
def cleaned(v):
    if isinstance(v,dict):return {k:cleaned(a) for k,a in v.items()}
    if isinstance(v,(list,tuple)):return [cleaned(a) for a in v]
    if isinstance(v,np.generic):return cleaned(v.item())
    if isinstance(v,float) and not np.isfinite(v):return None
    return v

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--android',type=Path,default=DEFAULT)
    ap.add_argument('--output',type=Path,default=Path(__file__).parent)
    ap.add_argument('--compare-to',type=Path);args=ap.parse_args()
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    matrix=json.loads((args.android/'matrix.json').read_text());assert matrix['status']=='passed'
    assert matrix['density']==2 and matrix['font_scale']==1
    caps=[c for c in matrix['captures'] if c['carrier']=='alert' and c['phase']=='rest']
    assert len(caps)==8
    delivery=json.loads((NATIVE/'delivery-validation.json').read_text())
    obs={x['condition'].replace('/','-'):x for x in delivery['observations']}
    result={'schema':1,'split':'public-historical-calibration','script_sha256':sha(__file__),
      'android_matrix':str(args.android/'matrix.json'),'android_matrix_sha256':sha(args.android/'matrix.json'),
      'native_delivery_sha256':sha(NATIVE/'delivery-validation.json'),'fixed_exterior_roi_pt':EXTERIOR,
      'body_rois_pt':BODY,'foreground_union_expansion_pt':2,'native_pane_ax_pt':[27.5,257.5,347.5,429.5],
      'android_required_pane_px':PANE,'curve_spacing_pt':.5,'derivative_smoothing':'fixed sigma.75pt,7samples; reflect endpoints; raw RGB retained',
      'coordinate_policy':'Original same-coordinate750x1334px display PNGs; no warp, resize, fitted translation, synthetic render or source substitution.',
      'color_policy':'raw encoded RGB and ICC-normalized sRGB independently evaluated; identity is recorded when PNG declares sRGB and has no ICC.',
      'limits':['REST carrier fixture, not full production page or motion proof.','Native fixed backing controls differ; body/exterior source identity does not prove refracted-footprint equality.',
        'Native AX is not an optical alpha mask. Corner scans are horizontal raster scans, not recovered contour normals.',
        'RGB derivatives/blue-opponent/appearance lag are response diagnostics, not physical thickness/dispersion or unique ray displacement.',
        'No aggregate acceptance threshold; all inputs are calibration.'], 'scenes':[]}
    straight_rows=[];corner_rows=[];ridge_rows=[];plots={};all_identity=True
    for c in sorted(caps,key=lambda x:x['scene']):
        bg=c['background'];th=c['theme'];assert bg in BACKGROUNDS and th in ('light','dark')
        scene=f'{bg}-{th}';o=obs[scene];prefix=f'alert-optics-{scene}'
        assert c['actual_alert_layout']['pane']['screen_rect_px']==PANE
        assert c['background_canvas']['screen_origin_px']==[0,0]
        assert c['background_canvas']['native_input_mapping']['actual_scale_xy']==[1,1]
        files={'native':NATIVE/'rest'/f'{prefix}-alert-rest.png',
               'native_before':NATIVE/'rest'/f'{prefix}-before.png',
               'native_source':NATIVE/'traces'/o['run']/'background-input.png',
               'android':args.android/c['screen_png'],
               'android_background':args.android/c['display_baseline_png']}
        images={};meta={}
        for key,p in files.items():images[key],meta[key]=load(p)
        assert meta['native']['sha256']==o['alertRest']['imageSHA256']
        identity=all(m['raw_equals_icc_srgb'] for m in meta.values());all_identity &= identity
        android_boxes=[(np.array(m['actual_screen_rect_px'])/2).tolist() for m in c['measurements']
            if m['tag'] in ('static-alert-title','static-alert-body','static-alert-confirm','static-alert-cancel')]
        assert len(android_boxes)==4;boxes=NATIVE_FOREGROUND+android_boxes
        rec={'scene':scene,'files':meta,'android_foreground_pt':android_boxes,'raw_equals_icc_srgb':identity,'tracks':{}}
        for mode in ('raw','icc_srgb'):
            ims={k:v[mode] for k,v in images.items()};n=ims['native'];a=ims['android']
            tr={'exterior':{'native':transfer(crop(ims['native_before'],EXTERIOR),crop(n,EXTERIOR)),
                'android':transfer(crop(ims['android_background'],EXTERIOR),crop(a,EXTERIOR)),
                'native_source_vs_before':stats(crop(ims['native_source'],EXTERIOR).reshape(-1,3),crop(ims['native_before'],EXTERIOR).reshape(-1,3)),
                'source_vs_android_background':stats(crop(ims['native_source'],EXTERIOR).reshape(-1,3),crop(ims['android_background'],EXTERIOR).reshape(-1,3))},
                'body':{},'straight':{},'corner':{},'blue_feature_tracks':{}}
            for name,r in BODY.items():
                x,y=grid(r);mask=clear(x,y,boxes);assert mask.sum()>0
                tr['body'][name]={'roi_pt':r,'available_pixels':int(mask.size),**stats(crop(n,r)[mask],crop(a,r)[mask])}
            for edge,(axis,boundary,sign,tangents,last) in EDGES.items():
                dist=np.arange(-5.75,last,.5);u=np.concatenate([np.arange(l+.25,r,.5) for l,r in tangents])
                v=boundary+sign*dist;x,y=(v[:,None],u[None,:]) if axis=='x' else (u[None,:],v[:,None])
                mask=clear(x,y,boxes);assert mask.all(),(scene,edge,'unexpected foreground')
                pn=sample(n,x,y).mean(1);pa=sample(a,x,y).mean(1);sn,dn,ddn=curves(pn);sa,da,dda=curves(pa)
                inside=(dist>=0)&(dist<min(last,20))
                blue_n=np.sum(sn*BLUE,axis=1);blue_a=np.sum(sa*BLUE,axis=1)
                tr['straight'][edge]={'normal_range_pt':[float(dist[0]),float(dist[-1])],'tangents_pt':tangents,
                    'rgb_rmse_inward_0_20':float(np.sqrt(np.mean((pn[inside]-pa[inside])**2))),
                    'd1_rgb_rmse_inward_0_20':float(np.sqrt(np.mean((dn[inside]-da[inside])**2))),
                    'd2_rgb_rmse_inward_0_20':float(np.sqrt(np.mean((ddn[inside]-dda[inside])**2))),
                    'native_blue_range_0_20':float(np.ptp(blue_n[inside])), 'android_blue_range_0_20':float(np.ptp(blue_a[inside])),
                    'native_blue_d1_rms':float(np.sqrt(np.mean(np.sum(dn[inside]*BLUE,axis=1)**2))),
                    'android_blue_d1_rms':float(np.sqrt(np.mean(np.sum(da[inside]*BLUE,axis=1)**2))),
                    'd1_rgb_appearance_lag':phase(dn[inside],da[inside])}
                if mode=='raw' or not identity:
                    for platform,p,s,d1,d2 in [('native',pn,sn,dn,ddn),('android',pa,sa,da,dda)]:
                        for i,position in enumerate(dist):
                            row={'mode':mode,'scene':scene,'platform':platform,'edge':edge,'normal_pt':float(position)}
                            for field,value in [('raw',p[i]),('smooth',s[i]),('d1',d1[i]),('d2',d2[i])]:
                                row.update({f'{field}_{ch}':float(value[k]) for k,ch in enumerate('rgb')})
                            straight_rows.append(row)
                if mode=='raw' and edge=='left':plots[scene]=(dist,pn,pa,dn,da,ddn,dda)
            for corner in ('TL','TR','BL','BR'):
                summaries=[];left=corner.endswith('L');top=corner.startswith('T')
                for depth in DEPTHS:
                    dist=np.arange(-5.75,28,.5);x=(27.5+dist) if left else (347.5-dist)
                    y=np.full_like(x,257.5+depth if top else 429.5-depth);mask=clear(x,y,boxes)
                    pn=sample(n,x,y);pa=sample(a,x,y);pn[~mask]=np.nan;pa[~mask]=np.nan
                    sn,dn,ddn=finite_derivatives(pn);sa,da,dda=finite_derivatives(pa)
                    valid=mask&(dist>=0);deriv=valid&np.isfinite(dn).all(1)&np.isfinite(da).all(1)
                    summaries.append({'depth_pt':depth,'sample_count':int(valid.sum()),
                        'rgb_rmse':float(np.sqrt(np.nanmean((pn[valid]-pa[valid])**2))),
                        'd1_rgb_rmse':float(np.sqrt(np.nanmean((dn[deriv]-da[deriv])**2))) if deriv.any() else None,
                        'd2_rgb_rmse':float(np.sqrt(np.nanmean((ddn[deriv]-dda[deriv])**2))) if deriv.any() else None})
                    if mode=='raw' or not identity:
                        for platform,p,s,d1,d2 in [('native',pn,sn,dn,ddn),('android',pa,sa,da,dda)]:
                            for i,position in enumerate(dist):
                                row={'mode':mode,'scene':scene,'platform':platform,'corner':corner,'depth_pt':depth,'horizontal_inward_pt':float(position),'clear':bool(mask[i])}
                                for field,value in [('raw',p[i]),('smooth',s[i]),('d1',d1[i]),('d2',d2[i])]:
                                    row.update({f'{field}_{ch}':float(value[k]) for k,ch in enumerate('rgb')})
                                corner_rows.append(row)
                tr['corner'][corner]=summaries
            # Frozen identifiable colored feature window, not an optical correspondence.
            if bg=='color_stripes':
                for band,ys in [('top',np.arange(259.75,277.5,.5)),('body',np.arange(350.25,359,.5)),('bottom',np.arange(415.75,427.5,.5))]:
                    xs=np.arange(60.25,96,.5);xx,yy=np.meshgrid(xs,ys);mask=clear(xx,yy,boxes);assert mask.all()
                    tracks={}
                    for platform,im in [('native',n),('android',a)]:
                        blue=np.sum(sample(im,xx,yy)*BLUE,axis=2);weight=np.maximum(blue,0)
                        den=weight.sum(1);center=np.divide(np.sum(weight*xs[None,:],axis=1),den,out=np.full(len(ys),np.nan),where=den>1e-8)
                        tracks[platform]={'centroid_x_range_pt':float(np.nanmax(center)-np.nanmin(center)),
                            'centroid_x_mean_pt':float(np.nanmean(center)),'blue_mean':float(blue.mean()),
                            'limit':'Positive blue-opponent centroid in fixed x60..96pt; source/color/blur response, not identified stripe ray.'}
                        if mode=='raw' or not identity:
                            for y,xc,amp in zip(ys,center,blue.max(1)):
                                ridge_rows.append({'mode':mode,'scene':scene,'platform':platform,'band':band,'y_pt':float(y),'positive_blue_centroid_x_pt':float(xc),'maximum_blue_opponent':float(amp)})
                    tr['blue_feature_tracks'][band]=tracks
            rec['tracks'][mode]=tr
        result['scenes'].append(rec)
    result['all_raw_equal_icc_srgb']=all_identity
    result['csv_modes']='raw only: all ICC tracks are byte-identical' if all_identity else 'raw plus distinct ICC tracks'
    channels=[f'{field}_{ch}' for field in ('raw','smooth','d1','d2') for ch in 'rgb']
    write_csv(out/'straight-profiles.csv',['mode','scene','platform','edge','normal_pt']+channels,straight_rows)
    write_csv(out/'corner-profiles.csv',['mode','scene','platform','corner','depth_pt','horizontal_inward_pt','clear']+channels,corner_rows)
    write_csv(out/'blue-feature-tracks.csv',['mode','scene','platform','band','y_pt','positive_blue_centroid_x_pt','maximum_blue_opponent'],ridge_rows)
    # Compact figures, generated only from fixed aggregate curves; no screenshot copies.
    for order,label in [(0,'response'),(1,'first-derivative'),(2,'second-derivative')]:
        fig,axs=plt.subplots(4,2,figsize=(11,11),sharex=True)
        for row,bg in enumerate(BACKGROUNDS):
            for col,th in enumerate(('light','dark')):
                scene=f'{bg}-{th}';v=plots[scene];ax=axs[row,col]
                pn,pa=(v[1],v[2]) if order==0 else ((v[3],v[4]) if order==1 else (v[5],v[6]))
                ax.plot(v[0],np.sum(pn*BLUE,axis=1),label='Native',color='#2357a1')
                ax.plot(v[0],np.sum(pa*BLUE,axis=1),label='Android',color='#c36d21');ax.axvline(0,color='.6',lw=.5)
                ax.set_title(scene,fontsize=9);ax.grid(alpha=.2)
                if row==3:ax.set_xlabel('Left inward normal, pt / dp')
                if col==0:ax.set_ylabel('B − (R+G)/2' + (' / pt' if order==1 else (' / pt²' if order==2 else '')))
        axs[0,0].legend(fontsize=8);fig.suptitle('Fixed left-edge blue-opponent '+label+' (encoded RGB; not physical dispersion)')
        fig.tight_layout();fig.savefig(out/f'left-edge-{label}.png',dpi=120);plt.close(fig)
    if args.compare_to:
        result['candidate_comparison']=candidate_compare(result,None,args.android,args.compare_to)
    (out/'analysis.json').write_text(json.dumps(cleaned(result),indent=2,allow_nan=False)+'\n')
    print(json.dumps({'output':str(out),'scenes':len(result['scenes']),'all_raw_equal_icc_srgb':all_identity,'straight_rows':len(straight_rows),'corner_rows':len(corner_rows),'analysis_sha256':sha(out/'analysis.json')}))

if __name__=='__main__':main()
