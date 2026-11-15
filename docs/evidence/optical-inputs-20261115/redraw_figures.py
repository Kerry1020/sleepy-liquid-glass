#!/usr/bin/env python3
"""Redraw selected figures from published numbers; no device capture or fitting."""
import argparse
import csv
import gzip
import hashlib
import io
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
LIBRARY = HERE.parents[2]
IMAGES = LIBRARY / 'docs/images/optical-inputs-20261115'
ARCHIVE = HERE / 'archive'
M = ARCHIVE / 'glass-dock-model-20261114'
C = ARCHIVE / 'glass-plain-context-20261114'
MC = M / 'material-correction-20261115'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--calibration-source-root', type=Path)
    args = parser.parse_args()
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'axes.spines.top': False,
                         'axes.spines.right': False, 'font.size': 10})
    figures = []

    def save(fig, name, sources, kind):
        for extension in ['svg', 'png']:
            out = IMAGES / f'{name}.{extension}'
            fig.savefig(out, dpi=170, bbox_inches='tight', metadata={'Creator': 'Sleepy controlled optical evidence'})
            figures.append({'published': out.relative_to(LIBRARY).as_posix(),
                            'sha256': sha(out), 'kind': kind, 'sources': sources})
        plt.close(fig)

    power_file = M / 'mechanism-analysis/profile-power-response.json'
    rows = json.loads(power_file.read_text())
    names = ['ic01_circle_top', 'ic02_triangle_body', 'ic03_star_right', 'ic04_asymmetric_lower']
    power_data = {p: [next(r['native_comparison']['mean_abs_RGB'] for r in rows
                           if r.get('pair') == n and r.get('power') == p and r.get('region') == 'base')
                      for n in names] for p in [1, 2]}
    fig, ax = plt.subplots(figsize=(9, 3.6))
    x = np.arange(4)
    for p, delta, color in [(1, -.18, '#416e9a'), (2, .18, '#c36148')]:
        ax.bar(x + delta, power_data[p], width=.35, color=color, label=f'Historical Q^{p}')
    ax.set_xticks(x, ['Circle / upper edge', 'Triangle / body', 'Star / right edge', 'Asymmetric / lower'])
    ax.set_ylabel('Conditional RGB MAE (0–255 code units)')
    ax.set_title('All four fixed light-calibration scenes regress with power 2')
    ax.legend(frameon=False)
    ax.set_ylim(bottom=0)
    save(fig, 'historical-power-regressions', [{'archive': power_file.relative_to(HERE).as_posix(), 'sha256': sha(power_file)}],
         'observed fixed-size static calibration; no product acceptance')

    differential_file = C / 'calibration-results/native-android-differential.csv.gz'
    with gzip.open(differential_file, 'rt') as stream:
        selected = [r for r in csv.DictReader(stream) if r['channel'] == 'rgb'
                    and r['stratum'] == 'nominal_base_excluding_selected_and_glyph_neighborhoods'
                    and float(r['nominal_boundary_offset_px']) == 0]
    assert len(selected) == 8
    selected.sort(key=lambda r: (r['theme_requested'], r['pair_id']))
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    for ax, theme in zip(axes, ['light', 'dark']):
        subset = sorted([r for r in selected if r['theme_requested'] == theme], key=lambda r: r['pair_id'])
        x = np.arange(4)
        ax.bar(x-.18, [float(r['abs_mean']) for r in subset], .35, label='Paired-response MAE', color='#277f82')
        ax.bar(x+.18, [float(r['absolute_control_RGB_error_abs_mean']) for r in subset], .35,
               label='Absolute control MAE', color='#b87b48')
        ax.set_xticks(x, ['Circle', 'Triangle', 'Star', 'Asymmetric'])
        ax.set_title(f'{theme.capitalize()} · 47,286 nominal base pixels')
        ax.set_ylim(0, 36)
    axes[0].set_ylabel('RGB MAE (0–255 code units)')
    axes[0].legend(frameon=False)
    fig.suptitle('A small conditional residual can coexist with a large absolute material error')
    save(fig, 'conditional-versus-absolute', [{'archive': differential_file.relative_to(HERE).as_posix(), 'sha256': sha(differential_file)}],
         'observed historical D46.5/plain-scroll static calibration')

    # Mathematical illustrations are explicitly separated from observed evidence.
    t = np.linspace(0, 1.2, 601)
    linear = np.maximum(1-t, 0)
    cosine = np.where(t < 1, np.cos(np.pi*t/2), 0)
    shoulder = np.where(t < 1, (1-t**3)**2, 0)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))
    for y, label, color in [(linear, 'Finite linear', '#777777'), (cosine, 'Truncated half-cosine', '#4777a0'),
                            (shoulder, '(1 − t³)² shoulder', '#277f82')]:
        axes[0].plot(t, y, label=label, color=color)
    axes[0].set(xlabel='Actual inward edge / registered width', ylabel='Rim profile amplitude', ylim=(-.02,1.05))
    axes[0].legend(frameon=False)
    shift = np.linspace(-.25, .35, 601)
    for body, color in [(.15, '#4777a0'), (.5, '#277f82'), (.9, '#b15d46')]:
        headroom = np.where(shift <= 0, np.maximum(body+shift, 0),
                            body+(1-body)*(-np.expm1(-shift/(1-body))))
        axes[1].plot(shift, headroom, color=color, label=f'Body={body}')
        axes[1].plot(shift, np.clip(body+shift,0,1), color=color, linestyle=':', alpha=.6)
    axes[1].set(xlabel='Signed channel shift', ylabel='Result (unpremultiplied channel)', ylim=(0,1.04))
    axes[1].legend(frameon=False)
    fig.suptitle('Current opt-in engineering functions · equations only, not native measurements')
    save(fig, 'shoulder-headroom-mathematics', [{'scope': 'runtime-source-identities.json; symbolic formulas documented in controlled-optical-studies.md'}],
         'mathematical illustration only; no fitted/native curve')

    review = MC / 'dark-rim-runtime-20261115/positive-headroom-runtime-gpu-v1/independent-review.md'
    table = {}
    for line in review.read_text().splitlines():
        if not line.startswith('|'): continue
        cells = [x.strip() for x in line.strip('|').split('|')]
        if len(cells) == 3:
            try: table[cells[0]] = [float(cells[1]), float(cells[2])]
            except ValueError: pass
    keys = ['Top first3 own-body RGB MAE', 'Top own-body maximum absolute error',
            'Six right-corner strips first-derivative error MAE',
            'Six right-corner strips second-derivative error MAE']
    observed = {k: table[k] for k in keys}
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.7))
    x = np.arange(2)
    for ax, pair, labels in [(axes[0], keys[:2], ['Top3 own-body MAE', 'Worst own-body error']),
                             (axes[1], keys[2:], ['Corner first derivative', 'Corner second derivative'])]:
        ax.bar(x-.18, [observed[k][0] for k in pair], .35, label='Logit control', color='#4777a0')
        ax.bar(x+.18, [observed[k][1] for k in pair], .35, label='Positive headroom', color='#b15d46')
        ax.set_xticks(x,labels)
        ax.set_ylim(bottom=0)
        ax.set_ylabel('Error (0–255 code units)')
    axes[0].legend(frameon=False)
    fig.suptitle('Actual headroom GPU diagnostic: an average gain does not remove corner regressions')
    save(fig, 'headroom-retained-regressions', [{'archive': review.relative_to(HERE).as_posix(), 'sha256': sha(review)}],
         'observed same-size static GPU diagnostic; disabled-by-default candidate')
    numbers = {'schema': 1, 'power_base_mae': power_data,
               'plain_nominal_base': selected, 'headroom_selected_aggregate_errors': observed,
               'no_new_fit': True, 'no_new_capture': True}
    (HERE / 'figure-data.json').write_text(json.dumps(numbers, indent=2) + '\n')

    if args.calibration_source_root:
        src = args.calibration_source_root
        files = [src / 'c01_rgb_noise_s0.png', src / 'c05_dots_s0.png']
        crop_box = [210, 1030, 510, 1250]
        canvas = Image.new('RGB', (620, 252), 'white')
        draw = ImageDraw.Draw(canvas)
        originals = []
        for index, (file, label) in enumerate(zip(files, ['Calibration RGB noise · source only', 'Calibration known dots · source only'])):
            with Image.open(file) as image:
                canvas.paste(image.crop(crop_box).convert('RGB'), (index*310, 30))
            draw.text((index*310+3, 6), label, fill='#18252c')
            originals.append({'file': file.name, 'sha256': sha(file), 'crop_ltrb_px': crop_box,
                              'source_only': True, 'resampling': 'none'})
        out = IMAGES / 'calibration-fields-source-only.png'
        canvas.save(out)
        figures.append({'published': out.relative_to(LIBRARY).as_posix(), 'sha256': sha(out),
                        'kind': 'generated calibration source crops; no observed output', 'sources': originals})

    (HERE / 'figure-manifest.json').write_text(json.dumps({'schema': 1, 'figures': figures,
                  'figure_data_sha256': sha(HERE/'figure-data.json')}, indent=2) + '\n')
    print(json.dumps({'figures': len(figures), 'data': 'figure-data.json', 'no_new_fit_or_capture': True}))


if __name__ == '__main__':
    main()
