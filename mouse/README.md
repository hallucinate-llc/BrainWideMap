# Mouse Mode: From Brain-Wide Activity to Receptor/Circuit Hypotheses

Goal: produce hypotheses like  
"**Drug X** acting on **receptor Y** should modulate **circuit Z** in a way consistent with **IBL/Allen observed activity**."

---

## 1) Mouse "starter triad" (recommended MVP)

1) **IBL Brain-Wide Map** (activation) ✓
2) **Allen Mouse Brain Atlas** (receptor gene expression)
3) **Allen Mouse Connectivity** (projection graph) ✓ **IMPLEMENTED**

This triad is sufficient to build a working end-to-end pipeline.

---

## 2) Mouse artifacts we will compute

### 2.1 ActivityMaps (from IBL/Allen)
- For each task variable / condition:
  - region-level effect size
  - uncertainty (bootstrap across sessions/mice)
  - metadata describing preprocessing choices

### 2.2 ReceptorMaps (from ISH + ABC Atlas)
- RegionMap per receptor/transporter gene:
  - expression summary
  - optional cell-type enrichment overlays (MERFISH panels)

### 2.3 ConnectivityGraph (from Allen Connectivity + optional MouseLight) ✓ **IMPLEMENTED**
- Directed weighted adjacency matrix
- Optional decomposition into major systems:
  - cortico-striatal, thalamo-cortical, etc.

**Implementation**: See `neurothera_map/mouse/allen_connectivity.py`
- `AllenConnectivityLoader` class for flexible loading
- `load_allen_connectivity()` convenience function
- Supports region filtering, normalization, and thresholding
- Returns standardized `ConnectivityGraph` format

---

## 3) First analyses (build these before "fancy ML")

### A) Receptor enrichment on active nodes
Compute:
- `score(receptor) = Σ_regions ActivityWeight(region) * ReceptorLevel(region)`
Rank receptors to generate candidate mechanisms.

### B) Circuit propagation
Use a small menu of propagation operators:
- diffusion / random-walk
- shortest-path / k-hop neighborhoods
- controllability-inspired heuristics (optional)

### C) Drug-to-circuit prediction (mouse)
Given `DrugProfile(targets, affinities, sign)`:
- compute region-level "direct effect prior"
- propagate through connectivity to predict downstream modulation
- output predicted activation signature with uncertainty bands

---

## 4) Optional "CLARITY-adjacent" support

If you have cleared-brain (CLARITY/iDISCO) volumes:
- add an adapter that:
  - registers volume to CCF
  - extracts IEG maps (c-Fos, Arc) as `ActivityMap`
  - extracts immunostaining density as `ReceptorMap` (when antibodies exist)

This repo won't dictate your clearing pipeline; it only defines the **registration + map extraction contract**.

---

## 5) Allen Connectivity Loader Usage

### Basic Usage
```python
from neurothera_map.mouse import load_allen_connectivity

# Load connectivity for specific regions
connectivity = load_allen_connectivity(
    region_acronyms=['VISp', 'MOp', 'SSp'],
    normalize=True,
    threshold=0.01
)

print(f"Regions: {connectivity.region_ids}")
print(f"Adjacency shape: {connectivity.adjacency.shape}")
```

### Advanced Usage
```python
from neurothera_map.mouse.allen_connectivity import AllenConnectivityLoader

# Initialize loader with custom cache
loader = AllenConnectivityLoader(
    manifest_file='/path/to/cache/manifest.json',
    resolution=25
)

# Get available structures
structures = loader.get_available_structures()

# Load connectivity with structure IDs
connectivity = loader.load_connectivity_matrix(
    region_ids=[385, 993],  # VISp, MOp
    normalize=True
)
```

### Example Scripts
See `examples/allen_connectivity_example.py` for complete examples including:
- Loading connectivity for visual cortex
- Visualizing connectivity matrices
- Network analysis (hubs, in/out degree)

---

## 6) Practical notes

- Many mouse datasets already use Allen CCF indexing. Prefer to preserve those IDs rather than invent a new ontology.
- Always store "raw summary" and "analysis-ready normalized" versions.
- The Allen connectivity loader supports two modes:
  - **Offline stub** (deterministic, no network, no `allensdk`): set `BWM_ALLEN_OFFLINE=1` (this is what the default test suite uses).
  - **Real allensdk** (uses Allen cache/manifest): set `BWM_ALLEN_OFFLINE=0` and install `allensdk` (Python < 3.12; Python 3.11 recommended). First run may require network access; later runs use local cache.

For end-to-end validation of the real allensdk path, prefer:

```bash
bash scripts/run_e2e_allensdk.sh
```
