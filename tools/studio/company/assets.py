"""Asset pipeline helpers."""

from __future__ import annotations

import json
from pathlib import Path

from .errors import CompanyError
from .timeutil import now_iso

VALID_ASSET_STATUSES = {"briefed", "generated", "cleanup", "unity_ready", "accepted", "rework", "rejected"}


def asset_new(root: Path, asset_id: str) -> Path:
    clean = asset_id.strip()
    if not clean:
        raise CompanyError("asset id required")
    base = root / "asset_pipeline"
    for child in ("briefs", "incoming_2d", "generated_3d", "blender_work", "unity_ready", "rejected"):
        (base / child).mkdir(parents=True, exist_ok=True)
    for child in ("generated_3d", "blender_work", "unity_ready"):
        (base / child / clean).mkdir(parents=True, exist_ok=True)
    brief = base / "briefs" / f"{clean}.md"
    brief.write_text(
        "\n".join(
            [
                f"# Asset Brief: {clean}",
                "",
                "Status: briefed",
                "Target: Unity prefab",
                "Scale reference: player height 2m",
                "Poly budget: low",
                "Texture style: broadcast-readable",
                "Source/license: TBD",
                "",
                "## Use",
                "",
                "TBD",
                "",
                "## Generation Prompt",
                "",
                "TBD",
                "",
                "## Review Notes",
                "",
                "TBD",
                "",
            ]
        ),
        encoding="utf-8",
    )
    index = base / "index.json"
    data = {"assets": []}
    if index.exists():
        data = json.loads(index.read_text(encoding="utf-8"))
    assets = data.setdefault("assets", [])
    if not any(item.get("id") == clean for item in assets):
        assets.append(
            {
                "id": clean,
                "status": "briefed",
                "brief": brief.relative_to(root).as_posix(),
                "created_at": now_iso(),
                "source_license": "TBD",
            }
        )
    index.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_asset_scaffolds(root, clean)
    return brief


def asset_status(root: Path, asset_id: str, status: str) -> Path:
    if status not in VALID_ASSET_STATUSES:
        raise CompanyError(f"Invalid asset status: {status}")
    index = root / "asset_pipeline" / "index.json"
    if not index.exists():
        raise CompanyError("asset_pipeline/index.json missing")
    data = json.loads(index.read_text(encoding="utf-8"))
    for item in data.get("assets", []):
        if item.get("id") == asset_id:
            item["status"] = status
            item["updated_at"] = now_iso()
            index.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return index
    raise CompanyError(f"Unknown asset: {asset_id}")


def asset_screenshot(root: Path, asset_id: str, screenshot: str) -> Path:
    index = root / "asset_pipeline" / "index.json"
    if not index.exists():
        raise CompanyError("asset_pipeline/index.json missing")
    data = json.loads(index.read_text(encoding="utf-8"))
    found = False
    for item in data.get("assets", []):
        if item.get("id") == asset_id:
            item["scene_screenshot"] = screenshot
            item["updated_at"] = now_iso()
            found = True
            break
    if not found:
        raise CompanyError(f"Unknown asset: {asset_id}")
    import_note = root / "asset_pipeline" / "unity_ready" / asset_id / "import_note.md"
    if import_note.exists():
        text = import_note.read_text(encoding="utf-8").replace("Scene screenshot: TBD", f"Scene screenshot: {screenshot}")
        import_note.write_text(text, encoding="utf-8")
    index.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return index


def _write_asset_scaffolds(root: Path, asset_id: str) -> None:
    blender_order = root / "asset_pipeline" / "blender_work" / asset_id / "cleanup_work_order.md"
    blender_order.write_text(
        "\n".join(
            [
                "# Blender Cleanup Work Order",
                "",
                f"Asset ID: {asset_id}",
                "Scale: match player height reference",
                "Origin: bottom center unless gameplay requires otherwise",
                "Collider proxy: required for interactable props",
                "Export: FBX or GLB to unity_ready folder",
                "",
            ]
        ),
        encoding="utf-8",
    )
    import_note = root / "asset_pipeline" / "unity_ready" / asset_id / "import_note.md"
    import_note.write_text(
        "\n".join(
            [
                "# Unity Import Note",
                "",
                f"Asset ID: {asset_id}",
                "Prefab path: TBD",
                "Material status: TBD",
                "Scene screenshot: TBD",
                "Review state: briefed",
                "",
            ]
        ),
        encoding="utf-8",
    )
