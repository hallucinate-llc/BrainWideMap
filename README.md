# NeuroThera-Map


A **cross-species “receptor → circuit → activation” integration toolkit** that helps you:

- **Mouse mode:** combine brain-wide electrophysiology / imaging with **receptor & neurotransmitter biology** in Allen CCF space.
- **Human mode:** translate candidate mechanisms into human brain spaces (MNI / fsaverage) using **PET receptor atlases**, transcriptomics, and multimodal imaging.
- **Drug mode:** map a compound (e.g., caffeine, SSRIs) to **targets + affinities** (curated DBs), then propagate effects through **receptor distribution + connectivity** to generate testable hypotheses.
- **Validation mode (paired with a separate AlphaFold package):**
  - compare *AlphaFold-predicted binding* to *observed / predicted functional effects*,
  - compute **mutual validation losses** and exchange gradients / constraints between machines.

> Date created: 2025-12-28

---

## 0) What this repo is (and isn’t)

**This repo focuses on brain- and receptor-level integration and validation.**  
It does **not** do structural prediction, docking, or protein folding. Those live in your separate AlphaFold package.

This repo also does **not** claim clinical efficacy. It is a research toolkit to generate and validate mechanistic hypotheses.

---

## 1) Repository map

- `datasets/README.md` — dataset catalog + access points + what each dataset contributes.
- `pipelines/README.md` — ingestion + harmonization plan (mouse + human).
- `mouse/README.md` — mouse-specific workflows (IBL / Allen / tracing / CCF alignment).
- `human/README.md` — human translation workflows (PET receptor maps, AHBA, OpenNeuro).
- `drug/README.md` — drug/target/affinity ingestion + normalization.
- `validation/README.md` — AlphaFold ↔ NeuroThera-Map mutual validation design.
- `orchestration/README.md` — multi-machine topology + message schema for feedback loops.
- `governance/README.md` — licensing, provenance, ethics, and citation expectations.
- `docs/README.md` — comprehensive implementation plan with milestones and deliverables.

---

## 2) Core idea (data model)

Everything is expressed as a small set of interoperable objects (stored in Parquet/Zarr/NWB/BIDS as appropriate):

- **RegionMap**: values indexed by atlas regions (mouse CCF; human parcellation).
- **VoxelMap / SurfaceMap**: dense maps (volumetric MNI, surface fsaverage/fsLR).
- **ReceptorMap**: receptor/transporters density or expression (gene or PET).
- **ActivityMap**: task/condition activation (spikes, calcium, fMRI, IEG).
- **ConnectivityGraph**: directed weighted edges between regions/cell classes.
- **DrugProfile**: targets + affinities + mechanism metadata + uncertainty.

---

## 3) Quickstart (developer ergonomics)

This repo is designed to be “VSCode-friendly”: each subfolder has a README that can be used as a step-by-step build spec for an agent or developer.

Suggested minimal environment:

- Python 3.11+
- `poetry` or `uv`
- `pydantic` (schemas), `numpy`, `pandas`, `pyarrow`, `xarray`, `zarr`
- `nwb` tooling (`pynwb`) for electrophysiology packages (optional)
- `bids` tooling (`pybids`, `nilearn`) for human imaging (optional)

Implementation guidance and milestones live in `docs/README.md`.

---

## 4) How this integrates with your AlphaFold package

The two packages communicate via a **stable exchange schema**:

- From AlphaFold → NeuroThera-Map:
  - predicted target list, predicted binding energies/affinities, binding-site uncertainty
- From NeuroThera-Map → AlphaFold:
  - receptor candidates prioritized by circuit relevance,
  - functional constraints (which targets “should” affect which circuits),
  - observed effect signatures to penalize structurally-plausible-but-functionally-wrong predictions.

Details: `validation/README.md` and `orchestration/README.md`.


# Brain Wide Map Data Science Utilities

A comprehensive Python toolkit for exploring and analyzing the International Brain Laboratory's Brain Wide Map dataset - a large-scale neurophysiology dataset of mouse decision-making across 241 brain regions.

## Overview

The Brain Wide Map project (2025 data release) contains:
- **459 experimental sessions** with 699 probe insertions
- **621,733 neural units** from 139 subjects
- **241 brain regions** recorded across 12 laboratories
- Neuropixels electrophysiology data + behavioral measurements

This package provides utilities for:
- **Data Loading**: Easy access to sessions, trials, spikes, and clusters
- **Data Exploration**: Query and filter by brain region, session, subject
- **Statistical Analysis**: Compute firing rates, population statistics, correlations
- **Visualization**: Plot neural activity, behavioral data, and brain region maps

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from brainwidemap import DataLoader, Explorer, Statistics, Visualizer

# Initialize data loader (connects to IBL ONE-api)
loader = DataLoader()

# Explore available sessions
explorer = Explorer(loader)
sessions = explorer.list_sessions(n_trials_min=400)

# Load neural data from a session
eid = sessions[0]['eid']
spikes, clusters = loader.load_spike_data(eid)

# Compute statistics
stats = Statistics()
firing_rates = stats.compute_firing_rates(spikes, clusters)

# Visualize results
viz = Visualizer()
viz.plot_firing_rates_by_region(firing_rates, clusters)
```

## Features

### Data Loading
- Connect to IBL ONE-api (local or AWS)
- Load sessions, trials, behavioral data
- Load spike times, cluster information
- Load wheel movements, video data

### Data Exploration
- List sessions by criteria (brain region, date, subject)
- Query specific brain regions
- Filter units by quality metrics
- Search across subjects and labs

### Statistical Analysis
- Firing rate calculations (mean, variance, CV)
- Population statistics across brain regions
- Trial-aligned analysis (PSTH, rasters)
- Correlation and dimensionality reduction
- Decoding and prediction models

### Visualization
- Raster plots and PSTHs
- Brain region activity heatmaps
- Behavioral performance plots
- 3D brain atlas visualization

## Data Sources

- **Documentation**: https://docs.internationalbrainlab.org/notebooks_external/2025_data_release_brainwidemap.html
- **Public Data**: https://ibl.flatironinstitute.org/public/
- **AWS Registry**: https://registry.opendata.aws/ibl-brain-wide-map/

## Examples

See the `examples/` directory for Jupyter notebooks demonstrating:
- Basic data loading and exploration
- Regional activity analysis
- Behavioral correlations
- Population decoding

## Requirements

- Python 3.8+
- ONE-api (IBL data access)
- NumPy, Pandas, SciPy
- Matplotlib, Seaborn
- scikit-learn (for ML utilities)

## License

MIT License - see LICENSE file

## Citation

If you use this toolkit, please cite the International Brain Laboratory:

```
International Brain Laboratory et al. (2023). 
A Brain-Wide Map of Neural Activity during Complex Behaviour.
Nature. DOI: 10.1038/s41586-023-06742-4
```

## Contributing

Contributions welcome! Please open issues or pull requests.

## Support

For questions about the Brain Wide Map dataset, see IBL documentation.
For questions about this toolkit, open a GitHub issue.
