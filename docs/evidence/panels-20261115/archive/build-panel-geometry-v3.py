from pathlib import Path
import subprocess,json,hashlib,os,time,sys,xml.etree.ElementTree as ET

NAME=sys.argv[1]
O=Path(__file__).resolve().parent
A=Path('/Users/kerrylee/.codex/worktrees/android-settings-glass-fixes/sleepy')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=json.loads((O/'panels-current-baseline-20261115/plan.json').read_text())
source_paths=[Path(p) for p in base['current_source_sha256']]
source_paths += [A/p for p in [
    'libraries/liquid-glass/runtime/src/androidMain/kotlin/com/lingion/sleepy/ui/component/liquidglass/LiquidGlassInputBlur.kt',
    'libraries/liquid-glass/runtime/src/androidMain/kotlin/com/lingion/sleepy/ui/component/liquidglass/LiquidGlassInputGeometry.kt',
    'third-party/kyant-backdrop/src/commonMain/kotlin/com/kyant/backdrop/BackdropEffectScope.kt',
    'third-party/kyant-backdrop/src/commonMain/kotlin/com/kyant/backdrop/DrawBackdropModifier.kt',
    'app/src/main/java/com/lingion/sleepy/ui/component/liquidglass/GlassHost.kt',
    'app/src/main/java/com/lingion/sleepy/ui/component/liquidglass/GlassFilterBands.kt',
]]
sources={str(p.relative_to(A)):sha(p) for p in source_paths}
cases=[
    ('app','testDebugUnitTest','com.lingion.sleepy.ui.component.liquidglass.GlassModalScrimTest','src/test/java'),
    ('app','testDebugUnitTest','com.lingion.sleepy.ui.component.liquidglass.LiquidGlassShaderContractTest','src/test/java'),
    ('libraries/liquid-glass/runtime','testAndroidHostTest','com.lingion.sleepy.ui.component.liquidglass.LiquidGlassInputBlurTest','src/androidHostTest/kotlin'),
    ('libraries/liquid-glass/runtime','testAndroidHostTest','com.lingion.sleepy.ui.component.liquidglass.LiquidGlassInputGeometryTest','src/androidHostTest/kotlin'),
    ('third-party/kyant-backdrop','testAndroidHostTest','com.kyant.backdrop.SampledEffectGeometryTest','src/commonTest/kotlin'),
]
tests={str(A/module/root/(cls.replace('.','/')+'.kt')):sha(A/module/root/(cls.replace('.','/')+'.kt')) for module,task,cls,root in cases}
cmd=['./gradlew',':liquid-glass-runtime:testAndroidHostTest','--tests','*LiquidGlassInputBlurTest','--tests','*LiquidGlassInputGeometryTest',':kyant-backdrop:testAndroidHostTest','--tests','*SampledEffectGeometryTest',':app:testDebugUnitTest','--tests','*GlassModalScrimTest','--tests','*LiquidGlassShaderContractTest',':app:assembleDebug',':app:assembleDebugAndroidTest','-Pandroid.injected.build.abi=arm64-v8a','--console=plain','--max-workers=3']
plan={'source_sha256':sources,'test_source_sha256':tests,'argv':cmd,'experiment_plan_sha256':sha(O/(NAME+'-plan.json')),'builder_sha256':sha(__file__)}
(O/(NAME+'-build-input.json')).write_text(json.dumps(plan,indent=2)+'\n')
env=os.environ.copy()
env['JAVA_HOME']='/Users/kerrylee/Library/Java/JavaVirtualMachines/jdk-21.jdk/Contents/Home'
env['ANDROID_HOME']='/Users/kerrylee/Library/Android/sdk'
start=time.time()
with (O/(NAME+'-build.log')).open('w') as log:
    result=subprocess.run(cmd,cwd=A,env=env,stdout=log,stderr=subprocess.STDOUT)
record={**plan,'exit_code':result.returncode,'elapsed_seconds':time.time()-start,'sources_unchanged':all(sha(A/p)==h for p,h in sources.items()),'test_sources_unchanged':all(sha(p)==h for p,h in tests.items()),'log_sha256':sha(O/(NAME+'-build.log')),'tests':[]}
if result.returncode==0:
    for module,task,cls,root in cases:
        p=A/module/'build/test-results'/task/('TEST-'+cls+'.xml')
        t=ET.parse(p).getroot()
        record['tests'].append({'file':str(p),'sha256':sha(p),'attributes':t.attrib})
    record['binaries']={str(p):sha(p) for p in [A/'app/build/intermediates/apk/debug/app-arm64-v8a-debug.apk',A/'app/build/intermediates/apk/androidTest/debug/app-debug-androidTest.apk']}
(O/(NAME+'-build-result.json')).write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k in ['exit_code','elapsed_seconds','sources_unchanged','test_sources_unchanged','tests','binaries']},indent=2),flush=True)
assert result.returncode==0 and record['sources_unchanged'] and record['test_sources_unchanged']
assert all(int(t['attributes']['failures'])==0 and int(t['attributes']['errors'])==0 for t in record['tests'])
