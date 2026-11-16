#!/usr/bin/env python3
"""Prepare an external replay; never build or edit the Sleepy checkout."""
import argparse
import csv
import hashlib
import io
import json
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_EVEN
from pathlib import Path

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parent / "toggle-tap-native26-20261116"
PACKAGE = "libraries/liquid-glass/runtime/src/androidMain/kotlin/com/lingion/sleepy/ui/component/liquidglass/"
HOST_FILES = [PACKAGE + name + ".kt" for name in (
    "GlassControlMotion", "DockInputClock", "ActiveFrameLoop",
    "LiquidGlassPhysics", "NativeGlassDragDeformation",
)] + ["app/src/main/java/com/lingion/sleepy/ui/component/liquidglass/GlassSwitch.kt"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def tsv(columns, rows):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, delimiter="\t", lineterminator="\n")
    writer.writerow(columns)
    writer.writerows(rows)
    return stream.getvalue().encode()


def nanos(value):
    return int((value * Decimal(1_000_000_000)).to_integral_value(rounding=ROUND_HALF_EVEN))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sleepy-root", type=Path, required=True)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    host = args.sleepy_root.resolve(strict=True)
    if HERE.is_relative_to(host):
        raise SystemExit("Study must live outside the Sleepy checkout")
    pins = json.loads((HERE / "native-input-pins.json").read_text())
    for name, expected in pins.items():
        actual = (NATIVE / name).read_bytes()
        if sha(actual) != expected:
            raise SystemExit(f"Native input identity changed: {name}")
    inputs = json.loads((NATIVE / "inputs.json").read_text(), parse_float=Decimal)
    with (NATIVE / "carrier.csv").open(newline="") as stream:
        reader = csv.DictReader(stream)
        native_columns = reader.fieldnames
        frames = list(reader)
    segments, events, prepared_frames = [], [], []
    seen = set()
    for segment in inputs["segments"]:
        sid = segment["id"]
        if sid in seen:
            raise SystemExit("Duplicate segment")
        seen.add(sid)
        delivery = [r for r in segment["touch_observations"] if r["row"]["source"] == "delivery"]
        assert [r["row"]["phase"] for r in delivery] == [0, 3]
        down, up = [r["row"]["deliveredT"] for r in delivery]
        value_events = segment["value_events"]
        assert len(value_events) == 1 and type(value_events[0]["row"]["value"]) is bool
        target = int(value_events[0]["row"]["value"])
        actual_frames = [r for r in frames if r["segment"] == sid]
        assert actual_frames
        times = [Decimal(r["frame_t"]) for r in actual_frames]
        assert all(a < b for a, b in zip(times, times[1:]))
        baseline = [r for r in actual_frames if Decimal(r["frame_t"]) < down][-1]
        center = Decimal(baseline["x"]) + Decimal(baseline["w"]) / 2
        segments.append([sid, segment["source_id"], 1-target, target,
                         baseline["source_line"], baseline["frame"], baseline["frame_t"], center,
                         down, up, value_events[0]["source_line"], value_events[0]["row"]["t"]])
        for observed in delivery:
            row = observed["row"]
            relative_sample = row["sampleT"] - down + 1
            # Native sampleT has a session origin, unlike Android uptime. The
            # common +1s replay origin preserves its lag relative to receipt.
            sample_ms = int((relative_sample * 1000).to_integral_value(rounding=ROUND_FLOOR))
            events.append([sid, observed["source_line"], row["phase"], row["deliveredT"],
                           row["sampleT"], row["t"], nanos(row["deliveredT"]-down+1), sample_ms])
        for row in actual_frames:
            prepared_frames.append([nanos(Decimal(row["frame_t"])-down+1)] + [row[c] for c in native_columns])
    assert len(seen) == 8 and len(events) == 16 and len(prepared_frames) == 838
    assert len(prepared_frames) == len(frames)
    products = {
        "segments.tsv": tsv(["segment", "source_id", "initial", "target", "baseline_source_line",
                             "baseline_frame", "baseline_frame_t", "baseline_world_center", "delivered_down_t",
                             "delivered_up_t", "value_source_line", "value_t"], segments),
        "events.tsv": tsv(["segment", "source_line", "phase", "delivered_t", "sample_t", "row_t",
                           "received_nanos", "sample_millis"], events),
        "frames.tsv": tsv(["replay_nanos"] + native_columns, prepared_frames),
    }
    receipt = {
        "schema": 1, "status": "prepared_unexecuted",
        "segments": len(segments), "events": len(events), "frames": len(prepared_frames),
        "native_inputs": pins,
        "host_sources": {p: sha((host / p).read_bytes()) for p in HOST_FILES},
        "study_sources": {p: sha((HERE / p).read_bytes()) for p in (
            "prepare.py", "Replay.java", "replay.init.gradle", "native-input-pins.json")},
        "prepared_files": {p: sha(data) for p, data in products.items()},
        "clocks": "frame_t scheduling only; deliveredT gating; sampleT retained independently; common per-segment +1s origin; nearest-ns frame/receipt and floor-ms sample quantization",
        "scope": "core-model diagnostic; no Android GPU, optical, natural-motion or timing-sync acceptance",
    }
    products["preparation.json"] = (json.dumps(receipt, indent=2) + "\n").encode()
    dest = HERE / "prepared"
    if args.verify:
        if {p.name for p in dest.iterdir()} != set(products):
            raise SystemExit("Prepared membership mismatch")
        for name, data in products.items():
            if (dest / name).read_bytes() != data:
                raise SystemExit(f"Prepared bytes changed: {name}")
        print("Verified 8 segments, 16 delivered events, 838 actual frames; replay not executed")
    else:
        dest.mkdir(exist_ok=False)
        for name, data in products.items():
            (dest / name).write_bytes(data)
        print("Prepared 8 segments, 16 delivered events, 838 actual frames; replay not executed")


if __name__ == "__main__":
    main()
