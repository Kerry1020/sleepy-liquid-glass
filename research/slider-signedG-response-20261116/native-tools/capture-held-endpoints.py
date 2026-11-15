#!/usr/bin/env python3
"""Observe real moved endpoints; never move the reference source or native control."""
import argparse
import glob
import json
import math
import pathlib
import re
import subprocess
import time


def safe(value):
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", value)


def lens_rows(frame):
    views = frame.get("views", [])
    owners = [v for v in views if v.get("identifier") == "swiftui-slider"]
    found = []
    for owner in owners:
        found.extend(v for v in views
                     if v["path"].startswith(owner["path"] + "/")
                     and "LiquidLens" in v.get("class", "")
                     and not v.get("effectiveHidden", v.get("hidden", False))
                     and v.get("effectiveOpacity", 0) > .5)
    return found


def geometry(v):
    return [v[k] for k in ["x", "y", "w", "h"]]


def wait_for_endpoint(signal, containers):
    deadline = time.monotonic() + 18
    # App containers may change on test-runner install. Resolve only the signal's
    # unique run rather than trusting a pre-test container path.
    trace = None
    rows, pending, position = [], b"", 0
    while time.monotonic() < deadline:
        if trace is None:
            candidates = glob.glob(str(containers / "*" / "Documents" / "reference" /
                                       safe(signal["run"]) / "trace.jsonl"))
            if len(candidates) == 1:
                trace = pathlib.Path(candidates[0])
            else:
                time.sleep(.03)
                continue
        try:
            session = json.loads((trace.parent / "session.json").read_text())
            with trace.open("rb") as stream:
                stream.seek(position)
                pending += stream.read()
                position = stream.tell()
        except (OSError, json.JSONDecodeError):
            time.sleep(.03)
            continue
        lines = pending.split(b"\n")
        pending = lines.pop()
        rows.extend(json.loads(line) for line in lines if line)
        origin = session["originUnixSeconds"]
        touches = [r for r in rows if r.get("event") == "touch" and r.get("source") == "delivery"
                   and origin + r["deliveredT"] >= signal["requestedAtUnixSeconds"]]
        if any(r["phase"] in (3, 4) for r in touches):
            raise RuntimeError("Touch ended before an endpoint screenshot could be taken")
        down = next((r for r in touches if r["phase"] == 0), None)
        moves = [r for r in touches if r["phase"] == 1]
        target = signal["requestedTargetPoint"]
        if not down or not moves:
            time.sleep(.03)
            continue
        last = moves[-1]
        at_target = math.hypot(last["x"] - target["x"], last["y"] - target["y"]) <= 1
        frames = [r for r in rows if r.get("event") == "frame"
                  and r["captureStartT"] >= last["deliveredT"] + .35]
        recent = frames[-12:]
        lenses = [lens_rows(frame) for frame in recent]
        stable = (len(recent) >= 4 and all(len(v) == 1 for v in lenses)
                  and recent[-1]["captureEndT"] - recent[0]["captureStartT"] >= .12
                  and all(max(abs(a - b) for a, b in zip(geometry(v[0]), geometry(lenses[-1][0]))) <= .1
                          for v in lenses))
        after_move = time.time() - origin - last["deliveredT"]
        fresh = bool(recent) and time.time() - origin - recent[-1]["captureEndT"] < .5
        if at_target and stable and fresh and after_move >= .65:
            return {"tracePathObserved": str(trace), "observedOriginUnixSeconds": origin,
                    "observedDown": down, "observedLastMove": last,
                    "stableFrames": [{"captureStartT": r["captureStartT"],
                                      "captureEndT": r["captureEndT"],
                                      "carrier": lens_rows(r)[0]} for r in recent],
                    "observedCarrierBoundsPt": geometry(lenses[-1][0]),
                    "observedEndpointWaitSeconds": after_move}
        time.sleep(.03)
    raise RuntimeError("No real moved endpoint with stable native carrier within bounded wait")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--simulator", required=True)
    parser.add_argument("--output", required=True, type=pathlib.Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    containers = pathlib.Path.home() / "Library/Developer/CoreSimulator/Devices" / args.simulator / "data/Containers/Data/Application"
    started, seen = time.time(), set()
    pattern = str(containers / "*" / "Documents" / "slider-shape-capture-signals.jsonl")
    with (output / "capture-events.jsonl").open("a", buffering=1) as events:
        while True:
            for name in glob.glob(pattern):
                try:
                    signals = pathlib.Path(name).read_text().splitlines()
                except OSError:
                    continue
                for line in signals:
                    try:
                        signal = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    key = (signal["run"], signal["name"], signal["requestedAtUnixSeconds"])
                    if key in seen or signal["requestedAtUnixSeconds"] < started:
                        continue
                    seen.add(key)
                    row = dict(signal)
                    try:
                        row.update(wait_for_endpoint(signal, containers))
                        directory = output / safe(signal["run"])
                        directory.mkdir(exist_ok=True)
                        path = directory / (safe(signal["name"]) + ".png")
                        row["screenshotBeginUnixSeconds"] = time.time()
                        capture = subprocess.run(["xcrun", "simctl", "io", args.simulator, "screenshot", str(path)],
                                                 capture_output=True, text=True, timeout=4)
                        row.update(screenshotEndUnixSeconds=time.time(), path=str(path),
                                   exitCode=capture.returncode, output=capture.stdout + capture.stderr)
                    except Exception as error:
                        row.update(observerError=f"{type(error).__name__}: {error}")
                    row["notice"] = "Endpoint observation only; full raw trace must prove the screenshot bracket after last MOVE and before actual UP."
                    events.write(json.dumps(row) + "\n")
                    print(json.dumps({"name": signal["name"], "exitCode": row.get("exitCode"),
                                      "observerError": row.get("observerError")}), flush=True)
            time.sleep(.05)


if __name__ == "__main__":
    main()
