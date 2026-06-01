"""Agent registry command."""

from __future__ import annotations

from pathlib import Path

from .state import CompanyPaths, read_json


def render_agents(root: Path) -> str:
    paths = CompanyPaths(root)
    registry = read_json(paths.agent_registry_json)
    agents = registry.get("agents", [])
    if not agents:
        return "No agents registered."

    lines = []
    for agent in agents:
        marker = "writer" if agent.get("writes_by_default") else "role"
        lines.append(f"{agent.get('id', 'unknown'):<26} {marker:<6} {agent.get('profile', '')}")
    return "\n".join(lines)
