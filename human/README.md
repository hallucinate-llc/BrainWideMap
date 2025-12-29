# Human Mode: Translating Receptor/Circuit Hypotheses to Human Maps

Goal: take hypotheses generated in mouse and test their plausibility in humans using:
- PET receptor distributions
- transcriptomics (AHBA)
- functional imaging datasets (BIDS)

---

## Quick Start: Loading Human PET Receptor Maps

```python
from neurothera_map.human import load_human_pet_receptor_maps

# Load all receptors from offline fixture
receptor_map = load_human_pet_receptor_maps(
    "datasets/human_pet_receptor_fixture.csv"
)

# Or load specific receptors
receptor_map = load_human_pet_receptor_maps(
    "datasets/human_pet_receptor_fixture.csv",
    receptors=["5HT1a", "D1", "D2"]
)

# Access individual receptor maps
serotonin_1a = receptor_map.get("5HT1a")
print(f"Regions: {serotonin_1a.region_ids}")
print(f"Values: {serotonin_1a.values}")

# List all available receptors
print(receptor_map.receptor_names())
```

### Optional Integration: hansen_receptors

If you have the `hansen_receptors` package installed, the loader will detect it automatically:

```bash
pip install hansen_receptors
```

The base implementation works entirely offline using CSV fixtures and does not require
`hansen_receptors` to be installed.

---


## 1) Human “starter triad” (recommended MVP)

1) **PET receptor atlas** (`hansen_receptors`)
2) **JuSpace** PET/SPECT map library
3) **AHBA** transcriptomics (via `abagen`)

This triad gives you:
- receptor density priors
- transcriptomic support / cross-checks
- standard workflows for spatial comparisons

---

## 2) Human spaces and map formats

Supported targets:
- **MNI152 volumetric** maps (NIfTI)
- **fsaverage surface** maps (GIFTI/CIFTI where relevant)

Inter-space transforms / comparisons:
- Use `neuromaps` for reproducible comparisons and spatial nulls.

---

## 3) Human artifacts we will compute

### 3.1 ReceptorMaps (PET)
- per-receptor density maps
- parcellated versions for fast analysis
- uncertainty where available (inter-individual variability if provided)

### 3.2 Transcriptomic ReceptorMaps (AHBA)
- per-gene parcellated expression maps (careful normalization!)
- gene sets per neurotransmitter system

**Phase 2.2 MVP Implementation:**

The `neurothera_map.human.transcriptomics` module provides tools for loading AHBA transcriptomic data:

```python
from neurothera_map.human import load_transcriptomic_map_from_csv

# Load from offline parcellated CSV fixture
rm = load_transcriptomic_map_from_csv(
    "datasets/human_ahba_expression_fixture.csv",
    genes=["DRD1", "DRD2", "HTR1A", "HTR2A"]
)

# Access gene expression by symbol
drd1_map = rm.get("DRD1")
print(drd1_map.region_ids)  # Parcellated regions
print(drd1_map.values)      # Expression values
```

**Optional abagen integration** (requires separate installation):

```python
from neurothera_map.human import load_transcriptomic_map_with_abagen

try:
    # Load directly from AHBA via abagen (downloads data if needed)
    rm = load_transcriptomic_map_with_abagen(
        atlas="schaefer",
        n_parcels=400,
        genes=["DRD1", "DRD2"]
    )
except ImportError:
    # Fallback to offline fixture if abagen not installed
    rm = load_transcriptomic_map_from_csv("datasets/human_ahba_expression_fixture.csv")
```

Install abagen as optional dependency:
```bash
pip install abagen
```

**Features:**
- Offline CSV loader (no downloads required for unit tests)
- Optional `abagen` integration with soft dependency handling
- Returns `ReceptorMap` keyed by gene symbol
- Provenance metadata tracking
- Support for both long and wide format CSVs

### 3.3 ActivityMaps (BIDS imaging)
We provide a generic “BIDS → ActivityMap” interface:
- user supplies GLM contrasts or precomputed statistical maps
- we standardize into the map contract and cache

---

## 4) Translating mouse results to human: recommended strategy

Avoid pretending there’s a perfect region mapping.

Instead generate a **translation report**:
- Which receptor systems exist in both species (ortholog-based)
- Whether the human receptor density supports the proposed mechanism
- Whether human networks plausibly place the effect in similar systems (coarse motif-level)

Outputs:
- `HumanPlausibilityScore`
- “Where in human cortex/subcortex would this likely act?”
- Predicted imaging signature templates (if the user supplies a human dataset)

---

## 5) Pharmaco-fMRI / intervention datasets

We do not assume the existence of a single canonical open pharmaco-fMRI dataset for each drug.
Instead:
- build a robust BIDS ingestion interface
- allow users to plug in datasets from OpenNeuro or local sources
- optionally include example dataset IDs in a config file as “smoke tests”
