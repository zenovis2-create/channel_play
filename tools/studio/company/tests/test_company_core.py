from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.studio.company.advance import advance_task
from tools.studio.company.errors import CompanyError
from tools.studio.company.locks import lock_path
from tools.studio.company.planner import assign_task, plan_task
from tools.studio.company.reports import create_review_checkpoint
from tools.studio.company.sessions import end_session, start_session
from tools.studio.company.tasks import archive_tasks
from tools.studio.company.verify import verify_task


class CompanyCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / ".git").mkdir()
        (self.root / "Assets").mkdir()
        memory = self.root / "memory" / "company"
        memory.mkdir(parents=True)
        (self.root / "memory" / "sessions").mkdir(parents=True)
        (self.root / "docs").mkdir()
        (self.root / "docs" / "channel_play_agent_company_plan.md").write_text("# plan\n", encoding="utf-8")
        (memory / "state.json").write_text(
            json.dumps({"project": "channel_play", "active_session": None, "current_orchestrator_task": None}),
            encoding="utf-8",
        )
        (memory / "agent_registry.json").write_text(
            json.dumps(
                {
                    "agents": [
                        {"id": "unity_gameplay", "profile": "agents/roles/unity_gameplay.agent.md"},
                        {"id": "research_librarian", "profile": "agents/roles/research_librarian.agent.md"},
                        {"id": "production_planner", "profile": "agents/roles/production_planner.agent.md"},
                        {"id": "coding_specialist", "profile": "agents/roles/coding_specialist.agent.md"},
                        {"id": "toolchain_integrator", "profile": "agents/roles/toolchain_integrator.agent.md"},
                        {"id": "operator_broadcast_designer", "profile": "agents/roles/operator_broadcast_designer.agent.md"},
                    ]
                }
            ),
            encoding="utf-8",
        )
        (memory / "task_board.json").write_text(json.dumps({"tasks": []}), encoding="utf-8")
        (memory / "locks.json").write_text(json.dumps({"locks": []}), encoding="utf-8")
        (memory / "current_context.md").write_text("# context\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_session_prevents_double_start(self) -> None:
        start_session(self.root, "first")
        with self.assertRaises(CompanyError):
            start_session(self.root, "second")
        end_session(self.root)

    def test_assign_rejects_unknown_agent(self) -> None:
        start_session(self.root, "assign")
        plan_task(self.root, "fix player movement")
        with self.assertRaises(CompanyError):
            assign_task(self.root, "task-0001", "unknown_agent")

    def test_korean_mvp_request_routes_to_unity_gameplay(self) -> None:
        plan_task(self.root, "mvp구현 레벨로 게임 제작해보자")

        board = json.loads((self.root / "memory" / "company" / "task_board.json").read_text(encoding="utf-8"))
        task = board["tasks"][0]
        self.assertEqual(task["suggested_agent"], "unity_gameplay")
        self.assertEqual(task["allowed_write_paths"], ["Assets/_Project/Scripts/Gameplay"])
        self.assertEqual(task["required_evidence"], "Unity compile or playtest evidence")

    def test_planning_request_routes_to_production_planner(self) -> None:
        plan_task(self.root, "다음 마일스톤 구현 순서와 의존성 계획 수립해줘")

        task = json.loads((self.root / "memory" / "company" / "task_board.json").read_text(encoding="utf-8"))["tasks"][0]
        self.assertEqual(task["suggested_agent"], "production_planner")
        self.assertIn("memory/company", task["allowed_write_paths"])
        self.assertIn("dependency map", task["required_evidence"])

    def test_coding_request_routes_to_coding_specialist(self) -> None:
        plan_task(self.root, "Studio UI 버튼 동작 코드 수정하고 테스트해줘")

        task = json.loads((self.root / "memory" / "company" / "task_board.json").read_text(encoding="utf-8"))["tasks"][0]
        self.assertEqual(task["suggested_agent"], "coding_specialist")
        self.assertIn("tools", task["allowed_write_paths"])
        self.assertIn("code diff", task["required_evidence"])

    def test_toolchain_request_routes_to_toolchain_integrator(self) -> None:
        plan_task(self.root, "Codex SDK와 Docker host-runner 연동 상태 검증해줘")

        task = json.loads((self.root / "memory" / "company" / "task_board.json").read_text(encoding="utf-8"))["tasks"][0]
        self.assertEqual(task["suggested_agent"], "toolchain_integrator")
        self.assertIn("memory/company", task["allowed_write_paths"])
        self.assertIn("adapter/runtime", task["required_evidence"])

    def test_research_request_routes_to_research_librarian(self) -> None:
        plan_task(self.root, "NotebookLM으로 Unity 아이템 상점 구현 근거 리서치해줘")

        task = json.loads((self.root / "memory" / "company" / "task_board.json").read_text(encoding="utf-8"))["tasks"][0]
        self.assertEqual(task["suggested_agent"], "research_librarian")
        self.assertIn("docs/research", task["allowed_write_paths"])
        self.assertIn("cited research", task["required_evidence"])

    def test_license_source_request_requires_critic_review(self) -> None:
        plan_task(
            self.root,
            "Truth Pen 원본 또는 명시적 라이선스 콘셉트 소스 준비 및 출처 기록",
        )

        task = json.loads(
            (
                self.root / "memory" / "company" / "task_board.json"
            ).read_text(encoding="utf-8")
        )["tasks"][0]
        self.assertEqual(task["suggested_agent"], "research_librarian")
        self.assertEqual(task["suggested_reviewer"], "critic_reviewer")
        self.assertIn("docs/research", task["allowed_write_paths"])
        self.assertIn("cited research", task["required_evidence"])

    def test_broadcast_request_routes_to_operator_broadcast_designer(self) -> None:
        plan_task(self.root, "OBS 방송용 운영자 화면과 파일럿 촬영 흐름 설계해줘")

        task = json.loads((self.root / "memory" / "company" / "task_board.json").read_text(encoding="utf-8"))["tasks"][0]
        self.assertEqual(task["suggested_agent"], "operator_broadcast_designer")
        self.assertIn("operator flow", task["required_evidence"])

    def test_operator_gameplay_implementation_stays_with_unity_gameplay(self) -> None:
        plan_task(self.root, "운영자 포인트 지급 UI를 Unity에서 구현해줘")

        task = json.loads((self.root / "memory" / "company" / "task_board.json").read_text(encoding="utf-8"))["tasks"][0]
        self.assertEqual(task["suggested_agent"], "unity_gameplay")

    def test_plan_injects_project_brain_and_standards(self) -> None:
        plan_path = plan_task(self.root, "mvp구현 레벨로 Unity 게임 제작해보자")

        memory = self.root / "memory" / "company"
        self.assertTrue((memory / "project_brain.md").exists())
        self.assertTrue((memory / "user_profile.md").exists())
        self.assertTrue((memory / "agent_memory").is_dir())
        self.assertTrue((memory / "standards" / "evidence.md").exists())
        self.assertTrue((memory / "standards" / "unity_scripts.md").exists())

        text = plan_path.read_text(encoding="utf-8")
        self.assertIn("## Project Brain Excerpt", text)
        self.assertIn("## Standards Excerpts", text)
        self.assertIn("Unity Scripts Standard", text)
        self.assertIn("Evidence Standard", text)
        self.assertIn("Do not mark done without evidence or receipt.", text)

    def test_work_order_injects_project_brain_and_standards(self) -> None:
        start_session(self.root, "brain")
        plan_task(self.root, "mvp구현 레벨로 Unity 게임 제작해보자")

        work_order = assign_task(self.root, "task-0001", "unity_gameplay")

        text = work_order.read_text(encoding="utf-8")
        self.assertIn("## Project Brain Excerpt", text)
        self.assertIn("## Standards Excerpts", text)
        self.assertIn("Unity Scripts Standard", text)
        self.assertIn("Evidence Standard", text)
        self.assertIn("Project Brain", text)

    def test_review_checkpoint_moves_task_to_evidence(self) -> None:
        plan_task(self.root, "mvp구현 레벨로 게임 제작해보자")

        report = create_review_checkpoint(self.root, "task-0001")

        board = json.loads((self.root / "memory" / "company" / "task_board.json").read_text(encoding="utf-8"))
        task = board["tasks"][0]
        self.assertEqual(task["status"], "needs_evidence")
        self.assertEqual(task["agent_status"], "reviewed")
        self.assertEqual(task["last_tool"], "studio")
        self.assertEqual(task["report"], report.relative_to(self.root).as_posix())
        self.assertEqual(task["agent_runs"][-1]["mode"], "review")

    def test_verify_accepts_studio_checkpoint_and_closes_task(self) -> None:
        plan_task(self.root, "mvp구현 레벨로 게임 제작해보자")
        report = create_review_checkpoint(self.root, "task-0001")

        verification = verify_task(self.root, "task-0001")

        board = json.loads((self.root / "memory" / "company" / "task_board.json").read_text(encoding="utf-8"))
        task = board["tasks"][0]
        self.assertEqual(task["status"], "closed")
        self.assertEqual(task["verification_status"], "passed")
        self.assertEqual(task["verification"], verification.relative_to(self.root).as_posix())
        self.assertEqual(task["evidence"][0]["path"], report.relative_to(self.root).as_posix())

    def test_verify_accepts_job_receipt_and_closes_task(self) -> None:
        plan_task(self.root, "mvp구현 레벨로 게임 제작해보자")
        jobs_dir = self.root / "memory" / "company" / "jobs"
        jobs_dir.mkdir(parents=True)
        (jobs_dir / "job-0001-receipt.md").write_text("# Job Receipt\n", encoding="utf-8")
        (jobs_dir / "jobs.json").write_text(
            json.dumps(
                {
                    "jobs": [
                        {
                            "id": "job-0001",
                            "commandName": "agent.run",
                            "taskId": "task-0001",
                            "payload": {"taskId": "task-0001"},
                            "status": "succeeded",
                            "ok": True,
                            "createdAt": "2026-06-03T00:00:00Z",
                            "updatedAt": "2026-06-03T00:00:02Z",
                            "receipt": {
                                "path": "memory/company/jobs/job-0001-receipt.md",
                                "summary": "done",
                                "verification": {"status": "passed"},
                            },
                            "events": [],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )

        verify_task(self.root, "task-0001")

        board = json.loads((self.root / "memory" / "company" / "task_board.json").read_text(encoding="utf-8"))
        task = board["tasks"][0]
        self.assertEqual(task["status"], "closed")
        self.assertEqual(task["verification_status"], "passed")
        self.assertEqual(task["evidence"][0]["path"], "memory/company/jobs/job-0001-receipt.md")

    def test_advance_reviews_verifies_and_closes_task(self) -> None:
        plan_task(self.root, "mvp구현 레벨로 게임 제작해보자")
        board = json.loads((self.root / "memory" / "company" / "task_board.json").read_text(encoding="utf-8"))
        board["tasks"][0].update(
            {
                "status": "needs_review",
                "last_agent_run": "runs/agent-codex-task-0001/agent_run.md",
                "report": "runs/agent-codex-task-0001/agent_run.md",
                "agent_runs": [
                    {
                        "tool": "codex",
                        "mode": "run",
                        "status": "dry_run",
                        "path": "runs/agent-codex-task-0001/agent_run.md",
                        "created_at": "2026-06-03T00:00:00+09:00",
                    }
                ],
            }
        )
        run_dir = self.root / "runs" / "agent-codex-task-0001"
        run_dir.mkdir(parents=True)
        (run_dir / "agent_run.md").write_text("# Agent Run\n", encoding="utf-8")
        (self.root / "memory" / "company" / "task_board.json").write_text(json.dumps(board), encoding="utf-8")

        report = advance_task(self.root, "task-0001")

        updated = json.loads((self.root / "memory" / "company" / "task_board.json").read_text(encoding="utf-8"))["tasks"][0]
        self.assertTrue(report.exists())
        self.assertEqual(updated["status"], "closed")
        self.assertEqual(updated["verification_status"], "passed")
        self.assertEqual(updated["review_status"], "reviewed")
        self.assertIn("memory/company/reviews/task-0001-review.md", [item["path"] for item in updated["evidence"]])

    def test_advance_normalizes_passed_task_to_closed(self) -> None:
        plan_task(self.root, "mvp구현 레벨로 게임 제작해보자")
        board = json.loads((self.root / "memory" / "company" / "task_board.json").read_text(encoding="utf-8"))
        board["tasks"][0].update(
            {
                "status": "needs_review",
                "verification_status": "passed",
                "verification": "memory/sessions/unassigned/verification/task-0001-verification.md",
                "last_agent_run": "runs/agent-codex-task-0001/agent_run.md",
            }
        )
        (self.root / "memory" / "company" / "task_board.json").write_text(json.dumps(board), encoding="utf-8")

        advance_task(self.root, "task-0001")

        updated = json.loads((self.root / "memory" / "company" / "task_board.json").read_text(encoding="utf-8"))["tasks"][0]
        self.assertEqual(updated["status"], "closed")
        self.assertEqual(updated["verification_status"], "passed")
        self.assertTrue(updated["closed_at"])

    def test_lock_conflict_detects_parent_child(self) -> None:
        lock_path(self.root, "Assets/_Project/Scripts", "unity_gameplay", "task-0001")
        with self.assertRaises(CompanyError):
            lock_path(self.root, "Assets/_Project/Scripts/Gameplay", "unity_gameplay", "task-0002")

    def test_archive_tasks_moves_entries_out_of_active_board(self) -> None:
        plan_task(self.root, "workflow smoke mvp game flow")
        plan_task(self.root, "mvp구현 레벨로 게임 제작해보자")

        archive_path = archive_tasks(self.root, ["task-0001"], reason="smoke cleanup")

        board = json.loads((self.root / "memory" / "company" / "task_board.json").read_text(encoding="utf-8"))
        archive = json.loads(archive_path.read_text(encoding="utf-8"))
        self.assertEqual([task["id"] for task in board["tasks"]], ["task-0002"])
        self.assertEqual(archive["tasks"][0]["id"], "task-0001")
        self.assertEqual(archive["tasks"][0]["archive_reason"], "smoke cleanup")


if __name__ == "__main__":
    unittest.main()
