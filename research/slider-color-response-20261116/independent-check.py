#!/usr/bin/env python3
"""Independent byte/interval audit: reads original held PNGs, never analyzer code.

Uses integer-rational interval intersections, so closed-boundary compatibility
does not depend on minimax bisection or floating threshold statistics.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
ROUNDS = ('control-pre', 'global-R', 'global-G', 'global-B', 'mask-R', 'mask-G', 'mask-B', 'control-post')
ROI = (331, 795, 419, 883)
BINS = (0, .5, 1, 1.5, 2, 3, 4, 5, 6, 7, 8, 10, 14, 20)
TOLERANCES = (1, 4, 8)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text())


def path_at(value, base):
    path = Path(value)
    return path if path.is_absolute() else base / path


def exact_interval(u, m, t):
    """Intersection of [0,1] and |m-a*u|≤t by integer cross-products."""
    u, m = np.asarray(u, np.int64), np.asarray(m, np.int64)
    shape = u.shape[:-1]
    lower_n, lower_d = np.zeros(shape, np.int64), np.ones(shape, np.int64)
    upper_n, upper_d = np.ones(shape, np.int64), np.ones(shape, np.int64)
    impossible = np.zeros(shape, bool)
    for k in range(u.shape[-1]):
        gain, response = u[..., k], m[..., k]
        positive, negative = gain > 0, gain < 0
        nonzero = positive | negative
        denominator = np.where(nonzero, abs(gain), 1)
        lo = np.where(positive, response - t, -response - t)
        hi = np.where(positive, response + t, -response + t)
        take_lo = nonzero & (lo * lower_d > lower_n * denominator)
        take_hi = nonzero & (hi * upper_d < upper_n * denominator)
        lower_n = np.where(take_lo, lo, lower_n)
        lower_d = np.where(take_lo, denominator, lower_d)
        upper_n = np.where(take_hi, hi, upper_n)
        upper_d = np.where(take_hi, denominator, upper_d)
        impossible |= (~nonzero) & (abs(response) > t)
    valid = (~impossible) & (lower_n * upper_d <= upper_n * lower_d)
    return valid, lower_n / lower_d, upper_n / upper_d


def main():
    target = ROOT / 'independent-check.json'
    require(not target.exists(), 'Refusing to overwrite independent audit')
    report_path = ROOT / 'analysis/analysis.json'
    arrays_path = ROOT / 'analysis/original-pixels.npz'
    report = read(report_path)
    require(report['ROI_xyxy_original_pixels'] == list(ROI), 'changed fixed ROI')
    require(report['round_order'] == list(ROUNDS), 'changed order')
    require(report['arrays_sha256'] == sha(arrays_path), 'analysis array hash differs')
    images, observed_hashes = {}, {}
    strict = {}
    for name in ROUNDS:
        folder = ROOT / 'rounds' / name / 'native-r1'
        index = read(folder / 'index-strict.json')
        strict[name] = read(folder / 'endpoint-verification-strict.json')
        receipt = read(folder / 'receipt.json')
        require(strict[name]['status'] == index['status'] == 'passed', 'unverified capture')
        require(strict[name]['verifiedHeldEndpoints'] == 2 and strict[name]['verifiedShapeFlatPairs'] == 1,
                'changed endpoint matrix')
        pair = index['captures'][0]
        require(len(index['captures']) == 1 and pair['stage_id'] == 'full100', 'changed pair scope')
        images[name] = {}
        observed_hashes[name] = {}
        for relative, digest in receipt['analysis_artifacts'].items():
            require(sha(folder / relative) == digest, 'captured artifact changed: ' + relative)
        for label, path_key, hash_key in (('shape', 'png', 'sha256'), ('flat', 'flat_png', 'flat_sha256')):
            path = path_at(pair[path_key], folder)
            require(path.resolve().is_relative_to(folder.resolve()) and sha(path) == pair[hash_key], 'raw PNG identity differs')
            with Image.open(path) as image:
                require(image.format == 'PNG' and image.size == (750, 1334) and image.mode in ('RGB', 'RGBA'), 'PNG grid differs')
                pixels = np.asarray(image)
                if image.mode == 'RGBA':
                    require(np.all(pixels[..., 3] == 255), 'nonopaque original screenshot')
                x0, y0, x1, y1 = ROI
                images[name][label] = pixels[y0:y1, x0:x1, :3].astype(np.int16)
            observed_hashes[name][label] = {'path': str(path), 'sha256': pair[hash_key]}
    pre = images['control-pre']['shape']
    u = np.stack([images['global-' + c]['shape'] - pre for c in 'RGB'], axis=-1)
    m = np.stack([images['mask-' + c]['shape'] - pre for c in 'RGB'], axis=-1)
    # Build capsule distance as distance to a line segment plus a radius, without
    # importing the analyzer's inset implementation or any fitting routine.
    pre_id = read(ROOT / 'inputs/rounds/control-pre/shape-spec.json')['first_input_id']
    pre_observation = next(o for o in strict['control-pre']['observations'] if o['event']['inputID'] == pre_id)
    left, top, width, height = pre_observation['actualCarrierBoundsPt']
    radius = height / 2
    yy, xx = np.mgrid[ROI[1]:ROI[3], ROI[0]:ROI[2]]
    x, y = (xx + .5) / 2, (yy + .5) / 2
    nearest_segment_x = np.clip(x, left + radius, left + width - radius)
    inset = radius - np.sqrt((x - nearest_segment_x) ** 2 + (y - top - radius) ** 2)
    regions = {'complete': np.ones(x.shape, bool), 'above_rail': y < 422,
               'rail_confounded': (y >= 422) & (y < 438), 'below_rail': y >= 438,
               'primary_above_rail_inset_ge1': (y < 422) & (inset >= 1),
               'above_rail_rim_inset_lt1': (y < 422) & (inset < 1)}
    for lo, hi in zip(BINS[:-1], BINS[1:]):
        for name, rail in (('above_rail', y < 422), ('rail_confounded', (y >= 422) & (y < 438))):
            regions[f'{name}_inset_{lo}_{hi}'] = rail & (inset >= lo) & (inset < hi)
    require(set(regions) == set(report['domains']), 'domain set differs')
    families = {'common_all': (u.reshape(*x.shape, 9), m.reshape(*x.shape, 9))}
    for j, c in enumerate('RGB'):
        families['input_' + c] = (u[..., :, j], m[..., :, j])
        families['output_' + c] = (u[..., j, :], m[..., j, :])
    def reported_model(domain, prefix):
        entry = report['domains'][domain]
        if prefix == 'common_all':
            return entry['common']
        family, channel = prefix.split('_')
        return entry['input_columns' if family == 'input' else 'output_rows'][channel]
    counts = {name: {'pixels': int(region.sum()), 'models': {}} for name, region in regions.items()}
    checks = 0
    with np.load(arrays_path, allow_pickle=False) as stored:
        require(np.array_equal(u, stored['raw_global_output_input']), 'independent original U differs')
        require(np.array_equal(m, stored['raw_mask_output_input']), 'independent original M differs')
        original = np.stack([np.stack([images[n][q] for q in ('shape', 'flat')]) for n in ROUNDS]).astype(np.uint8)
        require(np.array_equal(original, stored['original_ROIs_round_shape_flat_outputRGB']), 'stored original ROI differs')
        require(np.max(abs(inset - stored['inset_capsule_assumption'])) <= 1e-12, 'independent capsule inset differs')
        for prefix, (a, b) in families.items():
            for tolerance in TOLERANCES:
                valid, lower, upper = exact_interval(a, b, tolerance)
                require(np.array_equal(valid, stored[f'{prefix}_T{tolerance}_compatible']), f'exact interval compatibility differs: {prefix}, T{tolerance}')
                require(np.array_equal(lower, stored[f'{prefix}_T{tolerance}_lo']) and
                        np.array_equal(upper, stored[f'{prefix}_T{tolerance}_hi']), f'interval endpoints differ: {prefix}, T{tolerance}')
                for name, region in regions.items():
                    compatible, incompatible = int(np.sum(valid & region)), int(np.sum(~valid & region))
                    summary = reported_model(name, prefix)['tolerances_raw_byte'][str(tolerance)]
                    require(compatible == summary['compatible_pixels'] and incompatible == summary['incompatible_pixels'],
                            f'region count differs: {name}, {prefix}, T{tolerance}')
                    counts[name]['models'].setdefault(prefix, {})[str(tolerance)] = {
                        'compatible_pixels': compatible, 'incompatible_pixels': incompatible}
                    checks += 1
        t4_exact = ~stored['common_all_T4_compatible']
        t4_error = stored['common_all_minimax_error'] > 4
        near_boundary = np.argwhere(t4_error & ~t4_exact)
        floating_note = {'authoritative': 'exact closed alpha interval intersection, not minimax residual > threshold',
            'T4_interval_incompatible_pixels': int(t4_exact.sum()),
            'T4_floating_minimax_greater_than_4_pixels': int(t4_error.sum()),
            'floating_minimax_only_pixels': [
                {'world_pt': [float(x[r, c]), float(y[r, c])],
                 'floating_minimax_error': float(stored['common_all_minimax_error'][r, c])}
                for r, c in near_boundary]}
    drift = {'flat_each_round_max_abs_RGB': {name: np.max(abs(images[name]['flat'] - images['control-pre']['flat']), axis=(0, 1)).tolist() for name in ROUNDS},
             'post_pre_shape_max_abs_RGB': np.max(abs(images['control-post']['shape'] - pre), axis=(0, 1)).tolist()}
    require(all(max(v) == 0 for v in drift['flat_each_round_max_abs_RGB'].values()) and max(drift['post_pre_shape_max_abs_RGB']) == 0,
            'independent complete-ROI drift is nonzero')
    result = {'schema': 1, 'status': 'PASS_INDEPENDENT_ORIGINAL_PNG_AND_EXACT_INTERVAL_AUDIT',
        'audit_script_sha256': sha(__file__), 'analysis_json_sha256': sha(report_path), 'arrays_sha256': sha(arrays_path),
        'method': 'Read all 16 formal original held PNGs; form signed int16 global/pre and masked/pre RGB contrasts. Intersect each signed component constraint with alpha in [0,1] using exact int64 rational cross-products; test equality as closed intervals. No analyzer import, function reuse, registration, fit or pixel modification.',
        'matrix_axes': ['output_RGB', 'input_RGB'], 'ROI_xyxy_original_pixels': list(ROI),
        'tolerances_raw_byte': list(TOLERANCES), 'fixed_inset_bins': list(BINS),
        'original_PNGs': observed_hashes, 'original_ROIs_and_U_M_equal_saved_arrays': True,
        'all_exact_interval_endpoints_and_compatibility_arrays_equal': True,
        'region_model_tolerance_count_checks': checks, 'all_report_region_counts_equal': True,
        'independent_complete_ROI_drift': drift, 'floating_boundary_note': floating_note,
        'regions': counts,
        'limits': ['Calibration audit only; incompatibility is conditional on the prescribed bounded common-kernel null.',
                   'No physical thickness, causal pipeline, universal parity or optical acceptance is inferred.',
                   'No trace or xcresult is opened, and no source/capture/frozen result is changed.']}
    target.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'status': result['status'], 'output': str(target), 'checked_region_model_tolerances': checks,
                      'common_complete': counts['complete']['models']['common_all'],
                      'common_primary': counts['primary_above_rail_inset_ge1']['models']['common_all'],
                      'floating_note': floating_note}, indent=2))


if __name__ == '__main__':
    main()
