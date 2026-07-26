# Khufu V13 Python Tests

- Focused release-validator tests: `36 passed in 110.34s`
- Focused V13 prewrite-validator tests: `28 passed in 4.35s`
- Broader repository tests excluding legacy snapshot suites: `166 passed in 112.39s`
- Focused command: `python -B -m pytest -p no:cacheprovider tools/tests/test_validate_khufu_v13_release.py -q`
- Broader command: `python -B -m pytest -p no:cacheprovider tools/tests tools/studio -q --ignore=tools/tests/test_validate_khufu_v5_harness.py --ignore=tools/tests/test_validate_khufu_v6_visual_slice.py`
- Excluded suites: V5/V6 frozen snapshots whose historical source/build bindings were
  intentionally superseded by later repository revisions.
- V13 test failures: `0`

KHUFU_V13_PYTHON_TESTS: passed
