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
