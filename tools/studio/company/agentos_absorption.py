"""AgentOS benchmark absorption matrix for the Studio dashboard."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from tools.studio.company.state import read_json, write_json


MATRIX_PATH = Path("memory/company/agentos_absorption_matrix.json")


DEFAULT_MATRIX = {
    "updated_at": "2026-06-03",
    "summary": {
        "sources_reviewed": 9,
        "patterns": 8,
        "absorbed": 6,
        "partial": 5,
        "next": 7,
        "focus": "AgentOS/Hermes/OpenClaw의 mission-control, durable board, workspace preview, shared memory, control-room UX를 Channel Play Studio에 흡수",
    },
    "source_groups": [
        {
            "name": "Julian Goldie Agent OS",
            "role": "사용자 관점 mission-control 벤치마크",
            "sources": [
                "https://agentos.guide/hermes-agent-os",
                "https://agentos.guide/openclaw-agent-os",
                "https://agentos.guide/codex",
                "https://openclawdatabase.com/news/videos/2026-05-16-agent-os-claude-hermes-openclaw-dashboard/",
            ],
            "takeaway": "한 사이드바 안에 에이전트, 목표, 세션, 워크스페이스, 프리뷰를 묶어 탭 전환 비용을 줄인다.",
        },
        {
            "name": "Hermes official surfaces",
            "role": "실행/보드/데스크톱 구조 벤치마크",
            "sources": [
                "https://hermes-agent.nousresearch.com/docs/user-guide/desktop",
                "https://hermes-agent.nousresearch.com/docs/user-guide/features/kanban",
            ],
            "takeaway": "Desktop, CLI, TUI, Web Dashboard가 같은 agent core, config, sessions, skills, memory를 공유한다.",
        },
        {
            "name": "AgentOS architecture",
            "role": "메모리/스킬/브로커 구조 벤치마크",
            "sources": [
                "https://agentos.to/introduction/what-is-agentos/",
                "https://agentos.sh/",
            ],
            "takeaway": "엔진이 graph/memex, skills, auth, MCP를 중개하고 GUI는 선택적 human layer가 된다.",
        },
        {
            "name": "Odysseus self-hosted workspace",
            "role": "로컬 admin console 위험/기능 범위 참고",
            "sources": ["https://github.com/pewdiepie-archdaemon/odysseus"],
            "takeaway": "강력한 로컬 도구는 admin console로 취급하고 auth, secrets, network exposure를 엄격히 관리해야 한다.",
        },
    ],
    "patterns": [
        {
            "id": "mission_control_shell",
            "label": "Mission Control shell",
            "evidence": "왼쪽 agent rail, 중앙 live workspace, 오른쪽 brain/goal/memory rail",
            "studio_status": "partial",
            "studio_mapping": "현재 왼쪽 nav와 중앙 패널은 있으나 오른쪽 brain rail은 memory panel로 분리되어 있음",
            "next_action": "desktop 폭에서는 brain/goal/status를 sticky right rail로 재배치",
        },
        {
            "id": "durable_board",
            "label": "Durable multi-agent board",
            "evidence": "task row, named worker, heartbeat, block/unblock, complete metadata",
            "studio_status": "absorbed",
            "studio_mapping": "task_board.json, jobs receipt, tracker timeline, agent runs로 내구성 있는 상태를 표시",
            "next_action": "작업판을 Kanban lanes 형태로 시각화하고 heartbeat를 더 노출",
        },
        {
            "id": "goal_mode",
            "label": "Goal mode with judge and budget",
            "evidence": "standing goal, conservative judge, turn budget, resume, subgoal",
            "studio_status": "partial",
            "studio_mapping": "orchestrator.run과 company.advance가 자동 진행을 담당",
            "next_action": "목표별 budget, done judge, subgoal acceptance UI 추가",
        },
        {
            "id": "workspace_buckets",
            "label": "Workspace buckets and inline preview",
            "evidence": "Apps, Images, Videos, Voice, Skills, Scratchpads, saved searches를 bucket으로 분류",
            "studio_status": "partial",
            "studio_mapping": "tracker artifacts와 asset panel이 있지만 bucket gallery는 없음",
            "next_action": "Unity build, HTML, image, video, audio, logs, briefs bucket gallery 추가",
        },
        {
            "id": "agent_roster_identity",
            "label": "Named agent roster",
            "evidence": "각 에이전트가 이름, 역할, schedule, source, tools, brief를 갖는 동료처럼 보임",
            "studio_status": "partial",
            "studio_mapping": "agent_registry.json과 agent lanes가 있으나 identity card 깊이는 부족",
            "next_action": "각 agent card에 soul/skill/tools/current mission/last output/availability 추가",
        },
        {
            "id": "control_room",
            "label": "Control Room",
            "evidence": "health, agents, doctor, logs, cron, memory를 한 화면에서 점검",
            "studio_status": "absorbed",
            "studio_mapping": "adapter, worker fleet, gdx, runs, model cookbook 패널이 control room 역할",
            "next_action": "상단 health strip에 degraded reason과 action hint를 통합",
        },
        {
            "id": "session_browser",
            "label": "Session browser and replay",
            "evidence": "past sessions are surfaced newest-first and reused as workflow templates",
            "studio_status": "absorbed",
            "studio_mapping": "session search와 job ledger로 과거 실행/리뷰/문서를 검색",
            "next_action": "성공 세션을 template으로 pin/fork하는 UI 추가",
        },
        {
            "id": "operator_visibility",
            "label": "Operator visibility",
            "evidence": "live log, tool call summaries, file browser, preview rail, clear blocked reason",
            "studio_status": "absorbed",
            "studio_mapping": "command center, job ledger, tracker steps, production card, receipt preview가 해당 역할",
            "next_action": "작업 중인 agent가 어떤 tool call 단계인지 event stream으로 세분화",
        },
    ],
    "visual_rules": [
        "첫 화면은 mission-control이어야 한다. 마케팅 hero가 아니라 지금 실행 중인 목표, 작업, 에이전트, 결과가 보여야 한다.",
        "카드는 상태를 숨기지 않는다. status, owner, last event, artifact, next action이 같은 card 안에 있어야 한다.",
        "AgentOS류 dark editorial palette는 그대로 복사하지 않는다. Channel Play는 제작 운영툴이므로 밝고 dense한 workbench 톤을 유지하되 핵심 상태 색만 강하게 쓴다.",
        "버킷/보드/프리뷰는 세 칼럼으로 읽혀야 한다. 왼쪽 선택, 가운데 목록/상태, 오른쪽 결과 preview가 기본이다.",
        "blocked, waiting, running, done은 chip 하나로 끝내지 않는다. 왜 그런 상태인지와 다음 액션이 같이 표시되어야 한다.",
        "모든 산출물은 파일 시스템 경로, 생성 주체, 생성 시각, 검증 상태를 가진다.",
    ],
    "next_build_queue": [
        {
            "id": "ui-01",
            "title": "Mission Control 3-rail layout",
            "priority": "P1",
            "expected_result": "desktop에서 agent rail / live workspace / brain rail이 한 화면에 고정",
        },
        {
            "id": "ui-02",
            "title": "Workspace bucket gallery",
            "priority": "P1",
            "expected_result": "HTML, Unity build, image, video, audio, logs, briefs를 bucket으로 preview",
        },
        {
            "id": "ui-03",
            "title": "Goal mode budget and judge receipt",
            "priority": "P1",
            "expected_result": "목표별 turn budget, acceptance criteria, done/continue 판단 이유 표시",
        },
        {
            "id": "ui-04",
            "title": "Agent identity cards",
            "priority": "P2",
            "expected_result": "각 agent의 role, skills, tool, current mission, last output, health를 한 카드에서 확인",
        },
        {
            "id": "ui-05",
            "title": "Kanban lane board",
            "priority": "P2",
            "expected_result": "triage/todo/running/blocked/review/done lane으로 작업판 재구성",
        },
        {
            "id": "ui-06",
            "title": "Event stream drawer",
            "priority": "P2",
            "expected_result": "orchestrator와 worker의 tool call, heartbeat, handoff, receipt를 시간순으로 표시",
        },
        {
            "id": "ui-07",
            "title": "Visual annotation feedback loop",
            "priority": "P2",
            "expected_result": "스크린샷 주석이 작업/증거/수정 요청으로 자동 연결",
        },
    ],
    "captures": [
        "docs/research/agentos-hermes-odysseus/agentos_guide_home_benchmark.png",
        "docs/research/agentos-hermes-odysseus/hermes_desktop_docs_benchmark.png",
        "docs/research/agentos-hermes-odysseus/agentos_to_docs_benchmark.png",
        "docs/research/agentos-hermes-odysseus/agentos_hermes_agent_os_benchmark.png",
        "docs/research/agentos-hermes-odysseus/agentos_openclaw_agent_os_benchmark.png",
        "docs/research/agentos-hermes-odysseus/agentos_codex_goal_engine_benchmark.png",
        "docs/research/agentos-hermes-odysseus/hermes_kanban_docs_benchmark.png",
        "docs/research/agentos-hermes-odysseus/channel_play_studio_current_benchmark.png",
    ],
}


def ensure_agentos_absorption(root: Path) -> dict:
    """Return the benchmark matrix, creating the project copy when missing."""

    path = root / MATRIX_PATH
    if path.exists():
        data = read_json(path)
        if isinstance(data, dict) and data:
            return data

    data = deepcopy(DEFAULT_MATRIX)
    write_json(path, data)
    return data
