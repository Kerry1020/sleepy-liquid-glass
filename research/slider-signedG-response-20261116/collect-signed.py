#!/usr/bin/env python3
"""Validate frozen acquisition and collect direct endpoint bytes, without fits."""
from pathlib import Path
import argparse
import binascii
import hashlib
import json
import struct
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / 'slider-color-response-20261116'
ROI = (331, 795, 419, 883)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def chunks(data):
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    found, offset = [], 8
    while offset < len(data):
        n = struct.unpack('>I', data[offset:offset+4])[0]
        tag, value = data[offset+4:offset+8], data[offset+8:offset+8+n]
        assert len(value) == n
        crc = struct.unpack('>I', data[offset+8+n:offset+12+n])[0]
        assert binascii.crc32(tag+value) & 0xffffffff == crc
        found.append((tag, value))
        offset += n+12
        if tag == b'IEND':
            break
    assert offset == len(data) and found[-1] == (b'IEND', b'')
    return found


def read_png(path):
    metadata = chunks(path.read_bytes())
    assert [v for k, v in metadata if k == b'sRGB'] == [b'\x00'], str(path)
    assert not any(k in (b'iCCP', b'gAMA', b'cHRM') for k, _ in metadata), str(path)
    with Image.open(path) as im:
        assert im.size == (750, 1334) and im.mode in ('RGB', 'RGBA')
        a = np.asarray(im)
        if im.mode == 'RGBA':
            assert np.all(a[..., 3] == 255)
        return a[ROI[1]:ROI[3], ROI[0]:ROI[2], :3].copy()


def pair(folder, spec_root, expected_freeze):
    index_file = folder / 'index-strict.json'
    strict_file = folder / 'endpoint-verification-strict.json'
    index = json.loads(index_file.read_text())
    strict = json.loads(strict_file.read_text())
    receipt_file = folder / 'receipt.json'
    receipt = json.loads(receipt_file.read_text())
    specification_file = spec_root / 'shape-spec.json'
    manifest_file = spec_root / 'inputs/manifest.json'
    specification = json.loads(specification_file.read_text())
    manifest = json.loads(manifest_file.read_text())
    assert receipt['phase'] == 'capture' and receipt['round'] == folder.parent.name
    assert receipt['freeze_sha256'] == sha(expected_freeze)
    frozen = json.loads(expected_freeze.read_text())
    assert receipt['native_binaries'] == frozen['native_binaries']
    assert receipt['prepared_native_files'] == frozen['prepared_native_files']
    assert receipt['simulator_identity'] == frozen['simulator']
    assert receipt['spec_sha256'] == sha(specification_file) and receipt['manifest_sha256'] == sha(manifest_file)
    assert strict['specSHA256'] == sha(specification_file) and strict['manifestSHA256'] == sha(manifest_file)
    assert strict['sourceSetID'] == manifest['set_id']
    for relative, expected in receipt['analysis_artifacts'].items():
        assert sha(folder / relative) == expected, relative
    for row in manifest['inputs']:
        assert sha(spec_root / 'inputs' / row['file']) == row['sha256']
    assert index['status'] == strict['status'] == 'passed'
    assert strict['verifiedHeldEndpoints'] == 2 and strict['verifiedShapeFlatPairs'] == 1
    assert len(index['captures']) == 1
    record = index['captures'][0]
    assert record['stage_id'] == record['coverage_label'] == 'full100'
    assert record['shape_id'] == record['input_id'] == specification['first_input_id']
    assert specification['flat_input_id'] == 'st00_flat128'
    candidates = list((folder / 'held').rglob('*.png'))
    assert len(candidates) == 2
    by_sha = {sha(p): p for p in candidates}
    assert len(by_sha) == 2
    result = {}
    sources = {str(p): sha(p) for p in (index_file, strict_file, receipt_file, specification_file, manifest_file)}
    for role, key in [('shape', 'sha256'), ('flat', 'flat_sha256')]:
        path = by_sha[record[key]]
        sources[str(path)] = sha(path)
        result[role] = read_png(path)
    result['bounds'] = np.asarray(record['actual_carrier_bounds_world_xywh'], float)
    result['flat_bounds'] = np.asarray(record['flat_actual_carrier_bounds_world_xywh'], float)
    result['sources'] = sources
    return result


def self_test():
    def chunk(tag, value):
        return struct.pack('>I', len(value)) + tag + value + struct.pack('>I', binascii.crc32(tag+value) & 0xffffffff)
    data = b'\x89PNG\r\n\x1a\n' + chunk(b'sRGB', b'\x00') + chunk(b'IEND', b'')
    assert chunks(data) == [(b'sRGB', b'\x00'), (b'IEND', b'')]
    for bad in (data[:-1], data+b'x', data[:18]+b'\x00'+data[19:]):
        try:
            chunks(bad)
        except (AssertionError, struct.error):
            pass
        else:
            raise AssertionError('Invalid PNG chunk stream accepted')
    x, y = np.meshgrid((np.arange(ROI[0], ROI[2])+.5)/2, (np.arange(ROI[1], ROI[3])+.5)/2)
    assert x.shape == y.shape == (88, 88) and x[27, 54] == 192.75 and y[27, 54] == 411.25
    return {'status': 'PASS', 'contracts': 5, 'captures_read': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test', action='store_true')
    parser.add_argument('--output', type=Path, default=ROOT/'analysis')
    args = parser.parse_args()
    synthetic = self_test()
    if args.self_test:
        print(json.dumps(synthetic)); return
    assert not args.output.exists(), 'Refusing overwrite'
    freeze_file = ROOT / 'freeze.json'
    freeze = json.loads(freeze_file.read_text())
    for relative, expected in freeze['files'].items():
        assert sha(ROOT / relative) == expected, relative
    new = {name: pair(ROOT/'rounds'/name/'native-r1', ROOT/'inputs/rounds'/name, freeze_file)
           for name in freeze['round_order']}
    old = {name: pair(OLD/'evidence/rounds'/name/'native-r1', OLD/'inputs/rounds'/name, OLD/'freeze.json')
           for name in ('control-pre', 'global-G')}
    reference = old['control-pre']
    all_pairs = list(new.values()) + list(old.values())
    bounds = np.stack([v[key] for v in all_pairs for key in ('bounds', 'flat_bounds')])
    geometry_range = np.ptp(bounds, axis=0)
    flat_drift = [int(np.abs(v['flat'].astype(int)-reference['flat'].astype(int)).max()) for v in all_pairs]
    shape_control_drift = {name: int(np.abs(new[name]['shape'].astype(int)-reference['shape'].astype(int)).max())
                           for name in ('control-pre', 'control-post')}
    assert (geometry_range <= .1).all(), geometry_range
    assert max(flat_drift) == 0, flat_drift
    assert max(shape_control_drift.values()) == 0, shape_control_drift
    output = np.stack([new['Gminus40']['shape'], new['Gminus20']['shape'],
                       new['control-pre']['shape'], old['global-G']['shape']])
    x, y = np.meshgrid((np.arange(ROI[0], ROI[2])+.5)/2, (np.arange(ROI[1], ROI[3])+.5)/2)
    left, top, width, height = new['control-pre']['bounds']
    radius = height/2
    dx = np.maximum(np.abs(x-left-width/2)-(width-height)/2, 0)
    depth = radius-np.hypot(dx, y-top-radius)
    args.output.mkdir()
    target = args.output/'signed-output.npz'
    np.savez_compressed(target, t=np.array([-40, -20, 0, 20]), output_rgb=output,
                        x=x, y=y, inset=depth, baseline_flat=reference['flat'])
    sources = {str(freeze_file): sha(freeze_file)}
    for v in all_pairs:
        sources.update(v['sources'])
    report = {'status': 'VALID_ACQUISITION_NOT_OPTICAL_ACCEPTANCE',
        'self_test': synthetic, 'protocol_sha256': sha(ROOT/'PROTOCOL.md'), 'collector_sha256': sha(Path(__file__)),
        'freeze_sha256': sha(freeze_file), 'output_npz_sha256': sha(target),
        'geometry_range_pt': geometry_range.tolist(), 'all_flat_maxabs_RGB': flat_drift,
        'new_controls_vs_published_maxabs_RGB': shape_control_drift, 'sources': sources,
        'endpoint_t_encoded_G': [-40, -20, 0, 20], 'output_shape': list(output.shape),
        'sample_world_192_75_411_25': output[:, 27, 54].tolist(),
        'limits': ['Signed raw encoded endpoint bytes, not linear light or recovered native pipeline.',
                   'Clipped-family compatibility is not proof of shared saturation or native clipping.',
                   'Existing +20 output merged only after exact ROI control/flat equality and geometry gate.']}
    (args.output/'collection.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k != 'sources'}, indent=2))


if __name__ == '__main__':
    main()
