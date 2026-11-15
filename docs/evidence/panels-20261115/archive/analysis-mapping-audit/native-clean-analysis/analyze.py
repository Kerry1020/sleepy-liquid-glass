"""Frozen clean-native fixture feasibility audit, run only after root handoff.

No registration, crop-based repeat acceptance, fitting, devices, builds or Git.
All writes stay in this directory. No optical/heldout source outside the declared
two current calibration inputs and the new four clean sessions is decoded.
"""
from pathlib import Path
import argparse
import hashlib
import io
import json
import re
import sys

import numpy as np
from PIL import Image, ImageCms

O = Path(__file__).resolve().parent
P = O.parent.parent
N = P / 'native-panel-clean-r2-preparation'
S = P / 'panel-probes-preparation'
SHA = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def save(name, value):
    (O / name).write_text(json.dumps(value, indent=2, ensure_ascii=False,
                                   allow_nan=False) + '\n')


def rect(value):
    return [value['x'], value['y'], value['x'] + value['w'], value['y'] + value['h']]


def close_rect(actual, expected, tolerance):
    return len(actual) == 4 and max(abs(a-b) for a, b in zip(actual, expected)) <= tolerance


BOX = re.compile(r'\{\{([-\d.]+), ([-\d.]+)\}, \{([-\d.]+), ([-\d.]+)\}\}')


def ax_box(line):
    x, y, w, h = map(float, BOX.search(line).groups())
    return [x, y, x+w, y+h]


def rgba(path):
    im = Image.open(path)
    raw = np.asarray(im.convert('RGBA'))
    assert raw.shape == (1334, 750, 4), (path, im.size)
    icc = im.info.get('icc_profile')
    normalized = raw.copy()
    description = None
    if icc:
        profile = ImageCms.ImageCmsProfile(io.BytesIO(icc))
        normalized[:, :, :3] = np.asarray(ImageCms.profileToProfile(
            im.convert('RGB'), profile, ImageCms.createProfile('sRGB'), outputMode='RGB'))
        description = ImageCms.getProfileDescription(profile).strip()
    info = {'path': str(path), 'sha256': SHA(path), 'original_mode': im.mode,
            'size_px': list(im.size), 'icc_sha256': hashlib.sha256(icc).hexdigest() if icc else None,
            'icc_description': description, 'raw_rgba_sha256': hashlib.sha256(raw.tobytes()).hexdigest(),
            'normalized_rgba_sha256': hashlib.sha256(normalized.tobytes()).hexdigest(),
            'raw_normalized_identical': bool(np.array_equal(raw, normalized)),
            'normalized_sRGB_available': icc is not None,
            'no_profile_assumption': 'unnormalized diagnostic retained' if not icc else None}
    return raw, normalized, info


def difference(a, b, box=None):
    if box is not None:
        x0, y0, x1, y1 = box
        yy, xx = np.mgrid[0:1334, 0:750]
        select = ((xx+.5)/2 >= x0) & ((xx+.5)/2 < x1) & ((yy+.5)/2 >= y0) & ((yy+.5)/2 < y1)
        a, b = a[select], b[select]
    else:
        a, b = a.reshape(-1, 4), b.reshape(-1, 4)
    d = np.abs(a.astype(np.int16)-b.astype(np.int16))
    changed = np.any(d != 0, axis=1)
    # Never apply a tolerance to turn a nonzero pixel difference into zero.
    return {'pixels': int(len(d)), 'changed_RGBA_pixels': int(changed.sum()),
            'max_channel_delta': int(d.max()), 'mean_absolute_channel_delta': float(d.mean()),
            'q95_absolute_channel_delta': float(np.quantile(d, .95)),
            'changed_pixels_by_channel_RGBA': (d != 0).sum(axis=0).astype(int).tolist(),
            'strict_all_channels_exact_zero': bool(not changed.any())}


def parse_ax(text, carrier):
    lines = text.splitlines()
    panes, foreground = [], []
    if carrier == 'alert':
        relevant = False
        for line in lines:
            if 'Alert,' in line and "label: 'Native Alert'" in line:
                panes.append(ax_box(line)); relevant = True
            if relevant and BOX.search(line) and any(t in line for t in ['StaticText,', 'Button,']):
                if any(t in line for t in ["label: 'Native Alert'", "label: 'System-provided alert", "label: 'Cancel'", "label: 'Confirm'"]):
                    foreground.append(ax_box(line))
    else:
        relevant = False
        for i, line in enumerate(lines):
            if "label: 'Sheet Grabber'" in line:
                relevant = True
                if i and BOX.search(lines[i-1]): panes.append(ax_box(lines[i-1]))
                foreground.append(ax_box(line))
            elif relevant and BOX.search(line) and any(t in line for t in ['StaticText,', 'Switch,', 'Slider,', 'Button,']):
                foreground.append(ax_box(line))
    return {'panes_ltrb_pt': panes, 'foreground_ltrb_pt': foreground}


def execute():
    plan = json.loads((O / 'analysis-plan.json').read_text())
    frozen = json.loads((O / 'algorithm-freeze.json').read_text())
    for name, expected in frozen['algorithm_sha256'].items():
        assert SHA(O / name) == expected, ('algorithm changed', name)
    assert SHA(N / 'capture-plan.json') == plan['capture_plan_sha256']
    assert SHA(S / 'loader-manifest.json') == plan['input_manifest_sha256']
    execution = json.loads((N / 'execution-result.json').read_text())
    execution_input = json.loads((N / 'execution-input.json').read_text())
    capture_plan = json.loads((N / 'capture-plan.json').read_text())
    assert execution['exit_code'] == 0 and execution['sources_unchanged']
    assert execution_input['plan_sha256'] == execution['plan_sha256'] == plan['capture_plan_sha256']
    assert execution_input['freeze_sha256'] == execution['freeze_sha256'] == SHA(N / 'new-binary-freeze.json')
    assert capture_plan['selected_ids'] == plan['input_ids']
    assert capture_plan['carriers'] == plan['carriers'] and capture_plan['selected_themes'] == ['light']
    assert capture_plan['manifest_sha256'] == plan['input_manifest_sha256']

    manifest = json.loads((N / 'attachments/manifest.json').read_text())
    attachments = [a for group in manifest for a in group['attachments']]
    pngs = [a for a in attachments if a['exportedFileName'].endswith('.png')]
    texts = [a for a in attachments if a['exportedFileName'].endswith('.txt')]
    assert len(pngs) == len(texts) == 16, (len(pngs), len(texts))
    requests = []
    for attachment in attachments:
        if attachment['exportedFileName'].endswith('.json'):
            data = json.loads((N / 'attachments' / attachment['exportedFileName']).read_text())
            if isinstance(data, list): requests += [r for r in data if r.get('kind') == 'externalPanelPlainBacking']
    assert len(requests) == 24, len(requests)
    phases = plan['phases']
    def key_for_attachment(attachment):
        name = attachment['suggestedHumanReadableName']
        hits = []
        for sid in plan['input_ids']:
            for carrier in plan['carriers']:
                prefix = f'panel-plain-backing-{plan["input_set_id"]}-{sid}-light-{carrier}-'
                if name.startswith(prefix):
                    suffix = name[len(prefix):].split('_0_', 1)[0].removesuffix('-accessibility')
                    if suffix in phases: hits.append((sid, carrier, suffix))
        assert len(hits) == 1, name
        return hits[0]
    screenshots = {key_for_attachment(a): a for a in pngs}
    ax_attachments = {key_for_attachment(a): a for a in texts}
    expected_keys = {(sid, c, phase) for sid in plan['input_ids'] for c in plan['carriers'] for phase in phases}
    assert set(screenshots) == set(ax_attachments) == expected_keys
    session_dirs = [p for p in (N / 'sessions').iterdir() if p.is_dir()]
    assert len(session_dirs) == 4
    sessions = {}
    for directory in session_dirs:
        meta = json.loads((directory / 'external-input-metadata.json').read_text())
        session = json.loads((directory / 'session.json').read_text())
        trace = [json.loads(line) for line in (directory / 'trace.jsonl').read_text().splitlines()]
        configs = [r for r in trace if r['event'] == 'panel-plain-backing-configuration']
        assert len(configs) == 1
        key = (meta['id'], configs[0]['carrier'])
        assert key not in sessions
        sessions[key] = {'directory': directory, 'meta': meta, 'session': session,
                         'trace': trace, 'config': configs[0]}
    assert set(sessions) == {(sid, c) for sid in plan['input_ids'] for c in plan['carriers']}
    # All new image hashes and metadata are frozen before the first pixel decode.
    all_paths = [N / 'capture-plan.json', N / 'new-binary-freeze.json', N / 'execution-input.json',
                 N / 'execution-result.json', N / 'attachments/manifest.json', S / 'loader-manifest.json']
    all_paths += [N / 'attachments' / a['exportedFileName'] for a in attachments]
    all_paths += [p for directory in session_dirs for p in directory.rglob('*') if p.is_file()]
    all_paths += [S / 'inputs' / f'{sid}.png' for sid in plan['input_ids']]
    input_freeze = {'status': 'before-first-new-clean-fixture-pixel-decode',
                    'plan_sha256': SHA(O / 'analysis-plan.json'), 'script_sha256': SHA(Path(__file__)),
                    'files': {str(p): SHA(p) for p in all_paths},
                    'no_other_pixels_decoded': True}
    assert not (O / 'run-input-freeze.json').exists(), 'Do not overwrite an earlier analysis run'
    save('run-input-freeze.json', input_freeze)
    capture_receipts, session_receipts, ax_rows, geometry_rows, trace_rows = [], [], [], [], []
    for key, bundle in sorted(sessions.items()):
        sid, carrier = key
        meta, sess, trace, config = [bundle[t] for t in ['meta', 'session', 'trace', 'config']]
        run_requests = [r for r in requests if r['inputID'] == sid and r['requestedCarrier'] == carrier]
        run_requests.sort(key=lambda r: r['requestedAtUnixSeconds'])
        assert [r['phase'] for r in run_requests] == ['clean-before', 'present-request', 'rest', 'rest', 'dismiss-request', 'dismiss-after']
        source = S / 'inputs' / f'{sid}.png'
        expected_sha = plan['source_png_sha256'][sid]
        source_checks = {
            'original_source_bytes_exact': SHA(source) == SHA(bundle['directory'] / 'background-input.png') == expected_sha == meta['sha256'] == config['inputSHA256'],
            'input_metadata_identity': meta['id'] == config['inputID'] == sid and meta['set_id'] == plan['input_set_id'] and meta['split'] == 'calibration',
            'window_canvas_exact': rect(meta['windowRectPt']) == rect(meta['canvasRectInWindowPt']) == [0, 0, 375, 667],
            'original_world_mapping_exact': meta['worldSizePt'] == [375, 667] and meta['worldOriginPt'] == [0, 0] and meta['pixelsPerPt'] == 2 and meta['sizePx'] == [750, 1334],
            'session_world_traits_exact': all(sess.get(k) == v for k,v in plan['expected_session_traits'].items()),
            'native_OS_exact': sess['os'] == 'Version 26.5 (Build 23F77)',
            'hidden_trigger_configuration_exact': set(config['hiddenBackingIDs']) == set(plan['excluded_backing_AX_ids']) and config['trigger'] == 'reference-title-relay',
            'request_identity_manifest_and_source_exact': all(r['referenceRunID'].endswith(sess['run'][-36:]) and r['inputManifestSHA256'] == plan['input_manifest_sha256'] and r['selectedManifestEntry']['sha256'] == expected_sha for r in run_requests),
        }
        session_receipts.append({'input':sid, 'carrier':carrier, 'run':sess['run'], 'source_checks':source_checks,
                                 'configuration':config, 'metadata':meta,
                                 'session_traits':{k:sess.get(k) for k in ['os']+list(plan['expected_session_traits'])}})
        for phase in phases:
            attachment, ax_attachment = screenshots[(sid, carrier, phase)], ax_attachments[(sid, carrier, phase)]
            timestamp = attachment['timestamp']; rel = timestamp - sess['originUnixSeconds']
            req_phase = 'rest' if phase == 'rest-repeat' else phase
            wanted_sample = 1 if phase == 'rest-repeat' else 0 if phase == 'rest' else None
            matches = [r for r in run_requests if r['phase'] == req_phase and r.get('sampleIndex') == wanted_sample]
            assert len(matches) == 1
            request = matches[0]
            next_times = [r['requestedAtUnixSeconds'] for r in run_requests if r['requestedAtUnixSeconds'] > request['requestedAtUnixSeconds']]
            following = min(next_times) if next_times else None
            prior = [r for r in trace if r['event'] == 'external-presentation-context' and r['t'] <= rel]
            public = prior[-1] if prior else None
            receipt_checks = {'capture_after_request':timestamp >= request['requestedAtUnixSeconds'],
                              'capture_before_next_operation':following is None or timestamp < following,
                              'AX_after_PNG_before_next_operation':ax_attachment['timestamp'] >= timestamp and (following is None or ax_attachment['timestamp'] < following),
                              'public_context_present':public is not None}
            capture_receipts.append({'input':sid,'carrier':carrier,'phase':phase,'png':attachment,'AX':ax_attachment,
                                     'request':request,'capture_relative_session_s':rel,'checks':receipt_checks,'latest_public_context':public})
            text = (N / 'attachments' / ax_attachment['exportedFileName']).read_text()
            parsed = parse_ax(text, carrier)
            excluded = {identifier: f"identifier: '{identifier}'" not in text for identifier in plan['excluded_backing_AX_ids']}
            row = {'input':sid,'carrier':carrier,'phase':phase, 'excluded_backing_AX_absent':excluded,
                   'root_title_present':"identifier: 'reference-title'" in text,
                   'parsed':parsed}
            is_rest = phase in ['rest','rest-repeat']
            row['correct_panel_presence'] = bool(parsed['panes_ltrb_pt']) == is_rest
            ax_rows.append(row)
            expected = plan['old_fixture_geometry'][sid][carrier]
            ax_match = len(parsed['panes_ltrb_pt']) == 1 and close_rect(parsed['panes_ltrb_pt'][0], expected['AX_ltrb_pt'], .1) if is_rest else not parsed['panes_ltrb_pt']
            controllers = public.get('publicControllers', []) if public else []
            stable = all(not c['isBeingPresented'] and not c['isBeingDismissed'] for c in controllers)
            public_expected = expected['public_controllers'] if is_rest else expected['public_controllers'][:1]
            public_match = len(controllers) == len(public_expected) and all(
                actual['class'] == old['class'] and actual['presentationStyle'] == old['presentationStyle']
                and actual['effectiveInterfaceStyle'] == actual['viewEffectiveInterfaceStyle'] == 1
                and close_rect(rect(actual['viewRectInWindowPt']),rect(old['viewRectInWindowPt']),.01)
                for actual,old in zip(controllers,public_expected))
            foreground_match = (len(parsed['foreground_ltrb_pt']) == len(expected['foreground_ltrb_pt']) and all(
                close_rect(a,b,.1) for a,b in zip(parsed['foreground_ltrb_pt'],expected['foreground_ltrb_pt']))) if is_rest else True
            geometry_rows.append({'input':sid,'carrier':carrier,'phase':phase,'AX_pane_old_fixture_match':ax_match,
                                  'foreground_old_fixture_match':foreground_match,'actual_AX':parsed,
                                  'public_controller_geometry_old_fixture_match':public_match,'public_controllers_stable':stable,
                                  'actual_public_controllers':controllers,
                                  'limitation':'Public controller/AX geometry gate only; not an optical material contour or physical thickness measurement.'})
        phase_time = {phase:screenshots[(sid,carrier,phase)]['timestamp']-sess['originUnixSeconds'] for phase in phases}
        relay = [r for r in trace if r['event']=='panel-plain-backing-command' and r['phase']=='relay-requested']
        set_rows = [r for r in trace if r['event']=='panel-plain-backing-command' and r['phase']=='state-set']
        title_touches = [r for r in trace if r['event']=='touch' and r['source']=='delivery' and r['hitIdentifier']=='reference-title' and phase_time['clean-before']<r['t']<phase_time['rest']]
        trace_checks = {'one_relay_one_state_set':len(relay)==len(set_rows)==1,
                        'real_title_DOWN_UP':{r['phase'] for r in title_touches}>={0,3},
                        'rest_repeat_spacing_at_least025_s':phase_time['rest-repeat']-phase_time['rest']>=.25}
        if len(relay)==len(set_rows)==1:
            trace_checks['same_requestID_carrier_order'] = relay[0]['requestID']==set_rows[0]['requestID'] and relay[0]['carrier']==set_rows[0]['carrier']==carrier and phase_time['clean-before']<relay[0]['t']<=set_rows[0]['t']<phase_time['rest']
        else: trace_checks['same_requestID_carrier_order']=False
        trace_rows.append({'input':sid,'carrier':carrier,'checks':trace_checks,'relay':relay,'state_set':set_rows,'title_touches':title_touches})
    save('metadata-session-receipts.json',session_receipts)
    save('capture-time-and-public-context-receipts.json',capture_receipts)
    save('AX-trigger-and-panel-exclusion.json',ax_rows)
    save('old-fixture-geometry-gates.json',geometry_rows)
    save('relay-and-delivered-touch-receipts.json',trace_rows)
    # First decode only after complete new image inventory and immutable hashes.
    decode_rows, images, sources = [], {}, {}
    for sid in plan['input_ids']:
        raw,normal,info=rgba(S/'inputs'/f'{sid}.png'); sources[sid]=(raw,normal); decode_rows.append(info)
    for key,attachment in screenshots.items():
        raw,normal,info=rgba(N/'attachments'/attachment['exportedFileName']);images[key]=(raw,normal);decode_rows.append(info)
    repeat_rows, context_rows, footprint_rows = [], [], []
    for sid in plan['input_ids']:
        for carrier in plan['carriers']:
            rest,repeat,before,after=[images[(sid,carrier,phase)] for phase in ['rest','rest-repeat','clean-before','dismiss-after']]
            repeat_rows.append({'input':sid,'carrier':carrier,'scope':'ENTIRE750x1334 RGBA; no mask/crop/tolerance',
                                'raw_RGBA':difference(rest[0],repeat[0]),'normalized_sRGB_RGBA':difference(rest[1],repeat[1])})
            context_rows.append({'input':sid,'carrier':carrier,'scope':'ENTIRE750x1334 descriptive context only; no zero assumption or cropped replacement',
                                 'before_vs_after_raw_RGBA':difference(before[0],after[0]),
                                 'before_vs_bare_source_raw_RGBA':difference(before[0],sources[sid][0]),
                                 'after_vs_bare_source_raw_RGBA':difference(after[0],sources[sid][0])})
            for support in plan['source_footprints'][carrier]:
                for phase,frame in [('clean-before',before),('dismiss-after',after)]:
                    footprint_rows.append({'input':sid,'carrier':carrier,'phase':phase,'support':support,
                                           'raw_RGBA':difference(frame[0],sources[sid][0],support['ltrb_pt']),
                                           'normalized_sRGB_RGBA':difference(frame[1],sources[sid][1],support['ltrb_pt'])})
    save('decode-provenance.json',decode_rows)
    save('REST-repeat-FULL-RGBA.json',repeat_rows)
    save('full-context-system-differences.json',context_rows)
    save('fixed-source-footprint-exactness.json',footprint_rows)
    gates={
      'same_run_original_source_canvas_and_session_all':all(all(r['source_checks'].values()) for r in session_receipts),
      'capture_request_and_AX_time_binding_all':all(all(r['checks'].values()) for r in capture_receipts),
      'original_backing_trigger_AX_absence_and_panel_presence_all':all(all(r['excluded_backing_AX_absent'].values()) and r['root_title_present'] and r['correct_panel_presence'] for r in ax_rows),
      'old_fixture_public_AX_and_foreground_geometry_all':all(all(r[k] for k in ['AX_pane_old_fixture_match','foreground_old_fixture_match','public_controller_geometry_old_fixture_match','public_controllers_stable']) for r in geometry_rows),
      'explicit_title_touch_relay_and_repeat_spacing_all':all(all(r['checks'].values()) for r in trace_rows),
      'embedded_profile_available_for_normalized_sRGB_all':all(r['normalized_sRGB_available'] for r in decode_rows),
      'FULL_RAW_RGBA_rest_repeat_strict_zero_all':all(r['raw_RGBA']['strict_all_channels_exact_zero'] for r in repeat_rows),
      'FULL_NORMALIZED_sRGB_RGBA_rest_repeat_strict_zero_all':all(r['normalized_sRGB_RGBA']['strict_all_channels_exact_zero'] for r in repeat_rows),
      'all_fixed_source_footprints_and_support_stresses_raw_and_normalized_exact':all(r['raw_RGBA']['strict_all_channels_exact_zero'] and r['normalized_sRGB_RGBA']['strict_all_channels_exact_zero'] for r in footprint_rows),
    }
    decision={'status':'FEASIBILITY GATES ONLY; never optical parity or inverse recovery',
              'gates':gates,'all_requested_feasibility_gates_pass':all(gates.values()),
              'native_adaptation_condition':'plain-backing-v1 is separate from old polluted backing; do not pool its optical pixels',
              'full_context_changes_reported_separately_not_cropped_out':True,
              'native_central_optical_contour_and_tangent_invariance_established':False,
              'native_blur_source_support_bound_established':False,
              'unique_2D_mapping_recoverable_claim':False,
              'refraction_fit_performed':False,'physical_thickness_or_parity_claim':False,
              'next_decision':'Root reviews gate failures and independent contour/support feasibility; source exactness alone cannot approve paired-slope inversion.'}
    save('decision.json',decision)
    # Reject input changes during analysis, without touching the captured files.
    assert all(SHA(Path(name))==expected for name,expected in input_freeze['files'].items())
    print(json.dumps(decision,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute-after-root-handoff',action='store_true')
    args=parser.parse_args()
    if not args.execute_after_root_handoff:
        parser.error('Frozen algorithm only. Root handoff and completed captures are required before pixel decode.')
    try:
        execute()
    except Exception as error:
        save('analysis-error.json',{'error':str(error),'type':type(error).__name__,
                                   'no_threshold_or_ROI_fallback':True})
        raise
