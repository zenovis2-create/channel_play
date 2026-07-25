# Khufu V11 Royal Circuit — Final Release Review Pack

## Review Request

Act as the final independent reviewer for a Unity 6 archaeological-gameplay slice. Review the
implemented V11 release as it exists in the repository. Prioritize:

1. code and evidence correctness (Agency code-reviewer perspective);
2. exact staging, allowlist, and commit isolation (Agency git-workflow-master perspective);
3. whether all blockers from the prior Opus plan critique were actually closed.

Do not infer success from prose alone. Treat receipt tokens as claims that must be supported by the
described code, hashes, and negative controls. Identify any release-blocking finding with a concrete
file and reason. End with exactly one final line: `VERDICT: ship` or `VERDICT: revise`.

## Scope And Baseline

- Repository: `channel play`
- Unity: `6000.0.76f1`
- Baseline commit: `42a63801ea4699c170dbe39838d63d6d93a506ec`
- Scene: `Assets/_Project/Scenes/School_MVP.unity`
- V11 root: `Runtime_Khufu_V11_Royal_Circuit`
- Ownership: Great Step transition, royal entry, antechamber, King's Chamber, sarcophagus,
  shaft-mouth boundaries, and a non-traversable stacked-chamber display.
- Explicitly deferred: Queen branch, descending/Subterranean work, scan anomalies, global lighting,
  VFX, and audio.

The shared worktree contains unrelated pre-existing changes. The release gate stages only the exact
V11 allowlist and rejects staged paths outside it.

## Prior Opus Plan Findings And Resolution

| Finding | Resolution |
| --- | --- |
| Great Step capture was non-probative | Reframed from the actual V10 stop at player-eye height toward the V11 antechamber; `Transition` profile shows both roots. |
| Integration view appeared disconnected | Integration now keeps V4 cutaway plus V10 and V11; target/FOV widened. No fake section-poche mass was added. |
| Inventory was prose-only | Added fail-closed Python release validator, exact allowlist, staged byte inventory, post-commit gate, and tests. |
| Legacy regression absent | Added V4/V5/V8/V9/V10 runner. Later roots are detached in memory for frozen total-count validators. V10 accepts exactly 13 named Great Step transition deltas and no others. |
| Static clearance did not prove gameplay | Added a Windows player probe using the actual `DiagnosticPlayer` CharacterController. |
| No blocker-enabled runtime control | The same player probe enables the exact old blocker and requires the named collider plus `CollisionFlags.Sides`. |
| Image checks were integrity-only | Manually reviewed all six captures and recorded semantic checks. |
| Capture manifest omitted exporter hash | Manifest now hashes scene, builder, pipeline, validator, and exporter. |
| Renderer headroom was not stated | Status records the exact `5/5` ceiling and zero headroom. |
| Idempotence predated capture | Reran idempotence after the final capture export. |
| Test plan listed four controls | Test plan and receipt now describe all five negative controls. |

## Key Implementation

- `ChannelPlayKhufuV11RoyalCircuitBuilder.cs`: owns the V11 transition, generated mesh bindings,
  structural pairs, collider proxies, metadata anchors, and rollback behavior.
- `ChannelPlayKhufuV11RoyalCircuitValidator.cs`: checks exact geometry/ownership, frozen inputs,
  clearance, enclosure, budgets, idempotence, five mutations, and rollback.
- `ChannelPlayKhufuV11TraversalProofProbe.cs`: drives the built player across a 15-anchor round
  trip using the real controller and emits per-step CSV. The negative control enables
  `V10_PROXY_Great_Step_Boundary_Great_Step_Diegetic_Boundary`, confirms actual-controller capsule
  contact, and requires `CollisionFlags.Sides`.
- `ChannelPlayKhufuV11LegacyRegression.cs`: invokes original private V4/V8/V9/V10 validation logic,
  excludes only later roots from frozen whole-map totals, and fail-closes the exact V10 transition
  delta set.
- `ChannelPlayKhufuV11WindowsBuild.cs`: produces a Development Windows player and hashes the scene,
  player, level, assembly, all V11 runtime/editor sources, and restored project settings.
- `tools/validate_khufu_v11_release.py`: binds capture/build/player evidence to current hashes,
  validates PNGs and tokens, enforces final Fable `ship`, and checks exact staged/post-commit sets.

## Evidence Summary

- Static: `renderers=5_vertices=2016_triangles=1008_colliders=33`
- Full map: `renderers=829_vertices=65918_triangles=47984_colliders=567`
- Clearance: `78` samples, `0` blockers
- Enclosure: `13` rays, `0` misses
- Static signature: `9994b06134cf20f3225df94880f7f652e1de66ca00bb24770ad3274b8d2f0ed9`
- Scene SHA256: `dbc0c5e3e4afc10397ed3b95bdb57118993a1ba3631b1952c585eb654eb1297b`
- Idempotence: scene/generated/frozen V10 signatures stable
- Negative controls: five rejected; transition failure rolled back
- Captures: six unique 1600x1000 PNGs, exporter-bound and manually reviewed
- Windows build: exit 0, zero errors, settings hash restored
- Player normal: 15/15 anchors, 15.771m traversed, max/final error 0.348m, grounded 84/86
  (`0.977`), five V11 renderers and 33 enabled BoxColliders
- Player control: stopped at 1/15, named blocker confirmed by actual controller capsule overlap,
  flags `Sides|Above|Below`
- Actual controller: radius `0.450`, height `2.000`, stepOffset `0.300`, skinWidth `0.050`
- Legacy: V4/V5/V8/V9 pass; V10 has only 13 exact classified V11 transition deltas
- Python: `18 passed`
- Clean staged-index Unity import: exit 0, static validation passed, same scene hash
- Pre-review release validator: passed
- Exact staged-byte validator: passed before review with `89` paths; the refreshed review inventory
  contains `92` staged paths and zero unexpected paths

## Relevant Receipts

- `runs/khufu-v11-royal-circuit/validation.md`
- `runs/khufu-v11-royal-circuit/idempotence.md`
- `runs/khufu-v11-royal-circuit/negative-controls.md`
- `runs/khufu-v11-royal-circuit/captures/manifest.md`
- `runs/khufu-v11-royal-circuit/manual-qa.md`
- `runs/khufu-v11-royal-circuit/legacy-regression.md`
- `runs/khufu-v11-royal-circuit/windows-build.md`
- `runs/khufu-v11-royal-circuit/player-proof/v11-final-round-trip.md`
- `runs/khufu-v11-royal-circuit/player-proof/v11-final-boundary-control.md`
- `runs/khufu-v11-royal-circuit/clean-package-import.md`
- `runs/khufu-v11-royal-circuit/staged-index-validation.md`
- `docs/khufu-v11-royal-circuit/staging-allowlist.txt`

## Fail-Closed Code Excerpts

The V10 successor classification requires the raw failure count, every expected prefix, and every
raw failure to match the expected set:

```csharp
var exact = raw.Failures.Count == expected.Length &&
            expected.All(item => raw.Failures.Any(failure =>
                failure.StartsWith(item, StringComparison.Ordinal))) &&
            raw.Failures.All(failure => expected.Any(item =>
                failure.StartsWith(item, StringComparison.Ordinal)));
return exact
    ? new LegacyResult("V10", true,
        raw.Signature + " / classified V11 Great Step transition deltas=" + raw.Failures.Count,
        Array.Empty<string>(), raw.Failures)
    : raw;
```

The built-player proof distinguishes the open route from the blocker-enabled control and requires
the exact named collider plus `Sides`:

```csharp
var normalPassed = !boundaryControl && !blocked && reachedAnchors == route.Count &&
                   finalError <= MaximumStepError && maximumError <= MaximumStepError &&
                   traversedDistance >= expectedDistance - 1f && groundedFraction >= 0.90f &&
                   anchorsValid && v11Colliders == 33 && v11Renderers == 5;
var boundaryPassed = boundaryControl && blocked && blockedHit == ExpectedBoundaryCollider &&
                     (blockedHorizontalFlags & CollisionFlags.Sides) != 0 &&
                     reachedAnchors < route.Count && maximumError > MaximumStepError &&
                     anchorsValid && v11Colliders == 33 && v11Renderers == 5;
```

When `OnControllerColliderHit` does not identify the collider in the same frame, the proof uses the
actual controller dimensions for an overlap/cast and only promotes the known collider while the
same `Move` returned `Sides`:

```csharp
if ((horizontalFlags & CollisionFlags.Sides) != 0 &&
    string.IsNullOrEmpty(blockingHitName) &&
    !string.IsNullOrEmpty(namedBoundaryContact))
{
    blockingHitName = ExpectedBoundaryCollider;
    boundaryContactProof = namedBoundaryContact;
}
```

The staging gate rejects staged paths outside the allowlist, requires every dirty allowlisted
release path to be staged, rejects unlisted V11 source/doc/work paths, and compares every staged
blob with the recorded SHA-256:

```python
for path in sorted(staged - permitted):
    result.errors.append(f"unexpected staged path: {path}")
for path in sorted(dirty.intersection(permitted) - staged):
    result.errors.append(f"allowlisted release path is not staged: {path}")
for path in sorted(dirty - allowlist):
    if path.startswith(STRICT_PREFIXES):
        result.errors.append(f"unlisted V11 scope path: {path}")
if inventory_paths != staged - helpers:
    result.errors.append("staged inventory path set differs from the exact release inventory")
for record in records:
    check_index_record(root, record, "staged inventory", result)
```

## Known Constraints To Judge

1. V11 uses all five allowed renderers. Any new renderer is a release blocker.
2. V10's old exact validator cannot pass unchanged because V11 deliberately replaces the combined
   Great Step mesh bindings and blocker. The compatibility runner accepts only the observed 13
   named transition deltas and still runs the original validator body.
3. The integration screenshot is an evidence cutaway. Normal interior views and enclosure rays are
   the leak checks.
4. Raw iterative Unity logs and `Builds/` are not release artifacts and are intentionally outside
   the staging allowlist.

## Reviewer Checklist

- Look for false-positive receipt logic, especially traversal blocking identity and legacy delta
  classification.
- Check that hash binding covers every code input capable of changing the player or captures.
- Check that the staging validator cannot silently include unrelated dirty paths.
- Check whether the manual visual conclusions are consistent with the documented camera profiles.
- Check whether any plan-critique blocker remains unresolved.
- Separate non-blocking follow-up ideas from release blockers.
