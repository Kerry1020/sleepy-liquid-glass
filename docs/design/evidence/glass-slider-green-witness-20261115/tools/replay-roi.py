#!/usr/bin/env python3
"""Replay frozen G ROI statistics from portable exact-pixel crops.

Only filesystem lookup is adapted to the local package. The frozen v1.1
geometry checks, domain definitions, thresholds, bilinear sampling, direct-byte
subtraction and summary functions are imported unchanged. This cannot establish
the original full-screen PNG hashes from cropped pixels; see README.md.
"""
from pathlib import Path
import argparse
import gzip
import hashlib
import importlib.util
import json
import shutil
import tempfile
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SHA=lambda b:hashlib.sha256(b).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
manifest=read(ROOT/'manifest.json')
provenance={r['original_path']:r for r in manifest['provenance']}

def original_bytes(path):
    r=provenance[str(Path(path))]
    raw=(ROOT/r['file']).read_bytes()
    assert SHA(raw)==r['stored_sha256'],r['file']
    raw=gzip.decompress(raw) if r['compression']=='gzip' else raw
    assert SHA(raw)==r['original_sha256'],r['file']
    return raw

def frozen_key_subset(replayed,official,path=''):
    """Compare every numeric/semantic metric, omitting changed crop-file labels."""
    if isinstance(official,dict):
        assert isinstance(replayed,dict),path
        for k,v in official.items():
            if k in ['evidence','crop_original_pixel_xyxy']:continue
            assert k in replayed,path+'/'+k
            frozen_key_subset(replayed[k],v,path+'/'+k)
    elif isinstance(official,list):
        assert len(replayed)==len(official),path
        for i,(a,b) in enumerate(zip(replayed,official)):frozen_key_subset(a,b,path+'/'+str(i))
    elif isinstance(official,(float,int)) and not isinstance(official,bool):
        assert np.isclose(replayed,official,rtol=0,atol=2e-9), (path,replayed,official)
    else:
        assert replayed==official,(path,replayed,official)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',required=True,help='New output directory; all generated analysis scratch is removed after verified summary')
    args=p.parse_args();out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=False)
    checks=read(ROOT/'checksums.json')
    for file,digest in checks['files'].items():
        assert SHA((ROOT/file).read_bytes())==digest,file
    for r in manifest['provenance']:
        original_bytes(r['original_path'])
    spec=importlib.util.spec_from_file_location('frozen_v1_1',ROOT/'frozen/analyze-witness-control-v1_1.py')
    an=importlib.util.module_from_spec(spec);spec.loader.exec_module(an)
    assert SHA((ROOT/'frozen/analyze-witness-control-v1_1.py').read_bytes())=='ef475784d5aed32b0dc522ae80c5ff760ad6779a5ef676c5c0de2737307ac2d1'
    # Portable file lookup only. These functions have the same semantics on the
    # exact archived original bytes; no geometry/pixel/threshold rule is changed.
    an.read=lambda path:json.loads(original_bytes(path))
    an.SHA=lambda path:SHA(original_bytes(path))
    roles={}
    for role,r in manifest['source_roles'].items():
        roles[role]={'spec_sha256':r['spec']['original_sha256'],'manifest_sha256':r['manifest']['original_sha256'],
                     'main_id':r['main_id'],'manifest_value':json.loads(original_bytes(r['manifest']['original_path']))}
        for entry in roles[role]['manifest_value']['inputs']:
            local=next(v for v in r['inputs'] if v['id']==entry['id'])
            assert SHA(original_bytes(local['original_path']))==entry['sha256']
    wrole,crole=manifest['source_roles']['witness'],manifest['source_roles']['control']
    witness=np.asarray(Image.open(ROOT/next(v['file'] for v in wrole['inputs'] if v['id']==wrole['main_id'])))[...,:3]
    control=np.asarray(Image.open(ROOT/next(v['file'] for v in crole['inputs'] if v['id']==crole['main_id'])))[...,:3]
    assert np.array_equal(witness[..., [0,2]],control[..., [0,2]])
    assert np.all(control[...,1]==128) and np.all(witness[...,1]>=128)
    target=np.asarray(Image.open(ROOT/'masks/primary-ingress75-excessB-mask.png'))>0
    assert target.sum()==283
    report={'status':'pending','scope':'Portable cropped ROI replay only; not reacceptance of uncopied full-screen acquisition',
            'frozen_analyzer_sha256':checks['files']['frozen/analyze-witness-control-v1_1.py'],
            'manifest_sha256':SHA((ROOT/'manifest.json').read_bytes()),'versions':{},
            'limitations':['Original full-screen screenshot hashes are preserved provenance, not independently reconstructable from crops.',
                'Accepted acquisition indexes and geometry receipts are archived as exact bytes, but no device recapture occurs.',
                'Android effective opacity remains unknown; all current rounds are calibration.']}
    replay_arrays={}
    with tempfile.TemporaryDirectory(prefix='roi-replay-',dir=out) as scratch:
        for version,rounds in manifest['rounds'].items():
            official=json.loads(original_bytes(manifest['analysis_files'][version]['original_path']))
            loaded={}
            for role,rr in rounds.items():
                index_path=Path(rr['index']['original_path']);idx=json.loads(original_bytes(index_path))
                assert idx['status']==rr['accepted_status'] and len(idx['captures'])==6
                if idx['platform']=='android':
                    assert SHA(original_bytes(idx['source_result']['path']))==idx['source_result']['sha256']
                    receipt=json.loads(original_bytes(idx['host_receipt']['path']))
                    assert SHA(original_bytes(idx['host_receipt']['path']))==idx['host_receipt']['sha256']
                    assert receipt['test_passed'] is True and receipt['exit_code']==0
                    assert receipt['input_sha256']['inputs/manifest.json']==roles[role]['manifest_sha256']
                loaded[role]={}
                for c in idx['captures']:
                    row={'images':{},'mappings':{},'geometries':{},'errors':[]}
                    for flat,kind in [(False,'shape'),(True,'flat')]:
                        cr=next(v for v in manifest['captures'] if v['version']==version and v['role']==role and v['stage']==c['stage_id'] and v['kind']==kind)
                        original_png=c['flat_png' if flat else 'png'];original_sha=c['flat_sha256' if flat else 'sha256']
                        assert cr['original_full_png_path']==original_png and cr['original_full_png_sha256']==original_sha
                        assert SHA((ROOT/cr['file']).read_bytes())==cr['sha256']
                        with Image.open(ROOT/cr['file']) as im:
                            assert im.mode==cr['original_mode']
                            pixels=np.asarray(im,dtype=np.uint8)
                            assert pixels.ndim==3 and pixels.shape[2] in [3,4]
                            assert pixels.shape[2]==3 or np.all(pixels[...,3]==255)
                        box=cr['original_pixel_crop_xyxy'];assert list(pixels.shape[1::-1])==[box[2]-box[0],box[3]-box[1]]
                        mg=c['flat_geometry'] if flat else c
                        assert cr['original_world_origin_in_screenshot_px']==mg['world_origin_window_px']
                        assert cr['original_pixels_per_world_unit']==mg['pixels_per_world_unit']
                        row['images'][kind]=pixels[...,:3]
                        row['mappings'][kind]={'origin':np.asarray(mg['world_origin_window_px'],float)-box[:2],
                                              'scale':float(mg['pixels_per_world_unit'])}
                        g=an.native_observation(idx,c,flat,roles[role],index_path.parent) if idx['platform']=='ios' else an.android_geometry(c,flat,index_path.parent)
                        assert np.max(np.abs(g['carrier_bounds']-mg['actual_carrier_bounds_world_xywh']))<=.1
                        assert abs(g['actual_output_mapping']['scale']-mg['pixels_per_world_unit'])<=1e-7
                        assert np.max(np.abs(g['actual_output_mapping']['origin']-mg['world_origin_window_px']))<=1e-5
                        row['geometries'][kind]=g
                    loaded[role][c['stage_id']]=row
            rd=Path(scratch)/version;rd.mkdir()
            report['versions'][version]={}
            for stage in an.STAGES:
                got=an.analyze_stage(stage,loaded['witness'][stage],loaded['control'][stage],target,rd)
                old=next(v for v in official['stages'] if v['stage']==stage)
                # analyze_stage returns geometry evidence with original paths;
                # comparison otherwise includes every official threshold/domain.
                frozen_key_subset(got,old,version+'/'+stage)
                for suffix in ['world-grid','original-byte-differences']:
                    d=np.load(rd/(stage+'-'+suffix+'.npz'))
                    replay_arrays[(version,stage,suffix)]={k:d[k] for k in ['x','y','raw_witness_minus_control']}
                report['versions'][version][stage]={'status':got['status'],'all_official_metrics_match':True,
                                                  'flat_drift_gate':got['flat_drift_gate']}
    # Independently recompute actual added/removed support counts in the packet.
    support=read(ROOT/'summaries/r4-support-set-differences.json');fm=np.load(ROOT/'masks/r2-frost-subgroups-frozen-v1/masks.npz')
    for stage,domains in support['stages'].items():
        data={v:replay_arrays[(v,stage,'world-grid')] for v in ['native','r2','r4']}
        for name,d in domains.items():
            mask=np.ones(target.shape,bool) if name=='complete_fixed_ROI' else target if name=='frozen_ingress75_target' else fm[name]
            for threshold,signs in d['thresholds'].items():
                t=int(threshold)
                for sign,stats in signs.items():
                    ss={v:mask & ((a['raw_witness_minus_control'][...,1]>t) if sign=='positive_gt' else (a['raw_witness_minus_control'][...,1] < -t)) for v,a in data.items()}
                    n,a,b=[ss[v] for v in ['native','r2','r4']]
                    masks={'native_support':n,'r2_support':a,'r4_support':b,'support_added_r4_vs_r2':b & ~a,'support_removed_r4_vs_r2':a & ~b,
                           'r2_false_positive':a & ~n,'r4_false_positive':b & ~n,'false_positive_actually_added':b & ~n & ~a,'false_positive_actually_removed':a & ~n & ~b,
                           'r2_native_positive_missed':n & ~a,'r4_native_positive_missed':n & ~b,'native_support_miss_actually_added':n & a & ~b,'native_support_miss_actually_removed':n & ~a & b}
                    assert all(int(m.sum())==stats[k]['samples'] for k,m in masks.items()),(stage,name,t,sign)
    # The compact all-candidate audit retains r3 as well as r4, and records
    # actual additions/removals separately so a good net cannot hide new errors.
    audit=read(ROOT/'summaries/r3-r4-actual-support-sets.json')
    for candidate,stages in audit.items():
        for stage,domains in stages.items():
            data={v:replay_arrays[(v,stage,'world-grid')] for v in ['native','r2',candidate]}
            for name,thresholds in domains.items():
                mask=np.ones(target.shape,bool) if name=='complete_fixed_ROI' else target if name=='frozen_ingress75_target' else fm[name]
                for threshold,signs in thresholds.items():
                    t=int(threshold)
                    for sign,stats in signs.items():
                        ss={v:mask & ((a['raw_witness_minus_control'][...,1]>t) if sign=='positive_gt' else (a['raw_witness_minus_control'][...,1] < -t)) for v,a in data.items()}
                        n,a,b=ss['native'],ss['r2'],ss[candidate]
                        sets={'native_support':n,'r2_support':a,'candidate_support':b,'support_actually_added':b & ~a,'support_actually_removed':a & ~b,
                              'r2_false_positive':a & ~n,'candidate_false_positive':b & ~n,'false_positive_actually_added':b & ~n & ~a,'false_positive_actually_removed':a & ~n & ~b,
                              'r2_native_support_missed':n & ~a,'candidate_native_support_missed':n & ~b,'native_support_miss_actually_added':n & a & ~b,'native_support_miss_actually_removed':n & ~a & b}
                        assert all(int(m.sum())==stats[k]['samples'] for k,m in sets.items()),(candidate,stage,name,t,sign)
    # Rebuild r2-only reverse/neutral subgroups using archived original source and
    # actual r2 carrier/source geometry; confirm selection was not tuned to r4.
    cap=next(v for v in manifest['captures'] if v['version']=='r2' and v['role']=='witness' and v['stage']=='ingress75' and v['kind']=='shape')
    idx=json.loads(original_bytes(manifest['rounds']['r2']['witness']['index']['original_path']))
    c=next(c for c in idx['captures'] if c['stage_id']=='ingress75')
    left,top,width,height=c['actual_carrier_bounds_world_xywh'];x,y=fm['x'],fm['y'];r=height/2;cx,cy=left+width/2,top+r
    dx=x-np.clip(x,cx-(width-height)/2,cx+(width-height)/2);dy=y-cy;length=np.hypot(dx,dy);inset=r-length
    D=7.8*np.maximum(1-inset/7.5,0)**2;qx=x-D*dx/np.maximum(length,1e-12);qy=y-D*dy/np.maximum(length,1e-12)
    scale=np.asarray(c['source_layout_geometry']['layout_size_px'])/c['source_layout_geometry']['density']/[375,667]
    sx,sy=qx/scale[0]*2-.5,qy/scale[1]*2-.5;ix,iy=np.floor(sx).astype(int),np.floor(sy).astype(int);fx,fy=sx-ix,sy-iy
    source=witness[...,1].astype(float)-control[...,1].astype(float)
    sg=source[iy,ix]*(1-fx)*(1-fy)+source[iy,ix+1]*fx*(1-fy)+source[iy+1,ix]*(1-fx)*fy+source[iy+1,ix+1]*fx*fy
    assert np.array_equal(target & (sg>24),fm['reverse68_sourceG_gt24'])
    assert np.array_equal(target & (sg<=4),fm['neutral138_sourceG_le4'])
    subgroup_summary={}
    for version in manifest['rounds']:
        g=replay_arrays[(version,'ingress75','world-grid')]['raw_witness_minus_control'][...,1]
        subgroup_summary[version]={}
        for name in ['target','reverse68_sourceG_gt24','neutral138_sourceG_le4','frost_band222_inset1_5_to7']:
            m=fm[name];v=g[m]
            subgroup_summary[version][name]={'samples':int(m.sum()),'area_pt2':float(m.sum()/16),'quantiles_p0_10_50_90_100':np.percentile(v,[0,10,50,90,100]).tolist(),
                'positive_areas_pt2':[float((v>t).sum()/16) for t in [4,8,16,24]],'negative_areas_pt2':[float((v < -t).sum()/16) for t in [4,8,16,24]]}
    (out/'replayed-subgroups.json').write_text(json.dumps(subgroup_summary,indent=2)+'\n')
    report['subgroup_masks_rebuilt_from_r2_only']=True
    report['r4_actual_added_removed_support_counts_match']=True
    report['r3_r4_actual_added_removed_support_counts_match']=True
    report['status']='passed_portable_ROI_metric_replay'
    (out/'replay-summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'versions':len(report['versions']),'stages':24,'captures':len(manifest['captures']),'output':str(out)}))

if __name__=='__main__':main()
