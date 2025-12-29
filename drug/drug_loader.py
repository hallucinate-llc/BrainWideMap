"""
High-level drug profile loader and combiner.

Coordinates IUPHAR and ChEMBL adapters to build comprehensive drug profiles.
"""

from typing import Optional, List
from pathlib import Path
import json

from .schemas import DrugProfile, TargetInteraction
from .iuphar_adapter import IUPHARAdapter
from .chembl_adapter import ChEMBLAdapter


class DrugLoader:
    """
    High-level interface for loading drug profiles from multiple sources.
    """
    
    def __init__(self, cache_dir: Optional[str] = None, prefer_iuphar: bool = True):
        """
        Initialize drug loader.
        
        Args:
            cache_dir: Optional directory for caching profiles
            prefer_iuphar: If True, prefer IUPHAR data when merging
        """
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.prefer_iuphar = prefer_iuphar
        
        self.iuphar = IUPHARAdapter(cache_dir=cache_dir)
        self.chembl = ChEMBLAdapter(cache_dir=cache_dir)
    
    def load_drug_profile(
        self,
        drug_name: str,
        use_iuphar: bool = True,
        use_chembl: bool = True,
        merge: bool = True,
    ) -> Optional[DrugProfile]:
        """
        Load drug profile from one or more sources.
        
        Args:
            drug_name: Common drug name
            use_iuphar: Include IUPHAR data
            use_chembl: Include ChEMBL data
            merge: If True and both sources used, merge profiles
            
        Returns:
            Combined DrugProfile or None if not found
        """
        # Check cache first
        cached = self._load_from_cache(drug_name)
        if cached:
            return cached
        
        profiles = []
        
        # Fetch from IUPHAR
        if use_iuphar:
            iuphar_profile = self.iuphar.fetch_drug_profile(drug_name)
            if iuphar_profile:
                profiles.append(iuphar_profile)
        
        # Fetch from ChEMBL
        if use_chembl:
            chembl_profile = self.chembl.fetch_drug_profile(drug_name)
            if chembl_profile:
                profiles.append(chembl_profile)
        
        if not profiles:
            return None
        
        # Merge if multiple sources
        if len(profiles) > 1 and merge:
            combined = self._merge_profiles(profiles)
        else:
            combined = profiles[0]
        
        # Cache result
        self._save_to_cache(drug_name, combined)
        
        return combined
    
    def _merge_profiles(self, profiles: List[DrugProfile]) -> DrugProfile:
        """
        Merge multiple drug profiles intelligently.
        
        Combines target interactions, preferring higher-quality data.
        """
        # Use first profile as base
        base = profiles[0]
        
        # Collect all interactions by target
        target_map = {}
        for profile in profiles:
            for interaction in profile.interactions:
                key = interaction.target_gene_symbol
                if key not in target_map:
                    target_map[key] = []
                target_map[key].append((interaction, profile.source_databases[0]))
        
        # For each target, choose best interaction
        merged_interactions = []
        for target, interactions_list in target_map.items():
            if len(interactions_list) == 1:
                merged_interactions.append(interactions_list[0][0])
            else:
                # Prefer IUPHAR if configured, or higher evidence score
                if self.prefer_iuphar:
                    iuphar_ints = [i for i, s in interactions_list if s == 'IUPHAR']
                    if iuphar_ints:
                        merged_interactions.append(iuphar_ints[0])
                        continue
                
                # Otherwise choose by evidence score
                best = max(interactions_list, key=lambda x: x[0].evidence_score or 0)
                merged_interactions.append(best[0])
        
        # Build merged profile
        all_sources = set()
        for p in profiles:
            all_sources.update(p.source_databases)
        
        merged = DrugProfile(
            common_name=base.common_name,
            synonyms=list(set(syn for p in profiles for syn in p.synonyms)),
            chembl_id=base.chembl_id or next((p.chembl_id for p in profiles if p.chembl_id), None),
            iuphar_ligand_id=base.iuphar_ligand_id or next((p.iuphar_ligand_id for p in profiles if p.iuphar_ligand_id), None),
            inchi_key=base.inchi_key or next((p.inchi_key for p in profiles if p.inchi_key), None),
            smiles=base.smiles or next((p.smiles for p in profiles if p.smiles), None),
            interactions=merged_interactions,
            drug_class=base.drug_class,
            mechanism_summary=base.mechanism_summary,
            is_approved=any(p.is_approved for p in profiles),
            source_databases=list(all_sources),
            last_updated=base.last_updated,
            uncertainty_metadata={
                'merged_from': [p.source_databases[0] for p in profiles],
                'n_interactions_total': sum(len(p.interactions) for p in profiles),
                'n_interactions_merged': len(merged_interactions),
            }
        )
        
        return merged
    
    def _load_from_cache(self, drug_name: str) -> Optional[DrugProfile]:
        """Load profile from cache if available."""
        if not self.cache_dir:
            return None
        
        cache_file = self.cache_dir / f"{drug_name.lower().replace(' ', '_')}.json"
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            # TODO: Reconstruct DrugProfile from dict
            return None  # For now, skip cache reconstruction
        except Exception as e:
            print(f"Cache load error: {e}")
            return None
    
    def _save_to_cache(self, drug_name: str, profile: DrugProfile):
        """Save profile to cache."""
        if not self.cache_dir:
            return
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = self.cache_dir / f"{drug_name.lower().replace(' ', '_')}.json"
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(profile.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Cache save error: {e}")
    
    def get_primary_targets(self, drug_name: str, top_n: int = 3) -> List[TargetInteraction]:
        """
        Get primary targets for a drug.
        
        Args:
            drug_name: Drug name
            top_n: Number of top targets to return
            
        Returns:
            List of primary target interactions
        """
        profile = self.load_drug_profile(drug_name)
        if not profile:
            return []
        
        return profile.get_primary_targets(top_n=top_n)
