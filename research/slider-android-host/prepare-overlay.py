#!/usr/bin/env python3
"""Prepare a SHA-bound fixture and complete namespaced helpers outside Sleepy."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT.parent.parent
FIXTURE = ROOT.parent / 'slider-fixtures'
SOURCE_MAP_SHA256 = '4743df6a03b68f30fe5f0071b9d23a23aa5db6042696e60c5cf063cfa9227032'
SOURCE_COMMIT = 'db1e2470db900d4642b27339c9cef31523ab75f3'
SOURCE_PATH = 'app/src/androidTest/java/com/lingion/sleepy/ui/component/NativeSliderOpticalWorldRenderTest.kt'
SOURCE_BLOB = '9d534052fedc25c069cea4fc2f2b7924dbbaba90'
SOURCE_SHA256 = '1735702b83f009b1bfe2e01af82571b14017edb5f1dec851916b170a978cdb5e'
SOURCE_BYTES = 71695
ORIGINAL = b'NativeSliderOpticalWorldRenderTest'
ALIAS = b'AssetNativeSliderOpticalWorldRenderTest'
OUTPUT_PATH = 'com/lingion/sleepy/ui/component/AssetNativeSliderOpticalWorldRenderTest.kt'
OUTPUT_SHA256 = '4e25fe39264656134a48958bdd49aeb1506f17815c8610d2de4219042e52f360'
HELPER_MAP_PATH = 'research/sleepy-research-migration-20261116/followup/SOURCE-MAP.json'
HELPER_MAP_SHA256 = '1bf6f7e90a487470713c86bbc9da0183461198bcf5619d9633c9f876cc8d31d3'
HELPER_COMMIT = 'd38e9d1a92adcde69264bdd50313948bdd29ab0e'
HELPER_SOURCE_PATH = 'app/src/androidTest/java/com/lingion/sleepy/ui/component/GlassOpticalCaptureFixtures.kt'
HELPER_ASSET_PATH = 'research/sleepy-research-migration-20261116/followup/sources/' + HELPER_SOURCE_PATH
HELPER_BLOB = 'ec3922c4d1651ee5507f1b394b208cd9957c8d9d'
HELPER_SHA256 = '3bcee1b8b7d2d4f1d6e452f7ecd8dfa75e9e65329c40dfa7eff3436b9850d8d0'
HELPER_BYTES = 30049
HELPER_OUTPUT_PATH = 'com/lingion/sleepy/ui/component/assetresearch/AssetGlassOpticalCaptureFixtures.kt'
HELPER_OUTPUT_SHA256 = 'eee6b8de60ca26cc9845dd3ea9a6ecf8b443c8f4bd1cb05589afdd17c7852c8d'
PACKAGE = b'com.lingion.sleepy.ui.component'
HELPER_PACKAGE = PACKAGE + b'.assetresearch'
HELPER_ALIASES = (
    (b'OpticalBackground', b'AssetResearchOpticalBackground', 3),
    (b'OpticalCaptureBackground', b'AssetResearchOpticalCaptureBackground', 1),
    (b'OpticalLayoutGeometry', b'AssetResearchOpticalLayoutGeometry', 14),
    (b'OpticalCaptureWindow', b'AssetResearchOpticalCaptureWindow', 3),
    (b'saveOpticalPng', b'assetResearchSaveOpticalPng', 6),
    (b'awaitOpticalBackgroundScreen', b'assetResearchAwaitOpticalBackgroundScreen', 2),
    (b'awaitOpticalSurfaceScreen', b'assetResearchAwaitOpticalSurfaceScreen', 1),
    (b'opticalRegionMetrics', b'assetResearchOpticalRegionMetrics', 2),
)
GENERATED_ROOT = '.local/v2/sources'
GENERATED_RECEIPT = '.local/v2/preparation.json'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def unique_json(data):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'Duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=unique)


def frozen_bytes(relative, expected_sha, expected_bytes=None):
    path = ASSETS / relative
    require(not Path(relative).is_absolute() and path.resolve().is_relative_to(ASSETS),
            'Frozen source escaped the asset repository')
    for part in (path, *path.parents):
        if part == ASSETS:
            break
        require(not part.is_symlink(), 'Frozen source must contain no symlink')
    data = path.read_bytes()
    require(sha(data) == expected_sha, 'Frozen SHA differs: ' + relative)
    require(expected_bytes is None or len(data) == expected_bytes, 'Frozen byte count differs: ' + relative)
    return data


def imports_block():
    return b''.join(b'import ' + HELPER_PACKAGE + b'.' + old + b' as ' + alias + b'\n'
                    for old, alias, _ in HELPER_ALIASES)


def fixture_overlay(data):
    require(len(data) == SOURCE_BYTES and sha(data) == SOURCE_SHA256, 'Frozen fixture bytes differ')
    declaration = b'class ' + ORIGINAL + b' {'
    require(data.count(ORIGINAL) == 1 and data.count(declaration) == 1, 'Unexpected fixture declaration')
    require(ALIAS not in data and HELPER_PACKAGE not in data, 'Research alias/package already exists')
    result = data.replace(declaration, b'class ' + ALIAS + b' {', 1)
    for old, alias, count in HELPER_ALIASES:
        pattern = rb'\b' + old + rb'\b'
        require(alias not in data and len(re.findall(pattern, data)) == count,
                'Helper reference count differs: ' + old.decode())
        result, changed = re.subn(pattern, alias, result)
        require(changed == count, 'Helper reference replacement differs')
    anchor = b'package ' + PACKAGE + b'\n\n'
    require(result.count(anchor) == 1 and result.startswith(anchor), 'Unexpected fixture package header')
    result = result.replace(anchor, anchor + imports_block() + b'\n', 1)
    restored = result.replace(imports_block() + b'\n', b'', 1)
    for old, alias, count in HELPER_ALIASES:
        restored, changed = re.subn(rb'\b' + alias + rb'\b', old, restored)
        require(changed == count, 'Inverse helper reference count differs')
    restored = restored.replace(b'class ' + ALIAS + b' {', declaration, 1)
    require(restored == data, 'Fixture edits exceed the declared names/imports')
    require(sha(result) == OUTPUT_SHA256, 'Fixture overlay SHA differs')
    return result


def helper_overlay(data):
    require(len(data) == HELPER_BYTES and sha(data) == HELPER_SHA256, 'Frozen helper bytes differ')
    original = b'package ' + PACKAGE + b'\n'
    changed = b'package ' + HELPER_PACKAGE + b'\n'
    require(data.startswith(original) and data.count(original) == 1 and HELPER_PACKAGE not in data,
            'Unexpected helper package header')
    result = data.replace(original, changed, 1)
    require(result.replace(changed, original, 1) == data, 'Helper edits exceed the package change')
    require(sha(result) == HELPER_OUTPUT_SHA256, 'Helper overlay SHA differs')
    return result


def expected():
    mapping = unique_json(frozen_bytes('research/slider-fixtures/SOURCE-MAP.json', SOURCE_MAP_SHA256))
    require(mapping['source_commit'] == SOURCE_COMMIT, 'Unexpected fixture source commit')
    android = [r for r in mapping['files'] if r['export_path'].startswith('app/src/androidTest/')]
    require(len(android) == 2, 'Expected the two original Android fixture exports')
    rows = [r for r in android if r['export_path'] == SOURCE_PATH]
    require(len(rows) == 1, 'Fixture must have exactly one map entry')
    row = rows[0]
    require(row['source_path'] == SOURCE_PATH and row['source_git_mode'] == '100644' and
            row['source_git_blob_oid'] == SOURCE_BLOB and row['sha256'] == SOURCE_SHA256 and
            row['bytes'] == SOURCE_BYTES, 'Selected fixture map identity differs')
    helpers = unique_json(frozen_bytes(HELPER_MAP_PATH, HELPER_MAP_SHA256))
    require(helpers['source_repository'] == 'lingion/sleepy' and helpers['source_commit'] == HELPER_COMMIT,
            'Unexpected helper source repository/commit')
    matches = [r for r in helpers['files'] if r['source_path'] == HELPER_SOURCE_PATH]
    require(len(matches) == 1, 'Helpers must have exactly one map entry')
    helper = matches[0]
    require(helper['asset_path'] == HELPER_ASSET_PATH and helper['source_git_blob'] == HELPER_BLOB and
            helper['sha256'] == HELPER_SHA256 and helper['bytes'] == HELPER_BYTES,
            'Selected helper map identity differs')
    outputs = {
        OUTPUT_PATH: fixture_overlay(frozen_bytes('research/slider-fixtures/' + SOURCE_PATH, SOURCE_SHA256, SOURCE_BYTES)),
        HELPER_OUTPUT_PATH: helper_overlay(frozen_bytes(HELPER_ASSET_PATH, HELPER_SHA256, HELPER_BYTES)),
    }
    artifacts = [
        {'role': 'fixture', 'source_map': '../slider-fixtures/SOURCE-MAP.json',
         'source_map_sha256': SOURCE_MAP_SHA256, 'source_repository': 'lingion/sleepy',
         'source_commit': SOURCE_COMMIT, 'source_path': SOURCE_PATH,
         'asset_path': 'research/slider-fixtures/' + SOURCE_PATH, 'source_git_blob_oid': SOURCE_BLOB,
         'source_sha256': SOURCE_SHA256, 'source_bytes': SOURCE_BYTES, 'output_relative_path': OUTPUT_PATH,
         'transformation': {'class_rename': {'from': ORIGINAL.decode(), 'to': ALIAS.decode(), 'count': 1},
                            'helper_import_package': HELPER_PACKAGE.decode(),
                            'helper_identifier_aliases': [{'from': old.decode(), 'to': alias.decode(), 'count': count}
                                                          for old, alias, count in HELPER_ALIASES],
                            'fixed_import_block_insertions': 1, 'inverse_byte_equality_verified': True}},
        {'role': 'helpers', 'source_map': '../sleepy-research-migration-20261116/followup/SOURCE-MAP.json',
         'source_map_sha256': HELPER_MAP_SHA256, 'source_repository': 'lingion/sleepy',
         'source_commit': HELPER_COMMIT, 'source_path': HELPER_SOURCE_PATH, 'asset_path': HELPER_ASSET_PATH,
         'source_git_blob_oid': HELPER_BLOB, 'source_sha256': HELPER_SHA256, 'source_bytes': HELPER_BYTES,
         'output_relative_path': HELPER_OUTPUT_PATH,
         'transformation': {'package_rename': {'from': PACKAGE.decode(), 'to': HELPER_PACKAGE.decode(), 'count': 1},
                            'complete_source_retained': True, 'inverse_byte_equality_verified': True}},
    ]
    for artifact in artifacts:
        data = outputs[artifact['output_relative_path']]
        artifact.update(output_sha256=sha(data), output_bytes=len(data))
    receipt = {'schema': 2, 'status': 'PREPARED_NOT_BUILT_OR_RUN', 'source_root': GENERATED_ROOT,
               'alias_class': ALIAS.decode(), 'test_class': PACKAGE.decode() + '.' + ALIAS.decode(),
               'helper_package': HELPER_PACKAGE.decode(), 'selected_android_tests': 1,
               'selected_helper_files': 1, 'artifacts': artifacts,
               'host_required': 'Sleepy :app androidTest theme/adapters, AndroidJUnit/Compose and instrumentation runner',
               'host_helper_dependency': False, 'optical_acceptance': False}
    return outputs, receipt


def receipt_bytes(receipt):
    return (json.dumps(receipt, indent=2) + '\n').encode()


def local_path(relative):
    path = ROOT / relative
    require(path.resolve().is_relative_to((ROOT / '.local').resolve()), 'Output escaped .local')
    for part in (path, *path.parents):
        if part == ROOT:
            break
        require(not part.is_symlink(), 'Refusing symlink in generated output path')
    return path


def verify_tree(source_root, outputs):
    require(source_root.is_dir() and not source_root.is_symlink(), 'Prepared source root is missing or a symlink')
    files = set()
    for path in source_root.rglob('*'):
        require(not path.is_symlink(), 'Generated sources must contain no symlinks')
        require(path.is_dir() or path.is_file(), 'Unsupported generated source tree entry')
        if path.is_file():
            relative = path.relative_to(source_root).as_posix()
            files.add(relative)
            require(relative in outputs and path.read_bytes() == outputs[relative],
                    'Generated source is extra or modified: ' + relative)
    require(files == set(outputs), 'Overlay must contain exactly the prepared fixture and helpers')


def self_test():
    outputs, receipt = expected()
    rejected = 0
    for operation, source in ((fixture_overlay, frozen_bytes('research/slider-fixtures/' + SOURCE_PATH, SOURCE_SHA256)),
                              (helper_overlay, frozen_bytes(HELPER_ASSET_PATH, HELPER_SHA256))):
        for bad in (source + b'\n', source + source, source.replace(b'package ', b'package altered.', 1)):
            try:
                operation(bad)
            except ValueError:
                rejected += 1
            else:
                raise ValueError('Changed/ambiguous frozen source unexpectedly accepted')
    return {'status': 'PASS', 'prepared_kotlin_files': len(outputs), 'selected_android_tests': 1,
            'complete_namespaced_helper': True, 'inverse_byte_equality_verified': True,
            'helper_aliases': len(HELPER_ALIASES), 'invalid_inputs_rejected': rejected,
            'preparation_receipt_sha256': sha(receipt_bytes(receipt)),
            'gradle_executed': False, 'device_used': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Read-only check of the prepared v2 overlay')
    parser.add_argument('--self-test', action='store_true', help='Pure in-memory archive/transform contracts')
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), sort_keys=True))
        return
    outputs, receipt = expected()
    source_root = local_path(GENERATED_ROOT)
    receipt_file = local_path(GENERATED_RECEIPT)
    if not args.check:
        if source_root.exists():
            verify_tree(source_root, outputs)
        if receipt_file.exists():
            require(receipt_file.read_bytes() == receipt_bytes(receipt), 'Refusing to replace a different receipt')
        # All existing output is checked before the first write; old .local/sources stays untouched.
        for relative, data in outputs.items():
            target = local_path(GENERATED_ROOT + '/' + relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                with target.open('xb') as stream:
                    stream.write(data)
        if not receipt_file.exists():
            with receipt_file.open('xb') as stream:
                stream.write(receipt_bytes(receipt))
    verify_tree(source_root, outputs)
    require(receipt_file.read_bytes() == receipt_bytes(receipt), 'Prepared receipt changed')
    print(json.dumps({'status': 'VERIFIED' if args.check else 'PREPARED_NOT_BUILT_OR_RUN',
                      'source_root': str(source_root), 'test_class': receipt['test_class'],
                      'artifacts': {row['role']: {'path': row['output_relative_path'], 'sha256': row['output_sha256']}
                                    for row in receipt['artifacts']},
                      'preparation_receipt_sha256': sha(receipt_bytes(receipt))}, sort_keys=True))


if __name__ == '__main__':
    main()
