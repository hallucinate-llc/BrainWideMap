"""
Drug database ingestion and DrugProfile generation.

This module provides adapters for:
- IUPHAR Guide to Pharmacology (curated targets)
- ChEMBL (broad bioactivity data)
"""

from .schemas import DrugProfile, TargetInteraction, PotencyMeasure
from .iuphar_adapter import IUPHARAdapter
from .chembl_adapter import ChEMBLAdapter
from .drug_loader import DrugLoader

__all__ = [
    'DrugProfile',
    'TargetInteraction',
    'PotencyMeasure',
    'IUPHARAdapter',
    'ChEMBLAdapter',
    'DrugLoader',
]
