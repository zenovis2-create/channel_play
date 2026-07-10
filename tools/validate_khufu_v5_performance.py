from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path


METRIC_NAMES = {
    "frame_p95_ms": "Frame time",
    "main_thread_p95_ms": "Main thread",
    "render_thread_p95_ms": "Render thread",
    "gpu_p95_ms": "GPU frame",
}

MEMORY_NAMES = {
    "maximum_allocated_mb": "Maximum total allocated memory",
    "maximum_reserved_mb": "Maximum total reserved memory",
    "maximum_managed_mb": "Maximum managed memory",
}

COUNT_NAMES = {
    "maximum_visible_renderers": "Visible renderers",
    "maximum_visible_vertices": "Visible mesh vertices",
    "maximum_visible_triangles": "Visible mesh triangles",
}


def extract(pattern: str, text: str, label: str, failures: list[str]) -> str | None:
    match = re.search(pattern, text, re.MULTILINE)
    if match is None:
        failures.append(f"missing {label}")
        return None
    return match.group(1)


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as stream:
        header = stream.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError("invalid PNG signature or IHDR")
    return struct.unpack(">II", header[16:24])


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate(args: argparse.Namespace) -> tuple[bool, list[str], dict[str, float | int | str]]:
    budget = json.loads(args.budget.read_text(encoding="utf-8"))
    limits = budget["limits"]
    text = args.receipt.read_text(encoding="utf-8")
    failures: list[str] = []
    observed: dict[str, float | int | str] = {}

    if "PROFILE_RESULT: recorded" not in text:
        failures.append("missing PROFILE_RESULT: recorded")

    resolution = extract(r"^- Resolution: `([^`]+)`", text, "resolution", failures)
    quality = extract(r"quality `([^`]+)`", text, "quality", failures)
    if resolution is not None:
        observed["resolution"] = resolution
        if resolution != budget["target"]["resolution"]:
            failures.append(f"resolution {resolution} != {budget['target']['resolution']}")
    if quality is not None:
        observed["quality"] = quality
        if quality != budget["target"]["quality"]:
            failures.append(f"quality {quality} != {budget['target']['quality']}")

    samples = extract(r"^- Samples: `(\d+)`", text, "sample count", failures)
    if samples is not None:
        observed["samples"] = int(samples)
        if int(samples) < limits["minimum_samples"]:
            failures.append(f"samples {samples} < {limits['minimum_samples']}")

    for limit_key, metric_name in METRIC_NAMES.items():
        value = extract(
            rf"^- {re.escape(metric_name)} median: `[0-9.]+ ms`; p95: `([0-9.]+) ms`",
            text,
            f"{metric_name} p95",
            failures,
        )
        if value is not None:
            observed[limit_key] = float(value)
            if float(value) > limits[limit_key]:
                failures.append(f"{limit_key} {value} > {limits[limit_key]}")

    for limit_key, metric_name in MEMORY_NAMES.items():
        value = extract(rf"^- {re.escape(metric_name)}: `([0-9.]+) MB`", text, metric_name, failures)
        if value is not None:
            observed[limit_key] = float(value)
            if float(value) > limits[limit_key]:
                failures.append(f"{limit_key} {value} > {limits[limit_key]}")

    for limit_key, metric_name in COUNT_NAMES.items():
        value = extract(rf"^- {re.escape(metric_name)}: `(\d+)`", text, metric_name, failures)
        if value is not None:
            observed[limit_key] = int(value)
            if int(value) > limits[limit_key]:
                failures.append(f"{limit_key} {value} > {limits[limit_key]}")

    if not args.profiler_raw.is_file():
        failures.append(f"missing profiler raw file: {args.profiler_raw}")
    else:
        raw_size = args.profiler_raw.stat().st_size
        observed["profiler_raw_bytes"] = raw_size
        if not limits["minimum_profiler_raw_bytes"] <= raw_size <= limits["maximum_profiler_raw_bytes"]:
            failures.append(f"profiler raw bytes {raw_size} outside accepted range")

    screenshot_hashes: set[str] = set()
    for screenshot in args.screenshots:
        if not screenshot.is_file():
            failures.append(f"missing screenshot: {screenshot}")
            continue
        try:
            width, height = png_dimensions(screenshot)
        except ValueError as error:
            failures.append(f"{screenshot.name}: {error}")
            continue
        if f"{width}x{height}" != budget["target"]["resolution"]:
            failures.append(f"{screenshot.name}: {width}x{height} is not target resolution")
        if screenshot.stat().st_size < limits["minimum_screenshot_bytes"]:
            failures.append(f"{screenshot.name}: screenshot too small")
        screenshot_hashes.add(sha256(screenshot))
    if len(screenshot_hashes) != len(args.screenshots):
        failures.append("screenshots are missing or duplicate")

    if not args.player_log.is_file():
        failures.append(f"missing player log: {args.player_log}")
    else:
        log_text = args.player_log.read_text(encoding="utf-8", errors="replace")
        bad_lines = [
            line
            for line in log_text.splitlines()
            if re.search(r"(^|[\s:])(error|exception|crash)([\s:]|$)", line, re.IGNORECASE)
        ]
        if bad_lines:
            failures.append("player log contains error/exception/crash markers")

    return not failures, failures, observed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--profiler-raw", type=Path, required=True)
    parser.add_argument("--player-log", type=Path, required=True)
    parser.add_argument("--screenshots", type=Path, nargs=2, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    passed, failures, observed = validate(args)
    lines = [
        "# Khufu V5 Performance Validation",
        "",
        f"- Verdict: **{'passed' if passed else 'failed'}**",
        f"- Budget: `{args.budget.as_posix()}`",
        f"- Performance receipt: `{args.receipt.as_posix()}`",
        f"- Observed: `{json.dumps(observed, sort_keys=True)}`",
    ]
    lines.extend(f"- Failure: {failure}" for failure in failures)
    lines.extend(["", f"PERFORMANCE_VERDICT: {'passed' if passed else 'failed'}", ""])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(lines[-2])
    for failure in failures:
        print(f"FAIL: {failure}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
