"""Presentation-only five-way plot of frozen crops and raw curves; no new ROI."""
from pathlib import Path
import csv
import json
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

O = Path(__file__).resolve().parent
P = O.parent
N = P / 'native-panel-feasibility-preparation'
att = json.loads((N / 'attachments/manifest.json').read_text())[0]['attachments']
native = N / 'attachments' / next(a['exportedFileName'] for a in att
    if 'panel_probe_shapes-light-alert-rest_0_' in a['suggestedHumanReadableName']
    and a['exportedFileName'].endswith('.png'))
names = ['native', 'body8', 'additive', 'screen', 'budget']
labels = ['iOS 26.5 native', 'Body8 / zero floor', 'Additive floor .08', 'Screen increment .08', 'Budget increment .08']
colors = ['#2357a1', '#777777', '#c36d21', '#963760', '#07855b']
paths = {'native': native}
for name, directory in [('body8', 'panels-alert-body8-20261115'),
        ('additive', 'panels-alert-rim-bounded-20261115'),
        ('screen', 'panels-alert-floor-screen-20261115'),
        ('budget', 'panels-alert-floor-budget-20261115')]:
    matrix = json.loads((P / directory / 'matrix.json').read_text())
    cap = next(c for c in matrix['captures']
               if c['background'] == 'panel_probe_shapes' and c['carrier'] == 'alert')
    paths[name] = P / directory / cap['screen_png']
tracks = {}
luma = np.array([.2126, .7152, .0722])
for name, filename, platform in [
        ('native', 'budget-straight-tracks.csv', 'native'),
        ('body8', 'body8-straight-tracks.csv', 'candidate'),
        ('additive', 'budget-straight-tracks.csv', 'baseline'),
        ('screen', 'rim-screen-straight-tracks.csv', 'candidate'),
        ('budget', 'budget-straight-tracks.csv', 'candidate')]:
    rows = list(csv.DictReader((O / filename).open()))
    tracks[name] = {}
    for segment in ['neutral_top', 'neutral_left', 'neutral_right']:
        selected = [r for r in rows if r['input'] == 'panel_probe_shapes'
                    and r['carrier'] == 'alert' and r['segment'] == segment
                    and r['platform'] == platform]
        tracks[name][segment] = (
            np.array([float(r['distance_pt']) for r in selected]),
            np.array([[float(r['raw_' + c]) for c in 'rgb'] for r in selected]) @ luma)

fig = plt.figure(figsize=(14, 7))
grid = fig.add_gridspec(2, 15, height_ratios=[1.2, 1], hspace=.48, wspace=.9)
for i, name in enumerate(names):
    ax = fig.add_subplot(grid[0, i * 3:(i + 1) * 3])
    data = np.asarray(Image.open(paths[name]).convert('RGB'))
    assert data.shape[:2] == (1334, 750)
    ax.imshow(data[614:676, 43:103], extent=[43, 103, 676, 614],
              interpolation='nearest', aspect='equal')
    ax.axvline(55.5, color='#1362ff', lw=.8)
    ax.axvline(56.5, color='#111111', ls='--', lw=.8)
    ax.set_title(labels[i], fontsize=10)
    ax.set_xticks([43, 55.5, 103])
    ax.set_xticklabels(['43', '.25/.75', '103'], fontsize=8)
    ax.set_yticks([614, 676])
    ax.tick_params(labelsize=8)
    ax.set_xlabel('Original screen pixels', fontsize=8)
    if i == 0:
        ax.set_ylabel('Original y pixels', fontsize=8)

for i, segment in enumerate(['neutral_top', 'neutral_left', 'neutral_right']):
    ax = fig.add_subplot(grid[1, i * 5:(i + 1) * 5])
    for name, label, color in zip(names, labels, colors):
        distance, value = tracks[name][segment]
        if segment != 'neutral_top':
            value = value - value[(distance >= 8) & (distance < 12)].mean()
        ax.plot(distance, value, label=label, color=color, lw=1.4,
                ls='--' if name == 'budget' else '-')
    ax.set_xlim(-1.75, 11.75)
    ax.axvline(0, color='.6', lw=.6)
    ax.grid(alpha=.22)
    ax.set_xlabel('Original inward normal, pt / dp', fontsize=9)
    ax.set_title('Frozen ' + segment.replace('_', ' '), fontsize=10)
    if segment == 'neutral_top':
        ax.set_ylabel('Raw encoded luma')
        ax.legend(fontsize=7, loc='best')
    else:
        ax.set_ylabel('Luma minus shoulder', fontsize=9)
        ax.axhline(0, color='.5', lw=.6)
fig.suptitle('Budget increment: zero primary clipping, restored side highlight, remaining native mismatch', fontsize=12, y=.99)
fig.text(.5, .008, 'Same original60x62px crop; nearest-neighbor display only, no data resize/warp/registration. '
         'Curves use frozen tracks. Native and budget peak width unresolved under unchanged minimum3-pixel gate.',
         ha='center', fontsize=8)
fig.savefig(O / 'budget-five-way-fixed-comparison.png', dpi=150, bbox_inches='tight')
plt.close(fig)
print(O / 'budget-five-way-fixed-comparison.png')
