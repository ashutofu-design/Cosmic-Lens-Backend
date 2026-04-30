"""
health_topic_matcher.py — Phase 7.6
─────────────────────────────────────
Detects WHICH micro-topics from `health_topics.json` the user's question
covers, ranked by priority and confidence.

Layered:
  Layer 1 — keyword/synonym match (deterministic, free)
  Layer 2 — body-part hint match (catches anatomy words not in synonyms)
  Layer 3 — fallback to "overall_status" when nothing else matches

NO LLM call inside this module — pure Python. The optional Layer 2 LLM
fallback was descoped from Phase 7.6 Part A to keep the path zero-cost
and zero-latency. (Reserved for Phase 7.7 if needed.)

Inputs:
    question : raw user text
    qu       : optional classifier dict (topic, confidence, source). Used
               only as a tie-breaker — matcher does NOT depend on it.
    catalog  : the loaded `health_topics.json` dict.

Output:
    list[dict]  — each item: {
        "topic_id":    str,
        "confidence":  float,   # 0.0..1.0
        "matched_via": str,     # "keyword" | "body_part" | "fallback"
        "matched_synonyms": list[str],  # which synonyms triggered
    }

The list is sorted by (confidence desc, catalog_priority desc).

Usage:
    matches = match_topics(question, qu, catalog)
    top_topic_ids = [m["topic_id"] for m in matches[:3]]

Defensive: returns at least one match (the fallback) when the catalog
has an "overall_status" entry; otherwise returns [].
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Optional


# ── Catalog loader (cached) ──────────────────────────────────────────────────

_CATALOG_PATH = os.path.join(os.path.dirname(__file__), "health_topics.json")
_CATALOG_CACHE: Optional[dict] = None


def load_catalog(path: Optional[str] = None) -> dict:
    """Load and cache the health topics catalog.

    Pass `path=None` for the default `health_topics.json` next to this
    module. Cache is keyed on default path; explicit paths bypass cache.
    """
    global _CATALOG_CACHE
    if path is None:
        if _CATALOG_CACHE is not None:
            return _CATALOG_CACHE
        path = _CATALOG_PATH

    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        # Catalog must always exist; surface a clear error.
        raise RuntimeError(
            f"Phase 7.6 catalog load failed at {path}: {exc}"
        ) from exc

    if not isinstance(data, dict) or "topics" not in data:
        raise RuntimeError(
            f"Phase 7.6 catalog at {path} missing 'topics' key"
        )

    if path == _CATALOG_PATH:
        _CATALOG_CACHE = data
    return data


# ── Body-part hint vocabulary (Layer 2) ──────────────────────────────────────
# Maps body-area keywords → topic IDs. Acts as a safety net for questions
# that mention an anatomy word but don't hit any explicit synonym.
_BODY_PART_HINTS: dict[str, list[str]] = {
    "heart":     ["heart"],
    "dil":       ["heart"],
    "hriday":    ["heart"],
    "eye":       ["eyes"],
    "aankh":     ["eyes"],
    "stomach":   ["digestive"],
    "pet":       ["digestive"],
    "knee":      ["joints_bones"],
    "ghutna":    ["joints_bones"],
    "joint":     ["joints_bones"],
    "kamar":     ["joints_bones"],
    "back":      ["joints_bones"],
    "BP":        ["bp_diabetes"],
    "diabetes":  ["bp_diabetes"],
    "sugar":     ["bp_diabetes"],
    "thyroid":   ["bp_diabetes"],
    "depression": ["mental_health"],
    "anxiety":   ["mental_health"],
    "stress":    ["mental_health"],
    "tension":   ["mental_health"],
    "mann":      ["mental_health"],
    "mental":    ["mental_health"],
}


# ── Tokenisation (case-insensitive substring + word boundary match) ─────────

_WORD_RX = re.compile(r"[a-zA-Z\u0900-\u097F]+", re.UNICODE)


def _normalise(text: str) -> str:
    return (text or "").strip().lower()


def _contains_phrase(haystack: str, needle: str) -> bool:
    """True iff `needle` appears in `haystack` as a phrase (word-boundary
    aware for short phrases, substring for multi-word phrases).

    `haystack` and `needle` should be lowercase already.
    """
    if not needle:
        return False
    if " " in needle:
        # Multi-word phrase → plain substring check (cheap).
        return needle in haystack
    # Single word → word-boundary regex (avoid matching "BP" inside "BPM").
    pat = r"(?<![a-z\u0900-\u097F])" + re.escape(needle) + r"(?![a-z\u0900-\u097F])"
    return bool(re.search(pat, haystack))


# ── Public API ───────────────────────────────────────────────────────────────

def match_topics(
    question: str,
    qu: Optional[dict] = None,
    catalog: Optional[dict] = None,
    *,
    fallback_topic_id: str = "overall_status",
    max_topics: int = 3,
) -> list[dict]:
    """Match the user's question against the catalog. Always returns a
    list (possibly empty if the catalog has no fallback topic).

    Top-N matches by (confidence, priority). When NO topic matches, the
    fallback topic is returned with confidence 0.4 and matched_via="fallback".
    """
    cat = catalog or load_catalog()
    topics = cat.get("topics") or {}
    if not isinstance(topics, dict):
        return []

    q_norm = _normalise(question)
    if not q_norm:
        # Empty question → fallback only.
        return _build_fallback(topics, fallback_topic_id)

    matches_by_id: dict[str, dict] = {}

    # Layer 1 — synonym keyword match.
    for tid, tinfo in topics.items():
        if not isinstance(tinfo, dict):
            continue
        synonyms = tinfo.get("synonyms") or []
        priority = float(tinfo.get("priority") or 50.0)
        hit_syns: list[str] = []
        for syn in synonyms:
            if not isinstance(syn, str):
                continue
            if _contains_phrase(q_norm, syn.lower()):
                hit_syns.append(syn)
        if hit_syns:
            # Confidence climbs with hit count (saturates around 3 hits).
            base = 0.65
            bonus = min(0.30, 0.10 * len(hit_syns))
            conf = min(0.99, base + bonus)
            matches_by_id[tid] = {
                "topic_id":          tid,
                "confidence":        conf,
                "matched_via":       "keyword",
                "matched_synonyms":  hit_syns,
                "_priority":         priority,
            }

    # Layer 2 — body-part hint (only adds topics not already matched).
    for hint, candidate_topic_ids in _BODY_PART_HINTS.items():
        if not _contains_phrase(q_norm, hint.lower()):
            continue
        for tid in candidate_topic_ids:
            if tid in matches_by_id:
                continue
            tinfo = topics.get(tid) or {}
            if not isinstance(tinfo, dict):
                continue
            priority = float(tinfo.get("priority") or 50.0)
            matches_by_id[tid] = {
                "topic_id":          tid,
                "confidence":        0.55,
                "matched_via":       "body_part",
                "matched_synonyms":  [hint],
                "_priority":         priority,
            }

    # If we got hits, sort + truncate.
    if matches_by_id:
        ranked = sorted(
            matches_by_id.values(),
            key=lambda m: (m["confidence"], m["_priority"]),
            reverse=True,
        )
        for m in ranked:
            m.pop("_priority", None)
        return ranked[:max_topics]

    # Layer 3 — fallback.
    return _build_fallback(topics, fallback_topic_id)


def _build_fallback(topics: dict, fallback_topic_id: str) -> list[dict]:
    if fallback_topic_id not in topics:
        return []
    return [{
        "topic_id":         fallback_topic_id,
        "confidence":       0.4,
        "matched_via":      "fallback",
        "matched_synonyms": [],
    }]
