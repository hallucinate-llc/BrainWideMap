from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union

import numpy as np


ArrayLike1DFloat = Union[Sequence[float], np.ndarray]
ArrayLike1DStr = Union[Sequence[str], np.ndarray]


def _as_1d_float_array(values: ArrayLike1DFloat) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.ndim != 1:
        raise ValueError("values must be 1D")
    return arr


def _as_1d_str_array(values: ArrayLike1DStr) -> np.ndarray:
    arr = np.asarray(values, dtype=str)
    if arr.ndim != 1:
        raise ValueError("region_ids must be 1D")
    return arr


@dataclass(frozen=True)
class RegionMap:
    """Values indexed by region identifiers (acronyms or canonical IDs)."""

    region_ids: np.ndarray
    values: np.ndarray
    space: str = ""
    name: str = ""
    uncertainty: Optional[np.ndarray] = None
    provenance: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "region_ids", _as_1d_str_array(self.region_ids))
        object.__setattr__(self, "values", _as_1d_float_array(self.values))
        if len(self.region_ids) != len(self.values):
            raise ValueError("region_ids and values must have the same length")
        if self.uncertainty is not None:
            unc = _as_1d_float_array(self.uncertainty)
            if len(unc) != len(self.values):
                raise ValueError("uncertainty must match values length")
            object.__setattr__(self, "uncertainty", unc)

    def to_dict(self) -> Dict[str, float]:
        return {str(k): float(v) for k, v in zip(self.region_ids.tolist(), self.values.tolist())}

    def reindex(self, region_ids: Sequence[str], fill_value: float = np.nan) -> "RegionMap":
        """Return a new RegionMap aligned to `region_ids` (missing filled)."""
        target = _as_1d_str_array(region_ids)
        mapping = self.to_dict()
        vals = np.array([mapping.get(str(r), fill_value) for r in target], dtype=float)
        return RegionMap(
            region_ids=target,
            values=vals,
            space=self.space,
            name=self.name,
            provenance=dict(self.provenance),
        )


@dataclass(frozen=True)
class ReceptorMap:
    """A collection of region-indexed maps keyed by receptor/target identifiers."""

    receptors: Mapping[str, RegionMap]
    space: str = ""
    provenance: Dict[str, Any] = field(default_factory=dict)

    def receptor_names(self) -> List[str]:
        return sorted(self.receptors.keys())

    def get(self, receptor: str) -> Optional[RegionMap]:
        return self.receptors.get(receptor)


@dataclass(frozen=True)
class ActivityMap(RegionMap):
    """RegionMap representing an activity/effect-size signal."""


@dataclass(frozen=True)
class ConnectivityGraph:
    """Directed weighted region graph.

    Adjacency is a dense matrix A where A[i, j] is weight i→j.
    """

    region_ids: np.ndarray
    adjacency: np.ndarray
    name: str = ""
    provenance: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "region_ids", _as_1d_str_array(self.region_ids))
        adj = np.asarray(self.adjacency, dtype=float)
        if adj.ndim != 2 or adj.shape[0] != adj.shape[1]:
            raise ValueError("adjacency must be a square 2D array")
        if adj.shape[0] != len(self.region_ids):
            raise ValueError("adjacency size must match region_ids length")
        object.__setattr__(self, "adjacency", adj)

    def row_normalized(self, eps: float = 1e-12) -> np.ndarray:
        row_sums = self.adjacency.sum(axis=1)
        denom = np.where(row_sums > eps, row_sums, 1.0)
        return self.adjacency / denom[:, None]


@dataclass(frozen=True)
class DrugInteraction:
    """One drug-target interaction with units and provenance."""

    target: str
    affinity_nM: Optional[float] = None
    action: str = ""  # e.g. agonist/antagonist/inhibitor
    evidence: float = 0.0  # 0..1
    source: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DrugProfile:
    """Normalized drug profile: name + list of interactions."""

    name: str
    interactions: Tuple[DrugInteraction, ...] = ()
    provenance: Dict[str, Any] = field(default_factory=dict)

    def targets(self) -> List[str]:
        return sorted({i.target for i in self.interactions})

    def as_target_affinity_dict(self) -> Dict[str, float]:
        """Return best-known affinity per target (nM), dropping missing affinities."""
        out: Dict[str, float] = {}
        for inter in self.interactions:
            if inter.affinity_nM is None:
                continue
            prev = out.get(inter.target)
            if prev is None or inter.affinity_nM < prev:
                out[inter.target] = float(inter.affinity_nM)
        return out
