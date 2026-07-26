# Khufu V5 Gate 7 Fable Condition Closure

- Verdict: **passed for pre-commit remediation**
- Date: `2026-07-11`
- Implementation commit: `81c28f84d61d875a54f39d3fc74b202319103e24`
- Fable review SHA256: `40071ceccf26da41a5dea1e88876a084704a50fd08bdfcc00569a3be39a6314f`
- Fable decision: final line is `FABLE_VERDICT: ship`

## Required Condition 1: Build Input Binding

Status: **closed**.

- Accepted decision: `KV5-D-013`.
- Build manifest SHA256:
  `b023b46f3fd27a9632f6cab8b9adb9028ddf06971ba95db678fad2e5efa6cc09`.
- Bound inputs: scene, PlayerSettings, EditorBuildSettings, GraphicsSettings, QualitySettings,
  ProjectVersion, package manifest/lock, Bee input snapshot, and Bee build report.
- Profile instrumentation: exact one-occurrence `enableFrameTimingStats: 0` to `1` override;
  derived build-time ProjectSettings SHA256
  `95a70db75f3c5bacde2dd6f66d50b54accb8fa28fadf88935af79df30831afd7`.
- User-owned project/package changes remain unstaged. Their bytes are checked live, so drift fails
  without transferring Git ownership.
- Fail-closed tests: missing binding manifest and changed bound input both fail.

Evidence: [`build-input-binding.md`](build-input-binding.md) and
[`build-input-binding.json`](build-input-binding.json).

## Required Condition 2: KV5-D-012 Assertion Map

Status: **closed**.

`KV5-D-012` now maps every legacy V2 assertion to one of:

- a named V5 replacement assertion and receipt;
- a stronger V5 runtime/controller assertion; or
- explicit `N/A` with a V2 sensor/action-transport rationale.

The map covers scene open, root identity, route markers, fallback generation, command actions,
segmentation/semantic labels, agent spawn, movement/trajectory, observations, interactions,
unsupported-action rejection, and receipt generation. The retained V2 failure remains failed.

## Non-Blocking Risk Reductions

- `KV5-D-011` pins the known build-warning baseline at `185` upstream Sentis D3D11 warnings; an
  increase or non-Sentis warning requires investigation.
- `KV5-RSK-009` records that trigger-collider proxies do not test human chokepoint contention.
  Release language remains limited to the simulated eight-state roster.

## Verification

Focused command:

```powershell
python -m unittest tools.tests.test_validate_khufu_v5_performance tools.tests.test_validate_khufu_v5_harness -v
```

Result: `18/18 passed`.

Working-tree harness after remediation:

```text
HARNESS_VERDICT: passed
requirements=14 tests=16 evidence=19
artifact_sha256=c26e400a3e55f9ef22cb00ea73dcc4072c431f743ab0a05d168c7ec684635c12
```

## Deferred Ship Sequence

The following are not claimed by this artifact and remain Gate 7 work: fresh README-only
cold-reader, scoped evidence commit, final receipt, and `--require-committed`. Failure of any step
invalidates final completion even though Fable's review says ship.

GATE7_REMEDIATION_VERDICT: passed
