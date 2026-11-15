#!/usr/bin/env python3
"""Exact finite signed-G observable diagnostic; no image decoding or fitting LP."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
T_VALUES = (1, 4, 8)
BRANCHES = tuple((ell, high) for ell in range(5) for high in range(ell, 5))
Z = np.arange(4, dtype=np.float64)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def slope_interval(lower, upper, count):
    """Eliminate intercept from lower <= a+m*z <= upper, with m >= 0."""
    mlo = np.zeros(count, dtype=np.float64)
    mhi = np.full(count, np.inf, dtype=np.float64)
    valid = np.ones(count, dtype=bool)
    for zl, vl in lower:
        for zu, vu in upper:
            dz = zu - zl
            rhs = vu - vl
            if dz > 0:
                mhi = np.minimum(mhi, rhs / dz)
            elif dz < 0:
                mlo = np.maximum(mlo, rhs / dz)
            else:
                valid &= rhs >= 0
    valid &= mlo <= mhi
    return valid, mlo, mhi


def branch_bounds(lo, hi, ell, high):
    """Return exact branch validity and bounds on latent affine observations."""
    count = len(lo)
    has_low, has_mid, has_high = ell > 0, high > ell, high < 4
    valid = np.ones(count, dtype=bool)
    lower = [(float(i), lo[:, i]) for i in range(ell, high)]
    upper = [(float(i), hi[:, i]) for i in range(ell, high)]
    floor_lo = floor_hi = ceiling_lo = ceiling_hi = None
    if has_low:
        floor_lo, floor_hi = lo[:, :ell].max(axis=1), hi[:, :ell].min(axis=1)
        valid &= floor_lo <= floor_hi
        upper.append((float(ell - 1), floor_hi))
        if has_mid:
            lower.append((float(ell), floor_lo))
    if has_high:
        ceiling_lo, ceiling_hi = lo[:, high:].max(axis=1), hi[:, high:].min(axis=1)
        valid &= ceiling_lo <= ceiling_hi
        lower.append((float(high), ceiling_lo))
        if has_mid:
            upper.append((float(high - 1), ceiling_hi))
    if has_low and has_high:
        valid &= floor_lo <= ceiling_hi
        if not has_mid:
            upper.append((float(ell - 1), ceiling_hi))
            lower.append((float(high), floor_lo))
    return valid, lower, upper, (floor_lo, floor_hi, ceiling_lo, ceiling_hi)


def feasibility(ordered, tolerance):
    """Observations are rows of four bytes ordered in expected increasing direction."""
    ordered = np.asarray(ordered, dtype=np.float64).reshape(-1, 4)
    lo = np.maximum(0, ordered - tolerance)
    hi = np.minimum(255, ordered + tolerance)
    count = len(ordered)
    monotonic = np.ones(count, dtype=bool)
    for earlier in range(4):
        for later in range(earlier + 1, 4):
            monotonic &= lo[:, earlier] <= hi[:, later]
    linear, line_mlo, line_mhi = slope_interval(
        [(float(i), lo[:, i]) for i in range(4)],
        [(float(i), hi[:, i]) for i in range(4)], count)
    clipped = np.zeros(count, dtype=bool)
    first = np.full(count, -1, dtype=np.int8)
    first_mlo = np.full(count, np.nan)
    first_mhi = np.full(count, np.nan)
    branch_count = np.zeros(count, dtype=np.uint8)
    for bi, (ell, high) in enumerate(BRANCHES):
        branch_valid, lower, upper, _ = branch_bounds(lo, hi, ell, high)
        possible, mlo, mhi = slope_interval(lower, upper, count)
        possible &= branch_valid
        fresh = possible & ~clipped
        first[fresh] = bi
        first_mlo[fresh], first_mhi[fresh] = mlo[fresh], mhi[fresh]
        branch_count += possible.astype(np.uint8)
        clipped |= possible
    if np.any(linear & ~clipped) or np.any(clipped & ~monotonic):
        raise AssertionError("Model inclusion violated; diagnostic cannot continue")
    return dict(linear=linear, clipped_affine=clipped, monotonic=monotonic,
                linear_mlo=line_mlo, linear_mhi=line_mhi, branch_index=first,
                branch_mlo=first_mlo, branch_mhi=first_mhi, branch_count=branch_count)


def reconstruct(ordered, tolerance, bi, m):
    """Independent evaluation of a first feasible branch's explicit witness."""
    ordered = np.asarray(ordered, dtype=np.float64).reshape(1, 4)
    lo, hi = np.maximum(0, ordered - tolerance), np.minimum(255, ordered + tolerance)
    ell, high = BRANCHES[int(bi)]
    valid, lower, upper, platforms = branch_bounds(lo, hi, ell, high)
    if not valid[0]:
        raise AssertionError("Invalid witness branch")
    a_lo = max((float(v[0]) - m * z for z, v in lower), default=-np.inf)
    a_hi = min((float(v[0]) - m * z for z, v in upper), default=np.inf)
    if a_lo > a_hi + 1e-10:
        raise AssertionError("Empty witness intercept interval")
    a = a_lo if np.isfinite(a_lo) else a_hi if np.isfinite(a_hi) else 0.0
    latent = a + m * Z
    floor_lo, _, _, ceiling_hi = platforms
    floor = max(float(floor_lo[0]), float(latent[:ell].max())) if ell else 0.0
    ceiling = min(float(ceiling_hi[0]), float(latent[high:].min())) if high < 4 else 255.0
    predicted = np.clip(latent, floor, ceiling)
    # This guard covers floating-point witness reconstruction only, never model acceptance.
    if floor > ceiling + 1e-10 or np.max(np.abs(predicted - ordered[0])) > tolerance + 1e-10:
        raise AssertionError("Constructed witness fails direct clipped evaluation")
    return dict(intercept=a, slope_per_step=m, floor=floor, ceiling=ceiling,
                predicted=predicted.tolist())


def self_test():
    checks = []
    cases = (
        ("linear", [10, 20, 30, 40], (True, True, True)),
        ("low_platform", [10, 10, 20, 30], (False, True, True)),
        ("high_platform", [10, 20, 30, 30], (False, True, True)),
        ("empty_sampled_middle", [10, 10, 30, 30], (False, True, True)),
        ("constant", [42, 42, 42, 42], (True, True, True)),
        ("monotone_not_clipped_affine", [0, 2, 3, 5], (False, False, True)),
        ("nonmonotonic", [0, 20, 10, 30], (False, False, False)),
    )
    model_names = ("linear", "clipped_affine", "monotonic")
    for name, values, expected in cases:
        result = feasibility([values], 0)
        actual = tuple(bool(result[k][0]) for k in model_names)
        if actual != expected:
            raise AssertionError((name, actual, expected))
        if result["clipped_affine"][0]:
            reconstruct(values, 0, result["branch_index"][0], result["branch_mlo"][0])
        checks.append(name)
    # Already reported native sample, and toy-model negative-G extrapolations.
    # R/B are reversed to put their expected nonincreasing t response in ascending u order.
    counterexample = np.array([[6, 6, 15, 25], [87, 87, 100, 114], [87, 96, 106, 114]])
    result = feasibility(counterexample, 1)
    if not np.all(result["clipped_affine"]):
        raise AssertionError("Documented clamp counterexample not represented")
    checks.append("reported_counterexample_plus_unobserved_toy_negative_steps")
    # Exhaust all small four-endpoint records; every claimed feasible branch gets
    # a direct witness evaluated by np.clip, independent of the interval comparisons.
    exhaustive = np.array(list(itertools.product(range(6), repeat=4)), dtype=np.float64)
    for tolerance in (0, 1):
        result = feasibility(exhaustive, tolerance)
        for index in np.flatnonzero(result["clipped_affine"]):
            reconstruct(exhaustive[index], tolerance, result["branch_index"][index],
                        result["branch_mlo"][index])
    checks.append("1296_records_direct_witness_at_T0_T1")
    rng = np.random.default_rng(20261116)
    # Known true clipped-affine records with integer latent parameters and exact bytes.
    count = 2000
    floor = rng.integers(0, 220, size=count)
    ceiling = np.array([rng.integers(v, 256) for v in floor])
    intercept = rng.integers(-600, 601, size=count)
    slope = rng.integers(0, 601, size=count)
    generated = np.clip(intercept[:, None] + slope[:, None] * Z,
                        floor[:, None], ceiling[:, None])
    if not np.all(feasibility(generated, 0)["clipped_affine"]):
        raise AssertionError("Known generated clipped-affine record rejected")
    checks.append("2000_generated_clipped_records_exact")
    records = rng.integers(0, 256, size=(2000, 4))
    previous = None
    for tolerance in T_VALUES:
        result = feasibility(records, tolerance)
        if previous is not None:
            for model in model_names:
                if np.any(previous[model] & ~result[model]):
                    raise AssertionError("Endpoint-tolerance nesting failed")
        for index in np.flatnonzero(result["clipped_affine"]):
            reconstruct(records[index], tolerance, result["branch_index"][index],
                        result["branch_mlo"][index])
        previous = result
    checks.append("2000_random_records_T1_T4_T8_nesting_and_witnesses")
    return dict(status="PASS", seed=20261116, checks=checks,
                original_or_new_output_pixels_loaded=False,
                acceptance_float_epsilon=0,
                reconstruction_guard_only=1e-10)


def grid(value, axis):
    value = np.asarray(value, dtype=np.float64)
    if value.shape == (88, 88):
        return value
    if value.shape == (88,):
        return np.broadcast_to(value[None, :] if axis == "x" else value[:, None], (88, 88)).copy()
    raise ValueError(f"{axis} must have shape (88,) or (88,88)")


def masks_for(x, y, inset):
    above = y < 422
    masks = dict(full=np.ones_like(above), primary=above & (inset >= 1),
                 above_rail=above, rail_band=(y >= 422) & (y < 438), below_rail=y >= 438,
                 outside_carrier=inset < 0)
    for label, left, right in (("0_1", 0, 1), ("1_3", 1, 3), ("3_8", 3, 8),
                               ("8_plus", 8, np.inf)):
        member = (inset >= left) & (inset < right)
        masks[f"inset_{label}"] = member
        masks[f"above_rail_inset_{label}"] = above & member
    return masks


def analyze(path, out, tested):
    path = Path(path).resolve()
    if path.name != "signed-output.npz":
        raise ValueError("Only the collector's signed-output.npz is accepted")
    with np.load(path, allow_pickle=False) as source:
        required = {"t", "output_rgb", "x", "y", "inset"}
        if not required.issubset(source.files):
            raise ValueError(f"Missing required keys: {required - set(source.files)}")
        t, output = source["t"].copy(), source["output_rgb"].copy()
        x, y = grid(source["x"], "x"), grid(source["y"], "y")
        inset = np.asarray(source["inset"], dtype=np.float64).copy()
    if not np.array_equal(t, [-40, -20, 0, 20]) or output.shape != (4, 88, 88, 3):
        raise ValueError("Unexpected signed-G schedule or output shape")
    if output.dtype != np.uint8 or inset.shape != (88, 88):
        raise ValueError("Unexpected output dtype or inset shape")
    if not all(np.all(np.isfinite(a)) for a in (x, y, inset)):
        raise ValueError("Nonfinite coordinate/inset")
    expected_x = (np.arange(331, 419) + .5) / 2
    expected_y = (np.arange(795, 883) + .5) / 2
    if not np.array_equal(x, np.broadcast_to(expected_x, (88, 88))) or not np.array_equal(
            y, np.broadcast_to(expected_y[:, None], (88, 88))):
        raise ValueError("Coordinates differ from fixed original-pixel ROI")
    masks = masks_for(x, y, inset)
    names = ("linear", "clipped_affine", "monotonic")
    channels = ("R", "G", "B")
    store = {}
    results = {}
    for tolerance in T_VALUES:
        fit = {}
        for ci, channel in enumerate(channels):
            values = output[:, :, :, ci].reshape(4, -1).T
            if channel != "G":
                values = values[:, ::-1]
            fit[channel] = feasibility(values, tolerance)
        summary = {}
        for domain, mask in masks.items():
            flat = mask.ravel()
            row = dict(pixels=int(flat.sum()), channels={})
            for channel in channels:
                row["channels"][channel] = {
                    model: dict(compatible=int(fit[channel][model][flat].sum()),
                                incompatible=int((~fit[channel][model][flat]).sum()))
                    for model in names}
            row["any_RGB_incompatible"] = {
                model: int(np.any(np.stack([~fit[c][model] for c in channels]), axis=0)[flat].sum())
                for model in names}
            summary[domain] = row
        results[str(tolerance)] = summary
        for model in names:
            store[f"T{tolerance}_{model}_compatible"] = np.stack(
                [fit[c][model].reshape(88, 88) for c in channels], axis=-1)
        for field in ("branch_index", "branch_count", "branch_mlo", "branch_mhi"):
            store[f"T{tolerance}_{field}"] = np.stack(
                [fit[c][field].reshape(88, 88) for c in channels], axis=-1)
    out.mkdir(parents=True, exist_ok=True)
    array_path = out / "signed-analysis.npz"
    np.savez_compressed(array_path, **store)
    report = dict(
        status="CONDITIONAL_FINITE_SIGNED_G_OBSERVABLE_DIAGNOSTIC_NOT_PIPELINE_IDENTIFICATION",
        script_sha256=digest(__file__), input_sha256=digest(path), input=str(path),
        array_sha256=digest(array_path), self_test=tested,
        endpoint_tolerances_bytes=list(T_VALUES),
        endpoint_interval="[max(0,byte-T),min(255,byte+T)]; no additional half-byte",
        t=t.tolist(), expected_output_sign=dict(R="nonincreasing", G="nondecreasing", B="nonincreasing"),
        branch_table=[dict(index=i, low_count=a, high_start=b) for i, (a, b) in enumerate(BRANCHES)],
        slope_storage="m per 20 input bytes, in increasing u; first feasible branch only, not union bounds",
        masks="Fixed public-carrier inset approximation; not optical alpha; above y<422, rail422..438",
        collection_gate_limit="NPZ contains no repeated controls; root collector must verify pre/post and old/new original byte identity before emission. Analyzer does not assert those outcomes.",
        inference_limit="Per-output/pixel independent parameters; compatibility is not shared saturation proof. Encoded clipped-affine rejection does not reject linear-light clamp plus transfer or arbitrary monotonic pipelines.",
        results=results)
    (out / "analysis.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(dict(status=report["status"], report=str(out / "analysis.json"),
                          primary={t: results[t]["primary"] for t in results}), indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--input", type=Path)
    parser.add_argument("--out", type=Path, default=HERE / "signed-results")
    args = parser.parse_args()
    tested = self_test()  # Always before loading the sole observation file.
    tested["script_sha256"] = digest(__file__)
    if args.self_test:
        receipt = HERE / "self-test.json"
        receipt.write_text(json.dumps(tested, indent=2) + "\n")
        print(json.dumps(tested, indent=2))
        if args.input is None:
            return
    if args.input is None:
        parser.error("Use --self-test or supply the collector's --input signed-output.npz")
    out = args.out.resolve()
    if not out.is_relative_to(HERE):
        parser.error("Outputs must remain within this diagnostic's owned directory")
    analyze(args.input, out, tested)


if __name__ == "__main__":
    main()
