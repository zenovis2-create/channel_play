#!/usr/bin/env python3
"""Validate the Khufu V5 documentation and evidence harness."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


DOC_DIR = Path("docs/khufu-v5")
BUILD_BINDING_MANIFEST = Path("runs/khufu-mega-labyrinth-v5/build-input-binding.json")
IMPLEMENTATION_FABLE_REVIEW = Path(
    "work/fable-harness/khufu-v5-implementation-final-review.fable.md"
)
IMPLEMENTATION_FABLE_META = Path(
    "work/fable-harness/khufu-v5-implementation-final-review.fable.md.meta.json"
)
REQUIRED_DOCS = (
    "README.md",
    "GOAL.md",
    "PLAN.md",
    "STATUS.md",
    "TEST_PLAN.md",
    "DECISIONS.md",
    "RULES.md",
)
REQUIREMENT_RE = re.compile(r"^\|\s*(KV5-R-\d{3})\s*\|", re.MULTILINE)
TEST_RE = re.compile(r"^\|\s*(KV5-T-\d{3})\s*\|", re.MULTILINE)
EVIDENCE_RE = re.compile(r"^\|\s*(KV5-E-\d{3})\s*\|", re.MULTILINE)
COMPLETED_RE = re.compile(r"^\s*- \[x\]\s+(.+)$", re.MULTILINE | re.IGNORECASE)
EVIDENCE_REF_RE = re.compile(r"evidence:\s*(KV5-E-\d{3})", re.IGNORECASE)
LOCAL_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
ACCEPTED_VERDICTS = {"passed", "accepted"}
FABLE_ERROR_TOKENS = ("FABLE_HARNESS_ERROR", "<system-warning>", "tool-call warning")
ARTIFACT_REVISION_RE = re.compile(r"ARTIFACT:([0-9a-f]{64})", re.IGNORECASE)
ARTIFACT_PLACEHOLDER = "ARTIFACT:" + ("0" * 64)
FABLE_VERDICT_LINE_RE = re.compile(
    r"^FABLE_VERDICT:\s*(ship|revise|investigate)\s*$", re.IGNORECASE
)
COLD_READER_LABELS = (
    "Current decision:",
    "Current phase:",
    "Next action:",
    "Current blocker:",
    "Current proof:",
)


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    requirements_tests: str
    revision: str
    command: str
    verdict: str
    artifact: str
    timestamp: str
    notes: str


@dataclass
class ValidationReport:
    root: Path
    errors: list[str]
    warnings: list[str]
    requirements: set[str]
    tests: set[str]
    evidence: dict[str, EvidenceRecord]
    artifact_sha256: str
    baseline_commit: str

    @property
    def passed(self) -> bool:
        return not self.errors


def _read(path: Path, errors: list[str]) -> str:
    if not path.is_file():
        errors.append(f"missing required file: {path}")
        return ""
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        errors.append(f"empty required file: {path}")
    return text


def _duplicates(values: list[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def _parse_markdown_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _parse_evidence(status_text: str, errors: list[str]) -> dict[str, EvidenceRecord]:
    records: dict[str, EvidenceRecord] = {}
    for line in status_text.splitlines():
        if not re.match(r"^\|\s*KV5-E-\d{3}\s*\|", line):
            continue
        cells = _parse_markdown_row(line)
        if len(cells) != 8:
            errors.append(f"evidence row must have 8 cells: {line}")
            continue
        record = EvidenceRecord(*cells)
        if record.evidence_id in records:
            errors.append(f"duplicate evidence definition: {record.evidence_id}")
        records[record.evidence_id] = record
    return records


def _resolve_local_link(source: Path, raw_target: str) -> Path | None:
    target = raw_target.strip()
    if target.startswith(("http://", "https://", "mailto:", "#")):
        return None
    target = target.split("#", 1)[0]
    if not target:
        return None
    return (source.parent / target).resolve()


def _artifact_fingerprint(paths: list[Path], root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.as_posix()):
        if not path.is_file():
            continue
        try:
            label = path.relative_to(root).as_posix()
        except ValueError:
            label = path.as_posix()
        digest.update(label.encode("utf-8"))
        digest.update(b"\0")
        content = path.read_bytes()
        if path.suffix.lower() in {".md", ".py"}:
            text = content.decode("utf-8", errors="replace")
            content = ARTIFACT_REVISION_RE.sub(ARTIFACT_PLACEHOLDER, text).encode("utf-8")
        digest.update(content)
        digest.update(b"\0")
    return digest.hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _bound_path(root: Path, raw_path: object, label: str, errors: list[str]) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        errors.append(f"build binding {label} has no path")
        return None
    candidate = (root / raw_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        errors.append(f"build binding {label} escapes project root: {raw_path}")
        return None
    return candidate


def _check_bound_file(
    root: Path,
    entry: object,
    label: str,
    errors: list[str],
    *,
    check_tokens: bool = False,
) -> Path | None:
    if not isinstance(entry, dict):
        errors.append(f"build binding {label} must be an object")
        return None
    path = _bound_path(root, entry.get("path"), label, errors)
    if path is None:
        return None
    if not path.is_file():
        errors.append(f"build binding {label} file missing: {entry.get('path')}")
        return None
    expected = entry.get("sha256")
    actual = _sha256_file(path)
    if not isinstance(expected, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", expected):
        errors.append(f"build binding {label} has invalid sha256")
    elif actual != expected.lower():
        errors.append(
            f"build binding hash mismatch for {entry.get('path')}: expected={expected.lower()} actual={actual}"
        )
    if check_tokens:
        content = path.read_text(encoding="utf-8", errors="replace")
        tokens = entry.get("required_tokens", [])
        if not isinstance(tokens, list) or not tokens:
            errors.append(f"build binding {label} has no required tokens")
        else:
            for token in tokens:
                if not isinstance(token, str) or token not in content:
                    errors.append(
                        f"build binding {label} missing required token: {token!r}"
                    )
    return path


def _check_build_binding(root: Path, errors: list[str]) -> Path:
    manifest_path = root / BUILD_BINDING_MANIFEST
    if not manifest_path.is_file():
        errors.append(f"missing build input binding manifest: {BUILD_BINDING_MANIFEST}")
        return manifest_path
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid build input binding manifest: {exc}")
        return manifest_path
    if not isinstance(manifest, dict):
        errors.append("build input binding manifest must contain an object")
        return manifest_path
    if manifest.get("schema") != "channel_play.khufu_v5.build_input_binding.v1":
        errors.append("build input binding manifest has unexpected schema")
    if not re.fullmatch(r"[0-9a-f]{40}", str(manifest.get("implementation_commit", ""))):
        errors.append("build input binding manifest has invalid implementation commit")

    scene = manifest.get("scene")
    _check_bound_file(root, scene, "scene", errors)

    provenance = manifest.get("provenance")
    if not isinstance(provenance, list) or not provenance:
        errors.append("build input binding manifest has no provenance files")
    else:
        for index, entry in enumerate(provenance):
            _check_bound_file(
                root,
                entry,
                f"provenance[{index}]",
                errors,
                check_tokens=True,
            )

    inputs = manifest.get("inputs")
    if not isinstance(inputs, list) or not inputs:
        errors.append("build input binding manifest has no project inputs")
    else:
        seen: set[str] = set()
        for index, entry in enumerate(inputs):
            path = _check_bound_file(root, entry, f"inputs[{index}]", errors)
            if not isinstance(entry, dict):
                continue
            raw_path = entry.get("path")
            if isinstance(raw_path, str):
                if raw_path in seen:
                    errors.append(f"duplicate build input binding path: {raw_path}")
                seen.add(raw_path)
            override = entry.get("build_override")
            if override is None or path is None:
                continue
            if not isinstance(override, dict):
                errors.append(f"build binding override for {raw_path} must be an object")
                continue
            find = override.get("find")
            replace = override.get("replace")
            occurrences = override.get("occurrences")
            expected_derived = override.get("derived_build_sha256")
            if not isinstance(find, str) or not isinstance(replace, str):
                errors.append(f"build binding override for {raw_path} needs string find/replace")
                continue
            content = path.read_bytes()
            find_bytes = find.encode("utf-8")
            replace_bytes = replace.encode("utf-8")
            actual_occurrences = content.count(find_bytes)
            if not isinstance(occurrences, int) or actual_occurrences != occurrences:
                errors.append(
                    f"build binding override occurrence mismatch for {raw_path}: expected={occurrences} actual={actual_occurrences}"
                )
                continue
            derived = hashlib.sha256(content.replace(find_bytes, replace_bytes)).hexdigest()
            if (
                not isinstance(expected_derived, str)
                or not re.fullmatch(r"[0-9a-fA-F]{64}", expected_derived)
                or derived != expected_derived.lower()
            ):
                errors.append(
                    f"build binding derived hash mismatch for {raw_path}: expected={expected_derived} actual={derived}"
                )
    return manifest_path


def _check_implementation_fable_call(root: Path, errors: list[str]) -> tuple[Path, Path]:
    review_path = root / IMPLEMENTATION_FABLE_REVIEW
    meta_path = root / IMPLEMENTATION_FABLE_META
    if not review_path.is_file():
        errors.append(f"missing implementation Fable review: {IMPLEMENTATION_FABLE_REVIEW}")
    if not meta_path.is_file():
        errors.append(f"missing implementation Fable call metadata: {IMPLEMENTATION_FABLE_META}")
        return review_path, meta_path
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid implementation Fable call metadata: {exc}")
        return review_path, meta_path
    if not isinstance(meta, dict):
        errors.append("implementation Fable call metadata must contain an object")
        return review_path, meta_path
    expected = {
        "phase": "final-review",
        "dryRun": False,
        "exitCode": 0,
        "outputValidation": "passed",
        "timedOut": False,
    }
    for key, value in expected.items():
        if meta.get(key) != value:
            errors.append(
                f"implementation Fable call metadata mismatch for {key}: expected={value!r} actual={meta.get(key)!r}"
            )
    warnings = meta.get("warnings")
    if not isinstance(warnings, list) or warnings:
        errors.append(f"implementation Fable call metadata has warnings: {warnings!r}")
    if meta.get("model") != "claude-fable-5":
        errors.append("implementation Fable call did not use claude-fable-5")
    return review_path, meta_path


def _git_head(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unavailable"


def _check_evidence_artifact(
    record: EvidenceRecord,
    root: Path,
    errors: list[str],
    require_acceptance: bool,
    pending_artifact: Path | None,
) -> None:
    artifact = (root / DOC_DIR / record.artifact).resolve()
    if not artifact.is_file():
        if pending_artifact is not None and artifact == pending_artifact.resolve():
            return
        errors.append(f"{record.evidence_id} artifact missing: {record.artifact}")
        return
    content = artifact.read_text(encoding="utf-8", errors="replace")
    if not content.strip():
        errors.append(f"{record.evidence_id} artifact empty: {record.artifact}")
        return
    if require_acceptance and record.verdict.lower() not in ACCEPTED_VERDICTS:
        errors.append(
            f"{record.evidence_id} cannot complete status with verdict={record.verdict}"
        )
    normalized_artifact = record.artifact.replace("\\", "/").lower()
    is_pending_artifact = pending_artifact is not None and artifact == pending_artifact.resolve()
    is_fable_review = "KV5-T-014" in record.requirements_tests and (
        "work/fable-harness/" in normalized_artifact
        or record.command.lower().startswith("fable ")
    )
    if is_fable_review and require_acceptance:
        for token in FABLE_ERROR_TOKENS:
            if token.lower() in content.lower():
                errors.append(f"{record.evidence_id} Fable artifact contains invalid token: {token}")
        lines = content.splitlines()
        verdicts = [
            (index, match.group(1).lower())
            for index, line in enumerate(lines)
            if (match := FABLE_VERDICT_LINE_RE.fullmatch(line.strip()))
        ]
        last_nonempty = max(
            (index for index, line in enumerate(lines) if line.strip()),
            default=-1,
        )
        if len(verdicts) != 1:
            errors.append(
                f"{record.evidence_id} Fable artifact must contain exactly one verdict line"
            )
        elif verdicts[0][0] != last_nonempty:
            errors.append(f"{record.evidence_id} Fable verdict is not the final non-empty line")
        elif verdicts[0][1] != "ship":
            errors.append(
                f"{record.evidence_id} Fable final verdict is {verdicts[0][1]}, not ship"
            )
    if "KV5-T-016" in record.requirements_tests and require_acceptance:
        if "COLD_READER: passed" not in content:
            errors.append(f"{record.evidence_id} cold-reader artifact lacks passing token")
    if (
        "validate_khufu_v5_harness.py" in record.command
        and require_acceptance
        and not is_pending_artifact
    ):
        receipt_hash = re.search(r"Artifact SHA256:\s*`([0-9a-f]{64})`", content)
        revision_hash = ARTIFACT_REVISION_RE.search(record.revision)
        if "HARNESS_VERDICT: passed" not in content:
            errors.append(f"{record.evidence_id} harness receipt lacks passing verdict")
        if receipt_hash is None:
            errors.append(f"{record.evidence_id} harness receipt lacks artifact hash")
        elif revision_hash is None or receipt_hash.group(1).lower() != revision_hash.group(1).lower():
            errors.append(f"{record.evidence_id} harness receipt hash does not match revision")


def validate_harness(root: Path, pending_artifact: Path | None = None) -> ValidationReport:
    root = root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    doc_paths = [root / DOC_DIR / name for name in REQUIRED_DOCS]
    texts = {path.name: _read(path, errors) for path in doc_paths}
    build_binding_path = _check_build_binding(root, errors)
    fable_review_path, fable_meta_path = _check_implementation_fable_call(root, errors)

    requirement_values = REQUIREMENT_RE.findall(texts.get("GOAL.md", ""))
    test_values = TEST_RE.findall(texts.get("TEST_PLAN.md", ""))
    evidence_values = EVIDENCE_RE.findall(texts.get("STATUS.md", ""))

    for duplicate in sorted(_duplicates(requirement_values)):
        errors.append(f"duplicate requirement definition: {duplicate}")
    for duplicate in sorted(_duplicates(test_values)):
        errors.append(f"duplicate test definition: {duplicate}")
    for duplicate in sorted(_duplicates(evidence_values)):
        errors.append(f"duplicate evidence definition: {duplicate}")

    requirements = set(requirement_values)
    tests = set(test_values)
    evidence = _parse_evidence(texts.get("STATUS.md", ""), errors)

    test_plan_text = texts.get("TEST_PLAN.md", "")
    for requirement in sorted(requirements):
        if not re.search(
            rf"^\|\s*KV5-T-\d{{3}}\s*\|[^\n]*\b{re.escape(requirement)}\b",
            test_plan_text,
            re.MULTILINE,
        ):
            errors.append(f"requirement has no test matrix coverage: {requirement}")

    if len(requirements) < 10:
        errors.append(f"too few requirement definitions: {len(requirements)}")
    if len(tests) < 10:
        errors.append(f"too few test definitions: {len(tests)}")

    readme_text = texts.get("README.md", "")
    for label in COLD_READER_LABELS:
        if not re.search(rf"^- {re.escape(label)}\s*\S", readme_text, re.MULTILINE):
            errors.append(f"README cold-reader snapshot missing label/value: {label}")

    for path, text in zip(doc_paths, (texts.get(item.name, "") for item in doc_paths)):
        for raw_target in LOCAL_LINK_RE.findall(text):
            resolved = _resolve_local_link(path, raw_target)
            if resolved is not None and not resolved.exists():
                errors.append(f"broken local link in {path.relative_to(root)}: {raw_target}")

    completed_items = COMPLETED_RE.findall(texts.get("STATUS.md", ""))
    referenced_for_completion: set[str] = set()
    for item in completed_items:
        refs = EVIDENCE_REF_RE.findall(item)
        if not refs:
            errors.append(f"completed status lacks evidence reference: {item}")
            continue
        for evidence_id in refs:
            referenced_for_completion.add(evidence_id)
            if evidence_id not in evidence:
                errors.append(f"completed status references unknown evidence: {evidence_id}")

    for evidence_id in sorted(referenced_for_completion):
        record = evidence.get(evidence_id)
        if record is not None:
            _check_evidence_artifact(
                record, root, errors, require_acceptance=True, pending_artifact=pending_artifact
            )

    for record in evidence.values():
        if not re.search(r"\bKV5-R-\d{3}\b", record.requirements_tests):
            errors.append(f"{record.evidence_id} lacks requirement ID")
        if not re.search(r"\bKV5-T-\d{3}\b", record.requirements_tests):
            errors.append(f"{record.evidence_id} lacks test ID")
        if not record.revision.strip():
            errors.append(f"{record.evidence_id} lacks revision")
        if not record.command.strip():
            errors.append(f"{record.evidence_id} lacks command/procedure")
        if not record.timestamp.strip():
            errors.append(f"{record.evidence_id} lacks timestamp")
        _check_evidence_artifact(
            record, root, errors, require_acceptance=False, pending_artifact=pending_artifact
        )

    extra_paths = [
        root / "tools/validate_khufu_v5_harness.py",
        root / "tools/tests/test_validate_khufu_v5_harness.py",
        build_binding_path,
        fable_review_path,
        fable_meta_path,
    ]
    artifact_sha = _artifact_fingerprint(doc_paths + extra_paths, root)
    for evidence_id in sorted(referenced_for_completion):
        record = evidence.get(evidence_id)
        if record is None:
            continue
        match = ARTIFACT_REVISION_RE.search(record.revision)
        if match is None:
            errors.append(f"{evidence_id} completion evidence lacks ARTIFACT revision hash")
            continue
        declared = match.group(1).lower()
        artifact_path = (root / DOC_DIR / record.artifact).resolve()
        pending_zero = (
            pending_artifact is not None
            and artifact_path == pending_artifact.resolve()
            and declared == "0" * 64
        )
        requires_current_snapshot = "current-snapshot" in record.notes.lower()
        if requires_current_snapshot and declared != artifact_sha and not pending_zero:
            errors.append(
                f"{evidence_id} revision mismatch declared={declared} current={artifact_sha}"
            )
    return ValidationReport(
        root=root,
        errors=errors,
        warnings=warnings,
        requirements=requirements,
        tests=tests,
        evidence=evidence,
        artifact_sha256=artifact_sha,
        baseline_commit=_git_head(root),
    )


def write_receipt(report: ValidationReport, path: Path, command: str) -> None:
    path = path if path.is_absolute() else report.root / path
    path.parent.mkdir(parents=True, exist_ok=True)
    verdict = "passed" if report.passed else "failed"
    lines = [
        "# Khufu V5 Harness Validation Receipt",
        "",
        f"Timestamp: {datetime.now(timezone.utc).isoformat()}",
        f"HARNESS_VERDICT: {verdict}",
        f"Baseline commit: `{report.baseline_commit}`",
        f"Artifact SHA256: `{report.artifact_sha256}`",
        f"Command: `{command}`",
        "",
        "## Counts",
        "",
        f"- Requirements: {len(report.requirements)}",
        f"- Tests: {len(report.tests)}",
        f"- Evidence rows: {len(report.evidence)}",
        f"- Errors: {len(report.errors)}",
        f"- Warnings: {len(report.warnings)}",
        "",
        "## Errors",
        "",
    ]
    lines.extend(f"- {error}" for error in report.errors)
    if not report.errors:
        lines.append("- none")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {warning}" for warning in report.warnings)
    if not report.warnings:
        lines.append("- none")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _check_committed_freeze(root: Path, receipt: Path | None) -> list[str]:
    paths = [
        "docs/khufu-v5",
        "tools/validate_khufu_v5_harness.py",
        "tools/tests/test_validate_khufu_v5_harness.py",
        BUILD_BINDING_MANIFEST.as_posix(),
        IMPLEMENTATION_FABLE_REVIEW.as_posix(),
        IMPLEMENTATION_FABLE_META.as_posix(),
    ]
    errors: list[str] = []
    status_path = root / DOC_DIR / "STATUS.md"
    try:
        status_text = status_path.read_text(encoding="utf-8")
        parse_errors: list[str] = []
        evidence = _parse_evidence(status_text, parse_errors)
        errors.extend(parse_errors)
        completed_ids = {
            evidence_id
            for item in COMPLETED_RE.findall(status_text)
            for evidence_id in EVIDENCE_REF_RE.findall(item)
        }
        for evidence_id in sorted(completed_ids):
            record = evidence.get(evidence_id)
            if record is None:
                continue
            artifact = (root / DOC_DIR / record.artifact).resolve()
            try:
                paths.append(artifact.relative_to(root).as_posix())
            except ValueError:
                errors.append(
                    f"completion evidence escapes project root: {evidence_id} {record.artifact}"
                )
    except OSError as exc:
        errors.append(f"unable to read completion evidence for committed freeze: {exc}")
    if receipt is not None:
        try:
            paths.append(receipt.resolve().relative_to(root).as_posix())
        except ValueError:
            return ["freeze receipt must be inside the project root"]
    paths = list(dict.fromkeys(paths))
    try:
        status = subprocess.run(
            ["git", "status", "--porcelain", "--", *paths],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if status.stdout.strip():
            errors.append("harness freeze paths are uncommitted or dirty")
        tracked = subprocess.run(
            ["git", "ls-files", "--", *paths],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
        tracked_paths = {line.strip() for line in tracked.stdout.splitlines() if line.strip()}
        required_files = [
            *(f"docs/khufu-v5/{name}" for name in REQUIRED_DOCS),
            "tools/validate_khufu_v5_harness.py",
            "tools/tests/test_validate_khufu_v5_harness.py",
            BUILD_BINDING_MANIFEST.as_posix(),
            IMPLEMENTATION_FABLE_REVIEW.as_posix(),
            IMPLEMENTATION_FABLE_META.as_posix(),
            *[
                path
                for path in paths
                if path not in {"docs/khufu-v5"}
            ],
        ]
        if receipt is not None:
            required_files.append(receipt.resolve().relative_to(root).as_posix())
        for path in required_files:
            if path not in tracked_paths:
                errors.append(f"harness freeze file is not committed: {path}")
    except (OSError, subprocess.SubprocessError) as exc:
        errors.append(f"unable to verify committed harness freeze: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--require-committed", action="store_true")
    args = parser.parse_args()

    pending_artifact = None
    if args.receipt and not args.require_committed:
        root = args.root.resolve()
        pending_artifact = args.receipt if args.receipt.is_absolute() else root / args.receipt
    report = validate_harness(args.root, pending_artifact=pending_artifact)
    if args.require_committed:
        report.errors.extend(_check_committed_freeze(args.root.resolve(), pending_artifact))
    command = "python tools/validate_khufu_v5_harness.py --root ."
    if args.receipt:
        command += f" --receipt {args.receipt.as_posix()}"
    if args.require_committed:
        command += " --require-committed"
    if args.receipt and not args.require_committed:
        write_receipt(report, args.receipt, command)

    print(f"HARNESS_VERDICT: {'passed' if report.passed else 'failed'}")
    print(f"requirements={len(report.requirements)} tests={len(report.tests)} evidence={len(report.evidence)}")
    print(f"baseline_commit={report.baseline_commit}")
    print(f"artifact_sha256={report.artifact_sha256}")
    for error in report.errors:
        print(f"ERROR: {error}")
    for warning in report.warnings:
        print(f"WARNING: {warning}")
    return 0 if report.passed else 1


if __name__ == "__main__":
    sys.exit(main())
