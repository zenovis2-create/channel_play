# Khufu V12 Python Test Report

- Focused command: `python -m pytest tools/tests/test_validate_khufu_v12_prewrite.py tools/tests/test_validate_khufu_v12_release.py -q`
- Focused result: `29 passed`
- Full command: `python -m pytest tools/tests tools/studio -q`
- Full result: `184 passed, 13 failed, 11 subtests passed`

## Frozen Full-Suite Failure IDs

Legacy receipts that intentionally bind pre-V12 scene/build hashes:

- `tools/tests/test_validate_khufu_v5_harness.py::KhufuV5HarnessValidatorTests::test_current_harness_passes`
- `tools/tests/test_validate_khufu_v5_harness.py::KhufuV5HarnessValidatorTests::test_document_edit_invalidates_revision_hash`
- `tools/tests/test_validate_khufu_v5_harness.py::KhufuV5HarnessValidatorTests::test_validator_edit_invalidates_revision_hash`
- `tools/tests/test_validate_khufu_v6_visual_slice.py::KhufuV6VisualSliceValidatorTests::test_complete_fixture_passes`

Windows/POSIX portability or unavailable macOS-tool assumptions:

- `tools/studio/company/tests/test_agent_runner.py::AgentRunnerTests::test_adapter_health_matrix_reports_version_path_and_roles`
- `tools/studio/company/tests/test_agent_runner.py::AgentRunnerTests::test_codex_adapter_falls_back_to_cli_when_sdk_auth_fails`
- `tools/studio/company/tests/test_agent_runner.py::AgentRunnerTests::test_dry_run_writes_agent_run_without_external_process`
- `tools/studio/company/tests/test_agent_runner.py::AgentRunnerTests::test_review_dry_run_moves_to_evidence_step`
- `tools/studio/company/tests/test_company_core.py::CompanyCoreTests::test_review_checkpoint_moves_task_to_evidence`
- `tools/studio/company/tests/test_company_core.py::CompanyCoreTests::test_verify_accepts_studio_checkpoint_and_closes_task`
- `tools/studio/company/tests/test_worker_fleet.py::WorkerFleetTests::test_render_worker_fleet_includes_capabilities_and_recommended_jobs`
- `tools/studio/tests/test_workspace_server.py::WorkspaceServerTests::test_orchestrator_job_extracts_task_id_and_workflow_path`
- `tools/studio/tests/test_workspace_server.py::WorkspaceServerTests::test_run_command_creates_async_job_receipt`

No V12-focused test failed.

KHUFU_V12_PYTHON_TESTS: passed_with_frozen_unrelated_failures
