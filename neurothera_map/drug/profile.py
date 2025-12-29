from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Iterable, List, Optional, Tuple

from ..core.types import DrugInteraction, DrugProfile


def _normalize_name(name: str) -> str:
    return " ".join(name.strip().split()).lower()


def _to_nM(value: float, unit: str) -> float:
    unit_norm = unit.strip().lower()
    if unit_norm in {"nm", "nanomolar"}:
        return float(value)
    if unit_norm in {"um", "µm", "micromolar"}:
        return float(value) * 1e3
    if unit_norm in {"mm", "millimolar"}:
        return float(value) * 1e6
    raise ValueError(f"Unsupported affinity unit: {unit}")


# Minimal built-in seed data so the MVP can run offline.
# This is intentionally small and should be expanded via proper ingestion later.
_SEED_DB: Dict[str, List[Dict[str, Any]]] = {
    "caffeine": [
        {
            "target": "ADORA1",
            "affinity": 10.0,
            "unit": "uM",
            "action": "antagonist",
            "evidence": 0.7,
            "source": "seed",
        },
        {
            "target": "ADORA2A",
            "affinity": 10.0,
            "unit": "uM",
            "action": "antagonist",
            "evidence": 0.7,
            "source": "seed",
        },
    ]
}


def build_drug_profile(name: str) -> DrugProfile:
    """Build a normalized DrugProfile.

    MVP behavior:
    - Works offline using a tiny built-in seed DB.
    - Unknown drugs return an empty profile (with provenance noting the miss).

    Args:
        name: Drug/compound name.

    Returns:
        DrugProfile
    """
    normalized = _normalize_name(name)
    rows = _SEED_DB.get(normalized, [])

    interactions: List[DrugInteraction] = []
    for row in rows:
        affinity = row.get("affinity")
        unit = row.get("unit")
        affinity_nM: Optional[float]
        if affinity is None or unit is None:
            affinity_nM = None
        else:
            affinity_nM = _to_nM(float(affinity), str(unit))

        interactions.append(
            DrugInteraction(
                target=str(row.get("target", "")),
                affinity_nM=affinity_nM,
                action=str(row.get("action", "")),
                evidence=float(row.get("evidence", 0.0)),
                source=str(row.get("source", "")),
                meta={k: v for k, v in row.items() if k not in {"target", "affinity", "unit", "action", "evidence", "source"}},
            )
        )

    provenance: Dict[str, Any] = {
        "builder": "neurothera_map.drug.build_drug_profile",
        "normalized_name": normalized,
        "seed_db_hit": normalized in _SEED_DB,
    }

    return DrugProfile(name=normalized, interactions=tuple(interactions), provenance=provenance)
