# Allen Mouse Connectivity Loader

This repo provides an Allen Institute Mouse Brain Connectivity loader under:

- `neurothera_map/mouse/allen_connectivity.py`

It supports two modes:

## 1) Offline deterministic mode (default in unit tests)

When `BWM_ALLEN_OFFLINE=1`, the loader uses an internal deterministic stub:

- No `allensdk` dependency
- No network access
- Stable small structure list and synthetic connectivity values

This is what the default test suite exercises so CI and local runs are deterministic.

## 2) Real Allen SDK mode (opt-in)

When `BWM_ALLEN_OFFLINE=0`, the loader uses `allensdk` and the real Allen cache:

- Requires `allensdk` (Python < 3.12; Python 3.11 recommended)
- Usually requires network access on first run (to populate cache)
- Uses the Allen SDK cache/manifest for subsequent runs

## Usage

```python
from neurothera_map.mouse import load_allen_connectivity

connectivity = load_allen_connectivity(
    region_acronyms=["VISp", "MOp", "SSp"],
    normalize=True,
    threshold=0.01,
)
```

## Testing

There are three relevant layers:

### A) Default deterministic suite (offline)

```bash
pytest
```

### B) Live Allen SDK integration tests (opt-in)

Live tests are marked `allen_live` and are **deselected by default**.

```bash
pip install -e ".[dev,allen]"
BWM_ALLEN_OFFLINE=0 pytest --run-allen-live -m allen_live
```

### C) True end-to-end (E2E) allensdk installer + tests

This creates a dedicated env and runs `tests_e2e/`. These tests are **not skipped** and will **fail** if the real dependency/data path is broken.

```bash
bash scripts/run_e2e_allensdk.sh
```

## Notes

- `requirements.txt` intentionally does **not** include `allensdk` so the core package remains lightweight.
- If you’re diagnosing connectivity issues, start with the E2E runner, because it validates the real `allensdk` path end-to-end.
