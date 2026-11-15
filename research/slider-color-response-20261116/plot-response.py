#!/usr/bin/env python3
"""Render complete-ROI descriptive figures from an already completed analysis.

This adds no model, threshold, registration, fit, or native capture. --self-test
uses only generated arrays in a temporary ignored directory, never real pixels.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".local" / "matplotlib"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np

ROUNDS = ("control-pre", "global-R", "global-G", "global-B",
          "mask-R", "mask-G", "mask-B", "control-post")
ROI = (331, 795, 419, 883)
BINS = (0, .5, 1, 1.5, 2, 3, 4, 5, 6, 7, 8, 10, 14, 20)
CHANNELS = "RGB"
MODELS = (("common_all", "Common: all 9 components"),
          *(("input_" + c, "Input " + c + ": 3 output components") for c in CHANNELS),
          *(("output_" + c, "Output " + c + ": 3 input components") for c in CHANNELS))
EXTENT = (ROI[0] / 2, ROI[2] / 2, ROI[3] / 2, ROI[1] / 2)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def array(data, key, shape, kind="numeric"):
    require(key in data, "missing analysis array: " + key)
    a = data[key]
    require(a.shape == shape, f"{key} shape {a.shape}, expected {shape}")
    if kind == "bool":
        require(a.dtype == np.bool_, key + " must retain recorded boolean compatibility")
    else:
        require(np.issubdtype(a.dtype, np.number) and np.isfinite(a).all(),
                key + " must be finite numeric evidence")
    return a


def load_data(directory):
    report_path = directory / "analysis.json"
    arrays_path = directory / "original-pixels.npz"
    report = json.loads(report_path.read_text())
    require(report["status"] == "OBSERVED_ENCODED_COLOR_CALIBRATION_DIAGNOSTIC_NOT_OPTICAL_ACCEPTANCE",
            "only completed observed analysis is plotted; rejected evidence stays rejected")
    require(report["round_order"] == list(ROUNDS) and report["ROI_xyxy_original_pixels"] == list(ROI),
            "unexpected round order or fixed ROI")
    require(report["matrix_axes"] == ["output_RGB", "input_RGB"]
            and report["primary_tolerance_raw_byte"] == 4 and report["inset_bins"] == list(BINS),
            "unexpected frozen matrix axes, tolerance or inset bins")
    require(sha(arrays_path) == report["arrays_sha256"], "analysis array hash mismatch")
    shape = (ROI[3] - ROI[1], ROI[2] - ROI[0])
    with np.load(arrays_path, allow_pickle=False) as stored:
        keys = ["x", "y", "inset_capsule_assumption", "original_ROIs_round_shape_flat_outputRGB",
                "raw_global_output_input", "raw_mask_output_input"]
        keys += [prefix + suffix for prefix, _ in MODELS
                 for suffix in ("_minimax_error", "_T4_compatible")]
        require(all(key in stored.files for key in keys), "missing required descriptive array")
        data = {key: stored[key].copy() for key in keys}
    for key in ("x", "y", "inset_capsule_assumption"):
        array(data, key, shape)
    yy, xx = np.mgrid[ROI[1]:ROI[3], ROI[0]:ROI[2]]
    require(np.array_equal(data["x"], (xx + .5) / 2)
            and np.array_equal(data["y"], (yy + .5) / 2), "changed original pixel-center grid")
    images = array(data, "original_ROIs_round_shape_flat_outputRGB", (8, 2, *shape, 3))
    require(images.dtype == np.uint8, "original ROI bytes must be uint8")
    for key in ("raw_global_output_input", "raw_mask_output_input"):
        array(data, key, (*shape, 3, 3))
    for ids, key in (((1, 2, 3), "raw_global_output_input"), ((4, 5, 6), "raw_mask_output_input")):
        expected = np.stack([images[i, 0].astype(np.int16) - images[0, 0] for i in ids], axis=-1)
        require(np.array_equal(data[key], expected), key + " differs from original ROI byte contrasts")
    for prefix, _ in MODELS:
        error = array(data, prefix + "_minimax_error", shape)
        require(np.all(error >= 0), "negative minimax error")
        array(data, prefix + "_T4_compatible", shape, "bool")
    return report, data, {"analysis_json_sha256": sha(report_path), "original_pixels_npz_sha256": sha(arrays_path)}


def annotate(ax):
    for y in (422, 438):
        ax.axhline(y, color="white", linewidth=1.5, linestyle="--")
        ax.axhline(y, color="#171717", linewidth=.7, linestyle="--")
    ax.set(xlim=EXTENT[:2], ylim=EXTENT[2:], xlabel="World x (pt)", ylabel="World y (pt)")
    ax.tick_params(labelsize=7)


def save(fig, output, name, caption):
    fig.suptitle(caption, fontsize=12)
    fig.savefig(output / name, dpi=160, facecolor="white", bbox_inches="tight")
    plt.close(fig)


def native_figure(data, output):
    fig, axes = plt.subplots(8, 2, figsize=(8.2, 25), constrained_layout=True)
    images = data["original_ROIs_round_shape_flat_outputRGB"]
    for r, name in enumerate(ROUNDS):
        for c, label in enumerate(("Shape", "Unchanged-source flat partner")):
            ax = axes[r, c]
            ax.imshow(images[r, c], extent=EXTENT, origin="upper", interpolation="nearest")
            annotate(ax)
            ax.set_title(name + " — " + label, fontsize=9)
    save(fig, output, "native-eight-rounds-full-ROI.png",
         "All 16 original native ROI byte arrays; full fixed ROI, no registration\nDashed lines: rail band y=422…438pt; nearest-neighbor display only")


def matrix_figure(values, limit, output, name, label):
    fig, axes = plt.subplots(3, 3, figsize=(11, 10), constrained_layout=True)
    for i, out in enumerate(CHANNELS):
        for j, inp in enumerate(CHANNELS):
            v = values[..., i, j]
            ax = axes[i, j]
            image = ax.imshow(v, extent=EXTENT, origin="upper", interpolation="nearest",
                              cmap="RdBu_r", vmin=-limit, vmax=limit)
            annotate(ax)
            ax.set_title(f"out {out} / in {inp}; min {v.min():g}, max {v.max():g}", fontsize=8)
    fig.colorbar(image, ax=axes.ravel().tolist(), shrink=.7, label="Signed encoded-byte contrast")
    save(fig, output, name, f"{label}: all 9 signed components, complete fixed ROI\nShared U/M axis ±{limit:g} raw bytes; includes every observed extremum")


def model_figure(data, output, maximum, binary=False):
    fig, axes = plt.subplots(2, 4, figsize=(15, 7.5), constrained_layout=True)
    for ax, (prefix, title) in zip(axes.flat, MODELS):
        error = data[prefix + "_minimax_error"]
        compatible = data[prefix + "_T4_compatible"]
        if binary:
            image = ax.imshow(~compatible, extent=EXTENT, origin="upper", interpolation="nearest",
                              cmap=ListedColormap(["#f3f4f6", "#be123c"]), vmin=0, vmax=1)
        else:
            image = ax.imshow(error, extent=EXTENT, origin="upper", interpolation="nearest",
                              cmap="magma", vmin=0, vmax=maximum)
        annotate(ax)
        ax.set_title(f"{title}\nmax {error.max():.6g} bytes; T4 incompatible {(~compatible).sum()}/{compatible.size}", fontsize=8)
    note = axes.flat[-1]
    note.axis("off")
    note.text(.03, .97, ("Full 88×88 ROI in every panel.\nNo failure mask or rail cropping.\nDashed lines mark y=422 and 438pt.\n\n"
                         + ("Gray: recorded compatible.\nRed: recorded incompatible.\nUses saved T4 interval result;\nno threshold is recomputed."
                            if binary else
                            f"Shared linear color axis:\n0…{maximum:.6g} raw bytes.\nEvery error extremum is included.\nT4 compatibility is shown separately.")),
              va="top", fontsize=9, linespacing=1.6)
    if binary:
        name = "T4-compatibility-all-models-full-ROI.png"
        title = "Recorded T=4 bounded-null compatibility — all seven models"
    else:
        fig.colorbar(image, ax=list(axes.flat)[:-1], shrink=.7, label="Minimum possible maximum absolute residual (raw bytes)")
        name = "minimax-error-all-models-full-ROI.png"
        title = "Common, input-column and output-row minimax error — full fixed ROI"
    save(fig, output, name, title + "\nDescriptive calibration diagnostic; no optical acceptance")


def inset_curves(data, output):
    inset, y = data["inset_capsule_assumption"], data["y"]
    domains = {"Above rail (y<422pt)": y < 422, "Rail-confounded (422≤y<438pt)": (y >= 422) & (y < 438)}
    bins = np.asarray(BINS)
    centers = (bins[:-1] + bins[1:]) / 2
    fig, axes = plt.subplots(2, 2, figsize=(14, 9), constrained_layout=True)
    colors = plt.get_cmap("tab10")(np.arange(len(MODELS)))
    receipt = {}
    for row, (domain_name, domain) in enumerate(domains.items()):
        records = []
        for lo, hi in zip(bins[:-1], bins[1:]):
            mask = domain & (inset >= lo) & (inset < hi)
            record = {"inset_lo_inclusive_pt": float(lo), "inset_hi_exclusive_pt": float(hi), "pixels": int(mask.sum()), "models": {}}
            for prefix, _ in MODELS:
                error = data[prefix + "_minimax_error"][mask]
                record["models"][prefix] = {
                    "median_raw_byte": float(np.median(error)) if error.size else None,
                    "maximum_raw_byte": float(error.max()) if error.size else None,
                    "T4_incompatible_pixels": int(np.sum(~data[prefix + "_T4_compatible"][mask]))}
            records.append(record)
        for col, (key, label) in enumerate((("median_raw_byte", "Median"), ("maximum_raw_byte", "Maximum"))):
            ax = axes[row, col]
            for color, (prefix, _) in zip(colors, MODELS):
                values = [r["models"][prefix][key] for r in records]
                ax.plot(centers, [np.nan if v is None else v for v in values], marker="o", markersize=3,
                        linewidth=1.2, color=color, label=prefix)
            ax.axhline(4, color="#be123c", linestyle="--", linewidth=1, label="T=4 raw bytes")
            ax.set(xlim=(BINS[0], BINS[-1]), ylim=(0, None), xlabel="Capsule-assumption inset (pt), fixed bin centers",
                   ylabel=label + " minimax error (raw bytes)", title=domain_name + " — " + label.lower())
            ax.grid(alpha=.2)
        outside = {"negative_inset_pixels": int(np.sum(domain & (inset < BINS[0]))),
                   "inset_ge20_pixels": int(np.sum(domain & (inset >= BINS[-1])))}
        receipt[domain_name] = {"bins": records, "outside_frozen_bins": outside}
    axes[0, 0].legend(fontsize=7, ncol=2)
    below = int(np.sum(y >= 438))
    save(fig, output, "fixed-inset-minimax-error-curves.png",
         "Fixed original inset bins; empty bins are gaps; no y-axis clipping\nNegative inset, inset≥20pt and below-rail pixels remain visible in complete-ROI maps; below-rail count=" + str(below))
    return receipt


def render(directory, output):
    require(not output.exists(), "figure directory exists; refusing to overwrite")
    report, data, provenance = load_data(directory)
    output.mkdir(parents=True)
    signed_max = max(float(np.max(abs(data[key].astype(float))))
                     for key in ("raw_global_output_input", "raw_mask_output_input"))
    signed_limit = max(1., signed_max)
    error_max = max(float(data[prefix + "_minimax_error"].max()) for prefix, _ in MODELS)
    error_limit = max(4., error_max)
    native_figure(data, output)
    matrix_figure(data["raw_global_output_input"], signed_limit, output,
                  "U-global-all-nine-components-full-ROI.png", "U = global shape − pre shape")
    matrix_figure(data["raw_mask_output_input"], signed_limit, output,
                  "M-mask-all-nine-components-full-ROI.png", "M = masked shape − pre shape")
    model_figure(data, output, error_limit)
    model_figure(data, output, error_limit, binary=True)
    curves = inset_curves(data, output)
    receipt = {"schema": 1, "status": "DESCRIPTIVE_FIGURES_ONLY_NOT_MODEL_OR_ACCEPTANCE",
        "plot_script_sha256": sha(__file__), **provenance, "analysis_status": report["status"],
        "full_ROI_xyxy_original_pixels": list(ROI), "rail_band_world_y": [422, 438],
        "round_order": list(ROUNDS), "matrix_axes": ["output_RGB", "input_RGB"], "inset_bins": list(BINS),
        "color_axes": {"signed_U_M_shared": [-signed_limit, signed_limit], "observed_U_M_absolute_max": signed_max,
                       "minimax_shared": [0, error_limit], "observed_minimax_max": error_max,
                       "clipped_data_values": 0, "curve_y_axes": "automatic; every bin maximum retained; no manual upper bound"},
        "all_models_full_ROI": {prefix: {"maximum_minimax_error_raw_byte": float(data[prefix + "_minimax_error"].max()),
            "T4_incompatible_pixels": int(np.sum(~data[prefix + "_T4_compatible"])),
            "full_ROI_pixels": int(data[prefix + "_T4_compatible"].size)} for prefix, _ in MODELS},
        "fixed_inset_curve_data": curves,
        "limits": ["Figures render saved analysis arrays; they do not rerun or alter the frozen model or thresholds.",
                   "Native image panels show all original ROI bytes with nearest-neighbor display; rendered figure PNGs are not replacement measurement inputs.",
                   "Every heatmap shows the complete fixed ROI including rail, rim and incompatible pixels.",
                   "Inset curves use the frozen bins only; negative/large inset and below-rail pixels are retained in complete maps, not silently reclassified."],
        "files": {p.name: {"sha256": sha(p), "bytes": p.stat().st_size} for p in sorted(output.glob("*.png"))}}
    (output / "figure-manifest.json").write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")
    return receipt


def self_test():
    local = ROOT / ".local"
    local.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="plot-synthetic-", dir=local) as folder:
        work = Path(folder)
        input_dir = work / "synthetic-analysis"
        input_dir.mkdir()
        yy, xx = np.mgrid[ROI[1]:ROI[3], ROI[0]:ROI[2]]
        h, w = xx.shape
        base = np.stack((100 + (xx - ROI[0]) // 2, 110 + (yy - ROI[1]) // 3, np.full((h, w), 120)), axis=-1).astype(np.uint8)
        images = np.full((8, 2, h, w, 3), 128, np.uint8)
        images[:, 0] = base
        for j in range(3):
            images[1 + j, 0, ..., j] += 20
            images[4 + j, 0, ..., j] += ((xx - ROI[0]) % 15).astype(np.uint8)
        u = np.stack([images[1 + j, 0].astype(np.int16) - base for j in range(3)], axis=-1)
        m = np.stack([images[4 + j, 0].astype(np.int16) - base for j in range(3)], axis=-1)
        data = {"x": (xx + .5) / 2, "y": (yy + .5) / 2, "inset_capsule_assumption": (xx - ROI[0]) * .4 - 6,
                "original_ROIs_round_shape_flat_outputRGB": images, "raw_global_output_input": u, "raw_mask_output_input": m}
        for i, (prefix, _) in enumerate(MODELS):
            error = ((xx - ROI[0] + yy - ROI[1] + i) % 11).astype(float)
            data[prefix + "_minimax_error"] = error
            data[prefix + "_T4_compatible"] = error <= 4
        np.savez_compressed(input_dir / "original-pixels.npz", **data)
        report = {"status": "OBSERVED_ENCODED_COLOR_CALIBRATION_DIAGNOSTIC_NOT_OPTICAL_ACCEPTANCE",
                  "round_order": list(ROUNDS), "ROI_xyxy_original_pixels": list(ROI), "matrix_axes": ["output_RGB", "input_RGB"],
                  "primary_tolerance_raw_byte": 4, "inset_bins": list(BINS), "arrays_sha256": sha(input_dir / "original-pixels.npz")}
        (input_dir / "analysis.json").write_text(json.dumps(report))
        receipt = render(input_dir, work / "figures")
        require(len(receipt["files"]) == 6, "expected six complete figure artifacts")
        require(receipt["color_axes"]["observed_U_M_absolute_max"] == 20
                and receipt["color_axes"]["observed_minimax_max"] == 10, "extrema must be reported without clipping")
        for prefix, _ in MODELS:
            require(receipt["all_models_full_ROI"][prefix]["T4_incompatible_pixels"]
                    == int(np.sum(~data[prefix + "_T4_compatible"])), "incompatible pixels omitted")
        try:
            render(input_dir, work / "figures")
        except ValueError:
            pass
        else:
            raise ValueError("existing figure directory was overwritten")
        report["arrays_sha256"] = "0" * 64
        (input_dir / "analysis.json").write_text(json.dumps(report))
        try:
            load_data(input_dir)
        except ValueError:
            pass
        else:
            raise ValueError("array hash mismatch was accepted")
    print(json.dumps({"status": "synthetic_plot_checks_passed", "figure_count": 6,
        "checks": ["full 16 native panels", "U/M all nine components", "seven error and saved-T4 maps", "fixed inset bins",
                   "reported color extrema with no clipping", "all incompatible pixels retained", "overwrite refusal", "array hash refusal"],
        "scope": "generated synthetic arrays only; no actual analysis, native pixels, traces, devices or frozen files read or changed"}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", type=Path, default=ROOT / "analysis")
    parser.add_argument("--output", type=Path, default=ROOT / "figures-response")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    receipt = render(args.analysis.resolve(), args.output.resolve())
    print(json.dumps({"status": receipt["status"], "output": str(args.output.resolve()), "figures": len(receipt["files"])}))


if __name__ == "__main__":
    main()
