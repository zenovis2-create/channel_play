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


def asset_prepare(root: Path, asset_id: str) -> Path:
    clean = asset_id.strip()
    if not clean:
        raise CompanyError("asset id required")
    brief = root / "asset_pipeline" / "briefs" / f"{clean}.md"
    if not brief.exists():
        asset_new(root, clean)

    base = root / "asset_pipeline"
    incoming = base / "incoming_2d" / clean
    generated = base / "generated_3d" / clean
    blender = base / "blender_work" / clean
    unity_ready = base / "unity_ready" / clean
    for folder in (incoming, generated, blender, unity_ready):
        folder.mkdir(parents=True, exist_ok=True)

    source_drop = incoming / "source_drop.md"
    source_drop.write_text(
        "\n".join(
            [
                "# 2D Source Intake",
                "",
                f"Asset ID: {clean}",
                "Status: waiting_for_source",
                "Accepted inputs: PNG, JPG, SVG, concept sheet, screenshot reference",
                "License: required before generation",
                "",
                "## Required Notes",
                "",
                "- Intended gameplay use:",
                "- Required silhouette/readability:",
                "- Scale reference:",
                "",
            ]
        ),
        encoding="utf-8",
    )

    generation_handoff = generated / "generation_handoff.md"
    generation_handoff.write_text(
        "\n".join(
            [
                "# 2D to 3D Generation Handoff",
                "",
                f"Asset ID: {clean}",
                "Status: waiting_for_generation",
                "Tool: Pixel3D or equivalent image-to-3D service",
                "Output: GLB preferred, FBX accepted",
                "",
                "## Quality Gate",
                "",
                "- Shape readable from gameplay camera",
                "- No hidden license or watermark issue",
                "- Low-poly enough for MVP scene",
                "",
            ]
        ),
        encoding="utf-8",
    )

    blender_template = blender / "blender_batch_template.py"
    blender_template.write_text(
        "\n".join(
            [
                '"""Blender cleanup template for Channel Play assets."""',
                "",
                "import bpy",
                "",
                "ASSET_ID = " + repr(clean),
                "",
                "def main():",
                "    # Load generated GLB/FBX manually or extend this template with an import path.",
                "    bpy.ops.object.select_all(action='SELECT')",
                "    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)",
                "    bpy.ops.wm.save_as_mainfile(filepath=f'asset_pipeline/blender_work/{ASSET_ID}/{ASSET_ID}.blend')",
                "",
                "if __name__ == '__main__':",
                "    main()",
                "",
            ]
        ),
        encoding="utf-8",
    )

    import_manifest = unity_ready / "unity_import_manifest.md"
    import_manifest.write_text(
        "\n".join(
            [
                "# Unity Import Manifest",
                "",
                f"Asset ID: {clean}",
                "Status: waiting_for_unity_import",
                "Target folder: Assets/_Project/Art/Props",
                "Prefab path: TBD",
                "Collider: required when interactable",
                "Material pass: required",
                "Scene screenshot: TBD",
                "",
                "## Verification",
                "",
                "- Unity compile passes",
                "- Asset appears in scene or prefab preview",
                "- Screenshot attached through asset screenshot command",
                "",
            ]
        ),
        encoding="utf-8",
    )

    receipt_dir = root / "runs" / f"asset-pipeline-{clean}"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt = receipt_dir / "asset_pipeline_receipt.md"
    receipt.write_text(
        "\n".join(
            [
                "# Asset Pipeline Receipt",
                "",
                f"Asset ID: {clean}",
                f"Updated: {now_iso()}",
                "Status: pipeline_ready",
                "",
                "## Artifacts",
                "",
                f"- Source intake: {source_drop.relative_to(root).as_posix()}",
                f"- 2D to 3D handoff: {generation_handoff.relative_to(root).as_posix()}",
                f"- Blender template: {blender_template.relative_to(root).as_posix()}",
                f"- Unity import manifest: {import_manifest.relative_to(root).as_posix()}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _mark_asset_pipeline_ready(root, clean, receipt, source_drop, generation_handoff, blender_template, import_manifest)
    return receipt


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


def _mark_asset_pipeline_ready(
    root: Path,
    asset_id: str,
    receipt: Path,
    source_drop: Path,
    generation_handoff: Path,
    blender_template: Path,
    import_manifest: Path,
) -> None:
    index = root / "asset_pipeline" / "index.json"
    data = {"assets": []}
    if index.exists():
        data = json.loads(index.read_text(encoding="utf-8"))
    assets = data.setdefault("assets", [])
    target = next((item for item in assets if item.get("id") == asset_id), None)
    if target is None:
        target = {"id": asset_id, "created_at": now_iso()}
        assets.append(target)
    target.update(
        {
            "status": "generated" if target.get("status") == "briefed" else target.get("status", "generated"),
            "pipeline_receipt": receipt.relative_to(root).as_posix(),
            "source_intake": source_drop.relative_to(root).as_posix(),
            "generation_handoff": generation_handoff.relative_to(root).as_posix(),
            "blender_template": blender_template.relative_to(root).as_posix(),
            "unity_import_manifest": import_manifest.relative_to(root).as_posix(),
            "updated_at": now_iso(),
        }
    )
    index.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
