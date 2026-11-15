#!/usr/bin/env python3
"""Local oracle contours, with fixed supports; no optical fit or source-map solve."""
from pathlib import Path
import hashlib,json,csv,io,sys
import numpy as np
from PIL import Image,ImageCms
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parent;P=O.parent;S=P/'panel-probes-preparation';N=P/'native-panel-feasibility-preparation/attachments';A=P/'panels-nonperiodic-baseline-20261115';Z=P/'panels-nonperiodic-refraction-zero-20261115'
if len(sys.argv)>2:
    target=(O/sys.argv[2]).resolve();assert target.is_relative_to(O) and target!=O
    O=target;O.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(name,ob):(O/name).write_text(json.dumps(ob,indent=2,allow_nan=False)+'\n')
zero_files=[Z/'matrix.json',Z/'capture-result.json']+list(Z.glob('*-screen.png'))
zf=O/'zero-before-decode.json'
if not zf.exists():write('zero-before-decode.json',{'status':'before-first-zero-output-decode','files':{str(p):sha(p) for p in zero_files if p.exists()},'purpose':'single-variable refraction60→0 mechanism ablation; not a fix or parameter fit','unchanged_S02_transects':'All original rows y261.75..277.25pt in0.5pt steps; fixed right-edge scan x84.25..141.75pt, high plateau84..92, neutral120..140. New local operational plateau limits are declared before zero decode; parent analysis plan fixed support remains unchanged.'})
def load(p):return np.asarray(Image.open(p).convert('RGB'),float)
ims={'source':load(S/'inputs/panel_probe_shapes.png'),'native':load(N/'26EDA3DE-BADE-47D2-B16B-53CD93B19564.png'),'baseline60':load(A/'panel_probe_shapes-light-alert-rest-screen.png')}
if (Z/'capture-result.json').exists():ims['zero0']=load(Z/'panel_probe_shapes-light-alert-rest-screen.png')
candidate=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else None
if candidate:
    frozen=O/'rim-candidate-before-decode.json'
    if not frozen.exists():write(frozen.name,{'purpose':'Single rimBlur mechanism candidate; reuse unchanged baseline local supports and extraction','candidate_path':str(candidate),'files':{str(p):sha(p) for p in [candidate/'matrix.json',candidate/'capture-result.json']+list(candidate.glob('*-screen.png')) if p.exists()}})
    ims['rim_blur']=load(candidate/'panel_probe_shapes-light-alert-rest-screen.png')
u=np.array([-154.,-89.,41.]);u/=np.linalg.norm(u)
xs=np.arange(168,284);x=(xs+.5)/2
k=np.exp(-np.arange(-3,4)**2/(2*1.5**2));k/=k.sum()
def smooth(v):return np.convolve(np.pad(v,(3,3),mode='reflect'),k,'valid')
def falling_crossings(q,level):
    out=[]
    for i in range(len(q)-1):
        if q[i]>=level and q[i+1]<level:out.append(float(x[i]+(level-q[i])/(q[i+1]-q[i])*.5))
    return out
rows=[];tr=[]
for y in np.arange(261.75,277.5,.5):
    yi=int(y*2)
    for plat,v in ims.items():
        rgb=v[yi];neutral=np.median(rgb[240:280],0);high=np.median(rgb[168:184],0);vec=high-neutral;amp=float(np.sum(vec*u));spread=float(1.4826*np.median(np.abs(np.sum((rgb[240:280]-neutral)*u,1))));cos=float(np.sum(vec*u)/(np.linalg.norm(vec))) if np.linalg.norm(vec)>0 else 0
        q=np.sum((rgb[xs]-neutral)*u,1);qs=smooth(q);der=-np.gradient(qs,.5);peaks=[i for i in range(1,len(der)-1) if der[i]>=der[i-1] and der[i]>der[i+1] and der[i]>0];peaks=sorted(peaks,key=lambda i:der[i],reverse=True);primary=peaks[0] if peaks else None;secondary=next((i for i in peaks[1:] if abs(i-primary)>3),None) if primary is not None else None;ratio=float(der[secondary]/der[primary]) if secondary is not None else 0
        cs={f'cross{z}':falling_crossings(qs,amp*z/100) for z in [10,50,90]};rawcs={f'raw_cross{z}':falling_crossings(q,amp*z/100) for z in [10,50,90]};fail=[]
        if amp<8:fail.append('contrast<8')
        if amp<5*max(1.,spread):fail.append('contrast<5x_neutral_spread_floor1')
        if cos<.7:fail.append('source_color_direction_cosine<0.7')
        if ratio>.8:fail.append('secondary_peak>0.8primary')
        if any(len(v)!=1 for v in cs.values()):fail.append('threshold_crossing_not_unique_or_missing')
        # All values between90% and10% crossings must descend, allowing only
        # sub-quantization1count projected differences, logged explicitly.
        raw_up=None;plateau_hi_range=float(np.ptp(np.sum((rgb[168:184]-neutral)*u,1)));plateau_neutral_range=float(np.ptp(np.sum((rgb[240:280]-neutral)*u,1)))
        if all(len(v)==1 for v in cs.values()):
            t0,t1=cs['cross90'][0],cs['cross10'][0];ii=(x>=t0)&(x<=t1);up=np.diff(q[ii]);raw_up=float(np.max(up)) if len(up) else 0
            if raw_up>1:fail.append('transition_nonmonotone_above1count')
        uncertainty=.25
        if primary is not None:
            tied=np.flatnonzero(np.isclose(der,der[primary],rtol=0,atol=1e-9));uncertainty+=float((tied.max()-tied.min())*.25) if len(tied) else 0
        if uncertainty>1:fail.append('location_uncertainty>1pt')
        r={'feature':'S02_right_local_contour','platform':plat,'y_pt':float(y),'distance_from_alert_top_pt':float(y-257.5),'input_source_id':'S02','fixed_scan_x_pt':[84.25,141.75],'high_plateau_x_pt':[84,92],'neutral_plateau_x_pt':[120,140],'contrast_amplitude':amp,'contrast_rgb':vec.tolist(),'source_color_direction_cosine':cos,'neutral_robust_spread_counts':spread,'high_plateau_projected_range':plateau_hi_range,'neutral_plateau_projected_range':plateau_neutral_range,'secondary_peak_ratio':ratio,'raw_transition_max_upward_step':raw_up,'minimum_location_uncertainty_pt':uncertainty,'eligible':not fail,'failed_gates':fail,**cs,**rawcs}
        if all(len(v)==1 for v in rawcs.values()):r['descriptive_raw_width_10_90_pt']=rawcs['raw_cross10'][0]-rawcs['raw_cross90'][0]
        if not fail:r['apparent_width_10_90_pt']=cs['cross10'][0]-cs['cross90'][0];r['crossing_50_pt']=cs['cross50'][0]
        rows.append(r)
        for j,xx in enumerate(x):tr.append({'platform':plat,'feature':'S02','y_pt':y,'x_pt':xx,'contrast_raw':q[j],'contrast_smoothed':qs[j],'negative_d1_per_pt':der[j],**{f'raw_{c}':rgb[xs[j],i] for i,c in enumerate('rgb')}})
write('S02-local-contours.json',rows)
with (O/'S02-local-transects.csv').open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(tr[0]));w.writeheader();w.writerows(tr)
fig,ax=plt.subplots(2,2,figsize=(11,6.4),sharex=True)
for yy,axx in zip([261.75,265.75,269.75,273.75],ax.flat):
    for plat in ims:
        rr=[r for r in tr if r['platform']==plat and r['y_pt']==yy];axx.plot([r['x_pt'] for r in rr],[r['contrast_smoothed'] for r in rr],label=plat)
    axx.set_title(f'S02 fixed y={yy}pt, inward={yy-257.5}pt');axx.set_ylabel('source-direction contrast (encoded)');axx.grid(alpha=.2)
ax[0,0].legend();fig.tight_layout();fig.savefig(O/'S02-local-contours.png',dpi=130);plt.close(fig)
print(json.dumps([r for r in rows if r['y_pt'] in [261.75,265.75,269.75,273.75]],indent=2))

# A single fixed oracle seam in the preregistered Alert top-left segment.  The
# two x plateaus remain inside their original adjacent source cells. This is
# a local scalar color contour diagnostic, not an inverse2D color/source solve.
grid={'source':load(S/'inputs/panel_probe_coordinate.png'),'native':load(N/'5F2FA6A3-1BFF-4023-8E0A-10DCBF5C2BC2.png'),'baseline60':load(A/'panel_probe_coordinate-light-alert-rest-screen.png')}
if (Z/'capture-result.json').exists():grid['zero0']=load(Z/'panel_probe_coordinate-light-alert-rest-screen.png')
if candidate:grid['rim_blur']=load(candidate/'panel_probe_coordinate-light-alert-rest-screen.png')
gr=[];gt=[]
xs=np.arange(124,208);x=(xs+.5)/2
for y in np.arange(261.75,277.5,.5):
    yi=int(y*2);sr=grid['source'][yi];cv=np.median(sr[192:208],0)-np.median(sr[124:140],0);unit=cv/np.linalg.norm(cv)
    for plat,v in grid.items():
        rgb=v[yi];left=np.median(rgb[124:140],0);right=np.median(rgb[192:208],0);vec=right-left;amp=float(np.sum(vec*unit));cos=float(amp/np.linalg.norm(vec)) if np.linalg.norm(vec) else 0
        q=np.sum((rgb[xs]-left)*unit,1);qs=smooth(q);der=np.gradient(qs,.5);peaks=[i for i in range(1,len(der)-1) if der[i]>=der[i-1] and der[i]>der[i+1] and der[i]>0];peaks=sorted(peaks,key=lambda i:der[i],reverse=True);primary=peaks[0] if peaks else None;secondary=next((i for i in peaks[1:] if abs(i-primary)>3),None) if primary is not None else None;ratio=float(der[secondary]/der[primary]) if secondary is not None else 0
        # Reuse the frozen coordinate x array to find increasing crossings.
        cs={f'cross{z}':falling_crossings(-qs,-amp*z/100) for z in [10,50,90]};rawcs={f'raw_cross{z}':falling_crossings(-q,-amp*z/100) for z in [10,50,90]};spreads=[float(1.4826*np.median(np.abs(np.sum((rgb[b:e]-lev)*unit,1)))) for b,e,lev in [(124,140,left),(192,208,right)]]
        fail=[]
        if amp<8:fail.append('contrast<8')
        if amp<5*max(1.,*spreads):fail.append('contrast<5x_local_spread_floor1')
        if cos<.7:fail.append('source_contrast_direction_cosine<0.7')
        if ratio>.8:fail.append('secondary_peak>0.8primary')
        if any(len(v)!=1 for v in cs.values()):fail.append('missing_or_nonunique_plateau_crossing')
        gr.append({'feature':'coordinate_vertical_seam_x77pt','source_adjacent_x_cells_px':[[72,154],[154,244]],'source_normal_y_cell_px':[418,530] if y<265 else [530,642],'platform':plat,'y_pt':float(y),'distance_pt':float(y-257.5),'left_plateau_x_pt':[62,70],'right_plateau_x_pt':[96,104],'contrast_amplitude':amp,'source_contrast_rgb':cv.tolist(),'output_contrast_rgb':vec.tolist(),'source_direction_cosine':cos,'local_plateau_spread_counts':spreads,'secondary_peak_ratio':ratio,'eligible':not fail,'failed_gates':fail,**cs,**rawcs})
        for j,xx in enumerate(x):gt.append({'platform':plat,'feature':'coordinate_x77','y_pt':y,'x_pt':xx,'contrast_raw':q[j],'contrast_smoothed':qs[j],'positive_d1_per_pt':der[j]})
write('coordinate-local-contours.json',gr)
with (O/'coordinate-local-transects.csv').open('w',newline='') as f:w=csv.DictWriter(f,list(gt[0]));w.writeheader();w.writerows(gt)
fig,axs=plt.subplots(2,2,figsize=(11,6.4),sharex=True)
for yy,axx in zip([261.75,265.75,269.75,273.75],axs.flat):
    for plat in grid:
        rr=[r for r in gt if r['platform']==plat and r['y_pt']==yy];axx.plot([r['x_pt'] for r in rr],[r['contrast_smoothed'] for r in rr],label=plat)
    axx.set_title(f'Coordinate x77 seam at y={yy}pt');axx.set_ylabel('source-seam contrast (encoded)');axx.grid(alpha=.2)
axs[0,0].legend();fig.tight_layout();fig.savefig(O/'coordinate-local-contours.png',dpi=130);plt.close(fig)
