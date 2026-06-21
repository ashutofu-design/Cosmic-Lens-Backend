"""LLM-first intent classifier for the raw-passthrough Ask path.

A single cheap JSON call (gpt-4.1-mini) that reads the user's question and
returns the routing decisions the regex layer used to make:

  - domain        : marriage | love | career | finance | health | general
  - is_timing     : kab / when / muhurat style question
  - is_decision   : should-I / yes-no decision question
  - wants_explain : user explicitly wants a longer "why" explanation
  - mr_archetype  : one of the MR archetype ids (only when domain is
                    marriage/love), so the MR engine can be dispatched
                    precisely instead of falling through to general_mr
  - confidence    : float in [0, 1]
  - source        : "llm" | "llm_low_conf" | "llm_error" | "llm_unavailable"

This module NEVER raises — on any failure it returns a dict with
source="llm_error"/"llm_unavailable" so the caller can fall back to the
existing regex routing with zero behaviour change.

Gated upstream by ASK_LLM_INTENT=1 (see raw_passthrough_ask).
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Optional

# Keep in sync with ask_mr/classifier.py archetype ids.
MR_ARCHETYPES = {
    "spouse_profession",
    "spouse_wealth",
    "secret_relationship",
    "one_sided_love",
    "obsession",
    "bed_intimacy",
    "self_worth",
    "partner_nature",
    "long_distance",
    "general_mr",
    "loyalty_trust",
    "emotional_attachment",
    "patchup",
    "chemistry",
    "love_vs_arranged",
    "family_approval",
    "manglik",
    "second_marriage",
    "breakup_risk",
}

DOMAINS = {"marriage", "love", "career", "finance", "health", "general"}

# Low-confidence cutoff — below this the caller treats the result as
# untrustworthy and falls back to regex.
_LOW_CONF = 0.6
_TIMEOUT_S = 8

_PROMPT_TEMPLATE = """You are an intent router for a Vedic-astrology Q&A app. \
Read the user's question (Hindi/Hinglish/English) and return STRICT JSON only.

Decide:
1. "domain": the life area the question is really about. One of:
   marriage, love, career, finance, health, general.
   IMPORTANT: judge the REAL subject, not just keywords. e.g. "will my \
partner support my career" is about CAREER support, not marriage quality.
2. "is_timing": true if the user asks WHEN something happens (kab, timing, \
date, muhurat, age). false otherwise.
3. "is_decision": true if it is a should-I / yes-or-no decision question.
4. "wants_explain": true if the user wants a detailed "why" explanation \
(samjhao, explain, reason, kyun) rather than a short verdict.
5. "mr_archetype": ONLY when domain is marriage or love, pick the single \
best-fitting archetype id; otherwise null. Allowed ids and meaning:
   - spouse_profession: partner's job/career field
   - spouse_wealth: partner's wealth / financial status
   - secret_relationship: secret/hidden/parallel affair
   - one_sided_love: one-sided love, crush, proposal
   - obsession: obsession, jealousy, possessiveness
   - bed_intimacy: physical/sexual intimacy
   - self_worth: user's own confidence/boundaries
   - partner_nature: partner's nature/personality/behaviour/age, incl. \
whether partner supports the native's goals/career
   - long_distance: long-distance relationship
   - general_mr: overall marriage quality/happiness/compatibility
   - loyalty_trust: loyalty, trust, cheating, commitment
   - emotional_attachment: emotional bonding / feelings depth
   - patchup: reconciliation, ex returning
   - chemistry: attraction, romance, spark
   - love_vs_arranged: love vs arranged marriage
   - family_approval: family/parents approval, intercaste
   - manglik: manglik / mangal dosh
   - second_marriage: second/again marriage
   - breakup_risk: breakup, separation, divorce risk
6. "interpretation": ONE short plain sentence describing what the user really \
wants to know, phrased as "User wants to know ...". Write it in simple \
English. e.g. "User wants to know if their partner will support their career."
7. "confidence": 0.0-1.0 how sure you are.

Return ONLY this JSON object:
{{"domain": "...", "is_timing": false, "is_decision": false, \
"wants_explain": false, "mr_archetype": null, \
"interpretation": "User wants to know ...", "confidence": 0.0}}

Question: {question}"""


def _error(reason: str, source: str = "llm_error") -> dict:
    return {
        "domain": "general",
        "is_timing": False,
        "is_decision": False,
        "wants_explain": False,
        "mr_archetype": None,
        "interpretation": "",
        "confidence": 0.0,
        "source": source,
        "error": reason[:200],
    }


def classify_ask_intent(
    question: str,
    *,
    client: Any = None,
    model: Optional[str] = None,
) -> dict:
    """Classify an Ask question with one LLM call. Never raises.

    Returns a dict with keys: domain, is_timing, is_decision, wants_explain,
    mr_archetype, confidence, source (+ latency_ms / error diagnostics).
    """
    q = (question or "").strip()
    if not q:
        return _error("empty question", source="llm_unavailable")

    if model is None:
        model = (
            os.environ.get("ASK_INTENT_MODEL")
            or os.environ.get("QU_MODEL")
            or os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
        )

    if client is None:
        try:
            from openai_helper import _get_client  # type: ignore

            client = _get_client()
        except Exception as exc:  # pragma: no cover - defensive
            return _error(f"client import failed: {exc}", source="llm_unavailable")

    if client is None:
        return _error("no OpenAI client", source="llm_unavailable")

    t0 = time.time()
    _create_kwargs = dict(
        model=model,
        temperature=0.1,
        timeout=_TIMEOUT_S,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": _PROMPT_TEMPLATE.format(question=q)}],
    )
    try:
        # gpt-5 series / some proxies renamed max_tokens -> max_completion_tokens
        # and reject the legacy name with HTTP 400. Try new first, fall back.
        try:
            resp = client.chat.completions.create(
                max_completion_tokens=200, **_create_kwargs
            )
        except TypeError:
            resp = client.chat.completions.create(max_tokens=200, **_create_kwargs)
        except Exception as exc:
            _msg = str(exc).lower()
            if ("max_tokens" in _msg and "max_completion_tokens" in _msg) or (
                "use 'max_tokens'" in _msg
            ):
                resp = client.chat.completions.create(max_tokens=200, **_create_kwargs)
            else:
                raise

        latency_ms = int((time.time() - t0) * 1000)
        raw = (resp.choices[0].message.content or "").strip()
        data = json.loads(raw)
    except Exception as exc:
        fb = _error(str(exc))
        fb["latency_ms"] = int((time.time() - t0) * 1000)
        return fb

    domain = str(data.get("domain") or "").strip().lower()
    if domain not in DOMAINS:
        domain = "general"

    archetype = data.get("mr_archetype")
    if isinstance(archetype, str):
        archetype = archetype.strip().lower()
    if archetype not in MR_ARCHETYPES:
        archetype = None
    # Archetype only makes sense for relationship domains.
    if domain not in {"marriage", "love"}:
        archetype = None
    elif archetype is None:
        # Domain is relationship but model gave no/invalid archetype — use the
        # safe catch-all so the MR engine still runs deterministically.
        archetype = "general_mr"

    try:
        conf = float(data.get("confidence") or 0.0)
    except (TypeError, ValueError):
        conf = 0.0
    conf = max(0.0, min(1.0, conf))

    interpretation = str(data.get("interpretation") or "").strip()[:300]

    return {
        "domain": domain,
        "is_timing": bool(data.get("is_timing")),
        "is_decision": bool(data.get("is_decision")),
        "wants_explain": bool(data.get("wants_explain")),
        "mr_archetype": archetype,
        "interpretation": interpretation,
        "confidence": conf,
        "source": "llm_low_conf" if conf < _LOW_CONF else "llm",
        "latency_ms": latency_ms,
    }
