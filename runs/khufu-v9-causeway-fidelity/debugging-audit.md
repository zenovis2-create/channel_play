# Khufu V9 Debugging Runtime Audit

## Hypothesis 1: Visual and collision geometry can drift independently

- Test: mutate one structural proxy by `0.250m`, then rerun the pair validator.
- Evidence: the validator rejected `Causeway_Station_A_Beam delta=0.250`; restored output has 23/23 pair bounds at `0.000m` and inherited floor/art at `0.040m` maximum.
- Decision: rejected mutation proves the pair contract is sensitive; current state passes.

## Hypothesis 2: Causeway parapets can block existing hub branches

- Test: run V5 Gate 4 against every key route and hub proxy after replacing the approach art.
- Evidence: the first implementation blocked Sun/Crown branches; trimming the hub-side parapets to a 12m open fanout produced `415` clearance samples, `3` key routes, and `8/8` hub proxies passed.
- Decision: keep the open fanout and preserve the Gate 4 regression as required evidence.

## Hypothesis 3: A scripted traversal can report a false positive if the negative control is invisible or nonbinding

- Test: compare the same Windows player assembly in normal and deliberate proxy/graybox mutation modes.
- Evidence: normal mode binds three serialized floor anchors plus the 1.25m capsule-center offset and traverses the
  independent `88.146m` route with `0.000m` final error. Proxy mutation stops after `0.582m` with `1.078m` error.
  A separate waypoint perturbation reports `0.750m` and trips the `0.400m` threshold. Direct image inspection
  confirms the aligned graybox visibly intrudes into the route only in proxy-mutation mode.
- Decision: anchor/minimum-distance assertions, two distinct failing controls, and visible cause establish a
  falsifiable Windows proof.

## Evidence-System Checks

- The V9 visual envelope contains 32 solid colliders: 23 V9, two inherited floors, seven visible-matched extras,
  and zero orphaned. Superseded renderers may retain no solid collider except the two named inherited floors.
- Runtime route captures delete existing paths, prove freshness, decode and inspect pixels in Unity, and are decoded
  again by the aggregate validator with CRC/IEND/scanline checks.
- The build receipt and all three bindings cover all 268 files returned by `BuildReport.GetFiles()`.

## Bound State

- Scene SHA256: `0af39f99386da722f228611e0482cee46f9dfba2b57b00e6a791fc7c7fe3e346`
- Assembly-CSharp SHA256: `ef9123dac1f627f0e17e45f1f881e3fd3e61a036e2387926c5519897e547cc34`

V9_DEBUGGING_AUDIT: passed
