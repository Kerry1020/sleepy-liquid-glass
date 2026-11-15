#!/usr/bin/env python3
"""Post-acquisition schema adapter for frozen analyze.py; never optical acceptance.

Only metadata/path compatibility is repaired; v1 mathematics and thresholds are unchanged.
This adapter was not present in the pre-acquisition freeze.

Bounded full100 Android/native G-response diagnostics; never optical acceptance.

Requires Python 3, NumPy and Pillow. No device, build or image registration.
  python3 analyze.py --self-test
  python3 analyze.py --root /absolute/path/to/slider-android-response-20261116 \
      --output /absolute/path/to/new-analysis
The collector acquires 4 rounds x 6 poses x shape/flat = 48 held endpoints.
Only the full100 pair from each round (8 endpoints) is decoded for this analysis.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import sys

import numpy as np
from PIL import Image, ImageCms


HERE = Path(__file__).resolve().parent
ROUNDS = ("control-pre", "global-G", "mask-G", "control-post")
STAGES = ("ingress01", "ingress10", "ingress50", "ingress75", "full100", "far50")
ROI = np.array([165.5, 397.5, 209.5, 441.5])
ERRORS = (1, 4, 8)
NATIVE_SHA = {
    "original-pixels.npz": "11b1e76aa2a0a7766b579bdfd8a8fc8e4bceecda1fc996a34f07d9955a78f695",
    "analysis.json": "5499910555e7aa465f853c2361f55fe4a2300703416a98b82d00de98c393d9ba",
}
NATIVE_MANIFEST_SHA = "d1f2d2be9a2cb984cf9ffb8c8a85ee8f9e11ce892be998c9c95666e5644554f6"
MAIN_SHA = {
    "control-pre": "9757bdb14092023996f2bd46d30b682799aac1fe06c221b7cad256c991e46724",
    "global-G": "49746c72910f7a1218b0260b0126058a5e17cf6eadd29e068afac91e0f4c75d5",
    "mask-G": "bff58755a5a2e31a537d97a4adc8ad72e71a1dc7c2c724bba04385ee448257ad",
    "control-post": "9757bdb14092023996f2bd46d30b682799aac1fe06c221b7cad256c991e46724",
}
FLAT_SHA = "6e4291536355bff3dae7dee3957eec96bf4f3efc7566dd4257721a635ad8340b"
LIMITS = {"bounds": .1, "matrix": .001, "opacity": .01, "source": 1e-8, "drift": 2}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    def unique(pairs):
        d = {}
        for k, v in pairs:
            require(k not in d, f"Duplicate JSON key {k!r}: {path}")
            d[k] = v
        return d
    return json.loads(Path(path).read_text(), object_pairs_hook=unique,
                      parse_constant=lambda v: (_ for _ in ()).throw(ValueError(f"Nonfinite JSON {v}")))


def numeric(value, shape=None):
    a = np.asarray(value, dtype=float)
    require(np.isfinite(a).all(), "Nonfinite observed numeric field")
    require(shape is None or a.shape == shape, f"Observed shape {a.shape} != {shape}")
    return a


def resolve(path, parent):
    p = Path(path)
    return (p if p.is_absolute() else Path(parent) / p).resolve()


def artifact(path, expected=None, size=None):
    p = Path(path).resolve()
    require(p.is_file(), f"Missing artifact: {p}")
    h = sha(p)
    require(expected is None or h == expected, f"Artifact SHA mismatch: {p}")
    require(size is None or p.stat().st_size == size, f"Artifact size mismatch: {p}")
    return {"path": str(p), "sha256": h, "bytes": p.stat().st_size}


def bound(reference, parent):
    require(isinstance(reference, dict) and reference.get("sha256"), "Unbound evidence reference")
    return artifact(resolve(reference["path"], parent), reference["sha256"])


def stats(values):
    a = np.asarray(values, float).ravel()
    v = a[np.isfinite(a)]
    out = {"samples": int(v.size), "undefined_samples": int(a.size - v.size)}
    if not v.size:
        return out
    out.update(min=float(v.min()), max=float(v.max()), mean=float(v.mean()),
               signed_sum=float(v.sum()), max_abs=float(np.abs(v).max()),
               rmse=float(np.sqrt(np.mean(v * v))), mae=float(np.abs(v).mean()),
               signed_quantiles={str(q): float(np.quantile(v, q)) for q in (0, .01, .1, .5, .9, .99, 1)},
               absolute_quantiles={str(q): float(np.quantile(np.abs(v), q)) for q in (.5, .9, .99, 1)},
               threshold_counts={str(t): {"positive": int((v > t).sum()),
                                          "negative": int((v < -t).sum()),
                                          "absolute": int((np.abs(v) > t).sum())}
                                 for t in (1, 2, 4, 8, 16, 24)})
    return out


def channels(a, domain=None):
    return {name: stats(a[..., i] if domain is None else a[..., i][domain])
            for i, name in enumerate("RGB")}


def alpha_interval(u, m, endpoint_error):
    """Closed per-pixel compatibility with one shared baseline; keeps weak failures."""
    u, m = np.broadcast_arrays(numeric(u), numeric(m))
    e = float(endpoint_error)
    require(math.isfinite(e) and e >= 0, "Invalid endpoint allowance")
    lo, hi = np.zeros(u.shape), np.ones(u.shape)
    nonzero = u != 0
    a = np.divide(m - 2 * e, u, out=np.zeros(u.shape), where=nonzero)
    b = np.divide(m + 2 * e, u, out=np.ones(u.shape), where=nonzero)
    lo[nonzero] = np.maximum(0, np.minimum(a, b)[nonzero])
    hi[nonzero] = np.minimum(1, np.maximum(a, b)[nonzero])
    contradiction = ~nonzero & (np.abs(m) > 2 * e)
    lo[contradiction], hi[contradiction] = 1, 0
    return lo, hi, lo <= hi


def compare_alpha(un, mn, ua, ma, e):
    nl, nh, nok = alpha_interval(un, mn, e)
    al, ah, aok = alpha_interval(ua, ma, e)
    lo, hi = np.maximum(nl, al), np.minimum(nh, ah)
    compatible = nok & aok & (lo <= hi)
    nw, aw = np.abs(un) <= 2 * e, np.abs(ua) <= 2 * e
    nr = np.divide(mn, un, out=np.full(np.shape(un), np.nan), where=~nw)
    ar = np.divide(ma, ua, out=np.full(np.shape(ua), np.nan), where=~aw)
    return {"native_lo": nl, "native_hi": nh, "native_compatible": nok,
            "android_lo": al, "android_hi": ah, "android_compatible": aok,
            "common_lo": lo, "common_hi": hi, "common_compatible": compatible,
            "native_weak": nw, "android_weak": aw, "both_strong": ~nw & ~aw,
            "native_ratio_strong_only": nr, "android_ratio_strong_only": ar,
            "ratio_difference_strong_only": ar - nr,
            "common_gap": np.maximum(lo - hi, 0),
            "common_width_compatible_only": np.where(compatible, hi - lo, np.nan)}


def screen_indices(x, y, affine):
    b = numeric(affine, (2, 3))
    return b[0, 0] * x + b[0, 1] * y + b[0, 2] - .5, b[1, 0] * x + b[1, 1] * y + b[1, 2] - .5


def sample_once(field, x, y, affine):
    u, v = screen_indices(x, y, affine)
    require(u.min() >= 0 and v.min() >= 0 and u.max() < field.shape[1] - 1
            and v.max() < field.shape[0] - 1, "Fixed ROI lacks bilinear source-pixel support")
    i, j = np.floor(u).astype(int), np.floor(v).astype(int)
    du, dv = u - i, v - j
    if field.ndim == 3:
        du, dv = du[..., None], dv[..., None]
    return ((1 - du) * (1 - dv) * field[j, i] + du * (1 - dv) * field[j, i + 1]
            + (1 - du) * dv * field[j + 1, i] + du * dv * field[j + 1, i + 1])


def capsule_inset(x, y, bounds):
    left, top, width, height = numeric(bounds, (4,))
    r = height / 2
    return r - np.hypot(np.maximum(np.abs(x - left - width / 2) - (width / 2 - r), 0), y - top - r)


def fixed_domains(x, y, inset, android_bounds):
    primary = (y < 422) & (inset >= 1)
    return {"complete_fixed_ROI": np.ones(x.shape, bool), "above_rail": y < 422,
            "primary_native_capsule_inset1": primary,
            "rim_native_capsule_inset0_1": (y < 422) & (inset >= 0) & (inset < 1),
            "exterior_native_capsule": (y < 422) & (inset < 0),
            "rail_confounded_y422_438": (y >= 422) & (y < 438), "below_rail_y438_plus": y >= 438,
            "secondary_independent_capsule_interior_intersection": primary & (capsule_inset(x, y, android_bounds) >= 1)}


def colour_metadata(info):
    icc = info.get("icc_profile")
    description = None
    if icc:
        try:
            description = ImageCms.getProfileDescription(ImageCms.ImageCmsProfile(io.BytesIO(icc))).strip()
        except Exception:
            description = "unparseable ICC; preserved hash only"
    srgb = "srgb" in info or bool(description and "srgb" in description.lower().replace(" ", ""))
    return {"status": "DECLARED_SRGB_OUTPUT_METADATA" if srgb else "COLOR_SPACE_UNVERIFIED",
            "png_sRGB_rendering_intent": info.get("srgb"), "gamma": info.get("gamma"),
            "icc_sha256": hashlib.sha256(icc).hexdigest() if icc else None,
            "icc_description": description,
            "scope": "Original PNG declaration only; no profile conversion or proof of the internal colour pipeline"}


def png(path, expected):
    record = artifact(path, expected)
    with Path(path).open("rb") as stream:
        header = stream.read(33)
    require(header[:8] == b"\x89PNG\r\n\x1a\n" and header[12:16] == b"IHDR", "Not an original PNG")
    width, height, depth, kind = struct.unpack(">IIBB", header[16:26])
    require(depth == 8 and kind in (2, 6), "Original screenshot must be RGB8/RGBA8")
    with Image.open(path) as im:
        require(im.mode in ("RGB", "RGBA"), "PNG decoder mode differs from RGB/RGBA")
        a = np.array(im)
        colour = colour_metadata(im.info)
    require(a.dtype == np.uint8 and a.shape[:2] == (height, width), "Unexpected decoded PNG pixels")
    require(a.shape[-1] == 3 or np.all(a[..., 3] == 255), "Nonopaque screenshot")
    return a[..., :3], {**record, "dimensions_px": [width, height], "colour": colour}


def node_affine(node):
    basis = numeric(node["local_to_screen_unit_basis_px"], (3, 2))
    axes = (basis[1:] - basis[0]).T
    size = numeric(node["layout_size_px"], (2,))
    require((size > 0).all() and abs(np.linalg.det(axes)) > 1e-12, "Invalid attached node basis/size")
    corners = node["local_to_screen_corners_px"]
    require(len(corners) == 4, "Missing actual transformed four corners")
    expected_local = {(0., 0.), (float(size[0]), 0.), (0., float(size[1])), tuple(map(float, size))}
    require({tuple(numeric(c["local_px"], (2,))) for c in corners} == expected_local, "Unexpected local corner coordinates")
    points = []
    for c in corners:
        local, screen = numeric(c["local_px"], (2,)), numeric(c["screen_px"], (2,))
        require(np.max(np.abs(basis[0] + axes @ local - screen)) <= .05,
                "Actual four corners disagree with recorded affine basis")
        points.append(screen)
    return basis[0], axes, np.asarray(points), size


def xywh(points):
    return np.r_[points.min(axis=0), np.ptp(points, axis=0)]


def geometry(row, image_shape):
    g = row["geometry"]
    source = g["background_world"]["source"]
    origin, axes, source_corners, size = node_affine(source)
    density = float(source["density"])
    require(math.isfinite(density) and density > 0, "Missing actual source density")
    # Logical dp coordinates retain actual layout rounding. Producer-pixel mapping
    # below is separate; width/375 is not silently substituted for output density.
    linear = axes * density
    b = np.column_stack((linear, origin))
    inv = np.linalg.inv(linear)
    out = {"output_affine": b, "source_origin": origin / density,
           "source_sampling_matrix": np.diag(size / [375, 667]),
           "source_layout_size_px": size, "source_corners_screen_px": source_corners,
           "density": density, "unknowns": []}
    parsed = {}
    for role, key in (("holder", "outer_holder"), ("owner", "isotropic_thumb_owner"), ("carrier", "affine_visual_carrier")):
        node = g[key]
        no, na, nc, ns = node_affine(node)
        require(abs(float(node["density"]) - density) <= 1e-8, "Attached node density differs")
        world = (nc - origin) @ inv.T
        out[role + "_bounds"] = xywh(world)
        parent_origin = origin if role != "carrier" else numeric(g["isotropic_thumb_owner"]["screen_origin_px"], (2,))
        out[role + "_matrix"] = np.r_[na[:, 0], na[:, 1], (no - parent_origin) / density]
        op = node.get("effective_opacity")
        if op is None:
            out[role + "_opacity"] = None
            if role != "holder": out["unknowns"].append(role + " effective opacity is unobserved")
        else:
            op = float(op)
            require(math.isfinite(op) and 0 <= op <= 1, "Invalid observed effective opacity")
            out[role + "_opacity"] = op
        parsed[role] = nc
    claimed = numeric(g["visual_carrier_world_rect_dp"], (4,))
    require(np.max(np.abs(out["carrier_bounds"] - np.r_[claimed[:2], claimed[2:] - claimed[:2]])) <= .1,
            "Actual transformed carrier and recorded world rectangle differ")
    height, width = image_shape[:2]
    require((source_corners.min(axis=0) >= 0).all() and (source_corners.max(axis=0) <= [width, height]).all(), "Producer is clipped by the original screenshot")
    required = np.vstack((parsed["holder"], parsed["carrier"] - 6 * density, parsed["carrier"] + 6 * density))
    domain = numeric(row["display_readiness"]["compared_screen_rect_px"], (4,))
    require((required.min(axis=0) >= np.maximum(domain[:2], [0, 0])).all()
            and (required.max(axis=0) <= np.minimum(domain[2:], [width, height])).all(),
            "Holder/carrier+6pt guard is clipped or outside the observed app comparison surface")
    out["required_screen_bounds"] = np.r_[required.min(axis=0), required.max(axis=0)]
    return out


def stable_geometry(gs):
    checks, errors, unknowns = {}, [], []
    for role in ("owner", "carrier"):
        bounds = np.stack([g[role + "_bounds"] for g in gs])
        for name, values, limit in (("bounds", bounds, LIMITS["bounds"]),
                                    ("centre", bounds[:, :2] + bounds[:, 2:] / 2, LIMITS["bounds"]),
                                    ("matrix", np.stack([g[role + "_matrix"] for g in gs]), LIMITS["matrix"])):
            v = float(np.ptp(values, axis=0).max())
            checks[role + "_" + name + "_range"] = v
            if v > limit + 1e-10: errors.append(f"{role} {name} range {v} exceeds {limit}")
        ops = [g[role + "_opacity"] for g in gs]
        if any(v is None for v in ops):
            checks[role + "_opacity_range"] = None
            unknowns.append(role + " effective opacity is unobserved")
        else:
            v = float(np.ptp(ops)); checks[role + "_opacity_range"] = v
            if v > LIMITS["opacity"] + 1e-10: errors.append(role + " opacity drift")
    for name in ("source_origin", "source_sampling_matrix"):
        v = float(np.ptp(np.stack([g[name] for g in gs]), axis=0).max()); checks[name + "_range"] = v
        if v > LIMITS["source"] + 1e-10: errors.append(name + " drift")
    same = all(np.array_equal(g["output_affine"], gs[0]["output_affine"]) for g in gs)
    checks["identical_actual_output_affine"] = same
    if not same: errors.append("Output mapping changes between original pixel lattices")
    return {"status": "REJECTED" if errors else "MAPPING_UNKNOWN_PIXEL_DIAGNOSTICS_ONLY" if unknowns else "WITHIN_DECLARED_GEOMETRY_GATES",
            "checks": checks, "errors": errors, "unknowns": unknowns}


def native_reference(study):
    directory = study / "evidence/reference-analysis"
    identities = [artifact(directory / name, h) for name, h in NATIVE_SHA.items()]
    report = read(directory / "analysis.json")
    with np.load(directory / "original-pixels.npz", allow_pickle=False) as f:
        keys = ("x", "y", "inset_capsule_assumption", "raw_global_output_input", "raw_mask_output_input", "original_ROIs_round_shape_flat_outputRGB")
        arrays = {k: f[k].copy() for k in keys}
    x, y = arrays["x"], arrays["y"]
    xx, yy = np.meshgrid((np.arange(331, 419) + .5) / 2, (np.arange(795, 883) + .5) / 2)
    require(x.shape == (88, 88) and np.array_equal(x, xx) and np.array_equal(y, yy), "Frozen native grid differs")
    endpoints = arrays["original_ROIs_round_shape_flat_outputRGB"]
    require(endpoints.shape == (8, 2, 88, 88, 3) and endpoints.dtype == np.uint8, "Native raw endpoint shape/type differs")
    un, mn = arrays["raw_global_output_input"][..., 1, 1], arrays["raw_mask_output_input"][..., 1, 1]
    require(np.array_equal(un, endpoints[2, 0, ..., 1].astype(np.int16) - endpoints[0, 0, ..., 1]), "Native U_GG/raw endpoints disagree")
    require(np.array_equal(mn, endpoints[5, 0, ..., 1].astype(np.int16) - endpoints[0, 0, ..., 1]), "Native M_GG/raw endpoints disagree")
    mp = study / "evidence/manifest.json"; identities.append(artifact(mp, NATIVE_MANIFEST_SHA)); manifest = read(mp)
    relative = "rounds/control-pre/native-r1/endpoint-verification-strict.json"
    strict_path = study / "evidence" / relative
    identities.append(artifact(strict_path, manifest["files"][relative]["sha256"]))
    strict = read(strict_path)
    require(strict["status"] == "passed" and strict["errors"] == [], "Native frozen strict metadata failed")
    obs = [o for o in strict["observations"] if o["externalInput"]["id"] != "st00_flat128"]
    require(len(obs) == 1, "Native pre shape observation not unique")
    o = obs[0]; samples = o["presentedPoseSamples"]
    native_geom = {"carrier_bounds": numeric(o["actualCarrierBoundsPt"], (4,)),
                   "carrier_matrix": numeric([[s["carrier"][k] for k in ("m11", "m12", "m21", "m22", "m41", "m42")] for s in samples]),
                   "carrier_opacity": numeric([s["carrier"]["effectiveOpacity"] for s in samples])}
    return {"arrays": arrays, "report": report, "identities": identities, "geometry": native_geom}


def pointer_gate(row, result):
    require(row["phase"] == "held" and row["pointer_down"] is True and not row["finish_events"], "Endpoint was not held")
    dispatched = row["dispatched_pointer_events"]
    require([d["type"] for d in dispatched] == ["Press", "Move", "Move"], "Expected actual Press/Move/Move delivery")
    require(all(len(d["changes"]) == 1 and d["changes"][0]["pressed"] is True
                and d["changes"][0]["consumed_by_production_at_final_pass"] is True for d in dispatched), "Production did not consume the held pointer")
    injected = [i for i in result["input_events"] if i["scene"] == row["scene"]]
    require([i["action"] for i in injected] == ["DOWN", "MOVE_ESTABLISH_SLOP", "MOVE_TARGET", "CANCEL"], "Injection sequence differs")
    require(dispatched[-1]["wall_uptime_ms"] < row["capture_begin_wall_uptime_ms"] < row["capture_end_wall_uptime_ms"] < injected[-1]["wall_uptime_ms"], "Screenshot outside actual held bracket")
    require(row["compose_ms"] - dispatched[-1]["compose_ms"] >= 1600, "Declared static Compose settling interval not reached")
    attempts = row["display_readiness"]["attempts"]
    require(attempts and attempts[-1]["matched_fraction_rgb_tolerance3"] >= .995, "Original RGB3/99.5% readiness failed")


def load_round(root, study, name):
    directory = root / "evidence/rounds" / name / "android-r2"
    ip = directory / "index.json"; index_identity = artifact(ip); index = read(ip)
    require(index["schema"] == 1 and index["platform"] == "android" and index["status"] == "original_hashes_pointer_and_pair_checks_passed", "Android index did not pass frozen parser")
    identities = [index_identity]
    for key in ("adapter", "source_result", "host_receipt"):
        identities.append(bound(index[key], ip.parent))
    rp = resolve(index["source_result"]["path"], ip.parent); result = read(rp)
    hp = resolve(index["host_receipt"]["path"], ip.parent); receipt = read(hp)
    require(result["schema"] == 1 and result["status"] == "passed" and result["mode"] == "fixed-shape-coverage", "Wrong/failed result mode")
    require(receipt["exit_code"] == 0 and receipt["test_passed"] is True, "Failed instrumentation receipt")
    sp = root / "derived" / name / "shape-spec.json"; spec_identity = artifact(sp); identities.append(spec_identity); spec = read(sp)
    require(resolve(index["shape_spec"], ip.parent) == sp.resolve(), "Index references another derived specification")
    require(result["shape_plan"] == spec and result["shape_plan_sha256"] == spec_identity["sha256"] == receipt["input_sha256"]["shape-spec.json"], "Actual result/spec/input hash mismatch")
    require(receipt.get("spec_sha256", spec_identity["sha256"]) == spec_identity["sha256"], "Host spec identity mismatch")
    original_directory = study / "inputs/rounds" / name
    original_spec = read(original_directory / "shape-spec.json")
    for key in ("world", "rasterization", "inputs", "first_input_id", "flat_input_id"):
        require(spec[key] == original_spec[key], f"Derived spec changed original source field {key}")
    manifest_path = original_directory / "inputs/manifest.json"
    manifest = read(manifest_path); mh = sha(manifest_path)
    identities.append(artifact(manifest_path, receipt["input_sha256"]["inputs/manifest.json"]))
    if "source_manifest" in index:
        identities.append(bound(index["source_manifest"], ip.parent))
        require(resolve(index["source_manifest"]["path"], ip.parent) == manifest_path.resolve() and index["source_manifest"]["sha256"] == mh, "Actual manifest identity mismatch")
    require(result["external_input_manifest"] == manifest and result["inputs"] == manifest["inputs"], "Actual drawn source manifest differs")
    main = next(i for i in manifest["inputs"] if i["id"] == spec["first_input_id"])
    flat = next(i for i in manifest["inputs"] if i["id"] == spec["flat_input_id"])
    require(main["sha256"] == MAIN_SHA[name] and flat["sha256"] == FLAT_SHA, "Not the frozen S condition/ordinary flat")
    for entry in manifest["inputs"]:
        source = manifest_path.parent / entry["file"]
        require(Path(entry["file"]).name == entry["file"], "Noncanonical source filename")
        identities.append(artifact(source, entry["sha256"], entry["bytes"]))
        require(receipt["input_sha256"]["inputs/" + entry["file"]] == entry["sha256"], "Delivered source hash differs")
    files = receipt["files"]; paths = [f["file"] for f in files]
    require(len(files) == len(set(paths)) == 49, "Expected49 unique original result/image receipts")
    file_hashes = {}
    for f in files:
        p = resolve(f["file"], hp.parent)
        require(p.is_relative_to(hp.parent.resolve()) and f["host_device_match"] is True, "Unbound/escaping host-device artifact")
        identities.append(artifact(p, f["sha256"])); file_hashes[p] = f["sha256"]
    require(file_hashes.get(rp) == index["source_result"]["sha256"], "Result not bound to device receipt")
    require(result["shape_id"] == index.get("shape_id", spec["first_input_id"]) == spec["first_input_id"] and result["flat_input_id"] == spec["flat_input_id"], "Shape/flat roles differ")
    expected = {(s, r) for s in STAGES for r in ("shape", "flat")}
    actual = collections.Counter((c["stage_id"], c["source_role"]) for c in result["captures"])
    require(set(actual) == expected and all(v == 1 for v in actual.values()), "Expected exact six-pose shape/flat result")
    require(len(index["captures"]) == 6 and {c["stage_id"] for c in index["captures"]} == set(STAGES), "Frozen index lacks exact six poses")
    require(all(c["shape_id"] == c["input_id"] == spec["first_input_id"] for c in index["captures"]), "Index capture shape identities differ")
    require({s["id"] for s in spec["stages"]} == set(STAGES), "Derived acquisition pose set differs")
    for row in result["captures"]:
        require(row["shape_id"] == spec["first_input_id"] and row["input_id"] == (spec["first_input_id"] if row["source_role"] == "shape" else spec["flat_input_id"]), "Actual input role differs")
        pointer_gate(row, result)
    full = next(c for c in index["captures"] if c["stage_id"] == "full100")
    require(resolve(full["android_evidence_json"], ip.parent) == rp, "Index geometry references another result")
    require(full["shape_id"] == full["input_id"] == spec["first_input_id"], "Full100 index shape differs")
    stage = next(s for s in result["coverage_stages"] if s["stage_id"] == "full100")
    require(stage["pair_position_validation"] == "passed" and stage["pair_carrier_center_delta_dp"] == [0, 0] and stage["pair_value_delta"] == 0, "Shape/flat full100 pair moved")
    images, geometries, image_records = {}, {}, {}
    for role in ("shape", "flat"):
        row = next(c for c in result["captures"] if c["stage_id"] == "full100" and c["source_role"] == role)
        pk, hk = ("png", "sha256") if role == "shape" else ("flat_png", "flat_sha256")
        p = resolve(full[pk], ip.parent)
        require(p == resolve(row["screen_png"], rp.parent) and file_hashes.get(p) == full[hk], "Full100 PNG is not the original bound screen capture")
        images[role], image_records[role] = png(p, full[hk])
        require(row["theme"] == "light", "Non-light full100 capture")
        observations = [o for o in result["geometry_observations"] if o.get("scene") == row["scene"] and o.get("phase") == "held"]
        require(len(observations) == 1 and observations[0].get("geometry", observations[0].get("world")) == row["geometry"], "Held geometry observation differs from capture geometry")
        geometries[role] = geometry(row, images[role].shape)
        indexed = full if role == "shape" else full["flat_geometry"]
        require(np.max(np.abs(geometries[role]["carrier_bounds"] - numeric(indexed["actual_carrier_bounds_world_xywh"], (4,)))) <= .1, "Index/actual carrier mismatch")
        b = geometries[role]["output_affine"]
        require(np.max(np.abs(numeric(indexed["world_origin_window_px"], (2,)) - b[:, 2])) <= 1e-5, "Index/output source origin mismatch")
        require(abs(float(indexed["pixels_per_world_unit"]) - geometries[role]["density"]) <= 1e-7, "Index/output density mismatch")
    require(result["selected_themes"] == ["light"] and result["font_scale"] == 1, "Operating theme/font scale differs")
    require(int(result["sdk"]) >= 33 and str(result["production_shader_compile_and_bind"]).startswith("passed"), "RuntimeShader support/compile/bind not verified")
    package_identity = [{"package": p.get("application_id", p.get("package")), "sha256": p.get("sha256")}
                        for p in receipt.get("packages", [])]
    operating = {k: result.get(k) for k in ("sdk", "model", "fingerprint", "density", "font_scale", "selected_themes", "theme_preset", "production_shader_compile_and_bind")}
    for field in ("sources", "build", "display_before", "display_after"):
        operating[field] = receipt.get(field)
    operating["packages"] = package_identity
    return {"name": name, "images": images, "geometries": geometries, "image_records": image_records,
            "identities": identities, "operating": operating,
            "scope": {"acquired_held_endpoints": 12, "analyzed_held_endpoints": 2, "analyzed_stage": "full100", "other_stages_pixels_decoded": False}}


def freeze_status(root):
    path = root / "FREEZE.json"
    if not path.exists():
        return {"status": "IDENTITY_FREEZE_UNVERIFIED", "unknowns": ["No external pre-acquisition freeze provided"]}
    value = read(path)
    files = value.get("files")
    if not isinstance(files, dict) or not files:
        return {"status": "IDENTITY_FREEZE_UNVERIFIED", "identity": artifact(path), "unknowns": ["Unsupported/missing files mapping in acquisition freeze"]}
    checked, errors = [], []
    for rel, h in files.items():
        try:
            p = resolve(rel, root)
            require(not Path(rel).is_absolute() and p.is_relative_to(HERE.parents[1]) and p != path.resolve(), "Noncanonical/escaping/self-referential freeze member")
            checked.append(artifact(p, h if isinstance(h, str) else h["sha256"]))
        except (ValueError, OSError, KeyError, TypeError) as e:
            errors.append(str(e))
    required = {"PLAN.md", "analyze.py"}
    required.update(f"derived/{name}/shape-spec.json" for name in ROUNDS)
    missing = sorted(required - set(files))
    return {"status": "REJECTED" if errors else "IDENTITY_FREEZE_UNVERIFIED" if missing else "RECORDED_FREEZE_HASHES_MATCH",
            "identity": artifact(path), "checked_files": checked, "errors": errors,
            "unknowns": ["Required analysis/spec freeze members absent: " + ", ".join(missing)] if missing else [],
            "limit": "Hash equality checks recorded identity; it does not prove trusted acquisition time"}


def cross_geometry(android, native):
    ag = android[0]["geometries"]["shape"]; ng = native["geometry"]
    ab, nb = ag["carrier_bounds"], ng["carrier_bounds"]
    delta = ab - nb; centre = ab[:2] + ab[2:] / 2 - nb[:2] - nb[2:] / 2
    matrix_delta = ag["carrier_matrix"] - ng["carrier_matrix"][0]
    opacity = ag["carrier_opacity"]
    opacity_delta = None if opacity is None else opacity - float(ng["carrier_opacity"][0])
    errors = []
    if np.max(np.abs(delta)) > .1 + 1e-10 or np.max(np.abs(centre)) > .1 + 1e-10: errors.append("Cross-system public carrier bounds/centre differ beyond0.10pt")
    if np.max(np.abs(matrix_delta)) > .001 + 1e-10: errors.append("Cross-system carrier local affine elements differ beyond0.001; hierarchy/anchor conventions are not normalized")
    if opacity_delta is not None and abs(opacity_delta) > .01 + 1e-10: errors.append("Cross-system observed carrier opacity differs beyond0.01")
    return {"status": "GEOMETRY_CONFOUNDED" if errors else "MAPPING_UNKNOWN_PIXEL_DIAGNOSTICS_ONLY" if opacity_delta is None else "WITHIN_DECLARED_CROSS_GEOMETRY_GATES",
            "native_bounds_xywh": nb, "android_bounds_xywh": ab, "bounds_delta_xywh": delta,
            "centre_delta_xy": centre, "carrier_matrix_delta": matrix_delta,
            "observed_effective_opacity_delta": opacity_delta, "errors": errors,
            "scope": "Public carriers and declared local-affine conventions, not recovered optical outline or material alpha"}


def comparison(un, mn, ua, ma, x, y, domains, arrays):
    masks = {"all_fixed_domain_pixels": np.ones(un.shape, bool),
             "frozen_native_M_positive": mn > 0, "prespecified_nonzero_M_union": (mn != 0) | (ma != 0)}
    results = {}
    for e in ERRORS:
        c = compare_alpha(un, mn, ua, ma, e)
        arrays.update({f"E{e}_" + k: v for k, v in c.items()})
        results[str(e)] = {"total_endpoint_allowance_byte": e, "shared_baseline_residual_allowance_byte": 2 * e,
                           "domain_subsets": {},
                           "all_incompatible_coordinates_world_xy": np.stack((x[~c["common_compatible"]], y[~c["common_compatible"]]), axis=-1).tolist()}
        for dn, d in domains.items():
            table = {}
            for sn, sm in masks.items():
                selected = d & sm; resolved = selected & c["both_strong"]
                table[sn] = {"pixels": int(selected.sum()), "native_weak": int((selected & c["native_weak"]).sum()),
                             "android_weak": int((selected & c["android_weak"]).sum()), "both_strong": int(resolved.sum()),
                             "native_incompatible": int((selected & ~c["native_compatible"]).sum()),
                             "android_incompatible": int((selected & ~c["android_compatible"]).sum()),
                             "common_incompatible_all_pixels": int((selected & ~c["common_compatible"]).sum()),
                             "common_incompatible_both_strong": int((resolved & ~c["common_compatible"]).sum()),
                             "weak_but_common_incompatible": int((selected & ~c["both_strong"] & ~c["common_compatible"]).sum()),
                             "ratio_difference_both_strong": stats(c["ratio_difference_strong_only"][resolved]),
                             "native_ratio_both_strong": stats(c["native_ratio_strong_only"][resolved]),
                             "android_ratio_both_strong": stats(c["android_ratio_strong_only"][resolved]),
                             "common_interval_gap": stats(c["common_gap"][selected]),
                             "common_interval_width_compatible_only": stats(c["common_width_compatible_only"][selected])}
            results[str(e)]["domain_subsets"][dn] = table
    return results


def sanitize(value):
    if isinstance(value, np.ndarray): return sanitize(value.tolist())
    if isinstance(value, np.generic): return sanitize(value.item())
    if isinstance(value, float) and not math.isfinite(value): return None
    if isinstance(value, dict): return {k: sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [sanitize(v) for v in value]
    return value


def execute(root, study):
    report = {"schema": 1, "status": "REJECTED_INPUT_GATES", "optical_acceptance": False,
              "analyzer": artifact(__file__), "plan": artifact(root / "PLAN.md"), "round_order": ROUNDS,
              "compatibility_repair": {"timing": "post-acquisition schema adapter; not pre-acquisition-frozen",
                                       "frozen_analyzer": artifact(root / "analyze.py"),
                                       "mathematics_and_thresholds": "unchanged from frozen v1"},
              "scope": {"acquired_held_endpoints": 48, "analysis_held_endpoints": 8, "analysis_pose": "full100",
                        "difference_from_original_plan": "The unchanged six-pose fixture acquires48 endpoints; only the eight planned full100 endpoints enter response arrays; other PNGs are integrity-hashed, not decoded"},
              "errors": [], "unknowns": [], "limits": [
                  "All response and interval results are encoded-byte diagnostics conditional on the stated affine/common-alpha surrogate, never optical acceptance.",
                  "E1/4/8 are endpoint-box sensitivity allowances, not measured noise bounds; the shared-baseline residual allowance is2E, not the earlier native raw T4.",
                  "One mask cannot identify displacement, blur, opacity, refraction strength, physical thickness or an internal pipeline uniquely.",
                  "Clipping/floors, transfer/gamma, adaptive gain, tint, geometry/rasterization and layered rail/background signals can invalidate ratio cancellation.",
                  "An unobserved effective opacity/output colour space stays unknown; no guessed value or colour normalization is used.",
                  "Spatially correlated and interpolated samples are not independent statistical trials; no confidence p-values are attached."]}
    arrays = {}
    try:
        frozen = freeze_status(root); report["freeze"] = frozen
        report["errors"].extend(frozen.get("errors", [])); report["unknowns"].extend(frozen.get("unknowns", []))
        native = native_reference(study); report["native_evidence"] = native["identities"]; report["native_operating_state"] = native["report"]["operating_state"]
    except (ValueError, KeyError, OSError, TypeError) as e:
        report["errors"].append("reference/freeze: " + str(e)); return report, arrays
    rows = []
    for name in ROUNDS:
        try: rows.append(load_round(root, study, name))
        except (ValueError, KeyError, OSError, TypeError, StopIteration, struct.error) as e:
            report["errors"].append(name + ": " + str(e))
    report["rounds"] = [{k: v for k, v in r.items() if k != "images"} for r in rows]
    if report["errors"] or len(rows) != 4: return report, arrays
    gs = [r["geometries"][role] for r in rows for role in ("shape", "flat")]
    geom = stable_geometry(gs); report["within_android_geometry"] = geom
    report["errors"].extend(geom["errors"]); report["unknowns"].extend(geom["unknowns"])
    shapes = {im.shape for r in rows for im in r["images"].values()}
    if len(shapes) != 1: report["errors"].append("Original screenshot dimensions differ between rounds")
    operating = [r["operating"] for r in rows]
    if any(o != operating[0] for o in operating[1:]): report["errors"].append("Recorded source/build/package/display/operating identity changes between rounds")
    for field in ("sources", "build", "packages", "display_before", "display_after"):
        if not operating[0].get(field): report["unknowns"].append("Unrecorded Android " + field + " identity")
    if operating[0]["display_before"] != operating[0]["display_after"]: report["errors"].append("Display configuration changed during a round")
    for r in rows:
        for role, p in r["image_records"].items():
            if p["colour"]["status"] == "COLOR_SPACE_UNVERIFIED": report["unknowns"].append(r["name"] + ":" + role + " output colour space unverified")
    if report["errors"]: return report, arrays
    report["cross_system_geometry"] = cross_geometry(rows, native)
    na = native["arrays"]; x, y = na["x"], na["y"]; b = gs[0]["output_affine"]
    u, v = screen_indices(x, y, b)
    crop = [int(np.floor(u.min())), int(np.floor(v.min())), int(np.floor(u.max())) + 2, int(np.floor(v.max())) + 2]
    left, top, right, bottom = crop
    height, width, _ = next(iter(shapes))
    if not (0 <= left < right <= width and 0 <= top < bottom <= height):
        report["errors"].append("Fixed ROI/once-sampling guard outside screenshot"); return report, arrays
    originals = np.stack([np.stack([r["images"][role][top:bottom, left:right] for role in ("shape", "flat")]) for r in rows])
    ub = originals[1, 0].astype(np.int16) - originals[0, 0].astype(np.int16)
    mb = originals[2, 0].astype(np.int16) - originals[0, 0].astype(np.int16)
    fb = originals[:, 1].astype(np.int16) - originals[0, 1].astype(np.int16)
    post = originals[3, 0].astype(np.int16) - originals[0, 0].astype(np.int16)
    crop_b = b.copy(); crop_b[:, 2] -= [left, top]
    sampled_u, sampled_m = sample_once(ub, x, y, crop_b), sample_once(mb, x, y, crop_b)
    sampled_flat = np.stack([sample_once(f, x, y, crop_b) for f in fb]); sampled_post = sample_once(post, x, y, crop_b)
    px, py = np.meshgrid(np.arange(left, right) + .5, np.arange(top, bottom) + .5)
    inv = np.linalg.inv(b[:, :2]); wx = inv[0, 0] * (px - b[0, 2]) + inv[0, 1] * (py - b[1, 2]); wy = inv[1, 0] * (px - b[0, 2]) + inv[1, 1] * (py - b[1, 2])
    inside = (wx >= ROI[0]) & (wx < ROI[2]) & (wy >= ROI[1]) & (wy < ROI[3])
    arrays.update(x=x, y=y, android_crop_original_xyxy=np.asarray(crop), android_output_affine=b,
                  android_original_endpoint_ROIs_round_shape_flat_RGB=originals, android_original_lattice_x=wx, android_original_lattice_y=wy,
                  android_original_lattice_in_fixed_ROI=inside, android_original_lattice_U_RGB=ub, android_original_lattice_M_RGB=mb,
                  android_original_lattice_flat_drift=fb, android_original_lattice_post_pre_shape=post,
                  android_once_sampled_U_RGB=sampled_u, android_once_sampled_M_RGB=sampled_m,
                  android_once_sampled_flat_drift=sampled_flat, android_once_sampled_post_pre_shape=sampled_post)
    drift = {"max_allowed_each_RGB_byte": 2, "flat_by_round": {}, "post_pre_shape": {}}
    for i, name in enumerate(ROUNDS):
        drift["flat_by_round"][name] = {"original_lattice": channels(fb[i], inside), "once_sampled_native_grid": channels(sampled_flat[i])}
        if np.abs(fb[i][inside]).max() > 2 or np.abs(sampled_flat[i]).max() > 2: report["errors"].append(name + " flat drift exceeds2 bytes")
    drift["post_pre_shape"] = {"original_lattice": channels(post, inside), "once_sampled_native_grid": channels(sampled_post)}
    if np.abs(post[inside]).max() > 2 or np.abs(sampled_post).max() > 2: report["errors"].append("Post-pre shape drift exceeds2 bytes")
    report["drift"] = drift
    report["mapping"] = {"fixed_native_grid_shape": [88, 88], "ROI_world_xyxy": ROI, "original_android_crop_xyxy_with_bilinear_guard": crop,
                         "actual_world_to_screenshot_affine": b, "world_to_producer_pixel_matrix": gs[0]["source_sampling_matrix"],
                         "order": "Signed int16 differences on original pixel lattice, followed by exactly one bilinear sample per difference field; no registration or colour conversion"}
    if report["errors"]:
        report["status"] = "REJECTED_DRIFT_GATES_DIAGNOSTIC_ARRAYS_ONLY"; return report, arrays
    un, mn = na["raw_global_output_input"][..., 1, 1].astype(float), na["raw_mask_output_input"][..., 1, 1].astype(float)
    ua, ma = sampled_u[..., 1], sampled_m[..., 1]
    domains = fixed_domains(x, y, na["inset_capsule_assumption"], gs[0]["carrier_bounds"])
    arrays.update(native_U_GG=un, native_M_GG=mn, android_U_GG=ua, android_M_GG=ma,
                  native_input_G_output_RGB=na["raw_global_output_input"][..., :, 1], native_mask_G_output_RGB=na["raw_mask_output_input"][..., :, 1],
                  frozen_native_M_positive=mn > 0, prespecified_nonzero_M_union=(mn != 0) | (ma != 0),
                  native_capsule_inset_assumption=na["inset_capsule_assumption"])
    arrays.update({"domain_" + k: v for k, v in domains.items()})
    report["raw_response_domains"] = {dn: {"native_U_GG": stats(un[d]), "native_M_GG": stats(mn[d]),
                                              "android_U_GG": stats(ua[d]), "android_M_GG": stats(ma[d]),
                                              "android_minus_native_U_GG": stats((ua - un)[d]), "android_minus_native_M_GG": stats((ma - mn)[d]),
                                              "android_global_input_G_output_RGB": channels(sampled_u, d), "android_mask_input_G_output_RGB": channels(sampled_m, d),
                                              "android_only_nonzero_mask_support": int((d & (mn == 0) & (ma != 0)).sum()),
                                              "mask_sign_reversal": int((d & (mn * ma < 0)).sum())} for dn, d in domains.items()}
    report["endpoint_literal_clipping"] = {r["name"]: {role: {"original_fixed_ROI_zero_RGB": [int((originals[i, j, ..., c][inside] == 0).sum()) for c in range(3)],
                                                                 "original_fixed_ROI_255_RGB": [int((originals[i, j, ..., c][inside] == 255).sum()) for c in range(3)]}
                                                               for j, role in enumerate(("shape", "flat"))} for i, r in enumerate(rows)}
    native_ep = na["original_ROIs_round_shape_flat_outputRGB"][[0, 2, 5, 7]]
    report["native_endpoint_literal_clipping"] = {"zero_RGB": [int((native_ep[..., c] == 0).sum()) for c in range(3)], "255_RGB": [int((native_ep[..., c] == 255).sum()) for c in range(3)], "absence_does_not_exclude_internal_clamping": True}
    report["conditional_common_alpha"] = comparison(un, mn, ua, ma, x, y, domains, arrays)
    report["unknowns"] = sorted(set(report["unknowns"]))
    report["status"] = "DIAGNOSTIC_COMPOSITE_RESPONSE_GEOMETRY_CONFOUNDED" if report["cross_system_geometry"]["status"] == "GEOMETRY_CONFOUNDED" else "DIAGNOSTIC_RESPONSE_UNKNOWN_MAPPING_OR_COLOUR" if report["unknowns"] else "BOUNDED_CONDITIONAL_RESPONSE_COMPARISON_ONLY"
    report["inference_allowed"] = False
    report["primary_endpoint_allowance"] = 4
    return report, arrays


def self_test():
    count = 0
    def check(value, message):
        nonlocal count
        require(bool(value), "Self-test failed: " + message); count += 1
    def rejects(f, message):
        try: f()
        except (ValueError, KeyError): check(True, message); return
        check(False, message)
    lo, hi, ok = alpha_interval([0, 0, 1, -20, 20], [0, 20, 20, -10, 30], 4)
    check(ok.tolist() == [True, False, False, True, False], "zero/negative/weak contradiction/out-of-range alpha")
    check(lo[0] == 0 and hi[0] == 1, "zero unresolved interval")
    c = compare_alpha(np.array([1., 20]), np.array([20., 0]), np.array([1., 20]), np.array([0., 20]), 4)
    check(not c["common_compatible"].any(), "weak failure retained and strong common intersection empty")
    check(c["native_weak"].tolist() == [True, False] and np.isnan(c["native_ratio_strong_only"][0]), "weak ratio unpublished")
    c = compare_alpha(np.array([20.]), np.array([10.]), np.array([-20.]), np.array([-10.]), 1)
    check(c["common_compatible"].all() and c["ratio_difference_strong_only"][0] == 0, "signed gains permit same alpha")
    aa = np.linspace(0, 1, 11); check(np.all(np.abs(1) + np.abs(-aa) + np.abs(-(1 - aa)) == 2), "shared baseline factor2")
    # Tiny deterministic affine field, no synthetic screenshot/evidence files.
    iy, ix = np.mgrid[:12, :14]; field = 3 * ix + 5 * iy + 7
    x, y = np.meshgrid(np.array([1.25, 2.25]), np.array([2.25, 3.25])); b = np.array([[1.2, .1, 2], [.2, 1.1, 1]])
    u, v = screen_indices(x, y, b)
    check(np.max(np.abs(sample_once(field, x, y, b) - (3 * u + 5 * v + 7))) < 1e-12, "known affine once-sampling")
    rejects(lambda: sample_once(field, x + 100, y, b), "mapping/clipping rejected")
    check(int((np.array([2], np.uint8).astype(np.int16) - np.array([250], np.uint8))[0]) == -248, "signed original-lattice subtraction")
    check(colour_metadata({})["status"] == "COLOR_SPACE_UNVERIFIED", "missing colour evidence stays unknown")
    check(colour_metadata({"srgb": 0})["status"] == "DECLARED_SRGB_OUTPUT_METADATA", "declared colour metadata only")
    g = {"owner_bounds": np.array([0., 0, 2, 2]), "carrier_bounds": np.array([0., 0, 2, 2]),
         "owner_matrix": np.array([1., 0, 0, 1, 0, 0]), "carrier_matrix": np.array([1., 0, 0, 1, 0, 0]),
         "owner_opacity": None, "carrier_opacity": None, "source_origin": np.zeros(2),
         "source_sampling_matrix": np.eye(2), "output_affine": np.array([[1., 0, 0], [0, 1, 0]])}
    check(stable_geometry([g, g])["status"] == "MAPPING_UNKNOWN_PIXEL_DIAGNOSTICS_ONLY", "opacity not fabricated")
    bad = dict(g, carrier_bounds=np.array([.2, 0, 2, 2])); check(bool(stable_geometry([g, bad])["errors"]), "geometry drift rejected")
    bad = dict(g, source_sampling_matrix=np.eye(2) * 1.0001); check(bool(stable_geometry([g, bad])["errors"]), "source sampling drift rejected")
    rejects(lambda: require(np.max(np.abs(np.array([0, 0, 3]))) <= LIMITS["drift"], "drift"), "drift3 cannot pass max2")
    xx, yy = np.meshgrid(np.arange(2), np.array([421., 430.])); ds = fixed_domains(xx, yy, np.ones((2, 2)), [0, 420, 4, 20])
    check(ds["rail_confounded_y422_438"].sum() == 2 and not np.any(ds["primary_native_capsule_inset1"] & ds["rail_confounded_y422_438"]), "rail retained separately")
    node = {"local_to_screen_unit_basis_px": [[2, 3], [3, 3], [2, 4]], "layout_size_px": [4, 5],
            "local_to_screen_corners_px": [{"local_px": p, "screen_px": [p[0] + 2, p[1] + 3]} for p in [[0, 0], [4, 0], [0, 5], [4, 5]]]}
    check(np.array_equal(node_affine(node)[1], np.eye(2)), "actual attached four-corner affine")
    broken = dict(node, local_to_screen_corners_px=node["local_to_screen_corners_px"][:-1]); rejects(lambda: node_affine(broken), "missing geometry cannot pass")
    check(sanitize({"ratio": float("nan")}) == {"ratio": None}, "undefined JSON not silently numerical")
    print(json.dumps({"status": "PASS_PURE_MATH_AND_GATE_SELF_TESTS", "checks": count,
                      "evidence_read": False, "files_written": False, "optical_acceptance": False}))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=HERE)
    p.add_argument("--native-study", type=Path, default=None)
    p.add_argument("--output", type=Path, default=None)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test: self_test(); return 0
    root = args.root.resolve(); study = (args.native_study or root.parent / "slider-color-response-20261116").resolve()
    output = (args.output or root / "analysis").resolve()
    require(not output.exists(), "Refusing to overwrite an existing output directory")
    report, arrays = execute(root, study)
    output.mkdir(parents=True)
    if arrays:
        np.savez_compressed(output / "response-arrays.npz", **arrays)
        report["arrays"] = artifact(output / "response-arrays.npz")
        report["array_keys"] = sorted(arrays)
    (output / "analysis.json").write_text(json.dumps(sanitize(report), ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": report["status"], "optical_acceptance": False, "errors": report["errors"],
                      "unknowns": report["unknowns"], "report": str(output / "analysis.json")}, ensure_ascii=False))
    return 2 if report["errors"] else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError) as exc:
        print(json.dumps({"status": "CLI_ERROR", "error": str(exc), "optical_acceptance": False}), file=sys.stderr)
        sys.exit(2)
