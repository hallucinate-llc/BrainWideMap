# Orchestration: Running Two Packages on Separate Machines

We assume two compute roles:

1) **Structure worker** (AlphaFold package)
2) **Neuro worker** (this repo: data integration + prediction + validation)

They communicate over a *transport-agnostic* message format.

---

## 1) Minimal topology

### Option A — File drop (simplest)
- Shared folder (NFS/S3/minio)
- Each side writes JSON + binary references
- A small “watcher” process consumes messages

Pros: easiest to debug  
Cons: slower, eventual consistency issues

### Option B — HTTP service
- Each worker exposes a small endpoint:
  - `POST /submit_prediction`
  - `POST /submit_constraints`

Pros: clean, scalable  
Cons: needs ops/security

### Option C — Message queue
- Redis streams / RabbitMQ / Kafka

Pros: robust and scalable  
Cons: more infrastructure

MVP recommendation: **Option A** with a schema validator.

---

## 2) Exchange schema (suggested)

All messages must include:
- `schema_version`
- `run_id`
- `timestamp`
- `species` (mouse/human/both)
- `payload_type` (target_predictions, circuit_constraints, validation_report)
- `payload` (JSON)
- `blobs` (optional): list of content-addressed binary files (Zarr, NIfTI, Parquet)

---

## 3) How “mutual validation loss” becomes feedback

### AlphaFold side can use:
- `NeuroTheraTargetPrior` as a reweighting prior during candidate selection
- `L_empirical` and `L_effect` as auxiliary losses during fine-tuning / selection

### NeuroThera side can use:
- AlphaFold predicted affinities to update `DrugProfile` uncertainty distribution
- pocket plausibility to prune receptor hypotheses

---

## 4) Reproducibility & caching

Both machines should:
- pin tool versions
- store every run artifact under `runs/<run_id>/...`
- store dataset cache separately from run outputs

---

## 5) Security note

If you ever move beyond public datasets:
- avoid pushing raw human data across machines
- exchange only derived maps and summary statistics where allowed
