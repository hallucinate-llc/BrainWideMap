from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from ..core.types import ActivityMap


def compute_activity_map_from_spikes(
    spikes: Dict[str, np.ndarray],
    clusters: pd.DataFrame,
    time_window: Optional[Tuple[float, float]] = None,
    region_col: Optional[str] = None,
    name: str = "mean_firing_rate",
    space: str = "allen_ccf",
) -> ActivityMap:
    """Compute a simple region-level ActivityMap from spike data.

    MVP definition:
    - Per unit: firing rate over the provided `time_window` (or full duration).
    - Per region: mean firing rate across units in that region.

    This is designed to be deterministic and testable offline.

    Args:
        spikes: Dict with 'times' and 'clusters' arrays (or 'spike_times'/'spike_clusters').
        clusters: DataFrame containing unit metadata including a region column.
        time_window: Optional (start, end) seconds.
        region_col: Explicit region column name. If None, tries 'acronym', then 'brain_region', then 'region'.
        name: Name for the ActivityMap.
        space: Atlas/space label.

    Returns:
        ActivityMap
    """
    spike_times = spikes.get("times", spikes.get("spike_times"))
    spike_clusters = spikes.get("clusters", spikes.get("spike_clusters"))
    if spike_times is None or spike_clusters is None:
        raise ValueError("spikes must contain 'times' and 'clusters' (or aliases)")

    spike_times = np.asarray(spike_times, dtype=float)
    spike_clusters = np.asarray(spike_clusters)

    if time_window is not None:
        start, end = float(time_window[0]), float(time_window[1])
        mask = (spike_times >= start) & (spike_times <= end)
        spike_times = spike_times[mask]
        spike_clusters = spike_clusters[mask]
        duration = max(end - start, 1e-12)
    else:
        duration = max(float(spike_times.max() - spike_times.min()), 1e-12)

    if region_col is None:
        for cand in ("acronym", "brain_region", "region"):
            if cand in clusters.columns:
                region_col = cand
                break
    if region_col is None:
        raise ValueError("clusters must include a region column (e.g. 'acronym')")

    # Compute per-unit firing rates
    # Note: cluster IDs in spike_clusters should match clusters index OR 'cluster_id' column.
    if "cluster_id" in clusters.columns:
        unit_ids = clusters["cluster_id"].to_numpy()
        unit_regions = clusters[region_col].astype(str).to_numpy()
    else:
        unit_ids = clusters.index.to_numpy()
        unit_regions = clusters[region_col].astype(str).to_numpy()

    unit_rates = []
    for unit_id, region in zip(unit_ids, unit_regions):
        n_spikes = int(np.sum(spike_clusters == unit_id))
        unit_rates.append((str(region), n_spikes / duration))

    if len(unit_rates) == 0:
        return ActivityMap(region_ids=np.array([], dtype=str), values=np.array([], dtype=float), space=space, name=name)

    df = pd.DataFrame(unit_rates, columns=["region", "rate"])
    region_means = df.groupby("region")["rate"].mean().sort_index()

    return ActivityMap(
        region_ids=region_means.index.to_numpy(dtype=str),
        values=region_means.to_numpy(dtype=float),
        space=space,
        name=name,
        provenance={"method": "mean_firing_rate_across_units", "time_window": time_window},
    )
