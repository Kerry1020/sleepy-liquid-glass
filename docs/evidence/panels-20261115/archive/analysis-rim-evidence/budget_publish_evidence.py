"""Copy bounded evidence, losslessly compress numeric archives, export fixed synthetic-pane crops."""
from pathlib import Path
import csv
import gzip
import hashlib
import io
import json
import shutil
from PIL import Image, PngImagePlugin

O = Path(__file__).resolve().parent
P = O.parent
L = Path('/Users/kerrylee/Documents/Codex/sleepy-liquid-glass')
E = L / 'docs/evidence/panels-20261115'
I = L / 'docs/images/panels-20261115'
E.mkdir(parents=True, exist_ok=True)
I.mkdir(parents=True, exist_ok=True)
sha = lambda data: hashlib.sha256(data).hexdigest()
records = []


def publish(path, relative, compress=True):
    data = path.read_bytes()
    packed = compress and path.suffix in ('.json', '.csv') and len(data) > 262144
    dest = E / 'archive' / relative
    if packed:
        dest = dest.with_name(dest.name + '.gz')
    dest.parent.mkdir(parents=True, exist_ok=True)
    output = gzip.compress(data, compresslevel=9, mtime=0) if packed else data
    dest.write_bytes(output)
    if packed:
        assert gzip.decompress(output) == data
    records.append({'source_namespace': 'panel-study/' + str(relative),
                    'published': str(dest.relative_to(L)), 'source_sha256': sha(data),
                    'source_bytes': len(data), 'published_sha256': sha(output),
                    'published_bytes': len(output),
                    'processing': 'deterministic lossless gzip; decompress restores exact source bytes'
                                  if packed else 'byte-exact copy'})


analysis_dirs = ['analysis-alert-baseline', 'analysis-alert-frost8', 'analysis-alert-profile-half',
                 'analysis-dark-scrim', 'analysis-mapping-audit', 'analysis-native-probes',
                 'analysis-rim-evidence', 'radial-vs-nearest', 'panel-probes-preparation']
extensions = {'.py', '.md', '.json', '.csv', '.svg', '.txt'}
for name in analysis_dirs:
    for path in sorted((P / name).rglob('*')):
        if (path.is_file() and path.suffix in extensions and '__pycache__' not in path.parts
                and not path.name.endswith('-run.log')):
            publish(path, path.relative_to(P))

for path in sorted(P.iterdir()):
    if path.is_file() and (path.suffix in {'.json', '.md', '.py'}):
        publish(path, path.relative_to(P))
    elif path.is_dir() and path.name.startswith('panels-'):
        for item in sorted(path.glob('*.json')):
            publish(item, item.relative_to(P))

figure_sources = {
    'budget-five-way-fixed-comparison.png': O / 'budget-five-way-fixed-comparison.png',
    'screen-four-way-fixed-comparison.png': O / 'rim-screen-four-way-fixed-comparison.png',
    'additive-primary124-clipping.png': O / 'rim-bounded-left-red-124-pixels.png',
    'native-S02-local-contours.png': P / 'analysis-native-probes/S02-local-contours.png',
    'native-coordinate-local-contours.png': P / 'analysis-native-probes/coordinate-local-contours.png',
    'body8-S02-local-contours.png': P / 'analysis-native-probes/alert-body8/S02-local-contours.png',
    'sheet10-S07-local-contours.png': P / 'analysis-native-probes/sheet-radius10/Sheet-S07-local-contours.png',
    'profile-half-blue-feature-bend.png': P / 'analysis-alert-profile-half/blue-feature-bend-comparison.png',
    'rimBlur8-blue-feature-bend.png': P / 'analysis-alert-frost8/blue-feature-bend-comparison.png',
    'mapping-theory.svg': P / 'analysis-mapping-audit/scalar-mapping-model.svg',
}
figures = []
for name, source in figure_sources.items():
    assert source.is_file(), source
    target = I / name
    shutil.copyfile(source, target)
    data = target.read_bytes()
    figures.append({'published': str(target.relative_to(L)), 'source': 'panel-study/' + str(source.relative_to(P)),
                    'source_sha256': sha(source.read_bytes()), 'published_sha256': sha(data),
                    'bytes': len(data), 'processing': 'byte-exact existing figure; original captions/limits retained'})

crop_records = []
pane = {'alert': [55, 515, 695, 859], 'sheet': [16, 635, 734, 1318]}


def crop(source, name, carrier, expected=None):
    raw = source.read_bytes()
    if expected:
        assert sha(raw) == expected, source
    with Image.open(io.BytesIO(raw)) as image:
        assert image.size == (750, 1334), (source, image.size)
        box = pane[carrier]
        cropped = image.crop(box)
        metadata = PngImagePlugin.PngInfo()
        if 'srgb' in image.info:
            metadata.add(b'sRGB', bytes([image.info['srgb']]))
        target = I / 'original-crops' / (name + '.png')
        target.parent.mkdir(parents=True, exist_ok=True)
        cropped.save(target, pnginfo=metadata, icc_profile=image.info.get('icc_profile'))
        # Pixel identity check; the published crop is not rescaled or recolored.
        with Image.open(target) as restored:
            assert restored.mode == cropped.mode and restored.tobytes() == cropped.tobytes()
    crop_records.append({'name': name, 'carrier': carrier,
                         'published': str(target.relative_to(L)),
                         'source': 'panel-study/' + str(source.relative_to(P)) if source.is_relative_to(P)
                                   else 'historical-native/' + source.name,
                         'source_sha256': sha(raw), 'published_sha256': sha(target.read_bytes()),
                         'source_size_px': [750, 1334], 'crop_rect_px_half_open': box,
                         'processing': 'exact original composited-display pixels; no resize/warp/registration/recolor; '
                                       'original source hash retained; known Sheet bottom context remains'})
    return str(target.relative_to(I))


nonperiodic = {}
for label, directory in [('body8', 'panels-alert-body8-20261115'),
                         ('additive', 'panels-alert-rim-bounded-20261115'),
                         ('screen', 'panels-alert-floor-screen-20261115'),
                         ('budget', 'panels-alert-floor-budget-20261115'),
                         ('sheet12', 'panels-sheet-radius12-control-20261115'),
                         ('sheet10', 'panels-sheet-radius10-20261115')]:
    matrix = json.loads((P / directory / 'matrix.json').read_text())
    for cap in matrix['captures']:
        carrier = 'sheet' if cap['carrier'] == 'share_sheet' else cap['carrier']
        if label in ['body8', 'additive', 'screen'] and carrier != 'alert':
            continue
        if label in ['sheet12', 'sheet10'] and carrier != 'sheet':
            continue
        sid = cap['background']
        key = label + '-' + sid + '-' + carrier
        nonperiodic[key] = crop(P / directory / cap['screen_png'], key, carrier)

receipts = json.loads((P / 'analysis-native-probes/capture-receipts.json').read_text())
for row in receipts:
    if row['phase'] in ['alert-rest', 'sheet-rest']:
        carrier = 'alert' if row['phase'] == 'alert-rest' else 'sheet'
        key = 'native-' + row['input'] + '-' + carrier
        source = P / 'native-panel-feasibility-preparation/attachments' / row['file']
        nonperiodic[key] = crop(source, key, carrier)

history = {}
candidate_analysis = json.loads((O / 'budget-history/analysis.json').read_text())
for scene in candidate_analysis['scenes']:
    sid = scene['scene']
    for label, item in [('native', scene['files']['native']), ('budget', scene['files']['android'])]:
        key = label + '-' + sid + '-alert'
        history[key] = crop(Path(item['path']), key, 'alert', item['sha256'])
    for label, directory in [('additive', 'panels-alert-rim-bounded-history-20261115'),
                             ('screen', 'panels-alert-floor-screen-history-r2-20261115')]:
        matrix = json.loads((P / directory / 'matrix.json').read_text())
        cap = next(c for c in matrix['captures']
                   if c['scene'] == sid + '-alert' and c['carrier'] == 'alert')
        key = label + '-' + sid + '-alert'
        history[key] = crop(P / directory / cap['screen_png'], key, 'alert')

# One concise portable source index; no APKs, videos, build products or caches.
publication = {'schema': 1, 'scope': '2026-11-15 Alert/Sheet static calibration evidence',
               'records': records, 'figures': figures, 'original_crop_records': crop_records,
               'nonperiodic_crop_index': nonperiodic, 'history_crop_index': history,
               'failed_history_images_decoded_or_published': False,
               'exclusions': ['APKs/build products/caches', 'device videos',
                              'unpublished noise and heldout inputs', 'full status-bar screenshots',
                              'failed/incomplete history optical image batches'],
               'notes': ['Archived reports/scripts retain their original historical paths and roles.',
                         'Large numeric files use .gz and decompress to exact original bytes.',
                         'Some original report-relative links reference the prepublication tree; '
                         'the main study and REDRAWING.md provide portable entry points.',
                         'The archive contains recorded research artifacts, not an instruction to run device tools.']}
(E / 'sources.json').write_text(json.dumps(publication, indent=2) + '\n')
print(json.dumps({'archives': len(records), 'figures': len(figures), 'original_crops': len(crop_records),
                  'archive_source_bytes': sum(r['source_bytes'] for r in records),
                  'archive_published_bytes': sum(r['published_bytes'] for r in records)}, indent=2))
