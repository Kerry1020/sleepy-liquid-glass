#!/usr/bin/env python3
"""Check only source preparation and research boundaries; never run Gradle or a device."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', action='store_true')
    parser.add_argument('--origin', type=Path, help='Optionally check an original source file or product checkout root')
    args = parser.parse_args()
    commands = []
    check_options = ['--check']
    if args.origin:
        check_options.extend(['--origin', str(args.origin)])
    for options in (check_options, ['--self-test']):
        result = subprocess.run([sys.executable, str(ROOT / 'prepare-fixture.py'), *options],
                                capture_output=True, text=True, check=True)
        public_options = ['<LOCAL_ORIGIN>' if args.origin and value == str(args.origin) else value for value in options]
        commands.append({'argv': ['python3', 'prepare-fixture.py', *public_options],
                         'local_origin_argument_redacted': bool(args.origin and '--origin' in options),
                         'exit_code': result.returncode, 'result': json.loads(result.stdout)})
    for name in ('prepare-fixture.py', 'verify-static.py'):
        ast.parse((ROOT / name).read_text(), filename=name)
    receipt = json.loads((ROOT / 'prepared/preparation.json').read_text())
    source = ROOT / 'prepared/sources' / receipt['output_relative_path']
    generated = source.read_text()
    body = (ROOT / 'triplet-body.kt.inc').read_text()
    init = (ROOT / 'overlay.init.gradle').read_text()
    require(receipt['output_sha256'] in init and receipt['source_sha256'] in init,
            'Init script must pin reviewed input and output hashes')
    guards = ["gradle.beforeProject", "p.path == ':app'", "withPlugin('com.android.application')",
              "gradleProperty('languageResearchSources')", 'isAbsolute()', 'startsWith(host.toPath())',
              "new File(sources.parentFile, 'preparation.json')", 'digest(source) != expectedOutput',
              "sourceSets.named('androidTest')", 'ss.kotlin.srcDir(sources)', 'Language research alias must be unique']
    require(all(part in init for part in guards), 'Missing external source attachment guard')
    require('java.srcDir(' not in init, 'Use the observed AGP Kotlin source-root API')
    require(generated.count('@Test fun ') == 1, 'Only one explicit diagnostic test may be selected')
    require(generated.count('class AssetLanguageGpuTripletDiagnosticTest {') == 1, 'Alias must be unique')
    require(body.index('writeTripletReport(directory, report)') < body.index('assertTripletOriginalPredicates('),
            'Original assertions must follow evidence writing')
    required = [
        'captureTripletStage("C"', 'captureTripletStage("U"', 'captureTripletStage("C_restored"', 'captureTripletStage("E"',
        'E_stable_from_C_stable', 'E_stable_from_U_stable', 'E_late_from_C_late', 'E_late_from_U_late',
        'C_stable_from_U_stable', 'C_restored_stable_from_C_stable', 'temporal_C', 'temporal_U', 'temporal_C_restored', 'temporal_E',
        'probe.meanAbsDelta >= 6.0', 'distance <= 5.0', 'roi_pixel_edges', 'source_screen_bounds_px',
        'roi_fraction_inside_value_rect', 'sourceDrawSequence', 'png_roundtrip_same_pixels', 'bitmap.recycle()',
        'SAMPLING_NOT_COMPLETE', 'ALL_FIVE_ROWS_MEASURED_NOT_AN_OPTICAL_ACCEPTANCE',
        'C_U_raw_grid_pixels_equal_in_unoccluded_row_rois', 'C_restored_C_all_row_roi_pixels_equal',
        'all_temporal_controls_exactly_equal',
    ]
    require(all(part in body for part in required), 'Missing a requested measurement or evidence guard')
    require('neutral =' not in body and 'Color(' not in body, 'Triplet must not substitute background or material colors')
    require(body.index('captureTripletStage("C_restored"') < body.index('open(67L, 850L)'),
            'Real source must be restored/submitted before natural open')
    require('glassResearchSources' not in init and 'apply from:' not in init,
            'Independent entry point must not load or use the slider entry point')
    paths = ['source/LanguageMenuMotionCaptureTest.kt', 'triplet-body.kt.inc', 'prepare-fixture.py',
             'verify-static.py', 'overlay.init.gradle', 'README.md', 'prepared/preparation.json',
             'prepared/sources/' + receipt['output_relative_path']]
    report = {
        'schema': 1, 'status': 'STATIC_SOURCE_PREPARATION_VERIFIED_NOT_KOTLIN_OR_GPU_VALIDATED',
        'commands': commands, 'entry_point_guards': len(guards), 'measurement_contract_checks': len(required),
        'files_sha256': {path: digest(ROOT / path) for path in paths},
        'gradle_executed': False, 'kotlin_compilation_executed': False, 'device_used': False,
        'origin_verified': bool(args.origin),
        'gpu_sampling_complete': False, 'material_acceptance': False,
        'limits': ['Static text/transform checks do not establish Groovy or Kotlin execution.',
                   'The source-unpainted GPU control, temporal behavior and all numeric outcomes remain unmeasured.',
                   'A negative material/one-row-material control remains necessary for a final regression oracle.'],
    }
    if args.record:
        (ROOT / 'static-verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
