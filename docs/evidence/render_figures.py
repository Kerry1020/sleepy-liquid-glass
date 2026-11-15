#!/usr/bin/env python3
"""Redraw all public research figures from the committed small data and crops.
Requires Python 3, matplotlib and Pillow. Does not build or contact a device.
The frozen predictions are observations/analysis outputs, not a rerun of fitting.
"""
from pathlib import Path
import csv,hashlib,json,math,shutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent
OUT=ROOT.parent/'images/research';OUT.mkdir(parents=True,exist_ok=True)
DATA=ROOT/'data';CROP=ROOT/'crops'
BLUE='#2366ad';ORANGE='#c17a18';GREEN='#008579';PURPLE='#8452a3';GREY='#707b88'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':11,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#24364a','text.color':'#24364a','xtick.color':'#45556a','ytick.color':'#45556a','figure.facecolor':'white','axes.facecolor':'white','grid.color':'#dfe5ec','grid.linewidth':.65,'svg.hashsalt':'sleepy-research-20261114'})
def read(n):return list(csv.DictReader((DATA/n).open()))
def save(fig,name):
 fig.savefig(OUT/(name+'.png'),dpi=160,bbox_inches='tight',metadata={'Software':'Matplotlib; Sleepy evidence renderer'})
 fig.savefig(OUT/(name+'.svg'),bbox_inches='tight',metadata={'Date':None,'Creator':'Sleepy evidence renderer'})
 plt.close(fig)
def format_ax(ax):ax.grid(alpha=.75);ax.set_axisbelow(True)
def rms(x):return math.sqrt(sum(v*v for v in x)/len(x))
labels=['Slow forward','Slow reverse','Fast forward','Fast reverse']
# 1: matched actual parent-carrier draws; do not interpolate between platforms.
old=read('dock-android69.csv');new=read('dock-android72.csv')
oldkey={(r['gesture_index'],r['native_raw_line']):r for r in old}
common=[r for r in new if r['android_wholly_held']=='True' and oldkey[(r['gesture_index'],r['native_raw_line'])]['android_wholly_held']=='True']
assert len(common)==540
fig,axs=plt.subplots(2,2,figsize=(11.4,6.6))
for i,ax in enumerate(axs.flat):
 rs=[r for r in common if int(r['gesture_index'])==i];xs=[float(r['native_elapsed_mid_s']) for r in rs]
 ax.plot(xs,[float(r['native_parent_tx_pt']) for r in rs],color=BLUE,lw=2,label='iOS 26.5 observed parent')
 ax.plot([float(oldkey[(r['gesture_index'],r['native_raw_line'])]['android_elapsed_mid_s']) for r in rs],[float(oldkey[(r['gesture_index'],r['native_raw_line'])]['android_parent_tx_dp']) for r in rs],color=ORANGE,lw=1.2,ls='--',label='Android69 actual draw')
 ax.plot([float(r['android_elapsed_mid_s']) for r in rs],[float(r['android_parent_tx_dp']) for r in rs],color=GREEN,lw=1.2,marker='.',markersize=2,label='Android72 actual draw')
 ax.set_title(f'{labels[i]} | n={len(rs)}');ax.set_xlabel('Seconds from actual DOWN receipt');ax.set_ylabel('Parent translation (pt / dp)');format_ax(ax)
axs[0,0].legend(loc='upper left',fontsize=8)
fig.suptitle('Dock parent translation: actual observations, common HELD rows',fontsize=15)
fig.text(.5,.002,'Historical app replay. Parent carrier only; no optical contour / release claim. Other gestures were inspected, not blind.',ha='center',fontsize=9)
fig.tight_layout(rect=(0,.025,1,.96));save(fig,'dock-parent-trajectories')
summary=json.loads((DATA/'dock-summary.json').read_text())['cases']
fig,ax=plt.subplots(figsize=(9.7,4.3));x=list(range(4));w=.34
b=ax.bar([v-w/2 for v in x],[r['android69']['rmse'] for r in summary],w,color=ORANGE,label='Android69');a=ax.bar([v+w/2 for v in x],[r['android72']['rmse'] for r in summary],w,color=GREEN,label='Android72')
for bars in [b,a]:ax.bar_label(bars,fmt='%.3f',padding=3,fontsize=9)
ax.set_xticks(x,[f'{labels[i]}\n(n={r["n"]})' for i,r in enumerate(summary)]);ax.set_ylabel('Center translation RMSE (pt = dp mapping)');ax.set_ylim(0,5.5);ax.legend();format_ax(ax)
ax.set_title('Same 540 HELD observations; nearest real draws, no fitted time shift')
fig.text(.5,.005,'Motion calibration evidence, not whole-Dock similarity. Fast actual finger forcing differs between platforms.',ha='center',fontsize=9);fig.tight_layout(rect=(0,.04,1,1));save(fig,'dock-parent-errors')
# 2: native threshold family against actual GPU color/coverage boundaries.
rows=read('menu-corners.csv');fig,axs=plt.subplots(2,2,figsize=(10.8,7))
corner_metrics=[]
for c,ax in zip(['TL','TR','BL','BR'],axs.flat):
 rs=[r for r in rows if r['corner']==c and 2<=float(r['depth'])<=24 and r['usable_all_thresholds']=='True' and r['flat_matched_input_all_thresholds']=='True'];assert len(rs)==44
 ds=[float(r['depth']) for r in rs]
 ax.fill_between(ds,[float(r['native_low']) for r in rs],[float(r['native_high']) for r in rs],color=BLUE,alpha=.15,label='Native threshold family')
 ax.plot(ds,[float(r['native_reference']) for r in rs],color=BLUE,lw=2,label='Native reference threshold')
 ax.plot(ds,[float(r['baseline_reference']) for r in rs],color=ORANGE,ls='--',label='Android Menu24')
 ax.plot(ds,[float(r['candidate_reference']) for r in rs],color=GREEN,label='Android Menu32 actual GPU')
 split='light calibration' if c in ['TL','TR'] else 'dark evaluation'
 ax.set_title(f'{c}: {split}');ax.set_xlabel('Depth from pane edge (pt / dp)');ax.set_ylabel('Inset (pt / dp)');format_ax(ax)
 corner_metrics.append({'corner':c,'split':split,'n':len(rs),'baseline_mae':sum(abs(float(r['baseline_reference'])-float(r['native_reference'])) for r in rs)/len(rs),'candidate_mae':sum(abs(float(r['candidate_reference'])-float(r['native_reference'])) for r in rs)/len(rs)})
axs[0,0].legend(fontsize=8);fig.suptitle('Menu corner inset profiles | fixed depth 2–24',fontsize=15)
fig.text(.5,.005,'Native color-level boundaries are not alpha masks. These are static corner observations, not a recovered Apple radius.',ha='center',fontsize=9);fig.tight_layout(rect=(0,.025,1,.96));save(fig,'menu-corner-profiles')
fig,ax=plt.subplots(figsize=(8.8,4.1));x=list(range(4));b=ax.bar([v-w/2 for v in x],[r['baseline_mae'] for r in corner_metrics],w,color=ORANGE,label='Menu24');a=ax.bar([v+w/2 for v in x],[r['candidate_mae'] for r in corner_metrics],w,color=GREEN,label='Menu32 actual GPU')
for bars in [b,a]:ax.bar_label(bars,fmt='%.3f',padding=3)
ax.set_xticks(x,['TL · light','TR · light','BL · dark','BR · dark']);ax.set_ylabel('Inset MAE (pt / dp)');ax.set_ylim(0,4.6);format_ax(ax);ax.legend();ax.set_title('Menu static corners: 44 valid depth observations per corner')
fig.text(.5,.005,'Threshold-dependent image geometry; first scanlines excluded by the declared fixed depth window.',ha='center',fontsize=9);fig.tight_layout(rect=(0,.04,1,1));save(fig,'menu-corner-errors')
shutil.copyfile(CROP/'menu-corners.png',OUT/'menu-corner-montage.png')
# 3: native-only empirical predictions; measured lift is deliberately not modeled.
fitrows=read('slider-native-fit.csv');protocol=json.loads((DATA/'slider-protocol.json').read_text());fig,axs=plt.subplots(2,2,figsize=(11.4,7.2));slider_metrics=[]
for g,ax in zip(protocol['gestures'],axs.flat):
 i=g['gestureIndex'];rs=[r for r in fitrows if int(r['gestureIndex'])==i];t=[float(r['t']) for r in rs]
 ax.plot(t,[float(r['observed_sx']) for r in rs],color=BLUE,lw=1.3,label='Observed sx')
 ax.plot(t,[float(r['predicted_sx']) for r in rs],color=ORANGE,lw=1,ls='--',label='Empirical sx (exact)')
 ax.plot(t,[float(r['observed_sy']) for r in rs],color=PURPLE,lw=1.3,label='Observed sy')
 ax.plot(t,[float(r['predicted_sy']) for r in rs],color=GREEN,lw=1,ls='--',label='Empirical sy (exact)')
 ax.axvline(g['up'],color=GREY,lw=1,ls=':',label='Actual UP')
 ax.set_title(f'{labels[i]} · {"train" if g["split"]=="train" else "held out before fitting"} (n={len(rs)})');ax.set_xlabel('Seconds from actual DOWN receipt');ax.set_ylabel('Presentation carrier scale');format_ax(ax)
 baseline_w=[float(r['observed_w'])/float(r['observed_sx'])-float(r['observed_w']) for r in rs]
 baseline_h=[float(r['observed_h'])/float(r['observed_sy'])-float(r['observed_h']) for r in rs]
 slider_metrics.append({'gesture':i,'split':g['split'],'n':len(rs),'isotropic_width_rmse':rms(baseline_w),'isotropic_height_rmse':rms(baseline_h),'exact_width_rmse':rms([float(r['predicted_w_given_measured_lift'])-float(r['observed_w']) for r in rs]),'exact_height_rmse':rms([float(r['predicted_h_given_measured_lift'])-float(r['observed_h']) for r in rs])})
axs[0,0].legend(fontsize=8,ncols=2);fig.suptitle('Slider deformation: frozen native-only empirical feasibility study',fontsize=15)
fig.text(.5,.003,'Train: forward slow/fast. Held out: complete reverse slow/fast. Width/height condition on native measured lift; no Android replay.',ha='center',fontsize=9);fig.tight_layout(rect=(0,.025,1,.96));save(fig,'slider-native-deformation')
fig,axs=plt.subplots(1,2,figsize=(11.8,4.6))
for dim,ax in zip(['width','height'],axs):
 b=ax.bar([v-w/2 for v in x],[r['isotropic_'+dim+'_rmse'] for r in slider_metrics],w,color=ORANGE,label='Isotropic baseline')
 a=ax.bar([v+w/2 for v in x],[r['exact_'+dim+'_rmse'] for r in slider_metrics],w,color=GREEN,label='Exact empirical prediction')
 for bars in [b,a]:ax.bar_label(bars,fmt='%.3f',padding=2,fontsize=8)
 ax.set_xticks(x,['Slow +\ntrain','Slow −\nevaluation','Fast +\ntrain','Fast −\nevaluation']);ax.set_ylabel('Carrier '+dim+' RMSE (pt)');ax.set_title(dim.capitalize()+' given measured native lift');format_ax(ax)
axs[0].legend(fontsize=8);fig.suptitle('Native-only shape fit: full DOWN−0.1s through UP+1.2s windows',fontsize=14)
fig.text(.5,.005,'Exact analytic prediction, not the 240 Hz runtime result. Rise/fall, center, Android delivery and optics are not validated.',ha='center',fontsize=9);fig.tight_layout(rect=(0,.035,1,.94));save(fig,'slider-native-errors')
# 4: independent backgrounds and themes; retain actual differing pane contents.
body=read('sheet-body.csv');bgs=['fine_grid','color_stripes','tonal_blocks','synthetic_landscape'];names=['Fine grid','Color stripes','Tonal blocks','Synthetic landscape'];fig,ax=plt.subplots(figsize=(9.7,4.2))
for j,theme in enumerate(['light','dark']):
 vals=[float(next(r['mean_rgb_rmse_8bit'] for r in body if r['background']==bg and r['theme']==theme)) for bg in bgs]
 bars=ax.bar([v+(-w/2 if j==0 else w/2) for v in x],vals,w,color=[BLUE,PURPLE][j],label=theme.title());ax.bar_label(bars,fmt='%.3f',padding=3)
ax.set_xticks(x,names);ax.set_ylim(0,1.65);ax.set_ylabel('RMSE of three body-ROI mean RGB channels (0–255)');ax.set_title('Sheet body material: four backgrounds × light / dark');format_ax(ax);ax.legend()
fig.text(.5,.005,'Foreground-free interior ROI only. Different body layout, edges, rim and background phase remain outside this score.',ha='center',fontsize=9);fig.tight_layout(rect=(0,.045,1,1));save(fig,'sheet-body-errors')
# Pillow montage preserves aspect ratio. All inputs are crops; status bars excluded.
from matplotlib import font_manager
font=ImageFont.truetype(font_manager.findfont('DejaVu Sans'),18)
W=1060;head=76;rowh=420;canvas=Image.new('RGB',(W,head+4*rowh+60),'#f2f5f9');draw=ImageDraw.Draw(canvas)
cols=[('light','ios26.5'),('light','android36'),('dark','ios26.5'),('dark','android36')]
draw.text((18,12),'Sheet synthetic fixtures | historical app backend',fill='#24364a',font=font)
for j,(theme,platform) in enumerate(cols):draw.text((j*260+20,44),f'{platform} · {theme}',fill='#24364a',font=font)
for i,bg in enumerate(bgs):
 y=head+i*rowh;draw.text((18,y),names[i],fill='#24364a',font=font)
 for j,(theme,platform) in enumerate(cols):
  im=Image.open(CROP/f'sheet-{bg}-{theme}-{platform}.png');im.thumbnail((244,380),Image.Resampling.LANCZOS);canvas.paste(im,(j*260+16,y+28))
draw.text((18,head+4*rowh+10),'Cropped, aspect-preserved previews. Contents/heights differ; this is not a pixel or layout match.',fill='#24364a',font=font)
canvas.save(OUT/'sheet-background-matrix.png',optimize=True)
shutil.copyfile(CROP/'slider-held-optical-gap.png',OUT/'slider-held-optical-gap.png')
# 6: native-only decoded Toggle frames; no matched Android optical claim.
for n in ['switch-white-to-glass.png','switch-release-theme-fill.png']:
 shutil.copyfile(CROP/n,OUT/n)
# Publish reproducible computed tables as well as the pictures.
(DATA/'computed-results.json').write_text(json.dumps({'dock_common_rows':len(common),'menu_corners':corner_metrics,'slider_native_exact_prediction':slider_metrics},indent=2)+'\n')
outputs=[]
for p in sorted(OUT.iterdir()):
 if p.is_file():b=p.read_bytes();outputs.append({'path':p.name,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)})
(ROOT/'figure-manifest.json').write_text(json.dumps({'renderer':'render_figures.py','matplotlib':matplotlib.__version__,'outputs':outputs},indent=2)+'\n')
print(json.dumps({'figures':len(outputs),'bytes':sum(x['bytes'] for x in outputs),'common_held':len(common),'menu':corner_metrics,'slider':slider_metrics},indent=2))
