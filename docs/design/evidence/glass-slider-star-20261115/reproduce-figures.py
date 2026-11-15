#!/usr/bin/env python3
"""Rebuild display figures from packaged frozen numbers and original PNGs.

This script performs no fitting, image registration, measurement resampling,
threshold adjustment, or capture. PNG crops are display-only nearest-neighbor.
Run from any directory: python3 path/to/reproduce-figures.py
"""
from pathlib import Path
import hashlib
import html
import json
import math
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FIG = ROOT / 'figures'
FIG.mkdir(exist_ok=True)
NUM = json.loads((ROOT / 'numerical-summary.json').read_text())
BASE = json.loads((ROOT / 'baseline-transport-summary.json').read_text())
CAP = json.loads((ROOT / 'captures.json').read_text())
PROFILE = json.loads((ROOT / 'profile.json').read_text())
COLORS = {'left_blue': '#2873c5', 'middle_red': '#c44242', 'right_green': '#24814e'}
NAMES = {'left_blue': 'Blue source region', 'middle_red': 'Red source region', 'right_green': 'Green source region'}
STAGES = [s['stage_id'] for s in NUM['stages']]

def svg_start(w, h, title, desc):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img">',
            '<title>' + html.escape(title) + '</title><desc>' + html.escape(desc) + '</desc>',
            '<rect width="100%" height="100%" fill="#fff"/>',
            '<g font-family="Arial, sans-serif" fill="#17202a">']

def text(parts, x, y, value, size=13, anchor='start', color='#17202a'):
    parts.append(f'<text x="{x:.3f}" y="{y:.3f}" font-size="{size}" text-anchor="{anchor}" fill="{color}">{html.escape(str(value))}</text>')

def line(parts, x1, y1, x2, y2, color='#dce1e5', width=1, extra=''):
    parts.append(f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="{color}" stroke-width="{width}" {extra}/>')

def poly(parts, points, color, width=2, extra=''):
    pairs = ' '.join(f'{x:.3f},{y:.3f}' for x, y in points)
    parts.append(f'<polyline points="{pairs}" fill="none" stroke="{color}" stroke-width="{width}" {extra}/>')

def save_svg(name, parts):
    (FIG / name).write_text('\n'.join(parts + ['</g></svg>']) + '\n')

def primary(region):
    return next(t for t in region['thresholds'] if t['threshold_projection_byte'] == 8)

# Formula is the implemented common RGB sample displacement, not measured thickness.
p = svg_start(960, 470, 'Implemented r2 single-slider shoulder',
              'Engineering common RGB displacement profile as a function of contour inset. It is not a measurement of native lens thickness.')
text(p, 45, 35, 'r2 single-slider common RGB sampling shoulder', 21)
text(p, 45, 60, 'D(s) = 7.8 max(1 - s / 7.5, 0)^2; finite support 7.5 dp', 15)
text(p, 45, 82, 'Engineering displacement only; not a recovered native height or ray field.', 13, color='#59646d')
x0, y0, w, h = 90, 120, 785, 260
for value in range(0, 9, 2):
    y = y0 + h - h * value / 8
    line(p, x0, y, x0+w, y)
    text(p, x0-15, y+5, value, anchor='end')
for value in range(0, 11):
    x = x0+w*value/10
    line(p, x, y0+h, x, y0+h+5, '#707b84')
    text(p, x, y0+h+23, value, anchor='middle')
line(p, x0, y0, x0, y0+h, '#707b84')
line(p, x0, y0+h, x0+w, y0+h, '#707b84')
pts = [(x0+w*s/10, y0+h-h*(PROFILE['refraction']*max(1-s/PROFILE['widthDp'],0)**2)/8)
       for s in [i/100 for i in range(1001)]]
poly(p, pts, '#3268a8', 3)
line(p, x0+w*.75, y0, x0+w*.75, y0+h, '#ad5d23', extra='stroke-dasharray="6 4"')
text(p, x0+w*.75+10, y0+30, 'support ends at s=7.5', 13, color='#ad5d23')
text(p, x0, y0-15, 'sample displacement D(s), dp', 13)
text(p, x0+w/2, 438, 'inset s from carrier edge toward the center, dp', 14, anchor='middle')
save_svg('shoulder-profile.svg', p)

# The material is not a monotone output-to-source coordinate mapping. Preserve
# the fold instead of allowing the displacement-only plot to hide it.
p = svg_start(960, 470, 'Implemented source-normal sampling fold',
              'In the local planar-normal approximation the common RGB source inset is u=s+D(s). Its derivative is negative at the outer edge and crosses zero at 3.89423 dp. This is the Android engineering map, not a native or physical thickness measurement.')
text(p, 45, 35, 'Implemented source-normal coordinate: u(s) = s + D(s)', 21)
text(p, 45, 60, 'Local planar normal approximation; common RGB sample before dispersion.', 14)
text(p, 45, 82, "u'(0) = -1.08; fold at s = 3.89423 dp; minimum u = 5.69712 dp", 14, color='#8b4c29')
x0, y0, w, h = 90, 120, 785, 260
for value in range(0, 11, 2):
    yy = y0 + h - h * value / 10
    line(p, x0, yy, x0+w, yy)
    text(p, x0-15, yy+5, value, anchor='end')
for value in range(0, 11):
    xx = x0+w*value/10
    text(p, xx, y0+h+23, value, anchor='middle')
line(p, x0, y0, x0, y0+h, '#707b84')
line(p, x0, y0+h, x0+w, y0+h, '#707b84')
line(p, x0, y0+h, x0+w, y0, '#8c959d', 1.5, 'stroke-dasharray="5 4"')
samples = [i/100 for i in range(1001)]
poly(p, [(x0+w*s/10, y0+h-h*(s+PROFILE['refraction']*max(1-s/PROFILE['widthDp'],0)**2)/10) for s in samples], '#3268a8', 3)
fold = PROFILE['widthDp']*(1-PROFILE['widthDp']/(2*PROFILE['refraction']))
minimum = fold + PROFILE['refraction']*(1-fold/PROFILE['widthDp'])**2
line(p, x0+w*fold/10, y0, x0+w*fold/10, y0+h, '#ad5d23', 1.5, 'stroke-dasharray="6 4"')
p.append(f'<circle cx="{x0+w*fold/10:.3f}" cy="{y0+h-h*minimum/10:.3f}" r="5" fill="#ad5d23"/>')
text(p, x0+10, y0+25, 'outer normal coordinate reverses until the fold', 13, color='#ad5d23')
text(p, x0+10, y0+46, 'gray dashed: identity u=s', 13, color='#68747e')
text(p, x0, y0-15, 'common source inset u(s), dp', 13)
text(p, x0+w/2, 438, 'output inset s from carrier edge, dp', 14, anchor='middle')
save_svg('sampling-fold.svg', p)

# All six poses and all three source-color regions; same primary threshold for both candidates.
p = svg_start(1150, 435, 'Centroid distance to native color evidence',
              'Six settled poses and three regions at frozen threshold 8. Gray is r1; color is r2. Lower is closer for this descriptor only. Some regions regress.')
text(p, 40, 32, 'Color-evidence centroid distance to native', 21)
text(p, 40, 56, 'Frozen primary threshold 8; all six poses retained. This is one descriptor, not an acceptance score.', 14)
line(p, 43, 78, 75, 78, '#8b939b', 2, 'stroke-dasharray="5 3"')
text(p, 82, 83, 'r1 checkpoint', 13)
line(p, 230, 78, 262, 78, '#3268a8', 3)
text(p, 270, 83, 'r2 shoulder (region color)', 13)
for j, region_id in enumerate(COLORS):
    x, y, width, height = 55+j*370, 130, 310, 225
    text(p, x, y-12, NAMES[region_id], 16, color=COLORS[region_id])
    for v in range(6):
        yy=y+height-height*v/5
        line(p,x,yy,x+width,yy)
        text(p,x-9,yy+4,v,11,anchor='end')
    values1, values2 = [], []
    for i,s in enumerate(NUM['stages']):
        t = primary(next(r for r in s['regions'] if r['region_id']==region_id))
        xx=x+width*i/5
        values1.append((xx,y+height-height*t['r1_comparison']['centroid_distance_world']/5))
        values2.append((xx,y+height-height*t['r2_comparison']['centroid_distance_world']/5))
        text(p,xx,y+height+19,s['stage_id'].replace('ingress','in'),10,anchor='middle')
    poly(p,values1,'#8b939b',2,'stroke-dasharray="5 3"')
    poly(p,values2,COLORS[region_id],2.8)
    for xx,yy in values2:
        p.append(f'<circle cx="{xx:.3f}" cy="{yy:.3f}" r="3.5" fill="{COLORS[region_id]}"/>')
text(p,55,414,'Distance in world units. Area, support bounds, components and thresholds 4/8/16/24 remain in numerical-summary.json.',12,color='#59646d')
save_svg('centroid-errors.svg',p)

# Centroid transport relative to each platform's own source baseline, never called ray tracking.
p = svg_start(1180, 740, 'Own-baseline color-evidence centroid movement',
              'Arrows from the origin show color-evidence centroid movement from each platform own unchanged source baseline. Native black, r1 dashed gray, r2 region color. Screen y increases down.')
text(p,35,33,'Own-baseline color-evidence centroid movement',21)
text(p,35,57,'Primary threshold 8; +x right, +y down. Origin is each platform own unchanged source baseline.',14)
text(p,35,79,'Native black; r1 dashed gray; r2 source-region color. Vectors do not recover optical rays.',13,color='#59646d')
for j,region_id in enumerate(COLORS):
    text(p,35,130+j*190,NAMES[region_id],14,color=COLORS[region_id])
    for i,s in enumerate(BASE['stages']):
        cx,cy=132+i*185,215+j*190
        if j==0:text(p,cx,123,s['stage_id'],13,anchor='middle')
        for vv in [-4,-2,0,2,4]:
            xx=cx+vv*15; yy=cy+vv*15
            line(p,xx,cy-60,xx,cy+60,'#f0f2f4')
            line(p,cx-60,yy,cx+60,yy,'#f0f2f4')
        line(p,cx-60,cy,cx+60,cy,'#cbd1d7')
        line(p,cx,cy-60,cx,cy+60,'#cbd1d7')
        t=primary(next(r for r in s['regions'] if r['region_id']==region_id))
        for key,color,dashed in [('r1_centroid_movement','#9aa1a8',True),('native_centroid_movement','#161a1d',False),('r2_centroid_movement',COLORS[region_id],False)]:
            dx,dy=t[key]
            ex,ey=cx+15*dx,cy+15*dy
            line(p,cx,cy,ex,ey,color,2,'stroke-dasharray="4 3"' if dashed else '')
            angle=math.atan2(dy,dx)
            if math.hypot(dx,dy)>0.03:
                for sign in [-1,1]:
                    line(p,ex,ey,ex-5*math.cos(angle+sign*.5),ey-5*math.sin(angle+sign*.5),color,2)
        p.append(f'<circle cx="{cx}" cy="{cy}" r="2" fill="#161a1d"/>')
text(p,35,724,'Each cell spans -4..+4 world units in both axes. Full four-threshold vectors: baseline-transport-summary.json.',12,color='#59646d')
save_svg('centroid-movement.svg',p)

# Raw PNG checks before any display-only crop.
for rows in CAP['platforms'].values():
    for row in rows:
        for role in ['shape','flat']:
            raw=ROOT/row[role]['path']
            assert hashlib.sha256(raw.read_bytes()).hexdigest()==row[role]['sha256']

font=ImageFont.load_default(size=16)
small=ImageFont.load_default(size=13)
title=ImageFont.load_default(size=21)
roi=CAP['fixed_roi_xyxy_world']

def crop(row,role):
    image=Image.open(ROOT/row[role]['path']).convert('RGB')
    ppw=row['pixels_per_world_unit']; ox,oy=row['world_origin_window_px']
    box=(math.floor(ox+roi[0]*ppw),math.floor(oy+roi[1]*ppw),math.ceil(ox+roi[2]*ppw),math.ceil(oy+roi[3]*ppw))
    assert 0<=box[0]<box[2]<=image.width and 0<=box[1]<box[3]<=image.height
    return image.crop(box).resize((264,264),Image.Resampling.NEAREST),box

for role, filename in [('shape','six-pose-comparison.png'),('flat','six-pose-flat-controls.png')]:
    sheet=Image.new('RGB',(1150,1120),'white'); draw=ImageDraw.Draw(sheet)
    draw.text((25,20),'First-star r2 calibration: '+('shape captures' if role=='shape' else 'pose-matched flat controls'),font=title,fill='#17202a')
    draw.text((25,51),'Six settled poses; same fixed 44x44 world ROI. Nearest-neighbor crops for display only.',font=font,fill='#4c5861')
    draw.text((25,77),'Original native 2 px/pt and Android 2.9750001 px/dp kept for all measurements.',font=small,fill='#4c5861')
    for i,stage in enumerate(STAGES):
        col=i%3; row_index=i//3; x=25+col*375; y=120+row_index*495
        draw.text((x,y),stage+' (nominal pose label)',font=font,fill='#17202a')
        for k,(platform,label) in enumerate([('ios','iOS 26.5 native'),('android-r2','Android r2')]):
            row=next(v for v in CAP['platforms'][platform] if v['stage_id']==stage)
            image,box=crop(row,role)
            # Pair the two fixed-world views vertically within each pose tile.
            thumb=image.resize((176,176),Image.Resampling.NEAREST)
            xx=x+k*184
            draw.text((xx,y+28),label,font=small,fill='#17202a')
            sheet.paste(thumb,(xx,y+52))
            draw.rectangle((xx-1,y+51,xx+176,y+228),outline='#bec5cb')
            draw.text((xx,y+239),f'original crop {box[2]-box[0]}x{box[3]-box[1]} px',font=small,fill='#59646d')
            metric=next(s for s in NUM['stages'] if s['stage_id']==stage)
            coverage=metric['native_actual_discrete_capsule_approximation' if platform=='ios' else 'android_actual_discrete_capsule_approximation']
            draw.text((xx,y+260),f'capsule approx {coverage:.4f}',font=small,fill='#59646d')
        # A larger pair places the star/rail relationship in the retained ROI.
        draw.text((x,y+304),'Tint differs: native teal / Android theme purple.',font=small,fill='#59646d')
        draw.text((x,y+325),'Coverage is source-mask/capsule geometry,',font=small,fill='#59646d')
        draw.text((x,y+345),'not native alpha or measured physical thickness.',font=small,fill='#59646d')
    draw.text((25,1093),'Original full PNGs and SHA-256: raw/ and captures.json. No registration or color fitting.',font=small,fill='#59646d')
    sheet.save(FIG/filename,optimize=True)

source=Image.open(ROOT/'source/inputs/st01_rgb_star_d16.png').convert('RGB')
source.crop((331,795,419,883)).resize((440,440),Image.Resampling.NEAREST).save(FIG/'source-star.png',optimize=True)
print('Rebuilt 4 SVG plots and 3 PNG display figures from packaged originals/frozen numerical summaries.')
