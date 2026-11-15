#!/usr/bin/env python3
"""Reuse the unchanged frozen native products; do not build duplicate caches."""
from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / 'slider-color-response-20261116'


def collector():
    spec = importlib.util.spec_from_file_location('original_RGB_collector', OLD / 'capture-native.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = ROOT
    module.PROJECT = OLD / '.local/native-project'
    module.DERIVED = OLD / '.local/DerivedData'
    module.ROUNDS = ['control-pre', 'Gminus20', 'Gminus40', 'control-post']
    return module


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] != 'capture':
        raise SystemExit('Only capture is supported; exact original native products are reused.')
    collector().main()
