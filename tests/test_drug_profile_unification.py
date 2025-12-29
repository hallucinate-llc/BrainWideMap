"""
Unit tests for drug profile unification (Phase 3).

Tests cover:
- Seed mode behavior
- Conversion from /drug schema to neurothera_map schema
- Auto-mode fallback when /drug cannot import
- Ingest mode with error handling
"""

import pytest
from unittest.mock import Mock, patch
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
from enum import Enum

from neurothera_map import build_drug_profile, DrugProfile, DrugInteraction


# Mock classes to simulate /drug module schemas
class MockInteractionType(Enum):
    AGONIST = "agonist"
    ANTAGONIST = "antagonist"
    INHIBITOR = "inhibitor"


@dataclass
class MockPotencyMeasure:
    value: float
    unit: str
    measure_type: str
    
    def to_nanomolar(self) -> Optional[float]:
        """Convert to nanomolar."""
        conversions = {"nM": 1.0, "uM": 1e3, "mM": 1e6, "pM": 1e-3}
        if self.unit in conversions:
            return self.value * conversions[self.unit]
        return None


@dataclass
class MockTargetInteraction:
    target_gene_symbol: str
    target_uniprot_id: Optional[str] = None
    target_name: Optional[str] = None
    interaction_type: MockInteractionType = MockInteractionType.ANTAGONIST
    potency_measures: List[MockPotencyMeasure] = field(default_factory=list)
    evidence_score: Optional[float] = None
    source_database: Optional[str] = None
    
    def get_best_potency_nm(self) -> Optional[float]:
        """Get best (lowest) potency in nM."""
        potencies = [p.to_nanomolar() for p in self.potency_measures]
        potencies = [p for p in potencies if p is not None]
        return min(potencies) if potencies else None


@dataclass
class MockDrugProfile:
    common_name: str
    synonyms: List[str] = field(default_factory=list)
    chembl_id: Optional[str] = None
    iuphar_ligand_id: Optional[int] = None
    interactions: List[MockTargetInteraction] = field(default_factory=list)
    source_databases: List[str] = field(default_factory=list)


class TestSeedMode:
    """Test seed mode (existing offline behavior)."""
    
    def test_seed_mode_caffeine(self):
        """Test seed mode with caffeine."""
        profile = build_drug_profile("caffeine", mode="seed")
        
        assert profile.name == "caffeine"
        assert len(profile.interactions) == 2
        assert "ADORA1" in profile.targets()
        assert "ADORA2A" in profile.targets()
        assert profile.provenance["mode"] == "seed"
        assert profile.provenance["seed_db_hit"] is True
    
    def test_seed_mode_unknown_drug(self):
        """Test seed mode with unknown drug."""
        profile = build_drug_profile("unknown_drug", mode="seed")
        
        assert profile.name == "unknown_drug"
        assert len(profile.interactions) == 0
        assert profile.provenance["mode"] == "seed"
        assert profile.provenance["seed_db_hit"] is False
    
    def test_seed_mode_case_insensitive(self):
        """Test seed mode is case-insensitive."""
        profile1 = build_drug_profile("Caffeine", mode="seed")
        profile2 = build_drug_profile("CAFFEINE", mode="seed")
        profile3 = build_drug_profile("caffeine", mode="seed")
        
        assert profile1.name == profile2.name == profile3.name == "caffeine"
        assert len(profile1.interactions) == len(profile2.interactions) == len(profile3.interactions)
    
    def test_seed_mode_whitespace_normalization(self):
        """Test seed mode normalizes whitespace."""
        profile = build_drug_profile("  caffeine  ", mode="seed")
        
        assert profile.name == "caffeine"
        assert len(profile.interactions) == 2


class TestConversion:
    """Test conversion from /drug schema to neurothera_map schema."""
    
    def test_conversion_basic(self):
        """Test basic conversion with synthetic objects."""
        from neurothera_map.drug.profile import _convert_drug_profile
        
        # Create mock drug profile
        mock_profile = MockDrugProfile(
            common_name="TestDrug",
            chembl_id="CHEMBL123",
            iuphar_ligand_id=456,
            source_databases=["IUPHAR", "ChEMBL"],
            interactions=[
                MockTargetInteraction(
                    target_gene_symbol="ADORA1",
                    target_uniprot_id="P30542",
                    target_name="Adenosine receptor A1",
                    interaction_type=MockInteractionType.ANTAGONIST,
                    potency_measures=[
                        MockPotencyMeasure(100.0, "nM", "Ki"),
                        MockPotencyMeasure(150.0, "nM", "IC50"),
                    ],
                    evidence_score=0.9,
                    source_database="IUPHAR",
                )
            ],
        )
        
        # Convert
        profile = _convert_drug_profile(mock_profile)
        
        # Verify
        assert isinstance(profile, DrugProfile)
        assert profile.name == "testdrug"
        assert len(profile.interactions) == 1
        
        interaction = profile.interactions[0]
        assert interaction.target == "ADORA1"
        assert interaction.affinity_nM == 100.0  # Best potency
        assert interaction.action == "antagonist"
        assert interaction.evidence == 0.9
        assert interaction.source == "IUPHAR"
        assert interaction.meta["uniprot_id"] == "P30542"
        assert interaction.meta["target_name"] == "Adenosine receptor A1"
        assert interaction.meta["n_potency_measures"] == 2
    
    def test_conversion_multiple_interactions(self):
        """Test conversion with multiple target interactions."""
        from neurothera_map.drug.profile import _convert_drug_profile
        
        mock_profile = MockDrugProfile(
            common_name="MultiTarget",
            source_databases=["ChEMBL"],
            interactions=[
                MockTargetInteraction(
                    target_gene_symbol="TARGET1",
                    interaction_type=MockInteractionType.AGONIST,
                    potency_measures=[MockPotencyMeasure(50.0, "nM", "Ki")],
                    evidence_score=0.8,
                    source_database="ChEMBL",
                ),
                MockTargetInteraction(
                    target_gene_symbol="TARGET2",
                    interaction_type=MockInteractionType.INHIBITOR,
                    potency_measures=[MockPotencyMeasure(200.0, "nM", "IC50")],
                    evidence_score=0.6,
                    source_database="ChEMBL",
                ),
            ],
        )
        
        profile = _convert_drug_profile(mock_profile)
        
        assert len(profile.interactions) == 2
        assert profile.targets() == ["TARGET1", "TARGET2"]
        assert profile.interactions[0].action == "agonist"
        assert profile.interactions[1].action == "inhibitor"
    
    def test_conversion_no_potency(self):
        """Test conversion when no potency data available."""
        from neurothera_map.drug.profile import _convert_drug_profile
        
        mock_profile = MockDrugProfile(
            common_name="NoPotency",
            source_databases=["IUPHAR"],
            interactions=[
                MockTargetInteraction(
                    target_gene_symbol="TARGET1",
                    interaction_type=MockInteractionType.AGONIST,
                    potency_measures=[],  # No potency measures
                    evidence_score=0.5,
                    source_database="IUPHAR",
                ),
            ],
        )
        
        profile = _convert_drug_profile(mock_profile)
        
        assert len(profile.interactions) == 1
        assert profile.interactions[0].affinity_nM is None
    
    def test_conversion_unit_conversion(self):
        """Test that unit conversion works correctly."""
        from neurothera_map.drug.profile import _convert_drug_profile
        
        mock_profile = MockDrugProfile(
            common_name="UnitTest",
            source_databases=["ChEMBL"],
            interactions=[
                MockTargetInteraction(
                    target_gene_symbol="TARGET1",
                    potency_measures=[
                        MockPotencyMeasure(1.0, "uM", "Ki"),  # 1000 nM
                        MockPotencyMeasure(500.0, "pM", "IC50"),  # 0.5 nM
                    ],
                    source_database="ChEMBL",
                ),
            ],
        )
        
        profile = _convert_drug_profile(mock_profile)
        
        # Should pick best (lowest) potency: 0.5 nM
        assert profile.interactions[0].affinity_nM == 0.5
    
    def test_conversion_provenance(self):
        """Test that provenance is correctly set."""
        from neurothera_map.drug.profile import _convert_drug_profile
        
        mock_profile = MockDrugProfile(
            common_name="ProvenanceTest",
            chembl_id="CHEMBL999",
            iuphar_ligand_id=777,
            source_databases=["IUPHAR", "ChEMBL"],
            interactions=[],
        )
        
        profile = _convert_drug_profile(mock_profile)
        
        assert profile.provenance["builder"] == "neurothera_map.drug.build_drug_profile"
        assert profile.provenance["normalized_name"] == "provenancetest"  # Lowercased
        assert profile.provenance["mode"] == "ingest"
        assert profile.provenance["source_databases"] == ["IUPHAR", "ChEMBL"]
        assert profile.provenance["chembl_id"] == "CHEMBL999"
        assert profile.provenance["iuphar_ligand_id"] == 777


class TestAutoModeFallback:
    """Test auto-mode fallback when /drug cannot import."""
    
    def test_auto_mode_import_error_fallback(self):
        """Test auto mode falls back to seed when import fails."""
        # Patch the import to raise ImportError
        with patch('builtins.__import__', side_effect=ImportError("drug module not available")):
            # Should fall back to seed
            profile = build_drug_profile("caffeine", mode="auto")
            
            assert profile.name == "caffeine"
            assert len(profile.interactions) == 2
            assert profile.provenance["mode"] == "auto"
            assert profile.provenance["ingestion_attempted"] is True
            assert profile.provenance["ingestion_available"] is False
    
    def test_auto_mode_drug_not_found_fallback(self):
        """Test auto mode falls back to seed when drug not found in ingestion."""
        mock_loader = Mock()
        mock_loader.load_drug_profile.return_value = None
        
        with patch('drug.drug_loader.DrugLoader', return_value=mock_loader):
            profile = build_drug_profile("unknown_drug", mode="auto")
            
            assert profile.name == "unknown_drug"
            assert len(profile.interactions) == 0
            assert profile.provenance["mode"] == "auto"
            assert profile.provenance["ingestion_attempted"] is True
            assert profile.provenance["ingestion_available"] is False
    
    def test_auto_mode_success_no_fallback(self):
        """Test auto mode uses ingestion when available."""
        mock_drug_profile = MockDrugProfile(
            common_name="TestDrug",
            source_databases=["IUPHAR"],
            interactions=[
                MockTargetInteraction(
                    target_gene_symbol="TARGET1",
                    potency_measures=[MockPotencyMeasure(50.0, "nM", "Ki")],
                    source_database="IUPHAR",
                )
            ],
        )
        
        mock_loader = Mock()
        mock_loader.load_drug_profile.return_value = mock_drug_profile
        
        with patch('drug.drug_loader.DrugLoader', return_value=mock_loader):
            profile = build_drug_profile("TestDrug", mode="auto")
            
            assert profile.name == "testdrug"
            assert len(profile.interactions) == 1
            assert profile.provenance["mode"] == "ingest"
            assert profile.provenance["source_databases"] == ["IUPHAR"]


class TestIngestMode:
    """Test ingest mode with error handling."""
    
    def test_ingest_mode_import_error(self):
        """Test ingest mode raises ImportError when module not available."""
        # Patch the import to raise ImportError
        with patch('builtins.__import__', side_effect=ImportError("drug module not available")):
            with pytest.raises(ImportError) as exc_info:
                build_drug_profile("caffeine", mode="ingest")
            
            assert "Cannot use mode='ingest'" in str(exc_info.value)
            assert "/drug module is not available" in str(exc_info.value)
    
    def test_ingest_mode_drug_not_found(self):
        """Test ingest mode raises RuntimeError when drug not found."""
        mock_loader = Mock()
        mock_loader.load_drug_profile.return_value = None
        
        with patch('drug.drug_loader.DrugLoader', return_value=mock_loader):
            with pytest.raises(RuntimeError) as exc_info:
                build_drug_profile("unknown_drug", mode="ingest")
            
            assert "not found in ingestion databases" in str(exc_info.value)
            assert "unknown_drug" in str(exc_info.value)
    
    def test_ingest_mode_success(self):
        """Test ingest mode successfully loads drug."""
        mock_drug_profile = MockDrugProfile(
            common_name="SuccessDrug",
            chembl_id="CHEMBL123",
            source_databases=["ChEMBL"],
            interactions=[
                MockTargetInteraction(
                    target_gene_symbol="TARGET1",
                    potency_measures=[MockPotencyMeasure(100.0, "nM", "Ki")],
                    evidence_score=0.8,
                    source_database="ChEMBL",
                )
            ],
        )
        
        mock_loader = Mock()
        mock_loader.load_drug_profile.return_value = mock_drug_profile
        
        with patch('drug.drug_loader.DrugLoader', return_value=mock_loader):
            profile = build_drug_profile("SuccessDrug", mode="ingest")
            
            assert profile.name == "successdrug"
            assert len(profile.interactions) == 1
            assert profile.provenance["mode"] == "ingest"
            assert profile.provenance["chembl_id"] == "CHEMBL123"


class TestBackwardCompatibility:
    """Test that existing behavior is preserved."""
    
    def test_default_mode_is_auto(self):
        """Test that default mode is auto."""
        mock_loader = Mock()
        mock_loader.load_drug_profile.return_value = None
        
        with patch('drug.drug_loader.DrugLoader', return_value=mock_loader):
            # No mode specified should use auto
            profile = build_drug_profile("caffeine")
            
            # Should fall back to seed
            assert profile.name == "caffeine"
            assert len(profile.interactions) == 2
            assert profile.provenance["mode"] == "auto"
    
    def test_existing_tests_still_pass(self):
        """Test that existing test cases still work."""
        # Original test from test_neurothera_drug_profile.py
        p = build_drug_profile("caffeine")
        assert p.name == "caffeine"
        assert len(p.interactions) >= 1
        assert "ADORA1" in p.targets()
        
        # Unknown drug test
        p2 = build_drug_profile("some_unknown_compound")
        assert p2.name == "some_unknown_compound"
        assert len(p2.interactions) == 0


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_invalid_mode_raises_error(self):
        """Test that invalid mode raises ValueError."""
        # Note: With Literal type, this would be caught at type-check time,
        # but we test runtime behavior for completeness
        with pytest.raises(ValueError) as exc_info:
            build_drug_profile("caffeine", mode="invalid")  # type: ignore
        
        assert "Invalid mode" in str(exc_info.value)
    
    def test_empty_drug_name(self):
        """Test behavior with empty drug name."""
        profile = build_drug_profile("", mode="seed")
        
        assert profile.name == ""
        assert len(profile.interactions) == 0
    
    def test_whitespace_only_drug_name(self):
        """Test behavior with whitespace-only drug name."""
        profile = build_drug_profile("   ", mode="seed")
        
        assert profile.name == ""
        assert len(profile.interactions) == 0


class TestAffinityDictIntegration:
    """Test as_target_affinity_dict works with converted profiles."""
    
    def test_affinity_dict_from_conversion(self):
        """Test that converted profiles work with as_target_affinity_dict."""
        from neurothera_map.drug.profile import _convert_drug_profile
        
        mock_profile = MockDrugProfile(
            common_name="AffinityTest",
            source_databases=["IUPHAR"],
            interactions=[
                MockTargetInteraction(
                    target_gene_symbol="TARGET1",
                    potency_measures=[MockPotencyMeasure(50.0, "nM", "Ki")],
                    source_database="IUPHAR",
                ),
                MockTargetInteraction(
                    target_gene_symbol="TARGET2",
                    potency_measures=[MockPotencyMeasure(200.0, "nM", "Ki")],
                    source_database="IUPHAR",
                ),
            ],
        )
        
        profile = _convert_drug_profile(mock_profile)
        affinity_dict = profile.as_target_affinity_dict()
        
        assert len(affinity_dict) == 2
        assert affinity_dict["TARGET1"] == 50.0
        assert affinity_dict["TARGET2"] == 200.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
