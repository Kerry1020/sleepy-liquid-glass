#!/usr/bin/env python3
"""Render two explanatory figures from existing frozen signed-G analysis only."""
from pathlib import Path
import hashlib
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
F = ROOT.parent / "slider-linear-response-20261116"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    source = ROOT / "analysis/signed-output.npz"
    analysis = F / "signed-results/analysis.json"
    with np.load(source, allow_pickle=False) as data:
        t, rgb = data["t"].copy(), data["output_rgb"].copy()
        x, y = data["x"].copy(), data["y"].copy()
    results = json.loads(analysis.read_text())["results"]
    assert rgb.shape == (4, 88, 88, 3) and np.array_equal(t, [-40, -20, 0, 20])
    target = ROOT / "figures"
    target.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 4, figsize=(12, 3.7), layout="constrained")
    for i, ax in enumerate(axes):
        ax.imshow(rgb[i], interpolation="nearest")
        ax.set_title(f"Source G {int(t[i]):+d} encoded bytes")
        ax.set_xticks([]); ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
    fig.suptitle("Original native Slider pixels | same fixed 88 x 88 ROI", fontsize=14)
    fig.text(.5, .005, "Original PNG crop [331,795,419,883); nearest-neighbour presentation; no colour enhancement",
             ha="center", fontsize=10)
    roi_figure = target / "signed-G-native-ROI.png"
    fig.savefig(roi_figure, dpi=160, facecolor="white")
    plt.close(fig)

    match = (x == 192.75) & (y == 411.25)
    assert int(match.sum()) == 1
    samples = rgb[:, match, :][:, 0, :]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.7), layout="constrained",
                             gridspec_kw={"width_ratios": [1, 1.4]})
    fig.get_layout_engine().set(rect=(0, .08, 1, .92))
    ax = axes[0]
    for ci, (label, color) in enumerate((("Output R", "#d33d38"), ("Output G", "#228046"),
                                       ("Output B", "#326ac2"))):
        ax.plot(t, samples[:, ci], "o-", color=color, label=label, linewidth=1.8)
        for tx, value in zip(t, samples[:, ci]):
            ax.annotate(str(int(value)), (tx, value), xytext=(0, -14 if ci == 2 else 5), textcoords="offset points",
                        ha="center", fontsize=9, color=color)
    ax.set(title="Observed sample at world (192.75, 411.25)",
           xlabel="Encoded source G step (bytes)", ylabel="Observed output byte", xticks=t,
           ylim=(-3, 128))
    ax.grid(alpha=.18); ax.legend(loc="center left", fontsize=9)
    domains = ("full", "primary", "above_rail_inset_0_1")
    labels = ("Full ROI (n=7744)", "Primary (n=1630)", "Above-rail rim [0,1) (n=186)")
    columns = [(model, str(tol)) for model in ("linear", "clipped_affine") for tol in (1, 4, 8)]
    counts = np.array([[results[tol][domain]["any_RGB_incompatible"][model]
                        for model, tol in columns] for domain in domains])
    ax = axes[1]
    ax.imshow(counts, cmap="YlOrRd", vmin=0, vmax=16, aspect="auto")
    ax.set_xticks(np.arange(6), [f"{'Affine' if m == 'linear' else 'Clipped'}\nT{tol}"
                               for m, tol in columns])
    ax.set_yticks(np.arange(3), labels, fontsize=10)
    ax.set_title("Pixels incompatible in any RGB output")
    for r in range(3):
        for c in range(6):
            ax.text(c, r, str(int(counts[r, c])), ha="center", va="center",
                    color="white" if counts[r, c] > 8 else "#202020", fontsize=14)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.suptitle("Finite signed-G response: affine rejection does not reject clipping", fontsize=14)
    fig.text(.5, .002, "T is total endpoint error in bytes. Lines guide the eye; no fitted native pipeline. Monotonic failures: 0 at T1/T4/T8.",
             ha="center", fontsize=9)
    response_figure = target / "signed-G-response-and-compatibility.png"
    fig.savefig(response_figure, dpi=160, facecolor="white")
    plt.close(fig)
    receipt = dict(status="DERIVED_FIGURES_FROM_EXISTING_ARRAYS_ONLY", script_sha256=sha(__file__),
                   sources={"analysis/signed-output.npz": sha(source),
                            "../slider-linear-response-20261116/signed-results/analysis.json": sha(analysis)},
                   figures={p.name: {"sha256": sha(p), "bytes": p.stat().st_size}
                            for p in (roi_figure, response_figure)},
                   processing=["Original collector ROI is half-open PNG pixel crop [331,795,419,883), 88x88.",
                               "Native ROI uses exact output_rgb bytes; nearest-neighbour display scaling only.",
                               "No denoising, interpolation of image colours, sharpening, gamma change or saturation enhancement.",
                               "Curve sample is fixed world(192.75,411.25), original ROI row27/column54; straight segments guide the eye.",
                               "Compatibility counts copied from existing F JSON; no model rerun or new parameter fit.",
                               "Original full-screen PNGs retained only in evidence; figures show ROI only."],
                   sample_world=[192.75, 411.25], t=t.tolist(), sample_RGB=samples.tolist())
    (target / "figure-sources.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
