"""
Example usage of drug database ingestion.

Demonstrates loading drug profiles from IUPHAR and ChEMBL.
"""

from drug import DrugLoader


def example_caffeine():
    """Example: Fetch caffeine profile."""
    print("=" * 60)
    print("CAFFEINE PROFILE")
    print("=" * 60)
    
    loader = DrugLoader()
    profile = loader.load_drug_profile("caffeine")
    
    if not profile:
        print("Caffeine not found")
        return
    
    print(f"\nDrug: {profile.common_name}")
    print(f"ChEMBL ID: {profile.chembl_id}")
    print(f"IUPHAR ID: {profile.iuphar_ligand_id}")
    print(f"Sources: {', '.join(profile.source_databases)}")
    
    print(f"\n{len(profile.interactions)} target interactions found")
    
    # Show top 3 targets
    primary = profile.get_primary_targets(top_n=3)
    print("\nPrimary targets:")
    for i, interaction in enumerate(primary, 1):
        print(f"\n{i}. {interaction.target_gene_symbol}")
        print(f"   Type: {interaction.interaction_type.value}")
        print(f"   Target: {interaction.target_name}")
        
        best_potency = interaction.get_best_potency_nm()
        if best_potency:
            print(f"   Best potency: {best_potency:.1f} nM")
        
        if interaction.evidence_score:
            print(f"   Evidence score: {interaction.evidence_score:.2f}")
        
        print(f"   Source: {interaction.source_database}")


def example_ssri():
    """Example: Fetch SSRI (sertraline) profile."""
    print("\n\n" + "=" * 60)
    print("SERTRALINE (SSRI) PROFILE")
    print("=" * 60)
    
    loader = DrugLoader()
    profile = loader.load_drug_profile("sertraline")
    
    if not profile:
        print("Sertraline not found")
        return
    
    print(f"\nDrug: {profile.common_name}")
    print(f"Approved: {profile.is_approved}")
    print(f"Sources: {', '.join(profile.source_databases)}")
    
    # Show SERT specifically
    sert_interactions = [
        i for i in profile.interactions 
        if 'SLC6A4' in i.target_gene_symbol or 'SERT' in i.target_gene_symbol.upper()
    ]
    
    if sert_interactions:
        print("\nSERT (SLC6A4) interaction:")
        for interaction in sert_interactions:
            print(f"  Type: {interaction.interaction_type.value}")
            best_potency = interaction.get_best_potency_nm()
            if best_potency:
                print(f"  Best potency: {best_potency:.1f} nM")
    
    # Show top off-targets
    other_targets = [i for i in profile.interactions if i not in sert_interactions][:5]
    if other_targets:
        print(f"\nTop {len(other_targets)} off-targets:")
        for interaction in other_targets:
            best_potency = interaction.get_best_potency_nm()
            potency_str = f"{best_potency:.1f} nM" if best_potency else "N/A"
            print(f"  - {interaction.target_gene_symbol}: {potency_str}")


def example_compare_sources():
    """Example: Compare IUPHAR vs ChEMBL data."""
    print("\n\n" + "=" * 60)
    print("COMPARING IUPHAR vs ChEMBL")
    print("=" * 60)
    
    loader = DrugLoader()
    
    # Load separately
    iuphar_profile = loader.load_drug_profile("caffeine", use_chembl=False)
    chembl_profile = loader.load_drug_profile("caffeine", use_iuphar=False)
    merged_profile = loader.load_drug_profile("caffeine")
    
    print(f"\nIUPHAR targets: {len(iuphar_profile.interactions) if iuphar_profile else 0}")
    print(f"ChEMBL targets: {len(chembl_profile.interactions) if chembl_profile else 0}")
    print(f"Merged targets: {len(merged_profile.interactions) if merged_profile else 0}")
    
    if merged_profile:
        print(f"\nMerge metadata: {merged_profile.uncertainty_metadata}")


if __name__ == "__main__":
    example_caffeine()
    example_ssri()
    example_compare_sources()
