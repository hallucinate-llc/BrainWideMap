# Validation: Mutual Constraints Between AlphaFold Package and NeuroThera-Map

This repo is designed to work in tandem with a separate structural-prediction package (AlphaFold-based).
The two packages should be runnable on separate machines and exchange *structured messages*.

---

## 1) Why “mutual validation” instead of one-way validation?

- AlphaFold/docking can generate structurally plausible bindings that are functionally irrelevant.
- Brain-map predictions can find circuit-relevant receptors that have no feasible binding pocket for your ligand.

Mutual validation makes both models better:
- **Structural model** learns to prioritize functionally meaningful targets.
- **Functional model** learns to avoid biologically implausible target engagements.

---

## 2) Exchange artifacts (high level)

### AlphaFold → NeuroThera-Map
- candidate targets (protein identifiers)
- predicted binding energies / affinities (with uncertainty)
- binding-site annotations (residue ranges / pocket descriptors)
- confidence metrics (pLDDT-like or model-specific)

### NeuroThera-Map → AlphaFold
- ranked receptor targets prioritized by:
  - circuit relevance (from activity + connectivity)
  - species relevance (mouse vs human plausibility)
  - receptor availability (PET/gene expression)
- functional constraints:
  - “If this target is true, expect this network signature”
- validation datasets:
  - map IDs / references for observed effect signatures

---

## 3) Mutual validation losses (proposed)

These are *design targets*; implement them incrementally.

### Loss A — Target ranking agreement
Encourage AlphaFold target ranking to align with circuit relevance priors:
- `L_rank = ranking_loss(AlphaFoldTargets, NeuroTheraTargetPrior)`

### Loss B — Effect-size consistency
If AlphaFold predicts strong binding to a receptor:
- NeuroThera should predict stronger modulation in regions rich in that receptor.
- `L_effect = distance(predicted_effect_map, receptor_density_weighted_map)`

### Loss C — Cross-species coherence
If a target is mouse-only (no clear ortholog / expression absent in human):
- penalize claims of human therapeutic relevance unless supported by human receptor maps.
- `L_xspecies = penalty(inconsistent_species_claims)`

### Loss D — Empirical alignment (when you have intervention datasets)
When you have pharmaco-fMRI / EEG / behavior readouts:
- `L_empirical = distance(predicted_signature, observed_signature)`

---

## 4) What “validation” can mean without intervention datasets

Even without direct drug-administration data, you can validate via:
- receptor distribution plausibility (PET vs transcriptomics agreement)
- known “system sanity checks” (e.g., serotonergic targets enriched where expected)
- network propagation sanity (effects don’t jump to disconnected systems without support)

---

## 5) Output: a ValidationReport

A standard output object that includes:
- target list with confidence and evidence links
- predicted effect signatures (mouse + human)
- the loss components with interpretable diagnostics
- recommendations for next experiments (e.g., which receptor antagonists to use as controls)
