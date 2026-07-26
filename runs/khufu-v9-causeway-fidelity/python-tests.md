# Khufu V9 Python Validator Tests

- Command: `PYTHONPATH=. C:/Users/User/.local/bin/pytest.exe -q tools/tests/test_validate_khufu_v9_causeway_fidelity.py tools/tests/test_validate_khufu_v5_performance.py`
- Result: `15 passed in 0.22s`
- Coverage: exact artifact/runtime payload binding inventories, stale hashes, staged whitelist, staged/worktree drift,
  scene ownership delta, full PNG decoding/padding rejection, and performance budget parsing.

V9_PYTHON_TESTS: passed
