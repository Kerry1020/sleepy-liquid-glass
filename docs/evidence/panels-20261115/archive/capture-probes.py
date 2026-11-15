from pathlib import Path
import hashlib, json, subprocess, sys

P = Path(__file__).resolve().parent
A = Path('/Users/kerrylee/.codex/worktrees/android-settings-glass-fixes/sleepy')
ADB = ['/Users/kerrylee/Library/Android/sdk/platform-tools/adb', '-s', 'd3efcd6a']
RUN = sys.argv[1] if len(sys.argv) > 1 else 'panels-nonperiodic-baseline-20261115'
BUILD = P / (sys.argv[2] if len(sys.argv) > 2 else 'panel-probes-android-build-result.json')
DEST = P / RUN
DEST.mkdir(exist_ok=False)
INPUT = P / 'panel-probes-preparation'
DIRECTORY = 'panel-calibration-20261115'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def adb(*args): return subprocess.check_output(ADB + list(args), text=True).strip()
def write(name, value): (DEST / name).write_text(json.dumps(value, indent=2) + '\n')

build = json.loads(BUILD.read_text())
for path, expected in build['source_sha256'].items(): assert sha(A / path) == expected, path
manifest = json.loads((INPUT / 'android-manifest.json').read_text())
assert manifest['split'] == 'calibration' and len(manifest['inputs']) == 2
expected_display = {'size': 'Physical size: 1216x2640', 'density': 'Physical density: 560\nOverride density: 476'}
original = {k: adb('shell', 'wm', k) for k in expected_display}
write('display-before.json', original)
assert original == expected_display
installed = {}
for (package, (path, expected)) in zip(['com.lingion.sleepy.debug', 'com.lingion.sleepy.debug.test'], build['binaries'].items()):
    assert sha(path) == expected
    subprocess.run(ADB + ['install', '-t', '-r', path], check=True, stdout=subprocess.DEVNULL)
    remote = adb('shell', 'pm', 'path', package).removeprefix('package:')
    actual = adb('shell', 'sha256sum', remote).split()[0]
    assert actual == expected
    installed[package] = dict(local_path=path, sha256=actual, remote_path=remote)
remote_dir = '/sdcard/Android/data/com.lingion.sleepy.debug/files/' + DIRECTORY
adb('shell', 'mkdir', '-p', remote_dir)
subprocess.run(ADB + ['push', str(INPUT / 'android-manifest.json'), remote_dir + '/manifest.json'], check=True, stdout=subprocess.DEVNULL)
for entry in manifest['inputs']:
    path = INPUT / 'inputs' / entry['file']
    assert sha(path) == entry['sha256']
    subprocess.run(ADB + ['push', str(path), remote_dir + '/' + entry['file']], check=True, stdout=subprocess.DEVNULL)
    assert adb('shell', 'sha256sum', remote_dir + '/' + entry['file']).split()[0] == entry['sha256']
cmd = ['shell', 'am', 'instrument', '-w', '-r', '-e', 'class', 'com.lingion.sleepy.ui.component.NativeGlassParityCaptureTest#captureStaticOpticalBackgroundMatrix',
       '-e', 'glassStaticCapture', 'true', '-e', 'glassStaticExternalInputsDirectory', DIRECTORY,
       '-e', 'glassStaticNativeCanvas', 'true', '-e', 'glassStaticSheetContentHeightDp', '277.3',
       '-e', 'glassStaticBackgrounds', ','.join(manifest['selected_ids']), '-e', 'glassStaticThemes', 'light',
       '-e', 'glassStaticSurfaces', 'share_sheet,alert', '-e', 'glassStaticStates', 'rest', '-e', 'glassStaticRunId', RUN,
       'com.lingion.sleepy.debug.test/com.lingion.sleepy.SleepyRenderTestRunner']
write('capture-plan.json', dict(build_receipt=str(BUILD), build_receipt_sha256=sha(BUILD), manifest=manifest,
    manifest_sha256=sha(INPUT / 'android-manifest.json'), installed=installed, source_sha256=build['source_sha256'],
    argv=ADB + cmd, expected_count=4, purpose='Nonperiodic static calibration feasibility; no parity acceptance. Source PNGs match native originals; backing live UI differs and is separately audited.'))
try:
    adb('shell', 'wm', 'size', '750x1334')
    adb('shell', 'wm', 'density', '320')
    with (DEST / 'device.log').open('w') as log:
        result = subprocess.run(ADB + cmd, stdout=log, stderr=subprocess.STDOUT)
    subprocess.run(ADB + ['pull', '/sdcard/Android/data/com.lingion.sleepy.debug/files/glass-optical-backgrounds/' + RUN + '/.', str(DEST)], check=True, stdout=subprocess.DEVNULL)
    matrix = json.loads((DEST / 'matrix.json').read_text())
    assert result.returncode == 0 and matrix['status'] == 'passed', matrix.get('exception')
    assert len(matrix['captures']) == 4
    for capture in matrix['captures']:
        assert capture['background_canvas']['native_input_mapping']['actual_scale_xy'] == [1, 1]
        if capture['carrier'] == 'share_sheet':
            assert capture['sheet_geometry_comparison']['actual_material_layout']['screen_rect_px'] == [16, 635, 734, 1318]
    write('capture-result.json', dict(status='captured_not_parity_acceptance', count=4, matrix_sha256=sha(DEST / 'matrix.json'), sources_unchanged=all(sha(A / path) == h for path, h in build['source_sha256'].items())))
    print('captured4, geometry/source checked', flush=True)
finally:
    adb('shell', 'am', 'force-stop', 'com.lingion.sleepy.debug')
    adb('shell', 'wm', 'size', 'reset')
    adb('shell', 'wm', 'density', '476')
    restored = {k: adb('shell', 'wm', k) for k in expected_display}
    write('display-restored.json', dict(actual=restored, matches_original=restored == original))
    assert restored == original
