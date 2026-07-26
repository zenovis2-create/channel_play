# Khufu V12 Queen Circuit Plan

## Player Flow

`Gallery Foot -> opened V10 threshold -> low horizontal passage -> chamber entrance -> chamber
center -> same-route return`.

The passage compresses the view and the gabled chamber provides the release. From the chamber
center, the doorway remains readable without UI.

## Ownership

- Preserve all V10 threshold posts/lintel and their colliders.
- Disable the single inherited `Gallery_Floor_Ramp` collider that crosses the Queen branch;
  preserve its renderer and restore the collider for V11-context validation.
- Disable the inherited `Historic_Service_Mouth` west-post, east-post, and lintel colliders as
  one route-crossing frame; preserve its renderer and restore all three for V11 validation.
- Replace the V10 red-granite binding with a V12 successor that removes only
  `Queen_Ownership_Gate`; preserve the V11 Great-Step omissions.
- Disable only the ten audited V4 Queen passage/chamber renderer/collider pairs.
- Preserve the V4 Queen marker, its V10-disabled renderer, its V10-disabled glow, and
  `V4_Light_Queens`.
- Add a V12 root containing visuals, structural-pair markers, collision proxies, and metadata.

## Verification

Freeze the prewrite audit, build deterministic combined meshes, validate exact transitions and
enclosure, run eight negative controls plus rollback, invoke original legacy validators under
restored contexts, export six captures, run built-player normal/control routes, and close through
review-required exact staging.

## Operational Rule

After V12 exists, any V11 rebuild must be followed by a V12 rebuild before the scene is valid.
