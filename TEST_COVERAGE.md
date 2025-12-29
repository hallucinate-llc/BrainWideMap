# Test Coverage & Test Strategy

This repo intentionally separates **deterministic unit/integration tests** (offline, fast, no optional deps) from **live / end-to-end** tests that validate real external dependencies.

## Test tiers

### 1) Default deterministic suite (offline)

This is what `pytest` runs by default:

- No network access
- No `allensdk` required
- No optional neuroimaging dependencies required
- Live Allen tests are deselected by default (so you see zero “skipped” in a normal run)

Run:

```bash
pytest
```

### 2) Live Allen SDK integration tests (opt-in)

These tests validate that `neurothera_map.mouse.load_allen_connectivity()` works with a real `allensdk` installation.

Run:

```bash
pip install -e ".[dev,allen]"
BWM_ALLEN_OFFLINE=0 pytest --run-allen-live -m allen_live
```

Notes:

- Requires Python < 3.12 (Python 3.11 recommended).
- May require network access the first time to populate the Allen cache.

### 3) True E2E allensdk suite (installer + tests)

This suite is designed to **fail** if the real allensdk path is broken.

Run:

```bash
bash scripts/run_e2e_allensdk.sh
```

## Where the tests live

- `tests/`: default deterministic test suite
- `tests_e2e/`: end-to-end tests that require real dependencies/data

If you want to see exactly what will run in your environment, use:

```bash
pytest --collect-only -q
```
