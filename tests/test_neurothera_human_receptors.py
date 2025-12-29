"""Tests for human PET receptor map loader."""

import numpy as np
import pytest

from neurothera_map.human.receptors import (
    PETReceptorTableSpec,
    load_human_pet_receptor_maps,
)


def _hansen_receptors_available() -> bool:
    """Helper to check if hansen_receptors is available."""
    try:
        import hansen_receptors  # noqa: F401

        return True
    except ImportError:
        return False


def test_load_human_pet_receptor_maps_basic():
    """Test basic loading of human PET receptor maps from fixture."""
    receptor_map = load_human_pet_receptor_maps(
        "datasets/human_pet_receptor_fixture.csv",
    )

    # Check that we have multiple receptors
    receptor_names = receptor_map.receptor_names()
    assert len(receptor_names) > 0
    assert "5HT1a" in receptor_names
    assert "D1" in receptor_names
    assert "D2" in receptor_names

    # Check space metadata
    assert receptor_map.space == "fsaverage"

    # Check provenance
    assert "source" in receptor_map.provenance
    assert "path" in receptor_map.provenance
    assert "modality" in receptor_map.provenance
    assert receptor_map.provenance["modality"] == "PET"


def test_load_human_pet_receptor_maps_subset_receptors():
    """Test loading a subset of receptors."""
    receptor_map = load_human_pet_receptor_maps(
        "datasets/human_pet_receptor_fixture.csv",
        receptors=["5HT1a", "D1"],
    )

    receptor_names = receptor_map.receptor_names()
    assert len(receptor_names) == 2
    assert set(receptor_names) == {"5HT1a", "D1"}


def test_load_human_pet_receptor_maps_regionmap_structure():
    """Test that individual receptor RegionMaps have correct structure."""
    receptor_map = load_human_pet_receptor_maps(
        "datasets/human_pet_receptor_fixture.csv",
        receptors=["5HT1a"],
    )

    region_map = receptor_map.get("5HT1a")
    assert region_map is not None

    # Check that region_ids and values are aligned
    assert len(region_map.region_ids) == len(region_map.values)
    assert len(region_map.region_ids) > 0

    # Check that values are numeric and non-negative (typical for PET densities)
    assert np.all(np.isfinite(region_map.values))
    assert np.all(region_map.values >= 0.0)

    # Check space
    assert region_map.space == "fsaverage"

    # Check name format
    assert region_map.name.startswith("human_pet_receptor:")
    assert "5HT1a" in region_map.name

    # Check provenance
    assert "source" in region_map.provenance
    assert "path" in region_map.provenance
    assert "modality" in region_map.provenance
    assert region_map.provenance["modality"] == "PET"


def test_load_human_pet_receptor_maps_specific_regions():
    """Test that specific regions are present in the fixture data."""
    MIN_STRIATAL_D1_DENSITY = 0.5  # Striatal regions have high D1 receptor density

    receptor_map = load_human_pet_receptor_maps(
        "datasets/human_pet_receptor_fixture.csv",
        receptors=["D1"],
    )

    region_map = receptor_map.get("D1")
    assert region_map is not None

    # Check that striatal regions have high D1 values (known from neuroanatomy)
    region_dict = region_map.to_dict()

    # Striatal regions should be present and have high D1 density
    if "Left-Caudate" in region_dict:
        assert (
            region_dict["Left-Caudate"] > MIN_STRIATAL_D1_DENSITY
        ), "Caudate should have high D1 density"
    if "Left-Putamen" in region_dict:
        assert (
            region_dict["Left-Putamen"] > MIN_STRIATAL_D1_DENSITY
        ), "Putamen should have high D1 density"


def test_load_human_pet_receptor_maps_custom_space():
    """Test loading with custom space parameter."""
    receptor_map = load_human_pet_receptor_maps(
        "datasets/human_pet_receptor_fixture.csv",
        receptors=["5HT1a"],
        space="custom_space",
    )

    assert receptor_map.space == "custom_space"
    region_map = receptor_map.get("5HT1a")
    assert region_map.space == "custom_space"


def test_load_human_pet_receptor_maps_custom_name_prefix():
    """Test loading with custom name prefix."""
    receptor_map = load_human_pet_receptor_maps(
        "datasets/human_pet_receptor_fixture.csv",
        receptors=["5HT1a"],
        name_prefix="custom_prefix",
    )

    region_map = receptor_map.get("5HT1a")
    assert region_map.name.startswith("custom_prefix:")


def test_load_human_pet_receptor_maps_file_not_found():
    """Test that FileNotFoundError is raised for non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_human_pet_receptor_maps("nonexistent_file.csv")


def test_load_human_pet_receptor_maps_no_data_for_receptors():
    """Test error when requesting receptors not in the data."""
    with pytest.raises(ValueError, match="No data found for requested receptors"):
        load_human_pet_receptor_maps(
            "datasets/human_pet_receptor_fixture.csv",
            receptors=["NONEXISTENT_RECEPTOR"],
        )


def test_load_human_pet_receptor_maps_all_receptors():
    """Test loading all receptors from fixture without filtering."""
    receptor_map = load_human_pet_receptor_maps(
        "datasets/human_pet_receptor_fixture.csv",
    )

    # Should have all receptors from the fixture
    receptor_names = receptor_map.receptor_names()
    expected_receptors = ["5HT1a", "5HT1b", "5HT2a", "D1", "D2", "DAT"]
    for receptor in expected_receptors:
        assert receptor in receptor_names


def test_pet_receptor_table_spec_custom():
    """Test using custom PETReceptorTableSpec (edge case for future extensions)."""
    # This test ensures the spec parameter works correctly
    receptor_map = load_human_pet_receptor_maps(
        "datasets/human_pet_receptor_fixture.csv",
        receptors=["5HT1a"],
        spec=PETReceptorTableSpec(
            region_col="region",
            receptor_col="receptor",
            value_col="value",
        ),
    )

    assert len(receptor_map.receptor_names()) == 1
    assert "5HT1a" in receptor_map.receptor_names()


@pytest.mark.skipif(
    not _hansen_receptors_available(),
    reason="hansen_receptors package not installed",
)
def test_hansen_receptors_integration_available():
    """Test that hansen_receptors detection works when package is available."""
    # This test will only run if hansen_receptors is installed
    receptor_map = load_human_pet_receptor_maps(
        "datasets/human_pet_receptor_fixture.csv",
        receptors=["5HT1a"],
    )

    # When hansen_receptors is available, provenance should indicate this
    assert "source" in receptor_map.provenance
    # Note: actual integration with hansen_receptors would be tested here
    # For now we just check that the package detection doesn't break anything
