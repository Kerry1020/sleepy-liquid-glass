#!/usr/bin/env python3
"""Create a separate two-round multicolor-star G diagnostic; never edit prior packets."""
from pathlib import Path
import copy,hashlib,json,shutil
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
PARENT=HERE.parent/'multicolor-star-v2'/'pose-corrected-v3'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write_json(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
spec0=json.loads((PARENT/'shape-spec.json').read_text())
man0=json.loads((PARENT/'inputs'/'manifest.json').read_text())
original_path=PARENT/'inputs'/'st01_rgb_star_d16.png'
original=Image.open(original_path)
icc=original.info['icc_profile']
rgb=np.array(original.convert('RGB'))
shape0=next(x['shape'] for x in spec0['inputs'] if x['id']==spec0['first_input_id'])
blue_count=np.array(Image.open(PARENT/shape0['regions'][0]['coverage_count_mask_png']),dtype=np.int32)
assert set(np.unique(blue_count))<=set(range(17))
original_hashes={'parent_spec':sha(PARENT/'shape-spec.json'),'parent_manifest':sha(PARENT/'inputs'/'manifest.json'),'parent_source':sha(original_path)}
packets=[]
for name,input_id,has_pulse in [('witness','st01_rgb_star_gwitness_d16',True),('control','st01_rgb_star_gneutral_d16',False)]:
 out=HERE/name;(out/'inputs').mkdir(parents=True,exist_ok=True);(out/'masks').mkdir(exist_ok=True)
 for p in (PARENT/'masks').glob('*.png'):shutil.copyfile(p,out/'masks'/p.name)
 data=rgb.copy();data[:,:,1]=128
 if has_pulse:data[:,:,1]=((128*16+104*blue_count+8)//16).astype(np.uint8)
 png=out/'inputs'/(input_id+'.png');Image.fromarray(data,'RGB').save(png,icc_profile=icc)
 assert np.array_equal(data[:,:,[0,2]],rgb[:,:,[0,2]])
 manifest=copy.deepcopy(man0);manifest['set_id']='slider_multicolor_star_g_'+name+'_20261115_v1';manifest['split']='calibration';manifest['diagnostic_role']=name
 for entry in manifest['inputs']:
  if entry['id']==spec0['first_input_id']:
   entry.update(id=input_id,file=input_id+'.png',sha256=sha(png),bytes=png.stat().st_size)
  else:shutil.copyfile(PARENT/'inputs'/entry['file'],out/'inputs'/entry['file'])
 write_json(out/'inputs'/'manifest.json',manifest)
 spec=copy.deepcopy(spec0);spec.update(status='UNSAMPLED independent G finite-difference calibration; not held-out validation or capture acceptance',first_input_id=input_id,flat_input_id='st00_flat128',protocol_split='calibration',validation_state='UNSAMPLED',diagnostic_role=name)
 spec['rasterization']['method']='R/B copied exactly from frozen source pixels; control G128 everywhere; witness G=(128*16+104*original_left_blue_coverage_count+8)//16. Original 4x4 coverage masks and sRGB ICC retained.'
 spec['world']['background_rgb']=[128,128,128]
 for entry in spec['inputs']:
  if entry['id']==spec0['first_input_id']:
   entry.update(id=input_id,role='scheduled multicolor star '+name,source_sha256=sha(png));shape=entry['shape'];shape.update(id=input_id,source_png='inputs/'+input_id+'.png',source_sha256=sha(png));shape['color_partition']='Original local-x region identities retained. R/B unchanged. G128 everywhere except witness left_blue polygon G232; region names describe inherited geometry, not the new hue.'
   for region in shape['regions']:
    region['color_rgb'][1]=232 if has_pulse and region['id']=='left_blue' else 128
  elif entry['id']!='st00_flat128':entry['role']='frozen eight-input-loader compatibility source; not scheduled or analyzed'
 channel_masks={}
 positive_count=blue_count.astype(np.uint8) if has_pulse else np.zeros_like(blue_count,dtype=np.uint8)
 for label,counts in [('positive',positive_count),('negative',np.zeros_like(positive_count)),('neutral',16-positive_count)]:
  mask_path=out/'masks'/('diagnostic-G-'+label+'-coverage16.png');Image.fromarray(counts).save(mask_path)
  channel_masks[label]={'file':'masks/'+mask_path.name,'sha256':sha(mask_path),'coverage_denominator':16,'area_pt2':float(counts.sum()/64.)}
 spec['calibration_diagnostic']={'packet_id':'green-witness-calibration-v1','source_parent_spec_sha256':original_hashes['parent_spec'],'source_parent_png_sha256':original_hashes['parent_source'],'original_rb_preserved_pixel_exact':True,'source_G_negative_support':False,'source_G_positive_support_mask':shape0['regions'][0]['coverage_count_mask_png'] if has_pulse else None,'G_channel_masks':channel_masks,'G_input_change_vs_control':104 if has_pulse else 0,'primary_stage':'ingress75','reference_stage':'full100','other_stages':'collected for unchanged six-stage loader compatibility; exploratory only','native_flat_id_must_remain':'st00_flat128','counterpart_spec':'../'+('control' if has_pulse else 'witness')+'/shape-spec.json','paired_output':'Separate shape-minus-st00 each round; then witness-minus-control. Never relabel the multicolor G128 control as flat128.'}
 spec['analysis_limitations']=['Independent calibration packet; never overwrite, tune against, or relabel frozen held-out inputs.','The source contains only positive and neutral G support. A negative observed G finite difference requires reporting, not inventing a negative source region.','Input R/B equality permits an output R/B finite-difference coupling diagnostic; it does not prove the native transform is channel-separable.','Two G levels estimate one finite difference. R/B output changes show cross-channel or color-conditioned response; they do not by themselves prove nonlinearity. A third amplitude would be needed for a linearity test.','Native G positive support can constrain accessible source support; absent signal cannot uniquely distinguish missing common transport from angular contrast attenuation, tint, blur or nonlinear response.','full100 is a positive G-response/contrast control and a negative control for a cap-only change; it is not a negative G-stimulus control.','Use actual touch-held geometry and strict per-round verifier; no screenshot registration by source content.','All six requested stages are inherited unchanged. Only ingress75/full100 support preregistered conclusions. Rail-confounded y422..438 must remain visible and reported separately.']
 write_json(out/'shape-spec.json',spec)
 Image.fromarray((blue_count>0).astype(np.uint8)*255,'L').save(out/'masks'/'diagnostic-left-region-support.png')
 # Same-source finite difference is an encoded-G change map, not a screenshot/alpha mask.
 diff=np.zeros_like(rgb);diff[:,:,1]=data[:,:,1]-128
 Image.fromarray(diff,'RGB').save(out/'source-G-change-vs-control.png',icc_profile=icc)
 packets.append({'role':name,'first_input_id':input_id,'spec':str(out/'shape-spec.json'),'spec_sha256':sha(out/'shape-spec.json'),'manifest':str(out/'inputs'/'manifest.json'),'manifest_sha256':sha(out/'inputs'/'manifest.json'),'source_png':str(png),'source_sha256':sha(png),'G_min_max':list(map(int,[data[:,:,1].min(),data[:,:,1].max()])),'RB_pixel_exact_original':True})
# Source-only preview, no resampling of actual inputs. 1:8 nearest enlargement is explicitly illustrative.
canvas=Image.new('RGB',(900,330),(240,240,245));draw=ImageDraw.Draw(canvas)
for col,(title,path) in enumerate([('Original frozen RGB star',original_path),('G witness: only left region +104',Path(packets[0]['source_png'])),('G128 control: same R/B',Path(packets[1]['source_png']))]):
 im=Image.open(path).convert('RGB').crop((330,800,420,860)).resize((270,180),Image.Resampling.NEAREST);canvas.paste(im,(col*300+15,50));draw.text((col*300+15,18),title,fill=(0,0,0))
draw.text((15,260),'Source-only crops, nearest enlargement; not native or Android glass captures.',fill=(20,20,20));canvas.save(HERE/'source-preview.png')
assert original_hashes=={'parent_spec':sha(PARENT/'shape-spec.json'),'parent_manifest':sha(PARENT/'inputs'/'manifest.json'),'parent_source':sha(original_path)}
write_json(HERE/'asset-verification.json',{'schema':1,'status':'passed','packets':packets,'original_sources_unchanged':original_hashes,'world_size_pt':[375,667],'png_size_px':[750,1334],'ICC_sha256':hashlib.sha256(icc).hexdigest(),'same_multicolor_star_geometry':True,'source_G_support':'positive witness only in original left_blue polygon; no negative source support; neutral elsewhere','capture_status':'UNSAMPLED','note':'Both manifests contain the unchanged flat st00 plus one distinct scheduled multicolor source and six unused compatibility star inputs.'})
print(json.dumps({'status':'source assets verified; UNSAMPLED','packets':packets,'preview':str(HERE/'source-preview.png')},indent=2))
