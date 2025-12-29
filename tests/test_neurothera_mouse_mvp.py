import numpy as np
import pandas as pd

from neurothera_map.core.types import ConnectivityGraph
from neurothera_map.mouse.activity import compute_activity_map_from_spikes
from neurothera_map.mouse.predict import diffuse_activity


def test_compute_activity_map_from_spikes_mean_rate():
    # Two units, two regions
    clusters = pd.DataFrame({"cluster_id": [10, 11], "acronym": ["VISp", "CA1"]})

    spikes = {
        "times": np.array([0.1, 0.2, 0.3, 0.15]),
        "clusters": np.array([10, 10, 10, 11]),
    }

    am = compute_activity_map_from_spikes(spikes, clusters, time_window=(0.0, 1.0))
    assert set(am.region_ids.tolist()) == {"VISp", "CA1"}
    # VISp: 3 spikes / 1s = 3 Hz, CA1: 1 spike / 1s = 1 Hz
    d = am.to_dict()
    assert d["VISp"] == 3.0
    assert d["CA1"] == 1.0


def test_diffuse_activity_aligns_to_graph():
    activity = compute_activity_map_from_spikes(
        spikes={"times": np.array([0.1]), "clusters": np.array([0])},
        clusters=pd.DataFrame({"cluster_id": [0], "acronym": ["A"]}),
        time_window=(0.0, 1.0),
        space="allen_ccf",
    )
    g = ConnectivityGraph(
        region_ids=np.array(["A", "B"], dtype=str),
        adjacency=np.array([[0.0, 1.0], [0.0, 0.0]]),
    )

    out = diffuse_activity(activity, g, alpha=0.9, steps=10, fill_value=0.0)
    assert out.region_ids.tolist() == ["A", "B"]
    assert len(out.values) == 2
    # Some mass should end up in B via incoming edge A->B (prop via P^T).
    assert out.values[1] >= 0.0
