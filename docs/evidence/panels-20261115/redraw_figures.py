"""Portable presentation renderer. Reads only public crops and archived raw CSVs.

Run from any directory with Python3, numpy, Pillow and matplotlib installed.
The historical analysis scripts in archive/ retain original research paths;
this renderer needs neither those paths nor a phone, simulator, APK or build.
"""
from pathlib import Path
import csv
import gzip
import io
import json
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

E = Path(__file__).resolve().parent
I = E.parent.parent / 'images/panels-20261115'
S = json.loads((E / 'sources.json').read_text())
L = E.parent.parent.parent
LUMA = np.array([.2126, .7152, .0722])
PALETTE = {'native': '#2357a1', 'body8': '#777777', 'additive': '#c36d21',
           'screen': '#963760', 'budget': '#07855b'}


def numeric(relative):
    path = E / 'archive' / relative
    if path.is_file():
        return path.read_text()
    return gzip.decompress(path.with_name(path.name + '.gz').read_bytes()).decode()


def rows(relative):
    return list(csv.DictReader(io.StringIO(numeric(relative))))


def contact(name, scenes, platforms, index, carrier, title):
    fig, axes = plt.subplots(len(scenes), len(platforms),
                             figsize=(3.6 * len(platforms), (2.1 if carrier == 'alert' else 3.6) * len(scenes)),
                             squeeze=False)
    for row, scene in enumerate(scenes):
        for col, platform in enumerate(platforms):
            key = platform + '-' + scene + '-' + carrier
            image = np.asarray(Image.open(I / index[key]).convert('RGB'))
            assert image.shape[:2] == ((344, 640) if carrier == 'alert' else (683, 718))
            ax = axes[row, col]
            ax.imshow(image, interpolation='nearest', aspect='equal')
            ax.set_xticks([])
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_visible(False)
            ax.set_title(platform + ' / ' + scene.replace('panel_probe_', ''), fontsize=9)
    fig.suptitle(title, fontsize=12)
    fig.text(.5, .01, 'Identical frozen pane coordinates; original crops retained. '
             'Display scaling only. No registration, color correction or matching of foreground controls.',
             ha='center', fontsize=8)
    fig.tight_layout(rect=[0, .045, 1, .95])
    fig.savefig(I / name, dpi=150)
    plt.close(fig)


backgrounds = ['fine_grid', 'color_stripes', 'tonal_blocks', 'synthetic_landscape']
contact('history-light-alert-comparison.png', [x + '-light' for x in backgrounds],
        ['native', 'additive', 'screen', 'budget'], S['history_crop_index'], 'alert',
        'All four historical light backgrounds — static Alert calibration, mixed result')
contact('history-dark-alert-comparison.png', [x + '-dark' for x in backgrounds],
        ['native', 'budget'], S['history_crop_index'], 'alert',
        'All four historical dark backgrounds — unchanged Android control, native residuals retained')
contact('sheet12-10-comparison.png', ['panel_probe_coordinate', 'panel_probe_shapes'],
        ['native', 'sheet12', 'sheet10'], S['nonperiodic_crop_index'], 'sheet',
        'Sheet12→10 deployed API response — routing also changes; only1/14 local rows eligible')

new_tracks = {}
for platform, filename, raw_platform in [
        ('native', 'budget-straight-tracks.csv', 'native'),
        ('body8', 'body8-straight-tracks.csv', 'candidate'),
        ('additive', 'budget-straight-tracks.csv', 'baseline'),
        ('screen', 'rim-screen-straight-tracks.csv', 'candidate'),
        ('budget', 'budget-straight-tracks.csv', 'candidate')]:
    new_tracks[platform] = (rows('analysis-rim-evidence/' + filename), raw_platform)
fig, axes = plt.subplots(1, 3, figsize=(13, 3.7))
for ax, segment in zip(axes, ['neutral_top', 'neutral_left', 'neutral_right']):
    for platform, (data, raw_platform) in new_tracks.items():
        selected = [r for r in data if r['input'] == 'panel_probe_shapes' and r['carrier'] == 'alert'
                    and r['segment'] == segment and r['platform'] == raw_platform]
        distance = np.array([float(r['distance_pt']) for r in selected])
        values = np.array([[float(r['raw_' + c]) for c in 'rgb'] for r in selected]) @ LUMA
        if segment != 'neutral_top':
            values -= values[(distance >= 8) & (distance < 12)].mean()
        ax.plot(distance, values, color=PALETTE[platform], label=platform,
                ls='--' if platform == 'budget' else '-', lw=1.4)
    ax.set_xlim(-1.75, 11.75)
    ax.set_title(segment.replace('_', ' '))
    ax.set_xlabel('Original inward normal, pt / dp')
    ax.set_ylabel('Encoded luma' if segment == 'neutral_top' else 'Luma minus original8..<12pt shoulder')
    ax.axvline(0, color='.6', lw=.7)
    ax.grid(alpha=.2)
axes[0].legend(fontsize=7)
fig.suptitle('Fixed neutral edges — resolved raster peak location; unresolved native/budget FWHM', fontsize=12)
fig.tight_layout(rect=[0, 0, 1, .94])
fig.savefig(I / 'budget-neutral-curves.png', dpi=150)
plt.close(fig)

history_tracks = {}
for platform, directory, csv_platform in [
        ('native', 'budget-history', 'native'), ('budget', 'budget-history', 'android'),
        ('additive', 'history-rim-bounded', 'android'),
        ('screen', 'history-screen-increment', 'android')]:
    data = rows('analysis-rim-evidence/' + directory + '/straight-profiles.csv')
    history_tracks[platform] = [r for r in data if r['mode'] == 'raw' and r['platform'] == csv_platform]
for theme in ['light', 'dark']:
    fig, axes = plt.subplots(4, 4, figsize=(16, 10.5))
    for row, background in enumerate(backgrounds):
        for col, edge in enumerate(['left', 'right', 'top', 'bottom']):
            ax = axes[row, col]
            for platform, data in history_tracks.items():
                selected = [r for r in data if r['scene'] == background + '-' + theme and r['edge'] == edge]
                distance = np.array([float(r['normal_pt']) for r in selected])
                value = np.array([[float(r['raw_' + c]) for c in 'rgb'] for r in selected]) @ LUMA
                ax.plot(distance, value, color=PALETTE[platform], label=platform,
                        ls='--' if platform == 'budget' else '-', lw=1.1)
            ax.set_title(background + ' / ' + edge, fontsize=9)
            ax.axvline(0, color='.6', lw=.6)
            ax.grid(alpha=.18)
            ax.tick_params(labelsize=8)
            if row == 3:
                ax.set_xlabel('Original inward normal, pt / dp', fontsize=8)
            if col == 0:
                ax.set_ylabel('Raw encoded luma', fontsize=9)
    axes[0, 0].legend(fontsize=7)
    fig.suptitle('All historical ' + theme + ' straight-edge raw curves; no fitting, pooling or score', fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, .96])
    fig.savefig(I / ('history-' + theme + '-all-straight-curves.png'), dpi=150)
    plt.close(fig)
print('Rendered six figures from public crops/CSV only.')
