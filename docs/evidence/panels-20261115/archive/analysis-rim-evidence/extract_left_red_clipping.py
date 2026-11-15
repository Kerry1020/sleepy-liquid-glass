"""Fixed 62+62 pixel extraction; shoulder subtraction and additive diagnostics only."""
from pathlib import Path
import csv, hashlib, io, json
import numpy as np
from PIL import Image,ImageCms
O=Path(__file__).resolve().parent;P=O.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def clean(v):
    if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
    if isinstance(v,(list,tuple,np.ndarray)):return [clean(x) for x in v]
    if isinstance(v,np.generic):return clean(v.item())
    return v
def write(n,v):(O/n).write_text(json.dumps(clean(v),indent=2,allow_nan=False)+'\n')
sid='panel_probe_shapes';B=P/'panels-alert-body8-20261115';C=P/'panels-alert-rim-bounded-20261115'
paths={}
for key,d in [('body8',B),('candidate',C)]:
    c=next(x for x in json.loads((d/'matrix.json').read_text())['captures'] if x['background']==sid and x['carrier']=='alert')
    paths[key]=d/c['screen_png']
N=P/'native-panel-feasibility-preparation'
paths['native']=N/'attachments'/next(a['exportedFileName'] for a in json.loads((N/'attachments/manifest.json').read_text())[0]['attachments'] if sid+'-light-alert-rest_0_' in a['suggestedHumanReadableName'] and a['exportedFileName'].endswith('.png'))
ims={};meta={}
for k,p in paths.items():
    im=Image.open(p);a=np.asarray(im.convert('RGB'));ic=im.info.get('icc_profile')
    if ic:b=np.asarray(ImageCms.profileToProfile(im.convert('RGB'),ImageCms.ImageCmsProfile(io.BytesIO(ic)),ImageCms.createProfile('sRGB'),outputMode='RGB'))
    else:assert 'srgb' in im.info;b=a.copy()
    assert np.array_equal(a,b);ims[k]=a.astype(float);meta[k]={'path':str(p),'sha256':sha(p),'raw_icc_identical':True}
ys=np.arange(614,676);ds=[.25,.75];shoulder_ds=np.arange(8.25,12,.5);shoulder_xs=np.floor(2*(27.5+shoulder_ds)).astype(int)
rows=[];wide=[]
for d in ds:
    x=int(2*(27.5+d))
    for y in ys:
        record={'inset_pt':d,'x_px':x,'y_px':int(y),'x_pt':(x+.5)/2,'y_pt':(y+.5)/2,'platforms':{}}
        wr={k:record[k] for k in record if k!='platforms'}
        for k,a in ims.items():
            edge=a[y,x];ss=a[y,shoulder_xs];shoulder=ss.mean(0);response=edge-shoulder
            record['platforms'][k]={'edge_rgb':edge,'shoulder_8_12_rgb':shoulder,'edge_minus_shoulder_rgb':response,'shoulder_original_samples_rgb':ss}
            for j,ch in enumerate('rgb'):
                wr[k+'_edge_'+ch]=edge[j];wr[k+'_shoulder_'+ch]=shoulder[j];wr[k+'_response_'+ch]=response[j]
        delta=record['platforms']['candidate']['edge_rgb']-record['platforms']['body8']['edge_rgb']
        shoulder_delta=record['platforms']['candidate']['shoulder_8_12_rgb']-record['platforms']['body8']['shoulder_8_12_rgb']
        # Algebraic observation, not fitted material: equal additive RGB is
        # visible in the two unsaturated channels. Red excess cannot be recovered
        # from its saturated output. This value only tests clip consistency.
        gb=float(delta[1:].mean());rawred=float(record['platforms']['body8']['edge_rgb'][0]+gb)
        record.update({'candidate_minus_body8_edge_rgb':delta,'candidate_minus_body8_shoulder_rgb':shoulder_delta,'unsaturated_GB_mean_increment_counts':gb,'unsaturated_GB_increment_disagreement_counts':abs(float(delta[1]-delta[2])),'red_unclamped_from_measured_GB_increment_diagnostic':rawred,'red_observed_clipped':bool(record['platforms']['candidate']['edge_rgb'][0]==255)})
        for j,ch in enumerate('rgb'):wr['candidate_minus_body8_edge_'+ch]=delta[j];wr['candidate_minus_body8_shoulder_'+ch]=shoulder_delta[j]
        wr.update({k:record[k] for k in ['unsaturated_GB_mean_increment_counts','unsaturated_GB_increment_disagreement_counts','red_unclamped_from_measured_GB_increment_diagnostic','red_observed_clipped']})
        rows.append(record);wide.append(wr)
write('rim-bounded-left-red-124-pixels.json',{'policy':'Original fixed left y307..<338pt; inset.25/.75pt. Same-tangent original8..<12pt shoulder mean, 8 samples. No shift, fitting or retuning. Raw and ICC identical.','files':meta,'rows':rows})
with (O/'rim-bounded-left-red-124-pixels.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(wide[0]));w.writeheader();w.writerows(wide)
summary=[]
for d in ds:
    rr=[r for r in rows if r['inset_pt']==d];q={'inset_pt':d,'pixels':len(rr),'platforms':{}}
    for k in ims:
        ee=np.array([r['platforms'][k]['edge_rgb'] for r in rr]);ss=np.array([r['platforms'][k]['shoulder_8_12_rgb'] for r in rr]);response=ee-ss
        q['platforms'][k]={'mean_edge_rgb':ee.mean(0),'min_edge_rgb':ee.min(0),'max_edge_rgb':ee.max(0),'mean_shoulder_rgb':ss.mean(0),'mean_response_rgb':response.mean(0),'min_response_rgb':response.min(0),'max_response_rgb':response.max(0),'channel255_counts':(ee==255).sum(0)}
    deltas=np.array([r['candidate_minus_body8_edge_rgb'] for r in rr]);sh=np.array([r['candidate_minus_body8_shoulder_rgb'] for r in rr]);pred=np.array([r['red_unclamped_from_measured_GB_increment_diagnostic'] for r in rr]);cl=np.array([r['red_observed_clipped'] for r in rr]);gbdiff=np.array([r['unsaturated_GB_increment_disagreement_counts'] for r in rr])
    q['candidate_minus_body8']={'mean_edge_rgb':deltas.mean(0),'min_edge_rgb':deltas.min(0),'max_edge_rgb':deltas.max(0),'max_abs_shoulder_delta':abs(sh).max(),'GB_increment_disagreement_max':gbdiff.max(),'GB_increment_agree_within1_count_pixels':int((gbdiff<=1).sum()),'red_observed255_pixels':int(cl.sum()),'red_diagnostic_above255_pixels':int((pred>=255).sum()),'red_diagnostic_above254_5_pixels':int((pred>=254.5).sum()),'red_diagnostic_min_max': [pred.min(),pred.max()],'clipped_red_min_diagnostic_overshoot_counts':float((pred[cl]-255).min()) if cl.any() else None}
    summary.append(q)
S=Path('/Users/kerrylee/.codex/worktrees/android-settings-glass-fixes/sleepy')
refs=[]
for rel in ['libraries/liquid-glass/runtime/src/androidMain/assets/shaders/liquid_glass.agsl','libraries/liquid-glass/runtime/src/androidMain/kotlin/com/lingion/sleepy/ui/component/liquidglass/LiquidGlassShader.kt','libraries/liquid-glass/runtime/src/androidMain/kotlin/com/lingion/sleepy/ui/component/liquidglass/LiquidGlassGeometry.kt','app/src/main/java/com/lingion/sleepy/ui/component/liquidglass/GlassControlModifier.kt']:
    p=S/rel;refs.append({'path':str(p),'sha256':sha(p)})
write('rim-bounded-left-red-summary.json',{'summary':summary,'source_references_at_read':refs,'limits':['Shoulder subtraction is an observed image-response diagnostic, not isolation of only specular light.','Red clipping destroys its true unclamped value; measured unsaturated GB increments do not recover exact shader arithmetic.','Source+paired captures support additive floor as direct mechanism at these side samples; this does not prove an iOS physical lighting model.','CPU flat.06 is zero in the side-to-corner0 first gradient segment; the fixed side samples are within that zero segment.']})
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axs=plt.subplots(2,3,figsize=(12,6),sharex=True)
for ri,d in enumerate(ds):
    rr=[r for r in rows if r['inset_pt']==d];yy=[r['y_pt'] for r in rr]
    for ci,ch in enumerate('RGB'):
        ax=axs[ri,ci]
        for k,col in [('native','#2357a1'),('body8','#777777'),('candidate','#c36d21')]:
            ax.plot(yy,[r['platforms'][k]['edge_rgb'][ci] for r in rr],label=k,color=col,lw=1.3)
        ax.axhline(255,color='#ad2436',ls=':',lw=.8);ax.set_title(f'{ch}; inset {d:.2f}pt',fontsize=10);ax.grid(alpha=.2)
        if ci==0:ax.set_ylabel('Encoded channel value')
        if ri==1:ax.set_xlabel('Original y, pt')
axs[0,0].legend(fontsize=8)
fig.suptitle('Fixed left edge: 62 original pixels per row; additive-floor red clipping')
fig.tight_layout();fig.savefig(O/'rim-bounded-left-red-124-pixels.png',dpi=140);plt.close(fig)
print(json.dumps(clean(summary),indent=2))
