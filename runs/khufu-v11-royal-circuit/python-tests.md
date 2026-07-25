# Khufu V11 Focused Python Tests

- Command: `python -m pytest tools/tests/test_validate_khufu_v11_prewrite.py tools/tests/test_validate_khufu_v11_release.py -q`
- Result: `19 passed in 1.72s`
- Covered: prewrite contract parsing, Fable verdict fail-closed behavior, PNG headers, staging
  allowlist normalization, exact staged-byte inventory, unlisted-scope rejection, post-commit
  inventory drift, rename records, and schema rejection.

V11_PYTHON_TESTS: passed
