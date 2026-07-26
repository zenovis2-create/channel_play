"""Asset Forge pipeline for AI concept-to-3D game assets."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .asset_gate import asset_gate_a_init, evaluate_asset_gate_a, evaluate_asset_gate_b
from .errors import CompanyError
from .timeutil import now_iso

VALID_FORGE_KINDS = {"zone", "background", "prop", "character"}


def asset_forge_new(root: Path, asset_id: str, *, kind: str = "prop", prompt: str = "") -> Path:
    clean = _clean_asset_id(asset_id)
    asset_kind = (kind or "prop").strip().lower()
    if asset_kind not in VALID_FORGE_KINDS:
        raise CompanyError(f"Invalid forge kind: {kind}")
    asset_gate_a_init(root, clean)
    gate_a_passed = evaluate_asset_gate_a(root, clean)["passed"]
    gate_b_passed = evaluate_asset_gate_b(root, clean)["passed"]
    production_status = (
        "waiting_for_model_runtime"
        if gate_b_passed
        else "blocked_by_gate_b"
        if gate_a_passed
        else "blocked_by_gate_a"
    )
    description = prompt.strip() or _default_prompt(clean, asset_kind)

    forge_root = root / "asset_pipeline" / "forge" / clean
    concept_dir = forge_root / "concept"
    schema_dir = forge_root / "schema"
    cube_dir = forge_root / "cubepart"
    blender_dir = forge_root / "blender"
    unity_dir = forge_root / "unity"
    for folder in (concept_dir, schema_dir, cube_dir, blender_dir, unity_dir):
        folder.mkdir(parents=True, exist_ok=True)

    schema = _part_schema(clean, asset_kind, description)
    job = {
        "asset_id": clean,
        "kind": asset_kind,
        "status": (
            "forge_ready"
            if gate_b_passed
            else "waiting_for_source_creation"
            if gate_a_passed
            else "waiting_for_gate_a"
        ),
        "created_at": now_iso(),
        "prompt": description,
        "pipeline": [
            {"stage": "concept", "owner": "image_prompt_engineer", "status": "ready"},
            {
                "stage": "image_generation",
                "owner": "asset_factory",
                "status": "waiting_for_gpt_image" if gate_a_passed else "blocked_by_gate_a",
            },
            {"stage": "part_schema", "owner": "technical_artist_blender", "status": "ready"},
            {"stage": "cubepart", "owner": "gdx_ops", "status": production_status},
            {"stage": "blender_cleanup", "owner": "technical_artist_blender", "status": production_status},
            {"stage": "unity_import", "owner": "unity_architect", "status": production_status},
            {"stage": "gameplay_binding", "owner": "unity_gameplay", "status": production_status},
            {"stage": "qa", "owner": "qa_playtest", "status": production_status},
        ],
        "outputs": {
            "concept_prompt": f"asset_pipeline/forge/{clean}/concept/gpt_image_prompt.md",
            "source_intake": f"asset_pipeline/forge/{clean}/concept/source_intake.md",
            "part_schema": f"asset_pipeline/forge/{clean}/schema/part_schema.json",
            "cubepart_job": f"asset_pipeline/forge/{clean}/cubepart/cubepart_job.md",
            "blender_cleanup": f"asset_pipeline/forge/{clean}/blender/cleanup_plan.md",
            "unity_import": f"asset_pipeline/forge/{clean}/unity/unity_import_plan.md",
        },
    }

    (forge_root / "forge_job.json").write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (concept_dir / "gpt_image_prompt.md").write_text(
        _concept_prompt(clean, asset_kind, description, gate_a_passed),
        encoding="utf-8",
    )
    (concept_dir / "source_intake.md").write_text(
        _source_intake(clean, gate_a_passed),
        encoding="utf-8",
    )
    (schema_dir / "part_schema.json").write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (cube_dir / "cubepart_job.md").write_text(
        _cubepart_job(clean, asset_kind, description, schema, production_status),
        encoding="utf-8",
    )
    (blender_dir / "cleanup_plan.md").write_text(
        _blender_cleanup(clean, asset_kind, production_status),
        encoding="utf-8",
    )
    (unity_dir / "unity_import_plan.md").write_text(
        _unity_import(clean, asset_kind, production_status),
        encoding="utf-8",
    )

    receipt_dir = root / "runs" / f"asset-forge-{clean}"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt = receipt_dir / "asset_forge_receipt.md"
    receipt.write_text(
        _receipt(root, clean, asset_kind, forge_root, gate_a_passed, gate_b_passed),
        encoding="utf-8",
    )
    _update_index(
        root,
        clean,
        asset_kind,
        description,
        forge_root,
        receipt,
        gate_a_passed,
        gate_b_passed,
    )
    return receipt


def asset_forge_state(root: Path) -> dict:
    forge_root = root / "asset_pipeline" / "forge"
    jobs = []
    if forge_root.exists():
        for job_path in sorted(forge_root.glob("*/forge_job.json"), key=lambda item: item.stat().st_mtime, reverse=True):
            try:
                job = json.loads(job_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            job["path"] = job_path.relative_to(root).as_posix()
            jobs.append(job)
    ready = sum(1 for job in jobs if job.get("status") == "forge_ready")
    return {
        "status": "ready" if jobs else "empty",
        "jobCount": len(jobs),
        "readyCount": ready,
        "jobs": jobs[:24],
        "stages": ["concept", "image_generation", "part_schema", "cubepart", "blender_cleanup", "unity_import", "gameplay_binding", "qa"],
    }


def asset_semantic_pack(root: Path, asset_id: str) -> Path:
    clean = _clean_asset_id(asset_id)
    if clean != "pyramid_temple_full_environment":
        raise CompanyError("Semantic pack v1 is implemented for pyramid_temple_full_environment only.")

    forge_root = root / "asset_pipeline" / "forge" / clean
    forge_root.mkdir(parents=True, exist_ok=True)

    semantic_labels = _pyramid_semantic_labels()
    nav_points = _pyramid_nav_points()
    interactables = _pyramid_interactables()
    scenarios = _pyramid_test_scenarios()
    job = {
        "asset_id": clean,
        "kind": "full_environment_map",
        "status": "semantic_pack_ready",
        "updated_at": now_iso(),
        "outputs": {
            "simulation_contract": f"asset_pipeline/forge/{clean}/simulation_contract.md",
            "semantic_labels": f"asset_pipeline/forge/{clean}/semantic_labels.json",
            "nav_points": f"asset_pipeline/forge/{clean}/nav_points.json",
            "interactables": f"asset_pipeline/forge/{clean}/interactables.json",
            "test_scenarios": f"asset_pipeline/forge/{clean}/test_scenarios.json",
            "agent_eval_plan": f"asset_pipeline/forge/{clean}/agent_eval_plan.md",
        },
    }

    (forge_root / "forge_job.json").write_text(json.dumps(job, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (forge_root / "simulation_contract.md").write_text(_pyramid_simulation_contract(clean), encoding="utf-8")
    (forge_root / "semantic_labels.json").write_text(json.dumps({"labels": semantic_labels}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (forge_root / "nav_points.json").write_text(json.dumps({"route": nav_points}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (forge_root / "interactables.json").write_text(json.dumps({"interactables": interactables}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (forge_root / "test_scenarios.json").write_text(json.dumps({"scenarios": scenarios}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (forge_root / "agent_eval_plan.md").write_text(_pyramid_agent_eval_plan(clean), encoding="utf-8")

    receipt_dir = root / "runs" / f"asset-semantic-pack-{clean}"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt = receipt_dir / "receipt.md"
    receipt.write_text(_semantic_pack_receipt(clean, forge_root, receipt), encoding="utf-8")
    _update_semantic_index(root, clean, forge_root, receipt)
    return receipt


def _clean_asset_id(asset_id: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_-]+", "_", asset_id.strip()).strip("_").lower()
    if not clean:
        raise CompanyError("asset id required")
    return clean


def _default_prompt(asset_id: str, kind: str) -> str:
    if kind in {"zone", "background"}:
        return f"{asset_id} playable game environment with modular structures, paths, landmarks, and interaction-ready props"
    if kind == "character":
        return f"{asset_id} stylized humanoid game character with clear silhouette and rig-ready body parts"
    return f"{asset_id} gameplay prop with readable silhouette, distinct interactive parts, and collider-friendly shape"


def _part_schema(asset_id: str, kind: str, prompt: str) -> dict:
    if kind in {"zone", "background"}:
        parts = [
            "terrain_base",
            "main_structure",
            "entrance_gate",
            "corridor_modules",
            "room_chambers",
            "staircases",
            "pillars",
            "wall_panels",
            "interactive_doors",
            "trap_mechanisms",
            "cover_blocks",
            "landmark_props",
            "spawn_markers",
            "collider_proxies",
        ]
    elif kind == "character":
        parts = [
            "head",
            "torso",
            "left_arm",
            "right_arm",
            "left_leg",
            "right_leg",
            "hair_or_headwear",
            "clothing",
            "accessory",
            "rig_markers",
            "collider_proxy",
        ]
    else:
        parts = [
            "main_body",
            "base",
            "interactive_handle",
            "moving_part",
            "detail_panels",
            "material_slots",
            "collider_proxy",
        ]
    return {
        "asset_id": asset_id,
        "kind": kind,
        "global_prompt": prompt,
        "cube_part_prompt": f"{prompt}. This asset contains the following parts: {', '.join(parts)}.",
        "parts": [{"name": part, "gameplay_role": _part_role(part)} for part in parts],
    }


def _part_role(part: str) -> str:
    if "collider" in part:
        return "Unity collision proxy"
    if "marker" in part:
        return "spawn or gameplay locator"
    if any(term in part for term in ("door", "trap", "handle", "moving")):
        return "scripted interaction"
    if any(term in part for term in ("arm", "leg", "torso", "head", "rig")):
        return "character rig or animation target"
    return "visual mesh"


def _concept_prompt(asset_id: str, kind: str, prompt: str, gate_a_passed: bool) -> str:
    return "\n".join(
        [
            f"# GPT Image Prompt: {asset_id}",
            "",
            f"Kind: {kind}",
            (
                "Status: ready_for_image_generation"
                if gate_a_passed
                else "Status: blocked_by_gate_a"
            ),
            "",
            "## Prompt",
            "",
            prompt,
            "",
            "Create a game-asset concept sheet, not a marketing illustration.",
            "Use orthographic front, side, top, and three-quarter views.",
            "Keep silhouettes readable from a third-person gameplay camera.",
            "Separate major parts visually so CubePart/Blender cleanup can identify them.",
            "Avoid text baked into the image unless it is removable signage.",
            "",
            "## Negative Constraints",
            "",
            "- No heavy atmospheric blur.",
            "- No impossible geometry.",
            "- No hidden copyrighted logos.",
            "- No single-piece monolithic mesh assumption.",
            "",
        ]
    )


def _source_intake(asset_id: str, gate_a_passed: bool) -> str:
    return "\n".join(
        [
            "# Source Intake",
            "",
            f"Asset ID: {asset_id}",
            (
                "Status: waiting_for_concept_image"
                if gate_a_passed
                else "Status: blocked_by_gate_a"
            ),
            "",
            "## Required Files",
            "",
            "- concept.png or concept_sheet.png",
            "- optional reference images",
            "- license/source note",
            "",
        ]
    )


def _cubepart_job(
    asset_id: str,
    kind: str,
    prompt: str,
    schema: dict,
    production_status: str,
) -> str:
    return "\n".join(
        [
            f"# CubePart Job: {asset_id}",
            "",
            f"Kind: {kind}",
            f"Status: {production_status}",
            "Target runtime: gdx1 or cloud GPU if local runtime is unavailable.",
            "",
            "## CubePart Prompt",
            "",
            schema["cube_part_prompt"],
            "",
            "## Input",
            "",
            "- Preferred: cleaned source mesh from image-to-3D or Blender blockout.",
            "- Alternative: text-to-3D seed output if CubePart supports it in the active runtime.",
            "",
            "## Part Names",
            "",
            *(f"- {item['name']}: {item['gameplay_role']}" for item in schema["parts"]),
            "",
            "## Required Output",
            "",
            "- One mesh per schema part.",
            "- GLB or FBX export.",
            "- Part labels preserved in object names.",
            "- No final Unity import until Blender cleanup passes.",
            "",
        ]
    )


def _blender_cleanup(
    asset_id: str,
    kind: str,
    production_status: str,
) -> str:
    return "\n".join(
        [
            f"# Blender Cleanup Plan: {asset_id}",
            "",
            f"Kind: {kind}",
            f"Status: {production_status}",
            "",
            "## Cleanup Rules",
            "",
            "- Normalize scale to Unity meters.",
            "- Set origin to gameplay-useful pivot.",
            "- Name all objects with CP_ prefix.",
            "- Keep collider proxies as COL_ objects.",
            "- Merge only visual parts that do not need scripting.",
            "- Preserve interactive and physics parts as separate objects.",
            "- Export clean FBX to Unity-ready path.",
            "",
        ]
    )


def _unity_import(
    asset_id: str,
    kind: str,
    production_status: str,
) -> str:
    target = "Maps" if kind in {"zone", "background"} else "Characters" if kind == "character" else "Props"
    return "\n".join(
        [
            f"# Unity Import Plan: {asset_id}",
            "",
            f"Kind: {kind}",
            f"Status: {production_status}",
            f"Target folder: Assets/_Project/Art/{target}",
            f"Prefab folder: Assets/_Project/Prefabs/{target}",
            "",
            "## Unity Requirements",
            "",
            "- Create prefab with part hierarchy preserved.",
            "- Add colliders from COL_ proxies.",
            "- Add gameplay marker components or transform names for spawn/interactions.",
            "- Record scene screenshot after import.",
            "- Run Unity compile and playtest smoke before acceptance.",
            "",
        ]
    )


def _receipt(
    root: Path,
    asset_id: str,
    kind: str,
    forge_root: Path,
    gate_a_passed: bool,
    gate_b_passed: bool,
) -> str:
    rel_root = forge_root.relative_to(root).as_posix()
    return "\n".join(
        [
            "# Asset Forge Receipt",
            "",
            f"Asset ID: {asset_id}",
            f"Kind: {kind}",
            f"Updated: {now_iso()}",
            (
                "Status: forge_ready"
                if gate_b_passed
                else "Status: waiting_for_source_creation"
                if gate_a_passed
                else "Status: waiting_for_gate_a"
            ),
            "",
            "## Artifacts",
            "",
            f"- Forge job: {rel_root}/forge_job.json",
            f"- GPT Image prompt: {rel_root}/concept/gpt_image_prompt.md",
            f"- Source intake: {rel_root}/concept/source_intake.md",
            f"- Part schema: {rel_root}/schema/part_schema.json",
            f"- CubePart job: {rel_root}/cubepart/cubepart_job.md",
            f"- Blender cleanup: {rel_root}/blender/cleanup_plan.md",
            f"- Unity import: {rel_root}/unity/unity_import_plan.md",
            "",
        ]
    )


def _update_index(
    root: Path,
    asset_id: str,
    kind: str,
    prompt: str,
    forge_root: Path,
    receipt: Path,
    gate_a_passed: bool,
    gate_b_passed: bool,
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
            "forge_status": (
                "forge_ready"
                if gate_b_passed
                else "waiting_for_source_creation"
                if gate_a_passed
                else "blocked_by_gate_a"
            ),
            "kind": kind,
            "prompt": prompt,
            "source_license": "pending_generated_or_project_owned",
            "forge_job": (forge_root / "forge_job.json").relative_to(root).as_posix(),
            "forge_receipt": receipt.relative_to(root).as_posix(),
            "updated_at": now_iso(),
        }
    )
    index.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _update_semantic_index(root: Path, asset_id: str, forge_root: Path, receipt: Path) -> None:
    index = root / "asset_pipeline" / "index.json"
    data = {"assets": []}
    if index.exists():
        data = json.loads(index.read_text(encoding="utf-8"))
    assets = data.setdefault("assets", [])
    target = next((item for item in assets if item.get("id") == asset_id), None)
    if target is None:
        target = {"id": asset_id, "created_at": now_iso(), "status": "semantic_pack_ready"}
        assets.append(target)
    target.update(
        {
            "semantic_pack_status": "ready",
            "semantic_pack": forge_root.relative_to(root).as_posix(),
            "simulation_contract": (forge_root / "simulation_contract.md").relative_to(root).as_posix(),
            "semantic_labels": (forge_root / "semantic_labels.json").relative_to(root).as_posix(),
            "nav_points": (forge_root / "nav_points.json").relative_to(root).as_posix(),
            "interactables": (forge_root / "interactables.json").relative_to(root).as_posix(),
            "test_scenarios": (forge_root / "test_scenarios.json").relative_to(root).as_posix(),
            "agent_eval_plan": (forge_root / "agent_eval_plan.md").relative_to(root).as_posix(),
            "semantic_pack_receipt": receipt.relative_to(root).as_posix(),
            "updated_at": now_iso(),
        }
    )
    index.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _pyramid_nav_points() -> list[dict]:
    route = [
        ("MazeV2_Entrance_Threshold", "entrance", [0.0, 0.65, -15.8]),
        ("MazeV2_Djoser_Gallery", "corridor", [0.0, 0.65, -3.2]),
        ("MazeV2_Khufu_GrandGallery", "corridor", [0.0, 1.05, 6.4]),
        ("MazeV2_Hawara_Labyrinth_Core", "chamber", [0.0, 0.65, 15.2]),
        ("MazeV2_Burial_Chamber", "sarcophagus", [0.0, 0.65, 27.2]),
        ("MazeV2_Rear_Service_Exit", "exit", [0.0, 0.65, 36.8]),
    ]
    return [
        {
            "order": index + 1,
            "name": name,
            "category": category,
            "position": position,
            "radius": 1.25,
            "required": True,
        }
        for index, (name, category, position) in enumerate(route)
    ]


def _pyramid_semantic_labels() -> list[dict]:
    colors = ["#ff0000", "#00ff00", "#0066ff", "#ffbf00", "#cc00ff", "#00ffff"]
    labels = []
    for nav, color in zip(_pyramid_nav_points(), colors, strict=True):
        labels.append(
            {
                "objectId": nav["name"],
                "category": nav["category"],
                "segmentationColor": color,
                "worldPosition": nav["position"],
                "required": True,
                "source": "pyramid-maze-v2-route",
            }
        )
    labels.extend(
        [
            {"objectId": "MazeV2_Djoser_Floor_Trap_A", "category": "trap", "segmentationColor": "#e84545", "required": True, "source": "pyramid-maze-v2-builder"},
            {"objectId": "MazeV2_Djoser_Floor_Trap_B", "category": "trap", "segmentationColor": "#e84545", "required": True, "source": "pyramid-maze-v2-builder"},
            {"objectId": "MazeV2_Hawara_Blind_Archive_Door", "category": "false_door", "segmentationColor": "#7048e8", "required": True, "source": "pyramid-maze-v2-builder"},
            {"objectId": "MazeV2_Final_Sarcophagus", "category": "sarcophagus", "segmentationColor": "#f2c94c", "required": True, "source": "pyramid-maze-v2-builder"},
        ]
    )
    return labels


def _pyramid_interactables() -> list[dict]:
    return [
        {"objectId": "MazeV2_Djoser_Floor_Trap_A", "kind": "hazard", "category": "trap", "agentAction": "avoid", "required": True},
        {"objectId": "MazeV2_Djoser_Floor_Trap_B", "kind": "hazard", "category": "trap", "agentAction": "avoid", "required": True},
        {"objectId": "MazeV2_Hawara_Blind_Archive_Door", "kind": "decoy", "category": "false_door", "agentAction": "inspect", "required": True},
        {"objectId": "MazeV2_Final_Sarcophagus", "kind": "landmark", "category": "sarcophagus", "agentAction": "look_at_marker", "required": True},
        {"objectId": "MazeV2_Rear_Service_Exit", "kind": "exit", "category": "exit", "agentAction": "finish_run", "required": True},
    ]


def _pyramid_test_scenarios() -> list[dict]:
    route = [point["name"] for point in _pyramid_nav_points()]
    return [
        {
            "id": "pyramid-maze-v2-scripted-route",
            "command": "tools/channelctl unity agent-playtest pyramid-maze-v2 --agent scripted",
            "scene": "School_MVP",
            "environment": "Runtime_Pyramid_Maze_V2",
            "agent": "scripted",
            "route": route,
            "requiredObservations": 6,
            "passCriteria": {
                "routeCompletion": True,
                "collisionCountMax": 0,
                "stuckSecondsMax": 0,
                "requiredArtifacts": ["scene_state.json", "semantic_labels.json", "actions.jsonl", "metrics.jsonl", "trajectory.json", "receipt.md", "review.md"],
            },
        }
    ]


def _pyramid_simulation_contract(asset_id: str) -> str:
    return "\n".join(
        [
            "# Pyramid Temple Full Environment Simulation Contract",
            "",
            f"Asset ID: `{asset_id}`",
            f"Updated: {now_iso()}",
            "",
            "## Purpose",
            "",
            "This contract makes the pyramid environment legible to Channel Play agents. It links route markers, semantic labels, interactables, and test scenarios to the Unity scene.",
            "",
            "## Required Unity Scene",
            "",
            "- Scene: `Assets/_Project/Scenes/School_MVP.unity`",
            "- Root: `Runtime_Pyramid_Maze_V2`",
            "- Validator: `tools/channelctl unity semantic-check pyramid_temple_full_environment`",
            "",
            "## Required Files",
            "",
            "- `semantic_labels.json`",
            "- `nav_points.json`",
            "- `interactables.json`",
            "- `test_scenarios.json`",
            "- `agent_eval_plan.md`",
            "",
        ]
    )


def _pyramid_agent_eval_plan(asset_id: str) -> str:
    route = " -> ".join(point["name"] for point in _pyramid_nav_points())
    return "\n".join(
        [
            "# Pyramid Agent Evaluation Plan",
            "",
            f"Asset ID: `{asset_id}`",
            f"Updated: {now_iso()}",
            "",
            "## First Scenario",
            "",
            "`pyramid-maze-v2-scripted-route`",
            "",
            "## Route",
            "",
            f"`{route}`",
            "",
            "## Evidence",
            "",
            "- Unity semantic check receipt",
            "- Agent playtest receipt",
            "- RGB/segmentation/depth observations",
            "- actions/metrics/trajectory logs",
            "- Studio visible run panel",
            "",
            "## Failure Classes",
            "",
            "- missing_scene_object",
            "- missing_nav_point",
            "- missing_interactable",
            "- missing_observation",
            "- route_incomplete",
            "- review_artifact_missing",
            "",
        ]
    )


def _semantic_pack_receipt(asset_id: str, forge_root: Path, receipt: Path) -> str:
    rel_root = forge_root.relative_to(receipt.parents[2]).as_posix()
    return "\n".join(
        [
            "# Asset Semantic Pack Receipt",
            "",
            f"Asset ID: `{asset_id}`",
            f"Updated: {now_iso()}",
            "Status: `semantic_pack_ready`",
            "",
            "## Artifacts",
            "",
            f"- `{rel_root}/simulation_contract.md`",
            f"- `{rel_root}/semantic_labels.json`",
            f"- `{rel_root}/nav_points.json`",
            f"- `{rel_root}/interactables.json`",
            f"- `{rel_root}/test_scenarios.json`",
            f"- `{rel_root}/agent_eval_plan.md`",
            "",
            "## Next Command",
            "",
            "`tools/channelctl unity semantic-check pyramid_temple_full_environment`",
            "",
        ]
    )
