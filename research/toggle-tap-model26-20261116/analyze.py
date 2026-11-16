#!/usr/bin/env python3
"""Audit the executed replay and export unfitted, original-sample diagnostics."""
import argparse
import csv
import hashlib
import html
import json
import math
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODEL_COLUMNS = [
    "model_position", "model_geometry_lift", "model_lift", "model_stretch",
    "model_local_base_w", "model_local_base_h", "model_draw_w", "model_draw_h",
    "model_center_delta", "native_center_delta", "error_base_w", "error_base_h",
    "error_draw_w", "error_draw_h", "error_center_delta", "previous_model_frame_nanos",
    "model_frame_advanced", "begin_applied", "events_injected",
]
SERIES = {
    "native_local_width": "boundsW", "native_local_height": "boundsH",
    "native_world_center_delta": "native_center_delta",
    "model_base_width": "model_local_base_w", "model_base_height": "model_local_base_h",
    "model_draw_width": "model_draw_w", "model_draw_height": "model_draw_h",
    "model_center_delta": "model_center_delta",
}
ERRORS = {"base_width": "error_base_w", "base_height": "error_base_h",
          "draw_width": "error_draw_w", "draw_height": "error_draw_h",
          "center_delta": "error_center_delta"}
PLOT_IDS = ("b9b-swiftui-tap7-off-to-on", "b9b-swiftui-tap8-on-to-off")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_table(path, delimiter):
    with path.open(newline="") as stream:
        reader = csv.DictReader(stream, delimiter=delimiter)
        columns, rows = reader.fieldnames, list(reader)
    assert columns and len(set(columns)) == len(columns)
    assert all(set(row) == set(columns) and None not in row.values() for row in rows)
    return columns, rows


def finite(row, key):
    value = float(row[key])
    assert math.isfinite(value), (key, row[key])
    return value


def float32(value):
    # Java prints float fields with round-trip precision, while its error fields
    # use the widened original IEEE754 float. Restore it before auditing errors.
    return struct.unpack("f", struct.pack("f", float(value)))[0]


def provenance(row):
    return {key: row[key] for key in ("source_id", "source_line", "frame", "frame_t", "ms_from_delivered_up")}


def observed(row, column):
    return {"value": finite(row, column), **provenance(row)}


def statistics(rows):
    errors = {}
    for label, column in ERRORS.items():
        values = [finite(r, column) for r in rows]
        peak = max(rows, key=lambda r: abs(finite(r, column)))
        errors[label] = {"rmse": math.sqrt(math.fsum(v*v for v in values)/len(values)),
                         "max_abs": abs(finite(peak, column)), "max_abs_at": provenance(peak)}
    tail = [r for r in rows if 1200 <= finite(r, "ms_from_delivered_up") <= 1500]
    assert tail
    series = {}
    for label, column in SERIES.items():
        series[label] = {
            "observed_min": observed(min(rows, key=lambda r: finite(r, column)), column),
            "observed_max": observed(max(rows, key=lambda r: finite(r, column)), column),
            "tail_min": min(finite(r, column) for r in tail),
            "tail_max": max(finite(r, column) for r in tail),
            "final_observation": observed(rows[-1], column),
        }
    return {"frames": len(rows), "errors": errors, "series": series,
            "tail": {"frames": len(tail), "first": provenance(tail[0]), "last": provenance(tail[-1])}}


def figure(groups):
    """First SwiftUI ON/OFF segments by original order, selected before results."""
    selected = [groups[sid] for sid in PLOT_IDS]
    panels = [
        ("Local width / model drawing width", ["boundsW", "model_local_base_w", "model_draw_w"]),
        ("Local height / model drawing height", ["boundsH", "model_local_base_h", "model_draw_h"]),
        ("Signed center displacement", ["native_center_delta", "model_center_delta"]),
    ]
    colors = ["#172b4d", "#136fbe", "#db6a16"]
    xlo = min(finite(r, "ms_from_delivered_up") for rows in selected for r in rows)
    xhi = max(finite(r, "ms_from_delivered_up") for rows in selected for r in rows)
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1220" height="945" viewBox="0 0 1220 945" role="img">',
             '<title>iOS 26.5 native observations versus the executed Sleepy core-model replay</title>',
             '<desc>First SwiftUI OFF to ON and ON to OFF taps in input order. Actual observations only; x is original frame row time relative to delivered UP. Lines disconnect across gaps over 25 milliseconds. Drawing and native local bounds may represent different layer decompositions. No GPU, optical or timing-sync acceptance.</desc>',
             '<rect width="1220" height="945" fill="#f8fafc"/>',
             '<g font-family="sans-serif" fill="#172b4d">',
             '<text x="44" y="32" font-size="21" font-weight="700">Native iOS 26.5 vs executed core model</text>',
             '<text x="44" y="56" font-size="13">No fitting, retiming, interpolation or resampling. Different local/draw decompositions remain separate.</text>']
    for i, (label, color) in enumerate(zip(["Native observation", "Model base geometry / center", "Model drawing dimensions"], colors)):
        x = 44 + i*355
        parts.append(f'<path d="M{x} 80h28" stroke="{color}" stroke-width="2"/>')
        parts.append(f'<text x="{x+36}" y="84" font-size="13">{label}</text>')
    for pi, (label, columns) in enumerate(panels):
        values = [finite(r, col) for rows in selected for r in rows for col in columns]
        lo, hi = min(values), max(values)
        pad = max((hi-lo)*.08, .5)
        lo, hi = lo-pad, hi+pad
        for si, rows in enumerate(selected):
            left, top, width, height = 78+si*604, 150+pi*245, 490, 178
            sx = lambda x: left + (x-xlo)/(xhi-xlo)*width
            sy = lambda y: top+height-(y-lo)/(hi-lo)*height
            parts.append(f'<text x="{left}" y="{top-22}" font-size="14" font-weight="700">{html.escape(PLOT_IDS[si])}</text>')
            parts.append(f'<text x="{left}" y="{top-5}" font-size="12">{html.escape(label)} (dp / pt diagnostic convention)</text>')
            parts.append(f'<rect x="{left}" y="{top}" width="{width}" height="{height}" fill="white" stroke="#ccd5df"/>')
            for n in range(5):
                value = lo+(hi-lo)*n/4
                yy = sy(value)
                parts.append(f'<path d="M{left} {yy:.3f}h{width}" stroke="#e2e8f0"/>')
                parts.append(f'<text x="{left-8}" y="{yy+4:.3f}" text-anchor="end" font-size="11">{value:.1f}</text>')
            for value in (-250, 0, 250, 500, 750, 1000, 1250):
                if xlo <= value <= xhi:
                    xx = sx(value)
                    parts.append(f'<path d="M{xx:.3f} {top}v{height}" stroke="#e2e8f0"/>')
                    parts.append(f'<text x="{xx:.3f}" y="{top+height+17}" text-anchor="middle" font-size="11">{value}</text>')
            for ci, col in enumerate(columns):
                path, previous = [], None
                for row in rows:
                    broken = previous is None or any(
                        (finite(row, key)-finite(previous, key))*1000 > 25
                        for key in ("frame_t", "displayTimestamp"))
                    x, y = sx(finite(row, "ms_from_delivered_up")), sy(finite(row, col))
                    path.append(f'{"M" if broken else "L"}{x:.3f} {y:.3f}')
                    parts.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="1.2" fill="{colors[ci]}"/>')
                    previous = row
                parts.append(f'<path d="{" ".join(path)}" fill="none" stroke="{colors[ci]}" stroke-width="1.3"/>')
            parts.append(f'<text x="{left+width/2}" y="{top+height+35}" text-anchor="middle" font-size="11">Original frame_t minus delivered UP (ms)</text>')
    parts.extend(['<text x="44" y="908" font-size="12">Dots are actual frames; straight lines are visual guides and break if frame-row or display-timestamp gaps exceed 25 ms.</text>',
                  '<text x="44" y="929" font-size="12">Core-model diagnostic only. Native local bounds and Android drawing dimensions are not proved to be the same layer.</text>',
                  '</g></svg>'])
    return ("\n".join(parts)+"\n").encode()


def analyze():
    receipt = json.loads((HERE/"prepared/preparation.json").read_text())
    execution = json.loads((HERE/"execution.json").read_text())
    assert execution["status"] == "CORE_MODEL_REPLAY_EXECUTED" and execution["exit_code"] == 0
    assert digest(HERE/"execution.log") == execution["public_log_sha256"]
    assert digest(HERE/"prepared/preparation.json") == execution["prepared_receipt_sha256"]
    assert digest(HERE/"replay.csv") == execution["replay_csv"]["sha256"]
    assert (HERE/"replay.csv").stat().st_size == execution["replay_csv"]["bytes"]
    for category, base in (("prepared_files", HERE/"prepared"), ("study_sources", HERE),
                           ("native_inputs", HERE.parent/"toggle-tap-native26-20261116")):
        for name, pinned in receipt[category].items():
            assert digest(base/name) == pinned, (category, name)
    native_columns, expected = read_table(HERE/"prepared/frames.tsv", "\t")
    columns, actual = read_table(HERE/"replay.csv", ",")
    assert columns == native_columns+MODEL_COLUMNS
    assert len(actual) == len(expected) == receipt["frames"] == 838
    _, segments = read_table(HERE/"prepared/segments.tsv", "\t")
    _, events = read_table(HERE/"prepared/events.tsv", "\t")
    groups = {s["segment"]: [] for s in segments}
    assert len(groups) == receipt["segments"] == 8
    assert len(events) == receipt["events"] == 16
    assert {row["segment"] for row in events} == set(groups)
    text = {"segment", "source_id", "hidden", "effectiveHidden", "presentationAvailable", "model_frame_advanced", "begin_applied"}
    checked = 0
    for original, replay in zip(expected, actual):
        for key in native_columns:
            assert original[key] == replay[key], (replay["segment"], key, "native-field mismatch")
            checked += 1
        for key in columns:
            if key not in text and replay[key] != "":
                finite(replay, key)
        assert replay["model_frame_advanced"] in ("true", "false")
        assert replay["begin_applied"] in ("true", "false")
        assert replay["segment"] in groups
        groups[replay["segment"]].append(replay)
    summaries = []
    for segment in segments:
        sid, baseline = segment["segment"], float(segment["baseline_world_center"])
        rows = groups[sid]
        selected_events = [r for r in events if r["segment"] == sid]
        assert [r["phase"] for r in selected_events] == ["0", "3"]
        assert sum(int(r["events_injected"]) for r in rows) == len(selected_events) == 2
        assert all(int(a["replay_nanos"]) < int(b["replay_nanos"]) for a, b in zip(rows, rows[1:]))
        next_event = 0
        for row in rows:
            count = 0
            while next_event < len(selected_events) and int(selected_events[next_event]["received_nanos"]) <= int(row["replay_nanos"]):
                next_event += 1
                count += 1
            assert int(row["events_injected"]) == count
            center = finite(row,"x")+finite(row,"w")/2-baseline
            assert math.isclose(center, finite(row,"native_center_delta"), rel_tol=0, abs_tol=1e-12)
            for suffix, model, native in (("base_w","model_local_base_w","boundsW"),
                    ("base_h","model_local_base_h","boundsH"), ("draw_w","model_draw_w","boundsW"),
                    ("draw_h","model_draw_h","boundsH")):
                residual = float32(row[model])-finite(row,native)
                assert math.isclose(residual, finite(row,"error_"+suffix), rel_tol=0, abs_tol=1e-12)
            assert math.isclose(finite(row,"model_center_delta")-center, finite(row,"error_center_delta"), rel_tol=0, abs_tol=1e-12)
        assert next_event == 2
        summaries.append({"segment": sid, "events_injected": 2, **statistics(rows)})
    image = figure(groups)
    input_paths = ["execution.json", "execution.log", "replay.csv", "prepared/preparation.json",
                   "prepared/frames.tsv", "prepared/events.tsv", "prepared/segments.tsv"]
    result = {
        "schema": 1, "status": "EXECUTED_CORE_MODEL_DIAGNOSTIC_AUDITED",
        "analyzer_sha256": digest(HERE/"analyze.py"),
        "inputs": {name: digest(HERE/name) for name in input_paths},
        "checks": {"native_cells_exact": checked-len(actual), "prepared_cells_exact": checked,
                   "frames": len(actual), "segments": len(groups),
                   "delivered_events": len(events), "finite_recorded_numeric_fields": True,
                   "per_frame_injection_counts": True, "exported_residuals_recomputed": True,
                   "pinned_sources_and_prepared_files_unchanged": True},
        "metric_scope": "Every original selected frame, including pre-DOWN and settled tail; no weighting, fitting, retiming or resampling. Error=model minus native. RMSE=sqrt(sum(error^2)/N); tied extrema use the first actual row.",
        "units": "Numerical dp/pt diagnostic convention, not proved identical layer decomposition",
        "tail_rule": "Actual original frames inclusively UP+1200 through UP+1500 ms",
        "limitations": ["Native frame_t is logger row time, not exact getter instant or video PTS",
                        "Model base/draw dimensions and native local bounds may have different layer/transform decomposition",
                        "No Android GPU, optical, natural-motion or native timing-sync acceptance"],
        "segments": summaries,
        "figure": {"path": "native-core-model.svg", "sha256": hashlib.sha256(image).hexdigest(),
                   "segments_preselected_by_input_order": list(PLOT_IDS),
                   "time_axis": "Unmodified ms_from_delivered_up",
                   "gap_rule": "Disconnect if consecutive frame_t OR displayTimestamp differs by >25 ms"},
    }
    return {"analysis.json": (json.dumps(result, indent=2, allow_nan=False)+"\n").encode(), "native-core-model.svg": image}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="Check existing output bytes without writing")
    args = parser.parse_args()
    outputs = analyze()
    if args.verify:
        for name, data in outputs.items():
            assert (HERE/name).read_bytes() == data, name
    else:
        assert all(not (HERE/name).exists() for name in outputs), "Refusing to overwrite analysis output"
        for name, data in outputs.items():
            (HERE/name).write_bytes(data)
    print("Verified" if args.verify else "Exported", "838 frames / 8 segments / 16 events; native columns exact; core-model diagnostics only")


if __name__ == "__main__":
    main()
