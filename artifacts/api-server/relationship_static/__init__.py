"""Relationship deterministic facts — unified MR engine execution."""

from .relationship_facts import (
    compute_d9_relationship_facts,
    compute_relationship_engine_execution,
    compute_relationship_facts,
)

__all__ = [
    "compute_relationship_facts",
    "compute_d9_relationship_facts",
    "compute_relationship_engine_execution",
]
