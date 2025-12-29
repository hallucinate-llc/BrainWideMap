from __future__ import annotations

from dataclasses import asdict
from enum import Enum
from typing import Any, Dict, Iterable, List, Literal, Optional, Tuple

from ..core.types import DrugInteraction, DrugProfile


# Default evidence score for interactions with missing evidence
_DEFAULT_EVIDENCE_SCORE = 0.0


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


def _convert_drug_profile(
    drug_profile: Any,
) -> DrugProfile:
    """Convert /drug DrugProfile to neurothera_map DrugProfile.
    
    Args:
        drug_profile: DrugProfile from drug.schemas module
        
    Returns:
        DrugProfile in neurothera_map.core.types format
    """
    interactions: List[DrugInteraction] = []
    
    for interaction in drug_profile.interactions:
        # Get best potency in nM
        affinity_nM = interaction.get_best_potency_nm()
        
        # Map interaction type to action string
        # Handle both enum types (with .value) and string types
        if isinstance(interaction.interaction_type, Enum):
            action = interaction.interaction_type.value
        else:
            action = str(interaction.interaction_type)
        
        # Get evidence score with default fallback
        evidence = interaction.evidence_score if interaction.evidence_score is not None else _DEFAULT_EVIDENCE_SCORE
        
        # Get source database
        source = interaction.source_database if interaction.source_database else "ingestion"
        
        # Build meta dict with additional fields
        meta: Dict[str, Any] = {}
        if interaction.target_uniprot_id:
            meta["uniprot_id"] = interaction.target_uniprot_id
        if interaction.target_name:
            meta["target_name"] = interaction.target_name
        if interaction.potency_measures:
            meta["n_potency_measures"] = len(interaction.potency_measures)
        
        interactions.append(
            DrugInteraction(
                target=interaction.target_gene_symbol,
                affinity_nM=affinity_nM,
                action=action,
                evidence=evidence,
                source=source,
                meta=meta,
            )
        )
    
    provenance: Dict[str, Any] = {
        "builder": "neurothera_map.drug.build_drug_profile",
        "normalized_name": drug_profile.common_name.lower(),
        "mode": "ingest",
        "source_databases": drug_profile.source_databases,
    }
    
    if hasattr(drug_profile, 'chembl_id') and drug_profile.chembl_id:
        provenance["chembl_id"] = drug_profile.chembl_id
    if hasattr(drug_profile, 'iuphar_ligand_id') and drug_profile.iuphar_ligand_id:
        provenance["iuphar_ligand_id"] = drug_profile.iuphar_ligand_id
    
    return DrugProfile(
        name=drug_profile.common_name.lower(),
        interactions=tuple(interactions),
        provenance=provenance,
    )


def _build_from_seed(name: str) -> DrugProfile:
    """Build DrugProfile from seed database.
    
    Args:
        name: Drug/compound name (will be normalized).
        
    Returns:
        DrugProfile from seed data
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
        "mode": "seed",
        "seed_db_hit": normalized in _SEED_DB,
    }

    return DrugProfile(name=normalized, interactions=tuple(interactions), provenance=provenance)


def build_drug_profile(name: str, *, mode: Literal["auto", "seed", "ingest"] = "auto") -> DrugProfile:
    """Build a normalized DrugProfile.

    Behavior by mode:
    - "auto": Try /drug ingestion first, fall back to seed DB if unavailable
    - "seed": Force offline seed database behavior
    - "ingest": Force ingestion and raise clear error if unavailable

    Args:
        name: Drug/compound name.
        mode: Profile building mode ("auto", "seed", or "ingest")

    Returns:
        DrugProfile

    Raises:
        ImportError: If mode="ingest" and /drug module cannot be imported
        RuntimeError: If mode="ingest" and ingestion fails
    """
    # Handle seed mode (existing offline behavior)
    if mode == "seed":
        return _build_from_seed(name)
    
    # Handle ingest or auto mode
    if mode in ("ingest", "auto"):
        try:
            # Try to import drug loader
            from drug.drug_loader import DrugLoader
            
            # Attempt ingestion
            loader = DrugLoader()
            drug_profile = loader.load_drug_profile(name)
            
            if drug_profile is not None:
                # Successfully loaded from ingestion
                return _convert_drug_profile(drug_profile)
            
            # Ingestion returned None (drug not found)
            if mode == "ingest":
                raise RuntimeError(
                    f"Drug '{name}' not found in ingestion databases. "
                    "Try mode='seed' for offline fallback or check drug name spelling."
                )
            
            # Auto mode: fall back to seed
            profile = _build_from_seed(name)
            # Update provenance to note fallback
            provenance_updated = dict(profile.provenance)
            provenance_updated["mode"] = "auto"
            provenance_updated["ingestion_attempted"] = True
            provenance_updated["ingestion_available"] = False
            return DrugProfile(
                name=profile.name,
                interactions=profile.interactions,
                provenance=provenance_updated,
            )
            
        except ImportError as e:
            if mode == "ingest":
                raise ImportError(
                    "Cannot use mode='ingest': /drug module is not available. "
                    "The drug ingestion system requires the 'drug' package to be properly installed."
                ) from e
            
            # Auto mode: fall back to seed
            profile = _build_from_seed(name)
            # Update provenance to note fallback
            provenance_updated = dict(profile.provenance)
            provenance_updated["mode"] = "auto"
            provenance_updated["ingestion_attempted"] = True
            provenance_updated["ingestion_available"] = False
            return DrugProfile(
                name=profile.name,
                interactions=profile.interactions,
                provenance=provenance_updated,
            )
    
    # This should never happen due to Literal type, but handle gracefully
    raise ValueError(f"Invalid mode: {mode}. Must be 'auto', 'seed', or 'ingest'.")
