from __future__ import annotations

from typing import Optional

import numpy as np

from ..core.types import ActivityMap, ConnectivityGraph


def diffuse_activity(
    activity: ActivityMap,
    graph: ConnectivityGraph,
    alpha: float = 0.85,
    steps: int = 25,
    fill_value: float = 0.0,
    name: Optional[str] = None,
) -> ActivityMap:
    """Diffuse an ActivityMap over a ConnectivityGraph.

    Uses a simple random-walk-with-restart style update:
        x_{t+1} = alpha * P^T x_t + (1-alpha) * x0
    where P is row-normalized adjacency (i→j) and we propagate along incoming edges.

    Args:
        activity: ActivityMap on some subset of regions.
        graph: ConnectivityGraph.
        alpha: Diffusion strength.
        steps: Number of iterations.
        fill_value: Value for regions not present in `activity`.
        name: Optional output name.

    Returns:
        ActivityMap aligned to graph regions.
    """
    x0_map = activity.reindex(graph.region_ids.tolist(), fill_value=fill_value)
    x0 = x0_map.values.astype(float)

    P = graph.row_normalized()
    x = x0.copy()

    for _ in range(int(steps)):
        x = alpha * (P.T @ x) + (1.0 - alpha) * x0

    return ActivityMap(
        region_ids=graph.region_ids,
        values=x,
        space=activity.space or "",
        name=name or f"diffused({activity.name})",
        provenance={
            "alpha": alpha,
            "steps": steps,
            "fill_value": fill_value,
            "graph": graph.name,
        },
    )
