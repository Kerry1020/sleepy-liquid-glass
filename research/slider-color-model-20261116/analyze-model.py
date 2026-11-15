#!/usr/bin/env python3
"""Falsifiable finite encoded-color models of existing Slider U; no acquisitions."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np

W = np.array([.2126, .7152, .0722])
I = np.eye(3)
LUMA = np.tile(W, (3, 1))
THRESHOLDS = (1, 4, 8)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stats(values):
    a = np.asarray(values, float).ravel()
    if not len(a):
        return {"samples": 0}
    return {"samples": len(a), "min": float(a.min()), "max": float(a.max()),
            "maxabs": float(abs(a).max()), "rmse": float(np.sqrt(np.mean(a*a))),
            "mean": float(a.mean()), "absolute_quantiles": {str(q): float(np.quantile(abs(a), q)) for q in (.5, .9, .99)},
            "count_abs_gt": {str(t): int(np.sum(abs(a) > t)) for t in THRESHOLDS}}


def basis_models():
    diagonal = [np.diag(np.eye(3)[j]) for j in range(3)]
    return {
        "scalar_gain": np.array([I]),
        "brightness_saturation": np.array([I, LUMA]),
        "independent_diagonal_shared_luma": np.array(diagonal + [LUMA]),
        "output_row_saturation": np.array(diagonal + [np.outer(np.eye(3)[i], W) for i in range(3)]),
    }


def ls_model(u, basis):
    design = basis.reshape(len(basis), 9).T
    # Explicit contractions avoid platform BLAS status warnings on these tiny matrices.
    coefficients = np.einsum("ni,ki->nk", u.reshape(-1, 9), np.linalg.pinv(design))
    fitted = np.einsum("nk,ik->ni", coefficients, design).reshape(u.shape)
    require(np.isfinite(coefficients).all() and np.isfinite(fitted).all(), "nonfinite model fit")
    return coefficients.reshape(*u.shape[:-2], len(basis)), fitted


def scalar_intervals(values, weights, tolerance):
    """Solve all |values - c*weights|<=T for c, with nonzero signed weights."""
    weights = np.asarray(weights, float)
    require(np.all(weights != 0), "zero interval weight")
    a, b = (values-tolerance)/weights, (values+tolerance)/weights
    return np.max(np.minimum(a, b), axis=-1), np.min(np.maximum(a, b), axis=-1)


def feasible(u, model, tolerance):
    diagonal = np.diagonal(u, axis1=-2, axis2=-1)
    off = np.array([(i, j) for i in range(3) for j in range(3) if i != j])
    values = np.stack([u[..., i, j] for i,j in off], axis=-1)
    if model == "scalar_gain":
        return (np.max(abs(values), axis=-1) <= tolerance) & (np.ptp(diagonal, axis=-1) <= 2*tolerance)
    if model in ("brightness_saturation", "independent_diagonal_shared_luma"):
        lo, hi = scalar_intervals(values, np.array([W[j] for i,j in off]), tolerance)
        if model == "brightness_saturation":
            # Eliminate common a from diagonal intervals, leaving pairwise c inequalities.
            pairs = [(i,j) for i in range(3) for j in range(i+1,3)]
            differences = np.stack([diagonal[..., i]-diagonal[..., j] for i,j in pairs], axis=-1)
            dl, dh = scalar_intervals(differences, np.array([W[i]-W[j] for i,j in pairs]), 2*tolerance)
            lo, hi = np.maximum(lo,dl), np.minimum(hi,dh)
        return lo <= hi + 1e-12
    if model == "output_row_saturation":
        flags=[]
        for i in range(3):
            js=[j for j in range(3) if j != i]
            lo,hi=scalar_intervals(u[...,i,js], W[js], tolerance)
            flags.append(lo <= hi + 1e-12)
        return np.all(np.stack(flags,axis=-1),axis=-1)
    raise ValueError(model)


def report_model(u, fitted, flags, domain):
    residual=u-fitted
    return {"signed_residual_all_components":stats(residual[domain]),
            "components":{f"out-{i}_in-{j}":stats(residual[...,i,j][domain]) for i in range(3) for j in range(3)},
            "pixel_maxabs_residual":stats(np.max(abs(residual),axis=(-2,-1))[domain]),
            "infeasible_pixels_exact_unconstrained_family":{str(t):int(np.sum(domain & ~flags[t])) for t in THRESHOLDS}}


def localized_candidates(u,inset,y,parity):
    q=np.where(inset>=0,np.maximum(1-inset/8,0)**2,0)
    fit=(y<422)&(inset>=0)&(inset<8)&parity
    require(np.any(fit),"empty local fit")
    scalar=np.trace(u,axis1=-2,axis2=-1)/3
    saturation=I-LUMA
    centered=saturation-np.trace(saturation)/3*I
    orthogonal=u-scalar[...,None,None]*I
    k=float(np.sum(q[fit,None,None]*orthogonal[fit]*centered)/(np.sum(q[fit]**2)*np.sum(centered**2)))
    a=scalar-k*q*np.trace(saturation)/3
    satfit=a[...,None,None]*I+k*q[...,None,None]*saturation
    off=np.ones((3,3),bool)^np.eye(3,dtype=bool)
    coupling=np.sum(q[fit,None,None]*u[fit],axis=0)/np.sum(q[fit]**2)
    coupling[~off]=0
    arbitrary=u*I+q[...,None,None]*coupling
    return q, {"localized_shared_saturation":{"k_raw_byte":k,"finite_matrix_per_input_byte":(k*saturation/20).tolist(),"fitted":satfit},
               "localized_six_offdiagonals":{"raw_byte_matrix":coupling.tolist(),"finite_matrix_per_input_byte":(coupling/20).tolist(),"fitted":arbitrary}}



def localized_exact_feasibility(u, q, domain, model, tolerance):
    """Existence of shared coefficients; eliminate each pixel's free diagonal gain."""
    values, weights, tolerances = [], [], []
    if model == "localized_shared_saturation":
        basis = I-LUMA
        for i in range(3):
            for j in range(3):
                if i != j:
                    values.append(u[...,i,j][domain])
                    weights.append(q[domain]*basis[i,j])
                    tolerances.append(np.full(np.sum(domain),tolerance))
        for i in range(3):
            for j in range(i+1,3):
                values.append((u[...,i,i]-u[...,j,j])[domain])
                weights.append(q[domain]*(basis[i,i]-basis[j,j]))
                tolerances.append(np.full(np.sum(domain),2*tolerance))
        lo,hi=scalar_intervals(np.concatenate(values),np.concatenate(weights),np.concatenate(tolerances))
        return {"compatible":bool(lo<=hi+1e-12),"lower":float(lo),"upper":float(hi)}
    if model == "localized_six_offdiagonals":
        components={}
        for i in range(3):
            for j in range(3):
                if i != j:
                    lo,hi=scalar_intervals(u[...,i,j][domain],q[domain],tolerance)
                    components[f"out-{i}_in-{j}"]={"compatible":bool(lo<=hi+1e-12),"lower":float(lo),"upper":float(hi)}
        return {"compatible":all(v["compatible"] for v in components.values()),"components":components}
    raise ValueError(model)


def self_test():
    rng=np.random.default_rng(60261116)
    for name,basis in basis_models().items():
        coefficients=rng.normal(size=(20,len(basis)))
        u=np.einsum('nk,kij->nij',coefficients,basis)
        _, fitted=ls_model(u,basis)
        require(np.max(abs(u-fitted))<1e-10,"LS exact family")
        require(np.all(feasible(u,name,1e-9)),"feasibility exact family")
        noisy=u+rng.uniform(-.5,.5,size=u.shape)
        require(np.all(feasible(noisy,name,.500001)),"feasibility bounded perturbation")
    bad=20*I+np.array([[0,0,0],[0,0,0],[0,12,0]])
    require(not feasible(bad,"brightness_saturation",4),"offdiagonal contradiction must reject saturation")
    require(not feasible(bad,"independent_diagonal_shared_luma",4),"diagonal freedom cannot repair offdiagonal contradiction")
    bad=np.diag([0,0,30])
    require(not feasible(bad,"brightness_saturation",1),"shared diagonal contradiction")
    require(feasible(bad,"independent_diagonal_shared_luma",0),"independent diagonal fit")
    q=np.array([.4,.8])
    source=np.stack([20*I+5*qq*(I-LUMA) for qq in q])
    for model in ("localized_shared_saturation","localized_six_offdiagonals"):
        require(localized_exact_feasibility(source,q,np.ones(2,bool),model,1e-8)["compatible"],"exact localized family")
    source[0,0,1]=20
    require(not localized_exact_feasibility(source,q,np.ones(2,bool),"localized_six_offdiagonals",1)["compatible"],"shared coupling incompatible points")
    print(json.dumps({"status":"synthetic_models_passed","cases":["four exact families","bounded perturbation feasibility","fixed-weight offdiagonal contradiction","shared diagonal contradiction","localized shared-coefficient feasibility"]}))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test',action='store_true')
    parser.add_argument('--source',type=Path,default=Path(__file__).resolve().parent.parent/'slider-color-response-20261116')
    parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parent/'results')
    args=parser.parse_args()
    if args.self_test:
        self_test();return
    source=args.source.resolve();output=args.output.resolve()
    require(not output.exists(),'never overwrite prior model analysis')
    analysis=json.loads((source/'analysis/analysis.json').read_text())
    require(analysis['status']=='OBSERVED_ENCODED_COLOR_CALIBRATION_DIAGNOSTIC_NOT_OPTICAL_ACCEPTANCE','source analysis not accepted calibration')
    require(sha(source/'analysis/original-pixels.npz')==analysis['arrays_sha256'],'source NPZ changed')
    with np.load(source/'analysis/original-pixels.npz',allow_pickle=False) as a:
        u=a['raw_global_output_input'].astype(float)
        x,y,inset=a['x'].copy(),a['y'].copy(),a['inset_capsule_assumption'].copy()
        # M is intentionally not used to fit any candidate.
    yy,xx=np.indices(x.shape);even=(xx+yy)%2==0
    domains={"complete":np.ones(x.shape,bool),"above_rail":y<422,
      "above_rail_inside_inset_0_3":(y<422)&(inset>=0)&(inset<3),
      "above_rail_inside_inset_0_1":(y<422)&(inset>=0)&(inset<1),
      "above_rail_inside_inset_1_3":(y<422)&(inset>=1)&(inset<3),
      "above_rail_inside_inset_3_8":(y<422)&(inset>=3)&(inset<8),
      "above_rail_inside_inset_ge8":(y<422)&(inset>=8),
      "source_primary_above_rail_inset_ge1":(y<422)&(inset>=1)}
    arrays={'U':u,'x':x,'y':y,'capsule_inset':inset,'even_fit_parity':even}
    models={}
    for name,basis in basis_models().items():
        coefficients,fitted=ls_model(u,basis)
        flags={t:feasible(u,name,t) for t in THRESHOLDS}
        models[name]={'parameters_per_pixel':len(basis),'domains':{n:report_model(u,fitted,flags,d) for n,d in domains.items()}}
        arrays[name+'_coefficients']=coefficients;arrays[name+'_residual']=u-fitted
        for t,flag in flags.items():arrays[name+f'_T{t}_feasible']=flag
        if name=='brightness_saturation':
            aa,cc=coefficients[...,0],coefficients[...,1];brightness=(aa+cc)/20
            stable=abs(aa+cc)>1
            sat=np.divide(aa,aa+cc,out=np.zeros_like(aa),where=stable)
            models[name]['implied_unconstrained_values']={n:{'brightness':stats(brightness[d]),'saturation_stable_only':stats(sat[d&stable]),'weak_denominator_pixels':int(np.sum(d&~stable)),'negative_brightness_or_a_pixels':int(np.sum(d&((brightness<0)|(aa<0))))} for n,d in domains.items()}
    q,local=localized_candidates(u,inset,y,even)
    for name,candidate in local.items():
        fitted=candidate.pop('fitted');arrays[name+'_residual']=u-fitted
        candidate['exact_shared_coefficient_family_feasibility']={}
        for n in ('above_rail_inside_inset_0_3','above_rail_inside_inset_0_1','above_rail_inside_inset_1_3','above_rail_inside_inset_3_8'):
            d=domains[n]
            candidate['exact_shared_coefficient_family_feasibility'][n]={part:{str(t):localized_exact_feasibility(u,q,mask,name,t) for t in THRESHOLDS} for part,mask in [('all',d),('fit_even',d&even),('crosscheck_odd',d&~even)]}
        candidate['domains']={}
        for n,d in domains.items():
            candidate['domains'][n]={part:{'pixels':int(np.sum(mask)),'all_components':stats((u-fitted)[mask]),'pixel_maxabs':stats(np.max(abs(u-fitted),axis=(-2,-1))[mask])} for part,mask in [('all',d),('fit_even',d&even),('crosscheck_odd',d&~even)]}
    arrays['localized_q']=q
    invariants={}
    for j in range(3):
        rows=[i for i in range(3) if i!=j];difference=u[...,rows[0],j]-u[...,rows[1],j]
        invariants['input_column_'+str(j)]={n:{'difference':stats(difference[d]),'necessary_rejections_T1_T4_T8':{str(t):int(np.sum(d&(abs(difference)>2*t))) for t in THRESHOLDS}} for n,d in domains.items()}
    result={'schema':1,'status':'POSTHOC_FINITE_ENCODED_U_MODEL_DIAGNOSTIC_NOT_NATIVE_PIPELINE_IDENTIFICATION',
      'plan_sha256':sha(Path(__file__).with_name('PLAN.md')),'analyzer_sha256':sha(__file__),
      'source_analysis_sha256':sha(source/'analysis/analysis.json'),'source_npz_sha256':sha(source/'analysis/original-pixels.npz'),'source_freeze_sha256':sha(source/'freeze.json'),
      'weights':W.tolist(),'thresholds_raw_byte':list(THRESHOLDS),'axes':['outputRGB','inputRGB'],'domain_pixels':{n:int(np.sum(d)) for n,d in domains.items()},
      'models':models,'localized_models':local,'repeated_offdiagonal_column_invariant':invariants,
      'scope':'Existing U only; no trace/xcresult/source PNG read, new capture or production parameter change. Per-pixel parameters are expressive upper bounds, not runtime estimates. Checkerboard is internal spatial crosscheck, not independent holdout.'}
    output.mkdir(parents=True)
    np.savez_compressed(output/'model-arrays.npz',**arrays)
    result['model_arrays_sha256']=sha(output/'model-arrays.npz')
    (output/'analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':result['status'],'analysis':str(output/'analysis.json'),'sha256':sha(output/'analysis.json')}))


if __name__=='__main__':
    main()
