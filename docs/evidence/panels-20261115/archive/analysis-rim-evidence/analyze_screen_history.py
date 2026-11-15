"""Completed-r2 public history only; all source/depth regressions preserved."""
from pathlib import Path
import hashlib,io,json
import numpy as np
from PIL import Image,ImageCms
O=Path(__file__).resolve().parent;P=O.parent
B=P/'panels-alert-rim-bounded-history-20261115';R=P/'panels-dark-scrim-20261115';C=P/'panels-alert-floor-screen-history-r2-20261115'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def clean(v):
    if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple,np.ndarray)):return [clean(x) for x in v]
    if isinstance(v,np.generic):return clean(v.item())
    if isinstance(v,float) and not np.isfinite(v):return None
    return v
def write(n,v):(O/n).write_text(json.dumps(clean(v),indent=2,allow_nan=False)+'\n')
caps={}
for name,d in [('additive',B),('original',R),('candidate',C)]:caps[name]={(r['background'],r['theme'],r['carrier']):r for r in json.loads((d/'matrix.json').read_text())['captures']}
cache={};dec=[]
def load(p):
    if p in cache:return cache[p]
    im=Image.open(p);a=np.array(im.convert('RGBA'));ic=im.info.get('icc_profile')
    if ic:r=np.asarray(ImageCms.profileToProfile(im.convert('RGB'),ImageCms.ImageCmsProfile(io.BytesIO(ic)),ImageCms.createProfile('sRGB'),outputMode='RGB'));b=np.dstack([r,a[:,:,3]])
    else:assert 'srgb' in im.info;b=a.copy()
    assert np.array_equal(a,b);cache[p]=a;dec.append({'path':str(p),'sha256':sha(p),'raw_icc_rgba_identical':True});return a
def diff(a,b):
    assert a.shape==b.shape and a.size
    d=np.abs(a.astype(float)-b.astype(float));return {'channels':d.size,'changed_channels':int(np.count_nonzero(d)),'max_abs':d.max(),'mean_abs':d.mean()}
def box(a,r,origin):
    x0,y0,x1,y1=r;ox,oy=origin;assert x0>=ox and y0>=oy and x1-ox<=a.shape[1] and y1-oy<=a.shape[0];return a[y0-oy:y1-oy,x0-ox:x1-ox]
old=json.loads((O/'history-rim-bounded/analysis.json').read_text());orig=json.loads((O/'history-reference/analysis.json').read_text());new=json.loads((O/'history-screen-increment/analysis.json').read_text());olds={r['scene']:r for r in old['scenes']};origs={r['scene']:r for r in orig['scenes']};news={r['scene']:r for r in new['scenes']}
body=json.loads((P/'panel-probes-preparation/analysis-plan.json').read_text())['body_rois_pt']['alert']
controls=[];clip=[];cp=[]
def clear(x,y,boxes):
    m=np.ones(np.broadcast_shapes(np.shape(x),np.shape(y)),bool)
    for l,t,r,b in boxes:m&=~((x>=l-2)&(x<r+2)&(y>=t-2)&(y<b+2))
    return m
nativeboxes=[[57.5,279.5,317.5,300],[57.5,307,317.5,345],[43.5,365.5,183.5,413.5],[191.5,365.5,331.5,413.5]]
for key,c in caps['candidate'].items():
    b=caps['additive'][key];r=caps['original'][key];sid,theme,car=key
    assert b['window_geometry']['captured_surface_screen_rect_px']==c['window_geometry']['captured_surface_screen_rect_px']==r['window_geometry']['captured_surface_screen_rect_px'];assert b['actual_alert_layout']==c['actual_alert_layout']==r['actual_alert_layout']
    bw=load(B/b['window_png']);cw=load(C/c['window_png']);rw=load(R/r['window_png']);bs=load(B/b['screen_png']);cs=load(C/c['screen_png']);rs=load(R/r['screen_png']);origin=c['window_geometry']['captured_surface_screen_rect_px'][:2]
    q={'input':sid,'theme':theme,'carrier':car,'expected_unchanged':theme=='dark','comparison_scope':'strict original dark control' if theme=='dark' else ('isolated screen increment versus additive, blur8 constant' if car=='alert' else 'combined radius12to10 response; no same-source strict10 reference'),'window_vs_additive':diff(bw,cw),'window_vs_original':diff(rw,cw),'visible_app_vs_additive':diff(bs[80:1302],cs[80:1302]),'visible_app_vs_original':diff(rs[80:1302],cs[80:1302]),'full_screen_vs_additive':diff(bs,cs)}
    if car=='alert':
        deep=[135,595,615,779];q['deep80_vs_additive']=diff(box(bw,deep,origin),box(cw,deep,origin));q['original_body_rois']={}
        boxes=nativeboxes+news[sid+'-'+theme]['android_foreground_pt']
        for name,roi in body.items():
            rect=[round(v*2) for v in roi];x,y=np.meshgrid((np.arange(rect[0],rect[2])+.5)/2,(np.arange(rect[1],rect[3])+.5)/2);m=clear(x,y,boxes);q['original_body_rois'][name]=diff(box(bw,rect,origin)[m],box(cw,rect,origin)[m])
        if theme=='light':
            top=[280,503,470,539];inter=[280,max(503,origin[1]),470,539]
            q['neutral_top_full_declared_display']=diff(bs[503:539,280:470],cs[503:539,280:470]);q['neutral_top_actual_window_intersection']=diff(box(bw,inter,origin),box(cw,inter,origin));q['neutral_top_window_unavailable_screen_rows']=[503,origin[1]]
    controls.append(q)
    if car!='alert':continue
    nativepath=Path(news[sid+'-'+theme]['files']['native']['path']);ims={'native':load(nativepath)[:,:,:3],'additive':bs[:,:,:3],'candidate':cs[:,:,:3],'original':rs[:,:,:3]}
    def add(meta,xx,yy):
        xx,yy=np.broadcast_arrays(xx,yy);m=clear((xx+.5)/2,(yy+.5)/2,boxes);v={p:a[yy,xx][m].reshape(-1,3) for p,a in ims.items()}
        for p,a in v.items():clip.append({**meta,'platform':p,'clear_pixels':len(a),'channel255':(a==255).sum(0),'channel0':(a==0).sum(0),'RGB255':int(np.all(a==255,1).sum()),'any255':int(np.any(a==255,1).sum())})
        a=v['candidate'];q={**meta,'clear_pixels':len(a)}
        for p in ['additive','original','native']:
            for val in [0,255]:q[f'new{val}_vs_{p}_channels']=((a==val)&(v[p]!=val)).sum(0)
        cp.append(q)
    ed={'left':('x',27.5,1,[[307,338]],24),'right':('x',347.5,-1,[[307,338]],24),'top':('y',257.5,1,[[62,104],[271,313]],20),'bottom':('y',429.5,-1,[[62,104],[271,313]],10)}
    for edge,(ax,bd,sg,ts,last) in ed.items():
        tang=np.concatenate([np.arange(l+.25,r,.5) for l,r in ts]);ti=np.floor(2*tang).astype(int)
        for d in np.arange(-5.75,last,.5):
            ni=int(2*(bd+sg*d));xx,yy=(np.full_like(ti,ni),ti) if ax=='x' else (ti,np.full_like(ti,ni));add({'scene':sid+'-'+theme,'track':'straight','edge':edge,'distance_pt':d},xx,yy)
    for corner in ['TL','TR','BL','BR']:
        left=corner.endswith('L');top=corner.startswith('T')
        for dep in [4.25,8.25,12.25,16.25,20.25,24.25]:
            yy=int(2*((257.5+dep) if top else (429.5-dep)))
            for d in np.arange(-5.75,28,.5):
                xx=int(2*((27.5+d) if left else (347.5-d)));add({'scene':sid+'-'+theme,'track':'corner','corner':corner,'depth_pt':dep,'distance_pt':d},np.array([xx]),np.array([yy]))
write('rim-screen-history-controls.json',{'strict_dark8_actual_and_app_all_zero':all(x['window_vs_additive']['max_abs']==0 and x['window_vs_original']['max_abs']==0 and x['visible_app_vs_additive']['max_abs']==0 and x['visible_app_vs_original']['max_abs']==0 for x in controls if x['expected_unchanged']),'light_sheet_strict_same_source_control_available':False,'rows':controls})
write('rim-screen-history-clipping.json',clip);write('rim-screen-history-clipping-pointwise.json',cp);write('rim-screen-history-decode.json',dec)
changes=[]
for sid,s in news.items():
    for label,bas in [('additive',olds[sid]),('original',origs[sid])]:
        assert bas['files']['native']['sha256']==s['files']['native']['sha256']
        for mode in ['raw','icc_srgb']:
            a=bas['tracks'][mode];b=s['tracks'][mode]
            for name in a['body']:changes.append({'scene':sid,'reference':label,'mode':mode,'region':'body','name':name,'field':'rgb_rmse','baseline':a['body'][name]['rgb_rmse'],'candidate':b['body'][name]['rgb_rmse']})
            for name in a['straight']:
                for field in ['rgb_rmse_inward_0_20','d1_rgb_rmse_inward_0_20','d2_rgb_rmse_inward_0_20']:changes.append({'scene':sid,'reference':label,'mode':mode,'region':'straight','name':name,'field':field,'baseline':a['straight'][name][field],'candidate':b['straight'][name][field]})
            for name in a['corner']:
                for aa,bb in zip(a['corner'][name],b['corner'][name]):
                    assert aa['depth_pt']==bb['depth_pt'] and aa['sample_count']==bb['sample_count']
                    for field in ['rgb_rmse','d1_rgb_rmse','d2_rgb_rmse']:
                        if aa[field] is not None and bb[field] is not None:changes.append({'scene':sid,'reference':label,'mode':mode,'region':'corner','name':name,'depth_pt':aa['depth_pt'],'field':field,'baseline':aa[field],'candidate':bb[field]})
for r in changes:
    r['delta']=r['candidate']-r['baseline'];r['direction']='improved' if r['delta']< -1e-9 else ('regressed' if r['delta']>1e-9 else 'unchanged')
summaries=[]
for sid in news:
    for ref in ['additive','original']:
        rr=[r for r in changes if r['scene']==sid and r['reference']==ref and r['mode']=='raw'];s={'scene':sid,'reference':ref,'scope':'isolated incremental compositing' if ref=='additive' else 'combined blur+rim+compositing vs original factory'}
        for region,field in [('body','rgb_rmse'),('straight','rgb_rmse_inward_0_20'),('corner','rgb_rmse')]:s[region+'_rgb']={d:sum(r['region']==region and r['field']==field and r['direction']==d for r in rr) for d in ['improved','regressed','unchanged']}
        summaries.append(s)
write('rim-screen-history-metric-changes.json',changes);write('rim-screen-history-summary.json',summaries)
print(json.dumps(clean({'strict_dark8_zero':all(q['window_vs_original']['max_abs']==0 and q['visible_app_vs_original']['max_abs']==0 for q in controls if q['expected_unchanged']),'light_alert_deep_body_zero':all(q['deep80_vs_additive']['max_abs']==0 and all(v['max_abs']==0 for v in q['original_body_rois'].values()) for q in controls if q['carrier']=='alert' and q['theme']=='light'),'light_history':[s for s in summaries if s['scene'].endswith('light')],'candidate_added_clipped_channel_samples_vs_additive_inward':sum(sum(x['new255_vs_additive_channels'])+sum(x['new0_vs_additive_channels']) for x in cp if x['distance_pt']>=0)}),indent=2))
