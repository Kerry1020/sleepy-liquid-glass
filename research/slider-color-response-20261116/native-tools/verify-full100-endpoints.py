#!/usr/bin/env python3
"""Independently verify fixed-source native endpoint captures, preserving failures.

This verifies input identity, touch clocks, PNG integrity and public presented
carrier pose. It does not infer a native optical alpha contour or certify optical
stability from an unchanged public rectangle/transform.
"""
import argparse
import collections
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys


DEFAULT_PNG_VALIDATOR = Path(__file__).resolve().parents[2] / 'slider-fixtures/tools/native-glass-reference/verify-static-optics.py'
LIMITS = {
    'target_tolerance_pt': 1.0,
    'minimum_after_last_move_seconds': 0.65,
    'minimum_geometry_frames': 4,
    'maximum_geometry_gap_seconds': 0.05,
    'geometry_range_pt': 0.1,
    'matrix_range': 0.001,
    'opacity_range': 0.01,
}
RECT_KEYS = ('x', 'y', 'w', 'h')
GEOMETRY_KEYS = RECT_KEYS + ('boundsX', 'boundsY', 'boundsW', 'boundsH',
                           'positionX', 'positionY', 'anchorPointX', 'anchorPointY')
MATRIX_KEYS = ('m11', 'm22', 'm12', 'm21', 'm41', 'm42')
OPACITY_KEYS = ('opacity', 'effectiveOpacity')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def safe_run(value):
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', value)[:180].strip('.')


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def distance(point, other):
    return math.hypot(point['x'] - other['x'], point['y'] - other['y'])


def bounds(view):
    return [view[key] for key in RECT_KEYS]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_rows(path):
    rows = []
    for number, line in enumerate(Path(path).read_text().splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(f'{path.name} line{number}: {error}') from error
    return rows


def json_safe(value):
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def presented_pair(frame):
    require(frame.get('truncated') is False, 'Presentation traversal is truncated or unqualified')
    owners = [v for v in frame['views'] if v.get('identifier') == 'swiftui-slider']
    require(len(owners) == 1, f'Expected one native Slider owner, got {len(owners)}')
    owner = owners[0]
    candidates = [v for v in frame['views']
                  if v['path'].startswith(owner['path'] + '/') and 'LiquidLens' in v.get('class', '')
                  and not v.get('effectiveHidden', v.get('hidden', False))
                  and v.get('effectiveOpacity', 0) > 0.5]
    require(len(candidates) == 1, f'Expected one visible lens under Slider, got {len(candidates)}')
    lens = candidates[0]
    for label, view in [('owner', owner), ('lens', lens)]:
        require(view.get('presentationAvailable') is True, f'{label} uses model fallback, not a presented layer')
        require(view.get('effectiveHidden') is False and view.get('hidden') is False,
                f'{label} is hidden or visibility is unqualified')
        require(view.get('effectiveOpacity', 0) > 0.5, f'{label} is not sufficiently visible')
        require(all(finite(view.get(key)) for key in GEOMETRY_KEYS + MATRIX_KEYS + OPACITY_KEYS),
                f'{label} has missing or nonfinite pose fields')
        require(view['w'] > 0 and view['h'] > 0, f'{label} has empty bounds')
    return owner, lens


def pose_span(pairs, index):
    result = {}
    for label, keys, tolerance in [('geometry', GEOMETRY_KEYS, LIMITS['geometry_range_pt']),
                                   ('matrix', MATRIX_KEYS, LIMITS['matrix_range']),
                                   ('opacity', OPACITY_KEYS, LIMITS['opacity_range'])]:
        spans = {key: max(pair[index][key] for pair in pairs) - min(pair[index][key] for pair in pairs)
                 for key in keys}
        result[label] = {'ranges': spans, 'limit': tolerance,
                         'stable': all(value <= tolerance + 1e-9 for value in spans.values())}
    result['same_class_and_path'] = len({(pair[index]['class'], pair[index]['path']) for pair in pairs}) == 1
    # Native special contours can expose a nonfinite public cornerRadius,
    # serialized as null by the recorder. It is an optional diagnostic, never
    # evidence that the required bounds/transform/opacity sample is invalid.
    corner_values = [pair[index].get('cornerRadius') for pair in pairs]
    known_corners = [value for value in corner_values if finite(value)]
    result['cornerRadiusObservation'] = {
        'scope': 'optional public getter; unknown does not infer a radius or optical contour',
        'values': corner_values,
        'knownSamples': len(known_corners),
        'unknownSamples': len(corner_values) - len(known_corners),
        'status': 'known' if len(known_corners) == len(corner_values) else 'unknown_or_partial',
        'knownMinimum': min(known_corners) if known_corners else None,
        'knownMaximum': max(known_corners) if known_corners else None,
    }
    result['stable'] = result['same_class_and_path'] and all(result[k]['stable'] for k in ['geometry', 'matrix', 'opacity'])
    return result


def verify_capture(event, out, spec, manifest, input_by_id, stage_by_id, validate_png):
    report = {'event': event, 'verifiedHeldEndpoint': False, 'errors': []}
    errors = report['errors']

    def check(condition, message):
        if not condition:
            errors.append(message)

    try:
        stage_id, input_id = event['coverageLabel'], event['inputID']
        require(stage_id in stage_by_id, 'Unknown coverage stage')
        require(input_id in [spec['first_input_id'], spec['flat_input_id']], 'Unexpected input in first-shape feasibility')
        stage, expected = stage_by_id[stage_id], input_by_id[input_id]
        check(event['shapeID'] == spec['first_input_id'], 'Event shapeID differs from spec first_input_id')
        check(event.get('isFlatControl') is (input_id == spec['flat_input_id']), 'isFlatControl disagrees with input identity')
        planned_target = dict(zip(('x', 'y'), stage['requested_finger_world_pt']))
        check(distance(event['requestedTargetPoint'], planned_target) <= 1e-6, 'Requested endpoint differs from this spec stage')
        planned_center = dict(zip(('x', 'y'), stage['requested_lens_center_world_pt']))
        check(distance(event['nominalLensCenterPt'], planned_center) <= 1e-6, 'Nominal carrier center differs from this spec stage')
        check(event.get('captureMode') == 'drag-endpoint-held', 'Event is not an endpoint-hold signal')
        check(event.get('exitCode') == 0 and 'observerError' not in event, 'Observer failed or did not finish its screenshot')
        run = safe_run(event['run'])
        require(bool(run), 'Empty sanitized run ID')
        folder = out / 'traces' / run
        session = read_json(folder / 'session.json')
        rows = read_rows(folder / 'trace.jsonl')
        external = read_json(folder / 'external-input-metadata.json')
        marker = read_json(folder / 'slider-fixed-shape-coverage-metadata.json')
        report.update(run=run, session=session, externalInput=external,
                      trace_jsonl=str(folder / 'trace.jsonl'), session_json=str(folder / 'session.json'))
        check(session.get('run') == run, 'Session run identity disagrees with event/run directory')
        check('26.5' in session.get('os', '') and '23F77' in session.get('os', ''), 'Unexpected native OS reference')
        check(session.get('sliderFixedShapeCoverage') is True and session.get('sliderLayerProbe') is True,
              'Required native fixed-shape observation capability is absent')
        check(session.get('interfaceStyle') == 1 and event.get('requestedTheme') == 'light', 'First feasibility must use light traits')
        check(not session.get('reduceMotion') and not session.get('reduceTransparency'), 'Accessibility settings changed reference material/motion')
        check([session.get(k) for k in ('screenWidthPt', 'screenHeightPt', 'screenScale')] == [375, 667, 2],
              'Session world is not native375x667pt @2')
        check(all(external.get(key) == value for key, value in {
            'id': input_id, 'file': expected['file'], 'sha256': expected['sha256'],
            'set_id': manifest['set_id'], 'split': manifest['split'], 'worldOriginPt': [0, 0],
            'worldSizePt': [375, 667], 'pixelsPerPt': 2, 'sizePx': [750, 1334],
            'requestedInterfaceStyle': 'light', 'windowEffectiveInterfaceStyle': 1,
        }.items()), 'External input identity, hash, world or traits disagree with manifest/event')
        for key in ('canvasRectInWindowPt', 'windowRectPt'):
            check(external.get(key) == {'x': 0, 'y': 0, 'w': 375, 'h': 667}, f'{key} changed fixed world geometry')
        original = folder / 'background-input.png'
        check(sha(original) == expected['sha256'], 'Exported original background bytes do not match the registered input')
        check(marker.get('inputID') == input_id and marker.get('inputSHA256') == expected['sha256']
              and marker.get('set_id') == manifest['set_id'], 'Fixed-shape capability metadata names a different input')
        original_png = validate_png(original.read_bytes(), (750, 1334))
        report['originalPNGValidation'] = original_png
        png = Path(event['path'])
        if not png.is_absolute():
            png = out / png
        png = png.resolve()
        require(png.is_relative_to(out), 'Held PNG path escaped this capture directory')
        image = png.read_bytes()
        report.update(png=str(png), imageSHA256=hashlib.sha256(image).hexdigest(),
                      pngValidation=validate_png(image, (750, 1334)))

        origin = session['originUnixSeconds']
        begin = event['screenshotBeginUnixSeconds'] - origin
        end = event['screenshotEndUnixSeconds'] - origin
        require(all(finite(v) for v in (origin, begin, end)), 'Nonfinite screenshot/session clocks')
        require(begin < end, 'Screenshot receipt has empty or reversed interval')
        report.update(captureBeginT=begin, captureEndT=end)
        delivered = [r for r in rows if r.get('event') == 'touch' and r.get('source') == 'delivery']
        downs = [r for r in delivered if r.get('phase') == 0]
        ends = [r for r in delivered if r.get('phase') in (3, 4)]
        require(len(downs) == len(ends) == 1, 'Expected exactly one complete delivered gesture')
        down, ended = downs[0], ends[0]
        touch_id = down['touchID']
        require(ended['touchID'] == touch_id and all(r['touchID'] == touch_id for r in delivered),
                'Touch identity changes within the run')
        require(all(finite(r.get(clock)) for r in delivered for clock in ('sampleT', 'deliveredT')),
                'Delivered touch clocks are missing or nonfinite')
        check(ended['phase'] == 3, 'Gesture ended with CANCEL rather than public UP')
        check(distance(down, event['initialPoint']) <= LIMITS['target_tolerance_pt'], 'Actual DOWN differs from the recorded initial point')
        check(distance(event['initialPoint'], {'x': 113.5, 'y': 430}) <= 1e-6, 'Initial public press changed source72 anchor')
        for clock in ('sampleT', 'deliveredT'):
            check(origin + down[clock] >= event['requestedAtUnixSeconds'], f'{clock}: DOWN predates the durable request')
            check(down[clock] < begin < end < ended[clock], f'{clock}: screenshot is not fully inside this DOWN/UP interval')
        samples = [r for r in rows if r.get('event') == 'touch' and r.get('touchID') == touch_id
                   and r.get('source') in ('delivery', 'coalesced')]
        require(all(finite(r.get(clock)) for r in samples for clock in ('sampleT', 'deliveredT')),
                'Actual touch sample clocks are missing or nonfinite')
        moves = [r for r in samples if r.get('phase') == 1]
        require(bool(moves), 'Gesture contains no actual moved input')
        last_moves = {}
        for clock in ('sampleT', 'deliveredT'):
            clock_moves = [r for r in moves if clock != 'deliveredT' or r.get('source') == 'delivery']
            before = [r for r in clock_moves if r[clock] <= begin]
            require(bool(before), f'{clock}: no moved sample before capture')
            last = max(before, key=lambda r: r[clock])
            last_moves[clock] = last
            check(last[clock] + LIMITS['minimum_after_last_move_seconds'] <= begin,
                  f'{clock}: capture starts before last MOVE plus0.65s')
            check(distance(last, event['requestedTargetPoint']) <= LIMITS['target_tolerance_pt'],
                  f'{clock}: actual final moved endpoint misses requested target')
            check(not any(begin <= r[clock] <= end for r in moves), f'{clock}: actual movement occurs during screenshot')
        report.update(actualDown=down, actualEnd=ended, actualLastMoves=last_moves,
                      actualInputSamples=len(samples), actualMoveSamples=len(moves),
                      inputClockScope='Both sampleT and deliveredT independently bound capture and last MOVE; includes coalesced moves')

        frames = sorted([r for r in rows if r.get('event') == 'frame'], key=lambda r: r['captureStartT'])
        before = [r for r in frames if r['captureEndT'] <= begin]
        after = [r for r in frames if r['captureStartT'] >= end]
        require(before and after, 'Presented pose samples do not bracket both screenshot endpoints')
        # A bounded50ms context on each side permits >=4 real samples even for
        # a fast screenshot. Neither side may be replaced by an inferred pose.
        selected = [r for r in frames
                    if r['captureEndT'] >= begin - LIMITS['maximum_geometry_gap_seconds']
                    and r['captureStartT'] <= end + LIMITS['maximum_geometry_gap_seconds']]
        require(selected and selected[0]['captureEndT'] <= begin and selected[-1]['captureStartT'] >= end,
                'Presented pose context does not actually span both screenshot endpoints')
        first, final = selected[0], selected[-1]
        gap_before, gap_after = begin - first['captureEndT'], final['captureStartT'] - end
        starts = [r['captureStartT'] for r in selected]
        max_gap = max([b - a for a, b in zip(starts, starts[1:])] or [float('inf')])
        check(len(selected) >= LIMITS['minimum_geometry_frames'], 'Insufficient presented samples across complete screenshot bracket')
        check(max(gap_before, gap_after, max_gap) <= LIMITS['maximum_geometry_gap_seconds'],
              'Presented sampling has a gap greater than0.05s across screenshot bracket')
        require(all(finite(r.get('captureStartT')) and finite(r.get('captureEndT'))
                    and r['captureStartT'] <= r['captureEndT'] for r in selected), 'Invalid pose sampling brackets')
        pairs = [presented_pair(r) for r in selected]
        owner_stability, lens_stability = pose_span(pairs, 0), pose_span(pairs, 1)
        check(owner_stability['stable'], 'Slider presented owner bounds/transform/opacity changed across screenshot')
        check(lens_stability['stable'], 'Native presented carrier bounds/transform/opacity changed across screenshot')
        midpoint = (begin + end) / 2
        representative_index = min(range(len(selected)),
                                   key=lambda i: abs((selected[i]['captureStartT'] + selected[i]['captureEndT']) / 2 - midpoint))
        owner, lens = pairs[representative_index]
        check(all(abs(a - b) <= 0.5 for a, b in zip(bounds(owner), [20, 414, 335, 31])),
              'Presented native Slider owner changed original source72 control geometry')
        report.update(actualControlBoundsPt=bounds(owner), actualCarrierBoundsPt=bounds(lens),
                      actualCarrierCenterPt=[lens['x'] + lens['w'] / 2, lens['y'] + lens['h'] / 2],
                      presentedSampling={'frames': len(selected), 'gapBeforeSeconds': gap_before,
                                         'gapAfterSeconds': gap_after, 'maximumStartGapSeconds': max_gap,
                                         'firstCaptureStartT': first['captureStartT'], 'lastCaptureEndT': final['captureEndT'],
                                         'representativeCaptureStartT': selected[representative_index]['captureStartT'],
                                         'representativeCaptureEndT': selected[representative_index]['captureEndT']},
                      ownerPoseStability=owner_stability, carrierPoseStability=lens_stability,
                      poseScope='Actual public presented owner/carrier fields only; no optical alpha or optical-stability inference',
                      presentedPoseSamples=[{'captureStartT': frame['captureStartT'], 'captureEndT': frame['captureEndT'],
                                             'owner': pair[0], 'carrier': pair[1]} for frame, pair in zip(selected, pairs)])
    except Exception as error:
        errors.append(f'{type(error).__name__}: {error}')
    report['verifiedHeldEndpoint'] = not errors
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--spec', required=True, type=Path)
    parser.add_argument('--png-validator', type=Path, default=DEFAULT_PNG_VALIDATOR)
    args = parser.parse_args()
    out, spec_path = args.out.resolve(), args.spec.resolve()
    summary = {'schema': 1, 'status': 'failed', 'limits': LIMITS, 'errors': [], 'observations': [],
               'scope': 'Independent fixed-source identity, complete input brackets, PNG integrity and public presented pose; no optical parity or alpha claim',
               'spec': str(spec_path), 'verifierSHA256': sha(__file__)}
    captures = []
    try:
        require(out.is_dir(), 'Capture output directory does not exist')
        spec = read_json(spec_path)
        manifest_path = spec_path.parent / 'inputs/manifest.json'
        manifest = read_json(manifest_path)
        require(spec.get('schema') == 1 and manifest.get('schema') == 1, 'Unsupported spec or input manifest schema')
        require(len(spec['stages']) == 6 and len(manifest['inputs']) == 8, 'Expected six planned stages and eight registered inputs')
        stage_by_id = {row['id']: row for row in spec['stages']}
        input_by_id = {row['id']: row for row in manifest['inputs']}
        require(len(stage_by_id) == 6 and len(input_by_id) == 8, 'Duplicate spec stages or input identities')
        require(spec.get('scheduled_stages') == ['full100'], 'Expected explicitly scheduled full100-only protocol')
        stage_by_id = {'full100': stage_by_id['full100']}
        require(spec['first_input_id'] != spec['flat_input_id'], 'Shape and flat identities are the same')
        require(all(i in input_by_id for i in [spec['first_input_id'], spec['flat_input_id']]), 'Missing shape/flat manifest entry')
        summary.update(specSHA256=sha(spec_path), manifestSHA256=sha(manifest_path),
                       sourceSetID=manifest['set_id'], shapeID=spec['first_input_id'], flatID=spec['flat_input_id'])
        for row in manifest['inputs']:
            source = (manifest_path.parent / row['file']).resolve()
            require(source.is_relative_to(manifest_path.parent.resolve()), 'Manifest source escaped its registered directory')
            require(sha(source) == row['sha256'], f'Original registered input hash differs: {row["id"]}')
        module_spec = importlib.util.spec_from_file_location('strict_endpoint_png_validator', args.png_validator.resolve())
        validator = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(validator)
        summary['pngValidatorSHA256'] = sha(args.png_validator)
        events = read_rows(out / 'held/capture-events.jsonl')
        expected = {(stage_id, input_id) for stage_id in stage_by_id
                    for input_id in [spec['first_input_id'], spec['flat_input_id']]}
        actual = collections.Counter((e.get('coverageLabel'), e.get('inputID')) for e in events)
        missing = sorted(expected - set(actual))
        unexpected = sorted(set(actual) - expected, key=str)
        duplicates = [{'stage_id': key[0], 'input_id': key[1], 'count': count}
                      for key, count in actual.items() if count != 1]
        summary['matrix'] = {'expectedCaptures': 2, 'actualCaptures': len(events),
                             'missing': missing, 'unexpected': unexpected, 'duplicates': duplicates}
        if len(events) != 2 or missing or unexpected or duplicates:
            summary['errors'].append('Capture matrix is not exactly full100 × one shape and one flat')
        run_counts = collections.Counter(e.get('run') for e in events)
        if any(n != 1 for n in run_counts.values()):
            summary['errors'].append('Each capture must own a unique fresh native run')
        for event in events:
            summary['observations'].append(verify_capture(event, out, spec, manifest, input_by_id, stage_by_id, validator.validate_png))
        for row in summary['observations']:
            if not row['verifiedHeldEndpoint']:
                continue
            event = row['event']
            if event['isFlatControl']:
                continue
            flats = [r for r in summary['observations'] if r['event'].get('coverageLabel') == event['coverageLabel']
                     and r['event'].get('inputID') == spec['flat_input_id']]
            if len(flats) != 1 or not flats[0]['verifiedHeldEndpoint']:
                row['errors'].append('No unique strictly verified flat at the same stage')
            else:
                flat = flats[0]
                if max(abs(a - b) for a, b in zip(row['actualCarrierBoundsPt'], flat['actualCarrierBoundsPt'])) > LIMITS['geometry_range_pt']:
                    row['errors'].append('Shape and flat actual presented carrier rectangles differ by more than0.1pt')
                if max(abs(a - b) for a, b in zip(row['actualControlBoundsPt'], flat['actualControlBoundsPt'])) > LIMITS['geometry_range_pt']:
                    row['errors'].append('Shape and flat actual presented control rectangles differ by more than0.1pt')
            row['verifiedHeldEndpoint'] = not row['errors']
            if not row['verifiedHeldEndpoint']:
                continue
            flat_geometry = {'world_origin_window_px': [0, 0], 'pixels_per_world_unit': 2,
                             'actual_control_bounds_world_xywh': flat['actualControlBoundsPt'],
                             'actual_carrier_bounds_world_xywh': flat['actualCarrierBoundsPt']}
            captures.append({'stage_id': event['coverageLabel'], 'coverage_label': event['coverageLabel'],
                             'shape_id': event['shapeID'], 'input_id': event['inputID'], 'run': event['run'],
                             'png': row['png'], 'sha256': row['imageSHA256'], 'is_flat_control': False,
                             'world_origin_window_px': [0, 0], 'pixels_per_world_unit': 2,
                             'source_world_xywh': [0, 0, 375, 667],
                             'actual_control_bounds_world_xywh': row['actualControlBoundsPt'],
                             'bounds_kind': 'actual public presented native Slider owner bounds; not optical alpha',
                             'actual_carrier_bounds_world_xywh': row['actualCarrierBoundsPt'],
                             'carrier_bounds_scope': 'actual public presented carrier rectangle; not optical alpha or optical-stability proof',
                             'receipt_json': str(out / 'endpoint-verification-strict.json'),
                             'session_json': row['session_json'], 'trace_jsonl': row['trace_jsonl'],
                             'flat_png': flat['png'], 'flat_sha256': flat['imageSHA256'],
                             'flat_actual_carrier_bounds_world_xywh': flat['actualCarrierBoundsPt'],
                             'flat_geometry': flat_geometry})
        summary['captures'] = len(events)
        summary['verifiedHeldEndpoints'] = sum(row['verifiedHeldEndpoint'] for row in summary['observations'])
        summary['verifiedShapeFlatPairs'] = len(captures)
        if summary['verifiedHeldEndpoints'] != 2 or len(captures) != 1:
            summary['errors'].append('At least one endpoint or shape/flat pair failed strict verification')
        summary['status'] = 'passed' if not summary['errors'] else 'failed'
    except Exception as error:
        summary['errors'].append(f'{type(error).__name__}: {error}')
    # Keep every failed receipt and reason. Partial index entries stay explicitly
    # labelled failed; downstream analysis must not treat them as a full matrix.
    out.mkdir(parents=True, exist_ok=True)
    (out / 'endpoint-verification-strict.json').write_text(json.dumps(json_safe(summary), indent=2, allow_nan=False) + '\n')
    index = {'schema': 1, 'platform': 'ios', 'status': summary['status'], 'shape_manifest': str(spec_path),
             'strict_verification_json': str(out / 'endpoint-verification-strict.json'),
             'expected_shape_captures': 1, 'verified_shape_captures': len(captures), 'captures': captures}
    (out / 'index-strict.json').write_text(json.dumps(json_safe(index), indent=2, allow_nan=False) + '\n')
    print(json.dumps({'status': summary['status'], 'verifiedHeldEndpoints': summary.get('verifiedHeldEndpoints', 0),
                      'verifiedShapeFlatPairs': len(captures), 'report': str(out / 'endpoint-verification-strict.json')}))
    return 0 if summary['status'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
