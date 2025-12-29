# BrainWideMap

This repository contains two related Python toolkits:

- **brainwidemap**: utilities for exploring and analyzing the International Brain Laboratory (IBL) Brain Wide Map dataset via ONE-api.
- **neurothera_map**: a dependency-light “receptor → circuit → activation” integration toolkit (mouse ↔ human translation + validation primitives).

Both live in the same Python distribution (installed as `brainwidemap`), and are tested together.

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
