"""
ChEMBL database adapter.

Fetches broad bioactivity data from ChEMBL.
API documentation: https://www.ebi.ac.uk/chembl/api/data/docs
"""

import requests
from typing import Optional, List, Dict, Any
from datetime import datetime
import statistics

from .schemas import (
    DrugProfile,
    TargetInteraction,
    PotencyMeasure,
    InteractionType,
    PotencyUnit,
)


class ChEMBLAdapter:
    """Adapter for ChEMBL bioactivity database."""
    
    BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize ChEMBL adapter.
        
        Args:
            cache_dir: Optional directory for caching API responses
        """
        self.cache_dir = cache_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'NeuroThera-Map/1.0 (Research)',
            'Accept': 'application/json',
        })
    
    def search_molecule(self, drug_name: str) -> List[dict]:
        """
        Search for molecules by name.
        
        Args:
            drug_name: Common name or synonym
            
        Returns:
            List of molecule records
        """
        url = f"{self.BASE_URL}/molecule/search.json"
        params = {'q': drug_name, 'limit': 10}
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('molecules', [])
        except requests.RequestException as e:
            print(f"ChEMBL API error for {drug_name}: {e}")
            return []
    
    def get_molecule_activities(self, chembl_id: str, limit: int = 1000) -> List[dict]:
        """
        Get bioactivity data for a molecule.
        
        Args:
            chembl_id: ChEMBL molecule ID
            limit: Maximum number of activities to retrieve
            
        Returns:
            List of activity records
        """
        url = f"{self.BASE_URL}/activity.json"
        params = {
            'molecule_chembl_id': chembl_id,
            'limit': limit,
        }
        
        try:
            response = self.session.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data.get('activities', [])
        except requests.RequestException as e:
            print(f"ChEMBL API error for {chembl_id}: {e}")
            return []
    
    def get_target_info(self, target_chembl_id: str) -> Optional[dict]:
        """
        Get detailed target information.
        
        Args:
            target_chembl_id: ChEMBL target ID
            
        Returns:
            Target information dict or None
        """
        url = f"{self.BASE_URL}/target/{target_chembl_id}.json"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"ChEMBL API error for target {target_chembl_id}: {e}")
            return None
    
    def _parse_interaction_type(self, assay_type: str, standard_type: str) -> InteractionType:
        """Parse ChEMBL assay data to infer interaction type."""
        assay_lower = assay_type.lower() if assay_type else ''
        type_lower = standard_type.lower() if standard_type else ''
        
        # Binding assays or inhibition assays suggest inhibitor/antagonist
        if 'binding' in assay_lower or 'inhibition' in assay_lower or assay_lower == 'b':
            return InteractionType.INHIBITOR
        
        # Functional assays
        if 'functional' in assay_lower or 'activity' in assay_lower or assay_lower == 'f':
            if 'agonist' in type_lower:
                return InteractionType.AGONIST
            elif 'antagonist' in type_lower:
                return InteractionType.ANTAGONIST
        
        return InteractionType.UNKNOWN
    
    def _parse_potency_unit(self, unit_str: Optional[str]) -> PotencyUnit:
        """Parse potency unit string."""
        if not unit_str:
            return PotencyUnit.NANOMOLAR  # ChEMBL often uses nM as default
        
        unit_lower = unit_str.lower()
        if 'nm' in unit_lower:
            return PotencyUnit.NANOMOLAR
        elif 'um' in unit_lower:
            return PotencyUnit.MICROMOLAR
        elif 'mm' in unit_lower:
            return PotencyUnit.MILLIMOLAR
        elif 'pm' in unit_lower:
            return PotencyUnit.PICOMOLAR
        elif unit_lower == 'm':
            return PotencyUnit.MOLAR
        
        return PotencyUnit.NANOMOLAR
    
    def _aggregate_activities_by_target(self, activities: List[dict]) -> Dict[str, List[dict]]:
        """Group activities by target."""
        target_activities = {}
        
        for activity in activities:
            target_id = activity.get('target_chembl_id')
            if not target_id:
                continue
            
            # Filter for relevant potency measurements
            standard_type = activity.get('standard_type')
            if standard_type not in ['Ki', 'IC50', 'EC50', 'Kd', 'Kb']:
                continue
            
            # Must have a valid value
            value = activity.get('standard_value')
            if value is None:
                continue
            
            if target_id not in target_activities:
                target_activities[target_id] = []
            target_activities[target_id].append(activity)
        
        return target_activities
    
    def _calculate_evidence_score(self, activities: List[dict]) -> float:
        """
        Calculate evidence score based on number of studies and consistency.
        
        Returns score between 0 and 1.
        """
        n_studies = len(activities)
        
        # Extract potency values in nanomolar
        values = []
        for act in activities:
            value = act.get('standard_value')
            unit = act.get('standard_units')
            if value:
                potency = PotencyMeasure(
                    value=float(value),
                    unit=self._parse_potency_unit(unit),
                    measure_type=act.get('standard_type', 'unknown')
                )
                nm_value = potency.to_nanomolar()
                if nm_value:
                    values.append(nm_value)
        
        # Calculate consistency (lower CV = higher score)
        consistency_score = 0.5  # default
        if len(values) > 1:
            mean_val = statistics.mean(values)
            stdev_val = statistics.stdev(values)
            cv = stdev_val / mean_val if mean_val > 0 else 1.0
            consistency_score = max(0.0, 1.0 - cv)
        
        # Combine number of studies with consistency
        n_score = min(1.0, n_studies / 10.0)  # 10+ studies = max score
        final_score = 0.6 * n_score + 0.4 * consistency_score
        
        return round(final_score, 3)
    
    def fetch_drug_profile(self, drug_name: str) -> Optional[DrugProfile]:
        """
        Fetch complete drug profile from ChEMBL.
        
        Args:
            drug_name: Common drug name
            
        Returns:
            DrugProfile or None if not found
        """
        # Search for molecule
        molecules = self.search_molecule(drug_name)
        if not molecules:
            return None
        
        # Use first match (could be improved with disambiguation)
        molecule = molecules[0]
        chembl_id = molecule.get('molecule_chembl_id')
        
        # Get bioactivities
        activities = self.get_molecule_activities(chembl_id)
        
        # Aggregate by target
        target_activities = self._aggregate_activities_by_target(activities)
        
        # Build interactions
        interactions = []
        for target_id, target_acts in target_activities.items():
            # Get target info
            target_info = self.get_target_info(target_id)
            if not target_info:
                continue
            
            # Extract gene symbol
            components = target_info.get('target_components', [])
            if not components:
                continue
            
            gene_symbol = None
            uniprot_id = None
            for component in components:
                accession = component.get('accession')
                if accession:
                    uniprot_id = accession
                    # Gene symbol from component
                    syn = component.get('component_synonym')
                    if syn:
                        gene_symbol = syn
                    break
            
            if not gene_symbol:
                continue
            
            # Parse potency measures
            potency_measures = []
            for act in target_acts[:10]:  # limit to top 10 per target
                value = act.get('standard_value')
                if value:
                    potency_measures.append(PotencyMeasure(
                        value=float(value),
                        unit=self._parse_potency_unit(act.get('standard_units')),
                        measure_type=act.get('standard_type', 'unknown'),
                        assay_description=act.get('assay_description'),
                        pubmed_id=str(act.get('document_chembl_id', '')),
                    ))
            
            # Create interaction
            interaction = TargetInteraction(
                target_gene_symbol=gene_symbol,
                target_uniprot_id=uniprot_id,
                target_name=target_info.get('pref_name'),
                interaction_type=self._parse_interaction_type(
                    target_acts[0].get('assay_type', ''),
                    target_acts[0].get('standard_type', '')
                ),
                potency_measures=potency_measures,
                evidence_score=self._calculate_evidence_score(target_acts),
                source_database='ChEMBL',
            )
            interactions.append(interaction)
        
        # Build DrugProfile
        profile = DrugProfile(
            common_name=molecule.get('pref_name', drug_name),
            synonyms=molecule.get('molecule_synonyms', []),
            chembl_id=chembl_id,
            inchi_key=molecule.get('molecule_structures', {}).get('standard_inchi_key'),
            smiles=molecule.get('molecule_structures', {}).get('canonical_smiles'),
            interactions=interactions,
            drug_class=molecule.get('molecule_type'),
            mechanism_summary=None,
            is_approved=molecule.get('max_phase', 0) >= 4,
            source_databases=['ChEMBL'],
            last_updated=datetime.now().isoformat(),
            uncertainty_metadata={
                'n_activities_retrieved': len(activities),
                'n_targets_found': len(target_activities),
            }
        )
        
        return profile
