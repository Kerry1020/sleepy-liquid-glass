#!/usr/bin/env python3
"""Deterministically derive one opt-in GPU research class from frozen Sleepy bytes."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE_PATH = 'app/src/androidTest/java/com/lingion/sleepy/ui/component/LanguageMenuMotionCaptureTest.kt'
SOURCE_SHA = '94b488726ac48e666160f786c5881c53b960fc948016a74a7235a923be2f9639'
ALIAS = 'AssetLanguageGpuTripletDiagnosticTest'
OUTPUT = 'com/lingion/sleepy/ui/component/' + ALIAS + '.kt'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def replace_once(text, old, new):
    require(text.count(old) == 1, 'Transformation anchor must occur once: ' + old[:100])
    return text.replace(old, new, 1)


def transform(source, body):
    text = source.decode('utf-8')
    text = replace_once(text, 'class LanguageMenuMotionCaptureTest {', 'class ' + ALIAS + ' {')
    text = replace_once(text, 'import androidx.compose.ui.draw.drawBehind\n',
                        'import androidx.compose.ui.draw.drawBehind\nimport androidx.compose.ui.draw.drawWithContent\n')
    text = replace_once(text, 'import org.json.JSONObject\n',
                        'import org.json.JSONObject\nimport org.json.JSONArray\nimport java.io.File\n')
    text = replace_once(text, 'import com.lingion.sleepy.ui.component.liquidglass.LanguageMenuVisualStateKey\n',
                        'import com.lingion.sleepy.ui.component.liquidglass.LanguageMenuVisualStateKey\nimport com.lingion.sleepy.ui.component.liquidglass.LanguageMenuHandoffStateKey\n')
    text = replace_once(text, '    private var lastPointer = Offset.Zero\n',
                        '    private var lastPointer = Offset.Zero\n'
                        '    private var suppressClosedSourceDrawing by mutableStateOf(false)\n'
                        '    private val sourceDrawSequence = AtomicInteger()\n'
                        '    @Volatile private var lastSourceDrawSuppressed: Boolean? = null\n')
    for name in ('selectionDismissalAndLongPressKeepTheOriginalPointerBehavior',
                 'heldLanguageRowKeepsItsFourCornersOutsideTheHighlight'):
        text = replace_once(text, '@Test fun ' + name, 'fun ' + name)
    begin = '    /** Every language row must retain real GPU material after the menu opens naturally. */\n'
    end = '    private data class CornerProbe'
    require(text.count(begin) == text.count(end) == 1, 'Original GPU test boundaries changed')
    start, finish = text.index(begin), text.index(end)
    text = text[:start] + body.decode('utf-8') + '\n' + text[finish:]
    text = replace_once(text, '                            .width(requestedWidth.coerceAtMost(maxWidth))) {',
                        '                            .width(requestedWidth.coerceAtMost(maxWidth))\n'
                        '                            .drawWithContent {\n'
                        '                                val suppressed = suppressClosedSourceDrawing\n'
                        '                                lastSourceDrawSuppressed = suppressed\n'
                        '                                sourceDrawSequence.incrementAndGet()\n'
                        '                                if (!suppressed) drawContent()\n'
                        '                            }) {')
    require(text.count('@Test fun ') == 1, 'Only the explicit research test may be selected')
    require('fun gpuRowProbe(code: String, roi: Rect, baseline: Bitmap, expanded: Bitmap)' in text,
            'Original pixel algorithm must remain present')
    # Byte-for-byte invariants protect clock, GPU fence, pointer injection, and background.
    for start_anchor, end_anchor in (
        ('    private fun captureSettledGpu(', '    private data class GpuRowProbe'),
        ('    private fun gpuRowProbe(', '    @Composable private fun Fixture()'),
        ('    /** The rule only bootstraps', '    private fun captureSettledGpu('),
        ('    private fun inject(', '    /** Keep the same physical pointer'),
        ('                    GlassBackground(0f,', '                    BoxWithConstraints('),
    ):
        original = source.decode('utf-8')
        expected = original[original.index(start_anchor):original.index(end_anchor)]
        require(expected in text, 'Protected original section changed: ' + start_anchor)
    return text.encode('utf-8')


def expected():
    source = (ROOT / 'source/LanguageMenuMotionCaptureTest.kt').read_bytes()
    require(sha(source) == SOURCE_SHA, 'Frozen A source differs from its pinned SHA-256')
    body = (ROOT / 'triplet-body.kt.inc').read_bytes()
    output = transform(source, body)
    receipt = {
        'schema': 1, 'status': 'PREPARED_NOT_BUILT_OR_RUN', 'source_path': SOURCE_PATH,
        'source_ref_reported_by_parent_not_git_verified_here': '693c3b51',
        'source_snapshot': 'source/LanguageMenuMotionCaptureTest.kt', 'source_sha256': SOURCE_SHA,
        'body_path': 'triplet-body.kt.inc', 'body_sha256': sha(body),
        'generator_sha256': sha(Path(__file__).read_bytes()), 'alias_class': ALIAS,
        'output_relative_path': OUTPUT, 'output_sha256': sha(output), 'output_bytes': len(output),
        'source_root': 'prepared/sources', 'selected_android_tests': 1,
        'transformations': [
            'Rename the class; retain the original helper functions and unused non-test scenarios.',
            'Remove @Test only from the two unrelated scenarios so default discovery sees one research test.',
            'Replace only the original GPU test body with the reviewed triplet-body.kt.inc.',
            'Add imports and draw-phase research state; add a draw-only gate to the existing source wrapper.',
            'Preserve original background, layout modifiers, GPU capture, pixel algorithm, pointer and real-time recomposer bytes.',
        ],
        'gradle_executed': False, 'device_used': False,
    }
    return output, receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Read-only deterministic preparation check')
    parser.add_argument('--origin', type=Path, help='Optionally read/hash an original source file or product checkout root')
    parser.add_argument('--self-test', action='store_true', help='Exercise transformation rejection and preservation contracts')
    args = parser.parse_args()
    output, receipt = expected()
    if args.origin:
        origin = args.origin / SOURCE_PATH if args.origin.is_dir() else args.origin
        require(sha(origin.read_bytes()) == SOURCE_SHA, 'Read-only original source hash changed')
    if args.self_test:
        source = (ROOT / 'source/LanguageMenuMotionCaptureTest.kt').read_bytes()
        body = (ROOT / 'triplet-body.kt.inc').read_bytes()
        rejected = 0
        for old, new in (
            (b'class LanguageMenuMotionCaptureTest {', b'class Changed {'),
            (b'.width(requestedWidth.coerceAtMost(maxWidth))) {', b'.width(999.dp)) {'),
            (b'import org.json.JSONObject\n', b'import org.json.JSONObject\nimport org.json.JSONObject\n'),
        ):
            try:
                transform(source.replace(old, new), body)
            except ValueError:
                rejected += 1
            else:
                raise ValueError('Ambiguous or changed source was accepted')
        ast.parse(Path(__file__).read_text(), filename=__file__)
        print(json.dumps({'status': 'STATIC_TRANSFORM_CONTRACTS_PASS', 'invalid_inputs_rejected': rejected,
                          'byte_preserved_sections': 5, 'gradle_executed': False, 'device_used': False}))
        return
    root = ROOT / 'prepared/sources'
    target = root / OUTPUT
    for path in (ROOT, ROOT / 'prepared', root, *target.parents):
        if path.is_relative_to(ROOT):
            require(not path.is_symlink(), 'Generated output must not traverse symlinks')
    receipt_path = ROOT / 'prepared/preparation.json'
    if not args.check:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(output)
        receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    require(target.read_bytes() == output, 'Prepared Kotlin differs; regenerate and review it')
    require(json.loads(receipt_path.read_text()) == receipt, 'Preparation receipt differs')
    require([p for p in root.rglob('*') if p.is_file()] == [target], 'Research source root must contain exactly one file')
    print(json.dumps({'status': 'STATIC_PREPARATION_VERIFIED' if args.check else 'PREPARED_NOT_BUILT_OR_RUN',
                      'test_class': 'com.lingion.sleepy.ui.component.' + ALIAS,
                      'source_root': 'prepared/sources', 'output_sha256': sha(output),
                      'origin_verified': bool(args.origin),
                      'gradle_executed': False, 'device_used': False}, indent=2))


if __name__ == '__main__':
    main()
