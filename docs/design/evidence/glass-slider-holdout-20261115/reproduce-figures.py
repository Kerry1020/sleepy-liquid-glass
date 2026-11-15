#!/usr/bin/env python3
"""Regenerate the two holdout display figures from frozen JSON/original PNGs.

No fitting, new optical measurement, registration or capture is performed.
Source PNGs/masks are hash-checked through the sibling calibration packet.
"""
from pathlib import Path
import argparse
import hashlib
import html
import json
import math
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent
COLORS={'left_blue':'#286bb5','middle_red':'#c84b45','right_green':'#2b8658'}
LABELS={'left_blue':'Blue','middle_red':'Red','right_green':'Green'}
SHAPES=[('star8','st04_rgb_star8_d16','8-point / diameter 16pt'),('star6','st06_rgb_star6_d12','6-point / diameter 12pt')]
STAGES=['ingress01','ingress10','ingress50','ingress75','full100','far50']

def load(name):return json.loads((ROOT/name).read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def txt(parts,x,y,value,size=13,anchor='start',color='#1c2630'):
    parts.append(f'<text x="{x:.3f}" y="{y:.3f}" font-size="{size}" text-anchor="{anchor}" fill="{color}">{html.escape(str(value))}</text>')
def line(parts,x1,y1,x2,y2,color='#dce2e8',width=1,extra=''):
    parts.append(f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" stroke="{color}" stroke-width="{width}" {extra}/>')

def ratio_figure(fixed,primary,fig):
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="1150" viewBox="0 0 1100 1150" role="img">',
      '<title>Two frozen holdout shapes: primary area ratios and fixed-threshold range</title>',
      '<desc>All 36 color/pose rows. Dot is predeclared threshold 8, line spans thresholds 4,8,16,24. It is not a confidence interval or an acceptance score.</desc>',
      '<rect width="1100" height="1150" fill="white"/><g font-family="Arial, sans-serif">']
    txt(parts,30,32,'Frozen holdouts: observed color-evidence area ratios',22)
    txt(parts,30,58,'Dot = frozen primary T8; whisker = range over fixed T4 / 8 / 16 / 24.',14)
    txt(parts,30,79,'Threshold range is not a confidence interval. Ratio 1 does not imply matching support, position or components.',13,color='#596670')
    x0,w,max_ratio=260,775,9.5
    y0,yend=125,1075
    for v in range(10):
        xx=x0+w*v/max_ratio
        line(parts,xx,y0,xx,yend,'#edf0f3')
        txt(parts,xx,yend+23,v,12,anchor='middle')
    one=x0+w/max_ratio
    line(parts,one,y0,one,yend,'#4e5963',1.7,'stroke-dasharray="5 4"')
    for si,(_,shape_id,label) in enumerate(SHAPES):
        header=120+si*485
        txt(parts,30,header,label,17)
        for i,stage in enumerate(STAGES):
            for j,region in enumerate(COLORS):
                yy=header+29+(i*3+j)*24
                row=next(r for r in primary['rows'] if r['shape_id']==shape_id and r['stage_id']==stage and r['region_id']==region)
                values=[r['android_area_over_native_evidence_area'] for r in fixed['rows'] if r['shape_id']==shape_id and r['stage_id']==stage and r['region_id']==region]
                assert len(values)==4 and all(v is not None and 0<=v<=max_ratio for v in values)
                lo,hi=min(values),max(values);p=row['android_area_over_native_evidence_area'];color=COLORS[region]
                txt(parts,30,yy+4,stage,12)
                txt(parts,155,yy+4,LABELS[region],12,color=color)
                line(parts,x0+w*lo/max_ratio,yy,x0+w*hi/max_ratio,yy,color,2)
                for v in [lo,hi]:line(parts,x0+w*v/max_ratio,yy-4,x0+w*v/max_ratio,yy+4,color,1.5)
                parts.append(f'<circle cx="{x0+w*p/max_ratio:.3f}" cy="{yy:.3f}" r="4" fill="{color}"/>')
    txt(parts,260,1132,'Android evidence area / native evidence area; each original color and pose is kept separate.',13)
    (fig/'area-ratio-threshold-sensitivity.svg').write_text('\n'.join(parts+['</g></svg>'])+'\n')

def crop(row):
    im=Image.open(ROOT/row['shape']['path']).convert('RGB')
    density=row['pixels_per_world_unit'];ox,oy=row['world_origin_window_px'];roi=[165.5,397.5,209.5,441.5]
    box=(math.floor(ox+roi[0]*density),math.floor(oy+roi[1]*density),math.ceil(ox+roi[2]*density),math.ceil(oy+roi[3]*density))
    assert 0<=box[0]<box[2]<=im.width and 0<=box[1]<box[3]<=im.height
    return im.crop(box).resize((176,176),Image.Resampling.NEAREST),box

def capture_figure(captures,fig):
    title=ImageFont.load_default(size=21);font=ImageFont.load_default(size=15);small=ImageFont.load_default(size=12)
    image=Image.new('RGB',(1150,1350),'white');draw=ImageDraw.Draw(image)
    draw.text((25,20),'Frozen r2 holdouts: all 12 saved shape poses',font=title,fill='#1c2630')
    draw.text((25,53),'Fixed 44x44 world ROI; original 2px/pt native and 2.9750001px/dp Android grids remain unchanged.',font=font,fill='#596670')
    draw.text((25,77),'Display crops only: nearest-neighbor enlargement, no registration or color fitting. Native teal / Android purple track.',font=small,fill='#596670')
    for si,(key,shape_id,label) in enumerate(SHAPES):
        for i,stage in enumerate(STAGES):
            col=i%3;row=si*2+i//3;x=25+col*375;y=115+row*300
            draw.text((x,y),label+' / '+stage,font=font,fill='#1c2630')
            sizes=[]
            for j,(platform,platform_label) in enumerate([('ios','iOS 26.5 native'),('android','Android r2')]):
                record=next(r for r in captures['shapes'][key]['platforms'][platform] if r['stage_id']==stage)
                thumb,box=crop(record);xx=x+j*184
                draw.text((xx,y+27),platform_label,font=small,fill='#1c2630');image.paste(thumb,(xx,y+49))
                draw.rectangle((xx-1,y+48,xx+176,y+225),outline='#bdc5cc')
                sizes.append(f'{box[2]-box[0]}x{box[3]-box[1]}')
            draw.text((x,y+237),'Original crops N '+sizes[0]+' px / A '+sizes[1]+' px',font=small,fill='#596670')
            draw.text((x,y+258),'Nominal pose labels; actual geometry is in geometry.json.',font=small,fill='#596670')
    draw.text((25,1330),'48 byte-identical held shape/flat PNGs: raw/ and captures.json. Rejected 73-file attempt is excluded.',font=small,fill='#596670')
    image.save(fig/'all-holdout-poses.png',optimize=True)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.parse_args()
    fixed=load('numerical-fixed.json');primary=load('numerical-primary.json');captures=load('captures.json')
    assert len(fixed['rows'])==144 and len(primary['rows'])==36
    count=0
    for shape in captures['shapes'].values():
        for rows in shape['platforms'].values():
            for row in rows:
                for role in ['shape','flat']:
                    entry=row[role];assert digest(ROOT/entry['path'])==entry['sha256'];count+=1
    assert count==48
    for entry in load('shared-assets.json')['files']:assert digest(ROOT/entry['path'])==entry['sha256']
    fig=ROOT/'figures';fig.mkdir(exist_ok=True)
    ratio_figure(fixed,primary,fig);capture_figure(captures,fig)
    print('Regenerated 2 display figures; 48 original PNGs and shared original source/mask hashes verified.')

if __name__=='__main__':main()
