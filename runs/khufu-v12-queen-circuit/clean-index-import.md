# Khufu V12 Clean Alternate-Index Import

- Verdict: **passed**
- Source: exact V12 allowlist candidate exported from an alternate Git index and isolated object store
- Candidate tree: `d944b0dc4ba2db4e8a5f971cad9f761b14cad1fe`
- Candidate files present at export time: `98`
- Unity: `6000.0.76f1`
- Execute method: `ChannelPlayKhufuV12QueenCircuitValidator.ValidateBatch`
- Unity exit code: `0`
- Compiler errors: `0`
- Static signature: `6f7faced5cee8f6b199f18c979b5174473d85154c695a93a29f37db4db0059cd`
- Generated/material signature: `33fbeb4df333143dcc417e18e09e3ee430826ce8d87b0004ef5d53a3108d0435`
- Scene SHA256: `eec9cc9c0b52cd75066c20caf1710ab458423de2eea073c7cfe36e88a782ec8c`
- Static receipt SHA256 before/after: `d1e0042ca2c457a3ec3054487fac205632f2643c1dd62384fc3638bef2e7f3b2 / d1e0042ca2c457a3ec3054487fac205632f2643c1dd62384fc3638bef2e7f3b2`
- Main index SHA256 before/after: `f582723bfaa7ecb9faa77211d2cb0d46239127292a231d926581977e4982d844 / f582723bfaa7ecb9faa77211d2cb0d46239127292a231d926581977e4982d844`
- Builder SHA256: `e945183f3162709a08fca4e33f14bd7795e4faefd3c5194ca3d9ef6f473aa637`
- Mesh pipeline SHA256: `d4d357fa5ce11dad94d2c9102ff66b298a2fcc3d12d7a08fcfb175426d5c018a`
- Screenshot exporter SHA256: `24a462a3ba1b6e71d65caa691f9e4a4360f35eb1787ade02d059a1e4d6484862`
- Validator SHA256: `ec4df5d403fa59bd2fc5fd138db0f2eb19980a4f6c7eea63cb2b591237d337fc`
- Release validator SHA256: `5ac42c0f83aba30c5b262bf0e7d60be38d62189fc172d5f9225215c553ea2874`
- Allowlist SHA256: `12dd32a19fdbbf864fdffe5d4c52f3f375e93498ee193b2311922610131ff69f`
- `.gitattributes` SHA256: `716a9fd1e1cc08ea3fbce0f223282cc87d546f0b5aca20ff9f923441fff574fa`
- Capture blobs matched the candidate index: `6/6`, all unique, `1600x1000`

## Deliberately Deferred At Clean Export

The 10-path gap from the 108-path allowlist is exact and non-source:

- `runs/khufu-v12-queen-circuit/clean-index-import.md`
- `runs/khufu-v12-queen-circuit/review-resolution.md`
- `runs/khufu-v12-queen-circuit/release-validation.md`
- `runs/khufu-v12-queen-circuit/staged-inventory.json`
- `runs/khufu-v12-queen-circuit/staged-index-validation.md`
- `runs/khufu-v12-queen-circuit/post-commit-validation.md`
- `work/fable-harness/khufu-v12-queen-circuit-final-review-resolution.md`
- `work/fable-harness/khufu-v12-queen-circuit-final-review-followup.md`
- `work/fable-harness/khufu-v12-queen-circuit-final-review-followup.dry-run.txt`
- `work/fable-harness/khufu-v12-queen-circuit-final-review.opus.followup.md`

## Candidate Capture SHA256

- `queen_threshold_open_axis.png`: `636c3a60fe174cb45da6d90873d7a088253b097349424c2c11913ea9fc74e23b`
- `horizontal_passage_low_axis.png`: `6fe932969a6619b66b762bc651d55cd9e73145e8d04bc0257fa2d76108ead764`
- `chamber_doorway_release.png`: `1869a50d9baa8945c8a432574dd727ed624aca00db7a40f9241b5288bc398bfc`
- `queens_chamber_gabled_wide.png`: `4ddebde934d122421a6a38cb6ca5be1ebacc1f8811f429fda5f23504b35cd896`
- `east_niche_and_narrow_mouths.png`: `1c29ebac2e8956e822e9f4607bf9381cbe0b57af2762594fcfc04570449a12c2`
- `queen_circuit_integration.png`: `936f16ad940bd8a3dc696fa36ab8736514e7913a2b17b83cdc194fc6926173d1`

The first clean attempt exposed Git newline normalization in three canonical-signature JSON inputs and the static receipt. Exact `-text` rules now preserve those byte-bound files; the final clean candidate reproduced the reviewed signature and receipt bytes.

KHUFU_V12_CLEAN_INDEX_IMPORT: passed
