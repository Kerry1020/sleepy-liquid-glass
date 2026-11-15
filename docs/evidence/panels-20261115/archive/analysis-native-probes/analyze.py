#!/usr/bin/env python3
"""Fixed-world, preregistered calibration diagnostics; never register images."""
from pathlib import Path
import csv, hashlib, io, json, re, sys
import numpy as np
from PIL import Image, ImageCms
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

P=Path(__file__).resolve().parent.parent
O=Path(__file__).resolve().parent
if len(sys.argv)>2:
    # Later candidates receive separate outputs; the rejected original analysis
    # remains immutable. Only descendants of this analysis directory are allowed.
    target=(O/sys.argv[2]).resolve();assert target.is_relative_to(O) and target!=O
    O=target;O.mkdir(parents=True,exist_ok=True)
S=P/'panel-probes-preparation'
N=P/'native-panel-feasibility-preparation'
A=P/'panels-nonperiodic-baseline-20261115'
PLAN=json.loads((S/'analysis-plan.json').read_text())
ORACLE=json.loads((S/'oracle.json').read_text())
MATRIX=json.loads((A/'matrix.json').read_text())
ATT=json.loads((N/'attachments/manifest.json').read_text())[0]['attachments']
REQ=json.loads((N/'attachments/8ECDF7CD-A255-42D6-8CE0-F8035FDBF9A8.json').read_text())
SHA=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,obj):
    (O/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
def clean(v):
    if isinstance(v,dict):return {k:clean(t) for k,t in v.items()}
    if isinstance(v,(list,tuple)):return [clean(t) for t in v]
    if isinstance(v,np.ndarray):return clean(v.tolist())
    if isinstance(v,(np.floating,float)):return float(v) if np.isfinite(v) else None
    if isinstance(v,np.integer):return int(v)
    return v
if len(sys.argv)>1 and not (O/'run-input-freeze.json').exists():
    cp=Path(sys.argv[1]).resolve();ff=[cp/'matrix.json',cp/'capture-result.json']+list(cp.glob('*-screen.png'))
    save('run-input-freeze.json',{'status':'before-first-this-candidate-pixel-decode','candidate_directory':str(cp),'files':{str(p):SHA(p) for p in ff if p.exists()},'script_sha256':SHA(Path(__file__)),'fixed_parent_plan_sha256':SHA(S/'analysis-plan.json'),'no_registration_or_source_substitution':True})
def csvwrite(name,rows):
    if not rows:return
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with (O/name).open('w',newline='') as f:
        w=csv.DictWriter(f,keys);w.writeheader();w.writerows(clean(r) for r in rows)
def rectmask(boxes):
    yy,xx=np.mgrid[0:1334,0:750];xx=(xx+.5)/2;yy=(yy+.5)/2
    m=np.zeros((1334,750),bool)
    for b in boxes:
        x0,y0,x1,y1=b;m|=(xx>=x0-2)&(xx<x1+2)&(yy>=y0-2)&(yy<y1+2)
    return m
def crop(a,b):
    x0,y0,x1,y1=[round(v*2) for v in b];return a[y0:y1,x0:x1]
def stats(v):
    v=np.asarray(v,float)
    if not v.size:return {'n':0}
    v=v.reshape(-1,3)
    return clean({'n':len(v),'mean_rgb':v.mean(0),'q05_rgb':np.quantile(v,.05,axis=0),'q95_rgb':np.quantile(v,.95,axis=0),'rms_contrast_rgb':v.std(0),'mean_chroma_rgb_range':np.ptp(v,axis=1).mean()})

decode=[]; images={}; native={}; ax={}
def load(p):
    p=p.resolve()
    if str(p) in images:return images[str(p)]
    im=Image.open(p);raw=np.asarray(im.convert('RGB'));icc=im.info.get('icc_profile')
    if icc:
        profile=ImageCms.ImageCmsProfile(io.BytesIO(icc))
        normalized=np.asarray(ImageCms.profileToProfile(im.convert('RGB'),profile,ImageCms.createProfile('sRGB'),outputMode='RGB'))
        desc=ImageCms.getProfileDescription(profile).strip()
    else:normalized=raw.copy();desc=None
    d=np.abs(raw.astype(float)-normalized.astype(float))
    decode.append({'path':str(p),'sha256':SHA(p),'mode':im.mode,'size':list(im.size),'icc_sha256':hashlib.sha256(icc).hexdigest() if icc else None,'icc_description':desc,'raw_normalized_identical':bool(np.array_equal(raw,normalized)),'max_raw_normalized_channel_delta':float(d.max()),'rgb_sha256':hashlib.sha256(raw.tobytes()).hexdigest()})
    # Both representations are always retained in memory; no duplicate output track when exact.
    images[str(p)]=(raw.astype(float),normalized.astype(float));return images[str(p)]

def attkey(t):
    s=t['suggestedHumanReadableName'];sid=next((i for i in PLAN['selected_ids'] if i+'-light-' in s),None)
    if not sid:return None
    phase=s.split(sid+'-light-',1)[1].split('_0_',1)[0].replace('-accessibility','')
    return sid,phase
for t in ATT:
    k=attkey(t)
    if k and t['exportedFileName'].endswith('.png'):native[k]={'attachment':t,'pixels':load(N/'attachments'/t['exportedFileName'])}
    if k and t['exportedFileName'].endswith('.txt'):ax[k]={'attachment':t,'text':(N/'attachments'/t['exportedFileName']).read_text()}
src={i:load(S/'inputs'/f'{i}.png') for i in PLAN['selected_ids']}
andr={};back={}
for c in MATRIX['captures']:
    carrier='sheet' if c['carrier']=='share_sheet' else c['carrier']
    andr[(c['background'],carrier)]={'capture':c,'pixels':load(A/c['screen_png'])}
for b in MATRIX['baselines']:back[b['background']]=load(A/b['screen_png'])
candidate_dir=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else None
candidate={}
if candidate_dir:
    cm=json.loads((candidate_dir/'matrix.json').read_text());checks=[]
    for c in cm['captures']:
        carrier='sheet' if c['carrier']=='share_sheet' else c['carrier'];k=(c['background'],carrier);bc=andr[k]['capture'];layout=lambda x:{m['tag']:m['actual_screen_rect_px'] for m in x['measurements']};g=c['background_canvas'];pane=c['actual_alert_layout']['pane']['screen_rect_px'] if carrier=='alert' else c['sheet_geometry_comparison']['actual_material_layout']['screen_rect_px'];expected=[55,515,695,859] if carrier=='alert' else [16,635,734,1318]
        ck={'input':k[0],'carrier':carrier,'canvas_exact':g['screen_rect_px']==[0,0,750,1334],'basis_exact':g['local_to_screen_unit_basis_px']==[[0,0],[1,0],[0,1]],'pane_exact':pane==expected,'input_hash_exact':g['native_input_mapping']['input_sha256']==SHA(S/'inputs'/f'{k[0]}.png'),'foreground_layout_equal_to_baseline':layout(c)==layout(bc)};checks.append(ck)
        assert all(v for kk,v in ck.items() if kk not in ['input','carrier']),ck
        candidate[k]=load(candidate_dir/c['screen_png'])
    save('candidate-geometry-gates.json',checks)

sessions={}
for d in (N/'sessions').iterdir():
    meta=json.loads((d/'external-input-metadata.json').read_text());sess=json.loads((d/'session.json').read_text());trace=[json.loads(x) for x in (d/'trace.jsonl').read_text().splitlines()]
    sessions[meta['id']]={'meta':meta,'session':sess,'trace':trace,'dir':d}
receipts=[]
for (sid,phase),v in native.items():
    t=v['attachment']['timestamp'];ctx=sessions[sid];ss=ctx['session'];rel=t-ss['originUnixSeconds'];carrier='alert' if phase.startswith('alert') else 'sheet' if phase.startswith('sheet') else 'none'
    reqphase='rest' if carrier!='none' else phase
    sample=1 if phase.endswith('repeat') else 0
    possible=[r for r in REQ if r.get('inputID')==sid and r.get('phase')==reqphase and r.get('carrier')==carrier and (carrier=='none' or r.get('sampleIndex')==sample) and r['requestedAtUnixSeconds']<=t]
    prior=[x for x in ctx['trace'] if x['event']=='external-presentation-context' and x['t']<=rel]
    r=max(possible,key=lambda r:r['requestedAtUnixSeconds']) if possible else None
    pc=prior[-1] if prior else None
    nextreq=min([rr['requestedAtUnixSeconds'] for rr in REQ if r and rr['requestedAtUnixSeconds']>r['requestedAtUnixSeconds']],default=None)
    receipts.append({'input':sid,'phase':phase,'file':v['attachment']['exportedFileName'],'capture_unix':t,'capture_rel_session_s':rel,'request_matched':r is not None,'capture_after_request_s':t-r['requestedAtUnixSeconds'] if r else None,'capture_before_next_operation_s':nextreq-t if nextreq else None,'request_reference_run':r.get('referenceRunID') if r else None,'session_run':ss['run'],'request_session_uuid_matches':bool(r and r['referenceRunID'].endswith(ss['run'][-36:])),'loader_manifest_matches':bool(r and r['inputManifestSHA256']==SHA(S/'loader-manifest.json')),'ax_attachment':ax[(sid,phase)]['attachment']['exportedFileName'],'ax_after_png_s':ax[(sid,phase)]['attachment']['timestamp']-t,'latest_public_context':pc,'session_traits':{k:ss[k] for k in ['os','screenWidthPt','screenHeightPt','screenScale','interfaceStyle','reduceMotion','reduceTransparency','darkerSystemColors']},'source_original_bytes_equal':SHA(ctx['dir']/'background-input.png')==SHA(S/'inputs'/f'{sid}.png')})
save('capture-receipts.json',clean(receipts))

# Parse actual native AX, excluding giant virtual scrollbars and backing content.
pattern=re.compile(r'\{\{([-\d.]+), ([-\d.]+)\}, \{([-\d.]+), ([-\d.]+)\}\}')
def linebox(line):
    a=list(map(float,pattern.search(line).groups()));return [a[0],a[1],a[0]+a[2],a[1]+a[3]]
fg={};geoms=[]
for k,v in ax.items():
    sid,phase=k;carrier='alert' if phase.startswith('alert') else 'sheet' if phase.startswith('sheet') else 'none';lines=v['text'].splitlines();boxes=[]
    if carrier=='alert':
        relevant=False
        for l in lines:
            if 'Alert,' in l and "label: 'Native Alert'" in l:relevant=True;geoms.append({'input':sid,'phase':phase,'kind':'Alert AX pane','ltrb_pt':linebox(l)})
            if relevant and any(s in l for s in ["label: 'Native Alert'","label: 'System-provided alert", "label: 'Cancel'","label: 'Confirm'"]) and any(s in l for s in ['StaticText,','Button,']):boxes.append(linebox(l))
    elif carrier=='sheet':
        relevant=False
        for li,l in enumerate(lines):
            if "label: 'Sheet Grabber'" in l:
                relevant=True;boxes.append(linebox(l))
                geoms.append({'input':sid,'phase':phase,'kind':'Sheet actual AX parent immediately above grabber','ltrb_pt':linebox(lines[li-1]),'material_raster_ltrb_pt':[8,317.5,367,659]})
            elif relevant and any(s in l for s in ['StaticText,','Switch,','Slider,','Button,']):
                if pattern.search(l):boxes.append(linebox(l))
    fg[k]=boxes
native_masks={k:rectmask(v) for k,v in fg.items()}
union_masks={};union_boxes={}
for k,a in andr.items():
    sid,carrier=k;nb=fg[(sid,carrier+'-rest')];ab=[]
    for m in a['capture']['measurements']:
        tag=m['tag']
        # Whole Sheet content is a deliberately conservative actual layout box: it retains
        # primary top/side regions but excludes middle diagnostics rather than inventing slots.
        if carrier=='alert' and tag in ['static-alert-title','static-alert-body','static-alert-confirm','static-alert-cancel'] or carrier=='sheet' and tag=='static-sheet-content':
            ab.append([z/2 for z in m['actual_screen_rect_px']])
    if carrier=='sheet':
        # Native AX grabber is in nb. Android separate grabber layout not exported; conservatively
        # exclude the complete central strip top317.5..353.5 (see explicit limitation).
        ab.append([140,317.5,235,353.5])
    union_boxes[k]={'native_ax':nb,'android_actual_layout':ab,'padding_pt':2,'android_sheet_grabber_limitation':'No separate grabber layout export; central top strip conservative exclusion' if carrier=='sheet' else None}
    union_masks[k]=rectmask(nb+ab)
save('geometry-and-mask.json',clean({'native_ax':geoms,'native_foreground_boxes':[{ 'input':k[0],'phase':k[1],'boxes':v} for k,v in fg.items()],'union_foreground_boxes':[{ 'input':k[0],'carrier':k[1],**v} for k,v in union_boxes.items()]}))

def delta(a,b,m=None):
    d=np.abs(a-b);q=d[m] if m is not None else d.reshape(-1,3)
    return clean({'samples':len(q),'max_rgb':q.max(0),'mean_rgb':q.mean(0),'rms_rgb':np.sqrt((q*q).mean(0)),'changed_pixel_count':int(np.any(q!=0,axis=1).sum())})
repeats=[];contexts=[]
for sid in PLAN['selected_ids']:
    for carrier,b in [('alert',[27.5,257.5,347.5,429.5]),('sheet',[8,317.5,367,659])]:
        first=native[(sid,carrier+'-rest')]['pixels'];second=native[(sid,carrier+'-rest-repeat')]['pixels'];mask=union_masks[(sid,carrier)];inside=np.zeros(mask.shape,bool);x0,y0,x1,y1=[round(z*2) for z in b];inside[y0:y1,x0:x1]=True;inside&=~mask
        repeats.append({'input':sid,'carrier':carrier,'full_display_raw':delta(first[0],second[0]),'clear_pane_raw':delta(first[0],second[0],inside),'full_display_normalized':delta(first[1],second[1]),'clear_pane_normalized':delta(first[1],second[1],inside),'ax_fg_boxes_equal':fg[(sid,carrier+'-rest')]==fg[(sid,carrier+'-rest-repeat')]})
    for ph in ['after-alert-before-sheet-context','after-sheet-context']:
        contexts.append({'input':sid,'phase':ph,'full_display_raw':delta(native[(sid,'before-alert-context')]['pixels'][0],native[(sid,ph)]['pixels'][0]),'fixed_exterior_raw':delta(crop(native[(sid,'before-alert-context')]['pixels'][0],[32,176,343,220]),crop(native[(sid,ph)]['pixels'][0],[32,176,343,220]))})
save('repeat-stability.json',repeats);save('context-stability.json',contexts);save('decode-provenance.json',decode)

def smooth(v):
    v=np.asarray(v,float);o=np.full(v.shape,np.nan);good=np.all(np.isfinite(v),axis=1) if v.ndim==2 else np.isfinite(v);ix=np.flatnonzero(np.diff(np.r_[False,good,False]));kernel=np.exp(-np.arange(-3,4)**2/(2*1.5**2));kernel/=kernel.sum()
    for st,en in ix.reshape(-1,2):
        if en-st<2:continue
        vv=v[st:en];pad=np.pad(vv,((3,3),(0,0)) if v.ndim==2 else (3,3),mode='reflect')
        o[st:en]=np.stack([np.convolve(pad[:,j],kernel,'valid') for j in range(v.shape[1])],axis=1) if v.ndim==2 else np.convolve(pad,kernel,'valid')
    return o
def derivatives(v):
    d=np.full(v.shape,np.nan);dd=d.copy();good=np.all(np.isfinite(v),axis=1);ix=np.flatnonzero(np.diff(np.r_[False,good,False]))
    for st,en in ix.reshape(-1,2):
        if en-st>=3:d[st:en]=np.gradient(v[st:en],.5,axis=0);dd[st:en]=np.gradient(d[st:en],.5,axis=0)
    return d,dd
tracks=[];summaries=[];corner_rows=[];exclusions=[]
bins=[(-6,0),(0,2),(2,4),(4,12),(12,20),(20,24)]
def extract_track(arr,mask,seg):
    d=np.arange(-5.75,seg['last_inward_pt_exclusive'],.5);t=np.arange(seg['tangent_half_open_pt'][0]+.25,seg['tangent_half_open_pt'][1],.5)
    # Pixel-center coordinates are observed and never interpolated.
    ns=seg['boundary_pt']+seg['inward_sign']*d;ni=np.floor(ns*2).astype(int);ti=np.floor(t*2).astype(int)
    if seg['axis']=='x':v=arr[ti[:,None],ni[None,:]];m=mask[ti[:,None],ni[None,:]]
    else:v=arr[ni[None,:],ti[:,None]];m=mask[ni[None,:],ti[:,None]]
    count=(~m).sum(0);raw=np.full((len(d),3),np.nan)
    for i in range(len(d)):
        if count[i]:raw[i]=v[:,i][~m[:,i]].mean(0)
    sm=smooth(raw);d1,d2=derivatives(sm);return d,t,v,m,count,raw,sm,d1,d2
for sid in PLAN['selected_ids']:
    for carrier in ['alert','sheet']:
        mask=union_masks[(sid,carrier)];sets={'source':src[sid],'native':native[(sid,carrier+'-rest')]['pixels'],'android':andr[(sid,carrier)]['pixels']}
        if candidate:sets['rim_blur']=candidate[(sid,carrier)]
        reps=['raw'] if all(np.array_equal(v[0],v[1]) for v in sets.values()) else ['raw','icc_srgb']
        for ri,rep in enumerate(reps):
            for seg in [s for s in PLAN['straight'] if s['carrier']==carrier]:
                for plat,arrs in sets.items():
                    d,t,v,m,count,raw,sm,d1,d2=extract_track(arrs[ri],mask,seg)
                    if plat=='native' and ri==0:
                        exclusions.append({'input':sid,'carrier':carrier,'segment':seg['segment'],'tangent_samples':len(t),'normal_samples':len(d),'excluded_pixels':int(m.sum()),'exclusion_runs_by_normal':[[float(di),int(co)] for di,co in zip(d,len(t)-count) if co]})
                    for i,di in enumerate(d):
                        r={'input':sid,'carrier':carrier,'segment':seg['segment'],'context':seg['status'],'representation':rep,'platform':plat,'distance_pt':di,'clear_original_pixels':count[i]}
                        for lab,vv in [('raw',raw),('smooth',sm),('d1',d1),('d2',d2)]:
                            for j,ch in enumerate('rgb'):r[f'{lab}_{ch}']=vv[i,j]
                        tracks.append(r)
                    for lo,hi in bins:
                        ix=(d>=lo)&(d<hi)
                        if ix.any():summaries.append({'input':sid,'carrier':carrier,'segment':seg['segment'],'context':seg['status'],'representation':rep,'platform':plat,'bin_pt':f'[{lo},{hi})',**stats(v[:,ix][~m[:,ix]])})
                # Render no resized/recentered screenshots: fixed original-coordinate curves only.
                if rep=='raw':
                    fig,axs=plt.subplots(3,1,figsize=(7,6.2),sharex=True)
                    for plat,arrs in sets.items():
                        d,t,v,m,count,raw,sm,d1,d2=extract_track(arrs[0],mask,seg);lum=sm@np.array([.2126,.7152,.0722]);axs[0].plot(d,lum,label=plat);axs[1].plot(d,np.ptp(sm,axis=1),label=plat);axs[2].plot(d,np.linalg.norm(d1,axis=1),label=plat)
                    for axx in axs:axx.axvline(0,color='k',lw=.5);axx.grid(alpha=.2)
                    axs[0].set_ylabel('encoded luma');axs[1].set_ylabel('RGB range');axs[2].set_ylabel('|RGB D1| / pt');axs[2].set_xlabel('signed inward distance (pt)');axs[0].legend();fig.suptitle(f'{sid}: {carrier} {seg["segment"]}');fig.tight_layout();fig.savefig(O/f'track-{sid}-{carrier}-{seg["segment"]}.png',dpi=100);plt.close(fig)
        # Frozen horizontal corner raster slices; native shape not replaced by Android contour.
        for top,depths,last in [(True,[4.25,8.25,12.25,16.25,20.25,24.25]+([28.25,32.25] if carrier=='sheet' else []),40 if carrier=='sheet' else 28),(False,[4.25,8.25,12.25,16.25]+([20.25,24.25] if carrier=='alert' else []),24 if carrier=='sheet' else 28)]:
            for left in [True,False]:
                bx=(27.5 if left else 347.5) if carrier=='alert' else (8 if left else 367);by=(257.5 if top else 429.5) if carrier=='alert' else (317.5 if top else 659)
                for dep in depths:
                    ds=np.arange(-5.75,last,.5);xx=np.floor(2*(bx+(1 if left else -1)*ds)).astype(int);yy=int(2*(by+(1 if top else -1)*dep));mm=mask[yy,xx];ranges=np.flatnonzero(np.diff(np.r_[False,~mm,False])).reshape(-1,2);longest=max((e-s for s,e in ranges),default=0)
                    for plat,arrs in sets.items():
                        vals=arrs[0][yy,xx].copy();vals[mm]=np.nan;sm=smooth(vals);d1,d2=derivatives(sm)
                        if longest<16:d1[:]=np.nan;d2[:]=np.nan
                        for i,di in enumerate(ds):corner_rows.append({'input':sid,'carrier':carrier,'corner':('top' if top else 'bottom')+'_'+('left' if left else 'right'),'depth_pt':dep,'platform':plat,'distance_pt':di,'masked':bool(mm[i]),'longest_clear_run_px':longest,'derivative_eligible':longest>=16,**{f'{lab}_{c}':vv[i,j] for lab,vv in [('raw',vals),('smooth',sm),('d1',d1),('d2',d2)] for j,c in enumerate('rgb')}})
csvwrite('straight-tracks.csv',tracks);save('straight-bin-stats.json',summaries);save('exclusions.json',exclusions);csvwrite('corner-raster-tracks.csv',corner_rows)

# Exterior/body diagnostics, fixed regions. Gains remain encoded color and are never removed.
body={'alert':{'left':[49.5,307,54.5,338],'right':[320.5,307,325.5,338],'gap_left':[60,350,110,359],'gap_right':[265,350,315,359]},'sheet':{'upper_left_primary':[48,348,110,365],'middle_left_diagnostic':[48,430,110,442],'lower_right_diagnostic':[265,610,327,625]}}
metrics=[]
for sid in PLAN['selected_ids']:
    for carrier in ['alert','sheet']:
        mask=union_masks[(sid,carrier)];before=native[(sid,'before-alert-context' if carrier=='alert' else 'after-alert-before-sheet-context')]['pixels'][0];ext=[32,176,343,220] if carrier=='alert' else [24,170,351,272]
        metricsets=[('source',src[sid][0]),('native_before',before),('android_background',back[sid][0]),('native',native[(sid,carrier+'-rest')]['pixels'][0]),('android',andr[(sid,carrier)]['pixels'][0])]
        if candidate:metricsets.append(('rim_blur',candidate[(sid,carrier)][0]))
        for plat,arr in metricsets:
            for name,b in [('exterior',ext)]+list(body[carrier].items()):
                v=crop(arr,b);mm=crop(mask,b);vv=v[~mm];r={'input':sid,'carrier':carrier,'platform':plat,'region':name,'bbox_pt':b,'masked_pixels':int(mm.sum()),**stats(vv)}
                if name=='exterior':
                    target=crop(src[sid][0],b)[~mm];gain=np.sum(vv*target,axis=0)/np.sum(target*target,axis=0);r['encoded_through_origin_gain_rgb']=gain;r['gain_residual_rms_rgb']=np.sqrt(np.mean((vv-target*gain)**2,axis=0))
                if len(vv):
                    gx=np.diff(v,axis=1);gy=np.diff(v,axis=0);mx=~(mm[:,1:]|mm[:,:-1]);my=~(mm[1:]|mm[:-1]);r['gradient_rms_rgb_per_pt_x']=np.sqrt(np.mean(gx[mx]**2,axis=0))*2 if mx.any() else None;r['gradient_rms_rgb_per_pt_y']=np.sqrt(np.mean(gy[my]**2,axis=0))*2 if my.any() else None
                metrics.append(clean(r))
save('body-exterior.json',metrics)

if candidate:
    changes=[]
    for sid in PLAN['selected_ids']:
        for carrier in ['alert','sheet']:
            mask=union_masks[(sid,carrier)];ref=native[(sid,carrier+'-rest')]['pixels'][0];base=andr[(sid,carrier)]['pixels'][0];cand=candidate[(sid,carrier)][0]
            for seg in [s for s in PLAN['straight'] if s['carrier']==carrier]:
                r=extract_track(ref,mask,seg);b=extract_track(base,mask,seg);c=extract_track(cand,mask,seg);dist=r[0];m=r[3]
                for lo,hi in bins:
                    ix=(dist>=lo)&(dist<hi)
                    if not ix.any():continue
                    valid=~m[:,ix];rv=r[2][:,ix][valid];bv=b[2][:,ix][valid];cv=c[2][:,ix][valid]
                    if not len(rv):continue
                    be=np.abs(bv-rv).mean(0);ce=np.abs(cv-rv).mean(0)
                    changes.append({'input':sid,'carrier':carrier,'segment':seg['segment'],'context':seg['status'],'bin_pt':[lo,hi],'clear_original_pixels':len(rv),'baseline_native_mae_rgb':be.tolist(),'candidate_native_mae_rgb':ce.tolist(),'candidate_minus_baseline_mae_rgb':(ce-be).tolist(),'candidate_minus_baseline_mean_rgb':(cv-bv).mean(0).tolist(),'baseline_mean_rgb':bv.mean(0).tolist(),'candidate_mean_rgb':cv.mean(0).tolist(),'native_mean_rgb':rv.mean(0).tolist()})
    save('candidate-fixed-roi-delta.json',changes)

# Geometry/source-excitation audit of every shape. A full-material centroid is
# not manufactured by retaining the unrefracted part outside a pane or by
# closing foreground gaps.
audit=[];shapes=ORACLE['probes'][1]['shapes'];shape_source=src['panel_probe_shapes'][0]
for sh in shapes:
    ident=np.all(shape_source==np.array(sh['color_rgb']),axis=2);b=next(b['fixed_support_ltrb_px'] for b in PLAN['shape_supports'] if b['id']==sh['id']) if 'shape_supports' in PLAN else None
    if b is None:
        bb=sh['design_bbox_ltrb_px'];b=[max(0,bb[0]-64),max(0,bb[1]-64),min(750,bb[2]+64),min(1334,bb[3]+64)]
    x0,y0,x1,y1=map(int,b);region=shape_source[y0:y1,x0:x1];gx=np.diff(region,axis=1)[:-1];gy=np.diff(region,axis=0)[:,:-1];tensor=np.array([[np.sum(gx*gx),np.sum(gx*gy)],[np.sum(gx*gy),np.sum(gy*gy)]]);ev=np.linalg.eigvalsh(tensor);ratio=float(ev[0]/ev[1]) if ev[1] else 0
    for carrier,bb in [('alert',[55,515,695,859]),('sheet',[16,635,734,1318])]:
        pane=np.zeros(ident.shape,bool);pane[bb[1]:bb[3],bb[0]:bb[2]]=True;mask=union_masks[('panel_probe_shapes',carrier)];within=int((ident&pane).sum());clear=int((ident&pane&~mask).sum());total=int(ident.sum());reasons=[]
        if within<total:reasons.append('source_shape_intrinsically_pane_clipped_or_outside')
        if clear<within:reasons.append('source_shape_overlaps_direct_foreground_union')
        if clear<64:reasons.append('fewer_than64_clear_source_feature_pixels')
        if ratio<.05:reasons.append('source_2D_tensor_ratio<0.05')
        audit.append({'id':sh['id'],'shape':sh['shape'],'carrier':carrier,'source_bbox_px':sh['visible_raster_bbox_ltrb_px_half_open'],'fixed_support_px':b,'source_color_rgb':sh['color_rgb'],'source_feature_pixels':total,'source_feature_inside_pane_pixels':within,'source_feature_clear_in_pane_pixels':clear,'source_structure_tensor_eigenvalues':ev.tolist(),'source_structure_tensor_ratio':ratio,'complete_material_centroid_geometry_possible':not reasons,'complete_centroid_not_attempted_reasons':reasons+['observed_full_connected_support95percent_mass_and_ID_separation_not_established'],'local_contour_scope':'S02 right local transects separately measured' if sh['id']=='S02' and carrier=='alert' else 'not measured as a unique local contour in this pass; geometry audit does not assert invisibility'})
save('all-shape-geometry-audit.json',audit)

# Candidate-neutral rim profiles remain separate from color-edge and contour
# diagnostics. Fixed body reference is descriptive; it is never subtracted
# from screenshots or used as a recovered physical thickness.
highlights=[];highlightrows=[]
segs=[('alert','top',257.5,1,'y',[140,235]),('alert','bottom',429.5,-1,'y',[140,235]),('alert','left',27.5,1,'x',[353,359]),('alert','right',347.5,-1,'x',[353,359]),('sheet','top_left_center',317.5,1,'y',[140,160]),('sheet','top_right_center',317.5,1,'y',[215,235]),('sheet','bottom',659,-1,'y',[140,235])]
for carrier,name,bound,sgn,axis,tan in segs:
    sid='panel_probe_shapes';seg={'boundary_pt':bound,'inward_sign':sgn,'axis':axis,'tangent_half_open_pt':tan,'last_inward_pt_exclusive':12};mask=union_masks[(sid,carrier)];before=native[(sid,'before-alert-context' if carrier=='alert' else 'after-alert-before-sheet-context')]['pixels'][0]
    sets={'source':src[sid][0],'native_before':before,'native':native[(sid,carrier+'-rest')]['pixels'][0],'android':andr[(sid,carrier)]['pixels'][0]};neutral={}
    for plat in ['source','native_before']:
        d,t,v,m,count,raw,sm,d1,d2=extract_track(sets[plat],mask,seg);ix=(d>=-2)&(d<12);vals=v[:,ix][~m[:,ix]];neutral[plat]={'range_rgb':np.ptp(vals,axis=0).tolist() if len(vals) else None,'eligible_same_coordinate_neutral':bool(len(vals) and np.all(np.ptp(vals,axis=0)<=2))}
    if candidate:sets['rim_blur']=candidate[(sid,carrier)][0]
    for plat in ['native','android']+(['rim_blur'] if candidate else []):
        d,t,v,m,count,raw,sm,d1,d2=extract_track(sets[plat],mask,seg);sel=(d>=-2)&(d<12);lum=raw@np.array([.2126,.7152,.0722]);shoulder=(d>=4)&(d<12)&np.isfinite(lum);ref=float(np.mean(lum[shoulder])) if shoulder.any() else None;rim=(d>=-2)&(d<4)&np.isfinite(lum);peak_i=np.flatnonzero(rim)[np.argmax(lum[rim])] if rim.any() else None
        rec={'carrier':carrier,'segment':name,'platform':plat,'same_coordinate_neutrality':neutral,'direct_foreground_excluded_pixels':int(m[:,sel].sum()),'nearby_backdrop_context':'Alert top broad inward footprint may include System sheet; Alert bottom/Sheet body include system controls/Dock with different platform appearances. Same-coordinate neutrality does not remove these broad-footprint confounds.','interpretation':'mixed highlight/backdrop response; not physical thickness','shoulder_luma_reference_4_12':ref,'peak_distance_pt':float(d[peak_i]) if peak_i is not None else None,'peak_excess_luma':float(lum[peak_i]-ref) if peak_i is not None and ref is not None else None,'FWHM_pt':None,'FWHM_status':'unresolved'}
        if peak_i is not None and ref is not None and lum[peak_i]>ref:
            half=ref+(lum[peak_i]-ref)/2;above=(lum>=half)&rim;starts=np.flatnonzero(np.diff(np.r_[False,above,False])).reshape(-1,2);run=next((r for r in starts if r[0]<=peak_i<r[1]),None)
            if run is not None:
                st,en=run;rec['above_half_peak_original_pixels']=int(en-st)
                if en-st>=3 and st>0 and en<len(d) and np.isfinite(lum[st-1]) and np.isfinite(lum[en]):
                    l=d[st-1]+(half-lum[st-1])/(lum[st]-lum[st-1])*.5;r=d[en-1]+(half-lum[en-1])/(lum[en]-lum[en-1])*.5;rec['FWHM_pt']=float(r-l);rec['FWHM_status']='descriptive_halfheight_width; mixed_context'
                else:rec['FWHM_status']='insufficient3pixel_peak_coverage_or_missing_crossing'
        highlights.append(rec)
        for i,di in enumerate(d):
            if -2<=di<12:highlightrows.append({'carrier':carrier,'segment':name,'platform':plat,'distance_pt':di,'clear_tangent_pixels':count[i],'raw_luma':lum[i],**{f'{lab}_{c}':vv[i,j] for lab,vv in [('raw',raw),('smooth',sm),('d1',d1),('d2',d2)] for j,c in enumerate('rgb')}})
save('narrow-rim-diagnostics.json',clean(highlights));csvwrite('narrow-rim-tracks.csv',highlightrows)
save('decode-provenance.json',decode)

print(json.dumps({'decoded':len(decode),'raw_icc_different':[x['path'] for x in decode if not x['raw_normalized_identical']],'repeat_summary':repeats,'unmatched_receipts':[(r['input'],r['phase']) for r in receipts if not r['request_matched']],'straight_csv_rows':len(tracks),'corner_csv_rows':len(corner_rows)},indent=2))
