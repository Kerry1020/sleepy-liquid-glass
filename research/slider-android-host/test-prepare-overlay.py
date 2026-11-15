#!/usr/bin/env python3
"""Static regression contracts for the external two-file research overlay."""
import importlib.util
from pathlib import Path
import re
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('slider_overlay', ROOT / 'prepare-overlay.py')
overlay = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(overlay)

PACKAGE = b'com.lingion.sleepy.ui.component'
NAMESPACE = PACKAGE + b'.assetresearch'
ALIASES = {
    b'OpticalBackground': b'AssetResearchOpticalBackground',
    b'OpticalCaptureBackground': b'AssetResearchOpticalCaptureBackground',
    b'OpticalLayoutGeometry': b'AssetResearchOpticalLayoutGeometry',
    b'OpticalCaptureWindow': b'AssetResearchOpticalCaptureWindow',
    b'saveOpticalPng': b'assetResearchSaveOpticalPng',
    b'awaitOpticalBackgroundScreen': b'assetResearchAwaitOpticalBackgroundScreen',
    b'awaitOpticalSurfaceScreen': b'assetResearchAwaitOpticalSurfaceScreen',
    b'opticalRegionMetrics': b'assetResearchOpticalRegionMetrics',
}


class OverlayContracts(unittest.TestCase):
    def setUp(self):
        self.outputs, self.receipt = overlay.expected()
        self.records = {row['role']: row for row in self.receipt['artifacts']}

    def test_two_archived_inputs_and_two_outputs_are_bound(self):
        self.assertEqual(self.receipt['schema'], 2)
        self.assertEqual(set(self.records), {'fixture', 'helpers'})
        self.assertEqual(self.receipt['selected_android_tests'], 1)
        self.assertEqual(self.receipt['selected_helper_files'], 1)
        self.assertEqual(len(self.outputs), 2)
        for row in self.records.values():
            data = self.outputs[row['output_relative_path']]
            self.assertEqual(overlay.sha(data), row['output_sha256'])
            self.assertEqual(len(data), row['output_bytes'])
            self.assertEqual(len(row['source_map_sha256']), 64)
            self.assertEqual(len(row['source_git_blob_oid']), 40)

    def test_fixture_is_byte_exact_after_reversing_only_declared_edits(self):
        row = self.records['fixture']
        result = self.outputs[row['output_relative_path']]
        imports = b''.join(b'import ' + NAMESPACE + b'.' + old + b' as ' + alias + b'\n'
                           for old, alias in ALIASES.items())
        self.assertEqual(result.count(imports), 1)
        result = result.replace(imports + b'\n', b'', 1)
        for old, alias in ALIASES.items():
            self.assertNotRegex(result, rb'\b' + old + rb'\b')
            result = re.sub(rb'\b' + alias + rb'\b', old, result)
        result = result.replace(b'class AssetNativeSliderOpticalWorldRenderTest {',
                                b'class NativeSliderOpticalWorldRenderTest {', 1)
        original = (ROOT.parent / 'slider-fixtures' / row['source_path']).read_bytes()
        self.assertEqual(result, original)

    def test_complete_helper_changes_only_its_package(self):
        row = self.records['helpers']
        result = self.outputs[row['output_relative_path']]
        self.assertTrue(result.startswith(b'package ' + NAMESPACE + b'\n'))
        restored = result.replace(b'package ' + NAMESPACE + b'\n', b'package ' + PACKAGE + b'\n', 1)
        original = (ROOT.parent.parent / row['asset_path']).read_bytes()
        self.assertEqual(restored, original)
        for symbol in (b'OpticalLayoutGeometry', b'OpticalCaptureWindow', b'awaitOpticalSurfaceScreen'):
            self.assertIn(symbol, result)

    def test_changed_or_duplicate_frozen_inputs_are_rejected(self):
        fixture = (ROOT.parent / 'slider-fixtures' / self.records['fixture']['source_path']).read_bytes()
        helpers = (ROOT.parent.parent / self.records['helpers']['asset_path']).read_bytes()
        for operation, data in ((overlay.fixture_overlay, fixture), (overlay.helper_overlay, helpers)):
            for bad in (data + b'\n', data + data, data.replace(b'package ', b'package altered.', 1)):
                with self.assertRaises(ValueError):
                    operation(bad)

    def test_modified_extra_missing_and_symlink_outputs_are_rejected(self):
        local = ROOT / '.local'
        local.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='selftest-', dir=local) as directory:
            root = Path(directory) / 'sources'
            for relative, data in self.outputs.items():
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            overlay.verify_tree(root, self.outputs)
            target = root / next(iter(self.outputs))
            original = target.read_bytes()
            target.write_bytes(original + b'\n')
            with self.assertRaises(ValueError):
                overlay.verify_tree(root, self.outputs)
            target.write_bytes(original)
            extra = root / 'unexpected.kt'
            extra.write_bytes(b'package unexpected\n')
            with self.assertRaises(ValueError):
                overlay.verify_tree(root, self.outputs)
            extra.unlink()
            target.unlink()
            with self.assertRaises(ValueError):
                overlay.verify_tree(root, self.outputs)
            target.symlink_to(ROOT / 'README.md')
            with self.assertRaises(ValueError):
                overlay.verify_tree(root, self.outputs)


if __name__ == '__main__':
    unittest.main()
