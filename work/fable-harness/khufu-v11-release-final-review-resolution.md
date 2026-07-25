# Khufu V11 Final Review — Resolution Check

Role: Perform a narrow follow-up correctness and release-gate review. Do not implement.
End with exactly `VERDICT: ship` or `VERDICT: revise` as the final nonblank line.

## Goal

Decide whether the first-round findings in
`work/fable-harness/khufu-v11-release-final-review.opus.md` are resolved sufficiently to allow the
V11 release inventory to proceed to its review-required staged gate and local commit.

## Resolution

The complete classification is in
`runs/khufu-v11-royal-circuit/review-resolution.md`.

1. The failed budget output is preserved separately. The first valid `revise` review is also
   preserved unchanged. This call writes a separate follow-up output; the Python gate requires that
   file to contain exactly one final `VERDICT: ship`.
2. The resolution receipt now carries `V11_REVIEW_RESOLUTION: passed`. After this call, Codex will
   run `--require-reviews`, then refresh and converge the exact staged inventory with
   `--require-reviews --check-staged`. No commit occurs unless both pass.
3. Git porcelain `-z` rename/copy parsing now consumes the second pathname and retains both old and
   new paths. The focused suite now reports `19 passed`.
4. `STATUS.md` explicitly records zero renderer headroom for both V11 root (`5/5`) and full map
   (`829/829`).
5. `manual-qa.md` now describes the blocker control precisely: it begins overlapped and demonstrates
   depenetration plus `Sides` route falsification, not a forward walk-into-wall callback.
6. The build-case finding was checked against both implementations:
   `ChannelPlayKhufuV11WindowsBuild.OutputPath =
   "Builds/KhufuV11/ChannelPlayKhufuV11.exe"` and Python
   `BUILD_ROOT = Path("Builds/KhufuV11")`. The lowercase directory display is pre-existing Windows
   casing; a fresh case-sensitive build and verifier agree on `Builds/KhufuV11`.

No C#, Unity scene, generated asset, capture, or player artifact changed during resolution. Existing
evidence therefore remains bound: static `5/2016/1008/33`, map `829/65918/47984/567`, clearance
`78/0`, enclosure `13/0`, normal player `15/15` with `0.977` grounded fraction, boundary control
`1/15`, six unique captures, five negative controls plus rollback, legacy V4/V5/V8/V9 passes and
the exact 13 classified V10 successor deltas, clean staged-index Unity import, and scene SHA256
`dbc0c5e3e4afc10397ed3b95bdb57118993a1ba3631b1952c585eb654eb1297b`.

Residual risks are explicit: root and map renderer budgets have no headroom; V10 intentionally
cannot satisfy its closed Great Step mesh contract; the integration image is a controlled cutaway;
ignored build outputs must be regenerated before independent post-clone validation.

Decision needed: Did the resolution close the first-round blockers and accurately classify the
non-blocking findings, so the release may proceed to review-required staging and commit?
