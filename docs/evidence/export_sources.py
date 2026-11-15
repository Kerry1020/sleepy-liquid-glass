#!/usr/bin/env python3
"""Export small, public research inputs from the original local capture archive.
Run only when replacing evidence: python3 export_sources.py /path/to/session
Ordinary figure reproduction uses render_figures.py and needs no private archive.
"""
from pathlib import Path
import argparse,csv,hashlib,json,shutil
from PIL import Image
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('archive',type=Path);args=ap.parse_args()
sources=[]
def source(rel,purpose):
 p=args.archive/rel
 b=p.read_bytes();sources.append({'path_in_capture_archive':rel,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'purpose':purpose});return p
def dump(name,obj):
 (ROOT/'data'/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def export_csv(rel,name,fields,purpose):
 p=source(rel,purpose); rows=list(csv.DictReader(p.open()))
 with (ROOT/'data'/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:r[k] for k in fields} for r in rows)
 return rows
BASE='artifacts/glass-optics-20261112/'
DOCK=BASE+'android-dock-parent-response-72/independent-dock-parent-review/device-parent-comparison/'
fields=['gesture_index','native_raw_line','native_elapsed_mid_s','android_elapsed_mid_s','android_wholly_held','native_parent_tx_pt','android_parent_tx_dp','total_center_difference_dp','phase_gap_ms']
for n in ['69','72']:
 export_csv(DOCK+f'android{n}-nearest-draw-comparison.csv',f'dock-android{n}.csv',fields,'Actual nearest window-draw parent carrier translation; full eligible rows, including explicit non-held match.')
p=source(DOCK+'common-held-summary.json','Frozen same-row held summary; not a native optical score.');dump('dock-summary.json',json.load(p.open()))
MENU=BASE+'menu-alert-visible-corners-20261113/menu32-full-gpu-validation/'
export_csv(MENU+'candidate-baseline-native-intervals.csv','menu-corners.csv',['corner','scene','depth','native_low','native_reference','native_high','candidate_reference','baseline_reference','usable_all_thresholds','flat_matched_input_all_thresholds'],'Native color-threshold inset family against actual GPU Menu24 and Menu32 Window coverage.')
p=source(MENU+'native-baseline-candidate-corners.png','Existing synthetic-fixture corner montage, 6 pixels/unit density conversion only; no status bars or personal content.');shutil.copyfile(p,ROOT/'crops/menu-corners.png')
FIT=BASE+'android-native-replay-66/independent-slider-gap-review/'
export_csv(FIT+'native-empirical-predictions.csv','slider-native-fit.csv',['gestureIndex','split','frame','t','observed_sx','observed_sy','predicted_sx','predicted_sy','observed_w','observed_h','predicted_w_given_measured_lift','predicted_h_given_measured_lift'],'Frozen native-only empirical predictions; measured lift is an input, not predicted rise/fall.')
p=source(FIT+'native-fit-dataset.json','Only gesture split/direction/speed/actual UP extracted; private full raw capture not required to redraw.');d=json.load(p.open());dump('slider-protocol.json',{'scope':d['scope'],'forcing':d['forcing'],'geometry':d['geometry'],'train':d['train'],'held_out':d['held_out'],'gestures':[{k:g[k] for k in ['gestureIndex','split','direction','speed','up']} for g in d['gestures']]})
p=source(FIT+'native-empirical-fit.json','Parameter and numerical summary of frozen native-only fit.');d=json.load(p.open());dump('slider-fit-summary.json',{k:d[k] for k in ['status','method','observables','equations','parameters','identifiability','production_limits','per_gesture']})
SHEET='outputs/glass-native-parity-20261112/native-static-optics/sheet-comparison-rim-4/eight-rest/'
export_csv(SHEET+'body-summary.csv','sheet-body.csv',['background','theme','body_rect_px','native_mean_rgb_8bit','android_mean_rgb_8bit','mean_rgb_rmse_8bit'],'Foreground-free body ROI means; not an entire-sheet image score, and not edge/contour acceptance.')
for bg in ['fine_grid','color_stripes','tonal_blocks','synthetic_landscape']:
 for theme in ['light','dark']:
  for platform in ['ios26.5','android36']:
   rel=SHEET+f'{bg}-{theme}-{platform}-display-preview.png';p=source(rel,'Synthetic test fixture; strip system status bar and upper scene, retain full sheet pane and differences in contents/height.')
   im=Image.open(p).convert('RGB');top=300 if platform=='ios26.5' else 346
   crop=im.crop((0,top,im.width,im.height));out=f'sheet-{bg}-{theme}-{platform}.png';crop.save(ROOT/'crops'/out,optimize=True)
   sources[-1]['public_transform']={'crop_xyxy_px':[0,top,im.width,im.height],'output':'crops/'+out,'color':'RGB','resize':None,'note':'Crops use the existing preview pixel grids; montage is visual context, not geometry registration.'}
OPTIC=BASE+'android-dock-parent-response-72/independent-slider-optical-review/'
p=source(OPTIC+'held-comparison-contact.png','Historical settled-HELD synthetic fixture crops; rail palette differs and full RGB difference x3 includes it. No optical score for whole crop.');shutil.copyfile(p,ROOT/'crops/slider-held-optical-gap.png')
p=source(OPTIC+'comparison.json','Full methodology retained as sanitized text-only JSON; no user or device identifiers exported.');d=json.load(p.open());dump('slider-optical-method.json',d['methodology']);dump('slider-optical-residuals.json',[{'scene':r['scene'],'phase':r['phase'],'lower_inner_world_rect':r['windows']['lower_inner_haze_transmission_proxy']['world_window'],'lower_inner_direct_RGB_MAE':r['windows']['lower_inner_haze_transmission_proxy']['android_native_direct_difference']['mae_rgb'],'plain_source_crop_RGB_MAE':r['baseline_world_crop_difference']['mae_rgb']} for r in d['pairs'] if r['phase']=='held'])
TOGGLE='outputs/glass-native-parity-20261112/native-analysis/optical-review/'
for n in ['switch-white-to-glass.png','switch-release-theme-fill.png']:
 p=source(TOGGLE+n,'Native-only UIKit Toggle from original decoded video PTS, crop/enlargement only. Approximate video-trace registration one frame; not Android acceptance.');shutil.copyfile(p,ROOT/'crops'/n)
export_csv(TOGGLE+'switch-opacity-proxy.csv','toggle-white-mixture.csv',['videoPTSSec','sinceDownApproxMs','presentationWPt','presentationHPt','centerR','centerG','centerB','effectiveWhiteMixProxy'],'Stationary center patch white-mixture proxy, not measured layer alpha; native-only and approximate registration.')
source(TOGGLE+'optical-evidence.md','Original methodological interpretation, including video/trace alignment and moving-release limitations.')
# Additional archived diagnostics: no new capture, refit, or figure replacement.
STATIC='outputs/glass-native-parity-20261112/native-static-optics/'
MENUBASE=BASE+'menu-alert-visible-corners-20261113/'
residual_specs={
 'sheet_profiles':(STATIC+'sheet-comparison-rim-4/eight-rest/delta-from-geometry-2/delta.csv','Archived eight-rest horizontal body-profile errors; export only the after/rim4 mean and profile statistics. Profiles are not recomputed from raw pixels by the public figure renderer.'),
 'sheet_rim3_edges':(STATIC+'sheet-comparison-rim-3/edges/edge-summary.csv','Archived neutral/fine-grid edge RGB profile summary, rim3 baseline; inward 0..6 logical units, 8-bit channel values.'),
 'sheet_rim4_edges':(STATIC+'sheet-comparison-rim-4/edges/edge-summary.csv','Archived neutral/fine-grid edge RGB profile summary, rim4; retain light top degradation and dark residuals.'),
 'menu_secondary_grid':(MENUBASE+'menu32-secondary-grid-threshold-intervals.csv','Secondary fine-grid dark menu threshold diagnostics, not primary shape validation. Export fixed 2..24 depth rows with all threshold crossings present; retain grid/rim/shadow contamination.'),
 'sheet_profile_method':(STATIC+'sheet-comparison-rim-4/eight-rest/README.md','Archived methodology: matched body input policy and distinction between mean RGB, complete horizontal profiles, and mismatched edge inputs.'),
 'sheet_edge_method':(STATIC+'sheet-comparison-rim-4/README.md','Archived edge method: 16 logical units tangential average, interpolated original pixel centers, inward 0..6 RGB-profile RMSE; rim3 to rim4 failure retained.'),
 'menu_secondary_method':(MENUBASE+'GPU32-VALIDATION.md','Archived primary/secondary distinction, frozen fine-grid dark color thresholds 110/130/150, and native grid/rim/shadow dip explaining the retained outlier.'),
}
residual_sources={};residual_paths={}
for key,(rel,purpose) in residual_specs.items():
 residual_paths[key]=source(rel,purpose);residual_sources[key]=sources[-1]
def archive_rows(key):return list(csv.DictReader(residual_paths[key].open()))
def narrow_csv(name,fields,values):
 with (ROOT/'data'/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(values)
 return {'path':'data/'+name,'sha256':hashlib.sha256((ROOT/'data'/name).read_bytes()).hexdigest(),'rows':len(values)}
profile_rows=[{'background':r['background'],'theme':r['theme'],'carrier':r['carrier'],'mean_rgb_rmse_8bit':r['after_mean_rgb_error_8bit'],'horizontal_profile_rgb_rmse_8bit':r['after_horizontal_profile_error_8bit']} for r in archive_rows('sheet_profiles')]
edge_rows=[]
for stage in ['3','4']:
 for r in archive_rows('sheet_rim'+stage+'_edges'):
  edge_rows.append({'stage':'rim'+stage,'background':'fine_grid','theme':r['theme'],'edge':r['edge'],'rgb_profile_rmse_0_to_6_8bit':r['rgb_profile_rmse_0_to_6_8bit']})
secondary_fields=['corner','depth','native_color_low','native_color_reference','native_color_high','Window_coverage_low','Window_coverage_reference','Window_coverage_high','usable_all_thresholds']
secondary_rows=[{k:r[k] for k in secondary_fields} for r in archive_rows('menu_secondary_grid') if 2<=float(r['depth'])<=24 and r['usable_all_thresholds']=='True']
residual_exports={
 'sheet_profiles':narrow_csv('sheet-historical-profiles.csv',list(profile_rows[0]),profile_rows),
 'sheet_edges':narrow_csv('sheet-historical-edges.csv',list(edge_rows[0]),edge_rows),
 'menu_secondary':narrow_csv('menu-secondary-grid.csv',secondary_fields,secondary_rows),
}
secondary_summary=[]
for corner in ['TL','TR','BL','BR']:
 rs=[r for r in secondary_rows if r['corner']==corner];errors=[abs(float(r['Window_coverage_reference'])-float(r['native_color_reference'])) for r in rs];peak=rs[errors.index(max(errors))]
 secondary_summary.append({'corner':corner,'rows':len(rs),'reference_mae_dp':sum(errors)/len(errors),'reference_max_abs_dp':max(errors),'max_abs_depth_pt':float(peak['depth']),'native_reference_inset_pt_at_max':float(peak['native_color_reference']),'android_reference_inset_dp_at_max':float(peak['Window_coverage_reference'])})
light_top=[{'stage':r['stage'],'rgb_profile_rmse_0_to_6_8bit':float(r['rgb_profile_rmse_0_to_6_8bit'])} for r in edge_rows if r['theme']=='light' and r['edge']=='top']
dark_edges=[float(r['rgb_profile_rmse_0_to_6_8bit']) for r in edge_rows if r['stage']=='rim4' and r['theme']=='dark']
dump('historical-residual-summary.json',{
 'schema':1,
 'scope':'Archived historical application summaries and secondary diagnostics only; no new device run, public-backend parity, or new bevel result.',
 'reproduction_boundary':'Public verification recalculates secondary Menu statistics from the exported boundary rows and checks archived Sheet summary consistency. Sheet full profiles and edge pixels are not remeasured or refitted by render_figures.py.',
 'sources':residual_sources,'exports':residual_exports,
 'sheet_profile_method':{'stage':'rim4 eight-rest','metric':'RMSE across same-coordinate horizontal RGB profiles in the declared foreground-free body strips','units':'8-bit RGB code values (0..255)','input_policy':'Periodic phase matched; tonal body strip shifted by two whole 224-unit periods; synthetic landscape full-screen UV matched. These are body regions, not whole sheets.','roi_reference':'body_rect_px in sheet-body.csv; original method and source hash recorded above.'},
 'sheet_edge_method':{'background':'fine_grid / neutral fixture','metric':'Complete inward 0..6 logical-unit RGB profile RMSE','tangential_average_length_logical_units':16,'sampling':'Interpolate original pixel-center samples along the inward normal; preserve each actual pane position and size.','units':'8-bit RGB code values (0..255)','limitations':'Includes rasterization/refraction, native dimmed scene and possible native backing controls; not physical alpha or automatic optical parity.'},
 'sheet_light_top_rim3_to_rim4':light_top,
 'sheet_rim4_dark_edge_range_8bit':[min(dark_edges),max(dark_edges)],
 'menu_secondary_method':{'scene':'fine_grid-dark-menu','fixed_depth_window_pt':[2,24],'native_color_thresholds_maxRGB_less_than':[110,130,150],'reference_threshold_maxRGB_less_than':130,'android_window_coverage_thresholds':[64,128,192],'reference_coverage_threshold':128,'qualification':'All native and Window threshold crossings present; not the primary flat/matched-input selection.','limitations':'Color crossings are not alpha. Grid/rim/shadow dips contaminate this secondary scene; the outlier is retained and was not used to tune Menu32.'},
 'menu_secondary_by_corner':secondary_summary,
})
manifest={'schema':1,'publication_date':'2026-11-14','reference':'iOS 26.5 (23F77), synthetic native reference fixture','scope':'Historical Sleepy application calibration and diagnostics. The independent public runtime uses official Kyant AndroidLiquidGlass 2.0.0; these app captures are not equivalence validation of that public backend.','privacy':'Only control/synthetic fixture crops and numerical observations exported. No user schedule, photographs, account data, status bars, or raw device video.','reproduction':'python3 docs/evidence/render_figures.py reads only committed data/crops. export_sources.py requires the original capture archive to replace inputs.','sources':sources}
(ROOT/'sources.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(f'Exported {len(sources)} source records')
