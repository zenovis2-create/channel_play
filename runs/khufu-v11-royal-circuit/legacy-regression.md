# Khufu V11 Legacy Regression

- Verdict: **passed**
- Scope: `V4, V5, V8, V9, V10` original validation logic
- Compatibility rule: each frozen exact-map validator excludes only later-version roots in memory.
- Raw V8 full-map run: `expected failure` because the frozen V8 total excludes V9-V11; see `legacy-v8.log`.
- Raw V8 observed current map: `renderers=829_vertices=65918_triangles=47984_colliders=567`.
- V10 compatibility rule: only the 13 named Great Step open-transition mesh/collider deltas are accepted.
- Scene SHA256 before / after: `dbc0c5e3e4afc10397ed3b95bdb57118993a1ba3631b1952c585eb654eb1297b / dbc0c5e3e4afc10397ed3b95bdb57118993a1ba3631b1952c585eb654eb1297b`
- Scene bytes unchanged: `True`
- V4: `passed` / signature `original validator result`
- V5: `passed` / signature `objective permutations=6; clearance samples=415`
- V8: `passed` / signature `be64fa8b33e798093d55087fc279377446e6e5556e059ad273aeaf1d87ccdfa4`
- V9: `passed` / signature `8301ccc17bf1323fb8e9d1a525a778bf9ccdbf2da3dc15412b4bbf790ac85da8`
- V10: `passed` / signature `b8a6c315ef7b4cc40ec8eafd851555ecb21a1c455105f58355ececb21f995f20 / classified V11 Great Step transition deltas=13`
  - Classified V11 transition delta: `Unexpected V10 root metrics: renderers=6_vertices=4872_triangles=2436_colliders=70`
  - Classified V11 transition delta: `Unexpected full-map V10 metrics: renderers=824_vertices=63902_triangles=46976_colliders=534`
  - Classified V11 transition delta: `V10 mesh topology drifted: Limestone_Structure`
  - Classified V11 transition delta: `V10 mesh omits spec corners: Great_Step_Diegetic_Boundary`
  - Classified V11 transition delta: `V10 generated mesh binding drifted: Limestone_Structure`
  - Classified V11 transition delta: `V10 mesh topology drifted: Red_Granite_Boundary`
  - Classified V11 transition delta: `V10 mesh omits spec corners: Great_Step_Granite_Bar_00`
  - Classified V11 transition delta: `V10 mesh omits spec corners: Great_Step_Granite_Bar_01`
  - Classified V11 transition delta: `V10 mesh omits spec corners: Great_Step_Granite_Bar_02`
  - Classified V11 transition delta: `V10 mesh omits spec corners: Great_Step_Granite_Bar_03`
  - Classified V11 transition delta: `V10 mesh omits spec corners: Great_Step_Granite_Bar_04`
  - Classified V11 transition delta: `V10 generated mesh binding drifted: Red_Granite_Boundary`
  - Classified V11 transition delta: `V10 proxy collider drifted: Great_Step_Boundary_Great_Step_Diegetic_Boundary`
- V4 validator SHA256: `b4ec09ed37c8ad1b7597528a3a8ced42ae7a8613436cdc31a9b1e609a6e85c3c`
- V5 validator SHA256: `405573071d52ef12fa816cf230e51bab11e2f2cda2f7dfe7e708a7b99fbc5ebd`
- V8 validator SHA256: `87c2fda947d591896d5a1813625be03424f6d79cea482cc6179162eb3bf3e68e`
- V9 validator SHA256: `b47a170d7736499c04b3e82e2c5ed07cc85937cb3fc6b4671a00fc44b4b14c46`
- V10 validator SHA256: `b7a6d8603390afc1d95369cf5f287b8eaeadbc831de2d05b929ef50c3a209a14`

V11_LEGACY_REGRESSION: passed
