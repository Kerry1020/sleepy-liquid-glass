#!/usr/bin/env python3
"""Bounded descriptor deltas at already-frozen thresholds; no aggregate parity score."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def compare_descriptor(native, baseline, candidate):
    def value(g):
        center = None if g['centroid_world'] is None or native['centroid_world'] is None else math.dist(g['centroid_world'], native['centroid_world'])
        bbox = None if g['bounds_xyxy_world'] is None or native['bounds_xyxy_world'] is None else [a - b for a, b in zip(g['bounds_xyxy_world'], native['bounds_xyxy_world'])]
        return {'area_world2': g['area_world2'], 'centroid_world': g['centroid_world'], 'bounds_xyxy_world': g['bounds_xyxy_world'],
                'centroid_distance_from_native_world': center, 'absolute_area_difference_from_native_world2': abs(g['area_world2'] - native['area_world2']),
                'signed_bbox_difference_from_native_world': bbox}
    old, new = value(baseline), value(candidate)
    def delta(key):
        x, y = old[key], new[key]
        if x is None or y is None:
            return {'change': None, 'direction': 'unobserved_no_forced_identity'}
        return {'change': y - x, 'direction': 'smaller_native_error' if y < x else 'larger_native_error' if y > x else 'equal'}
    return {'native_geometry': native, 'baseline': old, 'candidate': new,
            'centroid_error_change': delta('centroid_distance_from_native_world'),
            'area_error_change': delta('absolute_area_difference_from_native_world2'),
            'candidate_minus_baseline_bbox_world': None if old['bounds_xyxy_world'] is None or new['bounds_xyxy_world'] is None else
                [y - x for x, y in zip(old['bounds_xyxy_world'], new['bounds_xyxy_world'])]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    paths = [args.native.resolve(), args.baseline.resolve(), args.candidate.resolve()]
    n, a, b = [json.loads(path.read_text()) for path in paths]
    require(all(x['complete_six_stage_set'] for x in (n, a, b)), 'All analyses need complete original six-stage sets')
    require(n['shape_id'] == a['shape_id'] == b['shape_id'], 'Declared shape identities differ')
    require(n.get('input_role', 'calibration') == a.get('input_role', 'calibration') == b.get('input_role', 'calibration'),
            'Declared source input roles differ')
    require(n['fixed_analysis_policy'] == a['fixed_analysis_policy'] == b['fixed_analysis_policy'], 'Frozen analysis policies differ')
    require(len({x['provenance']['original_source']['sha256'] for x in (n, a, b)}) == 1, 'Original source hashes differ')
    rows = []
    for ns, old, new in zip(n['stages'], a['stages'], b['stages']):
        require(ns['stage_id'] == old['stage_id'] == new['stage_id'], 'Stage order differs')
        for key in ('actual_carrier_bounds_world_xywh', 'actual_carrier_center_world', 'mapping', 'source_declared_world_to_actual_dp_scale_xy'):
            require(old[key] == new[key], 'Candidate changed original stage geometry or source mapping: ' + key)
        regions = []
        for nr, ar, br in zip(ns['color_region_responses'], old['color_region_responses'], new['color_region_responses']):
            require(nr['region_id'] == ar['region_id'] == br['region_id'], 'Region identity differs')
            thresholds = []
            for nt, at, bt in zip(nr['threshold_sensitivity'], ar['threshold_sensitivity'], br['threshold_sensitivity']):
                require(nt['threshold_projection_byte'] == at['threshold_projection_byte'] == bt['threshold_projection_byte'], 'Thresholds differ')
                thresholds.append({'threshold_projection_byte': nt['threshold_projection_byte'],
                                   **compare_descriptor(nt['geometry'], at['geometry'], bt['geometry']),
                                   'native_component_count': len(nt['components_eight_connected_raster_order']),
                                   'baseline_component_count': len(at['components_eight_connected_raster_order']),
                                   'candidate_component_count': len(bt['components_eight_connected_raster_order']),
                                   'candidate_roi_boundary_pixels': bt['boundary_evidence_pixel_count']})
            regions.append({'region_id': nr['region_id'], 'threshold_sensitivity': thresholds})
        rows.append({'stage_id': ns['stage_id'], 'baseline_candidate_geometry_and_source_mapping_identical': True,
                     'actual_carrier_bounds_world_xywh': new['actual_carrier_bounds_world_xywh'],
                     'actual_discrete_capsule_source_area_fraction': new['actual_public_bounds_source_overlap']['declared_capsule_source_area_fraction'],
                     'color_regions': regions,
                     'whole_threshold_sensitivity': [{'threshold_projection_byte': nt['threshold_projection_byte'],
                                                       **compare_descriptor(nt['geometry'], at['geometry'], bt['geometry'])}
                                                      for nt, at, bt in zip(ns['threshold_sensitivity'], old['threshold_sensitivity'], new['threshold_sensitivity'])]})
    output = args.out.resolve()
    require(not output.exists(), 'Refusing to overwrite candidate difference report')
    report = {'schema': 1, 'status': 'bounded_descriptor_changes_at_frozen_thresholds_no_combined_acceptance_score',
              'shape_id': n['shape_id'], 'input_role': n.get('input_role', 'calibration'),
              'inputs': {key: {'path': str(path), 'sha256': sha(path)} for key, path in zip(('native', 'baseline', 'candidate'), paths)},
              'script': {'path': str(Path(__file__).resolve()), 'sha256': sha(__file__)},
              'fixed_analysis_policy': n['fixed_analysis_policy'], 'stages': rows,
              'limits': ['Smaller/larger error refers only to the named observable descriptor, not complete shape fidelity or optical parity.',
                         'Centroids and area can change due to visibility/attenuation and multi-component color evidence; no pointwise ray identities are assigned.',
                         'All four frozen thresholds and all stage/region results are reported; no threshold expansion or favorable stage selection.']}
    output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'status': report['status'], 'out': str(output)}))


if __name__ == '__main__':
    main()
