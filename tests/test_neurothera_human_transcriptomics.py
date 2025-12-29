"""Tests for human transcriptomics module."""

import numpy as np
import pytest

from neurothera_map.human.transcriptomics import (
    TranscriptomicTableSpec,
    load_transcriptomic_map_from_csv,
    load_transcriptomic_map_with_abagen,
)


def test_load_transcriptomic_map_from_csv_long_format():
    """Test loading transcriptomic data from long-format CSV fixture."""
    rm = load_transcriptomic_map_from_csv(
        "datasets/human_ahba_expression_fixture.csv",
        genes=["DRD1", "DRD2"],
    )

    assert set(rm.receptor_names()) == {"DRD1", "DRD2"}
    assert rm.space == "mni152"
    assert rm.provenance["modality"] == "transcriptomics"
    assert rm.provenance["atlas"] == "ahba"

    # Check DRD1 data
    drd1 = rm.get("DRD1")
    assert drd1 is not None
    assert len(drd1.region_ids) == 6  # 6 regions in fixture
    assert "lh_caudate" in drd1.region_ids
    assert "rh_caudate" in drd1.region_ids

    # DRD1 should be highly expressed in caudate (striatum)
    drd1_dict = drd1.to_dict()
    assert drd1_dict["lh_caudate"] > 0.7
    assert drd1_dict["rh_caudate"] > 0.7


def test_load_transcriptomic_map_from_csv_all_genes():
    """Test loading all genes from fixture."""
    rm = load_transcriptomic_map_from_csv("datasets/human_ahba_expression_fixture.csv")

    expected_genes = {"DRD1", "DRD2", "HTR1A", "HTR2A"}
    assert set(rm.receptor_names()) == expected_genes


def test_load_transcriptomic_map_from_csv_with_custom_spec():
    """Test loading with custom column specification."""
    # Create a temporary CSV with different column names
    import tempfile
    from pathlib import Path

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("brain_region,gene_symbol,expr_value\n")
        f.write("region1,GENEA,1.5\n")
        f.write("region1,GENEB,2.5\n")
        f.write("region2,GENEA,3.5\n")
        temp_path = f.name

    try:
        spec = TranscriptomicTableSpec(
            region_col="brain_region",
            gene_col="gene_symbol",
            value_col="expr_value",
        )
        rm = load_transcriptomic_map_from_csv(temp_path, spec=spec)

        assert set(rm.receptor_names()) == {"GENEA", "GENEB"}
        genea = rm.get("GENEA")
        assert genea is not None
        assert len(genea.region_ids) == 2
    finally:
        Path(temp_path).unlink()


def test_load_transcriptomic_map_from_csv_subset_genes():
    """Test loading only a subset of genes."""
    rm = load_transcriptomic_map_from_csv(
        "datasets/human_ahba_expression_fixture.csv",
        genes=["HTR1A"],
    )

    assert rm.receptor_names() == ["HTR1A"]
    htr1a = rm.get("HTR1A")
    assert htr1a is not None


def test_load_transcriptomic_map_from_csv_provenance():
    """Test that provenance metadata is correctly recorded."""
    rm = load_transcriptomic_map_from_csv("datasets/human_ahba_expression_fixture.csv")

    assert "source" in rm.provenance
    assert "path" in rm.provenance
    assert "modality" in rm.provenance
    assert "atlas" in rm.provenance

    assert rm.provenance["source"] == "csv"
    assert rm.provenance["modality"] == "transcriptomics"
    assert rm.provenance["atlas"] == "ahba"

    # Check per-gene provenance
    drd1 = rm.get("DRD1")
    assert drd1 is not None
    assert "source" in drd1.provenance
    assert "format" in drd1.provenance
    assert drd1.provenance["format"] == "long"


def test_load_transcriptomic_map_from_csv_invalid_format():
    """Test that invalid CSV format raises appropriate error."""
    import tempfile
    from pathlib import Path

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("invalid_col1,invalid_col2\n")
        f.write("val1,val2\n")
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="Unrecognized transcriptomic CSV format"):
            load_transcriptomic_map_from_csv(temp_path)
    finally:
        Path(temp_path).unlink()


def test_load_transcriptomic_map_from_csv_wide_format():
    """Test loading from wide-format CSV."""
    import tempfile
    from pathlib import Path

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("region,GENE1,GENE2,GENE3\n")
        f.write("regionA,1.0,2.0,3.0\n")
        f.write("regionB,1.5,2.5,3.5\n")
        temp_path = f.name

    try:
        rm = load_transcriptomic_map_from_csv(temp_path)

        assert set(rm.receptor_names()) == {"GENE1", "GENE2", "GENE3"}
        gene1 = rm.get("GENE1")
        assert gene1 is not None
        assert len(gene1.region_ids) == 2
        assert gene1.values[0] == 1.0
        assert gene1.values[1] == 1.5
    finally:
        Path(temp_path).unlink()


@pytest.mark.skip(reason="abagen is an optional dependency, only run if installed")
def test_load_transcriptomic_map_with_abagen_requires_installation():
    """Test that abagen function raises ImportError when abagen not installed."""
    # This test will be skipped by default
    # If abagen is installed, it would actually run and potentially download data
    try:
        import abagen  # noqa: F401

        pytest.skip("abagen is installed, skipping ImportError test")
    except ImportError:
        # abagen not installed, test should raise ImportError
        with pytest.raises(ImportError, match="abagen is not installed"):
            load_transcriptomic_map_with_abagen(atlas="schaefer", n_parcels=100)


def test_load_transcriptomic_map_with_abagen_not_installed():
    """Test graceful handling when abagen is not available."""
    # This test checks that the function provides helpful error message
    try:
        import abagen  # noqa: F401

        pytest.skip("abagen is installed, cannot test ImportError handling")
    except ImportError:
        # Verify that the function raises ImportError with helpful message
        with pytest.raises(ImportError) as exc_info:
            load_transcriptomic_map_with_abagen()

        error_msg = str(exc_info.value)
        assert "abagen is not installed" in error_msg
        assert "pip install abagen" in error_msg
        assert "load_transcriptomic_map_from_csv" in error_msg


def test_receptor_map_keyed_by_gene_symbols():
    """Test that ReceptorMap is correctly keyed by gene symbols."""
    rm = load_transcriptomic_map_from_csv("datasets/human_ahba_expression_fixture.csv")

    # Test that we can access genes by their symbols
    for gene in ["DRD1", "DRD2", "HTR1A", "HTR2A"]:
        gene_map = rm.get(gene)
        assert gene_map is not None
        assert isinstance(gene_map.name, str)
        assert gene in gene_map.name


def test_region_map_values_are_floats():
    """Test that expression values are properly converted to floats."""
    rm = load_transcriptomic_map_from_csv("datasets/human_ahba_expression_fixture.csv")

    for gene_name in rm.receptor_names():
        gene_map = rm.get(gene_name)
        assert gene_map is not None
        assert gene_map.values.dtype == np.float64
        assert all(np.isfinite(gene_map.values))
