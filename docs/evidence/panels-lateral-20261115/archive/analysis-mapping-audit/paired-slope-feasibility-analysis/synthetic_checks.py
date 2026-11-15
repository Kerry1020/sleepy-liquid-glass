#!/usr/bin/env python3
"""Deterministic synthetic-only verification. No real source/output is decoded."""
from __future__ import annotations
import copy
import io
import json
import math
from pathlib import Path
import struct
import sys
import zlib

import numpy as np
from PIL import Image, ImageCms, PngImagePlugin

import analysis as A

HERE = Path(__file__).resolve().parent
CHECKS = []
ARTIFACTS = {}


def check(name, condition, evidence=None):
    CHECKS.append({'name':name,'passed':bool(condition),'evidence':evidence})


def curve(x, position, sigma=1.2):
    return .5*(1+np.array([math.erf((t-position)/(sigma*math.sqrt(2))) for t in x]))


def feature(position=158., *, side='left',polarity='normal',sigma=1.2,
            q=None, amplitude=130.,p0=None,p1=None,quantized=False,**kw):
    x = np.arange(128.25,187,.5)
    normalized = curve(x,position,sigma) if q is None else np.asarray(q,float)
    sign = int(np.sign(A.source_direction(side,polarity)[0]))
    first,last = ((60.,60.+amplitude) if sign>0 else (60.+amplitude,60.))
    gray = first+(last-first)*normalized
    if quantized:
        gray = np.rint(gray)
    rgb = np.repeat(gray[:,None],3,axis=1)
    start = np.full((16,3),first) if p0 is None else p0
    end = np.full((16,3),last) if p1 is None else p1
    return A.feature_operator(x,rgb,start,end,A.source_direction(side,polarity),
                              clear_support_px=kw.pop('clear_support_px',len(x)),**kw)


def scalar_feature(position, uncertainty=.25, eligible=True, failed=None):
    return {'eligible':eligible,'failed_gates':failed or [],'cross50_pt':position,
            'location_uncertainty_pt':uncertainty}


def apparent(a,d,g=None,u=0):
    g = d if g is None else g
    center = 187.5-u
    width = 2*a+.5*g
    return A.pair_observables(scalar_feature(center-width/2),
        scalar_feature(center+width/2),a,d)


def png_chunk(name,payload):
    kind=name.encode('ascii')
    return struct.pack('>I',len(payload))+kind+payload+struct.pack('>I',zlib.crc32(kind+payload)&0xffffffff)


def synthetic_png(*,srgb=0,icc=None,extra_before=(),extra_after=(),alpha=False):
    mode='RGBA' if alpha else 'RGB'
    image=Image.new(mode,(16,12),(60,90,120,255) if alpha else (60,90,120))
    info=PngImagePlugin.PngInfo()
    if srgb is not None:
        info.add(b'sRGB',bytes([srgb]))
    for name,payload in extra_before:
        info.add(name.encode('ascii'),payload)
    buffer=io.BytesIO()
    image.save(buffer,format='PNG',pnginfo=info,**({'icc_profile':icc} if icc else {}))
    data=buffer.getvalue()
    if extra_after:
        data=data[:-12]+b''.join(png_chunk(n,p) for n,p in extra_after)+data[-12:]
    return data


def run():
    baseline=feature()
    check('baseline_known_50_position',baseline['eligible'] and abs(baseline['cross50_pt']-158)<1e-10,
          {'cross50_pt':baseline.get('cross50_pt'),'failed_gates':baseline['failed_gates']})
    shifted=feature(position=161.)
    check('known_translation_3pt',shifted['eligible'] and abs(shifted['cross50_pt']-baseline['cross50_pt']-3)<1e-10)
    blur=feature(sigma=3.5)
    def width(f):
        c=f['smoothed_crossings'];return c['90']['increasing'][0]-c['10']['increasing'][0]
    check('known_blur_broadens_not_recenters',blur['eligible'] and width(blur)>width(baseline) and abs(blur['cross50_pt']-158)<1e-9,
          {'baseline_10_90_width':width(baseline),'blurred_10_90_width':width(blur)})
    reversed_f=feature(polarity='reversed')
    check('oracle_reversal_sign_orients_increasing',reversed_f['eligible'] and abs(reversed_f['cross50_pt']-158)<1e-10)
    inverted=feature(q=1-curve(np.arange(128.25,187,.5),158))
    check('wrong_output_direction_fails',not inverted['eligible'] and 'smoothed_increasing_10_50_90_missing_or_nonunique' in inverted['failed_gates'],inverted['failed_gates'])
    low=feature(amplitude=3)
    check('low_contrast_fails_original_threshold',not low['eligible'] and 'contrast<8' in low['failed_gates'],low['failed_gates'])
    p0=np.repeat(np.array([0,120]*8)[:,None],3,axis=1)
    variable=feature(p0=p0)
    check('both_plateau_spreads_preserved',not variable['eligible'] and 'contrast<5x_plateau0_spread_floor1' in variable['failed_gates'],
          {'failed':variable['failed_gates'],'spreads':variable['plateau_robust_spreads']})
    p1=np.repeat(np.array([130,250]*8)[:,None],3,axis=1)
    variable_end=feature(p1=p1)
    check('end_plateau_spread_independently_gated','contrast<5x_plateau1_spread_floor1' in variable_end['failed_gates'])
    x=np.arange(128.25,187,.5)
    double=feature(q=.5*curve(x,151)+.5*curve(x,166))
    check('double_peak_never_silently_nearest',not double['eligible'] and 'secondary_peak>0.8primary' in double['failed_gates'],
          {'ratio':double['secondary_to_primary'],'peaks':double['peaks'],'failed':double['failed_gates']})
    q=curve(x,158,3)
    q[58]-=.12
    nonmono=feature(q=q)
    check('raw_transition_backward_step_retained','transition_raw_backward_step>1count' in nonmono['failed_gates'],
          {'maximum_backward':nonmono['maximum_raw_backward_step'],'failed':nonmono['failed_gates']})
    many=feature(q=curve(x,148)-curve(x,158)+curve(x,168))
    check('all_crossing_directions_multiplicity_retained',len(many['smoothed_crossings']['50']['increasing'])>1 and len(many['smoothed_crossings']['50']['decreasing'])>0 and not many['eligible'],many['smoothed_crossings']['50'])
    missing=feature(q=np.zeros(len(x)))
    check('missing_edge_not_completed',not missing['eligible'] and 'cross50_pt' not in missing)
    fg=feature(foreground_collisions=[[140,250,160,280]])
    check('foreground_collision_always_fails','foreground_support_collision' in fg['failed_gates'] and not fg['eligible'])
    narrow=feature(clear_support_px=11)
    check('clear_support_gate','clear_support<12px' in narrow['failed_gates'])
    ramp=feature(q=np.clip((x-148)/20,0,1))
    check('tied_primary_uncertainty_fails_fine_scalar','location_uncertainty>1pt' in ramp['failed_gates'] and ramp['location_uncertainty_pt']>1,
          {'uncertainty':ramp['location_uncertainty_pt'],'tied_indices':ramp['tied_primary_indices']})
    quant=feature(quantized=True)
    check('quantized_50_respects_raster_floor',quant['eligible'] and quant['location_uncertainty_pt']>=.25 and abs(quant['cross50_pt']-158)<=.25)
    plateau=A.crossings(np.array([0,.5,1,1.5]),np.array([0,1,1,2]),1)
    check('threshold_exact_ties_explicit',plateau['level_plateau_segments']==[[.5,1.]] and plateau['increasing']==[1.])
    pair=apparent(20,5,g=9,u=2)
    check('known_stretch_and_shift_apparent_math',pair['eligible'] and pair['values']['g']==9 and pair['values']['U']==2 and pair['values']['D']==4,pair)
    check('absolute_bounds_source_quantization_propagated',pair['bounds']['W']==.5 and pair['bounds']['g']==1 and pair['bounds']['U']==.25)
    missing_pair=A.pair_observables(scalar_feature(160),{'eligible':False,'failed_gates':['missing']},20,1)
    check('pair_requires_both_independently_eligible',not missing_pair['eligible'] and 'values' not in missing_pair and missing_pair['failed_gates']==['right:missing'])
    grid={(p,a,c,float(d)):apparent(a,float(d),g=float(d)+2,u=1)
          for p in ('native','android') for a in (20,24) for c in ('normal','reversed')
          for d in np.arange(.25,20,.5)}
    finalized=A.apply_falsification(grid)
    check('all_reverse_width_conditions_required_and_compatible',all(r['eligible'] for r in finalized.values()))
    broken=copy.deepcopy(grid)
    broken[('native',20,'reversed',5.25)]=apparent(20,5.25,g=5.25+2,u=3)
    broken_final=A.apply_falsification(broken)
    check('reverse_and_width_failure_not_averaged_away',not broken_final[('native',20,'normal',5.25)]['eligible'] and not broken_final[('native',24,'reversed',5.25)]['eligible'],
          {'reverse':broken_final[('native',20,'normal',5.25)]['failed_gates'],'width':broken_final[('native',24,'reversed',5.25)]['failed_gates']})
    check('failing_quartet_cannot_export_favorable_subset',all(not broken_final[('native',a,c,5.25)]['eligible'] and 'values' not in broken_final[('native',a,c,5.25)] for a in (20,24) for c in ('normal','reversed')))
    sec=A.secants(finalized)
    s=next(r for r in sec if r['platform']=='native' and r['a_pt']==20 and r['polarity']=='normal' and r['d_nominal_AX_pt']==8.25)
    check('fixed_h4_known_linear_secants',s['g_prime']['value']==1 and s['g_second']['value']==0 and s['g_prime']['absolute_bound']>=.25 and s['g_second']['absolute_bound_per_pt']>=.25,s)
    check('no_boundary_derivatives_or_extrapolation',next(r for r in sec if r['d_nominal_AX_pt']==.25)['g_prime'] is None)
    failed_center=copy.deepcopy(finalized)
    failed_center[('native',20,'normal',8.25)]={'eligible':False,'failed_gates':['center_failed']}
    s=next(r for r in A.secants(failed_center) if r['platform']=='native' and r['a_pt']==20 and r['polarity']=='normal' and r['d_nominal_AX_pt']==8.25)
    check('first_secant_only_needs_endpoints_second_needs_center',s['g_prime'] is not None and s['g_second'] is None)
    residual=A.platform_residuals(finalized)
    check('platform_residuals_descriptive_without_pass_threshold',all(v['difference']==0 for r in residual for v in r['residuals'].values()))
    check('all_top_source_lines_analytically_constant',all(A.source_line_constant(xx,a,c) for xx in A.TOP_X for a in (20,24) for c in ('normal','reversed')))
    flat=A.top_flatness([scalar_feature(257.5+i*.02) for i in range(9)])
    nonflat=A.top_flatness([scalar_feature(257.5+i*.1) for i in range(9)])
    check('top50_all9_interval_intersection',flat['eligible'] and not nonflat['eligible'] and 'top50_intervals_no_common_intersection' in nonflat['failed_gates'])
    check('top50_missing_never_completed',not A.top_flatness([scalar_feature(257.5)]*8)['eligible'])
    no_direction=A.feature_operator(x,np.zeros((len(x),3)),np.zeros((16,3)),np.ones((16,3)),None,clear_support_px=len(x))
    check('undefined_top_direction_never_inferred','source_direction_undefined' in no_direction['failed_gates'])
    # Synthetic complete RGBA source and known warped wedge. No file is read.
    yy,xx=np.indices((1334,750))
    source_rgb=A.source_rgb((xx+.5)/2,(yy+.5)/2,20)
    frozen_plan=json.loads((HERE/'analysis-plan.json').read_text())
    for sid,spec in frozen_plan['source_pngs'].items():
        generated=A.source_rgb((xx+.5)/2,(yy+.5)/2,spec['a_pt'],spec['contrast'])
        check('analytic_raster_original_RGB_hash_'+sid,A.sha(generated.tobytes())==spec['source_RGB_sha256'])
    source=np.concatenate([source_rgb,np.full((1334,750,1),255,np.uint8)],axis=-1)
    warped=source.copy()
    for y in np.arange(257.75,277.5,.5):
        d=y-257.5
        # g=d+2; analytically widen each side by .5pt.
        row=A.source_rgb((np.arange(750)+.5)/2,y+2,20)
        warped[int(y*2),:,:3]=row
    tracks={'raw_encoded_RGBA':source,'normalized_sRGB_RGBA':source.copy()}
    rest_tracks={'raw_encoded_RGBA':warped,'normalized_sRGB_RGBA':warped.copy()}
    phases={'clean-before':tracks,'rest':rest_tracks,'rest-repeat':rest_tracks,'dismiss-after':tracks}
    session,session_rows=A.analyze_decoded_session(A.IDS[0],'native',tracks,phases,[])
    bilateral=sum(r['apparent']['eligible'] for r in session['tracks']['raw_encoded_RGBA']['rows'])
    check('bilateral_math_independent_from_unavailable_top',bilateral==40 and not session['overall_eligible'] and not session['tracks']['raw_encoded_RGBA']['top50']['eligible'],
          {'bilateral_eligible_rows':bilateral,'top_failed':session['tracks']['raw_encoded_RGBA']['top50']['failed_gates'][:3]})
    changed=warped.copy();changed[0,0,0]^=1
    nonzero_phases={**phases,'rest-repeat':{'raw_encoded_RGBA':changed,'normalized_sRGB_RGBA':changed.copy()}}
    rep,_=A.analyze_decoded_session(A.IDS[0],'native',tracks,nonzero_phases,[])
    check('repeat_entire_RGBA_one_pixel_outside_ROI_fails','nonzero_full_REST_repeat_RGBA' in rep['tracks']['raw_encoded_RGBA']['failed_gates'] and not any(r['apparent']['eligible'] for r in rep['tracks']['raw_encoded_RGBA']['rows']))
    before=source.copy();before[600,300,0]^=1
    foot_phases={**phases,'clean-before':{'raw_encoded_RGBA':before,'normalized_sRGB_RGBA':before.copy()}}
    footprint,_=A.analyze_decoded_session(A.IDS[0],'native',tracks,foot_phases,[])
    check('fixed_region_exactness_independent_before_after',any(s.startswith('source_region_nonexact:clean-before:') for s in footprint['tracks']['raw_encoded_RGBA']['failed_gates']))
    with_fg,_=A.analyze_decoded_session(A.IDS[0],'native',tracks,phases,[[120,260,150,264]])
    check('foreground_expansion2pt_and_full_failure_retention',any('foreground_support_collision' in r['sides']['left']['failed_gates'] for r in with_fg['tracks']['raw_encoded_RGBA']['rows']))
    frame=lambda t:{'captured_at_unix_seconds':t,'AX':{},'layout_receipt':{}}
    complete={'platform':'native','frames':{p:frame(i) for i,p in enumerate(A.PHASES)}}
    missing_android={'platform':'android','frames':{p:frame(i) for i,p in enumerate(('rest','rest-repeat'))}}
    missing_native={'platform':'native','frames':{p:frame(i) for i,p in enumerate(('rest','rest-repeat'))}}
    check('native_all_four_phases_mandatory',A.phase_gate(complete)['eligible'] and not A.phase_gate(missing_native)['eligible'])
    check('android_explicit_missing_before_after_insufficient',A.phase_gate(missing_android)['missing_phases']==['clean-before','dismiss-after'] and not A.phase_gate(missing_android)['eligible'],A.phase_gate(missing_android))
    tight=copy.deepcopy(complete);tight['frames']['rest-repeat']['captured_at_unix_seconds']=1.1
    check('repeat_spacing_time_gate','rest_repeat_spacing<0.25seconds' in A.phase_gate(tight)['failed_gates'])
    check('unknown_receipt_payload_never_becomes_provenance',not A.provenance_gate({'accepted':True})['eligible'])
    # PNG tests are generated in memory, including valid RGB/RGBA and ICC.
    srgb=synthetic_png()
    png_tracks,meta=A.decode_png(srgb,(16,12))
    check('PNG_explicit_sRGB_without_ICC_supported',meta['structurally_valid'] and meta['normalization']=='identity_explicit_sRGB' and set(png_tracks)=={'raw_encoded_RGBA','normalized_sRGB_RGBA'})
    rgba=synthetic_png(alpha=True)
    check('PNG_RGBA_alpha_declaration',A.parse_png(rgba,(16,12))['alpha_declaration']=='RGBA_channel')
    for intent in range(4):
        check(f'PNG_legal_sRGB_intent_{intent}',A.parse_png(synthetic_png(srgb=intent),(16,12))['normalization']=='identity_explicit_sRGB')
    bad=bytearray(srgb);bad[-1]^=1
    bad_tracks,badmeta=A.decode_png(bytes(bad),(16,12))
    check('PNG_CRC_rejected_before_decode',not bad_tracks and any('CRC' in s for s in badmeta['failed_gates']))
    duplicate=srgb[:-12]+png_chunk('sRGB',b'\x00')+srgb[-12:]
    check('PNG_duplicate_and_order_fail',not A.parse_png(duplicate,(16,12))['structurally_valid'])
    check('PNG_IEND_trailing_bytes_fail',not A.parse_png(srgb+b'x',(16,12))['structurally_valid'])
    check('PNG_chunk_bounds_fail',not A.parse_png(srgb[:-5],(16,12))['structurally_valid'])
    check('PNG_IHDR_geometry_fixed',not A.decode_png(srgb,(750,1334))[0])
    check('PNG_IHDR_first_unique_enforced',not A.parse_png(srgb[:8]+png_chunk('sRGB',b'\x00')+srgb[8:],(16,12))['structurally_valid'])
    unknown_critical=srgb[:33]+png_chunk('ABCD',b'x')+srgb[33:]
    check('PNG_unknown_critical_rejected_before_decode',not A.decode_png(unknown_critical,(16,12))[0])
    unsupported=synthetic_png(extra_before=(('cICP',bytes([9,16,0,1])),))
    u_tracks,u_meta=A.decode_png(unsupported,(16,12))
    check('PNG_unknown_high_priority_cICP_blocks_sRGB_fallback',u_meta['color_authority']=='cICP' and u_meta['normalization']=='unresolved' and 'normalized_sRGB_RGBA' not in u_tracks and 'raw_encoded_RGBA' in u_tracks)
    cicp=synthetic_png(extra_before=(('cICP',bytes([1,13,0,1])),))
    check('PNG_known_sRGB_cICP_supported',A.parse_png(cicp,(16,12))['normalization']=='identity_explicit_sRGB_cICP')
    gamma=synthetic_png(srgb=None,extra_before=(('gAMA',struct.pack('>I',45455)),))
    g_tracks,g_meta=A.decode_png(gamma,(16,12))
    check('PNG_gamma_only_raw_not_assumed_sRGB',g_meta['normalization']=='unresolved' and list(g_tracks)==['raw_encoded_RGBA'])
    conflicting=synthetic_png(extra_before=(('gAMA',struct.pack('>I',60000)),))
    check('PNG_conflicting_lower_declaration_retained',A.parse_png(conflicting,(16,12)).get('sRGB_gAMA_conflict') is True and A.parse_png(conflicting,(16,12))['normalization']=='unresolved')
    icc=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    icc_png=synthetic_png(srgb=None,icc=icc)
    icc_tracks,icc_meta=A.decode_png(icc_png,(16,12))
    check('PNG_valid_RGB_ICC_normalizes_with_profile_intent_hashes',icc_meta['normalization']=='ICC_to_sRGB' and 'normalized_sRGB_RGBA' in icc_tracks and icc_meta['icc_sha256']==A.sha(icc) and 'icc_intent_bytes_sha256' in icc_meta)
    invalid_icc=synthetic_png(srgb=None,extra_before=(('iCCP',b'bad\x00\x00'+zlib.compress(b'not a profile')),))
    # Pillow silently omits unknown chunks when writing; direct insertion ensures
    # metadata under test exactly exists in the synthetic original byte stream.
    invalid_icc=srgb[:33]+png_chunk('iCCP',b'bad\x00\x00'+zlib.compress(b'not a profile'))+srgb[33:]
    i_tracks,i_meta=A.decode_png(invalid_icc,(16,12))
    check('PNG_invalid_ICC_blocks_lower_sRGB',i_meta['normalization']=='unresolved' and i_meta['iCCP_sRGB_cooccurrence'] and 'normalized_sRGB_RGBA' not in i_tracks)
    alpha_trns=rgba[:33]+png_chunk('tRNS',b'\x00\x00\x00\x00\x00\x00')+rgba[33:]
    check('PNG_RGBA_tRNS_illegal_alpha_declaration_rejected',not A.decode_png(alpha_trns,(16,12))[0])
    illegal_srgb=srgb[:33]+png_chunk('sRGB',b'\x04')+srgb[33:]
    check('PNG_invalid_sRGB_intent_unresolved',A.parse_png(illegal_srgb,(16,12))['normalization']=='unresolved')
    schema=json.loads((HERE/'capture-handoff.schema.json').read_text())
    check('schema_evaluator_required_and_unknown_keys',bool(A.schema_errors({'schema':1,'surprise':True},schema)))
    art={'path':'/synthetic-only/not-opened','sha256':'a'*64}
    session_schema=schema['$defs']['session']
    ss={name:copy.deepcopy(art) for name in ('source_original','session_receipt','traits_receipt','canvas_mapping_receipt','foreground_geometry_receipt','binary_freeze','source_freeze')}
    ss.update({'source_id':A.IDS[0],'platform':'native','theme':'light','carrier':'alert',
        'trace_receipts':[copy.deepcopy(art)],'frames':{p:{'png':copy.deepcopy(art),'captured_at_unix_seconds':i,
        'phase_request_receipt':copy.deepcopy(art),'geometry_receipt':copy.deepcopy(art),'AX':copy.deepcopy(art)}
        for i,p in enumerate(A.PHASES)}})
    check('schema_native_full_four_phases_valid',not A.schema_errors(ss,session_schema,schema))
    ss['frames']['rest'].pop('AX')
    check('schema_native_missing_AX_rejected',any('missing:AX' in s for s in A.schema_errors(ss,session_schema,schema)))
    ss['platform']='android';ss['frames'].pop('clean-before');ss['frames'].pop('dismiss-after')
    check('schema_android_missing_context_preserved_as_error',any('missing:clean-before' in s for s in A.schema_errors(ss,session_schema,schema)) and not A.phase_gate(ss)['eligible'])
    check('frozen_preparation_files_unchanged',all(A.sha((HERE/name).read_bytes())==expected for name,expected in A.FROZEN.items()))
    result={'status':'SYNTHETIC IMPLEMENTATION CHECKS PASSED' if all(t['passed'] for t in CHECKS) else 'SYNTHETIC CHECK FAILURE',
            'synthetic_checks':CHECKS,'check_count':len(CHECKS),
            'passed_count':sum(t['passed'] for t in CHECKS),
            'real_source_pngs_decoded':0,'real_capture_pngs_decoded':0,
            'synthetic_image_provenance':'All arrays and PNG streams generated in this process; no capture/source PNG paths opened',
            'not_an_experimental_pass':True,'claims_disabled':A.DISABLED}
    save=HERE/'synthetic-results.json'
    A.save(save,result)
    print(json.dumps({'status':result['status'],'passed':result['passed_count'],
        'total':len(CHECKS),'failures':[t for t in CHECKS if not t['passed']],
        'report':str(save)},indent=2))
    return 0 if all(t['passed'] for t in CHECKS) else 1


if __name__=='__main__':
    sys.exit(run())
