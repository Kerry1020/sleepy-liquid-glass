#!/usr/bin/env python3
"""Prepare signed G sources without changing original geometry or native code."""
from pathlib import Path
import copy
import hashlib
import json
import os
import shutil
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / 'slider-color-response-20261116'
SOURCE = OLD / 'inputs/rounds/control-pre'
ROUNDS = [('control-pre', 0), ('Gminus20', -20), ('Gminus40', -40), ('control-post', 0)]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def masks_to_original(node, base):
    if isinstance(node, dict):
        for k, v in list(node.items()):
            if k in ('coverage_count_mask_png', 'binary_mask_png'):
                p = (SOURCE / v).resolve()
                assert p.is_relative_to((OLD / 'inputs/source-masks').resolve()) and p.is_file()
                node[k] = os.path.relpath(p, base)
            else:
                masks_to_original(v, base)
    elif isinstance(node, list):
        for v in node:
            masks_to_original(v, base)


def main():
    assert not (ROOT / 'inputs').exists() and not (ROOT / 'source-verification.json').exists()
    freeze = json.loads((OLD / 'freeze.json').read_text())
    for relative, expected in freeze['files'].items():
        assert sha(OLD / relative) == expected, relative
    original = json.loads((SOURCE / 'inputs/manifest.json').read_text())
    specification = json.loads((SOURCE / 'shape-spec.json').read_text())
    first = specification['first_input_id']
    assert first == 'st01_rgb_star_d16'
    with Image.open(SOURCE / 'inputs' / (first + '.png')) as im:
        assert im.mode == 'RGB' and im.size == (750, 1334)
        base, icc = np.asarray(im).copy(), im.info['icc_profile']
    assert base[..., 1].min() == 48
    receipt = {'status': 'PREPARED_NOT_CAPTURED', 'generator_sha256': sha(Path(__file__)),
               'protocol_sha256': sha(ROOT / 'PROTOCOL.md'), 'old_freeze_sha256': sha(OLD / 'freeze.json'),
               'source_base_sha256': sha(SOURCE / 'inputs' / (first + '.png')), 'rounds': []}
    for name, delta in ROUNDS:
        dest = ROOT / 'inputs/rounds' / name
        pngs = dest / 'inputs'
        pngs.mkdir(parents=True)
        identifier = first if delta == 0 else first + '_gminus' + str(-delta)
        actual = base.astype(np.int16)
        actual[..., 1] += delta
        assert actual.min() >= 0 and actual.max() <= 255
        assert np.array_equal(actual[..., [0, 2]], base[..., [0, 2]])
        assert np.all(actual[..., 1] - base[..., 1] == delta)
        target = pngs / (identifier + '.png')
        if delta:
            Image.fromarray(actual.astype(np.uint8)).save(target, icc_profile=icc)
        else:
            shutil.copyfile(SOURCE / 'inputs' / (first + '.png'), target)
        with Image.open(target) as im:
            assert im.info['icc_profile'] == icc and np.array_equal(np.asarray(im), actual)
        manifest = copy.deepcopy(original)
        manifest['set_id'] = 'slider_signedG_20261116_' + name.lower().replace('-', '_')
        for entry in manifest['inputs']:
            if entry['id'] == first:
                entry.update(id=identifier, file=identifier + '.png', sha256=sha(target), bytes=target.stat().st_size)
            else:
                shutil.copyfile(SOURCE / 'inputs' / entry['file'], pngs / entry['file'])
        spec = copy.deepcopy(specification)
        spec['first_input_id'] = identifier
        spec['status'] = 'signed G calibration preparation only; no optical acceptance'
        spec['world']['background_rgb'] = [128, 128 + delta, 128]
        spec['rasterization']['method'] = 'Original RGB-star raster plus signed global G integer delta; no source clipping or resampling'
        spec.pop('color_response_preparation', None)
        spec['signed_G_preparation'] = {'round': name, 'delta_encoded_G': delta, 'geometry_unchanged': True,
            'flat_unchanged': True, 'no_source_clipping': True, 'not_optical_acceptance': True}
        spec['scheduled_input_ids'] = [identifier, 'st00_flat128']
        for entry in spec['inputs']:
            if entry['id'] == first:
                entry.update(id=identifier, source_sha256=sha(target))
                shape = entry['shape']
                shape.update(id=identifier, source_png='inputs/' + identifier + '.png', source_sha256=sha(target))
                for region in shape['regions']:
                    region['color_rgb'][1] += delta
        masks_to_original(spec, dest)
        assert spec['stages'] == specification['stages']
        assert all(sha(pngs / e['file']) == e['sha256'] for e in manifest['inputs'])
        write(pngs / 'manifest.json', manifest)
        write(dest / 'shape-spec.json', spec)
        receipt['rounds'].append({'round': name, 'delta_encoded_G': delta, 'first_input_id': identifier,
            'source_sha256': sha(target), 'min_RGB': actual.min(axis=(0, 1)).tolist(),
            'max_RGB': actual.max(axis=(0, 1)).tolist(), 'flat_sha256': sha(pngs / 'st00_flat128.png')})
    write(ROOT / 'source-verification.json', receipt)
    print(json.dumps({'status': receipt['status'], 'rounds': receipt['rounds']}))


if __name__ == '__main__':
    main()
