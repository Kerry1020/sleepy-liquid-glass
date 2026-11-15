#!/usr/bin/env python3
"""Frozen offline G finite-difference analysis; never registers or modifies captures.

Run independently per platform. Mismatched observed bounds block subtraction;
unknown opacity permits labeled pixel diagnostics but blocks mapping acceptance.
A paired index
may carry pairing_geometry and flat_pairing_geometry (see PROTOCOL.md) when the
actual observation is unavailable through a native strict endpoint receipt.
"""
from __future__ import annotations
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
STAGES = ['ingress01', 'ingress10', 'ingress50', 'ingress75', 'full100', 'far50']
THRESHOLDS = [4, 8, 16, 24]
ROI = [165.5, 397.5, 209.5, 441.5]
SHA = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def resolve(path, parent):
    p = Path(path)
    return p if p.is_absolute() else Path(parent) / p


def require(condition, message):
    if not condition:
        raise ValueError(message)


def array(value, shape=None):
    a = np.asarray(value, dtype=float)
    require(np.isfinite(a).all(), 'nonfinite geometry')
    if shape is not None:
        require(a.shape == shape, f'geometry shape {a.shape} != {shape}')
    return a


def hashed(path, expected):
    require(expected and SHA(path) == expected, f'hash mismatch or missing hash: {path}')


def png(path, expected):
    hashed(path, expected)
    with Image.open(path) as im:
        require(im.mode in ['RGB', 'RGBA'], f'expected original RGB8 or opaque RGBA8 image, got {im.mode}: {path}')
        raw = np.array(im, dtype=np.uint8)
        if im.mode == 'RGBA':
            require(np.all(raw[...,3] == 255), f'nonopaque capture alpha has no registered compositing model: {path}')
        return raw[...,:3]


def verify_assets():
    verified = read(HERE / 'asset-verification.json')
    require(verified['status'] == 'passed', 'source assets did not pass')
    rounds = {}
    for packet in verified['packets']:
        role = packet['role']
        for key, digest in [('spec', 'spec_sha256'), ('manifest', 'manifest_sha256'), ('source_png', 'source_sha256')]:
            hashed(packet[key], packet[digest])
        spec = read(packet['spec'])
        manifest = read(packet['manifest'])
        require(spec['flat_input_id'] == 'st00_flat128', 'ordinary flat was relabeled')
        for entry in manifest['inputs']:
            hashed(Path(packet['manifest']).parent / entry['file'], entry['sha256'])
        main_id = spec['first_input_id']
        main = next(v for v in spec['inputs'] if v['id'] == main_id)
        rounds[role] = {**packet, 'spec_value': spec, 'main_id': main_id,
                        'manifest_value': manifest, 'main_sha256': main['source_sha256']}
    w = png(rounds['witness']['source_png'], rounds['witness']['source_sha256'])
    c = png(rounds['control']['source_png'], rounds['control']['source_sha256'])
    require(np.array_equal(w[..., [0, 2]], c[..., [0, 2]]), 'R/B source equality broken')
    require(np.all(c[..., 1] == 128) and np.all(w[..., 1] >= 128), 'unexpected G stimulus')
    return rounds


def native_observation(index, capture, flat, role, index_parent):
    receipt_path = resolve(capture.get('receipt_json', index.get('strict_verification_json', '')), index_parent)
    receipt = read(receipt_path)
    require(receipt.get('status') == 'passed' and not receipt.get('errors'), 'native strict verifier did not pass')
    require(receipt.get('captures') == receipt.get('verifiedHeldEndpoints') == 12, 'native strict receipt must verify 12 endpoints')
    require(receipt.get('verifiedShapeFlatPairs') == 6, 'native strict receipt must verify six pairs')
    require(receipt.get('specSHA256') == role['spec_sha256'], 'native strict receipt spec hash mismatch')
    require(receipt.get('manifestSHA256') == role['manifest_sha256'], 'native strict receipt manifest hash mismatch')
    expected_sha = capture['flat_sha256' if flat else 'sha256']
    matches = [o for o in receipt.get('observations', []) if o.get('imageSHA256') == expected_sha]
    require(len(matches) == 1, 'capture not uniquely bound to native strict receipt')
    o = matches[0]
    require(o.get('verifiedHeldEndpoint') is True and not o.get('errors'), 'native endpoint not verified')
    event = o['event']
    require(event['coverageStageID'] == capture['stage_id'], 'native stage binding mismatch')
    require(bool(event['isFlatControl']) == flat, 'native flat binding mismatch')
    expected_input = 'st00_flat128' if flat else role['main_id']
    require(event['inputID'] == expected_input, 'native input binding mismatch')
    source = o['externalInput']
    source_hash = next(e['sha256'] for e in role['manifest_value']['inputs'] if e['id'] == expected_input)
    require(source['sha256'] == source_hash, 'delivered native source hash mismatch')
    require(source.get('colorSpace') == 'sRGB' and source.get('worldSizePt') == [375, 667], 'native source declaration mismatch')
    canvas = source['canvasRectInWindowPt']
    require([canvas[k] for k in ['x', 'y', 'w', 'h']] == [0, 0, 375, 667], 'native actual canvas mapping differs')
    require(source.get('worldOriginPt') == [0, 0], 'native actual source origin differs')
    size = array(source['sizePx'], (2,))
    samples = o.get('presentedPoseSamples', [])
    require(len(samples) >= 4 and o['carrierPoseStability']['stable'], 'native observed carrier stability missing')
    carriers = [s['carrier'] for s in samples]
    require(all(v.get('presentationAvailable') and not v.get('effectiveHidden') for v in carriers), 'native presentation unavailable or hidden')
    matrices = [[v[k] for k in ['m11', 'm12', 'm21', 'm22', 'm41', 'm42']] for v in carriers]
    opacities = [v['effectiveOpacity'] for v in carriers]
    output_scale = float(o['session']['screenScale'])
    return {'carrier_bounds': array(o['actualCarrierBoundsPt'], (4,)),
            'matrix_samples': array(matrices), 'opacity_samples': array(opacities),
            'source_origin': array([canvas['x'], canvas['y']]),
            'source_sampling_matrix': array([[size[0]/375, 0], [0, size[1]/667]]),
            'actual_output_mapping':{'scale':output_scale,'origin':np.array([canvas['x'],canvas['y']])*output_scale,
                                     'dimensions_px':[int(round(o['session']['screenWidthPt']*output_scale)),int(round(o['session']['screenHeightPt']*output_scale))]},
            'evidence': {'path': str(receipt_path), 'sha256': SHA(receipt_path),
                         'scope': 'strict observed carrier presentation and actual external source canvas; source matrix maps world points to original source pixels'}}


def explicit_geometry(capture, flat, index_parent):
    key = 'flat_pairing_geometry' if flat else 'pairing_geometry'
    g = capture.get(key)
    require(g is not None, f'missing actual {key}; no transform/opacity inference allowed')
    evidence = g.get('evidence', [])
    require(evidence, 'actual pairing geometry has no hash-bound observation evidence')
    for e in evidence:
        hashed(resolve(e['path'], index_parent), e['sha256'])
    require(g.get('observed') is True, 'pairing geometry must identify actual observation')
    return {'carrier_bounds': array(g['carrier_bounds_world_xywh'], (4,)),
            'matrix_samples': array(g['presentation_matrix_samples']),
            'opacity_samples': None if g.get('effective_opacity_samples') is None else array(g['effective_opacity_samples']),
            'source_origin': array(g['actual_source_origin_world_xy'], (2,)),
            'source_sampling_matrix': array(g['actual_source_world_to_source_pixel_matrix'], (2, 2)),
            'actual_output_mapping':{'scale':float(g['actual_screenshot_pixels_per_world_unit']),
                                     'origin':array(g['actual_world_origin_in_screenshot_px'],(2,)),
                                     'dimensions_px':g['actual_screenshot_dimensions_px']},
            'evidence': evidence}


def android_geometry(capture, flat, index_parent):
    """Read actual transformed corners, owner and source from held acquisition."""
    if capture.get('flat_pairing_geometry' if flat else 'pairing_geometry'):
        return explicit_geometry(capture, flat, index_parent)
    path = resolve(capture['android_evidence_json'], index_parent)
    r = read(path)
    input_id = 'st00_flat128' if flat else capture['input_id']
    scene = input_id + '-light-' + capture['stage_id']
    observations = [o for o in r['geometry_observations'] if o.get('scene') == scene and o.get('phase') == 'held']
    require(len(observations) == 1, 'expected unique Android held geometry observation')
    g = observations[0]['geometry']; carrier = g['affine_visual_carrier']; owner = g['isotropic_thumb_owner']
    source = g['background_world']['source']; density = float(carrier['density'])
    cb = array(carrier['local_to_screen_unit_basis_px'], (3, 2)); ob = array(owner['screen_origin_px'], (2,))
    sb = array(source['local_to_screen_unit_basis_px'], (3, 2))
    corners = carrier['local_to_screen_corners_px']; require(len(corners) == 4, 'all transformed Android corners required')
    for corner in corners:
        local = array(corner['local_px'], (2,)); actual = array(corner['screen_px'], (2,))
        predicted = cb[0] + local[0]*(cb[1]-cb[0]) + local[1]*(cb[2]-cb[0])
        # Serialized one-pixel unit bases lose precision when projected 171px.
        require(np.max(np.abs(predicted-actual)) <= .05, 'Android four corners do not agree with observed local affine basis')
    rect = array(g['visual_carrier_world_rect_dp'], (4,))
    bounds = np.array([rect[0], rect[1], rect[2]-rect[0], rect[3]-rect[1]])
    matrix = np.r_[cb[1]-cb[0], cb[2]-cb[0], (cb[0]-ob)/density]
    size = array(source['layout_size_px'], (2,))
    require(np.all(size > 0), 'actual Android producer dimensions missing')
    # This is world -> actual producer pixels, separately from output density.
    source_matrix = np.diag(size / np.array([375, 667]))
    require(np.max(np.abs(sb[1:]-sb[0]-np.eye(2))) < 1e-5, 'nonidentity Android source-to-screen basis needs explicit observed source matrix')
    opacity = carrier.get('effective_opacity')
    require(str(capture['flat_png' if flat else 'png']).endswith('-held-screen.png'), 'Android default parser requires original full-screen capture; explicit observed output mapping is required for another screenshot domain')
    return {'carrier_bounds':bounds, 'matrix_samples':matrix[None],
            'opacity_samples':None if opacity is None else np.array([float(opacity)]),
            'source_origin':array(source['screen_origin_px'], (2,))/float(source['density']),
            'source_sampling_matrix':source_matrix,
            'actual_output_mapping':{'scale':float(source['density']),'origin':array(source['screen_origin_px'],(2,)),
                                     'dimensions_px':None},
            'evidence':{'path':str(path),'sha256':SHA(path),
                        'scope':'actual held transformed four corners and local basis, owner and parent, original producer layout dimensions; opacity unknown unless directly exported'},
            'unknowns':[] if opacity is not None else ['Android effective opacity not exported by current geometry observer']}


def load_round(path, role):
    path = Path(path).resolve()
    index = read(path)
    platform = index.get('platform')
    require(platform in ['ios', 'android'], 'unknown platform')
    require(index.get('status') in ['passed', 'original_hashes_pointer_and_pair_checks_passed'], 'round index not accepted')
    captures = index.get('captures', [])
    require(len(captures) == 6 and sorted(c['stage_id'] for c in captures) == sorted(STAGES), 'expected exact six shape/flat stages')
    if platform == 'android':
        audit = index.get('independent_acquisition_audit')
        if audit:
            p = resolve(audit['path'], path.parent)
            hashed(p, audit['sha256'])
            require(read(p).get('status') == 'passed', 'Android independent acquisition audit did not pass')
        else:
            require(index.get('status') == 'original_hashes_pointer_and_pair_checks_passed', 'Android independent audit status is missing')
            adapter = index['adapter']; hashed(resolve(adapter['path'], path.parent), adapter['sha256'])
        sr = index['source_result']; hashed(resolve(sr['path'], path.parent), sr['sha256'])
        host = index['host_receipt']
        hp = resolve(host['path'], path.parent)
        hashed(hp, host['sha256'])
        receipt = read(hp)
        require(receipt.get('test_passed') is True and receipt.get('exit_code') == 0, 'Android held acquisition failed')
        require(receipt['input_sha256']['inputs/manifest.json'] == role['manifest_sha256'], 'Android delivered manifest differs')
        main_file = Path(role['source_png']).name
        require(receipt['input_sha256']['inputs/' + main_file] == role['main_sha256'], 'Android delivered main source differs')
        flat_hash = next(e['sha256'] for e in role['manifest_value']['inputs'] if e['id'] == 'st00_flat128')
        require(receipt['input_sha256']['inputs/st00_flat128.png'] == flat_hash, 'Android delivered flat differs')
    loaded = {}
    for c in captures:
        require(c['input_id'] == c['shape_id'] == role['main_id'], 'wrong scheduled multicolor source')
        if platform == 'android':
            require(resolve(c['android_evidence_json'], path.parent).resolve() == resolve(sr['path'], path.parent).resolve(), 'capture geometry result not bound to accepted source-result')
            hashed(resolve(c['android_evidence_json'], path.parent), sr['sha256'])
        images, mappings, geometries, errors = {}, {}, {}, []
        for flat, label in [(False, 'shape'), (True, 'flat')]:
            pkey, hkey = ('flat_png', 'flat_sha256') if flat else ('png', 'sha256')
            p = resolve(c[pkey], path.parent)
            images[label] = png(p, c[hkey])
            mg = c['flat_geometry'] if flat else c
            mappings[label] = {'origin': array(mg['world_origin_window_px'], (2,)),
                               'scale': float(mg['pixels_per_world_unit'])}
            require(mappings[label]['scale'] > 0, 'invalid screenshot output scale')
            try:
                g = native_observation(index, c, flat, role, path.parent) if platform == 'ios' else android_geometry(c, flat, path.parent)
                require(g['matrix_samples'].ndim == 2 and g['matrix_samples'].shape[1] == 6 and len(g['matrix_samples']) >= 1, 'presentation matrix must have six observed affine elements per sample')
                if g['opacity_samples'] is not None:
                    require(g['opacity_samples'].ndim == 1 and len(g['opacity_samples']) >= 1, 'opacity samples invalid')
                output_mapping=g['actual_output_mapping']
                require(abs(mappings[label]['scale']-output_mapping['scale']) <= 1e-7, 'indexed screenshot scale differs from observed output density')
                require(np.max(np.abs(mappings[label]['origin']-output_mapping['origin'])) <= 1e-5, 'indexed screenshot world origin differs from actual output mapping')
                if output_mapping['dimensions_px'] is not None:
                    require(list(images[label].shape[1::-1]) == list(output_mapping['dimensions_px']), 'original screenshot dimensions differ from observed output mapping')
                claimed = mg['actual_carrier_bounds_world_xywh']
                require(np.max(np.abs(g['carrier_bounds'] - claimed)) <= .1, 'receipt versus index carrier mismatch')
                geometries[label] = g
            except (ValueError, KeyError, OSError, TypeError) as e:
                errors.append(label + ': ' + str(e))
        loaded[c['stage_id']] = {'images': images, 'mappings': mappings, 'geometries': geometries, 'errors': errors, 'capture': c}
    return {'path': str(path), 'sha256': SHA(path), 'platform': platform, 'synthetic_fixture':bool(index.get('synthetic_fixture',False)), 'stages': loaded}


def compare_geometry(rows):
    errors = [err for row in rows for err in row['errors']]
    if errors:
        return {'status': 'unknown', 'errors': errors}
    gs = [row['geometries'][k] for row in rows for k in ['shape', 'flat']]
    checks = {}
    bounds = np.stack([g['carrier_bounds'] for g in gs])
    centers = bounds[:, :2] + bounds[:, 2:] / 2
    checks['carrier_bounds_max_range_pt'] = float(np.ptp(bounds, axis=0).max())
    checks['carrier_center_max_range_pt'] = float(np.ptp(centers, axis=0).max())
    checks['presentation_matrix_max_range'] = float(np.ptp(np.concatenate([g['matrix_samples'] for g in gs]), axis=0).max())
    opacity_known = all(g['opacity_samples'] is not None for g in gs)
    checks['effective_opacity_max_range'] = float(np.ptp(np.concatenate([g['opacity_samples'] for g in gs]))) if opacity_known else None
    checks['source_origin_max_range'] = float(np.ptp(np.stack([g['source_origin'] for g in gs]), axis=0).max())
    checks['source_sampling_matrix_max_range'] = float(np.ptp(np.stack([g['source_sampling_matrix'] for g in gs]), axis=0).max())
    limits = [.1, .1, .001, .01, 1e-8, 1e-8]
    for (name, value), limit in zip(checks.items(), limits):
        if value is not None and value > limit + 1e-10:
            errors.append(f'{name}={value} exceeds {limit}')
    return {'status': 'rejected' if errors else 'passed' if opacity_known else 'mapping_unknown_pixel_diagnostics_only',
            'checks': checks, 'errors': errors,
            'unknowns':[] if opacity_known else ['effective opacity is unobserved; no full mapping/photometric comparability claim'],
            'evidence': [g['evidence'] for g in gs]}


def inset(x, y, bounds):
    # Public carrier capsule assumption, retained from existing calibration. It is
    # a geometry domain, never an inferred native optical alpha or thickness.
    left, top, width, height = bounds
    radius = height / 2
    dx = np.maximum(np.abs(x - (left + width/2)) - (width/2 - radius), 0)
    return radius - np.hypot(dx, y - (top + radius))


def regions(x, y, bounds, target):
    ds = np.stack([inset(x, y, b) for b in bounds])
    minimum, maximum = ds.min(axis=0), ds.max(axis=0)
    interior = minimum >= 1
    carrier = minimum >= 0
    boundary = carrier & (maximum < 1)
    # The narrow interval crossing inset1 in any observed carrier is explicit.
    ambiguous_boundary = carrier & ~(interior | boundary)
    target_col = np.floor((x - ROI[0])*4).astype(int)
    target_row = np.floor((y - ROI[1])*4).astype(int)
    target_sample = np.zeros(x.shape, bool)
    ok = (target_col >= 0) & (target_col < target.shape[1]) & (target_row >= 0) & (target_row < target.shape[0])
    target_sample[ok] = target[target_row[ok], target_col[ok]]
    return {'complete_fixed_ROI': np.ones(x.shape, bool), 'common_carrier_interior_inset1': interior,
            'unconfounded_top_interior': interior & (y < 422),
            'rail_confounded_interior_y422_438': interior & (y >= 422) & (y < 438),
            'lower_interior_y438_plus': interior & (y >= 438),
            'common_carrier_boundary_inset0_1': boundary,
            'boundary_domain_uncertain_due_to_observed_pose_range': ambiguous_boundary,
            'preregistered_ingress75_target_complete': target_sample,
            'preregistered_ingress75_target_interior': target_sample & interior}


def bilinear(im, x, y, mapping):
    xx = mapping['origin'][0] + x*mapping['scale'] - .5
    yy = mapping['origin'][1] + y*mapping['scale'] - .5
    require(xx.min() >= 0 and yy.min() >= 0 and xx.max() < im.shape[1]-1 and yy.max() < im.shape[0]-1, 'world ROI outside screenshot bilinear domain')
    ix, iy = np.floor(xx).astype(int), np.floor(yy).astype(int)
    ax, ay = (xx-ix)[...,None], (yy-iy)[...,None]
    return (im[iy,ix]*(1-ax)*(1-ay) + im[iy,ix+1]*ax*(1-ay) + im[iy+1,ix]*(1-ax)*ay + im[iy+1,ix+1]*ax*ay)


def support(mask, values, x, y, area, cache=None):
    cache_key = (mask.shape, mask.tobytes())
    if cache is not None and cache_key in cache:
        result = dict(cache[cache_key]); weights = np.abs(values[mask]); ws = weights.sum()
        result['absolute_signal_weighted_centroid_world'] = [float((x[mask]*weights).sum()/ws),float((y[mask]*weights).sum()/ws)] if ws else None
        return result
    count = int(mask.sum())
    if not count:
        return {'samples': 0, 'area_pt2': 0, 'centroid_world': None, 'absolute_signal_weighted_centroid_world': None, 'support_bounds_sample_centers_xyxy': None, 'components': []}
    weights = np.abs(values[mask])
    ws = weights.sum()
    component_seen = np.zeros(mask.shape, bool)
    components = []
    for rr, cc in np.argwhere(mask):
        if component_seen[rr,cc]:
            continue
        queue = deque([(int(rr), int(cc))]); component_seen[rr,cc] = True; points = []
        while queue:
            r,c = queue.popleft(); points.append((r,c))
            for dr,dc in [(1,0),(-1,0),(0,1),(0,-1)]:
                nr,nc=r+dr,c+dc
                if 0 <= nr < mask.shape[0] and 0 <= nc < mask.shape[1] and mask[nr,nc] and not component_seen[nr,nc]:
                    component_seen[nr,nc] = True; queue.append((nr,nc))
        rs,cs=np.asarray(points).T
        components.append({'samples':len(points),'area_pt2':float(len(points)*area),
                           'centroid_world':[float(x[rs,cs].mean()),float(y[rs,cs].mean())],
                           'bounds_sample_centers_xyxy':[float(x[rs,cs].min()),float(y[rs,cs].min()),float(x[rs,cs].max()),float(y[rs,cs].max())]})
    result = {'samples':count,'area_pt2':float(count*area),
            'centroid_world':[float(x[mask].mean()),float(y[mask].mean())],
            'absolute_signal_weighted_centroid_world':[float((x[mask]*weights).sum()/ws),float((y[mask]*weights).sum()/ws)] if ws else None,
            'support_bounds_sample_centers_xyxy':[float(x[mask].min()),float(y[mask].min()),float(x[mask].max()),float(y[mask].max())],
            'components_4_connected':sorted(components,key=lambda v:v['samples'],reverse=True)}
    if cache is not None:
        cache[cache_key] = result
    return result


def summarize(fields, x, y, domains, area):
    report = {}; component_cache = {}
    for name, domain in domains.items():
        domain_report = {'samples':int(domain.sum()), 'area_pt2':float(domain.sum()*area), 'fields':{}}
        for fname, field in fields.items():
            channel_report = {}
            for channel, ci in [('R',0),('G',1),('B',2)]:
                v=field[...,ci]; values=v[domain]
                stat={'signed_quantiles_p0_1_10_50_90_99_100':np.percentile(values,[0,1,10,50,90,99,100]).tolist() if values.size else None,
                      'absolute_p99':float(np.percentile(np.abs(values),99)) if values.size else None,
                      'signed_sum_byte_pt2':float(values.sum()*area), 'thresholds':{}}
                for threshold in THRESHOLDS:
                    stat['thresholds'][str(threshold)]={
                        'positive_gt':support(domain&(v>threshold),v,x,y,area,component_cache),
                        'negative_lt_minus':support(domain&(v < -threshold),v,x,y,area,component_cache),
                        'neutral_abs_le':support(domain&(np.abs(v)<=threshold),v,x,y,area,component_cache)}
                channel_report[channel]=stat
            domain_report['fields'][fname]=channel_report
        report[name]=domain_report
    return report


def analyze_stage(stage, w, c, target, out):
    gate=compare_geometry([w,c])
    result={'stage':stage,'role':'primary cap diagnostic' if stage=='ingress75' else 'positive G contrast / cap-only change control' if stage=='full100' else 'exploratory',
            'geometry_gate':gate}
    if gate['status'] not in ['passed', 'mapping_unknown_pixel_diagnostics_only']:
        result['status']='NO_SUBTRACTION_' + gate['status'].upper(); return result
    rows=[w,c]
    images=[row['images'][k] for row in rows for k in ['shape','flat']]
    mappings=[row['mappings'][k] for row in rows for k in ['shape','flat']]
    bounds=[row['geometries'][k]['carrier_bounds'] for row in rows for k in ['shape','flat']]
    xx=ROI[0]+(np.arange(176)+.5)/4; yy=ROI[1]+(np.arange(176)+.5)/4
    x,y=np.meshgrid(xx,yy)
    W,FW,C,FC=[bilinear(im,x,y,m) for im,m in zip(images,mappings)]
    fields={'witness_minus_own_flat':W-FW,'control_minus_own_flat':C-FC,'raw_witness_minus_control':W-C,'flat_round_residual':FW-FC,'corrected_difference_of_differences':(W-FW)-(C-FC)}
    domains=regions(x,y,bounds,target)
    interior=domains['common_carrier_interior_inset1']
    p99=np.percentile(np.abs(fields['flat_round_residual'][interior]),99,axis=0) if interior.any() else None
    result['flat_drift_gate']={'status':'pending_original_byte_check','bilinear_world_grid_encoded_RGB_absolute_p99':p99.tolist() if p99 is not None else None,'original_pixel_encoded_RGB_absolute_p99':None,'limit_each_channel':3}
    result['world_grid']={'sampling':'bilinear interpolation of encoded original bytes; values are not original captured pixel bytes','samples_per_pt':4,'roi_xyxy':ROI}
    result['world_grid_metrics']=summarize(fields,x,y,domains,1/16)
    np.savez_compressed(out/(stage+'-world-grid.npz'),x=x,y=y,W=W,FW=FW,C=C,FC=FC,**fields)
    # Original integer byte differences only when all four captures share exactly
    # the same pixel coordinate mapping. Never resample or shift for this branch.
    same_mapping=all(np.array_equal(m['origin'],mappings[0]['origin']) and m['scale']==mappings[0]['scale'] for m in mappings)
    same_dimensions=all(im.shape==images[0].shape for im in images)
    if same_mapping and same_dimensions:
        density=mappings[0]['scale'];origin=mappings[0]['origin']
        left=max(0,int(np.ceil(origin[0]+ROI[0]*density-.5)));right=min(images[0].shape[1],int(np.ceil(origin[0]+ROI[2]*density-.5)))
        top=max(0,int(np.ceil(origin[1]+ROI[1]*density-.5)));bottom=min(images[0].shape[0],int(np.ceil(origin[1]+ROI[3]*density-.5)))
        cols=np.arange(left,right);rws=np.arange(top,bottom)
        bx,by=np.meshgrid((cols+.5-origin[0])/density,(rws+.5-origin[1])/density)
        Wb,FWb,Cb,FCb=[im[top:bottom,left:right].astype(np.int16) for im in images]
        byte_fields={'witness_minus_own_flat':Wb-FWb,'control_minus_own_flat':Cb-FCb,'raw_witness_minus_control':Wb-Cb,'flat_round_residual':FWb-FCb,'corrected_difference_of_differences':(Wb-FWb)-(Cb-FCb)}
        np.savez_compressed(out/(stage+'-original-byte-differences.npz'),x=bx,y=by,W=Wb,FW=FWb,C=Cb,FC=FCb,**byte_fields)
        byte_domains=regions(bx,by,bounds,target)
        byte_interior=byte_domains['common_carrier_interior_inset1']
        byte_p99=np.percentile(np.abs(byte_fields['flat_round_residual'][byte_interior]),99,axis=0) if byte_interior.any() else None
        result['flat_drift_gate']['original_pixel_encoded_RGB_absolute_p99']=byte_p99.tolist() if byte_p99 is not None else None
        result['flat_drift_gate']['status']='passed' if byte_p99 is not None and p99 is not None and np.all(byte_p99<=3) and np.all(p99<=3) else 'uncertain'
        result['original_pixel_byte_metrics']={'status':'exact integer subtraction at original capture pixels; no interpolation, registration or color conversion','crop_original_pixel_xyxy':[left,top,right,bottom],
            'metrics':summarize(byte_fields,bx,by,byte_domains,1/density**2)}
    else:
        result['flat_drift_gate']['status']='uncertain'
        result['original_pixel_byte_metrics']={'status':'unknown/non-comparable pixel lattices; original bytes retained, no direct pixel differences fabricated'}
    result['status']='MAPPING_UNKNOWN_PIXEL_DIAGNOSTICS_ONLY' if gate['status']!='passed' else 'COMPARABLE' if result['flat_drift_gate']['status']=='passed' else 'PHOTOMETRIC_PAIRING_UNCERTAIN'
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--witness-index',required=True);p.add_argument('--control-index',required=True);p.add_argument('--output',required=True)
    args=p.parse_args();out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=True)
    report={'schema':1,'implementation_version':'1.1','frozen_criteria_script_sha256':SHA(HERE/'analyze-witness-control.py'),'status':'NOT_ANALYZED','script_sha256':SHA(__file__),'protocol_sha256':SHA(HERE/'PROTOCOL.md'),
            'analysis_plan_sha256':SHA(HERE/'analysis-plan.json'),'thresholds':[4,8,16,24],
            'identification':'finite differences only; no common sampler, physical thickness, native parity or nonlinear processing claim',
            'domains_scope':'capsule from actual public carrier bounds, not native optical alpha; no image registration'}
    try:
        roles=verify_assets();w=load_round(args.witness_index,roles['witness']);c=load_round(args.control_index,roles['control'])
        require(w['platform']==c['platform'],'different platforms cannot form a witness/control pair')
        report['evidence_class']='SYNTHETIC_ONLY_NO_CAPTURE_EVIDENCE' if w['synthetic_fixture'] or c['synthetic_fixture'] else 'observed_capture_indexes';report['platform']=w['platform'];report['indexes']=[{k:v for k,v in row.items() if k!='stages'} for row in [w,c]]
        plan=read(HERE/'analysis-plan.json');hashed(HERE/plan['source_mask']['file'],plan['source_mask']['sha256'])
        target=np.asarray(Image.open(HERE/plan['source_mask']['file']))>0
        report['stages']=[analyze_stage(stage,w['stages'][stage],c['stages'][stage],target,out) for stage in STAGES]
        report['status']='ANALYZED_WITH_GATES';report['comparability_by_stage']={s['stage']:s['status'] for s in report['stages']}
        report['interpretation_gate']='No absent ingress75 response interpretation until full100 is comparable and all four threshold supports are inspected. R/B finite differences are coupling evidence, not a two-level nonlinearity test.'
    except (ValueError,KeyError,OSError,TypeError,StopIteration) as e:
        report['status']='REJECTED_OR_UNKNOWN_BEFORE_SUBTRACTION';report['error']=str(e)
    (out/'analysis.json').write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
    print(json.dumps({k:report[k] for k in ['status','error','comparability_by_stage'] if k in report}))
    return 0 if report['status']=='ANALYZED_WITH_GATES' else 2


if __name__=='__main__':
    sys.exit(main())
