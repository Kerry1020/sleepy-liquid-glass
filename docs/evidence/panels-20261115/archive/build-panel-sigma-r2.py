from pathlib import Path
import subprocess,json,hashlib,os,time,sys,xml.etree.ElementTree as ET
NAME=sys.argv[1]
R=Path(__file__).resolve().parents[2];O=Path(__file__).resolve().parent;A=Path('/Users/kerrylee/.codex/worktrees/android-settings-glass-fixes/sleepy')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=json.loads((O/'panels-current-baseline-20261115/plan.json').read_text())
sources={str(Path(p).relative_to(A)):sha(p) for p in base['current_source_sha256']}
extra=A/'libraries/liquid-glass/runtime/src/androidMain/kotlin/com/lingion/sleepy/ui/component/liquidglass/LiquidGlassInputBlur.kt'
sources[str(extra.relative_to(A))]=sha(extra)
tests={p:sha(p) for p in json.loads((R/'artifacts/glass-dock-model-20261114/material-correction-20261115/dark-rim-runtime-20261115/positive-headroom-build-result.json').read_text())['test_source_sha256']}
tests={str(A/'app/src/test/java/com/lingion/sleepy/ui/component/liquidglass/GlassModalScrimTest.kt'):sha(A/'app/src/test/java/com/lingion/sleepy/ui/component/liquidglass/GlassModalScrimTest.kt')}
tests[str(A/'libraries/liquid-glass/runtime/src/androidHostTest/kotlin/com/lingion/sleepy/ui/component/liquidglass/LiquidGlassInputBlurTest.kt')]=sha(A/'libraries/liquid-glass/runtime/src/androidHostTest/kotlin/com/lingion/sleepy/ui/component/liquidglass/LiquidGlassInputBlurTest.kt')
tests[str(A/'app/src/test/java/com/lingion/sleepy/ui/component/liquidglass/LiquidGlassShaderContractTest.kt')]=sha(A/'app/src/test/java/com/lingion/sleepy/ui/component/liquidglass/LiquidGlassShaderContractTest.kt')
cmd=['./gradlew',':liquid-glass-runtime:testAndroidHostTest','--tests','*LiquidGlassInputBlurTest',':app:testDebugUnitTest','--tests','*GlassModalScrimTest','--tests','*LiquidGlassShaderContractTest',':app:assembleDebug',':app:assembleDebugAndroidTest','-Pandroid.injected.build.abi=arm64-v8a','--console=plain','--max-workers=3']
plan={'source_sha256':sources,'test_source_sha256':tests,'argv':cmd,'experiment_plan_sha256':sha(O/(NAME+'-plan.json'))}
(O/(NAME+'-build-input.json')).write_text(json.dumps(plan,indent=2)+'\n')
env=os.environ.copy();env['JAVA_HOME']='/Users/kerrylee/Library/Java/JavaVirtualMachines/jdk-21.jdk/Contents/Home';env['ANDROID_HOME']='/Users/kerrylee/Library/Android/sdk'
start=time.time()
with (O/(NAME+'-build.log')).open('w') as log:result=subprocess.run(cmd,cwd=A,env=env,stdout=log,stderr=subprocess.STDOUT)
record={**plan,'exit_code':result.returncode,'elapsed_seconds':time.time()-start,'sources_unchanged':all(sha(A/p)==h for p,h in sources.items()),'log_sha256':sha(O/(NAME+'-build.log')),'tests':[]}
for p in [A/'app/build/test-results/testDebugUnitTest/TEST-com.lingion.sleepy.ui.component.liquidglass.GlassModalScrimTest.xml',A/'app/build/test-results/testDebugUnitTest/TEST-com.lingion.sleepy.ui.component.liquidglass.LiquidGlassShaderContractTest.xml',A/'libraries/liquid-glass/runtime/build/test-results/testAndroidHostTest/TEST-com.lingion.sleepy.ui.component.liquidglass.LiquidGlassInputBlurTest.xml']:
 t=ET.parse(p).getroot();record['tests'].append({'file':str(p),'sha256':sha(p),'attributes':t.attrib})
record['binaries']={str(p):sha(p) for p in [A/'app/build/intermediates/apk/debug/app-arm64-v8a-debug.apk',A/'app/build/intermediates/apk/androidTest/debug/app-debug-androidTest.apk']}
(O/(NAME+'-build-result.json')).write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k in ['exit_code','elapsed_seconds','sources_unchanged','tests','binaries']},indent=2),flush=True)
assert result.returncode==0 and record['sources_unchanged']
assert all(int(t['attributes']['failures'])==0 and int(t['attributes']['errors'])==0 for t in record['tests'])
