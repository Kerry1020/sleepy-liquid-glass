#!/usr/bin/env python3
"""Fixed static texture statistics; no captured-output loading in this revision."""
import argparse
import hashlib
import io
import json
import math
import platform
from pathlib import Path

import numpy as np
import PIL
from PIL import Image, ImageCms, features

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
EPS = 1e-24
CHANNELS = ("R", "G", "B", "Yprime", "Ylinear")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def protocol():
    return json.loads((HERE / "protocol.json").read_text())


def capsule(x, y, rect, inset=0.0):
    l, t, r, b = map(float, rect)
    l, t, r, b = l + inset, t + inset, r - inset, b - inset
    radius = (b - t) / 2.0
    if radius <= 0 or r - l < 2 * radius:
        raise ValueError("Invalid horizontal capsule")
    cx = np.clip(x, l + radius, r - radius)
    cy = (t + b) / 2.0
    return (x - cx) ** 2 + (y - cy) ** 2 < radius ** 2


def rect_mask(x, y, rect, padding=0.0):
    l, t, r, b = rect
    return ((x >= l - padding) & (x < r + padding) &
            (y >= t - padding) & (y < b + padding))


def supports(p):
    """Masks are fixed geometry in world pixel-center coordinates, never image-led."""
    result = []
    for roi in p["rois"]:
        l, t, r, b = roi["bounds_ltrb_px"]
        x = np.arange(l, r, dtype=np.float64)[None, :] + .5
        y = np.arange(t, b, dtype=np.float64)[:, None] + .5
        shape = np.ones((b - t, r - l), dtype=bool)
        kind = roi["mask_kind"]
        if kind == "rectangle":
            mask = shape
        elif kind == "base_interior":
            mask = capsule(x, y, p["dock_ltrb_px"], p["interior_inset_px"])
            mask &= ~capsule(x, y, p["lens_ltrb_px"], -p["lens_exclusion_outset_px"])
        elif kind == "lens_interior":
            mask = capsule(x, y, p["lens_ltrb_px"], p["interior_inset_px"])
        elif kind == "base_edge":
            mask = capsule(x, y, p["dock_ltrb_px"])
            mask &= ~capsule(x, y, p["dock_ltrb_px"], p["interior_inset_px"])
            mask &= ~capsule(x, y, p["lens_ltrb_px"], -p["lens_exclusion_outset_px"])
        elif kind == "dock_context":
            mask = capsule(x, y, p["dock_ltrb_px"])
        else:
            raise ValueError("Unknown mask kind")
        if roi["exclude_context"]:
            for rect in p["foreground_rects_ltrb_px"]:
                mask &= ~rect_mask(x, y, rect, p["foreground_padding_px"])
            mask &= ~rect_mask(x, y, p["sparse_scroll_context_ltrb_px"], p["context_padding_px"])
        if not np.any(mask):
            raise ValueError("Empty predeclared support: " + roi["id"])
        result.append((roi, mask))
    return result


def fields(rgb):
    """RGB/Yprime in code units; Ylinear in normalized linearized-sRGB units."""
    rgb = np.asarray(rgb, dtype=np.float64)
    if rgb.ndim != 3 or rgb.shape[2] != 3 or not np.all(np.isfinite(rgb)):
        raise ValueError("Expected finite HxWx3 array")
    u = rgb / 255.0
    linear = np.where(u <= .04045, u / 12.92, ((u + .055) / 1.055) ** 2.4)
    weights = np.array([.2126, .7152, .0722])
    return {"R": rgb[:, :, 0], "G": rgb[:, :, 1], "B": rgb[:, :, 2],
            "Yprime": np.sum(rgb * weights, axis=2),
            "Ylinear": np.sum(linear * weights, axis=2)}


def spatial(source, observed, mask):
    s, o = source[mask], observed[mask]
    if not (np.all(np.isfinite(s)) and np.all(np.isfinite(o))):
        raise ValueError("Nonfinite spatial input")
    sm, om = float(np.mean(s)), float(np.mean(o))
    ds, do = s - sm, o - om
    vs, vo = float(np.mean(ds * ds)), float(np.mean(do * do))
    cov = float(np.mean(ds * do))
    denominator = math.sqrt(vs * vo)
    return {"n_pixels": int(s.size), "source_mean": sm, "observed_mean": om,
            "mean_difference": om - sm, "source_variance": vs,
            "observed_variance": vo, "signed_covariance": cov,
            "signed_zero_lag_correlation": cov / denominator if denominator > EPS else None,
            "correlation_denominator": denominator,
            "texture_rms_ratio": math.sqrt(vo / vs) if vs > EPS else None,
            "raw_difference_rms": float(np.sqrt(np.mean((o - s) ** 2))),
            "undefined_reason": "numerically_zero_source_or_observed_variance" if denominator <= EPS else None}


def fft_frame(field, mask):
    h, w = mask.shape
    taper = np.hanning(h)[:, None] * np.hanning(w)[None, :] * mask
    sw, sw2 = float(np.sum(taper)), float(np.sum(taper * taper))
    if sw <= EPS or sw2 <= EPS:
        raise ValueError("Insufficient fixed Hann/mask support")
    mu = float(np.sum(taper * field) / sw)
    windowed = taper * (field - mu)
    spectrum = np.fft.fft2(windowed)
    return spectrum, {"weighted_mean": mu, "sum_window": sw, "sum_window_squared": sw2,
                      "window_support_effective_count": sw2 * sw2 / float(np.sum(taper ** 4)),
                      "parseval_spatial_energy": float(np.sum(windowed * windowed) / sw2)}


def spectral(source, observed, mask, bands):
    fs, ds = fft_frame(source, mask)
    fo, do = fft_frame(observed, mask)
    h, w = mask.shape
    radial = np.sqrt(np.fft.fftfreq(h)[:, None] ** 2 + np.fft.fftfreq(w)[None, :] ** 2)
    normalization = h * w * ds["sum_window_squared"]
    ps, po = np.abs(fs) ** 2, np.abs(fo) ** 2
    cross = np.real(np.conj(fs) * fo)
    rows = []
    covered = np.zeros(mask.shape, dtype=bool)
    for band in bands:
        lo, hi = band["cycles_per_px"]
        support = (radial >= lo) & (radial < hi)
        covered |= support
        es, eo = float(np.sum(ps[support]) / normalization), float(np.sum(po[support]) / normalization)
        ec = float(np.sum(cross[support]) / normalization)
        denominator = math.sqrt(es * eo)
        rows.append({"band": band["id"], "cycles_per_px": [lo, hi],
                     "fourier_bin_count": int(np.count_nonzero(support)),
                     "source_energy": es, "observed_energy": eo,
                     "signed_cross_energy": ec,
                     "signed_spectral_correlation": ec / denominator if denominator > EPS else None,
                     "correlation_denominator": denominator,
                     "texture_power_ratio": eo / es if es > EPS else None,
                     "texture_rms_ratio": math.sqrt(eo / es) if es > EPS else None,
                     "undefined_reason": "numerically_zero_source_or_observed_band_energy" if denominator <= EPS else None})
    return {"source_window": ds, "observed_window": do, "bands": rows,
            "source_total_energy": float(np.sum(ps) / normalization),
            "observed_total_energy": float(np.sum(po) / normalization),
            "source_unbinned_energy": float(np.sum(ps[~covered]) / normalization),
            "observed_unbinned_energy": float(np.sum(po[~covered]) / normalization)}


def pair_rows(source_rgb, observed_rgb, p):
    expected = (p["world_px"][1], p["world_px"][0], 3)
    if source_rgb.shape != expected or observed_rgb.shape != expected:
        raise ValueError("Exact registered world dimensions required; no resize/crop fitting")
    sf, of = fields(source_rgb), fields(observed_rgb)
    rows = []
    for roi, mask in supports(p):
        l, t, r, b = roi["bounds_ltrb_px"]
        for channel in CHANNELS:
            s, o = sf[channel][t:b, l:r], of[channel][t:b, l:r]
            rows.append({"roi": roi["id"], "channel": channel,
                         "context_status": roi["context_status"],
                         "spatial": spatial(s, o, mask),
                         "spectral": spectral(s, o, mask, p["frequency_bands"])})
    return rows


def self_test(p):
    """Constructed arrays only. No path to a source or captured PNG is opened."""
    rng = np.random.Generator(np.random.PCG64(202611140731))
    x = rng.standard_normal((64, 96))
    mask = np.ones(x.shape, dtype=bool)
    tests = []

    def check(name, condition, details):
        if not condition:
            raise AssertionError(name + ": " + str(details))
        tests.append({"name": name, "passed": True, "details": details})

    for a in [1., .25, 2., -1.]:
        y = a * x + 17.
        sp, ft = spatial(x, y, mask), spectral(x, y, mask, p["frequency_bands"])
        target = 1. if a > 0 else -1.
        check("signed_affine_spatial_%s" % a,
              abs(sp["signed_zero_lag_correlation"] - target) < 1e-12 and abs(sp["texture_rms_ratio"] - abs(a)) < 1e-12,
              {"correlation": sp["signed_zero_lag_correlation"], "rms_ratio": sp["texture_rms_ratio"]})
        for row in ft["bands"]:
            if row["fourier_bin_count"] and row["source_energy"] > EPS:
                check("signed_affine_spectral_%s_%s" % (a, row["band"]),
                      abs(row["signed_spectral_correlation"] - target) < 1e-12 and abs(row["texture_rms_ratio"] - abs(a)) < 1e-12,
                      {"correlation": row["signed_spectral_correlation"], "rms_ratio": row["texture_rms_ratio"]})
    blank = spatial(x, np.full_like(x, 3.), mask)
    check("blank_is_undefined_not_zero_correlation", blank["signed_zero_lag_correlation"] is None,
          {"correlation": blank["signed_zero_lag_correlation"]})
    ft = spectral(x, x, mask, p["frequency_bands"])
    error = abs(ft["source_total_energy"] - ft["source_window"]["parseval_spatial_energy"])
    check("parseval_normalization", error < 1e-12, {"absolute_error": error})

    # Known per-frequency attenuation, without fitting a transfer function.
    h, w = x.shape
    radial = np.sqrt(np.fft.fftfreq(h)[:, None] ** 2 + np.fft.fftfreq(w)[None, :] ** 2)
    filtered = np.fft.ifft2(np.fft.fft2(x) * np.exp(-2 * math.pi ** 2 * 3. ** 2 * radial ** 2)).real
    bands = spectral(x, filtered, mask, p["frequency_bands"])["bands"]
    medium = next(q for q in bands if q["band"] == "medium")
    fine = next(q for q in bands if q["band"] == "fine")
    check("constructed_lowpass_reduces_fine_more_than_medium", fine["texture_rms_ratio"] < medium["texture_rms_ratio"] < 1,
          {"medium_rms_ratio": medium["texture_rms_ratio"], "fine_rms_ratio": fine["texture_rms_ratio"]})

    all_supports = supports(p)
    counts = {roi["id"]: int(np.count_nonzero(m)) for roi, m in all_supports}
    check("all_fixed_supports_nonempty", all(v > 0 for v in counts.values()), counts)
    roi, m = next((r, m) for r, m in all_supports if r["id"] == "base_interior")
    a = rng.standard_normal(m.shape)
    b = a.copy()
    b[~m] += 10000
    same = spectral(a, b, m, p["frequency_bands"])
    check("excluded_pixels_cannot_leak_into_masked_fft", all(
        q["texture_power_ratio"] is None or abs(q["texture_power_ratio"] - 1) < 1e-12 for q in same["bands"]),
        {"changed_pixels": int(np.count_nonzero(~m))})
    sample = np.array([[[0., 128., 255.]]])
    f = fields(sample)
    expected_y = 128 * .7152 + 255 * .0722
    check("explicit_code_Yprime", abs(float(f["Yprime"][0, 0]) - expected_y) < 1e-12,
          {"Yprime": float(f["Yprime"][0, 0])})
    check("linear_Y_is_not_code_Y", abs(float(f["Ylinear"][0, 0]) - expected_y / 255) > .01,
          {"Ylinear": float(f["Ylinear"][0, 0])})
    return {"schema": 1, "status": "passed", "scope": "constructed NumPy arrays only; no PNG opened",
            "test_count": len(tests), "tests": tests,
            "not_established": ["native material correspondence", "capture adapter validity", "holdout performance", "UI acceptance"]}


def source_check(p):
    """The hard-coded calibration-only allowlist cannot consume test or captures."""
    manifest_path = ROOT / "calibration" / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    inv = json.loads((HERE / "input-inventory.json").read_text())
    if sha(manifest_path) != inv["metadata_sha256"]["calibration/manifest.json"]:
        raise ValueError("Calibration manifest changed")
    if manifest["split"] != "calibration":
        raise ValueError("Calibration source split required")
    expected_ids = ["c01_rgb_noise_s0", "c02_rgb_noise_s1", "c03_rgb_noise_s2", "c04_rgb_noise_s3"]
    entries = [e for e in manifest["inputs"] if e["kind"] == "rgb_noise"]
    if [e["id"] for e in entries] != expected_ids:
        raise ValueError("Calibration source identity changed")
    sources = []
    for e in entries:
        path = ROOT / "calibration" / (e["id"] + ".png")
        if e["file"] != path.name or sha(path) != e["sha256"]:
            raise ValueError("Calibration source file changed")
        with Image.open(path) as image:
            if image.mode != "RGB" or image.size != tuple(p["world_px"]):
                raise ValueError("Source must be exact opaque RGB")
            icc = image.info.get("icc_profile")
            if not icc or hashlib.sha256(icc).hexdigest() != manifest["icc_profile_sha256"]:
                raise ValueError("Frozen embedded source profile changed")
            array = np.asarray(image).copy()
            if hashlib.sha256(array.tobytes()).hexdigest() != e["pixel_sha256"]:
                raise ValueError("Registered source pixels changed")
        identity_rows = pair_rows(array, array, p)
        sources.append({"id": e["id"], "source_sha256": e["sha256"], "seed": e["seed"],
                        "rows": identity_rows})
    return {"schema": 1, "scope": "c01–c04 calibration SOURCE PNGs only; source identity statistics are not captured performance",
            "captured_outputs_opened": 0, "test_outputs_opened": 0, "sources": sources}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--source-check", action="store_true")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise ValueError("Output directory must be new")
    p = protocol()
    report = self_test(p) if args.self_test else source_check(p)
    report["protocol_sha256"] = sha(HERE / "protocol.json")
    report["implementation_sha256"] = sha(Path(__file__))
    report["dependencies"] = {"python": platform.python_version(), "numpy": np.__version__,
                              "pillow": PIL.__version__, "littlecms2": features.version("littlecms2")}
    args.output.mkdir(parents=True)
    write_json(args.output / "report.json", report)
    print(json.dumps({"status": report.get("status", "source-only checked"),
                      "report": str((args.output / "report.json").resolve()),
                      "captured_outputs_opened": 0, "test_outputs_opened": 0}))


if __name__ == "__main__":
    main()
