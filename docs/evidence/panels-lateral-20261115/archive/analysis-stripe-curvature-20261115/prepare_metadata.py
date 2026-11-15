#!/usr/bin/env python3
"""Read old metadata/original bytes only. No image decoder or pixel inspection."""
import hashlib
import json
from pathlib import Path
import struct

HERE=Path(__file__).resolve().parent
P=HERE.parent
ROOT=P.parent.parent
PARITY=ROOT/'outputs/glass-native-parity-20261112'
ANDROID=P/'panels-alert-floor-budget-history-r2-20261115'
NATIVE_ALERT=PARITY/'native-alert-optics-20261113'
NATIVE_SHEET=PARITY/'native-static-optics'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def record(path):
    path=Path(path).resolve()
    data=path.read_bytes()
    result={'path':str(path),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
    if path.suffix=='.png':
        assert data[:8]==b'\x89PNG\r\n\x1a\n'
        result['IHDR_fields_without_decode']=list(struct.unpack('>IIBBBBB',data[16:29]))
        result['pixel_decode_performed']=False
    return result


def write(name,value):
    (HERE/name).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')


def main():
    current_plan=json.loads((ANDROID/'plan.json').read_text())
    matrix=json.loads((ANDROID/'matrix.json').read_text())
    history=json.loads((P/'analysis-rim-evidence/budget-history/analysis.json').read_text())
    predecode=json.loads((P/'analysis-rim-evidence/budget-history-predecode.json').read_text())
    delivery=json.loads((NATIVE_ALERT/'delivery-validation.json').read_text())
    native_obs={r['condition'].replace('/','-'):r for r in delivery['observations']}
    rows=[]
    for theme in ('light','dark'):
        obs=native_obs['color_stripes-'+theme]
        alert_session=NATIVE_ALERT/'traces'/obs['run']
        sheet_source=Path(current_plan['inputs']['color_stripes-'+theme+'.png']['local_original'])
        sheet_session=sheet_source.parent
        session=json.loads((sheet_session/'session.json').read_text())
        config=[json.loads(l) for l in (sheet_session/'trace.jsonl').read_text().splitlines()
                if '"reference-configuration"' in l]
        assert len(config)==1 and config[0]['scene']=='presentations'
        assert config[0]['background']['id']=='color_stripes'
        for carrier in ('alert','share_sheet'):
            native_carrier='sheet' if carrier=='share_sheet' else 'alert'
            cap=next(c for c in matrix['captures'] if c['background']=='color_stripes'
                     and c['theme']==theme and c['carrier']==carrier and c['phase']=='rest')
            files={k:record(ANDROID/cap[k]) for k in ('window_png','screen_png')}
            files['background_screen']=record(ANDROID/('color_stripes-'+theme+'-background-screen.png'))
            files['background_window']=record(ANDROID/('color_stripes-'+theme+'-background-window.png'))
            if carrier=='alert':
                scene=next(s for s in history['scenes'] if s['scene']=='color_stripes-'+theme)
                files.update({key:record(value['path']) for key,value in scene['files'].items()
                              if key in ('native','native_before','native_source')})
                files['native_AX']=record(NATIVE_ALERT/'rest'/f'alert-optics-color_stripes-{theme}-alert-rest-accessibility.txt')
                files['native_session']=record(alert_session/'session.json')
                files['native_trace']=record(alert_session/'trace.jsonl')
                rejected=ANDROID/f'color_stripes-{theme}-alert-rest-rejected-display.png'
                files['rejected_display_NOT_PRIMARY']=record(rejected)
                native_meta={'run':obs['run'],'session_os':obs['session']['os'],
                    'configuration':obs['configuration'],'AX_pane_record':obs['alertAX'],
                    'rest_image_sha256_in_delivery':obs['alertRest']['imageSHA256'],
                    'source_phase_policy':'Native before, source, REST and later after-confirm/cancel are distinct phases; do not replace one with another.'}
            else:
                files['native']=record(NATIVE_SHEET/'rest'/f'optics-color_stripes-{theme}-presentations-sheet-rest.png')
                files['native_before']=record(NATIVE_SHEET/'rest'/f'optics-color_stripes-{theme}-presentations-rest.png')
                files['native_source']=record(sheet_source)
                files['native_AX']=record(NATIVE_SHEET/'rest'/f'optics-color_stripes-{theme}-presentations-sheet-rest-accessibility.txt')
                files['native_session']=record(sheet_session/'session.json')
                files['native_trace']=record(sheet_session/'trace.jsonl')
                native_meta={'run':sheet_session.name,'session_os':session['os'],'configuration':config[0],
                    'source_phase_policy':'Native presentations-rest is before Sheet; full source differs from backing UI. No native repeat or clean dismiss-after is registered for this diagnostic.'}
            assert files['native_source']['sha256']=='be768f215b3818c5c276f3fa136bc8c67409aab57f9046795730c801a3412b93'
            for key in ('screen_png','window_png'):
                actual=files[key]
                assert predecode['files'][actual['path']]==actual['sha256']
            rows.append({'scene':'color_stripes-'+theme+'-'+native_carrier,
                'role':'Previously observed historical calibration; current production-source candidate mixed/unaccepted',
                'files':files,'native_metadata':native_meta,
                'android_metadata':{k:cap.get(k) for k in ('background_canvas','window_geometry',
                    'actual_alert_layout','sheet_geometry_comparison','measurements','display_readiness')},
                'primary_track_policy':'Use original complete screen only when its provenance/readiness supports it. Window is a separate original track in measured coordinates; never fabricate/pad a full screen from it. Rejected display is not primary.'})
    build_receipt=Path(current_plan['build_receipt'])
    assert sha(build_receipt)==current_plan['build_receipt_sha256']
    current_sources=[]
    for path,expected in current_plan['current_source_sha256'].items():
        if Path(path).name in ('LiquidGlassStyle.kt','LiquidGlassShader.kt','LiquidGlassEffect.kt','liquid_glass.agsl','LiquidGlassGeometry.kt'):
            item=record(path);item['capture_plan_sha256']=expected
            item['matches_capture_source']=item['sha256']==expected
            current_sources.append(item)
    protocol_paths=[HERE/'prepare_metadata.py',ANDROID/'plan.json',ANDROID/'matrix.json',ANDROID/'capture-result.json',
        build_receipt,NATIVE_ALERT/'delivery-validation.json',NATIVE_ALERT/'capture-manifest.json',
        NATIVE_SHEET/'rest-attachment-index.json',NATIVE_SHEET/'background-input-consistency.json',
        P/'analysis-alert-baseline/analyze_alert_baseline.py',P/'analysis-rim-evidence/budget_history_driver.py',
        P/'analysis-rim-evidence/budget_analyze_history.py',P/'analysis-rim-evidence/budget-history-predecode.json',
        P/'analysis-rim-evidence/budget-history-decode.json',P/'analysis-rim-evidence/budget-history/analysis.json',
        P/'analysis-rim-evidence/budget-manifest.json',P/'public-runtime-sync.json',
        P/'analysis-mapping-audit/paired-slope-feasibility-analysis/analysis.py',
        P/'analysis-mapping-audit/paired-slope-feasibility-analysis/implementation-freeze.json']
    write('source-index.json',{'schema':1,'status':'PREDECODE PREPARATION ONLY — NO CONTOUR RESULTS',
        'real_png_pixels_decoded':0,'conditions':rows,'protocol_and_metadata_hashes':[record(p) for p in protocol_paths],
        'android_binary':current_plan['installed'],'current_source_checks':current_sources,
        'binary_limit':'Installed APK hashes are historical receipt facts, not freshly read from a device; no build/device/Git performed.',
        'baseline_separate':record(P/'panels-current-baseline-20261115/matrix.json'),
        'source_geometry':'Opaque18pt stripes at global x=18*k,6-color period108pt; fixed source original hash retained. Source phase must be checked against before/context, not inferred from matching colors.',
        'prior_analysis_limit':'Historical blue-opponent centroid in x60..96 is response-only; it is not a colored boundary identity or unique2D correspondence.'})
    print(json.dumps({'conditions':len(rows),'real_pixels_decoded':0,
                      'all_current_source_hashes_match':all(r['matches_capture_source'] for r in current_sources),
                      'source_index_sha256':sha(HERE/'source-index.json')},indent=2))


if __name__=='__main__':
    main()
