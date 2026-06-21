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
    "spouse_appearance",
    "children_parenting",
    "karmic_marriage",
    "lifestyle_marriage",
    "dating_courtship",
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

CAREER_ARCHETYPES = {
    "job_vs_business",
    "sector_fit",
    "career_traits",
    "strengths_skills",
    "entrepreneurship",
    "work_environment",
    "income_wealth",
    "foreign_career",
    "workplace_relations",
    "fame_recognition",
    "creativity_innovation",
    "career_obstacles",
    "education_career",
    "retirement_legacy",
    "general_career",
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
   CRITICAL RULE: if the question is ABOUT THE PARTNER / SPOUSE / lover \
(their support, nature, behaviour, loyalty, feelings, family) — even if it \
also mentions career or money — the domain is "marriage" or "love" (the \
PARTNER is the subject). e.g. "will my partner support my career" → domain \
love (partner is the subject), NOT career. Use "career" / "finance" ONLY when \
the question is about the NATIVE's own job / money, with no partner focus.
2. "is_timing": true if the user asks WHEN something happens (kab, timing, \
date, muhurat, age). false otherwise.
3. "is_decision": true if it is a should-I / yes-or-no decision question.
4. "wants_explain": true if the user wants a detailed "why" explanation \
(samjhao, explain, reason, kyun) rather than a short verdict.
5. "mr_archetype": ONLY when domain is marriage or love, pick the single \
best-fitting archetype id; otherwise null. Allowed ids and meaning:
   - spouse_profession: partner's job/career field (doctor/IT/gov/business etc.)
   - spouse_wealth: partner's wealth / financial status / saving habits
   - spouse_appearance: partner's physical look (height, face, eyes, complexion, voice, aura)
   - children_parenting: spouse parenting style, bond with children, family values
   - karmic_marriage: soulmate, past life, karmic debt, spiritual growth via marriage
   - lifestyle_marriage: luxury/travel/social/home/abroad settlement after marriage
   - dating_courtship: true love, dating, flirting, red/green flags, friend-to-lover
   - secret_relationship: secret/hidden/parallel affair
   - one_sided_love: one-sided love, crush, proposal
   - obsession: obsession, jealousy, possessiveness
   - bed_intimacy: physical/sexual intimacy
   - self_worth: user's own confidence/boundaries
   - partner_nature: partner's nature/personality/behaviour/age/respect/temper; \
OR spouse's in-laws / family-wale (8th house axis — NOT user's parents approval)
   - long_distance: long-distance relationship
   - general_mr: overall marriage quality/happiness/compatibility, OR whether \
the partner will SUPPORT the native's career / life goals / decisions
   - loyalty_trust: loyalty, trust, cheating, commitment
   - emotional_attachment: emotional bonding / feelings depth
   - patchup: reconciliation, ex returning
   - chemistry: attraction, romance, spark
   - love_vs_arranged: love vs arranged marriage
   - family_approval: family/parents approval, intercaste
   - manglik: manglik / mangal dosh
   - second_marriage: second/again marriage
   - breakup_risk: breakup, separation, divorce risk
6. "career_archetype": ONLY when domain is career, pick best id; otherwise null:
   - job_vs_business: ONLY employment vs self-employment (job OR business, naukri ya dhandha)
   - sector_fit: industry/field OR which business is best / konsa business / business type / line
   - career_traits: leadership, pressure, risk, discipline, team, independence
   - strengths_skills: strengths, weaknesses, skills to develop
   - entrepreneurship: startup, partnership business, online, family business, trading business
   - work_environment: remote, corporate, MNC, public/private sector
   - income_wealth: salary, passive income, high income, freelancing, commission
   - foreign_career: abroad job, foreign company, settle abroad for work
   - workplace_relations: boss, colleagues, job satisfaction
   - fame_recognition: fame, reputation, recognition in career
   - creativity_innovation: creative field, innovation, content creation
   - career_obstacles: delays, setbacks, obstacles in career
   - education_career: study, degree, education for career
   - retirement_legacy: late career, legacy, retirement tone
   - general_career: other career questions
7. "interpretation": ONE short plain sentence describing what the user really \
wants to know, phrased as "User wants to know ...". Write it in simple \
English. e.g. "User wants to know if their partner will support their career."
8. "confidence": 0.0-1.0 how sure you are.

Return ONLY this JSON object:
{{"domain": "...", "is_timing": false, "is_decision": false, \
"wants_explain": false, "mr_archetype": null, "career_archetype": null, \
"interpretation": "User wants to know ...", "confidence": 0.0}}

Question: {question}"""


def _error(reason: str, source: str = "llm_error") -> dict:
    return {
        "domain": "general",
        "is_timing": False,
        "is_decision": False,
        "wants_explain": False,
        "mr_archetype": None,
        "career_archetype": None,
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

    if domain == "career":
        career_arch = data.get("career_archetype")
        if isinstance(career_arch, str):
            career_arch = career_arch.strip().lower()
        if career_arch not in CAREER_ARCHETYPES:
            career_arch = None
        if career_arch is None:
            career_arch = "general_career"
    else:
        career_arch = None

    interpretation = str(data.get("interpretation") or "").strip()[:300]

    return {
        "domain": domain,
        "is_timing": bool(data.get("is_timing")),
        "is_decision": bool(data.get("is_decision")),
        "wants_explain": bool(data.get("wants_explain")),
        "mr_archetype": archetype,
        "career_archetype": career_arch,
        "interpretation": interpretation,
        "confidence": conf,
        "source": "llm_low_conf" if conf < _LOW_CONF else "llm",
        "latency_ms": latency_ms,
    }
