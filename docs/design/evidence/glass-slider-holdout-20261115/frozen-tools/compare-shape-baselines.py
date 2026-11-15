#!/usr/bin/env python3
"""Report color-evidence displacement from each platform's unchanged baseline.

Centroid movement is a descriptor of observed color evidence, not an optical ray.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import runpy
from PIL import Image, ImageDraw


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--android', type=Path, required=True)
    parser.add_argument('--android-result', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    npth, apth, result_path, out = args.native.resolve(), args.android.resolve(), args.android_result.resolve(), args.out.resolve()
    n, a, result = [json.loads(p.read_text()) for p in (npth, apth, result_path)]
    require_same_identity = n['shape_id'] == a['shape_id'] == result['shape_id']
    if not require_same_identity or n.get('input_role', 'calibration') != a.get('input_role', 'calibration'):
        raise ValueError('Declared shape identity or source input role differs')
    analyzer = runpy.run_path(str(Path(__file__).with_name('analyze-shape-captures.py')))
    np, require = analyzer['np'], analyzer['require']
    require(not out.exists(), 'Refusing to overwrite baseline comparison output')
    require(n['provenance']['original_source']['sha256'] == a['provenance']['original_source']['sha256'], 'Source hashes differ')
    roi, policy = n['fixed_analysis_policy']['fixed_roi_xyxy_world'], n['fixed_analysis_policy']
    palette = policy['region_color_direction_unit_rgb']
    bg = np.asarray(n['source']['shape'].get('background_rgb', [128, 128, 128]), dtype=float)
    source_path = Path(n['provenance']['original_source']['path'])
    original, _ = analyzer['rgb_image'](source_path)
    native_grid = {'world_origin_window_px': [0, 0], 'pixels_per_world_unit': 2}
    nx, ny, baseline_native, _ = analyzer['crop_roi'](original, native_grid, roi)
    rows = []
    baseline_reference = None
    for ns, as_ in zip(n['stages'], a['stages']):
        require(ns['stage_id'] == as_['stage_id'], 'Stage order differs')
        sid = ns['stage_id']
        capture = next(c for c in result['captures'] if c['stage_id'] == sid and c['source_role'] == 'shape')
        baseline_path = result_path.parent / capture['baseline_screen_png']
        full, _ = analyzer['rgb_image'](baseline_path)
        ax, ay, baseline_android, _ = analyzer['crop_roi'](full, as_['mapping'], roi)
        if baseline_reference is None:
            baseline_reference = baseline_android
        require(np.array_equal(baseline_reference, baseline_android), 'Actual source baseline ROI changed across stages')
        region_rows = []
        for nr, ar in zip(ns['color_region_responses'], as_['color_region_responses']):
            rid = nr['region_id']
            direction = np.asarray(palette[rid])
            native_signal, android_signal = baseline_native.astype(float) - bg, baseline_android.astype(float) - bg
            baselines = []
            for data, xx, yy, density in ((native_signal, nx, ny, 2), (android_signal, ax, ay, as_['mapping']['pixels_per_world_unit'])):
                chroma = data - data.mean(axis=2, keepdims=True)
                norm = np.linalg.norm(chroma, axis=2)
                projection = (chroma * direction).sum(axis=2)
                cosine = np.divide(projection, norm, out=np.zeros(norm.shape), where=norm != 0)
                baselines.append({t: analyzer['weighted_geometry'](xx, yy, ((projection >= t) & (cosine >= policy['minimum_color_cosine'])).astype(float), density)
                                  for t in policy['projection_thresholds_byte']})
            thresholds = []
            for nt, at in zip(nr['threshold_sensitivity'], ar['threshold_sensitivity']):
                t = nt['threshold_projection_byte']
                nb, ab = baselines[0][t], baselines[1][t]
                ng, ag = nt['geometry'], at['geometry']
                nm = None if ng['centroid_world'] is None else (np.asarray(ng['centroid_world']) - nb['centroid_world']).tolist()
                am = None if ag['centroid_world'] is None else (np.asarray(ag['centroid_world']) - ab['centroid_world']).tolist()
                thresholds.append({'threshold_projection_byte': t,
                                   'native_baseline_geometry': nb, 'android_baseline_geometry': ab,
                                   'native_evidence_centroid_movement_from_actual_baseline_world': nm,
                                   'android_evidence_centroid_movement_from_actual_baseline_world': am,
                                   'native_evidence_area_ratio_from_actual_baseline': ng['area_world2'] / nb['area_world2'],
                                   'android_evidence_area_ratio_from_actual_baseline': ag['area_world2'] / ab['area_world2'],
                                   'android_minus_native_evidence_centroid_movement_world': None if nm is None or am is None else (np.asarray(am) - nm).tolist()})
            region_rows.append({'region_id': rid, 'threshold_sensitivity': thresholds})
        rows.append({'stage_id': sid, 'native_baseline_source_png': str(source_path), 'android_actual_baseline_png': str(baseline_path),
                     'android_baseline_sha256': sha(baseline_path), 'all_stage_baseline_ROIs_byte_identical': True,
                     'color_regions': region_rows})
    out.mkdir(parents=True)
    chart = Image.new('RGB', (1500, 850), '#f5f6f8')
    draw = ImageDraw.Draw(chart)
    colors = {'left_blue': '#3e42b9', 'middle_red': '#c73437', 'right_green': '#218b46'}
    for col, sid in enumerate(('ingress75', 'full100', 'far50')):
        stage = next(row for row in rows if row['stage_id'] == sid)
        x0, y0 = 250 + 500 * col, 430
        scale = 60
        draw.text((col * 500 + 20, 20), sid + ' / color-evidence centroid movement', fill='black')
        draw.text((col * 500 + 20, 40), 'Own original baseline -> held; threshold8', fill='black')
        draw.line([(x0 - 230, y0), (x0 + 230, y0)], fill='#b0b0b0')
        draw.line([(x0, y0 - 310), (x0, y0 + 310)], fill='#b0b0b0')
        for tick in range(-3, 4):
            draw.text((x0 + tick * scale - 8, y0 + 5), str(tick), fill='#555555')
            if tick:
                draw.text((x0 + 5, y0 + tick * scale - 5), str(tick), fill='#555555')
        for ri, region in enumerate(stage['color_regions']):
            row = next(t for t in region['threshold_sensitivity'] if t['threshold_projection_byte'] == 8)
            color = colors[region['region_id']]
            for platform, key in [('native', 'native_evidence_centroid_movement_from_actual_baseline_world'),
                                  ('android', 'android_evidence_centroid_movement_from_actual_baseline_world')]:
                v = row[key]
                end = (x0 + v[0] * scale, y0 + v[1] * scale)
                draw.line([(x0, y0), end], fill=color, width=4 if platform == 'native' else 1)
                if platform == 'native':
                    draw.ellipse((end[0] - 5, end[1] - 5, end[0] + 5, end[1] + 5), fill=color)
                else:
                    draw.rectangle((end[0] - 5, end[1] - 5, end[0] + 5, end[1] + 5), outline=color, width=2)
                yy = 730 + ri * 28 + (0 if platform == 'native' else 13)
                draw.text((col * 500 + 20, yy), f'{region["region_id"]} {platform}: ({v[0]:+.3f},{v[1]:+.3f})', fill=color)
    draw.text((20, 820), 'Native: filled circle / thick line. Android: outlined square / thin line. Axes in world units; y grows downward. Centroids are NOT optical rays.', fill='black')
    chart_path = out / 'evidence-centroid-movement-own-baseline.png'
    chart.save(chart_path)
    report = {'schema': 1, 'status': 'descriptive_own_source_baseline_color_transport_no_ray_or_parity_claim',
              'shape_id': n['shape_id'], 'input_role': n.get('input_role', 'calibration'),
              'native_analysis': {'path': str(npth), 'sha256': sha(npth)}, 'android_analysis': {'path': str(apth), 'sha256': sha(apth)},
              'android_result': {'path': str(result_path), 'sha256': sha(result_path)},
              'script': {'path': str(Path(__file__).resolve()), 'sha256': sha(__file__)}, 'stages': rows,
              'figure': {'path': str(chart_path), 'sha256': sha(chart_path)},
              'limits': ['Actual Android source baseline is measured on its original density2.9750001 pixel grid, without normalizing to native2x.',
                         'Own baseline removes source integer rasterization/AA differences from centroid and area descriptors; it does not undo blur/refraction or assign optical rays.',
                         'Native uses unchanged original external source raster at exact375x667@2 mapping; Android baseline screenshots are byte-identical inside the frozen ROI across all six stages.',
                         'Independent color evidence cones, all components retained. Centroid movement can reflect visibility/attenuation as well as refraction.']}
    (out / 'baseline-transport.json').write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'status': report['status'], 'out': str(out)}))


if __name__ == '__main__':
    main()
