# Docs

## Start here

If you want to use this repo to analyze how **chemicals interact with the brain**, follow the end-to-end walkthrough:

- `docs/WORKFLOW.md`

If you want the reference API surface:

- `docs/API.md`

If you want the deterministic vs live/E2E test story:

- `DEVELOPMENT.md`
- `TEST_COVERAGE.md`

---

# Implementation Plan (Comprehensive)

This document is written to be “agent-ready”: it’s an executable plan for building the toolkit with minimal ambiguity.

---

## Phase 0 — Project foundations (week 0–1)

### Deliverables
- [x] Repo skeleton (this)
- [x] `core/` package scaffold + packaging config
- [x] **Unified schema** for exchanged artifacts:
  - `RegionMap`, `ReceptorMap`, `ActivityMap`, `ConnectivityGraph`, `DrugProfile`
  - Implemented in `neurothera_map/core/types.py`
- [~] Data provenance + caching conventions
  - Implemented ad-hoc via `provenance` dicts on core types; still needs a single shared convention doc
- [~] Minimum CI: lint + typecheck + unit tests
  - Unit tests exist and pass locally; CI wiring is still TBD

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
- [~] IBL Brain-Wide Map (via ONE API and/or AWS mirror)
  - Implemented in the `brainwidemap/` package; NeuroThera-level "task → ActivityMap" is still evolving
- [~] Allen Mouse Brain Atlas expression summaries for a panel of receptors
  - MVP implemented as an *offline CSV panel loader* in `neurothera_map/mouse/expression.py`
  - Direct Allen API ingestion not yet implemented
- [x] Allen Mouse Connectivity Atlas projection matrices (region-level)
  - Implemented in `neurothera_map/mouse/allen_connectivity.py`

### 1.2 Harmonization
- [ ] Region ontology / acronym normalization (Allen CCF ids)
- [ ] “Experiment → region map” generation:
  - for each dataset, produce `ActivityMap(region_id -> effect_size)` + uncertainty

### 1.3 Analytic primitives
- [x] Receptor enrichment in circuit nodes:
  - region activity importance weights × receptor expression → candidate receptor list
- [x] Graph propagation:
  - diffusion / random-walk / controllability approximations on `ConnectivityGraph`
- [x] Simple prediction:
  - `PredictedActivation = f(DrugProfile ⊙ ReceptorMap, ConnectivityGraph)`
  - Implemented as `predict_mouse_effects()` in `neurothera_map/mouse/mvp_predict.py`

### 1.4 Validation hooks (mouse)
- [ ] Consistency checks:
  - known neuromodulatory systems should score high in known targets (sanity tests)
- [ ] “Leave-one-region-out” and “leave-one-session-out” robustness tests

---

## Parallel workstreams (agent-friendly)

This plan is designed to be implemented via independent PRs that can run in parallel.

Suggested split:
- **Mouse**: Allen expression API ingestion + region normalization + robustness tests
- **Human**: PET receptor maps loader (optional deps) + AHBA transcriptomics loader (optional deps)
- **Human activation**: BIDS/parcellated-map ingestion interface + smoke-test dataset config
- **Drug**: unify `build_drug_profile()` to optionally use the richer `/drug` ingestion layer
- **Validation**: schema validators + dummy mutual-loss loop (no real AlphaFold required)

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
2) `mouse_pred = predict_mouse_effects(drug_profile, receptor_map, connectivity_graph)`  
3) `human_pred = translate_to_human(mouse_pred)`  
4) `validate_against_pet_and_fmri(human_pred)`  
5) send `human_pred` constraints back to AlphaFold package

…without hand-editing file paths or special-casing datasets.
