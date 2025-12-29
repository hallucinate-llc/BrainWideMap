"""
Core schemas for drug-target-affinity data.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum


class InteractionType(Enum):
    """Types of drug-target interactions."""
    AGONIST = "agonist"
    ANTAGONIST = "antagonist"
    PARTIAL_AGONIST = "partial_agonist"
    INVERSE_AGONIST = "inverse_agonist"
    ALLOSTERIC_MODULATOR = "allosteric_modulator"
    INHIBITOR = "inhibitor"
    BLOCKER = "blocker"
    ACTIVATOR = "activator"
    UNKNOWN = "unknown"


class PotencyUnit(Enum):
    """Units for potency measurements."""
    MOLAR = "M"
    MILLIMOLAR = "mM"
    MICROMOLAR = "uM"
    NANOMOLAR = "nM"
    PICOMOLAR = "pM"
    UNKNOWN = "unknown"


@dataclass
class PotencyMeasure:
    """A single potency measurement (Ki, IC50, EC50, etc.)."""
    value: float
    unit: PotencyUnit
    measure_type: str  # "Ki", "IC50", "EC50", "Kd", etc.
    assay_description: Optional[str] = None
    pubmed_id: Optional[str] = None
    
    def to_nanomolar(self) -> Optional[float]:
        """Convert to nanomolar for standardization."""
        conversions = {
            PotencyUnit.MOLAR: 1e9,
            PotencyUnit.MILLIMOLAR: 1e6,
            PotencyUnit.MICROMOLAR: 1e3,
            PotencyUnit.NANOMOLAR: 1.0,
            PotencyUnit.PICOMOLAR: 1e-3,
        }
        if self.unit in conversions:
            return self.value * conversions[self.unit]
        return None


@dataclass
class TargetInteraction:
    """A drug-target interaction with mechanism and potency."""
    target_gene_symbol: str
    target_uniprot_id: Optional[str] = None
    target_name: Optional[str] = None
    interaction_type: InteractionType = InteractionType.UNKNOWN
    potency_measures: List[PotencyMeasure] = field(default_factory=list)
    evidence_score: Optional[float] = None
    source_database: Optional[str] = None
    
    def get_best_potency_nm(self) -> Optional[float]:
        """Get the most potent (lowest) value in nanomolar."""
        potencies = [p.to_nanomolar() for p in self.potency_measures]
        potencies = [p for p in potencies if p is not None]
        return min(potencies) if potencies else None


@dataclass
class DrugProfile:
    """
    Complete drug profile with identifiers, targets, and metadata.
    
    This is the standard output format for all drug database adapters.
    """
    # Identifiers
    common_name: str
    synonyms: List[str] = field(default_factory=list)
    chembl_id: Optional[str] = None
    iuphar_ligand_id: Optional[int] = None
    inchi_key: Optional[str] = None
    smiles: Optional[str] = None
    
    # Target interactions
    interactions: List[TargetInteraction] = field(default_factory=list)
    
    # Metadata
    drug_class: Optional[str] = None
    mechanism_summary: Optional[str] = None
    is_approved: bool = False
    
    # Provenance
    source_databases: List[str] = field(default_factory=list)
    last_updated: Optional[str] = None
    
    # Uncertainty tracking
    uncertainty_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_primary_targets(self, top_n: int = 3) -> List[TargetInteraction]:
        """Get the most potent target interactions."""
        sorted_interactions = sorted(
            self.interactions,
            key=lambda x: x.get_best_potency_nm() or float('inf')
        )
        return sorted_interactions[:top_n]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'common_name': self.common_name,
            'synonyms': self.synonyms,
            'chembl_id': self.chembl_id,
            'iuphar_ligand_id': self.iuphar_ligand_id,
            'inchi_key': self.inchi_key,
            'smiles': self.smiles,
            'interactions': [
                {
                    'target_gene_symbol': i.target_gene_symbol,
                    'target_uniprot_id': i.target_uniprot_id,
                    'target_name': i.target_name,
                    'interaction_type': i.interaction_type.value,
                    'potency_measures': [
                        {
                            'value': p.value,
                            'unit': p.unit.value,
                            'measure_type': p.measure_type,
                            'assay_description': p.assay_description,
                            'pubmed_id': p.pubmed_id,
                        }
                        for p in i.potency_measures
                    ],
                    'evidence_score': i.evidence_score,
                    'source_database': i.source_database,
                }
                for i in self.interactions
            ],
            'drug_class': self.drug_class,
            'mechanism_summary': self.mechanism_summary,
            'is_approved': self.is_approved,
            'source_databases': self.source_databases,
            'last_updated': self.last_updated,
            'uncertainty_metadata': self.uncertainty_metadata,
        }
