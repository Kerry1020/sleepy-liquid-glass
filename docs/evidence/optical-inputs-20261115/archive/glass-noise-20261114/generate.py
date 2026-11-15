#!/usr/bin/env python3
"""Precommitted source stimuli; no screenshot input or device dependency."""

import argparse
import csv
import hashlib
import io
import json
import math
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import PIL
from PIL import Image, ImageCms, features

ROOT = Path(__file__).resolve().parent
PROTOCOL = ROOT / "protocol.json"
FREEZE = ROOT / "freeze.json"
PROFILE = ROOT / "sRGB.icc"


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    return sha_bytes(path.read_bytes())


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def dependencies():
    return {"python": platform.python_version(), "numpy": np.__version__,
            "pillow": PIL.__version__, "littlecms2": features.version("littlecms2")}


def frozen_files():
    return {name: sha_file(ROOT / name) for name in
            ("protocol.json", "generate.py", "README.md", "sRGB.icc")}


def check_protocol(p):
    assert p["schema"] == 1
    assert p["dimensions_px"] == [750, 1334]
    assert p["px_per_pt"] == 2
    entries = [v for split in p["splits"].values() for v in split["inputs"]]
    assert len(entries) == 16
    assert len({x["seed"] for x in entries}) == 16
    assert len({x["id"] for x in entries}) == 16
    for split in p["splits"].values():
        assert len(split["inputs"]) == 8
        assert [x["kind"] for x in split["inputs"]].count("dots") == 4
        assert [x["kind"] for x in split["inputs"]].count("rgb_noise") == 4


def freeze(p):
    check_protocol(p)
    assert not FREEZE.exists(), "Freeze already exists; do not replace a registered protocol."
    if not PROFILE.exists():
        PROFILE.write_bytes(ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes())
    write_json(FREEZE, {"schema": 1, "protocol_id": p["protocol_id"],
                       "frozen_utc": datetime.now(timezone.utc).isoformat(),
                       "file_sha256": frozen_files(), "dependencies": dependencies(),
                       "generation_started": False,
                       "statement": "Frozen before registered calibration/test PNG generation; no native or Android capture consumed."})


def check_freeze(p):
    check_protocol(p)
    f = json.loads(FREEZE.read_text())
    assert f["protocol_id"] == p["protocol_id"]
    assert f["file_sha256"] == frozen_files(), "Frozen source/profile changed."
    assert f["dependencies"] == dependencies(), "Use frozen dependency versions."
    return f


def gaussian_field(rng, h, w, sigma):
    # A real-space N(0,1) field filtered by the exactly declared periodic kernel.
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    transfer = np.exp(-2 * math.pi ** 2 * sigma ** 2 * (fx * fx + fy * fy))
    transfer[0, 0] = 0.0
    expected_gain = math.sqrt(float(np.mean(transfer * transfer)))
    white = rng.standard_normal((h, w))
    return np.fft.ifft2(np.fft.fft2(white) * transfer).real / expected_gain


def noise_pixels(p, entry):
    w, h = p["dimensions_px"]
    rng = np.random.Generator(np.random.PCG64(entry["seed"]))
    out = np.full((h, w, 3), 128.0, dtype=np.float64)
    correlation = p["noise"]["expected_rgb_channel_correlation"]
    for scale in p["noise"]["scales"]:
        shared = gaussian_field(rng, h, w, scale["gaussian_sigma_px"])
        for channel in range(3):
            independent = gaussian_field(rng, h, w, scale["gaussian_sigma_px"])
            out[:, :, channel] += scale["expected_channel_std_code"] * (
                math.sqrt(correlation) * shared + math.sqrt(1 - correlation) * independent)
    return np.rint(np.clip(out, 0, 255)).astype(np.uint8), None


def dots_pixels(p, entry):
    w, h = p["dimensions_px"]
    ratio = p["px_per_pt"]
    rng = np.random.Generator(np.random.PCG64(entry["seed"]))
    palette = p["dots"]["palette_rgb"]
    dots = []
    for scale in p["dots"]["scales_in_draw_order"]:
        positions = rng.uniform([0.0, 0.0], [float(w), float(h)], size=(scale["count"], 2))
        color_indices = rng.permutation(np.arange(scale["count"]) % len(palette))
        radius = scale["radius_px"]
        for (x, y), color_index in zip(positions, color_indices):
            rgb = palette[int(color_index)]
            code_luma = float(np.dot(rgb, [0.2126, 0.7152, 0.0722]))
            dots.append({"id": entry["id"] + "_dot_%06d" % (len(dots) + 1),
                         "source_x_px": float(x), "source_y_px": float(y),
                         "source_x_pt": float(x / ratio), "source_y_pt": float(y / ratio),
                         "rgb": rgb, "polarity": "light" if code_luma > 128 else "dark",
                         "source_code_luma": code_luma,
                         "radius_px": radius, "radius_pt": radius / ratio,
                         "sigma_px": None, "seed": entry["seed"],
                         "scale": scale["name"], "draw_order": len(dots),
                         "edge_clipped": bool(min(x, y, w - x, h - y) < radius)})
    assert len(dots) == p["dots"]["total_per_image"]
    antialias = p["dots"]["antialias_samples_per_axis"]
    # Every high-resolution sample is at an exactly known subpixel center.
    raster = np.full((h * antialias, w * antialias, 3), 128, dtype=np.uint8)
    for dot in dots:
        x, y, r = dot["source_x_px"], dot["source_y_px"], dot["radius_px"]
        x0 = max(0, int(math.floor((x - r) * antialias)))
        x1 = min(w * antialias, int(math.ceil((x + r) * antialias)))
        y0 = max(0, int(math.floor((y - r) * antialias)))
        y1 = min(h * antialias, int(math.ceil((y + r) * antialias)))
        xs = (np.arange(x0, x1) + 0.5) / antialias
        ys = (np.arange(y0, y1) + 0.5) / antialias
        member = (xs[None, :] - x) ** 2 + (ys[:, None] - y) ** 2 <= r ** 2
        raster[y0:y1, x0:x1][member] = dot["rgb"]
    pixels = np.asarray(Image.fromarray(raster, mode="RGB").resize((w, h), Image.Resampling.BOX)).copy()
    del raster

    coords = np.array([[d["source_x_px"], d["source_y_px"]] for d in dots])
    radii = np.array([d["radius_px"] for d in dots])
    neighborhood = p["dots"]["source_neighborhood"]
    signature_counts = {}
    for i, dot in enumerate(dots):
        delta = coords - coords[i]
        distance = np.linalg.norm(delta, axis=1)
        others = np.arange(len(dots)) != i
        overlaps = np.flatnonzero(others & (distance < radii + radii[i]))
        nearby = np.flatnonzero(others & (distance <= neighborhood["radius_px"]))
        dot["overlapping_dot_ids"] = [dots[j]["id"] for j in overlaps]
        dot["occluding_later_dot_ids"] = [dots[j]["id"] for j in overlaps if j > i]
        dot["nearest_source_neighbor_ids"] = [dots[j]["id"] for j in
            np.argsort(distance, kind="stable")[1:1 + neighborhood["nearest_source_neighbors"]]]
        descriptor = sorted([[int(np.rint(delta[j, 0] / neighborhood["relative_coordinate_quantization_px"])),
                              int(np.rint(delta[j, 1] / neighborhood["relative_coordinate_quantization_px"])),
                              dots[j]["scale"], dots[j]["rgb"]] for j in nearby])
        dot["source_neighborhood_count"] = len(nearby)
        signature = sha_bytes(json.dumps(descriptor, separators=(",", ":")).encode())
        dot["source_neighborhood_signature"] = signature
        signature_counts[signature] = signature_counts.get(signature, 0) + 1
        dot["final_source_center_pixel_rgb"] = pixels[int(math.floor(dot["source_y_px"])),
                                                      int(math.floor(dot["source_x_px"]))].tolist()
    for dot in dots:
        dot["source_neighborhood_signature_multiplicity"] = signature_counts[dot["source_neighborhood_signature"]]
    point_data = {"schema": 1, "input_id": entry["id"], "seed": entry["seed"],
                  "coordinate_system": {"source_px": [w, h], "logical_pt": p["logical_dimensions_pt"],
                                        "px_per_pt": ratio, "origin": "top-left image edge",
                                        "pixel_centers": "integer index + 0.5"},
                  "background_rgb": p["background_rgb"], "point_count": len(dots),
                  "shape": p["dots"]["shape"], "neighborhood": neighborhood,
                  "source_signature_duplicate_point_count": sum(v for v in signature_counts.values() if v > 1),
                  "source_signature_uniqueness_is_not_target_matchability": True,
                  "dots": dots}
    return pixels, point_data


def csv_points(path, point_data):
    fields = list(point_data["dots"][0])
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for dot in point_data["dots"]:
            writer.writerow({key: json.dumps(value, separators=(",", ":"))
                             if isinstance(value, (list, dict)) or value is None else value
                             for key, value in dot.items()})


def generate(p):
    frozen = check_freeze(p)
    profile = PROFILE.read_bytes()
    for split_name, specification in p["splits"].items():
        directory = ROOT / split_name
        directory.mkdir(exist_ok=True)
        manifest = {"schema": 1, "split": specification["manifest_split"],
                    "set_id": specification["set_id"], "protocol_id": p["protocol_id"],
                    "protocol_sha256": sha_file(PROTOCOL), "freeze_sha256": sha_file(FREEZE),
                    "dimensions_px": p["dimensions_px"], "color_space": "sRGB",
                    "icc_profile_sha256": sha_bytes(profile), "opaque": True, "inputs": []}
        for specification_entry in specification["inputs"]:
            pixels, point_data = (noise_pixels(p, specification_entry)
                                  if specification_entry["kind"] == "rgb_noise"
                                  else dots_pixels(p, specification_entry))
            input_id = specification_entry["id"]
            path = directory / (input_id + ".png")
            Image.fromarray(pixels, mode="RGB").save(path, format="PNG", icc_profile=profile,
                                                    optimize=False, compress_level=9)
            entry = {**specification_entry, "file": path.name, "sha256": sha_file(path),
                     "pixel_sha256": sha_bytes(pixels.tobytes()),
                     "width": pixels.shape[1], "height": pixels.shape[0], "mode": "RGB"}
            if point_data is not None:
                point_path = directory / (input_id + ".points.json")
                csv_path = directory / (input_id + ".points.csv")
                point_data["image_file"] = path.name
                point_data["image_sha256"] = entry["sha256"]
                point_data["image_pixel_sha256"] = entry["pixel_sha256"]
                write_json(point_path, point_data)
                csv_points(csv_path, point_data)
                entry.update({"points_file": point_path.name, "points_sha256": sha_file(point_path),
                              "points_csv": csv_path.name, "points_csv_sha256": sha_file(csv_path),
                              "point_count": point_data["point_count"]})
            manifest["inputs"].append(entry)
            print(json.dumps({"split": split_name, "id": input_id, "sha256": entry["sha256"]}), flush=True)
        write_json(directory / "manifest.json", manifest)
    write_json(ROOT / "generation.json", {"schema": 1, "freeze_sha256": sha_file(FREEZE),
               "generated_utc": datetime.now(timezone.utc).isoformat(), "dependencies": dependencies(),
               "manifest_sha256": {split: sha_file(ROOT / split / "manifest.json") for split in p["splits"]},
               "captures_consumed": 0, "visual_input_selection": False,
               "calibration_or_training_completed": False})


def verify(p):
    check_freeze(p)
    all_seeds = set()
    summary = []
    for split_name, specification in p["splits"].items():
        directory = ROOT / split_name
        manifest = json.loads((directory / "manifest.json").read_text())
        assert manifest["schema"] == 1 and manifest["split"] == specification["manifest_split"]
        assert manifest["set_id"] == specification["set_id"]
        assert len(manifest["inputs"]) == 8
        for actual, expected in zip(manifest["inputs"], specification["inputs"]):
            for key in ("id", "kind", "seed"):
                assert actual[key] == expected[key]
            assert actual["seed"] not in all_seeds
            all_seeds.add(actual["seed"])
            assert actual["file"] == actual["id"] + ".png"
            path = directory / actual["file"]
            assert sha_file(path) == actual["sha256"]
            with Image.open(path) as image:
                assert image.mode == "RGB" and image.size == tuple(p["dimensions_px"])
                assert image.info["icc_profile"] == PROFILE.read_bytes()
                assert sha_bytes(np.asarray(image).tobytes()) == actual["pixel_sha256"]
            if actual["kind"] == "dots":
                assert sha_file(directory / actual["points_file"]) == actual["points_sha256"]
                assert sha_file(directory / actual["points_csv"]) == actual["points_csv_sha256"]
                points = json.loads((directory / actual["points_file"]).read_text())
                assert points["image_sha256"] == actual["sha256"]
                assert len(points["dots"]) == p["dots"]["total_per_image"]
                assert len({d["id"] for d in points["dots"]}) == len(points["dots"])
                for d in points["dots"]:
                    assert d["source_x_pt"] == d["source_x_px"] / 2
                    assert d["source_y_pt"] == d["source_y_px"] / 2
                    assert 0 <= d["source_x_px"] < 750 and 0 <= d["source_y_px"] < 1334
                    assert d["seed"] == actual["seed"]
                summary.append({"id": actual["id"], "point_count": len(points["dots"]),
                                "edge_clipped_count": sum(d["edge_clipped"] for d in points["dots"]),
                                "source_signature_duplicate_point_count": points["source_signature_duplicate_point_count"]})
    assert len(all_seeds) == 16
    print(json.dumps({"verified": True, "image_count": 16, "total_source_points": 13440,
                      "calibration_or_training_completed": False, "point_tables": summary}, indent=2))


def main():
    parser = argparse.ArgumentParser()
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--freeze", action="store_true")
    actions.add_argument("--generate", action="store_true")
    actions.add_argument("--verify", action="store_true")
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
