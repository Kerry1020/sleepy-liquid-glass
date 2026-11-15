"""Generate rejected-for-current-fixture proposal inputs and exact raster oracles.

Only writes below analysis-mapping-audit/probe-preparation. Existing images read
are the two current nonperiodic calibration inputs and their native BEFORE
Alert context, never heldout or native/candidate optical output images.
"""
from pathlib import Path
import csv
import hashlib
import io
import json
import math
import re
import shutil
import struct

import numpy as np
from PIL import Image, ImageCms

O = Path(__file__).resolve().parent / 'probe-preparation'
P = O.parent.parent
A = Path('/Users/kerrylee/.codex/worktrees/android-settings-glass-fixes/sleepy')
N = P / 'native-panel-feasibility-preparation'
S = P / 'panel-probes-preparation'
O.mkdir(exist_ok=True)
(O / 'inputs').mkdir(exist_ok=True)
SHA = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def save(name, data):
    (O / name).write_text(json.dumps(data, indent=2, ensure_ascii=False,
                                   allow_nan=False) + '\n')


manifest_path = N / 'attachments/manifest.json'
attachments = json.loads(manifest_path.read_text())[0]['attachments']
sid_list = ['panel_probe_coordinate', 'panel_probe_shapes']
contexts = {}
for sid in sid_list:
    items = [r for r in attachments if f'{sid}-light-before-alert-context_' in
             r['suggestedHumanReadableName'] and r['exportedFileName'].endswith('.png')]
    ax = [r for r in attachments if f'{sid}-light-before-alert-context-accessibility_' in
          r['suggestedHumanReadableName'] and r['exportedFileName'].endswith('.txt')]
    assert len(items) == len(ax) == 1
    contexts[sid] = {'png': N / 'attachments' / items[0]['exportedFileName'],
                     'ax': N / 'attachments' / ax[0]['exportedFileName'],
                     'source': S / 'inputs' / f'{sid}.png',
                     'attachment': items[0]}
read_paths = [Path(__file__), manifest_path, S / 'srgb.icc', S / 'analysis-plan.json',
              P / 'analysis-native-probes/geometry-and-mask.json',
              P / 'radial-vs-nearest/summary.json',
              A / 'tools/native-glass-reference/App/NativeStage.swift',
              A / 'tools/native-glass-reference/App/main.swift']
for context in contexts.values():
    read_paths += [context[k] for k in ['png', 'ax', 'source']]

# Frozen before decoding the two explicitly named calibration context images.
provenance = {'status': 'proposal-input preparation only; no new captures',
              'read_scope': 'two existing current nonperiodic calibration source/before-context pairs; no heldout images or optical output decoded',
              'files_sha256': {str(p): SHA(p) for p in read_paths},
              'frozen_source_diagnostic_corridor_ltrb_pt': [148.5, 257.5, 226.5, 317.5],
              'corridor_reason': 'c +/- (24 + .25*60), b..b+60; illustrative A60 flat-model footprint, not a proven bound on native sampling',
              'fixed_world': {'size_px': [750, 1334], 'size_pt': [375, 667], 'px_per_pt': 2},
              'no_registration_no_warp_no_gate_changes': True}
save('input-provenance-before-decode.json', provenance)

icc = (S / 'srgb.icc').read_bytes()
assert hashlib.sha256(icc).hexdigest() == 'fdc96271cfac30d9fff540752580b2938ff09118c7347dcc4328d52d00342623'
shutil.copyfile(S / 'srgb.icc', O / 'srgb.icc')
height, width = 1334, 750
yy, xx = np.mgrid[0:height, 0:width]
xpt, ypt = (xx + .5) / 2., (yy + .5) / 2.
c, b, m, u0, u1 = 187.5, 257.5, .25, -64., 128.
u = ypt - b
rows = []
oracle_sources = []
for a in [20., 24.]:
    left = c - a - m * u
    right = c + a + m * u
    # Half-open raster membership is explicit; no polygon drawing/AA rounding.
    mask = (u >= u0) & (u < u1) & (xpt >= left) & (xpt < right)
    indices = np.argwhere(mask)
    row_spans = []
    for py in np.flatnonzero(mask.any(axis=1)):
        xs = np.flatnonzero(mask[py])
        row_spans.append({'row_index_px': int(py), 'y_center_pt': (int(py)+.5)/2.,
                          'left_filled_index_px': int(xs[0]),
                          'right_filled_index_exclusive_px': int(xs[-1]+1),
                          'continuous_left_pt': c-a-m*((int(py)+.5)/2.-b),
                          'continuous_right_pt': c+a+m*((int(py)+.5)/2.-b)})
    mask_hash = hashlib.sha256(mask.astype(np.uint8).tobytes()).hexdigest()
    for reversed_contrast in [False, True]:
        contrast = 'reversed' if reversed_contrast else 'normal'
        sid = f'paired_slope_alert_a{int(a)}_{contrast}'
        fill, background = (190, 60) if reversed_contrast else (60, 190)
        rgb = np.full((height, width, 3), background, dtype=np.uint8)
        rgb[mask] = fill
        output = O / 'inputs' / f'{sid}.png'
        Image.fromarray(rgb).save(output, icc_profile=icc, optimize=True)
        data = output.read_bytes()
        assert data[:8] == b'\x89PNG\r\n\x1a\n'
        assert struct.unpack('>IIBBBBB', data[16:29]) == (750, 1334, 8, 2, 0, 0, 0)
        image = Image.open(output)
        assert image.mode == 'RGB' and image.size == (750, 1334)
        assert image.info['icc_profile'] == icc
        assert np.array_equal(np.asarray(image), rgb)
        entry = {'id': sid, 'file': f'inputs/{sid}.png', 'a_pt': a,
                 'contrast': contrast, 'fill_rgb': [fill]*3, 'background_rgb': [background]*3,
                 'size_px': [width, height], 'world_size_pt': [375, 667],
                 'png_sha256': SHA(output), 'decoded_rgb_sha256': hashlib.sha256(rgb.tobytes()).hexdigest(),
                 'binary_mask_sha256': mask_hash, 'icc_sha256': hashlib.sha256(icc).hexdigest(),
                 'encoding': 'opaque RGB8 PNG with persisted sRGB ICC',
                 'split': 'unmeasured proposal; not calibration/test acceptance evidence',
                 'current_fixture_capture_eligible': False}
        rows.append(entry)
    oracle_sources.append({'a_pt': a, 'binary_mask_sha256': mask_hash,
                           'vertices_world_pt': [[c-a-m*u0, b+u0], [c+a+m*u0, b+u0],
                                                 [c+a+m*u1, b+u1], [c-a-m*u1, b+u1]],
                           'filled_pixel_count': int(mask.sum()),
                           'raster_centroid_world_pt': [float((indices[:,1]+.5).mean()/2.),
                                                        float((indices[:,0]+.5).mean()/2.)],
                           'continuous_centroid_world_pt': [c, b + (a*(u1*u1-u0*u0)/2.+m*(u1**3-u0**3)/3.)/(a*(u1-u0)+m*(u1*u1-u0*u0)/2.)],
                           'row_spans': row_spans})
save('oracle.json', {'status': 'exact input geometry; not a measured optical correspondence',
                     'coordinate_convention': 'world pt at fixed origin0,0; pixel center=(index+.5)/2',
                     'world_anchor_c_b_pt': [c,b], 'm': m, 'u_extent_half_open_pt': [u0,u1],
                     'membership': 'u>=-64 AND u<128 AND x>=c-a-m*u AND x<c+a+m*u',
                     'side_equations': {'left': 'x=c-a-.25*(y-b)', 'right': 'x=c+a+.25*(y-b)'},
                     'antialiasing': 'none; analytic pixel-center membership',
                     'sources': oracle_sources})

box_pattern = re.compile(r'\{\{([-\d.]+), ([-\d.]+)\}, \{([-\d.]+), ([-\d.]+)\}\}')
backing = []
for sid, context in contexts.items():
    boxes = []
    for line in context['ax'].read_text().splitlines():
        if any(f"identifier: '{name}'" in line for name in
               ['reference-title','background-selector','scene-selector','show-sheet','show-alert','show-menu','uikit-tabbar']):
            match = box_pattern.search(line)
            if match:
                x,y,w,h = map(float, match.groups())
                boxes.append({'identifier': re.search("identifier: '([^']+)'",line).group(1),
                              'ltrb_pt': [x,y,x+w,y+h]})
    def decode(path):
        im = Image.open(path)
        raw = np.asarray(im.convert('RGB'))
        profile = im.info.get('icc_profile')
        normalized = np.asarray(ImageCms.profileToProfile(im.convert('RGB'),
                      ImageCms.ImageCmsProfile(io.BytesIO(profile)), ImageCms.createProfile('sRGB'),
                      outputMode='RGB')) if profile else raw.copy()
        return raw, normalized, {'path': str(path), 'sha256': SHA(path),
                                'raw_normalized_identical': bool(np.array_equal(raw,normalized)),
                                'max_raw_normalized_channel_delta': int(np.abs(raw.astype(int)-normalized.astype(int)).max()),
                                'size_px': list(im.size), 'mode': im.mode}
    raw, normalized, before_decode = decode(context['png'])
    source_raw, source_normalized, source_decode = decode(context['source'])
    assert raw.shape == source_raw.shape == (1334,750,3)
    diagnostic_mask = (xpt>=148.5)&(xpt<226.5)&(ypt>=257.5)&(ypt<317.5)
    sheet_mask = (xpt>=126.5)&(xpt<249.)&(ypt>=286.)&(ypt<319.5)
    regions = {}
    for name, selection in [('fixed_proposed_corridor',diagnostic_mask),
                            ('corridor_intersection_show_sheet_AX',diagnostic_mask&sheet_mask)]:
        difference = np.abs(normalized.astype(int)-source_normalized.astype(int))[selection]
        regions[name] = {'pixels': int(selection.sum()), 'pixels_any_exact_RGB_difference': int((difference>0).any(axis=1).sum()),
                         'max_channel_difference': int(difference.max()),
                         'mean_absolute_channel_difference': float(difference.mean()),
                         'q95_absolute_channel_difference': float(np.quantile(difference,.95)),
                         'meaning': 'descriptive existing context/source difference, no optical threshold or clean-source acceptance'}
    backing.append({'input': sid, 'before_alert_attachment': context['attachment'],
                    'before_decode': before_decode, 'source_decode': source_decode,
                    'before_alert_AX_controls': boxes, 'fixed_diagnostic_regions': regions})
save('before-alert-backing-audit.json', {'status': 'current fixture invalidates proposed central clean-source assumption',
      'scope': 'existing nonperiodic source/before-context pairs only; proposal images not presented',
      'source_footprint_not_native_bound': True, 'observations': backing})

summary = json.loads((P/'radial-vs-nearest/summary.json').read_text())
curve = summary['shape']['top_left_cubics'][0]
def bezier(t, axis):
    s = 1.-t
    return curve[0][axis]*s**3+3*curve[1][axis]*s*s*t+3*curve[2][axis]*s*t*t+curve[3][axis]*t**3
def sample_contour(world_x):
    local_x = 160.-abs(world_x-187.5)
    low,high = 0.,1.
    for _ in range(80):
        middle=(low+high)/2.
        if bezier(middle,0)>local_x:low=middle
        else:high=middle
    t=(low+high)/2.;s=1.-t
    dx=3*(curve[1][0]-curve[0][0])*s*s+6*(curve[2][0]-curve[1][0])*s*t+3*(curve[3][0]-curve[2][0])*t*t
    dy=3*(curve[1][1]-curve[0][1])*s*s+6*(curve[2][1]-curve[1][1])*s*t+3*(curve[3][1]-curve[2][1])*t*t
    return {'world_x':world_x,'contour_offset_from_AX_top_pt':bezier(t,1),
            'absolute_tangent_slope':abs(dy/dx)}
contour_samples=[sample_contour(148.5+.5*i) for i in range(157)]
geometry = {'status': 'not capture eligible; actual native central straightness unresolved',
    'native_alert_AX_ltrb_pt':[27.5,257.5,347.5,429.5],
    'AX_is_not_optical_contour':True,
    'inherited_primary_top_ROIs_pt':[[62,104],[271,313]],
    'proposed_central_ROI_is_new_not_inherited':True,
    'proposed_output_row_centers_pt':{'first':257.75,'last':277.25,'step':.5},
    'title_union_mask_ltrb_pt':[55.5,277.5,319.5,302.5],
    'title_direct_output_clearance_last_row_pt':.25,
    'no_sampling_beyond_last_clear_row':True,
    'native_actual_central_tangent_invariance_confirmed':False,
    'android_CPU_contour_scope':'Double replay from existing cubic summary, not GPU bit-equivalence/native raster proof',
    'android_CPU_contour_offset_pt_range':[min(r['contour_offset_from_AX_top_pt'] for r in contour_samples),max(r['contour_offset_from_AX_top_pt'] for r in contour_samples)],
    'android_CPU_max_abs_tangent_slope':max(r['absolute_tangent_slope'] for r in contour_samples),
    'android_CPU_contour_samples':contour_samples,
    'backing_source_failure':'Proposed possible source coordinates y286..317.5 and x148.5..226.5 overlap native show-sheet AX x126.5..249,y286..319.5. Native optical footprint and blur support are not bounded.',
    'decision':'Generate inspectable input proposals only; no loader/capture matrix approved; no inversion, fitting, parity or physical-thickness claim.'}
save('geometry-eligibility.json', geometry)

original_plan = json.loads((S/'analysis-plan.json').read_text())
plan = {'status':'UNMEASURED PROPOSAL — NOT ELIGIBLE FOR CURRENT NATIVE FIXTURE',
    'scope':'Four Alert-centered paired-slope wedge inputs only; no Sheet source included',
    'parameters_frozen':{'anchor_c_b_pt':[c,b],'half_widths_a_pt':[20,24],'m':m,'u_extent_pt':[u0,u1],
                         'gray_pair':[60,190],'output_inward_centers_pt':[.25,19.75,.5]},
    'source_files_generated':True,'capture_authorized_or_performed':False,
    'capture_matrix':None,'loader_manifest':None,
    'why_blocked':['Center source-footprint overlaps native backing show-sheet glass button',
                   'Actual native central optical contour/tangent invariance not established',
                   'Before-context PNG for these four proposals has not been captured; existing contexts only demonstrate fixture interference'],
    'preconditions_for_a_separate_future_plan':['Establish an interpretable unobstructed backing/source footprint without silently changing this proposal',
                                             'Freeze any fixture/ROI revision before new outputs',
                                             'Confirm actual contour and both source sides under the same original gates'],
    'required_local_model':'S_t=x+U(d), S_n=g(d); g independent of tangent across both sides and both widths',
    'conditional_observables':{'g':'(R-L-2*a)/(2*m)','D':'g-d','U':'c-(R+L)/2','g_prime':'W_prime/(2*m)','g_second':'W_second/(2*m)'},
    'operator':'Centered secants h4pt only with both eligible endpoints; retain multiplicity/sign; no edge extrapolation',
    'quantization_floor':{'edge_pt':.25,'g_pt':1.,'g_prime_h4':.25,'g_second_h4_per_pt':.25},
    'visibility_gates_UNCHANGED':original_plan['visibility_gates'],
    'required_falsification':'two widths and reversed contrast must agree within declared uncertainty before scalar inversion',
    'on_failure':'Report unresolved; never move ROI, lower gates, fill missing edges or fit refraction/power'}
save('proposal-plan.json',plan)
manifest={'schema':1,'status':plan['status'],'set_id':'paired_slope_alert_proposal_20261115',
          'capture_eligible':False,'not_a_loader_manifest':True,
          'inputs':rows,'oracle_sha256':SHA(O/'oracle.json'),
          'proposal_plan_sha256':SHA(O/'proposal-plan.json'),
          'geometry_eligibility_sha256':SHA(O/'geometry-eligibility.json'),
          'before_alert_backing_audit_sha256':SHA(O/'before-alert-backing-audit.json'),
          'generator_sha256':SHA(Path(__file__))}
save('proposal-manifest.json',manifest)
(O/'README.md').write_text('''# Paired-slope Alert inputs — unmeasured, ineligible proposal

The four PNGs are exact deterministic input assets, **not measured optical data**.
They are intentionally not registered in a loader or capture matrix. The proposed
center source footprint overlaps the native `show-sheet` glass button, and the
native central optical contour/tangent invariance has not been established.
The proposal must not be used to claim a recovered normal/tangential map.

The anchor is fixed at `(187.5,257.5)pt`, with `a20/a24`, slope `.25`, support
`u=-64..<128pt`, and gray60/190 normal/reversed contrast. Raster membership is
analytic at pixel centers; exact row spans, centroids, masks, RGB/PNG hashes, and
the reused persisted sRGB profile are recorded in `oracle.json` and
`proposal-manifest.json`. Output rows remain `d=.25..19.75pt`; the last one is
only .25pt above the existing expanded title mask. No original ROI or gate was
moved to make the new center appear eligible.

`before-alert-backing-audit.json` compares only the two existing nonperiodic
calibration sources with their native before-Alert contexts in a fixed corridor.
These differences expose fixture content; they do not certify that hypothetical
new source pixels would remain untouched. `geometry-eligibility.json` distinguishes
native AX, native optical uncertainty, and a CPU-only Android cubic calculation.

No native/Android source, build, device, Git operation, optical-output image, or
heldout image was changed or used by this preparation script.
''')
for path in O.glob('*.json'):
    json.loads(path.read_text())
print(json.dumps({'output':str(O),'capture_eligible':False,'files':rows,
                  'CPU_android_contour_range_pt':geometry['android_CPU_contour_offset_pt_range'],
                  'existing_backing_differences':[{'input':v['input'],'regions':v['fixed_diagnostic_regions']} for v in backing]},indent=2))
