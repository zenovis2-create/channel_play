# Khufu V5 V4 Regression Receipt

- Verdict: **passed**
- Date: `2026-07-11`
- Tested implementation commit: `81c28f84d61d875a54f39d3fc74b202319103e24`
- Unity: `6000.0.76f1`
- Scene: `Assets/_Project/Scenes/School_MVP.unity`
- Scene SHA256: `7606cfb305d7b0269af5db6f35544583765a56ebee2bb68844b5b239bf5e65ff`
- V4 builder SHA256: `b4ec09ed37c8ad1b7597528a3a8ced42ae7a8613436cdc31a9b1e609a6e85c3c`

## Validator

Unity menu `Channel Play/Validate Pyramid Reference Matched V4` emitted:

```text
CHANNEL_PLAY_PYRAMID_REFERENCE_V4 result=passed core_blocks=217 casing_panels=8 cut_ratio=0.026 corbels=14 relieving=5 envelope_violations=0
```

The detailed receipt also records eight route markers, three foundation sections, Queen's floor
`5.200 / 5.218 m`, and King's floor `10.500 / 10.436 m`:
[`validation-receipt.md`](../pyramid-reference-matched-v4/validation-receipt.md).

## Focused Comparison

The pre-V5 V4 receipt dated `2026-07-10` records the same contract values: 56.000 m base,
35.636 m height, 217 dense-core blocks, 14 corbel bands, five relieving chambers, eight casing
panels, and zero envelope violations. Its SHA256 is
`c7862502760c42c89e45efdf0f8a86151b492cec23688cd11eef24ae6ff1f6a3`:
[`receipt.md`](../pyramid-reference-matched-v4/receipt.md).

The baseline Git commit did not track the already-present V4 builder, so a source diff alone cannot
prove preservation. The accepted comparison is therefore the pre-V5 receipt versus the
post-implementation validator on the committed scene. Git confirms that V5 was added in commit
`81c28f84...`; no later working-tree change exists on the committed V4 builder or scene.

## Hierarchy Snapshot

Unity Editor snapshot at the tested scene:

```text
root=Runtime_Pyramid_Reference_Matched_V4
parent=TraitorEscape_Runtime_Map
direct_children=7
descendants=395
renderers=368
bounds_center=(0.000,13.743,8.000)
bounds_size=(220.000,43.786,220.000)
children=[V4_Foundation_Bedrock_Cutaway,V4_Section_Poche,V4_Smooth_Casing_With_Tapered_Cutaway,V4_Dense_Exposed_Core_Masonry,V4_Embedded_Interior_Architecture,V4_Gameplay_Route,V4_Lighting]
```

The 220 m bounds include the V4 desert horizon; pyramid dimensions are asserted separately by the
V4 validator. V5 district roots are siblings under the shared map root and do not mutate these
seven V4 ownership roots.

V4_REGRESSION_VERDICT: passed
