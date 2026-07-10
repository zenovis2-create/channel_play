#!/usr/bin/env python3
"""Validate the Khufu V5 documentation and evidence harness."""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


DOC_DIR = Path("docs/khufu-v5")
REQUIRED_DOCS = (
    "README.md",
    "GOAL.md",
    "PLAN.md",
    "STATUS.md",
    "TEST_PLAN.md",
    "DECISIONS.md",
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
        "work/fable-harness/khufu-v5-final-review.ship.fable.md",
    ]
    if receipt is not None:
        try:
            paths.append(receipt.resolve().relative_to(root).as_posix())
        except ValueError:
            return ["freeze receipt must be inside the project root"]
    errors: list[str] = []
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
            errors.append("Gate 0 freeze paths are uncommitted or dirty")
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
            "work/fable-harness/khufu-v5-final-review.ship.fable.md",
        ]
        if receipt is not None:
            required_files.append(receipt.resolve().relative_to(root).as_posix())
        for path in required_files:
            if path not in tracked_paths:
                errors.append(f"Gate 0 freeze file is not committed: {path}")
    except (OSError, subprocess.SubprocessError) as exc:
        errors.append(f"unable to verify committed Gate 0 freeze: {exc}")
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
