"""
IUPHAR Guide to Pharmacology adapter.

Fetches curated drug-target interactions from IUPHAR web services.
API documentation: https://www.guidetopharmacology.org/webServices.jsp
"""

import requests
from typing import Optional, List
from datetime import datetime

from .schemas import (
    DrugProfile,
    TargetInteraction,
    PotencyMeasure,
    InteractionType,
    PotencyUnit,
)


class IUPHARAdapter:
    """Adapter for IUPHAR Guide to Pharmacology database."""
    
    BASE_URL = "https://www.guidetopharmacology.org/services"
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize IUPHAR adapter.
        
        Args:
            cache_dir: Optional directory for caching API responses
        """
        self.cache_dir = cache_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NeuroThera-Map/1.0 (Research)',
        })
    
    def search_ligand(self, drug_name: str) -> List[dict]:
        """
        Search for ligands by name.
        
        Args:
            drug_name: Common name or synonym
            
        Returns:
            List of ligand records
        """
        url = f"{self.BASE_URL}/ligands"
        params = {'name': drug_name}
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"IUPHAR API error for {drug_name}: {e}")
            return []
        except Exception as e:
            print(f"IUPHAR API error for {drug_name}: {e}")
            return []
    
    def get_ligand_interactions(self, ligand_id: int) -> List[dict]:
        """
        Get target interactions for a ligand.
        
        Args:
            ligand_id: IUPHAR ligand ID
            
        Returns:
            List of interaction records
        """
        url = f"{self.BASE_URL}/ligands/{ligand_id}/interactions"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"IUPHAR API error for ligand {ligand_id}: {e}")
            return []
    
    def _parse_interaction_type(self, interaction_str: str) -> InteractionType:
        """Parse IUPHAR interaction type string."""
        interaction_lower = interaction_str.lower()
        
        # Check antagonist first (before agonist) since "antagonist" contains "agonist"
        if 'antagonist' in interaction_lower:
            return InteractionType.ANTAGONIST
        elif 'agonist' in interaction_lower:
            if 'partial' in interaction_lower:
                return InteractionType.PARTIAL_AGONIST
            elif 'inverse' in interaction_lower:
                return InteractionType.INVERSE_AGONIST
            return InteractionType.AGONIST
        elif 'inhibitor' in interaction_lower or 'inhibit' in interaction_lower:
            return InteractionType.INHIBITOR
        elif 'blocker' in interaction_lower or 'block' in interaction_lower:
            return InteractionType.BLOCKER
        elif 'modulator' in interaction_lower:
            return InteractionType.ALLOSTERIC_MODULATOR
        
        return InteractionType.UNKNOWN
    
    def _parse_potency_unit(self, unit_str: Optional[str]) -> PotencyUnit:
        """Parse potency unit string."""
        if not unit_str:
            return PotencyUnit.UNKNOWN
        
        unit_lower = unit_str.lower()
        # Handle both 'u' and 'μ' for micro
        if 'nm' in unit_lower or 'nanomolar' in unit_lower:
            return PotencyUnit.NANOMOLAR
        elif 'um' in unit_lower or 'micromolar' in unit_lower or 'μm' in unit_lower:
            return PotencyUnit.MICROMOLAR
        elif 'mm' in unit_lower or 'millimolar' in unit_lower:
            return PotencyUnit.MILLIMOLAR
        elif 'pm' in unit_lower or 'picomolar' in unit_lower:
            return PotencyUnit.PICOMOLAR
        
        return PotencyUnit.UNKNOWN
    
    def fetch_drug_profile(self, drug_name: str) -> Optional[DrugProfile]:
        """
        Fetch complete drug profile from IUPHAR.
        
        Args:
            drug_name: Common drug name
            
        Returns:
            DrugProfile or None if not found
        """
        # Search for ligand
        ligands = self.search_ligand(drug_name)
        if not ligands:
            return None
        
        # Use first match (could be improved with disambiguation)
        ligand = ligands[0]
        ligand_id = ligand.get('ligandId')
        
        # Get interactions
        interactions_data = self.get_ligand_interactions(ligand_id)
        
        # Parse interactions
        interactions = []
        for int_data in interactions_data:
            target_gene = int_data.get('targetGeneSymbol')
            if not target_gene:
                continue
            
            # Parse potency measures
            potency_measures = []
            for measure_type in ['affinity', 'IC50', 'EC50', 'Ki', 'Kd']:
                value = int_data.get(measure_type)
                unit = int_data.get(f'{measure_type}Unit')
                if value is not None:
                    potency_measures.append(PotencyMeasure(
                        value=float(value),
                        unit=self._parse_potency_unit(unit),
                        measure_type=measure_type,
                        assay_description=int_data.get('assayDescription'),
                        pubmed_id=int_data.get('pubmedId'),
                    ))
            
            interaction = TargetInteraction(
                target_gene_symbol=target_gene,
                target_uniprot_id=int_data.get('targetUniprotId'),
                target_name=int_data.get('targetName'),
                interaction_type=self._parse_interaction_type(
                    int_data.get('interactionType', '')
                ),
                potency_measures=potency_measures,
                evidence_score=None,  # IUPHAR doesn't provide numerical scores
                source_database='IUPHAR',
            )
            interactions.append(interaction)
        
        # Build DrugProfile
        profile = DrugProfile(
            common_name=ligand.get('name', drug_name),
            synonyms=ligand.get('synonyms', '').split('|') if ligand.get('synonyms') else [],
            iuphar_ligand_id=ligand_id,
            inchi_key=ligand.get('inchiKey'),
            smiles=ligand.get('smiles'),
            interactions=interactions,
            drug_class=ligand.get('type'),
            mechanism_summary=None,
            is_approved=ligand.get('approved', False),
            source_databases=['IUPHAR'],
            last_updated=datetime.now().isoformat(),
        )
        
        return profile
