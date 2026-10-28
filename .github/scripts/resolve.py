"""Validate the cross-repository dispatch contract before scheduling any work."""

import argparse
import json
import os
import re
from pathlib import Path

BACKENDS = ("runtime", "ty", "pyrefly")
FEATURES = {"lsp": "runtime", "lsp-ty": "ty", "lsp-pyrefly": "pyrefly"}
CHANNELS = ("alpha", "beta", "rc", "stable")


def resolve(event, inputs, event_name):
    payload = event.get("client_payload", {}) if event_name == "repository_dispatch" else {}
    if not isinstance(payload, dict):
        raise ValueError("client_payload must be an object")
    sha = payload.get("sha") or inputs.get("source_sha", "")
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-fA-F]{40}", sha):
        raise ValueError("source_sha must be a full 40-character commit SHA")
    ref = payload.get("ref") or inputs.get("source_ref") or "main"
    if not isinstance(ref, str) or not ref or any(ord(c) < 32 for c in ref):
        raise ValueError("source_ref must be a non-empty single-line ref")
    legacy = payload.get("features")
    if legacy is not None and (not isinstance(legacy, str) or legacy not in FEATURES):
        raise ValueError("Unsupported legacy features; use backend=all|runtime|ty|pyrefly")
    if payload.get("package", "apk") != "apk":
        raise ValueError("Only package=apk is supported")
    backend = payload.get("backend") or FEATURES.get(legacy) or inputs.get("backend") or "all"
    if backend not in ("all", *BACKENDS):
        raise ValueError("backend must be all, runtime, ty, or pyrefly")
    release = payload.get("release", inputs.get("release", False))
    if not isinstance(release, bool):
        raise ValueError("release must be a JSON boolean")
    release_backend = payload.get("release_backend") or inputs.get("release_backend") or "ty"
    # Retain the old run-release entry point, but always run the full test gate.
    if event_name == "repository_dispatch" and event.get("action") == "run-release":
        release = True
        release_backend = payload.get("release_backend") or payload.get("backend") or FEATURES.get(legacy) or release_backend
        backend = "all"
    channel = payload.get("release_channel") or inputs.get("release_channel") or "alpha"
    if release_backend not in BACKENDS or channel not in CHANNELS:
        raise ValueError("Invalid release backend or channel")
    if release and backend != "all":
        raise ValueError("Releases require backend=all")
    return {
        "sha": sha.lower(), "ref": ref, "backend": backend,
        "release": str(release).lower(), "release_backend": release_backend,
        "channel": channel,
        "status_context": "apk-build / tests" + (f" ({backend})" if backend != "all" else ""),
    }


def resolve_publish(inputs):
    # The internal publisher accepts a single backend, after the test gate.
    request = {**inputs, "backend": "all", "release": True,
               "release_backend": inputs.get("backend")}
    if request["release_backend"] not in BACKENDS:
        raise ValueError("A publisher must select one release backend")
    return resolve({}, request, "workflow_call")


def resolve_benchmark(event, inputs):
    # Reusable-workflow inputs override the caller's repository_dispatch event.
    request = inputs if inputs.get("source_sha") else event.get("client_payload", {})
    if not isinstance(request, dict):
        raise ValueError("Benchmark request must be an object")
    mode = request.get("benchmark_mode") or "performance"
    backend = request.get("backend") or "ty"
    if mode not in ("smoke", "performance") or backend not in BACKENDS:
        raise ValueError("Invalid benchmark mode or backend")
    result = resolve({}, {
        "source_sha": request.get("source_sha") or request.get("sha"),
        "source_ref": request.get("source_ref") or request.get("ref"),
        "backend": backend,
    }, "workflow_call")
    return {"sha": result["sha"], "ref": result["ref"], "backend": backend, "mode": mode}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--publish", action="store_true")
    modes.add_argument("--benchmark", action="store_true")
    args = parser.parse_args()
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    inputs = json.loads(os.environ.get("INPUTS_JSON") or "{}") or {}
    if args.publish:
        if os.environ["GITHUB_EVENT_NAME"] == "repository_dispatch" and event.get("action") == "run-release":
            result = resolve(event, inputs, "repository_dispatch")
        else:
            result = resolve_publish(inputs)
    elif args.benchmark:
        result = resolve_benchmark(event, inputs)
    else:
        result = resolve(event, inputs, os.environ["GITHUB_EVENT_NAME"])
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        for key, value in result.items():
            output.write(f"{key}={value}\n")
    print(json.dumps(result, indent=2))
