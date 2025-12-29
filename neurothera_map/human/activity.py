"""Human ActivityMap ingestion from parcellated tables and optional NIfTI support.

Phase 2.3 MVP implementation:
- Load activity maps from CSV/tabular files (region, value columns)
- Optional NIfTI support if neuroimaging libraries available
- Keep neuroimaging dependencies optional
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np
import pandas as pd

from ..core.types import ActivityMap

# Optional neuroimaging dependencies
try:
    import nibabel as nib

    NIBABEL_AVAILABLE = True
except ImportError:
    NIBABEL_AVAILABLE = False


def activity_map_from_parcellated_table(
    path: Union[str, Path],
    region_col: str = "region",
    value_col: str = "value",
    space: str = "mni152",
    name: str = "",
) -> ActivityMap:
    """Create an ActivityMap from a parcellated table (CSV or similar).

    This function loads region-level activity data from a tabular file,
    typically CSV format, containing region identifiers and corresponding values.

    Args:
        path: Path to the CSV/table file containing parcellated data
        region_col: Name of the column containing region identifiers (default: "region")
        value_col: Name of the column containing activity values (default: "value")
        space: Atlas/space identifier (default: "mni152" for human data)
        name: Descriptive name for the activity map (default: "")

    Returns:
        ActivityMap with region_ids and values from the table

    Raises:
        FileNotFoundError: If the specified file does not exist
        ValueError: If required columns are missing or data is invalid

    Examples:
        >>> # Load from CSV with default columns
        >>> am = activity_map_from_parcellated_table("activity.csv")
        >>> # Load with custom column names
        >>> am = activity_map_from_parcellated_table(
        ...     "data.csv",
        ...     region_col="brain_region",
        ...     value_col="activation",
        ...     space="mni152",
        ...     name="task_activation"
        ... )
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # Load the table
    df = pd.read_csv(path)

    # Validate columns
    if region_col not in df.columns:
        raise ValueError(
            f"Column '{region_col}' not found in file. Available columns: {list(df.columns)}"
        )
    if value_col not in df.columns:
        raise ValueError(
            f"Column '{value_col}' not found in file. Available columns: {list(df.columns)}"
        )

    # Extract and validate data
    # Note: Convert to str after filtering NaNs to avoid 'nan' strings
    region_series = df[region_col]
    value_series = df[value_col]
    
    # Check for empty table
    if len(region_series) == 0:
        raise ValueError("Table contains no data rows")
    
    # Remove rows with NaN values before conversion
    valid_mask = ~(region_series.isna() | value_series.isna())
    if valid_mask.sum() == 0:
        raise ValueError("No valid (non-NaN) region-value pairs found in table")
    
    regions = region_series[valid_mask].astype(str).to_numpy()
    values = value_series[valid_mask].to_numpy(dtype=float)

    # Build provenance information
    provenance: Dict[str, Any] = {
        "source_file": str(path.absolute()),
        "region_col": region_col,
        "value_col": value_col,
        "n_regions": len(regions),
    }

    return ActivityMap(
        region_ids=regions,
        values=values,
        space=space,
        name=name or path.stem,
        provenance=provenance,
    )


def activity_map_from_nifti(
    nifti_path: Union[str, Path],
    atlas_path: Union[str, Path],
    space: str = "mni152",
    name: str = "",
    aggregation: str = "mean",
) -> ActivityMap:
    """Create an ActivityMap from a NIfTI volume using an atlas for parcellation.

    This function requires nibabel to be installed. If this library is not
    available, an ImportError will be raised.

    Args:
        nifti_path: Path to the NIfTI file containing activity/activation data
        atlas_path: Path to the atlas NIfTI file with integer region labels
        space: Atlas/space identifier (default: "mni152")
        name: Descriptive name for the activity map (default: "")
        aggregation: How to aggregate voxel values within each region
                     Options: "mean", "median", "sum" (default: "mean")

    Returns:
        ActivityMap with parcellated values from the NIfTI volume

    Raises:
        ImportError: If nibabel is not installed
        FileNotFoundError: If specified files do not exist
        ValueError: If aggregation method is not supported

    Examples:
        >>> # Requires nibabel to be installed
        >>> am = activity_map_from_nifti(
        ...     "activation_map.nii.gz",
        ...     "atlas.nii.gz",
        ...     space="mni152",
        ...     name="fmri_task"
        ... )
    """
    if not NIBABEL_AVAILABLE:
        raise ImportError(
            "nibabel is required for NIfTI support. "
            "Install with: pip install nibabel"
        )

    nifti_path = Path(nifti_path)
    atlas_path = Path(atlas_path)

    if not nifti_path.exists():
        raise FileNotFoundError(f"NIfTI file not found: {nifti_path}")
    if not atlas_path.exists():
        raise FileNotFoundError(f"Atlas file not found: {atlas_path}")

    # Load images
    data_img = nib.load(nifti_path)
    atlas_img = nib.load(atlas_path)

    data_array = data_img.get_fdata()
    atlas_array = atlas_img.get_fdata().astype(int)

    # Get unique region labels (excluding 0 which is typically background)
    region_labels = np.unique(atlas_array)
    region_labels = region_labels[region_labels != 0]

    # Aggregate values for each region
    region_ids = []
    values = []

    for label in region_labels:
        mask = atlas_array == label
        voxel_values = data_array[mask]

        # Filter out NaN and infinite values
        voxel_values = voxel_values[np.isfinite(voxel_values)]

        if len(voxel_values) == 0:
            continue

        # Apply aggregation
        if aggregation == "mean":
            agg_value = float(np.mean(voxel_values))
        elif aggregation == "median":
            agg_value = float(np.median(voxel_values))
        elif aggregation == "sum":
            agg_value = float(np.sum(voxel_values))
        else:
            raise ValueError(
                f"Unsupported aggregation method: {aggregation}. "
                f"Use 'mean', 'median', or 'sum'"
            )

        region_ids.append(str(label))
        values.append(agg_value)

    if len(region_ids) == 0:
        raise ValueError("No valid regions found in atlas")

    # Build provenance
    provenance: Dict[str, Any] = {
        "nifti_file": str(nifti_path.absolute()),
        "atlas_file": str(atlas_path.absolute()),
        "aggregation": aggregation,
        "n_regions": len(region_ids),
    }

    return ActivityMap(
        region_ids=np.array(region_ids, dtype=str),
        values=np.array(values, dtype=float),
        space=space,
        name=name or nifti_path.stem,
        provenance=provenance,
    )
