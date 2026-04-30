"""
health_recipe_composer.py — Phase 7.6
──────────────────────────────────────
Given a list of matched topic IDs, return the deduped union of:
  • slot list (which chart pieces to pull)
  • rule list (which rule IDs to evaluate)

Pure function — no I/O, no LLM. Defensive on missing topics.

Why a separate module:
  Multi-topic matches (e.g. "mental health + sleep + chronic") would
  otherwise duplicate slots/rules, blow up the rule-engine pass, and
  bloat the prompt. The composer collapses overlap with stable order.
"""
from __future__ import annotations

from typing import Optional


def compose_recipe(
    topic_ids: list[str],
    catalog: dict,
) -> dict:
    """Compose a deduped slot+rule manifest from matched topics.

    Returns:
        {
          "topics_used": list[str],   # topics actually found in catalog
          "topics_skipped": list[str],# requested but not in catalog
          "slots":        list[str],  # deduped, original-order
          "rules":        list[str],  # deduped, original-order
        }
    """
    out: dict = {
        "topics_used":    [],
        "topics_skipped": [],
        "slots":          [],
        "rules":          [],
    }
    if not isinstance(catalog, dict):
        return out
    topics = catalog.get("topics") or {}
    if not isinstance(topics, dict):
        return out

    seen_slots: set[str] = set()
    seen_rules: set[str] = set()
    seen_topics: set[str] = set()
    seen_skipped: set[str] = set()

    for tid in (topic_ids or []):
        if not isinstance(tid, str):
            continue
        tinfo = topics.get(tid)
        if not isinstance(tinfo, dict):
            if tid not in seen_skipped:
                seen_skipped.add(tid)
                out["topics_skipped"].append(tid)
            continue
        if tid in seen_topics:
            continue
        seen_topics.add(tid)
        out["topics_used"].append(tid)

        for slot in (tinfo.get("recipe") or []):
            if isinstance(slot, str) and slot not in seen_slots:
                seen_slots.add(slot)
                out["slots"].append(slot)

        for rule in (tinfo.get("rules") or []):
            if isinstance(rule, str) and rule not in seen_rules:
                seen_rules.add(rule)
                out["rules"].append(rule)

    return out


def slot_summary_for_trace(recipe: dict) -> dict:
    """Tiny dict suitable for trace logging — counts only, not full lists."""
    if not isinstance(recipe, dict):
        return {"topics": 0, "slots": 0, "rules": 0}
    return {
        "topics":  len(recipe.get("topics_used") or []),
        "skipped": len(recipe.get("topics_skipped") or []),
        "slots":   len(recipe.get("slots") or []),
        "rules":   len(recipe.get("rules") or []),
    }
