"""Read-only source audit + Double scalar model; writes only beside this script."""
from pathlib import Path
import csv
import hashlib
import json
import math

OUT = Path(__file__).resolve().parent
P = OUT.parent
A = Path('/Users/kerrylee/.codex/worktrees/android-settings-glass-fixes/sleepy')
SOURCES = [
    A / 'libraries/liquid-glass/runtime/src/androidMain/assets/shaders/liquid_glass.agsl',
    A / 'libraries/liquid-glass/runtime/src/androidMain/kotlin/com/lingion/sleepy/ui/component/liquidglass/LiquidGlassStyle.kt',
    A / 'app/src/main/java/com/lingion/sleepy/ui/component/liquidglass/GlassControlModifier.kt',
    P / 'panel-probes-preparation/oracle.json',
    P / 'panel-probes-preparation/analysis-plan.md',
    P / 'analysis-native-probes/S02-local-contours.json',
    P / 'analysis-native-probes/coordinate-local-contours.json',
    P / 'analysis-native-probes/alert-body8/S02-local-contours.json',
    P / 'analysis-native-probes/alert-body8/coordinate-local-contours.json',
    P / 'analysis-native-probes/alert-body8/Sheet-S07-local-contours.json',
    P / 'analysis-native-probes/alert-body8/decision.json',
]


def dump(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def mapping(d, a, b, power):
    if a == 0 or d >= b:
        return {'d': d, 'D': 0., 'g': d, 'gp': 1., 'gpp': 0.}
    r = 1. - d / b
    q = math.sqrt(1. - r * r)
    # Stable equivalent of 1-sqrt(1-r^2), for CPU reasoning only.
    f = r * r / (1. + q)
    fp = -r / (b * q)
    fpp = 1. / (b * b * q ** 3)
    depth = a * f ** power
    dp = a * power * f ** (power - 1.) * fp
    dpp = a * power * ((power - 1.) * f ** (power - 2.) * fp * fp
                       + f ** (power - 1.) * fpp)
    return {'d': d, 'D': depth, 'g': d + depth, 'gp': 1. + dp, 'gpp': dpp}


profiles = [(0., 20., 1.), (30., 20., 1.), (60., 20., 1.),
            (60., 20., .5), (60., 20., 2.)]
rows = []
for a, b, power in profiles:
    for index in range(1, 121):
        row = mapping(index * .25, a, b, power)
        row.update(A=a, B=b, power=power,
                   signed_local_image_scale=1. / row['gp'] if abs(row['gp']) > 1e-12 else None)
        rows.append(row)
with (OUT / 'scalar-mapping-model.csv').open('w', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=['A', 'B', 'power', 'd', 'D', 'g', 'gp', 'gpp',
                                               'signed_local_image_scale'])
    writer.writeheader()
    writer.writerows(rows)

# Verify the symbolic derivatives against the model itself, not against native/GPU output.
checks = []
for a, b, power in profiles[1:]:
    for d in [.25, 1., 4., 8., 12., 16., 19.5]:
        h = 1e-4
        analytic = mapping(d, a, b, power)
        minus, plus = mapping(d-h, a, b, power), mapping(d+h, a, b, power)
        numerical = (plus['g'] - minus['g']) / (2.*h)
        checks.append({'A': a, 'B': b, 'power': power, 'd': d,
                       'gp_analytic': analytic['gp'], 'gp_finite_difference': numerical,
                       'absolute_difference': abs(analytic['gp']-numerical)})
dump('model-derivative-self-check.json', {
    'scope': 'CPU Double formula self-check only, not Kotlin/GPU/native validation',
    'step_pt': 1e-4, 'max_absolute_difference': max(r['absolute_difference'] for r in checks),
    'rows': checks,
})

data = []
for relative in ['analysis-native-probes/S02-local-contours.json',
                 'analysis-native-probes/coordinate-local-contours.json',
                 'analysis-native-probes/alert-body8/S02-local-contours.json',
                 'analysis-native-probes/alert-body8/coordinate-local-contours.json']:
    for r in json.loads((P/relative).read_text()):
        if r.get('y_pt') not in [261.75, 265.75, 269.75, 273.75]:
            continue
        cross = r.get('cross50', [])
        raw_cross = r.get('raw_cross50', [])
        data.append({'source_file': relative, 'feature': r['feature'], 'platform': r['platform'],
                     'rendered_condition': 'alert_body_radius8' if 'alert-body8/' in relative and r['platform']=='rim_blur' else r['platform'],
                     'world_y_pt': r['y_pt'], 'eligible': r['eligible'],
                     'failed_gates': r['failed_gates'],
                     'cross50_fixed_smoothed_pt': cross[0] if len(cross) == 1 else None,
                     'raw_cross50_pt': raw_cross[0] if len(raw_cross) == 1 else None,
                     'raw_width_pt': r.get('descriptive_raw_width_10_90_pt'),
                     'contrast_amplitude_encoded': r['contrast_amplitude']})
dump('current-probe-observations.json', {'scope': 'Existing nonperiodic calibration only; no new image decode',
                                        'rows': data})

fold_d = 20. * (1. - 20. / math.hypot(60., 20.))
fold_g = 60. + 20. - math.hypot(60., 20.)
dump('diagnosis.json', {
    'scope': 'Ordinary Alert/Sheet static positive refraction only; no Dock change or inference',
    'sampling_map': 'S(q)=q-D(d)*n(q); flat inward g(d)=d+D(d)',
    'image_magnification': 'signed 1/g_prime, only on an invertible local branch',
    'A60_B20_p1': {'stationary_d_pt': fold_d, 'minimum_source_inward_g_pt': fold_g,
                  'source_u20_preimages_d_pt': [8., 20.]},
    'amplitude_counterexample_at_d8': [mapping(8., a, 20., 1.) | {'A': a} for a in [30., 60.]],
    'half_power_shoulder': {'gp_limit_inside': 1.-60./(math.sqrt(2.)*20.),
                            'gp_outside': 1., 'continuous_first_derivative': False},
    'model_limitations': ['Exact scalar flat-edge mathematics, not exact contour solver/GPU arithmetic',
                          'No native refraction field or physical thickness recovered',
                          'Rendered contour crossings are not automatically source coordinates'],
})

dump('proposed-diagnostic-plan.json', {
    'status': 'Proposal only; not a capture plan approval or generated source assets',
    'source': {'shape': 'one filled wide trapezoid with two nonparallel straight sides',
               'local_source_coordinates': 'u=y_source-b; v=x_source-c',
               'side_equations': 'v_left=-a-m*u; v_right=a+m*u',
               'u_extent_pt': [-64., 128.], 'm': .25,
               'contrast_pair_rgb': [[60, 60, 60], [190, 190, 190]],
               'reverse_contrast_with_identical_geometry': True,
               'base_half_width_a_pt': 20., 'falsification_half_width_a_pt': 24.,
               'alert_proposed_world_anchor_c_b_pt': [187.5, 257.5],
               'sheet_proposed_world_anchor_c_b_pt': [90., 317.5],
               'anchors_require_actual_contour_and_foreground_eligibility_before_freeze': True},
    'observables': {'W': 'right_edge_x-left_edge_x', 'C': '(right_edge_x+left_edge_x)/2',
                    'g': '(W-2*a)/(2*m)', 'D': 'g-d', 'tangent_input_shift_U': 'c-C',
                    'g_prime': 'W_prime/(2*m)', 'g_second': 'W_second/(2*m)'},
    'required_model_condition': 'Flat strip with mapping approximately invariant along its tangent; two widths must agree before scalar inversion',
    'capture_basis': 'Keep original 750x1334 pixels / 375x667 world; never register/warp output images',
    'output_depth_sample_centers_pt': [.25, 19.75, .5],
    'derivative_operator': 'Fixed centered secants at h=4pt for g_prime/g_second only where both endpoints are eligible; otherwise report interval slopes at their interval center or unresolved, never an edge derivative extrapolation',
    'minimum_quantization_floor': {'each_edge_location_pt': .25, 'g_bound_pt_at_m025': 1.,
                                  'g_prime_bound_h4': .25, 'g_second_bound_h4_per_pt': .25},
    'gates': ['Freeze every new source PNG hash, its oracle and actual pre-presentation backing capture',
              'Require clean source/foreground footprint for BOTH sides; do not fill missing edges',
              'Reuse original contrast/secondary-peak/plateau/location gates, report failures',
              'Reverse contrast positions must agree within declared uncertainty',
              'Two widths must yield compatible g and U; disagreement rejects local 1D model',
              'Retain crossing multiplicity/sign, do not choose nearest correspondence',
              'No refraction/power fitting if these conditions fail'],
    'caveat': 'Crossing reversal tests can expose bias but cannot prove an isolated blur kernel; any remaining spatially varying photometric bias keeps g apparent, not physical',
})

# Small standalone SVG plots; all curves are theoretical and explicitly labelled.
colors = ['#555555', '#00816a', '#245bc0', '#c26000', '#922e9a']
svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1050" height="840" viewBox="0 0 1050 840">',
       '<rect width="1050" height="840" fill="white"/>',
       '<text x="45" y="28" font-family="sans-serif" font-size="19">Flat-edge sampling model only — no native/GPU fit</text>']
panels = [('D', 'Input displacement D(d)', 0., 65.),
          ('g', 'Source inward coordinate g(d)=d+D(d)', 0., 65.),
          ('gp', "Derivative g′(d); displayed range clipped to [-12, 3]", -12., 3.)]
for panel_index, (key, label, ymin, ymax) in enumerate(panels):
    x0, y0, width, height = 65., 65.+panel_index*240., 940., 185.
    svg.append(f'<text x="{x0}" y="{y0-10}" font-family="sans-serif" font-size="15">{label}</text>')
    for d in [0, 5, 10, 15, 20, 25, 30]:
        x=x0+width*d/30.
        svg.append(f'<line x1="{x}" y1="{y0}" x2="{x}" y2="{y0+height}" stroke="#eeeeee"/>')
        svg.append(f'<text x="{x-5}" y="{y0+height+16}" font-family="sans-serif" font-size="11">{d}</text>')
    for tick in ([0., 20., 40., 60.] if key != 'gp' else [-12., -8., -4., 0., 1., 3.]):
        y=y0+height*(ymax-tick)/(ymax-ymin)
        svg.append(f'<line x1="{x0}" y1="{y}" x2="{x0+width}" y2="{y}" stroke="#dddddd"/>')
        svg.append(f'<text x="{x0-35}" y="{y+4}" font-family="sans-serif" font-size="11">{tick:g}</text>')
    for index, profile in enumerate(profiles):
        selected=[r for r in rows if (r['A'],r['B'],r['power'])==profile]
        points=' '.join(f'{x0+width*r["d"]/30.:.3f},{y0+height*(ymax-max(ymin,min(ymax,r[key])))/(ymax-ymin):.3f}' for r in selected)
        svg.append(f'<polyline points="{points}" fill="none" stroke="{colors[index]}" stroke-width="2"/>')
for index,(a,b,power) in enumerate(profiles):
    x=50+index*200
    svg.append(f'<line x1="{x}" y1="808" x2="{x+22}" y2="808" stroke="{colors[index]}" stroke-width="3"/>')
    svg.append(f'<text x="{x+28}" y="812" font-family="sans-serif" font-size="12">A={a:g}, B={b:g}, p={power:g}</text>')
svg.append('</svg>')
(OUT/'scalar-mapping-model.svg').write_text('\n'.join(svg))
dump('input-provenance.json', {
    'scope': 'Local source and current nonperiodic calibration data only; no old heldout image/source decode',
    'no_devices_builds_git_or_runtime_code_changes': True,
    'files': [{'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for path in SOURCES],
    'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
})
print(json.dumps({'output': str(OUT), 'fold_d': fold_d, 'fold_g': fold_g,
                  'derivative_self_check_max_error': max(r['absolute_difference'] for r in checks)}, indent=2))
