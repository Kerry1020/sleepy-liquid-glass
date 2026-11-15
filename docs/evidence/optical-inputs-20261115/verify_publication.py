#!/usr/bin/env python3
"""Verify public bytes, frozen input metadata and links; no optical evaluation.

Only standard-library reads and one JSON report write are performed. No images
are decoded, generators run, devices queried, network accessed or builds invoked.
"""
import ast
import gzip
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote

HERE = Path(__file__).resolve().parent
LIBRARY = HERE.parents[2]
ARCHIVE = HERE / 'archive'
IMAGES = LIBRARY / 'docs/images/optical-inputs-20261115'
PRIMARY = [LIBRARY / 'docs/controlled-optical-studies.md', HERE / 'PUBLICATION.md']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def relative(path):
    return path.relative_to(LIBRARY).as_posix()


def markdown_links(file):
    text = re.sub(r'```.*?```', '', file.read_text(), flags=re.S)
    links, missing = [], []
    for match in re.finditer(r'!?\[[^\]]*\]\(([^\n)]+)\)', text):
        target = match.group(1).strip().split(' "', 1)[0].strip('<>')
        if not target or target.startswith(('#', 'http:', 'https:', 'mailto:', 'data:')):
            continue
        local = unquote(target.split('#', 1)[0])
        if not local:
            continue
        path = (file.parent / local).resolve()
        entry = {'document': relative(file), 'target': target}
        links.append(entry)
        if not path.exists():
            missing.append(entry)
    return links, missing


def main():
    failures, checks = [], []

    def check(condition, message):
        checks.append(message)
        if not condition:
            failures.append(message)

    sources = json.loads((HERE / 'sources.json').read_text())
    check(sources['unopened_outputs_accessed'] is False, 'Declared unopened outputs remain unaccessed')
    check(sources['device_or_build_operations'] is False, 'Declared export has no device/build operations')
    source_bytes = {}
    for record in sources['records']:
        path = LIBRARY / record['published']
        check(path.is_file(), 'Published file exists: ' + record['published'])
        if not path.is_file():
            continue
        encoded = path.read_bytes()
        check(len(encoded) == record['published_bytes'] and sha(encoded) == record['published_sha256'],
              'Published byte identity: ' + record['source_namespace'])
        original = gzip.decompress(encoded) if record['processing'] == 'deterministic lossless gzip' else encoded
        check(len(original) == record['source_bytes'] and sha(original) == record['source_sha256'],
              'Original/decompressed identity: ' + record['source_namespace'])
        source_bytes[record['source_namespace']] = original

    input_records, oracle_references = 0, 0
    for packet in ['glass-noise-20261114', 'glass-isolated-shapes-20261114']:
        freeze = json.loads(source_bytes[packet + '/freeze.json'])
        for name, expected in freeze['file_sha256'].items():
            check(sha(source_bytes[packet + '/' + name]) == expected,
                  'Original freeze binds generator input: ' + packet + '/' + name)
        for split in ['calibration', 'test']:
            manifest = json.loads(source_bytes[packet + '/' + split + '/manifest.json'])
            check(manifest['protocol_sha256'] == sha(source_bytes[packet + '/protocol.json']),
                  'Manifest binds protocol: ' + packet + '/' + split)
            check(manifest['freeze_sha256'] == sha(source_bytes[packet + '/freeze.json']),
                  'Manifest binds freeze: ' + packet + '/' + split)
            check(manifest['icc_profile_sha256'] == sha(source_bytes[packet + '/sRGB.icc']),
                  'Manifest binds ICC: ' + packet + '/' + split)
            check(manifest['dimensions_px'] == [750, 1334] and manifest['opaque'] is True,
                  'Input world contract: ' + packet + '/' + split)
            for entry in manifest['inputs']:
                input_records += 1
                prefix = packet + '/' + split + '/'
                image_key = prefix + entry['file']
                if image_key in source_bytes:
                    check(sha(source_bytes[image_key]) == entry['sha256'], 'Published input PNG identity: ' + image_key)
                for filekey, hashkey in [('points_file', 'points_sha256'), ('geometry_file', 'geometry_sha256')]:
                    if filekey not in entry:
                        continue
                    key = prefix + entry[filekey]
                    oracle_references += 1
                    check(key in source_bytes and sha(source_bytes[key]) == entry[hashkey],
                          'Published input oracle identity: ' + key)
                    if key in source_bytes and filekey == 'points_file':
                        points = json.loads(source_bytes[key])
                        check(points['image_sha256'] == entry['sha256'] and len(points['dots']) == entry['point_count'],
                              'Dot oracle binds generated input: ' + key)

    figure_manifest = json.loads((HERE / 'figure-manifest.json').read_text())
    check(sha((HERE / 'figure-data.json').read_bytes()) == figure_manifest['figure_data_sha256'],
          'New figure numerical data identity')
    for figure in figure_manifest['figures']:
        path = LIBRARY / figure['published']
        check(path.is_file() and sha(path.read_bytes()) == figure['sha256'], 'Figure byte identity: ' + figure['published'])
        for source in figure.get('sources', []):
            if 'archive' in source:
                origin = HERE / source['archive']
                check(origin.is_file() and sha(origin.read_bytes()) == source['sha256'],
                      'Figure numerical provenance: ' + source['archive'])

    runtime = json.loads((HERE / 'runtime-source-identities.json').read_text())
    for record in runtime['sources']:
        path = LIBRARY / record['path']
        data = path.read_bytes()
        check(len(data) == record['bytes'] and sha(data) == record['sha256'],
              'Runtime snapshot identity: ' + record['path'])

    rebuild = json.loads((HERE / 'rebuild-verification.json').read_text())
    check(rebuild['status'] == 'passed' and rebuild['input_count'] == 40,
          'Actual source-only reconstruction passed for all40 registered inputs')
    check(rebuild['helper_sha256'] == sha((HERE / 'rebuild_inputs.py').read_bytes()),
          'Reconstruction receipt binds the published helper source')
    check(rebuild['registered_manifests_matched'] == 4 and
          all(code == 0 for code in rebuild['original_generator_generate_and_verify_exit_codes']),
          'Original generate/verify actions and all4 manifests matched')
    check(all(r['png_matches'] and r['pixels_match'] for r in rebuild['flat_source_only_checks']),
          'Flat source-only reconstructions match original PNG/pixel identities')

    primary_links, missing_primary = [], []
    for document in PRIMARY:
        links, missing = markdown_links(document)
        primary_links.extend(links)
        missing_primary.extend(missing)
    check(not missing_primary, 'All local file/image links in the two new documents resolve')
    archival_links, missing_archival = [], []
    for document in sorted(ARCHIVE.rglob('*.md')):
        links, missing = markdown_links(document)
        archival_links.extend(links)
        missing_archival.extend(missing)

    files = sorted([p for base in [HERE, IMAGES] for p in base.rglob('*') if p.is_file()])
    forbidden_extensions = {'.apk', '.aab', '.ipa', '.mov', '.mp4', '.m4v', '.xcresult', '.zip'}
    forbidden_segments = {'build', '.gradle', 'DerivedData', '__pycache__', '.pytest_cache'}
    forbidden = [relative(p) for p in files if p.suffix.lower() in forbidden_extensions or
                 any(part in forbidden_segments for part in p.parts)]
    check(not forbidden, 'No build binary/cache/video bundles in the publication packet')
    parsed_scripts = []
    for script in sorted(HERE.rglob('*.py')):
        try:
            ast.parse(script.read_text(), filename=str(script))
            parsed_scripts.append(relative(script))
        except SyntaxError as error:
            failures.append('Python syntax: ' + relative(script) + ': ' + str(error))
    report = {
        'schema': 1, 'status': 'passed' if not failures else 'failed',
        'verification_scope': 'Published byte identity, input manifest/oracle relationships, current source snapshot, Python AST and local documentation links; no optical evaluation',
        'source_records': len(sources['records']),
        'source_bytes': sum(r['source_bytes'] for r in sources['records']),
        'published_record_bytes': sum(r['published_bytes'] for r in sources['records']),
        'omitted_numeric_identities': len(sources['omitted_numeric_identities']),
        'registered_input_manifest_records': input_records,
        'published_oracle_references': oracle_references,
        'new_figure_files': len(figure_manifest['figures']),
        'runtime_sources': len(runtime['sources']),
        'actual_input_reconstruction': {'status': rebuild['status'], 'input_count': rebuild['input_count'],
                                       'receipt': relative(HERE / 'rebuild-verification.json')},
        'primary_local_links': len(primary_links), 'missing_primary_local_links': missing_primary,
        'archival_link_observations': {
            'status': 'historical byte-exact Markdown, outside complete-link gate',
            'local_links': len(archival_links), 'missing_local_links': missing_archival},
        'forbidden_files': forbidden, 'python_ast_files': parsed_scripts,
        'checks': len(checks), 'failures': failures,
        'not_executed': ['build/device operations', 'capture image decoding',
                         'new optical fitting or heldout evaluation',
                         'dynamic v4 acquisition and frame analysis'],
    }
    (HERE / 'verification-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    files = [p for base in [HERE, IMAGES] for p in base.rglob('*') if p.is_file()] + [PRIMARY[0]]
    summary = {'status': report['status'], 'source_records': report['source_records'],
               'figures': report['new_figure_files'], 'checks': len(checks),
               'new_document_local_links': len(primary_links), 'new_document_missing_links': len(missing_primary),
               'historical_missing_links_outside_gate': len(missing_archival),
               'total_files_in_new_packet_and_document': len(files),
               'total_bytes_in_new_packet_and_document': sum(p.stat().st_size for p in files),
               'failures': failures, 'report': relative(HERE / 'verification-report.json')}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == '__main__':
    sys.exit(main())
