# API Documentation

This repo contains two related Python packages:

- `brainwidemap`: IBL Brain Wide Map utilities (ONE-api based)
- `neurothera_map`: receptor → circuit → activation integration primitives

## neurothera_map

### Top-level public API

The top-level `neurothera_map` namespace exports a small set of stable types and helpers:

```python
import neurothera_map

drug = neurothera_map.build_drug_profile("caffeine", mode="seed")
```

**Exports (high level):**

- `RegionMap`, `ReceptorMap`, `ActivityMap`, `ConnectivityGraph`
- `DrugInteraction`, `DrugProfile`
- `build_drug_profile(...)`
- `translate_to_human(...)`
- `validate_against_pet_and_fmri(...)`

See the smoke workflow in `tests/test_neurothera_public_api_smoke.py`.

### Mouse helpers (`neurothera_map.mouse`)

Mouse connectivity and MVP prediction live under `neurothera_map.mouse`:

```python
from neurothera_map.mouse import load_allen_connectivity, predict_mouse_effects
```

Key functions/classes:

- `AllenConnectivityLoader`, `load_allen_connectivity(...)`
- `ExpressionTableSpec`, `load_receptor_map_from_csv(...)`
- `predict_mouse_effects(...)`

Notes:

- The connectivity loader supports an offline stub via `BWM_ALLEN_OFFLINE=1`.
- Real `allensdk` integration requires `BWM_ALLEN_OFFLINE=0` and Python < 3.12.

### Human helpers (`neurothera_map.human`)

Human translation and validation live under `neurothera_map.human`:

- `translate_to_human(...)`
- `validate_against_pet_and_fmri(...)`
- `load_human_pet_receptor_maps(...)`

See `tests/test_neurothera_end_to_end_integration.py` for an offline end-to-end example.

---

## DataLoader

The `DataLoader` class provides access to Brain Wide Map data through the ONE-api.

### Initialization

```python
loader = DataLoader(mode='auto', cache_dir=None)
```

**Parameters:**
- `mode` (str): Connection mode - 'auto', 'local', or 'remote'. Default: 'auto'
- `cache_dir` (str, optional): Directory for caching downloaded data

### Methods

#### `list_sessions(project='brainwide', **kwargs)`
List available experimental sessions.

**Returns:** DataFrame with session information (eid, subject, date, lab, etc.)

#### `load_trials(eid)`
Load trial data for a session.

**Parameters:**
- `eid` (str): Experiment ID

**Returns:** DataFrame with trial information

#### `load_spike_data(eid, probe=None)`
Load spike times and cluster information.

**Parameters:**
- `eid` (str): Experiment ID
- `probe` (str, optional): Specific probe name

**Returns:** Tuple of (spikes dict, clusters DataFrame)

#### `load_wheel_data(eid)`
Load wheel movement data.

**Parameters:**
- `eid` (str): Experiment ID

**Returns:** Dictionary with wheel data

#### `load_behavior_data(eid)`
Load comprehensive behavioral data.

**Parameters:**
- `eid` (str): Experiment ID

**Returns:** Dictionary with behavioral data

#### `get_brain_regions(eid)`
Get list of brain regions recorded in a session.

**Parameters:**
- `eid` (str): Experiment ID

**Returns:** List of brain region acronyms

---

## Explorer

The `Explorer` class provides methods to query and filter Brain Wide Map data.

### Initialization

```python
explorer = Explorer(loader)
```

**Parameters:**
- `loader`: DataLoader instance

### Methods

#### `list_sessions(n_trials_min=None, n_trials_max=None, date_range=None, subject=None, lab=None)`
List sessions with filtering options.

**Parameters:**
- `n_trials_min` (int, optional): Minimum number of trials
- `n_trials_max` (int, optional): Maximum number of trials
- `date_range` (list, optional): Date range ['YYYY-MM-DD', 'YYYY-MM-DD']
- `subject` (str, optional): Subject identifier
- `lab` (str, optional): Lab name

**Returns:** DataFrame of filtered sessions

#### `get_session_summary(eid)`
Get comprehensive summary of a session.

**Parameters:**
- `eid` (str): Experiment ID

**Returns:** Dictionary with summary information

#### `find_sessions_by_region(region, min_units=10)`
Find sessions containing recordings from a specific brain region.

**Parameters:**
- `region` (str): Brain region acronym (e.g., 'VISp', 'CA1')
- `min_units` (int): Minimum number of units from that region

**Returns:** DataFrame of matching sessions

#### `get_brain_region_coverage(eid)`
Get brain region coverage for a session.

**Parameters:**
- `eid` (str): Experiment ID

**Returns:** DataFrame with brain regions and unit counts

#### `filter_units_by_quality(clusters, quality_threshold=0.9, isi_violations_max=0.5)`
Filter neural units by quality metrics.

**Parameters:**
- `clusters` (DataFrame): Cluster information
- `quality_threshold` (float): Minimum quality score
- `isi_violations_max` (float): Maximum ISI violation rate

**Returns:** Filtered DataFrame

#### `get_all_brain_regions()`
Get list of all brain regions in the dataset.

**Returns:** List of unique brain region acronyms

---

## Statistics

The `Statistics` class provides statistical analysis methods.

### Initialization

```python
stats = Statistics()
```

### Methods

#### `compute_firing_rates(spikes, clusters, time_window=None)`
Compute firing rates for all units.

**Parameters:**
- `spikes` (dict): Dictionary with 'times' and 'clusters' arrays
- `clusters` (DataFrame): Cluster information
- `time_window` (tuple, optional): (start, end) time window in seconds

**Returns:** DataFrame with firing rate statistics

#### `compute_psth(spike_times, spike_clusters, cluster_id, event_times, window=(-0.5, 1.0), bin_size=0.01)`
Compute peri-stimulus time histogram.

**Parameters:**
- `spike_times` (array): Spike times
- `spike_clusters` (array): Cluster IDs
- `cluster_id` (int): Cluster to analyze
- `event_times` (array): Event times to align to
- `window` (tuple): Time window around events
- `bin_size` (float): Bin size in seconds

**Returns:** Tuple of (time_bins, psth) arrays

#### `compute_trial_firing_rates(spike_times, spike_clusters, cluster_id, trial_windows)`
Compute firing rate for each trial.

**Parameters:**
- `spike_times` (array): Spike times
- `spike_clusters` (array): Cluster IDs
- `cluster_id` (int): Cluster to analyze
- `trial_windows` (list): List of (start, end) tuples

**Returns:** Array of firing rates per trial

#### `compute_fano_factor(spike_counts)`
Compute Fano factor (variance/mean).

**Parameters:**
- `spike_counts` (array): Spike counts across trials

**Returns:** Fano factor value

#### `compute_correlation_matrix(firing_rates_matrix)`
Compute pairwise correlation matrix.

**Parameters:**
- `firing_rates_matrix` (array): Matrix (neurons x time_bins)

**Returns:** Correlation matrix

#### `compute_population_statistics(spikes, clusters, brain_region=None)`
Compute population-level statistics.

**Parameters:**
- `spikes` (dict): Spike data
- `clusters` (DataFrame): Cluster information
- `brain_region` (str, optional): Filter by region

**Returns:** Dictionary with population statistics

#### `perform_anova(data_groups)`
Perform one-way ANOVA test.

**Parameters:**
- `data_groups` (list): List of arrays

**Returns:** Tuple of (F-statistic, p-value)

#### `perform_ttest(group1, group2, paired=False)`
Perform t-test.

**Parameters:**
- `group1` (array): First group
- `group2` (array): Second group
- `paired` (bool): Paired test

**Returns:** Tuple of (t-statistic, p-value)

#### `smooth_data(data, window_size=5, method='gaussian')`
Smooth data.

**Parameters:**
- `data` (array): Input data
- `window_size` (int): Window size
- `method` (str): Method ('gaussian', 'boxcar', 'savgol')

**Returns:** Smoothed array

---

## Visualizer

The `Visualizer` class provides visualization methods.

### Initialization

```python
viz = Visualizer(style='seaborn-v0_8-darkgrid')
```

**Parameters:**
- `style` (str): Matplotlib style

### Methods

#### `plot_firing_rates_by_region(firing_rates, top_n=20, figsize=None)`
Plot firing rates by brain region.

**Parameters:**
- `firing_rates` (DataFrame): Firing rates with region info
- `top_n` (int): Number of top regions
- `figsize` (tuple, optional): Figure size

**Returns:** Matplotlib figure

#### `plot_raster(spike_times, spike_clusters, cluster_ids=None, time_range=None, figsize=None)`
Create spike raster plot.

**Parameters:**
- `spike_times` (array): Spike times
- `spike_clusters` (array): Cluster IDs
- `cluster_ids` (list, optional): Specific clusters
- `time_range` (tuple, optional): Time range
- `figsize` (tuple, optional): Figure size

**Returns:** Matplotlib figure

#### `plot_psth(time_bins, psth, event_name='Event', figsize=None)`
Plot PSTH.

**Parameters:**
- `time_bins` (array): Time bin centers
- `psth` (array): Firing rates
- `event_name` (str): Event name
- `figsize` (tuple, optional): Figure size

**Returns:** Matplotlib figure

#### `plot_trial_activity(trial_rates, trial_types=None, figsize=None)`
Plot firing rates across trials.

**Parameters:**
- `trial_rates` (array): Rates per trial
- `trial_types` (array, optional): Trial type labels
- `figsize` (tuple, optional): Figure size

**Returns:** Matplotlib figure

#### `plot_correlation_matrix(correlation_matrix, labels=None, figsize=None)`
Plot correlation matrix.

**Parameters:**
- `correlation_matrix` (array): Correlation matrix
- `labels` (list, optional): Labels
- `figsize` (tuple, optional): Figure size

**Returns:** Matplotlib figure

#### `plot_behavioral_performance(trials, window_size=50, figsize=None)`
Plot behavioral performance.

**Parameters:**
- `trials` (DataFrame): Trial data
- `window_size` (int): Rolling window size
- `figsize` (tuple, optional): Figure size

**Returns:** Matplotlib figure

#### `plot_brain_region_distribution(clusters, top_n=20, figsize=None)`
Plot unit distribution across regions.

**Parameters:**
- `clusters` (DataFrame): Cluster information
- `top_n` (int): Number of top regions
- `figsize` (tuple, optional): Figure size

**Returns:** Matplotlib figure

#### `save_figure(fig, filename, dpi=300)`
Save figure to file.

**Parameters:**
- `fig`: Matplotlib figure
- `filename` (str): Output filename
- `dpi` (int): Resolution
