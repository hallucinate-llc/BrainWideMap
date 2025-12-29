# Drug Mode: Drug → Targets → Affinities → Mechanism Priors

**Status: ✅ Phase A Complete - Real drug DB ingestion skeleton with IUPHAR/ChEMBL adapters**

Goal: normalize "drug facts" into a standard `DrugProfile` that the rest of the toolkit can use.

---

## Implementation Overview

The drug ingestion system provides a unified interface to fetch drug-target-affinity data from multiple curated databases. It is designed to:

1. **Fetch** drug data from IUPHAR and ChEMBL
2. **Normalize** into a common `DrugProfile` schema
3. **Merge** data from multiple sources intelligently
4. **Track uncertainty** and evidence quality
5. **Cache** results for efficiency

### Architecture

```
DrugLoader (high-level API)
    ├── IUPHARAdapter (curated targets)
    └── ChEMBLAdapter (broad bioactivity)
         └── DrugProfile (unified output)
```

---

## 1) Sources (implemented)

### IUPHAR Guide to Pharmacology (high-confidence curated)
- Web services: https://www.guidetopharmacology.org/webServices.jsp
- **Implemented**: `drug/iuphar_adapter.py`

Why:
- curated target interactions
- mechanistic annotations (agonist/antagonist, etc.) are often clearer

### ChEMBL (broad bioactivity)
- API docs: https://www.ebi.ac.uk/chembl/api/data/docs
- Python client: https://github.com/chembl/chembl_webresource_client
- **Implemented**: `drug/chembl_adapter.py`

Why:
- many assays and compounds
- can estimate uncertainty / variability across studies

---

## 2) Standard DrugProfile schema

**Implemented**: `drug/schemas.py`

A `DrugProfile` includes:

- **identifiers**:
  - common name, synonyms
  - ChEMBL id, IUPHAR ligand id
  - InChI key, SMILES
- **interactions**: list of `TargetInteraction` with:
  - target id(s) (gene symbol + Uniprot)
  - interaction type: agonist / antagonist / reuptake inhibitor / etc.
  - potency measures (Ki/IC50/EC50) with units
  - evidence score (curation level, number of studies, consistency)
  - source database
- **metadata**:
  - drug class
  - mechanism summary
  - approval status
- **uncertainty model**:
  - distribution over potencies (multiple measurements)
  - evidence scores
  - provenance tracking

---

## 3) Usage

### Basic usage

```python
from drug import DrugLoader

# Initialize loader
loader = DrugLoader()

# Fetch drug profile (merges IUPHAR + ChEMBL by default)
profile = loader.load_drug_profile("caffeine")

print(f"Drug: {profile.common_name}")
print(f"Sources: {', '.join(profile.source_databases)}")

# Get primary targets
primary_targets = profile.get_primary_targets(top_n=3)
for target in primary_targets:
    print(f"  {target.target_gene_symbol}: {target.get_best_potency_nm():.1f} nM")
```

### Fetch from specific sources

```python
# IUPHAR only
iuphar_profile = loader.load_drug_profile("sertraline", use_chembl=False)

# ChEMBL only
chembl_profile = loader.load_drug_profile("sertraline", use_iuphar=False)

# Both, but don't merge
profiles = loader.load_drug_profile("sertraline", merge=False)
```

### Direct adapter usage

```python
from drug import IUPHARAdapter, ChEMBLAdapter

# Use adapters directly
iuphar = IUPHARAdapter()
profile = iuphar.fetch_drug_profile("caffeine")

chembl = ChEMBLAdapter()
profile = chembl.fetch_drug_profile("caffeine")
```

---

## 4) Why uncertainty matters

Two drugs with identical "top targets" can differ dramatically in:
- off-target profile
- partial vs full agonism
- active metabolites
- brain penetration

Therefore:
- the pipeline preserves evidence provenance (source DB, pubmed IDs)
- the model propagates uncertainty through:
  - multiple potency measurements per target
  - evidence scores based on consistency and number of studies
  - metadata tracking merge operations

---

## 5) Files

### Core modules
- `drug/__init__.py` - Package exports
- `drug/schemas.py` - Data models (`DrugProfile`, `TargetInteraction`, `PotencyMeasure`)
- `drug/iuphar_adapter.py` - IUPHAR Guide to Pharmacology adapter
- `drug/chembl_adapter.py` - ChEMBL database adapter
- `drug/drug_loader.py` - High-level loader with merging logic

### Examples and tests
- `examples/drug_ingestion_example.py` - Usage examples (caffeine, SSRIs)
- `tests/test_drug_ingestion.py` - Unit tests

---

## 6) Examples implemented

### Caffeine
- Primary mechanism: adenosine receptor antagonism (A1/A2A)
- Fetches all targets with affinities
- Shows evidence quality scores

### SSRIs (e.g., sertraline)
- Primary mechanism: SERT (SLC6A4) inhibition
- Shows off-target profile
- Compares IUPHAR vs ChEMBL data

### Multi-source comparison
- Demonstrates merging IUPHAR + ChEMBL
- Shows how evidence is combined
- Tracks provenance

---

## 7) Next steps (future phases)

- [ ] Integration with receptor distribution maps (mouse/human modules)
- [ ] Propagation of drug effects through connectivity graphs
- [ ] Uncertainty quantification in circuit-level predictions
- [ ] AlphaFold binding prediction validation loop
- [ ] Brain penetration / PK modeling
- [ ] Active metabolite handling

---

## 8) Testing

Run tests:
```bash
pytest tests/test_drug_ingestion.py -v
```

Run examples:
```bash
python examples/drug_ingestion_example.py
```

All tests passing ✅ (8/8)
