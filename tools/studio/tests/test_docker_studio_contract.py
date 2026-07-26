from __future__ import annotations

import unittest
from pathlib import Path


class DockerStudioContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[3]
        self.compose = (self.root / "docker-compose.studio.yml").read_text(
            encoding="utf-8"
        )
        self.app = (self.root / "tools" / "studio" / "app" / "app.js").read_text(
            encoding="utf-8"
        )
        self.index = (
            self.root / "tools" / "studio" / "app" / "index.html"
        ).read_text(encoding="utf-8")
        self.style = (
            self.root / "tools" / "studio" / "app" / "style.css"
        ).read_text(encoding="utf-8")

    def test_admin_console_is_published_on_host_loopback_only(self) -> None:
        self.assertIn(
            '"127.0.0.1:${CHANNEL_PLAY_STUDIO_PORT:-8776}:8776"',
            self.compose,
        )

    def test_container_has_no_privileged_or_docker_socket_access(self) -> None:
        self.assertNotIn("privileged:", self.compose)
        self.assertNotIn("/var/run/docker.sock", self.compose)

    def test_game_next_action_can_open_guidance_artifact(self) -> None:
        self.assertIn("next.artifact", self.app)
        self.assertIn(
            'data-game-artifact-path="${esc(next.artifact)}"',
            self.app,
        )
        self.assertIn(
            'next.actionLabel || "안내서 열기"',
            self.app,
        )

    def test_procurement_checklist_is_read_only_and_accessible(self) -> None:
        self.assertIn('id="gameProcurementChecklist"', self.index)
        self.assertIn('aria-label="작가 조달 미결정 항목"', self.index)
        self.assertNotIn('aria-live="polite"', self.index)
        start = self.app.index(
            '$("#gameProcurementChecklist").innerHTML'
        )
        end = self.app.index(
            '$("#gameProductionChecks").innerHTML',
            start,
        )
        checklist = self.app[start:end]

        self.assertIn("procurement.errors", self.app)
        self.assertIn("procurement.issueGroups", self.app)
        self.assertIn("procurement.decisionProgress", self.app)
        self.assertIn("procurement.decisionWorksheet", self.app)
        self.assertIn(
            "procurement.passed\n    && Boolean(procurement.receipt)",
            self.app,
        )
        self.assertIn("procurementContactReady", checklist)
        self.assertIn("최신 PASS 영수증 전에는 작가 연락 금지", self.app)
        self.assertIn("의사결정 통과 · 최신 PASS 영수증 대기", self.app)
        self.assertIn("procurementChecklistGroups.map", checklist)
        self.assertIn("game-procurement-group", checklist)
        self.assertIn('role="group"', checklist)
        self.assertIn("${esc(group.label", checklist)
        self.assertIn("${esc(item.field", checklist)
        self.assertIn("${esc(item.label", checklist)
        self.assertIn("${esc(item.guidance", checklist)
        self.assertIn("${esc(item.message", checklist)
        self.assertIn('role="progressbar"', checklist)
        self.assertIn('aria-valuemax="${esc(procurementProgressTotal)}"', checklist)
        self.assertIn(
            'procurementProgressIndeterminate ? "" : '
            '`aria-valuenow="${esc(procurementProgressCompleted)}"`',
            checklist,
        )
        self.assertIn("연락 허가와 별도", checklist)
        self.assertIn("추가 검증을 먼저 해결", checklist)
        self.assertIn("game-procurement-item", checklist)
        self.assertIn("data-procurement-worksheet", checklist)
        self.assertIn(
            'procurementWorksheetAvailable ? "" : "disabled"',
            checklist,
        )
        self.assertIn(
            'procurementWorksheet.reason === "complete"',
            checklist,
        )
        self.assertIn(
            'procurementWorksheet.reason === "indeterminate"',
            checklist,
        )
        self.assertIn('role="status"', checklist)
        self.assertIn('aria-live="polite"', checklist)
        self.assertIn('role="listitem"', checklist)
        self.assertIn(
            'class="game-procurement-empty" role="listitem"',
            checklist,
        )
        self.assertIn("data-game-artifact-path", checklist)
        self.assertNotIn("data-command", checklist)
        self.assertIn(".game-procurement-checklist", self.style)
        self.assertIn(".game-procurement-progress", self.style)
        self.assertIn(".game-procurement-actions", self.style)
        self.assertIn(".game-procurement-copy-status", self.style)

    def test_procurement_progress_counts_are_finite_and_bounded(self) -> None:
        start = self.app.index("function boundedCount")
        end = self.app.index(
            "activeStudioView =",
            start,
        )
        helper = self.app[start:end]

        self.assertIn("Number.isFinite(numeric)", helper)
        self.assertIn("Number.isFinite(numericMaximum)", helper)
        self.assertIn("Math.max(0, Math.floor(numericMaximum))", helper)
        self.assertIn("numeric <= 0", helper)
        self.assertIn("Math.min(Math.floor(numeric), safeMaximum)", helper)
        self.assertIn("boundedCount(group.total)", self.app)
        self.assertIn("boundedCount(group.completed, total)", self.app)
        self.assertIn("unresolved: total - completed", self.app)

    def test_procurement_worksheet_copy_is_local_and_read_only(self) -> None:
        start = self.app.index("async function copyProcurementWorksheet")
        end = self.app.index("function bind()", start)
        helper = self.app[start:end]

        self.assertIn(
            "state?.gameProduction?.procurement?.decisionWorksheet",
            helper,
        )
        self.assertIn("navigator.clipboard.writeText(text)", helper)
        self.assertIn("if (!worksheet.available || !text)", helper)
        self.assertNotIn("runCommand(", helper)
        self.assertNotIn("fetch(", helper)
        self.assertNotIn("procurement.errors", helper)
        self.assertNotIn("item.message", helper)
        self.assertIn(
            'event.target.closest(\n      "[data-procurement-worksheet]"',
            self.app,
        )


if __name__ == "__main__":
    unittest.main()
