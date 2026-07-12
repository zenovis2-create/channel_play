# Khufu V10 Windows Player Validation

- Verdict: **passed**
- Scene SHA256: `d1778ecb2edfb7e83173a893ec82f5acb8959078ec68fc714a5f1a1320e83ad2`
- Assembly-CSharp SHA256: `2fe263fa573edd5eec9022b1238588df92a6e48f6a86991c0af7228fa46af468`
- Normal route: `16/16` anchors, expected/traversed `96.105/95.815 m`, max/final error
  `0.150/0.030 m`, three fresh semantic PNGs.
- Great Step control: attempted/advanced `2.200/0.299 m`, exact side collider
  `V10_PROXY_Great_Step_Boundary_Great_Step_Diegetic_Boundary`, ground collider
  `V10_PROXY_Grand_Gallery_Gallery_Floor_Ramp`, two fresh semantic PNGs.
- Error metric control: independent `0.750 m` offset rejected by the frozen `0.4 m` threshold.
- V10 runtime inventory: `6` renderers and `70` enabled BoxColliders in all three processes.

V10_WINDOWS_PLAYER_VALIDATION: passed
