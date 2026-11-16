#!/usr/bin/env python3
"""Export measured Toggle tap observations; --verify reads without writing."""
import argparse
import collections
import csv
import hashlib
import html
import io
import json
import math
from pathlib import Path
import statistics
import xml.etree.ElementTree as ET


HERE = Path(__file__).resolve().parent
SOURCES = [
    {
        "id": "b9b-swiftui",
        "directory": "outputs/glass-native-parity-20261112/native-toggle-gap-20261113/traces/-_NativeReferenceTests_testToggleHeldDirectionAndRapidProbe_-B9B0304D-E04E-4C56-9399-06118974D0DC",
        "trace_sha256": "16215cb7978344388499aad7691617e8a3e7382ac15d283724362ec3dfe437ec",
        "session_sha256": "9958cdb5d8ba2a67b6a2abe6feb183695b2836b9bd14aac98f74ccd3a3c5d3d1",
        "control": "swiftui-toggle",
        "control_path": "window0/0/0/0/4/0/0",
        "lens_path": "window0/0/0/0/4/0/0/0/2",
        "touch_ids": [7, 8, 9, 10, 11, 12],
    },
    {
        "id": "grid-uikit",
        "directory": "outputs/glass-native-parity-20261112/ios-traces/-_NativeReferenceTests_testToggleGrid_-58D8137C-0C43-4758-AD02-A7FA4F49A5C0",
        "trace_sha256": "e93fc12a7be9c33f723721fdb5a48111b54afd6db8da73923365d86d667f2a04",
        "session_sha256": "00e565d6573bedd3ad06838af0dec219f1433bdb8e2b7dcf7f38e7916e894171",
        "control": "uikit-toggle",
        "control_path": "window0/0/0/0/4/1/0",
        "lens_path": "window0/0/0/0/4/1/0/0/2",
        "touch_ids": [6, 7],
    },
]
STATE_FIELDS = ["boundsW", "boundsH", "x", "y", "w", "h", "m11", "m12", "m21", "m22", "m41", "m42", "opacity", "effectiveOpacity", "hidden", "effectiveHidden"]
PLOT_PANELS = [("boundsW", "Local bounds width (pt)", 34, 64, [35, 40, 45, 50, 55, 60]),
               ("boundsH", "Local bounds height (pt)", 22, 42, [24, 28, 32, 36, 40]),
               ("center_dx", "World center x displacement from last pre-DOWN frame (pt)", -25, 25, [-20, -10, 0, 10, 20])]
PLOT_COLORS = ["#1b6ca8", "#00876c", "#d17c00", "#a34f91", "#6a60a9", "#b34c52", "#222222", "#7b5a2a"]


def plot_xy(row, summary, panel_index):
    key, _, low, high, _ = PLOT_PANELS[panel_index]
    before = summary["last_observed_pre_down"]
    value = float(row[key]) if key != "center_dx" else (
        float(row["x"]) + float(row["w"]) / 2 - before["x"] - before["w"] / 2)
    time_ms = float(row["ms_from_delivered_up"])
    assert -300 <= time_ms <= 1500 and low <= value <= high
    return f"{96 + (time_ms + 300) / 1800 * 994:.3f}", f"{168 + panel_index * 218 + 164 - (value - low) / (high - low) * 164:.3f}"


def plot_chunks(rows):
    chunks = []
    for index, row in enumerate(rows):
        if index == 0 or max((float(row["displayTimestamp"]) - float(rows[index - 1]["displayTimestamp"])) * 1000,
                            (float(row["frame_t"]) - float(rows[index - 1]["frame_t"])) * 1000) > 25:
            chunks.append([])
        chunks[-1].append(row)
    return chunks


def make_native_svg(rows, summaries):
    """Pure-stdlib SVG: actual points, straight guides, explicit sampling gaps."""
    grouped = collections.defaultdict(list)
    for row in rows:
        grouped[row["segment"]].append(row)
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="880" viewBox="0 0 1120 880" role="img" aria-labelledby="title desc">',
             '<title id="title">iOS 26.5 ordinary Toggle taps: native carrier observations</title>',
             '<desc id="desc">Native only, not an Android comparison. Eight actual carrier traces aligned to delivered UP. Local width, local height, and signed world center x displacement from each last observed pre-DOWN frame. No fit, interpolation, resampling or retiming. Gaps over 25 ms in either display timestamps or frame-row time are disconnected. Opacity and material alpha are not plotted.</desc>',
             '<rect width="1120" height="880" fill="#ffffff"/>',
             '<g font-family="system-ui, sans-serif" fill="#1d2732">',
             '<text x="32" y="32" font-size="23" font-weight="650">iOS 26.5 ordinary Toggle taps · native carrier observations</text>',
             '<text x="32" y="56" font-size="13" fill="#52606d">Native only · no Android comparison · frame t relative to delivered UP · original window-point geometry</text>']
    for index, summary in enumerate(summaries):
        left, top = 32 + (index % 4) * 272, 87 + (index // 4) * 24
        control = "SwiftUI" if summary["source_id"] == "b9b-swiftui" else "UIKit"
        direction = "OFF→ON" if summary["direction"] == "off-to-on" else "ON→OFF"
        dash = ' stroke-dasharray="6 3"' if control == "UIKit" else ""
        label = f"{control} {summary['touch_id']} {direction} · {summary['delivered_duration_ms']:.2f} ms"
        parts += [f'<line x1="{left}" y1="{top - 4}" x2="{left + 25}" y2="{top - 4}" stroke="{PLOT_COLORS[index]}" stroke-width="2"{dash}/>',
                  f'<text x="{left + 31}" y="{top}" font-size="11">{html.escape(label)}</text>']
    for panel_index, (key, title, low, high, ticks) in enumerate(PLOT_PANELS):
        top = 168 + panel_index * 218
        parts.append(f'<text x="96" y="{top - 15}" font-size="14" font-weight="600">{html.escape(title)}</text>')
        for value in ticks:
            y = top + 164 - (value - low) / (high - low) * 164
            parts += [f'<line x1="96" y1="{y:.3f}" x2="1090" y2="{y:.3f}" stroke="#e3e8ee"/>',
                      f'<text x="83" y="{y + 4:.3f}" text-anchor="end" font-size="11" fill="#52606d">{value}</text>']
        for value in [-250, 0, 250, 500, 750, 1000, 1250, 1500]:
            x = 96 + (value + 300) / 1800 * 994
            stroke, dash = ("#788795", ' stroke-dasharray="4 4"') if value == 0 else ("#eef1f5", "")
            parts += [f'<line x1="{x:.3f}" y1="{top}" x2="{x:.3f}" y2="{top + 164}" stroke="{stroke}"{dash}/>',
                      f'<text x="{x:.3f}" y="{top + 183}" text-anchor="middle" font-size="11" fill="#52606d">{value}</text>']
        if panel_index == 0:
            parts.append(f'<text x="{96 + 300 / 1800 * 994 + 6:.3f}" y="{top + 14}" font-size="11" fill="#52606d">UP</text>')
        for index, summary in enumerate(summaries):
            series = grouped[summary["id"]]
            parts.append(f'<g data-panel="{key}" data-segment="{summary["id"]}" data-source-lines="{",".join(str(row["source_line"]) for row in series)}" stroke="{PLOT_COLORS[index]}" fill="{PLOT_COLORS[index]}">')
            dash = ' stroke-dasharray="6 3"' if summary["source_id"] == "grid-uikit" else ""
            for chunk in plot_chunks(series):
                points = " ".join(",".join(plot_xy(row, summary, panel_index)) for row in chunk)
                parts.append(f'<polyline points="{points}" fill="none" stroke-width="1.25" stroke-opacity="0.85"{dash}/>')
            for row in series:
                x, y = plot_xy(row, summary, panel_index)
                parts.append(f'<circle cx="{x}" cy="{y}" r="1.15" stroke="none"/>')
            parts.append('</g>')
    parts += ['<text x="593" y="817" text-anchor="middle" font-size="13">Time relative to delivered UP (ms)</text>',
              '<text x="32" y="847" font-size="12" fill="#52606d">Dots = actual frames; straight connectors are visual guides. No fit, interpolation, resampling or retiming.</text>',
              '<text x="32" y="867" font-size="12" fill="#52606d">Disconnect if consecutive display timestamps OR frame-row t differ by &gt;25 ms. Signed center displacement; no direction flip.</text>',
              '</g></svg>']
    return ("\n".join(parts) + "\n").encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value, compact=False):
    return (json.dumps(value, ensure_ascii=False, allow_nan=False,
                       separators=(",", ":") if compact else None,
                       indent=None if compact else 2) + "\n").encode()


def read_source(root, spec):
    directory = root / spec["directory"]
    files = {}
    for name in ["session.json", "trace.jsonl"]:
        payload = (directory / name).read_bytes()
        expected = spec["session_sha256" if name == "session.json" else "trace_sha256"]
        assert sha(payload) == expected, f"Source SHA mismatch: {spec['id']}/{name}"
        files[name] = {"path": f"{spec['directory']}/{name}", "bytes": len(payload), "sha256": sha(payload)}
    session = json.loads((directory / "session.json").read_text())
    assert session["os"] == "Version 26.5 (Build 23F77)"
    frames, touches, values = [], [], []
    session_line = None
    with (directory / "trace.jsonl").open() as handle:
        for line, text in enumerate(handle, 1):
            row = json.loads(text)
            item = {"source_line": line, "row": row}
            if row["event"] == "frame":
                frames.append(item)
            elif row["event"] == "touch":
                touches.append(item)
            elif row["event"] == "value":
                values.append(item)
            elif row["event"] == "session":
                assert row["metadata"] == session
                session_line = line
    return session, files, session_line, frames, touches, values


def ranges(rows, fields):
    return {key: [min(row[key] for row in rows), max(row[key] for row in rows)]
            for key in fields if all(key in row for row in rows)}


def build(root):
    source_records, segments, summaries = [], [], []
    frame_columns, node_columns, catalog, catalog_lookup = [], [], [], {}
    csv_rows = []
    input_segments = []
    for spec in SOURCES:
        session, files, session_line, frames, touches, values = read_source(root, spec)
        source_records.append({"id": spec["id"], "path_base": "R-relative", "files": files,
                               "session_trace_line": session_line, "session": session})
        deliveries = collections.defaultdict(list)
        for item in touches:
            if item["row"]["source"] == "delivery":
                deliveries[item["row"]["touchID"]].append(item)
        for touch_id in spec["touch_ids"]:
            delivery = deliveries[touch_id]
            down, up = [item["row"] for item in delivery]
            assert [down["phase"], up["phase"]] == [0, 3]
            assert down["x"] == up["x"] and down["y"] == up["y"]
            assert down["tapCount"] == up["tapCount"] == 1
            low, high = down["deliveredT"] - .2, up["deliveredT"] + 1.5
            selected = [item for item in frames if low <= item["row"]["t"] <= high]
            next_downs = [item for rows in deliveries.values() for item in rows
                          if item["row"]["phase"] == 0 and item["row"]["deliveredT"] > up["deliveredT"]]
            next_down = min(next_downs, key=lambda item: item["row"]["deliveredT"]) if next_downs else None
            segment_values = [item for item in values if item["row"]["control"] == spec["control"]
                              and low <= item["row"]["t"] <= high]
            assert len(segment_values) == 1
            direction = "off-to-on" if segment_values[0]["row"]["value"] else "on-to-off"
            segment_id = f"{spec['id']}-tap{touch_id}-{direction}"
            segment = {"id": segment_id, "source_id": spec["id"], "touch_id": touch_id,
                       "control": spec["control"], "direction": direction,
                       "requested_window_t": [low, high], "frame_rows": []}
            carrier_rows, raw_frame_rows = [], []
            for item in selected:
                frame, line = item["row"], item["source_line"]
                kept = [view for view in frame["views"] if view["path"] == spec["control_path"]
                        or view["path"] == spec["lens_path"] or view["path"].startswith(spec["lens_path"] + "/")]
                lens = next(view for view in kept if view["path"] == spec["lens_path"])
                assert lens["class"] == "_UILiquidLensView"
                carrier_rows.append(lens)
                raw_frame_rows.append(frame)
                for key in frame:
                    if key != "views" and key not in frame_columns:
                        frame_columns.append(key)
                observed_nodes = []
                for view in kept:
                    fields = sorted(view)
                    identity = (spec["id"], view["path"], view["class"], tuple(fields))
                    if identity not in catalog_lookup:
                        catalog_lookup[identity] = len(catalog)
                        catalog.append({"id": len(catalog), "source_id": spec["id"], "path": view["path"],
                                        "class": view["class"], "recorded_fields": fields,
                                        "role": "control" if view["path"] == spec["control_path"] else
                                        "lens_carrier" if view["path"] == spec["lens_path"] else "observed_descendant"})
                    for key in view:
                        if key not in ["path", "class"] and key not in node_columns:
                            node_columns.append(key)
                    observed_nodes.append((catalog_lookup[identity], view))
                segment["frame_rows"].append((line, frame, observed_nodes))
                csv_rows.append({"segment": segment_id, "source_id": spec["id"], "source_line": line,
                                 "frame": frame["frame"], "frame_t": frame["t"],
                                 "ms_from_delivered_down": (frame["t"] - down["deliveredT"]) * 1000,
                                 "ms_from_delivered_up": (frame["t"] - up["deliveredT"]) * 1000,
                                 "displayTimestamp": frame["displayTimestamp"],
                                 "displayIntervalMs": frame["displayIntervalMs"],
                                 "captureCostMs": frame["captureCostMs"],
                                 "captureStartT": frame.get("captureStartT"), "captureEndT": frame.get("captureEndT"),
                                 **{key: lens.get(key) for key in STATE_FIELDS},
                                 "presentationAvailable": lens.get("presentationAvailable")})
            segment["recorded_frame_fields"] = sorted(key for key in raw_frame_rows[0] if key != "views")
            assert all(set(frame) - {"views"} == set(segment["recorded_frame_fields"]) for frame in raw_frame_rows)
            intervals = [(b["displayTimestamp"] - a["displayTimestamp"]) * 1000
                         for a, b in zip(raw_frame_rows, raw_frame_rows[1:])]
            gaps = [{"before_source_line": a["source_line"], "after_source_line": b["source_line"], "interval_ms": dt}
                    for a, b, dt in zip(selected, selected[1:], intervals) if dt > 25]
            tail = [(item, lens) for item, lens in zip(selected, carrier_rows)
                    if up["deliveredT"] + 1.2 <= item["row"]["t"] <= up["deliveredT"] + 1.5]
            final = carrier_rows[-1]
            suffix = len(carrier_rows) - 1
            while suffix > 0 and all(carrier_rows[suffix - 1].get(key) == final.get(key) for key in STATE_FIELDS):
                suffix -= 1
            peak_index = max(range(len(carrier_rows)), key=lambda index: carrier_rows[index]["boundsW"])
            def observation(index):
                item, lens = selected[index], carrier_rows[index]
                return {"source_line": item["source_line"], "frame": item["row"]["frame"], "t": item["row"]["t"],
                        "ms_from_delivered_up": (item["row"]["t"] - up["deliveredT"]) * 1000,
                        **{key: lens[key] for key in STATE_FIELDS if key in lens}}
            before_indices = [index for index, item in enumerate(selected) if item["row"]["t"] < down["deliveredT"]]
            summary = {"id": segment_id, "source_id": spec["id"], "touch_id": touch_id, "direction": direction,
                       "sample_down_t": down["sampleT"], "sample_up_t": up["sampleT"],
                       "sample_duration_ms": (up["sampleT"] - down["sampleT"]) * 1000,
                       "delivered_down_t": down["deliveredT"], "delivered_up_t": up["deliveredT"],
                       "delivered_duration_ms": (up["deliveredT"] - down["deliveredT"]) * 1000,
                       "delivery_source_lines": [item["source_line"] for item in delivery],
                       "phases": [down["phase"], up["phase"]], "displacement_pt": [0, 0],
                       "requested_window_t": [low, high], "frame_count": len(selected),
                       "frame_source_line_range": [selected[0]["source_line"], selected[-1]["source_line"]],
                       "first_frame_ms_from_down": (raw_frame_rows[0]["t"] - down["deliveredT"]) * 1000,
                       "last_frame_ms_from_up": (raw_frame_rows[-1]["t"] - up["deliveredT"]) * 1000,
                       "observed_hz_by_display_timestamp": (len(selected) - 1) / (raw_frame_rows[-1]["displayTimestamp"] - raw_frame_rows[0]["displayTimestamp"]),
                       "interval_ms_min_median_max": [min(intervals), statistics.median(intervals), max(intervals)],
                       "display_gaps_over_25ms": gaps,
                       "estimated_unobserved_60hz_slots": sum(max(0, math.floor(dt / (1000 / 60) + .5) - 1) for dt in intervals),
                       "missing_source_frame_ids_inside_window": sum(max(0, b["frame"] - a["frame"] - 1) for a, b in zip(raw_frame_rows, raw_frame_rows[1:])),
                       "truncated_frame_count": sum(bool(row["truncated"]) for row in raw_frame_rows),
                       "next_delivered_down_t": next_down["row"]["deliveredT"] if next_down else None,
                       "next_input_inside_window": bool(next_down and next_down["row"]["deliveredT"] <= high),
                       "last_observed_pre_down": observation(before_indices[-1]),
                       "peak_local_width_observation": observation(peak_index),
                       "last_observation": observation(len(selected) - 1),
                       "all_frame_ranges": ranges(carrier_rows, STATE_FIELDS),
                       "tail_1200_to_1500ms_after_up": {"frame_count": len(tail),
                           "first_source_line": tail[0][0]["source_line"], "last_source_line": tail[-1][0]["source_line"],
                           "ranges": ranges([lens for item, lens in tail], STATE_FIELDS)},
                       "final_exact_state_suffix": {"first_observed": observation(suffix),
                           "preceding_observation": observation(suffix - 1) if suffix else None,
                           "frame_count": len(selected) - suffix},
                       "value_events": segment_values}
            summaries.append(summary)
            segments.append(segment)
            input_segments.append({"id": segment_id, "source_id": spec["id"], "touch_id": touch_id,
                                   "touch_observations": [item for item in touches if item["row"]["touchID"] == touch_id],
                                   "value_events": segment_values})
    for segment in segments:
        segment["frame_rows"] = [[line, [frame.get(key) for key in frame_columns],
                                  [[catalog_id, [view.get(key) for key in node_columns]] for catalog_id, view in nodes]]
                                 for line, frame, nodes in segment["frame_rows"]]
    observation_data = {"schema": 1, "frame_columns": frame_columns, "node_columns": node_columns,
                        "node_catalog": catalog, "segments": segments}
    rules = {"coordinate_unit": "original window pt; no scaling, alignment, fitting, smoothing or interpolation",
             "frame_selection": "Each actual frame row whose original t is inclusively within delivered DOWN minus 0.200 s and delivered UP plus 1.500 s; no synthetic boundary frames.",
             "node_selection": "Original UISwitch control node plus the exact _UILiquidLensView carrier path and every recorded descendant under that path; non-target controls excluded.",
             "line_numbering": "1-based physical lines of the SHA-checked original trace.jsonl",
             "time_clocks": "sampleT is UITouch timestamp minus source origin; deliveredT is observer delivery time; frame t is row enqueue time. displayTimestamp is absolute display-link uptime. These clocks/fields are retained separately.",
             "absent_fields": "Null column cells for fields absent from recorded_fields mean unrecorded, not zero/identity. Explicit original null is retained when the field occurs in recorded_fields.",
             "opacity": "opacity/effectiveOpacity are recorded CALayer/view-chain opacity. No materialAlpha, optical alpha, solid fill alpha or rendered pixel transparency is inferred.",
             "cadence": "Observed Hz=(N-1)/displayTimestamp span; gaps are consecutive selected displayTimestamp differences >25 ms. Estimated unobserved 60 Hz slots=sum(max(0,floor(dt/(1000/60)+0.5)-1)); this is a sampling-cadence estimate, not a claim of rendered dropped frames.",
             "tail": "Tail ranges use actual frame t from UP+1.200 to UP+1.500 s. Exact-state suffix is equality of recorded carrier geometry/transform/opacity/hidden fields to the final selected row; its first row is only an observed bound, not an inferred settling instant."}
    output = {"sources.json": encoded({"schema": 1, "source_root_alias": "R (original Sleepy reference workspace supplied through --source-root)", "selection_rules": rules, "sources": source_records}),
              "inputs.json": encoded({"schema": 1, "segments": input_segments}),
              "observations.json": encoded(observation_data, compact=True),
              "summary.json": encoded({"schema": 1, "segments": summaries})}
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(csv_rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(csv_rows)
    output["carrier.csv"] = stream.getvalue().encode()
    output["native-tap-curves.svg"] = make_native_svg(csv_rows, summaries)
    output["README.md"] = make_readme(summaries, catalog).encode()
    output["verification.json"] = encoded(audit_tables(root, output))
    manifest = {"schema": 1, "generator_sha256": sha(Path(__file__).read_bytes()),
                "artifacts": [{"path": name, "bytes": len(payload), "sha256": sha(payload)} for name, payload in output.items()]}
    output["manifest.json"] = encoded(manifest)
    return output


def audit_tables(root, output):
    """Independently decode the exported tables and compare to original rows."""
    data = json.loads(output["observations.json"])
    inputs = {item["id"]: item for item in json.loads(output["inputs.json"])["segments"]}
    summaries = {item["id"]: item for item in json.loads(output["summary.json"])["segments"]}
    csv_data = list(csv.DictReader(io.StringIO(output["carrier.csv"].decode())))
    node_instances = frame_instances = touch_instances = 0
    unique_frames = set()
    csv_index = 0
    for spec in SOURCES:
        segments = [item for item in data["segments"] if item["source_id"] == spec["id"]]
        reconstructed = {}
        expected_lines = {item["id"]: [] for item in segments}
        expected_touches = {item["id"]: [] for item in segments}
        expected_values = {item["id"]: [] for item in segments}
        for segment in segments:
            for line, frame_values, node_values in segment["frame_rows"]:
                fields = dict(zip(data["frame_columns"], frame_values))
                fields = {key: fields[key] for key in segment["recorded_frame_fields"]}
                nodes = []
                for catalog_id, values in node_values:
                    entry = data["node_catalog"][catalog_id]
                    assert entry["source_id"] == spec["id"]
                    view = dict(zip(data["node_columns"], values))
                    view.update(path=entry["path"], **{"class": entry["class"]})
                    view = {key: view[key] for key in entry["recorded_fields"]}
                    nodes.append(view)
                    node_instances += 1
                reconstructed[(segment["id"], line)] = (fields, nodes)
                unique_frames.add((spec["id"], line))
        with (root / spec["directory"] / "trace.jsonl").open() as handle:
            for line, text in enumerate(handle, 1):
                raw = json.loads(text)
                for segment in segments:
                    low, high = segment["requested_window_t"]
                    if raw["event"] == "frame" and low <= raw["t"] <= high:
                        expected_lines[segment["id"]].append(line)
                        frame, nodes = reconstructed[(segment["id"], line)]
                        assert frame == {key: value for key, value in raw.items() if key != "views"}
                        expected = [view for view in raw["views"] if view["path"] == spec["control_path"]
                                    or view["path"] == spec["lens_path"] or view["path"].startswith(spec["lens_path"] + "/")]
                        assert nodes == expected, f"Raw node reconstruction mismatch: {segment['id']}:{line}"
                        frame_instances += 1
                    elif raw["event"] == "touch" and raw["touchID"] == segment["touch_id"]:
                        expected_touches[segment["id"]].append({"source_line": line, "row": raw})
                    elif raw["event"] == "value" and raw["control"] == spec["control"] and low <= raw["t"] <= high:
                        expected_values[segment["id"]].append({"source_line": line, "row": raw})
        for segment in segments:
            assert [row[0] for row in segment["frame_rows"]] == expected_lines[segment["id"]]
            assert inputs[segment["id"]]["touch_observations"] == expected_touches[segment["id"]]
            assert inputs[segment["id"]]["value_events"] == expected_values[segment["id"]]
            touch_instances += len(expected_touches[segment["id"]])
            summary = summaries[segment["id"]]
            assert summary["missing_source_frame_ids_inside_window"] == 0
            assert summary["truncated_frame_count"] == 0
            assert not summary["next_input_inside_window"]
            assert summary["tail_1200_to_1500ms_after_up"]["frame_count"] == 18
            for line, frame_values, node_values in segment["frame_rows"]:
                frame, nodes = reconstructed[(segment["id"], line)]
                lens = next(view for view in nodes if view["path"] == spec["lens_path"])
                row = csv_data[csv_index]
                assert row["segment"] == segment["id"] and int(row["source_line"]) == line
                assert float(row["frame_t"]) == frame["t"]
                assert int(row["frame"]) == frame["frame"]
                assert float(row["ms_from_delivered_up"]) == (frame["t"] - summary["delivered_up_t"]) * 1000
                assert float(row["ms_from_delivered_down"]) == (frame["t"] - summary["delivered_down_t"]) * 1000
                for field in STATE_FIELDS + ["presentationAvailable"]:
                    assert row[field] == (str(lens[field]) if field in lens else "")
                csv_index += 1
    assert csv_index == len(csv_data) == frame_instances
    svg_root = ET.fromstring(output["native-tap-curves.svg"])
    ns = {"s": "http://www.w3.org/2000/svg"}
    series_groups = svg_root.findall(".//s:g[@data-panel]", ns)
    assert len(series_groups) == 24
    plot_breaks = {}
    plotted_points = 0
    for group in series_groups:
        segment_id = group.attrib["data-segment"]
        rows = [row for row in csv_data if row["segment"] == segment_id]
        panel_index = next(i for i, panel in enumerate(PLOT_PANELS) if panel[0] == group.attrib["data-panel"])
        assert group.attrib["data-source-lines"] == ",".join(row["source_line"] for row in rows)
        circles = group.findall("s:circle", ns)
        assert len(circles) == len(rows)
        for circle, row in zip(circles, rows):
            x, y = plot_xy(row, summaries[segment_id], panel_index)
            assert (circle.attrib["cx"], circle.attrib["cy"]) == (x, y)
        chunks = plot_chunks(rows)
        polylines = group.findall("s:polyline", ns)
        assert len(polylines) == len(chunks)
        for polyline, chunk in zip(polylines, chunks):
            assert polyline.attrib["points"] == " ".join(",".join(plot_xy(row, summaries[segment_id], panel_index)) for row in chunk)
            for before, after in zip(chunk, chunk[1:]):
                assert (float(after["displayTimestamp"]) - float(before["displayTimestamp"])) * 1000 <= 25
                assert (float(after["frame_t"]) - float(before["frame_t"])) * 1000 <= 25
        plot_breaks[segment_id] = len(chunks) - 1
        plotted_points += len(circles)
    return {"schema": 1, "passed": True, "method": "Decode compact tables, reconstruct each selected original frame context and view dictionary, compare exactly to original physical source lines; independently enumerate complete time-window membership, touch/value rows and CSV carrier values.",
            "source_sha_checked_files": 4, "segments": len(data["segments"]),
            "frame_instances": frame_instances, "unique_source_frames": len(unique_frames),
            "node_instances": node_instances, "touch_observations": touch_instances,
            "carrier_csv_rows": len(csv_data), "complete_requested_window_membership": True,
            "exact_raw_field_reconstruction": True, "no_missing_original_frame_ids": True,
            "no_next_input_in_selected_windows": True, "no_truncated_frame": True,
            "tail_frames_per_segment": 18, "material_alpha_inferred": False,
            "native_svg": {"panels": 3, "series_per_panel": 8, "actual_markers": plotted_points,
                           "marker_coordinates_match_carrier_csv": True,
                           "disconnect_threshold_ms": 25, "gap_clocks": ["displayTimestamp", "frame_t"],
                           "line_breaks_per_series_per_panel": plot_breaks,
                           "center_displacement_baseline": "World x+w/2 of last observed frame before delivered DOWN; no sign flip",
                           "time_axis": "Original frame t minus delivered UP; no retiming", "native_only": True}}


def make_readme(summaries, catalog):
    lines = ["# iOS 26.5 ordinary Toggle taps", "",
             "Eight observed taps: six SwiftUI taps (B9B touch IDs 7–12), then the first two UIKit taps in ToggleGrid (IDs 6/7). Both session files say `Version 26.5 (Build 23F77)`, 375×667 pt, scale 2, requested capture 60 Hz, reduce motion/transparency false. Native reference fixture evidence; no Android parity or material-alpha claim.", "",
             "[sources.json](sources.json) retains both complete sessions, R-relative source paths, byte sizes, SHA-256 identities and selection/time rules. R denotes the original Sleepy reference workspace passed to the script; no machine-specific absolute path is embedded.", "",
             "[inputs.json](inputs.json) retains original delivery and coalesced DOWN/UP rows and value events, all with original 1-based line numbers. Every selected delivery has phases `[0,3]`, `tapCount=1`, zero displacement and no move. Ordinary taps are distinct from the 450 ms hold/drag endpoint traces.", "",
             "## Reproduce and verify", "", "```sh",
             "python3 export.py --source-root /path/to/original-sleepy-workspace",
             "python3 export.py --source-root /path/to/original-sleepy-workspace --verify", "```", "",
             "The second command reads sources, recomputes every selected observation and compares every generated file byte-for-byte without writing. A separate table audit decodes each compact row, reconstructs every selected original frame/view dictionary and compares it to the original physical source line; it also independently enumerates complete time-window membership and validates the CSV/input rows. [verification.json](verification.json) retains counts and checks. Source SHA mismatches fail immediately. Only files in this study directory are generated; no full trace/video is copied. `manifest.json` covers generated outputs and the generator identity.", "",
             "## Measured input and sampling", "",
             "`sampleT` is the touch sample clock. `deliveredT` is the observer delivery clock. Frame `t` is row enqueue time; it is not the exact per-node getter instant. Rich B9B frames also retain capture start/end; earlier UIKit source frames never recorded those fields. All times remain separate.", "",
             "Frames are selected inclusively by original frame `t`, from delivery DOWN−200 ms through delivery UP+1500 ms. No invented endpoints, resampling, fitting or interpolation. None of these eight windows includes the next delivered DOWN.", "",
             "| Segment | Sample ms | Delivery ms | Actual frames | Observed Hz | >25 ms gaps | Largest gap ms | Estimated 60 Hz slots absent | Last frame after UP ms |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for row in summaries:
        lines.append(f"| {row['id']} | {row['sample_duration_ms']:.3f} | {row['delivered_duration_ms']:.3f} | {row['frame_count']} | {row['observed_hz_by_display_timestamp']:.3f} | {len(row['display_gaps_over_25ms'])} | {row['interval_ms_min_median_max'][2]:.3f} | {row['estimated_unobserved_60hz_slots']} | {row['last_frame_ms_from_up']:.3f} |")
    lines += ["", "Observed Hz uses consecutive actual display timestamps; >25 ms gaps and the explicitly defined 60 Hz slot estimate describe sampling cadence, not proved rendered frame drops. All selected original frame IDs are consecutive, no selected frame reports traversal truncation, and every selected frame contains the target lens. Exact gap endpoints are in [summary.json](summary.json).", "",
              "## Width, height and x trajectories", "",
              "![iOS 26.5 native-only ordinary Toggle tap curves](native-tap-curves.svg)", "",
              "The reproducible SVG uses the same eight actual carrier series. Its x axis is original frame `t` minus delivered UP; y axes are local bounds width/height and signed world-center displacement `(x+w/2) − baseline`, where baseline is the last observed frame before that tap's delivered DOWN. OFF→ON and ON→OFF retain their actual signs. The eight legend durations are delivery durations. Each marker is an actual frame; straight connectors are visual guides, disconnected whenever either consecutive display timestamps or frame-row `t` differ by >25 ms. No points are added, fitted, interpolated, resampled or retimed. This is native evidence only, not an Android comparison. SVG screen coordinates are rounded to 0.001 px; original numerical values remain in the CSV/JSON.", "",
              "[carrier.csv](carrier.csv) contains every selected carrier frame, original source line/frame number, original timing, local bounds, world x/y/w/h, recorded transform components, and recorded layer opacity. Blank CSV cells are unrecorded fields. World bounding width/height can differ from local bounds during transforms; x is the world left edge, not the lens center.", "",
              "The following values are actual rows: local width maximum, that same row's local height and world left x, then the final selected row. The peak time uses frame row t relative to delivered UP; it is not a fitted peak or an exact getter time.", "",
              "| Segment | Peak local W×H pt | World x at that row pt | Row after UP ms | Final local W×H pt | Final world x/y pt | Tail frames |",
              "|---|---:|---:|---:|---:|---:|---:|"]
    for row in summaries:
        peak, final = row["peak_local_width_observation"], row["last_observation"]
        lines.append(f"| {row['id']} | {peak['boundsW']:.6f}×{peak['boundsH']:.6f} | {peak['x']:.6f} | {peak['ms_from_delivered_up']:.3f} | {final['boundsW']:g}×{final['boundsH']:g} | {final['x']:g}/{final['y']:g} | {row['tail_1200_to_1500ms_after_up']['frame_count']} |")
    lines += ["", "All 18 observed frames in each UP+1200…1500 ms tail have exact local/world 37×24 pt and constant destination x (318 pt ON, 296 pt OFF); y is 317 pt for B9B SwiftUI and 389.5 pt for ToggleGrid UIKit. Recorded m11/m22 and layer opacity are 1 in these tails. This establishes only the recorded geometry/opacity over that tail. Full-interval ranges and the preceding/first exact final-state rows remain in summary.json; no settling time between frames is asserted.", "",
              "## Retained target nodes and limitations", "",
              "[observations.json](observations.json) uses compact column arrays. Each `frame_rows` entry is `[source_line, frame_values, [[node_catalog_id, node_values], …]]`. Zip values with `frame_columns`/`node_columns`, retain only the frame's `recorded_frame_fields` or catalog's `recorded_fields`, and restore catalog path/class. This reconstructs each selected original frame context and each selected original view dictionary exactly. Every original recorded descendant beneath the lens is retained; node absence on a frame is not filled forward.", "",
              "B9B records the UISwitch, _UILiquidLensView carrier and observed ClearGlassView, SDFView, SDFElementView and _UIPortalView descendants. Their paths can change with the native hierarchy. The earlier ToggleGrid logger records UISwitch, _UILiquidLensView and ClearGlassView here, and only m11/m22 of the transform. It does not record m12/m21/m41/m42, effectiveOpacity, presentationAvailable, captureStartT or captureEndT. Missing fields stay missing; identity transforms are not invented.", "",
              "No recorded target class is explicitly named Solid. SDF/Portal classes are preserved as observed classes, not relabeled as a solid fill or as proof of material implementation. Unlogged native layers cannot be reconstructed. Carrier/descendant opacity (1 in these observations) is CALayer/view-chain opacity; it is never materialAlpha, optical alpha or proof that the material was opaque. These traces do not establish rendered pixel transparency, blur/refraction, or video synchronization.", "",
              "Only small derived evidence and this script are stored here. No whole trace/video, Git operation, build, device operation, product edit or model fit is part of this study.", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--verify", action="store_true", help="compare regenerated bytes without writing")
    args = parser.parse_args()
    output = build(args.source_root)
    if args.verify:
        for name, payload in output.items():
            assert (HERE / name).read_bytes() == payload, f"Export mismatch: {name}"
        print(json.dumps({"verified": True, "generated_files": len(output), "segments": 8,
                          "carrier_frames": sum(1 for line in output["carrier.csv"].splitlines()) - 1,
                          "total_generated_bytes": sum(map(len, output.values()))}))
    else:
        for name, payload in output.items():
            (HERE / name).write_bytes(payload)
        print(json.dumps({"written": list(output), "total_generated_bytes": sum(map(len, output.values()))}))


if __name__ == "__main__":
    main()
