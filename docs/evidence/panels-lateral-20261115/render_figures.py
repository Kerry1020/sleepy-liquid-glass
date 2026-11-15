#!/usr/bin/env python3
"""Render only the committed supplement data; no device, build, fitting or network."""
from pathlib import Path
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / 'docs/images/panels-lateral-20261115'

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    h = json.loads((HERE / 'archive/lateral-sampling-results/harmonic-results.json').read_text())
    assert len(h['rows']) == 80
    styles = [('native', '#111111', 'Native iOS 26.5'), ('baseline', '#757575', 'Budget baseline'),
              ('gain0025', '#d18a12', 'Gain 0.025'), ('gain045', '#116ca3', 'Gain 0.45')]
    fig, axes = plt.subplots(2, 2, figsize=(12, 7.5), layout='constrained')
    for col, side in enumerate(['left', 'right']):
        for name, color, label in styles:
            rows = sorted([r for r in h['rows'] if r['side'] == side and r['image'] == name], key=lambda r: r['y'])
            axes[0, col].plot([r['y'] for r in rows], [r['apparent_harmonic_shift_px'] for r in rows],
                              marker='o', markersize=4, linewidth=1.2, color=color, label=label)
            axes[1, col].plot([r['y'] for r in rows], [r['rgb_fit_rmse'] for r in rows],
                              marker='o', markersize=4, linewidth=1.2, color=color)
        axes[0, col].set_title(side.capitalize() + ' fixed x window')
        axes[0, col].axhline(0, color='#b0b0b0', linewidth=.6)
        axes[0, col].set_ylabel('Apparent harmonic shift [original px]')
        axes[1, col].set_ylabel('RGB sinusoid fit RMSE [encoded values]')
        for ax in axes[:, col]:
            ax.set_xlabel('Original screenshot row y [px]')
            ax.set_xticks(h['plan']['rows_px'])
            ax.tick_params(axis='x', labelrotation=55)
            ax.grid(alpha=.2)
    axes[0, 0].legend(fontsize=8)
    fig.suptitle('All 80 descriptive harmonic rows; connecting lines are guides, not interpolation\n'
                 'Historical light Alert calibration; phase is not source-point correspondence', fontsize=11)
    fig.savefig(OUT / 'harmonic-phase-and-fit.png', dpi=160, metadata={'Software': 'Matplotlib'})
    plt.close(fig)

    overlay = json.loads((HERE / 'portable-inputs.json').read_text())
    captures = {r['scene']: r for r in overlay['gain045_captures']}
    backgrounds = ['fine_grid', 'color_stripes', 'tonal_blocks', 'synthetic_landscape']
    columns = [('light', 'alert'), ('light', 'share_sheet'), ('dark', 'alert'), ('dark', 'share_sheet')]
    canvas = Image.new('RGB', (1240, 1320), '#f5f5f7')
    draw = ImageDraw.Draw(canvas)
    draw.text((12, 8), 'Gain 0.45: all 16 component crops; resized only for this contact sheet', fill='black')
    operations = []
    for y, bg in enumerate(backgrounds):
        for x, (theme, carrier) in enumerate(columns):
            name = bg + '-' + theme + '-' + carrier
            entry = captures[name]
            source = ROOT / entry['published']
            # Public inputs have already been cropped in original Window pixels.
            # Applying those coordinates again would truncate the material.
            crop = Image.open(source).convert('RGBA')
            retained_size = list(crop.size)
            under = Image.new('RGBA', crop.size, '#f0f0f5')
            under.alpha_composite(crop)
            crop = under.convert('RGB')
            crop.thumbnail((296, 280), Image.Resampling.LANCZOS)
            ox, oy = 8 + x * 310, 32 + y * 320
            draw.text((ox, oy), bg + ' / ' + theme + ' / ' + carrier, fill='black')
            canvas.paste(crop, (ox, oy + 18))
            operations.append({'scene': name, 'source': entry['published'],
                               'original_window_crop_px': entry['crop_box_px'],
                               'published_input_size_px': retained_size,
                               'additional_crop': False,
                               'rendered_size_px': list(crop.size), 'alpha_preview_background': '#F0F0F5'})
    canvas.save(OUT / 'gain045-all-16.png')

    app = Image.open(ROOT / overlay['app_page']).convert('RGB')
    app_entry = next(r for r in overlay['inputs'] if r['role'] == 'application/add-table-initial')
    crop = app.copy()
    crop.thumbnail((608, 900), Image.Resampling.LANCZOS)
    crop.save(OUT / 'application-add-table-buttons.png')
    operations.append({'scene': 'application-add-table', 'source': overlay['app_page'],
                       'original_screenshot_crop_px': app_entry['crop_box_px'],
                       'published_input_size_px': list(app.size), 'additional_crop': False,
                       'rendered_size_px': list(crop.size),
                       'scope': 'Sleepy application only; not a complete public-library control'})
    (HERE / 'figure-processing.json').write_text(json.dumps({'schema': 1,
        'harmonic_rows': 80, 'harmonic_smoothing': False,
        'contact_sheets': operations,
        'comparison': {'source': 'archive/lateral-sampling-results original comparison',
                       'processing': 'byte-exact copied 2x2 display of original 640x344 integer crops; no screenshot warping'}}, indent=2) + '\n')
    print('Rendered all 80 harmonic rows, all 16 candidate panes and one labelled application illustration.')

if __name__ == '__main__':
    main()
