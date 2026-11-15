#!/usr/bin/env python3
"""Prospective B40 geometry prediction; creates new outputs, preserves B20 files."""
import csv
import hashlib
import json
from pathlib import Path
import runpy

OUT = Path(__file__).resolve().parent
BASE = runpy.run_path(str(OUT/'geometry.py'))
MAP = BASE['mapping']
MAP.__globals__['BEVEL'] = 40.
DERIVATIVE = BASE['derivative']
EXTREMA = BASE['extrema']
XS = [32.5+.5*i for i in range(73)]
YS = [2.25+.5*j for j in range(36)]

def local_derivative(p,h):
    x,y=p
    xp,xm = MAP((x+h,y))['source'],MAP((x-h,y))['source']
    yp,ym = MAP((x,y+h))['source'],MAP((x,y-h))['source']
    a,b = (xp[0]-xm[0])/(2*h),(yp[0]-ym[0])/(2*h)
    c,d = (xp[1]-xm[1])/(2*h),(yp[1]-ym[1])/(2*h)
    return dict(dsx_dx=a,dsy_dy=d,jacobian_det=a*d-b*c)

def main():
    grid=[[MAP((x,y)) for x in XS] for y in YS]
    records=[]
    for j,y in enumerate(YS):
        for i,x in enumerate(XS):
            item=grid[j][i]
            a=DERIVATIVE([v['source'][0] for v in grid[j]],i)
            c=DERIVATIVE([v['source'][1] for v in grid[j]],i)
            b=DERIVATIVE([row[i]['source'][0] for row in grid],j)
            d=DERIVATIVE([row[i]['source'][1] for row in grid],j)
            records.append(dict(x=x,y=y,inset=item['inset'],nx=item['normal'][0],ny=item['normal'][1],dx=item['shift'][0],dy=item['shift'][1],source_x=item['source'][0],source_y=item['source'][1],dsx_dx=a,dsy_dy=d,jacobian_det=a*d-b*c))
    with (OUT/'bevel40-field.csv').open('w') as file:
        writer=csv.DictWriter(file,fieldnames=list(records[0]))
        writer.writeheader()
        for record in records:
            writer.writerow({k:f'{v:.9g}' for k,v in record.items()})
    summary=dict(method='Prospective CPU Double geometry prediction only; no image reads, native fitting, or acceptance',baseline_script_sha256=hashlib.sha256((OUT/'geometry.py').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(BASE['SOURCE'].read_bytes()).hexdigest(),shape=[320.,172.,34.],refraction=60.,bevel=40.,profile_power=1.,solver_reference_steps=70,gpu_bit_equivalence=False,grid=dict(local_x=[XS[0],XS[-1]],local_y=[YS[0],YS[-1]],step=.5,points=len(records)),derivative_method='0.5pt grid finite difference; central inside, one-sided at ROI endpoints',dx=EXTREMA([v['dx'] for v in records]),rows={},columns={},derivatives={})
    for y in [2.25,10.25,19.75]:
        row=[v for v in records if v['y']==y]
        summary['rows'][str(y)]=dict(dx=EXTREMA([v['dx'] for v in row]),dsx_dx=EXTREMA([v['dsx_dx'] for v in row]),horizontal_negative_count=sum(v['dsx_dx']<0 for v in row))
    for x in [32.5,40.,50.5,68.5]:
        col=[v for v in records if v['x']==x]
        summary['columns'][str(x)]=dict(dx=EXTREMA([v['dx'] for v in col]),dx_start_end=[col[0]['dx'],col[-1]['dx']],dx_peak_y=max(col,key=lambda v:v['dx'])['y'])
    for key in ['dsx_dx','dsy_dy','jacobian_det']:
        minimum=min(records,key=lambda v:v[key]);p=minimum['x'],minimum['y']
        summary['derivatives'][key]=dict(**EXTREMA([v[key] for v in records]),negative_count=sum(v[key]<0 for v in records),minimum_local_point=p,minimum_point_refinements={str(h):local_derivative(p,h) for h in [.1,.01]})
    (OUT/'bevel40-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__': main()
