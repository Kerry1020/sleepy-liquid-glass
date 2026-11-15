from pathlib import Path
import json,numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2]
A=R/'artifacts/glass-panel-thickness-20261115/panels-current-baseline-20261115/color_stripes-light-alert-rest-screen.png'
N=R/'outputs/glass-native-parity-20261112/native-alert-optics-20261113/rest/alert-optics-color_stripes-light-alert-rest.png'
res={'scope':'historical stripe calibration only; phase modulo108pt, not unique displacement, encoded RGB; no source warp','rows':[]}
for role,path in [('native',N),('android',A)]:
 im=np.asarray(Image.open(path).convert('RGB'),float)
 # Content-free band below message and above action controls. One216px period.
 template=im[699:711,250:466].mean(0)
 side=im[620:690].mean(0)
 for x in range(57,113,2):
  c=side[x]
  # ignore varying white highlight by subtracting achromatic component for phase only.
  chrom=template-template.mean(1,keepdims=True); cc=c-c.mean()
  errs=np.mean((chrom-cc)**2,axis=1); i=int(errs.argmin()); phase=(250+i-x)%216
  depth=(x+.5-55)/2;rise=1-min(depth/20,1);shift=60*(1-(1-rise*rise)**.5)
  res['rows'].append({'role':role,'x':x,'depth_pt':depth,'rgb':c.tolist(),'best_mod108_phase_pt':phase/2,'min_chroma_rmse':float(errs[i]**.5),'legacy_shift_pt':shift})
print(json.dumps(res,indent=2))
(Path(__file__).parent/'stripe-phase-diagnostic.json').write_text(json.dumps(res,indent=2)+'\n')
