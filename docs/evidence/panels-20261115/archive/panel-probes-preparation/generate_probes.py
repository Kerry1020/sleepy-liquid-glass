#!/usr/bin/env python3
"""Generate new public calibration probes; never reads an existing stimulus/image."""
from __future__ import annotations
import hashlib
import json
import math
import platform
import random
from pathlib import Path

import numpy as np
import PIL
from PIL import Image, ImageCms, ImageDraw

OUT = Path(__file__).resolve().parent
INPUTS = OUT / 'inputs'
W, H = 750, 1334
SEED = 0x2650515
NEUTRAL = (184, 184, 184)
ICC_PATH = OUT / 'srgb.icc'
if ICC_PATH.exists():
    ICC = ICC_PATH.read_bytes()
else:
    ICC = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    ICC_PATH.write_bytes(ICC)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save_image(identifier, array, selected, purpose):
    array = np.asarray(array, dtype=np.uint8)
    assert array.shape == (H, W, 3)
    path = INPUTS / f'{identifier}.png'
    Image.fromarray(array).save(path, icc_profile=ICC, optimize=True)
    with Image.open(path) as im:
        assert im.mode == 'RGB' and im.size == (W, H)
        assert im.info.get('icc_profile') == ICC
        assert np.array_equal(np.asarray(im), array)
    ihdr = path.read_bytes()[24:29]
    assert ihdr[0] == 8 and ihdr[1] == 2, ihdr
    return {'id': identifier, 'path': str(path.resolve()), 'filename': path.name,
            'selected': selected, 'split': 'calibration' if selected else 'compatibility_unselected',
            'purpose': purpose, 'size_px': [W, H], 'mode': 'RGB', 'bit_depth': 8,
            'color_profile': 'embedded sRGB ICC', 'icc_sha256': sha(ICC),
            'sha256': sha(path.read_bytes()), 'decoded_rgb_sha256': sha(array.tobytes()),
            'bytes': path.stat().st_size}


def coordinate_probe():
    """Large irregular cells with two non-collinear within-cell RGB slopes."""
    rng = random.Random(SEED)
    xcuts = [0, 72, 154, 244, 350, 438, 532, 630, 750]
    ycuts = [0, 96, 202, 306, 418, 530, 642, 750, 850, 958, 1070, 1182, 1292, 1334]
    image = np.empty((H, W, 3), dtype=np.uint8)
    cells, bases = [], {}
    sx_options = [(26, -14, 10), (-24, 16, 12), (18, 24, -14), (12, -24, 24)]
    sy_options = [(10, 26, -18), (22, 10, -26), (-20, 24, 8), (-16, 12, 26)]
    used_colors = set()
    for row in range(len(ycuts) - 1):
        for col in range(len(xcuts) - 1):
            # Adjacent centers differ by at least100 encoded-RGB units.
            neighbors = [bases[k] for k in ((row-1, col), (row, col-1)) if k in bases]
            for attempt in range(10000):
                base = tuple(rng.randrange(48, 209) for _ in range(3))
                if base not in used_colors and all(sum((a-b)**2 for a, b in zip(base, n)) >= 100**2 for n in neighbors):
                    break
            else:
                raise RuntimeError('Cannot construct distinct cell colors')
            sx = np.array(rng.choice(sx_options), dtype=float)
            sy = np.array(rng.choice(sy_options), dtype=float)
            assert np.linalg.norm(np.cross(sx, sy)) > 100
            l, t, r, b = xcuts[col], ycuts[row], xcuts[col+1], ycuts[row+1]
            xx = ((np.arange(l, r) + .5 - l) / (r-l) - .5)[None, :, None]
            yy = ((np.arange(t, b) + .5 - t) / (b-t) - .5)[:, None, None]
            patch = np.rint(np.asarray(base)[None, None, :] + xx*sx + yy*sy).clip(0,255).astype(np.uint8)
            image[t:b, l:r] = patch
            bases[(row, col)] = base
            used_colors.add(base)
            cells.append({'id': f'C{row:02d}_{col:02d}', 'row': row, 'column': col,
                          'bbox_ltrb_px_half_open': [l,t,r,b], 'center_rgb': list(base),
                          'full_width_rgb_slope': sx.astype(int).tolist(),
                          'full_height_rgb_slope': sy.astype(int).tolist(),
                          'raster_rgb_sha256': sha(patch.tobytes())})
    return image, {'id': 'panel_probe_coordinate', 'seed': SEED, 'x_cuts_px': xcuts,
                   'y_cuts_px': ycuts, 'cells': cells,
                   'pixel_formula': 'round(center_rgb + ((x+.5-left)/width-.5)*x_slope + ((y+.5-top)/height-.5)*y_slope), clipped0..255; x/y integer pixel indices.',
                   'minimum_full_cell_width_px': 72, 'minimum_full_cell_height_px': 96,
                   'last_canvas_clipped_row_height_px': 42,
                   'meaning': 'Two-dimensional nonperiodic coarse RGB code. Each tile/color/ramp is a known input; local output correspondence remains conditional on visibility/uniqueness gates. No fine dot coding.'}


def polygon(center, width, height, points):
    x, y = center
    return [(x + width*a/2, y + height*b/2) for a, b in points]


def regular(center, width, height, count, rotation=-math.pi/2):
    return [(center[0]+width/2*math.cos(rotation+i*2*math.pi/count),
             center[1]+height/2*math.sin(rotation+i*2*math.pi/count)) for i in range(count)]


def shape_mask(kind, center, width, height):
    mask = Image.new('L', (W,H), 0)
    draw = ImageDraw.Draw(mask)
    x,y = center
    box = [x-width/2, y-height/2, x+width/2, y+height/2]
    vertices = None
    if kind in ('circle', 'ellipse_horizontal'):
        draw.ellipse(box, fill=255)
    elif kind == 'capsule_vertical':
        draw.rounded_rectangle(box, radius=width/2, fill=255)
    elif kind == 'crescent':
        draw.ellipse(box, fill=255)
        draw.ellipse([x-width*.10,y-height*.43,x+width*.67,y+height*.43],fill=0)
    else:
        shapes = {
            'triangle_up': [(0,-1),(1,1),(-1,1)],
            'diamond': [(0,-1),(1,0),(0,1),(-1,0)],
            'bowtie': [(-1,-1),(1,1),(1,-1),(-1,1)],
            'rotated_rectangle': [(-.35,-1),(1,-.50),(.35,1),(-1,.50)],
            'cross': [(-.35,-1),(.35,-1),(.35,-.35),(1,-.35),(1,.35),(.35,.35),(.35,1),(-.35,1),(-.35,.35),(-1,.35),(-1,-.35),(-.35,-.35)],
            'triangle_down': [(-1,-1),(1,-1),(0,1)],
            'L_shape': [(-1,-1),(-.2,-1),(-.2,.25),(1,.25),(1,1),(-1,1)],
            'arrow_up': [(0,-1),(1,-.15),(.36,-.15),(.36,1),(-.36,1),(-.36,-.15),(-1,-.15)],
            'trapezoid': [(-.5,-1),(.5,-1),(1,1),(-1,1)],
            'parallelogram': [(-.45,-1),(1,-1),(.45,1),(-1,1)],
        }
        if kind == 'pentagon':
            vertices = regular(center,width,height,5)
        elif kind == 'hexagon':
            vertices = regular(center,width,height,6,rotation=0)
        else:
            vertices = polygon(center,width,height,shapes[kind])
        draw.polygon(vertices, fill=255)
    return np.asarray(mask) > 0, box, vertices


def shapes_probe():
    rng = random.Random(SEED ^ 0x53484150)
    image = np.full((H,W,3), NEUTRAL, dtype=np.uint8)
    # Positions are stimulus-design coordinates, independent of any output image.
    spec = [
        ('circle',55,512,84,84,(222,40,62),'Alert TL corner'),
        ('triangle_up',166,510,104,104,(30,95,225),'Alert top-left straight'),
        ('pentagon',584,510,112,108,(25,173,92),'Alert top-right straight'),
        ('diamond',700,513,88,100,(235,119,24),'Alert TR corner'),
        ('bowtie',56,642,104,102,(156,48,211),'Alert left / Sheet TL'),
        ('rotated_rectangle',699,644,92,110,(20,169,210),'Alert right / Sheet TR'),
        ('cross',174,652,108,108,(215,43,154),'Sheet top-left straight'),
        ('ellipse_horizontal',584,652,120,80,(118,63,30),'Sheet top-right straight'),
        ('hexagon',168,857,108,104,(10,136,140),'Alert bottom-left'),
        ('triangle_down',585,857,112,108,(168,153,15),'Alert bottom-right'),
        ('L_shape',54,1034,92,112,(60,47,171),'Sheet left mid'),
        ('capsule_vertical',700,1038,84,124,(175,49,34),'Sheet right mid'),
        ('arrow_up',55,1231,100,116,(64,137,20),'Sheet left lower'),
        ('crescent',699,1230,90,110,(218,72,17),'Sheet right lower'),
        ('trapezoid',169,1283,112,94,(111,35,137),'Sheet bottom-left'),
        ('parallelogram',584,1283,120,96,(30,105,154),'Sheet bottom-right'),
    ]
    occupied = np.zeros((H,W), dtype=bool)
    shapes = []
    for index,(kind,x,y,width,height,color,purpose) in enumerate(spec,1):
        center = [x+rng.randrange(-2,3), y+rng.randrange(-2,3)]
        mask, bbox, vertices = shape_mask(kind,center,width,height)
        assert bbox[0]>=0 and bbox[1]>=0 and bbox[2]<=W and bbox[3]<=H, (kind,'source clipped')
        assert not np.any(mask & occupied), (kind,'input overlap')
        occupied |= mask
        image[mask] = color
        yy,xx = np.nonzero(mask)
        shapes.append({'id': f'S{index:02d}', 'shape': kind, 'center_px': center,
                       'width_px': width, 'height_px': height, 'color_rgb': list(color),
                       'design_bbox_ltrb_px': bbox, 'vertices_px': vertices,
                       'visible_raster_bbox_ltrb_px_half_open': [int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)],
                       'visible_area_px': int(mask.sum()), 'visible_pixel_center_centroid_px': [float(xx.mean()+.5),float(yy.mean()+.5)],
                       'mask_sha256': sha(mask.astype(np.uint8).tobytes()),
                       'purpose': purpose,
                       'tracking_warning': 'Output may be clipped by pane/foreground, blurred or blended with nearby color. No automatic correspondence unless fixed gates pass.'})
    controls = []
    for index,(box,color) in enumerate([([86,352,208,438],(210,54,70)),([292,352,414,438],(36,152,90)),([498,352,620,438],(37,94,211))],1):
        l,t,r,b=box
        assert not occupied[t:b,l:r].any()
        image[t:b,l:r] = color
        controls.append({'id':f'K{index:02d}','bbox_ltrb_px_half_open':box,'color_rgb':list(color),'purpose':'Exterior encoded-RGB scrim control; not a glass feature.'})
    return image, {'id':'panel_probe_shapes','seed':SEED ^ 0x53484150,
                   'background_rgb':list(NEUTRAL),'shapes':shapes,'exterior_controls':controls,
                   'rasterization':'Pillow ImageDraw filled shapes at original750x1334 pixels, no supersampling/resizing; polygon vertices/ellipse bbox and visible raster mask hashes provided.',
                   'minimum_nominal_shape_dimension_px':80,
                   'warning':'No microdots, outline-only features, text glyphs or periodic shape lattice. Nearby markers still require empirical blur/separability gates.'}


def main():
    INPUTS.mkdir(parents=True,exist_ok=True)
    coordinate, coordinate_map = coordinate_probe()
    shapes, shapes_map = shapes_probe()
    files = [save_image('panel_probe_coordinate',coordinate,True,'Two-dimensional nonperiodic coordinate-coded color cells/ramps'),
             save_image('panel_probe_shapes',shapes,True,'Sparse unique filled multicolor shapes at declared pane locations')]
    gray = np.full((H,W,3),NEUTRAL,dtype=np.uint8)
    for index in range(1,7):
        files.append(save_image(f'compatibility_unselected_{index:02d}',gray,False,'Fresh uniform gray compatibility slot; excluded from capture, analysis and scoring'))
    oracle = {'schema':1,'split':'calibration','seed':SEED,'world_px':[W,H],'pixels_per_pt_or_dp':2,
              'coordinate_convention':'Continuous source pixel bounds from0; pixel centers(i+.5,j+.5); world logical coordinate=pixel/2.',
              'no_prior_inputs_read':True,'probes':[coordinate_map,shapes_map]}
    oracle_path = OUT/'oracle.json'
    oracle_path.write_text(json.dumps(oracle,indent=2)+'\n')
    manifest = {'schema':1,'id':'panel-nonperiodic-calibration-v1','split':'calibration',
                'seed':SEED,'world_px':[W,H],'selected_ids':['panel_probe_coordinate','panel_probe_shapes'],
                'unselected_policy':'Six fresh gray slots are compatibility_unselected. They must never be captured, decoded as experimental observations, tuned on, or scored.',
                'asset_count':8,'selected_count':2,'compatibility_unselected_count':6,
                'generator':{'path':str(Path(__file__).resolve()),'sha256':sha(Path(__file__).read_bytes()),
                             'python':platform.python_version(),'pillow':PIL.__version__,'numpy':np.__version__,'prng':'Python random.Random / MT19937'},
                'oracle':{'path':str(oracle_path.resolve()),'sha256':sha(oracle_path.read_bytes())},
                'srgb_icc':{'path':str(ICC_PATH.resolve()),'sha256':sha(ICC),'policy':'Persist one generated ICC profile so metadata creation time cannot change output bytes on regeneration.'},
                'files':files,'constraints':['New deterministic calibration sources only; no old noise, hidden or holdout input was read.',
                    'The input images are original sources, not simulations of native/Android glass.',
                    'No runtime source, device, build or capture is changed by this generator.',
                    'This first light pair is an identifiability feasibility check, not parity/generalization acceptance.']}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'manifest':str(OUT/'manifest.json'),'manifest_sha256':sha((OUT/'manifest.json').read_bytes()),
                      'selected':[{'id':f['id'],'sha256':f['sha256']} for f in files if f['selected']],
                      'total_png_bytes':sum(f['bytes'] for f in files)}))


if __name__ == '__main__':
    main()
