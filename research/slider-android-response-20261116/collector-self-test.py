#!/usr/bin/env python3
"""Exercise collector failure preservation with mocks and auto-cleaned temp files.

No command is executed by this test. It checks failure handling, not screenshots,
device capture validity, or optical acceptance.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
COLLECTOR = HERE / "capture.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def run_case(name, pull_fails=False, display_fails=False):
    with tempfile.TemporaryDirectory(prefix="glass-collector-mock-") as temp:
        scratch = Path(temp)
        assets = scratch / "assets"
        root = assets / "research/slider-android-response-20261116"
        host = scratch / "host"
        source = assets / "research/slider-color-response-20261116/inputs/rounds/control-pre"
        spec = root / "derived/control-pre/shape-spec.json"
        marker = source / "inputs/mock-marker.png"
        write(spec, b'{"mock":true}\n')
        write(marker, b"mock original source bytes\x00\x80\xff")
        manifest = source / "inputs/manifest.json"
        write(manifest, (json.dumps({"split": "calibration", "inputs": [
            {"file": marker.name, "sha256": sha(marker), "bytes": marker.stat().st_size}
        ]}) + "\n").encode())
        write(assets / "research/slider-android-host/host-build-20261116.json", b'{}\n')
        write(host / "frozen-source.kt", b"// mock frozen host\n")
        host_commit = "a" * 40
        apk_hashes = {"com.lingion.sleepy.debug": "b" * 64,
                      "com.lingion.sleepy.debug.test": "c" * 64}
        freeze = {"files": {str(spec.relative_to(root)): sha(spec)},
                  "host_files": {"frozen-source.kt": sha(host / "frozen-source.kt")},
                  "host_commit": host_commit,
                  "apks": [{"application_id": key, "sha256": value}
                           for key, value in apk_hashes.items()]}
        write(root / "FREEZE.json", (json.dumps(freeze) + "\n").encode())
        module_spec = importlib.util.spec_from_file_location("mocked_glass_capture", COLLECTOR)
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        module.ROOT, module.ASSETS = root, assets
        tag = "mock-" + name
        out = root / "evidence/rounds/control-pre" / tag
        remote_result = ("/sdcard/Android/data/com.lingion.sleepy.debug/files/slider-optical-world/"
                         f"g-response-control-pre-{tag}-{sha(spec)[:12]}-20261116")
        remote_files = {"result.json": b'{"status":"running","mock":true}\n',
                        "partial-held-screen.png": b"mock partial original bytes\x00\x80\xff"}
        pushed_hashes, calls = {}, []
        display_calls = 0
        probe_calls = 0
        instrument_calls = 0
        timeout = subprocess.TimeoutExpired("mock-instrumentation", 240,
                                            output=b"partial stdout\n", stderr="partial stderr\n")

        def fake_run(argv, **kwargs):
            nonlocal display_calls
            command = [str(value) for value in argv]
            calls.append(command)
            if command == ["git", "-C", str(host), "rev-parse", "HEAD"]:
                return host_commit
            if command == ["git", "-C", str(host), "status", "--porcelain"]:
                return ""
            assert command[:3] == ["mock-adb", "-s", "mock-serial"], command
            device = command[3:]
            if len(device) == 3 and device[:2] == ["shell", "wm"]:
                display_calls += 1
                if display_calls > 2 and display_fails:
                    raise RuntimeError("mock display disconnected")
                return {"size": "Physical size: 1216x2640",
                        "density": "Physical density: 476"}[device[2]]
            if device[:3] == ["shell", "pm", "path"]:
                return "package:/mock-installed/" + device[3] + ".apk"
            if device[:2] == ["shell", "sha256sum"]:
                remote = device[2]
                if remote.startswith("/mock-installed/"):
                    application_id = Path(remote).name.removesuffix(".apk")
                    return apk_hashes[application_id] + "  " + remote
                return pushed_hashes[remote] + "  " + remote
            if device[:3] == ["shell", "mkdir", "-p"]:
                return ""
            if device[0] == "push":
                pushed_hashes[device[2]] = sha(Path(device[1]))
                return "mock source pushed"
            if device[0] == "pull":
                assert device[1] == remote_result and device[2] == str(out / "trace")
                if pull_fails:
                    raise RuntimeError("mock partial pull disconnected")
                for filename, data in remote_files.items():
                    write(Path(device[2]) / filename, data)
                return "mock partial evidence pulled"
            if device[:2] == ["shell", "find"]:
                assert device[2] == remote_result
                return "\n".join(hashlib.sha256(data).hexdigest() + "  " + remote_result + "/" + filename
                                 for filename, data in remote_files.items())
            raise AssertionError("Unexpected command: " + repr(command))

        def fake_subprocess_run(argv, **kwargs):
            nonlocal probe_calls, instrument_calls
            command = [str(value) for value in argv]
            calls.append(command)
            assert command[:3] == ["mock-adb", "-s", "mock-serial"], command
            if command[3:6] == ["shell", "test", "-e"]:
                probe_calls += 1
                assert command[6] == remote_result
                return SimpleNamespace(returncode=1, stdout="", stderr="")
            if command[3:6] == ["shell", "am", "instrument"]:
                instrument_calls += 1
                assert kwargs["timeout"] == 240
                raise timeout
            raise AssertionError("Unexpected subprocess: " + repr(command))

        caught = None
        argv = [str(COLLECTOR), "--host", str(host), "--adb", "mock-adb",
                "--serial", "mock-serial", "--round", "control-pre", "--tag", tag]
        with patch.object(sys, "argv", argv), patch.object(module, "run", fake_run), \
                patch.object(module.subprocess, "run", fake_subprocess_run):
            try:
                module.main()
            except BaseException as error:
                caught = error
        assert caught is timeout, "Recovery/finalization replaced the original timeout"
        assert probe_calls == instrument_calls == 1
        assert (out / "instrumentation.txt").read_text() == "partial stdout\npartial stderr\n"
        receipt = json.loads((out / "receipt.json").read_text())
        assert receipt["error"] == repr(timeout)
        assert receipt["instrumentation_timeout_seconds"] == 240
        assert receipt["finished_unix"] >= receipt["started_unix"]
        assert receipt["test_passed"] is False
        assert receipt["collector_sha256"] == sha(COLLECTOR)
        assert receipt["freeze_sha256"] == sha(root / "FREEZE.json")
        assert len(receipt["input_sha256"]) == 3
        assert len(receipt["packages"]) == 2
        if pull_fails:
            assert "mock partial pull disconnected" in receipt["partial_evidence_recovery_error"]
            assert receipt["files"] == []
        else:
            assert "partial_evidence_recovery_error" not in receipt
            assert len(receipt["files"]) == len(remote_files)
            for record in receipt["files"]:
                actual = out / record["file"]
                assert actual.read_bytes() == remote_files[actual.name]
                assert record["sha256"] == sha(actual) and record["host_device_match"] is True
        if display_fails:
            assert "mock display disconnected" in receipt["display_after_error"]
        else:
            assert receipt["display_after"] == receipt["display_before"]
        assert not any("settings" in command or "install" in command or "uninstall" in command
                       for command in calls)
        result = {"case": name, "status": "passed", "original_timeout_preserved": True,
                  "instrumentation_output_saved": True, "finished_receipt_saved": True,
                  "partial_pull": "failed_and_recorded" if pull_fails else "preserved_and_hash_verified",
                  "display_after": "failed_and_recorded" if display_fails else "recorded",
                  "external_commands_executed": 0}
    assert not scratch.exists(), "Temporary test directory was not automatically removed"
    result["temporary_files_cleaned"] = True
    return result


def main():
    cases = [run_case("timeout-pull-ok"),
             run_case("timeout-display-fails", display_fails=True),
             run_case("timeout-pull-and-display-fail", pull_fails=True, display_fails=True)]
    print(json.dumps({"status": "passed", "collector_sha256": sha(COLLECTOR),
                      "scope": "Pure mocked failure-preservation checks; no device, Git, build, or optical validation.",
                      "cases": cases}, indent=2))


if __name__ == "__main__":
    main()
