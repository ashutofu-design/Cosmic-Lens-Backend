"""Batch DNA extraction — classification only, no quota, no astrology answer."""
from __future__ import annotations

import os
from typing import Any, Iterator


def _dna_batch_max() -> int:
    try:
        return max(1, min(500, int(os.environ.get("DNA_BATCH_MAX_QUESTIONS", "500"))))
    except (TypeError, ValueError):
        return 500


def parse_dna_questions(raw: Any) -> list[str]:
    """Accept list or newline string; cap at DNA_BATCH_MAX_QUESTIONS."""
    questions: list[str] = []
    if isinstance(raw, list):
        questions = [str(q).strip() for q in raw if str(q).strip()]
    elif isinstance(raw, str):
        questions = [x.strip() for x in raw.splitlines() if x.strip()]
    cap = _dna_batch_max()
    return questions[:cap]


def iter_dna_batch(
    questions: list[str],
    *,
    history: list | None = None,
) -> Iterator[dict]:
    """Yield one DNA result per question (sequential — one LLM call each)."""
    from ask_question_dna import extract_question_dna

    total = len(questions)
    for idx, q in enumerate(questions, 1):
        q = (q or "").strip()
        if not q:
            continue
        try:
            dna = extract_question_dna(q, history=history)
        except Exception as exc:
            dna = {
                "questions": [],
                "source": f"dna_runner_error:{exc}",
                "latency_ms": 0,
            }
        primary = (dna.get("questions") or [{}])[0] if isinstance(dna, dict) else {}
        yield {
            "index": idx,
            "total": total,
            "question": q,
            "dna": dna,
            "domain": primary.get("domain"),
            "bucket": primary.get("bucket"),
            "engine_archetype": primary.get("engine_archetype"),
            "bucket_coerced": primary.get("bucket_coerced"),
            "bucket_match_score": primary.get("bucket_match_score"),
            "bucket_match_confidence": primary.get("bucket_match_confidence"),
            "intent": primary.get("intent"),
            "subject": primary.get("subject"),
            "target": primary.get("target"),
            "question_type": primary.get("question_type"),
            "timing": primary.get("timing"),
            "tense": primary.get("tense"),
            "emotion": primary.get("emotion"),
            "risk": primary.get("risk"),
            "is_followup": primary.get("is_followup"),
            "followup_of": primary.get("followup_of"),
            "normalized_question": primary.get("normalized_question"),
            "confidence": primary.get("confidence"),
            "required_modules": primary.get("required_modules") or [],
            "split_count": len(dna.get("questions") or []) if isinstance(dna, dict) else 0,
            "source": dna.get("source") if isinstance(dna, dict) else "error",
            "latency_ms": dna.get("latency_ms") if isinstance(dna, dict) else 0,
        }
