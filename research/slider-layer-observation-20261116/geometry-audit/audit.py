#!/usr/bin/env python3
"""Existing-evidence audit."""
import argparse
import ast
import hashlib
import json
import math
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
L = HERE.parents[2]
STUDY = L / 'research/slider-android-response-20261116'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def sub(a, b):
    return [x - y for x, y in zip(a, b)]


def near(a, b):
    assert len(a) == len(b) and max(map(abs, sub(a, b))) < 1e-10


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--app-root', required=True, type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    paths = {
        'android': STUDY / 'evidence/rounds/control-pre/android-r2/trace/result.json',
        'freeze': STUDY / 'FREEZE.json',
        'native': L / 'research/slider-color-response-20261116/evidence/rounds/control-pre/native-r1/endpoint-verification-strict.json',
        'report': STUDY / 'analysis-v2-post-acquisition-compatible-20261116/report/analysis.json',
        'analyzer': STUDY / 'analyze-compatible.py',
    }
    raw, freeze, native, prior = [read(paths[k]) for k in list(paths)[:4]]
    limits = ast.literal_eval(re.search(r'^LIMITS = (.+)$', paths['analyzer'].read_text(), re.M)[1])
    assert limits['bounds'] == .1 and limits['matrix'] == .001
    host = {p: sha(args.app_root / p) for p in freeze['host_files'] if not p.startswith('app/build/')}
    assert len(host) == 7 and all(h == freeze['host_files'][p] for p, h in host.items())
    native_rel, = [p for p in freeze['files'] if p.endswith('/endpoint-verification-strict.json')]
    assert sha(paths['native']) == freeze['files'][native_rel]
    assert native['status'] == 'passed' and not native['errors']
    rows = [r for r in raw['captures'] if r['input_id'] == raw['shape_id']]
    row, = [r for r in rows if r['coverage_stage_id'] == 'full100']
    g = row['geometry']
    source = g['background_world']['source']
    d = float(source['density'])
    assert d == raw['density'] and d > 0
    b = source['local_to_screen_unit_basis_px']
    a, c = sub(b[1], b[0]), sub(b[2], b[0])
    det = (a[0] * c[1] - c[0] * a[1]) * d

    def world(p):
        x, y = sub(p, b[0])
        return [(c[1] * x - c[0] * y) / det, (-a[1] * x + a[0] * y) / det]

    obs, calc = {}, {}
    for role, key in [('owner', 'isotropic_thumb_owner'), ('carrier', 'affine_visual_carrier')]:
        node = g[key]
        assert node['density'] == d
        corners = [p['screen_px'] for p in node['local_to_screen_corners_px']]
        obs[role] = dict(layout_px=node['layout_size_px'], basis_px=node['local_to_screen_unit_basis_px'],
                         corners_px=corners, effective_opacity=node.get('effective_opacity'))
        points = list(map(world, corners))
        lo = [min(p[i] for p in points) for i in (0, 1)]
        size = [max(p[i] for p in points) - lo[i] for i in (0, 1)]
        calc[role + '_xywh_dp'] = lo + size
    ob, cb = [calc[k + '_xywh_dp'] for k in ('owner', 'carrier')]
    n, = [o for o in native['observations'] if o['externalInput']['id'] != 'st00_flat128']
    nb = n['actualCarrierBoundsPt']
    nm = [n['presentedPoseSamples'][0]['carrier'][k] for k in ('m11', 'm12', 'm21', 'm22', 'm41', 'm42')]
    b = obs['carrier']['basis_px']
    cm = sub(b[1], b[0]) + sub(b[2], b[0]) + [v / d for v in sub(b[0], g['isotropic_thumb_owner']['screen_origin_px'])]
    metrics = (args.app_root / next(p for p in host if p.endswith('/SliderVisuals.kt'))).read_text()
    constants = [float(re.search(r'const val ' + name + r' = ([\d.]+)f', metrics)[1])
                 for name in ('SINGLE_WIDTH', 'SINGLE_HEIGHT', 'LIFT_SCALE')]
    ideal = [v * constants[2] for v in constants[:2]]
    ideal_px = [v * d for v in ideal]
    rounded = [math.floor(v + .5) for v in ideal_px]
    assert rounded == obs['owner']['layout_px'] == [171, 111]
    quant = sub(ob[2:], ideal)
    residual = sub(cb[2:], ob[2:])
    delta = sub(cb, nb)
    matrix_delta = sub(cm, nm)
    centre_delta = [cb[i] + cb[i + 2] / 2 - nb[i] - nb[i + 2] / 2 for i in (0, 1)]
    cross = prior['cross_system_geometry']
    for ours, key in [(delta, 'bounds_delta_xywh'), (matrix_delta, 'carrier_matrix_delta'), (centre_delta, 'centre_delta_xy')]:
        near(ours, cross[key])
    near(delta[2:], [quant[i] + residual[i] + ideal[i] - nb[i + 2] for i in (0, 1)])
    calc.update(ideal_held_dp=ideal, ideal_held_px=ideal_px, nearest_integer_px=rounded,
                      owner_quantization_dp=quant, carrier_minus_owner_size_dp=residual,
                      ideal_minus_native_size_dp=sub(ideal, nb[2:]), carrier_minus_native_xywh_dp=delta,
                      centre_delta_dp=centre_delta,
                      carrier_matrix_delta=matrix_delta, carrier_minus_owner_origin_dp=cm[4:],
                      bounds_gate_failed=max(map(abs, delta + centre_delta)) > limits['bounds'] + 1e-10,
                      matrix_gate_failed=max(map(abs, matrix_delta)) > limits['matrix'] + 1e-10)
    hashes = {Path(p).name: h for p, h in host.items()}
    assert len(hashes) == 7
    result = dict(schema=1, scope='No confirmed product bug; no optical acceptance.',
                  inputs={str(p.relative_to(L)): sha(p) for p in paths.values()},
                  current_source_sha256=hashes, all_seven_match_freeze=True,
                  observed=dict(density=d, **obs, native_xywh_pt=nb,
                                stage_business_values={r['coverage_stage_id']: r['value'] for r in rows},
                                prior_status=prior['status'], optical_acceptance=prior['optical_acceptance'],
                                inference_allowed=prior['inference_allowed']),
                  calculated=calc, unchanged_gates={'bounds_pt': limits['bounds'], 'matrix_per_element': limits['matrix']},
                  hypothesis={'centre_pivot_compensation_dp': [-v / 2 for v in residual],
                              'observed_origin_minus_hypothesis_dp': [cm[i + 4] + residual[i] / 2 for i in (0, 1)],
                              'limit': 'Public-corner hypothesis; not raw translation or a measured pivot.'})
    encoded = json.dumps(result, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n'
    assert not re.search(r'/(?:Users|home)/[^/]+/', encoded)
    output = HERE / 'audit.json'
    if args.check:
        assert output.read_text() == encoded
    else:
        with output.open('x') as f:
            f.write(encoded)
    print('verified: 7 source hashes match; gates still fail; no acceptance')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, AssertionError, StopIteration):
        raise SystemExit('geometry-audit: input/invariant failure') from None
