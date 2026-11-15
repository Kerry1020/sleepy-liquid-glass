#!/usr/bin/env python3
"""Replay the frozen midpoint ROI calculations from exact portable pixel crops.

Only file lookup changes. Native geometry gates, inset calculation and summary
functions are imported from the archived original analyzers without edits.
Full-screen PNG and endpoint-trace verification cannot be rerun from this packet.
"""
from pathlib import Path
import argparse, gzip, hashlib, importlib.util, json
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
GREEN=ROOT.parent/'glass-slider-green-witness-20261115'
sha=lambda b:hashlib.sha256(b).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
manifest=read(ROOT/'manifest.json')
originals={}
for base,records in [(GREEN,read(GREEN/'manifest.json')['provenance']),(ROOT,manifest['provenance'])]:
    for r in records: originals[r['original_path']]=(base,r)

def original_bytes(path):
    base,r=originals[str(path)];b=(base/r['file']).read_bytes()
    assert sha(b)==r['stored_sha256'],r['file']
    b=gzip.decompress(b) if r['compression']=='gzip' else b
    assert sha(b)==r['original_sha256'],r['file']
    return b

def same(a,b,path=''):
    if isinstance(b,dict):
        assert isinstance(a,dict),path
        for k,v in b.items():
            if k=='evidence': continue
            assert k in a,path+'/'+k
            same(a[k],v,path+'/'+k)
    elif isinstance(b,list):
        assert len(a)==len(b),path
        for k,(x,y) in enumerate(zip(a,b)):same(x,y,path+'/'+str(k))
    elif isinstance(b,(float,int)) and not isinstance(b,bool):
        assert np.isclose(a,b,rtol=0,atol=1e-12),(path,a,b)
    else:assert a==b,(path,a,b)

def load():
    for file,digest in read(ROOT/'checksums.json')['files'].items():
        assert sha((ROOT/file).read_bytes())==digest,file
    for r in manifest['shared_dependencies']:
        assert sha((ROOT/r['file']).read_bytes())==r['sha256'],r['file']
    for path in [r['original_path'] for r in manifest['provenance']]:original_bytes(path)
    modspec=importlib.util.spec_from_file_location('frozen_midpoint',ROOT/'frozen/analyze-midpoint-v1_1.py')
    mid=importlib.util.module_from_spec(modspec);modspec.loader.exec_module(mid)
    plan=read(ROOT/'original/analysis-plan-v1_1.json')
    assert sha((ROOT/'frozen/analyze-midpoint-v1_1.py').read_bytes())==plan['analysis_sha256']
    assert sha((ROOT/'frozen/analyze-witness-control-v1_1.py').read_bytes())==plan['frozen_parser_sha256']
    an=mid.f;an.read=lambda path:json.loads(original_bytes(path));an.SHA=lambda path:sha(original_bytes(path))
    loaded={}
    for role,r in manifest['rounds'].items():
        idx=json.loads(original_bytes(r['index']['original_path']))
        spec=json.loads(original_bytes(r['spec']['original_path']))
        source_manifest=json.loads(original_bytes(r['manifest']['original_path']))
        assert idx['platform']=='ios' and idx['status']=='passed' and len(idx['captures'])==6
        rr={'main_id':r['main_id'],'spec_sha256':r['spec']['original_sha256'],
            'manifest_sha256':r['manifest']['original_sha256'],'manifest_value':source_manifest}
        loaded[role]={}
        for c in idx['captures']:
            row={'images':{},'geometries':{},'errors':[]}
            for flat,kind in [(False,'shape'),(True,'flat')]:
                cr=next(x for x in manifest['captures'] if x['round']==role and x['stage']==c['stage_id'] and x['kind']==kind)
                assert cr['original_full_png_sha256']==c['flat_sha256' if flat else 'sha256']
                assert cr['original_full_png_path']==c['flat_png' if flat else 'png']
                b=(ROOT/cr['file']).read_bytes();assert sha(b)==cr['sha256']
                im=Image.open(ROOT/cr['file']);assert im.mode==cr['original_mode']
                pixels=np.asarray(im);assert pixels.shape[:2]==(94,94)
                assert pixels.shape[-1]==3 or np.all(pixels[...,3]==255)
                row['images'][kind]=pixels[3:91,3:91,:3].astype(float)
                geo=an.native_observation(idx,c,flat,rr,Path(r['index']['original_path']).parent)
                assert geo['actual_output_mapping']['scale']==2 and np.array_equal(geo['actual_output_mapping']['origin'],[0,0])
                row['geometries'][kind]=geo
            loaded[role][c['stage_id']]=row
    return mid,plan,loaded

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,help='New JSON file; must not exist');args=p.parse_args()
    out=Path(args.output).resolve();assert not out.exists(),out
    mid,plan,loaded=load();an=mid.f
    official=json.loads(gzip.decompress((ROOT/'original/analysis.json.gz').read_bytes()))
    report={'status':'passed','scope':'Original ROI numerical replay; not full-screen hash or endpoint recapture verification',
        'stages':{},'above_rail_exception_pixels':[],'seven_point_consumed':False,
        'limitations':['Archived strict receipts are original evidence, not a new trace-verifier run.',
            'Original full PNG hashes cannot be reconstructed from crops.',
            'Encoded-sRGB midpoint does not establish physical linearity or identify an internal processing layer.']}
    yy,xx=np.mgrid[795:883,331:419];x,y=(xx+.5)/2,(yy+.5)/2
    for st in an.STAGES:
        staged={k:v[st] for k,v in loaded.items()};old=next(r for r in official['stages'] if r['stage']==st)
        gate=an.compare_geometry(list(staged.values()));same(gate,old['geometry'],st+'/geometry');assert gate['status']=='passed'
        images={k:v['images'] for k,v in staged.items()};flat0=images['control']['flat']
        flat_per_round={k:{'p99_RGB':np.quantile(abs(v['flat']-flat0),.99,axis=(0,1)).tolist(),
            'max_RGB':np.max(abs(v['flat']-flat0),axis=(0,1)).tolist(),
            'abs_gt3_counts_RGB':np.sum(abs(v['flat']-flat0)>3,axis=(0,1)).tolist()} for k,v in images.items()}
        same(flat_per_round,old['flat_per_round'],st+'/flat_per_round')
        delta={k:v['shape']-v['flat'] for k,v in images.items()}
        repeat=delta['control_repeat']-delta['control'];full=delta['full']-delta['control']
        active=(np.max(abs(full),axis=2)>4)|((x>=179)&(x<197)&(y>=410)&(y<428))
        rp=np.quantile(abs(repeat[active]),.99,axis=0);same(rp.tolist(),old['repeat_active_p99_RGB'],st+'/repeat_p99')
        assert np.all(rp<=3) and all(np.all(np.asarray(v['p99_RGB'])<=3) for v in flat_per_round.values())
        raw=images['half']['shape']-.5*(images['full']['shape']+images['control']['shape'])
        flat=images['half']['flat']-.5*(images['full']['flat']+images['control']['flat'])
        corrected=delta['half']-.5*(delta['full']+delta['control'])
        inset=an.inset(x,y,staged['full']['geometries']['shape']['carrier_bounds'])
        fields={'raw_encoded_midpoint':raw,'flat_midpoint':flat,'corrected_encoded_midpoint':corrected,
            'repeat_control':repeat,'full_finite_difference':full,'half_finite_difference':delta['half']-delta['control']}
        arr=np.load(ROOT/'original'/(st+'-midpoint-original-byte.npz'))
        for key,value in dict(x=x,y=y,inset=inset,**fields).items():assert np.array_equal(value,arr[key]),(st,key)
        regions={'complete':np.ones(x.shape,bool),'above_rail':y<422,'rail_confounded':(y>=422)&(y<438),
            'below_rail':y>=438,'above_rail_full_G_ge8':(y<422)&(full[...,1]>=8),'above_rail_prior_active':(y<422)&active}
        got={name:{region:mid.summary(a,m) for region,m in regions.items()} for name,a in fields.items()}
        same(got,old['fields'],st+'/fields')
        bins=[]
        for lo,hi in zip(plan['inset_bins'][:-1],plan['inset_bins'][1:]):
            for domain,dm in [('above_rail',y<422),('rail_confounded',(y>=422)&(y<438))]:
                m=dm&(inset>=lo)&(inset<hi)
                bins.append({'bin':[lo,hi],'domain':domain,'all':mid.summary(corrected,m),
                    'condition_full_G_ge8':mid.summary(corrected,m&(full[...,1]>=8)),'repeat':mid.summary(repeat,m)})
        same(bins,old['inset_rows'],st+'/inset_rows')
        m=y<422;bad=np.any(abs(corrected)>1.5,axis=2)&m
        for iy,ix in zip(*np.where(bad)):
            report['above_rail_exception_pixels'].append({'stage':st,'xy':[float(x[iy,ix]),float(y[iy,ix])],
                'inset':float(inset[iy,ix]),'E_RGB':corrected[iy,ix].tolist(),
                'C_RGB':images['control']['shape'][iy,ix].tolist(),'H_RGB':images['half']['shape'][iy,ix].tolist(),
                'F_RGB':images['full']['shape'][iy,ix].tolist()})
        report['stages'][st]={'all_official_metrics_match':True,'all_original_NPZ_arrays_match':True,
            'flat_per_round_max_RGB':{k:v['max_RGB'] for k,v in flat_per_round.items()},
            'repeat_complete_max_RGB':np.max(abs(repeat),axis=(0,1)).tolist(),
            'above_rail_max_abs_RGB':np.max(abs(corrected[m]),axis=0).tolist(),
            'above_rail_abs_gt1_5_RGB':np.sum(abs(corrected[m])>1.5,axis=0).tolist()}
    assert len(report['above_rail_exception_pixels'])==5
    assert sum(abs(p['E_RGB'][0])>4 for p in report['above_rail_exception_pixels'])==3
    assert max(abs(p['E_RGB'][0]) for p in report['above_rail_exception_pixels'])==7.5
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 6 stages, all official ROI summaries/inset bins and original arrays; 5 exceptions, 3 >4, max7.5.')

if __name__=='__main__':main()
