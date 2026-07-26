# Khufu V12 Queen Circuit — Adopted Plan

Opus recommendation: **adopt with changes**.

## Finding Resolution

- **B1 — adopted.** Component-count metrics include disabled objects. V12 will add exactly five
  renderers, so the map renderer contract is exactly `834`, not `<=829`. V12 structural collision
  is capped before implementation and the exact final map collider total must be frozen after the
  read-only audit.
- **B2 — adopted.** The committed-context V11 signature must change because it hashes V10 mesh
  binding paths. V12 records both the new committed-context signature and the restored-V11-context
  signature; only the latter must equal V11's committed
  `9994b06134cf20f3225df94880f7f652e1de66ca00bb24770ad3274b8d2f0ed9`.
- **B3 — adopted.** V12 adds an original V11-validator gate under restored V11 bindings and later
  root detachment. V10 deltas are observed first and then frozen as an exact complete set/count;
  no prefix-only numeric family is accepted.
- **B4 — adopted.** `V4_Glow_Queens` and the route-marker renderer are already V10-owned disabled
  transitions. V12 only asserts their disabled state and preserves the marker transform.
- **B5 — adopted.** The boundary contract starts at least 1.5 m outside the gate, uses steps no
  larger than 0.1 m, requires an empty pre-Move overlap, same-frame `Sides`, and the exact
  `OnControllerColliderHit` name. Control mode rebinds the V11 granite (visible gate) and enables
  the exact proxy; the normal run asserts the gate is never reported.
- **B6 — adopted.** V12 accepts only V11-open or V12-open inputs. It freezes the V11 open assets and
  metadata by SHA256. V12 limestone must be geometry-identical to V11 limestone; V12 granite must
  equal V11 granite minus exactly `Queen_Ownership_Gate`, with missing- and extra-omission
  mutations rejected.

## Additional Frozen Rules

- V10 threshold posts/lintel remain visible and collidable; the existing opening is not widened.
- V12 builds a real enclosed chamber including an entrance wall split/lintel and doorway exception.
- `V4_Light_Queens` remains active and is declared as an inherited capture dependency.
- V4 components are disabled individually; `SetActive(false)` is forbidden and mutation-tested.
- Narrow-mouth object names avoid the V5-forbidden `Queens_Shaft` token.
- Re-running V11 can restore a stale pre-V12 transition; V12 rules require an immediate V12 rebuild
  and validation after any V11 rebuild.
- Rollback enumerates both V10 mesh bindings, Queen proxy, Great Step proxy, all V4 Queen component
  states, and scene bytes.
- Shaft non-traversability is collider/probe evidence, not a screenshot-only claim.

## Execution Order

1. Add the V12 contract documents, read-only Unity audit, Python prewrite validator, and mutation
   tests. Run them before any scene write.
2. Freeze the observed V4 transition count, V10/V11 binding hashes, exact predecessor metrics, and
   expected V10 legacy deltas.
3. Implement the V12 route contract, generated meshes/materials, reversible builder, metadata, and
   exact validator.
4. Prove idempotence, rollback, negative controls, restored-context V11 validation, and exact legacy
   deltas.
5. Export six fresh captures and run manual semantic/closure review.
6. Build and run the Windows normal round trip and genuine walk-into-gate control.
7. Run dependency-closed clean-index import, exact release validator, Opus final review, resolution,
   staged-index convergence, scoped commit, and post-commit validation.

No Unity scene write is authorized until step 1 passes.
