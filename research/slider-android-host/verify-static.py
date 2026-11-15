#!/usr/bin/env python3
"""Record only local preparation/static contracts; never invoke Gradle or a device."""
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


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', action='store_true', help='Write static-verification.json in this directory')
    args = parser.parse_args()
    commands = []
    for option in ('--check', '--self-test'):
        result = subprocess.run([sys.executable, str(ROOT/'prepare-overlay.py'), option],
                                capture_output=True, text=True, check=True)
        commands.append({'argv': ['python3', 'prepare-overlay.py', option],
                         'exit_code': result.returncode, 'result': json.loads(result.stdout)})
    for name in ('prepare-overlay.py', 'verify-static.py'):
        ast.parse((ROOT/name).read_text(), filename=name)
    init = (ROOT/'overlay.init.gradle').read_text()
    required = ["gradle.beforeProject", "p.path == ':app'", "withPlugin('com.android.application')",
                "gradleProperty('glassResearchSources')", 'isAbsolute()', 'sources.isDirectory()',
                'startsWith(host.toPath())', "new File(sources.parentFile, 'preparation.json')",
                'digest(source) != expectedOutput', "sourceSets.named('androidTest')",
                'ss.kotlin.srcDir(sources)', 'p.afterEvaluate', 'Research alias must be unique']
    require(all(text in init for text in required), 'Missing inspected Gradle entry-point guard/API')
    require('java.srcDir(' not in init, 'Must use AGP built-in Kotlin source roots')
    require("['gradlew'" not in (ROOT/'prepare-overlay.py').read_text(), 'Preparation must not invoke Gradle')
    readme = (ROOT/'README.md').read_text()
    image = '../../docs/design/evidence/glass-slider-star-20261115/figures/six-pose-comparison.png'
    require(image in readme and (ROOT/image).is_file(), 'Existing comparison image link is missing')
    require('has not passed optical acceptance' in readme, 'Missing acceptance limitation')
    require('/.local/' in (ROOT/'.gitignore').read_text(), 'Generated overlay must be ignored')
    names = ('.gitignore', 'README.md', 'prepare-overlay.py', 'overlay.init.gradle', 'verify-static.py')
    report = {
        'schema': 1,
        'status': 'STATIC_PREPARATION_VERIFIED_NOT_GRADLE_VALIDATED',
        'commands': commands,
        'files_sha256': {name: sha(ROOT/name) for name in names},
        'generated_receipt_sha256': sha(ROOT/'.local/preparation.json'),
        'static_entry_point_checks': len(required),
        'existing_comparison': {'path': image, 'sha256': sha(ROOT/image)},
        'observed_agp_api': {'version': '9.5.1',
            'signatures': ['AndroidSourceSet.getKotlin()', 'AndroidSourceDirectorySet.srcDir(Object)',
                           'AndroidSourceDirectorySet.getDirectories()'],
            'method': 'Read-only javap of the installed gradle-api-9.5.1.jar; not Gradle execution'},
        'gradle_executed': False,
        'kotlin_compilation_executed': False,
        'device_used': False,
        'optical_acceptance': False,
        'limits': ['Static text guards do not prove Groovy/Gradle execution.',
                   'The corresponding Sleepy :app instrumentation host is required.'],
    }
    if args.record:
        (ROOT/'static-verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
