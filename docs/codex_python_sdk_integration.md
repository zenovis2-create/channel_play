# Codex Python SDK Integration

Updated: 2026-06-03

Channel Play Studio now treats Codex as a dual-path adapter:

- Primary path when installed: `openai-codex` Python SDK via `openai_codex`
- Fallback path: existing `codex exec` CLI subprocess

The integration is isolated in `tools/studio/company/codex_sdk.py` because the SDK is still beta. If the SDK API changes, the blast radius should stay inside that wrapper.

## Install

```bash
python3 -m venv .venv/codex-sdk
.venv/codex-sdk/bin/python -m pip install openai-codex
```

Homebrew Python blocks direct global installs through PEP 668. The Studio runner automatically adds `.venv/codex-sdk/lib/python*/site-packages` to its import path and only uses the SDK when `openai_codex` is importable.

## Adapter Config

The default Codex adapter lives in `memory/company/tool_adapters.json` after `agent.adapters` or any agent run initializes it.

Important fields:

- `execution: codex_auto`
- `sdk_package: openai_codex`
- `sdk_approval_mode: auto_review`
- `sdk_sandbox: workspace_write`
- `fallback_on_sdk_error: true`

To force CLI-only execution, set:

```json
{
  "tools": {
    "codex": {
      "execution": "cli"
    }
  }
}
```

## Verification

```bash
python3 -m unittest tools.studio.company.tests.test_agent_runner
python3 tools/channelctl company adapters
```

The Studio UI adapter panel shows whether Codex is using `Python SDK`, `CLI fallback`, or `CLI`.
