#!/usr/bin/env python3
"""Export original signed-G endpoints; replay unchanged collectors in a temporary clone root.

The committed export contains only this study's new 8 PNGs and required metadata.
Frozen sibling dependencies are reused from the cloned asset repository, never duplicated
in the evidence directory. No trace archives, xcresult, DerivedData or binaries are read.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile

import numpy as np

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
F = ROOT.parent / "slider-linear-response-20261116"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def relpath(value):
    p = PurePosixPath(value)
    require(value and not p.is_absolute() and ".." not in p.parts and p.as_posix() == value,
            "Unsafe portable relative path")
    return Path(value)


def safe(path):
    path = Path(path).resolve()
    require(path.is_relative_to(REPO), "File outside cloned asset repository")
    require(not any(p.endswith(".xcresult") or p == "DerivedData" or p.endswith(".app")
                    for p in path.parts), "Build/result payload forbidden")
    require(path.name not in {"trace.jsonl", "trace.jsonl.gz"} and path.suffix != ".gz",
            "Trace archive reading forbidden")
    return path


def allowed_artifact(relative):
    p = relpath(relative)
    require(p.suffix == ".png" or p.name in {
        "receipt.json", "index-strict.json", "endpoint-verification-strict.json",
        "capture-events.jsonl", "session.json"}, "Unneeded capture payload forbidden")
    return p


def frozen_dependencies():
    freeze = read(ROOT / "freeze.json")
    result = {}
    for relative, expected in freeze["files"].items():
        path = safe(ROOT / relative)
        require(sha(path) == expected, "Frozen dependency changed: " + relative)
        result[path.relative_to(REPO).as_posix()] = path
    return freeze, result


def repository_rules():
    """Unfrozen transfer rules; they do not alter capture or analysis inputs."""
    frozen = read(ROOT / "freeze.json")["files"]
    result = {}
    for relative in ("inputs/.gitignore", "evidence/.gitignore"):
        require(relative not in frozen, "Cannot amend a frozen ignore rule")
        path = safe(ROOT / relative)
        result[relative] = {"sha256": sha(path), "bytes": path.stat().st_size,
                            "purpose": "Unignore only this directory's portable rounds subtree"}
    return result


def reference_capture_sha(relative):
    candidates = [v for k, v in read(ROOT / "analysis/collection.json")["sources"].items()
                  if k.endswith("/" + ROOT.name + "/" + relative)]
    require(len(candidates) == 1, "Capture not uniquely bound by original collection")
    return candidates[0]


def export():
    freeze, _ = frozen_dependencies()
    target = ROOT / "evidence"
    require(not target.exists(), "Refusing to overwrite an existing original-byte export")
    plan, rounds = {}, {}
    for name in freeze["round_order"]:
        folder = ROOT / "rounds" / name / "native-r1"
        prefix = Path("rounds") / name / "native-r1"
        receipt_path = folder / "receipt.json"
        receipt = read(receipt_path)
        require(sha(receipt_path) == reference_capture_sha((prefix / "receipt.json").as_posix()),
                "Original receipt changed")
        require(receipt["freeze_sha256"] == sha(ROOT / "freeze.json"), "Wrong original freeze")
        require(receipt["native_binaries"] == freeze["native_binaries"]
                and receipt["prepared_native_files"] == freeze["prepared_native_files"]
                and receipt["simulator_identity"] == freeze["simulator"], "Capture identity changed")
        require(receipt["verified_held_endpoints"] == 2
                and receipt["verified_shape_flat_pairs"] == 1, "Unexpected original endpoint count")
        artifacts = {"receipt.json": sha(receipt_path), **receipt["analysis_artifacts"]}
        require(sum(Path(p).suffix == ".png" for p in artifacts) == 2, "Expected two original PNGs")
        for relative, expected in artifacts.items():
            relative_path = allowed_artifact(relative)
            source = safe(folder / relative_path)
            require(sha(source) == expected, "Original artifact changed: " + str(source))
            destination = (prefix / relative_path).as_posix()
            plan[destination] = (source, {"sha256": expected, "bytes": source.stat().st_size,
                                          "source_relative_study_path": destination})
        strict, index = read(folder / "endpoint-verification-strict.json"), read(folder / "index-strict.json")
        require(strict["status"] == index["status"] == "passed"
                and strict["verifiedHeldEndpoints"] == 2, "Strict verification failed")
        rounds[name] = {"receipt": (prefix / "receipt.json").as_posix(),
                        "lossless_trace_storage_declarations_only": receipt["lossless_trace_storage"]}
    target.mkdir()
    (target / ".gitignore").write_bytes((ROOT / "inputs/.gitignore").read_bytes())
    for relative, (source, row) in plan.items():
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        require(sha(destination) == row["sha256"], "Copy changed original bytes")
    manifest = dict(schema=1, format="signed-G-original-bytes-sibling-dependent-portable-evidence",
                    freeze_sha256=sha(ROOT / "freeze.json"), collector_sha256=sha(ROOT / "collect-signed.py"),
                    f_analyzer_sha256=sha(F / "analyze-signed-g.py"), export_tool_sha256=sha(__file__),
                    files={k: v for k, (_, v) in sorted(plan.items())}, rounds=rounds,
                    repository_rules=repository_rules(),
                    required_layout="Clone this asset repository with its existing sibling research directories; do not copy this evidence folder alone.",
                    exclusions="No trace archive/xcresult/DerivedData/app binary read or copied. Receipt trace hashes/sizes are original declarations only.")
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    checked = verify_files()
    print(json.dumps(dict(status="EXPORTED_ORIGINAL_BYTES", **checked), indent=2))


def verify_files():
    target = ROOT / "evidence"
    manifest = read(target / "manifest.json")
    require(manifest["freeze_sha256"] == sha(ROOT / "freeze.json")
            and manifest["collector_sha256"] == sha(ROOT / "collect-signed.py")
            and manifest["f_analyzer_sha256"] == sha(F / "analyze-signed-g.py")
            and manifest["export_tool_sha256"] == sha(__file__), "Export tools/freeze changed")
    require(manifest["repository_rules"] == repository_rules(), "Portable Git transfer rules changed")
    actual = {p.relative_to(target).as_posix() for p in target.rglob("*") if p.is_file()}
    actual -= {"manifest.json", ".gitignore"}
    require(actual == set(manifest["files"]), "Unbound extra or missing export file")
    size, pngs = 0, 0
    for relative, row in manifest["files"].items():
        p = relpath(relative)
        require(len(p.parts) >= 4 and p.parts[0] == "rounds" and p.parts[2] == "native-r1",
                "Unexpected export structure")
        allowed_artifact(Path(*p.parts[3:]).as_posix())
        path = safe(target / p)
        require(path.stat().st_size == row["bytes"] and sha(path) == row["sha256"],
                "Changed export original: " + relative)
        pngs += path.suffix == ".png"
        size += path.stat().st_size
    require(pngs == 8 and len(manifest["rounds"]) == 4, "Expected exactly eight new PNGs")
    return dict(files=len(actual), bytes=size, original_pngs=pngs,
                unfrozen_repository_rule_files=2,
                manifest_sha256=sha(target / "manifest.json"))


def normalise(value, roots):
    if isinstance(value, dict):
        return {normalise(k, roots): normalise(v, roots) for k, v in value.items()}
    if isinstance(value, list):
        return [normalise(v, roots) for v in value]
    if isinstance(value, str) and value.startswith("/"):
        p = Path(value)
        for root in sorted(roots, key=lambda item: len(item.parts), reverse=True):
            if p.is_relative_to(root):
                return "<asset>/" + p.relative_to(root).as_posix()
    return value


def compare_npz(reference, actual):
    with np.load(reference, allow_pickle=False) as left, np.load(actual, allow_pickle=False) as right:
        require(set(left.files) == set(right.files), "Replay NPZ keys changed")
        matches = {key: bool(np.array_equal(left[key], right[key], equal_nan=True)) for key in left.files}
    require(all(matches.values()), "Replay NPZ array differs")
    return dict(array_count=len(matches), all_arrays_exact_equal=True,
                npz_container_sha256_exact_equal=sha(reference) == sha(actual))


def verify():
    exported = verify_files()
    freeze, dependencies = frozen_dependencies()
    manifest = read(ROOT / "evidence/manifest.json")
    workspace = ROOT / ".local"
    workspace.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="portable-verify-", dir=workspace) as name:
        portable = Path(name) / "asset"
        for relative, source in dependencies.items():
            destination = portable / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        d = portable / ROOT.relative_to(REPO)
        f = portable / F.relative_to(REPO)
        shutil.copyfile(ROOT / "freeze.json", d / "freeze.json")
        for relative in manifest["files"]:
            destination = d / relpath(relative)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / "evidence" / relative, destination)
        commands = ([sys.executable, str(d / "collect-signed.py"), "--output", str(d / "analysis")],
                    [sys.executable, str(f / "analyze-signed-g.py"), "--input",
                     str(d / "analysis/signed-output.npz"), "--out", str(f / "signed-results")])
        logs = []
        for command in commands:
            process = subprocess.run(command, cwd=portable, text=True, capture_output=True)
            require(process.returncode == 0, "Frozen replay failed: " + process.stderr[-4000:])
            logs.append(dict(program=Path(command[1]).name, returncode=process.returncode,
                             stdout_sha256=hashlib.sha256(process.stdout.encode()).hexdigest(),
                             stderr=process.stderr))
        collection_arrays = compare_npz(ROOT / "analysis/signed-output.npz", d / "analysis/signed-output.npz")
        f_arrays = compare_npz(F / "signed-results/signed-analysis.npz", f / "signed-results/signed-analysis.npz")
        comparisons = {}
        for label, reference, actual in (
            ("D_collection", ROOT / "analysis/collection.json", d / "analysis/collection.json"),
            ("F_analysis", F / "signed-results/analysis.json", f / "signed-results/analysis.json")):
            before = normalise(read(reference), [REPO, portable])
            after = normalise(read(actual), [REPO, portable])
            matches = before == after
            require(matches, label + " JSON differs after declared path normalisation")
            comparisons[label] = dict(normalized_json_exact_equal=True,
                                      reference_sha256=sha(reference), replay_sha256=sha(actual))
        require(collection_arrays["npz_container_sha256_exact_equal"]
                and f_arrays["npz_container_sha256_exact_equal"], "Replay NPZ containers differ")
        result = dict(status="PASS_ORIGINAL_BYTES_AND_UNCHANGED_ANALYZERS_PORTABLE_REPLAY",
                      export=exported, freeze_sha256=sha(ROOT / "freeze.json"),
                      collector_sha256=sha(ROOT / "collect-signed.py"),
                      f_analyzer_sha256=sha(F / "analyze-signed-g.py"), tool_sha256=sha(__file__),
                      sibling_frozen_dependencies=len(dependencies),
                      sibling_dependency_bytes=sum(p.stat().st_size for p in dependencies.values()),
                      duplicate_dependency_bytes_committed=0, new_endpoints=8,
                      D_arrays=collection_arrays, F_arrays=f_arrays, JSON=comparisons, programs=logs,
                      normalisation="Absolute dictionary keys and string values only under original/temporary asset root map to <asset>/; no numeric/hash/status field ignored.",
                      trace_policy=manifest["exclusions"],
                      optical_acceptance=False)
    result["temporary_root_removed"] = not Path(name).exists()
    require(result["temporary_root_removed"], "Temporary replay root was not removed")
    receipt = ROOT / "portable-validation.json"
    receipt.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("export", "verify"))
    args = parser.parse_args()
    export() if args.mode == "export" else verify()


if __name__ == "__main__":
    main()
