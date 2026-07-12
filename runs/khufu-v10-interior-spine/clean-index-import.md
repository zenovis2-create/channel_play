# Khufu V10 Clean Index Import

- Staged tree SHA: `a141d355e00253a138e93709d2bb85577d0ad473`.
- Exported tracked files: `872`.
- Unity editor: `6000.0.76f1`.
- Project path: `D:/Temp/User/khufu-v10-clean-index-20260713-stable`.
- Package mode: `-noUpm`; the baseline package manifest cannot resolve
  `com.unity.multiplayer.center 1.0.0` in this editor, while the current package changes belong to the
  previously configured MCP/AI setup and remain outside the V10 commit.
- All six V10 material assets imported with their committed GUID metadata.
- Seven scene-referenced V4 mesh assets and both parent folder metadata files were added to the exact
  release dependency inventory after the first clean import exposed their absence.
- Unity `.asset`, `.mat`, `.meta`, and `.unity` paths are checkout-stable at LF through
  `.gitattributes`; this preserves raw-hash validators under `core.autocrlf=true`.
- Static validation: `220` clearance samples, enclosure minimum `0.792`.
- Rebuilds: two deterministic builds at six renderers, 5,016 vertices, 2,508 triangles, and 70
  colliders with 60/39 renderer/collider transitions.
- Final clean scene SHA256:
  `d1778ecb2edfb7e83173a893ec82f5acb8959078ec68fc714a5f1a1320e83ad2`.
- Source scene SHA256:
  `d1778ecb2edfb7e83173a893ec82f5acb8959078ec68fc714a5f1a1320e83ad2`.
- Compiler errors: `0`.
- Validation exceptions: `0`.
- Terminal marker: `CHANNEL_PLAY_KHUFU_V10_STATIC_GATES result=passed`.

The clean editor reports a different non-frozen V10 diagnostic signature because `-noUpm` causes
`V10_Route_Amber.mat` to be reserialized differently during the isolated rebuild. The structural
metrics, required GUID imports, all static and mutation gates, and final scene bytes remain identical.

V10_CLEAN_INDEX_IMPORT: passed
