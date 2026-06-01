"""Shim — numerology.core.scope"""
from numerology.core.scope import *  # noqa: F403
from numerology.core.scope import include_celebrity_match, include_extended_extras


def include_vedic_tiers() -> bool:
    return False
