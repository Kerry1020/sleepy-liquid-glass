#!/usr/bin/env python3
"""Reproducible offline fixture test. No devices, new captures or production edits."""
import hashlib, json
from pathlib import Path
import subprocess, sys, tempfile
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
SCRIPT=HERE/'analyze-witness-control-v1_1.py'
STAGES=['ingress01','ingress10','ingress50','ingress75','full100','far50']
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
write=lambda p,j:Path(p).write_text(json.dumps(j,indent=2)+'\n')
assets=json.loads((HERE/'asset-verification.json').read_text())
packets={p['role']:p for p in assets['packets']}
results=[]
with tempfile.TemporaryDirectory(prefix='synthetic-g-witness-',dir=HERE) as td:
 root=Path(td)
 evidence=root/'synthetic-observations.json';write(evidence,{'status':'passed','synthetic_fixture':True,'note':'Generated constant byte fixture only; not actual device/control evidence.'})
 audit={'path':str(evidence),'sha256':sha(evidence)}
 indexes={}
 for role in ['witness','control']:
  d=root/role;d.mkdir();p=packets[role];sp=json.loads(Path(p['spec']).read_text());manifest=json.loads(Path(p['manifest']).read_text())
  receipt=d/'synthetic-host.json'
  hashes={'inputs/manifest.json':p['manifest_sha256']}
  hashes.update({'inputs/'+e['file']:e['sha256'] for e in manifest['inputs']})
  write(receipt,{'synthetic_fixture':True,'test_passed':True,'exit_code':0,'input_sha256':hashes})
  index={'schema':1,'platform':'android','status':'passed','synthetic_fixture':True,'independent_acquisition_audit':audit,'source_result':audit,
         'host_receipt':{'path':str(receipt),'sha256':sha(receipt)},'captures':[]}
  for si,stage in enumerate(STAGES):
   geom={'observed':True,'carrier_bounds_world_xywh':[160,405,70,50],
         'presentation_matrix_samples':[[1,0,0,1,0,0]],'effective_opacity_samples':[1],
         'actual_source_origin_world_xy':[0,0],'actual_source_world_to_source_pixel_matrix':[[2,0],[0,2]],'actual_screenshot_pixels_per_world_unit':2,'actual_world_origin_in_screenshot_px':[0,0],'actual_screenshot_dimensions_px':[750,1334],'evidence':[audit]}
   c={'stage_id':stage,'input_id':sp['first_input_id'],'shape_id':sp['first_input_id'],
      'world_origin_window_px':[0,0],'pixels_per_world_unit':2,'actual_carrier_bounds_world_xywh':[160,405,70,50],
      'flat_geometry':{'world_origin_window_px':[0,0],'pixels_per_world_unit':2,'actual_carrier_bounds_world_xywh':[160,405,70,50]},
      'pairing_geometry':geom,'flat_pairing_geometry':json.loads(json.dumps(geom)),'android_evidence_json':str(evidence)}
   for flat in [False,True]:
    arr=np.full((1334,750,4),128,dtype=np.uint8);arr[...,3]=255
    arr[0,0,0]=si*4+int(flat)+(0 if role=='witness' else 40)
    if role=='witness' and not flat:
     for rr,vs in enumerate([[5,9,17,25],[-5,-9,-17,-25]]):
      for cc,v in enumerate(vs):arr[832+rr*2:834+rr*2,370+cc*2:372+cc*2,1]=128+v
    image=d/(stage+('-flat' if flat else '-shape')+'.png');Image.fromarray(arr).save(image)
    c['flat_png' if flat else 'png']=str(image);c['flat_sha256' if flat else 'sha256']=sha(image)
   index['captures'].append(c)
  ip=d/'index.json';write(ip,index);indexes[role]=(ip,index)
 def run_case(name,wi,ci):
  wp=root/(name+'-witness-index.json');cp=root/(name+'-control-index.json');write(wp,wi);write(cp,ci)
  out=root/(name+'-analysis')
  argv=[sys.executable,str(SCRIPT),'--witness-index',str(wp),'--control-index',str(cp),'--output',str(out)]
  p=subprocess.run(argv,capture_output=True,text=True)
  r=json.loads((out/'analysis.json').read_text())
  results.append({'case':name,'exit_code':p.returncode,'stdout':p.stdout.strip(),'stderr':p.stderr.strip(),
                  'evidence_class':r.get('evidence_class'),'analysis_json_sha256':sha(out/'analysis.json')})
  return r
 baseline=run_case('known-signed-G',indexes['witness'][1],indexes['control'][1])
 expected={4:(16,16,7712),8:(12,12,7720),16:(8,8,7728),24:(4,4,7736)}
 checks=[]
 for stage in baseline['stages']:
  checks.append({'check':'comparable and opaque RGBA loader at '+stage['stage'],'passed':stage['status']=='COMPARABLE'})
  r=stage['original_pixel_byte_metrics']['metrics']['complete_fixed_ROI']['fields']
  for t,counts in expected.items():
   actual=tuple(r['raw_witness_minus_control']['G']['thresholds'][str(t)][k]['samples'] for k in ['positive_gt','negative_lt_minus','neutral_abs_le'])
   checks.append({'check':f"{stage['stage']} original G support T={t}",'passed':actual==counts,'actual':actual,'expected':counts})
   for ch in ['R','B']:
    s=r['raw_witness_minus_control'][ch]['thresholds'][str(t)]
    checks.append({'check':f"{stage['stage']} unchanged {ch} T={t}",'passed':s['positive_gt']['samples']==s['negative_lt_minus']['samples']==0 and s['neutral_abs_le']['samples']==7744})
  checks.append({'check':stage['stage']+' exact original-byte zero flat residual','passed':stage['flat_drift_gate']['original_pixel_encoded_RGB_absolute_p99']==[0,0,0]})
  npz=np.load(root/'known-signed-G-analysis'/(stage['stage']+'-original-byte-differences.npz'))
  checks.append({'check':stage['stage']+' exact integer raw/corrected equality','passed':np.array_equal(npz['raw_witness_minus_control'],npz['corrected_difference_of_differences']) and npz['raw_witness_minus_control'].dtype==np.int16})
 bad=json.loads(json.dumps(indexes['control'][1]))
 for c in bad['captures']:
  for key in ['pairing_geometry','flat_pairing_geometry']:c[key]['carrier_bounds_world_xywh'][0]+=.11
  c['actual_carrier_bounds_world_xywh'][0]+=.11;c['flat_geometry']['actual_carrier_bounds_world_xywh'][0]+=.11
 rejected=run_case('reject-bounds',indexes['witness'][1],bad)
 checks.append({'check':'all six 0.11pt mismatches reject without subtraction','passed':all(s['status']=='NO_SUBTRACTION_REJECTED' for s in rejected['stages'])})
 uw=json.loads(json.dumps(indexes['witness'][1]));uc=json.loads(json.dumps(indexes['control'][1]))
 for i in [uw,uc]:
  for c in i['captures']:
   c['pairing_geometry']['effective_opacity_samples']=None;c['flat_pairing_geometry']['effective_opacity_samples']=None
 unknown=run_case('unknown-opacity',uw,uc)
 checks.append({'check':'missing opacity preserves exact raw G diagnostics and mapping unknown for all six poses','passed':all(s['status']=='MAPPING_UNKNOWN_PIXEL_DIAGNOSTICS_ONLY' and s['original_pixel_byte_metrics']['metrics']['complete_fixed_ROI']['fields']['raw_witness_minus_control']['G']['thresholds']['24']['positive_gt']['samples']==4 for s in unknown['stages'])})
 checks.append({'check':'synthetic label propagated in all reports','passed':all(v['evidence_class']=='SYNTHETIC_ONLY_NO_CAPTURE_EVIDENCE' for v in results)})
 report={'schema':1,'scope':'Actual CLI execution on generated synthetic opaque RGBA constant-byte fixtures. No actual new capture read; fixture/output working files removed after extracting checks.',
         'script':str(SCRIPT),'script_sha256':sha(SCRIPT),'frozen_v1_criteria_sha256':sha(HERE/'analyze-witness-control.py'),'analysis_plan_sha256':sha(HERE/'analysis-plan.json'),
         'cases':results,'checks':checks,'passed':all(c['passed'] for c in checks) and all(r['exit_code']==0 for r in results)}
 write(HERE/'synthetic-cli-validation.json',report)
 print(json.dumps({'passed':report['passed'],'checks':len(checks),'cases':results,'report':str(HERE/'synthetic-cli-validation.json')},indent=2))
 sys.exit(0 if report['passed'] else 1)
