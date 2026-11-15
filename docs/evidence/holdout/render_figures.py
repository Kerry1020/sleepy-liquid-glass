#!/usr/bin/env python3
"""Render saved Dock holdout results locally; no captures, fitting or network.

Requires Python 3 and matplotlib. Reads only the committed small CSV/JSON files.
Run: python3 docs/evidence/holdout/render_figures.py
"""
from pathlib import Path
import csv
import hashlib
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent.parent/"images/holdout"
OUT.mkdir(parents=True, exist_ok=True)
BLUE, ORANGE, BLACK, GREY = "#2366ad", "#c17a18", "#24364a", "#8c96a1"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": "white", "axes.facecolor": "white", "svg.hashsalt": "sleepy-holdout-20261114"})


def read(name):
    with (ROOT/name).open() as handle:
        return list(csv.DictReader(handle))


def save(fig, name):
    fig.savefig(OUT/(name+".png"), dpi=160, bbox_inches="tight",
                metadata={"Software": "Matplotlib; Sleepy frozen holdout results"})
    fig.savefig(OUT/(name+".svg"), bbox_inches="tight",
                metadata={"Date": None, "Creator": "Sleepy frozen holdout results"})
    plt.close(fig)


summary = json.loads((ROOT/"summary.json").read_text())
for record in summary["exports"]:
    assert hashlib.sha256((ROOT/record["file"]).read_bytes()).hexdigest() == record["sha256"], record["file"]
cells = read("candidate-minus-baseline.csv")
triggers = read("engineering-review-triggers.csv")
assert len(cells) == 656 and len(triggers) == 12
cases = [("h01_horizontal_steps-light", "top", "2-6", "h01 light · top 2–6 pt"),
         ("h01_horizontal_steps-light", "bottom", "2-6", "h01 light · bottom 2–6 pt"),
         ("h02_chirp_pos-dark", "tip", "6-12", "h02 dark · tip 6–12 pt"),
         ("h04_multiscale_checker-dark", "bottom", "2-6", "h04 dark · bottom 2–6 pt")]
# Use original band spelling rather than silently choosing a near match.
selected = []
for scene, probe, band, title in cases:
    candidates = [r for r in cells if r["scene"] == scene and r["kind"] == "probe_depth"
                  and r["probe_or_roi"] == probe and r["depth_band_pt"] == band]
    assert len(candidates) == 1, (scene, probe, band, [r["kind"] for r in cells[:3]])
    selected.append(candidates[0])

fig, axs = plt.subplots(2, 2, figsize=(10.4, 7.2))
for ax, row, (_, _, _, title) in zip(axs.flat, selected, cases):
    values = [float(row[k+"_deltaE00_median"]) for k in ("baseline", "candidate")]
    bars = ax.bar([0, 1], values, width=.55, color=[ORANGE, BLUE])
    ax.bar_label(bars, fmt="%.3f", padding=3)
    ax.set_xticks([0, 1], ["D31 baseline", "D46.5 candidate"])
    ax.set_ylim(0, max(values)*1.25)
    ax.set_ylabel("Absolute error vs native (ΔE00 median)")
    ax.set_title(title)
    ax.grid(axis="y", alpha=.25)
    ax.set_axisbelow(True)
    change = float(row["change_deltaE00_median"])
    bound = float(row["geometry_sensitivity_bound_deltaE00_median"])
    ax.text(.5, .88, f"Candidate − baseline: {change:+.3f}\nFinite contour sensitivity G: {bound:.3f}",
            transform=ax.transAxes, ha="center", fontsize=9)
fig.suptitle("Selected local Dock REST results: improvement and regression", fontsize=14)
fig.text(.5, .012, "Deliberately selected examples, not a global score. Separate axes; G is not an error bar or confidence interval.",
         ha="center", fontsize=9)
fig.tight_layout(rect=(0, .04, 1, .95))
save(fig, "local-median-errors")

curves = read("representative-normal-curves.csv")
fig, axs = plt.subplots(2, 2, figsize=(10.4, 7.2))
roles = [("native_rest", "Native REST", BLACK, "-", 2.2),
         ("native_repeat", "Native repeat", GREY, "--", 1.8),
         ("baseline", "D31 baseline", ORANGE, "-", 1.4),
         ("D46.5", "D46.5 candidate", BLUE, "-", 1.4)]
for ax, (scene, probe, band, title) in zip(axs.flat, cases):
    for role, label, color, style, width in roles:
        rows = [r for r in curves if r["scene"] == scene and r["probe"] == probe and r["role"] == role]
        assert len(rows) == 129, (scene, probe, role, len(rows))
        ax.plot([float(r["inset_pt"]) for r in rows], [float(r["mean_linear_Y"]) for r in rows],
                label=label, color=color, ls=style, lw=width)
    low, high = map(float, band.split("-"))
    ax.axvspan(low, high, color=BLUE, alpha=.07)
    ax.set_title(title+" · full probe")
    ax.set_xlabel("Fixed nominal inward distance (pt)")
    ax.set_ylabel("Linear sRGB relative Y")
    ax.set_xlim(-4, 28)
    ax.set_ylim(0, 1)
    ax.grid(alpha=.25)
axs[0, 0].legend(fontsize=8)
fig.suptitle("Saved native / Android luminance curves, without output alignment", fontsize=14)
fig.text(.5, .012, "Shaded depth matches the selected median cell. Repeat overlaps native in these measurements; luminance is not ΔE00 or topology.",
         ha="center", fontsize=9)
fig.tight_layout(rect=(0, .04, 1, .95))
save(fig, "representative-Y-curves")
outputs = [{"file": str(p.relative_to(ROOT.parent.parent)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "bytes": p.stat().st_size} for p in sorted(OUT.iterdir()) if p.suffix in (".png", ".svg")]
(ROOT/"figure-manifest.json").write_text(json.dumps({"renderer": "render_figures.py",
    "matplotlib": matplotlib.__version__, "scope": "charts from committed completed outputs, not a fresh analysis",
    "outputs": outputs}, indent=2)+"\n")
print(json.dumps({"figures": len(outputs), "outputs": outputs}, indent=2))
