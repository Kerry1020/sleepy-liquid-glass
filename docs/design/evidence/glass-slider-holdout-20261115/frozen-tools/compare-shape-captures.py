#!/usr/bin/env python3
"""Compare descriptors of original same-source captures, with no image registration."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import math
from PIL import Image, ImageDraw


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def entry(path):
    return {'path': str(path), 'sha256': sha(path)}


def difference(a, b):
    return None if a is None or b is None else [y - x for x, y in zip(a, b)]


def descriptor(row):
    return {'area_world2': row['area_world2'], 'centroid_world': row['centroid_world'],
            'bounds_xyxy_world': row['bounds_xyxy_world'], 'principal_axes': row['principal_axes'],
            'covariance_world2': row['covariance_world2']}


def compare_geometry(native, android):
    nc, ac = native['centroid_world'], android['centroid_world']
    cd = difference(nc, ac)
    return {'native': descriptor(native), 'android': descriptor(android),
            'android_minus_native_centroid_world': cd,
            'centroid_distance_world': None if cd is None else math.hypot(*cd),
            'android_minus_native_bounds_xyxy_world': difference(native['bounds_xyxy_world'], android['bounds_xyxy_world']),
            'android_minus_native_area_world2': android['area_world2'] - native['area_world2'],
            'android_area_over_native_evidence_area': None if native['area_world2'] == 0 else android['area_world2'] / native['area_world2']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--android', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    np, ap, out = args.native.resolve(), args.android.resolve(), args.out.resolve()
    n, a = json.loads(np.read_text()), json.loads(ap.read_text())
    require(n['complete_six_stage_set'] and a['complete_six_stage_set'], 'Need complete saved six-stage analyses')
    require(n['shape_id'] == a['shape_id'], 'Declared shape identities differ')
    require(n.get('input_role', 'calibration') == a.get('input_role', 'calibration'), 'Declared source input roles differ')
    require(n['native_endpoint_validity']['source'] == 'strict_endpoint_verifier', 'Native endpoint validity is not strict-verifier-established')
    require(n['provenance']['original_source']['sha256'] == a['provenance']['original_source']['sha256'], 'Sources differ')
    require(n['provenance']['coverage_count_mask']['sha256'] == a['provenance']['coverage_count_mask']['sha256'], 'Source area masks differ')
    require(n['fixed_analysis_policy'] == a['fixed_analysis_policy'], 'Frozen analysis policy differs')
    require(not out.exists(), 'Refusing to overwrite comparison output')
    out.mkdir(parents=True)
    rows = []
    stages = {s['stage_id']: s for s in a['stages']}
    width, height, header = 352, 352, 82
    sheet = Image.new('RGB', (5 * width, (height + header) * 6), '#242424')
    draw = ImageDraw.Draw(sheet)
    source_info = n['source']['shape']
    source_file = Path(n['provenance']['original_source']['path'])
    roi = source_info['fixed_analysis_roi_xyxy_world']
    with Image.open(source_file) as im:
        source_tile = im.crop(tuple(int(v * 2) for v in roi)).convert('RGB')
    for i, ns in enumerate(n['stages']):
        sid = ns['stage_id']
        as_ = stages[sid]
        require(ns['pose_matched_flat_supplied'] and as_['pose_matched_flat_supplied'], 'Need pose-matched flat pairs')
        nc, ac = ns['actual_carrier_center_world'], as_['actual_carrier_center_world']
        regions = []
        for nr, ar in zip(ns['color_region_responses'], as_['color_region_responses']):
            require(nr['region_id'] == ar['region_id'], 'Region order differs')
            thresholds = []
            for nt, at in zip(nr['threshold_sensitivity'], ar['threshold_sensitivity']):
                require(nt['threshold_projection_byte'] == at['threshold_projection_byte'], 'Fixed threshold differs')
                thresholds.append({'threshold_projection_byte': nt['threshold_projection_byte'],
                                   **compare_geometry(nt['geometry'], at['geometry']),
                                   'native_component_count': len(nt['components_eight_connected_raster_order']),
                                   'android_component_count': len(at['components_eight_connected_raster_order']),
                                   'native_fixed_roi_boundary_pixels': nt['boundary_evidence_pixel_count'],
                                   'android_fixed_roi_boundary_pixels': at['boundary_evidence_pixel_count']})
            regions.append({'region_id': nr['region_id'], 'threshold_sensitivity': thresholds,
                            'native_color_statistics': nr['visible_color_statistics'],
                            'android_color_statistics': ar['visible_color_statistics'],
                            'native_inner_color_statistics': nr['visible_inner_color_statistics'],
                            'android_inner_color_statistics': ar['visible_inner_color_statistics'],
                            'native_boundary_color_statistics': nr['visible_boundary_color_statistics'],
                            'android_boundary_color_statistics': ar['visible_boundary_color_statistics']})
        native_fraction = ns['actual_public_bounds_source_overlap']['declared_capsule_source_area_fraction']
        android_fraction = as_['actual_public_bounds_source_overlap']['declared_capsule_source_area_fraction']
        rows.append({'stage_id': sid, 'requested_stage_label_only': ns['planned_stage'],
                     'native_actual_carrier_bounds_world_xywh': ns['actual_carrier_bounds_world_xywh'],
                     'android_actual_carrier_bounds_world_xywh': as_['actual_carrier_bounds_world_xywh'],
                     'android_minus_native_carrier_center_world': difference(nc, ac),
                     'native_actual_discrete_capsule_approximation': native_fraction,
                     'android_actual_discrete_capsule_approximation': android_fraction,
                     'native_source_render_scale_xy': ns.get('source_declared_world_to_actual_dp_scale_xy', [1, 1]),
                     'android_source_render_scale_xy': as_['source_declared_world_to_actual_dp_scale_xy'],
                     'native_mapping': ns['mapping'], 'android_mapping': as_['mapping'],
                     'color_regions': regions,
                     'whole_threshold_sensitivity': [{'threshold_projection_byte': nt['threshold_projection_byte'],
                                                       **compare_geometry(nt['geometry'], at['geometry'])}
                                                      for nt, at in zip(ns['threshold_sensitivity'], as_['threshold_sensitivity'])],
                     'native_ambiguity_flags': ns['ambiguity_flags'], 'android_ambiguity_flags': as_['ambiguity_flags']})
        paths = [None, np.parent / f'{sid}-original-roi.png', ap.parent / f'{sid}-original-roi.png',
                 np.parent / f'{sid}-color-region-evidence-white-ambiguous.png',
                 ap.parent / f'{sid}-color-region-evidence-white-ambiguous.png']
        labels = ['SOURCE canonical original', 'NATIVE original pixels', 'ANDROID original pixels', 'NATIVE fixed color evidence', 'ANDROID fixed color evidence']
        for col, (path, label) in enumerate(zip(paths, labels)):
            x, y = col * width, i * (height + header)
            tile = source_tile if path is None else Image.open(path).convert('RGB')
            draw.text((x + 5, y + 4), sid + ' / ' + label, fill='white')
            draw.text((x + 5, y + 20), 'Fixed44x44 world ROI; DISPLAY nearest only', fill='#bbbbbb')
            draw.text((x + 5, y + 36), f'Native actual capsule approx {native_fraction:.3%}', fill='#9ae4f5')
            draw.text((x + 5, y + 52), f'Android actual capsule approx {android_fraction:.3%}', fill='#9ae4f5')
            delta = difference(nc, ac)
            draw.text((x + 5, y + 68), f'Carrier delta A-N ({delta[0]:+.4f},{delta[1]:+.4f})', fill='#bbbbbb')
            sheet.paste(tile.resize((width, height), Image.Resampling.NEAREST), (x, y + header))
    sheet_path = out / 'native-android-fixed-world-contact-sheet.png'
    sheet.save(sheet_path)
    result = {'schema': 1, 'status': 'descriptive_same_source_color_transport_comparison_no_parity_score',
              'shape_id': n['shape_id'], 'input_role': n.get('input_role', 'calibration'),
              'native_analysis': entry(np), 'android_analysis': entry(ap),
              'script': entry(Path(__file__).resolve()), 'fixed_analysis_policy': n['fixed_analysis_policy'],
              'same_source_sha256': n['provenance']['original_source']['sha256'],
              'stages': rows, 'display_only_contact_sheet': entry(sheet_path),
              'limits': ['Original pixels keep actual native2x and Android2.9750001-density grids. No registration, image alignment, image normalization or optical contour completion.',
                         'Android original source was drawn into observed1116x1984 integer layout; exact exported source render scale is retained, never treated as ideal375x667dp.',
                         'Color cone masks describe observable evidence, not guaranteed object alpha or pixelwise optical rays. All disconnected parts and threshold variants retained.',
                         'Shape/flat subtraction removes static same-pose channel bias; colors are original encoded8bit channels without cross-device profile conversion.',
                         'Approximate capsules are discrete source-mask integrals based on public actual carrier bounds, not optical coverage or physical thickness.',
                         'Six static poses of one declared shape cannot establish all controls/sizes/materials or motion parity.']}
    (out / 'comparison.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'status': result['status'], 'stages': len(rows), 'out': str(out)}))


if __name__ == '__main__':
    main()
