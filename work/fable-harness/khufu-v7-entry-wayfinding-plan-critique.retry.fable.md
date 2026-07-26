Both prior blockers are closed: the exact-name pylon match eliminates over-broad cutaway triggering, and the explicit execution-order chain (100/200/300) plus `ForceRefresh` + end-of-frame capture makes the camera/cutaway evidence same-frame and unambiguous. Scope containment is sound — frozen V5/V6 hashes, a separate V7 root with tight renderer/vertex/collider budgets, and a defined fallback (drop overlay, keep camera hardening) is the smallest safe shape for this change.

Remaining non-blocking cautions, stated as findings rather than blockers:

1. The two-second settle threshold before the probe samples is a heuristic; if the first D3D11 frames stall on shader compilation, the probe could sample a not-yet-converged cutaway state. The blocking gates (`ActiveCutawayCount >= 1` and `DiagnosticVisibleOccluderCount == 0` checked together, plus the blocked-pylon mutation failure test) already catch a false pass, so this does not block — but if the entry proof flakes, extend the settle window before touching anything else.

2. The plan asserts the V7 validator does not falsely inherit the historical V6 validator's pass. Ensure the aggregate gate actually re-executes the V7 checks against the freshly rebuilt scene rather than reading a cached receipt; the staged-index verification step should confirm the receipt hash matches the current scene hash. This is already implied by "bound to scene/player hashes," so it is a confirmation, not a gap.

Neither rises to a concrete blocker. The mutation-failure tests (off-route guide mutation, blocked-pylon mutation) give the negative controls that were missing before, and making pixel deltas advisory while runtime occluder counts plus screenshot inspection remain blocking is the right evidence hierarchy.

PLAN_VERDICT: accept
