"""Screen capture helper."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from .errors import CompanyError
from .timeutil import now_iso, slugify


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def capture_screen(root: Path) -> Path:
    out_dir = root / "reviews" / "captures"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"screen-{slugify(now_iso())}.png"
    command = _capture_command(path)
    env = os.environ.copy()
    env["CHANNEL_PLAY_CAPTURE_PATH"] = str(path)
    try:
        result = subprocess.run(
            command,
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CompanyError(f"Screenshot capture failed: {exc}") from exc

    if result.returncode != 0 or not _is_png(path):
        path.unlink(missing_ok=True)
        detail = (result.stderr or result.stdout or "capture command produced no PNG").strip()
        raise CompanyError(f"Screenshot capture failed: {detail[-500:]}")
    return path


def _capture_command(path: Path) -> list[str]:
    if sys.platform == "darwin":
        executable = shutil.which("screencapture") or "/usr/sbin/screencapture"
        return [executable, "-x", str(path)]

    if sys.platform == "win32":
        executable = shutil.which("powershell.exe") or shutil.which("powershell")
        if not executable:
            raise CompanyError("Screenshot capture requires Windows PowerShell.")
        script = """
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$bounds = [System.Windows.Forms.SystemInformation]::VirtualScreen
$bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
try {
    $graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
    $bitmap.Save($env:CHANNEL_PLAY_CAPTURE_PATH, [System.Drawing.Imaging.ImageFormat]::Png)
}
finally {
    $graphics.Dispose()
    $bitmap.Dispose()
}
""".strip()
        return [
            executable,
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            script,
        ]

    raise CompanyError(f"Screenshot capture is unsupported on {sys.platform}.")


def _is_png(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        with path.open("rb") as stream:
            return stream.read(len(PNG_SIGNATURE)) == PNG_SIGNATURE
    except OSError:
        return False
