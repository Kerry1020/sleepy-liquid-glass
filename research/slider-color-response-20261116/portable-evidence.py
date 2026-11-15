#!/usr/bin/env python3
"""Export original evidence bytes and replay the frozen analyzer without rewriting receipts.

export --study STUDY --output STUDY/evidence [--reference-analysis STUDY/analysis]
replay --study STUDY --evidence STUDY/evidence --output NEW [--compare ANALYSIS]
self-test

Trace/xcresult bytes are never read or copied. Trace identities are declarations
retained verbatim from the original capture receipt, not reverified archives.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sys
import tempfile
import types


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def valid_sha(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def relative_path(value):
    require(isinstance(value, str) and value and "\\" not in value, "invalid relative evidence path")
    p = PurePosixPath(value)
    require(not p.is_absolute() and p.as_posix() == value and ".." not in p.parts and value != ".",
            "noncanonical or escaping evidence path: " + value)
    return Path(value)


def exportable_artifact(relative):
    p = relative_path(relative)
    require(not any(part.endswith(".xcresult") for part in p.parts), "xcresult export forbidden")
    require(p.suffix == ".png" or p.name in
            {"index-strict.json", "endpoint-verification-strict.json", "capture-events.jsonl", "session.json"},
            "unsupported artifact; trace/xcresult bytes must never be read: " + relative)
    return p


def load_analyzer(study):
    study = Path(study).resolve()
    path = study / "analyze-response.py"
    frozen = read(study / "freeze.json")
    require(sha(path) == frozen["files"]["analyze-response.py"], "executing analyzer differs from freeze")
    module = types.ModuleType("frozen_slider_color_response")
    module.__file__ = str(path)
    # Compile the original source directly: no source edits or __pycache__ writes.
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def trace_declarations(receipt):
    rows = receipt["lossless_trace_storage"]
    require(isinstance(rows, list) and len(rows) == 2, "expected two trace identity declarations")
    seen = set()
    for row in rows:
        path = relative_path(row["archive"])
        require(path.parts[0] == "traces" and path.name == "trace.jsonl.gz", "unexpected trace archive declaration")
        require(row["archive"] not in seen, "duplicate trace archive declaration")
        seen.add(row["archive"])
        require(valid_sha(row["original_sha256"]) and valid_sha(row["archive_sha256"]), "missing declared trace hashes")
        require(all(type(row[k]) is int and row[k] > 0 for k in ("original_bytes", "archive_bytes")),
                "invalid declared trace sizes")
    return rows


def add_plan(plan, destination, source, study, expected=None):
    relative_path(destination)
    source = Path(source).resolve()
    require(source.is_file() and source.is_relative_to(study), "source is not a current study file")
    digest = sha(source)
    require(expected is None or digest == expected, "source changed before export: " + str(source))
    row = {"sha256": digest, "bytes": source.stat().st_size,
           "source_relative_study_path": source.relative_to(study).as_posix()}
    require(destination not in plan or plan[destination][1] == row, "conflicting export destination")
    plan[destination] = (source, row)


def copy_exact(plan, output):
    require(not output.exists(), "export output exists; never overwrite prior evidence")
    output.mkdir(parents=True)
    for relative, (source, row) in plan.items():
        data = source.read_bytes()
        require(hashlib.sha256(data).hexdigest() == row["sha256"] and len(data) == row["bytes"],
                "source changed during export: " + str(source))
        target = output / relative_path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        require(sha(target) == row["sha256"], "export copy hash mismatch")


def export_evidence(study, output, reference=None):
    study, output = Path(study).resolve(), Path(output).resolve()
    module = load_analyzer(study)
    frozen = module.load_freeze(study)
    plan, rounds = {}, {}
    for name in module.ROUNDS:
        parent = study / "rounds" / name / "native-r1"
        cp = parent / "receipt.json"
        receipt = read(cp)
        source = study / "inputs/rounds" / name
        role = {"spec_sha256": sha(source / "shape-spec.json"),
                "manifest_sha256": sha(source / "inputs/manifest.json")}
        module.check_capture_identity(receipt, frozen, name, role)
        for relative in receipt["analysis_artifacts"]:
            exportable_artifact(relative)  # Reject trace reads before the original hash verifier.
        paths = module.verify_capture_artifacts(parent, receipt,
            [parent / "index-strict.json", parent / "endpoint-verification-strict.json"])
        index, strict = read(parent / "index-strict.json"), read(parent / "endpoint-verification-strict.json")
        module.check_receipt(strict)
        require(index["status"] == "passed" and index["platform"] == "ios"
                and not index.get("synthetic_fixture", False), "only actual accepted native index may be exported")
        require(len(index["captures"]) == 1 and index["captures"][0]["stage_id"] == "full100", "unexpected export stage")
        capture = index["captures"][0]
        pngs = []
        for key, hkey in (("png", "sha256"), ("flat_png", "flat_sha256")):
            path = module.resolve(capture[key], parent).resolve()
            require(path in paths, "indexed original PNG absent from capture artifact receipt")
            module.bound_file(path, capture[hkey])
            pngs.append(path)
        require(len(set(pngs)) == 2 and sum(Path(p).suffix == ".png" for p in receipt["analysis_artifacts"]) == 2,
                "export must contain exactly the two indexed original PNGs")
        prefix = Path("rounds") / name / "native-r1"
        add_plan(plan, (prefix / "receipt.json").as_posix(), cp, study)
        for relative, digest in receipt["analysis_artifacts"].items():
            add_plan(plan, (prefix / relative_path(relative)).as_posix(), parent / relative, study, digest)
        rounds[name] = {"capture_receipt": (prefix / "receipt.json").as_posix(),
                        "lossless_trace_storage": trace_declarations(receipt)}
    reference_files = []
    if reference is not None:
        reference = Path(reference).resolve()
        require((reference / "analysis.json").is_file(), "missing reference analysis.json")
        for filename in ("analysis.json", "original-pixels.npz"):
            if (reference / filename).is_file():
                destination = "reference-analysis/" + filename
                add_plan(plan, destination, reference / filename, study)
                reference_files.append(destination)
    manifest = {"schema": 1, "format": "original-byte-portable-slider-evidence",
                "old_study_root": str(study), "freeze_sha256": frozen["sha256"],
                "analyzer_sha256": sha(study / "analyze-response.py"),
                "protocol_sha256": sha(study / "PROTOCOL.md"), "export_tool_sha256": sha(__file__),
                "files": {key: row for key, (_, row) in sorted(plan.items())}, "rounds": rounds,
                "reference_analysis_files": reference_files,
                "trace_policy": "Only original capture-receipt hash/size declarations retained; trace and xcresult bytes never read or copied."}
    copy_exact(plan, output)
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    verify_exported_files(output, manifest)
    result = {"status": "original_bytes_exported", "manifest": str(manifest_path),
              "manifest_sha256": sha(manifest_path), "files": len(plan), "rounds": len(rounds),
              "bytes": sum(row["bytes"] for _, row in plan.values()), "freeze_sha256": frozen["sha256"]}
    print(json.dumps(result))
    return 0


def verify_exported_files(evidence, manifest):
    evidence = Path(evidence).resolve()
    files = manifest["files"]
    require(isinstance(files, dict) and files, "empty portable file manifest")
    seen = set()
    for relative, row in files.items():
        rel = relative_path(relative)
        require(rel.parts[0] in ("rounds", "reference-analysis"), "unsupported portable file location")
        if rel.parts[0] == "rounds":
            require(len(rel.parts) >= 4 and rel.parts[2] == "native-r1", "unexpected portable capture directory")
            artifact = Path(*rel.parts[3:]).as_posix()
            if artifact != "receipt.json":
                exportable_artifact(artifact)
        else:
            require(len(rel.parts) == 2 and rel.parts[1] in {"analysis.json", "original-pixels.npz"},
                    "unexpected reference-analysis artifact")
        path = (evidence / rel).resolve()
        require(path.is_relative_to(evidence) and path not in seen, "portable path escapes or aliases")
        seen.add(path)
        require(valid_sha(row["sha256"]) and type(row["bytes"]) is int and row["bytes"] >= 0,
                "invalid portable file hash/size")
        require(path.is_file() and path.stat().st_size == row["bytes"] and sha(path) == row["sha256"],
                "missing or changed portable original: " + relative)
        relative_path(row["source_relative_study_path"])
    actual = {p.resolve() for folder in ("rounds", "reference-analysis")
              if (evidence / folder).is_dir() for p in (evidence / folder).rglob("*") if p.is_file()}
    require(actual == seen, "unbound extra file or missing portable file")


class RoundRoot:
    """Route only load_round's first /rounds lookup; preserve current verifier paths."""
    def __init__(self, study, evidence):
        self.study, self.evidence = Path(study), Path(evidence)

    def __truediv__(self, value):
        return self.evidence / "rounds" if value == "rounds" else self.study / value

    @property
    def parent(self):
        return self.study.parent


def install_replay_mapping(module, study, evidence, old_study):
    original_load, original_resolve = module.load_round, module.resolve
    old_rounds = Path(old_study) / "rounds"
    new_rounds = Path(evidence) / "rounds"

    def mapped_resolve(path, parent):
        p = Path(path)
        if p.is_absolute():
            canonical = Path(os.path.normpath(str(p)))
            if canonical.is_relative_to(old_rounds):
                return new_rounds / canonical.relative_to(old_rounds)
        return original_resolve(path, parent)

    def mapped_load(root, name, role, frozen):
        require(Path(root).resolve() == Path(study).resolve(), "unexpected replay study root")
        return original_load(RoundRoot(study, evidence), name, role, frozen)

    module.resolve, module.load_round = mapped_resolve, mapped_load
    return original_load, original_resolve


def normalized_report(value, study_roots, round_roots):
    if isinstance(value, dict):
        return {k: normalized_report(v, study_roots, round_roots) for k, v in value.items()}
    if isinstance(value, list):
        return [normalized_report(v, study_roots, round_roots) for v in value]
    if isinstance(value, str) and value.startswith("/"):
        p = Path(value)
        for root in round_roots:
            if p.is_relative_to(root):
                return "<rounds>/" + p.relative_to(root).as_posix()
        for root in study_roots:
            if p.is_relative_to(root):
                return "<study>/" + p.relative_to(root).as_posix()
    return value


def compare_analysis(reference, output, study, evidence, old_study):
    import numpy as np
    reference, output = Path(reference), Path(output)
    roots = [Path(old_study), Path(study)]
    round_roots = [Path(evidence) / "rounds", Path(old_study) / "rounds", Path(study) / "rounds"]
    before = normalized_report(read(reference / "analysis.json"), roots, round_roots)
    after = normalized_report(read(output / "analysis.json"), roots, round_roots)
    result = {"normalized_json_exact_equal": json.dumps(before, sort_keys=True, allow_nan=False) == json.dumps(after, sort_keys=True, allow_nan=False),
              "path_normalization": "Only absolute paths under declared old/current study and round roots.",
              "arrays": {}}
    left, right = reference / "original-pixels.npz", output / "original-pixels.npz"
    require(left.is_file() == right.is_file(), "reference/replay array archive presence differs")
    if left.is_file():
        with np.load(left, allow_pickle=False) as a, np.load(right, allow_pickle=False) as b:
            result["array_keys_exact_equal"] = set(a.files) == set(b.files)
            for key in sorted(set(a.files) | set(b.files)):
                result["arrays"][key] = key in a.files and key in b.files and a[key].dtype == b[key].dtype and a[key].shape == b[key].shape and np.array_equal(a[key], b[key], equal_nan=True)
        result["array_archive_bytes_equal"] = sha(left) == sha(right)
    else:
        result["array_keys_exact_equal"] = True
        result["array_archive_bytes_equal"] = True
    result["exact_except_declared_paths"] = (result["normalized_json_exact_equal"] and result["array_keys_exact_equal"]
        and result["array_archive_bytes_equal"] and all(result["arrays"].values()))
    return result


def replay_evidence(study, evidence, output, reference=None, expected_manifest=None):
    study, evidence, output = Path(study).resolve(), Path(evidence).resolve(), Path(output).resolve()
    manifest_path = evidence / "manifest.json"
    if expected_manifest is not None:
        require(valid_sha(expected_manifest) and sha(manifest_path) == expected_manifest, "portable manifest external SHA mismatch")
    manifest = read(manifest_path)
    require(manifest["schema"] == 1 and manifest["format"] == "original-byte-portable-slider-evidence", "unknown portable schema")
    old = Path(manifest["old_study_root"])
    require(old.is_absolute() and str(old) == os.path.normpath(str(old)), "noncanonical declared old study root")
    module = load_analyzer(study)
    frozen = module.load_freeze(study)
    require(manifest["freeze_sha256"] == frozen["sha256"]
            and manifest["analyzer_sha256"] == sha(study / "analyze-response.py")
            and manifest["protocol_sha256"] == sha(study / "PROTOCOL.md"), "portable/frozen study identity differs")
    require(manifest["export_tool_sha256"] == sha(__file__), "portable tool changed since export")
    verify_exported_files(evidence, manifest)
    require(set(manifest["rounds"]) == set(module.ROUNDS), "portable round matrix differs")
    for name in module.ROUNDS:
        rel = f"rounds/{name}/native-r1/receipt.json"
        require(manifest["rounds"][name]["capture_receipt"] == rel and rel in manifest["files"], "missing round capture receipt")
        receipt = read(evidence / rel)
        require(trace_declarations(receipt) == manifest["rounds"][name]["lossless_trace_storage"], "trace declarations changed")
        prefix = str(Path(rel).parent)
        required = {prefix + "/" + key for key in receipt["analysis_artifacts"]}
        require(required <= set(manifest["files"]), "portable round artifact omitted")
        for key in receipt["analysis_artifacts"]:
            exportable_artifact(key)
        for key in required | {rel}:
            require(manifest["files"][key]["source_relative_study_path"] == key, "original capture source path relabeled")
    declared_reference = manifest["reference_analysis_files"]
    require(isinstance(declared_reference, list) and len(set(declared_reference)) == len(declared_reference),
            "invalid reference-analysis declaration")
    actual_reference = {key for key in manifest["files"] if key.startswith("reference-analysis/")}
    require(set(declared_reference) == actual_reference
            and (not declared_reference or "reference-analysis/analysis.json" in declared_reference),
            "reference-analysis declaration differs from bound files")
    if reference is None and declared_reference:
        reference = evidence / "reference-analysis"
    originals = install_replay_mapping(module, study, evidence, old)
    argv = sys.argv
    try:
        sys.argv = [str(study / "analyze-response.py"), "--root", str(study), "--output", str(output)]
        code = module.main()  # Original frozen main, checks, geometry, model and thresholds.
    finally:
        sys.argv = argv
        module.load_round, module.resolve = originals
    comparison = compare_analysis(reference, output, study, evidence, old) if reference is not None else None
    result = {"status": "replayed_frozen_analyzer" if code == 0 else "frozen_analyzer_rejected_evidence",
              "frozen_exit_code": code, "manifest_sha256": sha(manifest_path), "freeze_sha256": frozen["sha256"],
              "analysis": str(output / "analysis.json"), "comparison": comparison,
              "comparison_limitation": None if comparison is not None else "No reference analysis supplied; equivalence is not claimed."}
    (output / "portable-replay.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
    return 2 if comparison is not None and not comparison["exact_except_declared_paths"] else code


def expect_rejection(fn, label):
    try:
        fn()
    except (ValueError, KeyError, OSError):
        return
    raise ValueError("synthetic failure was accepted: " + label)


def self_test():
    import numpy as np
    with tempfile.TemporaryDirectory(prefix="portable-slider-evidence-self-test-") as folder:
        root = Path(folder).resolve()
        study, evidence = root / "study", root / "evidence"
        source = study / "rounds/control-pre/native-r1/receipt.json"
        source.parent.mkdir(parents=True)
        original = b'{  "original": "/old/study/rounds/control-pre/native-r1/x.png" }\n'
        source.write_bytes(original)
        plan = {}
        rel = "rounds/control-pre/native-r1/receipt.json"
        add_plan(plan, rel, source, study)
        copy_exact(plan, evidence)
        require((evidence / rel).read_bytes() == original, "original receipt bytes rewritten")
        manifest = {"files": {key: row for key, (_, row) in plan.items()}}
        verify_exported_files(evidence, manifest)
        (evidence / rel).write_bytes(original + b" ")
        expect_rejection(lambda: verify_exported_files(evidence, manifest), "tampered copy")
        (evidence / rel).write_bytes(original)
        expect_rejection(lambda: exportable_artifact("traces/run/trace.jsonl.gz"), "trace read")
        expect_rejection(lambda: exportable_artifact("result.xcresult/x.png"), "xcresult read")
        expect_rejection(lambda: relative_path("../outside"), "path escape")
        forbidden = {"files": {"rounds/control-pre/native-r1/traces/run/trace.jsonl.gz":
                    {"sha256": "a" * 64, "bytes": 1, "source_relative_study_path": rel}}}
        expect_rejection(lambda: verify_exported_files(evidence, forbidden), "trace manifest before byte read")
        (evidence / "rounds/unbound.json").write_bytes(b"{}")
        expect_rejection(lambda: verify_exported_files(evidence, manifest), "unbound extra file")
        (evidence / "rounds/unbound.json").unlink()
        module = types.SimpleNamespace(resolve=lambda p, parent: Path(p) if Path(p).is_absolute() else Path(parent) / p)
        def native_loader(proxy, name, role, frozen):
            return proxy / "rounds" / name, proxy / "native-tools/verify.py", proxy.parent
        module.load_round = native_loader
        install_replay_mapping(module, study, evidence, Path("/old/study"))
        routed = module.load_round(study, "control-pre", None, None)
        require(routed == (evidence / "rounds/control-pre", study / "native-tools/verify.py", study.parent), "root routing changed verifier/source scope")
        require(module.resolve("/old/study/rounds/control-pre/x.png", study) == evidence / "rounds/control-pre/x.png", "declared absolute mapping missing")
        require(module.resolve("/old/study/inputs/x.png", study) == Path("/old/study/inputs/x.png"), "non-round absolute path remapped")
        require(module.resolve("/old/study-other/rounds/x.png", study) == Path("/old/study-other/rounds/x.png"), "prefix collision remapped")
        require(module.resolve("inputs/x.png", study) == study / "inputs/x.png", "relative source mapping changed")
        before, after = root / "before", root / "after"
        before.mkdir(); after.mkdir()
        np.savez_compressed(before / "original-pixels.npz", raw=np.array([1., np.nan, 3.]))
        (after / "original-pixels.npz").write_bytes((before / "original-pixels.npz").read_bytes())
        for where, path in ((before, "/old/study/rounds/control-pre/x.png"), (after, str(evidence / "rounds/control-pre/x.png"))):
            (where / "analysis.json").write_text(json.dumps({"path": path, "value": 4}))
        require(compare_analysis(before, after, study, evidence, Path("/old/study"))["exact_except_declared_paths"], "exact replay comparison")
        (after / "analysis.json").write_text(json.dumps({"path": str(evidence / "rounds/control-pre/x.png"), "value": 5}))
        require(not compare_analysis(before, after, study, evidence, Path("/old/study"))["exact_except_declared_paths"], "nonpath model change hidden")
        (after / "analysis.json").write_text(json.dumps({"path": str(evidence / "rounds/control-pre/x.png"), "value": 4}))
        np.savez_compressed(after / "original-pixels.npz", raw=np.array([1., np.nan, 4.]))
        require(not compare_analysis(before, after, study, evidence, Path("/old/study"))["exact_except_declared_paths"], "array value change hidden")
    print(json.dumps({"status": "portable_synthetic_contract_checks_passed", "scope": "synthetic text/arrays only; no study captures, optical PNGs, traces or xcresults read",
        "cases": ["original bytes preserved", "tamper rejection", "trace/xcresult exclusion", "path escape rejection", "unbound extra rejection", "round-only proxy", "declared old-root-only mapping", "current source/verifier preserved", "exact JSON/array comparison", "nonpath mismatch retained", "array value mismatch retained"]}))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("export")
    export.add_argument("--study", type=Path, default=Path(__file__).resolve().parent)
    export.add_argument("--output", type=Path, required=True)
    export.add_argument("--reference-analysis", type=Path)
    replay = commands.add_parser("replay")
    replay.add_argument("--study", type=Path, default=Path(__file__).resolve().parent)
    replay.add_argument("--evidence", type=Path, required=True)
    replay.add_argument("--output", type=Path, required=True)
    replay.add_argument("--compare", type=Path)
    replay.add_argument("--manifest-sha256")
    commands.add_parser("self-test")
    args = parser.parse_args()
    if args.command == "self-test":
        return self_test()
    if args.command == "export":
        return export_evidence(args.study, args.output, args.reference_analysis)
    return replay_evidence(args.study, args.evidence, args.output, args.compare, args.manifest_sha256)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, KeyError, TypeError, OSError) as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        raise SystemExit(2)
