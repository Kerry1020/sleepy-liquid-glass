#!/usr/bin/env python3
"""Check this bounded public evidence package without building app code."""
from pathlib import Path
import csv,hashlib,json,math,re
from PIL import Image
ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data';OUT=ROOT.parent/'images/research'
def rows(name):return list(csv.DictReader((DATA/name).open()))
def close(a,b):assert math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-11),(a,b)
def rms(xs):return math.sqrt(sum(x*x for x in xs)/len(xs))
manifest=json.loads((ROOT/'figure-manifest.json').read_text());checks=0
for r in manifest['outputs']:
 p=OUT/r['path'];b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==r['sha256'];assert len(b)==r['bytes'];checks+=2
 if p.suffix=='.png':
  im=Image.open(p);assert not im.getexif();Image.open(p).verify();checks+=2
old={(r['gesture_index'],r['native_raw_line']):r for r in rows('dock-android69.csv')};new=rows('dock-android72.csv')
assert len(new)==541;common=[r for r in new if r['android_wholly_held']=='True' and old[(r['gesture_index'],r['native_raw_line'])]['android_wholly_held']=='True'];assert len(common)==540;checks+=2
for case in json.loads((DATA/'dock-summary.json').read_text())['cases']:
 rs=[r for r in common if int(r['gesture_index'])==case['gesture_index']];assert len(rs)==case['n']
 close(rms([float(r['total_center_difference_dp']) for r in rs]),case['android72']['rmse']);close(rms([float(old[(r['gesture_index'],r['native_raw_line'])]['total_center_difference_dp']) for r in rs]),case['android69']['rmse']);checks+=3
computed=json.loads((DATA/'computed-results.json').read_text())
for result in computed['menu_corners']:
 rs=[r for r in rows('menu-corners.csv') if r['corner']==result['corner'] and 2<=float(r['depth'])<=24 and r['usable_all_thresholds']=='True' and r['flat_matched_input_all_thresholds']=='True'];assert len(rs)==result['n']==44
 for column,out in [('baseline_reference','baseline_mae'),('candidate_reference','candidate_mae')]:close(sum(abs(float(r[column])-float(r['native_reference'])) for r in rs)/len(rs),result[out])
 checks+=3
fit=rows('slider-native-fit.csv');assert len(fit)==907;checks+=1
for result in computed['slider_native_exact_prediction']:
 rs=[r for r in fit if int(r['gestureIndex'])==result['gesture']];assert len(rs)==result['n'];checks+=1
 for dim in ['width','height']:
  observed='observed_'+('w' if dim=='width' else 'h');pred='predicted_'+('w' if dim=='width' else 'h')+'_given_measured_lift';close(rms([float(r[pred])-float(r[observed]) for r in rs]),result['exact_'+dim+'_rmse']);checks+=1
for r in rows('sheet-body.csv'):
 native=json.loads(r['native_mean_rgb_8bit']);android=json.loads(r['android_mean_rgb_8bit']);close(rms([a-b for a,b in zip(native,android)]),float(r['mean_rgb_rmse_8bit']));checks+=1
source=json.loads((ROOT/'sources.json').read_text());assert len(source['sources'])==38;checks+=1
for r in source['sources']:assert len(r['sha256'])==64 and not r['path_in_capture_archive'].startswith('/');checks+=1
historical=json.loads((DATA/'historical-residual-summary.json').read_text())
source_by_path={r['path_in_capture_archive']:r for r in source['sources']}
for r in historical['sources'].values():
 assert source_by_path[r['path_in_capture_archive']]==r;checks+=1
for r in historical['exports'].values():
 p=ROOT/r['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'];assert len(list(csv.DictReader(p.open())))==r['rows'];checks+=2
body_by_scene={(r['background'],r['theme']):r for r in rows('sheet-body.csv')}
for r in rows('sheet-historical-profiles.csv'):
 close(float(r['mean_rgb_rmse_8bit']),float(body_by_scene[(r['background'],r['theme'])]['mean_rgb_rmse_8bit']));assert math.isfinite(float(r['horizontal_profile_rgb_rmse_8bit']));checks+=2
edges=rows('sheet-historical-edges.csv')
for r in historical['sheet_light_top_rim3_to_rim4']:
 match=next(e for e in edges if e['stage']==r['stage'] and e['theme']=='light' and e['edge']=='top');close(float(match['rgb_profile_rmse_0_to_6_8bit']),r['rgb_profile_rmse_0_to_6_8bit']);checks+=1
dark=[float(r['rgb_profile_rmse_0_to_6_8bit']) for r in edges if r['stage']=='rim4' and r['theme']=='dark']
assert len(dark)==4;close(min(dark),historical['sheet_rim4_dark_edge_range_8bit'][0]);close(max(dark),historical['sheet_rim4_dark_edge_range_8bit'][1]);checks+=3
secondary=rows('menu-secondary-grid.csv')
for r in historical['menu_secondary_by_corner']:
 rs=[s for s in secondary if s['corner']==r['corner']];assert len(rs)==r['rows']==44
 assert all(s['usable_all_thresholds']=='True' and 2<=float(s['depth'])<=24 for s in rs)
 errors=[abs(float(s['Window_coverage_reference'])-float(s['native_color_reference'])) for s in rs]
 close(sum(errors)/len(errors),r['reference_mae_dp']);close(max(errors),r['reference_max_abs_dp'])
 peak=rs[errors.index(max(errors))];close(float(peak['depth']),r['max_abs_depth_pt']);close(float(peak['native_color_reference']),r['native_reference_inset_pt_at_max']);close(float(peak['Window_coverage_reference']),r['android_reference_inset_dp_at_max']);checks+=7
# This atlas owns its immediate metadata, data and crops. Later studies have
# separate manifests/verifiers and may retain compressed historical receipts.
owned_files = [p for p in ROOT.iterdir() if p.is_file()]
owned_files += [p for base in [DATA, ROOT/'crops'] for p in base.rglob('*') if p.is_file()]
for p in owned_files:
 if p.suffix in ['.json','.csv']:
  assert '/Users/' not in p.read_text();checks+=1
text=(ROOT/'RESULTS.md').read_text()
for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',text):
 if not link.startswith(('http:','https:','#')):assert (ROOT/link.split('#')[0]).exists(),link;checks+=1
assert sum(p.stat().st_size for p in owned_files)+sum(p.stat().st_size for p in OUT.iterdir() if p.is_file())<12*1024*1024;checks+=1
print(json.dumps({'status':'PASS','checks':checks,'figures':len(manifest['outputs']),'dock_common_held':len(common),'slider_native_frames':len(fit),'note':'Package consistency and figure reproduction only; no new device/native acceptance.'},indent=2))
