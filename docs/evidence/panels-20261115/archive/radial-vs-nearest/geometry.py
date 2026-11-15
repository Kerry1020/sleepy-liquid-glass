#!/usr/bin/env python3
"""CPU geometry diagnostic only; no image reads, fit, runtime or device operation.

Port the existing Kotlin cubic construction using Double arithmetic, retaining
its control tables. Radial depth/normal follows signedExactGeometry. A 70-step
reference solve removes the GPU's separate 16-step/Float numerical limitation.
This is not a GPU bit-equivalence or a claim about UIKit's distance model.
"""
import csv
import hashlib
import json
import math
from pathlib import Path
import re

SOURCE = Path('/Users/kerrylee/.codex/worktrees/android-settings-glass-fixes/sleepy/libraries/liquid-glass/runtime/src/androidMain/kotlin/com/lingion/sleepy/ui/component/liquidglass/LiquidGlassSuperellipse.kt')
SHADER = SOURCE.parent.parent.parent.parent.parent.parent.parent / 'assets/shaders/liquid_glass.agsl'
OUT = Path(__file__).resolve().parent
TEXT = SOURCE.read_text()
W, H, R = 320., 172., 34.
C = (W / 2, H / 2)
REFRACTION, BEVEL = 60., 20.

def table(name):
    text = re.search(r'private val ' + name + r' = floatArrayOf\((.*?)\n    \)', TEXT, re.S).group(1)
    text = re.sub(r'//[^\n]*', '', text)
    return [float(x) for x in re.findall(r'([-+]?\d+(?:\.\d+)?)f', text)]

PRE, BEZ = table('kPrecomputedVariables'), table('kBezierFactors')
def add(a,b): return a[0]+b[0], a[1]+b[1]
def sub(a,b): return a[0]-b[0], a[1]-b[1]
def mul(a,s): return a[0]*s, a[1]*s
def dot(a,b): return a[0]*b[0]+a[1]*b[1]
def cross(a,b): return a[0]*b[1]-a[1]*b[0]
def length(a): return math.hypot(*a)
def unit(a): return mul(a, 1/length(a))

def nk(ratio):
    if ratio > 5:
        n = 1.559599389*(ratio-5)+PRE[-2]
        k = .522807185*(ratio-5)+PRE[-1]
    else:
        r = max(2,min(5,ratio))
        steps = (r-2)*10 if r < 2.5 else (r-2.5)*2+5
        left = max(0,min(9,math.floor(steps))); f = steps-left
        n = (1-f)*PRE[2*left]+f*PRE[2*left+2]
        k = (1-f)*PRE[2*left+1]+f*PRE[2*left+3]
    return n,1-1/k

def octant(a,r):
    n,x = nk(2*a/r); g = .29289321881*r
    j = x*a,(1-x**n)**(1/n)*a
    m = a-g,a-g
    tan_phi = (j[0]/j[1])**(n-1)
    d = (j[0]-tan_phi*j[1])/(1-tan_phi)
    radius = (a-d-g)*math.sqrt(2)
    ab = sub(m,j)
    center = sub(mul(add(j,m),.5),mul(unit((-ab[1],ab[0])),math.sqrt(radius**2-(length(ab)/2)**2)))
    v,e = sub(j,center),sub(m,center)
    angle = math.atan2(cross(e,v),dot(e,v))
    if n >= 15:
        factors = (1.07-math.exp(1.307649835)*n**(-.8568516731),-.01+math.exp(-.9287690322)*n**(-.6120901398))
    else:
        steps = max(0,min(13,n-2)); left = max(0,min(12,math.floor(steps))); f = steps-left
        factors = ((1-f)*BEZ[2*left]+f*BEZ[2*left+2],(1-f)*BEZ[2*left+1]+f*BEZ[2*left+3])
    se = [(0,a),(factors[0]*a,a),add(j,mul(unit((-v[1],v[0])),factors[1]*a)),j]
    ca,sa = math.cos(-angle),math.sin(-angle)
    ev = v[0]*ca-v[1]*sa,v[0]*sa+v[1]*ca
    factor = math.tan(angle/4)*4/3*length(v)
    end = add(center,ev)
    circle = [j,add(j,mul(unit((v[1],-v[0])),factor)),add(end,mul(unit((-ev[1],ev[0])),factor)),end]
    return se,circle

def make_curves():
    c = W/2-H/2
    se_t,ci_t = octant(W/2,R)
    se_r,ci_r = octant(H/2,R)
    curves = []
    # Top-left is the exact symmetry of source AddQuadrant's top-right.
    for points,off,flip,reverse in [(se_t,(0,-c),False,False),(ci_t,(0,-c),False,False),(ci_r,(c,0),True,True),(se_r,(c,0),True,True)]:
        result = []
        for p in points[::-1] if reverse else points:
            if flip: p = p[1],p[0]
            p = add(p,off)
            result.append((C[0]-p[0],C[1]-p[1]))
        curves.append(result)
    return curves

CURVES = make_curves()
def bezier(q,t):
    u=1-t
    return tuple(q[0][j]*u**3+3*q[1][j]*u*u*t+3*q[2][j]*u*t*t+q[3][j]*t**3 for j in (0,1))
def tangent(q,t):
    u=1-t
    return tuple(3*(q[1][j]-q[0][j])*u*u+6*(q[2][j]-q[1][j])*u*t+3*(q[3][j]-q[2][j])*t*t for j in (0,1))
def normal(q,t):
    b,v = bezier(q,t),tangent(q,t)
    n = unit((v[1],-v[0]))
    return mul(n,-1) if dot(n,sub(b,C)) < 0 else n

def radial(p,steps=70):
    ray=unit(sub(p,C)); candidates=[]
    for index,q in enumerate(CURVES):
        f=lambda t:cross(sub(bezier(q,t),C),ray)
        low,high=0.,1.; fl,fh=f(low),f(high)
        if abs(fl)<1e-10: t=0.
        elif abs(fh)<1e-10: t=1.
        elif fl*fh>0: continue
        else:
            for _ in range(steps):
                middle=(low+high)/2; fm=f(middle)
                if fm*fl>0: low=middle; fl=fm
                else: high=middle
            t=(low+high)/2
        b,n=bezier(q,t),normal(q,t)
        candidates.append(dict(segment=index,t=t,boundary=b,normal=n,inset=dot(sub(b,p),n)))
    assert len(candidates)==1, (p,candidates)
    return candidates[0]

def nearest(p):
    candidates=[]
    for index,q in enumerate(CURVES):
        f=lambda t:dot(sub(bezier(q,t),p),sub(bezier(q,t),p))
        k=min(range(1025),key=lambda i:f(i/1024))
        low,high=max(0,(k-1)/1024),min(1,(k+1)/1024)
        for _ in range(90):
            a=low+(high-low)*.3819660112501051; b=low+(high-low)*.6180339887498949
            if f(a)<f(b): high=b
            else: low=a
        t=(low+high)/2
        candidates.append(dict(segment=index,t=t,boundary=bezier(q,t),normal=normal(q,t),inset=math.sqrt(f(t))))
    return min(candidates,key=lambda result:result['inset'])

def mapping(p,power=1.,geometry=None):
    g=radial(p) if geometry is None else geometry
    rise=1-max(0,min(g['inset']/BEVEL,1))
    profile=1-math.sqrt(max(0,1-rise*rise))
    depth=REFRACTION*profile**power
    shift=mul(g['normal'],-depth)
    return dict(shift=shift,source=add(p,shift),depth=depth,**g)

def points():
    result=[]
    for p in [(32.5,2.25),(40.,10.)]:
        r,n=radial(p),nearest(p)
        result.append(dict(point=p,radial=mapping(p,geometry=r),nearest=mapping(p,geometry=n),direction_difference_degrees=math.degrees(math.acos(max(-1,min(1,dot(r['normal'],n['normal'])))))))
    return result

def derivative(values,index,step=.5):
    if index==0: return (values[1]-values[0])/step
    if index==len(values)-1: return (values[-1]-values[-2])/step
    return (values[index+1]-values[index-1])/(2*step)

def extrema(values): return dict(min=min(values),max=max(values),span=max(values)-min(values))

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'two-points.json').write_text(json.dumps(points(),indent=2)+'\n')
    xs=[32.5+.5*i for i in range(73)]
    ys=[2.25+.5*j for j in range(36)]
    geometries=[[radial((x,y)) for x in xs] for y in ys]
    summary=dict(method='CPU Double geometry only; no images, native fitting, or acceptance',source=str(SOURCE),source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),shape=dict(width=W,height=H,radius=R,top_left_cubics=CURVES),refraction=REFRACTION,bevel=BEVEL,radial_solver_steps=70,gpu_solver_steps=16,gpu_bit_equivalence=False,world_origin=[27.5,257.5],grid=dict(local_x=[xs[0],xs[-1]],local_y=[ys[0],ys[-1]],step=.5,points_per_power=len(xs)*len(ys)),powers={})
    fields=['power','x','y','world_x','world_y','inset','nx','ny','dx','dy','source_x','source_y','dsx_dx','dsy_dy','jacobian_det']
    with (OUT/'point-shift-field.csv').open('w') as file:
        writer=csv.DictWriter(file,fieldnames=fields);writer.writeheader()
        for power in [1.,.5,2.]:
            grid=[[mapping((x,y),power,geometries[j][i]) for i,x in enumerate(xs)] for j,y in enumerate(ys)]
            derivatives=[]
            for j,y in enumerate(ys):
                for i,x in enumerate(xs):
                    item=grid[j][i]
                    dsx_dx=derivative([a['source'][0] for a in grid[j]],i)
                    dsy_dx=derivative([a['source'][1] for a in grid[j]],i)
                    dsx_dy=derivative([a[i]['source'][0] for a in grid],j)
                    dsy_dy=derivative([a[i]['source'][1] for a in grid],j)
                    det=dsx_dx*dsy_dy-dsx_dy*dsy_dx
                    derivatives.append((dsx_dx,dsy_dy,det))
                    values=[power,x,y,x+27.5,y+257.5,item['inset'],*item['normal'],*item['shift'],*item['source'],dsx_dx,dsy_dy,det]
                    writer.writerow(dict(zip(fields,[f'{v:.9g}' for v in values])))
            flat=[a for row in grid for a in row]
            rows={}
            for y in [2.25,10.25,19.75]:
                j=ys.index(y); row=grid[j]; slopes=[derivative([a['source'][0] for a in row],i) for i in range(len(xs))]
                rows[str(y)]=dict(dx=extrema([a['shift'][0] for a in row]),dsx_dx=extrema(slopes),horizontal_negative_count=sum(s<0 for s in slopes))
            columns={}
            for x in [32.5,40.,50.5,68.5]:
                i=xs.index(x); col=[row[i] for row in grid]
                columns[str(x)]=dict(dx=extrema([a['shift'][0] for a in col]),dy=extrema([a['shift'][1] for a in col]),dx_at_y_start_end=[col[0]['shift'][0],col[-1]['shift'][0]],dx_peak_y=ys[max(range(len(ys)),key=lambda j:col[j]['shift'][0])])
            summary['powers'][str(power)]=dict(dx=extrema([a['shift'][0] for a in flat]),rows=rows,columns=columns,dsx_dx=extrema([a[0] for a in derivatives]),dsy_dy=extrema([a[1] for a in derivatives]),jacobian_det=extrema([a[2] for a in derivatives]),negative_counts=dict(dsx_dx=sum(a[0]<0 for a in derivatives),dsy_dy=sum(a[1]<0 for a in derivatives),jacobian_det=sum(a[2]<0 for a in derivatives)))
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__': main()
