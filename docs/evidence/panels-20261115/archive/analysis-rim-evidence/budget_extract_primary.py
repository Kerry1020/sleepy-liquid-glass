"""Frozen screen-increment primary pixels and delta-zero Window controls."""
from pathlib import Path
import csv,hashlib,io,json
import numpy as np
from PIL import Image,ImageCms
O=Path(__file__).resolve().parent;P=O.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def clean(v):
    if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple,np.ndarray)):return [clean(x) for x in v]
    if isinstance(v,np.generic):return clean(v.item())
    if isinstance(v,float) and not np.isfinite(v):return None
    return v
def write(n,v):(O/n).write_text(json.dumps(clean(v),indent=2,allow_nan=False)+'\n')
def diff(a,b):
    assert a.shape==b.shape and a.size
    d=np.abs(a.astype(float)-b.astype(float))
    return {'channels':d.size,'changed_channels':int(np.count_nonzero(d)),'max_abs':d.max(),'mean_abs':d.mean()}
dirs={'body8':P/'panels-alert-body8-20261115','additive':P/'panels-alert-rim-bounded-20261115','candidate':P/'panels-alert-floor-budget-20261115','screen':P/'panels-alert-floor-screen-20261115','radius10':P/'panels-sheet-radius10-20261115'}
caps={k:{(c['background'],'sheet' if c['carrier']=='share_sheet' else c['carrier']):c for c in json.loads((d/'matrix.json').read_text())['captures']} for k,d in dirs.items()}
dec=[];cache={}
def load(p):
    if p in cache:return cache[p]
    im=Image.open(p);a=np.asarray(im.convert('RGBA'));ic=im.info.get('icc_profile')
    if ic:
        r=np.asarray(ImageCms.profileToProfile(im.convert('RGB'),ImageCms.ImageCmsProfile(io.BytesIO(ic)),ImageCms.createProfile('sRGB'),outputMode='RGB'));b=np.dstack([r,a[:,:,3]])
    else:assert 'srgb' in im.info;b=a.copy()
    assert np.array_equal(a,b);dec.append({'path':str(p),'sha256':sha(p),'raw_icc_rgba_identical':True});cache[p]=a;return a
N=P/'native-panel-feasibility-preparation';att=json.loads((N/'attachments/manifest.json').read_text())[0]['attachments'];native={}
for a in att:
    for sid in ['panel_probe_coordinate','panel_probe_shapes']:
        if sid+'-light-alert-rest_0_' in a['suggestedHumanReadableName'] and a['exportedFileName'].endswith('.png'):native[sid]=N/'attachments'/a['exportedFileName']
controls=[]
for sid in ['panel_probe_coordinate','panel_probe_shapes']:
    bc=caps['additive'][(sid,'alert')];cc=caps['candidate'][(sid,'alert')];rb=caps['radius10'][(sid,'alert')]
    assert bc['window_geometry']['captured_surface_screen_rect_px']==cc['window_geometry']['captured_surface_screen_rect_px']==rb['window_geometry']['captured_surface_screen_rect_px']
    assert bc['actual_alert_layout']==cc['actual_alert_layout']==rb['actual_alert_layout']
    b=load(dirs['additive']/bc['window_png']);c=load(dirs['candidate']/cc['window_png']);r=load(dirs['radius10']/rb['window_png']);sc=caps['screen'][(sid,'alert')];sw=load(dirs['screen']/sc['window_png']);org=cc['window_geometry']['captured_surface_screen_rect_px'][:2]
    assert sc['window_geometry']['captured_surface_screen_rect_px']==cc['window_geometry']['captured_surface_screen_rect_px']
    def box(a,rect):
        x0,y0,x1,y1=rect;x0-=org[0];x1-=org[0];y0-=org[1];y1-=org[1];assert x0>=0 and y0>=0 and x1<=a.shape[1] and y1<=a.shape[0]
        return a[y0:y1,x0:x1]
    # Existing neutral-top original pixels: signed -5.75..<12pt,
    # all190 tangent columns. Original row centers, no fitted alignment.
    top=[280,503,470,539];row4=[280,515,470,519]
    intersection=[top[0],max(top[1],org[1]),top[2],top[3]]
    bs=load(dirs['additive']/bc['screen_png']);cs=load(dirs['candidate']/cc['screen_png']);ss=load(dirs['screen']/sc['screen_png'])
    controls.append({'input':sid,'neutral_top_rect_screen_px':top,'neutral_top_full_declared_display_rgba':diff(bs[top[1]:top[3],top[0]:top[2]],cs[top[1]:top[3],top[0]:top[2]]),'neutral_top_display_vs_screen_rgba':diff(ss[top[1]:top[3],top[0]:top[2]],cs[top[1]:top[3],top[0]:top[2]]),'neutral_top_window_vs_screen_rgba':diff(box(sw,intersection),box(c,intersection)),'neutral_top_window_intersection_rect_screen_px':intersection,'neutral_top_window_intersection_rgba':diff(box(b,intersection),box(c,intersection)),'unavailable_window_rows_screen_px_half_open':[top[1],org[1]],'window_coverage_limit':'Prescribed6 exterior rows503..<509 fall outside actual Window; original coordinates retained and full segment separately checked in display, no synthetic Window padding.','first4_top_rows_window_rgba':diff(box(b,row4),box(c,row4)),'radius10_alert_vs_additive_window_rgba':diff(b,r)})
sid='panel_probe_shapes';ims={k:load(dirs[k]/caps[k][(sid,'alert')]['screen_png'])[:,:,:3].astype(float) for k in ['body8','additive','screen','candidate']};ims['native']=load(native[sid])[:,:,:3].astype(float)
rows=[];flat=[];ys=np.arange(614,676);sd=np.arange(8.25,12,.5);sx=np.floor(2*(27.5+sd)).astype(int)
for d in [.25,.75]:
    x=int(2*(27.5+d))
    for y in ys:
        q={'inset_pt':d,'x_px':x,'y_px':int(y),'y_pt':(y+.5)/2,'platforms':{}};f={k:v for k,v in q.items() if k!='platforms'}
        for k,a in ims.items():
            edge=a[y,x];ss=a[y,sx];shoulder=ss.mean(0);q['platforms'][k]={'edge_rgb':edge,'shoulder_rgb':shoulder,'shoulder_original_samples_rgb':ss,'response_rgb':edge-shoulder}
            for j,ch in enumerate('rgb'):f[k+'_edge_'+ch]=edge[j];f[k+'_shoulder_'+ch]=shoulder[j];f[k+'_response_'+ch]=edge[j]-shoulder[j]
        rows.append(q);flat.append(f)
summary=[]
for d in [.25,.75]:
    rr=[r for r in rows if r['inset_pt']==d];q={'inset_pt':d,'pixels':len(rr),'platforms':{}}
    for k in ims:
        a=np.array([r['platforms'][k]['edge_rgb'] for r in rr]);s=np.array([r['platforms'][k]['shoulder_rgb'] for r in rr]);v=a-s
        q['platforms'][k]={'mean_edge_rgb':a.mean(0),'min_edge_rgb':a.min(0),'max_edge_rgb':a.max(0),'mean_shoulder_rgb':s.mean(0),'mean_response_rgb':v.mean(0),'channel255':(a==255).sum(0),'channel0':(a==0).sum(0)}
    q['candidate_vs_additive_shoulder_max_abs']=max(np.abs(r['platforms']['candidate']['shoulder_original_samples_rgb']-r['platforms']['additive']['shoulder_original_samples_rgb']).max() for r in rr)
    q['candidate_vs_screen_shoulder_max_abs']=max(np.abs(r['platforms']['candidate']['shoulder_original_samples_rgb']-r['platforms']['screen']['shoulder_original_samples_rgb']).max() for r in rr)
    summary.append(q)
write('budget-124-pixels.json',{'policy':'fixed original62+62 pixels and same-tangent8..<12pt shoulder; no fit/translation','rows':rows})
with (O/'budget-124-pixels.csv').open('w',newline='') as f:w=csv.DictWriter(f,list(flat[0]));w.writeheader();w.writerows(flat)
write('budget-primary-controls.json',controls);write('budget-124-summary.json',summary);write('budget-primary-decode.json',dec)
print(json.dumps(clean({'controls':controls,'pixels':summary}),indent=2))
