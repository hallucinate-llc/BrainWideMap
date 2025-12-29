# Implementation Plan (Comprehensive)

This document is written to be “agent-ready”: it’s an executable plan for building the toolkit with minimal ambiguity.

---

## Phase 0 — Project foundations (week 0–1)

### Deliverables
- [ ] Repo skeleton (this)
- [ ] `core/` package scaffold + packaging config
- [ ] **Unified schema** for exchanged artifacts:
  - `RegionMap`, `ReceptorMap`, `ActivityMap`, `ConnectivityGraph`, `DrugProfile`
- [ ] Data provenance + caching conventions
- [ ] Minimum CI: lint + typecheck + unit tests

### Decisions to lock early
- Canonical mouse atlas space: **Allen CCF (2020)**.
- Canonical human spaces: **MNI152 volume** and **fsaverage (surface)** (fsLR optional).
- Primary storage:
  - “tables”: Parquet
  - “dense arrays”: Zarr (chunked)
  - “raw neurophys”: NWB (or link-out to NWB)

---

## Phase 1 — Mouse integration MVP (week 1–4)

Goal: From mouse brain-wide activity → receptor hypotheses → circuit propagation.

### 1.1 Data ingestion connectors (MVP)
- [ ] IBL Brain-Wide Map (via ONE API and/or AWS mirror)
- [ ] Allen Mouse Brain Atlas expression summaries for a panel of receptors
- [ ] Allen Mouse Connectivity Atlas projection matrices (region-level)

### 1.2 Harmonization
- [ ] Region ontology / acronym normalization (Allen CCF ids)
- [ ] “Experiment → region map” generation:
  - for each dataset, produce `ActivityMap(region_id -> effect_size)` + uncertainty

### 1.3 Analytic primitives
- [ ] Receptor enrichment in circuit nodes:
  - region activity importance weights × receptor expression → candidate receptor list
- [ ] Graph propagation:
  - diffusion / random-walk / controllability approximations on `ConnectivityGraph`
- [ ] Simple prediction:
  - `PredictedActivation = f(DrugProfile ⊙ ReceptorMap, ConnectivityGraph)`

### 1.4 Validation hooks (mouse)
- [ ] Consistency checks:
  - known neuromodulatory systems should score high in known targets (sanity tests)
- [ ] “Leave-one-region-out” and “leave-one-session-out” robustness tests

---

## Phase 2 — Human translation MVP (week 4–8)

Goal: map the same receptor/circuit hypotheses into human receptor distributions + imaging spaces.

### 2.1 Human receptor maps
- [ ] PET receptor maps (19 receptors/transporters) via `hansen_receptors`
- [ ] JuSpace maps (PET/SPECT collection)

### 2.2 Human transcriptomics
- [ ] Allen Human Brain Atlas microarray via `abagen`
- [ ] Provide “parcellate transcriptomics to atlas” pipeline

### 2.3 Human activation datasets (pilot)
- [ ] Ingest *at least one* BIDS dataset from OpenNeuro as a working example
- [ ] Build generic BIDS ingestion interface so users can plug in their own pharmaco-fMRI datasets

### 2.4 Cross-species alignment (pragmatic)
We do **not** assume a perfect mouse↔human region correspondence.
Instead, we use **multiple weak links**:
- gene ortholog mapping (mouse receptor genes ↔ human orthologs)
- receptor system homology (e.g., SLC6A4 vs 5HT families)
- network-level alignment using coarse motifs (cortico-striatal-thalamic loops, etc.)

Deliverable:
- [ ] “Translation report” summarizing which conclusions are mouse-only vs plausible in human.

---

## Phase 3 — Drug mode (week 6–10)

Goal: accept a compound name and produce a standardized DrugProfile + predicted effects.

### 3.1 Drug databases
- [ ] IUPHAR Guide to Pharmacology (high-confidence curated targets)
- [ ] ChEMBL (broad bioactivity evidence)

### 3.2 Normalization
- [ ] Target identifier normalization: gene symbol, Uniprot, receptor family naming
- [ ] Affinity unit normalization: Ki/IC50/EC50 conversions where defensible, else store as-is with metadata
- [ ] Mechanism tagging: agonist/antagonist/partial, transporter inhibitor, etc.

### 3.3 Uncertainty-first interface
- Treat DrugProfile as a *distribution*, not a point estimate:
  - evidence score per interaction
  - range/CI if available
  - provenance for each claim

---

## Phase 4 — AlphaFold mutual validation (week 8–14)

Goal: make it possible to *train/validate* both models against each other without requiring co-location.

Deliverables:
- [ ] Exchange schema + validators
- [ ] Mutual loss definitions (see `validation/README.md`)
- [ ] Example loop that runs locally with dummy data, then can be swapped to real AlphaFold outputs

---

## Phase 5 — Scaling and polish (week 12+)

- [ ] “Dataset registry” CLI:
  - `neurothera datasets list`
  - `neurothera datasets fetch <dataset>`
- [ ] Reproducible pipeline runner (e.g., `prefect`, `dagster`, or simple Makefile)
- [ ] Caching and chunking strategy documented for 10TB+ datasets
- [ ] Export report templates (Markdown + JSON) for results

---

## Definition of Done (MVP)

You can run:

1) `drug_profile = build_drug_profile("caffeine")`  
2) `mouse_pred = predict_mouse_effects(drug_profile, task="decision-making")`  
3) `human_pred = translate_to_human(mouse_pred)`  
4) `validate_against_pet_and_fmri(human_pred)`  
5) send `human_pred` constraints back to AlphaFold package

…without hand-editing file paths or special-casing datasets.
