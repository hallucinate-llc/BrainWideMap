"""Tests for human ActivityMap ingestion from parcellated tables.

These tests are designed to run offline using fixture data.
Optional NIfTI tests are skipped if neuroimaging libraries are not available.
"""
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from neurothera_map.core.types import ActivityMap
from neurothera_map.human.activity import (
    NIBABEL_AVAILABLE,
    activity_map_from_parcellated_table,
)

# Check if optional dependencies are available for NIfTI tests
NIFTI_SUPPORT = NIBABEL_AVAILABLE


@pytest.fixture
def fixture_table_path():
    """Path to the offline fixture table in datasets/."""
    repo_root = Path(__file__).parent.parent
    return repo_root / "datasets" / "human_activity_parcellated_fixture.csv"


@pytest.fixture
def temp_csv_file():
    """Create a temporary CSV file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("region,value\n")
        f.write("ACC,0.5\n")
        f.write("DLPFC,0.3\n")
        f.write("mPFC,-0.2\n")
        temp_path = Path(f.name)
    yield temp_path
    temp_path.unlink()


def test_activity_map_from_parcellated_table_basic(fixture_table_path):
    """Test basic loading from the fixture table."""
    am = activity_map_from_parcellated_table(fixture_table_path)

    assert isinstance(am, ActivityMap)
    assert len(am.region_ids) > 0
    assert len(am.values) == len(am.region_ids)
    assert am.space == "mni152"
    assert "source_file" in am.provenance


def test_activity_map_from_parcellated_table_region_values(fixture_table_path):
    """Test that specific regions and values are correctly loaded."""
    am = activity_map_from_parcellated_table(fixture_table_path)

    # Check that the fixture data is correctly parsed
    region_dict = am.to_dict()
    
    # The fixture should contain these regions
    assert "ACC" in region_dict
    assert "DLPFC" in region_dict
    assert "Hippocampus" in region_dict
    
    # Check specific values from fixture
    assert region_dict["ACC"] == 0.25
    assert region_dict["DLPFC"] == 0.15
    assert region_dict["mPFC"] == -0.10


def test_activity_map_from_parcellated_table_custom_columns(temp_csv_file):
    """Test loading with custom column names."""
    # Create a file with custom column names
    df = pd.DataFrame({
        "brain_region": ["A", "B", "C"],
        "activation": [1.0, 2.0, 3.0],
    })
    custom_path = temp_csv_file.with_suffix(".custom.csv")
    df.to_csv(custom_path, index=False)

    try:
        am = activity_map_from_parcellated_table(
            custom_path,
            region_col="brain_region",
            value_col="activation",
        )

        assert len(am.region_ids) == 3
        assert set(am.region_ids) == {"A", "B", "C"}
        region_dict = am.to_dict()
        assert region_dict["A"] == 1.0
        assert region_dict["B"] == 2.0
        assert region_dict["C"] == 3.0
    finally:
        custom_path.unlink()


def test_activity_map_from_parcellated_table_custom_space_name(fixture_table_path):
    """Test that space and name parameters are correctly set."""
    am = activity_map_from_parcellated_table(
        fixture_table_path,
        space="custom_space",
        name="test_activity",
    )

    assert am.space == "custom_space"
    assert am.name == "test_activity"


def test_activity_map_from_parcellated_table_provenance(fixture_table_path):
    """Test that provenance information is correctly recorded."""
    am = activity_map_from_parcellated_table(
        fixture_table_path,
        region_col="region",
        value_col="value",
    )

    assert "source_file" in am.provenance
    assert "region_col" in am.provenance
    assert "value_col" in am.provenance
    assert "n_regions" in am.provenance
    
    assert am.provenance["region_col"] == "region"
    assert am.provenance["value_col"] == "value"
    assert am.provenance["n_regions"] == len(am.region_ids)


def test_activity_map_from_parcellated_table_file_not_found():
    """Test error handling for missing file."""
    with pytest.raises(FileNotFoundError):
        activity_map_from_parcellated_table("/nonexistent/path/file.csv")


def test_activity_map_from_parcellated_table_missing_region_column(temp_csv_file):
    """Test error handling when region column is missing."""
    df = pd.DataFrame({"wrong_col": ["A", "B"], "value": [1.0, 2.0]})
    df.to_csv(temp_csv_file, index=False)

    with pytest.raises(ValueError, match="Column 'region' not found"):
        activity_map_from_parcellated_table(temp_csv_file)


def test_activity_map_from_parcellated_table_missing_value_column(temp_csv_file):
    """Test error handling when value column is missing."""
    df = pd.DataFrame({"region": ["A", "B"], "wrong_col": [1.0, 2.0]})
    df.to_csv(temp_csv_file, index=False)

    with pytest.raises(ValueError, match="Column 'value' not found"):
        activity_map_from_parcellated_table(temp_csv_file)


def test_activity_map_from_parcellated_table_empty_file(temp_csv_file):
    """Test error handling for empty table."""
    df = pd.DataFrame({"region": [], "value": []})
    df.to_csv(temp_csv_file, index=False)

    with pytest.raises(ValueError, match="contains no data rows"):
        activity_map_from_parcellated_table(temp_csv_file)


def test_activity_map_from_parcellated_table_with_nan_values(temp_csv_file):
    """Test that rows with NaN values are handled gracefully."""
    df = pd.DataFrame({
        "region": ["A", "B", "C", "D"],
        "value": [1.0, np.nan, 3.0, 4.0],
    })
    df.to_csv(temp_csv_file, index=False)

    am = activity_map_from_parcellated_table(temp_csv_file)

    # Should skip the row with NaN
    assert len(am.region_ids) == 3
    assert set(am.region_ids) == {"A", "C", "D"}


def test_activity_map_from_parcellated_table_all_nan_values(temp_csv_file):
    """Test error handling when all values are NaN."""
    df = pd.DataFrame({
        "region": ["A", "B", "C"],
        "value": [np.nan, np.nan, np.nan],
    })
    df.to_csv(temp_csv_file, index=False)

    with pytest.raises(ValueError, match="No valid.*pairs found"):
        activity_map_from_parcellated_table(temp_csv_file)


def test_activity_map_from_parcellated_table_numeric_string_values(temp_csv_file):
    """Test that numeric values stored as strings are correctly parsed."""
    # Write CSV with string numbers
    with open(temp_csv_file, "w") as f:
        f.write("region,value\n")
        f.write("A,1.5\n")
        f.write("B,2.5\n")
    
    am = activity_map_from_parcellated_table(temp_csv_file)
    
    assert len(am.region_ids) == 2
    assert am.to_dict()["A"] == 1.5
    assert am.to_dict()["B"] == 2.5


def test_activity_map_from_parcellated_table_negative_values(fixture_table_path):
    """Test that negative values are correctly handled."""
    am = activity_map_from_parcellated_table(fixture_table_path)
    
    region_dict = am.to_dict()
    # mPFC has negative value in fixture
    assert region_dict["mPFC"] < 0


def test_activity_map_default_name_from_filename():
    """Test that default name is derived from filename."""
    # Create a temporary file with a specific name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, prefix="my_activity_data_") as f:
        f.write("region,value\n")
        f.write("A,1.0\n")
        specific_path = Path(f.name)
    
    try:
        am = activity_map_from_parcellated_table(specific_path)
        # Name should be the stem (filename without extension)
        assert am.name == specific_path.stem
    finally:
        if specific_path.exists():
            specific_path.unlink()


@pytest.mark.skipif(not NIFTI_SUPPORT, reason="nibabel not available")
def test_nifti_import_available():
    """Test that NIfTI support is available when dependencies are installed."""
    from neurothera_map.human.activity import activity_map_from_nifti
    
    # Just check the function exists and can be called with correct signature
    assert callable(activity_map_from_nifti)


@pytest.mark.skipif(NIFTI_SUPPORT, reason="Testing behavior without nibabel")
def test_nifti_import_error_when_not_available():
    """Test that appropriate error is raised when NIfTI dependencies are missing."""
    from neurothera_map.human.activity import activity_map_from_nifti
    
    with pytest.raises(ImportError, match="nibabel is required"):
        activity_map_from_nifti("dummy.nii.gz", "atlas.nii.gz")


def test_activity_map_integration_with_core_types(fixture_table_path):
    """Test that ActivityMap returned integrates well with core types."""
    am = activity_map_from_parcellated_table(fixture_table_path)
    
    # Test to_dict() method inherited from RegionMap
    region_dict = am.to_dict()
    assert isinstance(region_dict, dict)
    assert all(isinstance(k, str) for k in region_dict.keys())
    assert all(isinstance(v, float) for v in region_dict.values())
    
    # Test reindex method inherited from RegionMap
    new_regions = ["ACC", "DLPFC", "NewRegion"]
    reindexed = am.reindex(new_regions)
    assert len(reindexed.region_ids) == 3
    assert np.isnan(reindexed.to_dict()["NewRegion"])  # Fill value for missing region


def test_activity_map_immutability(fixture_table_path):
    """Test that ActivityMap is immutable (frozen dataclass)."""
    am = activity_map_from_parcellated_table(fixture_table_path)
    
    # Should not be able to modify frozen dataclass
    with pytest.raises((AttributeError, TypeError)):
        am.name = "new_name"
    
    with pytest.raises((AttributeError, TypeError)):
        am.space = "new_space"
