#!/usr/bin/env python3
"""Registered static material calibration only; no dynamic or test outputs."""
from pathlib import Path
import hashlib
import json
import platform
import shutil
import sys
import PIL
from PIL import Image

ROOT = Path(__file__).resolve().parent
S = ROOT.parent / 'glass-isolated-shapes-20261114'
A = Path('/Users/kerrylee/.codex/worktrees/android-settings-glass-fixes/sleepy')
COLORS = [(26,26,26),(77,77,77),(128,128,128),(179,179,179),(230,230,230),
          (232,48,48),(48,232,48),(48,48,232)]

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def write(p, data):
    p.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')

def main():
    out = ROOT / 'material-sweep'
    out.mkdir(exist_ok=False)
    protocol = {'schema':1,'protocol_id':'plain_flat_material_transfer_20261114_v1',
        'scope':'Calibration diagnostic: same native plain-scroll context, five gray and three chromatic constants. No motion, refractive geometry, control-size or held-out validation claim.',
        'dimensions_px':[750,1334],'world_dimensions_pt':[375,667],'pixels_per_pt':2,
        'colors_rgb':COLORS,'mode':'RGB','alpha':255,'raster':'Every pixel is the declared RGB code, no resampling or normalization.',
        'native_context':'Unchanged built testSwiftUITabViewDockPlainInputMatrix; independently relaunched sessions; retain requested and all effective traits without forcing material appearance.',
        'android_context':'Original preserved D46.5 APK, production default backdrop appearance disabled; REST only, no override.',
        'analysis':'Posthoc transfer diagnostic on original source pixels and previously frozen nominal base/glyph exclusions and inward-depth bins. Report theme and effective native appearance separately; one constant cannot identify alpha vs tint.',
        'comparison_limits':'No physical thickness/IOR inference; pixels and repeat frames are correlated; context and foreground differences remain.',
        'budget':{'native_sessions':16,'native_png':32,'android_scenes':16,'dynamic_clips':0},
        'icc_sha256':sha(S/'sRGB.icc'),'generator_sha256':sha(__file__),
        'python':platform.python_version(),'pillow':PIL.__version__}
    write(out/'protocol.json',protocol)
    icc=(S/'sRGB.icc').read_bytes()
    records=[]
    for i,rgb in enumerate(COLORS):
        key='gray_'+str(rgb[0]) if len(set(rgb))==1 else ['red','green','blue'][i-5]
        identity='ms%02d_%s'%(i+1,key)
        image=Image.new('RGB',(750,1334),rgb)
        file=out/(identity+'.png')
        image.save(file,icc_profile=icc)
        with Image.open(file) as read:
            assert read.mode=='RGB' and read.size==(750,1334)
            assert read.getextrema()==tuple((v,v) for v in rgb)
            assert read.info['icc_profile']==icc
        records.append({'id':identity,'file':file.name,'sha256':sha(file),
            'pixel_sha256':hashlib.sha256(image.tobytes()).hexdigest(),
            'rgb':list(rgb),'width':750,'height':1334,'mode':'RGB','role':'flat_material_calibration'})
    manifest={'schema':1,'set_id':'plain_flat_material_20261114_v1','split':'calibration',
        'protocol_id':protocol['protocol_id'],'protocol_sha256':sha(out/'protocol.json'),
        'dimensions_px':[750,1334],'color_space':'sRGB','opaque':True,
        'icc_profile_sha256':sha(S/'sRGB.icc'),'inputs':records}
    write(out/'manifest.json',manifest)
    binaries=ROOT/'prior-candidate-binaries';binaries.mkdir(exist_ok=False)
    prior=json.loads((S/'capture-plan.json').read_text())['identity']
    files=[('app/build/intermediates/apk/debug/app-arm64-v8a-debug.apk','main.apk',prior['candidate_main_apk_sha256']),
        ('app/build/intermediates/apk/androidTest/debug/app-debug-androidTest.apk','test.apk','51bf0cb70457e45c37d22997b2ffc24704b3e047c46516d98cde25c9c226aa6c')]
    for source,name,expected in files:
        assert sha(A/source)==expected
        shutil.copyfile(A/source,binaries/name)
        assert sha(binaries/name)==expected
    write(out/'generation-receipt.json',{'scope':protocol['scope'],'generator_sha256':sha(__file__),
        'protocol_sha256':sha(out/'protocol.json'),'manifest_sha256':sha(out/'manifest.json'),
        'checks':'8 exact RGB rasters, dimensions/mode/profile/hash and preserved APK hashes verified',
        'binaries':{name:sha(binaries/name) for _,name,_ in files}})
    print(json.dumps({'source_count':len(records),'directory':str(out),'scope':protocol['scope']}))

if __name__=='__main__':
    main()
