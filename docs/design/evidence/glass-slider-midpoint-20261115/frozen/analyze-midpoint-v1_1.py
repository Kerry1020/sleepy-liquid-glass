#!/usr/bin/env python3
"""Bounded original-byte midpoint diagnostic, reusing the frozen native parser."""
from pathlib import Path
import hashlib, importlib.util, json
import numpy as np

P = Path(__file__).resolve().parent
O = P / 'midpoint-v1'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
module = importlib.util.spec_from_file_location('frozen_G', P / 'analyze-witness-control-v1_1.py')
f = importlib.util.module_from_spec(module)
module.loader.exec_module(f)

def read(p): return json.loads(p.read_text())
def role(root):
    spec = read(root / 'shape-spec.json')
    manifest = read(root / 'inputs/manifest.json')
    main = next(v for v in spec['inputs'] if v['id'] == spec['first_input_id'])
    return dict(spec_value=spec, manifest_value=manifest, main_id=main['id'],
                spec_sha256=sha(root/'shape-spec.json'), manifest_sha256=sha(root/'inputs/manifest.json'),
                main_sha256=main['source_sha256'], source_png=str(root/main['shape']['source_png']))

def summary(a, mask):
    values = a[mask]
    if not len(values): return {'samples':0}
    return {'samples':len(values), 'channels':{c:{'mean':float(values[:,k].mean()),
        'rmse':float(np.sqrt(np.mean(values[:,k]**2))), 'min':float(values[:,k].min()),
        'max':float(values[:,k].max()), 'p99_abs':float(np.quantile(abs(values[:,k]),.99)),
        'abs_gt_counts':{str(t):int(np.sum(abs(values[:,k])>t)) for t in [4,8,16,24]}}
        for k,c in enumerate('RGB')}}

def main():
    plan = read(O/'analysis-plan-v1_1.json')
    assert sha(__file__) == plan['analysis_sha256']
    assert sha(P/'analyze-witness-control-v1_1.py') == plan['frozen_parser_sha256']
    for rel, digest in plan['source_and_prior_hashes'].items(): assert sha(P/rel) == digest
    loaded = {}
    for name, rec in plan['rounds'].items():
        root = P/rec['root']
        loaded[name] = f.load_round(root/rec['index'], role(root))
        assert loaded[name]['platform'] == 'ios' and not loaded[name]['synthetic_fixture']
    rows = []
    for st in f.STAGES:
        staged = {k:v['stages'][st] for k,v in loaded.items()}
        gate = f.compare_geometry(list(staged.values()))
        row = {'stage':st, 'geometry':gate}
        if gate['status'] != 'passed':
            row['status']='REJECTED_GEOMETRY'; rows.append(row); continue
        mappings = [v['mappings'][k] for v in staged.values() for k in ['shape','flat']]
        assert all(v['scale']==2 and np.array_equal(v['origin'],[0,0]) for v in mappings)
        yy,xx = np.mgrid[795:883,331:419]
        x,y=(xx+.5)/2,(yy+.5)/2
        images={k:{q:v['images'][q][795:883,331:419].astype(float) for q in ['shape','flat']} for k,v in staged.items()}
        flat0=images['control']['flat']
        drift=np.stack([v['flat']-flat0 for v in images.values()])
        deltas={k:v['shape']-v['flat'] for k,v in images.items()}
        repeat=deltas['control_repeat']-deltas['control']
        full=deltas['full']-deltas['control']
        active=np.max(abs(full),axis=2)>4
        prior_source_box=(x>=179)&(x<197)&(y>=410)&(y<428)
        drift_active=active|prior_source_box
        flat_per_round={k:{'p99_RGB':np.quantile(abs(v['flat']-flat0),.99,axis=(0,1)).tolist(),
            'max_RGB':np.max(abs(v['flat']-flat0),axis=(0,1)).tolist(),
            'abs_gt3_counts_RGB':np.sum(abs(v['flat']-flat0)>3,axis=(0,1)).tolist()} for k,v in images.items()}
        flat_p99=np.max([v['p99_RGB'] for v in flat_per_round.values()],axis=0)
        null_p99=np.quantile(abs(repeat[drift_active]),.99,axis=0)
        row.update(flat_per_round=flat_per_round,flat_worst_round_p99_RGB=flat_p99.tolist(),flat_max_RGB=np.max(abs(drift),axis=(0,1,2)).tolist(),
            repeat_active_p99_RGB=null_p99.tolist(),repeat_complete=summary(repeat,np.ones(x.shape,bool)))
        if np.any(flat_p99>3) or np.any(null_p99>3):
            row['status']='REJECTED_DRIFT'; rows.append(row); continue
        # Control is shared exactly, not treated as two independent observations.
        raw=images['half']['shape']-.5*(images['full']['shape']+images['control']['shape'])
        flat=images['half']['flat']-.5*(images['full']['flat']+images['control']['flat'])
        corrected=deltas['half']-.5*(deltas['full']+deltas['control'])
        assert np.array_equal(corrected,raw-flat)
        inset=f.inset(x,y,staged['full']['geometries']['shape']['carrier_bounds'])
        fields={'raw_encoded_midpoint':raw,'flat_midpoint':flat,'corrected_encoded_midpoint':corrected,
                'repeat_control':repeat,'full_finite_difference':full,
                'half_finite_difference':deltas['half']-deltas['control']}
        regions={'complete':np.ones(x.shape,bool),'above_rail':y<422,
                 'rail_confounded':(y>=422)&(y<438),'below_rail':y>=438,
                 'above_rail_full_G_ge8':(y<422)&(full[...,1]>=8),
                 'above_rail_prior_active':(y<422)&drift_active}
        row.update(status='OBSERVED_ENCODED_MIDPOINT_DIAGNOSTIC',fields={
            name:{region:summary(a,m) for region,m in regions.items()} for name,a in fields.items()})
        row['inset_rows']=[]
        for lo,hi in zip(plan['inset_bins'][:-1],plan['inset_bins'][1:]):
            for domain,dm in [('above_rail',y<422),('rail_confounded',(y>=422)&(y<438))]:
                m=dm&(inset>=lo)&(inset<hi)
                row['inset_rows'].append({'bin':[lo,hi],'domain':domain,
                    'all':summary(corrected,m),'condition_full_G_ge8':summary(corrected,m&(full[...,1]>=8)),
                    'repeat':summary(repeat,m)})
        np.savez_compressed(O/(st+'-midpoint-original-byte.npz'),x=x,y=y,inset=inset,**fields)
        rows.append(row)
    result={'status':'bounded_original_pixel_diagnostic', 'plan_sha256':sha(O/'analysis-plan-v1_1.json'),
        'indexes':{k:{'path':v['path'],'sha256':v['sha256']} for k,v in loaded.items()},
        'scope':plan['interpretation_limits'], 'stages':rows}
    (O/'analysis.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    print(json.dumps({'stages':{r['stage']:r['status'] for r in rows}}))
    return 0 if all(r['status']=='OBSERVED_ENCODED_MIDPOINT_DIAGNOSTIC' for r in rows) else 2

if __name__=='__main__': raise SystemExit(main())
