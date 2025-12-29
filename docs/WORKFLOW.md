# Workflow: From a Chemical to a Brain-Level Hypothesis

This guide is for people who want to use this repo to reason about **how a chemical (drug/compound) might modulate the brain**.

It’s written as a practical walkthrough with a clear mental model:

- **Drug / chemical** → a set of **targets** with **strength** and **direction** (DrugProfile)
- **Targets** → regional “susceptibility” (ReceptorMap)
- **Circuits** → propagation through a connectivity graph (ConnectivityGraph)
- **Predicted modulation** → a region-indexed signature (ActivityMap)
- **Human translation + validation** → pragmatic adapters to run comparison utilities

This repo is intentionally lightweight and testable:

- Default tests are deterministic and offline.
- Real Allen SDK (`allensdk`) is supported via opt-in live/E2E runs.

## 0) Choose your execution mode

You have two ways to run the Allen connectivity piece:

- **Offline (recommended to start)**: deterministic synthetic connectivity (no network, no `allensdk`).
- **Real Allen SDK**: uses `allensdk` and downloads/caches real data.

The toggle is the environment variable:

- `BWM_ALLEN_OFFLINE=1` → offline stub
- `BWM_ALLEN_OFFLINE=0` → real `allensdk` path (Python < 3.12 recommended)

If you want to validate the *real* integration end-to-end, use:

- `bash scripts/run_e2e_allensdk.sh`

## 1) Build a DrugProfile (chemical → targets)

Entry point:

- `neurothera_map.build_drug_profile(...)`

This returns a `DrugProfile`: a normalized name plus a list of `DrugInteraction` items.

### Start offline (seed mode)

```python
import neurothera_map

drug = neurothera_map.build_drug_profile("caffeine", mode="seed")
print(drug.name)
print(len(drug.interactions))
```

### Use ingestion (optional)

The repo also contains a richer ingestion system under `drug/`. The `neurothera_map` wrapper defaults to offline-safe behavior, and you can opt into ingestion explicitly.

```python
import neurothera_map

# Requires the ingestion stack to be available and (optionally) network access.
# These are intentionally opt-in.

drug = neurothera_map.build_drug_profile(
    "caffeine",
    mode="ingest",
    use_iuphar=True,
    use_chembl=True,
)
```

Practical note: if your goal is to prototype the brain-side pipeline first, seed mode is usually the fastest path.

## 2) Build a ReceptorMap (targets → regional susceptibility)

A `ReceptorMap` is conceptually “for each target, how much is it expressed/dense in each region?”.

In this repo, the MVP loader is CSV-based:

- `neurothera_map.mouse.load_receptor_map_from_csv(...)`

You can start with a small receptor panel that matches your `DrugProfile` targets.

## 3) Load a ConnectivityGraph (circuits)

Entry point:

- `neurothera_map.mouse.load_allen_connectivity(...)`

Offline stub example:

```python
import os
from neurothera_map.mouse import load_allen_connectivity

os.environ["BWM_ALLEN_OFFLINE"] = "1"

graph = load_allen_connectivity(region_acronyms=["VISp", "MOp", "SSp"], normalize=True)
print(graph.adjacency.shape)
```

Real Allen SDK example (opt-in):

```python
import os
from neurothera_map.mouse import load_allen_connectivity

os.environ["BWM_ALLEN_OFFLINE"] = "0"

graph = load_allen_connectivity(region_acronyms=["VISp", "MOp", "SSp"], normalize=True)
```

## 4) Predict mouse effects (DrugProfile + ReceptorMap + ConnectivityGraph → ActivityMap)

Entry point:

- `neurothera_map.mouse.predict_mouse_effects(...)`

This is deliberately simple and deterministic:

- It constructs a **direct regional prior** by weighting each target’s expression by (evidence × 1/affinity) and a sign inferred from action.
- It optionally **diffuses** that prior over the connectivity graph.

```python
from neurothera_map.mouse import predict_mouse_effects

mouse_pred = predict_mouse_effects(drug, receptor_map, graph)
print(mouse_pred.space)
print(mouse_pred.values[:5])
```

## 5) Translate to human (placeholder MVP)

Entry point:

- `neurothera_map.translate_to_human(...)`

This function is explicitly a **workflow placeholder**: it preserves the numeric signature and updates provenance so downstream human-side adapters can run.

If you have a mapping (even a crude acronym-to-acronym mapping), you can pass it:

```python
import neurothera_map

region_id_map = {"VISp": "V1"}

human_pred = neurothera_map.translate_to_human(
    mouse_pred,
    human_space="mni152",
    region_id_map=region_id_map,
)
```

## 6) Validate against human receptor/activity observations (optional)

Entry point:

- `neurothera_map.validate_against_pet_and_fmri(...)`

This returns a `ValidationReport` (ranking / simple summary statistics). It’s designed to be usable even with offline fixtures.

```python
import neurothera_map

report = neurothera_map.validate_against_pet_and_fmri(human_pred)
print(report)
```

## Where to look next

- API reference: `docs/API.md`
- Mouse connectivity notes: `ALLEN_CONNECTIVITY_IMPLEMENTATION.md`
- Mouse workflow guide: `mouse/README.md`
- Examples: `examples/`
- The most reliable “executable documentation”: `tests/test_neurothera_end_to_end_integration.py` and `tests_e2e/`

## Implementation map (what code runs)

This section is intentionally concrete: it tells you *which modules implement each step*.

### Core data model

The small set of core types is defined in:

- `neurothera_map/core/types.py`

You’ll see these passed between steps:

- `DrugProfile` / `DrugInteraction`: chemical → targets/affinities/evidence
- `RegionMap` / `ReceptorMap`: region-indexed measurements (expression/density)
- `ConnectivityGraph`: directed weighted adjacency between regions
- `ActivityMap`: region-indexed activity/prediction signature

### Step 1: chemical → DrugProfile

Entry point:

- `neurothera_map.drug.profile.build_drug_profile`

What it does:

- Normalizes the name.
- In `mode="seed"`, returns a small built-in offline profile (fast, deterministic).
- In `mode="ingest"`/`"auto"`, uses the ingestion system under `drug/` (and can optionally query adapters when enabled).
- Records provenance fields like `mode`, `seed_db_hit`, and ingestion availability.

### Step 2: targets → ReceptorMap

Mouse MVP CSV loader:

- `neurothera_map.mouse.expression.load_receptor_map_from_csv`

What it does:

- Reads a parcellated table from CSV and returns a `ReceptorMap` keyed by receptor/target names.
- Produces region-aligned `RegionMap` objects internally.

### Step 3: circuits → ConnectivityGraph

Entry point:

- `neurothera_map.mouse.allen_connectivity.load_allen_connectivity`

What it does:

- When `BWM_ALLEN_OFFLINE=1`, returns deterministic synthetic connectivity (no `allensdk`, no network).
- When `BWM_ALLEN_OFFLINE=0`, uses `allensdk` to build a region-to-region projection matrix (cached by Allen’s manifest/cache).

### Step 4: DrugProfile + ReceptorMap (+ ConnectivityGraph) → predicted ActivityMap

Entry point:

- `neurothera_map.mouse.mvp_predict.predict_mouse_effects`

What it does internally:

- Builds a **direct regional prior** by combining receptor expression with drug interactions.
    - Weight uses `evidence` and (when available) `1/affinity_nM`.
    - Sign is inferred from `action` (agonist vs antagonist/inhibitor).
- If a graph is provided, it propagates/diffuses that prior over `ConnectivityGraph` via:
    - `neurothera_map.mouse.predict.diffuse_activity`

This is designed to be deterministic and simple (MVP), so you can swap in richer models later while keeping the same inputs/outputs.

### Step 5: mouse ActivityMap → human ActivityMap (translation)

Entry point:

- `neurothera_map.human.translate.translate_to_human`

What it does:

- MVP placeholder that preserves the numeric signature and updates `space`.
- Optionally accepts a `region_id_map` for a pragmatic acronym/label remap.
- Records provenance explicitly indicating placeholder translation.

### Step 6: validation report

Entry point:

- `neurothera_map.human.validate.validate_against_pet_and_fmri`

What it does:

- Computes simple ranking/summary statistics comparing a predicted `ActivityMap` with optional receptor/activity observations.
- Returns a `ValidationReport` (see `neurothera_map/validation/`).

## Executable references (recommended)

If you want to understand the workflow end-to-end, start with these files because they are continuously exercised by tests:

- `tests/test_neurothera_public_api_smoke.py` (minimal public API workflow)
- `tests/test_neurothera_end_to_end_integration.py` (offline integration across drug → mouse prediction → translation → validation)
- `tests_e2e/test_e2e_allensdk_pipeline.py` (real `allensdk` E2E; requires Python 3.11 and `BWM_ALLEN_OFFLINE=0`)

There are also runnable example scripts/notebooks:

- `examples/allen_connectivity_example.py`
- `examples/01_basic_usage.ipynb`
- `examples/02_statistical_analysis.ipynb`

## Troubleshooting

### “My Allen connectivity load is slow / tries to download things”

You are likely in real-Allen mode.

- For deterministic offline runs (no network, no `allensdk`):

```bash
export BWM_ALLEN_OFFLINE=1
pytest
```

- For real Allen SDK mode (may download/cache on first run):

```bash
export BWM_ALLEN_OFFLINE=0
```

If you want a single command that verifies the real integration end-to-end, use:

```bash
bash scripts/run_e2e_allensdk.sh
```

### “`allensdk` won’t install / import”

The Allen SDK currently requires Python < 3.12.

- Recommended: use Python 3.11 for real-Allen runs.
- For a no-sudo install of Python 3.11, see `DEVELOPMENT.md` (uses `uv`).

### “My live Allen tests aren’t running”

Live tests are **deselected by default** so a normal `pytest` run is skip-free.

Run them explicitly:

```bash
pip install -e ".[dev,allen]"
export BWM_ALLEN_OFFLINE=0
pytest --run-allen-live -m allen_live
```

### “`predict_mouse_effects` returns all zeros / empty output”

Common causes:

- Your `DrugProfile` targets don’t match the receptor names in your `ReceptorMap`.
    - Fix: ensure the receptor map keys include the same strings as `DrugInteraction.target`.
- Your receptor map is empty or the regions don’t align.
    - Fix: confirm your CSV loader produced non-empty maps and that regions are aligned to your graph.

### “`build_drug_profile` has no interactions”

- In `mode="seed"`, only a small set of compounds is available (it’s intentionally tiny).
    - Fix: try a known seed entry (e.g. caffeine), or switch to ingestion mode.
- In `mode="ingest"`, ingestion may not be available or the compound may not be found.
    - Fix: use `mode="auto"` to allow fallback, or check the ingestion docs under `drug/`.

### “What should I run to make sure things work?”

- Fast, deterministic sanity check:

```bash
pytest
```

- Full surface area including real Allen E2E (will manage its own env):

```bash
bash scripts/run_all_tests.sh
```
