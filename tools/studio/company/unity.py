"""Unity project checks."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from .errors import CompanyError
from .timeutil import now_iso, slugify


UNITY_VERSION = "6000.0.76f1"
UNITY_MAC_DEFAULT = Path(f"/Applications/Unity/Hub/Editor/{UNITY_VERSION}/Unity.app/Contents/MacOS/Unity")


def resolve_unity_editor() -> Path:
    configured = os.environ.get("UNITY_EDITOR")
    if configured:
        return Path(configured)

    if os.name == "nt":
        candidates = [
            Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
            / "Unity"
            / "Hub"
            / "Editor"
            / UNITY_VERSION
            / "Editor"
            / "Unity.exe",
            Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
            / "Unity"
            / "Hub"
            / "Editor"
            / UNITY_VERSION
            / "Editor"
            / "Unity.exe",
            Path.home()
            / "Unity"
            / "Hub"
            / "Editor"
            / UNITY_VERSION
            / "Editor"
            / "Unity.exe",
        ]
    else:
        candidates = [UNITY_MAC_DEFAULT]

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def unity_check(root: Path, args: list[str]) -> Path:
    run_batch = "--batch" in args
    unity = resolve_unity_editor()
    if not (root / "ProjectSettings" / "ProjectVersion.txt").exists():
        raise CompanyError("Unity ProjectSettings/ProjectVersion.txt not found.")
    run_dir = root / "runs" / f"unity-check-{slugify(now_iso())}"
    run_dir.mkdir(parents=True, exist_ok=True)
    log_path = run_dir / "unity_check.md"
    lines = [
        "# Unity Check",
        "",
        f"Checked: {now_iso()}",
        f"Unity editor: {unity}",
        f"Unity editor exists: {unity.exists()}",
        f"Project root: {root}",
        f"Batch mode requested: {run_batch}",
        "",
    ]
    if run_batch:
        if not unity.exists():
            raise CompanyError(f"Unity editor not found: {unity}")
        editor_log = run_dir / "Editor.log"
        result = subprocess.run(
            [
                str(unity),
                "-batchmode",
                "-quit",
                "-projectPath",
                str(root),
                "-logFile",
                str(editor_log),
            ],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=180,
        )
        errors = _summarize_unity_errors(editor_log)
        lines.extend([f"Exit code: {result.returncode}", f"Editor log: {editor_log.relative_to(root)}", f"Compile errors: {len(errors)}"])
        if errors:
            lines.extend(["", "## Error Summary", "", *[f"- {error}" for error in errors[:20]]])
    else:
        lines.append("Result: quick project check passed. Use `--batch` for Unity batchmode.")
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {log_path.relative_to(root)}")
    return log_path


def _summarize_unity_errors(log_path: Path) -> list[str]:
    if not log_path.exists():
        return []
    errors: list[str] = []
    for line in log_path.read_text(errors="ignore").splitlines():
        stripped = line.strip()
        lower = stripped.lower()
        if "error cs" in lower or "exception" in lower:
            errors.append(stripped[:240])
    return errors
