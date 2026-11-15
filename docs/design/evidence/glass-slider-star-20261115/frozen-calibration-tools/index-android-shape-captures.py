#!/usr/bin/env python3
"""Normalize original fixed-shape Android evidence without touching device pixels."""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
from pathlib import Path


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def xywh(rect):
    return [rect[0], rect[1], rect[2] - rect[0], rect[3] - rect[1]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--result', type=Path, required=True)
    parser.add_argument('--spec', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    path, spec_path, output = args.result.resolve(), args.spec.resolve(), args.out.resolve()
    root = path.parent
    result, spec = json.loads(path.read_text()), json.loads(spec_path.read_text())
    receipt_path = root.parent / 'receipt.json'
    receipt = json.loads(receipt_path.read_text())
    require(result['schema'] == 1 and result['status'] == 'passed' and result['mode'] == 'fixed-shape-coverage', 'Not passed fixed-shape result')
    require(receipt['exit_code'] == 0 and receipt['test_passed'] is True, 'Host instrumentation receipt failed')
    require(sha(spec_path) == result['shape_plan_sha256'] == receipt['input_sha256']['shape-spec.json'], 'Source specification SHA differs')
    require(result['shape_plan'] == spec, 'Exported embedded source plan differs')
    file_receipts = {row['file']: row for row in receipt['files']}
    require(len(file_receipts) == len(receipt['files']) == 49, 'Expected49 distinct original result/image receipts')
    for relative, row in file_receipts.items():
        original = root.parent / relative
        require(row['host_device_match'] is True and sha(original) == row['sha256'], f'Host/device original hash mismatch: {relative}')
    expected = {(stage['id'], role) for stage in spec['stages'] for role in ('shape', 'flat')}
    actual = collections.Counter((row['stage_id'], row['source_role']) for row in result['captures'])
    require(set(actual) == expected and all(n == 1 for n in actual.values()) and len(result['captures']) == 12, 'Expected six stages by shape/flat, exactly once')
    require(len(result['coverage_stages']) == 6, 'Missing coverage stage results')
    captures = []
    checks = []
    for stage in result['coverage_stages']:
        require(stage['pair_position_validation'] == 'passed' and stage['pair_carrier_center_delta_dp'] == [0, 0]
                and stage['pair_value_delta'] == 0, 'Actual shape/flat carrier pose differs')
        pair = {role: next(row for row in result['captures'] if row['stage_id'] == stage['stage_id'] and row['source_role'] == role)
                for role in ('shape', 'flat')}
        for role, row in pair.items():
            require(row['phase'] == 'held' and row['pointer_down'] is True and not row['finish_events'], 'Capture was not held before commit')
            dispatched = row['dispatched_pointer_events']
            require([event['type'] for event in dispatched] == ['Press', 'Move', 'Move'], 'Expected delivered DOWN and two MOVE events')
            require(all(len(event['changes']) == 1 and event['changes'][0]['pressed'] is True
                        and event['changes'][0]['consumed_by_production_at_final_pass'] is True for event in dispatched), 'Real production pointer not consumed/pressed')
            begin, end = row['capture_begin_wall_uptime_ms'], row['capture_end_wall_uptime_ms']
            last_move = dispatched[-1]['wall_uptime_ms']
            injected = [e for e in result['input_events'] if e['scene'] == row['scene']]
            require([e['action'] for e in injected] == ['DOWN', 'MOVE_ESTABLISH_SLOP', 'MOVE_TARGET', 'CANCEL'], 'Unexpected injection sequence')
            require(last_move < begin < end < injected[-1]['wall_uptime_ms'], 'Capture not wholly between actual MOVE and cleanup CANCEL')
            require(row['compose_ms'] - dispatched[-1]['compose_ms'] >= 1600, 'Compose settling interval below declared1600ms')
            attempts = row['display_readiness']['attempts']
            require(attempts and attempts[-1]['matched_fraction_rgb_tolerance3'] >= .995, 'Display readiness did not pass unchanged RGB3/99.5%')
            source = row['geometry']['background_world']['source']
            require(source['screen_origin_px'] == [0, 0] and source['local_to_screen_unit_basis_px'] == [[0, 0], [1, 0], [0, 1]], 'Source world is not observed untranslated unit axes')
            checks.append({'stage_id': stage['stage_id'], 'role': role, 'scene': row['scene'], 'capture_begin_wall_uptime_ms': begin,
                           'capture_end_wall_uptime_ms': end, 'last_move_dispatch_wall_uptime_ms': last_move,
                           'settle_wall_ms': begin - last_move, 'settle_compose_ms': row['compose_ms'] - dispatched[-1]['compose_ms'],
                           'cleanup_cancel_wall_uptime_ms': injected[-1]['wall_uptime_ms'],
                           'scope': 'actual observed static pointer/readiness evidence; no dynamic or optical acceptance'})
        shape, flat = pair['shape'], pair['flat']
        source = shape['geometry']['background_world']['source']
        require(source == flat['geometry']['background_world']['source'], 'Shape/flat source mapping differs')
        density, origin = source['density'], source['screen_origin_px']
        shape_bounds = xywh(shape['geometry']['visual_carrier_world_rect_dp'])
        flat_bounds = xywh(flat['geometry']['visual_carrier_world_rect_dp'])
        holder = shape['geometry']['outer_holder']['screen_rect_px']
        holder_world = [(holder[0] - origin[0]) / density, (holder[1] - origin[1]) / density,
                        (holder[2] - holder[0]) / density, (holder[3] - holder[1]) / density]
        mapping = {'world_origin_window_px': origin, 'pixels_per_world_unit': density,
                   'actual_control_bounds_world_xywh': holder_world, 'actual_carrier_bounds_world_xywh': flat_bounds}
        captures.append({'stage_id': stage['stage_id'], 'shape_id': result['shape_id'], 'input_id': shape['input_id'],
                         'run': result['run_id'] + '/' + shape['scene'], 'png': str(root / shape['screen_png']),
                         'sha256': sha(root / shape['screen_png']), 'world_origin_window_px': origin,
                         'pixels_per_world_unit': density, 'source_world_xywh': [0, 0, 375, 667],
                         'source_layout_geometry': source,
                         'source_declared_world_to_actual_dp_scale_xy': [source['layout_size_px'][0] / density / 375,
                                                                         source['layout_size_px'][1] / density / 667],
                         'actual_control_bounds_world_xywh': holder_world,
                         'bounds_kind': 'actual attached production touch-holder layout, not native optical alpha',
                         'actual_carrier_bounds_world_xywh': shape_bounds,
                         'carrier_bounds_scope': 'actual attached affine visual carrier corners excluding shadow, not optical alpha',
                         'flat_png': str(root / flat['screen_png']), 'flat_sha256': sha(root / flat['screen_png']),
                         'flat_actual_carrier_bounds_world_xywh': flat_bounds, 'flat_geometry': mapping,
                         'android_evidence_json': str(path), 'android_receipt_json': str(receipt_path),
                         'android_stage_source': stage['requested_stage'], 'android_actual_target_center_world': stage['actual_carrier_target_center_world_pt'],
                         'capture_checks': [check for check in checks if check['stage_id'] == stage['stage_id']]})
    index = {'schema': 1, 'platform': 'android', 'status': 'original_hashes_pointer_and_pair_checks_passed',
             'shape_spec': str(spec_path), 'captures': captures,
             'source_result': {'path': str(path), 'sha256': sha(path)},
             'host_receipt': {'path': str(receipt_path), 'sha256': sha(receipt_path)},
             'adapter': {'path': str(Path(__file__).resolve()), 'sha256': sha(__file__)},
             'limits': ['Source is originally drawn into actual integer layout1116x1984, density2.975; no @2 normalization or registration.',
                        'Declared source world-to-render scale is exported. It is not a recovered optical transform.',
                        'Actual pointers/readiness validate settled capture, not millisecond trajectory or full native parity.']}
    require(not output.exists(), 'Refusing to overwrite an existing index')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(index, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'status': index['status'], 'pairs': len(captures), 'index': str(output)}))


if __name__ == '__main__':
    main()
