# Khufu V13 Release Gate Review

- Review task: `v12_release_pattern`
- Scope: release validator, validator tests, exact staging allowlist, and Git byte-preservation rules
- P0 / P1: `0 / 0`
- Focused validation: `36 passed`
- `tools/validate_khufu_v13_release.py` SHA256: `32a07627ff89045333f01058a80897cf5f70af9f64a8f6d6b006f2daacae96f1`
- `tools/tests/test_validate_khufu_v13_release.py` SHA256: `b9d00277ffff75304fa55719e8302873a7b073d05b3aa29926e925a29cba0a42`
- `docs/khufu-v13-subterranean-threshold/staging-allowlist.txt` SHA256: `30d22393312d68d8d6f5a764f8967e79a451bb73accaf08a03f1dddb8873fdf9`
- `.gitattributes` SHA256: `c1f8583c50e5d7ad0035e41f8cb9f8990fb545decc50429e6d9414bee9448017`

## Review Result

The orchestrator fallback now requires three independent, task-specific artifacts and binds
each artifact to the exact files it reviewed. The clean-import gate validates its source commit
and candidate tree, compares canonical Git blobs, and switches to staged-index blobs during the
staged gate. Staged validation produces a passing inventory-bound report, requires an
index-to-output byte match on the convergence rerun, and post-commit validation verifies both
helper blobs plus all allowlisted worktree paths. No P0 or P1 release-gate defect remains in the
reviewed scope.

ORCHESTRATOR_REVIEW_VERDICT: passed
