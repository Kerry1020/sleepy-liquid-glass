"""Compact fixed-region comparison, no warp/registration/new ROI selection."""
from pathlib import Path
import csv,json
import numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parent;P=O.parent;N=P/'native-panel-feasibility-preparation'
att=json.loads((N/'attachments/manifest.json').read_text())[0]['attachments']
native=N/'attachments'/next(a['exportedFileName'] for a in att if 'panel_probe_shapes-light-alert-rest_0_' in a['suggestedHumanReadableName'] and a['exportedFileName'].endswith('.png'))
names=['native','body8','additive','screen'];labels=['iOS 26.5 native','Old body8 / zero floor','Old additive floor .08','New screen increment .08'];cols=['#2357a1','#777777','#c36d21','#963760']
paths={'native':native}
for n,d in [('body8','panels-alert-body8-20261115'),('additive','panels-alert-rim-bounded-20261115'),('screen','panels-alert-floor-screen-20261115')]:
    m=json.loads((P/d/'matrix.json').read_text());c=next(c for c in m['captures'] if c['background']=='panel_probe_shapes' and c['carrier']=='alert');paths[n]=P/d/c['screen_png']
tracks={};L=np.array([.2126,.7152,.0722])
for n,file,plat in [('native','rim-screen-straight-tracks.csv','native'),('body8','body8-straight-tracks.csv','candidate'),('additive','rim-screen-straight-tracks.csv','baseline'),('screen','rim-screen-straight-tracks.csv','candidate')]:
    rr=list(csv.DictReader((O/file).open()));tracks[n]={}
    for seg in ['neutral_top','neutral_left']:
        a=[r for r in rr if r['input']=='panel_probe_shapes' and r['carrier']=='alert' and r['segment']==seg and r['platform']==plat]
        tracks[n][seg]=(np.array([float(r['distance_pt']) for r in a]),np.array([[float(r['raw_'+c]) for c in 'rgb'] for r in a])@L)
fig=plt.figure(figsize=(11.6,6.1));gs=fig.add_gridspec(2,4,height_ratios=[1.1,1],hspace=.48,wspace=.35)
for i,n in enumerate(names):
    ax=fig.add_subplot(gs[0,i]);im=np.array(Image.open(paths[n]).convert('RGB'))
    # Exactly the existing straight left fixed track support: x43..<103,
    # y614..<676. All four original crops are60x62px, identical aspect.
    ax.imshow(im[614:676,43:103],extent=[43,103,676,614],interpolation='nearest',aspect='equal')
    ax.axvline(55.5,color='#1362ff',lw=.8);ax.axvline(56.5,color='#111111',ls='--',lw=.8)
    ax.set_title(labels[i],fontsize=10);ax.set_xticks([43,55.5,103]);ax.set_xticklabels(['43','.25/.75','103'],fontsize=8);ax.set_yticks([614,676]);ax.tick_params(labelsize=8)
    ax.set_xlabel('Original screen pixels',fontsize=8)
    if i==0:ax.set_ylabel('Original y pixels',fontsize=8)
ax=fig.add_subplot(gs[1,:2]);bx=fig.add_subplot(gs[1,2:])
for n,label,col in zip(names,labels,cols):
    d,v=tracks[n]['neutral_top'];ax.plot(d,v,label=label,color=col,lw=1.4,ls='--' if n=='screen' else '-')
    d,v=tracks[n]['neutral_left'];shoulder=v[(d>=8)&(d<12)].mean();bx.plot(d,v-shoulder,label=label,color=col,lw=1.4,ls='--' if n=='screen' else '-')
for aa in [ax,bx]:aa.set_xlim(-1.75,11.75);aa.axvline(0,color='.6',lw=.6);aa.grid(alpha=.22);aa.set_xlabel('Original inward normal, pt / dp')
ax.set_title('Frozen neutral top x140..<235pt: raw encoded luma',fontsize=10);ax.set_ylabel('Encoded luma');ax.legend(fontsize=7,loc='best')
bx.set_title('Frozen neutral left y353..<359pt: edge minus shoulder',fontsize=10);bx.set_ylabel('Luma minus fixed8..<12pt mean');bx.axhline(0,color='.5',lw=.6)
fig.suptitle('Screen increment removes colored red clipping but loses neutral-side highlight',fontsize=12,y=.99)
fig.text(.5,.005,'Identical60x62px original crops; no resize/warp/registration. Blue solid/black dashed mark inset0.25/0.75pt. Curves use only frozen neutral tracks.',ha='center',fontsize=8)
fig.savefig(O/'rim-screen-four-way-fixed-comparison.png',dpi=150,bbox_inches='tight');plt.close(fig)
print(O/'rim-screen-four-way-fixed-comparison.png')
