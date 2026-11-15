from pathlib import Path
import json,io,hashlib
from PIL import Image,ImageCms
import numpy as np
P=Path(__file__).resolve().parent.parent;O=Path(__file__).resolve().parent;B=P/'panels-dark-scrim-20261115';C=P/'panels-alert-rim-bounded-history-20261115';bm=json.loads((B/'matrix.json').read_text());cm=json.loads((C/'matrix.json').read_text());base={(r['background'],r['theme'],r['carrier']):r for r in bm['captures']}
def load(p):
 im=Image.open(p);a=np.array(im.convert('RGBA'));ic=im.info.get('icc_profile');rgb=im.convert('RGB');n=np.asarray(ImageCms.profileToProfile(rgb,ImageCms.ImageCmsProfile(io.BytesIO(ic)),ImageCms.createProfile('sRGB'),outputMode='RGB')) if ic else a[:,:,:3];nn=np.dstack([n,a[:,:,3]]);assert np.array_equal(a,nn);return a.astype(float)
def diff(a,b):
 assert a.shape==b.shape
 d=np.abs(a-b);return {'changed_channels':int(np.count_nonzero(d)),'max_abs':float(d.max()),'mean_abs':float(d.mean()),'samples':int(d.size)}
rows=[]
for c in cm['captures']:
 k=(c['background'],c['theme'],c['carrier']);b=base[k];assert b['window_geometry']['captured_surface_screen_rect_px']==c['window_geometry']['captured_surface_screen_rect_px'];assert b['actual_alert_layout']==c['actual_alert_layout'];bw=load(B/b['window_png']);cw=load(C/c['window_png']);bs=load(B/b['screen_png']);cs=load(C/c['screen_png']);rows.append({'input':k[0],'theme':k[1],'carrier':k[2],'expected_unchanged':k[2]=='share_sheet' or k[1]=='dark','actual_window':diff(bw,cw),'visible_app_screen':diff(bs[80:1302],cs[80:1302]),'full_screen':diff(bs,cs),'paths':{key:{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for key,p in [('baseline_window',B/b['window_png']),('candidate_window',C/c['window_png']),('baseline_screen',B/b['screen_png']),('candidate_screen',C/c['screen_png'])]}})
rec={'strict_controls_all_zero':all(r['actual_window']['max_abs']==0 for r in rows if r['expected_unchanged']),'raw_equals_icc':True,'baseline':str(B),'candidate':str(C),'rows':rows};(O/'rim-bounded-history-controls.json').write_text(json.dumps(rec,indent=2)+'\n')
print('strict_controls_all_zero',rec['strict_controls_all_zero'])
for r in rows:print(r['input'],r['theme'],r['carrier'],'actualWindow',r['actual_window']['max_abs'],'changed',r['actual_window']['changed_channels'],'appScreen',r['visible_app_screen']['max_abs'])
