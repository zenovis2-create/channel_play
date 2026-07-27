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
        self.assertIn("data-procurement-worksheet-preview", checklist)
        self.assertIn("data-procurement-worksheet-download", checklist)
        self.assertIn(
            'procurementWorksheetAvailable ? "" : "disabled"',
            checklist,
        )
        self.assertGreaterEqual(
            checklist.count(
                'procurementWorksheetAvailable ? "" : "disabled"'
            ),
            3,
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
        self.assertIn(
            'aria-controls="gameProcurementWorksheetPreview"',
            checklist,
        )
        self.assertIn('aria-expanded="false"', checklist)
        self.assertIn(
            '<pre tabindex="0">${esc(procurementWorksheetText)}</pre>',
            checklist,
        )
        self.assertNotIn(
            '<pre tabindex="0">${procurementWorksheetText}</pre>',
            checklist,
        )
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
        self.assertIn(".game-procurement-worksheet-preview", self.style)
        self.assertIn(
            ".game-procurement-worksheet-preview[hidden]",
            self.style,
        )
        self.assertIn('id="gameProcurementAnswerInput"', checklist)
        self.assertIn('maxlength="16000"', checklist)
        self.assertIn("procurementAnswerPreviewAvailable", checklist)
        self.assertIn("data-procurement-answer-preview", checklist)
        self.assertIn("data-procurement-answer-clear", checklist)
        self.assertIn("data-procurement-answer-status", checklist)
        self.assertIn("data-procurement-answer-result", checklist)
        self.assertIn(
            "data-procurement-answer-apply-panel",
            checklist,
        )
        self.assertIn(
            "data-procurement-change-summary",
            checklist,
        )
        self.assertIn(
            "data-procurement-save-verification",
            checklist,
        )
        self.assertIn(
            "data-procurement-save-recovery",
            checklist,
        )
        self.assertIn('aria-label="저장 결과 복구"', checklist)
        self.assertIn("data-procurement-apply-owner-check", checklist)
        self.assertIn("data-procurement-apply-contact-check", checklist)
        self.assertIn(
            "data-procurement-apply-confirmation",
            checklist,
        )
        self.assertIn("data-procurement-answer-apply", checklist)
        self.assertIn("PROCUREMENT_APPLY_CONFIRMATION", checklist)
        self.assertIn("승인값 저장", checklist)
        self.assertIn("PASS 영수증 전에는", checklist)
        self.assertIn('role="region"', checklist)
        self.assertIn(
            'aria-label="소유자 답변 사전검증 결과"',
            checklist,
        )
        self.assertIn(".game-procurement-answer-preview", self.style)
        self.assertIn(".game-procurement-answer-result", self.style)
        self.assertIn(".game-procurement-answer-apply", self.style)
        self.assertIn(".game-procurement-change-summary", self.style)
        self.assertIn(".game-procurement-save-verification", self.style)
        self.assertIn(".game-procurement-save-recovery", self.style)
        self.assertIn(
            ".game-procurement-answer-apply[hidden]",
            self.style,
        )
        self.assertIn(
            ".game-procurement-save-recovery[hidden]",
            self.style,
        )

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
        self.assertIn(
            "Markdown 다운로드를 사용하세요",
            helper,
        )

    def test_procurement_worksheet_preview_is_escaped_and_local(self) -> None:
        start = self.app.index("function toggleProcurementWorksheetPreview")
        end = self.app.index("function procurementWorksheetFilename", start)
        helper = self.app[start:end]

        self.assertIn(
            "state?.gameProduction?.procurement?.decisionWorksheet",
            helper,
        )
        self.assertIn("if (!worksheet.available || !worksheet.text", helper)
        self.assertIn("preview.hidden = !willOpen", helper)
        self.assertIn('button.setAttribute("aria-expanded"', helper)
        self.assertNotIn("runCommand(", helper)
        self.assertNotIn("fetch(", helper)

    def test_procurement_worksheet_download_revokes_local_url(self) -> None:
        start = self.app.index("function procurementWorksheetFilename")
        end = self.app.index("function bind()", start)
        helper = self.app[start:end]

        self.assertIn('.replace(/[^a-z0-9_-]+/g, "-")', helper)
        self.assertIn(".slice(0, 64)", helper)
        self.assertIn("new Blob([text]", helper)
        self.assertIn('"text/markdown;charset=utf-8"', helper)
        self.assertIn("URL.createObjectURL(blob)", helper)
        self.assertIn("document.createElement(\"a\")", helper)
        self.assertIn("link.download = procurementWorksheetFilename", helper)
        self.assertIn("link.remove()", helper)
        self.assertIn(
            "window.setTimeout(() => URL.revokeObjectURL(objectUrl), 0)",
            helper,
        )
        self.assertNotIn("runCommand(", helper)
        self.assertNotIn("fetch(", helper)
        self.assertIn(
            'event.target.closest(\n      '
            '"[data-procurement-worksheet-download]"',
            self.app,
        )

    def test_procurement_answer_preview_is_memory_only_and_escaped(
        self,
    ) -> None:
        start = self.app.index("function renderProcurementAnswerPreview")
        end = self.app.index(
            "function procurementSaveRecoveryContainer",
            start,
        )
        request_start = self.app.index(
            "async function previewProcurementAnswers",
            end,
        )
        request_end = self.app.index(
            "function clearProcurementAnswerPreview",
            request_start,
        )
        helper = (
            self.app[start:end]
            + self.app[request_start:request_end]
        )

        self.assertIn("resultNode.replaceChildren()", helper)
        self.assertIn('document.createElement("strong")', helper)
        self.assertIn('document.createElement("li")', helper)
        self.assertIn("preview.changedFields", helper)
        self.assertIn("preview.unchangedFields", helper)
        self.assertIn("preview.protectedStatePreserved", helper)
        self.assertIn("item.textContent = field", helper)
        self.assertIn("item.textContent = String(error", helper)
        self.assertIn('"연락 허가 아님"', helper)
        self.assertIn('"영수증 생성 안 함"', helper)
        self.assertIn("JSON.parse(input.value)", helper)
        self.assertIn("Array.isArray(answers)", helper)
        self.assertIn('api("/api/procurement/preview"', helper)
        self.assertIn("JSON.stringify({", helper)
        self.assertNotIn("runCommand(", helper)
        self.assertNotIn("loadState(", helper)
        self.assertNotIn("localStorage", helper)
        self.assertNotIn("sessionStorage", helper)
        self.assertNotIn(".innerHTML", helper)
        self.assertIn(
            'event.target.closest(\n      '
            '"[data-procurement-answer-preview]"',
            self.app,
        )

    def test_procurement_answer_apply_requires_grant_and_confirmation(
        self,
    ) -> None:
        start = self.app.index("function procurementApplyControls")
        end = self.app.index("function bind", start)
        helper = self.app[start:end]

        self.assertIn("let procurementApplyGrant = null", self.app)
        self.assertIn("let procurementSaveRecovery = null", self.app)
        self.assertIn("let procurementSaveRecoveryTimer = null", self.app)
        self.assertIn(
            'const PROCUREMENT_APPLY_CONFIRMATION = "소유자 승인값 저장"',
            self.app,
        )
        self.assertIn("preview.applyGrant", helper)
        self.assertIn("preview.applyGrantExpiresInSeconds", helper)
        self.assertIn(
            "preview.applyResultRecoveryExpiresInSeconds",
            helper,
        )
        self.assertIn("changedFields: [...summary.changedFields]", helper)
        self.assertIn("summary.changeCount > 0", helper)
        self.assertIn("summary.changedFields.length", helper)
        self.assertIn("summary.unchangedFields.length", helper)
        self.assertIn("controls.changeSummary", helper)
        self.assertIn("window.setTimeout(() =>", helper)
        self.assertIn("window.clearTimeout", helper)
        self.assertIn("Date.now() < procurementApplyGrant.expiresAt", helper)
        self.assertIn("manifestSha256.slice(0, 12)", helper)
        self.assertIn("updateProcurementApplyButton()", helper)
        self.assertIn(
            "controls.confirmation?.value "
            "=== PROCUREMENT_APPLY_CONFIRMATION",
            helper,
        )
        self.assertIn('api("/api/procurement/apply"', helper)
        self.assertEqual(
            helper.count('api("/api/procurement/apply"'),
            1,
        )
        self.assertIn('api("/api/procurement/apply-status"', helper)
        self.assertIn("createProcurementApplyAttemptId()", helper)
        self.assertIn("new Uint8Array(16)", helper)
        self.assertIn("crypto.getRandomValues(bytes)", helper)
        self.assertIn('padStart(2, "0")', helper)
        self.assertIn("applyAttemptId,", helper)
        self.assertIn("grant.recoveryExpiresInSeconds * 1000", helper)
        self.assertIn("result.found !== true", helper)
        self.assertIn("result.pending !== false", helper)
        self.assertIn(
            "recoverProcurementSaveVerification(",
            helper,
        )
        self.assertIn("showProcurementSaveRecovery(", helper)
        self.assertIn("saveRecovered = true", helper)
        self.assertIn("applyGrant: grant.grant", helper)
        self.assertIn(
            "expectedManifestSha256: grant.manifestSha256",
            helper,
        )
        self.assertIn("result.contactAuthorized !== false", helper)
        self.assertIn("result.receiptCreated !== false", helper)
        self.assertIn("result.savedVerified", helper)
        self.assertIn("result.savedChangedFields", helper)
        self.assertIn("result.savedChangeCount", helper)
        self.assertIn("result.protectedStatePreserved", helper)
        self.assertIn("grant.changedFields", helper)
        self.assertIn("item.textContent = field", helper)
        self.assertIn(
            "저장되었을 수 있으므로 재시도하지 말고",
            helper,
        )
        self.assertIn(
            "renderProcurementSaveVerification",
            helper,
        )
        self.assertIn("await loadState()", helper)
        self.assertNotIn("runCommand(", helper)
        self.assertNotIn("localStorage", helper)
        self.assertNotIn("sessionStorage", helper)
        self.assertNotIn(".innerHTML", helper)
        self.assertIn(
            'event.target.matches("#gameProcurementAnswerInput")',
            self.app,
        )
        self.assertIn(
            "invalidateProcurementApplyGrant()",
            self.app,
        )

    def test_procurement_manual_save_recovery_is_status_only_and_ephemeral(
        self,
    ) -> None:
        start = self.app.index("function clearProcurementSaveRecovery")
        end = self.app.index(
            "async function previewProcurementAnswers",
            start,
        )
        recovery_helper = self.app[start:end]
        status_start = self.app.index(
            "async function recoverProcurementSaveVerification",
        )
        status_end = self.app.index(
            "function clearProcurementSaveVerification",
            status_start,
        )
        status_helper = self.app[status_start:status_end]

        self.assertIn("assetId,", recovery_helper)
        self.assertIn("applyAttemptId,", recovery_helper)
        self.assertIn(
            "manifestSha256: grant.manifestSha256",
            recovery_helper,
        )
        self.assertIn("changeCount: grant.changeCount", recovery_helper)
        self.assertIn("changedFields: [...changedFields]", recovery_helper)
        self.assertIn("expiresAt,", recovery_helper)
        record_start = recovery_helper.index(
            "procurementSaveRecovery = {",
        )
        record_end = recovery_helper.index("};", record_start)
        retained_record = recovery_helper[record_start:record_end]
        self.assertEqual(retained_record.count("\n    "), 6)
        self.assertNotIn("answers", retained_record)
        self.assertNotIn("grant,", retained_record)
        self.assertNotIn("confirmation", retained_record)
        self.assertIn(
            "expiresAt > Date.now() + (3600 * 1000)",
            recovery_helper,
        )
        self.assertIn("window.setTimeout(", recovery_helper)
        self.assertIn("window.clearTimeout", recovery_helper)
        self.assertIn("Date.now() >= recovery.expiresAt", recovery_helper)
        self.assertIn(
            "data-procurement-save-recovery-check",
            self.app,
        )
        self.assertIn(
            "retryProcurementSaveRecovery(saveRecoveryButton)",
            self.app,
        )
        self.assertIn(
            "recoverProcurementSaveVerification(",
            recovery_helper,
        )
        self.assertIn(
            "아직 확정된 결과가 없습니다.",
            recovery_helper,
        )
        self.assertIn(
            "네트워크 오류로 결과를 확인하지 못했습니다.",
            recovery_helper,
        )
        self.assertIn(
            "저장 결과 조회 시간이 만료되었습니다.",
            recovery_helper,
        )
        self.assertIn("clearProcurementSaveRecovery()", recovery_helper)
        self.assertIn("input.value = input.defaultValue", recovery_helper)
        self.assertIn("await loadState()", recovery_helper)
        self.assertIn(
            'api("/api/procurement/apply-status"',
            status_helper,
        )
        self.assertIn("assetId,", status_helper)
        self.assertIn("applyAttemptId,", status_helper)
        self.assertNotIn("answers", status_helper)
        self.assertNotIn("applyGrant", status_helper)
        self.assertNotIn("confirmation", status_helper)
        self.assertNotIn("/api/procurement/apply\"", recovery_helper)
        self.assertNotIn("localStorage", recovery_helper)
        self.assertNotIn("sessionStorage", recovery_helper)
        self.assertNotIn(".innerHTML", recovery_helper)
        self.assertEqual(
            self.app.count('api("/api/procurement/apply"'),
            1,
        )


if __name__ == "__main__":
    unittest.main()
