#!/usr/bin/env python3
"""Derive an asset-only exact terminal-geometry observer; never build or use a device."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent / 'control-regression-diagnostics-20261116/language-gpu'
PARENT_REL = 'prepared/sources/com/lingion/sleepy/ui/component/AssetLanguageGpuTripletDiagnosticTest.kt'
PARENT_SHA = 'ca4d1638eb08a05ea32dfcdbfd9c2442420ec389062500cc19be5e57ef18d5ce'
SOURCE_SHA = '94b488726ac48e666160f786c5881c53b960fc948016a74a7235a923be2f9639'
ALIAS = 'AssetLanguageObservedTerminalGeometryTest'
OUTPUT = 'com/lingion/sleepy/ui/component/' + ALIAS + '.kt'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def once(text, old, new):
    require(text.count(old) == 1, 'Expected one transformation anchor: ' + old[:100])
    return text.replace(old, new, 1)


def transform(parent, helper):
    text = parent.decode()
    text = once(text, 'class AssetLanguageGpuTripletDiagnosticTest {', 'class ' + ALIAS + ' {')
    text = once(text, 'arguments.getString("languageGpuTripletCheck")', 'arguments.getString("languageSettledObservation")')
    text = once(text, '"language-gpu-triplet")', '"language-settled-observation")')
    text = once(text, '.put("schema", 1).put("research_only", true)',
                '.put("schema", 1).put("research_only", true)\n'
                '            .put("observation_protocol", "observed-terminal-geometry-20261116")\n'
                '            .put("previous_failure_report_sha256", "630dabe31fe3c69e2daf9aed26a6c414221ec6e9ecbf1c72aec62d3e64967ce2")')
    text = once(text, '"stable names the first settled request; stable/late pixels must be examined before claiming temporal stability.",',
                '"E_stable follows exact observed terminal geometry; this is not observation of mathematical motion rest.",')
    begin = '            waitFor("All five rows finish natural expansion") {\n'
    end = '            report.getJSONObject("geometry").put("E_before", tripletGeometry())'
    require(text.count(begin) == text.count(end) == 1, 'Original settled observation boundaries changed')
    start, finish = text.index(begin), text.index(end)
    text = text[:start] + '            val stableRows = awaitObservedTerminalGeometry(directory, report, closedBounds)\n' + text[finish:]
    text = once(text, '    private data class TripletCapturePair', helper.decode() + '\n\n    private data class TripletCapturePair')
    require(text.count('@Test fun ') == 1, 'Exactly one selected Android test is required')
    for start, finish in (
        ('    private fun captureSettledGpu(', '    private data class GpuRowProbe'),
        ('    private fun gpuRowProbe(', '    @Composable private fun Fixture()'),
        ('    /** The rule only bootstraps', '    private fun captureSettledGpu('),
        ('    private fun inject(', '    /** Keep the same physical pointer'),
        ('                    GlassBackground(0f,', '                    BoxWithConstraints('),
        ('    private fun captureTripletStage(', '    private fun writeTripletCapture('),
        ('    private fun measureTripletPair(', '    private fun assertTripletOriginalPredicates('),
        ('    private fun assertTripletOriginalPredicates(', '    private fun tripletRows('),
    ):
        expected = parent.decode()[parent.decode().index(start):parent.decode().index(finish)]
        require(expected in text, 'Protected parent section changed: ' + start)
    for line in (
        '            open(67L, 850L)',
        '            assertEquals("Settled row geometry stays unchanged in late capture", stableRows, lateRows)',
        '            assertTrue("Each settled/late pair has identical pixels in every sampled row ROI", temporalPixelsEqual)',
    ):
        require(line in text, 'Original pointer/control removed: ' + line)
    return text.encode()


def expected():
    parent = (PARENT / PARENT_REL).read_bytes()
    require(digest(parent) == PARENT_SHA, 'Parent prepared source changed')
    require(digest((PARENT / 'source/LanguageMenuMotionCaptureTest.kt').read_bytes()) == SOURCE_SHA, 'Frozen original changed')
    helper = (ROOT / 'terminal-observation.kt.inc').read_bytes()
    output = transform(parent, helper)
    receipt = {
        'schema': 1, 'status': 'PREPARED_NOT_BUILT_OR_RUN', 'alias_class': ALIAS,
        'parent_source': '../control-regression-diagnostics-20261116/language-gpu/' + PARENT_REL,
        'parent_output_sha256': PARENT_SHA, 'original_source_sha256': SOURCE_SHA,
        'helper_sha256': digest(helper), 'generator_sha256': digest(Path(__file__).read_bytes()),
        'output_relative_path': OUTPUT, 'output_sha256': digest(output), 'output_bytes': len(output),
        'selected_android_tests': 1, 'source_root': 'prepared/sources',
        'mathematical_rest_observed': False, 'gradle_executed': False, 'device_used': False,
    }
    return output, receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Read-only deterministic output/receipt check')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    output, receipt = expected()
    if args.self_test:
        parent = (PARENT / PARENT_REL).read_bytes()
        helper = (ROOT / 'terminal-observation.kt.inc').read_bytes()
        rejected = 0
        for old, new in (
            (b'class AssetLanguageGpuTripletDiagnosticTest {', b'class Changed {'),
            (b'waitFor("All five rows finish natural expansion")', b'waitFor("Changed")'),
            (b'    private data class TripletCapturePair', b'    private data class Changed'),
        ):
            try:
                transform(parent.replace(old, new), helper)
            except ValueError:
                rejected += 1
            else:
                raise ValueError('Changed parent anchor accepted')
        ast.parse(Path(__file__).read_text())
        print(json.dumps({'status': 'STATIC_TRANSFORM_CONTRACTS_PASS', 'invalid_inputs_rejected': rejected,
                          'byte_preserved_sections': 8, 'gradle_executed': False, 'device_used': False}))
        return
    source_root = ROOT / 'prepared/sources'
    target = source_root / OUTPUT
    receipt_file = ROOT / 'prepared/preparation.json'
    for path in (ROOT, ROOT / 'prepared', source_root, *target.parents):
        if path.is_relative_to(ROOT):
            require(not path.is_symlink(), 'Output must not traverse symlinks')
    if not args.check:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(output)
        receipt_file.write_text(json.dumps(receipt, indent=2) + '\n')
    require(target.read_bytes() == output, 'Generated source differs')
    require(json.loads(receipt_file.read_text()) == receipt, 'Receipt differs')
    require([p for p in source_root.rglob('*') if p.is_file()] == [target], 'Expected exactly one prepared source')
    print(json.dumps({'status': 'STATIC_PREPARATION_VERIFIED' if args.check else 'PREPARED_NOT_BUILT_OR_RUN',
                      'alias_class': ALIAS, 'output_sha256': receipt['output_sha256'],
                      'gradle_executed': False, 'device_used': False}, indent=2))


if __name__ == '__main__':
    main()
