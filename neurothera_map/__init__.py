"""NeuroThera-Map: receptor → circuit → activation integration toolkit.

This package is layered on top of the existing `brainwidemap` utilities in this repo.
The goal is to provide a stable schema and minimal MVP primitives for:
- region-indexed maps (mouse CCF, human parcellations)
- drug/target/affinity profiles
- connectivity graphs and propagation

The implementation is intentionally dependency-light.
"""

from .core.types import (
    ActivityMap,
    ConnectivityGraph,
    DrugInteraction,
    DrugProfile,
    ReceptorMap,
    RegionMap,
)

from .drug.profile import build_drug_profile

__all__ = [
    "RegionMap",
    "ReceptorMap",
    "ActivityMap",
    "ConnectivityGraph",
    "DrugInteraction",
    "DrugProfile",
    "build_drug_profile",
]
