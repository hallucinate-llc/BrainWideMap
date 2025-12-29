# BrainWideMap

This repository contains two related Python toolkits.

If you’re new here: the goal is to make it easy to go from **brain-wide activity data** (what changed in which regions) to **mechanistic hypotheses** (which receptors/targets and circuits could explain it), with a workflow that stays testable and reproducible.

## Why this exists

In practice, mechanistic “brain → receptor → circuit” work often gets stuck because:

- Your data sources live in different ecosystems (IBL sessions, Allen connectivity, receptor maps, human PET), each with their own formats.
- You can compute results, but it’s hard to keep the *data model* consistent and validate that components still work together over time.
- Live dependencies (network downloads, optional SDKs) make tests flaky and discourage end-to-end coverage.

This repo addresses that by:

- Providing small, explicit **core types** (region-indexed maps and connectivity graphs) that you can pass between steps.
- Keeping the **default test suite deterministic and offline**, while also providing opt-in **live/E2E tests** that validate real external integrations.

## What you can do with it

Common use cases:

- Explore IBL Brain Wide Map sessions and compute region-level summaries.
- Build a lightweight drug/target profile and generate a toy prediction pipeline.
- Load a mouse connectivity graph (offline stub or real Allen SDK) and propagate effects through circuits.
- Translate a region-indexed prediction into a human space and run simple validation utilities.

## Packages in this repo

There are two packages, used for different jobs:

- **brainwidemap**: utilities for exploring and analyzing the International Brain Laboratory (IBL) Brain Wide Map dataset via ONE-api.
- **neurothera_map**: a dependency-light “receptor → circuit → activation” integration toolkit (mouse ↔ human translation + validation primitives).

Both live in the same Python distribution (installed as `brainwidemap`), and are tested together.

## How it works (conceptual)

At a high level, `neurothera_map` encourages a simple, composable pipeline:

1. Represent your data as **region-indexed arrays** (`ActivityMap`, `ReceptorMap`).
2. Load or construct a **ConnectivityGraph** (offline stub for tests, or real Allen SDK for real runs).
3. (Optional) Build a **DrugProfile** (targets/affinities).
4. Combine/propagate these pieces to get a predicted activity signature.
5. Translate/validate the result in a human space.

This is intentionally not “one big model” — it’s a small set of interoperable building blocks.

## Workflow: chemical → brain hypothesis

If your goal is “I have a chemical/drug; help me reason about how it could modulate the brain,” start here:

- [docs/WORKFLOW.md](docs/WORKFLOW.md)

That guide walks through:

- Building a `DrugProfile` (chemical → targets)
- Building a `ReceptorMap` (targets → regional susceptibility)
- Loading a `ConnectivityGraph` (circuits; offline stub or real Allen SDK)
- Predicting a mouse `ActivityMap` and translating/validating in human space

## Quickstart

### Install

Core (runtime) dependencies:

```bash
pip install -r requirements.txt
```

Developer install (recommended for working on the repo):

```bash
pip install -e ".[dev]"
```

### Run tests

Deterministic offline test suite (no network, no optional deps; default):

```bash
pytest
```

Run the full end-to-end surface area (default suite + real allensdk E2E + live Allen tests):

```bash
bash scripts/run_all_tests.sh
```

Notes:

- The Allen SDK (`allensdk`) requires **Python < 3.12** (Python 3.11 recommended).
- Live Allen tests are **deselected by default**; they run only when explicitly enabled.

## Package overview

### `brainwidemap`

High-level interface for IBL Brain Wide Map utilities:

```python
from brainwidemap import DataLoader, Explorer, Statistics, Visualizer

loader = DataLoader()
explorer = Explorer(loader)

sessions = explorer.list_sessions(n_trials_min=400)
eid = sessions.iloc[0]["eid"]

spikes, clusters = loader.load_spike_data(eid)
stats = Statistics()
firing_rates = stats.compute_firing_rates(spikes, clusters)

viz = Visualizer()
viz.plot_firing_rates_by_region(firing_rates, clusters)
```

### `neurothera_map`

Core public API exports are intentionally small:

```python
import numpy as np
import neurothera_map

drug = neurothera_map.build_drug_profile("caffeine", mode="seed")

mouse_pred = neurothera_map.ActivityMap(
    region_ids=np.asarray(["VISp", "CA1"], dtype=str),
    values=np.asarray([1.0, -0.5], dtype=float),
    space="allen_ccf",
    name="mouse_pred",
)

human_pred = neurothera_map.translate_to_human(mouse_pred, human_space="mni152")
report = neurothera_map.validate_against_pet_and_fmri(human_pred)
```

Mouse connectivity + MVP prediction live under `neurothera_map.mouse`.

## Repository map

- [DEVELOPMENT.md](DEVELOPMENT.md): installation + test matrix (offline / live / E2E).
- [docs/API.md](docs/API.md): public API reference for `brainwidemap` and `neurothera_map`.
- [mouse/README.md](mouse/README.md): mouse workflows (Allen connectivity; offline stub vs real allensdk).
- [human/README.md](human/README.md): human translation workflows.
- [drug/README.md](drug/README.md): drug ingestion and profile building.

## License

MIT License — see [LICENSE](LICENSE).
