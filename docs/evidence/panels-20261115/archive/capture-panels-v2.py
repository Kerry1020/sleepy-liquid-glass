"""Current production-carrier calibration capture. No source/image fitting."""
from pathlib import Path
import hashlib,json,subprocess,time,sys
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
APP=Path('/Users/kerrylee/.codex/worktrees/android-settings-glass-fixes/sleepy')
ADB=['/Users/kerrylee/Library/Android/sdk/platform-tools/adb','-s','d3efcd6a']
RUN=sys.argv[1] if len(sys.argv)>1 else 'panels-alert-frost8-20261115'
assert all(c.isalnum() or c in '_-' for c in RUN)
DEST=OUT/RUN
DEST.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def adb(*args):return subprocess.check_output(ADB+list(args),text=True).strip()
def write(name,data): (DEST/name).write_text(json.dumps(data,indent=2)+'\n')
expected={'size':'Physical size: 1216x2640','density':'Physical density: 560\nOverride density: 476'}
original={k:adb('shell','wm',k) for k in expected}
write('display-before.json',original)
assert original==expected,original
build=Path(sys.argv[2]).resolve() if len(sys.argv)>2 else OUT/'alert-edge-frost8-build-result.json'
b=json.loads(build.read_text())
installed={}
for pkg,p in zip(['com.lingion.sleepy.debug','com.lingion.sleepy.debug.test'],b['binaries']):
    local=sha(p); assert local==b['binaries'][p]
    path=adb('shell','pm','path',pkg).splitlines();assert len(path)==1,path
    remote=path[0].removeprefix('package:')
    hashed=adb('shell','sha256sum',remote).split()[0];assert hashed==local,(pkg,hashed,local)
    installed[pkg]={'installed_path':remote,'sha256':hashed,'local_path':p}
paths=[APP/p for p in b['source_sha256']]
paths += [APP/'app/src/androidTest/java/com/lingion/sleepy/ui/component/NativeGlassParityCaptureTest.kt',APP/'app/src/main/java/com/lingion/sleepy/ui/component/liquidglass/GlassOverlays.kt',APP/'app/src/main/java/com/lingion/sleepy/ui/component/liquidglass/GlassControlModifier.kt',APP/'libraries/liquid-glass/runtime/src/androidMain/kotlin/com/lingion/sleepy/ui/component/liquidglass/LiquidGlassGeometry.kt']
for p,h in b['source_sha256'].items(): assert sha(APP/p)==h,p
sources={str(p):sha(p) for p in paths}
old=json.loads((ROOT/'artifacts/glass-thickness-profile-20261114/sheet-quantitative/analysis.json').read_text())
inputs={}
for s in old['scenes']:
    p=s['native_provenance']; fn=s['scene']+'.png';h=sha(p['bare_source_png']); assert h==p['bare_source_sha256']
    dh=adb('shell','sha256sum','/sdcard/Android/data/com.lingion.sleepy.debug/files/native-optics-20261114/'+fn).split()[0]
    assert dh==h,(fn,dh,h)
    inputs[fn]={'local_original':p['bare_source_png'],'sha256':h}
refs={str(p):sha(p) for root in [ROOT/'outputs/glass-native-parity-20261112/native-static-optics/rest',ROOT/'outputs/glass-native-parity-20261112/native-alert-optics-20261113/rest'] for p in root.glob('*.png') if 'sheet-rest' in p.name or 'alert-rest' in p.name}
assert len(refs)==16,len(refs)
cmd=['shell','am','instrument','-w','-r','-e','class','com.lingion.sleepy.ui.component.NativeGlassParityCaptureTest#captureStaticOpticalBackgroundMatrix','-e','glassStaticCapture','true','-e','glassStaticNativeInputDirectory','native-optics-20261114','-e','glassStaticNativeCanvas','true','-e','glassStaticSheetContentHeightDp','277.3','-e','glassStaticBackgrounds','fine_grid,color_stripes,tonal_blocks,synthetic_landscape','-e','glassStaticThemes','light,dark','-e','glassStaticSurfaces','share_sheet,alert','-e','glassStaticStates','rest','-e','glassStaticRunId',RUN,'com.lingion.sleepy.debug.test/com.lingion.sleepy.SleepyRenderTestRunner']
plan={'schema':1,'split':'historical-calibration','script_sha256':sha(__file__),'build_receipt':str(build),'build_receipt_sha256':sha(build),'installed':installed,'current_source_sha256':sources,'inputs':inputs,'native_refs_sha256':refs,'capture_argv':ADB+cmd,'expected_count':16,'expected_world_px':[750,1334],'expected_sheet_material_ltrb_px':[16,635,734,1318],'expected_alert_native_ax_ltrb_pt':[27.5,257.5,347.5,429.5],'analysis_policy':'No posthoc resize/recenter/warp. Raw encoded RGB and ICC-normalized sRGB retained separately. Source registration, exterior dimming, body, straight edges and corners separated. Native backdrop controls differ; lower sheet bands diagnostic only. Native AX is not an optical alpha contour. Static carrier fixture uses production wrappers and illustrative content, not full product data flow. No heldout inputs read. No universal parity acceptance threshold.','limits':['Candidate build receipt enumerates all registered current fixture and wrapper hashes; exact installed APK independently matched.','Historical source references validated by original session metadata rather than later mutable Swift source.']}
write('plan.json',plan);print('registered',RUN,flush=True)
try:
    subprocess.run(ADB+['shell','wm','size','750x1334'],check=True)
    subprocess.run(ADB+['shell','wm','density','320'],check=True)
    with (DEST/'device.log').open('w') as log:r=subprocess.run(ADB+cmd,stdout=log,stderr=subprocess.STDOUT)
    print((DEST/'device.log').read_text(),flush=True)
    subprocess.run(ADB+['pull','/sdcard/Android/data/com.lingion.sleepy.debug/files/glass-optical-backgrounds/'+RUN+'/.',str(DEST)],check=True,stdout=subprocess.DEVNULL)
    matrix=json.loads((DEST/'matrix.json').read_text());assert r.returncode==0 and matrix['status']=='passed',matrix.get('exception')
    assert len(matrix['captures'])==16
    for c in matrix['captures']:
        assert c['background_canvas']['native_input_mapping']['actual_scale_xy']==[1,1]
        if c['carrier']=='share_sheet':assert c['sheet_geometry_comparison']['actual_material_layout']['screen_rect_px']==[16,635,734,1318]
    write('capture-result.json',{'status':'captured_geometry_checked_not_parity_acceptance','count':16,'matrix_sha256':sha(DEST/'matrix.json'),'sources_unchanged':all(sha(p)==h for p,h in sources.items())})
    print('captured16; geometry checked',flush=True)
finally:
    restored=[]
    for args in [['shell','am','force-stop','com.lingion.sleepy.debug'],['shell','wm','size','reset'],['shell','wm','density','476']]:restored.append({'argv':args,'exit_code':subprocess.run(ADB+args).returncode})
    actual={k:adb('shell','wm',k) for k in expected};write('display-restored.json',{'commands':restored,'actual':actual,'matches_original':actual==original});assert actual==original
