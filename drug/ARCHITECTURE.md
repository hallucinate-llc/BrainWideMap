# Drug Module Architecture

## Overview

The drug module provides a unified interface for fetching drug-target-affinity data from multiple curated pharmacological databases.

## Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        User Code                            │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
           ┌────────────────────────┐
           │     DrugLoader         │  High-level API
           │  (drug_loader.py)      │  - load_drug_profile()
           └────────┬───────────────┘  - merge strategies
                    │                  - caching
         ┌──────────┴──────────┐
         │                     │
         ▼                     ▼
┌─────────────────┐   ┌─────────────────┐
│ IUPHARAdapter   │   │ ChEMBLAdapter   │  Database adapters
│ (iuphar_.py)    │   │ (chembl_.py)    │  - API clients
└────────┬────────┘   └────────┬────────┘  - response parsing
         │                     │            - evidence scoring
         │                     │
         └──────────┬──────────┘
                    │
                    ▼
         ┌────────────────────┐
         │   DrugProfile      │  Unified schema
         │   (schemas.py)     │  - identifiers
         │                    │  - interactions
         │  TargetInteraction │  - potencies
         │  PotencyMeasure    │  - metadata
         └────────────────────┘
```

## Data Flow

```
1. User Request
   └─> DrugLoader.load_drug_profile("caffeine")

2. Parallel Fetching
   ├─> IUPHARAdapter.fetch_drug_profile("caffeine")
   │   ├─> Search ligand by name
   │   ├─> Get interactions for ligand
   │   └─> Parse to DrugProfile
   │
   └─> ChEMBLAdapter.fetch_drug_profile("caffeine")
       ├─> Search molecule by name
       ├─> Get activities for molecule
       ├─> Aggregate by target
       ├─> Calculate evidence scores
       └─> Parse to DrugProfile

3. Intelligent Merging
   └─> DrugLoader._merge_profiles([iuphar, chembl])
       ├─> Deduplicate targets by gene symbol
       ├─> Prefer higher-quality data (configurable)
       ├─> Combine potency measurements
       └─> Track provenance

4. Result
   └─> Unified DrugProfile with complete metadata
```

## Schema Relationships

```
DrugProfile
├─ common_name: str
├─ identifiers: ChEMBL ID, IUPHAR ID, InChI, SMILES
├─ interactions: List[TargetInteraction]
│  └─ TargetInteraction
│     ├─ target_gene_symbol: str
│     ├─ target_uniprot_id: str
│     ├─ interaction_type: InteractionType (enum)
│     ├─ potency_measures: List[PotencyMeasure]
│     │  └─ PotencyMeasure
│     │     ├─ value: float
│     │     ├─ unit: PotencyUnit (enum)
│     │     ├─ measure_type: str (Ki, IC50, EC50)
│     │     └─ to_nanomolar() -> float
│     ├─ evidence_score: float (0-1)
│     └─ source_database: str
├─ metadata: drug_class, mechanism, approval
└─ uncertainty_metadata: Dict[str, Any]
```

## API Layers

### Layer 1: Direct Adapters
```python
from drug import IUPHARAdapter, ChEMBLAdapter

# Direct database access
iuphar = IUPHARAdapter()
profile = iuphar.fetch_drug_profile("caffeine")
```

**Use when**: You need specific database features or custom processing

### Layer 2: Unified Loader
```python
from drug import DrugLoader

# Multi-source with merging
loader = DrugLoader()
profile = loader.load_drug_profile("caffeine")
```

**Use when**: You want best-of-both-worlds with minimal code

### Layer 3: Schema-Only
```python
from drug.schemas import DrugProfile, TargetInteraction

# Manual construction
profile = DrugProfile(
    common_name="Custom Drug",
    interactions=[...]
)
```

**Use when**: Building from custom data sources

## Extension Points

### Add New Database
```python
# 1. Create adapter
class NewDBAdapter:
    def fetch_drug_profile(self, drug_name: str) -> DrugProfile:
        # Fetch and parse
        return profile

# 2. Register in DrugLoader
class DrugLoader:
    def __init__(self):
        self.newdb = NewDBAdapter()
    
    def load_drug_profile(self, drug_name, use_newdb=True):
        # Add to fetching logic
```

### Add Interaction Type
```python
# In schemas.py
class InteractionType(Enum):
    # ... existing types
    NEW_TYPE = "new_type"

# In adapters
def _parse_interaction_type(self, type_str):
    # Add parsing logic
```

### Custom Merging Strategy
```python
loader = DrugLoader(prefer_iuphar=False)  # Prefer ChEMBL

# Or override
def custom_merge(profiles):
    # Custom logic
    return merged_profile

loader._merge_profiles = custom_merge
```

## Error Handling

```
API Failures
└─> Try alternative source (if available)
    └─> Return None (graceful degradation)

Parsing Errors
└─> Log warning, skip malformed data
    └─> Continue with valid data

Cache Errors
└─> Fall back to direct API fetch
    └─> Continue operation
```

## Performance Characteristics

- **First fetch**: 2-5 seconds (API latency)
- **Cached fetch**: <100ms (JSON deserialization)
- **Memory**: ~1-5 KB per DrugProfile
- **Scalability**: Independent per-drug (embarrassingly parallel)

## Future Extensions

1. **Additional Sources**
   - DrugBank
   - PubChem
   - BindingDB

2. **Enhanced Features**
   - Batch fetching
   - Async API calls
   - Background cache updates
   - Confidence intervals on potencies

3. **Integration**
   - Receptor expression maps
   - Connectivity graphs
   - AlphaFold binding predictions
