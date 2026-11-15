#!/usr/bin/env python3
"""Read existing frozen PNG metadata; --write creates the audit, otherwise verifies it.

No image decoder, color conversion, pixel analysis, capture, build, or source edit.
Paths are relative to the asset repository so verification survives relocation.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import zlib

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
STUDY = REPO / "research/slider-color-response-20261116"
OUTPUT = HERE / "native-color-metadata.json"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def relative(path):
    return path.relative_to(REPO).as_posix()


def metadata(path, expected_sha):
    data = path.read_bytes()
    require(sha(data) == expected_sha, "Original PNG SHA mismatch: " + relative(path))
    require(data[:8] == b"\x89PNG\r\n\x1a\n", "Missing PNG signature")
    row = {"path": relative(path), "png_sha256": sha(data), "bytes": len(data)}
    chunks, color, position = [], {}, 8
    while position + 12 <= len(data):
        count = int.from_bytes(data[position:position + 4], "big")
        kind = data[position + 4:position + 8]
        require(count <= len(data) - position - 12, "Truncated PNG chunk")
        payload = data[position + 8:position + 8 + count]
        crc = int.from_bytes(data[position + 8 + count:position + 12 + count], "big")
        require(zlib.crc32(kind + payload) & 0xffffffff == crc, "PNG chunk CRC mismatch")
        name = kind.decode("ascii")
        chunks.append(name)
        if kind == b"IHDR":
            require(len(payload) == 13 and "ihdr" not in row, "Malformed or duplicate IHDR")
            values = struct.unpack(">IIBBBBB", payload)
            row["ihdr"] = dict(zip(("width", "height", "bit_depth", "color_type", "compression", "filter", "interlace"), values))
        elif kind == b"iCCP":
            require(name not in color, "Duplicate iCCP")
            keyword, compressed = payload.split(b"\0", 1)
            require(compressed[0] == 0, "Unsupported ICC compression")
            profile = zlib.decompress(compressed[1:])
            require(len(profile) >= 128 and int.from_bytes(profile[:4], "big") == len(profile), "Malformed ICC header")
            color[name] = {"keyword": keyword.decode("latin1"), "profile_bytes": len(profile),
                           "profile_sha256": sha(profile), "data_color_space": profile[16:20].decode("latin1"),
                           "profile_connection_space": profile[20:24].decode("latin1")}
        elif kind == b"sRGB":
            require(name not in color and len(payload) == 1, "Malformed or duplicate sRGB")
            color[name] = {"rendering_intent": payload[0]}
        elif kind == b"gAMA":
            require(name not in color and len(payload) == 4, "Malformed or duplicate gAMA")
            color[name] = {"integer_value": int.from_bytes(payload, "big")}
        elif kind == b"cHRM":
            require(name not in color and len(payload) == 32, "Malformed or duplicate cHRM")
            color[name] = {"integer_values": list(struct.unpack(">8I", payload))}
        position += count + 12
        if kind == b"IEND":
            require(count == 0 and position == len(data), "Malformed IEND or trailing data")
            break
    require(chunks[0] == "IHDR" and chunks[-1] == "IEND" and "IDAT" in chunks, "Incomplete PNG")
    require(row["ihdr"]["width"] == 750 and row["ihdr"]["height"] == 1334, "Unexpected PNG geometry")
    row.update(chunk_types=chunks, color_chunk_markers={k: k in color for k in ("sRGB", "iCCP", "gAMA", "cHRM")},
               color_chunks=color, all_chunk_crcs_valid=True)
    return row


def document():
    manifest_path = STUDY / "evidence/manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    freeze = STUDY / "freeze.json"
    require(sha(freeze.read_bytes()) == manifest["freeze_sha256"], "Frozen study differs from portable manifest")
    rounds_path = STUDY / "inputs/rounds.json"
    rounds = json.loads(rounds_path.read_bytes())
    require(len(rounds["rounds"]) == 8, "Expected eight existing formal rounds")
    captures, inputs = [], []
    for item in rounds["rounds"]:
        prefix = "rounds/" + item["id"] + "/native-r1/held/"
        paths = sorted((p, v) for p, v in manifest["files"].items() if p.startswith(prefix) and p.endswith(".png"))
        require(len(paths) == 2, "Expected exactly shape and flat captures for " + item["id"])
        for name, record in paths:
            row = metadata(STUDY / "evidence" / name, record["sha256"])
            require(row["bytes"] == record["bytes"], "Portable evidence byte size differs")
            row.update(round=item["id"], role="flat" if "st00_flat128" in name else "shape")
            captures.append(row)
        directory = STUDY / "inputs" / item["input_dir"]
        source_manifest = json.loads((directory / "manifest.json").read_bytes())
        source_rows = {entry["id"]: entry for entry in source_manifest["inputs"]}
        for role, key in (("shape", "first_input_id"), ("flat", "flat_input_id")):
            source = source_rows[item[key]]
            row = metadata(directory / source["file"], source["sha256"])
            row.update(round=item["id"], role=role, input_id=item[key])
            inputs.append(row)
    require(len(captures) == len(inputs) == 16, "Expected sixteen captures and sixteen scheduled input paths")
    require(all(r["color_chunks"] == {"sRGB": {"rendering_intent": 0}} for r in captures), "Capture color marker differs")
    iccs = sorted({r["color_chunks"]["iCCP"]["profile_sha256"] for r in inputs})
    require(len(iccs) == 1 and all(r["color_chunk_markers"]["iCCP"] for r in inputs), "Input ICC changed")
    return {
        "schema": 1, "scope": "Metadata-only audit of existing frozen formal inputs and original native captures; no new experiment",
        "source_study": relative(STUDY), "portable_manifest": relative(manifest_path),
        "portable_manifest_sha256": sha(manifest_bytes), "freeze_sha256": sha(freeze.read_bytes()),
        "rounds_index_sha256": sha(rounds_path.read_bytes()),
        "method": "Read PNG signature, IHDR, ordered chunk names, CRCs and color-description payloads directly from original bytes; no IDAT/image decoding or color conversion",
        "summary": {"native_capture_count": 16, "scheduled_input_path_count": 16,
                    "all_native_captures_have_sRGB_chunk": True, "native_rendering_intent": 0,
                    "native_iCCP_gAMA_cHRM_present": False, "input_icc_sha256": iccs,
                    "native_output_label": "sRGB, as declared by each original PNG sRGB chunk"},
        "interpretation_limits": [
            "PNG output color labels and input ICC identity do not identify UIKit's internal material working color space, transfer functions, blending, or processing order.",
            "This audit does not prove optical parity or fit any color matrix, saturation, gamma, clamp, or physical glass model.",
            "Existing analyze-response.py checks source ICC equality, but ignores capture ICC and does not lock the PNG sRGB marker; this separate audit records the missing metadata constraint.",
            "sRGB intent0 on all captures rejects a mixed-output-label explanation for these files; it does not independently measure their encoded pixel correctness."
        ],
        "inputs": inputs, "native_captures": captures,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Create new metadata receipt, refusing replacement")
    args = parser.parse_args()
    expected = document()
    if args.write:
        with OUTPUT.open("x") as stream:
            json.dump(expected, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
    else:
        require(json.loads(OUTPUT.read_bytes()) == expected, "Metadata receipt differs from original frozen files")
    print(json.dumps({"status": "written" if args.write else "verified", "receipt": relative(OUTPUT),
                      "native_captures": len(expected["native_captures"]), "inputs": len(expected["inputs"])}))


if __name__ == "__main__":
    main()
