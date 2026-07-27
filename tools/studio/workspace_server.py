"""Local web cockpit for Channel Play Studio."""

from __future__ import annotations

from copy import deepcopy
import json
import mimetypes
import os
import re
import secrets
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from tools.studio.company.agent_runner import collect_agent_adapter_state
from tools.studio.company.agentos_absorption import ensure_agentos_absorption
from tools.studio.company.asset_forge import asset_forge_state
from tools.studio.company.brain import ensure_brain_files
from tools.studio.company.errors import CompanyError
from tools.studio.company.game_production import game_production_state
from tools.studio.company.git_info import git_head, git_short_status
from tools.studio.company.goal_engine import goal_state
from tools.studio.company.image_to_blender import image3d_state
from tools.studio.company.model_cookbook import ensure_model_cookbook
from tools.studio.company.paths import find_repo_root, rel
from tools.studio.company.procurement import (
    OWNER_DECISION_FIELDS,
    apply_procurement_answers,
    preview_procurement_answers,
    procurement_answer_digest,
)
from tools.studio.company.search import search_sessions
from tools.studio.company.state import CompanyPaths, load_company_state, read_json, read_text
from tools.studio.company.worker_fleet import ensure_worker_fleet
from tools.studio.company.world_builder import world_state
from tools.studio.docker_runtime import (
    RUNNER_TOKEN_HEADER,
    host_runner_url,
    read_runner_token,
    studio_runtime_state,
)
from tools.studio.jobs import create_job, get_job, list_jobs, start_job

APP_DIR = Path(__file__).resolve().parent / "app"
MAX_FILE_BYTES = 120_000
MAX_PROCUREMENT_PREVIEW_BYTES = 20_000
MAX_PROCUREMENT_STATUS_BYTES = 1_000
PROCUREMENT_APPLY_GRANT_TTL_SECONDS = 300
PROCUREMENT_APPLY_MAX_GRANTS = 64
PROCUREMENT_APPLY_RESULT_TTL_SECONDS = 300
PROCUREMENT_APPLY_MAX_RESULTS = 64
PROCUREMENT_APPLY_ATTEMPT_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
PROCUREMENT_APPLY_CONFIRMATION = "소유자 승인값 저장"
ALLOWED_READ_PREFIXES = (
    "Assets/_Project",
    "agents",
    "asset_pipeline",
    "docs",
    "memory",
    "reviews",
    "runs",
    "tools/studio/templates",
)
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
ALLOW_REMOTE_ENV = "CHANNEL_PLAY_STUDIO_ALLOW_REMOTE"
TOKEN_HEADER = "X-Channel-Play-Token"


class ProcurementApplyGrantStore:
    """Short-lived one-time grants bound to answers and manifest state."""

    def __init__(
        self,
        ttl_seconds: int = PROCUREMENT_APPLY_GRANT_TTL_SECONDS,
        clock=None,
        max_grants: int = PROCUREMENT_APPLY_MAX_GRANTS,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("grant TTL must be positive")
        if max_grants <= 0:
            raise ValueError("grant capacity must be positive")
        self.ttl_seconds = ttl_seconds
        self.max_grants = max_grants
        self._clock = clock or time.monotonic
        self._grants: dict[str, dict[str, object]] = {}
        self._lock = threading.Lock()

    def mint(
        self,
        asset_id: str,
        answer_digest: str,
        manifest_sha256: str,
    ) -> str:
        now = float(self._clock())
        grant_id = secrets.token_urlsafe(32)
        with self._lock:
            self._purge_expired(now)
            if len(self._grants) >= self.max_grants:
                oldest = min(
                    self._grants,
                    key=lambda current: float(
                        self._grants[current].get("expiresAt") or 0
                    ),
                )
                del self._grants[oldest]
            self._grants[grant_id] = {
                "assetId": asset_id,
                "answerDigest": answer_digest,
                "manifestSha256": manifest_sha256,
                "expiresAt": now + self.ttl_seconds,
            }
        return grant_id

    def consume(
        self,
        grant_id: object,
        asset_id: str,
        answer_digest: str,
        manifest_sha256: str,
    ) -> None:
        if not isinstance(grant_id, str) or not grant_id:
            raise CompanyError("Apply grant is invalid or expired.")
        now = float(self._clock())
        with self._lock:
            self._purge_expired(now)
            grant = self._grants.get(grant_id)
            if grant is None:
                raise CompanyError("Apply grant is invalid or expired.")
            matches = (
                grant.get("assetId") == asset_id
                and secrets.compare_digest(
                    str(grant.get("answerDigest") or ""),
                    answer_digest,
                )
                and secrets.compare_digest(
                    str(grant.get("manifestSha256") or ""),
                    manifest_sha256,
                )
            )
            if not matches:
                raise CompanyError(
                    "Apply grant does not match the current preview."
                )
            del self._grants[grant_id]

    def _purge_expired(self, now: float) -> None:
        expired = [
            grant_id
            for grant_id, grant in self._grants.items()
            if float(grant.get("expiresAt") or 0) <= now
        ]
        for grant_id in expired:
            del self._grants[grant_id]


class ProcurementApplyResultStore:
    """Bounded value-redacted results for ambiguous apply responses."""

    SAFE_RESULT_FIELDS = (
        "saved",
        "savedVerified",
        "savedChangeCount",
        "savedChangedFields",
        "protectedStatePreserved",
        "contactAuthorized",
        "receiptCreated",
        "manifest",
        "manifestSha256",
        "nextCommand",
    )

    def __init__(
        self,
        ttl_seconds: int = PROCUREMENT_APPLY_RESULT_TTL_SECONDS,
        clock=None,
        max_results: int = PROCUREMENT_APPLY_MAX_RESULTS,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("result TTL must be positive")
        if max_results <= 0:
            raise ValueError("result capacity must be positive")
        self.ttl_seconds = ttl_seconds
        self.max_results = max_results
        self._clock = clock or time.monotonic
        self._results: dict[str, dict[str, object]] = {}
        self._lock = threading.Lock()

    def reserve(self, attempt_id: object, asset_id: str) -> None:
        clean_attempt_id = _require_procurement_apply_attempt_id(attempt_id)
        now = float(self._clock())
        with self._lock:
            self._purge_expired(now)
            if clean_attempt_id in self._results:
                raise CompanyError("Apply attempt ID has already been used.")
            if len(self._results) >= self.max_results:
                oldest = min(
                    self._results,
                    key=lambda current: float(
                        self._results[current].get("expiresAt") or 0
                    ),
                )
                del self._results[oldest]
            self._results[clean_attempt_id] = {
                "assetId": asset_id,
                "expiresAt": now + self.ttl_seconds,
                "result": None,
            }

    def complete(
        self,
        attempt_id: object,
        asset_id: str,
        result: dict,
    ) -> None:
        clean_attempt_id = _require_procurement_apply_attempt_id(attempt_id)
        safe_result = self._safe_result(asset_id, result)
        now = float(self._clock())
        with self._lock:
            self._purge_expired(now)
            record = self._results.get(clean_attempt_id)
            if (
                record is None
                or record.get("assetId") != asset_id
                or record.get("result") is not None
            ):
                raise CompanyError("Apply attempt is invalid or expired.")
            record["result"] = safe_result

    def lookup(self, attempt_id: object, asset_id: str) -> dict:
        if (
            not isinstance(attempt_id, str)
            or not PROCUREMENT_APPLY_ATTEMPT_ID_PATTERN.fullmatch(attempt_id)
        ):
            return {"found": False, "pending": False}
        now = float(self._clock())
        with self._lock:
            self._purge_expired(now)
            record = self._results.get(attempt_id)
            if record is None or record.get("assetId") != asset_id:
                return {"found": False, "pending": False}
            result = record.get("result")
            if result is None:
                return {"found": False, "pending": True}
            return {
                "found": True,
                "pending": False,
                **deepcopy(result),
            }

    def _safe_result(self, asset_id: str, result: dict) -> dict:
        safe = {
            field: deepcopy(result.get(field))
            for field in self.SAFE_RESULT_FIELDS
        }
        changed_fields = safe["savedChangedFields"]
        canonical_fields = [
            field
            for field in OWNER_DECISION_FIELDS
            if isinstance(changed_fields, list) and field in changed_fields
        ]
        expected_manifest = (
            f"asset_pipeline/manifests/"
            f"{asset_id}_procurement_decision.json"
        )
        valid = (
            safe["saved"] is True
            and isinstance(safe["savedVerified"], bool)
            and type(safe["savedChangeCount"]) is int
            and safe["savedChangeCount"] > 0
            and isinstance(changed_fields, list)
            and safe["savedChangeCount"] == len(changed_fields)
            and changed_fields == canonical_fields
            and safe["protectedStatePreserved"] is True
            and safe["contactAuthorized"] is False
            and safe["receiptCreated"] is False
            and safe["manifest"] == expected_manifest
            and isinstance(safe["manifestSha256"], str)
            and bool(re.fullmatch(r"[0-9a-f]{64}", safe["manifestSha256"]))
            and safe["nextCommand"] == "asset.procurementCheck"
        )
        if not valid:
            raise CompanyError(
                "Apply result could not be retained safely."
            )
        return safe

    def _purge_expired(self, now: float) -> None:
        expired = [
            attempt_id
            for attempt_id, record in self._results.items()
            if float(record.get("expiresAt") or 0) <= now
        ]
        for attempt_id in expired:
            del self._results[attempt_id]


def serve(host: str = "127.0.0.1", port: int = 8766, open_browser: bool = False) -> None:
    _ensure_safe_bind(host)
    root = find_repo_root()
    token = secrets.token_urlsafe(32)
    server = ThreadingHTTPServer((host, port), _handler(root, token=token, host=host, port=port))
    url = f"http://{host}:{port}/"
    if open_browser:
        threading.Timer(0.25, lambda: webbrowser.open(url)).start()
    print(f"Channel Play Studio serving {url}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nChannel Play Studio stopped")
    finally:
        server.server_close()


def collect_workspace_state(root: Path, security: dict | None = None) -> dict:
    company = load_company_state(root)
    paths = CompanyPaths(root)
    jobs = list_jobs(root, limit=50)
    tasks = _enrich_tasks(root, company["tasks"], jobs)
    open_tasks = [task for task in tasks if task.get("status") not in {"closed", "closed_blocked"}]
    brain = ensure_brain_files(root)
    return {
        "project": "channel_play",
        "root": str(root),
        "git": {
            "head": git_head(root),
            "dirty": git_short_status(root),
        },
        "company": {
            "state": company["state"],
            "agents": company["agents"],
            "tasks": tasks,
            "openTasks": open_tasks,
            "locks": company["locks"],
        },
        "memory": {
            "currentContext": read_text(paths.current_context_md),
            "currentBrief": read_text(paths.current_brief_md),
            "decisionLog": read_text(paths.memory_dir / "decision_log.md"),
            "projectBrain": brain["projectBrain"],
            "projectBrainPath": brain["projectBrainPath"],
            "userProfile": brain["userProfile"],
            "userProfilePath": brain["userProfilePath"],
            "agentMemoryPath": brain["agentMemoryPath"],
            "standardsPath": brain["standardsPath"],
            "standards": brain["standards"],
        },
        "feedback": _list_feedback(root),
        "assets": _load_assets(root),
        "assetForge": asset_forge_state(root),
        "imageToBlender": image3d_state(root),
        "worldBuilder": world_state(root),
        "sessions": _list_dirs(root / "memory" / "sessions"),
        "runs": _list_runs(root),
        "sim": {"latestRun": latest_sim_run(root), "proofRefresh": latest_sim_proof_refresh(root)},
        "activity": _activity_state(jobs),
        "adapters": collect_runtime_adapter_state(root),
        "workers": ensure_worker_fleet(root),
        "modelCookbook": ensure_model_cookbook(root),
        "agentosAbsorption": ensure_agentos_absorption(root),
        "gameProduction": game_production_state(root),
        "goals": goal_state(root),
        "runtime": studio_runtime_state(root),
        "jobs": jobs,
        "commands": sorted(COMMANDS.keys()),
        "security": security or {},
    }


def build_command(root: Path, name: str, payload: dict) -> list[str]:
    channelctl = str(root / "tools" / "channelctl")
    if name not in COMMANDS:
        raise CompanyError(f"Command not allowed: {name}")
    return [channelctl, *COMMANDS[name](payload)]


def collect_runtime_adapter_state(root: Path) -> dict:
    if host_runner_url():
        try:
            return _fetch_host_adapters(root)
        except CompanyError as exc:
            state = collect_agent_adapter_state(root)
            state["hostRunnerAdapterError"] = str(exc)
            return state
    return collect_agent_adapter_state(root)


def run_command(root: Path, name: str, payload: dict) -> dict:
    if host_runner_url():
        return _run_command_via_host_runner(root, name, payload)
    return run_local_command(root, name, payload)


def run_local_command(root: Path, name: str, payload: dict) -> dict:
    command = build_command(root, name, payload)
    timeout = 1800 if name in {
        "agent.run",
        "agent.review",
        "orchestrator.run",
        "unity.playtest",
        "unity.simCheck",
        "unity.agentPlaytestPyramid",
        "simAcceptance.proofRefresh",
        "unity.build.windows",
        "unity.build.mac",
        "unity.build.linuxServer",
        "game.productionCheck",
        "game.feedbackLoop",
    } else 240
    env = os.environ.copy()
    env.update(
        {
            "HOME": os.environ.get("HOME", ""),
            "PATH": os.environ.get("PATH", "/usr/bin:/bin:/usr/sbin:/sbin"),
            "UNITY_EDITOR": os.environ.get("UNITY_EDITOR", ""),
            "LANG": os.environ.get("LANG", "en_US.UTF-8"),
        }
    )
    job = create_job(root, name, command, payload)
    start_job(
        root,
        str(job["id"]),
        timeout=timeout,
        env=env,
        task_id_parser=_workflow_task_id if name == "orchestrator.run" else None,
    )
    return {
        "ok": True,
        "jobId": job["id"],
        "status": job["status"],
        "command": command,
        "stdout": "",
        "stderr": "",
    }


def _run_command_via_host_runner(root: Path, name: str, payload: dict) -> dict:
    build_command(root, name, payload)
    token = read_runner_token(root)
    if not token:
        raise CompanyError("Host runner token is not configured.")
    request = urllib.request.Request(
        f"{host_runner_url()}/api/command",
        data=json.dumps({"command": name, "payload": payload}, ensure_ascii=False).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            RUNNER_TOKEN_HEADER: token,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        raise CompanyError(text or f"Host runner returned {exc.code}") from exc
    except (OSError, urllib.error.URLError) as exc:
        raise CompanyError(f"Host runner unavailable: {exc}") from exc
    if not isinstance(data, dict):
        raise CompanyError("Host runner returned an invalid response.")
    if data.get("ok") is False and data.get("error"):
        raise CompanyError(str(data["error"]))
    return data


def _fetch_host_adapters(root: Path) -> dict:
    token = read_runner_token(root)
    if not token:
        raise CompanyError("Host runner token is not configured.")
    request = urllib.request.Request(
        f"{host_runner_url()}/api/adapters",
        headers={RUNNER_TOKEN_HEADER: token},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        raise CompanyError(text or f"Host runner returned {exc.code}") from exc
    except (OSError, urllib.error.URLError) as exc:
        raise CompanyError(f"Host runner unavailable: {exc}") from exc
    if not isinstance(data, dict) or not data.get("ok") or not isinstance(data.get("adapters"), dict):
        raise CompanyError("Host runner returned invalid adapter state.")
    adapters = data["adapters"]
    adapters["source"] = "host_runner"
    return adapters


def read_workspace_file(root: Path, raw_path: str) -> dict:
    path = _safe_path(root, raw_path)
    if not path.exists() or not path.is_file():
        raise CompanyError(f"File not found: {raw_path}")
    if path.stat().st_size > MAX_FILE_BYTES:
        raise CompanyError(f"File too large for preview: {raw_path}")
    return {"path": rel(root, path), "content": path.read_text(encoding="utf-8", errors="replace")}


def _handler(
    root: Path,
    *,
    token: str = "",
    host: str = "127.0.0.1",
    port: int = 8766,
    procurement_grant_ttl_seconds: int = (
        PROCUREMENT_APPLY_GRANT_TTL_SECONDS
    ),
    procurement_grant_clock=None,
    procurement_result_ttl_seconds: int = (
        PROCUREMENT_APPLY_RESULT_TTL_SECONDS
    ),
    procurement_result_clock=None,
    procurement_result_store: ProcurementApplyResultStore | None = None,
):
    procurement_grants = ProcurementApplyGrantStore(
        procurement_grant_ttl_seconds,
        procurement_grant_clock,
    )
    procurement_results = (
        procurement_result_store
        or ProcurementApplyResultStore(
            procurement_result_ttl_seconds,
            procurement_result_clock,
        )
    )
    procurement_apply_lock = threading.Lock()

    class StudioHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            try:
                if parsed.path == "/api/state":
                    self._json(collect_workspace_state(root, self._security_state()))
                    return
                if parsed.path == "/api/sim/latest-run":
                    self._json({"latestRun": latest_sim_run(root)})
                    return
                if parsed.path == "/api/jobs":
                    self._json({"jobs": list_jobs(root)})
                    return
                if parsed.path == "/api/search":
                    query = parse_qs(parsed.query)
                    limit = _query_limit(query.get("limit", ["20"])[0])
                    rebuild = query.get("rebuild", [""])[0].lower() in {"1", "true", "yes"}
                    self._json(search_sessions(root, query.get("q", [""])[0], limit=limit, rebuild=rebuild))
                    return
                if parsed.path.startswith("/api/jobs/"):
                    job_id = parsed.path.rsplit("/", 1)[-1]
                    job = get_job(root, job_id)
                    if not job:
                        self._json({"ok": False, "error": "Job not found"}, status=HTTPStatus.NOT_FOUND)
                        return
                    self._json({"ok": True, "job": job})
                    return
                if parsed.path == "/api/file":
                    query = parse_qs(parsed.query)
                    self._json(read_workspace_file(root, query.get("path", [""])[0]))
                    return
                if parsed.path.startswith("/artifact/"):
                    self._artifact(parsed.path[len("/artifact/"):])
                    return
                if parsed.path == "/favicon.ico":
                    self.send_response(HTTPStatus.NO_CONTENT)
                    self.end_headers()
                    return
                self._static(parsed.path)
            except CompanyError as exc:
                self._json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            except Exception as exc:  # pragma: no cover - defensive web boundary
                self._json({"ok": False, "error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            try:
                if parsed.path not in {
                    "/api/command",
                    "/api/procurement/apply",
                    "/api/procurement/apply-status",
                    "/api/procurement/preview",
                }:
                    self._json({"ok": False, "error": "Unknown API path"}, status=HTTPStatus.NOT_FOUND)
                    return
                self._require_execution_gate()
                if parsed.path == "/api/procurement/preview":
                    data = self._read_json_body(
                        MAX_PROCUREMENT_PREVIEW_BYTES,
                        strict=True,
                    )
                    _require_request_fields(
                        data,
                        {"assetId", "answers"},
                        "Procurement preview",
                    )
                    asset_id = str(data.get("assetId") or "")
                    answers = data.get("answers")
                    result = preview_procurement_answers(
                        root,
                        asset_id,
                        answers,
                    )
                    if (
                        result["valid"]
                        and result["answerCount"]
                        == result["expectedAnswerCount"]
                        and result["changeCount"] > 0
                        and result["protectedStatePreserved"]
                    ):
                        answer_digest = procurement_answer_digest(answers)
                        result["applyGrant"] = procurement_grants.mint(
                            asset_id,
                            answer_digest,
                            result["manifestSha256"],
                        )
                        result["applyGrantExpiresInSeconds"] = (
                            procurement_grants.ttl_seconds
                        )
                        result[
                            "applyResultRecoveryExpiresInSeconds"
                        ] = procurement_results.ttl_seconds
                    self._json({"ok": True, **result})
                    return
                if parsed.path == "/api/procurement/apply-status":
                    data = self._read_json_body(
                        MAX_PROCUREMENT_STATUS_BYTES,
                        strict=True,
                    )
                    _require_request_fields(
                        data,
                        {"assetId", "applyAttemptId"},
                        "Procurement apply status",
                    )
                    asset_id = str(data.get("assetId") or "")
                    attempt_id = _require_procurement_apply_attempt_id(
                        data.get("applyAttemptId")
                    )
                    result = procurement_results.lookup(
                        attempt_id,
                        asset_id,
                    )
                    self._json({"ok": True, **result})
                    return
                if parsed.path == "/api/procurement/apply":
                    data = self._read_json_body(
                        MAX_PROCUREMENT_PREVIEW_BYTES,
                        strict=True,
                    )
                    _require_request_fields(
                        data,
                        {
                            "assetId",
                            "answers",
                            "applyAttemptId",
                            "applyGrant",
                            "confirmation",
                            "expectedManifestSha256",
                        },
                        "Procurement apply",
                    )
                    if (
                        data.get("confirmation")
                        != PROCUREMENT_APPLY_CONFIRMATION
                    ):
                        raise CompanyError(
                            "Explicit owner-save confirmation is required."
                        )
                    asset_id = str(data.get("assetId") or "")
                    attempt_id = _require_procurement_apply_attempt_id(
                        data.get("applyAttemptId")
                    )
                    answers = data.get("answers")
                    expected_digest = str(
                        data.get("expectedManifestSha256") or ""
                    )
                    with procurement_apply_lock:
                        preview = preview_procurement_answers(
                            root,
                            asset_id,
                            answers,
                        )
                        if (
                            not preview["valid"]
                            or preview["answerCount"]
                            != preview["expectedAnswerCount"]
                            or preview["changeCount"] <= 0
                            or not preview["protectedStatePreserved"]
                            or preview["manifestSha256"]
                            != expected_digest
                        ):
                            raise CompanyError(
                                "Owner answers or manifest changed; "
                                "run the preview again."
                            )
                        procurement_results.reserve(
                            attempt_id,
                            asset_id,
                        )
                        answer_digest = procurement_answer_digest(answers)
                        procurement_grants.consume(
                            data.get("applyGrant"),
                            asset_id,
                            answer_digest,
                            expected_digest,
                        )
                        result = apply_procurement_answers(
                            root,
                            asset_id,
                            answers,
                            expected_digest,
                        )
                        procurement_results.complete(
                            attempt_id,
                            asset_id,
                            result,
                        )
                    self._json({"ok": True, **result})
                    return
                data = self._read_json_body()
                self._json(run_command(root, str(data.get("command", "")), data.get("payload") or {}))
            except CompanyError as exc:
                self._json({"ok": False, "error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            except Exception as exc:  # pragma: no cover - defensive web boundary
                self._json({"ok": False, "error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        def log_message(self, fmt: str, *args) -> None:
            return

        def _json(self, data: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
            encoded = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _static(self, path_text: str) -> None:
            target = "index.html" if path_text in {"/", ""} else path_text.lstrip("/")
            path = (APP_DIR / target).resolve()
            if not str(path).startswith(str(APP_DIR.resolve())) or not path.exists() or not path.is_file():
                self.send_error(HTTPStatus.NOT_FOUND, "not found")
                return
            data = path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _artifact(self, raw_path: str) -> None:
            path = _safe_path(root, unquote(raw_path))
            if not path.exists() or not path.is_file():
                self.send_error(HTTPStatus.NOT_FOUND, "not found")
                return
            data = path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _require_execution_gate(self) -> None:
            if not _client_is_loopback(self.client_address[0]) and not _remote_allowed():
                raise CompanyError("Execution API is local-only.")
            if not _host_header_allowed(self.headers.get("Host", ""), host, port):
                raise CompanyError("Execution API rejected this Host header.")
            if not _origin_allowed(self.headers.get("Origin", ""), host, port):
                raise CompanyError("Execution API rejected this Origin header.")
            if token and self.headers.get(TOKEN_HEADER, "") != token:
                raise CompanyError("Execution token missing or invalid.")
            content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
            if content_type != "application/json":
                raise CompanyError("Execution API requires application/json.")

        def _read_json_body(
            self,
            max_bytes: int | None = None,
            *,
            strict: bool = False,
        ) -> dict:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError as exc:
                raise CompanyError("Request Content-Length is invalid.") from exc
            if length < 0:
                raise CompanyError("Request Content-Length is invalid.")
            if max_bytes is not None and length > max_bytes:
                raise CompanyError(
                    "Procurement request exceeds "
                    f"{max_bytes} bytes."
                )
            try:
                body = self.rfile.read(length).decode("utf-8")
                if strict:
                    data = json.loads(
                        body or "{}",
                        parse_constant=_reject_preview_json_constant,
                    )
                else:
                    data = json.loads(body or "{}")
            except (UnicodeDecodeError, ValueError) as exc:
                raise CompanyError(
                    "Request body must be valid UTF-8 JSON."
                ) from exc
            if not isinstance(data, dict):
                raise CompanyError("Request body must be a JSON object.")
            return data

        def _security_state(self) -> dict:
            return {
                "executionToken": token,
                "tokenHeader": TOKEN_HEADER,
                "localOnly": True,
                "host": host,
                "port": port,
                "allowRemote": _remote_allowed(),
            }

    return StudioHandler


def _ensure_safe_bind(host: str) -> None:
    if _host_is_loopback(host) or _remote_allowed():
        return
    raise CompanyError(
        f"Refusing to bind Channel Play Studio to non-loopback host {host!r}. "
        f"Set {ALLOW_REMOTE_ENV}=1 only for a trusted network."
    )


def _reject_preview_json_constant(value: str) -> None:
    raise ValueError(
        f"non-standard numeric constant is prohibited: {value}"
    )


def _require_procurement_apply_attempt_id(value: object) -> str:
    if (
        not isinstance(value, str)
        or not PROCUREMENT_APPLY_ATTEMPT_ID_PATTERN.fullmatch(value)
    ):
        raise CompanyError("Apply attempt ID is invalid.")
    return value


def _require_request_fields(
    data: dict,
    expected: set[str],
    label: str,
) -> None:
    if set(data) != expected:
        raise CompanyError(f"{label} request fields are invalid.")


def _remote_allowed() -> bool:
    return os.environ.get(ALLOW_REMOTE_ENV, "").strip().lower() in {"1", "true", "yes"}


def _host_is_loopback(host: str) -> bool:
    clean = host.strip().strip("[]").lower()
    return clean in LOOPBACK_HOSTS


def _client_is_loopback(host: str) -> bool:
    return _host_is_loopback(host)


def _host_header_allowed(value: str, bind_host: str, bind_port: int) -> bool:
    if not value:
        return False
    host_text, port_text = _split_host_port(value)
    if _host_is_loopback(host_text):
        return True
    if port_text and port_text != str(bind_port):
        return False
    return _remote_allowed() and host_text in {bind_host, "0.0.0.0"}


def _origin_allowed(value: str, bind_host: str, bind_port: int) -> bool:
    if not value:
        return True
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        return False
    if _host_is_loopback(parsed.hostname or ""):
        return True
    if parsed.port and parsed.port != bind_port:
        return False
    return _remote_allowed() and (parsed.hostname or "") in {bind_host, "0.0.0.0"}


def _split_host_port(value: str) -> tuple[str, str]:
    text = value.strip()
    if text.startswith("[") and "]" in text:
        host_text, _, rest = text[1:].partition("]")
        port_text = rest[1:] if rest.startswith(":") else ""
        return host_text, port_text
    if ":" in text:
        host_text, port_text = text.rsplit(":", 1)
        return host_text, port_text
    return text, ""


def _safe_path(root: Path, raw_path: str) -> Path:
    clean = raw_path.strip().lstrip("/")
    if not clean:
        raise CompanyError("Path is required.")
    if not any(clean == prefix or clean.startswith(prefix + "/") for prefix in ALLOWED_READ_PREFIXES):
        raise CompanyError(f"Path not readable from Studio: {raw_path}")
    path = (root / clean).resolve()
    if not str(path).startswith(str(root.resolve())):
        raise CompanyError(f"Path escapes repo: {raw_path}")
    return path


def _list_dirs(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for child in sorted(path.iterdir(), key=lambda item: item.stat().st_mtime if item.exists() else 0, reverse=True)[:24]:
        if child.is_dir():
            rows.append({"name": child.name, "path": rel(path.parents[1], child)})
    return rows


def _list_feedback(root: Path) -> list[dict]:
    rows = []
    base = root / "reviews"
    if not base.exists():
        return rows
    for note in sorted(base.glob("20*/feedback-*/feedback.md"), key=lambda item: item.stat().st_mtime, reverse=True)[:24]:
        text = note.read_text(encoding="utf-8", errors="ignore")
        rows.append(
            {
                "id": note.parent.name,
                "path": rel(root, note),
                "status": _field(text, "Status") or "unknown",
                "scene": _field(text, "Scene") or "TBD",
                "screenshot": _field(text, "Screenshot") or "TBD",
                "run": _field(text, "Run") or "TBD",
                "frame": _field(text, "Frame") or "TBD",
                "action": _field(text, "Action") or "TBD",
                "request": _section_excerpt(text, "Requested Change") or "TBD",
            }
        )
    return rows


def _load_assets(root: Path) -> list[dict]:
    index = root / "asset_pipeline" / "index.json"
    if not index.exists():
        return []
    return read_json(index).get("assets", [])


def _list_runs(root: Path) -> list[dict]:
    base = root / "runs"
    if not base.exists():
        return []
    rows = []
    for child in sorted(base.iterdir(), key=lambda item: item.stat().st_mtime if item.exists() else 0, reverse=True)[:32]:
        if not child.is_dir():
            continue
        md_files = list(child.glob("*.md"))
        rows.append({"name": child.name, "path": rel(root, child), "file": rel(root, md_files[0]) if md_files else ""})
    return rows


def latest_sim_run(root: Path) -> dict:
    base = root / "runs"
    if not base.exists():
        return {"exists": False}

    candidates = [
        child
        for child in base.iterdir()
        if child.is_dir() and child.name.startswith("agent-playtest-")
    ]
    if not candidates:
        return {"exists": False}

    ordered_runs = sorted(candidates, key=lambda item: item.stat().st_mtime, reverse=True)
    run_dir = ordered_runs[0]
    previous_run = ordered_runs[1] if len(ordered_runs) > 1 else None
    observations_dir = run_dir / "observations"
    rgb_frames = sorted(observations_dir.glob("*_rgb.png")) if observations_dir.exists() else []
    segmentation_frames = sorted(observations_dir.glob("*_segmentation.png")) if observations_dir.exists() else []
    depth_frames = sorted(observations_dir.glob("*_depth.png")) if observations_dir.exists() else []
    metadata_frames = sorted(observations_dir.glob("frame_*.json")) if observations_dir.exists() else []
    command = _read_json_safe(run_dir / "command.json")
    actions_tail = _read_jsonl_tail(run_dir / "actions.jsonl", 8)
    latest_metadata = _read_json_safe(metadata_frames[-1]) if metadata_frames else {}
    receipt_text = _read_text_safe(run_dir / "receipt.md", limit=8000)
    review_text = _read_text_safe(run_dir / "review.md", limit=6000)
    status = _extract_backtick_value(receipt_text, "Status") or "unknown"
    route_completion = "Route completion: `true`" in receipt_text
    action_count = _count_nonempty_lines(run_dir / "actions.jsonl")
    metric_count = _count_nonempty_lines(run_dir / "metrics.jsonl")
    latest_frame = rgb_frames[-1] if rgb_frames else None
    first_frame = rgb_frames[0] if rgb_frames else None

    return {
        "exists": True,
        "name": run_dir.name,
        "path": rel(root, run_dir),
        "previousRun": rel(root, previous_run) if previous_run else "",
        "status": status,
        "routeCompletion": route_completion,
        "agent": command.get("agent", "scripted") if isinstance(command, dict) else "scripted",
        "environment": command.get("environment", "pyramid-maze-v2") if isinstance(command, dict) else "pyramid-maze-v2",
        "scene": command.get("scene", "School_MVP") if isinstance(command, dict) else "School_MVP",
        "counts": {
            "rgb": len(rgb_frames),
            "segmentation": len(segmentation_frames),
            "depth": len(depth_frames),
            "metadata": len(metadata_frames),
            "actions": action_count,
            "metrics": metric_count,
        },
        "command": {
            "text": command.get("command", "") if isinstance(command, dict) else "",
            "routeOrder": command.get("routeOrder", []) if isinstance(command, dict) else [],
            "allowedActions": command.get("allowedActions", []) if isinstance(command, dict) else [],
        },
        "artifacts": {
            "receipt": rel(root, run_dir / "receipt.md") if (run_dir / "receipt.md").exists() else "",
            "review": rel(root, run_dir / "review.md") if (run_dir / "review.md").exists() else "",
            "command": rel(root, run_dir / "command.json") if (run_dir / "command.json").exists() else "",
            "sceneState": rel(root, run_dir / "scene_state.json") if (run_dir / "scene_state.json").exists() else "",
            "semanticLabels": rel(root, run_dir / "semantic_labels.json") if (run_dir / "semantic_labels.json").exists() else "",
            "actions": rel(root, run_dir / "actions.jsonl") if (run_dir / "actions.jsonl").exists() else "",
            "metrics": rel(root, run_dir / "metrics.jsonl") if (run_dir / "metrics.jsonl").exists() else "",
            "trajectory": rel(root, run_dir / "trajectory.json") if (run_dir / "trajectory.json").exists() else "",
        },
        "frames": {
            "firstRgb": rel(root, first_frame) if first_frame else "",
            "latestRgb": rel(root, latest_frame) if latest_frame else "",
            "latestMetadata": rel(root, metadata_frames[-1]) if metadata_frames else "",
        },
        "latestAction": actions_tail[-1] if actions_tail else {},
        "latestFrame": latest_metadata,
        "eventStream": _sim_event_stream(actions_tail, latest_metadata),
        "summary": _sim_summary(status, route_completion, len(rgb_frames), action_count, metric_count),
        "reviewExcerpt": _excerpt_markdown(review_text),
        "updatedAt": run_dir.stat().st_mtime,
    }


def latest_sim_proof_refresh(root: Path) -> dict:
    base = root / "runs"
    if not base.exists():
        return {"exists": False}

    candidates = [
        child
        for child in base.iterdir()
        if child.is_dir() and child.name.startswith("sim-proof-refresh-")
    ]
    if not candidates:
        return {"exists": False}

    run_dir = max(candidates, key=lambda item: item.stat().st_mtime)
    bundle_path = run_dir / "proof_bundle.json"
    receipt_path = run_dir / "receipt.md"
    bundle = _read_json_safe(bundle_path)
    steps = bundle.get("steps") if isinstance(bundle.get("steps"), list) else []
    evidence = bundle.get("evidence") if isinstance(bundle.get("evidence"), dict) else {}
    passed_steps = [step for step in steps if step.get("status") == "passed"]
    failed_steps = [step for step in steps if step.get("status") not in {"passed", "skipped"}]
    evidence_rows = [
        {
            "key": key,
            "path": str(path or ""),
            "exists": bool(path) and (root / str(path)).exists(),
        }
        for key, path in evidence.items()
    ]
    status = str(bundle.get("status") or "unknown")
    return {
        "exists": True,
        "name": run_dir.name,
        "path": rel(root, run_dir),
        "status": status,
        "mode": str(bundle.get("mode") or ""),
        "checkedAt": str(bundle.get("checkedAt") or ""),
        "semanticAssetId": str(bundle.get("semanticAssetId") or ""),
        "summary": f"{status} · steps {len(passed_steps)}/{len(steps)} · evidence {sum(1 for item in evidence_rows if item['exists'])}/{len(evidence_rows)}",
        "counts": {
            "steps": len(steps),
            "passed": len(passed_steps),
            "failed": len(failed_steps),
            "evidence": len(evidence_rows),
            "evidenceReady": sum(1 for item in evidence_rows if item["exists"]),
        },
        "steps": [
            {
                "id": str(step.get("id") or ""),
                "status": str(step.get("status") or ""),
                "required": bool(step.get("required", True)),
                "path": _display_path(root, str(step.get("path") or "")),
                "detail": str(step.get("detail") or ""),
            }
            for step in steps[:12]
        ],
        "evidence": evidence_rows,
        "artifacts": {
            "receipt": rel(root, receipt_path) if receipt_path.exists() else "",
            "bundle": rel(root, bundle_path) if bundle_path.exists() else "",
        },
        "updatedAt": run_dir.stat().st_mtime,
    }


def _sim_summary(status: str, route_completion: bool, observations: int, actions: int, metrics: int) -> str:
    route = "route complete" if route_completion else "route incomplete"
    return f"{status} · {route} · observations {observations} · actions {actions} · metrics {metrics}"


def _activity_state(jobs: list[dict]) -> dict:
    active = next((job for job in jobs if not job.get("isTerminal")), None)
    latest = jobs[0] if jobs else {}
    return {
        "activeCommand": _activity_job(active) if active else {},
        "latestCommand": _activity_job(latest) if latest else {},
        "latestEvents": _latest_job_events(jobs),
    }


def _activity_job(job: dict) -> dict:
    return {
        "id": str(job.get("id") or ""),
        "commandName": str(job.get("commandName") or ""),
        "status": str(job.get("status") or ""),
        "command": " ".join(str(part) for part in (job.get("command") or [])),
        "event": _job_last_event(job),
        "receipt": str((job.get("receipt") or {}).get("path") or ""),
        "isTerminal": bool(job.get("isTerminal")),
    }


def _latest_job_events(jobs: list[dict]) -> list[dict]:
    rows = []
    for job in jobs[:8]:
        for event in (job.get("events") or [])[-4:]:
            rows.append(
                {
                    "jobId": str(job.get("id") or ""),
                    "commandName": str(job.get("commandName") or ""),
                    "status": str(job.get("status") or ""),
                    "time": str(event.get("time") or ""),
                    "type": str(event.get("type") or ""),
                    "message": str(event.get("message") or ""),
                }
            )
    rows.sort(key=lambda item: item.get("time", ""), reverse=True)
    return rows[:12]


def _read_jsonl_tail(path: Path, limit: int) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines()[-limit:]:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            rows.append(json.loads(stripped))
        except json.JSONDecodeError:
            rows.append({"raw": stripped})
    return rows


def _sim_event_stream(actions: list[dict], latest_metadata: dict) -> list[dict]:
    rows = [
        {
            "type": "action",
            "label": str(action.get("action") or action.get("raw") or ""),
            "status": str(action.get("status") or "ok"),
            "target": str(action.get("target") or ""),
            "reason": str(action.get("reason") or ""),
        }
        for action in actions[-6:]
    ]
    if latest_metadata:
        rows.append(
            {
                "type": "frame",
                "label": "latest_observation",
                "status": str(latest_metadata.get("depthStatus") or ""),
                "target": str(latest_metadata.get("routeMarker") or ""),
                "reason": str(latest_metadata.get("depthMethod") or ""),
            }
        )
    return rows


def _read_json_safe(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))
    except json.JSONDecodeError:
        return {}


def _display_path(root: Path, path: str) -> str:
    if not path:
        return ""
    candidate = Path(path)
    if candidate.is_absolute() and str(candidate).startswith(str(root)):
        return rel(root, candidate)
    return path


def _read_text_safe(path: Path, *, limit: int) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")[:limit]


def _extract_backtick_value(text: str, key: str) -> str:
    marker = f"{key}: `"
    start = text.find(marker)
    if start < 0:
        return ""
    start += len(marker)
    end = text.find("`", start)
    return text[start:end] if end >= 0 else ""


def _excerpt_markdown(text: str) -> str:
    lines = [line.strip("# ").strip() for line in text.splitlines() if line.strip()]
    return " · ".join(lines[:4])


def _count_nonempty_lines(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip())


def _enrich_tasks(root: Path, tasks: list[dict], jobs: list[dict]) -> list[dict]:
    enriched = []
    for task in tasks:
        task_jobs = _task_jobs(task, jobs)
        row = {
            **task,
            "jobs": task_jobs,
            "artifacts": _task_artifacts(root, task, task_jobs),
        }
        row["answerSummary"] = _task_answer_summary(root, row)
        row["productionCard"] = _production_card(row)
        enriched.append(row)
    return enriched


def _task_answer_summary(root: Path, task: dict) -> dict:
    path = _preferred_answer_path(task)
    if not path:
        return {"path": "", "summary": ""}
    full_path = (root / path).resolve()
    if not str(full_path).startswith(str(root.resolve())) or not full_path.exists() or not full_path.is_file():
        return {"path": path, "summary": ""}
    text = full_path.read_text(encoding="utf-8", errors="replace")
    summary = _markdown_section(text, "Output") or _markdown_section(text, "Result") or _markdown_section(text, "Summary")
    if not summary:
        summary = _fallback_markdown_summary(text)
    return {"path": path, "summary": _compact_summary(summary)}


def _preferred_answer_path(task: dict) -> str:
    runs = [
        run
        for run in task.get("agent_runs") or []
        if str(run.get("mode") or "") == "run" and str(run.get("path") or "")
    ]
    if runs:
        return str(runs[-1].get("path") or "")
    for artifact in task.get("artifacts") or []:
        if artifact.get("kind") == "answer" and artifact.get("path"):
            return str(artifact.get("path") or "")
    return str(task.get("last_agent_run") or "")


def _markdown_section(text: str, heading: str) -> str:
    lines = text.splitlines()
    capture = False
    rows: list[str] = []
    target = f"## {heading}".lower()
    for line in lines:
        lower = line.strip().lower()
        if lower.startswith("## ") and capture:
            break
        if lower == target:
            capture = True
            continue
        if capture:
            rows.append(line)
    return "\n".join(rows).strip()


def _fallback_markdown_summary(text: str) -> str:
    rows = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith(("Task ID:", "Role:", "Tool:", "Executor:", "Mode:", "Status:", "Exit:", "Created:")):
            continue
        rows.append(stripped)
    return "\n".join(rows)


def _compact_summary(text: str, limit: int = 1200) -> str:
    compact = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    if len(compact) <= limit:
        return compact
    return f"{compact[:limit].rstrip()}..."


def _task_artifacts(root: Path, task: dict, jobs: list[dict] | None = None) -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    task_id = str(task.get("id") or "")

    if task_id:
        _add_artifact(root, rows, seen, "plan", "작업 계획", f"memory/company/{task_id}-plan.md", "plan")
        _add_artifact(root, rows, seen, "workflow", "워크플로우 요약", f"memory/company/workflows/{task_id}-workflow.md", "workflow")

    for key, kind, label in (
        ("work_order", "plan", "작업 주문"),
        ("last_agent_run", "answer", "에이전트 답변"),
        ("report", "report", "보고/리뷰"),
        ("verification", "verification", "검증 결과"),
    ):
        _add_artifact(root, rows, seen, kind, label, str(task.get(key) or ""), label)

    for index, run in enumerate(task.get("agent_runs") or [], start=1):
        tool = str(run.get("tool") or "agent")
        mode = str(run.get("mode") or "run")
        label = f"에이전트 실행 {index}: {tool} {mode}"
        artifact = _add_artifact(root, rows, seen, "run", label, str(run.get("path") or ""), str(run.get("status") or "run"))
        if artifact:
            artifact["created_at"] = str(run.get("created_at") or "")
            artifact["tool"] = tool
            artifact["mode"] = mode
            artifact["status"] = str(run.get("status") or "")

    for index, evidence in enumerate(task.get("evidence") or [], start=1):
        label = f"증거 {index}"
        artifact = _add_artifact(root, rows, seen, "evidence", label, str(evidence.get("path") or ""), str(evidence.get("note") or "evidence"))
        if artifact:
            artifact["created_at"] = str(evidence.get("attached_at") or "")
            artifact["note"] = str(evidence.get("note") or "")

    for index, job in enumerate(jobs or [], start=1):
        receipt = job.get("receipt") or {}
        receipt_path = str(receipt.get("path") or "")
        label = f"실행 영수증 {index}: {commandText(job)}"
        artifact = _add_artifact(root, rows, seen, "receipt", label, receipt_path, str(receipt.get("summary") or job.get("status") or "receipt"))
        if artifact:
            artifact["created_at"] = str(job.get("endedAt") or job.get("updatedAt") or "")
            artifact["jobId"] = str(job.get("id") or "")
            artifact["status"] = str(job.get("status") or "")

    return rows


def _task_jobs(task: dict, jobs: list[dict]) -> list[dict]:
    task_id = str(task.get("id") or "")
    if not task_id:
        return []
    rows = []
    for job in jobs:
        payload = job.get("payload") if isinstance(job.get("payload"), dict) else {}
        job_task_id = str(job.get("taskId") or payload.get("taskId") or payload.get("task_id") or "")
        if job_task_id == task_id:
            rows.append(job)
    return rows


def _production_card(task: dict) -> dict:
    jobs = task.get("jobs") or []
    latest_job = jobs[0] if jobs else {}
    receipt = latest_job.get("receipt") or {}
    next_action = _task_next_action(task, latest_job)
    return {
        "goal": str(task.get("request") or task.get("id") or ""),
        "agent": str(task.get("assigned_agent") or task.get("suggested_agent") or "chief_orchestrator"),
        "collaborators": [
            value
            for value in (
                str(task.get("suggested_reviewer") or "critic_reviewer"),
                "evidence_board" if task.get("evidence") or receipt else "",
            )
            if value
        ],
        "stage": _production_stage(task, latest_job),
        "runningCommand": " ".join(str(part) for part in (latest_job.get("command") or [])),
        "lastHeartbeat": _job_last_event(latest_job),
        "artifactCount": len(task.get("artifacts") or []),
        "verification": str(task.get("verification_status") or (receipt.get("verification") or {}).get("status") or "pending"),
        "receiptPath": str(receipt.get("path") or ""),
        "nextAction": next_action,
        "completionMethod": _completion_method(task, latest_job),
    }


def _task_next_action(task: dict, latest_job: dict) -> dict:
    status = str(task.get("status") or "")
    receipt = latest_job.get("receipt") or {}
    if task.get("closed_at") or task.get("verification_status") == "passed":
        return {"command": "", "label": "완료 결과 확인", "reason": "검증이 통과되어 결과물과 receipt만 확인하면 됩니다."}
    if latest_job and not latest_job.get("isTerminal"):
        return {"command": "", "label": "실행 이벤트 확인", "reason": "명령이 아직 진행 중입니다."}
    if status == "needs_review":
        return {"command": "company.advance", "label": "자동 리뷰/검증 진행", "reason": "실행 보고가 있어 리뷰와 검증을 자동으로 시도할 수 있습니다."}
    if status in {"needs_evidence", "evidence_attached"}:
        if receipt.get("path") or task.get("report") or task.get("last_agent_run"):
            return {"command": "company.advance", "label": "자동 증거 검증", "reason": "receipt/report/checkpoint를 증거로 사용해 완료를 시도할 수 있습니다."}
        return {"command": "company.evidence", "label": "증거 파일 연결", "reason": "완료하려면 증거나 receipt가 필요합니다."}
    if status == "closed":
        return {"command": "", "label": "완료 결과 확인", "reason": "작업이 닫혔습니다."}
    if status == "closed_blocked":
        return {"command": "", "label": "차단 사유 확인", "reason": str(task.get("blocked_reason") or "차단 종료되었습니다.")}
    return {"command": "agent.run", "label": "에이전트 실행", "reason": "작업을 실행하고 결과 receipt를 생성합니다."}


def _completion_method(task: dict, latest_job: dict) -> str:
    if task.get("closed_at") or task.get("verification_status") == "passed":
        if task.get("verification_status") == "passed":
            return "검증 통과로 완료"
        return "수동 종료"
    receipt = (latest_job.get("receipt") or {}).get("path")
    if receipt:
        return "실행 receipt 생성됨"
    if task.get("last_agent_run"):
        return "에이전트 실행 결과 대기"
    return "아직 완료되지 않음"


def _production_stage(task: dict, latest_job: dict) -> str:
    if task.get("closed_at") or task.get("verification_status") == "passed":
        return "closed"
    if latest_job and not latest_job.get("isTerminal"):
        return str(latest_job.get("status") or "running")
    return str(task.get("status") or latest_job.get("status") or "pending")


def _job_last_event(job: dict) -> str:
    events = job.get("events") or []
    if not events:
        return ""
    event = events[-1]
    return f"{event.get('type', '')}: {event.get('message', '')}"


def commandText(job: dict) -> str:
    return str(job.get("commandName") or job.get("id") or "job")


def _add_artifact(root: Path, rows: list[dict], seen: set[str], kind: str, label: str, raw_path: str, note: str) -> dict | None:
    path = raw_path.strip()
    if not path or path in seen:
        return None
    seen.add(path)
    full_path = (root / path).resolve()
    exists = str(full_path).startswith(str(root.resolve())) and full_path.exists() and full_path.is_file()
    artifact = {
        "kind": kind,
        "label": label,
        "path": path,
        "note": note,
        "exists": exists,
    }
    rows.append(artifact)
    return artifact


def _field(text: str, name: str) -> str:
    prefix = f"{name}:"
    for line in text.splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    return ""


def _section_excerpt(text: str, name: str) -> str:
    marker = f"## {name}"
    if marker not in text:
        return ""
    tail = text.split(marker, 1)[1]
    if "\n## " in tail:
        tail = tail.split("\n## ", 1)[0]
    lines = [line.strip() for line in tail.splitlines() if line.strip() and line.strip().upper() != "TBD"]
    return " ".join(lines)[:240]


def _required(payload: dict, key: str) -> str:
    value = str(payload.get(key, "")).strip()
    if not value:
        raise CompanyError(f"Missing field: {key}")
    return value


def _optional(payload: dict, key: str) -> str:
    return str(payload.get(key, "")).strip()


def _query_limit(raw_value: str) -> int:
    try:
        return max(1, min(int(raw_value), 50))
    except ValueError:
        return 20


def _agent_args(action: str, payload: dict) -> list[str]:
    args = ["agent", action, _required(payload, "taskId")]
    tool = _optional(payload, "tool")
    if tool:
        args.extend(["--tool", tool])
    if payload.get("dryRun"):
        args.append("--dry-run")
    if payload.get("fullApproval", action == "run") and not payload.get("manualReview"):
        args.append("--full-approval")
    if payload.get("manualReview"):
        args.append("--manual-review")
    message = _optional(payload, "message")
    if message:
        args.extend(["--message", message])
    return args


def _goal_run_args(payload: dict) -> list[str]:
    args = ["company", "goal", "run", "--max-iterations", str(int(payload.get("maxIterations") or 12))]
    if not payload.get("dryRun", False):
        args.append("--real")
    return args


def _proof_refresh_args(payload: dict) -> list[str]:
    args = ["sim-acceptance", "proof-refresh"]
    if payload.get("collectOnly"):
        args.append("--collect-only")
    asset_id = str(payload.get("assetId") or payload.get("semanticAssetId") or "").strip()
    if asset_id:
        args.extend(["--semantic-asset", asset_id])
    return args


COMMANDS = {
    "company.status": lambda payload: ["company", "status"],
    "company.agents": lambda payload: ["company", "agents"],
    "company.brief": lambda payload: ["company", "brief"],
    "company.workers.probe": lambda payload: ["company", "workers", "--probe"],
    "company.models.refresh": lambda payload: ["company", "models", "--refresh"],
    "company.session.start": lambda payload: ["company", "session", "start", _required(payload, "goal")],
    "company.session.end": lambda payload: ["company", "session", "end"],
    "company.plan": lambda payload: ["company", "plan", _required(payload, "request")],
    "company.goal.set": lambda payload: ["company", "goal", "set", _required(payload, "objective"), "--max-iterations", str(int(payload.get("maxIterations") or 12))],
    "company.goal.run": lambda payload: _goal_run_args(payload),
    "company.goal.status": lambda payload: ["company", "goal", "status"],
    "orchestrator.run": lambda payload: _workflow_args(payload),
    "company.assign": lambda payload: ["company", "assign", _required(payload, "taskId"), _required(payload, "agentId")],
    "company.locks": lambda payload: ["company", "locks"],
    "company.lock": lambda payload: ["company", "lock", _required(payload, "path"), _required(payload, "owner"), _required(payload, "taskId")],
    "company.unlock": lambda payload: ["company", "unlock", _required(payload, "path")],
    "company.report": lambda payload: ["company", "report", _required(payload, "taskId"), _required(payload, "agentId"), str(payload.get("status", "needs_review"))],
    "company.review": lambda payload: ["company", "review", _required(payload, "taskId"), str(payload.get("reviewerId", "critic_reviewer"))],
    "company.evidence": lambda payload: ["company", "evidence", _required(payload, "taskId"), _required(payload, "path"), str(payload.get("note", ""))],
    "company.verify": lambda payload: ["company", "verify", _required(payload, "taskId")],
    "company.advance": lambda payload: ["company", "advance", _required(payload, "taskId")],
    "company.close": lambda payload: ["company", "close", _required(payload, "taskId")],
    "agent.adapters": lambda payload: ["agent", "adapters"],
    "agent.run": lambda payload: _agent_args("run", payload),
    "agent.review": lambda payload: _agent_args("review", payload),
    "unity.check": lambda payload: ["unity", "check"],
    "unity.compile": lambda payload: ["unity", "check", "--batch"],
    "unity.playtest": lambda payload: ["unity", "playtest"],
    "unity.simCheck": lambda payload: ["unity", "sim-check"],
    "unity.semanticCheck": lambda payload: ["unity", "semantic-check", _required(payload, "assetId")],
    "unity.agentPlaytestPyramid": lambda payload: ["unity", "agent-playtest", "pyramid-maze-v2", "--agent", "scripted"],
    "unity.simReviewLatest": lambda payload: ["unity", "sim-review", _required(payload, "runDir")],
    "unity.simReplayLatest": lambda payload: ["unity", "sim-replay", _required(payload, "runDir")],
    "unity.simCompare": lambda payload: ["unity", "sim-compare", _required(payload, "runDirA"), _required(payload, "runDirB")],
    "unity.build.windows": lambda payload: ["unity", "build", "windows-dev"],
    "unity.build.mac": lambda payload: ["unity", "build", "mac-dev"],
    "unity.build.linuxServer": lambda payload: ["unity", "build", "linux-server"],
    "game.status": lambda payload: ["game", "status"],
    "game.productionCheck": lambda payload: ["game", "production-check", "--capture", "--build"],
    "game.feedbackLoop": lambda payload: ["game", "feedback-loop"],
    "game.serverHandoff": lambda payload: ["game", "server-handoff"],
    "simworld.probe": lambda payload: ["simworld", "probe"],
    "simworld.doctor": lambda payload: ["simworld", "doctor"],
    "simworld.installBaseDryRun": lambda payload: ["simworld", "install-base", "--dry-run"],
    "simworld.routePlan": lambda payload: ["simworld", "route-plan"],
    "simworld.startServer": lambda payload: ["simworld", "start-server"],
    "simworld.workerGuide": lambda payload: ["simworld", "worker-guide"],
    "simAgent.runCodex": lambda payload: ["sim-agent", "run", "codex", _required(payload, "runDir")],
    "simAgent.runOpenClaw": lambda payload: ["sim-agent", "run", "openclaw", _required(payload, "runDir")],
    "simAgent.packet": lambda payload: ["sim-agent", "packet", _required(payload, "runDir")],
    "simAgent.liveCheckAll": lambda payload: [
        "sim-agent",
        "live-check",
        "all",
        _required(payload, "runDir"),
        "--timeout",
        str(int(payload.get("timeout") or 240)),
    ],
    "simAcceptance.check": lambda payload: ["sim-acceptance", "check"],
    "simAcceptance.proofRefresh": _proof_refresh_args,
    "simAcceptance.handoff": lambda payload: ["sim-acceptance", "handoff"],
    "capture.screen": lambda payload: ["capture", "screen"],
    "feedback.new": lambda payload: ["feedback", "new"],
    "feedback.process": lambda payload: ["feedback", "process", _required(payload, "path")],
    "asset.new": lambda payload: ["asset", "new", _required(payload, "assetId")],
    "asset.prepare": lambda payload: ["asset", "prepare", _required(payload, "assetId")],
    "asset.procurementCheck": lambda payload: [
        "asset",
        "procurement-check",
        _required(payload, "assetId"),
    ],
    "asset.status": lambda payload: ["asset", "status", _required(payload, "assetId"), _required(payload, "status")],
    "asset.screenshot": lambda payload: ["asset", "screenshot", _required(payload, "assetId"), _required(payload, "path")],
    "asset.semanticPack": lambda payload: ["asset", "semantic-pack", _required(payload, "assetId")],
    "asset.forge": lambda payload: [
        "asset",
        "forge",
        _required(payload, "assetId"),
        "--kind",
        str(payload.get("kind") or "prop"),
        "--prompt",
        str(payload.get("prompt") or ""),
    ],
    "asset.image3d": lambda payload: [
        "asset",
        "image3d",
        _required(payload, "assetId"),
        "--provider",
        str(payload.get("provider") or "trellis2"),
        "--prompt",
        str(payload.get("prompt") or ""),
        "--source-image",
        str(payload.get("sourceImage") or ""),
    ],
    "world.build": lambda payload: [
        "world",
        "build",
        _required(payload, "worldId"),
        "--theme",
        str(payload.get("theme") or "pyramid"),
        "--prompt",
        str(payload.get("prompt") or ""),
    ],
    "gdx.probe": lambda payload: ["gdx", "probe"],
    "gdx.sync": lambda payload: ["gdx", "sync"],
    "gdx.runServer": lambda payload: ["gdx", "run-server"],
    "gdx.runBots": lambda payload: ["gdx", "run-bots"],
    "gdx.collectLogs": lambda payload: ["gdx", "collect-logs"],
}


def _workflow_args(payload: dict) -> list[str]:
    args = ["company", "workflow", _required(payload, "request")]
    if not payload.get("dryRun", False):
        args.append("--real")
    return args


def _workflow_task_id(stdout: str) -> str:
    marker = "memory/company/workflows/"
    if marker not in stdout:
        return ""
    tail = stdout.split(marker, 1)[1].strip()
    filename = tail.split()[0].split("/", 1)[0]
    if filename.startswith("task-") and filename.endswith("-workflow.md"):
        return filename.removesuffix("-workflow.md")
    return ""
