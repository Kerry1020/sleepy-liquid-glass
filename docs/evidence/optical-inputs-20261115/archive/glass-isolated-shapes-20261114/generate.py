#!/usr/bin/env python3
"""Frozen source-only isolated shape/control pairs; no capture inputs."""

import argparse
import hashlib
import json
import math
import platform
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import PIL
from PIL import Image, ImageDraw, features


ROOT = Path(__file__).resolve().parent
PROTOCOL = ROOT / "protocol.json"
FREEZE = ROOT / "freeze.json"
PROFILE = ROOT / "sRGB.icc"
FROZEN_NAMES = ("protocol.json", "generate.py", "README.md", "sRGB.icc")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    return sha(path.read_bytes())


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def dependencies():
    return {"python": platform.python_version(), "numpy": np.__version__,
            "pillow": PIL.__version__, "littlecms2": features.version("littlecms2")}


def file_hashes():
    return {name: sha_file(ROOT / name) for name in FROZEN_NAMES}


def check_protocol(p):
    assert p["schema"] == 1
    assert p["world"]["dimensions_px"] == [750, 1334]
    assert p["world"]["pixels_per_pt"] == 2
    assert p["rasterization"]["antialias_samples_per_axis"] == 4
    assert p["pair_contract"]["pairs_per_split"] == 4
    assert len(p["cases"]) == 4
    assert {c["family"] for c in p["cases"]} == {"circle", "triangle", "star", "asymmetric"}
    seeds = [s for split in p["splits"].values() for s in split["pair_seeds"]]
    assert len(seeds) == len(set(seeds)) == 8
    assert all(len(s["pair_seeds"]) == 4 for s in p["splits"].values())


def freeze(p):
    check_protocol(p)
    assert PROFILE.exists(), "Copy the intended ICC profile before freeze."
    assert not FREEZE.exists(), "Existing freeze must be preserved, never overwritten."
    write_json(FREEZE, {"schema": 1, "protocol_id": p["protocol_id"],
                       "frozen_utc": datetime.now(timezone.utc).isoformat(),
                       "file_sha256": file_hashes(), "dependencies": dependencies(),
                       "before_registered_generation": True,
                       "statement": "Source protocol/generator frozen before this packet's PNG generation. No new actual capture used to choose parameters; prior pilot explicitly informs design."})


def check_freeze(p):
    check_protocol(p)
    f = json.loads(FREEZE.read_text())
    assert f["protocol_id"] == p["protocol_id"]
    assert f["file_sha256"] == file_hashes(), "Frozen source/profile changed."
    assert f["dependencies"] == dependencies(), "Frozen dependencies changed."
    assert f["before_registered_generation"] is True


def geometry(p, split_name, index):
    case = p["cases"][index]
    seed = p["splits"][split_name]["pair_seeds"][index]
    center = np.array(case["anchor_center_px"], dtype=np.float64)
    radius = case["calibration_radius_px"]
    palette = np.array([p["palette_rgb"][(j + case["palette_roll"]) % 3]
                        for j in range(3)], dtype=np.int16)
    draws = {"dx_px": 0, "dy_px": 0, "radius_px": radius,
             "rgb_perturbations": [[0, 0, 0]] * 3, "rng_drawn": False}
    if split_name == "test":
        variation = p["test_variation"]
        rng = np.random.Generator(np.random.PCG64(seed))
        d0, d1 = variation["dx_dy_inclusive_px"]
        dx = int(rng.integers(d0, d1 + 1))
        dy = int(rng.integers(d0, d1 + 1))
        r0, r1 = variation["radius_inclusive_px"]
        radius = int(rng.integers(r0, r1 + 1))
        c0, c1 = variation["rgb_per_channel_perturbation_inclusive"]
        jitter = rng.integers(c0, c1 + 1, size=(3, 3))
        center += [dx, dy]
        palette += jitter
        draws = {"dx_px": dx, "dy_px": dy, "radius_px": radius,
                 "rgb_perturbations": jitter.tolist(), "rng_drawn": True}
        color_lo, color_hi = variation["color_result_bounds"]
        assert color_lo <= int(palette.min()) <= int(palette.max()) <= color_hi
    family = case["family"]
    if family == "circle":
        relative = None
    elif family in ("triangle", "star"):
        n = 3 if family == "triangle" else 10
        angles = -math.pi / 2 + np.arange(n) * 2 * math.pi / n
        radii = np.ones(n)
        if family == "star":
            radii[1::2] = 0.45
        relative = np.column_stack((np.cos(angles), np.sin(angles))) * radii[:, None]
    else:
        relative = np.array(p["rasterization"]["asymmetric_normalized_vertices_before_unit_radius_normalization"], dtype=np.float64)
        relative /= np.linalg.norm(relative, axis=1).max()
    vertices = None if relative is None else relative * radius + center
    w, h = p["world"]["dimensions_px"]
    assert min(center[0] - radius, center[1] - radius) > 0
    assert center[0] + radius < w and center[1] + radius < h
    return {"case_id": case["id"], "family": family, "target": case["target"],
            "seed": seed, "draws": draws, "anchor_center_px": case["anchor_center_px"],
            "center_px": center.tolist(), "center_pt": (center / 2).tolist(),
            "circumradius_px": radius, "circumradius_pt": radius / 2,
            "vertices_px": None if vertices is None else vertices.tolist(),
            "vertices_pt": None if vertices is None else (vertices / 2).tolist(),
            "rgb_by_band": palette.tolist(), "orientation_rad": -math.pi / 2 if family in ("triangle", "star") else None}


def polygon_inside(xs, ys, vertices):
    inside = np.zeros(np.broadcast_shapes(xs.shape, ys.shape), dtype=bool)
    previous = vertices[-1]
    for current in vertices:
        x0, y0 = previous
        x1, y1 = current
        if y0 != y1:
            crossing = ((y0 > ys) != (y1 > ys))
            x_crossing = x0 + (ys - y0) * (x1 - x0) / (y1 - y0)
            inside ^= crossing & (xs < x_crossing)
        previous = current
    return inside


def band_coverage(p, g):
    w, h = p["world"]["dimensions_px"]
    aa = p["rasterization"]["antialias_samples_per_axis"]
    cx, cy = g["center_px"]
    r = g["circumradius_px"]
    x0 = max(0, math.floor(cx - r))
    y0 = max(0, math.floor(cy - r))
    x1 = min(w, math.ceil(cx + r))
    y1 = min(h, math.ceil(cy + r))
    xs = x0 + (np.arange((x1 - x0) * aa) + 0.5) / aa
    ys = y0 + (np.arange((y1 - y0) * aa) + 0.5) / aa
    xx, yy = xs[None, :], ys[:, None]
    if g["family"] == "circle":
        inside = (xx - cx) ** 2 + (yy - cy) ** 2 <= r ** 2
    else:
        inside = polygon_inside(xx, yy, np.asarray(g["vertices_px"]))
    band_index = np.where(xx - cx < -r / 4, 0, np.where(xx - cx < r / 4, 1, 2))
    coverage = []
    for band in range(3):
        samples = inside & (band_index == band)
        counts = samples.reshape(y1 - y0, aa, x1 - x0, aa).sum(axis=(1, 3)).astype(np.uint8)
        coverage.append(counts)
    counts = np.stack(coverage)
    assert int(counts.sum(axis=0).max()) <= aa * aa
    return [x0, y0, x1, y1], counts


def coverage_rle(box, counts):
    x0, y0, _, _ = box
    # Each row stores exactly its nonzero span; interior zero samples remain.
    bands = []
    for band in counts:
        rows = []
        for row_index, row in enumerate(band):
            nonzero = np.flatnonzero(row)
            if nonzero.size:
                left, right = int(nonzero[0]), int(nonzero[-1]) + 1
                rows.append({"y": y0 + row_index, "x_start": x0 + left,
                             "counts": row[left:right].tolist()})
        bands.append(rows)
    return {"encoding": "one nonzero-span run per nonempty row and color band; counts include any internal zeros",
            "denominator": 16, "bbox_ltrb_px": box, "band_rows": bands}


def decode_coverage(table):
    x0, y0, x1, y1 = table["bbox_ltrb_px"]
    counts = np.zeros((3, y1 - y0, x1 - x0), dtype=np.uint8)
    assert table["denominator"] == 16
    for band, rows in enumerate(table["band_rows"]):
        seen_y = set()
        for row in rows:
            assert row["y"] not in seen_y
            seen_y.add(row["y"])
            y, x = row["y"] - y0, row["x_start"] - x0
            values = np.array(row["counts"], dtype=np.uint8)
            assert 0 <= y < y1 - y0 and 0 <= x < x1 - x0
            assert x + len(values) <= x1 - x0 and int(values.max()) <= 16
            counts[band, y, x:x + len(values)] = values
    assert int(counts.sum(axis=0).max()) <= 16
    return counts


def compose(p, g, box, counts):
    w, h = p["world"]["dimensions_px"]
    background = np.array(p["world"]["background_rgb"], dtype=np.int32)
    pixels = np.empty((h, w, 3), dtype=np.uint8)
    pixels[:] = background
    x0, y0, x1, y1 = box
    total_coverage = counts.astype(np.int32).sum(axis=0)
    sums = (16 - total_coverage)[:, :, None] * background
    for band, rgb in enumerate(g["rgb_by_band"]):
        sums += counts[band, :, :, None].astype(np.int32) * np.array(rgb, dtype=np.int32)
    pixels[y0:y1, x0:x1] = ((sums + 8) // 16).astype(np.uint8)
    return pixels


def moments(box, counts):
    x0, y0, x1, y1 = box
    weight = counts.sum(axis=0).astype(np.float64) / 16
    xx, yy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
    area = float(weight.sum())
    assert area > 0
    centroid = np.array([(weight * xx).sum(), (weight * yy).sum()]) / area
    dx, dy = xx - centroid[0], yy - centroid[1]
    covariance = np.array([[(weight * dx * dx).sum(), (weight * dx * dy).sum()],
                           [(weight * dx * dy).sum(), (weight * dy * dy).sum()]]) / area
    return {"coverage_area_px2": area, "coverage_area_pt2": area / 4,
            "nonzero_coverage_pixel_count": int(np.count_nonzero(weight)),
            "per_band_coverage_area_px2": (counts.astype(np.int32).sum(axis=(1, 2)) / 16).tolist(),
            "pixel_center_centroid_px": centroid.tolist(),
            "pixel_center_covariance_px2": covariance.tolist(),
            "moment_scope": "coverage-weighted output pixel centers; not continuum or native-response moments"}


def png_bytes(path, pixels):
    Image.fromarray(pixels, mode="RGB").save(path, format="PNG", icc_profile=PROFILE.read_bytes(),
                                            optimize=False, compress_level=9)


def atlas(p, manifests):
    tile = 260
    row_height = 314
    image = Image.new("RGB", (4 * tile, 50 + len(p["cases"]) * row_height), "white")
    draw = ImageDraw.Draw(image)
    headers = ["calibration control", "calibration shape", "test control", "test shape"]
    for col, header in enumerate(headers):
        draw.text((col * tile + 12, 12), header, fill="black")
    for row, case in enumerate(p["cases"]):
        ax, ay = case["anchor_center_px"]
        x0 = min(max(math.floor(ax - 60), 0), 750 - 120)
        y0 = min(max(math.floor(ay - 60), 0), 1334 - 120)
        crop = (x0, y0, x0 + 120, y0 + 120)
        for col, (split_name, role) in enumerate((("calibration", "control"), ("calibration", "shape"), ("test", "control"), ("test", "shape"))):
            entry = next(e for e in manifests[split_name]["inputs"] if e["case_id"] == case["id"] and e["role"] == role)
            with Image.open(ROOT / split_name / entry["file"]) as source:
                enlarged = source.crop(crop).resize((240, 240), Image.Resampling.NEAREST)
            left, top = col * tile + 10, 50 + row * row_height
            image.paste(enlarged, (left, top))
            draw.text((left, top + 245), case["id"] + " / " + role, fill="black")
            draw.text((left, top + 262), "source crop " + str(crop), fill="black")
            draw.text((left, top + 279), "2x nearest; no capture", fill="black")
    image.save(ROOT / "input-atlas.png", format="PNG", icc_profile=PROFILE.read_bytes(), optimize=False, compress_level=9)


def generate(p):
    check_freeze(p)
    w, h = p["world"]["dimensions_px"]
    control = np.full((h, w, 3), p["world"]["background_rgb"], dtype=np.uint8)
    manifests = {}
    for split_name, split in p["splits"].items():
        directory = ROOT / split_name
        directory.mkdir(exist_ok=True)
        manifest = {"schema": 1, "set_id": split["set_id"], "split": split["manifest_split"],
                    "protocol_id": p["protocol_id"], "protocol_sha256": sha_file(PROTOCOL),
                    "freeze_sha256": sha_file(FREEZE), "dimensions_px": [w, h],
                    "color_space": "sRGB", "opaque": True,
                    "icc_profile_sha256": sha_file(PROFILE), "inputs": []}
        for index, case in enumerate(p["cases"]):
            g = geometry(p, split_name, index)
            pair_id = "%s%02d_%s" % (split["pair_prefix"], index + 1, case["id"])
            box, counts = band_coverage(p, g)
            shape = compose(p, g, box, counts)
            records = []
            for role, pixels in (("control", control), ("shape", shape)):
                input_id = pair_id + "_" + role
                path = directory / (input_id + ".png")
                png_bytes(path, pixels)
                records.append({"id": input_id, "file": path.name, "sha256": sha_file(path),
                                "pixel_sha256": sha(pixels.tobytes()), "role": role,
                                "pair_id": pair_id, "case_id": case["id"], "seed": g["seed"],
                                "kind": "isolated_shape_" + role,
                                "width": w, "height": h, "mode": "RGB"})
            metadata_path = directory / (pair_id + ".geometry.json")
            metadata = {"schema": 1, "protocol_id": p["protocol_id"], "pair_id": pair_id,
                        "split": split["manifest_split"], "source_id": pair_id + "_object_000001",
                        "geometry": g, "coordinate_system": p["world"],
                        "color_bands": {"local_u_boundaries_px": [-g["circumradius_px"] / 4, g["circumradius_px"] / 4],
                                        "world_x_boundaries_px": [g["center_px"][0] - g["circumradius_px"] / 4,
                                                                   g["center_px"][0] + g["circumradius_px"] / 4],
                                        "rgb_by_band": g["rgb_by_band"]},
                        "analytic_circle": {"center_px": g["center_px"], "radius_px": g["circumradius_px"]} if g["family"] == "circle" else None,
                        "coverage_mask": coverage_rle(box, counts),
                        "source_measurements": moments(box, counts),
                        "inputs": [{k: r[k] for k in ("id", "role", "file", "sha256", "pixel_sha256")} for r in records],
                        "generation_failure": None}
            write_json(metadata_path, metadata)
            for record in records:
                record.update({"geometry_file": metadata_path.name, "geometry_sha256": sha_file(metadata_path)})
                manifest["inputs"].append(record)
        write_json(directory / "manifest.json", manifest)
        manifests[split_name] = manifest
    atlas(p, manifests)
    write_json(ROOT / "generation-report.json", {"schema": 1, "generated_utc": datetime.now(timezone.utc).isoformat(),
                                               "protocol_sha256": sha_file(PROTOCOL), "freeze_sha256": sha_file(FREEZE),
                                               "fixture_png_count": 16, "pair_metadata_count": 8,
                                               "manifest_sha256": {s: sha_file(ROOT / s / "manifest.json") for s in manifests},
                                               "atlas_sha256": sha_file(ROOT / "input-atlas.png"),
                                               "captures": 0, "product_changes": 0})


def verify(p):
    check_freeze(p)
    profile = PROFILE.read_bytes()
    w, h = p["world"]["dimensions_px"]
    controls, seen_ids, details = set(), set(), []
    for split_name, split in p["splits"].items():
        directory = ROOT / split_name
        manifest = json.loads((directory / "manifest.json").read_text())
        assert manifest["schema"] == 1 and manifest["split"] == split["manifest_split"]
        assert manifest["protocol_sha256"] == sha_file(PROTOCOL)
        assert manifest["freeze_sha256"] == sha_file(FREEZE)
        assert manifest["icc_profile_sha256"] == sha(profile)
        assert len(manifest["inputs"]) == 8
        for index, case in enumerate(p["cases"]):
            expected_g = geometry(p, split_name, index)
            expected_box, expected_counts = band_coverage(p, expected_g)
            pair_id = "%s%02d_%s" % (split["pair_prefix"], index + 1, case["id"])
            metadata_path = directory / (pair_id + ".geometry.json")
            metadata = json.loads(metadata_path.read_text())
            assert metadata["pair_id"] == pair_id and metadata["geometry"] == expected_g
            assert metadata["generation_failure"] is None
            decoded = decode_coverage(metadata["coverage_mask"])
            assert metadata["coverage_mask"]["bbox_ltrb_px"] == expected_box
            assert np.array_equal(decoded, expected_counts)
            assert metadata["source_measurements"] == moments(expected_box, decoded)
            reconstructed = compose(p, expected_g, expected_box, decoded)
            control = np.full((h, w, 3), p["world"]["background_rgb"], dtype=np.uint8)
            records = [r for r in manifest["inputs"] if r["pair_id"] == pair_id]
            assert {r["role"] for r in records} == {"control", "shape"} and len(records) == 2
            for record in records:
                assert record["id"] == pair_id + "_" + record["role"]
                assert record["id"] not in seen_ids
                seen_ids.add(record["id"])
                assert record["seed"] == expected_g["seed"]
                assert record["geometry_sha256"] == sha_file(metadata_path)
                assert record["geometry_file"] == metadata_path.name
                path = directory / record["file"]
                assert record["sha256"] == sha_file(path)
                with Image.open(path) as image:
                    assert image.mode == "RGB" and image.size == (w, h)
                    assert image.info.get("icc_profile") == profile
                    pixels = np.asarray(image)
                    assert sha(pixels.tobytes()) == record["pixel_sha256"]
                    assert np.array_equal(pixels, control if record["role"] == "control" else reconstructed)
                metadata_input = next(r for r in metadata["inputs"] if r["role"] == record["role"])
                assert all(metadata_input[k] == record[k] for k in ("id", "role", "file", "sha256", "pixel_sha256"))
                if record["role"] == "control":
                    controls.add(record["sha256"])
            details.append({"pair_id": pair_id, "center_px": expected_g["center_px"],
                            "radius_px": expected_g["circumradius_px"], "coverage_area_px2": metadata["source_measurements"]["coverage_area_px2"],
                            "metadata_sha256": sha_file(metadata_path)})
    assert len(seen_ids) == 16 and len(controls) == 1
    report = {"schema": 1, "verified_utc": datetime.now(timezone.utc).isoformat(),
              "protocol_sha256": sha_file(PROTOCOL), "freeze_sha256": sha_file(FREEZE),
              "manifest_sha256": {s: sha_file(ROOT / s / "manifest.json") for s in p["splits"]},
              "input_pngs": 16, "pairs": 8, "byte_identical_controls": 8,
              "control_sha256": next(iter(controls)),
              "coverage_reconstruction": "all pixels of16 inputs checked; all8 shape masks match fresh frozen geometry rasterization",
              "atlas_sha256": sha_file(ROOT / "input-atlas.png"),
              "capture_or_optical_validation_claimed": False, "passed": True, "pair_details": details}
    write_json(ROOT / "verification-report.json", report)
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--freeze", action="store_true")
    action.add_argument("--generate", action="store_true")
    action.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    p = json.loads(PROTOCOL.read_text())
    if args.freeze:
        freeze(p)
    elif args.generate:
        generate(p)
    else:
        verify(p)


if __name__ == "__main__":
    main()
