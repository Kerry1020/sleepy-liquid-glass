#!/usr/bin/env python3
"""Verify this bounded increment; replay fixed ROI tables, not omitted acquisition logs."""
import csv
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent


def read(p):
    data = p.read_bytes()
    return json.loads(gzip.decompress(data) if p.suffix == '.gz' else data)


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def verified(e):
    p = HERE / e['path']
    assert p.is_file() and sha(p) == e['sha256'] and p.stat().st_size == e['bytes'], e['path']
    return p


def close(a, b):
    if a is None or b is None:
        assert a == b
    elif isinstance(a, (list, tuple)):
        assert len(a) == len(b)
        for x, y in zip(a, b):
            close(x, y)
    else:
        assert math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-10), (a, b)


shared = read(HERE / 'shared-dependencies.json')['files']
for e in shared:
    verified(e)
index = read(HERE / 'measurements/index.json')
helper = verified(index['frozen_helpers'])
spec = importlib.util.spec_from_file_location('frozen_roi_geometry', helper)
frozen = importlib.util.module_from_spec(spec);spec.loader.exec_module(frozen)
assert frozen.THRESHOLDS_BYTE == (4., 8., 16., 24.) and frozen.MIN_COLOR_COSINE == .8
captures = read(HERE / 'captures.json')
roi = captures['fixed_roi_xyxy_world']
directions = read(verified(index['comparisons']['star5-r4']))['fixed_analysis_policy']['region_color_direction_unit_rgb']
cache = {}
originals = set()
for group, records in captures['groups'].items():
    assert len(records) == 6
    for row in records:
        files = [verified(row[k]) for k in ('shape', 'flat')]
        originals.update(str(p.resolve()) for p in files)
        images = [frozen.rgb_image(p)[0] for p in files]
        grids = [frozen.mapping(row, im) for im in images]
        assert grids[0] == grids[1]
        xx, yy, rgb, sampling = frozen.crop_roi(images[0], grids[0], roi)
        _, _, flat, _ = frozen.crop_roi(images[1], grids[1], roi)
        if 'saved_sampling' in row:
            assert sampling == row['saved_sampling']
            for key, crop in [('shape', rgb), ('flat', flat)]:
                assert hashlib.sha256(crop.tobytes()).hexdigest() == row['original_screen_archives'][key]['fixed_roi_decoded_sha256']
        delta = rgb.astype(float) - flat.astype(float)
        chroma = delta - delta.mean(axis=2, keepdims=True)
        norm = np.linalg.norm(chroma, axis=2)
        masks = {}
        for region, direction in directions.items():
            projection = chroma @ np.asarray(direction)
            cosine = np.divide(projection, norm, out=np.zeros(norm.shape), where=norm != 0)
            for t in frozen.THRESHOLDS_BYTE:
                masks[region, t] = (projection >= t) & (cosine >= .8)
        for t in frozen.THRESHOLDS_BYTE:
            masks['whole', t] = np.logical_or.reduce([masks[k, t] for k in directions])
        geometry = {k: frozen.weighted_geometry(xx, yy, m.astype(float), grids[0]['pixels_per_world_unit']) for k, m in masks.items()}
        cache[group, row['stage_id']] = dict(masks=masks, geometry=geometry, xx=xx, yy=yy, row=row)

replayed = []
supports = []
for tag, entry in index['comparisons'].items():
    d = read(verified(entry));shape, candidate = tag.split('-')
    assert d['input_role'] == ('calibration' if shape == 'star5' else 'holdout')
    for stage in d['stages']:
        assert stage['baseline_candidate_geometry_and_source_mapping_identical']
        stage_id = stage['stage_id']
        n, b, c = [cache[f'{shape}-{v}', stage_id] for v in ('native', 'r2', candidate)]
        assert b['row']['actual_carrier_bounds_world_xywh'] == c['row']['actual_carrier_bounds_world_xywh']
        for region in stage['color_regions'] + [dict(region_id='whole', threshold_sensitivity=stage['whole_threshold_sensitivity'])]:
            name = region['region_id']
            for t in region['threshold_sensitivity']:
                threshold = t['threshold_projection_byte']
                ng, bg, cg = [x['geometry'][name, threshold] for x in (n, b, c)]
                for measured, saved in ((ng, t['native_geometry']), (bg, t['baseline']), (cg, t['candidate'])):
                    for field in ('area_world2', 'centroid_world', 'bounds_xyxy_world'):
                        close(measured[field], saved[field])
                na, ba, ca = [g['area_world2'] for g in (ng, bg, cg)]
                be, ce = [None if g['centroid_world'] is None or ng['centroid_world'] is None else
                          float(np.linalg.norm(np.asarray(g['centroid_world'])-ng['centroid_world'])) for g in (bg,cg)]
                close(be, t['baseline']['centroid_distance_from_native_world']);close(ce, t['candidate']['centroid_distance_from_native_world'])
                ae = abs(ca-na)-abs(ba-na);de = None if ce is None or be is None else ce-be
                close(ae,t['area_error_change']['change']);close(de,t['centroid_error_change']['change'])
                replayed.append(dict(experiment=tag, stage=stage_id, region=name, threshold=threshold,
                    native_area=na,r2_area=ba,candidate_area=ca,r2_area_error=abs(ba-na),candidate_area_error=abs(ca-na),
                    area_error_change=ae,r2_centroid_error=be,candidate_centroid_error=ce,centroid_error_change=de))
                if name != 'whole':
                    bm, cm = b['masks'][name,threshold], c['masks'][name,threshold]
                    supports.append(dict(experiment=tag,stage=stage_id,region=name,threshold=threshold,
                        r2_pixels=int(bm.sum()),candidate_pixels=int(cm.sum()),added_pixels=int((cm&~bm).sum()),
                        removed_pixels=int((bm&~cm).sum()),intersection_pixels=int((bm&cm).sum())))
    assert len(stage['color_regions']) == 3
assert len(replayed)==384 and len(supports)==288
saved = list(csv.DictReader((HERE/'measurements/all-thresholds.tsv').open(),delimiter='\t'))
assert len(saved)==len(replayed)
for original, replay in zip(saved,replayed):
    for k,v in replay.items():
        if k in ('experiment','stage','region'):
            assert original[k]==v
        else:
            close(None if original[k]=='' else float(original[k]),v)
for tag in ('star5-r4','star6-r4','star8-r4'):
    data=read(HERE/f'measurements/{tag}-actual-support-changes.json.gz')
    rows=data['rows'] if 'rows' in data else data['original_raster_color_cone']['rows']
    assert len(rows)==72
    for s in rows:
        t=s.get('threshold',s.get('threshold_byte'))
        rr=next(x for x in supports if (x['experiment'],x['stage'],x['region'],x['threshold'])==(tag,s['stage'],s['region'],t))
        for old,new in [('r2_pixels','r2_pixels'),('r4_pixels','candidate_pixels'),('added_pixels','added_pixels'),('removed_pixels','removed_pixels'),('intersection_pixels','intersection_pixels')]:
            alt={'r2_pixels':'r2_samples','r4_pixels':'r4_samples','added_pixels':'actual_added_samples','removed_pixels':'actual_removed_samples','intersection_pixels':'intersection_samples'}
            assert s.get(old,s.get(alt[old]))==rr[new]
with (HERE/'measurements/replayed-actual-support.tsv').open('w',newline='') as f:
    writer=csv.DictWriter(f,supports[0].keys(),delimiter='\t');writer.writeheader();writer.writerows(supports)

links=0
for md in [HERE/'README.md',HERE.parents[2]/'glass-slider-shoulder-experiments.md']:
    for target in re.findall(r'\]\(([^)]+)\)',md.read_text()):
        assert not target.startswith('/') and '://' not in target,target
        resolved=(md.parent/target.split('#')[0]).resolve()
        assert resolved.exists() or resolved in (HERE/'validation.json',HERE/'manifest.json',HERE/'SHA256SUMS'),(str(md),target)
        links+=1
if (HERE/'manifest.json').exists():
    manifest=read(HERE/'manifest.json')
    for e in manifest['local_files']+manifest['shared_files']+[manifest['companion_report']]:
        verified(e)
report=dict(schema=1,status='passed_bounded_original_png_and_fixed_table_replay',
    shared_dependency_files=len(shared),original_pngs_verified=len(originals),shape_flat_pairs=60,
    replayed_threshold_rows=len(replayed),actual_support_rows=len(supports),relative_markdown_links=links,
    maximum_numeric_tolerance=dict(relative=1e-12,absolute=1e-10),
    replay_scope='Original retained Window PNG RGB equals archived analysis Screen ROI. Shared native/r2 originals retained. Replays area/centroid/bounds/error arithmetic and actual added/removed sets at all frozen thresholds.',
    not_replayed=['Omitted full native endpoint/presentation traces and all49 acquisition files per run; saved checks remain hash-addressed historical receipts.',
                  'Stored signed-grid/prepredicted-source diagnostics and normal-localization JSON are preserved with hashes; this minimal checker does not rerun those exploratory models.',
                  'Full omitted Screen PNG hash cannot be reverified from an ROI, Window PNG or resized contact sheet.',
                  'No new GPU rendering, physical thickness recovery, dynamics or parity acceptance.'],
    r3='rejected as universal replacement',r4='rejected as universal replacement',restored_r2='unaccepted checkpoint',seven_point='not acquired')
(HERE/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
