# Drug Mode: Drug → Targets → Affinities → Mechanism Priors

Goal: normalize “drug facts” into a standard `DrugProfile` that the rest of the toolkit can use.

---

## 1) Sources (recommended)

### IUPHAR Guide to Pharmacology (high-confidence curated)
- Web services: https://www.guidetopharmacology.org/webServices.jsp

Why:
- curated target interactions
- mechanistic annotations (agonist/antagonist, etc.) are often clearer

### ChEMBL (broad bioactivity)
- API docs: https://www.ebi.ac.uk/chembl/api/data/docs
- Python client: https://github.com/chembl/chembl_webresource_client

Why:
- many assays and compounds
- can estimate uncertainty / variability across studies

---

## 2) Standard DrugProfile schema (conceptual)

A `DrugProfile` should include:

- identifiers:
  - common name, synonyms
  - ChEMBL id (if available)
- interactions: list of
  - target id(s) (gene symbol + Uniprot if possible)
  - interaction type: agonist / antagonist / reuptake inhibitor / etc.
  - potency estimate (Ki/IC50/EC50), unit, assay context
  - evidence score (curation level, number of studies, consistency)
- pharmacokinetic metadata (optional; often not available openly)
- uncertainty model:
  - distribution over potencies
  - distribution over off-target likelihood

---

## 3) Why uncertainty matters

Two drugs with identical “top targets” can differ dramatically in:
- off-target profile
- partial vs full agonism
- active metabolites
- brain penetration

Therefore:
- the pipeline must preserve evidence provenance
- the model must propagate uncertainty into predicted circuit effects

---

## 4) MVP examples

- **Caffeine**:
  - primary mechanism is antagonism at adenosine receptors (A1/A2A) (store as target hypotheses)
- **SSRIs**:
  - primary mechanism is SERT (SLC6A4) inhibition; downstream receptor adaptations are secondary hypotheses

The tool should allow you to expand beyond these “headline” targets automatically using ChEMBL evidence.
