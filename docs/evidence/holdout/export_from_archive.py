#!/usr/bin/env python3
"""Export completed Dock photometry, without running analysis or reading images.

Usage: python3 docs/evidence/holdout/export_from_archive.py --archive /path/to/glass-holdout-20261114
This requires the original research archive. Normal figure reproduction uses
render_figures.py and the small committed exports only.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil

OUT = Path(__file__).resolve().parent
CASES = [
    ("h01_horizontal_steps-light", "top"),
    ("h01_horizontal_steps-light", "bottom"),
    ("h02_chirp_pos-dark", "tip"),
    ("h04_multiscale_checker-dark", "bottom"),
]
EXPECTED = {
    "analysis/frozen-analysis.json": "ba4dba6459e9d81e60069051a370f7fb5d9524d924a638a22c14a982818a80c7",
    "analysis/analyze_holdout.py": "9dfad1e0a6664013a31743295eb3720251aded697c0083f9cd79e259ca3403bf",
    "analysis/sampling-spec.json": "4a8a4fff71562cc896725cf7558c180b3ac2590b684b23e6754ecb7915ac75d6",
    "protocol.json": "61e7e45f7728eae53cda2b8b2e6c7f1a2c32f439ff20490b45426d9500fa40a4",
    "inputs/manifest.json": "33bf9b7d34bfba3537318aac7adf5d08bb6876e1fd41b704e472d10909a2ccf8",
    "native-dock-index.json": "04236b47219cead46d7a4877bb3c4c5d000fa60fef86b72ec2ce71355271d2a8",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    archive = parser.parse_args().archive.resolve()
    sources = []
    for name, expected in EXPECTED.items():
        actual = sha(archive/name)
        if actual != expected:
            raise ValueError(f"Frozen archive identity mismatch: {name}")
        sources.append({"path_in_capture_archive": "artifacts/glass-holdout-20261114/"+name,
                        "sha256": actual})
    result = archive/"analysis/results"
    analysis = json.loads((result/"analysis.json").read_text())
    exported = []
    # These tables are byte-for-byte original outputs, including failures.
    for filename in ("candidate-minus-baseline.csv", "engineering-review-triggers.csv",
                     "native-repeat-stability.csv", "source-guards.csv"):
        source = result/filename
        shutil.copyfile(source, OUT/filename)
        with source.open() as handle:
            rows = sum(1 for _ in csv.DictReader(handle))
        exported.append({"file": filename, "sha256": sha(OUT/filename), "rows": rows,
                         "export": "byte-for-byte original completed output"})
        sources.append({"path_in_capture_archive": "artifacts/glass-holdout-20261114/analysis/results/"+filename,
                        "sha256": sha(source)})
    with (result/"normal-curves.csv").open() as handle:
        reader = csv.DictReader(handle)
        fields = reader.fieldnames
        curves = [row for row in reader if (row["scene"], row["probe"]) in CASES]
    with (OUT/"representative-normal-curves.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(curves)
    exported.append({"file": "representative-normal-curves.csv",
                     "sha256": sha(OUT/"representative-normal-curves.csv"), "rows": len(curves),
                     "export": "exact CSV values selected by the four declared scene/probe keys; no interpolation, refit or new measurement"})
    for filename in ("analysis.json", "normal-curves.csv", "README.md"):
        sources.append({"path_in_capture_archive": "artifacts/glass-holdout-20261114/analysis/results/"+filename,
                        "sha256": sha(result/filename)})
    # Expose the small exact protocol and sampling records; no runtime source.
    for source_name, filename in (("protocol.json", "protocol.json"),
                                  ("analysis/sampling-spec.json", "sampling-spec.json"),
                                  ("analysis/frozen-analysis.json", "frozen-analysis.json")):
        shutil.copyfile(archive/source_name, OUT/filename)
        exported.append({"file": filename, "sha256": sha(OUT/filename),
                         "export": "byte-for-byte frozen methodological record"})
    native = json.loads((archive/"native-dock-index.json").read_text())
    with (OUT/"engineering-review-triggers.csv").open() as handle:
        trigger_rows = list(csv.DictReader(handle))
    with (OUT/"native-repeat-stability.csv").open() as handle:
        repeat_rows = list(csv.DictReader(handle))
    repeat_metrics = ("Y_bias", "Y_MAE", "Y_RMSE", "Y_abs_p95", "deltaE00_median",
                      "deltaE00_mean", "deltaE00_p95", "deltaE00_max")
    assert len(trigger_rows) == 12 and len(repeat_rows) == 656 and len(native["entries"]) == 16
    assert sum(r["kind"] == "roi" for r in trigger_rows) == 2
    assert sum(r["kind"] == "probe_depth" for r in trigger_rows) == 10
    assert all(float(r[k]) == 0 for r in repeat_rows for k in repeat_metrics)
    assert all(r["effective_bar_theme"] == r["repeat_effective_bar_theme"] == r["requested_theme"]
               for r in native["entries"])
    identical_png_pairs = sum(r["rest_png_sha256"] == r["repeat_png_sha256"] for r in native["entries"])
    gaps = [r["capture_provenance"]["minimum_capture_separation_seconds"] for r in native["entries"]]
    summary = {"schema": 1, "publication_date": "2026-11-14",
        "status": "completed fixed Dock REST photometry; candidate NOT accepted; no global score",
        "backend_scope": "Historical Sleepy application path, not validation of this repository's official Kyant 2.0.0 backend",
        "reference": "iOS 26.5 (23F77), native four-item SwiftUI TabView Dock",
        "comparison": "old D31 baseline versus frozen D46.5 / b15.5 / refractionLimit1.5 candidate",
        "design": {"backgrounds": 8, "approximately_designed_families": 7,
                   "paired_requested_themes": 2, "scenes": 16,
                   "world_logical_units": [375, 667], "pixels_per_unit": 2,
                   "input_pixels": [750, 1334], "state": "REST"},
        "rows": analysis["rows"], "engineering_review_cells": len(trigger_rows),
        "review_count_scope": "Two ROI and ten normal/depth cells; overlapping and correlated, not twelve independent errors or trials",
        "representative_curve_selection": [{"scene": s, "probe": p} for s, p in CASES],
        "selection_purpose": "Show one large local improvement and three local median regressions, with the same-scene full probe curves; not an average, random subset or pass rate",
        "native_repeat": {"metric_cells": len(repeat_rows), "all_reported_Y_and_deltaE00_residuals_zero": True,
            "full_png_pairs_sha256_equal": identical_png_pairs, "full_png_pairs_total": len(native["entries"]),
            "minimum_capture_separation_range_seconds": [min(gaps), max(gaps)],
            "limit": "Two observed REST captures establish this capture's sampled stability only, not a noise distribution or future dynamic stability"},
        "effective_theme_scope": "Actual UITabBar public effectiveInterfaceStyle observed within acquisition brackets; does not reveal private material shader adaptation",
        "analysis_freeze_sha256": analysis["analysis_freeze_sha256"],
        "native_index_sha256": analysis["native_index_sha256"],
        "baseline_result_sha256": analysis["baseline_result_sha256"],
        "candidate_result_sha256": analysis["candidate_result_sha256"],
        "sources": sources, "exports": exported,
        "limits": ["No candidate acceptance, universal similarity percentage, population inference or native-equivalence claim.",
                   "Source-step loci, color islands and topology require independent transport review; smaller color residuals cannot pass those checks.",
                   "Sheet, other controls, sizes, real photographs, nested surfaces and dynamics remain outside this Dock REST analysis.",
                   "Rendering this public subset reproduces charts of saved values, not original screenshot photometry.",
                   "If these results guide tuning, this set becomes calibration and another preregistered unseen set is required."]}
    (OUT/"summary.json").write_text(json.dumps(summary, indent=2)+"\n")
    print(json.dumps({"exported_files": len(exported)+1, "curve_rows": len(curves),
                      "summary_sha256": sha(OUT/"summary.json")}, indent=2))


if __name__ == "__main__":
    main()
