#!/usr/bin/env python3
"""Frozen full100 encoded-color diagnostic; no trace reads or image registration."""
from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
from pathlib import Path, PurePosixPath
import sys
import tempfile

import numpy as np
from PIL import Image

ROUNDS = ("control-pre", "global-R", "global-G", "global-B",
          "mask-R", "mask-G", "mask-B", "control-post")
CHANNELS = "RGB"
ROI = (331, 795, 419, 883)
THRESHOLDS = (1, 4, 8, 16, 24)
COUNTS = (1, 2, 4, 8, 16, 24)
INSET_BINS = (0, .5, 1, 1.5, 2, 3, 4, 5, 6, 7, 8, 10, 14, 20)
BASE_SHA = "9757bdb14092023996f2bd46d30b682799aac1fe06c221b7cad256c991e46724"
FLAT_SHA = "6e4291536355bff3dae7dee3957eec96bf4f3efc7566dd4257721a635ad8340b"
MASK_SHA = "0520b9b21148d9b0febef0f706c5ae9766d6ba3f6600d483e6d0f1980083202d"
LIMITS = {"bounds_pt": .1, "matrix": .001, "opacity": .01,
          "source_mapping": 1e-8, "drift_max_byte": 2}
UNIDENTIFIED = [
    "unique native pipeline or color-processing order",
    "unique spatial displacement, blur kernel, optical alpha or physical thickness",
    "linear-light matrix or infinitesimal Jacobian from finite encoded +20 secants",
    "cause of common-kernel incompatibility: channel sampling, transfer, nonlinear/adaptive color, clipping, layer mixtures and residual drift remain confounded",
    "universal linearity, motion timing or parity across backgrounds, sizes, shapes and controls",
    "alpha at weak uniform-response pixels; compatibility does not identify alpha",
]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def resolve(path, parent):
    p = Path(path)
    return p if p.is_absolute() else Path(parent) / p


def valid_sha(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def bound_file(path, expected):
    require(valid_sha(expected) and sha(path) == expected,
            f"missing or mismatched SHA-256: {path}")



def hash_map(value, label, allow_parent=False):
    require(isinstance(value, dict) and bool(value), f"missing or empty {label}")
    for relative, digest in value.items():
        require(isinstance(relative, str) and bool(relative) and "\\" not in relative,
                f"invalid relative path in {label}")
        path = PurePosixPath(relative)
        require(not path.is_absolute() and path.as_posix() == relative and posixpath.normpath(relative) == relative and relative != "."
                and (allow_parent or ".." not in path.parts), f"noncanonical relative path in {label}: {relative}")
        require(valid_sha(digest), f"invalid SHA-256 in {label}: {relative}")
    return value


def simulator_identity(value):
    require(isinstance(value, dict) and set(value) == {"udid", "runtime", "build"}
            and all(isinstance(v, str) and bool(v.strip()) for v in value.values()),
            "missing simulator udid/runtime/build identity")
    return value


def verify_frozen_files(root, frozen, required, asset_root):
    """Hash bytes only; parent entries are permitted strictly inside the asset repo."""
    files = hash_map(frozen["files"], "freeze.files", allow_parent=True)
    root, asset_root = Path(root).resolve(), Path(asset_root).resolve()
    seen = {}
    for relative, expected in files.items():
        path = (root / relative).resolve()
        require(path.is_relative_to(asset_root), f"frozen path escapes asset repository: {relative}")
        require(path != (root / "freeze.json").resolve(), "freeze.json cannot hash itself")
        require(path not in seen, f"duplicate frozen file aliases: {relative}")
        require(path.is_file(), f"missing frozen file: {relative}")
        bound_file(path, expected)
        seen[path] = relative
    for path in required:
        require(Path(path).resolve() in seen, f"required current file absent from freeze.files: {path}")
    return files


def load_freeze(root):
    path = root / "freeze.json"
    frozen = read(path)
    require(isinstance(frozen, dict), "freeze must be an object")
    require((root / "analyze-response.py").resolve() == Path(__file__).resolve(),
            "study analyzer is not the currently executing analyzer")
    required = [root / name for name in ("PROTOCOL.md", "analyze-response.py", "capture-native.py", "source-verification.json")]
    required += sorted((root / "native-tools").glob("*.py"))
    required += [root / "native-tools" / "capture-held-endpoints.py",
                 root / "native-tools" / "verify-full100-endpoints.py",
                 root.parent / "slider-fixtures" / "SOURCE-MAP.json",
                 root.parent / "slider-fixtures" / "tools/native-glass-reference/verify-static-optics.py"]
    required += [p for p in (root / "inputs").rglob("*") if p.is_file()]
    for name in ROUNDS:
        parent = root / "inputs/rounds" / name
        required += [parent / "shape-spec.json", parent / "inputs/manifest.json"]
        spec = read(parent / "shape-spec.json")
        manifest = read(parent / "inputs/manifest.json")
        required += [parent / "inputs" / row["file"] for row in manifest["inputs"]]
        def referenced_pngs(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    if key.endswith("_png"):
                        require(isinstance(item, str), "invalid source PNG reference")
                        required.append(resolve(item, parent))
                    else:
                        referenced_pngs(item)
            elif isinstance(value, list):
                for item in value:
                    referenced_pngs(item)
        referenced_pngs(spec)
    files = verify_frozen_files(root, frozen, required, Path(__file__).resolve().parents[2])
    hash_map(frozen["prepared_native_files"], "freeze.prepared_native_files")
    hash_map(frozen["native_binaries"], "freeze.native_binaries")
    simulator_identity(frozen["simulator"])
    return {"sha256": sha(path), "path": str(path), "value": frozen,
            "verified_current_file_count": len(files)}



def verify_capture_artifacts(parent, receipt, required):
    artifacts = hash_map(receipt["analysis_artifacts"], "capture.analysis_artifacts")
    seen = {}
    parent = Path(parent).resolve()
    for relative, expected in artifacts.items():
        path = (parent / relative).resolve()
        require(path.is_relative_to(parent), f"capture artifact escapes capture directory: {relative}")
        require(path != parent / "receipt.json", "capture receipt cannot hash itself")
        require(path not in seen, f"duplicate capture artifact aliases: {relative}")
        require(path.is_file(), f"missing capture artifact: {relative}")
        bound_file(path, expected)
        seen[path] = relative
    for path in required:
        require(Path(path).resolve() in seen, f"required output absent from capture receipt artifacts: {path}")
    return seen


def check_capture_identity(receipt, frozen, name, role):
    value = frozen["value"]
    require(receipt["phase"] == "capture" and receipt["round"] == name, "wrong capture phase or round")
    require(receipt["freeze_sha256"] == frozen["sha256"], "capture freeze SHA-256 differs from current freeze")
    for key in ("prepared_native_files", "native_binaries"):
        actual = hash_map(receipt[key], "capture." + key)
        require(actual == value[key], "capture " + key + " differs from frozen native identity")
    identity = simulator_identity(receipt["simulator_identity"])
    require(identity == value["simulator"] and receipt["simulator"] == identity["udid"],
            "capture simulator identity differs from freeze")
    require(receipt["spec_sha256"] == role["spec_sha256"]
            and receipt["manifest_sha256"] == role["manifest_sha256"], "capture source identities differ")
    require(receipt["captures"] == receipt["verified_held_endpoints"] == 2
            and receipt["verified_shape_flat_pairs"] == 1, "capture did not complete exact endpoint/pair scope")
    times = numeric([receipt["started_unix"], receipt["finished_unix"]], (2,))
    require(times[1] >= times[0], "capture finish precedes start")
    commands = receipt["commands"]
    require(isinstance(commands, list) and bool(commands)
            and all(c["exit_code"] == 0 for c in commands), "capture command failed or missing")


def numeric(value, shape=None):
    a = np.asarray(value, dtype=float)
    require(np.isfinite(a).all(), "nonfinite numeric evidence")
    if shape is not None:
        require(a.shape == shape, f"evidence shape {a.shape}, required {shape}")
    return a


def rgb(path, expected):
    bound_file(path, expected)
    with Image.open(path) as im:
        require(im.format == "PNG" and im.mode in ("RGB", "RGBA"), f"expected RGB8 PNG: {path}")
        require(im.size == (750, 1334), f"original 750x1334 PNG required: {path}")
        a = np.asarray(im, dtype=np.uint8)
        if im.mode == "RGBA":
            require(np.all(a[..., 3] == 255), f"nonopaque PNG: {path}")
        return a[..., :3].copy(), hashlib.sha256(im.info.get("icc_profile", b"")).hexdigest()


def load_sources(root):
    roles = {}
    for name in ROUNDS:
        parent = root / "inputs" / "rounds" / name
        sp, mp = parent / "shape-spec.json", parent / "inputs" / "manifest.json"
        spec, manifest = read(sp), read(mp)
        require(manifest.get("split") == "calibration", f"non-calibration source: {name}")
        require(spec["flat_input_id"] == "st00_flat128", "ordinary flat relabeled")
        main_id = spec["first_input_id"]
        main = next(v for v in spec["inputs"] if v["id"] == main_id)
        entries = {v["id"]: v for v in manifest["inputs"]}
        require(main["source_sha256"] == entries[main_id]["sha256"], "spec/main manifest identity differs")
        require(entries["st00_flat128"]["sha256"] == FLAT_SHA, "ordinary flat source changed")
        source_path = resolve(main["shape"]["source_png"], parent)
        require(source_path.resolve() == (mp.parent / entries[main_id]["file"]).resolve(),
                "spec/manifest source paths differ")
        image, icc = rgb(source_path, main["source_sha256"])
        flat_path = mp.parent / entries["st00_flat128"]["file"]
        flat, flat_icc = rgb(flat_path, FLAT_SHA)
        require(np.all(flat == 128), "ordinary flat is not RGB128")
        shape = main["shape"]
        require(shape["point_count"] == 5 and shape["size_pt"] == 16
                and shape["center_world_pt"] == [187.5, 419.5], "changed star geometry")
        left = next(v for v in shape["regions"] if v["id"] == "left_blue")
        require(left["coverage_denominator"] == 16 and left["coverage_count_mask_sha256"] == MASK_SHA,
                "changed left-blue coverage identity")
        mask_path = resolve(left["coverage_count_mask_png"], parent)
        bound_file(mask_path, MASK_SHA)
        with Image.open(mask_path) as im:
            require(im.mode == "L" and im.size == (750, 1334), "coverage16 source must be original L8 grid")
            coverage = np.asarray(im, dtype=np.int16)
            require(np.all((coverage >= 0) & (coverage <= 16)), "invalid coverage16 counts")
        roles[name] = {"id": main_id, "image": image, "icc": icc, "flat_icc": flat_icc,
                       "coverage": coverage, "source_sha256": main["source_sha256"],
                       "spec_sha256": sha(sp), "manifest_sha256": sha(mp),
                       "geometry": {k: shape[k] for k in ("vertices_world_pt", "size_pt", "center_world_pt", "point_count")},
                       "paths": {"spec": str(sp), "manifest": str(mp), "source": str(source_path), "flat": str(flat_path), "mask": str(mask_path)}}
    require(roles["control-pre"]["id"] == "st01_rgb_star_d16"
            and roles["control-pre"]["source_sha256"] == BASE_SHA, "baseline is not original RGB star")
    require(roles["control-post"]["source_sha256"] == BASE_SHA, "post baseline source differs")
    validate_source_arrays(roles)
    return roles


def validate_source_arrays(roles):
    base = roles["control-pre"]
    b = base["image"].astype(np.int16)
    require(np.array_equal(roles["control-post"]["image"], base["image"]), "pre/post source bytes differ")
    increment = (20 * base["coverage"] + 8) // 16
    for name, role in roles.items():
        require(role["icc"] == base["icc"] and role["flat_icc"] == base["flat_icc"], "source ICC changed")
        require(role["geometry"] == base["geometry"] and np.array_equal(role["coverage"], base["coverage"]),
                "source geometry/mask differs")
        expected = b.copy()
        if name.startswith(("global-", "mask-")):
            j = CHANNELS.index(name[-1])
            expected[..., j] += 20 if name.startswith("global-") else increment
        require(np.all((expected >= 0) & (expected <= 255)), "source perturbation would clip")
        require(np.array_equal(role["image"], expected), f"unexpected source perturbation: {name}")


def check_receipt(receipt):
    require(receipt.get("status") == "passed" and receipt.get("errors") == [], "strict receipt did not pass")
    require(receipt.get("captures") == receipt.get("verifiedHeldEndpoints") == 2
            and receipt.get("verifiedShapeFlatPairs") == 1, "strict full100 receipt must verify 2 endpoints/1 pair")
    matrix = receipt["matrix"]
    require(matrix["expectedCaptures"] == matrix["actualCaptures"] == 2
            and all(matrix[k] == [] for k in ("missing", "unexpected", "duplicates")), "strict matrix is not exact")
    require(len(receipt["observations"]) == 2, "strict receipt must have exactly two observations")


def source_mapping(source):
    require(source["colorSpace"] == "sRGB" and source["worldSizePt"] == [375, 667]
            and source["worldOriginPt"] == [0, 0] and source["sizePx"] == [750, 1334]
            and source["pixelsPerPt"] == 2, "source mapping/declaration differs")
    canvas = numeric([source["canvasRectInWindowPt"][k] for k in ("x", "y", "w", "h")], (4,))
    require(np.array_equal(canvas, [0, 0, 375, 667]), "source canvas mapping differs")
    return canvas[:2], np.diag([2., 2.])


def observation_geometry(o):
    session, source = o["session"], o["externalInput"]
    require(session["screenScale"] == 2 and session["screenWidthPt"] == 375
            and session["screenHeightPt"] == 667, "actual screen grid differs")
    origin, sampling = source_mapping(source)
    require(o["ownerPoseStability"]["stable"] is True and o["carrierPoseStability"]["stable"] is True,
            "public owner/carrier not stable")
    samples = o["presentedPoseSamples"]
    require(len(samples) >= 4, "missing presented owner/carrier samples")
    result = {"source_origin": origin, "source_matrix": sampling}
    for role, key in (("owner", "actualControlBoundsPt"), ("carrier", "actualCarrierBoundsPt")):
        values = [s[role] for s in samples]
        require(all(v["presentationAvailable"] is True and v["effectiveHidden"] is False for v in values),
                "unavailable or hidden public presentation")
        result[role + "_bounds"] = numeric(o[key], (4,))
        require(np.all(result[role + "_bounds"][2:] > 0), "invalid actual presented bounds")
        result[role + "_sample_bounds"] = numeric([[v[k] for k in ("x", "y", "w", "h")] for v in values])
        result[role + "_matrix"] = numeric([[v[k] for k in ("m11", "m12", "m21", "m22", "m41", "m42")] for v in values])
        result[role + "_opacity"] = numeric([v["effectiveOpacity"] for v in values])
        require(np.max(abs(result[role + "_sample_bounds"] - result[role + "_bounds"])) <= .1 + 1e-10,
                "representative bounds differ from actual presented samples")
    require(np.max(abs(numeric(o["actualCarrierCenterPt"], (2,)) -
                       (result["carrier_bounds"][:2] + result["carrier_bounds"][2:] / 2))) <= 1e-6,
            "carrier center/bounds mismatch")
    return result


def load_round(root, name, role, frozen):
    parent = root / "rounds" / name / "native-r1"
    ip, rp = parent / "index-strict.json", parent / "endpoint-verification-strict.json"
    cp = parent / "receipt.json"
    capture_receipt = read(cp)
    check_capture_identity(capture_receipt, frozen, name, role)
    artifact_paths = verify_capture_artifacts(parent, capture_receipt, [ip, rp])
    index, receipt = read(ip), read(rp)
    require(index.get("platform") == "ios" and index.get("status") == "passed"
            and not index.get("synthetic_fixture", False), "only accepted actual native index is allowed")
    check_receipt(receipt)
    require(receipt["verifierSHA256"] == sha(root / "native-tools/verify-full100-endpoints.py")
            and receipt["pngValidatorSHA256"] == sha(root.parent / "slider-fixtures/tools/native-glass-reference/verify-static-optics.py"),
            "strict verifier/PNG validator differs from current frozen verifier")
    require(receipt["specSHA256"] == role["spec_sha256"] and receipt["manifestSHA256"] == role["manifest_sha256"],
            "strict receipt source spec/manifest hash mismatch")
    require(receipt["shapeID"] == role["id"] and receipt["flatID"] == "st00_flat128", "receipt source IDs differ")
    captures = index["captures"]
    require(len(captures) == 1 and captures[0]["stage_id"] == "full100", "index must contain only full100")
    c = captures[0]
    require(c["shape_id"] == c["input_id"] == role["id"], "index scheduled input differs")
    require(resolve(c["receipt_json"], parent).resolve() == rp.resolve(), "index is bound to another receipt")
    require(all(resolve(c[key], parent).resolve() in artifact_paths for key in ("png", "flat_png")),
            "shape/flat PNG missing from capture receipt artifacts")
    loaded = {"geometries": {}, "images": {}, "evidence": {"index": str(ip), "index_sha256": sha(ip),
              "receipt": str(rp), "receipt_sha256": sha(rp),
              "capture_receipt": str(cp), "capture_receipt_sha256": sha(cp), "freeze_sha256": frozen["sha256"],
              "analysis_artifacts": capture_receipt["analysis_artifacts"],
              "prepared_native_files": capture_receipt["prepared_native_files"],
              "native_binaries": capture_receipt["native_binaries"], "simulator_identity": capture_receipt["simulator_identity"],
              "verifier_sha256": receipt["verifierSHA256"],
              "png_validator_sha256": receipt["pngValidatorSHA256"], "source": role["paths"],
              "source_sha256": role["source_sha256"], "spec_sha256": role["spec_sha256"],
              "manifest_sha256": role["manifest_sha256"]}}
    operating = []
    for flat, label in ((False, "shape"), (True, "flat")):
        hkey, pkey = ("flat_sha256", "flat_png") if flat else ("sha256", "png")
        matches = [o for o in receipt["observations"] if o["imageSHA256"] == c[hkey]]
        require(len(matches) == 1, "PNG not uniquely bound to strict observation")
        o = matches[0]
        require(o["verifiedHeldEndpoint"] is True and o["errors"] == [], "endpoint not verified")
        event = o["event"]
        require(event["coverageStageID"] == "full100" and event["isFlatControl"] is flat
                and event["inputID"] == ("st00_flat128" if flat else role["id"]), "event stage/flat/input differs")
        require(event["nativeControlOverrides"] == [] and event["requestedTheme"] == "light", "changed native control/style")
        require(o["externalInput"]["sha256"] == (FLAT_SHA if flat else role["source_sha256"]),
                "delivered native source hash mismatch")
        p = resolve(c[pkey], parent)
        require(p.resolve() == resolve(o["png"], parent).resolve(), "index/receipt PNG paths differ")
        image, _ = rgb(p, c[hkey])
        pv = o["pngValidation"]
        require(pv["width"] == 750 and pv["height"] == 1334 and pv["bitDepth"] == 8
                and pv["colorType"] in (2, 6), "strict PNG declaration differs")
        g = observation_geometry(o)
        mg = c["flat_geometry"] if flat else c
        require(mg["pixels_per_world_unit"] == 2 and mg["world_origin_window_px"] == [0, 0], "index output mapping differs")
        require(np.max(abs(numeric(mg["actual_carrier_bounds_world_xywh"], (4,)) - g["carrier_bounds"])) <= .1 + 1e-10,
                "index/receipt carrier bounds differ")
        operating.append({k: o["session"][k] for k in ("os", "device", "interfaceStyle", "screenScale", "screenWidthPt",
                          "screenHeightPt", "reduceMotion", "reduceTransparency", "darkerSystemColors", "tintSRGB")})
        require(all(o["session"][k] is False for k in ("reduceMotion", "reduceTransparency", "darkerSystemColors")),
                "changed accessibility color/motion settings")
        loaded["geometries"][label] = g
        x0, y0, x1, y1 = ROI
        loaded["images"][label] = image[y0:y1, x0:x1].copy()
        loaded["evidence"][label + "_png_sha256"] = c[hkey]
    require(operating[0] == operating[1], "shape/flat operating state differs")
    loaded["operating"] = operating[0]
    return loaded


def compare_geometry(geometries):
    checks = {}
    for role in ("owner", "carrier"):
        bounds = np.concatenate([np.vstack((g[role + "_bounds"], g[role + "_sample_bounds"])) for g in geometries])
        centers = bounds[:, :2] + bounds[:, 2:] / 2
        checks[role + "_bounds_max_range_pt"] = float(np.ptp(bounds, axis=0).max())
        checks[role + "_center_max_range_pt"] = float(np.ptp(centers, axis=0).max())
        checks[role + "_matrix_max_range"] = float(np.ptp(np.concatenate([g[role + "_matrix"] for g in geometries]), axis=0).max())
        checks[role + "_opacity_max_range"] = float(np.ptp(np.concatenate([g[role + "_opacity"] for g in geometries])))
    checks["source_origin_max_range"] = float(np.ptp(np.stack([g["source_origin"] for g in geometries]), axis=0).max())
    checks["source_matrix_max_range"] = float(np.ptp(np.stack([g["source_matrix"] for g in geometries]), axis=0).max())
    for key, value in checks.items():
        limit = LIMITS["bounds_pt"] if "bounds" in key or "center" in key else (
            LIMITS["source_mapping"] if key.startswith("source_") else
            LIMITS["opacity"] if "opacity" in key else LIMITS["matrix"])
        require(value <= limit + 1e-10, f"geometry mismatch: {key}={value} > {limit}")
    return checks


def statistics(a):
    a = np.asarray(a, dtype=float).ravel()
    finite = np.isfinite(a)
    v = a[finite]
    if not len(v):
        return {"samples": 0, "unidentified_samples": int(len(a))}
    return {"samples": int(len(v)), "unidentified_samples": int(np.sum(~finite)),
            "min": float(v.min()), "max": float(v.max()), "max_abs": float(abs(v).max()),
            "mean": float(v.mean()), "median": float(np.median(v)),
            "signed_quantiles": {str(q): float(np.quantile(v, q)) for q in (.01, .1, .5, .9, .99)},
            "absolute_quantiles": {str(q): float(np.quantile(abs(v), q)) for q in (.5, .9, .99)},
            "energy_sum_squares": float(np.sum(v * v)), "rmse": float(np.sqrt(np.mean(v * v))),
            "threshold_counts": {str(t): {"positive": int(np.sum(v > t)), "negative": int(np.sum(v < -t)),
                                         "absolute": int(np.sum(abs(v) > t))} for t in COUNTS}}


def channel_statistics(a):
    return {c: statistics(a[..., i]) for i, c in enumerate(CHANNELS)}


def check_drift(images):
    baseline = images["control-pre"]
    result = {name: channel_statistics(v["flat"].astype(float) - baseline["flat"]) for name, v in images.items()}
    post = channel_statistics(images["control-post"]["shape"].astype(float) - baseline["shape"])
    offending = [f"{name}:flat:{c}" for name, vals in result.items() for c, s in vals.items()
                 if s["max_abs"] > LIMITS["drift_max_byte"]]
    offending += ["post-pre:shape:" + c for c, s in post.items() if s["max_abs"] > LIMITS["drift_max_byte"]]
    return {"flat_per_round_RGB": result, "post_pre_shape_RGB": post, "errors": offending,
            "gate_max_byte": LIMITS["drift_max_byte"], "status": "rejected" if offending else "within_frozen_gate"}


def interval(u, m, tolerance):
    """Necessary bounded-alpha feasibility, including zero/negative gain entries."""
    u, m = np.asarray(u, float), np.asarray(m, float)
    t = np.asarray(tolerance, float)
    if t.ndim == u.ndim - 1:
        t = t[..., None]
    nz = u != 0
    safe = np.where(nz, u, 1.)
    a, b = (m - t) / safe, (m + t) / safe
    lo = np.maximum(0., np.max(np.where(nz, np.minimum(a, b), -np.inf), axis=-1))
    hi = np.minimum(1., np.min(np.where(nz, np.maximum(a, b), np.inf), axis=-1))
    impossible_zero = np.any((~nz) & (abs(m) > t), axis=-1)
    valid = (lo <= hi) & ~impossible_zero
    return lo, hi, valid


def model_diagnostic(u, m):
    """Constraint intervals plus a descriptive minimax residual, never parity."""
    uniform_resolved = np.max(abs(u), axis=-1) > 4
    mask_resolved = np.max(abs(m), axis=-1) > 4
    intervals = {t: interval(u, m, t) for t in THRESHOLDS}
    low = np.zeros(u.shape[:-1], dtype=float)
    high = np.max(abs(m), axis=-1).astype(float)
    # Alpha=0 always makes high feasible. Bisection accuracy is fixed before capture.
    for _ in range(40):
        mid = (low + high) / 2
        good = interval(u, m, mid)[2]
        high = np.where(good, mid, high)
        low = np.where(good, low, mid)
    lo, hi, good = interval(u, m, high + 1e-10)
    require(np.all(good), "internal minimax feasibility failure")
    minimax_alpha = (lo + hi) / 2
    residual = m - minimax_alpha[..., None] * u
    return {"intervals": intervals, "minimax_residual": residual,
            "minimax_error": np.max(abs(residual), axis=-1),
            "alpha_descriptive": np.where(uniform_resolved, minimax_alpha, np.nan),
            "uniform_resolved": uniform_resolved, "mask_resolved": mask_resolved,
            "response_unresolved": ~uniform_resolved & ~mask_resolved}


def capsule_inset(x, y, bounds):
    left, top, width, height = bounds
    radius = height / 2
    dx = np.maximum(abs(x - (left + width / 2)) - (width / 2 - radius), 0)
    return radius - np.hypot(dx, y - (top + radius))


def component_statistics(a, domain):
    return {f"out-{o}_in-{j}": statistics(a[..., i, k][domain])
            for i, o in enumerate(CHANNELS) for k, j in enumerate(CHANNELS)}


def summarize_model(model, domain):
    return {"uniform_resolved_pixels": int(np.sum(domain & model["uniform_resolved"])),
            "uniform_weak_mask_resolved_pixels": int(np.sum(domain & ~model["uniform_resolved"] & model["mask_resolved"])),
            "response_unresolved_pixels": int(np.sum(domain & model["response_unresolved"])),
            "minimax_error_raw_byte": statistics(model["minimax_error"][domain]),
            "alpha_descriptive_uniform_resolved_only": statistics(model["alpha_descriptive"][domain]),
            "tolerances_raw_byte": {str(t): {
                "compatible_pixels": int(np.sum(domain & val[2])),
                "incompatible_pixels": int(np.sum(domain & ~val[2])),
                "compatible_interval_width": statistics((val[1] - val[0])[domain & val[2]])}
                for t, val in model["intervals"].items()}}


def analyze(loaded, output, result):
    images = {k: v["images"] for k, v in loaded.items()}
    drift = check_drift(images)
    result["drift"] = drift
    if drift["errors"]:
        result["status"] = "REJECTED_DRIFT_NO_RESPONSE_ANALYSIS"
        return
    pre = images["control-pre"]["shape"].astype(np.int16)
    u = np.stack([images["global-" + c]["shape"].astype(np.int16) - pre for c in CHANNELS], axis=-1)
    m = np.stack([images["mask-" + c]["shape"].astype(np.int16) - pre for c in CHANNELS], axis=-1)
    yy, xx = np.mgrid[ROI[1]:ROI[3], ROI[0]:ROI[2]]
    x, y = (xx + .5) / 2, (yy + .5) / 2
    bounds = loaded["control-pre"]["geometries"]["shape"]["carrier_bounds"]
    inset = capsule_inset(x, y, bounds)
    domains = {"complete": np.ones(x.shape, bool), "above_rail": y < 422,
               "rail_confounded": (y >= 422) & (y < 438), "below_rail": y >= 438,
               "primary_above_rail_inset_ge1": (y < 422) & (inset >= 1),
               "above_rail_rim_inset_lt1": (y < 422) & (inset < 1)}
    for lo, hi in zip(INSET_BINS[:-1], INSET_BINS[1:]):
        for name, region in (("above_rail", y < 422), ("rail_confounded", (y >= 422) & (y < 438))):
            domains[f"{name}_inset_{lo}_{hi}"] = region & (inset >= lo) & (inset < hi)
    common = model_diagnostic(u.reshape(*x.shape, 9), m.reshape(*x.shape, 9))
    columns = {c: model_diagnostic(u[..., :, j], m[..., :, j]) for j, c in enumerate(CHANNELS)}
    rows = {c: model_diagnostic(u[..., i, :], m[..., i, :]) for i, c in enumerate(CHANNELS)}
    common_residual = common["minimax_residual"].reshape(*x.shape, 3, 3)
    column_residual = np.stack([columns[c]["minimax_residual"] for c in CHANNELS], axis=-1)
    row_residual = np.stack([rows[c]["minimax_residual"] for c in CHANNELS], axis=-2)
    result["domains"] = {name: {"pixels": int(np.sum(domain)),
        "raw_global_components": component_statistics(u, domain), "raw_mask_components": component_statistics(m, domain),
        "Jglobal_components": component_statistics(u / 20., domain), "Jmask_components": component_statistics(m / 20., domain),
        "common": summarize_model(common, domain),
        "input_columns": {c: summarize_model(v, domain) for c, v in columns.items()},
        "output_rows": {c: summarize_model(v, domain) for c, v in rows.items()},
        "common_signed_residual_components": component_statistics(common_residual, domain),
        "column_signed_residual_components": component_statistics(column_residual, domain),
        "row_signed_residual_components": component_statistics(row_residual, domain)} for name, domain in domains.items()}
    arrays = {"x": x, "y": y, "inset_capsule_assumption": inset,
              "original_ROIs_round_shape_flat_outputRGB": np.stack([np.stack([images[n][q] for q in ("shape", "flat")]) for n in ROUNDS]),
              "raw_global_output_input": u, "raw_mask_output_input": m, "Jglobal_output_input": u / 20., "Jmask_output_input": m / 20.,
              "common_signed_minimax_residual": common_residual,
              "input_column_signed_minimax_residual": column_residual, "output_row_signed_minimax_residual": row_residual,
              "flat_drift_round_output": np.stack([images[n]["flat"].astype(np.int16) - images["control-pre"]["flat"] for n in ROUNDS]),
              "post_pre_shape_drift": images["control-post"]["shape"].astype(np.int16) - pre}
    for family, models in (("common", {"all": common}), ("input", columns), ("output", rows)):
        for name, model in models.items():
            prefix = family + "_" + name
            for key in ("minimax_error", "alpha_descriptive", "uniform_resolved", "mask_resolved", "response_unresolved"):
                arrays[prefix + "_" + key] = model[key]
            for t, (lo, hi, compatible) in model["intervals"].items():
                for key, a in (("lo", lo), ("hi", hi), ("compatible", compatible)):
                    arrays[f"{prefix}_T{t}_{key}"] = a
    np.savez_compressed(output / "original-pixels.npz", **arrays)
    result["arrays_sha256"] = sha(output / "original-pixels.npz")
    result["primary_T4_incompatibility_coordinates_world_pt"] = {
        "common": np.stack((x[~common["intervals"][4][2]], y[~common["intervals"][4][2]]), axis=-1).tolist(),
        "input_columns": {c: np.stack((x[~v["intervals"][4][2]], y[~v["intervals"][4][2]]), axis=-1).tolist() for c, v in columns.items()},
        "output_rows": {c: np.stack((x[~v["intervals"][4][2]], y[~v["intervals"][4][2]]), axis=-1).tolist() for c, v in rows.items()}}
    result["status"] = "OBSERVED_ENCODED_COLOR_CALIBRATION_DIAGNOSTIC_NOT_OPTICAL_ACCEPTANCE"


def self_test():
    # Dense mixing makes row- and column-dependent spatial responses distinguishable
    # in this synthetic example; diagonal matrices would not provide that guarantee.
    u = np.full((2, 3, 3, 3), 20.)
    common = model_diagnostic(u.reshape(2, 3, 9), (.35 * u).reshape(2, 3, 9))
    require(np.all(common["intervals"][1][2]) and np.max(common["minimax_error"]) < 1e-7, "common-kernel example")
    ci = u * np.array([.1, .5, .9])[None, None, None, :]
    co = u * np.array([.1, .5, .9])[None, None, :, None]
    for m, family in ((ci, "input"), (co, "output")):
        require(not np.any(model_diagnostic(u.reshape(2, 3, 9), m.reshape(2, 3, 9))["intervals"][4][2]), "distinct kernels must challenge common null")
        for i in range(3):
            a, b = (u[..., :, i], m[..., :, i]) if family == "input" else (u[..., i, :], m[..., i, :])
            require(np.all(model_diagnostic(a, b)["intervals"][1][2]), "matching row/column family")
        a, b = (u[..., 0, :], m[..., 0, :]) if family == "input" else (u[..., :, 0], m[..., :, 0])
        require(not np.any(model_diagnostic(a, b)["intervals"][4][2]), "wrong family cannot explain dense synthetic case")
    none = model_diagnostic(np.zeros((1, 9)), np.zeros((1, 9)))
    require(none["response_unresolved"][0] and np.isnan(none["alpha_descriptive"][0]), "no-response is unidentified")
    contradiction = model_diagnostic(np.zeros((1, 9)), np.full((1, 9), 10.))
    require(not contradiction["intervals"][4][2][0] and np.isnan(contradiction["alpha_descriptive"][0]), "weak DC cannot hide strong masked contradiction")
    require(interval(np.array([[-20., 0., 10.]]), np.array([[-10., 0., 5.]]), 0)[2][0], "negative/zero gain handling")
    images = {n: {q: np.zeros((10, 10, 3), dtype=np.uint8) for q in ("shape", "flat")} for n in ROUNDS}
    require(not check_drift(images)["errors"], "stable synthetic repeated controls")
    images["global-G"]["flat"][0, 0, 1] = 3
    require(check_drift(images)["errors"] == ["global-G:flat:G"], "one drifting pixel cannot be pooled away")
    images["global-G"]["flat"][0, 0, 1] = 0
    images["control-post"]["shape"][0, 0, 0] = 3
    require(check_drift(images)["errors"] == ["post-pre:shape:R"], "post shape drift must reject")
    g = {"source_origin": np.zeros(2), "source_matrix": np.eye(2) * 2}
    for role in ("owner", "carrier"):
        g.update({role + "_bounds": np.array([20., 410., 57., 37.]),
                  role + "_sample_bounds": np.array([[20., 410., 57., 37.]]),
                  role + "_matrix": np.array([[1., 0., 0., 1., 0., 0.]]), role + "_opacity": np.ones(1)})
    compare_geometry([g, g])
    bad = {k: v.copy() for k, v in g.items()}
    bad["carrier_bounds"][0] += .11
    expect_rejection(lambda: compare_geometry([g, bad]), "geometry")
    bad = {k: v.copy() for k, v in g.items()}
    bad["source_matrix"][0, 0] += .001
    expect_rejection(lambda: compare_geometry([g, bad]), "source mapping")
    expect_rejection(lambda: observation_geometry({}), "missing required evidence")
    base = np.full((2, 2, 3), 128, dtype=np.uint8)
    coverage = np.array([[0, 4], [8, 16]], dtype=np.int16)
    roles = {}
    for n in ROUNDS:
        a = base.astype(np.int16)
        if n.startswith(("global-", "mask-")):
            a[..., CHANNELS.index(n[-1])] += 20 if n.startswith("global-") else (20 * coverage + 8) // 16
        roles[n] = {"image": a.astype(np.uint8), "coverage": coverage, "icc": "same", "flat_icc": "same", "geometry": "same"}
    validate_source_arrays(roles)
    roles["mask-B"]["image"][0, 0, 0] += 1
    expect_rejection(lambda: validate_source_arrays(roles), "source channel mismatch")
    with tempfile.TemporaryDirectory(prefix="slider-freeze-self-test-") as directory:
        asset = Path(directory) / "asset"
        study = asset / "research/study"
        study.mkdir(parents=True)
        current = study / "analyze-response.py"
        current.write_bytes(b"synthetic analyzer bytes\n")
        shared = study.parent / "shared.txt"
        shared.write_bytes(b"synthetic shared provenance\n")
        files = {"analyze-response.py": sha(current), "../shared.txt": sha(shared)}
        verify_frozen_files(study, {"files": files}, [current, shared], asset)
        expect_rejection(lambda: verify_frozen_files(study, {"files": {"analyze-response.py": sha(current)}},
                                                     [current, shared], asset), "missing required freeze member")
        current.write_bytes(b"changed synthetic analyzer bytes\n")
        expect_rejection(lambda: verify_frozen_files(study, {"files": files}, [current], asset), "frozen script drift")
        files["analyze-response.py"] = sha(current)
        outside = dict(files, **{"../../../outside.txt": "a" * 64})
        expect_rejection(lambda: verify_frozen_files(study, {"files": outside}, [current], asset), "freeze repository escape")
        aliases = dict(files, **{"nested/../analyze-response.py": sha(current)})
        expect_rejection(lambda: verify_frozen_files(study, {"files": aliases}, [current], asset), "freeze aliases")
        artifact = study / "synthetic-output.txt"
        artifact.write_bytes(b"synthetic capture artifact\n")
        receipt = {"analysis_artifacts": {artifact.name: sha(artifact)}}
        verify_capture_artifacts(study, receipt, [artifact])
        expect_rejection(lambda: verify_capture_artifacts(study, receipt, [current]), "missing required capture artifact")
        artifact.write_bytes(b"changed synthetic capture artifact\n")
        expect_rejection(lambda: verify_capture_artifacts(study, receipt, [artifact]), "capture artifact drift")
        expect_rejection(lambda: verify_capture_artifacts(study, {"analysis_artifacts": {"../shared.txt": sha(shared)}}, []),
                         "capture artifact path escape")
    identity = {"udid": "synthetic-udid", "runtime": "synthetic-runtime", "build": "synthetic-build"}
    frozen = {"sha256": "a" * 64, "value": {
        "prepared_native_files": {"App/main.swift": "b" * 64},
        "native_binaries": {"Build/Products/Native.app/Native": "c" * 64}, "simulator": identity}}
    role = {"spec_sha256": "d" * 64, "manifest_sha256": "e" * 64}
    capture = {"phase": "capture", "round": ROUNDS[0], "freeze_sha256": frozen["sha256"],
               "prepared_native_files": frozen["value"]["prepared_native_files"],
               "native_binaries": frozen["value"]["native_binaries"],
               "simulator_identity": identity, "simulator": identity["udid"], **role,
               "captures": 2, "verified_held_endpoints": 2, "verified_shape_flat_pairs": 1,
               "started_unix": 1, "finished_unix": 2, "commands": [{"exit_code": 0}]}
    check_capture_identity(capture, frozen, ROUNDS[0], role)
    def changed_capture(key, value):
        bad = json.loads(json.dumps(capture))
        bad[key] = value
        return lambda: check_capture_identity(bad, frozen, ROUNDS[0], role)
    expect_rejection(changed_capture("freeze_sha256", "f" * 64), "capture freeze drift")
    expect_rejection(changed_capture("prepared_native_files", {"App/main.swift": "f" * 64}), "native source drift")
    expect_rejection(changed_capture("native_binaries", {"Build/Products/Native.app/Native": "f" * 64}), "native binary drift")
    expect_rejection(changed_capture("simulator_identity", {**identity, "build": "other"}), "simulator build drift")
    expect_rejection(changed_capture("commands", [{"exit_code": 1}]), "failed capture command")
    expect_rejection(lambda: hash_map({"../escape": "a" * 64}, "native paths"), "nonrelative native identity path")
    print(json.dumps({"status": "synthetic_contract_checks_passed", "scope": "synthetic only; no optical images or traces read",
                      "cases": ["common kernel", "input-channel kernels", "output-channel kernels", "no response", "weak DC contradiction",
                                "negative/zero gains", "localized flat drift", "post-shape drift", "geometry mismatch", "source mapping mismatch",
                                "missing evidence", "source channel mismatch", "frozen current script/hash and required membership",
                                "allowed in-repository parent provenance", "freeze repository escape and duplicate aliases",
                                "capture freeze identity", "native source/binary identity", "simulator build identity", "failed capture", "capture artifact membership/hash/path binding"]}))


def expect_rejection(fn, label):
    try:
        fn()
    except (ValueError, KeyError, TypeError):
        return
    raise ValueError("synthetic case was not rejected: " + label)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    root = args.root.resolve()
    output = args.output.resolve() if args.output else root / "analysis"
    require(not output.exists(), "output already exists; never overwrite a prior analysis")
    output.mkdir(parents=True)
    result = {"status": "NOT_ANALYZED", "analyzer_sha256": sha(__file__),
              "protocol_sha256": sha(Path(__file__).with_name("PROTOCOL.md")),
              "round_order": list(ROUNDS), "ROI_xyxy_original_pixels": list(ROI), "matrix_axes": ["output_RGB", "input_RGB"],
              "inset_bins": list(INSET_BINS), "primary_tolerance_raw_byte": 4, "all_tolerances_raw_byte": list(THRESHOLDS),
              "limits": LIMITS, "not_identified": UNIDENTIFIED,
              "interpretation": "conditional encoded-space finite-perturbation diagnostic; no optical acceptance, time fit, registration or native pipeline identification"}
    exit_code = 2
    try:
        frozen = load_freeze(root)
        result["freeze"] = {"path": frozen["path"], "sha256": frozen["sha256"],
                            "verified_current_file_count": frozen["verified_current_file_count"],
                            "prepared_native_files": frozen["value"]["prepared_native_files"],
                            "native_binaries": frozen["value"]["native_binaries"],
                            "simulator": frozen["value"]["simulator"]}
        sources = load_sources(root)
        loaded = {name: load_round(root, name, sources[name], frozen) for name in ROUNDS}
        require(all(v["operating"] == loaded["control-pre"]["operating"] for v in loaded.values()), "cross-round operating state differs")
        for field in ("verifier_sha256", "png_validator_sha256"):
            require(len({v["evidence"][field] for v in loaded.values()}) == 1, "cross-round verifier/validator identity differs")
        result["inputs"] = {k: v["evidence"] for k, v in loaded.items()}
        result["geometry"] = compare_geometry([v["geometries"][q] for v in loaded.values() for q in ("shape", "flat")])
        result["actual_carrier_bounds_pre_xywh"] = loaded["control-pre"]["geometries"]["shape"]["carrier_bounds"].tolist()
        result["operating_state"] = loaded["control-pre"]["operating"]
        analyze(loaded, output, result)
        exit_code = 0 if result["status"].startswith("OBSERVED_") else 2
    except (ValueError, KeyError, TypeError, OSError, StopIteration) as error:
        result["status"] = "REJECTED_REQUIRED_EVIDENCE_OR_COMPARABILITY"
        result["error"] = f"{type(error).__name__}: {error}"
    (output / "analysis.json").write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "analysis": str(output / "analysis.json")}, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
