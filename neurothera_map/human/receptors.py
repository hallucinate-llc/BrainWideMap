"""Human PET receptor map loader.

This module provides offline fixture-based loading of human PET receptor density maps,
with optional integration for the `hansen_receptors` package if installed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Sequence

import numpy as np
import pandas as pd

from ..core.types import ReceptorMap, RegionMap


@dataclass(frozen=True)
class PETReceptorTableSpec:
    """Column specification for PET receptor CSV tables."""

    region_col: str = "region"
    receptor_col: str = "receptor"
    value_col: str = "value"
    uncertainty_col: Optional[str] = None


def load_human_pet_receptor_maps(
    path: str | Path,
    *,
    receptors: Optional[Sequence[str]] = None,
    spec: PETReceptorTableSpec = PETReceptorTableSpec(),
    space: str = "fsaverage",
    name_prefix: str = "human_pet_receptor",
) -> ReceptorMap:
    """Load human PET receptor density maps from CSV fixture.

    This function provides offline loading of human PET receptor maps from a CSV table.
    The table should contain region-level receptor density measurements in long format.

    If the optional `hansen_receptors` package is installed, this function can be
    extended to load data from that source. However, the base implementation works
    entirely offline using the provided CSV fixture.

    Supported CSV format:
        Long format with columns: region, receptor, value (and optionally uncertainty)

    Args:
        path: Path to CSV file containing receptor density data.
        receptors: Optional list of receptor names to load. If None, loads all.
        spec: Column specification for the CSV table.
        space: Brain space identifier (default: "fsaverage").
        name_prefix: Prefix for RegionMap names.

    Returns:
        ReceptorMap containing region-indexed density maps for each receptor.

    Example:
        >>> receptor_map = load_human_pet_receptor_maps(
        ...     "datasets/human_pet_receptor_fixture.csv",
        ...     receptors=["5HT1a", "D1", "D2"]
        ... )
        >>> print(receptor_map.receptor_names())
        ['5HT1a', 'D1', 'D2']
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    df = pd.read_csv(p)

    # Check for hansen_receptors integration (soft dependency)
    try:
        _check_hansen_receptors_available()
        provenance_source = "csv_with_hansen_receptors_available"
    except ImportError:
        provenance_source = "csv_offline_fixture"

    return _load_pet_receptor_long_format(
        df,
        receptors=receptors,
        spec=spec,
        space=space,
        name_prefix=name_prefix,
        src=p,
        provenance_source=provenance_source,
    )


def _load_pet_receptor_long_format(
    df: pd.DataFrame,
    *,
    receptors: Optional[Sequence[str]],
    spec: PETReceptorTableSpec,
    space: str,
    name_prefix: str,
    src: Path,
    provenance_source: str,
) -> ReceptorMap:
    """Parse long-format PET receptor CSV into ReceptorMap."""
    # Validate required columns
    required_cols = [spec.region_col, spec.receptor_col, spec.value_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Missing required columns in CSV: {missing_cols}. "
            f"Expected columns: {required_cols}"
        )

    # Prepare data
    work = df.copy()
    work[spec.region_col] = work[spec.region_col].astype(str)
    work[spec.receptor_col] = work[spec.receptor_col].astype(str)

    # Filter receptors if specified
    if receptors is not None:
        keep = {str(r) for r in receptors}
        work = work[work[spec.receptor_col].isin(keep)]
        if len(work) == 0:
            raise ValueError(f"No data found for requested receptors: {receptors}")

    receptors_out: Dict[str, RegionMap] = {}

    # Group by receptor and create RegionMap for each
    for receptor, sub in work.groupby(spec.receptor_col, sort=True):
        # Select columns for this receptor's data
        columns_to_select = [spec.region_col, spec.value_col]
        if spec.uncertainty_col and spec.uncertainty_col in sub.columns:
            columns_to_select.append(spec.uncertainty_col)

        sub2 = sub[columns_to_select].copy()

        # Drop NaN values and aggregate duplicates by mean
        sub2 = sub2.dropna(subset=[spec.value_col])
        sub2 = sub2.groupby(spec.region_col, as_index=False).mean(numeric_only=True)
        sub2 = sub2.sort_values(spec.region_col)

        region_ids = sub2[spec.region_col].to_numpy(dtype=str)
        values = sub2[spec.value_col].to_numpy(dtype=float)

        uncertainty = None
        if spec.uncertainty_col and spec.uncertainty_col in sub2.columns:
            uncertainty = sub2[spec.uncertainty_col].to_numpy(dtype=float)

        receptors_out[str(receptor)] = RegionMap(
            region_ids=region_ids,
            values=values,
            uncertainty=uncertainty,
            space=space,
            name=f"{name_prefix}:{receptor}",
            provenance={
                "source": provenance_source,
                "path": str(src),
                "format": "long",
                "region_col": spec.region_col,
                "value_col": spec.value_col,
                "modality": "PET",
            },
        )

    return ReceptorMap(
        receptors=receptors_out,
        space=space,
        provenance={
            "source": provenance_source,
            "path": str(src),
            "modality": "PET",
            "n_receptors": len(receptors_out),
        },
    )


def _check_hansen_receptors_available() -> None:
    """Check if hansen_receptors package is available (soft dependency).

    Raises:
        ImportError if hansen_receptors is not installed.
    """
    try:
        import hansen_receptors  # noqa: F401
    except ImportError as e:
        raise ImportError(
            "hansen_receptors package is not installed. "
            "Install it with: pip install hansen_receptors"
        ) from e
