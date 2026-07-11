# Khufu V7 Entry Wayfinding

Khufu V7 is a fictional game wayfinding slice layered over the accepted V5/V6 map. It does not claim
to reconstruct the Great Pyramid. The slice fixes the player-entry camera, preserves the Valley Gate
as a readable frame, and adds eight non-colliding floor guides toward the Temple Hub.

## Owned Surface

- `Runtime_Khufu_V7_Entry_Wayfinding`: eight guide renderers, no colliders or lights.
- `KhufuV7EntryCameraProfile`: V7-only follow offset and route look-ahead.
- Exact Valley Gate pylon cutaway handling with deterministic restoration.
- Rendered normal and blocked-mutation evidence at 1536x1024.

## Verification

```powershell
python tools/validate_khufu_v7_entry_wayfinding.py `
  --output runs/khufu-v7-entry-wayfinding/final-validation.md
```

The aggregate validator rechecks frozen inputs, scene-bound receipts, build hashes, entry screenshots,
the negative control, performance evidence, documentation, and the Fable final decision.
