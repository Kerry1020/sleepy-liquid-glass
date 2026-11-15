#!/usr/bin/env python3
"""Frozen paired-slope feasibility implementation; not a product optics fit.

CLI accepts one handoff.json, writes a new run under this file's directory.
Import has no file reads or image decodes. Missing/unknown receipt semantics fail
closed. The frozen plan/schema are never modified, and missing phases are never
manufactured. Pure numerical helpers are exercised by synthetic_checks.py.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import time
import zlib

import numpy as np
from PIL import Image, ImageCms

HERE = Path(__file__).resolve().parent
PHASES = ('clean-before', 'rest', 'rest-repeat', 'dismiss-after')
IDS = tuple(f'paired_slope_alert_a{a}_{p}' for a in (20, 24)
            for p in ('normal', 'reversed'))
FROZEN = {
    'analysis-plan.json': 'ee56e7a1ec61b415379a6689c40a412477e26b61a05b8c20dbc1926886a30f21',
    'capture-handoff.schema.json': 'cce44bb099f39069cfe75a235fd1121dbb2f536fb9d3408f5d2f3697518c4952',
    'README.md': 'cd03f4e3ffade226831e8670522e8d768b5a87aa09d774b8943e3ade76a77b93',
}
DISABLED = ['unique_2D_mapping', 'physical_thickness', 'true_blur_source_support',
            'refraction_or_power_fit', 'runtime_parameter_fit_or_product_update',
            'optical_parity_or_99_99_percent']
KERNEL = np.exp(-np.arange(-3, 4, dtype=float)**2 / (2 * 1.5**2))
KERNEL /= KERNEL.sum()
EDGE_SPECS = {
    'left': ((128.25, 186.75), (128, 136), (176, 184)),
    'right': ((188.25, 246.75), (191, 199), (239, 247)),
}
TOP_X = (136.25, 144.25, 152.25, 180.25, 187.25, 194.25,
         222.75, 230.75, 238.75)
CORE = (148.5, 257.5, 226.5, 317.5)
SUPPORTS = {f'core_collar_{k}pt': (CORE[0]-k, CORE[1]-k, CORE[2]+k, CORE[3]+k)
            for k in (0, 2, 8, 24, 60)}
SUPPORTS.update({'old_show-sheet': (126.5, 286, 249, 319.5),
                 'old_show-alert': (130, 345.5, 245, 379),
                 'old_show-menu': (126.5, 405, 249, 438.5),
                 'fixed_left_scan_plateau_union': (128,257.5,187,277.5),
                 'fixed_right_scan_plateau_union': (188,257.5,247,277.5)})


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False,
                                    allow_nan=False) + '\n')


def unique(values):
    return list(dict.fromkeys(values))


def smooth(values):
    return np.convolve(np.pad(values, (3, 3), mode='reflect'), KERNEL, 'valid')


def crossings(coords, values, level):
    """Original half-open crossing rule, both signs and exact ties retained."""
    up, down, equal = [], [], []
    for i, (v, w) in enumerate(zip(values[:-1], values[1:])):
        if v == level and w == level:
            equal.append([float(coords[i]), float(coords[i+1])])
        if v <= level and w > level:
            up.append(float(coords[i] + (level-v)/(w-v)*(coords[i+1]-coords[i])))
        if v >= level and w < level:
            down.append(float(coords[i] + (level-v)/(w-v)*(coords[i+1]-coords[i])))
    return {'increasing': up, 'decreasing': down, 'level_plateau_segments': equal,
            'increasing_count': len(up), 'decreasing_count': len(down)}


def intersects(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def expand(box, amount=2):
    return [box[0]-amount, box[1]-amount, box[2]+amount, box[3]+amount]


def feature_operator(coords, rgb, start_rgb, end_rgb, source_vector,
                     *, clear_support_px=None, foreground_collisions=(),
                     inherited_failures=()):
    """All original 1-D gates; no nearest crossing, ROI adaptation or filling."""
    x = np.asarray(coords, float)
    v = np.asarray(rgb, float)
    p0, p1 = np.asarray(start_rgb, float), np.asarray(end_rgb, float)
    fail = list(inherited_failures)
    result = {'eligible': False, 'failed_gates': fail,
              'inapplicable_2D_gates': {'complete_feature_area_px>=64': 'inapplicable_1D',
                 'contained_contrast_mass>=0.95': 'inapplicable_1D',
                 'source_tensor_eigenvalue_ratio>=0.05': 'inapplicable_1D'},
              'foreground_collisions': list(foreground_collisions)}
    if foreground_collisions:
        fail.append('foreground_support_collision')
    if (len(x) < 7 or v.shape != (len(x), 3) or p0.ndim != 2 or
            p1.ndim != 2 or p0.shape[1:] != (3,) or p1.shape[1:] != (3,) or
            not len(p0) or not len(p1) or not np.isfinite(v).all() or
            not np.isfinite(p0).all() or not np.isfinite(p1).all()):
        fail.append('missing_or_invalid_scan_or_plateau')
        result['failed_gates'] = unique(fail)
        return result
    if not np.allclose(np.diff(x), .5, rtol=0, atol=1e-12):
        fail.append('sample_pitch_not_fixed_0.5pt')
    if clear_support_px is None:
        fail.append('clear_support_unmeasured')
    elif clear_support_px < 12:
        fail.append('clear_support<12px')
    source = None if source_vector is None else np.asarray(source_vector, float)
    if (source is None or source.shape != (3,) or not np.isfinite(source).all()
            or np.linalg.norm(source) == 0):
        fail.append('source_direction_undefined')
        result['failed_gates'] = unique(fail)
        return result
    unit = source / np.linalg.norm(source)
    first, last = np.median(p0, axis=0), np.median(p1, axis=0)
    vec = last-first
    amp = float(vec @ unit)
    cosine = float(amp/np.linalg.norm(vec)) if np.linalg.norm(vec) else 0.0
    spreads = [float(1.4826*np.median(np.abs((p-level)@unit)))
               for p, level in ((p0, first), (p1, last))]
    ranges = [float(np.ptp((p-level)@unit)) for p, level in ((p0, first), (p1, last))]
    q = (v-first)@unit
    qs = smooth(q)
    derivative = np.gradient(qs, .5)
    peaks = [i for i in range(1, len(x)-1) if derivative[i] >= derivative[i-1]
             and derivative[i] > derivative[i+1] and derivative[i] > 0]
    ordered = sorted(peaks, key=lambda i: derivative[i], reverse=True)
    primary = ordered[0] if ordered else None
    secondary = next((i for i in ordered[1:] if abs(i-primary) > 3), None) if primary is not None else None
    ratio = float(derivative[secondary]/derivative[primary]) if secondary is not None else 0.0
    tied = np.flatnonzero(np.isclose(derivative, derivative[primary], rtol=0, atol=1e-9)) if primary is not None else np.array([], int)
    uncertainty = .25 + (float(tied.max()-tied.min())*.25 if len(tied) else 0)
    raw_cs = {str(z): crossings(x, q, amp*z/100) for z in (10, 50, 90)}
    smooth_cs = {str(z): crossings(x, qs, amp*z/100) for z in (10, 50, 90)}
    if amp < 8:
        fail.append('contrast<8')
    for j, spread in enumerate(spreads):
        if amp < 5*max(1., spread):
            fail.append(f'contrast<5x_plateau{j}_spread_floor1')
    if cosine < .7:
        fail.append('source_color_direction_cosine<0.7')
    if primary is None:
        fail.append('positive_derivative_peak_missing')
    if ratio > .8:
        fail.append('secondary_peak>0.8primary')
    crossing_ok = all(len(t['increasing']) == 1 for t in smooth_cs.values())
    if not crossing_ok:
        fail.append('smoothed_increasing_10_50_90_missing_or_nonunique')
    raw_backward = None
    if crossing_ok:
        lower = smooth_cs['10']['increasing'][0]
        upper = smooth_cs['90']['increasing'][0]
        if lower >= upper:
            fail.append('threshold_order_invalid')
        else:
            support = (x >= lower) & (x <= upper)
            steps = np.diff(q[support])
            raw_backward = float(max(0., -steps.min())) if len(steps) else 0.
            if raw_backward > 1:
                fail.append('transition_raw_backward_step>1count')
    if uncertainty > 1:
        fail.append('location_uncertainty>1pt')
    result.update({'source_vector_RGB': source.tolist(), 'source_unit_RGB': unit.tolist(),
        'start_median_RGB': first.tolist(), 'end_median_RGB': last.tolist(),
        'contrast_RGB': vec.tolist(), 'encoded_contrast': amp,
        'source_color_direction_cosine': cosine, 'plateau_robust_spreads': spreads,
        'plateau_projected_ranges': ranges, 'clear_support_px': clear_support_px,
        'peaks': [{'index': i, 'position_pt': float(x[i]), 'height': float(derivative[i])} for i in peaks],
        'primary_peak_index': primary, 'secondary_peak_index': secondary,
        'secondary_to_primary': ratio, 'tied_primary_indices': tied.tolist(),
        'location_uncertainty_pt': uncertainty, 'source_raster_floor_pt': .25,
        'raw_crossings': raw_cs, 'smoothed_crossings': smooth_cs,
        'maximum_raw_backward_step': raw_backward,
        'transect': {'coordinates_pt': x.tolist(), 'projected_raw': q.tolist(),
                     'projected_smoothed': qs.tolist(), 'derivative_per_pt': derivative.tolist()},
        'failed_gates': unique(fail), 'eligible': not fail})
    # Diagnostic candidates stay available even when eligibility fails.
    if len(smooth_cs['50']['increasing']) == 1:
        result['diagnostic_cross50_pt'] = smooth_cs['50']['increasing'][0]
    if not fail:
        result['cross50_pt'] = smooth_cs['50']['increasing'][0]
    return result


def source_rgb(x, y, a, polarity='normal'):
    x, y = np.broadcast_arrays(np.asarray(x, float), np.asarray(y, float))
    u = y-257.5
    inside = ((u >= -64) & (u < 128) & (x >= 187.5-a-.25*u)
              & (x < 187.5+a+.25*u))
    # Generator's normal polarity is dark wedge (60), light exterior (190).
    gray = np.where(inside, 60, 190)
    if polarity == 'reversed':
        gray = 250-gray
    return np.repeat(gray[..., None], 3, axis=-1).astype(np.uint8)


def source_direction(side, polarity):
    sign = (-1 if side == 'left' else 1) * (1 if polarity == 'normal' else -1)
    return np.full(3, 130*sign, float)


def source_line_constant(x, a, polarity):
    y = np.arange(241.75, 273.5, .5)
    rgb = source_rgb(x, y, a, polarity)
    return bool(np.all(rgb == rgb[0]))


def edge_from_image(image, y, side, polarity, foreground=(), inherited_failures=()):
    (lo, hi), p0, p1 = EDGE_SPECS[side]
    x = np.arange(lo, hi+.25, .5)
    row = image[int(y*2), :, :3]
    box = [min(lo-.25, p0[0], p1[0]), y-.25,
           max(hi+.25, p0[1], p1[1]), y+.25]
    collisions = [b for b in foreground if intersects(box, expand(b))]
    coords = (np.arange(image.shape[1])+.5)/2
    return feature_operator(x, row[(x*2).astype(int)],
        row[(coords >= p0[0]) & (coords < p0[1])],
        row[(coords >= p1[0]) & (coords < p1[1])], source_direction(side, polarity),
        clear_support_px=len(x) if not collisions else 0,
        foreground_collisions=collisions, inherited_failures=inherited_failures)


def pair_observables(left, right, a, d, failures=()):
    fail = list(failures)
    for side, feature in (('left', left), ('right', right)):
        if not feature.get('eligible'):
            fail += [f'{side}:{s}' for s in feature.get('failed_gates', ['missing_side'])]
    result = {'eligible': not fail, 'failed_gates': unique(fail),
              'a_pt': float(a), 'd_nominal_AX_pt': float(d),
              'label': 'APPARENT hypothetical local1D nominal-coordinate quantities'}
    if fail:
        return result
    l, r = left['cross50_pt'], right['cross50_pt']
    el, er = left['location_uncertainty_pt'], right['location_uncertainty_pt']
    width, center = r-l, (r+l)/2
    g = (width-2*a)/.5
    result['values'] = {'L50': l, 'R50': r, 'W': width, 'C': center,
                        'g': g, 'U': 187.5-center, 'D': g-d}
    result['bounds'] = {'L50': el, 'R50': er, 'W': el+er, 'C': (el+er)/2,
                        'g': max(1., (el+er)/.5), 'U': (el+er)/2,
                        'D': max(1., (el+er)/.5)}
    return result


def compare_compatible(first, second, quantities, label):
    failures, checks = [], {}
    if not first.get('eligible') or not second.get('eligible'):
        failures.append(label+':missing_independently_eligible_condition')
    else:
        for q in quantities:
            delta = abs(first['values'][q]-second['values'][q])
            bound = first['bounds'][q]+second['bounds'][q]
            checks[q] = {'absolute_difference': delta, 'sum_absolute_bounds': bound,
                         'compatible': delta <= bound}
            if delta > bound:
                failures.append(label+':'+q+'_disagreement')
    return {'eligible': not failures, 'failed_gates': failures, 'checks': checks}


def apply_falsification(rows):
    """Rows keyed (platform, a, polarity, d); preserve pre-falsification values."""
    output = {}
    for key, row in rows.items():
        plat, a, polarity, d = key
        reverse = rows.get((plat, a, 'reversed' if polarity == 'normal' else 'normal', d), {})
        width = rows.get((plat, 24 if a == 20 else 20, polarity, d), {})
        reverse_test = compare_compatible(row, reverse, ('L50', 'R50'), 'reverse')
        width_test = compare_compatible(row, width, ('g', 'U'), 'width')
        failed = unique(row.get('failed_gates', []) + reverse_test['failed_gates'] + width_test['failed_gates'])
        output[key] = {'diagnostic_pre_falsification': row,
            'reverse_test': reverse_test, 'width_test': width_test,
            'eligible': not failed, 'failed_gates': failed}
        if not failed:
            output[key].update({k: row[k] for k in ('values', 'bounds', 'a_pt', 'd_nominal_AX_pt', 'label')})
    # Every preregistered reverse/width condition at the platform/d sample is a
    # requisite local1D check. Keep an individually passing diagnostic, but do
    # not export it as fully eligible if another member of its quartet fails.
    cohorts = {(p,d) for p,a,pol,d in rows}
    for platform,d in cohorts:
        keys = [(platform,a,pol,d) for a in (20,24) for pol in ('normal','reversed')]
        rejected = {f'a{key[1]}_{key[2]}':output[key]['failed_gates'] if key in output else ['condition_missing']
                    for key in keys if key not in output or not output[key]['eligible']}
        if rejected:
            for key in keys:
                if key not in output:
                    continue
                out = output[key]
                out['quartet_failed_conditions'] = rejected
                out['failed_gates'] = unique(out['failed_gates']+['platform_row_reverse_width_quartet_ineligible'])
                out['eligible'] = False
                for field in ('values','bounds'):
                    out.pop(field,None)
    return output


def secants(rows):
    output = []
    for key, center in sorted(rows.items()):
        plat, a, pol, d = key
        minus, plus = rows.get((plat, a, pol, d-4)), rows.get((plat, a, pol, d+4))
        failures = {name: item.get('failed_gates', []) if item else ['outside_fixed_sample_domain']
                    for name, item in (('minus', minus), ('center', center), ('plus', plus))
                    if not item or not item.get('eligible')}
        out = {'platform': plat, 'a_pt': a, 'polarity': pol, 'd_nominal_AX_pt': d,
               'label': 'fixed h4 secants of APPARENT nominal-coordinate g; not true map derivatives',
               'endpoint_and_center_failures': failures, 'g_prime': None, 'g_second': None}
        if minus and plus and minus.get('eligible') and plus.get('eligible'):
            out['g_prime'] = {'value': (plus['values']['g']-minus['values']['g'])/8,
                'absolute_bound': max(.25, (plus['bounds']['g']+minus['bounds']['g'])/8)}
            if center.get('eligible'):
                out['g_second'] = {'value': (plus['values']['g']-2*center['values']['g']+minus['values']['g'])/16,
                    'absolute_bound_per_pt': max(.25, (plus['bounds']['g']+2*center['bounds']['g']+minus['bounds']['g'])/16)}
        output.append(out)
    return output


def top_flatness(features):
    fail = []
    if len(features) != 9:
        fail.append('top50_requires_all9_fixed_lines')
    for i, feature in enumerate(features):
        if not feature.get('eligible'):
            fail += [f'line{i}:{s}' for s in feature.get('failed_gates', ['missing_top_line'])]
    common = None
    if not fail:
        lower = max(f['cross50_pt']-f['location_uncertainty_pt'] for f in features)
        upper = min(f['cross50_pt']+f['location_uncertainty_pt'] for f in features)
        common = [lower, upper]
        if lower > upper:
            fail.append('top50_intervals_no_common_intersection')
    return {'eligible': not fail, 'failed_gates': unique(fail),
            'common_interval_pt': common, 'features': features,
            'limitation': 'operational encoded50 material contour; not geometric silhouette or tangent; b remains257.5'}


def top_from_image(image, a, polarity, foreground=(), material_direction=None,
                   inherited_failures=()):
    """Separate top diagnostic; no direction learned from the output itself."""
    y = np.arange(241.75,273.5,.5)
    yc = (np.arange(image.shape[0])+.5)/2
    items = []
    for x in TOP_X:
        column = image[:,int(x*2),:3]
        box = [x-.25,241.5,x+.25,273.5]
        collisions = [b for b in foreground if intersects(box,expand(b))]
        inherited = list(inherited_failures)
        constant = source_line_constant(x,a,polarity)
        if not constant:
            inherited.append('top_source_line_not_analytically_constant')
        if material_direction is None:
            inherited.append('top_material_direction_not_independently_registered')
        f = feature_operator(y,column[(y*2).astype(int)],
            column[(yc>=241.5)&(yc<247.5)], column[(yc>=267.5)&(yc<273.5)],
            material_direction,clear_support_px=len(y) if not collisions else 0,
            foreground_collisions=collisions,inherited_failures=inherited)
        f.update({'x_pt':x,'source_constant_analytically':constant})
        items.append(f)
    return top_flatness(items)


def analyze_decoded_session(source_id, platform, source_tracks, phase_tracks,
                            foreground_union, provenance_failures=(),
                            material_direction=None):
    """Pure analysis after independently validated raw receipts, no I/O.

    source_tracks maps track name to unchanged original RGBA; phase_tracks maps
    each phase to the same track mapping. Native/Android foreground must already
    be an independently measured union in the common unwarped world. Top50 is
    independent from bilateral observables, but its failure prevents an overall
    experimental pass. Passing edge diagnostics never certifies the top contour.
    """
    a = int(source_id.rsplit('_a',1)[1].split('_')[0])
    polarity = 'reversed' if source_id.endswith('_reversed') else 'normal'
    report = {'platform':platform,'source_id':source_id,'tracks':{},
              'failed_gates':list(provenance_failures),'overall_eligible':False}
    raw_source=source_tracks.get('raw_encoded_RGBA')
    if raw_source is not None and raw_source.shape==(1334,750,4):
        yy,xx=np.indices(raw_source.shape[:2])
        expected_source=source_rgb((xx+.5)/2,(yy+.5)/2,a,polarity)
        report['source_raster']={'raw_RGB_sha256':sha(raw_source[:,:,:3].tobytes()),
            'analytic_RGB_sha256':sha(expected_source.tobytes()),
            'opaque_alpha':bool(np.all(raw_source[:,:,3]==255)),
            'exact_analytic_RGB':bool(np.array_equal(raw_source[:,:,:3],expected_source))}
        if not report['source_raster']['exact_analytic_RGB'] or not report['source_raster']['opaque_alpha']:
            report['failed_gates'].append('original_source_raster_or_alpha_not_exact_analytic_oracle')
    missing = [p for p in PHASES if p not in phase_tracks]
    report['failed_gates'] += ['missing_phase:'+p for p in missing]
    rows = {}
    for track in ('raw_encoded_RGBA','normalized_sRGB_RGBA'):
        inherited = list(report['failed_gates'])
        if track not in source_tracks:
            inherited.append('original_source_track_unavailable:'+track)
        missing_track = [p for p in PHASES if track not in phase_tracks.get(p,{})]
        inherited += ['phase_track_unavailable:'+p+':'+track for p in missing_track]
        tr = {'failed_gates':unique(inherited),'source_checks':[],
              'context_differences':{},'repeat':None,'rows':[], 'top50':None}
        report['tracks'][track] = tr
        if missing or missing_track or track not in source_tracks:
            continue
        ims = {phase:phase_tracks[phase][track] for phase in PHASES}
        source = source_tracks[track]
        if any(im.shape != (1334,750,4) for im in [source,*ims.values()]):
            tr['failed_gates'].append('decoded_geometry_not_750x1334_RGBA')
            continue
        tr['repeat'] = difference(ims['rest'],ims['rest-repeat'])
        if not tr['repeat']['strict_zero']:
            tr['failed_gates'].append('nonzero_full_REST_repeat_RGBA')
        for phase in ('clean-before','dismiss-after'):
            for name,box in SUPPORTS.items():
                delta = difference(ims[phase],source,box)
                tr['source_checks'].append({'phase':phase,'region':name,'ltrb_pt':list(box),**delta})
                if not delta['strict_zero']:
                    tr['failed_gates'].append('source_region_nonexact:'+phase+':'+name)
        tr['context_differences'] = {
            'before_vs_after_FULL':difference(ims['clean-before'],ims['dismiss-after']),
            'before_vs_source_FULL':difference(ims['clean-before'],source),
            'after_vs_source_FULL':difference(ims['dismiss-after'],source)}
        tr['source_exactness_limitation'] = 'No named region/collar bounds native blur source support'
        if foreground_union is None:
            tr['failed_gates'].append('independently_measured_cross_platform_foreground_union_missing')
        tr['failed_gates'] = unique(tr['failed_gates'])
        for d in np.arange(.25,20,.5):
            y = 257.5+float(d)
            sides = {side:edge_from_image(ims['rest'],y,side,polarity,
                foreground_union or [],tr['failed_gates']) for side in ('left','right')}
            apparent = pair_observables(sides['left'],sides['right'],a,float(d))
            item = {'d_nominal_AX_pt':float(d),'y_pt':y,'sides':sides,'apparent':apparent}
            tr['rows'].append(item)
            rows[(track,platform,a,polarity,float(d))] = apparent
        tr['top50'] = top_from_image(ims['rest'],a,polarity,foreground_union or [],material_direction,
                                   tr['failed_gates'])
        if not tr['top50']['eligible']:
            tr['failed_gates'].append('top50_unavailable_or_nonflat')
    report['overall_eligible'] = all(not tr['failed_gates'] for tr in report['tracks'].values())
    return report,rows


def platform_residuals(final_rows):
    """Descriptive residuals only; no optical parity threshold or parameter fit."""
    out = []
    keys = sorted({(a,p,d) for _,a,p,d in final_rows})
    for a,p,d in keys:
        native,android = final_rows.get(('native',a,p,d)), final_rows.get(('android',a,p,d))
        record = {'a_pt':a,'polarity':p,'d_nominal_AX_pt':d,'residuals':None,
                  'label':'Android minus native; descriptive only; no parity threshold'}
        failed = {name:(item or {}).get('failed_gates',['condition_missing'])
                  for name,item in (('native',native),('android',android))
                  if not item or not item.get('eligible')}
        record['failed_conditions'] = failed
        if not failed:
            record['residuals'] = {q:{'difference':android['values'][q]-native['values'][q],
                'sum_absolute_bounds':android['bounds'][q]+native['bounds'][q]}
                for q in ('L50','R50','W','C','g','U','D')}
        out.append(record)
    return out


def top_across_conditions(session_reports, track):
    """Report all fixed-line source/reverse differences; never reanchor b."""
    results = []
    keyed = {(r['platform'],r['source_id']):r['tracks'].get(track,{}).get('top50')
             for r in session_reports}
    for platform in ('native','android'):
        for i,first_id in enumerate(IDS):
            for second_id in IDS[i+1:]:
                first,second = keyed.get((platform,first_id)),keyed.get((platform,second_id))
                row = {'platform':platform,'source_ids':[first_id,second_id],
                       'b_fixed_nominal_AX_pt':257.5,'differences':None}
                if first and second and first.get('eligible') and second.get('eligible'):
                    row['differences'] = [{'x_pt':x,'second_minus_first_pt':b['cross50_pt']-a['cross50_pt'],
                        'sum_absolute_bounds_pt':a['location_uncertainty_pt']+b['location_uncertainty_pt']}
                        for x,a,b in zip(TOP_X,first['features'],second['features'])]
                    row['failed_gates'] = []
                else:
                    row['failed_gates'] = ['top50_unavailable_or_nonflat_in_condition_pair']
                results.append(row)
    return results


def analyze_decoded_matrix(sessions):
    """Pure matrix composition, called only after a frozen receipt adapter.

    A session item contains source_id/platform/source_tracks/phase_tracks/
    foreground_union/provenance_failures/material_direction, already extracted
    from raw evidence. No such contract is present in the original handoff, so
    execute() deliberately never calls this function on unreviewed payloads.
    """
    reports,rows = [],{}
    failed = []
    counts = Counter((s['platform'],s['source_id']) for s in sessions)
    expected = {(p,s) for p in ('native','android') for s in IDS}
    if set(counts) != expected or any(n!=1 for n in counts.values()):
        failed.append('matrix_not_exact_eight_source_platform_sessions')
    for session in sessions:
        report,local = analyze_decoded_session(**session)
        reports.append(report)
        for key,value in local.items():
            if key in rows:
                failed.append('duplicate_decoded_matrix_condition')
            rows[key]=value
    output = {'status':'INSUFFICIENT EVIDENCE — NOT PASSED','failed_gates':unique(failed),
              'sessions':reports,'tracks':{},'claims_disabled':DISABLED}
    for track in ('raw_encoded_RGBA','normalized_sRGB_RGBA'):
        chosen = {key[1:]:value for key,value in rows.items() if key[0]==track}
        final = apply_falsification(chosen)
        serialized = [{'platform':key[0],'a_pt':key[1],'polarity':key[2],
                       'd_nominal_AX_pt':key[3],**value} for key,value in sorted(final.items())]
        output['tracks'][track] = {'rows':serialized,'h4_secants':secants(final),
            'platform_residuals':platform_residuals(final),
            'top50_across_conditions':top_across_conditions(reports,track)}
        if len(final)!=320 or not all(r['eligible'] for r in final.values()):
            output['failed_gates'].append(track+':paired_edge_or_reverse_width_ineligible')
    if not all(r['overall_eligible'] for r in reports) or len(reports)!=8:
        output['failed_gates'].append('one_or_more_session_or_top50_gates_ineligible')
    if not output['failed_gates']:
        output['status']='APPARENT1D FEASIBILITY GATES COMPATIBLE — NO OPTICAL PARITY OR PHYSICAL CLAIM'
    return output


def difference(a, b, box=None):
    if a.shape != b.shape:
        return {'strict_zero': False, 'failed_gates': ['image_geometry_mismatch']}
    if box:
        yy, xx = np.indices(a.shape[:2])
        selected = ((xx+.5)/2 >= box[0]) & ((xx+.5)/2 < box[2]) & ((yy+.5)/2 >= box[1]) & ((yy+.5)/2 < box[3])
        a, b = a[selected], b[selected]
    else:
        a, b = a.reshape(-1, a.shape[-1]), b.reshape(-1, b.shape[-1])
    delta = np.abs(a.astype(np.int16)-b.astype(np.int16))
    changed = np.any(delta != 0, axis=1)
    return {'pixels': len(a), 'changed_pixels': int(changed.sum()),
            'maximum_channel_difference': int(delta.max()) if delta.size else 0,
            'mean_absolute_channel_difference': float(delta.mean()) if delta.size else 0,
            'changed_by_channel': (delta != 0).sum(axis=0).tolist(),
            'strict_zero': bool(not changed.any())}


def parse_png(data, expected_size=(750, 1334)):
    """Validate original bytes/chunks/CRCs before a decoder sees the stream."""
    fail, chunks, payloads = [], [], {}
    info = {'original_sha256': sha(data), 'chunks': chunks, 'failed_gates': fail,
            'structurally_valid': False, 'normalization': 'unresolved',
            'color_reference': 'W3C PNG Third Edition §4.3/Table1 and §11.3.2.3/5/6'}
    if not data.startswith(b'\x89PNG\r\n\x1a\n'):
        fail.append('PNG_signature_invalid')
        return info
    offset, ended = 8, False
    while offset < len(data):
        if len(data)-offset < 12:
            fail.append('PNG_truncated_chunk_header'); break
        size = struct.unpack('>I', data[offset:offset+4])[0]
        if size > 0x7fffffff or offset+12+size > len(data):
            fail.append('PNG_chunk_bounds_invalid'); break
        kind = data[offset+4:offset+8]
        value = data[offset+8:offset+8+size]
        crc = struct.unpack('>I', data[offset+8+size:offset+12+size])[0]
        valid = (zlib.crc32(kind+value) & 0xffffffff) == crc
        name = kind.decode('ascii', 'replace')
        chunks.append({'kind': name, 'length': size, 'offset': offset, 'crc_valid': valid,
                       'payload_sha256': sha(value),
                       **({'data_hex': value.hex()} if size <= 64 else {})})
        payloads.setdefault(name, []).append(value)
        if not valid:
            fail.append('PNG_CRC_invalid:'+name)
        if len(kind) != 4 or not all(65 <= b <= 90 or 97 <= b <= 122 for b in kind) or kind[2] & 32:
            fail.append('PNG_chunk_type_invalid:'+name)
        if not (kind[0] & 32) and name not in ('IHDR', 'PLTE', 'IDAT', 'IEND'):
            fail.append('PNG_unknown_critical_chunk:'+name)
        offset += size+12
        if name == 'IEND':
            ended = True
            if size:
                fail.append('PNG_IEND_payload_nonempty')
            if offset != len(data):
                fail.append('PNG_bytes_after_IEND')
            break
    names = [c['kind'] for c in chunks]
    unique_chunks = ('IHDR','PLTE','IEND','cICP','iCCP','sRGB','cHRM','gAMA','tRNS','bKGD','hIST','pHYs','tIME','eXIf','sBIT')
    for name in unique_chunks:
        if len(payloads.get(name, [])) > 1:
            fail.append('PNG_duplicate_chunk:'+name)
    if not names or names[0] != 'IHDR' or len(payloads.get('IHDR', [])) != 1:
        fail.append('PNG_IHDR_not_first_unique')
    if not ended:
        fail.append('PNG_IEND_missing')
    if 'IDAT' not in names:
        fail.append('PNG_IDAT_missing')
    else:
        first_idat = names.index('IDAT')
        idat_indices = [i for i, n in enumerate(names) if n == 'IDAT']
        if idat_indices != list(range(idat_indices[0], idat_indices[-1]+1)):
            fail.append('PNG_IDAT_not_consecutive')
        for name in ('PLTE','cICP','iCCP','sRGB','cHRM','gAMA','tRNS','sBIT'):
            if name in names and names.index(name) > first_idat:
                fail.append('PNG_chunk_after_IDAT:'+name)
        if 'PLTE' in names:
            for name in ('cICP','iCCP','sRGB','cHRM','gAMA','sBIT'):
                if name in names and names.index(name) > names.index('PLTE'):
                    fail.append('PNG_color_chunk_after_PLTE:'+name)
    if any(name in names for name in ('acTL','fcTL','fdAT')):
        fail.append('PNG_animation_not_fixed_primary_still')
    ihdr = payloads.get('IHDR', [b''])[0]
    if len(ihdr) == 13:
        w, h, bits, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', ihdr)
        info['IHDR'] = {'width': w, 'height': h, 'bit_depth': bits, 'color_type': color,
                        'compression': compression, 'filter': filtering, 'interlace': interlace}
        if (w,h) != tuple(expected_size):
            fail.append('PNG_dimensions_not_fixed')
        if bits != 8 or color not in (2,6) or compression != 0 or filtering != 0 or interlace not in (0,1):
            fail.append('PNG_IHDR_not_supported_RGB_RGBA8')
        trns = payloads.get('tRNS', [])
        info['alpha_declaration'] = 'RGBA_channel' if color == 6 else ('tRNS_RGB_key' if trns else 'RGB_opaque')
        if trns and (color == 6 or len(trns[0]) != 6):
            fail.append('PNG_alpha_transparency_declaration_invalid')
        if trns and color == 2 and len(trns[0]) == 6 and max(struct.unpack('>HHH', trns[0])) > 255:
            fail.append('PNG_tRNS_RGB8_key_out_of_range')
        if 'PLTE' in payloads and (not len(payloads['PLTE'][0]) or len(payloads['PLTE'][0])%3 or len(payloads['PLTE'][0])>768):
            fail.append('PNG_PLTE_length_invalid')
    else:
        fail.append('PNG_IHDR_length_invalid')
    info['structurally_valid'] = not fail
    info['lower_priority_color_chunks'] = [n for n in ('cICP','iCCP','sRGB','cHRM','gAMA') if n in names]
    info['iCCP_sRGB_cooccurrence'] = 'iCCP' in names and 'sRGB' in names
    color_fail = []
    info['color_failed_gates'] = color_fail
    # Invalid higher priority declarations do not authorize fallback.
    if 'cICP' in payloads:
        cicp = payloads['cICP'][0]
        info['color_authority'] = 'cICP'
        if len(cicp) == 4 and tuple(cicp) == (1,13,0,1):
            info['normalization'] = 'identity_explicit_sRGB_cICP'
        else:
            color_fail.append('unsupported_or_invalid_high_priority_cICP')
    elif 'iCCP' in payloads:
        info['color_authority'] = 'iCCP'
        try:
            value = payloads['iCCP'][0]
            sep = value.index(0)
            if not 1 <= sep <= 79 or value[sep+1] != 0:
                raise ValueError('profile name/compression invalid')
            decoder = zlib.decompressobj()
            profile = decoder.decompress(value[sep+2:], 16*1024*1024+1)
            if len(profile) > 16*1024*1024 or not decoder.eof or decoder.unused_data:
                raise ValueError('profile compression bounds invalid')
            if len(profile) < 128 or struct.unpack('>I', profile[:4])[0] != len(profile) or profile[16:20] != b'RGB ' or profile[36:40] != b'acsp':
                raise ValueError('not a complete RGB ICC profile')
            intent = struct.unpack('>I', profile[64:68])[0]
            if intent not in range(4):
                raise ValueError('invalid profile rendering intent')
            ImageCms.ImageCmsProfile(io.BytesIO(profile))
            info.update({'normalization': 'ICC_to_sRGB', 'icc_sha256': sha(profile),
                         'icc_rendering_intent': intent,
                         'icc_intent_bytes_sha256': sha(profile[64:68])})
        except Exception as exc:
            color_fail.append('invalid_or_unsupported_RGB_ICC:'+str(exc))
    elif 'sRGB' in payloads:
        info['color_authority'] = 'sRGB'
        value = payloads['sRGB'][0]
        if len(value) == 1 and value[0] in range(4):
            info.update({'normalization': 'identity_explicit_sRGB', 'sRGB_intent': value[0],
                         'sRGB_intent_sha256': sha(value)})
        else:
            color_fail.append('invalid_sRGB_rendering_intent')
    else:
        info['color_authority'] = 'cHRM+gAMA' if 'cHRM' in names or 'gAMA' in names else 'unmarked'
        color_fail.append('no_supported_explicit_color_provenance')
    for name, size in (('gAMA',4), ('cHRM',32), ('sRGB',1), ('cICP',4)):
        if name in payloads and len(payloads[name][0]) != size:
            color_fail.append('color_chunk_length_invalid:'+name)
    if 'gAMA' in payloads and len(payloads['gAMA'][0]) == 4 and struct.unpack('>I', payloads['gAMA'][0])[0] == 0:
        color_fail.append('gAMA_zero_invalid')
    if 'sRGB' in payloads and (len(payloads['sRGB'][0]) != 1 or payloads['sRGB'][0][0] not in range(4)):
        color_fail.append('lower_or_primary_sRGB_invalid')
    if 'sRGB' in payloads and 'gAMA' in payloads and len(payloads['gAMA'][0]) == 4:
        info['sRGB_gAMA_conflict'] = struct.unpack('>I', payloads['gAMA'][0])[0] != 45455
    if 'sRGB' in payloads and 'cHRM' in payloads and len(payloads['cHRM'][0]) == 32:
        info['sRGB_cHRM_conflict'] = struct.unpack('>8I',payloads['cHRM'][0]) != (31270,32900,64000,33000,30000,60000,15000,6000)
    if info.get('sRGB_gAMA_conflict') or info.get('sRGB_cHRM_conflict'):
        color_fail.append('conflicting_color_declarations')
    if color_fail or not info['structurally_valid']:
        info['normalization'] = 'unresolved'
    return info


def decode_png(data, expected_size=(750,1334)):
    metadata = parse_png(data, expected_size)
    tracks = {}
    if not metadata['structurally_valid']:
        return tracks, metadata
    try:
        image = Image.open(io.BytesIO(data))
        image.load()
        raw = np.asarray(image.convert('RGBA'))
        tracks['raw_encoded_RGBA'] = raw
        normalization = metadata['normalization']
        if normalization.startswith('identity_explicit_sRGB'):
            tracks['normalized_sRGB_RGBA'] = raw.copy()
        elif normalization == 'ICC_to_sRGB':
            profile = ImageCms.ImageCmsProfile(io.BytesIO(image.info['icc_profile']))
            target = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB'))
            metadata['normalization_target_profile_sha256'] = sha(target.tobytes())
            rgb = ImageCms.profileToProfile(image.convert('RGB'), profile,
                target, renderingIntent=metadata['icc_rendering_intent'], outputMode='RGB')
            normalized = raw.copy()
            normalized[:,:,:3] = np.asarray(rgb)
            tracks['normalized_sRGB_RGBA'] = normalized
        metadata['decoded_track_sha256'] = {k: sha(v.tobytes()) for k,v in tracks.items()}
        metadata['decoded_alpha_nonopaque_pixels'] = int(np.sum(raw[:,:,3] != 255))
    except Exception as exc:
        metadata['failed_gates'].append('PNG_decode_or_ICC_conversion_failed:'+str(exc))
        metadata['normalization'] = 'unresolved'
    return tracks, metadata


def schema_errors(value, schema, root=None, path='$'):
    """Dependency-free evaluator for every keyword used in the frozen schema."""
    root = schema if root is None else root
    errors = []
    if '$ref' in schema:
        target = root
        for part in schema['$ref'].split('/')[1:]:
            target = target[part]
        return schema_errors(value, target, root, path)
    if 'const' in schema and value != schema['const']:
        errors.append(path+':const')
    if 'enum' in schema and value not in schema['enum']:
        errors.append(path+':enum')
    kind = schema.get('type')
    types = {'object':dict,'array':list,'string':str,'number':(int,float)}
    if kind and (not isinstance(value, types[kind]) or kind == 'number' and isinstance(value,bool)):
        return errors+[path+':type='+kind]
    if isinstance(value, dict):
        for key in schema.get('required', []):
            if key not in value:
                errors.append(path+':missing:'+key)
        props = schema.get('properties', {})
        if schema.get('additionalProperties') is False:
            errors += [path+':unexpected:'+key for key in value if key not in props]
        for key, sub in props.items():
            if key in value:
                errors += schema_errors(value[key], sub, root, path+'.'+key)
    if isinstance(value, list):
        if len(value) < schema.get('minItems',0): errors.append(path+':minItems')
        if len(value) > schema.get('maxItems',float('inf')): errors.append(path+':maxItems')
        if schema.get('uniqueItems') and len({json.dumps(v,sort_keys=True) for v in value}) != len(value): errors.append(path+':uniqueItems')
        for i, item in enumerate(value):
            errors += schema_errors(item, schema.get('items',{}), root, path+f'[{i}]')
    if isinstance(value, str) and 'pattern' in schema:
        import re
        if not re.search(schema['pattern'],value): errors.append(path+':pattern')
    for sub in schema.get('allOf', []):
        if 'if' in sub:
            branch = 'then' if not schema_errors(value,sub['if'],root,path) else 'else'
            errors += schema_errors(value,sub.get(branch,{}),root,path)
        else:
            errors += schema_errors(value,sub,root,path)
    return errors


def artifact_records(value, path='$'):
    if isinstance(value, dict):
        if set(value) == {'path','sha256'}:
            yield path, value
        else:
            for key, item in value.items():
                yield from artifact_records(item,path+'.'+key)
    elif isinstance(value,list):
        for i,item in enumerate(value):
            yield from artifact_records(item,path+f'[{i}]')


def phase_gate(session):
    frames = session.get('frames', {})
    missing = [p for p in PHASES if p not in frames]
    fail = ['missing_phase:'+p for p in missing]
    if session.get('platform') == 'native':
        fail += ['missing_native_AX:'+p for p in PHASES if p in frames and 'AX' not in frames[p]]
    if session.get('platform') == 'android':
        fail += ['missing_android_layout:'+p for p in PHASES if p in frames and 'layout_receipt' not in frames[p]]
    ts = [frames.get(p,{}).get('captured_at_unix_seconds') for p in PHASES]
    if all(isinstance(t,(float,int)) and not isinstance(t,bool) and np.isfinite(t) for t in ts):
        if not all(b>a for a,b in zip(ts,ts[1:])):
            fail.append('phase_chronology_not_strict')
        if ts[2]-ts[1] < .25:
            fail.append('rest_repeat_spacing<0.25seconds')
    else:
        fail.append('phase_time_missing_or_invalid')
    return {'eligible':not fail,'failed_gates':fail,'missing_phases':missing,
            'never_synthesized':True,'captured_times':ts}


def provenance_gate(session):
    """Payload contracts absent from frozen schema cannot become measured facts.

    All referenced raw receipts are hashed and preserved by execute(). A future
    independently frozen receipt adapter is required to interpret them. Booleans
    in an adapter are never substitutes for measured AX/layout/mapping/traits,
    request/session/trace timestamps and binary/source linkage.
    """
    fail = ['unregistered_raw_receipt_payload_contract:'+name for name in (
        'session_request_source_loader_binary_linkage', 'traits',
        'canvas_identity_mapping', 'cross_platform_foreground_union',
        'phase_geometry_AX_or_attached_layout')]
    return {'eligible':False,'failed_gates':fail,'raw_artifacts_retained':True,
            'requires_separate_frozen_adapter':True}


def execute(handoff_path):
    # The only filesystem-reading execution entry point. No other input path CLI.
    handoff_path = Path(handoff_path).resolve()
    if handoff_path.name != 'handoff.json':
        raise ValueError('Only the registered handoff.json is accepted')
    run = HERE/'runs'/f'{time.time_ns()}'
    run.mkdir(parents=True,exist_ok=False)
    failure, hashes = [], {}
    for name, expected in FROZEN.items():
        actual = sha((HERE/name).read_bytes())
        hashes[str(HERE/name)] = actual
        if actual != expected:
            failure.append('frozen_preparation_changed:'+name)
    plan = json.loads((HERE/'analysis-plan.json').read_text())
    schema = json.loads((HERE/'capture-handoff.schema.json').read_text())
    data = handoff_path.read_bytes()
    handoff = json.loads(data)
    hashes[str(handoff_path)] = sha(data)
    errors = schema_errors(handoff,schema)
    for label, art in artifact_records(handoff):
        try:
            actual = sha(Path(art['path']).read_bytes())
            hashes[art['path']] = actual
            if actual != art['sha256']:
                failure.append(label+':artifact_hash_mismatch')
        except (OSError,ValueError) as exc:
            failure.append(label+':artifact_unavailable:'+str(exc))
    # Verify every frozen source and original oracle before first pixel decode.
    for sid, spec in plan['source_pngs'].items():
        try:
            actual = sha(Path(spec['path']).read_bytes())
            hashes[spec['path']] = actual
            if actual != spec['sha256']: failure.append('original_source_hash_changed:'+sid)
        except OSError: failure.append('original_source_unavailable:'+sid)
    for path, expected in plan['provenance'].items():
        try:
            actual = sha(Path(path).read_bytes()); hashes[path] = actual
            if actual != expected: failure.append('frozen_provenance_changed:'+path)
        except OSError: failure.append('frozen_provenance_unavailable:'+path)
    if set(handoff.get('selected_ids',[])) != set(IDS):
        failure.append('selected_sources_not_exact_four')
    sessions = handoff.get('sessions',[])
    counts = Counter((s.get('platform'),s.get('source_id')) for s in sessions)
    expected = {(p,s) for p in ('native','android') for s in IDS}
    if set(counts) != expected or any(n != 1 for n in counts.values()):
        failure.append('platform_source_matrix_not_exact_once')
    oracle_art = handoff.get('oracle',{})
    oracle_hash = next(v for k,v in plan['provenance'].items() if k.endswith('/oracle.json'))
    if oracle_art.get('sha256') != oracle_hash:
        failure.append('handoff_oracle_not_frozen_original')
    for s in sessions:
        spec = plan['source_pngs'].get(s.get('source_id'),{})
        if s.get('source_original',{}).get('sha256') != spec.get('sha256'):
            failure.append('session_source_not_frozen_original:'+str(s.get('source_id')))
    save(run/'before-first-decode.json',{'handoff_sha256':sha(data),
        'all_artifact_original_hashes':hashes,'schema_errors':errors,
        'predecode_failures':unique(failure),'pixel_decodes_so_far':0,
        'policy':'All hashes before decode; neutral compatibility never decoded or scored'})
    # A schema error (including Android missing before/after) is a complete
    # insufficient-evidence outcome; never read a convenient substitute image.
    report = {'status':'INSUFFICIENT EVIDENCE — NOT PASSED','schema_errors':errors,
              'failed_gates':unique(failure),'sessions':[], 'real_pngs_decoded':0,
              'claims_disabled':DISABLED,'plan_sha256':hashes[str(HERE/'analysis-plan.json')]}
    for session in sessions:
        report['sessions'].append({'platform':session.get('platform'),
            'source_id':session.get('source_id'),'phases':phase_gate(session),
            'provenance':provenance_gate(session)})
    if errors or failure:
        report['failed_gates'] += ['handoff_schema_or_predecode_integrity_failed']
        save(run/'decision.json',report)
        return report,run
    # No unregistered receipt interpretation: do not turn mere valid file hashes
    # into permission for optical decoding. A future supplemental adapter must
    # be frozen and reviewed before this conservative boundary is changed.
    report['failed_gates'].append('receipt_semantics_unresolved_before_real_decode')
    save(run/'decision.json',report)
    return report,run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('handoff_json', metavar='handoff.json')
    args = parser.parse_args()
    report, run = execute(args.handoff_json)
    print(json.dumps({'status':report['status'],'output_directory':str(run),
                      'real_pngs_decoded':report['real_pngs_decoded']},indent=2))
    return 2 if report['status'].startswith('INSUFFICIENT') else 0


if __name__ == '__main__':
    sys.exit(main())
