from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Sequence

import numpy as np
import pandas as pd

from ..core.types import ReceptorMap, RegionMap


@dataclass(frozen=True)
class TranscriptomicTableSpec:
    """Column specification for parcellated transcriptomic expression tables."""

    region_col: str = "region"
    gene_col: str = "gene"
    value_col: str = "expression"
    uncertainty_col: Optional[str] = None


def load_transcriptomic_map_from_csv(
    path: str | Path,
    *,
    genes: Optional[Sequence[str]] = None,
    spec: TranscriptomicTableSpec = TranscriptomicTableSpec(),
    space: str = "mni152",
    name_prefix: str = "human_transcriptomics",
) -> ReceptorMap:
    """Load human transcriptomic expression data into a `ReceptorMap`.

    This is the Phase 2.2 MVP connector for AHBA (Allen Human Brain Atlas)
    transcriptomic expression summaries in an *offline* form: you provide a CSV
    table that already contains parcellated expression summaries.

    Supported CSV layouts:

    1) Long format (recommended):
       - columns: region, gene, expression (and optionally uncertainty)

    2) Wide format:
       - one row per region
       - columns: region, <GENE_1>, <GENE_2>, ...

    Args:
        path: CSV file path containing parcellated expression data.
        genes: Optional subset of genes to load.
        spec: Column names for long-format CSV.
        space: Space label (default: "mni152").
        name_prefix: Prefix used for `RegionMap.name`.

    Returns:
        ReceptorMap keyed by gene symbols.

    Example:
        >>> rm = load_transcriptomic_map_from_csv(
        ...     "datasets/human_ahba_expression_fixture.csv",
        ...     genes=["DRD1", "DRD2"]
        ... )
        >>> drd1 = rm.get("DRD1")
    """
    p = Path(path)
    df = pd.read_csv(p)

    if spec.gene_col in df.columns and spec.value_col in df.columns:
        return _load_long_format(
            df, genes=genes, spec=spec, space=space, name_prefix=name_prefix, src=p
        )

    if spec.region_col in df.columns:
        return _load_wide_format(
            df, genes=genes, region_col=spec.region_col, space=space, name_prefix=name_prefix, src=p
        )

    raise ValueError(
        "Unrecognized transcriptomic CSV format. Expected long format with columns "
        f"'{spec.region_col}', '{spec.gene_col}', '{spec.value_col}' "
        "or wide format with a region column and gene columns."
    )


def _load_long_format(
    df: pd.DataFrame,
    *,
    genes: Optional[Sequence[str]],
    spec: TranscriptomicTableSpec,
    space: str,
    name_prefix: str,
    src: Path,
) -> ReceptorMap:
    if spec.region_col not in df.columns:
        raise ValueError(f"Missing required column '{spec.region_col}'")

    work = df.copy()
    work[spec.region_col] = work[spec.region_col].astype(str)
    work[spec.gene_col] = work[spec.gene_col].astype(str)

    if genes is not None:
        keep = {str(g) for g in genes}
        work = work[work[spec.gene_col].isin(keep)]

    genes_out: Dict[str, RegionMap] = {}

    for gene, sub in work.groupby(spec.gene_col, sort=True):
        sub2 = sub[
            [spec.region_col, spec.value_col]
            + ([spec.uncertainty_col] if spec.uncertainty_col else [])
        ].copy()
        sub2 = sub2.dropna(subset=[spec.value_col])
        sub2 = sub2.groupby(spec.region_col, as_index=False).mean(numeric_only=True)
        sub2 = sub2.sort_values(spec.region_col)

        region_ids = sub2[spec.region_col].to_numpy(dtype=str)
        values = sub2[spec.value_col].to_numpy(dtype=float)

        uncertainty = None
        if spec.uncertainty_col and spec.uncertainty_col in sub2.columns:
            uncertainty = sub2[spec.uncertainty_col].to_numpy(dtype=float)

        genes_out[str(gene)] = RegionMap(
            region_ids=region_ids,
            values=values,
            uncertainty=uncertainty,
            space=space,
            name=f"{name_prefix}:{gene}",
            provenance={
                "source": "csv",
                "path": str(src),
                "format": "long",
                "region_col": spec.region_col,
                "value_col": spec.value_col,
            },
        )

    return ReceptorMap(
        receptors=genes_out,
        space=space,
        provenance={
            "source": "csv",
            "path": str(src),
            "modality": "transcriptomics",
            "atlas": "ahba",
        },
    )


def _load_wide_format(
    df: pd.DataFrame,
    *,
    genes: Optional[Sequence[str]],
    region_col: str,
    space: str,
    name_prefix: str,
    src: Path,
) -> ReceptorMap:
    work = df.copy()
    work[region_col] = work[region_col].astype(str)

    gene_cols = [c for c in work.columns if c != region_col]
    if len(gene_cols) == 0:
        raise ValueError("Wide-format transcriptomic CSV has no gene columns")

    if genes is not None:
        keep = {str(g) for g in genes}
        gene_cols = [c for c in gene_cols if str(c) in keep]

    work = work[[region_col] + gene_cols]
    work = work.sort_values(region_col)
    region_ids = work[region_col].to_numpy(dtype=str)

    genes_out: Dict[str, RegionMap] = {}
    for gene in gene_cols:
        values = pd.to_numeric(work[gene], errors="coerce").to_numpy(dtype=float)
        genes_out[str(gene)] = RegionMap(
            region_ids=region_ids,
            values=values,
            space=space,
            name=f"{name_prefix}:{gene}",
            provenance={
                "source": "csv",
                "path": str(src),
                "format": "wide",
                "region_col": region_col,
            },
        )

    return ReceptorMap(
        receptors=genes_out,
        space=space,
        provenance={
            "source": "csv",
            "path": str(src),
            "modality": "transcriptomics",
            "atlas": "ahba",
        },
    )


def load_transcriptomic_map_with_abagen(
    atlas: str = "schaefer",
    n_parcels: int = 400,
    genes: Optional[Sequence[str]] = None,
    space: str = "mni152",
    name_prefix: str = "human_transcriptomics_abagen",
    **abagen_kwargs,
) -> ReceptorMap:
    """Load human transcriptomic expression using abagen (optional dependency).

    This function requires abagen to be installed. If abagen is not available,
    an ImportError will be raised with installation instructions.

    Args:
        atlas: Parcellation atlas name (default: "schaefer").
        n_parcels: Number of parcels (default: 400).
        genes: Optional subset of gene symbols to include.
        space: Space label (default: "mni152").
        name_prefix: Prefix used for `RegionMap.name`.
        **abagen_kwargs: Additional keyword arguments passed to abagen.get_expression_data().

    Returns:
        ReceptorMap keyed by gene symbols.

    Raises:
        ImportError: If abagen is not installed.

    Example:
        >>> try:
        ...     rm = load_transcriptomic_map_with_abagen(
        ...         atlas="schaefer",
        ...         n_parcels=400,
        ...         genes=["DRD1", "DRD2"]
        ...     )
        ... except ImportError:
        ...     print("abagen not installed, using offline fixture instead")
        ...     rm = load_transcriptomic_map_from_csv("datasets/human_ahba_expression_fixture.csv")
    """
    try:
        import abagen
    except ImportError as e:
        raise ImportError(
            "abagen is not installed. To use this function, install it with:\n"
            "  pip install abagen\n"
            "Alternatively, use load_transcriptomic_map_from_csv() with pre-parcellated data."
        ) from e

    # Get expression data from abagen
    # Note: This will download AHBA data if not already cached
    expression_df = abagen.get_expression_data(
        atlas=atlas,
        n_parcels=n_parcels,
        **abagen_kwargs,
    )

    # Filter genes if specified
    if genes is not None:
        available_genes = set(expression_df.columns)
        genes_to_keep = [g for g in genes if g in available_genes]
        if not genes_to_keep:
            raise ValueError(f"None of the requested genes found in abagen output: {genes}")
        expression_df = expression_df[genes_to_keep]

    # Convert to ReceptorMap
    region_ids = expression_df.index.to_numpy(dtype=str)
    genes_out: Dict[str, RegionMap] = {}

    for gene in expression_df.columns:
        values = expression_df[gene].to_numpy(dtype=float)
        genes_out[str(gene)] = RegionMap(
            region_ids=region_ids,
            values=values,
            space=space,
            name=f"{name_prefix}:{gene}",
            provenance={
                "source": "abagen",
                "atlas": atlas,
                "n_parcels": n_parcels,
                "abagen_version": abagen.__version__,
            },
        )

    return ReceptorMap(
        receptors=genes_out,
        space=space,
        provenance={
            "source": "abagen",
            "atlas": atlas,
            "n_parcels": n_parcels,
            "modality": "transcriptomics",
            "atlas_name": "ahba",
        },
    )
