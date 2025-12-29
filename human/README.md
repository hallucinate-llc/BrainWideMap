# Human Mode: Translating Receptor/Circuit Hypotheses to Human Maps

Goal: take hypotheses generated in mouse and test their plausibility in humans using:
- PET receptor distributions
- transcriptomics (AHBA)
- functional imaging datasets (BIDS)

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
