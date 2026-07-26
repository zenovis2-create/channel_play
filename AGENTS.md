# Repository Guidelines

## Project Structure & Module Organization

This is a Unity 6 project (`6000.0.76f1`) with a Python control plane. Project-owned Unity content lives in `Assets/_Project/`: gameplay and editor C# in `Scripts/`, scenes in `Scenes/`, reusable objects in `Prefabs/`, and art, audio, and materials in their named folders. Keep Unity tests under `Assets/_Project/Tests/EditMode` or `PlayMode`, and commit each asset's `.meta` file. `tools/channelctl` is the main CLI; supporting Python modules are in `tools/studio/`, with validator tests in `tools/tests/`. Specifications belong in `docs/`; pipeline inputs and handoffs belong in `asset_pipeline/`. Do not commit Unity-generated `Library/`, `Logs/`, `UserSettings/`, or `builds/` content.

## Build, Test, and Development Commands

- `python tools/channelctl status` - show repository and agent-company status.
- `python tools/channelctl unity check --batch` - run the headless Unity import/compile gate.
- `python tools/channelctl unity playtest` - run the MVP smoke validation.
- `python -m pytest tools/tests tools/studio` - run Python validator and control-plane tests.
- `scripts/start_docker_studio.sh` - start the Docker Studio UI and host runner; see `docs/docker_studio.md`.

Use Unity Editor `6000.0.76f1` for scene or asset work. Run focused checks first, then the full relevant gate before review.

## Coding Style & Naming Conventions

Use four spaces in C# and Python. Follow existing C# style: `ChannelPlay.*` namespaces, PascalCase types and public members, camelCase locals and serialized private fields, and braces on new lines. Python follows PEP 8: snake_case functions/modules, PascalCase classes, type hints, and `pathlib.Path` for paths. No repository-wide formatter is configured, so match adjacent code and keep imports organized.

## Testing Guidelines

Name Python tests `test_<behavior>.py` and test functions `test_<expected_result>`. Place pure rules in Unity EditMode tests and scene/player flows in PlayMode tests. Every bug fix or changed validator gate needs a regression test. No numeric coverage threshold is configured; cover changed branches and failure paths, especially fail-closed validation behavior.

## Commit & Pull Request Guidelines

Recent history uses concise Conventional Commit subjects, commonly `feat(unity): ...`, `chore(unity): ...`, and `docs: ...`. Keep commits narrowly scoped and imperative. Pull requests must summarize the change, link the task or issue, list exact verification commands, and attach screenshots or `runs/` receipts for visible Unity changes. Call out configuration or asset-pipeline impacts and avoid unrelated generated files.

## Security & Configuration

Never commit `.env` files or `memory/company/secrets/`. Keep Docker unprivileged, do not mount the Docker socket, and use the host-runner token file described in `docs/docker_studio.md`.
