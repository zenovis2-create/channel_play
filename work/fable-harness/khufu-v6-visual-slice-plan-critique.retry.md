# Khufu V6 Visual Slice - Focused Fable Decision

You are Claude Fable 5 reviewing a Unity technical-art plan. Do not implement or call tools.
Return exactly these sections with concise content:

VERDICT: overlay | direct | material-only | block
BLOCKERS:
- ...
MINIMUM_TESTS:
- ...
CORRECTED_PLAN:
1. ...

Decision needed:
Choose the smallest safe implementation for a production-readability slice over an accepted Unity
map. Should Codex use a separate overlay builder, edit the accepted V5 builder directly, or use
material reassignment only?

What would change implementation:
The answer selects the files and rollback boundary before any production code is edited.

Facts:
- Unity 6000.0.76f1, Built-in Render Pipeline, Standard shader, no SRP package/settings change.
- Accepted V5 geometry/gameplay must remain. V5 rebuild deletes/recreates its own root.
- Current final performance is 781 renderers, 23,710 vertices, 16,888 triangles; hard caps are
  820 / 25,000 / 18,000. Frame p95 is 8.337 ms against 9.0 ms.
- Visual gap is concentrated in same-camera dense-core and Temple Hub captures.
- The worktree is heavily dirty; Packages, ProjectSettings, V4/V5 source, route markers, collision,
  keys, terminal, exit, operator bounds, and truth boundary are frozen.
- Archaeology permits the complex relationship but not a factual reconstruction of lost temple
  appearance. V6 is a fictionalized production-readability slice, not final art.

Proposed plan:
1. Add a separate V6 builder that calls V5 rebuild, generates deterministic 512px albedo/normal
   textures and Standard materials, and reassigns selected existing V4 casing/core and V5 Temple
   Hub surfaces.
2. Add at most 12 builder-owned, non-colliding decorative renderers under a separate V6 root;
   hard caps: 800 added vertices, 600 added triangles, no new lights or shadows.
3. Add V6 fail-closed validation for material roles, normal-map import settings, no colliders,
   object budgets, and same-camera capture integrity plus meaningful pixel delta from V5.
4. Rerun V5 static Gate 4, PlayMode CharacterController probe, UI captures, Windows Player profile,
   compile, and Python validators before any completion claim.

False-done conditions:
- Camera/exposure-only improvement; changed gameplay/collision; non-rerunnable hand dressing;
  stale V5 evidence; performance regression; or full-map/final-art overclaim.

Ask:
Name only blockers that would change this approach. Prefer the separate overlay unless evidence
requires a smaller option.
