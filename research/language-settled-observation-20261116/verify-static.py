#!/usr/bin/env python3
"""Verify only derivation, exact observation contracts and asset ownership."""
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', action='store_true')
    args = parser.parse_args()
    commands = []
    for option in ('--check', '--self-test'):
        result = subprocess.run([sys.executable, str(ROOT / 'prepare-fixture.py'), option],
                                check=True, capture_output=True, text=True)
        commands.append({'option': option, 'exit_code': result.returncode, 'result': json.loads(result.stdout)})
    for name in ('prepare-fixture.py', 'verify-static.py'):
        ast.parse((ROOT / name).read_text(), filename=name)
    receipt = json.loads((ROOT / 'prepared/preparation.json').read_text())
    source = ROOT / 'prepared/sources' / receipt['output_relative_path']
    generated = source.read_text()
    helper = (ROOT / 'terminal-observation.kt.inc').read_text()
    overlay = (ROOT / 'overlay.init.gradle').read_text()
    required = ['visual == targetVisual', 'menu == targetMenu', 'current == previous',
                'val timeoutMs = 5_000L', 'val intervalMs = 50L', 'val windowMs = 350L',
                'val minimumSamples = 4', 'count >= minimumSamples && coveredMs >= windowMs',
                'TIMED_OUT_WITHOUT_OBSERVED_TERMINAL_GEOMETRY', 'throw AssertionError(',
                'it.scaleX, it.scaleY, it.alpha, it.contentAlpha, it.translationXDp, it.translationYDp',
                'listOf(1f, 1f, 1f, 1f,',
                'val snapshot = nodes()', 'visual?.let(::exactVisualRecord)', 'exactVisualRecord(targetVisual)',
                'exactRectRecord', 'toRawBits()', 'samples.put(sample.record)',
                'SystemClock.sleep(minOf(intervalMs, remaining))', '"mathematical_rest_observed", false']
    require(all(part in helper for part in required), 'Exact observation or timeout contract missing')
    require(not any(part in helper for part in ('epsilon', 'abs(', 'advanceTime', 'mainClock', '.finish(', '.jumpTo(',
                                               'LanguageMenuMotion(', 'java.lang.reflect', 'setAccessible')),
            'Observer must not adjust motion, clocks, private state or equality')
    require(generated.count('@Test fun ') == 1, 'Only the explicit research test may be discovered')
    require('state.alpha >= .999f && abs(state.scaleX - 1f) <= .001f' not in generated,
            'Approximate readiness must be replaced')
    for value in (receipt['parent_output_sha256'], receipt['output_sha256']):
        require(value in overlay, 'Overlay must pin reviewed parent/output hashes')
    guards = ["gradleProperty('languageSettledObservationSources')", 'isAbsolute()', 'startsWith(host.toPath())',
              'actualFiles != ([source] as Set)', 'digest(source) != expectedOutput',
              "sourceSets.named('androidTest')", 'ss.kotlin.srcDir(sources)', 'definitions != ([source] as Set)']
    require(all(part in overlay for part in guards), 'Explicit external-source guard missing')
    require('apply from:' not in overlay and 'java.srcDir(' not in overlay, 'Overlay must remain independent')
    report = {
        'schema': 1, 'status': 'STATIC_PREPARATION_VERIFIED_NOT_KOTLIN_OR_GPU_VALIDATED',
        'commands': commands, 'observation_contract_checks': len(required), 'overlay_guard_checks': len(guards),
        'gradle_executed': False, 'device_used': False, 'mathematical_rest_observed': False,
        'optical_acceptance': False,
        'files_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in [ROOT / 'prepare-fixture.py', ROOT / 'terminal-observation.kt.inc',
                                   ROOT / 'overlay.init.gradle', ROOT / 'README.md', ROOT / 'baseline-trigger.json',
                                   ROOT / 'prepared/preparation.json', source]},
    }
    if args.record:
        (ROOT / 'static-verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
