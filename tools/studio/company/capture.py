"""Screen capture helper."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .timeutil import now_iso, slugify


def capture_screen(root: Path) -> Path:
    out_dir = root / "reviews" / "captures"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"screen-{slugify(now_iso())}.png"
    result = subprocess.run(["screencapture", "-x", str(path)], cwd=root, check=False)
    if result.returncode != 0 or not path.exists():
        path.write_text("Screenshot capture failed or unavailable.\n", encoding="utf-8")
    return path
