#!/usr/bin/env python3
"""Render native/r2/r4 crops with the same G response scale; no registration."""
from pathlib import Path
import argparse
import importlib.util
import json
import numpy as np
from PIL import Image,ImageDraw,ImageFont

root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'manifest.json').read_text())
spec=importlib.util.spec_from_file_location('frozen',root/'frozen/analyze-witness-control-v1_1.py')
an=importlib.util.module_from_spec(spec);spec.loader.exec_module(an)

def font(size):
    for name in ['/System/Library/Fonts/Supplemental/Arial.ttf','DejaVuSans.ttf','Arial.ttf']:
        try:return ImageFont.truetype(name,size)
        except OSError:pass
    return ImageFont.load_default(size=size)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True);args=p.parse_args()
    fig=Image.new('RGB',(1240,930),'#f4f5f7');draw=ImageDraw.Draw(fig)
    draw.text((28,20),'Ingress75: original capture ROI and G witness response',font=font(28),fill='#111827')
    draw.text((28,58),'Same 44 x 44 pt ROI; thresholds and response scale are fixed. Calibration only.',font=font(18),fill='#374151')
    target=np.asarray(Image.open(root/'masks/primary-ingress75-excessB-mask.png'))>0
    edge=target & ~(np.roll(target,1,0)&np.roll(target,-1,0)&np.roll(target,1,1)&np.roll(target,-1,1))
    stops=np.array([[8,12,35],[29,72,145],[0,165,177],[232,220,67],[255,255,218]],float)
    def palette(v):
        q=np.clip(v/104,0,1)*4;i=np.minimum(np.floor(q).astype(int),3);f=(q-i)[...,None]
        return np.rint(stops[i]*(1-f)+stops[i+1]*f).astype(np.uint8)
    xx=an.ROI[0]+(np.arange(176)+.5)/4;yy=an.ROI[1]+(np.arange(176)+.5)/4;x,y=np.meshgrid(xx,yy)
    for ci,(version,title) in enumerate([('native','Native iOS'),('r2','Android r2'),('r4','Android r4 (candidate)')]):
        px=40+ci*405;draw.text((px,96),title,font=font(24),fill='#111827');values={}
        for role in ['witness','control']:
            rec=next(r for r in manifest['captures'] if r['version']==version and r['role']==role and r['stage']=='ingress75' and r['kind']=='shape')
            im=Image.open(root/rec['file']);raw=np.asarray(im,dtype=np.uint8)[...,:3];b=rec['original_pixel_crop_xyxy'];d=rec['original_pixels_per_world_unit'];o=np.asarray(rec['original_world_origin_in_screenshot_px'],float)
            values[role]=an.bilinear(raw,x,y,{'origin':o-b[:2],'scale':d})
            if role=='witness':
                roi=[int(np.ceil(o[0]+an.ROI[0]*d-.5))-b[0],int(np.ceil(o[1]+an.ROI[1]*d-.5))-b[1],int(np.ceil(o[0]+an.ROI[2]*d-.5))-b[0],int(np.ceil(o[1]+an.ROI[3]*d-.5))-b[1]]
                fig.paste(im.crop(roi).convert('RGB').resize((352,352),Image.Resampling.NEAREST),(px,135))
        draw.text((px,492),'Original ROI pixels (display enlarged)',font=font(16),fill='#374151')
        g=(values['witness']-values['control'])[...,1];heat=palette(g);heat[edge]=[250,250,250]
        fig.paste(Image.fromarray(heat).resize((352,352),Image.Resampling.NEAREST),(px,531))
        draw.text((px,887),'Target median G: %.3f'%np.median(g[target]),font=font(19),fill='#111827')
    fig.paste(Image.fromarray(palette(np.linspace(0,104,352)[None,:])).resize((352,12)),(444,514))
    draw.text((40,514),'G response: 0',font=font(13),fill='#374151');draw.text((803,514),'104; white outline = frozen target',font=font(13),fill='#374151')
    path=Path(args.output);assert not path.exists();path.parent.mkdir(parents=True,exist_ok=True);fig.save(path)
    print(path)

if __name__=='__main__':main()
