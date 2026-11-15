#!/usr/bin/env python3
"""Verify the v2 preparation/static contracts without Gradle or a device."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', action='store_true', help='Write only .local/v2/static-verification.json')
    args = parser.parse_args()
    commands = []
    for option in ('--check', '--self-test'):
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'prepare-overlay.py'), option],
                                capture_output=True, text=True, check=True)
        commands.append({'argv': ['python3', '-B', 'prepare-overlay.py', option],
                         'exit_code': result.returncode, 'result': json.loads(result.stdout)})
    tests = subprocess.run([sys.executable, '-B', str(ROOT / 'test-prepare-overlay.py')],
                           capture_output=True, text=True, check=True)
    commands.append({'argv': ['python3', '-B', 'test-prepare-overlay.py'],
                     'exit_code': tests.returncode, 'output': tests.stdout + tests.stderr})
    for name in ('prepare-overlay.py', 'verify-static.py', 'test-prepare-overlay.py'):
        ast.parse((ROOT / name).read_text(), filename=name)
    spec = importlib.util.spec_from_file_location('slider_overlay', ROOT / 'prepare-overlay.py')
    overlay = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(overlay)
    outputs, receipt = overlay.expected()
    init = (ROOT / 'overlay.init.gradle').read_text()
    required = ["gradle.beforeProject", "p.path == ':app'", "withPlugin('com.android.application')",
                "gradleProperty('glassResearchSources')", 'isAbsolute()', 'sources.isDirectory()',
                'startsWith(host.toPath())', "new File(sources.parentFile, 'preparation.json')",
                'digest(receiptFile) != expectedReceipt', 'receipt.schema != 2',
                'receipt.selected_helper_files != 1', 'receipt.host_helper_dependency != false',
                'digest(source) != expectedSha', 'Files.walk(sources.toPath())',
                'Files.isSymbolicLink(path)', 'actualFiles != expectedSources',
                "sourceSets.named('androidTest')", 'ss.kotlin.srcDir(sources)', 'p.afterEvaluate',
                'Research alias must be unique', 'Research helper namespace must belong only']
    require(all(text in init for text in required), 'Missing inspected Gradle entry-point guard/API')
    require('java.srcDir(' not in init, 'Must use AGP built-in Kotlin source roots')
    receipt_pin = re.search(r"def expectedReceipt = '([0-9a-f]{64})'", init)
    require(receipt_pin is not None and receipt_pin[1] == overlay.sha(overlay.receipt_bytes(receipt)),
            'Gradle preparation receipt pin differs from the complete deterministic receipt')
    output_pins = re.findall(r"'(com/[^']+\.kt)': '([0-9a-f]{64})'", init)
    require(len(output_pins) == 2 and dict(output_pins) == {path: overlay.sha(data) for path, data in outputs.items()},
            'Gradle output pins differ from the exact fixture/helper pair')
    readme = (ROOT / 'README.md').read_text()
    image = '../../docs/design/evidence/glass-slider-star-20261115/figures/six-pose-comparison.png'
    require(image in readme and (ROOT / image).is_file(), 'Existing comparison image link is missing')
    require('has not passed optical acceptance' in readme, 'Missing acceptance limitation')
    require('.local/v2/sources' in readme and '8 explicit import aliases' in readme,
            'Missing v2 invocation or transformation boundary')
    require('/.local/' in (ROOT / '.gitignore').read_text(), 'Generated overlay must be ignored')
    names = ('.gitignore', 'README.md', 'prepare-overlay.py', 'overlay.init.gradle',
             'verify-static.py', 'test-prepare-overlay.py')
    report = {
        'schema': 2,
        'status': 'STATIC_PREPARATION_VERIFIED_NOT_GRADLE_VALIDATED',
        'commands': commands,
        'files_sha256': {name: sha(ROOT / name) for name in names},
        'generated_receipt_sha256': sha(ROOT / overlay.GENERATED_RECEIPT),
        'generated_sources': {row['role']: {'path': row['output_relative_path'], 'sha256': row['output_sha256']}
                              for row in receipt['artifacts']},
        'static_entry_point_checks': len(required),
        'complete_receipt_and_output_pins_match': True,
        'existing_comparison': {'path': image, 'sha256': sha(ROOT / image)},
        'observed_agp_api': {'version': '9.5.1',
            'signatures': ['AndroidSourceSet.getKotlin()', 'AndroidSourceDirectorySet.srcDir(Object)',
                           'AndroidSourceDirectorySet.getDirectories()'],
            'method': 'Historical read-only API inspection; not a new Gradle execution'},
        'gradle_executed': False,
        'kotlin_compilation_executed': False,
        'device_used': False,
        'optical_acceptance': False,
        'limits': ['Static guards and inverse byte equality do not prove Groovy/Gradle execution or Kotlin compilation.',
                   'Sleepy :app adapters/theme, AndroidJUnit/Compose and runner remain required.',
                   'The old schema1 static/build receipts do not validate this two-file integration.'],
    }
    if args.record:
        target = overlay.local_path('.local/v2/static-verification.json')
        target.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
