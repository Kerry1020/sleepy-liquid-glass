#!/usr/bin/env python3
"""Check this bounded export and recompute harmonic rows; no build/device/network.

Requires numpy and Pillow. Original full captures and AX exports are omitted:
source hashes identify them, but crop checks cannot reconstruct their encoding.
The frozen full-image stripe analyzer is not rerun by this program.
"""
from collections import Counter
from pathlib import Path
import gzip
import hashlib
import json
import math
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
IMAGES = ROOT / 'docs/images/panels-lateral-20261115'
CHECKS = 0


def check(condition, label):
    global CHECKS
    if not condition:
        raise AssertionError(label)
    CHECKS += 1


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text())


def public_path(name):
    path = (ROOT / name).resolve()
    check(path.is_relative_to(ROOT), 'public path remains inside repository')
    return path


def verify_sources():
    sources = read('sources.json')
    records = sources['records']
    check(len(records) == 87, '87 source records')
    by_path = {row['published']: row for row in records}
    check(len(by_path) == len(records), 'unique source-record paths')
    for row in records:
        path = public_path(row['published'])
        data = path.read_bytes()
        check(sha(data) == row['published_sha256'], str(path) + ' published SHA')
        check(len(data) == row['published_bytes'], str(path) + ' published length')
        processing = row['processing']
        if processing == 'byte-exact copy':
            check(sha(data) == row['source_sha256'], str(path) + ' exact source SHA')
            check(len(data) == row['source_bytes'], str(path) + ' exact source length')
        elif processing == 'deterministic lossless gzip (mtime=0)':
            restored = gzip.decompress(data)
            check(sha(restored) == row['source_sha256'], str(path) + ' restored SHA')
            check(len(restored) == row['source_bytes'], str(path) + ' restored length')
            check(data[4:8] == bytes(4), str(path) + ' deterministic gzip mtime')
        else:
            check(processing == 'integer PNG component crop; no pixel resize or retouch; original excluded',
                  str(path) + ' known transform')
            box = row['crop_box_px']
            with Image.open(path) as im:
                check(im.size == (box[2] - box[0], box[3] - box[1]), str(path) + ' crop dimensions')
                check(im.mode == row['mode'], str(path) + ' retained mode')
                check(sha(im.tobytes()) == row['retained_pixel_bytes_sha256'], str(path) + ' retained pixels')
                for key, expected in row['color_declaration_preserved'].items():
                    check(im.info.get(key) == expected, str(path) + ' retained color declaration')
            check(all(isinstance(v, int) for v in box), str(path) + ' integer crop')
            width, height = row['original_size_px']
            check(0 <= box[0] < box[2] <= width and 0 <= box[1] < box[3] <= height,
                  str(path) + ' crop inside recorded original')
    return by_path


def verify_overlay(sources):
    overlay = read('portable-inputs.json')
    inputs = overlay['inputs']
    paths = {row['published'] for row in inputs}
    check(len(paths) == 23, '23 deduplicated public input files')
    check(paths == {str(path.relative_to(ROOT)) for path in (HERE / 'inputs').iterdir()},
          'overlay covers every public input')
    for row in inputs:
        source = sources[row['published']]
        check(row['original_sha256'] == source['source_sha256'], row['role'] + ' original identity')
        check(row['original_bytes'] == source['source_bytes'], row['role'] + ' original length')
        check(row['crop_box_px'] == source['crop_box_px'], row['role'] + ' crop identity')
    captures = overlay['gain045_captures']
    check(len(captures) == 16, '16 public candidate component crops')
    check(Counter((r['theme'], r['carrier']) for r in captures) ==
          Counter({(t, c): 4 for t in ['light', 'dark'] for c in ['alert', 'share_sheet']}),
          'four backgrounds for each theme/carrier')
    matrix_bytes = gzip.decompress((HERE / 'archive/panels-lateral045-20261115/matrix.json.gz').read_bytes())
    receipt = read('archive/panels-lateral045-20261115/capture-result.json')
    check(sha(matrix_bytes) == receipt['matrix_sha256'], 'capture receipt binds original matrix')
    check(receipt['count'] == 16 and receipt['sources_unchanged'] is True, 'capture receipt scope')
    check(receipt['status'] == 'captured_geometry_checked_not_parity_acceptance', 'capture is not acceptance')
    original = {r['scene']: r for r in json.loads(matrix_bytes)['captures']}
    check(set(original) == {r['scene'] for r in captures}, 'all matrix scenes exported')
    for row in captures:
        old = original[row['scene']]
        check(row['window_geometry'] == old['window_geometry'], row['scene'] + ' observed Window geometry')
        if row['carrier'] == 'alert':
            box = next(m['actual_window_rect_px'] for m in old['measurements'] if m['tag'] == 'static-alert-carrier')
        else:
            screen_box = old['sheet_geometry_comparison']['actual_material_layout']['screen_rect_px']
            origin = old['window_geometry']['root_screen_origin_px']
            box = [v - origin[i % 2] for i, v in enumerate(screen_box)]
        check(row['crop_box_px'] == box, row['scene'] + ' crop uses material rectangle')
        check(row['published'] in paths, row['scene'] + ' crop exists in overlay')
    return overlay


def verify_harmonics(overlay):
    archive = read('archive/lateral-sampling-results/harmonic-results.json')
    plan = read('archive/lateral-harmonic-plan.json')
    check(archive['plan'] == plan, 'harmonic plan unchanged')
    expected_rows = {(image, side, y) for image in ['native', 'baseline', 'gain0025', 'gain045']
                     for side in ['left', 'right'] for y in plan['rows_px']}
    actual = {(r['image'], r['side'], r['y']) for r in archive['rows']}
    check(len(archive['rows']) == 80 and actual == expected_rows, 'all 80 unique harmonic rows retained')
    index = {(r['image'], r['side'], r['y']): r for r in archive['rows']}
    role_index = {r['role']: r for r in overlay['inputs']}
    angular_frequency = 2 * np.pi / plan['frequency_px']
    for name, path in overlay['harmonic_inputs'].items():
        entry = role_index['harmonic/' + name]
        check(entry['original_sha256'] == archive['inputs'][name]['sha256'], name + ' original harmonic source')
        x_origin, y_origin = entry['crop_box_px'][:2]
        pixels = np.asarray(Image.open(public_path(path)).convert('RGB'), dtype=np.float64)
        for side, (start, stop) in plan['x_windows_px'].items():
            xs = np.arange(start, stop)
            basis = np.stack([np.ones(len(xs)), np.cos(angular_frequency * xs),
                              np.sin(angular_frequency * xs)], axis=1)
            band_start, band_stop = plan['reference_y_px']
            reference = pixels[band_start-y_origin:band_stop-y_origin, xs-x_origin].mean(axis=0)
            ref_coefs = np.linalg.lstsq(basis, reference, rcond=None)[0]
            ref_complex = ref_coefs[1] + 1j * ref_coefs[2]
            for y in plan['rows_px']:
                samples = pixels[y-y_origin, xs-x_origin]
                coefs = np.linalg.lstsq(basis, samples, rcond=None)[0]
                complex_product = (coefs[1] + 1j * coefs[2]) * np.conj(ref_complex)
                computed = [float(np.angle(np.sum(complex_product)) / angular_frequency),
                            float(np.sqrt(np.mean((samples-basis@coefs)**2)))]
                computed += list(np.angle(complex_product) / angular_frequency)
                row = index[(name, side, y)]
                recorded = [row['apparent_harmonic_shift_px'], row['rgb_fit_rmse']] + row['channel_shift_px']
                for got, expected in zip(computed, recorded):
                    check(math.isclose(got, expected, rel_tol=0, abs_tol=1e-9),
                          f'{name}/{side}/y{y}: retained-pixel harmonic reproduction')
    deltas = read('archive/lateral-sampling-results/baseline-deltas.json')
    check(len(deltas) == 24, '24 historical Window delta records')
    backgrounds = [r for r in deltas if '-background-' in r['file']]
    check(len(backgrounds) == 8 and all(r['changed_pixels'] == 0 and r['max_rgb_delta'] == 0 for r in backgrounds),
          'eight unchanged historical background Window records')


def verify_frozen_diagnostics():
    base = 'archive/analysis-mapping-audit/paired-slope-feasibility-analysis/'
    freeze_bytes = (HERE / base / 'implementation-freeze.json').read_bytes()
    check(sha(freeze_bytes) == '8b3deaca28c66c8527528f13664abd00042fba958b12e7c2d91c01e5d1056a54',
          'original 69-check freeze identity')
    freeze = json.loads(freeze_bytes)
    check(freeze['verification']['checks'] == 69 and freeze['verification']['passed'] == 69,
          '69 synthetic implementation checks recorded')
    check(freeze['verification']['source_and_capture_PNGs_decoded'] == 0, 'freeze before real decode')
    for name, expected in freeze['files_sha256'].items():
        check(sha((HERE / base / name).read_bytes()) == expected, 'frozen operator ' + name)
    stripe = HERE / 'archive/analysis-stripe-curvature-20261115'
    for name in ['plan-freeze.json', 'execution-predecode-freeze.json']:
        data = json.loads((stripe / name).read_text())
        hashes = data.get('files_sha256', {})
        for file, expected in hashes.items():
            check(sha((stripe / file).read_bytes()) == expected, 'frozen stripe ' + file)
    rows = [json.loads(line) for line in gzip.decompress((stripe / 'rows.jsonl.gz').read_bytes()).splitlines()]
    groups = Counter((r['image'], r['track'], r['boundary_pt']) for r in rows)
    check(len(rows) == 8256 and len(groups) == 24 and set(groups.values()) == {344},
          'all frozen stripe rows and series retained')
    decision = json.loads((stripe / 'decision-summary.json').read_text())
    check(decision['raw_normalized_all_4128_rows_identical'] is True, 'recorded raw/normalized agreement')
    for row in decision['summary']:
        check(row['top24_derivative_rows'] == row['bottom24_derivative_rows'] == 0,
              'no complete edge derivative support retained')
        if row['boundary_pt'] in [54, 324]:
            check(row['center_reference_18_of_18_pass'] == (row['image'] == 'native'),
                  'native/Android primary center-reference distinction retained')


def verify_regressions():
    build = read('archive/lateral045-buttons-build-result.json')
    check(build['exit_code'] == 0, 'application build exit')
    tests = build['tests']
    check([int(r['attributes']['tests']) for r in tests] == [50, 23, 3], '76 JVM scope')
    for row in tests:
        check(all(int(row['attributes'][key]) == 0 for key in ['failures', 'errors', 'skipped']),
              row['name'] + ' original receipt')
    check(sha((HERE / 'archive/lateral045-buttons-build.log').read_bytes()) == build['build_log_sha256'],
          '76-test build log identity')
    later = read('archive/buttons-datepicker-regression-result.json')
    check(later['testCount'] == 18 and later['failureCount'] == 0, '18 later JVM scope')
    for row in later['suiteReceipts']:
        file = HERE / ('app-validation/jvm/TEST-' + row['name'] + '.xml')
        check(sha(file.read_bytes()) == row['sha256'], row['name'] + ' XML hash')
        attrs = ET.parse(file).getroot().attrib
        check(all(int(attrs[key]) == row[key] for key in ['tests', 'failures', 'errors', 'skipped']),
              row['name'] + ' XML counts')
    check(sha((HERE / 'archive/buttons-datepicker-regression.log').read_bytes()) == later['logSha256'],
          '18-test log identity')
    check('OK (3 tests)' in (HERE / 'archive/button-layout-fixed-device.log').read_text(), 'final three device tests')
    check('Tests run: 3,  Failures: 2' in (HERE / 'archive/button-layout-device.log').read_text(),
          'earlier two device failures preserved')
    independent = json.loads((ROOT / 'provenance/validation-20261115-lateral.json').read_text())
    check(independent['sourceBaseCommit'] == '386d4c09a78234c4bc04507f6ef4952d856de3f4',
          'independent build source is separate from application evidence')
    check(independent['hostTestCount'] == 56 and independent['exitCode'] == 0 and
          independent['hostTestFailures'] == independent['hostTestSkipped'] == 0, 'independent 56-test receipt')


def verify_figures_and_manifest(overlay):
    processing = read('figure-processing.json')
    check(processing['harmonic_rows'] == 80 and processing['harmonic_smoothing'] is False, 'figure rows unsmoothed')
    operations = processing['contact_sheets']
    check(len(operations) == 17, 'sixteen panels and one application illustration')
    for row in operations:
        with Image.open(public_path(row['source'])) as im:
            check(list(im.size) == row['published_input_size_px'], row['scene'] + ' no double crop')
        check(row['additional_crop'] is False, row['scene'] + ' display only resize')
    manifest = read('publication-manifest.json')
    expected_files = {str(p.relative_to(ROOT)) for directory in [HERE, IMAGES]
                      for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts
                      and p.name != 'publication-manifest.json'}
    expected_files.add('docs/panel-lateral-sampling-study.md')
    check({r['path'] for r in manifest['files']} == expected_files, 'bounded publication owns exactly its files')
    for row in manifest['files']:
        data = public_path(row['path']).read_bytes()
        check(sha(data) == row['sha256'] and len(data) == row['bytes'], row['path'] + ' publication identity')


def main():
    sources = verify_sources()
    overlay = verify_overlay(sources)
    verify_harmonics(overlay)
    verify_frozen_diagnostics()
    verify_regressions()
    verify_figures_and_manifest(overlay)
    print(f'{CHECKS} checks passed: bounded publication, 23 inputs and all 80 harmonic rows reproduced.')
    print('No device, original-full-image stripe rerun, optical acceptance or parity verdict.')


if __name__ == '__main__':
    main()
