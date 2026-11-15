#!/usr/bin/env python3
"""Publish an explicit allowlist of already-observed optical studies.
No screenshot capture, device command, builds, downloads or heldout output discovery.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIBRARY = HERE.parents[2]
IMAGES = LIBRARY / 'docs/images/optical-inputs-20261115'
N = 'glass-noise-20261114'
S = 'glass-isolated-shapes-20261114'
C = 'glass-plain-context-20261114'
M = 'glass-dock-model-20261114'
MC = M + '/material-correction-20261115'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts', type=Path, required=True)
    args = parser.parse_args()
    source_root = args.artifacts.resolve()
    records = []
    omitted = []

    def copy(relative, image_name=None, compress=False, identity_only=False):
        # Paths are always hard-coded below. Never enumerate output directories.
        src = source_root / relative
        data = src.read_bytes()
        record = {'source_namespace': relative, 'source_sha256': digest(data),
                  'source_bytes': len(data)}
        if identity_only:
            record.update({'published': None, 'processing': 'identity only; original bytes omitted'})
            omitted.append(record)
            return
        if image_name is not None:
            out = IMAGES / image_name
        else:
            out = HERE / 'archive' / relative
            if compress:
                out = out.with_name(out.name + '.gz')
        out.parent.mkdir(parents=True, exist_ok=True)
        encoded = gzip.compress(data, compresslevel=9, mtime=0) if compress else data
        out.write_bytes(encoded)
        record.update({'published': out.relative_to(LIBRARY).as_posix(),
                       'published_sha256': digest(encoded), 'published_bytes': len(encoded),
                       'processing': 'deterministic lossless gzip' if compress else 'byte-exact copy'})
        records.append(record)

    # Inputs and their source oracles only. test/manifest and geometry/points are
    # generated input metadata; no test/, noise, holdout capture PNG is opened.
    for packet in [N, S]:
        for f in ['README.md', 'generate.py', 'protocol.json', 'freeze.json', 'sRGB.icc',
                  'calibration/manifest.json', 'test/manifest.json']:
            copy(packet + '/' + f)
    for f in ['generation.json', 'verification.json']:
        copy(N + '/' + f)
    for f in ['generation-report.json', 'verification-report.json']:
        copy(S + '/' + f)
    for split, ids in [('calibration', ['c05_dots_s0', 'c06_dots_s1', 'c07_dots_s2', 'c08_dots_s3']),
                       ('test', ['n05_dots_s0', 'n06_dots_s1', 'n07_dots_s2', 'n08_dots_s3'])]:
        for identity in ids:
            copy(N + '/' + split + '/' + identity + '.points.json', compress=True)
    shapes = ['circle_top', 'triangle_body', 'star_right', 'asymmetric_lower']
    for split, prefix in [('calibration', 'ic'), ('test', 'it')]:
        for i, shape in enumerate(shapes, 1):
            stem = f'{prefix}{i:02d}_{shape}'
            copy(S + '/' + split + '/' + stem + '.geometry.json')
            if split == 'calibration':
                for role in ['control', 'shape']:
                    copy(S + '/' + split + '/' + stem + '_' + role + '.png')
    # Freeze-bound README refers to this tiny source-only atlas. It contains no output.
    copy(S + '/input-atlas.png')
    copy(S + '/input-atlas.png', image_name='isolated-source-atlas.png')

    for f in ['analysis/README.md', 'analysis/STATIC-RESULTS.md',
              'analysis/track_dots_v2.py', 'analysis/tracking-protocol-v2.json',
              'analysis/frozen-tracker-v2.json', 'analysis/tracker-v1-review.md',
              'analysis/tracker-v2-independent-review.json',
              'analysis/tracking-summary-v2/summary.json',
              'analysis/tracking-summary-v2/status-counts.csv',
              'analysis/tracking-summary-v2/conditional-center-differences.csv',
              'analysis/rejection-audit-n05-light-native/README.md',
              'analysis/rejection-audit-n05-light-native/rejection-summary.json',
              'analysis/rejection-audit-n05-light-native/per-source-rejection-summary.csv',
              'noise-analysis/README.md', 'noise-analysis/protocol.json', 'noise-analysis/analyze_noise.py',
              'next-stage-dynamic-controlled-shapes-protocol.md',
              'next-stage-dynamic-controlled-shapes-protocol.json']:
        copy(N + '/' + f)
    for f in ['all-point-statuses.csv', 'same-id-comparisons.csv']:
        copy(N + '/analysis/tracking-summary-v2/' + f, compress=True)
    copy(N + '/analysis/synthetic-selftest-v2.png', image_name='dot-tracker-synthetic-check.png')
    copy(N + '/analysis/rejection-audit-n05-light-native/source-native-dock.png', image_name='dot-pilot-source-native-crop.png')

    for f in ['analysis/README.md', 'analysis/CALIBRATION-RESULTS.md',
              'analysis/analysis-protocol.json', 'analysis/frozen-analysis.json',
              'analysis/sampling-spec.json', 'numeric-audit/calibration-numerics-audit.json']:
        copy(S + '/' + f)
    for packet, prefix in [(S, 'analysis/'), (C, '')]:
        for f in ['native-android-differential.csv', 'signed-response-strata.csv',
                  'threshold-sensitivity.csv']:
            copy(packet + '/' + prefix + 'calibration-results/' + f, compress=True)
        for f in ['report.json', 'bare-source-guards.csv']:
            copy(packet + '/' + prefix + 'calibration-results/' + f)
        copy(packet + '/' + prefix + 'calibration-results/components.jsonl.gz')
    for f in ['README.md', 'CALIBRATION-RESULTS.md', 'protocol.json', 'analysis-plan.json',
              'control-profiles/gray-control-depth-profiles.csv', 'numeric-audit.json']:
        copy(C + '/' + f)
    copy(C + '/context-comparison-at-nominal-offset.csv', compress=True)
    copy(C + '/control-profiles/gray-control-depth-profiles.png', image_name='plain-gray-control-depth-profiles.png')
    for i, shape in enumerate(shapes, 1):
        for theme in ['light', 'dark']:
            name = f'ic{i:02d}_{shape}-{theme}-signed-dock-detail.png'
            copy(C + '/calibration-visualizations/' + name, image_name='plain-' + name)

    for f in ['dock-material-root-cause.md', 'dock-edge-root-cause.md',
              'dynamic-size-claims-audit.md', 'native-size-capability-audit.md',
              'mechanism-numerical-review.md', 'flat-material-independent-review.md',
              'mechanism-analysis/profile-power-response.json', 'generate_material_sweep.py',
              'material-sweep/manifest.json', 'material-sweep/protocol.json']:
        copy(M + '/' + f)
    for f in ['flat-material-analysis/scene-summaries.csv', 'flat-material-analysis/scene-errors.csv',
              'flat-material-analysis/depth-bins.csv', 'flat-material-analysis/depth-bin-errors.csv',
              'mechanism-analysis/border-hairline-depth.json']:
        copy(M + '/' + f, compress=True)
    # Pure curves derived from already-observed calibration, never full device screens.
    copy(M + '/flat-material-analysis/gray-nominal_base-response.svg', image_name='historical-gray-transfer.svg')
    copy(M + '/mechanism-analysis/border-hairline-depth.png', image_name='historical-border-hairline-depth.png')
    for f in ['analysis/summary.md', 'haze-sigma39-20261115/SUMMARY.md',
              'rim-cosine-structure-20261115/REVIEW.md',
              'dark-rim-runtime-20261115/analysis/signed-three-coeff-summary.md',
              'dark-rim-runtime-20261115/positive-headroom-runtime-gpu-v1/independent-review.md',
              'dark-rim-runtime-20261115/positive-headroom-runtime-gpu-v1/protocol.json']:
        copy(MC + '/' + f)
    for f in ['rim-cosine-structure-20261115/report.json',
              'rim-cosine-structure-20261115/method-r2.json',
              'dark-rim-runtime-20261115/analysis/signed-three-coeff-report.json',
              'dark-rim-runtime-20261115/positive-headroom-runtime-gpu-v1/report.json',
              'haze-sigma39-20261115/numbers.json']:
        copy(MC + '/' + f, compress=True)
    # Completed observed numeric evidence is compressed without changing its bytes,
    # so another machine can resume analysis without the original working tree.
    for f in ['dark-rim-runtime-20261115/positive-headroom-runtime-gpu-v1/analysis/strips.csv',
              'dark-rim-runtime-20261115/positive-headroom-runtime-gpu-v1/analysis/metrics.csv',
              'dark-rim-runtime-20261115/positive-headroom-runtime-gpu-v1/analysis/regressions.csv']:
        copy(MC + '/' + f, compress=True)

    data = {'schema': 1, 'publication_date': '2026-11-15',
            'scope': 'Controlled synthetic inputs and already-observed fixed-size static optical diagnostics; not native parity acceptance.',
            'unopened_outputs_accessed': False, 'device_or_build_operations': False,
            'records': records, 'omitted_numeric_identities': omitted,
            'exclusions': ['APKs', 'build caches', 'xcresult', 'video', 'raw full-screen device captures',
                           'unopened RGB noise n01-n04 outputs', 'unopened isolated-shape test outputs',
                           'fresh calibration or parameter fitting']}
    (HERE / 'sources.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'files': len(records), 'source_bytes': sum(r['source_bytes'] for r in records),
                      'published_bytes': sum(r['published_bytes'] for r in records),
                      'numeric_identity_only': len(omitted)}, indent=2))


if __name__ == '__main__':
    main()
