"""Prompt-to-editable-world graph generator for Channel Play."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .errors import CompanyError
from .timeutil import now_iso

VALID_THEMES = {"pyramid", "city", "school", "arena"}


def world_build(root: Path, world_id: str, *, theme: str = "pyramid", prompt: str = "") -> Path:
    clean = _clean_id(world_id)
    world_theme = (theme or "pyramid").strip().lower()
    if world_theme not in VALID_THEMES:
        raise CompanyError(f"Invalid world theme: {theme}")

    description = prompt.strip() or _default_prompt(clean, world_theme)
    graph = _build_graph(clean, world_theme, description)

    scene_dir = root / "world_pipeline" / "scenes" / clean
    scene_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = root / "Assets" / "_Project" / "WorldGraphs"
    assets_dir.mkdir(parents=True, exist_ok=True)

    graph_path = scene_dir / "scene_graph.json"
    unity_graph_path = assets_dir / f"{clean}.scenegraph.json"
    prompt_path = scene_dir / "prompt.md"
    receipt_dir = root / "runs" / f"world-builder-{clean}"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt = receipt_dir / "world_builder_receipt.md"

    graph_json = json.dumps(graph, ensure_ascii=False, indent=2) + "\n"
    graph_path.write_text(graph_json, encoding="utf-8")
    unity_graph_path.write_text(graph_json, encoding="utf-8")
    prompt_path.write_text(_prompt_doc(clean, world_theme, description), encoding="utf-8")
    receipt.write_text(_receipt(root, clean, world_theme, graph_path, unity_graph_path), encoding="utf-8")
    return receipt


def world_state(root: Path) -> dict:
    scene_root = root / "world_pipeline" / "scenes"
    worlds = []
    if scene_root.exists():
        for graph_path in sorted(scene_root.glob("*/scene_graph.json"), key=lambda item: item.stat().st_mtime, reverse=True):
            try:
                graph = json.loads(graph_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            worlds.append(
                {
                    "id": graph.get("id", graph_path.parent.name),
                    "theme": graph.get("theme", "unknown"),
                    "status": graph.get("status", "unknown"),
                    "nodeCount": len(graph.get("nodes", [])),
                    "path": graph_path.relative_to(root).as_posix(),
                    "unityGraph": f"Assets/_Project/WorldGraphs/{graph_path.parent.name}.scenegraph.json",
                    "updatedAt": graph.get("updated_at", ""),
                }
            )
    return {"status": "ready" if worlds else "empty", "worldCount": len(worlds), "worlds": worlds[:12]}


def _clean_id(value: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip()).strip("_").lower()
    if not clean:
        raise CompanyError("world id required")
    return clean


def _default_prompt(world_id: str, theme: str) -> str:
    if theme == "pyramid":
        return "editable stepped pyramid temple with interior rooms, traps, relic props, pickups, and gameplay markers"
    if theme == "city":
        return "editable city block with roads, buildings, plazas, alleys, and gameplay markers"
    if theme == "school":
        return "editable school stage with classrooms, corridors, lockers, terminals, and gameplay markers"
    return f"editable {theme} game world for {world_id}"


def _build_graph(world_id: str, theme: str, prompt: str) -> dict:
    if theme != "pyramid":
        return _basic_graph(world_id, theme, prompt)
    return {
        "schema": "channel_play.world_graph.v1",
        "id": world_id,
        "theme": theme,
        "status": "editable_graph_ready",
        "updated_at": now_iso(),
        "prompt": prompt,
        "scene": "Assets/_Project/Scenes/School_MVP.unity",
        "root": "TraitorEscape_Runtime_Map",
        "materials": [
            {"id": "sandstone", "color": [0.58, 0.45, 0.28, 1.0]},
            {"id": "limestone", "color": [0.72, 0.62, 0.42, 1.0]},
            {"id": "relic", "color": [0.43, 0.32, 0.2, 1.0]},
            {"id": "gold", "color": [0.95, 0.64, 0.16, 1.0]},
            {"id": "danger", "color": [0.55, 0.18, 0.12, 1.0]},
            {"id": "operator", "color": [0.12, 0.56, 0.32, 1.0]},
            {"id": "key", "color": [0.2, 0.85, 0.95, 1.0]},
            {"id": "blue", "color": [0.13, 0.35, 0.88, 1.0]},
            {"id": "red", "color": [0.82, 0.18, 0.16, 1.0]},
            {"id": "exit", "color": [0.55, 0.28, 0.85, 1.0]},
        ],
        "nodes": [
            *_pyramid_shell_nodes(),
            *_pyramid_room_nodes(),
            *_pyramid_prop_nodes(),
            *_gameplay_nodes(),
        ],
    }


def _basic_graph(world_id: str, theme: str, prompt: str) -> dict:
    return {
        "schema": "channel_play.world_graph.v1",
        "id": world_id,
        "theme": theme,
        "status": "editable_graph_ready",
        "updated_at": now_iso(),
        "prompt": prompt,
        "scene": "Assets/_Project/Scenes/School_MVP.unity",
        "root": "TraitorEscape_Runtime_Map",
        "materials": [{"id": "default", "color": [0.45, 0.45, 0.45, 1.0]}],
        "nodes": [
            _cube("Runtime_Floor", [0, -0.1, 0], [18, 0.2, 14], "default", "floor"),
            _cube("Runtime_Center_Block", [0, 0.6, 0], [3, 1.2, 3], "default", "landmark"),
        ],
    }


def _pyramid_shell_nodes() -> list[dict]:
    nodes = [_cube("Runtime_Floor", [0, -0.1, 0], [26, 0.2, 22], "sandstone", "terrain_base")]
    for tier in range(6):
        width = 26 - tier * 3
        depth = 22 - tier * 2.5
        y = 0.45 + tier * 0.55
        strip = 0.75
        z = depth * 0.5
        x = width * 0.5
        gap = max(3.4 - tier * 0.25, 1.7)
        side_width = max((width - gap) * 0.5, 1.0)
        nodes.extend(
            [
                _cube(f"Runtime_Pyramid_Tier_{tier}_Front_L", [-(gap + side_width) * 0.5, y, -z], [side_width, 0.9, strip], "limestone", "pyramid_shell"),
                _cube(f"Runtime_Pyramid_Tier_{tier}_Front_R", [(gap + side_width) * 0.5, y, -z], [side_width, 0.9, strip], "limestone", "pyramid_shell"),
                _cube(f"Runtime_Pyramid_Tier_{tier}_Back", [0, y, z], [width, 0.9, strip], "limestone", "pyramid_shell"),
                _cube(f"Runtime_Pyramid_Tier_{tier}_Left", [-x, y, 0], [strip, 0.9, max(depth - 1.4, 1)], "limestone", "pyramid_shell"),
                _cube(f"Runtime_Pyramid_Tier_{tier}_Right", [x, y, 0], [strip, 0.9, max(depth - 1.4, 1)], "limestone", "pyramid_shell"),
            ]
        )
    nodes.append(_cube("Runtime_Pyramid_Capstone", [0, 4.05, 0.6], [4.2, 0.8, 3.6], "gold", "landmark"))
    nodes.append(_cube("Runtime_Entrance_Ramp", [0, 0.08, -9.8], [4.6, 0.16, 2.4], "sandstone", "path"))
    return nodes


def _pyramid_room_nodes() -> list[dict]:
    return [
        _cube("Runtime_Central_Corridor_Floor", [0, 0.02, -3.6], [4, 0.08, 11.4], "sandstone", "corridor"),
        _cube("Runtime_Burial_Chamber_Floor", [0, 0.03, 3.9], [8, 0.08, 4.2], "sandstone", "room"),
        _cube("Runtime_West_Relic_Room_Floor", [-7.1, 0.03, -1.4], [4.6, 0.08, 5], "sandstone", "room"),
        _cube("Runtime_East_Trap_Room_Floor", [7.1, 0.03, -1.4], [4.6, 0.08, 5], "sandstone", "room"),
        _cube("Runtime_Corridor_Wall_West_A", [-2.35, 1, -4.8], [0.35, 2, 5.6], "limestone", "wall"),
        _cube("Runtime_Corridor_Wall_East_A", [2.35, 1, -4.8], [0.35, 2, 5.6], "limestone", "wall"),
        _cube("Runtime_Corridor_Wall_West_B", [-2.35, 1, 2.2], [0.35, 2, 2.4], "limestone", "wall"),
        _cube("Runtime_Corridor_Wall_East_B", [2.35, 1, 2.2], [0.35, 2, 2.4], "limestone", "wall"),
        *_pillar("Runtime_Pillar_Front_L", [-1.6, 0.85, -6.2], 1.7),
        *_pillar("Runtime_Pillar_Front_R", [1.6, 0.85, -6.2], 1.7),
        *_pillar("Runtime_Pillar_Chamber_L", [-3.2, 0.95, 4.1], 1.9),
        *_pillar("Runtime_Pillar_Chamber_R", [3.2, 0.95, 4.1], 1.9),
    ]


def _pyramid_prop_nodes() -> list[dict]:
    nodes = [
        _cube("Runtime_Sarcophagus", [0, 0.55, 3.7], [2.4, 1.1, 1.05], "relic", "sarcophagus"),
        _cube("Runtime_Sarcophagus_Lid", [0, 1.18, 3.7], [2.7, 0.25, 1.25], "limestone", "sarcophagus_lid"),
        _cube("Runtime_Treasure_Altar", [0, 0.6, 5.6], [2.6, 1.2, 0.9], "gold", "treasure"),
        _cube("Runtime_Pressure_Plate_A", [0, 0.09, -2.2], [1.5, 0.1, 1.1], "operator", "trap_trigger"),
        _cube("Runtime_Pressure_Plate_B", [6.9, 0.09, -2.8], [1.4, 0.1, 1.1], "operator", "trap_trigger"),
        _cube("Runtime_Spike_Trap_West", [-6.8, 0.28, -3.2], [2.2, 0.55, 0.35], "danger", "trap"),
        _cube("Runtime_Spike_Trap_East", [6.8, 0.28, -3.2], [2.2, 0.55, 0.35], "danger", "trap"),
    ]
    for index in range(5):
        nodes.append(_cylinder(f"Runtime_Canopic_Jar_West_{index}", [-8.4 + index * 0.6, 0.45, 0.15], [0.22, 0.45, 0.22], "relic", "jar"))
        nodes.append(_cylinder(f"Runtime_Canopic_Jar_East_{index}", [5.9 + index * 0.6, 0.45, 0.15], [0.22, 0.45, 0.22], "relic", "jar"))
    return nodes


def _gameplay_nodes() -> list[dict]:
    return [
        _cube("Runtime_Blue_Spawn", [-1.4, 0.04, -8.1], [2.1, 0.08, 1.7], "blue", "spawn_blue"),
        _cube("Runtime_Red_Spawn", [1.4, 0.04, -8.1], [2.1, 0.08, 1.7], "red", "spawn_red"),
        _cube("Runtime_Mission_Terminal", [-7.8, 1, 5.2], [1.2, 2, 0.8], "operator", "mission_terminal"),
        _cube("Runtime_Shop_Terminal", [7.8, 1, 5.2], [1.2, 2, 0.8], "operator", "shop_terminal"),
        _cube("Runtime_Final_Exit_Door", [0, 1.6, 8.45], [3.2, 3.2, 0.45], "exit", "final_door"),
        _cylinder("Runtime_Key_A", [-7.2, 0.65, -1.6], [0.28, 0.18, 0.28], "key", "key"),
        _cylinder("Runtime_Key_B", [0, 0.65, 2.7], [0.28, 0.18, 0.28], "key", "key"),
        _cylinder("Runtime_Key_C", [7.2, 0.65, -1.6], [0.28, 0.18, 0.28], "key", "key"),
        _sphere("Runtime_Point_A", [-3.6, 0.55, -5.5], [0.55, 0.55, 0.55], "gold", "point"),
        _sphere("Runtime_Point_B", [3.6, 0.55, -5.5], [0.55, 0.55, 0.55], "gold", "point"),
        _sphere("Runtime_Point_C", [0, 0.55, 5.4], [0.55, 0.55, 0.55], "gold", "point"),
        _label("Runtime_Label_Map_Title", "PYRAMID TEMPLE", [0, 3.1, -7.8]),
    ]


def _pillar(name: str, position: list[float], height: float) -> list[dict]:
    return [
        _cylinder(name, position, [0.42, height * 0.5, 0.42], "limestone", "pillar"),
        _cube(name + "_Base", [position[0], position[1] - (height * 0.5 - 0.12), position[2]], [1.05, 0.24, 1.05], "relic", "pillar_base"),
        _cube(name + "_Cap", [position[0], position[1] + (height * 0.5 + 0.12), position[2]], [1.05, 0.24, 1.05], "relic", "pillar_cap"),
    ]


def _cube(node_id: str, position: list[float], scale: list[float], material: str, role: str) -> dict:
    return {"id": node_id, "primitive": "cube", "position": position, "scale": scale, "material": material, "role": role, "editable": True}


def _cylinder(node_id: str, position: list[float], scale: list[float], material: str, role: str) -> dict:
    return {"id": node_id, "primitive": "cylinder", "position": position, "scale": scale, "material": material, "role": role, "editable": True}


def _sphere(node_id: str, position: list[float], scale: list[float], material: str, role: str) -> dict:
    return {"id": node_id, "primitive": "sphere", "position": position, "scale": scale, "material": material, "role": role, "editable": True}


def _label(node_id: str, text: str, position: list[float]) -> dict:
    return {"id": node_id, "primitive": "label", "position": position, "scale": [1, 1, 1], "material": "gold", "role": "label", "text": text, "editable": True}


def _prompt_doc(world_id: str, theme: str, prompt: str) -> str:
    return "\n".join(["# World Builder Prompt", "", f"World ID: {world_id}", f"Theme: {theme}", "", prompt, ""])


def _receipt(root: Path, world_id: str, theme: str, graph_path: Path, unity_graph_path: Path) -> str:
    return "\n".join(
        [
            "# World Builder Receipt",
            "",
            f"World ID: {world_id}",
            f"Theme: {theme}",
            f"Updated: {now_iso()}",
            "Status: editable_graph_ready",
            "",
            "## Artifacts",
            "",
            f"- Scene graph: {graph_path.relative_to(root).as_posix()}",
            f"- Unity graph asset: {unity_graph_path.relative_to(root).as_posix()}",
            "",
            "## Next",
            "",
            "Run Unity menu: Channel Play/World Builder/Rebuild From Active Graph",
            "",
        ]
    )
