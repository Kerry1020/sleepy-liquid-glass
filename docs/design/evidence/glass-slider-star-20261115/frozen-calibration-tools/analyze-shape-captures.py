#!/usr/bin/env python3
"""Measure a known fixed colored shape through original saved Slider captures.

python3 analyze-shape-captures.py --index native/index-light.json --out analysis/native-light

Index schema1: {platform, shape_spec, captures:[{stage_id,shape_id,run,png,
sha256,world_origin_window_px:[0,0],pixels_per_world_unit:2,
actual_control_bounds_world_xywh:[...],bounds_kind,receipt_json?,session_json?,
trace_jsonl?,external_metadata_json?,flat_png?,flat_sha256?,flat_geometry?}]}.
The generator's shape-spec.json fixes identity, original masks and analysis ROI.
No source/capture alignment, outline completion, largest-component selection,
native acceptance score, production change or device operation is performed.
"""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import json
import math
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
# Frozen before the new captures. All thresholds are reported, never selected
# after observing the image. A mask is color evidence, not recovered optical alpha.
THRESHOLDS_BYTE = (4., 8., 16., 24.)
PRIMARY_THRESHOLD_BYTE = 8.
MIN_COLOR_COSINE = .8
EDGE_BINS_WORLD = np.arange(-8., 8.0001, .5)


def require(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, f"Duplicate JSON key {key}: {path}")
            result[key] = value
        return result
    return json.loads(Path(path).read_text(), object_pairs_hook=unique)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def entry(path):
    path = Path(path).resolve()
    return {"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size}


def resolve(value, root):
    path = Path(value)
    return (path if path.is_absolute() else root / path).resolve()


def rgb_image(path):
    with Image.open(path) as im:
        require(im.format == "PNG" and im.mode in ("RGB", "RGBA"), f"Expected original RGB8/RGBA8 PNG: {path}")
        pixels = np.asarray(im, dtype=np.uint8).copy()
        icc = im.info.get("icc_profile", b"")
        if im.mode == "RGBA":
            require(np.all(pixels[:, :, 3] == 255), f"Nonopaque screenshot alpha cannot be silently discarded: {path}")
            pixels = pixels[:, :, :3].copy()
        return pixels, {"size_px": list(im.size), "mode": im.mode,
                        "icc_sha256": hashlib.sha256(icc).hexdigest() if icc else None,
                        "alpha_handling": "verified opaque255, original RGB channels retained" if im.mode == "RGBA" else "no alpha channel",
                        "encoding": "original stored8bit channels; no profile conversion or color fit"}


def mask_image(path, size):
    with Image.open(path) as im:
        require(im.format == "PNG" and im.mode == "L" and list(im.size) == size, f"Expected original L8 mask: {path}")
        return np.asarray(im, dtype=np.uint8).copy()


def validate_sources(spec_path, shape_id):
    spec = read(spec_path)
    require(spec["schema"] == 1, "Unsupported shape-spec schema")
    world = spec["world"]
    require(world["size"] == [375, 667] and world["source_size_px"] == [750, 1334]
            and world["pixels_per_world_unit"] == 2 and world["origin_world_pt"] == [0, 0], "Unexpected source world")
    manifest_path = spec_path.parent / "inputs/manifest.json"
    manifest = read(manifest_path)
    require(manifest["schema"] == 1 and isinstance(manifest["set_id"], str) and manifest["set_id"]
            and manifest["split"] == "calibration", "Wrong shape source manifest/schema/split")
    inputs = {item["id"]: item for item in manifest["inputs"]}
    require(len(inputs) == len(manifest["inputs"]) == 8, "Expected eight unique native-loader source entries")
    selected = shape_id or spec["first_input_id"]
    candidates = [item["shape"] for item in spec["inputs"] if item["id"] == selected]
    require(len(candidates) == 1 and candidates[0] is not None, "Unknown/non-shape input identity")
    shape = candidates[0]
    source_path = resolve(shape["source_png"], spec_path.parent)
    require(sha(source_path) == shape["source_sha256"] == inputs[selected]["sha256"], "Original source SHA mismatch")
    require(source_path.stat().st_size == inputs[selected]["bytes"], "Original source byte count mismatch")
    source, encoding = rgb_image(source_path)
    require(encoding["size_px"] == world["source_size_px"] and encoding["mode"] == "RGB", "Unexpected original source raster")
    coverage_path = resolve(shape["coverage_count_mask_png"], spec_path.parent)
    binary_path = resolve(shape["binary_mask_png"], spec_path.parent)
    require(sha(coverage_path) == shape["coverage_count_mask_sha256"] and sha(binary_path) == shape["binary_mask_sha256"],
            "Original source masks SHA mismatch")
    coverage = mask_image(coverage_path, world["source_size_px"])
    binary = mask_image(binary_path, world["source_size_px"])
    denominator = shape["coverage_denominator"]
    require(denominator == 16 and coverage.max() <= denominator and set(np.unique(binary)) <= {0, 255}, "Invalid original mask values")
    require(np.array_equal(binary > 0, coverage > 0), "Binary support differs from area sample mask")
    bg = np.asarray(world["background_rgb"], dtype=np.int32)
    region_specs = shape.get("regions") or [{"id": shape["id"], "color_rgb": shape["color_rgb"],
        "coverage_count_mask_png": shape["coverage_count_mask_png"], "coverage_count_mask_sha256": shape["coverage_count_mask_sha256"],
        "binary_mask_png": shape["binary_mask_png"], "binary_mask_sha256": shape["binary_mask_sha256"], "coverage_denominator": denominator}]
    require(region_specs and len({region["id"] for region in region_specs}) == len(region_specs), "Need unique fixed color-region identities")
    region_data, region_receipts = [], []
    coverage_sum = np.zeros(coverage.shape, dtype=np.int32)
    color_sum = np.broadcast_to(bg * denominator, source.shape).copy()
    for region in region_specs:
        region_coverage_path = resolve(region["coverage_count_mask_png"], spec_path.parent)
        region_binary_path = resolve(region["binary_mask_png"], spec_path.parent)
        require(sha(region_coverage_path) == region["coverage_count_mask_sha256"] and
                sha(region_binary_path) == region["binary_mask_sha256"], f"Changed original region masks: {region['id']}")
        region_coverage = mask_image(region_coverage_path, world["source_size_px"])
        region_binary = mask_image(region_binary_path, world["source_size_px"])
        require(region.get("coverage_denominator", denominator) == denominator and region_coverage.max() <= denominator and
                np.array_equal(region_binary > 0, region_coverage > 0), "Region source masks disagree")
        color = np.asarray(region["color_rgb"], dtype=np.int32)
        require(color.shape == (3,) and np.all(color >= 0) and np.all(color <= 255) and np.linalg.norm(color - color.mean()) > 0,
                "Each source color region needs a declared non-neutral RGB identity")
        coverage_sum += region_coverage
        color_sum += region_coverage[:, :, None].astype(np.int32) * (color - bg)
        region_data.append({"spec": region, "coverage": region_coverage / float(denominator), "support": region_binary > 0})
        region_receipts.append({"region_id": region["id"], "coverage_mask": entry(region_coverage_path), "binary_mask": entry(region_binary_path)})
    require(np.array_equal(coverage_sum, coverage), "Region area-sample masks do not partition whole-shape coverage")
    expected = (color_sum + 8) // denominator
    require(np.array_equal(source, expected.astype(np.uint8)), "Original source RGB is not the declared color-region/mask integer blend")
    area = float(coverage.astype(float).sum() / denominator / 4.)
    require(area == shape["source_coverage_area_pt2"], "Original coverage area differs from source spec")
    require(encoding["icc_sha256"] == spec["rasterization"]["icc_sha256"], "Original source ICC changed")
    require(len(spec["stages"]) == 6 and len({s["id"] for s in spec["stages"]}) == 6, "Expected six fixed approach stages")
    return spec, shape, source, coverage / float(denominator), binary > 0, region_data, {
        "specification": entry(spec_path), "manifest": entry(manifest_path), "original_source": entry(source_path),
        "coverage_count_mask": entry(coverage_path), "binary_support_mask": entry(binary_path), "source_encoding": encoding,
        "source_coverage_area_world2": area, "fixed_color_region_masks": region_receipts,
    }


def mapping(record, pixels):
    origin = np.asarray(record["world_origin_window_px"], dtype=float)
    density = float(record["pixels_per_world_unit"])
    require(origin.shape == (2,) and np.isfinite(origin).all() and math.isfinite(density) and density > 0,
            "Need finite recorded source Window origin and density")
    require(record.get("source_world_xywh", [0, 0, 375, 667]) == [0, 0, 375, 667], "Unexpected fixed source world")
    return {"world_origin_window_px": origin.tolist(), "pixels_per_world_unit": density,
            "png_size_px": list(pixels.shape[1::-1]),
            "rule": "world=(original Window pixel center-recorded source Window origin)/recorded pixels-per-world-unit"}


def crop_roi(pixels, grid, roi):
    origin, density = grid["world_origin_window_px"], grid["pixels_per_world_unit"]
    x = (np.arange(pixels.shape[1]) + .5 - origin[0]) / density
    y = (np.arange(pixels.shape[0]) + .5 - origin[1]) / density
    left, top, right, bottom = roi
    cols = np.flatnonzero((x >= left) & (x < right))
    rows = np.flatnonzero((y >= top) & (y < bottom))
    require(len(cols) and len(rows), "Fixed ROI has no captured original pixels")
    require(x[0] - .5 / density <= left and x[-1] + .5 / density >= right and
            y[0] - .5 / density <= top and y[-1] + .5 / density >= bottom, "Fixed ROI is cropped by the original PNG")
    values = pixels[np.ix_(rows, cols)]
    if values.shape[2] == 4:
        require(np.all(values[:, :, 3] == 255), "Fixed ROI contains nonopaque pixels; synthetic compositing is not allowed")
    return x[cols], y[rows], values[:, :, :3], {
        "original_pixel_rect_xyxy": [int(cols[0]), int(rows[0]), int(cols[-1] + 1), int(rows[-1] + 1)],
        "sample_x_world": x[cols].tolist(), "sample_y_world": y[rows].tolist(),
        "original_sample_count": int(len(rows) * len(cols)), "sample_pixel_area_world2": 1. / density ** 2,
    }


def weighted_geometry(xx, yy, weights, density):
    x, y = np.meshgrid(xx, yy)
    mass = float(weights.sum())
    if mass == 0:
        return {"status": "unobserved_zero_evidence", "mass": 0., "area_world2": 0., "centroid_world": None,
                "covariance_world2": None, "principal_axes": None, "bounds_xyxy_world": None}
    cx, cy = float((weights * x).sum() / mass), float((weights * y).sum() / mass)
    dx, dy = x - cx, y - cy
    covariance = np.array([[float((weights * dx * dx).sum() / mass), float((weights * dx * dy).sum() / mass)],
                           [float((weights * dx * dy).sum() / mass), float((weights * dy * dy).sum() / mass)]])
    axes = None
    if np.all(weights >= 0):
        values, vectors = np.linalg.eigh(covariance)
        order = np.argsort(values)[::-1]
        values, vectors = values[order], vectors[:, order]
        for i in range(2):
            if vectors[0, i] < 0 or (vectors[0, i] == 0 and vectors[1, i] < 0):
                vectors[:, i] *= -1
        degenerate = abs(values[0] - values[1]) <= 1e-12 * max(1., abs(values[0]))
        axes = {"eigenvalues_world2": values.tolist(), "unit_axes_columns": vectors.tolist(),
                "major_angle_degrees": None if degenerate else float(np.degrees(np.arctan2(vectors[1, 0], vectors[0, 0]))),
                "orientation_status": "undefined_equal_eigenvalues" if degenerate else "defined",
                "four_sigma_axis_lengths_world": (4 * np.sqrt(np.maximum(values, 0.))).tolist(),
                "axis_length_ratio": None if values[1] <= 0 else float(np.sqrt(values[0] / values[1]))}
    selected = weights != 0
    return {"status": "descriptive_raw_weights", "mass": mass, "area_world2": mass / density ** 2,
            "centroid_world": [cx, cy], "covariance_world2": covariance.tolist(), "principal_axes": axes,
            "bounds_xyxy_world": [float(x[selected].min() - .5 / density), float(y[selected].min() - .5 / density),
                                   float(x[selected].max() + .5 / density), float(y[selected].max() + .5 / density)]}


def byte_signal_moments(xx, yy, signal, density):
    result = weighted_geometry(xx, yy, signal, density)
    result["mass_integral_byte_world2"] = result.pop("area_world2")
    result["weight_unit"] = "stored_channel_byte; integrated signal is not geometric area or optical alpha"
    return result


def edge_segments(xx, yy, mask, density):
    """All outer and hole cell edges; no smoothing or outline completion."""
    edges = []
    half = .5 / density
    for row, col in np.argwhere(mask):
        x, y = xx[col], yy[row]
        if row == 0 or not mask[row - 1, col]:
            edges.append([[x - half, y - half], [x + half, y - half]])
        if col == mask.shape[1] - 1 or not mask[row, col + 1]:
            edges.append([[x + half, y - half], [x + half, y + half]])
        if row == mask.shape[0] - 1 or not mask[row + 1, col]:
            edges.append([[x + half, y + half], [x - half, y + half]])
        if col == 0 or not mask[row, col - 1]:
            edges.append([[x - half, y + half], [x - half, y - half]])
    return np.asarray(edges, dtype=float).reshape((-1, 2, 2))


def components(mask, xx, yy, density):
    remaining = mask.copy()
    result = []
    # Raster order is retained. No component is selected as the true object.
    for row, col in np.argwhere(mask):
        if not remaining[row, col]:
            continue
        queue = deque([(row, col)])
        remaining[row, col] = False
        cells = []
        while queue:
            ry, cx = queue.popleft()
            cells.append((ry, cx))
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    ny, nx = ry + dy, cx + dx
                    if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] and remaining[ny, nx]:
                        remaining[ny, nx] = False
                        queue.append((ny, nx))
        local = np.zeros(mask.shape, dtype=bool)
        rows, cols = np.asarray(cells).T
        local[rows, cols] = True
        result.append({"component_id": len(result), "original_pixel_count": len(cells),
                       **weighted_geometry(xx, yy, local.astype(float), density)})
    return result


def nearest_distance(points, segments):
    if not len(segments):
        return None
    a = segments[:, 0]
    delta = segments[:, 1] - a
    length2 = (delta * delta).sum(axis=1)
    result = np.empty(len(points))
    for start in range(0, len(points), 1024):
        block = points[start:start + 1024]
        relative = block[:, None, :] - a
        t = np.clip((relative * delta).sum(axis=2) / length2, 0, 1)
        squared = ((relative - t[:, :, None] * delta) ** 2).sum(axis=2)
        result[start:start + len(block)] = np.sqrt(squared.min(axis=1))
    return result


def distance_summary(values):
    if values is None or not len(values):
        return {"status": "unavailable_no_visible_boundary"}
    return {"status": "descriptive_original_cell_edge_distance", "samples": len(values),
            "minimum_world": float(values.min()), "mean_world": float(values.mean()),
            "quantiles_world": {str(p): float(np.percentile(values, p)) for p in (0, 10, 25, 50, 75, 90, 95, 100)}}


def source_membership(points, full_mask, source_density):
    cols = np.floor(points[:, 0] * source_density).astype(int)
    rows = np.floor(points[:, 1] * source_density).astype(int)
    valid = (cols >= 0) & (rows >= 0) & (cols < full_mask.shape[1]) & (rows < full_mask.shape[0])
    result = np.zeros(len(points), bool)
    result[valid] = full_mask[rows[valid], cols[valid]]
    return result


def original_area_sample_points(shape, support, coverage, density):
    """Recreate the declared4x4 source geometry samples, not a screenshot fit."""
    vertices = shape.get("vertices_world_pt")
    if not vertices:
        rows, cols = np.nonzero(support)
        return np.column_stack(((cols + .5) / density, (rows + .5) / density)), coverage[rows, cols], "original source pixel centers weighted by declared coverage"
    rows, cols = np.nonzero(support)
    x0, x1, y0, y1 = cols.min(), cols.max() + 1, rows.min(), rows.max() + 1
    xx = (x0 + (np.arange((x1 - x0) * 4) + .5) / 4) / density
    yy = (y0 + (np.arange((y1 - y0) * 4) + .5) / 4) / density
    x, y = np.meshgrid(xx, yy)
    inside = np.zeros(x.shape, bool)
    previous = vertices[-1]
    for current in vertices:
        ax, ay = previous
        bx, by = current
        if ay != by:
            inside ^= ((ay > y) != (by > y)) & (x < ax + (y - ay) * (bx - ax) / (by - ay))
        previous = current
    counts = inside.reshape(y1 - y0, 4, x1 - x0, 4).sum(axis=(1, 3))
    require(np.array_equal(counts / 16., coverage[y0:y1, x0:x1]), "Source polygon samples disagree with original area mask")
    return np.column_stack((x[inside], y[inside])), np.ones(np.count_nonzero(inside)), "exact declared4x4 original source polygon sample centers"


def public_bounds_overlap(points, weights, bounds):
    if bounds is None:
        return {"status": "unavailable_no_public_carrier_rectangle"}
    require(len(bounds) == 4 and np.isfinite(bounds).all() and bounds[2] > 0 and bounds[3] > 0,
            "Invalid public carrier rectangle for declared geometric overlap")
    require(len(points) == len(weights) and weights.sum() > 0, "Empty declared source integration samples")
    left, top, width, height = bounds
    x, y = points[:, 0], points[:, 1]
    rect = (x >= left) & (x < left + width) & (y >= top) & (y < top + height)
    radius = min(width, height) / 2.
    cx, cy = left + width / 2., top + height / 2.
    if width >= height:
        qx = np.maximum(np.abs(x - cx) - (width / 2. - radius), 0)
        qy = np.abs(y - cy)
    else:
        qx = np.abs(x - cx)
        qy = np.maximum(np.abs(y - cy) - (height / 2. - radius), 0)
    capsule = qx * qx + qy * qy <= radius * radius
    return {"status": "declared_public_rectangle_and_capsule_approximation_not_native_optical_coverage",
            "public_rectangle_source_area_fraction": float(weights[rect].sum() / weights.sum()),
            "declared_capsule_source_area_fraction": float(weights[capsule].sum() / weights.sum()),
            "integration_sample_count": len(points), "integration_total_source_weight": float(weights.sum()),
            "public_rectangle_source_weight": float(weights[rect].sum()),
            "declared_capsule_source_weight": float(weights[capsule].sum()),
            "integration_scope": "discrete integral over original declared source samples, never optical alpha",
            "capsule_radius_world": radius,
            "warning": "Public presentation bounds and an inscribed capsule are planning geometry, never recovered native optical alpha."}


def requested_public_bounds(spec, stage):
    supplied = stage.get("requested_carrier_bounds_world_xywh")
    if supplied is not None:
        return supplied
    reference = spec.get("native_public_geometry_reference", {}).get("observed_public_presentation_xywh_pt")
    if reference is None:
        return None
    width, height = reference[2:]
    cx, cy = stage["requested_lens_center_world_pt"]
    return [cx - width / 2., cy - height / 2., width, height]


def color_stats(rgb, selected):
    values = rgb[selected].astype(float)
    if not len(values):
        return {"status": "unobserved_empty_region", "samples": 0}
    chroma = values - values.mean(axis=1, keepdims=True)
    high, low = values.max(axis=1), values.min(axis=1)
    saturation = np.divide(high - low, high, out=np.zeros(len(values)), where=high != 0)
    return {"status": "descriptive_original_encoded_channels", "samples": len(values),
            "mean_rgb_byte": values.mean(axis=0).tolist(), "std_rgb_byte": values.std(axis=0).tolist(),
            "quantile_rgb_byte": {str(q): np.percentile(values, q, axis=0).tolist() for q in (0, 10, 25, 50, 75, 90, 100)},
            "mean_chroma_norm_byte": float(np.linalg.norm(chroma, axis=1).mean()),
            "mean_hsv_saturation": float(saturation.mean())}


def scalar_stats(values):
    if not len(values):
        return None
    return {"mean": float(values.mean()), "minimum": float(values.min()), "maximum": float(values.max()),
            "quantiles": {str(q): float(np.percentile(values, q)) for q in (10, 25, 50, 75, 90)}}


def source_edge_profile(xx, yy, rgb, signal, source_mask, source_edges, source_density):
    x, y = np.meshgrid(xx, yy)
    points = np.column_stack((x.ravel(), y.ravel()))
    distance = nearest_distance(points, source_edges)
    inside = source_membership(points, source_mask, source_density)
    signed = distance * np.where(inside, -1., 1.)
    rows = []
    for low, high in zip(EDGE_BINS_WORLD[:-1], EDGE_BINS_WORLD[1:]):
        selected = ((signed >= low) & (signed < high)).reshape(rgb.shape[:2])
        rows.append({"source_boundary_signed_distance_interval_world": [float(low), float(high)],
                     "inside_source_is_negative": True, "color": color_stats(rgb, selected),
                     "color_direction_projection_byte": scalar_stats(signal[selected])})
    return rows


def contour_descriptor(xx, yy, evidence, signal, density, roi, source_edges):
    geometry = weighted_geometry(xx, yy, evidence.astype(float), density)
    edges = edge_segments(xx, yy, evidence, density)
    edge_mask = np.zeros(evidence.shape, bool)
    edge_mask[[0, -1], :] = True
    edge_mask[:, [0, -1]] = True
    observed_midpoints = edges.mean(axis=1) if len(edges) else np.empty((0, 2))
    source_midpoints = source_edges.mean(axis=1)
    return {"geometry": geometry, "components_eight_connected_raster_order": components(evidence, xx, yy, density),
            "contour_cell_edges_world": edges.tolist(), "cell_edge_perimeter_world": len(edges) / density,
            "boundary_evidence_pixel_count": int(np.count_nonzero(evidence & edge_mask)),
            "boundary_positive_projection_mass_byte": float(np.maximum(signal[evidence & edge_mask], 0.).sum()),
            "fixed_roi_xyxy_world": roi,
            "visible_boundary_to_original_source_boundary": distance_summary(nearest_distance(observed_midpoints, source_edges)),
            "original_source_boundary_to_visible_boundary": distance_summary(nearest_distance(source_midpoints, edges)),
            "distance_scope": "All original raster cell edges and their midpoints; no correspondence, fitting, smoothing, missing-contour interpolation or optical alpha inference."}


def threshold_descriptors(xx, yy, masks, signal, density, roi, source_edges, rail_domain):
    descriptors = []
    for threshold in THRESHOLDS_BYTE:
        evidence = masks[threshold]
        descriptor = contour_descriptor(xx, yy, evidence, signal, density, roi, source_edges)
        descriptor["rail_excluded_restricted_geometry"] = weighted_geometry(xx, yy, (evidence & ~rail_domain).astype(float), density)
        descriptor["rail_domain_evidence_pixel_count"] = int(np.count_nonzero(evidence & rail_domain))
        descriptor["rail_domain_positive_projection_mass_byte"] = float(np.maximum(signal[evidence & rail_domain], 0.).sum())
        descriptor["threshold_projection_byte"] = threshold
        descriptor["minimum_color_direction_cosine"] = MIN_COLOR_COSINE
        descriptors.append(descriptor)
    return descriptors


def fixed_direction_support(xx, yy, mask, shape):
    """Extents along predeclared vertex directions; never assign recovered tips."""
    vertices = shape.get("vertices_world_pt") or []
    center = np.asarray(shape["center_world_pt"], dtype=float)
    x, y = np.meshgrid(xx, yy)
    points = np.column_stack((x[mask], y[mask]))
    rows = []
    for vi, vertex in enumerate(vertices):
        direction = np.asarray(vertex, dtype=float) - center
        direction /= np.linalg.norm(direction)
        row = {"source_vertex_id": f"vertex{vi:02d}", "source_vertex_world": vertex,
               "fixed_unit_direction": direction.tolist()}
        if not len(points):
            row.update({"status": "unobserved_no_color_evidence", "all_maximum_support_positions_world": [], "maximum_support_from_source_center_world": None})
        else:
            relative = points - center
            # Explicit2D arithmetic also avoids backend BLAS floating-status
            # warnings for these short vectors on the local Accelerate runtime.
            projection = relative[:, 0] * direction[0] + relative[:, 1] * direction[1]
            require(np.isfinite(projection).all(), "Nonfinite original-coordinate directional extent")
            maximum = projection.max()
            row.update({"status": "descriptive_visible_directional_extent_not_vertex_correspondence",
                        "maximum_support_from_source_center_world": float(maximum),
                        "all_maximum_support_positions_world": points[projection == maximum].tolist()})
        rows.append(row)
    return rows


def observed_color_regions(xx, yy, rgb, evidence, density):
    x, y = np.meshgrid(xx, yy)
    edges = edge_segments(xx, yy, evidence, density)
    distance = nearest_distance(np.column_stack((x.ravel(), y.ravel())), edges)
    if distance is None:
        interior = boundary = np.zeros(evidence.shape, bool)
    else:
        distance = distance.reshape(evidence.shape)
        interior = evidence & (distance >= .75)
        boundary = evidence & (distance < .75)
    return {"visible_color_statistics": color_stats(rgb, evidence),
            "visible_inner_color_statistics": color_stats(rgb, interior),
            "visible_boundary_color_statistics": color_stats(rgb, boundary)}


def validate_capture_context(record, index_root, expected_source_sha, pixels, platform):
    receipts = {}
    for key in ("session_json", "trace_jsonl", "external_metadata_json", "receipt_json", "shape_metadata_json", "android_evidence_json", "android_receipt_json"):
        if record.get(key):
            path = resolve(record[key], index_root)
            receipts[key] = entry(path)
    result = {"files": receipts, "checks": [], "limitations": []}
    if record.get("external_metadata_json"):
        external = read(resolve(record["external_metadata_json"], index_root))
        require(external["sha256"] == expected_source_sha, "Native exported source hash differs from fixed shape")
        require(external["worldOriginPt"] == [0, 0] and external["worldSizePt"] == [375, 667] and external["pixelsPerPt"] == 2,
                "Native external source world changed")
        canvas = external["canvasRectInWindowPt"]
        require([canvas[k] for k in ("x", "y", "w", "h")] == [0, 0, 375, 667], "Native source canvas moved")
        result["checks"].append("exported_source_hash_and_fixed_canvas")
    else:
        result["limitations"].append("No external metadata supplied; screenshot source identity not independently established")
    if platform == "ios" and record.get("session_json"):
        session = read(resolve(record["session_json"], index_root))
        safe_run = re.sub(r"[^a-zA-Z0-9_.-]", "_", record["run"])
        require(session["run"] in (record["run"], safe_run), "Index run differs from original native session identity")
        result["run_identity"] = {"original_host_run": record["run"], "session_run": session["run"],
                                  "recorded_path_sanitization": "replace each[^a-zA-Z0-9_.-]with_"}
        require(session["os"] == "Version 26.5 (Build 23F77)", "Requested native baseline is iOS26.5 build23F77")
        require([session["screenWidthPt"], session["screenHeightPt"], session["screenScale"]] == [375, 667, 2]
                and pixels.shape[1::-1] == (750, 1334), "Native original raster/world differs")
        require(session.get("sliderFixedShapeCoverage") is True, "Missing explicit fixed-shape native guard")
        require(not session["reduceMotion"] and not session["reduceTransparency"] and not session["darkerSystemColors"], "Native accessibility traits changed")
        require(record["world_origin_window_px"] == [0, 0] and record["pixels_per_world_unit"] == 2,
                "Native input index contradicts recorded full source canvas")
        result["checks"].append("iOS26.5_native_guard_screen_and_traits")
        if record.get("trace_jsonl") and (record.get("receipt_json") or record.get("receipt")):
            receipt = read(resolve(record["receipt_json"], index_root)) if record.get("receipt_json") else record["receipt"]
            if "observations" in receipt:
                candidates = [row for row in receipt["observations"] if row.get("event", row).get("run") == record["run"]]
                require(len(candidates) == 1, "Aggregate host receipt lacks one unique original capture run")
                observation = candidates[0]
                require(observation.get("imageSHA256") == record["sha256"], "Aggregate host screenshot SHA differs from capture index")
                if "verifiedHeldEndpoint" in observation:
                    require(receipt.get("status") == "passed" and observation["verifiedHeldEndpoint"] is True and not observation["errors"],
                            "Strict endpoint verifier did not pass this complete capture matrix and endpoint")
                    require(observation["actualCarrierBoundsPt"] == record["actual_carrier_bounds_world_xywh"],
                            "Index carrier geometry differs from strict endpoint verifier")
                    result["strict_endpoint_verifier"] = {
                        "verifiedHeldEndpoint": True, "validity_source": receipts["receipt_json"],
                        **{key: observation[key] for key in ("presentedSampling", "ownerPoseStability", "carrierPoseStability", "actualLastMoves")
                           if key in observation}}
                    result["checks"].append("strict_endpoint_verifier_passed")
                receipt = observation.get("event", observation)
            begin, end = receipt["screenshotBeginUnixSeconds"], receipt["screenshotEndUnixSeconds"]
            require(begin < end and receipt.get("exitCode", 0) == 0, "Invalid screenshot receipt bracket")
            trace = [json.loads(line) for line in resolve(record["trace_jsonl"], index_root).read_text().splitlines() if line.strip()]
            touches = [row for row in trace if row.get("event") == "touch" and row.get("source") == "delivery"]
            eligible = []
            for down in touches:
                if down.get("phase") != 0:
                    continue
                endings = [row for row in touches if row.get("touchID") == down["touchID"] and row.get("phase") in (3, 4)
                           and row["deliveredT"] > down["deliveredT"]]
                for ending in endings:
                    start = session["originUnixSeconds"] + down["deliveredT"]
                    finish = session["originUnixSeconds"] + ending["deliveredT"]
                    if start <= begin < end <= finish:
                        preceding = [row for row in touches if row.get("touchID") == down["touchID"] and row.get("phase") in (0, 1)
                                     and session["originUnixSeconds"] + row["deliveredT"] <= begin]
                        last_move = max(session["originUnixSeconds"] + row["deliveredT"] for row in preceding)
                        eligible.append({"down_unix": start, "end_unix": finish, "screenshot_begin_unix": begin,
                                         "screenshot_end_unix": end, "last_delivered_down_or_move_before_capture_unix": last_move,
                                         "settle_before_screenshot_seconds": begin - last_move})
            require(len(eligible) == 1, "Original screenshot is not wholly within one actual delivered DOWN/END pair")
            result["held_bracket"] = eligible[0]
            result["checks"].append("original_screenshot_wholly_inside_delivered_held_bracket")
            if eligible[0]["settle_before_screenshot_seconds"] < .65:
                result["limitations"].append("Less than0.65s after last delivered DOWN/MOVE; static settled endpoint is not established")
        else:
            result["limitations"].append("No complete original trace/host bracket supplied; actual held state not independently established")
    elif platform == "ios":
        result["limitations"].append("No native session supplied; OS/traits/guard not independently established")
    if platform == "android":
        result["checks"].extend(record.get("capture_checks", []))
        result["source_layout_geometry"] = record.get("source_layout_geometry")
        result["limitations"].append("Capture validity comes from original Android pointer/readiness receipts and adapter checks; no native endpoint-verifier verdict applies to Android")
    return result


def make_stage_images(out, stem, source_rgb, capture_rgb, mask, signal, xx, yy, density, source_edges, rail, has_flat):
    original = Image.fromarray(capture_rgb)
    original.save(out / f"{stem}-original-roi.png")
    Image.fromarray(mask.astype(np.uint8) * 255).save(out / f"{stem}-visible-color-evidence-mask.png")
    clipped = np.clip(signal / 128., -1, 1)
    positive = np.maximum(clipped, 0.)
    negative = np.maximum(-clipped, 0.)
    heat = np.stack((negative * 255, positive * 230, positive * 255), axis=2).astype(np.uint8)
    Image.fromarray(heat).save(out / f"{stem}-color-projection.png")
    overlay = original.copy()
    draw = ImageDraw.Draw(overlay)
    ox, oy = xx[0] - .5 / density, yy[0] - .5 / density
    for segment in source_edges:
        pts = [((x - ox) * density, (y - oy) * density) for x, y in segment]
        draw.line(pts, fill=(255, 220, 0), width=1)
    for segment in edge_segments(xx, yy, mask, density):
        pts = [((x - ox) * density, (y - oy) * density) for x, y in segment]
        draw.line(pts, fill=(255, 80, 190), width=1)
    if not has_flat:
        for value in rail:
            py = (value - oy) * density
            if 0 <= py < overlay.height:
                draw.line([(0, py), (overlay.width, py)], fill=(255, 150, 30))
    overlay.save(out / f"{stem}-source-visible-overlay.png")
    return {"source": Image.fromarray(source_rgb), "captured_original": original,
            "source_yellow_visible_pink": overlay, "color_direction_projection": Image.fromarray(heat)}


def contact_sheet(path, displays, rows):
    w, h, header = 360, 340, 112
    keys = ("source", "captured_original", "source_yellow_visible_pink", "color_regions", "color_direction_projection")
    sheet = Image.new("RGB", (w * len(keys), (h + header) * len(displays)), "#252525")
    draw = ImageDraw.Draw(sheet)
    for ri, images in enumerate(displays):
        row = rows[ri]
        for ci, key in enumerate(keys):
            left, top = ci * w, ri * (h + header)
            draw.text((left + 5, top + 3), f"{row['stage_id']} / {key}", fill="white")
            draw.text((left + 5, top + 19), "DISPLAY ONLY: nearest resize, fixed world ROI", fill="#bbbbbb")
            draw.text((left + 5, top + 35), "flat difference" if row["pose_matched_flat_supplied"] else "NO FLAT: rail remains confounded", fill="#ffb060")
            comparison = row["requested_actual_public_geometry_comparison"]
            requested = comparison["requested_discrete_capsule_fraction"]
            actual = comparison["actual_discrete_capsule_fraction"]
            requested_text = "unknown" if requested is None else f"{requested:.3%}"
            actual_text = "unknown" if actual is None else f"{actual:.3%}"
            nominal = comparison["nominal_requested_fraction"]
            nominal_text = "unknown" if nominal is None else f"{nominal:.1%}"
            draw.text((left + 5, top + 51), f"Nominal {nominal_text}; discrete request {requested_text}", fill="#bbbbbb")
            draw.text((left + 5, top + 67), f"Actual capsule approx {actual_text}; NOT alpha", fill="#a3dbff")
            delta = row["actual_minus_planned_carrier_center_world"]
            delta_text = "unknown" if delta is None else f"({delta[0]:+.4f}, {delta[1]:+.4f})"
            draw.text((left + 5, top + 83), f"Actual-request center delta {delta_text} pt", fill="#bbbbbb")
            strict = "strict endpoint passed" if row["capture_context"].get("strict_endpoint_verifier") else "no strict endpoint validity verdict"
            draw.text((left + 5, top + 99), strict, fill="#9ef0aa" if row["capture_context"].get("strict_endpoint_verifier") else "#ffb060")
            sheet.paste(images[key].resize((w, h), Image.Resampling.NEAREST), (left, top + header))
    sheet.save(path)


def line_chart(path, rows):
    image = Image.new("RGB", (1440, 700), "#f6f6f8")
    draw = ImageDraw.Draw(image)
    panels = (("Color-evidence area / source-rule area", "area_ratio"),
              ("Evidence centroid displacement from original (world)", "centroid_displacement"),
              ("Evidence major/minor axis ratio", "axis_ratio"))
    for pi, (title, key) in enumerate(panels):
        x0, y0, x1, y1 = 65 + pi * 475, 75, 440 + pi * 475, 600
        draw.text((x0 - 15, 25), title, fill="black")
        draw.line([(x0, y0), (x0, y1), (x1, y1)], fill="#333333", width=2)
        values = [r["summary"][key] for r in rows]
        finite = [v for v in values if v is not None]
        maximum = max([1., *finite]) * 1.12
        points = []
        for i, (row, value) in enumerate(zip(rows, values)):
            x = x0 + i * (x1 - x0) / max(len(rows) - 1, 1)
            draw.text((x - 24, y1 + 8), row["stage_id"], fill="black")
            actual_fraction = row["requested_actual_public_geometry_comparison"]["actual_discrete_capsule_fraction"]
            if actual_fraction is not None:
                draw.text((x - 24, y1 + 24), f"{actual_fraction:.2%}", fill="#444444")
            if value is None:
                draw.text((x - 15, y0 + 10), "missing", fill="#bd2850")
                points.append(None)
            else:
                y = y1 - value / maximum * (y1 - y0)
                points.append((x, y))
                draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill="#007f92")
                draw.text((x - 18, y - 18), f"{value:.3g}", fill="#005c6a")
        for a, b in zip(points[:-1], points[1:]):
            if a is not None and b is not None:
                draw.line([a, b], fill="#007f92", width=3)
    draw.text((25, 655), "Stage labels are requested poses; percentages below are actual public-bounds capsule approximation, never optical alpha.", fill="black")
    draw.text((25, 675), "Descriptive color evidence only. Threshold8; full sensitivity tables/all components in JSON. Missing contour is never completed.", fill="black")
    image.save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--index", type=Path)
    parser.add_argument("--spec", type=Path, default=HERE / "shape-spec.json")
    parser.add_argument("--shape-id")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--allow-partial", action="store_true", help="Analyze saved stages so far without claiming a complete six-stage set")
    parser.add_argument("--require-strict-verification", action="store_true", help="Require a passed complete native endpoint-verifier index")
    parser.add_argument("--validate-inputs", action="store_true")
    args = parser.parse_args()
    spec, shape, source, coverage, source_support, color_regions, provenance = validate_sources(args.spec.resolve(), args.shape_id)
    source_density = float(spec["world"]["pixels_per_world_unit"])
    source_grid = {"world_origin_window_px": [0., 0.], "pixels_per_world_unit": source_density}
    roi = shape["fixed_analysis_roi_xyxy_world"]
    sxx, syy, source_crop, _ = crop_roi(source, source_grid, roi)
    # The source geometry is measured directly on the original mask, not a resized
    # screenshot and not a rendering of a hypothesized lens.
    sleft, stop = int(round(roi[0] * source_density)), int(round(roi[1] * source_density))
    source_roi_support = source_support[stop:stop + len(syy), sleft:sleft + len(sxx)]
    source_roi_coverage = coverage[stop:stop + len(syy), sleft:sleft + len(sxx)]
    source_edges = edge_segments(sxx, syy, source_roi_support, source_density)
    source_geo = weighted_geometry(sxx, syy, source_roi_coverage, source_density)
    source_binary_geo = weighted_geometry(sxx, syy, source_roi_support.astype(float), source_density)
    source_area_points, source_area_weights, source_area_sample_method = original_area_sample_points(shape, source_support, coverage, source_density)
    region_geometry = []
    for region in color_regions:
        color = np.asarray(region["spec"]["color_rgb"], dtype=float)
        chroma = color - color.mean()
        region["direction"] = chroma / np.linalg.norm(chroma)
        support = region["support"][stop:stop + len(syy), sleft:sleft + len(sxx)]
        weights = region["coverage"][stop:stop + len(syy), sleft:sleft + len(sxx)]
        region["edges"] = edge_segments(sxx, syy, support, source_density)
        region_geometry.append({"region_id": region["spec"]["id"], "color_rgb": region["spec"]["color_rgb"],
                                "color_direction_unit_rgb": region["direction"].tolist(),
                                "original_area_weighted_geometry": weighted_geometry(sxx, syy, weights, source_density),
                                "original_binary_support_geometry": weighted_geometry(sxx, syy, support.astype(float), source_density),
                                "original_cell_edge_segments_world": region["edges"].tolist(),
                                "original_inner_color_statistics": color_stats(source_crop, weights == 1)})
    source_background = np.asarray(spec["world"]["background_rgb"], dtype=float)
    source_signal = source_crop.astype(float) - source_background
    source_chroma = source_signal - source_signal.mean(axis=2, keepdims=True)
    source_norm = np.linalg.norm(source_chroma, axis=2)
    source_rule_masks = {t: np.zeros(source_norm.shape, bool) for t in THRESHOLDS_BYTE}
    for region in color_regions:
        projection = source_chroma @ region["direction"]
        cosine = np.divide(projection, source_norm, out=np.zeros(source_norm.shape), where=source_norm != 0)
        for threshold in THRESHOLDS_BYTE:
            source_rule_masks[threshold] |= (projection >= threshold) & (cosine >= MIN_COLOR_COSINE)
    source_same_color_rule = [{"threshold_projection_byte": threshold,
                              "geometry": weighted_geometry(sxx, syy, source_rule_masks[threshold].astype(float), source_density)}
                             for threshold in THRESHOLDS_BYTE]
    source_primary_rule_area = next(row["geometry"]["area_world2"] for row in source_same_color_rule
                                    if row["threshold_projection_byte"] == PRIMARY_THRESHOLD_BYTE)
    require(source_primary_rule_area > 0, "Original source is not visible to its preregistered fixed color rule")
    if args.validate_inputs:
        print(json.dumps({"status": "source_RGB_masks_hashes_area_verified", "shape_id": shape["id"],
                          "source_area_world2": source_geo["area_world2"], "source_binary_area_world2": source_binary_geo["area_world2"]}))
        return
    if args.index is None or args.out is None:
        parser.error("Provide --index and --out, or --validate-inputs")
    index_path, out = args.index.resolve(), args.out.resolve()
    index = read(index_path)
    require(index["schema"] == 1 and index["platform"] in ("ios", "android"), "Unsupported capture index")
    strict_receipt = None
    if index.get("strict_verification_json"):
        strict_path = resolve(index["strict_verification_json"], index_path.parent)
        strict = read(strict_path)
        require(index.get("status") == "passed" and strict["schema"] == 1 and strict["status"] == "passed"
                and not strict["errors"] and strict["verifiedHeldEndpoints"] == 12 and strict["verifiedShapeFlatPairs"] == 6,
                "Strict verifier did not pass the complete12-endpoint/six-pair native matrix")
        require(len(strict["observations"]) == 12 and all(row["verifiedHeldEndpoint"] is True and not row["errors"]
                                                        for row in strict["observations"]), "Strict endpoint observations are incomplete or failed")
        require(index.get("expected_shape_captures") == 6 and index.get("verified_shape_captures") == 6,
                "Strict native index does not contain six verified shape/flat pairs")
        strict_receipt = entry(strict_path)
    require(not args.require_strict_verification or strict_receipt is not None, "A passed strict native endpoint index is required")
    index_spec = index.get("shape_spec", index.get("shape_manifest"))
    if index_spec:
        require(resolve(index_spec, index_path.parent) == args.spec.resolve(), "Index refers to another shape spec")
    planned = {stage["id"]: stage for stage in spec["stages"]}
    stage_ids = [row["stage_id"] for row in index["captures"]]
    require(len(stage_ids) == len(set(stage_ids)) and set(stage_ids) <= set(planned), "Duplicate or unplanned capture stage")
    require(args.allow_partial or set(stage_ids) == set(planned), "Missing stage; use --allow-partial for an explicitly partial report")
    require(stage_ids, "No captures supplied")
    require(not out.exists(), "Select a new output directory; refusing to overwrite existing analysis")
    source_bg = np.asarray(spec["world"]["background_rgb"], dtype=float)
    rail = shape["fixed_rail_confounded_band_world_y"]
    rows, displays = [], []
    # Validate all originals before creating output files.
    loaded = []
    for supplied_record in index["captures"]:
        record = dict(supplied_record)
        if record.get("session_json"):
            session_dir = resolve(record["session_json"], index_path.parent).parent
            for key, name in (("external_metadata_json", "external-input-metadata.json"),
                              ("shape_metadata_json", "slider-fixed-shape-coverage-metadata.json")):
                if not record.get(key) and (session_dir / name).is_file():
                    record[key] = str(session_dir / name)
        require(record["shape_id"] == shape["id"], "Stage changed fixed shape identity")
        require(record.get("run"), "Stage lacks capture run identity")
        path = resolve(record.get("png", record.get("held_png")), index_path.parent)
        require(sha(path) == record["sha256"], "Original capture SHA does not match index")
        pixels, encoding = rgb_image(path)
        grid = mapping(record, pixels)
        xx, yy, crop, sampling = crop_roi(pixels, grid, roi)
        require(record.get("actual_control_bounds_world_xywh") is not None or record.get("actual_public_presentation_xywh_world") is not None,
                "Capture needs actual observed bounds with an explicit scope, not requested overlap alone")
        actual_bounds = record.get("actual_control_bounds_world_xywh", record.get("actual_public_presentation_xywh_world"))
        require(len(actual_bounds) == 4 and np.isfinite(actual_bounds).all() and actual_bounds[2] > 0 and actual_bounds[3] > 0,
                "Invalid actual observed control/carrier bounds")
        context = validate_capture_context(record, index_path.parent, shape["source_sha256"], pixels, index["platform"])
        flat_crop = None
        flat_file = None
        flat_pose = None
        if record.get("flat_png"):
            flat_path = resolve(record["flat_png"], index_path.parent)
            require(sha(flat_path) == record["flat_sha256"], "Pose-matched flat PNG hash mismatch")
            flat_pixels, flat_encoding = rgb_image(flat_path)
            require(flat_pixels.shape == pixels.shape and flat_encoding["icc_sha256"] == encoding["icc_sha256"],
                    "Flat/source original raster/profile differs; no registration/color normalization permitted")
            flat_grid = mapping(record.get("flat_geometry", record), flat_pixels)
            require(flat_grid == grid, "Pose-matched flat source pixel grid differs")
            _, _, flat_crop, _ = crop_roi(flat_pixels, flat_grid, roi)
            flat_file = entry(flat_path)
            flat_geometry = record.get("flat_geometry", {})
            flat_bounds = record.get("flat_actual_carrier_bounds_world_xywh", flat_geometry.get("actual_carrier_bounds_world_xywh"))
            shape_bounds = record.get("actual_carrier_bounds_world_xywh", record.get("actual_public_presentation_xywh_world"))
            flat_pose = {"status": "flat_pose_geometry_unverified", "shape_actual_carrier_bounds_world_xywh": shape_bounds,
                         "flat_actual_carrier_bounds_world_xywh": flat_bounds, "registration_performed": False}
            if shape_bounds is not None and flat_bounds is not None:
                delta = np.asarray(shape_bounds, dtype=float) - np.asarray(flat_bounds, dtype=float)
                require(delta.shape == (4,) and np.isfinite(delta).all(), "Invalid shape/flat actual carrier bounds")
                flat_pose.update({"status": "recorded_carrier_bounds_identical" if np.all(delta == 0) else "recorded_carrier_bounds_differ_no_correction",
                                  "shape_minus_flat_carrier_xywh_world": delta.tolist()})
        loaded.append((record, crop, xx, yy, grid, sampling, encoding, entry(path), context, flat_crop, flat_file, flat_pose))
    out.mkdir(parents=True)
    script_snapshot = out / "analysis-script.py"
    script_snapshot.write_bytes(Path(__file__).read_bytes())
    for record, crop, xx, yy, grid, sampling, encoding, original_file, context, flat_crop, flat_file, flat_pose in loaded:
        density = grid["pixels_per_world_unit"]
        has_flat = flat_crop is not None
        residual = crop.astype(float) - (flat_crop.astype(float) if has_flat else source_bg)
        chroma = residual - residual.mean(axis=2, keepdims=True)
        norm = np.linalg.norm(chroma, axis=2)
        ygrid = np.broadcast_to(yy[:, None], norm.shape)
        rail_domain = (ygrid >= rail[0]) & (ygrid <= rail[1])
        union_masks = {t: np.zeros(norm.shape, bool) for t in THRESHOLDS_BYTE}
        signal = np.full(norm.shape, -np.inf)
        membership_count = np.zeros(norm.shape, dtype=np.uint16)
        region_rows = []
        color_identity_display = np.zeros(crop.shape, dtype=np.uint8)
        for region in color_regions:
            projection = chroma @ region["direction"]
            cosine = np.divide(projection, norm, out=np.zeros(norm.shape), where=norm != 0)
            masks = {t: (projection >= t) & (cosine >= MIN_COLOR_COSINE) for t in THRESHOLDS_BYTE}
            for threshold in THRESHOLDS_BYTE:
                union_masks[threshold] |= masks[threshold]
            membership_count += masks[PRIMARY_THRESHOLD_BYTE]
            color_identity_display[masks[PRIMARY_THRESHOLD_BYTE]] = region["spec"]["color_rgb"]
            signal = np.maximum(signal, projection)
            region_descriptors = threshold_descriptors(xx, yy, masks, projection, density, roi, region["edges"], rail_domain)
            region_rows.append({"region_id": region["spec"]["id"], "original_color_rgb": region["spec"]["color_rgb"],
                "original_color_direction_unit_rgb": region["direction"].tolist(),
                "raw_color_direction_projection_byte": projection.tolist(), "raw_color_direction_cosine": cosine.tolist(),
                "threshold_sensitivity": region_descriptors,
                "positive_projection_weighted_visible_signal": byte_signal_moments(xx, yy, np.maximum(projection, 0.) * masks[PRIMARY_THRESHOLD_BYTE], density),
                "visible_directional_support": fixed_direction_support(xx, yy, masks[PRIMARY_THRESHOLD_BYTE], shape),
                **observed_color_regions(xx, yy, crop, masks[PRIMARY_THRESHOLD_BYTE], density),
                "source_frame_edge_color_profile": source_edge_profile(xx, yy, crop, projection, region["support"], region["edges"], source_density),
                "classification_policy": "Independent fixed color-direction cone; a pixel can belong to multiple color identities. Overlap is retained as ambiguity, never resolved by nearest-color assignment."})
        thresholds = threshold_descriptors(xx, yy, union_masks, signal, density, roi, source_edges, rail_domain)
        primary = next(d for d in thresholds if d["threshold_projection_byte"] == PRIMARY_THRESHOLD_BYTE)
        primary_mask = union_masks[PRIMARY_THRESHOLD_BYTE]
        raw_channel_transport = []
        for ci, channel in enumerate("RGB"):
            value = residual[:, :, ci]
            raw_channel_transport.append({"channel": channel,
                "declared_source_region_channel_deltas_byte": {r["spec"]["id"]: float(r["spec"]["color_rgb"][ci] - source_bg[ci]) for r in color_regions},
                "signed": byte_signal_moments(xx, yy, value, density),
                "positive_polarity": byte_signal_moments(xx, yy, np.maximum(value, 0), density),
                "negative_polarity_magnitude": byte_signal_moments(xx, yy, np.maximum(-value, 0), density),
                "scope": "Raw channel first/second moments across the same fixed ROI; no recovered ray correspondence."})
        geo = primary["geometry"]
        centroid = geo["centroid_world"]
        displacement = None if centroid is None else float(np.linalg.norm(np.asarray(centroid) - source_geo["centroid_world"]))
        axes = geo["principal_axes"]
        actual_carrier = record.get("actual_carrier_bounds_world_xywh", record.get("actual_public_presentation_xywh_world"))
        actual_center = None if actual_carrier is None else [actual_carrier[0] + actual_carrier[2] / 2., actual_carrier[1] + actual_carrier[3] / 2.]
        target_center = planned[record["stage_id"]]["requested_lens_center_world_pt"]
        actual_minus_target = None if actual_center is None else (np.asarray(actual_center) - target_center).tolist()
        requested_carrier = requested_public_bounds(spec, planned[record["stage_id"]])
        source_render_scale = np.asarray(record.get("source_declared_world_to_actual_dp_scale_xy", [1., 1.]), dtype=float)
        require(source_render_scale.shape == (2,) and np.isfinite(source_render_scale).all() and np.all(source_render_scale > 0),
                "Invalid observed source layout render scale")
        actual_source_samples = source_area_points * source_render_scale
        requested_overlap = public_bounds_overlap(actual_source_samples, source_area_weights, requested_carrier)
        actual_overlap = public_bounds_overlap(actual_source_samples, source_area_weights, actual_carrier)
        requested_fraction = requested_overlap.get("declared_capsule_source_area_fraction")
        actual_fraction = actual_overlap.get("declared_capsule_source_area_fraction")
        nominal_fraction = planned[record["stage_id"]].get("requested_fraction")
        comparison = {"nominal_requested_fraction": nominal_fraction,
                      "nominal_fraction_scope": "declared continuous polygon planning target, not measured native coverage",
                      "requested_discrete_capsule_fraction": requested_fraction,
                      "actual_discrete_capsule_fraction": actual_fraction,
                      "actual_minus_requested_discrete_capsule_fraction": None if requested_fraction is None or actual_fraction is None else actual_fraction - requested_fraction,
                      "actual_minus_nominal_capsule_fraction": None if nominal_fraction is None or actual_fraction is None else actual_fraction - nominal_fraction,
                      "scope": "same original4x4 source sample integral within requested/actual public-bounds capsules; not optical alpha"}
        flags = ["color_evidence_is_not_optical_alpha", "no_contour_completion_or_component_selection", "nominal_coverage_is_not_measured_coverage"]
        if np.any(source_render_scale != 1):
            flags.append("original_source_rendered_into_observed_integer_layout_scale_not_ideal_world_size")
        if not has_flat:
            flags.append("no_pose_matched_flat_material_highlights_and_rail_can_share_color_direction")
        elif flat_pose["status"] != "recorded_carrier_bounds_identical":
            flags.append(flat_pose["status"])
        if primary["rail_domain_evidence_pixel_count"]:
            flags.append("color_evidence_intersects_conservative_rail_confounded_domain")
        if primary["boundary_evidence_pixel_count"]:
            flags.append("color_evidence_touches_fixed_ROI_boundary_support_may_be_clipped")
        if len(primary["components_eight_connected_raster_order"]) > 1:
            flags.append("multiple_color_components_all_retained_no_forced_identity")
        if not primary_mask.any():
            flags.append("source_shape_unobserved_at_declared_color_threshold")
        if np.any(membership_count > 1):
            flags.append("multiple_region_color_cones_overlap_no_unique_color_identity_assignment")
        color_identity_display[membership_count > 1] = [255, 255, 255]
        stem = record["stage_id"]
        # Rendering the original source at a different measurement density is
        # allowed only here, for the explicitly display-only contact sheet.
        source_display = np.asarray(Image.fromarray(source_crop).resize((crop.shape[1], crop.shape[0]), Image.Resampling.NEAREST))
        display_images = make_stage_images(out, stem, source_display, crop, primary_mask, signal, xx, yy, density, source_edges, rail, has_flat)
        display_images["color_regions"] = Image.fromarray(color_identity_display)
        display_images["color_regions"].save(out / f"{stem}-color-region-evidence-white-ambiguous.png")
        displays.append(display_images)
        rows.append({"stage_id": stem, "shape_id": shape["id"], "run": record["run"], "planned_stage": planned[stem],
                     "actual_observed_bounds_world_xywh": record.get("actual_control_bounds_world_xywh", record.get("actual_public_presentation_xywh_world")),
                     "actual_bounds_scope": record.get("bounds_kind", record.get("carrier_bounds_scope", "unspecified scope; not optical alpha")),
                     "actual_carrier_bounds_world_xywh": record.get("actual_carrier_bounds_world_xywh"),
                     "actual_carrier_center_world": actual_center, "planned_lens_center_world": target_center,
                     "actual_minus_planned_carrier_center_world": actual_minus_target,
                     "requested_carrier_bounds_world_xywh": requested_carrier,
                     "requested_public_bounds_source_overlap": requested_overlap,
                     "actual_public_bounds_source_overlap": actual_overlap,
                     "source_declared_world_to_actual_dp_scale_xy": source_render_scale.tolist(),
                     "source_render_scope": "Original source masks kept in canonical375x667 coordinates; geometric overlap uses their exact original samples mapped by observed integer layout scale. Device pixels remain on original actual-density grid; no registration or image resampling.",
                     "android_actual_target_center_world": record.get("android_actual_target_center_world"),
                     "requested_actual_public_geometry_comparison": comparison,
                     "mapping": grid, "sampling": sampling, "original_capture": original_file, "capture_encoding": encoding,
                     "capture_context": context, "pose_matched_flat_supplied": has_flat, "flat_capture": flat_file,
                     "flat_pose_geometry_check": flat_pose,
                     "signal_definition": "Independent chroma(shape_capture-flat_capture) projections onto each original region color; whole evidence is union" if has_flat else
                                          "Independent chroma(capture-neutral128) projections onto each original region color; whole evidence is union; rail/material remain confounded",
                     "raw_original_roi_rgb_bytes": crop.tolist(), "raw_maximum_palette_projection_byte": signal.tolist(),
                     "primary_color_membership_count": membership_count.tolist(),
                     "ambiguous_multiple_region_color_pixels": int(np.count_nonzero(membership_count > 1)),
                     "color_region_responses": region_rows,
                     "threshold_sensitivity": thresholds, "primary_threshold_byte": PRIMARY_THRESHOLD_BYTE,
                     "visible_directional_support": fixed_direction_support(xx, yy, primary_mask, shape),
                     **observed_color_regions(xx, yy, crop, primary_mask, density),
                     "interior_definition": "at least0.75world units inside the observed color-evidence cell-edge boundary, if present",
                     "source_frame_edge_color_profile": source_edge_profile(xx, yy, crop, signal, source_support, source_edges, source_density),
                     "channel_color_transport": raw_channel_transport, "ambiguity_flags": flags,
                     "summary": {"area_ratio": geo["area_world2"] / source_primary_rule_area,
                                 "area_ratio_denominator": "original source evaluated with same frozen primary color rule, not AA weighted area",
                                 "area_ratio_over_original_AA_weighted_mask": geo["area_world2"] / source_geo["area_world2"],
                                 "observed_evidence_area_world2": geo["area_world2"], "centroid_displacement": displacement,
                                 "axis_ratio": None if axes is None else axes["axis_length_ratio"]}})
    contact_path, chart_path = out / "source-visible-contact-sheet.png", out / "six-stage-descriptors.png"
    contact_sheet(contact_path, displays, rows)
    line_chart(chart_path, rows)
    result = {"schema": 1, "status": "descriptive_saved_shape_color_evidence_no_parity_verdict", "platform": index["platform"],
              "complete_six_stage_set": set(stage_ids) == set(planned), "shape_id": shape["id"],
              "native_endpoint_validity": {"source": "strict_endpoint_verifier" if strict_receipt else "no_strict_verifier_validity_verdict",
                                           "strict_report": strict_receipt},
              "provenance": {"index": entry(index_path), "script": entry(script_snapshot), "executing_script_path": str(Path(__file__).resolve()), **provenance},
              "fixed_analysis_policy": {"projection_thresholds_byte": list(THRESHOLDS_BYTE), "primary_projection_threshold_byte": PRIMARY_THRESHOLD_BYTE,
                                        "minimum_color_cosine": MIN_COLOR_COSINE, "fixed_roi_xyxy_world": roi,
                                        "morphological_closing_or_opening": False, "largest_component_selection": False,
                                        "color_profile_normalization_or_registration": False,
                                        "region_color_direction_unit_rgb": {r["spec"]["id"]: r["direction"].tolist() for r in color_regions}},
              "source": {"shape": shape, "original_area_weighted_geometry": source_geo, "original_binary_support_geometry": source_binary_geo,
                         "original_cell_edge_segments_world": source_edges.tolist(), "original_inner_color_statistics": color_stats(source_crop, source_roi_coverage == 1),
                         "original_directional_support": fixed_direction_support(sxx, syy, source_roi_support, shape),
                         "source_area_sample_method_for_public_geometry": source_area_sample_method,
                         "same_frozen_color_rule_original_source_sensitivity": source_same_color_rule,
                         "color_regions": region_geometry},
              "stages": rows, "display_only_figures": [entry(contact_path), entry(chart_path)],
              "interpretation_limits": [
                  "Color evidence masks are observable threshold sets, not recovered optical alpha or guaranteed complete source silhouettes. All components and threshold variants are retained.",
                  "No invisible region is filled. Boundary clipping, rail/color confounds and missing observations remain explicit. Rail-excluded geometry is a restricted-domain descriptor, never a completed object.",
                  "All measurements use original stored device pixels and original source masks with recorded world mapping. Only contact-sheet display tiles are resized.",
                  "Declared nominal overlap is planning geometry. Public control/carrier bounds are not optical alpha. No nominal percentage is labeled achieved native coverage.",
                  "Area, moments, principal axes, edge distances and color distributions describe visible responses; they do not establish pointwise rays, physical thickness, causal refraction or native parity.",
                  "Single shape/six settled poses is feasibility evidence, not all sizes, colors, backgrounds, action timing or dynamics acceptance.",
              ]}
    (out / "analysis.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "shape_id": shape["id"], "stages": len(rows),
                      "pose_matched_flat_stages": sum(r["pose_matched_flat_supplied"] for r in rows),
                      "complete_six_stage_set": result["complete_six_stage_set"], "out": str(out)}))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError) as error:
        raise SystemExit(f"Shape capture analysis invalid: {error}") from error
