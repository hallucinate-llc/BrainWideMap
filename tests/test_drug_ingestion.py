"""
Unit tests for drug database adapters.

Comprehensive test suite covering:
- Schema functionality and data models
- Unit conversions and potency calculations
- Interaction type parsing
- Evidence scoring algorithms
- Profile merging logic
- Edge cases and error handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from drug.schemas import DrugProfile, TargetInteraction, PotencyMeasure, InteractionType, PotencyUnit
from drug.iuphar_adapter import IUPHARAdapter
from drug.chembl_adapter import ChEMBLAdapter
from drug.drug_loader import DrugLoader


class TestPotencyMeasure:
    """Test PotencyMeasure unit conversions."""
    
    def test_nanomolar_to_nanomolar(self):
        """Test nM to nM conversion (identity)."""
        p = PotencyMeasure(value=100.0, unit=PotencyUnit.NANOMOLAR, measure_type="Ki")
        assert p.to_nanomolar() == 100.0
    
    def test_micromolar_to_nanomolar(self):
        """Test μM to nM conversion."""
        p = PotencyMeasure(value=1.0, unit=PotencyUnit.MICROMOLAR, measure_type="Ki")
        assert p.to_nanomolar() == 1000.0
        
        p2 = PotencyMeasure(value=0.5, unit=PotencyUnit.MICROMOLAR, measure_type="IC50")
        assert p2.to_nanomolar() == 500.0
    
    def test_millimolar_to_nanomolar(self):
        """Test mM to nM conversion."""
        p = PotencyMeasure(value=2.0, unit=PotencyUnit.MILLIMOLAR, measure_type="Kd")
        assert p.to_nanomolar() == 2000000.0
        
        p2 = PotencyMeasure(value=0.001, unit=PotencyUnit.MILLIMOLAR, measure_type="Kb")
        assert p2.to_nanomolar() == 1000.0
    
    def test_picomolar_to_nanomolar(self):
        """Test pM to nM conversion."""
        p = PotencyMeasure(value=500.0, unit=PotencyUnit.PICOMOLAR, measure_type="Ki")
        assert p.to_nanomolar() == 0.5
        
        p2 = PotencyMeasure(value=10.0, unit=PotencyUnit.PICOMOLAR, measure_type="EC50")
        assert p2.to_nanomolar() == 0.01
    
    def test_molar_to_nanomolar(self):
        """Test M to nM conversion."""
        p = PotencyMeasure(value=0.000001, unit=PotencyUnit.MOLAR, measure_type="Ki")
        assert p.to_nanomolar() == 1000.0
    
    def test_unknown_unit_conversion(self):
        """Test that unknown units return None."""
        p = PotencyMeasure(value=100.0, unit=PotencyUnit.UNKNOWN, measure_type="Ki")
        assert p.to_nanomolar() is None


class TestTargetInteraction:
    """Test TargetInteraction potency calculations."""
    
    def test_best_potency_single_measure(self):
        """Test best potency with single measurement."""
        interaction = TargetInteraction(
            target_gene_symbol="ADORA1",
            potency_measures=[PotencyMeasure(50, PotencyUnit.NANOMOLAR, "Ki")]
        )
        assert interaction.get_best_potency_nm() == 50.0
    
    def test_best_potency_multiple_measures(self):
        """Test best potency selection from multiple measurements."""
        measures = [
            PotencyMeasure(value=100, unit=PotencyUnit.NANOMOLAR, measure_type="Ki"),
            PotencyMeasure(value=50, unit=PotencyUnit.NANOMOLAR, measure_type="IC50"),
            PotencyMeasure(value=200, unit=PotencyUnit.NANOMOLAR, measure_type="EC50"),
        ]
        interaction = TargetInteraction(
            target_gene_symbol="ADORA2A",
            potency_measures=measures
        )
        assert interaction.get_best_potency_nm() == 50.0
    
    def test_best_potency_mixed_units(self):
        """Test best potency with mixed units (should convert all to nM)."""
        measures = [
            PotencyMeasure(value=1, unit=PotencyUnit.MICROMOLAR, measure_type="Ki"),  # 1000 nM
            PotencyMeasure(value=50, unit=PotencyUnit.NANOMOLAR, measure_type="IC50"),  # 50 nM
            PotencyMeasure(value=500, unit=PotencyUnit.PICOMOLAR, measure_type="EC50"),  # 0.5 nM
        ]
        interaction = TargetInteraction(
            target_gene_symbol="TEST",
            potency_measures=measures
        )
        assert interaction.get_best_potency_nm() == 0.5
    
    def test_best_potency_no_measures(self):
        """Test best potency returns None when no measurements."""
        interaction = TargetInteraction(
            target_gene_symbol="TEST",
            potency_measures=[]
        )
        assert interaction.get_best_potency_nm() is None
    
    def test_best_potency_ignores_unknown_units(self):
        """Test that unknown units are skipped in best potency calculation."""
        measures = [
            PotencyMeasure(value=100, unit=PotencyUnit.UNKNOWN, measure_type="Ki"),
            PotencyMeasure(value=50, unit=PotencyUnit.NANOMOLAR, measure_type="IC50"),
        ]
        interaction = TargetInteraction(
            target_gene_symbol="TEST",
            potency_measures=measures
        )
        assert interaction.get_best_potency_nm() == 50.0


class TestDrugProfile:
    """Test DrugProfile functionality."""
    
    def test_primary_targets_ordering(self):
        """Test that primary targets are ordered by potency (best first)."""
        interactions = [
            TargetInteraction(
                target_gene_symbol="TARGET1",
                potency_measures=[PotencyMeasure(100, PotencyUnit.NANOMOLAR, "Ki")]
            ),
            TargetInteraction(
                target_gene_symbol="TARGET2",
                potency_measures=[PotencyMeasure(10, PotencyUnit.NANOMOLAR, "Ki")]
            ),
            TargetInteraction(
                target_gene_symbol="TARGET3",
                potency_measures=[PotencyMeasure(1000, PotencyUnit.NANOMOLAR, "Ki")]
            ),
        ]
        
        profile = DrugProfile(
            common_name="TestDrug",
            interactions=interactions
        )
        
        primary = profile.get_primary_targets(top_n=3)
        assert len(primary) == 3
        assert primary[0].target_gene_symbol == "TARGET2"  # 10 nM
        assert primary[1].target_gene_symbol == "TARGET1"  # 100 nM
        assert primary[2].target_gene_symbol == "TARGET3"  # 1000 nM
    
    def test_primary_targets_limit(self):
        """Test that top_n parameter limits results."""
        interactions = [
            TargetInteraction(f"TARGET{i}", 
                            [PotencyMeasure(i*10, PotencyUnit.NANOMOLAR, "Ki")])
            for i in range(1, 11)
        ]
        
        profile = DrugProfile(common_name="TestDrug", interactions=interactions)
        
        primary_3 = profile.get_primary_targets(top_n=3)
        assert len(primary_3) == 3
        
        primary_5 = profile.get_primary_targets(top_n=5)
        assert len(primary_5) == 5
    
    def test_primary_targets_no_potency(self):
        """Test targets without potency are ranked last."""
        interactions = [
            TargetInteraction(
                target_gene_symbol="TARGET1",
                potency_measures=[PotencyMeasure(100, PotencyUnit.NANOMOLAR, "Ki")]
            ),
            TargetInteraction(
                target_gene_symbol="TARGET2",
                potency_measures=[]
            ),  # No potency
            TargetInteraction(
                target_gene_symbol="TARGET3",
                potency_measures=[PotencyMeasure(50, PotencyUnit.NANOMOLAR, "Ki")]
            ),
        ]
        
        profile = DrugProfile(common_name="TestDrug", interactions=interactions)
        primary = profile.get_primary_targets(top_n=3)
        
        # Should get TARGET3 (50), TARGET1 (100), TARGET2 (no potency)
        assert primary[0].target_gene_symbol == "TARGET3"
        assert primary[1].target_gene_symbol == "TARGET1"
        assert primary[2].target_gene_symbol == "TARGET2"
    
    def test_to_dict_serialization(self):
        """Test DrugProfile serialization to dict."""
        profile = DrugProfile(
            common_name="TestDrug",
            synonyms=["Synonym1", "Synonym2"],
            chembl_id="CHEMBL123",
            interactions=[
                TargetInteraction(
                    target_gene_symbol="TEST",
                    potency_measures=[PotencyMeasure(50, PotencyUnit.NANOMOLAR, "Ki")]
                )
            ],
            source_databases=["IUPHAR"]
        )
        
        data = profile.to_dict()
        
        assert data["common_name"] == "TestDrug"
        assert len(data["synonyms"]) == 2
        assert data["chembl_id"] == "CHEMBL123"
        assert len(data["interactions"]) == 1
        assert data["interactions"][0]["target_gene_symbol"] == "TEST"


class TestIUPHARAdapter:
    """Test IUPHAR adapter parsing and API handling."""
    
    def test_parse_interaction_type_agonist(self):
        """Test agonist interaction type parsing."""
        adapter = IUPHARAdapter()
        
        assert adapter._parse_interaction_type("Agonist") == InteractionType.AGONIST
        assert adapter._parse_interaction_type("Full agonist") == InteractionType.AGONIST
        assert adapter._parse_interaction_type("AGONIST") == InteractionType.AGONIST
    
    def test_parse_interaction_type_antagonist(self):
        """Test antagonist parsing (must check before agonist due to substring)."""
        adapter = IUPHARAdapter()
        
        assert adapter._parse_interaction_type("Antagonist") == InteractionType.ANTAGONIST
        assert adapter._parse_interaction_type("Competitive antagonist") == InteractionType.ANTAGONIST
        assert adapter._parse_interaction_type("ANTAGONIST") == InteractionType.ANTAGONIST
    
    def test_parse_interaction_type_partial_agonist(self):
        """Test partial agonist detection."""
        adapter = IUPHARAdapter()
        
        assert adapter._parse_interaction_type("Partial agonist") == InteractionType.PARTIAL_AGONIST
        assert adapter._parse_interaction_type("Partial Agonist") == InteractionType.PARTIAL_AGONIST
    
    def test_parse_interaction_type_inverse_agonist(self):
        """Test inverse agonist detection."""
        adapter = IUPHARAdapter()
        
        assert adapter._parse_interaction_type("Inverse agonist") == InteractionType.INVERSE_AGONIST
    
    def test_parse_interaction_type_inhibitor(self):
        """Test inhibitor detection."""
        adapter = IUPHARAdapter()
        
        assert adapter._parse_interaction_type("Inhibitor") == InteractionType.INHIBITOR
        assert adapter._parse_interaction_type("Reuptake inhibitor") == InteractionType.INHIBITOR
        assert adapter._parse_interaction_type("Inhibition") == InteractionType.INHIBITOR
    
    def test_parse_interaction_type_blocker(self):
        """Test blocker/channel blocker detection."""
        adapter = IUPHARAdapter()
        
        assert adapter._parse_interaction_type("Blocker") == InteractionType.BLOCKER
        assert adapter._parse_interaction_type("Channel blocker") == InteractionType.BLOCKER
    
    def test_parse_interaction_type_modulator(self):
        """Test allosteric modulator detection."""
        adapter = IUPHARAdapter()
        
        assert adapter._parse_interaction_type("Allosteric modulator") == InteractionType.ALLOSTERIC_MODULATOR
        assert adapter._parse_interaction_type("Positive allosteric modulator") == InteractionType.ALLOSTERIC_MODULATOR
    
    def test_parse_interaction_type_unknown(self):
        """Test unknown interaction types."""
        adapter = IUPHARAdapter()
        
        assert adapter._parse_interaction_type("") == InteractionType.UNKNOWN
        assert adapter._parse_interaction_type("Substrate") == InteractionType.UNKNOWN
        assert adapter._parse_interaction_type("Binding partner") == InteractionType.UNKNOWN
    
    def test_parse_potency_unit_nanomolar(self):
        """Test nanomolar unit parsing."""
        adapter = IUPHARAdapter()
        
        assert adapter._parse_potency_unit("nM") == PotencyUnit.NANOMOLAR
        assert adapter._parse_potency_unit("nanomolar") == PotencyUnit.NANOMOLAR
        assert adapter._parse_potency_unit("NM") == PotencyUnit.NANOMOLAR
    
    def test_parse_potency_unit_micromolar(self):
        """Test micromolar unit parsing."""
        adapter = IUPHARAdapter()
        
        assert adapter._parse_potency_unit("uM") == PotencyUnit.MICROMOLAR
        assert adapter._parse_potency_unit("μM") == PotencyUnit.MICROMOLAR
        assert adapter._parse_potency_unit("micromolar") == PotencyUnit.MICROMOLAR
    
    def test_parse_potency_unit_picomolar(self):
        """Test picomolar unit parsing."""
        adapter = IUPHARAdapter()
        
        assert adapter._parse_potency_unit("pM") == PotencyUnit.PICOMOLAR
        assert adapter._parse_potency_unit("picomolar") == PotencyUnit.PICOMOLAR
    
    def test_parse_potency_unit_millimolar(self):
        """Test millimolar unit parsing."""
        adapter = IUPHARAdapter()
        
        assert adapter._parse_potency_unit("mM") == PotencyUnit.MILLIMOLAR
        assert adapter._parse_potency_unit("millimolar") == PotencyUnit.MILLIMOLAR
    
    def test_parse_potency_unit_unknown(self):
        """Test unknown unit handling."""
        adapter = IUPHARAdapter()
        
        assert adapter._parse_potency_unit(None) == PotencyUnit.UNKNOWN
        assert adapter._parse_potency_unit("") == PotencyUnit.UNKNOWN
        assert adapter._parse_potency_unit("mg/mL") == PotencyUnit.UNKNOWN
    
    @patch('drug.iuphar_adapter.requests.Session.get')
    def test_search_ligand_success(self, mock_get):
        """Test successful ligand search."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {'ligandId': 407, 'name': 'caffeine'}
        ]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        adapter = IUPHARAdapter()
        results = adapter.search_ligand("caffeine")
        
        assert len(results) == 1
        assert results[0]['ligandId'] == 407
        mock_get.assert_called_once()
    
    @patch('drug.iuphar_adapter.requests.Session.get')
    def test_search_ligand_api_error(self, mock_get):
        """Test ligand search with API error (should catch and return empty list)."""
        # Mock exception during API call
        mock_get.side_effect = Exception("API Error")
        
        adapter = IUPHARAdapter()
        results = adapter.search_ligand("nonexistent")
        
        # Should handle error gracefully and return empty list
        assert results == []
    
    @patch('drug.iuphar_adapter.requests.Session.get')
    def test_get_ligand_interactions_success(self, mock_get):
        """Test successful interaction retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                'targetGeneSymbol': 'ADORA1',
                'interactionType': 'Antagonist',
                'affinity': 12.0,
                'affinityUnit': 'nM'
            }
        ]
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        adapter = IUPHARAdapter()
        interactions = adapter.get_ligand_interactions(407)
        
        assert len(interactions) == 1
        assert interactions[0]['targetGeneSymbol'] == 'ADORA1'


class TestChEMBLAdapter:
    """Test ChEMBL adapter parsing and calculations."""
    
    def test_parse_interaction_type_binding_inhibition(self):
        """Test interaction type inference from binding assays."""
        adapter = ChEMBLAdapter()
        
        assert adapter._parse_interaction_type("Binding", "IC50") == InteractionType.INHIBITOR
        assert adapter._parse_interaction_type("B", "Ki") == InteractionType.INHIBITOR
        assert adapter._parse_interaction_type("Inhibition", "IC50") == InteractionType.INHIBITOR
    
    def test_parse_interaction_type_functional(self):
        """Test interaction type inference from functional assays."""
        adapter = ChEMBLAdapter()
        
        # Functional assays without specific type markers = unknown
        result = adapter._parse_interaction_type("Functional", "EC50")
        assert result == InteractionType.UNKNOWN
        
        # But if type mentions agonist/antagonist, should detect
        result2 = adapter._parse_interaction_type("Functional", "agonist EC50")
        assert result2 == InteractionType.AGONIST
    
    def test_parse_potency_unit_default_nanomolar(self):
        """Test that ChEMBL defaults to nanomolar."""
        adapter = ChEMBLAdapter()
        
        assert adapter._parse_potency_unit(None) == PotencyUnit.NANOMOLAR
        assert adapter._parse_potency_unit("") == PotencyUnit.NANOMOLAR
    
    def test_aggregate_activities_by_target(self):
        """Test activity aggregation by target."""
        adapter = ChEMBLAdapter()
        
        activities = [
            {'target_chembl_id': 'CHEMBL123', 'standard_type': 'Ki', 'standard_value': 100},
            {'target_chembl_id': 'CHEMBL123', 'standard_type': 'IC50', 'standard_value': 150},
            {'target_chembl_id': 'CHEMBL456', 'standard_type': 'Ki', 'standard_value': 50},
            {'target_chembl_id': 'CHEMBL123', 'standard_type': 'LogP', 'standard_value': 2.5},  # Not potency
        ]
        
        aggregated = adapter._aggregate_activities_by_target(activities)
        
        assert len(aggregated) == 2
        assert len(aggregated['CHEMBL123']) == 2  # Only Ki and IC50
        assert len(aggregated['CHEMBL456']) == 1
    
    def test_evidence_score_single_study(self):
        """Test evidence score with single study."""
        adapter = ChEMBLAdapter()
        
        activities = [
            {'standard_value': 100, 'standard_units': 'nM', 'standard_type': 'Ki'}
        ]
        
        score = adapter._calculate_evidence_score(activities)
        assert 0 <= score <= 1
        # Single study should have lower score than multiple
        assert score < 0.3
    
    def test_evidence_score_consistent_studies(self):
        """Test evidence score with consistent multiple studies."""
        adapter = ChEMBLAdapter()
        
        # Very consistent values (low CV)
        activities = [
            {'standard_value': 100, 'standard_units': 'nM', 'standard_type': 'Ki'},
            {'standard_value': 105, 'standard_units': 'nM', 'standard_type': 'Ki'},
            {'standard_value': 95, 'standard_units': 'nM', 'standard_type': 'Ki'},
            {'standard_value': 102, 'standard_units': 'nM', 'standard_type': 'Ki'},
        ]
        
        score = adapter._calculate_evidence_score(activities)
        assert score > 0.5  # Should be high due to consistency
    
    def test_evidence_score_inconsistent_studies(self):
        """Test evidence score with inconsistent studies."""
        adapter = ChEMBLAdapter()
        
        # Highly variable values (high CV)
        activities = [
            {'standard_value': 10, 'standard_units': 'nM', 'standard_type': 'Ki'},
            {'standard_value': 1000, 'standard_units': 'nM', 'standard_type': 'Ki'},
            {'standard_value': 50, 'standard_units': 'nM', 'standard_type': 'Ki'},
        ]
        
        score = adapter._calculate_evidence_score(activities)
        assert score < 0.5  # Should be lower due to inconsistency
    
    def test_evidence_score_many_studies(self):
        """Test evidence score increases with number of studies."""
        adapter = ChEMBLAdapter()
        
        # Create 15 consistent studies
        activities = [
            {'standard_value': 100 + i, 'standard_units': 'nM', 'standard_type': 'Ki'}
            for i in range(15)
        ]
        
        score = adapter._calculate_evidence_score(activities)
        assert score > 0.6  # Should be high with many consistent studies
    
    @patch('drug.chembl_adapter.requests.Session.get')
    def test_search_molecule_success(self, mock_get):
        """Test successful molecule search."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'molecules': [{'molecule_chembl_id': 'CHEMBL113', 'pref_name': 'CAFFEINE'}]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        adapter = ChEMBLAdapter()
        results = adapter.search_molecule("caffeine")
        
        assert len(results) == 1
        assert results[0]['molecule_chembl_id'] == 'CHEMBL113'
    
    @patch('drug.chembl_adapter.requests.Session.get')
    def test_get_molecule_activities_success(self, mock_get):
        """Test activity retrieval."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'activities': [
                {'target_chembl_id': 'CHEMBL123', 'standard_type': 'Ki', 'standard_value': 50}
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        adapter = ChEMBLAdapter()
        activities = adapter.get_molecule_activities("CHEMBL113")
        
        assert len(activities) == 1
        assert activities[0]['standard_type'] == 'Ki'


class TestDrugLoader:
    """Test high-level drug loader and merging logic."""
    
    def test_merge_profiles_non_overlapping(self):
        """Test merging profiles with completely different targets."""
        loader = DrugLoader()
        
        profile1 = DrugProfile(
            common_name="TestDrug",
            chembl_id="CHEMBL123",
            interactions=[
                TargetInteraction(
                    target_gene_symbol="TARGET1",
                    potency_measures=[PotencyMeasure(100, PotencyUnit.NANOMOLAR, "Ki")],
                    source_database="IUPHAR"
                )
            ],
            source_databases=["IUPHAR"]
        )
        
        profile2 = DrugProfile(
            common_name="TestDrug",
            chembl_id="CHEMBL123",
            interactions=[
                TargetInteraction(
                    target_gene_symbol="TARGET2",
                    potency_measures=[PotencyMeasure(50, PotencyUnit.NANOMOLAR, "Ki")],
                    source_database="ChEMBL"
                )
            ],
            source_databases=["ChEMBL"]
        )
        
        merged = loader._merge_profiles([profile1, profile2])
        
        assert len(merged.interactions) == 2
        assert set(merged.source_databases) == {"IUPHAR", "ChEMBL"}
        assert merged.chembl_id == "CHEMBL123"
    
    def test_merge_profiles_overlapping_targets(self):
        """Test merging with same target from both sources."""
        loader = DrugLoader(prefer_iuphar=True)
        
        profile1 = DrugProfile(
            common_name="TestDrug",
            interactions=[
                TargetInteraction(
                    target_gene_symbol="ADORA1",
                    potency_measures=[PotencyMeasure(100, PotencyUnit.NANOMOLAR, "Ki")],
                    evidence_score=0.9,
                    source_database="IUPHAR"
                )
            ],
            source_databases=["IUPHAR"]
        )
        
        profile2 = DrugProfile(
            common_name="TestDrug",
            interactions=[
                TargetInteraction(
                    target_gene_symbol="ADORA1",
                    potency_measures=[PotencyMeasure(120, PotencyUnit.NANOMOLAR, "Ki")],
                    evidence_score=0.7,
                    source_database="ChEMBL"
                )
            ],
            source_databases=["ChEMBL"]
        )
        
        merged = loader._merge_profiles([profile1, profile2])
        
        # Should have only one ADORA1 entry
        assert len(merged.interactions) == 1
        # Should prefer IUPHAR
        assert merged.interactions[0].source_database == "IUPHAR"
        assert merged.interactions[0].evidence_score == 0.9
    
    def test_merge_profiles_prefer_chembl(self):
        """Test merging with ChEMBL preference by evidence score."""
        loader = DrugLoader(prefer_iuphar=False)
        
        profile1 = DrugProfile(
            common_name="TestDrug",
            interactions=[
                TargetInteraction(
                    target_gene_symbol="ADORA1",
                    evidence_score=0.6,
                    source_database="IUPHAR"
                )
            ],
            source_databases=["IUPHAR"]
        )
        
        profile2 = DrugProfile(
            common_name="TestDrug",
            interactions=[
                TargetInteraction(
                    target_gene_symbol="ADORA1",
                    evidence_score=0.9,
                    source_database="ChEMBL"
                )
            ],
            source_databases=["ChEMBL"]
        )
        
        merged = loader._merge_profiles([profile1, profile2])
        
        # Should prefer higher evidence score
        assert merged.interactions[0].source_database == "ChEMBL"
        assert merged.interactions[0].evidence_score == 0.9
    
    def test_merge_profiles_combines_metadata(self):
        """Test that merging combines all metadata correctly."""
        loader = DrugLoader()
        
        profile1 = DrugProfile(
            common_name="Caffeine",
            synonyms=["1,3,7-Trimethylxanthine"],
            chembl_id="CHEMBL113",
            iuphar_ligand_id=None,
            is_approved=False,
            source_databases=["IUPHAR"]
        )
        
        profile2 = DrugProfile(
            common_name="Caffeine",
            synonyms=["Theine", "Guaranine"],
            chembl_id="CHEMBL113",
            iuphar_ligand_id=407,
            is_approved=True,
            source_databases=["ChEMBL"]
        )
        
        merged = loader._merge_profiles([profile1, profile2])
        
        # Should combine synonyms
        assert len(set(merged.synonyms)) >= 3
        # Should get both IDs
        assert merged.chembl_id == "CHEMBL113"
        assert merged.iuphar_ligand_id == 407
        # Should be approved if either says so
        assert merged.is_approved is True
        # Should track both sources
        assert set(merged.source_databases) == {"IUPHAR", "ChEMBL"}
    
    def test_merge_profiles_tracks_merge_metadata(self):
        """Test that merge metadata is recorded."""
        loader = DrugLoader()
        
        profile1 = DrugProfile(
            common_name="Test",
            interactions=[TargetInteraction("A")],
            source_databases=["IUPHAR"]
        )
        profile2 = DrugProfile(
            common_name="Test",
            interactions=[TargetInteraction("B")],
            source_databases=["ChEMBL"]
        )
        
        merged = loader._merge_profiles([profile1, profile2])
        
        assert 'merged_from' in merged.uncertainty_metadata
        assert 'n_interactions_total' in merged.uncertainty_metadata
        assert 'n_interactions_merged' in merged.uncertainty_metadata
        assert merged.uncertainty_metadata['n_interactions_total'] == 2
    
    def test_get_primary_targets_integration(self):
        """Test the convenience method for getting primary targets."""
        loader = DrugLoader()
        
        # Mock the load_drug_profile method
        mock_profile = DrugProfile(
            common_name="TestDrug",
            interactions=[
                TargetInteraction(
                    target_gene_symbol="TARGET1",
                    potency_measures=[PotencyMeasure(50, PotencyUnit.NANOMOLAR, "Ki")]
                ),
                TargetInteraction(
                    target_gene_symbol="TARGET2",
                    potency_measures=[PotencyMeasure(10, PotencyUnit.NANOMOLAR, "Ki")]
                ),
                TargetInteraction(
                    target_gene_symbol="TARGET3",
                    potency_measures=[PotencyMeasure(200, PotencyUnit.NANOMOLAR, "Ki")]
                ),
            ]
        )
        
        loader.load_drug_profile = Mock(return_value=mock_profile)
        
        targets = loader.get_primary_targets("test_drug", top_n=2)
        
        assert len(targets) == 2
        assert targets[0].target_gene_symbol == "TARGET2"  # 10 nM (best)
        assert targets[1].target_gene_symbol == "TARGET1"  # 50 nM (second best)
    
    def test_get_primary_targets_drug_not_found(self):
        """Test primary targets when drug is not found."""
        loader = DrugLoader()
        loader.load_drug_profile = Mock(return_value=None)
        
        targets = loader.get_primary_targets("nonexistent_drug")
        
        assert targets == []


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_drug_profile(self):
        """Test drug profile with no interactions."""
        profile = DrugProfile(common_name="Empty", interactions=[])
        
        primary = profile.get_primary_targets()
        assert primary == []
    
    def test_interaction_with_all_unknown_units(self):
        """Test interaction where all potencies have unknown units."""
        interaction = TargetInteraction(
            target_gene_symbol="TEST",
            potency_measures=[
                PotencyMeasure(100, PotencyUnit.UNKNOWN, "Ki"),
                PotencyMeasure(50, PotencyUnit.UNKNOWN, "IC50"),
            ]
        )
        
        assert interaction.get_best_potency_nm() is None
    
    def test_drug_profile_serialization_roundtrip(self):
        """Test that serialization preserves data structure."""
        original = DrugProfile(
            common_name="Test",
            synonyms=["Syn1", "Syn2"],
            chembl_id="CHEMBL123",
            interactions=[
                TargetInteraction(
                    target_gene_symbol="TARGET1",
                    interaction_type=InteractionType.AGONIST,
                    potency_measures=[
                        PotencyMeasure(50, PotencyUnit.NANOMOLAR, "Ki", 
                                     assay_description="Test assay",
                                     pubmed_id="12345678")
                    ]
                )
            ],
            is_approved=True
        )
        
        serialized = original.to_dict()
        
        # Check key fields preserved
        assert serialized['common_name'] == "Test"
        assert len(serialized['synonyms']) == 2
        assert serialized['chembl_id'] == "CHEMBL123"
        assert serialized['is_approved'] is True
        assert len(serialized['interactions']) == 1
        assert serialized['interactions'][0]['interaction_type'] == 'agonist'
        assert serialized['interactions'][0]['potency_measures'][0]['value'] == 50
        assert serialized['interactions'][0]['potency_measures'][0]['pubmed_id'] == "12345678"
    
    def test_potency_measure_with_zero_value(self):
        """Test that zero potency values are handled (edge case)."""
        p = PotencyMeasure(value=0.0, unit=PotencyUnit.NANOMOLAR, measure_type="Ki")
        # Should convert to 0.0, not None
        assert p.to_nanomolar() == 0.0
    
    def test_very_small_potency_conversion(self):
        """Test conversion of very small (picomolar) potencies."""
        p = PotencyMeasure(value=1.0, unit=PotencyUnit.PICOMOLAR, measure_type="Ki")
        assert p.to_nanomolar() == 0.001
        
        # Ensure precision is maintained
        p2 = PotencyMeasure(value=50.5, unit=PotencyUnit.PICOMOLAR, measure_type="IC50")
        assert p2.to_nanomolar() == 0.0505
    
    def test_very_large_potency_conversion(self):
        """Test conversion of very large (molar/millimolar) potencies."""
        p = PotencyMeasure(value=1.0, unit=PotencyUnit.MOLAR, measure_type="Ki")
        assert p.to_nanomolar() == 1e9
        
        p2 = PotencyMeasure(value=10.0, unit=PotencyUnit.MILLIMOLAR, measure_type="IC50")
        assert p2.to_nanomolar() == 10000000.0
    
    def test_interaction_type_case_insensitivity(self):
        """Test that interaction type parsing is case-insensitive."""
        adapter = IUPHARAdapter()
        
        assert adapter._parse_interaction_type("agonist") == InteractionType.AGONIST
        assert adapter._parse_interaction_type("AGONIST") == InteractionType.AGONIST
        assert adapter._parse_interaction_type("Agonist") == InteractionType.AGONIST
        assert adapter._parse_interaction_type("aGoNiSt") == InteractionType.AGONIST


class TestIntegration:
    """Integration tests for end-to-end workflows."""
    
    @patch('drug.iuphar_adapter.IUPHARAdapter.fetch_drug_profile')
    @patch('drug.chembl_adapter.ChEMBLAdapter.fetch_drug_profile')
    def test_full_drug_loading_workflow(self, mock_chembl_fetch, mock_iuphar_fetch):
        """Test complete workflow from drug name to merged profile."""
        # Mock IUPHAR profile
        iuphar_profile = DrugProfile(
            common_name="caffeine",
            is_approved=True,
            interactions=[
                TargetInteraction(
                    target_gene_symbol="ADORA1",
                    target_uniprot_id="P30542",
                    interaction_type=InteractionType.ANTAGONIST,
                    potency_measures=[PotencyMeasure(12.0, PotencyUnit.NANOMOLAR, "affinity")],
                    source_database="IUPHAR"
                )
            ],
            source_databases=["IUPHAR"]
        )
        
        # Mock ChEMBL profile
        chembl_profile = DrugProfile(
            common_name="CAFFEINE",
            interactions=[
                TargetInteraction(
                    target_gene_symbol="ADORA2A",
                    target_uniprot_id="P29274",
                    target_name="Adenosine receptor A2a",
                    potency_measures=[PotencyMeasure(15.0, PotencyUnit.NANOMOLAR, "Ki")],
                    evidence_score=0.8,
                    source_database="ChEMBL"
                )
            ],
            source_databases=["ChEMBL"]
        )
        
        mock_iuphar_fetch.return_value = iuphar_profile
        mock_chembl_fetch.return_value = chembl_profile
        
        # Run the workflow
        loader = DrugLoader()
        profile = loader.load_drug_profile("caffeine")
        
        # Verify results
        assert profile is not None
        assert profile.common_name in ["caffeine", "CAFFEINE"]
        assert len(profile.interactions) == 2  # One from each source
        assert "IUPHAR" in profile.source_databases
        assert "ChEMBL" in profile.source_databases


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
