# Pipelines: Ingestion + Harmonization + Map-Making

This folder describes the pipeline architecture—**not** a single monolithic script.

---

## Design goals

- Deterministic, resumable pipelines (idempotent steps, cached outputs)
- Atlas-aware (mouse CCF; human MNI/fsaverage)
- Scale-friendly (chunked arrays, lazy loading, remote object stores)
- “Bring your own dataset” (especially for human pharmaco-fMRI)

---

## Pipeline stages (common pattern)

### Stage A — Fetch
- Input: dataset identifier + config (credentials, local cache dir)
- Output: *raw* files in a structured cache:
  - `data/raw/<dataset>/<version>/...`

### Stage B — Normalize
Convert raw modality formats into project-standard representations.
Examples:
- IBL: session tables → Parquet; spike times remain NWB/ALF references
- Allen ISH: expression grid summaries → Parquet + optional voxel Zarr
- PET receptor maps: NIfTI/surface → standardized space + metadata

Output:
- `data/normalized/<dataset>/<version>/...`

### Stage C — Register / Resample
- Mouse: register to Allen CCF ids (often already provided)
- Human: transform to MNI / fsaverage (use `neuromaps` as needed)

Output:
- `data/registered/<space>/<dataset>/<version>/...`

### Stage D — Derive Maps
Produce the canonical analysis objects:
- `ActivityMap` (region effects + uncertainty)
- `ReceptorMap` (receptor density/expression + uncertainty)
- `ConnectivityGraph` (edges + weights + sign if known)

Output:
- `data/derived/<object_type>/<space>/...`

### Stage E — QA + provenance
- checksums, shape checks, missingness
- provenance record: inputs + tool versions + parameters

---

## Key harmonization problems (and how we handle them)

### 1) Region naming
- Canonical: numeric region IDs (mouse CCF ids; human parcellation labels)
- Store acronyms as metadata only.

### 2) Units and modalities
- PET receptor maps can have differing scales; keep native units + apply z-scoring only in analysis layers.
- Gene expression:
  - keep raw summaries
  - derive “rank within cortex” for robust comparisons across donors

### 3) Multi-resolution mapping
Support:
- region-level (fast, robust, lower detail)
- voxel-level (expensive, high detail)
- surface-level (human cortex analyses)

---

## Suggested tools/libraries (implementation hints)

- Tables: `pyarrow`, `polars` or `pandas`
- Arrays: `xarray`, `zarr`
- Mouse atlas: Allen CCF volumes and structure trees
- Human transforms: `neuromaps` for map comparisons and space transforms
- BIDS: `pybids`, `nilearn`

---

## Output contract (what every derived artifact must include)

Every derived artifact must have:
- `space` (e.g., `mouse_ccf_2020`, `mni152_2mm`, `fsaverage`)
- `index` description (region ids or vertex/voxel coords)
- `value` + `uncertainty` (or explicit missingness)
- `provenance` (source dataset + version + script hash + parameters)
