"""Top-level non-company command dispatch."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from .asset_forge import asset_forge_new, asset_semantic_pack
from .asset_gate import (
    asset_gate_a_check,
    asset_gate_a_init,
    asset_gate_b_check,
    asset_gate_b_init,
)
from .assets import asset_new, asset_prepare, asset_screenshot, asset_status
from .capture import capture_screen
from .dashboard import generate_dashboard
from .errors import CompanyError
from .feedback import feedback_new, feedback_process
from .gdx import gdx_collect_logs, gdx_probe, gdx_run_bots, gdx_run_server, gdx_simworld_doctor, gdx_simworld_install_base, gdx_simworld_probe, gdx_simworld_route_plan, gdx_simworld_start_server, gdx_simworld_worker_guide, gdx_sync
from .game_loops import game_feedback_loop, game_server_handoff
from .game_production import game_production_check, render_game_production_status
from .image_to_blender import image3d_generate, image3d_new
from .paths import find_repo_root, rel
from .simulation_acceptance import sim_acceptance_check, sim_acceptance_handoff, sim_acceptance_proof_refresh
from .sim_agent_bridge import sim_agent_compare, sim_agent_live_check, sim_agent_packet, sim_agent_run
from .unity import (
    unity_agent_playtest,
    unity_build,
    unity_check,
    unity_manual_auto_capture,
    unity_manual_capture_setup,
    unity_manual_finish,
    unity_manual_recorder_smoke,
    unity_manual_review,
    unity_manual_review_smoke,
    unity_playtest,
    unity_pyramid_maze_v2,
    unity_semantic_check,
    unity_sim_compare,
    unity_sim_check,
    unity_sim_replay,
    unity_sim_review,
)
from .world_builder import world_build


def dispatch_top_level(command: str, args: list[str]) -> int:
    try:
        root = find_repo_root()
        if command == "unity" and any(arg in {"help", "-h", "--help"} for arg in args):
            print("Usage: tools/channelctl unity check [--batch] | playtest | pyramid-maze-v2 | sim-check | agent-playtest pyramid-maze-v2 --agent scripted | sim-review <run-dir> | sim-replay <run-dir> | sim-compare <run-a> <run-b> | manual-capture-setup | manual-auto-capture | manual-recorder-smoke | manual-review-smoke | manual-review [manual_traversal_session.md] | manual-finish [manual_traversal_session.md] | build [mac-dev|linux-server]")
            return 0
        if command == "game" and any(arg in {"help", "-h", "--help"} for arg in args):
            print("Usage: tools/channelctl game status | production-check [--capture] [--build] | feedback-loop [--no-playtest] | server-handoff")
            return 0
        if command == "unity" and args[:1] == ["check"]:
            unity_check(root, args[1:])
            return 0
        if command == "unity" and args[:1] == ["playtest"]:
            unity_playtest(root, args[1:])
            return 0
        if command == "unity" and args[:1] == ["pyramid-maze-v2"]:
            unity_pyramid_maze_v2(root, args[1:])
            return 0
        if command == "unity" and args[:1] == ["sim-check"]:
            unity_sim_check(root, args[1:])
            return 0

        if command == "unity" and args[:1] == ["semantic-check"]:
            unity_semantic_check(root, args[1:])
            return 0
        if command == "unity" and args[:1] == ["agent-playtest"]:
            unity_agent_playtest(root, args[1:])
            return 0
        if command == "unity" and args[:1] == ["sim-review"]:
            unity_sim_review(root, args[1:])
            return 0
        if command == "unity" and args[:1] == ["sim-replay"]:
            unity_sim_replay(root, args[1:])
            return 0

        if command == "unity" and args[:1] == ["sim-compare"]:
            unity_sim_compare(root, args[1:])
            return 0
        if command == "unity" and args[:1] == ["manual-capture-setup"]:
            unity_manual_capture_setup(root, args[1:])
            return 0
        if command == "unity" and args[:1] == ["manual-auto-capture"]:
            unity_manual_auto_capture(root, args[1:])
            return 0
        if command == "unity" and args[:1] == ["manual-recorder-smoke"]:
            unity_manual_recorder_smoke(root, args[1:])
            return 0
        if command == "unity" and args[:1] == ["manual-review-smoke"]:
            unity_manual_review_smoke(root, args[1:])
            return 0
        if command == "unity" and args[:1] == ["manual-review"]:
            unity_manual_review(root, args[1:])
            return 0
        if command == "unity" and args[:1] == ["manual-finish"]:
            unity_manual_finish(root, args[1:])
            return 0
        if command == "unity" and args[:1] == ["build"]:
            unity_build(root, args[1:])
            return 0
        if command == "game" and args[:1] == ["status"]:
            print(render_game_production_status(root))
            return 0
        if command == "game" and args[:1] == ["production-check"]:
            path = game_production_check(root, args[1:])
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "game" and args[:1] == ["feedback-loop"]:
            path = game_feedback_loop(root, args[1:])
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "game" and args[:1] == ["server-handoff"]:
            path = game_server_handoff(root)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "open":
            return _open(root, args)
        if command == "capture" and args[:1] == ["screen"]:
            path = capture_screen(root)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "feedback" and args[:1] == ["new"]:
            path = feedback_new(root)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "feedback" and args[:1] == ["process"]:
            if len(args) < 2:
                raise CompanyError("Usage: feedback process <feedback.md>")
            path = feedback_process(root, args[1])
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "asset" and args[:1] == ["new"]:
            if len(args) < 2:
                raise CompanyError("Usage: asset new <asset-id>")
            path = asset_new(root, args[1])
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "asset" and args[:1] == ["gate-a-init"]:
            if len(args) < 2:
                raise CompanyError(
                    "Usage: asset gate-a-init <asset-id> "
                    "[--path unselected|commissioned_human|openai|cc0]"
                )
            source_path = _option(args[2:], "--path", "unselected")
            path = asset_gate_a_init(root, args[1], source_path=source_path)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "asset" and args[:1] == ["gate-a-check"]:
            if len(args) != 2:
                raise CompanyError("Usage: asset gate-a-check <asset-id>")
            path = asset_gate_a_check(root, args[1])
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "asset" and args[:1] == ["gate-b-init"]:
            if len(args) != 2:
                raise CompanyError("Usage: asset gate-b-init <asset-id>")
            path = asset_gate_b_init(root, args[1])
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "asset" and args[:1] == ["gate-b-check"]:
            if len(args) != 2:
                raise CompanyError("Usage: asset gate-b-check <asset-id>")
            path = asset_gate_b_check(root, args[1])
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "asset" and args[:1] == ["status"]:
            if len(args) < 3:
                raise CompanyError("Usage: asset status <asset-id> <status>")
            path = asset_status(root, args[1], args[2])
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "asset" and args[:1] == ["prepare"]:
            if len(args) < 2:
                raise CompanyError("Usage: asset prepare <asset-id>")
            path = asset_prepare(root, args[1])
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "asset" and args[:1] == ["screenshot"]:
            if len(args) < 3:
                raise CompanyError("Usage: asset screenshot <asset-id> <path>")
            path = asset_screenshot(root, args[1], args[2])
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "asset" and args[:1] == ["forge"]:
            if len(args) < 2:
                raise CompanyError("Usage: asset forge <asset-id> [--kind zone|background|prop|character] [--prompt TEXT]")
            kind = _option(args[2:], "--kind", "prop")
            prompt = _option(args[2:], "--prompt", "")
            path = asset_forge_new(root, args[1], kind=kind, prompt=prompt)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "asset" and args[:1] == ["semantic-pack"]:
            if len(args) != 2:
                raise CompanyError("Usage: asset semantic-pack <asset-id>")
            path = asset_semantic_pack(root, args[1])
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "asset" and args[:1] == ["image3d"]:
            if len(args) < 2:
                raise CompanyError("Usage: asset image3d <asset-id> [--provider rodin25|pixal3d|trellis2|tripo|both|local] [--prompt TEXT] [--source-image PATH]")
            provider = _option(args[2:], "--provider", "pixal3d")
            prompt = _option(args[2:], "--prompt", "")
            source_image = _option(args[2:], "--source-image", "")
            path = image3d_new(root, args[1], provider=provider, prompt=prompt, source_image=source_image)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "asset" and args[:1] == ["generate3d"]:
            if len(args) < 2:
                raise CompanyError("Usage: asset generate3d <asset-id> [--provider auto|rodin25|pixal3d|trellis2|tripo|both|local] [--timeout SECONDS]")
            provider = _option(args[2:], "--provider", "auto")
            timeout = int(_option(args[2:], "--timeout", "1800"))
            path = image3d_generate(root, args[1], provider=provider, timeout=timeout)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "gdx" and args[:1] == ["probe"]:
            path = gdx_probe(root)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "gdx" and args[:1] == ["sync"]:
            path = gdx_sync(root)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "gdx" and args[:1] == ["run-server"]:
            path = gdx_run_server(root)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "gdx" and args[:1] == ["run-bots"]:
            path = gdx_run_bots(root)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "gdx" and args[:1] == ["collect-logs"]:
            path = gdx_collect_logs(root)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "simworld" and args[:1] == ["probe"]:
            path = gdx_simworld_probe(root)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "simworld" and args[:1] == ["doctor"]:
            path = gdx_simworld_doctor(root)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "simworld" and args[:1] == ["install-base"]:
            path = gdx_simworld_install_base(root, args[1:])
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "simworld" and args[:1] == ["route-plan"]:
            path = gdx_simworld_route_plan(root)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "simworld" and args[:1] == ["start-server"]:
            path = gdx_simworld_start_server(root)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "simworld" and args[:1] == ["worker-guide"]:
            path = gdx_simworld_worker_guide(root)
            print(f"Wrote {rel(root, path)}")
            return 0
        if command == "sim-agent" and args[:1] == ["packet"]:
            sim_agent_packet(root, args[1:])
            return 0
        if command == "sim-agent" and args[:1] == ["run"]:
            sim_agent_run(root, args[1:])
            return 0
        if command == "sim-agent" and args[:1] == ["compare"]:
            sim_agent_compare(root, args[1:])
            return 0
        if command == "sim-agent" and args[:1] == ["live-check"]:
            sim_agent_live_check(root, args[1:])
            return 0
        if command == "sim-acceptance" and args[:1] == ["check"]:
            sim_acceptance_check(root, args[1:])
            return 0
        if command == "sim-acceptance" and args[:1] == ["proof-refresh"]:
            sim_acceptance_proof_refresh(root, args[1:])
            return 0
        if command == "sim-acceptance" and args[:1] == ["handoff"]:
            sim_acceptance_handoff(root, args[1:])
            return 0
        if command == "world" and args[:1] == ["build"]:
            if len(args) < 2:
                raise CompanyError("Usage: world build <world-id> [--theme pyramid|city|school|arena] [--prompt TEXT]")
            theme = _option(args[2:], "--theme", "pyramid")
            prompt = _option(args[2:], "--prompt", "")
            path = world_build(root, args[1], theme=theme, prompt=prompt)
            print(f"Wrote {rel(root, path)}")
            return 0
        raise CompanyError(f"Unknown command: {command} {' '.join(args)}")
    except CompanyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


def _open(root: Path, args: list[str]) -> int:
    if not args:
        raise CompanyError("Usage: open dashboard")
    target = args[0]
    if target == "dashboard":
        path = generate_dashboard(root)
    elif target == "studio":
        path = root / "tools" / "studio" / "app" / "index.html"
    elif target == "unity":
        path = root
    elif target == "obsidian":
        path = root / "obsidian" / "channel_play"
    else:
        raise CompanyError(f"Unknown open target: {target}")
    subprocess.run(["open", str(path)], cwd=root, check=False)
    print(f"Opened {rel(root, path)}")
    return 0


def _option(args: list[str], flag: str, default: str) -> str:
    if flag not in args:
        return default
    index = args.index(flag)
    if index + 1 >= len(args):
        raise CompanyError(f"Missing value for {flag}")
    return args[index + 1]
