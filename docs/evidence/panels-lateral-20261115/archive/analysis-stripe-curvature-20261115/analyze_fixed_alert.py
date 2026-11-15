#!/usr/bin/env python3
"""Bounded, frozen apparent-color contour diagnostic: historical light Alert only."""
from pathlib import Path
import csv, gzip, hashlib, importlib.util, json, math, re
from collections import Counter
import numpy as np
from PIL import Image, ImageDraw
HERE=Path(__file__).resolve().parent
OP=HERE.parent/'analysis-mapping-audit/paired-slope-feasibility-analysis/analysis.py'
EXPECTED_OP='4182b26a2f7c1d5f0e32c74981bc9c91bb81aae85e1280e4336ab4ea420ead64'
BOUNDS=(54.,324.,72.,306.)
YS=np.arange(257.75,429.5,.5)
TRACKS=('raw_encoded_RGBA','normalized_sRGB_RGBA')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def stats(v):
 v=np.asarray([x for x in v if x is not None],float)
 return {'n':len(v),'min':float(v.min()),'median':float(np.median(v)),'max':float(v.max())} if len(v) else {'n':0}
def runs(indices):
 out=[]
 for i in indices:
  if not out or i!=out[-1][-1]+1:out.append([int(i)])
  else:out[-1].append(int(i))
 return [{'first_y_pt':float(YS[r[0]]),'last_y_pt':float(YS[r[-1]]),'rows':len(r)} for r in out]
def freeze():
 f=json.loads((HERE/'plan-freeze.json').read_text())
 for n,h in f['files_sha256'].items():assert sha(HERE/n)==h,n
 assert sha(OP)==EXPECTED_OP
 original=HERE.parent/'analysis-mapping-audit/paired-slope-feasibility-analysis/implementation-freeze.json'
 assert sha(original)==f['paired_slope_69_check_freeze_unchanged']
 return {'frozen_plan_sha256':sha(HERE/'plan-freeze.json'),'original_69_check_freeze_sha256':sha(original),'operator_sha256':sha(OP),'implementation_sha256':sha(__file__),'scope':'light Alert only, 4 fixed boundaries, native/screen/window separately; no new captures or fits','real_png_pixels_decoded_when_implementation_frozen':0}
def main():
 before=freeze();save(HERE/'execution-predecode-freeze.json',before)
 spec=importlib.util.spec_from_file_location('unchanged_frozen_operator',OP);op=importlib.util.module_from_spec(spec);spec.loader.exec_module(op)
 index=json.loads((HERE/'source-index.json').read_text());condition=index['conditions'][0];assert condition['scene']=='color_stripes-light-alert'
 records=condition['files']; decoded={}; metadata={}
 names={'native':'native','android_screen':'screen_png','android_window':'window_png','source':'native_source'}
 for name,key in names.items():
  r=records[key];p=Path(r['path']);assert sha(p)==r['sha256'],key
  tracks,md=op.decode_png(p.read_bytes(),tuple(r['IHDR_fields_without_decode'][:2]));assert tracks and md['structurally_valid'],key
  decoded[name]=tracks;metadata[name]={'path':str(p),'sha256':sha(p),'png':md,'tracks':list(tracks),'raw_equals_normalized':bool(np.array_equal(tracks.get(TRACKS[0]),tracks.get(TRACKS[1])))}
 # Native foreground boxes come only from inside the Alert subtree. Underlying
 # show-sheet/show-alert/show-menu buttons are context, not foreground masks.
 ax=Path(records['native_AX']['path']).read_text().split("Alert, 0x10abf5b80",1)[1]
 fg=[]
 for line in ax.splitlines():
  if not re.search(r'\b(?:StaticText|Button|TextField),',line):continue
  m=re.search(r'\{\{([-\d.]+), ([-\d.]+)\}, \{([-\d.]+), ([-\d.]+)\}\}',line)
  if m:
   x,y,w,h=map(float,m.groups());fg.append({'platform':'native_AX','label':line.strip(),'bounds_pt':[x,y,x+w,y+h]})
 assert len(fg)==4,len(fg)
 for r in condition['android_metadata']['measurements']:
  if r['tag']!='static-alert-carrier':fg.append({'platform':'android_actual','label':r['tag'],'bounds_pt':[v/2 for v in r['actual_screen_rect_px']]})
 assert len(fg)==8
 origin=condition['android_metadata']['window_geometry']['root_screen_origin_px'];assert origin==[46,509]
 series=[];all_rows=[]
 for image_name in ('native','android_screen','android_window'):
  origin_px=np.array(origin if image_name=='android_window' else [0,0],int)
  for track in TRACKS:
   if track not in decoded[image_name] or track not in decoded['source']:
    series.append({'image':image_name,'track':track,'unavailable':'no supported normalized source/output track'});continue
   im=decoded[image_name][track];src=decoded['source'][track]
   for xb in BOUNDS:
    xx=np.arange(xb-9+.25,xb+9,.5);xi=(xx*2).astype(int)-origin_px[0]
    p0=(xx>=xb-9)&(xx<xb-1);p1=(xx>=xb+1)&(xx<xb+9)
    assert len(xx)==36 and p0.sum()==16 and p1.sum()==16
    source_row=src[int(350.25*2),:,:3].astype(float)
    a=source_row[int((xb-.25)*2)];b=source_row[int((xb+.25)*2)];direction=b-a
    rows=[]
    for iy,y in enumerate(YS):
     yi=int(y*2)-origin_px[1];assert 0<=yi<im.shape[0] and xi.min()>=0 and xi.max()<im.shape[1]
     support=[xb-9,y-.25,xb+9,y+.25]
     hit=[r for r in fg if op.intersects(support,op.expand(r['bounds_pt']))]
     rgb=im[yi,xi,:3];alpha=im[yi,xi,3]
     f=op.feature_operator(xx,rgb,rgb[p0],rgb[p1],direction,clear_support_px=36 if not hit else 0,foreground_collisions=hit)
     f.update({'image':image_name,'track':track,'boundary_pt':xb,'boundary_role':'primary' if xb in BOUNDS[:2] else 'secondary','side':'left' if xb<187.5 else 'right','y_pt':float(y),'rgb_samples':rgb.tolist(),'alpha_samples':alpha.tolist(),'scan_support_world_pt':support,'source_left_RGB':a.tolist(),'source_right_RGB':b.tolist(),'image_origin_screen_px':origin_px.tolist()})
     # Alpha is retained as context, without adding or relaxing a frozen gate.
     f['observed_alpha_range']=[int(alpha.min()),int(alpha.max())]
     rows.append(f)
    center=[r for r in rows if 350<=r['y_pt']<359]
    assert len(center)==18
    center_ok=all(r['eligible'] for r in center)
    ref=None
    if center_ok:
     cv=np.array([r['cross50_pt'] for r in center]);ce=np.array([r['location_uncertainty_pt'] for r in center]);value=float(np.median(cv));lo=float(np.median(cv-ce));hi=float(np.median(cv+ce));ref={'value_pt':value,'interval_pt':[lo,hi],'absolute_bound_pt':max(value-lo,hi-value),'all_18_rows_eligible':True}
    for i,r in enumerate(rows):
     if r['eligible'] and ref:
      delta=r['cross50_pt']-ref['value_pt'];err=r['location_uncertainty_pt']+ref['absolute_bound_pt'];sign=-1 if xb<187.5 else 1
      r['relative_to_center']={'delta_x_pt':delta,'outward_pt':sign*delta,'absolute_bound_pt':err,'delta_x_interval_pt':[delta-err,delta+err],'outward_interval_pt':[sign*delta-err,sign*delta+err]}
     if i>=8 and i+8<len(rows) and all(z['eligible'] for z in rows[i-8:i+9]):
      l,c,u=rows[i-8],r,rows[i+8];s=(u['cross50_pt']-l['cross50_pt'])/8;q=(u['cross50_pt']-2*c['cross50_pt']+l['cross50_pt'])/16
      se=(u['location_uncertainty_pt']+l['location_uncertainty_pt'])/8;qe=(u['location_uncertainty_pt']+2*c['location_uncertainty_pt']+l['location_uncertainty_pt'])/16
      srange=[s-se,s+se];qrange=[q-qe,q+qe];mn=0 if srange[0]<=0<=srange[1] else min(abs(z) for z in srange);mx=max(abs(z) for z in srange);den=[(1+mn*mn)**1.5,(1+mx*mx)**1.5];ki=[v/d for v in qrange for d in den]
      r['fixed_h4_derivative']={'slope_dx_per_dy':s,'slope_absolute_bound':se,'inclination_deg':math.degrees(math.atan(s)),'inclination_interval_deg':[math.degrees(math.atan(s-se)),math.degrees(math.atan(s+se))],'second_dx_per_dy2_per_pt':q,'second_absolute_bound_per_pt':qe,'apparent_signed_curvature_per_pt':q/(1+s*s)**1.5,'curvature_interval_per_pt':[min(ki),max(ki)],'complete_17_row_support':True}
    eligible=[i for i,r in enumerate(rows) if r['eligible']]
    rec={'image':image_name,'track':track,'boundary_pt':xb,'side':rows[0]['side'],'rows_total':len(rows),'eligible_rows':len(eligible),'eligible_runs':runs(eligible),'all_failed_gate_counts':dict(Counter(g for r in rows for g in r['failed_gates'])),'center_reference':ref,'center_reference_failed_rows':[{'y_pt':r['y_pt'],'failed_gates':r['failed_gates']} for r in center if not r['eligible']],'source_transition_RGB':[a.tolist(),b.tolist()],'regions':{}}
    for region,lo,hi in [('top24',257.5,281.5),('bottom24',405.5,429.5),('center_reference',350,359),('all',257.5,429.5)]:
     rr=[r for r in rows if lo<=r['y_pt']<hi];ok=[r for r in rr if r['eligible']]
     rec['regions'][region]={'rows':len(rr),'eligible_rows':len(ok),'x50_pt':stats([r.get('cross50_pt') for r in ok]),'delta_x_pt':stats([r.get('relative_to_center',{}).get('delta_x_pt') for r in ok]),'outward_pt':stats([r.get('relative_to_center',{}).get('outward_pt') for r in ok]),'slope':stats([r.get('fixed_h4_derivative',{}).get('slope_dx_per_dy') for r in ok]),'inclination_deg':stats([r.get('fixed_h4_derivative',{}).get('inclination_deg') for r in ok]),'curvature_per_pt':stats([r.get('fixed_h4_derivative',{}).get('apparent_signed_curvature_per_pt') for r in ok]),'outward_positive_absolute_bound_excluded_zero_rows':sum(r.get('relative_to_center',{}).get('outward_interval_pt',[0,0])[0]>0 for r in ok),'outward_negative_absolute_bound_excluded_zero_rows':sum(r.get('relative_to_center',{}).get('outward_interval_pt',[0,0])[1]<0 for r in ok)}
    series.append(rec);all_rows+=rows
 # Keep all failing branches, full RGB, alpha, projections, peaks and crossings.
 with gzip.open(HERE/'rows.jsonl.gz','wt',encoding='utf-8',compresslevel=6) as f:
  for r in all_rows:f.write(json.dumps(r,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\n')
 fields=['image','track','boundary_pt','y_pt','eligible','x50_pt','diagnostic_cross50_pt','uncertainty_pt','delta_x_pt','outward_pt','relative_bound_pt','slope','slope_bound','inclination_deg','curvature_per_pt','curvature_lo','curvature_hi','failed_gates']
 with (HERE/'contours.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for r in all_rows:
   rel=r.get('relative_to_center',{});d=r.get('fixed_h4_derivative',{});ki=d.get('curvature_interval_per_pt',[None,None]);w.writerow({'image':r['image'],'track':r['track'],'boundary_pt':r['boundary_pt'],'y_pt':r['y_pt'],'eligible':r['eligible'],'x50_pt':r.get('cross50_pt'),'diagnostic_cross50_pt':r.get('diagnostic_cross50_pt'),'uncertainty_pt':r.get('location_uncertainty_pt'),'delta_x_pt':rel.get('delta_x_pt'),'outward_pt':rel.get('outward_pt'),'relative_bound_pt':rel.get('absolute_bound_pt'),'slope':d.get('slope_dx_per_dy'),'slope_bound':d.get('slope_absolute_bound'),'inclination_deg':d.get('inclination_deg'),'curvature_per_pt':d.get('apparent_signed_curvature_per_pt'),'curvature_lo':ki[0],'curvature_hi':ki[1],'failed_gates':'|'.join(r['failed_gates'])})
 by={(r['image'],r['track'],r['boundary_pt'],r['y_pt']):r for r in all_rows};paired=[]
 for other in ('android_screen','android_window'):
  for track in TRACKS:
   for xb in BOUNDS:
    vals=[]
    for y in YS:
     n=by[('native',track,xb,float(y))];a=by[(other,track,xb,float(y))]
     if n['eligible'] and a['eligible']:vals.append({'y_pt':float(y),'android_minus_native_x_pt':a['cross50_pt']-n['cross50_pt'],'sum_absolute_bounds_pt':a['location_uncertainty_pt']+n['location_uncertainty_pt']})
    paired.append({'image':other,'track':track,'boundary_pt':xb,'same_y_eligible_rows':len(vals),'absolute_x_difference_pt':stats([r['android_minus_native_x_pt'] for r in vals]),'rows':vals})
 summary={'label':'APPARENT COLORED CONTOURS, not unique2D mapping or true thickness','scope':'color_stripes-light-alert only; previously observed historical calibration; Android mixed/unaccepted budget r2','execution_freeze':before,'decoded_originals':metadata,'real_images_decoded':4,'real_png_pixels_decoded':sum(v[TRACKS[0]].shape[0]*v[TRACKS[0]].shape[1] for v in decoded.values()),'foreground_union_unexpanded':fg,'foreground_expansion_pt':2,'series':series,'paired_comparisons':paired,'limitations':['Source is periodic 18pt stripes: apparent color boundary identification is not unique 2D inversion.','Old native before/source/rest phases and Android context differ; no clean repeat/after source gate is manufactured.','All raw and smooth crossings, multi-peaks and failures retained; no nearest-branch matching or changed gates.','Full screen and actual Window analyzed independently at measured origin; rejected display never decoded.','Window alpha retained without inventing a new gate; contour can include material boundary/context effects.','Fixed 0.25pt floor and absolute bounds propagated; no independent-Gaussian/noise assumption.','Derived derivatives require every row in fixed +/-4pt support eligible; no interpolation across gaps.']}
 save(HERE/'analysis.json',summary)
 # Small original integer crop comparison: no output warping or blur.
 canvas=Image.new('RGB',(1300,380),'#eeeeee');draw=ImageDraw.Draw(canvas)
 for i,k in enumerate(('native','android_screen')):
  arr=decoded[k][TRACKS[0]][515:859,55:695,:3];canvas.paste(Image.fromarray(arr),(10+i*645,28));draw.text((10+i*645,8),k+' original 640x344 crop',fill='black')
 canvas.save(HERE/'small-original-comparison.png')
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 fig,axs=plt.subplots(1,4,figsize=(11,6),sharey=True)
 for ax,xb in zip(axs,BOUNDS):
  for image,col in [('native','#111111'),('android_screen','#e87920'),('android_window','#159a83')]:
   rr=[r for r in all_rows if r['image']==image and r['track']==TRACKS[0] and r['boundary_pt']==xb]
   for run in runs([i for i,r in enumerate(rr) if r['eligible']]):
    rrr=[r for r in rr if run['first_y_pt']<=r['y_pt']<=run['last_y_pt']];ax.plot([r['cross50_pt']-xb for r in rrr],[r['y_pt'] for r in rrr],color=col,lw=1.5,label=image if run==runs([i for i,r in enumerate(rr) if r['eligible']])[0] else None)
   # Every 50% branch retained, faint points; no branch selected from failures.
   for r in rr:
    if not r['eligible']:
     branches=r.get('smoothed_crossings',{}).get('50',{}).get('increasing',[])
     ax.scatter([x-xb for x in branches],[r['y_pt']]*len(branches),s=2,color=col,alpha=.12)
  ax.axvline(0,color='gray',lw=.7);ax.axhspan(350,359,color='#88bbdd',alpha=.15);ax.set_title(f'fixed boundary x={xb:g}pt');ax.set_xlim(-9,9);ax.set_xlabel('x50 - source boundary [pt]');ax.grid(alpha=.2)
 axs[0].set_ylim(429.5,257.5);axs[0].set_ylabel('world y [pt]');axs[0].legend(fontsize=7)
 fig.suptitle('Apparent colored contours — eligible contiguous curves; faint dots retain failed 50% branches\nraw encoded; normalized sRGB is byte-identical; no contour fit / correspondence assertion',fontsize=10);fig.tight_layout();fig.savefig(HERE/'apparent-contours.png',dpi=130);plt.close(fig)
 lines=['# Fixed light Alert apparent-color diagnostic','', 'Only the frozen four boundaries were analyzed. Raw and normalized-sRGB tracks are identical by explicit PNG sRGB provenance. Screen and Window remain separate. This is historical calibration and does not identify unique2Dmap, physical thickness or native equivalence.','', '| image | source boundary | eligible / 344 | center reference | top24 outward median [pt] | bottom24 outward median [pt] |','|---|---:|---:|---:|---:|---:|']
 for r in series:
  if r['track']!=TRACKS[0]:continue
  num=lambda v:'unavailable' if v is None else f'{v:.4f}'
  lines.append(f"| {r['image']} | {r['boundary_pt']:g} | {r['eligible_rows']} | {num((r.get('center_reference') or {}).get('value_pt'))} | {num(r['regions']['top24']['outward_pt'].get('median'))} | {num(r['regions']['bottom24']['outward_pt'].get('median'))} |")
 lines+=['','Failed rows stay failed. `rows.jsonl.gz` retains RGB/alpha, all 10/50/90 up/down/tie branches, peak structure and exact failed gates. `contours.csv` contains x(y), center differences and h=4pt slope/angle/curvature only on complete contiguous eligible support. `analysis.json` contains every support and paired difference; no favorable branch or center segment is substituted.','','Foreground masks jointly exclude native AX and actual Android front slots (+2pt). In particular y363.5–415.5 is occluded at these supports; no derivative crosses it. Native underlying source buttons remain historical context, not reclassified as front masks.','','`small-original-comparison.png` is two exact 640×344 integer crops. `apparent-contours.png` shows eligible contiguous curves; faint points preserve every failed 50% branch and are not measurements accepted by the gate.']
 (HERE/'RESULTS.md').write_text('\n'.join(lines)+'\n')
 save(HERE/'execution-result.json',{'status':'bounded historical light Alert executed; no fit or runtime change','real_images_decoded':4,'series':len(series),'detailed_rows':len(all_rows),'artifacts_sha256':{n:sha(HERE/n) for n in ['analysis.json','contours.csv','rows.jsonl.gz','RESULTS.md','small-original-comparison.png','apparent-contours.png']},'original_freezes_unchanged':freeze()==before})
 print(json.dumps({'series':[{k:r[k] for k in ['image','track','boundary_pt','eligible_rows','center_reference','regions','all_failed_gate_counts']} for r in series if r['track']==TRACKS[0]],'output':str(HERE)},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
