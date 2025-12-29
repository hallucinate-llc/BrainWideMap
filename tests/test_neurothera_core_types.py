import numpy as np

from neurothera_map.core.types import ConnectivityGraph, RegionMap


def test_region_map_reindex_and_to_dict():
    rm = RegionMap(region_ids=np.array(["A", "B"], dtype=str), values=np.array([1.0, 2.0]), space="test", name="rm")
    assert rm.to_dict() == {"A": 1.0, "B": 2.0}

    rm2 = rm.reindex(["B", "C"], fill_value=-1.0)
    assert rm2.region_ids.tolist() == ["B", "C"]
    assert np.allclose(rm2.values, np.array([2.0, -1.0]))


def test_connectivity_graph_row_normalized():
    g = ConnectivityGraph(
        region_ids=np.array(["A", "B"], dtype=str),
        adjacency=np.array([[0.0, 2.0], [1.0, 1.0]]),
        name="g",
    )
    P = g.row_normalized()
    assert np.allclose(P.sum(axis=1), np.array([1.0, 1.0]))
