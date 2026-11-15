#!/usr/bin/env python3
"""Render original full100 ROI pixels and five observed red-channel curves.

The nearest-neighbor crops and chart are displays only. The replay script uses
unaltered original 2x pixel samples; it never measures this assembled figure.
"""
from pathlib import Path
import argparse,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);a=p.parse_args();out=Path(a.output).resolve();assert not out.exists()
 m=json.loads((ROOT/'manifest.json').read_text());canvas=Image.new('RGB',(1240,800),'#f6f8fb');d=ImageDraw.Draw(canvas)
 font=lambda size:ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',size) if Path('/System/Library/Fonts/Supplemental/Arial.ttf').exists() else ImageFont.load_default()
 title,fontbody,small=font(28),font(19),font(16)
 d.text((24,18),'Native Slider: original pixels, third G amplitude',font=title,fill='#142333')
 d.text((24,54),'iOS 26.5 | fixed multicolor star | full100 | original 2x raster | no registration',font=fontbody,fill='#49576a')
 images={}
 for i,(r,label) in enumerate([('control','C: G128'),('half','H: G180'),('full','F: G232'),('control_repeat','Repeated C')]):
  cr=next(c for c in m['captures'] if c['round']==r and c['stage']=='full100' and c['kind']=='shape');im=Image.open(ROOT/cr['file']).convert('RGB');images[r]=np.asarray(im)[3:91,3:91]
  x=24+i*300;d.text((x,92),label,font=fontbody,fill='#142333');canvas.paste(im.resize((282,282),Image.Resampling.NEAREST),(x,122))
  # y=422 is a display annotation outside the original-pixel crop files.
  yy=122+(844-792)*3;d.line((x,yy,x+282,yy),fill='#e0b23c',width=2);d.text((x,411),'Gold line: y=422 rail boundary',font=small,fill='#6c5823')
 d.text((24,452),'Measured red channel at the five exceptional pixels',font=fontbody,fill='#142333')
 x0,y0,w,h=72,718,590,210
 d.line((x0,y0-h,x0,y0,x0+w,y0),fill='#64748b',width=2)
 for v in [0,15,30,45,60]:
  yy=y0-v/60*h;d.line((x0,yy,x0+w,yy),fill='#d9e1ea');d.text((x0-31,yy-8),str(v),font=small,fill='#49576a')
 for level in [128,180,232]:
  xx=x0+(level-128)/104*w;d.text((xx-16,y0+10),str(level),font=small,fill='#49576a')
 d.text((x0+200,y0+38),'Input G code (encoded sRGB)',font=small,fill='#49576a');d.text((24,480),'R byte',font=small,fill='#49576a')
 positions=[(183.25,411.25),(183.75,411.25),(184.25,411.25),(184.75,411.25),(185.25,411.75)];colors=['#1d4ed8','#b91c1c','#7e22ce','#047857','#c16a0a'];levels=[128,180,232]
 for k,((x,y),color) in enumerate(zip(positions,colors)):
  iy,ix=int(y*2)-795,int(x*2)-331;values=[int(images[r][iy,ix,0]) for r in ['control','half','full']]
  pts=[(x0+(level-128)/104*w,y0-v/60*h) for level,v in zip(levels,values)];d.line(pts,fill=color,width=3)
  for xx,yy in pts:d.ellipse((xx-4,yy-4,xx+4,yy+4),fill=color)
  yy=488+k*38;d.line((720,yy+9,746,yy+9),fill=color,width=4);d.text((758,yy),f'({x:.2f}, {y:.2f}): {values[0]} / {values[1]} / {values[2]}',font=small,fill='#142333')
 d.text((720,700),'Above rail: 5 red pixels |E| > 1.5 byte',font=fontbody,fill='#142333');d.text((720,730),'3 exceed 4; maximum 7.5. No parity verdict.',font=small,fill='#49576a')
 out.parent.mkdir(parents=True,exist_ok=True);canvas.save(out);print(out)
if __name__=='__main__':main()
