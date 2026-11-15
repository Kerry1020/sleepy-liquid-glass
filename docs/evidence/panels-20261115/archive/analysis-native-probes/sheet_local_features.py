#!/usr/bin/env python3
"""Exploratory Sheet local contour inside the unchanged frozen support/ROI."""
from pathlib import Path
import csv,hashlib,json,sys
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parent;P=ROOT.parent;O=ROOT/(sys.argv[2] if len(sys.argv)>2 else 'sigma-unified');O.mkdir(exist_ok=True)
C=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else P/'panels-clear-edge-sigma-20261115'
paths={'source':P/'panel-probes-preparation/inputs/panel_probe_shapes.png','native':P/'native-panel-feasibility-preparation/attachments/D7877EDC-B156-4BCF-8306-36EC447D522E.png','baseline60':P/'panels-nonperiodic-baseline-20261115/panel_probe_shapes-light-share_sheet-rest-screen.png','candidate':C/'panel_probe_shapes-light-share_sheet-rest-screen.png'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(fn,obj):(O/fn).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
plan={'status':'exploratory operational local extraction after existing screenshot decode, not independent preregistration','source_id':'S07 cross vertical stem right edge','source_vertices_after_y668.9px':'stem x153.1..190.9px, y668.9..704px','frozen_parent_region':'Sheet top_left x48..110pt, inward[-5.75,24)pt','local_scan_x_pixel_centers_pt':[84.25,109.75],'row_centers_pt':[334.75,341.25],'row_step_pt':.5,'high_plateau_pt':[84,90],'neutral_plateau_pt':[100,110],'reason':'The upper horizontal arm has no right gray plateau inside frozen x110 bound; only stem rows have one. Both plateaus use original known source membership. No ROI movement or centroid completion.','gates':'same frozen source direction/contrast,5xrobustspread_floor1,secondary_peak<=.8,12clear_pixels,±.25pt minimum sampling floor','files':{k:{'path':str(v),'sha256':sha(v)} for k,v in paths.items()}}
save('Sheet-S07-local-plan.json',plan)
ims={k:np.asarray(Image.open(v).convert('RGB'),float) for k,v in paths.items()};u=np.array([31.,-141.,-30.]);u/=np.linalg.norm(u);xs=np.arange(168,220);x=(xs+.5)/2;kernel=np.exp(-np.arange(-3,4)**2/(2*1.5**2));kernel/=kernel.sum()
def smooth(v):return np.convolve(np.pad(v,(3,3),mode='reflect'),kernel,'valid')
def cross(q,level):
    z=[]
    for i in range(len(q)-1):
        if q[i]>=level and q[i+1]<level:z.append(float(x[i]+(level-q[i])/(q[i+1]-q[i])*.5))
    return z
rows=[];tracks=[]
for yy in np.arange(334.75,341.5,.5):
    for plat,im in ims.items():
        rgb=im[int(2*yy)];hi=np.median(rgb[168:180],0);ne=np.median(rgb[200:220],0);vec=hi-ne;amp=float(np.sum(vec*u));cos=float(amp/np.linalg.norm(vec)) if np.linalg.norm(vec) else 0.;spr=float(1.4826*np.median(np.abs(np.sum((rgb[200:220]-ne)*u,1))));q=np.sum((rgb[xs]-ne)*u,1);qs=smooth(q);der=-np.gradient(qs,.5);peaks=sorted([i for i in range(1,len(q)-1) if der[i]>=der[i-1] and der[i]>der[i+1] and der[i]>0],key=lambda i:der[i],reverse=True);primary=peaks[0] if peaks else None;secondary=next((i for i in peaks[1:] if abs(i-primary)>3),None) if primary is not None else None;ratio=float(der[secondary]/der[primary]) if secondary is not None else 0.;cs={f'cross{z}':cross(qs,amp*z/100) for z in [10,50,90]};rawcs={f'raw_cross{z}':cross(q,amp*z/100) for z in [10,50,90]};fail=[]
        if amp<8:fail.append('contrast<8')
        if amp<5*max(1,spr):fail.append('contrast<5x_neutral_spread_floor1')
        if cos<.7:fail.append('source_direction_cosine<0.7')
        if ratio>.8:fail.append('secondary_peak>0.8primary')
        if any(len(v)!=1 for v in cs.values()):fail.append('threshold_crossing_missing_or_nonunique')
        if all(len(v)==1 for v in cs.values()):
            ii=(x>=cs['cross90'][0])&(x<=cs['cross10'][0]);steps=np.diff(q[ii]);maxup=float(steps.max()) if len(steps) else 0
            if maxup>1:fail.append('transition_nonmonotone_above1count')
        else:maxup=None
        tied=np.flatnonzero(np.isclose(der,der[primary],rtol=0,atol=1e-9)) if primary is not None else [];unc=.25+(float((tied.max()-tied.min())*.25) if len(tied) else 0)
        if unc>1:fail.append('location_uncertainty_floor>1pt')
        rec={'source_id':'S07','carrier':'sheet','platform':plat,'world_y_pt':float(yy),'inward_distance_pt':float(yy-317.5),'source_high_rgb':[215,43,154],'source_low_rgb':[184,184,184],'output_contrast_rgb':vec.tolist(),'source_direction_cosine':cos,'contrast_amplitude':amp,'neutral_robust_spread':spr,'secondary_peak_ratio':ratio,'raw_transition_max_upward_step':maxup,'minimum_location_uncertainty_pt':unc,'eligible':not fail,'failed_gates':fail,**cs,**rawcs}
        if all(len(v)==1 for v in rawcs.values()):rec['descriptive_raw_10_90_width_pt']=rawcs['raw_cross10'][0]-rawcs['raw_cross90'][0]
        if all(len(v)==1 for v in cs.values()):rec['descriptive_smoothed_10_90_width_pt']=cs['cross10'][0]-cs['cross90'][0]
        rows.append(rec)
        for i,xx in enumerate(x):tracks.append({'platform':plat,'world_y_pt':yy,'world_x_pt':xx,'contrast_raw':q[i],'contrast_smoothed':qs[i],'negative_d1':der[i],**{f'raw_{ch}':rgb[xs[i],j] for j,ch in enumerate('rgb')}})
save('Sheet-S07-local-contours.json',rows)
with (O/'Sheet-S07-local-transects.csv').open('w',newline='') as f:w=csv.DictWriter(f,list(tracks[0]));w.writeheader();w.writerows(tracks)
fig,axs=plt.subplots(2,2,figsize=(11,6.4),sharex=True)
for yy,ax in zip([335.75,337.75,339.75,341.25],axs.flat):
    for plat in ims:
        rr=[r for r in tracks if r['platform']==plat and r['world_y_pt']==yy];ax.plot([r['world_x_pt'] for r in rr],[r['contrast_smoothed'] for r in rr],label=plat)
    ax.set_title(f'Sheet S07 stem y={yy}pt, inward={yy-317.5}pt');ax.grid(alpha=.2);ax.set_ylabel('S07 direction contrast')
axs[0,0].legend();fig.tight_layout();fig.savefig(O/'Sheet-S07-local-contours.png',dpi=130);plt.close(fig)
print(json.dumps({'platforms':{plat:{'passing':sum(r['eligible'] for r in rows if r['platform']==plat),'rows':sum(r['platform']==plat for r in rows)} for plat in ims},'selected':[r for r in rows if r['world_y_pt'] in [335.75,337.75,339.75,341.25]]},indent=2))
