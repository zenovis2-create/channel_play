# Khufu V11 Final Review — Concise Decision Pack

Role: Perform final correctness, regression, evidence, and Git-scope review. Do not implement.
Return blocking findings first with the cited contract/evidence, then end with exactly
`VERDICT: ship` or `VERDICT: revise`.

## Accepted Plan And Scope

Unity 6 (`6000.0.76f1`) V11 opens the V10 Great Step and adds the royal entry, antechamber,
King's Chamber, sarcophagus, shaft boundaries, and a non-traversable stacked-chamber display.
V10 baseline is `42a63801ea4699c170dbe39838d63d6d93a506ec`. Queen, descending/Subterranean,
scan anomalies, global lighting, VFX, and audio are excluded.

Prior Opus blockers were addressed:

- Great Step capture now shows V10 and V11 from the actual route stop.
- Integration capture keeps V4 cutaway, V10, and V11; no fake poche mass was added.
- Added exact staging allowlist, SHA-bound inventory, release validator, and tests.
- Added V4/V5/V8/V9/V10 regression runner.
- Added real built-player CharacterController round trip and blocker-enabled control.
- Capture manifest hashes the exporter; status records renderer headroom `0`.
- Idempotence was rerun after captures; test plan records all five negative controls.

## Changed Contracts

- `ChannelPlayKhufuV11RoyalCircuitBuilder.cs`: generated meshes, structural pairs, colliders,
  anchors, V10 Great Step replacement bindings, and rollback.
- `ChannelPlayKhufuV11RoyalCircuitValidator.cs`: exact ownership/geometry, frozen inputs,
  clearance/enclosure/budgets, idempotence, five mutations, rollback.
- `KhufuV11TraversalProofProbe.cs`: real Windows-player controller movement and CSV.
- `ChannelPlayKhufuV11LegacyRegression.cs`: original legacy validation bodies with later roots
  detached from frozen whole-map totals.
- `ChannelPlayKhufuV11WindowsBuild.cs`: hashes scene, built artifacts, all V11 sources, and restored
  project settings.
- `tools/validate_khufu_v11_release.py`: hash/evidence/Fable/staged/post-commit fail-closed gates.

## Critical Fail-Closed Logic

V10's deliberate Great Step successor change is accepted only when the raw original-validator
failure set has the exact expected count and bidirectional prefix match:

```csharp
var exact = raw.Failures.Count == expected.Length &&
    expected.All(e => raw.Failures.Any(f => f.StartsWith(e, StringComparison.Ordinal))) &&
    raw.Failures.All(f => expected.Any(e => f.StartsWith(e, StringComparison.Ordinal)));
return exact
    ? new LegacyResult("V10", true, raw.Signature + " / classified deltas=" +
        raw.Failures.Count, Array.Empty<string>(), raw.Failures)
    : raw;
```

Built-player pass predicates:

```csharp
normalPassed = !boundaryControl && !blocked && reachedAnchors == route.Count &&
    finalError <= 0.40f && maximumError <= 0.40f &&
    groundedFraction >= 0.90f && anchorsValid &&
    v11Colliders == 33 && v11Renderers == 5;
boundaryPassed = boundaryControl && blocked &&
    blockedHit == ExpectedBoundaryCollider &&
    (blockedHorizontalFlags & CollisionFlags.Sides) != 0 &&
    reachedAnchors < route.Count && maximumError > 0.40f &&
    anchorsValid && v11Colliders == 33 && v11Renderers == 5;
```

If Unity's same-frame callback omits the name, the probe promotes only the exact blocker after an
actual-controller capsule overlap/cast and only when the same `Move` returned `Sides`.

Staging rejects any staged path outside the allowlist, requires all dirty allowlisted paths, rejects
unlisted V11 source/doc/work paths, rejects staged-plus-unstaged deltas, and SHA-checks each staged
blob against `staged-inventory.json`. Final Fable parsing rejects `FABLE_HARNESS_ERROR`, requires
exactly one verdict line, and requires it to be the final nonblank line.

## Verification

- Static V11: `5 renderers / 2016 vertices / 1008 triangles / 33 colliders`.
- Full map: `829 / 65918 / 47984 / 567`; renderer budget exactly `5/5`.
- Clearance `78` samples, `0` blockers; enclosure `13` rays, `0` misses.
- Scene SHA256 `dbc0c5e3e4afc10397ed3b95bdb57118993a1ba3631b1952c585eb654eb1297b`.
- Static signature `9994b06134cf20f3225df94880f7f652e1de66ca00bb24770ad3274b8d2f0ed9`.
- Idempotence stable; five negative controls rejected and rollback passed.
- Six unique `1600x1000` captures, exporter-bound and manually reviewed.
- Windows build: exit 0, zero errors, project settings restored.
- Normal player: `15/15`, 15.771m, max/final error 0.348m, grounded `84/86` (`0.977`).
- Boundary control: stopped `1/15` at exact named blocker; actual-controller overlap;
  `Sides|Above|Below`.
- Actual controller: radius 0.450, height 2.000, stepOffset 0.300, skinWidth 0.050.
- Legacy: V4/V5/V8/V9 pass; V10 raw result contains exactly 13 classified Great Step deltas.
- Focused Python: `18 passed`.
- Current 92-path staged index: release gate passed, zero unexpected staged paths.
- Exact staged-index clean Unity import: exit 0, same scene hash and static signature.

## Residual Risks

1. No renderer headroom remains.
2. V10 cannot pass its old exact mesh contract because V11 intentionally opens that boundary;
   only the exact 13-delta set is accepted.
3. Integration is a controlled evidence cutaway; normal views plus enclosure rays are leak checks.
4. Raw iterative logs and `Builds/` are intentionally not release artifacts.
5. The shared worktree has unrelated changes, but the release inventory is allowlist-bound.

Decision needed: Are any blocking correctness, regression, evidence-binding, or staging risks still
present? Is this release safe to commit?
