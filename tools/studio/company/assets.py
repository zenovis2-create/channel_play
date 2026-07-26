"""Asset pipeline helpers."""

from __future__ import annotations

import json
from pathlib import Path

from .asset_gate import (
    asset_gate_a_init,
    clean_asset_id,
    evaluate_asset_gate_a,
    evaluate_asset_gate_b,
    require_asset_gate_b,
)
from .errors import CompanyError
from .timeutil import now_iso

VALID_ASSET_STATUSES = {
    "briefed",
    "generated",
    "cleanup",
    "unity_ready",
    "accepted",
    "rework",
    "rejected",
}
GATE_B_PROTECTED_STATUSES = {"generated", "cleanup", "unity_ready", "accepted"}


def asset_new(root: Path, asset_id: str) -> Path:
    clean = clean_asset_id(asset_id)
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
    asset_gate_a_init(root, clean)
    production_status = _production_status(root, clean)
    _write_asset_scaffolds(root, clean, production_status)
    return brief


def asset_status(root: Path, asset_id: str, status: str) -> Path:
    clean = clean_asset_id(asset_id)
    if status not in VALID_ASSET_STATUSES:
        raise CompanyError(f"Invalid asset status: {status}")
    if status in GATE_B_PROTECTED_STATUSES:
        require_asset_gate_b(root, clean)
    index = root / "asset_pipeline" / "index.json"
    if not index.exists():
        raise CompanyError("asset_pipeline/index.json missing")
    data = json.loads(index.read_text(encoding="utf-8"))
    for item in data.get("assets", []):
        if item.get("id") == clean:
            item["status"] = status
            item["updated_at"] = now_iso()
            index.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return index
    raise CompanyError(f"Unknown asset: {clean}")


def asset_screenshot(root: Path, asset_id: str, screenshot: str) -> Path:
    clean = clean_asset_id(asset_id)
    index = root / "asset_pipeline" / "index.json"
    if not index.exists():
        raise CompanyError("asset_pipeline/index.json missing")
    data = json.loads(index.read_text(encoding="utf-8"))
    found = False
    for item in data.get("assets", []):
        if item.get("id") == clean:
            item["scene_screenshot"] = screenshot
            item["updated_at"] = now_iso()
            found = True
            break
    if not found:
        raise CompanyError(f"Unknown asset: {clean}")
    import_note = root / "asset_pipeline" / "unity_ready" / clean / "import_note.md"
    if import_note.exists():
        text = import_note.read_text(encoding="utf-8").replace("Scene screenshot: TBD", f"Scene screenshot: {screenshot}")
        import_note.write_text(text, encoding="utf-8")
    index.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return index


def asset_prepare(root: Path, asset_id: str) -> Path:
    clean = clean_asset_id(asset_id)
    brief = root / "asset_pipeline" / "briefs" / f"{clean}.md"
    if not brief.exists():
        asset_new(root, clean)
    else:
        asset_gate_a_init(root, clean)
    gate_a_passed = evaluate_asset_gate_a(root, clean)["passed"]
    gate_b_passed = evaluate_asset_gate_b(root, clean)["passed"]
    source_status = "waiting_for_source" if gate_a_passed else "blocked_by_gate_a"
    production_status = (
        "waiting_for_generation"
        if gate_b_passed
        else "blocked_by_gate_b"
        if gate_a_passed
        else "blocked_by_gate_a"
    )
    import_status = "waiting_for_unity_import" if gate_b_passed else production_status
    _write_asset_scaffolds(root, clean, production_status)

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
                f"Status: {source_status}",
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
                f"Status: {production_status}",
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
        _blender_template_text(clean, production_status),
        encoding="utf-8",
    )

    import_manifest = unity_ready / "unity_import_manifest.md"
    import_manifest.write_text(
        _unity_import_manifest_text(clean, import_status),
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
                f"Status: scaffolds_{production_status}",
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
    _mark_asset_pipeline_ready(
        root,
        clean,
        receipt,
        source_drop,
        generation_handoff,
        blender_template,
        import_manifest,
        production_status,
    )
    return receipt


def _production_status(root: Path, asset_id: str) -> str:
    if evaluate_asset_gate_b(root, asset_id)["passed"]:
        return "waiting_for_generation"
    if evaluate_asset_gate_a(root, asset_id)["passed"]:
        return "blocked_by_gate_b"
    return "blocked_by_gate_a"


def _write_asset_scaffolds(
    root: Path,
    asset_id: str,
    production_status: str,
) -> None:
    blender_dir = root / "asset_pipeline" / "blender_work" / asset_id
    unity_dir = root / "asset_pipeline" / "unity_ready" / asset_id
    blender_dir.mkdir(parents=True, exist_ok=True)
    unity_dir.mkdir(parents=True, exist_ok=True)
    blender_order = blender_dir / "cleanup_work_order.md"
    blender_order.write_text(
        "\n".join(
            [
                "# Blender Cleanup Work Order",
                "",
                f"Asset ID: {asset_id}",
                f"Status: {production_status}",
                "Scale: match player height reference",
                "Origin: bottom center unless gameplay requires otherwise",
                "Collider proxy: required for interactable props",
                "Export: FBX or GLB to unity_ready folder",
                "",
            ]
        ),
        encoding="utf-8",
    )
    blender_template = blender_dir / "blender_batch_template.py"
    blender_template.write_text(
        _blender_template_text(asset_id, production_status),
        encoding="utf-8",
    )
    import_note = unity_dir / "import_note.md"
    import_note.write_text(
        "\n".join(
            [
                "# Unity Import Note",
                "",
                f"Asset ID: {asset_id}",
                f"Gate status: {production_status}",
                "Prefab path: TBD",
                "Material status: TBD",
                "Scene screenshot: TBD",
                f"Review state: {production_status}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    import_status = (
        "waiting_for_unity_import"
        if production_status == "waiting_for_generation"
        else production_status
    )
    import_manifest = unity_dir / "unity_import_manifest.md"
    import_manifest.write_text(
        _unity_import_manifest_text(asset_id, import_status),
        encoding="utf-8",
    )


def _blender_template_text(asset_id: str, production_status: str) -> str:
    return "\n".join(
        [
            '"""Blender cleanup template for Channel Play assets."""',
            "",
            "from pathlib import Path",
            "import sys",
            "",
            "import bpy",
            "",
            "ASSET_ID = " + repr(asset_id),
            "GATE_STATUS = " + repr(production_status),
            "REPO_ROOT = Path(__file__).resolve().parents[3]",
            "",
            "def require_production_gate():",
            "    if str(REPO_ROOT) not in sys.path:",
            "        sys.path.insert(0, str(REPO_ROOT))",
            "    from tools.studio.company.asset_gate import require_asset_gate_b",
            "    require_asset_gate_b(REPO_ROOT, ASSET_ID)",
            "",
            "def main():",
            "    require_production_gate()",
            "    # Load generated GLB/FBX manually or extend this template with an import path.",
            "    bpy.ops.object.select_all(action='SELECT')",
            "    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)",
            "    bpy.ops.wm.save_as_mainfile(filepath=f'asset_pipeline/blender_work/{ASSET_ID}/{ASSET_ID}.blend')",
            "",
            "if __name__ == '__main__':",
            "    main()",
            "",
        ]
    )


def _unity_import_manifest_text(asset_id: str, import_status: str) -> str:
    return "\n".join(
        [
            "# Unity Import Manifest",
            "",
            f"Asset ID: {asset_id}",
            f"Status: {import_status}",
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
    )


def _mark_asset_pipeline_ready(
    root: Path,
    asset_id: str,
    receipt: Path,
    source_drop: Path,
    generation_handoff: Path,
    blender_template: Path,
    import_manifest: Path,
    production_status: str,
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
            "status": target.get("status", "briefed"),
            "pipeline_scaffold_status": production_status,
            "pipeline_receipt": receipt.relative_to(root).as_posix(),
            "source_intake": source_drop.relative_to(root).as_posix(),
            "generation_handoff": generation_handoff.relative_to(root).as_posix(),
            "blender_template": blender_template.relative_to(root).as_posix(),
            "unity_import_manifest": import_manifest.relative_to(root).as_posix(),
            "updated_at": now_iso(),
        }
    )
    index.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
