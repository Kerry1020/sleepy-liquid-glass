#!/usr/bin/env python3
"""Prepare one SHA-bound research test outside the Sleepy checkout."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT.parent / 'slider-fixtures'
SOURCE_MAP_SHA256 = '4743df6a03b68f30fe5f0071b9d23a23aa5db6042696e60c5cf063cfa9227032'
SOURCE_COMMIT = 'db1e2470db900d4642b27339c9cef31523ab75f3'
SOURCE_PATH = 'app/src/androidTest/java/com/lingion/sleepy/ui/component/NativeSliderOpticalWorldRenderTest.kt'
SOURCE_SHA256 = '1735702b83f009b1bfe2e01af82571b14017edb5f1dec851916b170a978cdb5e'
SOURCE_BYTES = 71695
ORIGINAL = b'NativeSliderOpticalWorldRenderTest'
ALIAS = b'AssetNativeSliderOpticalWorldRenderTest'
OUTPUT_PATH = 'com/lingion/sleepy/ui/component/AssetNativeSliderOpticalWorldRenderTest.kt'
OUTPUT_SHA256 = '2ab0164e70f7374f9851e03631c35613ba838152aa8ef10c107347dd33965da5'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def renamed(data):
    declaration = b'class ' + ORIGINAL + b' {'
    require(data.count(ORIGINAL) == 1, 'Original class must occur exactly once')
    require(data.count(declaration) == 1, 'Unexpected class declaration')
    require(ALIAS not in data, 'Alias already exists in frozen input')
    output = data.replace(declaration, b'class ' + ALIAS + b' {', 1)
    require(output.replace(ALIAS, ORIGINAL, 1) == data, 'Change exceeds the class rename')
    return output


def expected():
    mapping_file = FIXTURE / 'SOURCE-MAP.json'
    mapping_bytes = mapping_file.read_bytes()
    require(sha(mapping_bytes) == SOURCE_MAP_SHA256, 'Frozen SOURCE-MAP SHA differs')
    mapping = json.loads(mapping_bytes)
    require(mapping['source_commit'] == SOURCE_COMMIT, 'Unexpected source commit')
    android = [r for r in mapping['files'] if r['export_path'].startswith('app/src/androidTest/')]
    require(len(android) == 2, 'Expected the two original Android fixture exports')
    rows = [r for r in android if r['export_path'] == SOURCE_PATH]
    require(len(rows) == 1, 'Selected source must have exactly one manifest entry')
    row = rows[0]
    require(row['source_path'] == SOURCE_PATH and row['source_git_mode'] == '100644',
            'Unexpected selected source identity')
    require(row['sha256'] == SOURCE_SHA256 and row['bytes'] == SOURCE_BYTES,
            'Selected SOURCE-MAP entry differs from the pinned fixture')
    source = FIXTURE / SOURCE_PATH
    require(not source.is_symlink() and source.resolve().is_relative_to(FIXTURE.resolve()),
            'Source must stay inside the frozen fixture')
    data = source.read_bytes()
    require(len(data) == SOURCE_BYTES and sha(data) == SOURCE_SHA256, 'Source bytes differ')
    output = renamed(data)
    require(sha(output) == OUTPUT_SHA256, 'Renamed output differs')
    receipt = {
        'schema': 1,
        'status': 'PREPARED_NOT_BUILT_OR_RUN',
        'source_map': '../slider-fixtures/SOURCE-MAP.json',
        'source_map_sha256': SOURCE_MAP_SHA256,
        'source_commit': SOURCE_COMMIT,
        'source_path': SOURCE_PATH,
        'source_git_blob_oid': row['source_git_blob_oid'],
        'source_sha256': SOURCE_SHA256,
        'source_bytes': SOURCE_BYTES,
        'transformation': 'Only the single Kotlin class declaration is renamed; all other bytes retained.',
        'original_class': ORIGINAL.decode(),
        'alias_class': ALIAS.decode(),
        'output_relative_path': OUTPUT_PATH,
        'output_sha256': OUTPUT_SHA256,
        'output_bytes': len(output),
        'source_root': '.local/sources',
        'selected_android_tests': 1,
        'host_required': 'Sleepy :app androidTest helpers, theme/adapters and instrumentation runner',
    }
    return output, receipt


def local_path(relative):
    path = ROOT / '.local' / relative
    for part in [path, *path.parents]:
        if part == ROOT:
            break
        require(not part.is_symlink(), 'Refusing symlink in generated output path')
    require(path.resolve().is_relative_to((ROOT / '.local').resolve()), 'Output escaped .local')
    return path


def verify_tree(source_root, target):
    require(source_root.is_dir(), 'Prepared source root is missing; run prepare-overlay.py')
    files = []
    for path in source_root.rglob('*'):
        require(not path.is_symlink(), 'Generated sources must contain no symlinks')
        if path.is_file():
            files.append(path)
    require(files == [target], 'Overlay must contain only the selected aliased Kotlin file')


def self_test():
    source = b'package test\nclass NativeSliderOpticalWorldRenderTest {\n}\n'
    require(renamed(source) == b'package test\nclass AssetNativeSliderOpticalWorldRenderTest {\n}\n',
            'Rename contract failed')
    rejected = 0
    for bad in (b'class Other {}', source + source, source + ALIAS):
        try:
            renamed(bad)
        except ValueError:
            rejected += 1
        else:
            raise ValueError('Ambiguous/missing class unexpectedly accepted')
    return {'status': 'PASS', 'rename_only': True, 'invalid_inputs_rejected': rejected,
            'gradle_executed': False, 'device_used': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Read-only check of the prepared overlay')
    parser.add_argument('--self-test', action='store_true', help='Pure in-memory rename contracts only')
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), sort_keys=True))
        return
    output, receipt = expected()
    source_root = local_path('sources')
    target = local_path('sources/' + OUTPUT_PATH)
    receipt_file = local_path('preparation.json')
    if not args.check:
        if source_root.exists():
            verify_tree(source_root, target)
            require(target.read_bytes() == output, 'Refusing to replace modified prepared source')
        if receipt_file.exists():
            require(json.loads(receipt_file.read_text()) == receipt, 'Refusing to replace a different receipt')
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            with target.open('xb') as stream:
                stream.write(output)
        if not receipt_file.exists():
            with receipt_file.open('x') as stream:
                stream.write(json.dumps(receipt, indent=2) + '\n')
    verify_tree(source_root, target)
    require(target.read_bytes() == output, 'Prepared source changed')
    require(json.loads(receipt_file.read_text()) == receipt, 'Preparation receipt changed')
    print(json.dumps({'status': 'VERIFIED' if args.check else 'PREPARED_NOT_BUILT_OR_RUN',
                      'source_root': str(source_root), 'test_class': 'com.lingion.sleepy.ui.component.' + ALIAS.decode(),
                      'source_sha256': SOURCE_SHA256, 'output_sha256': OUTPUT_SHA256}, sort_keys=True))


if __name__ == '__main__':
    main()
