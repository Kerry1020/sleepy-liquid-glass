#!/usr/bin/env python3
"""Known-source dot tracking. NumPy/Pillow only; no nearest-neighbor assignment.

Freeze/self-test before opening actual captures. Each source identity is retained,
including weak, hidden, overlapping, ambiguous and multiply imaged dots.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import math
import platform
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageCms, features, __version__ as PILLOW_VERSION

LITTLECMS_VERSION = features.version_module('littlecms2')

HERE = Path(__file__).resolve().parent
FREEZE = HERE / 'frozen-tracker-v2.json'
PROTOCOL = HERE / 'tracking-protocol-v2.json'
PARAMS = {
    'schema': 2, 'implementation_version': 2, 'world_px': [750,1334], 'pixels_per_pt': 2,
    'dock_ltrb_px': [42,1168,708,1292],
    'near_dock_distance_px': 160, 'near_search_radius_px': 160, 'far_search_radius_px': 8,
    'template_blur_sigmas_px': [0,2,6], 'template_radius_rule': 'ceil(max(9,2*radius+6)+2*sigma)',
    'minimum_template_sd_code': 1.5, 'minimum_ncc': .60, 'minimum_peak_margin': .08,
    'minimum_color_ncc': .40, 'minimum_context_ncc': .40,
    'minimum_context_sd_code': 1.0, 'maximum_retained_peaks': 3,
    'distinct_peak_radius_rule': 'max(4,2*source_radius)',
    'minimum_local_snr': 3, 'minimum_local_contrast_code': 2.0,
    'segmentation_peak_fractions': [.25,.50,.75],
    'morphology_primary_fraction': .50, 'minimum_component_pixels': 2,
    'shape_radius_rule': 'ceil(max(8,3*radius+3*sigma+4))',
    'identity_competition_radius_px': 2.0, 'maximum_returned_centroid_shift_rule': 'max(5,2*radius+2*sigma)',
    'identity_competition_support_rule': 'reject any shared observed component pixel; retain overlap counts and centroid fallback',
    'foreground_occlusion_rule': 'correlation center or any primary-component pixel cell intersects fixed foreground rectangles',
    'template_foreground_rule': 'record full template rectangle intersection; diagnostic only, not an automatic rejection',
    'effective_search_boundary_margin_px': 1,
    'color_policy': 'profiled RGB converted to sRGB through frozen LittleCMS; unprofiled inputs explicitly assumed sRGB; nonopaque alpha rejected',
    'maximum_components_per_peak': 4,
    'saturation_channel_limits_code': [1,254], 'maximum_component_saturated_fraction': .05,
    'foreground_rects_pt': [[48,592,91,640],[127,592,170,640],[207,592,250,640],[286,592,329,640]],
    'selected_lens_layer_rect_pt': [25,588,113.25,642],
    'background_foreground_context_rect_pt': [16,593.2,180,613.7],
    'status_semantics': {
        'tracked': 'unique translation-template identity and isolated visible component; conditional measurement, not proof of physical correspondence',
        'multiple_lobes': 'multiple separated candidates pass NCC/color/contrast checks; no forced single displacement',
        'fused': 'source overlap or multiple source identities compete for the same observed component',
        'disappeared': 'reserved, never emitted by v2: retained NCC candidates cannot establish absence across a full search',
        'unidentified': 'signal exists but identity, shape, search-boundary or local translation assumptions are insufficient',
        'outside_support': 'source more than160px from Dock; local8px control search only; no inference about Dock refraction',
    },
    'no_actual_output_read_before_freeze': True,
}


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write_json(path, value): Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def serial(value):
    if isinstance(value, np.generic): return value.item()
    if isinstance(value, dict): return {k:serial(v) for k,v in value.items()}
    if isinstance(value, (tuple,list)): return [serial(v) for v in value]
    return value


def blur(rgb, sigma):
    if not sigma: return rgb
    im = Image.fromarray(np.uint8(np.clip(np.rint(rgb),0,255)))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(float(sigma))),dtype=float)


def load_rgb(path,return_info=False):
    with Image.open(path) as original:
        profile=original.info.get('icc_profile')
        if 'A' in original.getbands() or 'transparency' in original.info:
            if original.convert('RGBA').getchannel('A').getextrema()!=(255,255):
                raise ValueError('Nonopaque alpha input rejected; no implicit compositing or alpha dropping')
        info={'original_mode':original.mode,'dimensions_px':list(original.size),
            'icc_profile_sha256':hashlib.sha256(profile).hexdigest() if profile else None,
            'unprofiled_assumed_srgb':not bool(profile),'output_color_space':'sRGB',
            'alpha_policy':'nonopaque alpha rejected','littlecms2':LITTLECMS_VERSION}
        if profile:
            image=ImageCms.profileToProfile(original.convert('RGB'),ImageCms.ImageCmsProfile(io.BytesIO(profile)),
                                           ImageCms.createProfile('sRGB'),outputMode='RGB')
        else:image=original.convert('RGB')
        array=np.asarray(image,dtype=float)
    return (array,info) if return_info else array


def crop_template(image, x, y, radius):
    # Source coordinates are continuous edge-origin coordinates; pixel i center=i+.5.
    ix,iy=int(round(x-.5)),int(round(y-.5))
    if ix-radius<0 or iy-radius<0 or ix+radius>=image.shape[1] or iy+radius>=image.shape[0]: return None
    return image[iy-radius:iy+radius+1,ix-radius:ix+radius+1], (ix+.5,iy+.5)


def boxsum(a, height, width):
    b=np.pad(np.cumsum(np.cumsum(a,axis=0),axis=1),((1,0),(1,0)))
    return b[height:,width:]-b[:-height,width:]-b[height:,:-width]+b[:-height,:-width]


def ncc_valid(image, template):
    """All valid translations, zero mean and energy normalization, FFT numerator.

    Pearson correlation is a correspondence diagnostic, never a parity score.
    """
    h,w=template.shape
    t=template-template.mean(); energy=float(np.sum(t*t))
    if energy<1e-9: return np.full((image.shape[0]-h+1,image.shape[1]-w+1),-1.)
    shape=tuple(1<<(int(v)-1).bit_length() for v in (image.shape[0]+h-1,image.shape[1]+w-1))
    full=np.fft.irfft2(np.fft.rfft2(image,s=shape)*np.fft.rfft2(t[::-1,::-1],s=shape),s=shape)
    numerator=full[h-1:image.shape[0],w-1:image.shape[1]]
    sums=boxsum(image,h,w);sq=boxsum(image*image,h,w)
    denominator=np.sqrt(np.maximum(sq-sums*sums/(h*w),0)*energy)
    return np.clip(np.divide(numerator,denominator,out=np.full_like(numerator,-1.),where=denominator>1e-8),-1,1)


def color_ncc(a,b, mask=None):
    aa=a.reshape(-1,3);bb=b.reshape(-1,3)
    if mask is not None: aa=aa[mask.ravel()];bb=bb[mask.ravel()]
    if len(aa)<3:return None
    aa=aa-aa.mean(axis=0);bb=bb-bb.mean(axis=0)
    denominator=np.linalg.norm(aa)*np.linalg.norm(bb)
    return float(np.sum(aa*bb)/denominator) if denominator>1e-8 else None


def connected(mask):
    """Eight-neighbor components; local windows only, no external libraries."""
    seen=np.zeros(mask.shape,bool);components=[]
    for y,x in np.argwhere(mask):
        if seen[y,x]:continue
        stack=[(int(y),int(x))];seen[y,x]=True;pixels=[]
        while stack:
            yy,xx=stack.pop();pixels.append((yy,xx))
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    ny,nx=yy+dy,xx+dx
                    if 0<=ny<mask.shape[0] and 0<=nx<mask.shape[1] and mask[ny,nx] and not seen[ny,nx]:
                        seen[ny,nx]=True;stack.append((ny,nx))
        components.append(np.asarray(pixels,dtype=int))
    return components


def component_geometry(pixels,weights,origin):
    y,x=pixels[:,0],pixels[:,1];w=np.maximum(weights[y,x],0)
    if w.sum()<=0:w=np.ones(len(x))
    xy=np.column_stack([x+origin[0]+.5,y+origin[1]+.5]);center=np.sum(xy*w[:,None],axis=0)/w.sum()
    d=xy-center;cov=(d*w[:,None]).T@d/w.sum()
    eig,vec=np.linalg.eigh(cov);eig=np.maximum(eig,0);v=vec[:,-1]
    return {'center_px':center.tolist(),'area_px2':int(len(x)),
        'moment_major_axis_px':float(4*np.sqrt(eig[-1])), 'moment_minor_axis_px':float(4*np.sqrt(eig[0])),
        'moment_axis_angle_deg':float(np.degrees(np.arctan2(v[1],v[0]))%180),
        'axis_definition':'4*sqrt(weighted covariance eigenvalue); not fitted physical ellipse or unblurred size',
        'bbox_ltrb_px':[int(x.min()+origin[0]),int(y.min()+origin[1]),int(x.max()+origin[0]+1),int(y.max()+origin[1]+1)],
        'pixel_support_rle_y_xstart_xstop':component_support_spans(pixels,origin)}


def component_support_spans(pixels,origin):
    """Lossless actual component support; global pixel indices, exclusive x-stop."""
    ordered=pixels[np.lexsort((pixels[:,1],pixels[:,0]))];spans=[]
    for yy,xx in ordered:
        y,x=int(yy+origin[1]),int(xx+origin[0])
        if spans and spans[-1][0]==y and spans[-1][2]==x:spans[-1][2]=x+1
        else:spans.append([y,x,x+1])
    return spans


def support_rect_overlap_pixels(spans,rect):
    """Count component pixel cells that intersect a half-open geometric rectangle."""
    left,top,right,bottom=rect;count=0
    for y,start,stop in spans:
        if y+1<=top or y>=bottom:continue
        count+=max(0,min(stop,math.ceil(right))-max(start,math.floor(left)))
    return count


def component_support_overlap_pixels(a,b):
    """Exact pixel intersection, not bounding-box or centroid identity matching."""
    al,at,ar,ab=a['bbox_ltrb_px'];bl,bt,br,bb=b['bbox_ltrb_px']
    if ar<=bl or br<=al or ab<=bt or bb<=at:return 0
    aa=a['pixel_support_rle_y_xstart_xstop'];ba=b['pixel_support_rle_y_xstart_xstop']
    i=j=count=0
    while i<len(aa) and j<len(ba):
        ay,al,ar=aa[i];by,bl,br=ba[j]
        if ay<by:i+=1;continue
        if by<ay:j+=1;continue
        count+=max(0,min(ar,br)-max(al,bl))
        if ar<=br:i+=1
        else:j+=1
    return count


def local_shape(observed,point,center,sigma,direction):
    radius=float(point['radius_px']);r=int(math.ceil(max(8,3*radius+3*sigma+4)))
    x,y=center;ix,iy=int(round(x-.5)),int(round(y-.5))
    l,t,rr,b=max(0,ix-r),max(0,iy-r),min(observed.shape[1],ix+r+1),min(observed.shape[0],iy+r+1)
    patch=observed[t:b,l:rr];yy,xx=np.mgrid[:patch.shape[0],:patch.shape[1]]
    distance=np.hypot(xx+l+.5-x,yy+t+.5-y)
    outer=(distance>=r*.75)&(distance<=r)
    if outer.sum()<8:return {'valid':False,'reason':'clipped_shape_window'}
    background=np.median(patch[outer],axis=0);projection=np.sum((patch-background)*direction,axis=-1)
    noise=float(1.4826*np.median(np.abs(projection[outer]-np.median(projection[outer]))))
    support=distance<=max(3,radius*2+sigma*2)
    peak=float(projection[support].max());snr=peak/max(noise,.5)
    result={'valid':False,'background_rgb':background.tolist(),'projected_peak_contrast_code':peak,
        'local_noise_mad_code':noise,'local_snr':snr,'segmentation':[]}
    if peak<max(PARAMS['minimum_local_contrast_code'],PARAMS['minimum_local_snr']*max(noise,.5)):
        result['reason']='weak_local_contrast';return result
    maximum_center_shift=max(5,2*radius+2*sigma)
    for fraction in PARAMS['segmentation_peak_fractions']:
        threshold=max(fraction*peak,2*noise,1.)
        candidates=[]
        for pixels in connected((projection>=threshold)&(distance<r)):
            if len(pixels)<PARAMS['minimum_component_pixels']:continue
            row=component_geometry(pixels,projection,(l,t))
            row['distance_from_correlation_center_px']=float(np.linalg.norm(np.asarray(row['center_px'])-center))
            if row['distance_from_correlation_center_px']>maximum_center_shift:continue
            vals=patch[pixels[:,0],pixels[:,1]];row['mean_rgb']=vals.mean(axis=0).tolist()
            row['contrast_rgb']=(vals.mean(axis=0)-background).tolist();row['threshold_code']=threshold
            row['touches_measurement_window']=bool(np.any(distance[pixels[:,0],pixels[:,1]]>=r-1))
            candidates.append(row)
        candidates.sort(key=lambda q:q['area_px2'],reverse=True)
        result['segmentation'].append({'peak_fraction':fraction,'components':candidates[:PARAMS['maximum_components_per_peak']],
                                       'total_components':len(candidates)})
    primary=result['segmentation'][1]['components']
    if not primary:result['reason']='no_connected_component';return result
    if len(primary)>1:result['reason']='multiple_components_inside_identity_patch';return result
    if primary[0]['touches_measurement_window']:result['reason']='component_truncated';return result
    result.update(valid=True,primary=primary[0]);return result


def near_dock(x,y):
    l,t,r,b=PARAMS['dock_ltrb_px'];d=PARAMS['near_dock_distance_px']
    return l-d<=x<=r+d and t-d<=y<=b+d


def in_rect(x,y,rect):return rect[0]<=x<rect[2] and rect[1]<=y<rect[3]


def rect_intersection_area(a,b):
    return max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))


def layer_at(center):
    x,y=center;px,py=x/2,y/2
    if not in_rect(x,y,PARAMS['dock_ltrb_px']):return 'outside_dock'
    if in_rect(px,py,PARAMS['selected_lens_layer_rect_pt']):return 'selected_lens_layer'
    return 'dock_base_nominal_bounds'


def annotate_candidate(p,observed):
    center=p['correlation_center_px'];x,y=center;p['layer']=layer_at(center)
    p['foreground_center_in_mask']=any(in_rect(x/2,y/2,r) for r in PARAMS['foreground_rects_pt'])
    p['foreground_component_intersection_pixels']=0
    if p['shape'].get('primary'):
        spans=p['shape']['primary']['pixel_support_rle_y_xstart_xstop']
        # Masks are disjoint; count once per rectangle and retain the exact support.
        p['foreground_component_intersection_pixels']=sum(support_rect_overlap_pixels(spans,[v*2 for v in rect])
            for rect in PARAMS['foreground_rects_pt'])
        p['foreground_component_intersection_fraction']=p['foreground_component_intersection_pixels']/p['shape']['primary']['area_px2']
    p['foreground_occlusion_risk']=bool(p['foreground_center_in_mask'] or p['foreground_component_intersection_pixels'])
    if p.get('template_bounds_ltrb_px'):
        bounds=p['template_bounds_ltrb_px'];area=(bounds[2]-bounds[0])*(bounds[3]-bounds[1])
        p['template_foreground_intersection_area_px2']=sum(rect_intersection_area(bounds,[v*2 for v in rect])
            for rect in PARAMS['foreground_rects_pt'])
        p['template_foreground_intersection_fraction']=p['template_foreground_intersection_area_px2']/area
        p['template_background_foreground_context_area_px2']=rect_intersection_area(bounds,
            [v*2 for v in PARAMS['background_foreground_context_rect_pt']])
    p['background_foreground_context']=in_rect(x/2,y/2,PARAMS['background_foreground_context_rect_pt'])
    if p['shape'].get('primary'):
        box=p['shape']['primary']['bbox_ltrb_px'];l,t,r,b=box;patch=observed[t:b,l:r]
        p['saturated_fraction_in_component_bbox']=float(np.mean(np.any((patch<=1)|(patch>=254),axis=-1)))
        saturated=sum(int(np.any((observed[y,start:stop]<=1)|(observed[y,start:stop]>=254),axis=-1).sum())
            for y,start,stop in p['shape']['primary']['pixel_support_rle_y_xstart_xstop'])
        p['saturated_fraction_in_component_pixels']=saturated/p['shape']['primary']['area_px2']
    else:
        p['saturated_fraction_in_component_bbox']=None;p['saturated_fraction_in_component_pixels']=None


def track_one(source, observed, point, blurred_sources):
    x,y=float(point['source_x_px']),float(point['source_y_px']);radius=float(point['radius_px'])
    row={'id':point['id'],'source_center_px':[x,y],'source_center_pt':[x/2,y/2],
         'source_radius_px':radius,'source_rgb':point['rgb'],'source_polarity':point.get('polarity'),
         'draw_order':point.get('draw_order'),'source_overlap_ids':point.get('overlapping_dot_ids',[]),
         'source_occluding_later_ids':point.get('occluding_later_dot_ids',[]),
         'edge_clipped':point.get('edge_clipped',False),'status':'unidentified','reasons':[], 'candidates':[]}
    if row['edge_clipped']:row['reasons'].append('source_edge_clipped');return row
    direction=np.asarray(point['rgb'],float)-128
    if np.linalg.norm(direction)<2:row['reasons'].append('source_color_has_no_reference_contrast');return row
    direction/=np.linalg.norm(direction)
    search=PARAMS['near_search_radius_px'] if near_dock(x,y) else PARAMS['far_search_radius_px']
    row['search_radius_px']=search
    ix,iy=int(round(x-.5)),int(round(y-.5));possible=[];template_sds=[]
    for sigma in PARAMS['template_blur_sigmas_px']:
        r=int(math.ceil(max(9,2*radius+6)+2*sigma))
        got=crop_template(blurred_sources[sigma],x,y,r)
        if got is None:continue
        template,anchor=got;projected=np.sum(template*direction,axis=-1)
        sd=float(projected.std());template_sds.append(sd)
        if sd<PARAMS['minimum_template_sd_code']:continue
        l,t=max(r,ix-search)-r,max(r,iy-search)-r
        rr,b=min(observed.shape[1]-r-1,ix+search)+r+1,min(observed.shape[0]-r-1,iy+search)+r+1
        field=np.sum(observed[t:b,l:rr]*direction,axis=-1)
        scores=ncc_valid(field,projected)
        effective_bounds=[float(l+r+.5),float(t+r+.5),float(rr-r-.5),float(b-r-.5)]
        for _ in range(PARAMS['maximum_retained_peaks']):
            py,px=np.unravel_index(np.argmax(scores),scores.shape);score=float(scores[py,px])
            if score<0:break
            center=(float(l+px+r+.5),float(t+py+r+.5))
            patch=observed[t+py:t+py+2*r+1,l+px:l+px+2*r+1]
            color=color_ncc(template,patch)
            yy,xx=np.mgrid[:2*r+1,:2*r+1];annulus=np.hypot(xx-r,yy-r)>max(3,1.5*radius+sigma)
            context=color_ncc(template,patch,annulus)
            possible.append({'ncc':score,'color_ncc':color,'context_ncc':context,'template_blur_sigma_px':sigma,
                             'source_context_sd_code':float(np.std(template[annulus],axis=0).mean()),
                             'correlation_center_px':list(center),'template_center_px':list(anchor),
                             'template_bounds_ltrb_px':[int(l+px),int(t+py),int(l+px+2*r+1),int(t+py+2*r+1)],
                             'effective_search_center_bounds_xyxy_inclusive_px':effective_bounds,
                             'correlation_score_shape_yx':list(scores.shape),'correlation_peak_index_xy':[int(px),int(py)],
                             'nominal_search_boundary':abs(center[0]-anchor[0])>=search-1 or abs(center[1]-anchor[1])>=search-1,
                             'effective_search_boundary':bool(px<=PARAMS['effective_search_boundary_margin_px'] or
                                 py<=PARAMS['effective_search_boundary_margin_px'] or
                                 px>=scores.shape[1]-1-PARAMS['effective_search_boundary_margin_px'] or
                                 py>=scores.shape[0]-1-PARAMS['effective_search_boundary_margin_px'])})
            possible[-1]['search_boundary']=possible[-1]['nominal_search_boundary'] or possible[-1]['effective_search_boundary']
            yy,xx=np.mgrid[:scores.shape[0],:scores.shape[1]]
            scores[np.hypot(xx-px,yy-py)<max(4,2*radius)]=-1
    row['template_sd_code_by_available_scale']=template_sds
    possible.sort(key=lambda p:p['ncc'],reverse=True);peaks=[]
    for p in possible:
        if all(np.linalg.norm(np.asarray(p['correlation_center_px'])-q['correlation_center_px'])>=max(4,2*radius) for q in peaks):
            peaks.append(p)
        if len(peaks)>=PARAMS['maximum_retained_peaks']:break
    if not peaks:row['reasons'].append('insufficient_source_template_excitation');return row
    for p in peaks:
        p['shape']=local_shape(observed,point,p['correlation_center_px'],p['template_blur_sigma_px'],direction)
        annotate_candidate(p,observed)
        if p['shape'].get('primary'):
            p['dx_dy_from_ideal_source_px']=(np.asarray(p['shape']['primary']['center_px'])-[x,y]).tolist()
        p['identity_eligible']=bool(p['ncc']>=PARAMS['minimum_ncc'] and p['color_ncc'] is not None and p['color_ncc']>=PARAMS['minimum_color_ncc'] and p['context_ncc'] is not None and p['context_ncc']>=PARAMS['minimum_context_ncc'] and p['source_context_sd_code']>=PARAMS['minimum_context_sd_code'] and p['shape']['valid'] and not p['search_boundary'] and not p['foreground_occlusion_risk'] and (p['saturated_fraction_in_component_pixels'] or 0)<=PARAMS['maximum_component_saturated_fraction'])
    row['candidates']=peaks
    best=peaks[0];second=peaks[1]['ncc'] if len(peaks)>1 else -1
    row['ncc_peak_margin']=best['ncc']-second
    eligible=[p for p in peaks if p['identity_eligible']]
    if len(eligible)>1:
        row['status']='multiple_lobes';row['reasons'].append('multiple_source_patch_correspondences');return row
    if not eligible:
        if all(not p['shape']['valid'] and p['shape'].get('reason')=='weak_local_contrast' for p in peaks):
            row['reasons'].append('retained_candidates_weak_not_full_search_absence')
        else:row['reasons'].append('correspondence_or_component_checks_failed')
        return row
    chosen=eligible[0]
    if chosen is not best or row['ncc_peak_margin']<PARAMS['minimum_peak_margin']:
        row['reasons'].append('ambiguous_template_peak');return row
    if row['source_overlap_ids']:
        row['status']='fused';row['reasons'].append('source_was_overlapped_no_independent_dot_identity');return row
    row['status']='tracked' if near_dock(x,y) else 'outside_support'
    chosen['selected_for_measurement']=True
    row['measurement_layer']=chosen['layer'];shape=chosen['shape']['primary'];center=np.asarray(shape['center_px']);displacement=center-[x,y]
    row.update(observed_center_px=center.tolist(),observed_center_pt=(center/2).tolist(),dx_dy_px=displacement.tolist(),dx_dy_pt=(displacement/2).tolist(),
               morphology=shape,confidence={'interpretation':'engineering diagnostics, not calibrated probability',
                 'ncc':chosen['ncc'],'peak_margin':row['ncc_peak_margin'],'local_snr':chosen['shape']['local_snr']})
    reference=local_shape(source,point,[x,y],0,direction)
    row['observable_source_reference_shape']=reference
    if reference.get('primary'):
        row['dx_dy_vs_observable_source_centroid_px']=(center-np.asarray(reference['primary']['center_px'])).tolist()
    return row


def reject_identity_competition(rows):
    # Identity competition is a rejection gate, never a nearest-neighbor match.
    good=[i for i,r in enumerate(rows) if r['status'] in ('tracked','outside_support')]
    for a,i in enumerate(good):
        for j in good[a+1:]:
            p,q=rows[i],rows[j]
            distance=float(np.linalg.norm(np.asarray(p['observed_center_px'])-q['observed_center_px']))
            overlap=component_support_overlap_pixels(p['morphology'],q['morphology'])
            if overlap>0 or distance<=PARAMS['identity_competition_radius_px']:
                for row,other in [(p,q),(q,p)]:
                    row['status']='fused'
                    reason='multiple_source_identities_share_observed_component_pixels' if overlap else 'multiple_source_identities_compete_for_observed_center'
                    if reason not in row['reasons']:row['reasons'].append(reason)
                    row.setdefault('competing_source_ids',[]).append(other['id'])
                    row.setdefault('identity_competition_diagnostics',[]).append({'other_id':other['id'],
                        'shared_component_pixels':overlap,'center_distance_px':distance})
    for row in rows:
        if row['status']=='fused' and row.get('observed_center_px'):
            # Preserve the rejected diagnostic in JSON, but expose no accepted measurement.
            keys=['observed_center_px','observed_center_pt','dx_dy_px','dx_dy_pt','morphology','confidence',
                  'measurement_layer','dx_dy_vs_observable_source_centroid_px']
            row['rejected_measurement']={key:row.pop(key) for key in keys if key in row}
    return rows


def track(source,observed,points):
    blurred={sigma:blur(source,sigma) for sigma in PARAMS['template_blur_sigmas_px']}
    rows=reject_identity_competition([track_one(source,observed,p,blurred) for p in points])
    for row in rows:
        if not near_dock(*row['source_center_px']):
            row['control_status']=row['status'];row['status']='outside_support'
    return rows


def fixture():
    """Only synthetic known truth; deliberately includes blur and false matches."""
    rng=np.random.default_rng(80931812);size=(240,180);im=Image.new('RGB',size,(128,128,128));draw=ImageDraw.Draw(im);points=[]
    for i,(x,y) in enumerate([(35,35),(90,35),(155,35),(35,100),(100,100),(165,110)]):
        radius=[1.5,4,10][i%3];rgb=rng.integers(20,235,3).tolist()
        point={'id':f'synthetic_{i}','source_x_px':x+.3,'source_y_px':y+.2,'radius_px':radius,'rgb':rgb,
               'edge_clipped':False,'overlapping_dot_ids':[],'draw_order':i}
        points.append(point);draw.ellipse((x-radius,y-radius,x+radius,y+radius),fill=tuple(rgb))
        for k in range(8):
            dx,dy=rng.integers(-18,19,2);rr=1
            draw.ellipse((x+dx-rr,y+dy-rr,x+dx+rr,y+dy+rr),fill=tuple(rng.integers(15,240,3)))
    return np.asarray(im,dtype=float),points


def v2_gate_tests():
    """Regression counterexamples constructed in memory; never load captured output."""
    def source_with_context(x,y,seed):
        rng=np.random.default_rng(seed);image=np.full((1334,750,3),128.)
        image[y-4:y+5,x-4:x+5]=[24,24,24]
        for dx,dy in [(-10,-10),(10,-10),(-11,9),(10,11),(0,-12)]:
            image[y+dy-1:y+dy+2,x+dx-1:x+dx+2]=rng.integers(20,235,3)
        point={'id':'synthetic_gate','source_x_px':x+.5,'source_y_px':y+.5,
            'radius_px':4,'rgb':[24,24,24],'overlapping_dot_ids':[],'edge_clipped':False}
        return image,point
    source,point=source_with_context(350,1050,122);observed=np.full_like(source,128.)
    for dx in [-70,0,70]:observed[950:991,330+dx:371+dx]=128+(source[1030:1071,330:371]-128)*.005
    observed[1100:1130,348:353]=[24,24,24]
    weak=track(source,observed,[point])[0]
    assert weak['status']=='unidentified' and 'retained_candidates_weak_not_full_search_absence' in weak['reasons'],weak['status']
    source,point=source_with_context(102,1050,433);observed=np.full_like(source,128.)
    observed[:,:-88]=source[:,88:]
    boundary=track(source,observed,[point])[0];best=boundary['candidates'][0]
    assert best['effective_search_boundary'] and best['search_boundary'] and boundary['status']!='tracked'
    observed=np.full((1334,750,3),128.);observed[1192:1208,176:192]=[232,232,232]
    shape=local_shape(observed,{'radius_px':10,'rgb':[232,232,232]},[184,1200],0,np.ones(3)/np.sqrt(3))
    candidate={'correlation_center_px':[184,1200],'shape':shape,'template_bounds_ltrb_px':[160,1180,210,1220]}
    annotate_candidate(candidate,observed)
    assert not candidate['foreground_center_in_mask'] and candidate['foreground_component_intersection_pixels']==96
    assert candidate['foreground_occlusion_risk']
    assert candidate['template_foreground_intersection_area_px2']==792
    observed=np.full((1334,750,3),128.)
    observed[1046:1054,340:350]=[190,20,160];observed[1046:1054,350:360]=[160,20,190]
    fused=[]
    for i,rgb in enumerate([[232,48,48],[48,48,232]]):
        direction=np.asarray(rgb,float)-128;direction/=np.linalg.norm(direction)
        shape=local_shape(observed,{'radius_px':10,'rgb':rgb},[350,1050],0,direction)
        assert shape['valid'];primary=shape['primary']
        fused.append({'id':'shared_support_'+str(i),'status':'tracked','reasons':[],
            'observed_center_px':primary['center_px'],'morphology':primary})
    distance=float(np.linalg.norm(np.asarray(fused[0]['observed_center_px'])-fused[1]['observed_center_px']))
    overlap=component_support_overlap_pixels(fused[0]['morphology'],fused[1]['morphology'])
    assert distance>PARAMS['identity_competition_radius_px'] and overlap==160
    reject_identity_competition(fused)
    assert all(row['status']=='fused' and not row.get('observed_center_px') and row.get('rejected_measurement') for row in fused)
    # Overlapping bounding boxes alone do not imply shared component pixels.
    a=np.array([[y,0] for y in range(5)]+[[4,x] for x in range(1,5)])
    b=np.array([[y,x] for y in range(2) for x in range(3,5)])
    disjoint=[]
    for i,pixels in enumerate([a,b]):
        primary=component_geometry(pixels,np.ones((5,5)),(0,0))
        disjoint.append({'id':'disjoint_'+str(i),'status':'tracked','reasons':[],
            'observed_center_px':primary['center_px'],'morphology':primary})
    assert component_support_overlap_pixels(disjoint[0]['morphology'],disjoint[1]['morphology'])==0
    reject_identity_competition(disjoint);assert all(row['status']=='tracked' for row in disjoint)
    # Only registered source files are opened here, never any native/Android captures.
    source_path=HERE.parent/'test/n05_dots_s0.png';points_path=HERE.parent/'test/n05_dots_s0.points.json'
    metadata,points,preflight=source_preflight(source_path,points_path)
    rejected=0
    for bad in [dict(metadata,schema=99),dict(metadata,point_count=len(points)-1),
                dict(metadata,coordinate_system=dict(metadata['coordinate_system'],origin='pixel centers')),
                dict(metadata,dots=[dict(points[0],source_x_pt=points[0]['source_x_pt']+.5)]+points[1:]),
                dict(metadata,dots=[dict(points[0],seed=-1)]+points[1:])]:
        try:validate_point_contract(bad)
        except ValueError:rejected+=1
    assert rejected==5
    try:source_preflight(HERE.parent/'test/n06_dots_s1.png',points_path)
    except ValueError as error:
        assert str(error)=='Original shared PNG hash mismatch';wrong_source_rejected=True
    else:raise AssertionError('Wrong source accepted')
    with tempfile.TemporaryDirectory(prefix='glass-tracker-color-selftest-') as temporary:
        rgba_path=Path(temporary)/'synthetic-rgba.png'
        Image.new('RGBA',(3,3),(128,64,192,128)).save(rgba_path)
        try:load_rgb(rgba_path)
        except ValueError:nonopaque_rejected=True
        else:raise AssertionError('Nonopaque input was silently flattened')
        Image.new('RGBA',(3,3),(128,64,192,255)).save(rgba_path)
        color,info=load_rgb(rgba_path,return_info=True)
        assert info['unprofiled_assumed_srgb'] and np.all(color==[128,64,192])
    color,source_color=load_rgb(source_path,return_info=True)
    assert not source_color['unprofiled_assumed_srgb'] and source_color['littlecms2']==LITTLECMS_VERSION
    return {'weak_candidates_remain':weak['status'],'clamped_peak_boundary':best['correlation_center_px'],
        'foreground_overlap_pixels':candidate['foreground_component_intersection_pixels'],
        'foreground_overlap_fraction':candidate['foreground_component_intersection_fraction'],
        'template_foreground_intersection_area_px2':candidate['template_foreground_intersection_area_px2'],
        'shared_support_pixels':overlap,'shared_support_centroid_separation_px':distance,
        'shared_support_identities_rejected':len(fused),'disjoint_support_bbox_overlap_not_fused':True,
        'registered_source_contract_points':len(points),'malformed_contracts_rejected':rejected,
        'wrong_source_sha_rejected':wrong_source_rejected,'nonopaque_alpha_rejected':nonopaque_rejected,
        'opaque_unprofiled_input_assumption_recorded':True,'profiled_source_converted_with_littlecms2':LITTLECMS_VERSION,
        'scope':'source inputs and constructed arrays only; no captured output read'}


def self_test():
    source,points=fixture();dx,dy=3,-2
    shifted=Image.fromarray(source.astype('uint8')).transform((240,180),Image.Transform.AFFINE,(1,0,-dx,0,1,-dy),Image.Resampling.BILINEAR,fillcolor=(128,128,128))
    rows=track(source,np.asarray(shifted,dtype=float),points)
    identified=[r for r in rows if r.get('observed_center_px')];assert len(identified)>=4, [(r['id'],r['status']) for r in rows]
    err=[np.linalg.norm(np.asarray(r['dx_dy_px'])-[dx,dy]) for r in identified]
    assert max(err)<2.0,err
    blank=np.full_like(source,128);hidden=track(source,blank,points)
    assert not any(r.get('observed_center_px') for r in hidden)
    blurred=np.asarray(shifted.filter(ImageFilter.GaussianBlur(2)),dtype=float)
    blur_rows=track(source,blurred,points);blur_good=[r for r in blur_rows if r.get('observed_center_px')]
    assert all(np.linalg.norm(np.asarray(r['dx_dy_px'])-[dx,dy])<3 for r in blur_good)
    duplicate=points+[dict(points[0],id='duplicate_source_identity')];dup_rows=track(source,np.asarray(shifted,dtype=float),duplicate)
    assert dup_rows[0].get('control_status')=='fused' and dup_rows[-1].get('control_status')=='fused'
    # Mild known affine warp: not a production model, only a synthetic check.
    sx,sy=1.04,.97
    affine=Image.fromarray(source.astype('uint8')).transform((240,180),Image.Transform.AFFINE,
        (1/sx,0,-1/sx,0,1/sy,1/sy),Image.Resampling.BILINEAR,fillcolor=(128,128,128))
    affine_rows=track(source,np.asarray(affine,dtype=float),points)
    affine_good=[r for r in affine_rows if r.get('observed_center_px') and r.get('control_status') in ('tracked','outside_support')]
    affine_errors=[float(np.linalg.norm(np.asarray(r['observed_center_px'])-(np.asarray(r['source_center_px'])*[sx,sy]+[1,-1]))) for r in affine_good]
    assert len(affine_good)>=3 and max(affine_errors)<3,affine_errors
    # A shared observed lobe cannot supply two identities, even on a control.
    # Deliberately gross/nonlocal distortion may reject all; it is never passed.
    reflected=np.asarray(Image.fromarray(source.astype('uint8')).transpose(Image.Transpose.FLIP_LEFT_RIGHT),dtype=float)
    reflected_rows=track(source,reflected,points)
    assert not any(r.get('observed_center_px') for r in reflected_rows)
    large=np.full((1334,750,3),128.);large[1100:1280,260:500]=source
    large_points=[dict(p,source_x_px=p['source_x_px']+260,source_y_px=p['source_y_px']+1100) for p in points]
    large_shift=np.full_like(large,128);large_shift[:,70:]=large[:,:-70]
    large_rows=track(large,large_shift,large_points)
    large_good=[r for r in large_rows if r.get('observed_center_px') and r['status']=='tracked']
    large_errors=[float(np.linalg.norm(np.asarray(r['dx_dy_px'])-[70,0])) for r in large_good]
    assert len(large_good)>=2 and max(large_errors)<2,[(r['id'],r['status']) for r in large_rows]
    duplicate_image=np.full_like(large,128)
    px,py=int(round(large_points[0]['source_x_px']-.5)),int(round(large_points[0]['source_y_px']-.5))
    for offset in (-70,70):
        duplicate_image[py-30:py+31,px+offset-30:px+offset+31]=large[py-30:py+31,px-30:px+31]
    lobe_row=track(large,duplicate_image,[large_points[0]])[0]
    assert lobe_row['status']=='multiple_lobes',lobe_row['status']
    # FFT must match direct Pearson at the known shift on independent random data.
    rng=np.random.default_rng(771);a=rng.normal(size=(30,35));t=a[7:14,12:21];c=ncc_valid(a,t)
    assert np.unravel_index(np.argmax(c),c.shape)==(7,12) and abs(c[7,12]-1)<1e-10
    return {'v2_gates':v2_gate_tests(),'translation_known_px':[dx,dy],'translation_tracked':len(identified),'translation_total':len(rows),
        'translation_max_center_error_px':float(max(err)), 'blur_sigma_px':2,'blur_tracked':len(blur_good),
        'blank_false_tracked':0,'duplicate_identity_rejected':True,'fft_direct_identity_check':True,
        'affine_known_scale_xy':[sx,sy],'affine_identified':len(affine_good),'affine_max_center_error_px':max(affine_errors),
        'nonlocal_reflection_false_tracked':0,
        'wide_search_translation_px':[70,0],'wide_search_identified':len(large_good),'wide_search_max_error_px':max(large_errors),
        'duplicated_patch_lobes_status':lobe_row['status'],
        'scope':'synthetic algorithm checks only; rejected points retained; no real capture opened'}


def self_test_picture():
    source,points=fixture();panels=[Image.fromarray(source.astype('uint8'))]
    shifted=panels[0].transform((240,180),Image.Transform.AFFINE,(1,0,-3,0,1,2),Image.Resampling.BILINEAR,fillcolor=(128,128,128))
    panels.extend([shifted,shifted.filter(ImageFilter.GaussianBlur(2)),Image.new('RGB',(240,180),(128,128,128))])
    out=Image.new('RGB',(960,204),'white');draw=ImageDraw.Draw(out)
    for i,(label,panel) in enumerate(zip(['Synthetic known source','Known translation (+3,-2)px','Translation + sigma2 blur','Hidden / blank rejection'],panels)):
        out.paste(panel,(i*240,24));draw.text((i*240+4,5),label,fill='black')
    out.save(HERE/'synthetic-selftest-v2.png')


def freeze():
    if FREEZE.exists() or PROTOCOL.exists():raise RuntimeError('Preserve existing freeze; create a new version instead of overwriting')
    report=self_test()
    protocol={**PARAMS,'registered_at_utc':datetime.now(timezone.utc).isoformat(),
        'reference':'Rajendran/Bane/Vlachos arXiv1812.10870 section3: known-dot windows and local correlation only; its small-displacement/yield claims and fluid inversion are not adopted',
        'algorithm':'source RGB direction projection; multi-blur local translation NCC; independent peak rejection; RGB/context diagnostics; local contrast components at three thresholds; weighted centroid/moment axes; identity-competition rejection',
        'limits':'Large non-affine warp, unknown tint/blur, occlusion, source overlap and multivalued refraction can prevent identification. NCC is not physical transmittance, per-point confidence is not probability, no nearest-neighbor forced matching.',
        'test_data_use':'Any actual output used to revise this algorithm/thresholds becomes calibration; preserve failures and validate next frozen version on new test seeds.'}
    write_json(PROTOCOL,protocol)
    source_manifests={str(p.relative_to(HERE.parent)):sha(p) for p in
                      [HERE.parent/'protocol.json',HERE.parent/'test/manifest.json',HERE.parent/'calibration/manifest.json'] if p.exists()}
    record={'schema':2,'implementation_version':2,'frozen_at_utc':datetime.now(timezone.utc).isoformat(),'actual_captures_opened':False,
        'preserved_v1':{name:sha(HERE/name) for name in ['track_dots.py','tracking-protocol.json','frozen-tracker.json']},
        'source_sha256':sha(__file__),'protocol_sha256':sha(PROTOCOL),'self_test':report,
        'input_registration_sha256':source_manifests,
        'versions':{'python':platform.python_version(),'numpy':np.__version__,'pillow':PILLOW_VERSION,'littlecms2':LITTLECMS_VERSION}}
    write_json(FREEZE,record);self_test_picture();print(json.dumps(record,indent=2))


def verify_freeze():
    f=json.loads(FREEZE.read_text())
    if sha(__file__)!=f['source_sha256'] or sha(PROTOCOL)!=f['protocol_sha256']:raise ValueError('Frozen implementation changed')
    for name,value in f['input_registration_sha256'].items():
        if sha(HERE.parent/name)!=value:raise ValueError('Input registration changed')
    if np.__version__!=f['versions']['numpy'] or PILLOW_VERSION!=f['versions']['pillow'] or LITTLECMS_VERSION!=f['versions']['littlecms2']:
        raise ValueError('Frozen NumPy/Pillow/LittleCMS versions differ; preserve this freeze and use a new version')
    return f


def validate_point_contract(metadata):
    """Validate source identity/coordinate semantics before any observed file is opened."""
    def require(ok,reason):
        if not ok:raise ValueError(reason)
    require(metadata.get('schema')==1,'Unsupported source-point schema')
    require(metadata.get('coordinate_system')=={'source_px':[750,1334],'logical_pt':[375,667],
        'px_per_pt':2,'origin':'top-left image edge','pixel_centers':'integer index + 0.5'},'Source coordinate contract mismatch')
    require(metadata.get('background_rgb')==[128,128,128],'Source reference background mismatch')
    points=metadata.get('dots');require(isinstance(points,list) and len(points)>0,'Missing source identities')
    require(metadata.get('point_count')==len(points),'Source point count mismatch')
    ids=[point.get('id') for point in points];known_ids=set(ids)
    require(all(isinstance(identity,str) and identity for identity in ids) and len(set(ids))==len(ids),'Duplicate or invalid source identity')
    for point in points:
        for key in ['source_x_px','source_y_px','source_x_pt','source_y_pt','radius_px','radius_pt']:
            value=point.get(key);require(isinstance(value,(int,float)) and math.isfinite(value),'Nonfinite/missing source geometry: '+key)
        require(0<=point['source_x_px']<750 and 0<=point['source_y_px']<1334,'Source center outside registered world')
        require(point['radius_px']>0 and point['radius_pt']>0,'Invalid source radius')
        for pixel_key,point_key in [('source_x_px','source_x_pt'),('source_y_px','source_y_pt'),('radius_px','radius_pt')]:
            require(abs(point[pixel_key]-2*point[point_key])<=1e-9,'Inconsistent source pixel/point coordinates')
        rgb=point.get('rgb');require(isinstance(rgb,list) and len(rgb)==3 and
            all(type(v) is int and 0<=v<=255 for v in rgb),'Invalid source RGB')
        require(point.get('sigma_px') is None,'Unexpected source disk blur')
        require(all(identity in known_ids for key in ['overlapping_dot_ids','occluding_later_dot_ids']
                    for identity in point.get(key,[])),'Unknown source-overlap identity')
        require(point.get('seed')==metadata.get('seed'),'Source point seed mismatch')
        require(point['id'].startswith(metadata.get('input_id','')+'_dot_'),'Source point identity/input mismatch')
    return points


def source_preflight(source_path,points_path):
    metadata=json.loads(Path(points_path).read_text());points=validate_point_contract(metadata)
    source_sha=sha(source_path)
    if metadata.get('image_sha256')!=source_sha:raise ValueError('Original shared PNG hash mismatch')
    matches=[]
    for split in ['test','calibration']:
        manifest=json.loads((HERE.parent/split/'manifest.json').read_text())
        matches.extend((split,manifest,entry) for entry in manifest['inputs'] if entry['id']==metadata.get('input_id'))
    if len(matches)!=1:raise ValueError('Source ID is not uniquely registered in frozen input manifests')
    split,manifest,entry=matches[0]
    if entry.get('kind')!='dots' or entry['sha256']!=source_sha or entry.get('points_sha256')!=sha(points_path):
        raise ValueError('Source PNG / point table does not match frozen manifest binding')
    if metadata.get('image_file')!=entry['file'] or metadata['point_count']!=entry['point_count']:
        raise ValueError('Source metadata and frozen manifest disagree')
    if metadata.get('seed')!=entry['seed']:raise ValueError('Source seed differs from frozen manifest')
    with Image.open(source_path) as original:
        if original.mode!='RGB' or list(original.size)!=PARAMS['world_px']:raise ValueError('Registered source must be opaque RGB750x1334')
        if hashlib.sha256(original.info.get('icc_profile',b'')).hexdigest()!=manifest['icc_profile_sha256']:
            raise ValueError('Source ICC profile differs from frozen input')
        if hashlib.sha256(np.asarray(original).tobytes()).hexdigest()!=entry['pixel_sha256']:
            raise ValueError('Source decoded pixels differ from frozen input')
    return metadata,points,{'split':split,'manifest_id':manifest['set_id'],'input_id':entry['id'],
        'png_sha256':source_sha,'points_sha256':sha(points_path),'coordinate_contract_validated':True}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--freeze',action='store_true');p.add_argument('--self-test',action='store_true')
    p.add_argument('--source');p.add_argument('--points');p.add_argument('--observed');p.add_argument('--baseline');p.add_argument('--output');p.add_argument('--label',default='unspecified-role-theme')
    args=p.parse_args()
    if args.freeze:freeze();return
    if args.self_test:print(json.dumps(self_test(),indent=2));return
    frozen=verify_freeze() # Must occur before opening any actual capture.
    if not all([args.source,args.points,args.observed,args.output]):raise ValueError('source/points/observed/output required')
    out=Path(args.output)
    if out.exists():raise ValueError('Do not overwrite a viewed run')
    metadata,points,preflight=source_preflight(args.source,args.points)
    source,source_color=load_rgb(args.source,return_info=True);observed,observed_color=load_rgb(args.observed,return_info=True)
    if list(source.shape[:2][::-1])!=PARAMS['world_px'] or source.shape!=observed.shape:
        raise ValueError('Exact shared 2x world required; no registration fitting')
    out.mkdir(parents=True)
    rows=track(source,observed,points)
    baseline_rows=None;baseline_color=None
    if args.baseline:
        baseline,baseline_color=load_rgb(args.baseline,return_info=True)
        if baseline.shape!=source.shape:raise ValueError('Exact shared baseline dimensions required')
        baseline_rows=track(source,baseline,points);write_json(out/'baseline-per-source.json',serial(baseline_rows))
    status={k:sum(r['status']==k for r in rows) for k in PARAMS['status_semantics']}
    report={'schema':2,'implementation_version':2,'input_id':metadata['input_id'],'label':args.label,'source_points':len(points),'status_counts':status,
        'source_preflight':preflight,
        'color_inputs':{'source':source_color,'observed':observed_color,'baseline':baseline_color},
        'frozen_tracker_sha256':sha(FREEZE),'source_png_sha256':sha(args.source),'points_sha256':sha(args.points),
        'observed_png_sha256':sha(args.observed),'baseline_png_sha256':sha(args.baseline) if args.baseline else None,
        'hashes_describe_files_not_optics':'No result is an absolute native pass or a physical model inversion',
        'points':rows,'freeze':frozen}
    write_json(out/'per-source.json',serial(report))
    flat=[]
    for r in rows:
        row={k:r.get(k) for k in ['id','status','source_radius_px','draw_order','edge_clipped','search_radius_px','ncc_peak_margin']}
        for key in ['source_center_px','observed_center_px','dx_dy_px']:
            v=r.get(key,[None,None]);row[key+'_x'],row[key+'_y']=v
        row['reasons']='|'.join(r['reasons']);row['candidate_count']=len(r['candidates']);flat.append(row)
        for key in ['area_px2','moment_major_axis_px','moment_minor_axis_px','moment_axis_angle_deg']:
            row[key]=r.get('morphology',{}).get(key)
        row['measurement_layer']=r.get('measurement_layer');row['control_status']=r.get('control_status')
        for key in ['ncc','peak_margin','local_snr']:row['confidence_'+key]=r.get('confidence',{}).get(key)
        row['mean_rgb']=json.dumps(r.get('morphology',{}).get('mean_rgb'))
        row['contrast_rgb']=json.dumps(r.get('morphology',{}).get('contrast_rgb'))
    with (out/'per-source.csv').open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(flat[0]));writer.writeheader();writer.writerows(flat)
    print(json.dumps({'output':str(out),'status_counts':status},indent=2))


if __name__=='__main__':main()
