"""Phase 2 Understand — ONE LLM that owns branch + routing JSON.

Authority for: branch, domain, archetype, question_type, timing,
subject, target, knowledge, and follow-up (new vs continuing thread).
Downstream engines consume this JSON. Knowledge vs engine and follow-up
resolution are decided HERE — not by regex first.
"""
from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Optional

# Final architecture: exactly TWO execution branches after hard gates.
BRANCHES = frozenset({"knowledge", "engine"})
TURN_TYPES = frozenset({"new", "followup"})

_DOMAINS = frozenset({
    "love", "marriage", "relationship", "career", "health", "finance",
    "education", "children", "property", "travel", "litigation", "vehicle",
    "spiritual", "remedy", "general",
})

# domain → static engine key used by raw_passthrough_ask flags
_DOMAIN_ENGINE_KEY: dict[str, str] = {
    "love": "mr",
    "marriage": "mr",
    "relationship": "mr",
    "career": "career",
    "health": "health",
    "finance": "finance",
    "education": "education",
    "children": "children",
    "property": "property",
    "travel": "travel",
    "litigation": "litigation",
    "vehicle": "vehicle",
    "spiritual": "gap",
    "remedy": "mr",
    "general": "mr",
}

_TIMEOUT_S = 16

_PROMPT = """You are Cosmo Understand — ONE classification step for an astrology Ask product.
Read the CURRENT user message and Recent chat (if any). Hindi/Hinglish/English OK.
Return STRICT JSON only:

{{
  "turn_type": "new|followup",
  "effective_question": "<one standalone question to answer>",
  "wants_explain": false,
  "branch": "knowledge|engine",
  "domain": "<one domain>",
  "archetype": "<snake_case theme bucket>",
  "question_type": "prediction|timing|decision|verification|explanation|overview|remedy",
  "timing": false,
  "subject": "self|partner|couple|ex|family|friend|other|unknown",
  "target": "self|partner|couple|third_person|situation|unknown",
  "knowledge": false,
  "question_summary": "<2-6 short lines explaining what user wants — do NOT echo the question>",
  "confidence": 0.0
}}

turn_type / effective_question (decide BEFORE branch):
- new = fresh topic; effective_question = current message (cleaned).
- followup = continues Recent chat (e.g. "aur detail", "exact month?", "kaise bataya?", "uske baare me", short "kab?" after a prior topic).
  effective_question = rewrite as ONE clear standalone question using prior user topic + current message.
  Example: prior "meri shaadi kab?" + current "exact month?" → "Meri shaadi kab hogi — exact month batao".
- wants_explain=true ONLY if user asks how/why the previous answer was decided ("kaise bataya", "kya check kiya").
  Then effective_question = the prior astrology question being explained.

branch (ONLY these two values):
- knowledge = general astrology THEORY / education / named-lagna advice NOT reading THIS user's personal chart.
  Examples: "Leo lagna gemstone?", "dasha kya hoti hai?", "3rd house strong for younger brother?"
  knowledge=true when branch=knowledge.
- engine = personal life/chart outcome for THIS user (mera/meri/mujhe/my chart) OR clearly their future result.
  Examples: "meri shaadi kab?", "mera career kaisa?", "partner loyal hai?"
  knowledge=false when branch=engine.

domain: love|marriage|relationship|career|health|finance|education|children|property|travel|litigation|vehicle|spiritual|remedy|general
archetype: short snake_case theme (e.g. gemstone_remedy, marriage_timing, partner_loyalty, younger_sibling).
timing=true ONLY for a real WHEN anchor (kab/when/kis saal/month/date). "Kya hoga" alone → timing=false.
question_summary: explain intent — never copy-paste the question.

Recent chat:
{history}

Current user message:
{question}"""


def format_history_for_understand(history: Any, *, max_turns: int = 6) -> str:
    """Compact recent chat for Understand — empty string if none."""
    if not isinstance(history, (list, tuple)) or not history:
        return "(none)"
    lines: list[str] = []
    for item in list(history)[-max_turns:]:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip().lower()
        if role in ("user", "human"):
            who = "User"
        elif role in ("assistant", "cosmo", "bot", "ai"):
            who = "Assistant"
        else:
            continue
        text = str(item.get("text") or item.get("content") or "").strip()
        if not text:
            continue
        text = re.sub(r"\s+", " ", text)[:220]
        lines.append(f"{who}: {text}")
    return "\n".join(lines) if lines else "(none)"


def phase2_understand_enabled() -> bool:
    return (os.environ.get("ASK_UNDERSTAND_PHASE2") or "1").strip() != "0"


def normalize_branch(raw: Any) -> str:
    b = str(raw or "").strip().lower()
    if b in BRANCHES:
        return b
    # Compat bridges — refuse/off-topic collapse to engine (hard gates already ran).
    if b in ("llm_knowledge", "theory", "general_knowledge", "education"):
        return "knowledge"
    if b in (
        "llm_chart", "chart_llm", "chart_fact", "engine_static", "engine_timing",
        "refuse", "block", "deny", "off_topic",
    ):
        return "engine"
    return "engine"


def domain_to_engine_key(domain: str) -> str:
    d = _normalize_domain(domain)
    return _DOMAIN_ENGINE_KEY.get(d, "mr")


def phase2_engine_static_flags(u: dict[str, Any] | None) -> dict[str, bool]:
    """Sole engine routing from Understand JSON — no secondary detectors."""
    keys = (
        "education", "children", "property", "vehicle", "travel", "litigation",
        "gap", "network", "luck", "career", "finance", "health", "mr",
    )
    flags = {k: False for k in keys}
    src = u if isinstance(u, dict) else {}
    if str(src.get("branch") or "engine") != "engine":
        return flags
    eng = domain_to_engine_key(str(src.get("domain") or "general"))
    if eng in flags:
        flags[eng] = True
    else:
        flags["mr"] = True
    return flags


def phase2_llm_intent(u: dict[str, Any], *, question: str = "") -> dict[str, Any]:
    """Intent dict derived only from Understand JSON."""
    domain = str(u.get("domain") or "general")
    archetype = str(u.get("archetype") or "general")
    timing = bool(u.get("timing"))
    out: dict[str, Any] = {
        "domain": domain,
        "is_timing": timing,
        "is_decision": str(u.get("question_type") or "") == "decision",
        "wants_explain": False,
        "question_summary": str(u.get("question_summary") or ""),
        "source": "understand_phase2",
        "confidence": float(u.get("confidence") or 0.7),
        "branch": u.get("branch"),
        "knowledge": bool(u.get("knowledge")),
    }
    if domain in ("love", "marriage", "relationship"):
        out["mr_archetype"] = archetype
    elif domain == "career":
        out["career_archetype"] = archetype
    elif domain == "finance":
        out["finance_archetype"] = archetype
    elif domain == "health":
        out["health_archetype"] = archetype
    elif domain == "education":
        out["education_archetype"] = archetype
    elif domain == "children":
        out["children_archetype"] = archetype
    elif domain == "property":
        out["property_archetype"] = archetype
    elif domain == "travel":
        out["travel_archetype"] = archetype
    elif domain == "litigation":
        out["litigation_archetype"] = archetype
    _ = question
    return out


def _normalize_domain(raw: Any) -> str:
    d = str(raw or "").strip().lower()
    aliases = {
        "legal": "litigation",
        "job": "career",
        "money": "finance",
        "wealth": "finance",
        "sehat": "health",
        "shaadi": "marriage",
        "pyaar": "love",
        "self": "general",
        "family": "general",
        "partner": "love",
        "couple": "love",
    }
    d = aliases.get(d, d)
    return d if d in _DOMAINS else "general"


def _coerce_bool(raw: Any, default: bool = False) -> bool:
    if isinstance(raw, bool):
        return raw
    if raw is None:
        return default
    s = str(raw).strip().lower()
    if s in ("1", "true", "yes", "on"):
        return True
    if s in ("0", "false", "no", "off"):
        return False
    return default


def normalize_understand(data: dict[str, Any] | None, *, question: str = "") -> dict[str, Any]:
    """Normalize LLM/raw dict into the locked Phase 2 schema."""
    src = data if isinstance(data, dict) else {}
    branch = normalize_branch(src.get("branch"))
    knowledge = _coerce_bool(src.get("knowledge"), default=(branch == "knowledge"))
    if branch == "knowledge":
        knowledge = True
    if branch == "engine":
        knowledge = False

    domain = _normalize_domain(src.get("domain"))
    if branch == "knowledge" and domain == "general":
        domain = "remedy" if re.search(
            r"(?ix)\b(gemstone|ratna|ratn|remedy|upay|mani)\b", question or ""
        ) else "spiritual"

    archetype = str(src.get("archetype") or src.get("bucket") or "").strip().lower()
    archetype = re.sub(r"[^a-z0-9_]+", "_", archetype).strip("_") or (
        "gemstone_remedy" if branch == "knowledge" else "general"
    )

    qtype = str(src.get("question_type") or "explanation").strip().lower()
    if qtype not in (
        "prediction", "timing", "decision", "verification",
        "explanation", "overview", "remedy",
    ):
        qtype = "timing" if _coerce_bool(src.get("timing")) else "explanation"

    timing = _coerce_bool(src.get("timing"), default=(qtype == "timing"))
    if branch != "engine":
        timing = False

    summary = str(src.get("question_summary") or src.get("user_wants") or "").strip()
    summary = summary.replace("\\n", "\n")[:1800]

    try:
        confidence = float(src.get("confidence") or 0.7)
    except (TypeError, ValueError):
        confidence = 0.7
    confidence = max(0.0, min(1.0, confidence))

    turn_raw = str(src.get("turn_type") or src.get("turn") or "new").strip().lower()
    if turn_raw in ("follow_up", "follow-up", "continuation", "continue"):
        turn_raw = "followup"
    turn_type = turn_raw if turn_raw in TURN_TYPES else "new"
    if _coerce_bool(src.get("is_followup")):
        turn_type = "followup"

    wants_explain = _coerce_bool(src.get("wants_explain"))
    if wants_explain:
        turn_type = "followup"

    current_q = (question or "").strip()
    effective = str(src.get("effective_question") or src.get("resolved_question") or "").strip()
    effective = re.sub(r"\s+", " ", effective).strip()
    if not effective:
        effective = current_q
    if len(effective) > 900:
        effective = effective[:900].rstrip()

    answer_mode = "llm_knowledge" if branch == "knowledge" else "engine"

    return {
        "branch": branch,
        "domain": domain,
        "archetype": archetype,
        "bucket": archetype,
        "question_type": qtype,
        "timing": timing,
        "subject": str(src.get("subject") or "unknown").strip().lower() or "unknown",
        "target": str(src.get("target") or "unknown").strip().lower() or "unknown",
        "knowledge": knowledge,
        "question_summary": summary,
        "user_wants": summary,
        "confidence": confidence,
        "answer_mode": answer_mode,
        "turn_type": turn_type,
        "is_followup": turn_type == "followup",
        "effective_question": effective,
        "wants_explain": wants_explain,
        "source": str(src.get("source") or "understand_phase2"),
        "latency_ms": int(src.get("latency_ms") or 0),
    }


def understand_to_question_dna(u: dict[str, Any], *, question: str = "") -> dict[str, Any]:
    """Synthetic DNA payload so existing DNA fast-path routing keeps working."""
    item = {
        "normalized_question": (question or "").strip()[:500],
        "domain": u.get("domain") or "general",
        "bucket": u.get("archetype") or u.get("bucket") or "general",
        "intent": str(u.get("question_summary") or "")[:400],
        "subject": u.get("subject") or "unknown",
        "target": u.get("target") or "unknown",
        "question_type": u.get("question_type") or "explanation",
        "timing": bool(u.get("timing")),
        "tense": "future" if u.get("timing") else "present",
        "emotion": "neutral",
        "risk": "low",
        "is_followup": bool(u.get("is_followup") or u.get("turn_type") == "followup"),
        "followup_of": "",
        "confidence": float(u.get("confidence") or 0.7),
        "user_wants": str(u.get("question_summary") or "")[:400],
        "understanding_confidence": float(u.get("confidence") or 0.7),
        "answer_style": "short_paragraph",
        "answer_approach": "phase2_understand",
        "bucket_match_confidence": "high",
        "engine_archetype": u.get("archetype"),
        "turn_type": u.get("turn_type") or "new",
        "effective_question": str(u.get("effective_question") or question or "")[:500],
        "wants_explain": bool(u.get("wants_explain")),
    }
    return {
        "questions": [item],
        "source": "understand_phase2",
        "latency_ms": int(u.get("latency_ms") or 0),
        "branch": u.get("branch"),
        "knowledge": bool(u.get("knowledge")),
        "turn_type": u.get("turn_type") or "new",
    }


def understand_to_admin(u: dict[str, Any], *, question: str = "", question_raw: str = "") -> dict[str, Any]:
    """Admin intent dict consumed by raw_passthrough / master router."""
    dna = understand_to_question_dna(u, question=question)
    summary = str(u.get("question_summary") or "").strip()
    domain = str(u.get("domain") or "general")
    archetype = str(u.get("archetype") or "general")
    admin: dict[str, Any] = {
        "branch": u.get("branch"),
        "knowledge": bool(u.get("knowledge")),
        "domain": domain,
        "routed_domain": domain,
        "archetype": archetype,
        "routed_archetype": archetype,
        "routed_timing": bool(u.get("timing")),
        "answer_mode": u.get("answer_mode") or "engine",
        "question_summary": summary,
        "question_meaning": summary,
        "question_scope": domain,
        "question_raw": question_raw or question,
        "question_normalized": question,
        "understanding_source": "understand_phase2",
        "question_understood": "yes" if len(summary) >= 20 else "no",
        "question_dna": dna,
        "understand_phase2": u,
        "dna_routing_applied": True,
        "subject": u.get("subject"),
        "target": u.get("target"),
        "confidence": float(u.get("confidence") or 0.7),
        "turn_type": u.get("turn_type") or "new",
        "is_followup": bool(u.get("is_followup") or u.get("turn_type") == "followup"),
        "effective_question": str(u.get("effective_question") or question or ""),
        "wants_explain": bool(u.get("wants_explain")),
    }
    # Domain archetype keys used by classify_and_route_ask
    key_map = {
        "love": "mr_archetype",
        "marriage": "mr_archetype",
        "relationship": "mr_archetype",
        "career": "career_archetype",
        "finance": "finance_archetype",
        "health": "health_archetype",
        "education": "education_archetype",
        "children": "children_archetype",
        "property": "property_archetype",
        "travel": "travel_archetype",
        "litigation": "litigation_archetype",
    }
    ak = key_map.get(domain)
    if ak:
        admin[ak] = archetype
    return admin


def refuse_payload(*, question: str = "", lang: str = "hn", reason: str = "understand_refuse") -> dict[str, Any]:
    if lang == "en":
        text = (
            "I can't help with that request. Ask me about your chart, timing, "
            "relationship, career, health, or general Vedic astrology."
        )
    else:
        text = (
            "Maaf kijiye — yeh request Cosmic Lens ke astrology scope me nahi aati. "
            "Apni kundli, timing, relationship, career, health, ya general jyotish "
            "ke baare me poochiye."
        )
    return {
        "text": text,
        "topic": "general",
        "question_type": "STATIC",
        "confidence": 1.0,
        "source": reason,
        "engine_tag": "ans-cosmo",
        "follow_ups": [
            "Meri kundli se related sawaal poochun?",
            "General jyotish concept samjhao",
        ],
    }


def run_understand_phase2(
    question: str,
    *,
    client: Any = None,
    model: Optional[str] = None,
    question_raw: str = "",
    history: Any = None,
) -> dict[str, Any]:
    """ONE Understand LLM call. Never raises — returns normalized dict + ok flag."""
    q = (question or "").strip()
    hist_block = format_history_for_understand(history)
    if not q:
        out = normalize_understand(
            {"branch": "engine", "domain": "general", "question_summary": "Empty question", "confidence": 1.0},
            question=q,
        )
        out["ok"] = False
        out["source"] = "understand_phase2_empty"
        return out

    if not phase2_understand_enabled():
        out = normalize_understand({"branch": "engine", "source": "phase2_disabled"}, question=q)
        out["ok"] = False
        return out

    if client is None:
        try:
            from openai_helper import _get_client  # type: ignore

            client = _get_client()
        except Exception as exc:
            out = normalize_understand({"branch": "engine", "source": "understand_phase2_no_client"}, question=q)
            out["ok"] = False
            out["error"] = str(exc)[:160]
            return out

    if client is None:
        out = normalize_understand({"branch": "engine", "source": "understand_phase2_no_client"}, question=q)
        out["ok"] = False
        return out

    if model is None:
        model = (
            os.environ.get("ASK_UNDERSTAND_PHASE2_MODEL")
            or os.environ.get("ASK_UNDERSTAND_MODEL")
            or os.environ.get("ASK_INTENT_MODEL")
            or os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
        )

    t0 = time.time()
    try:
        prompt = _PROMPT.format(history=hist_block[:2400], question=q[:900])
        kwargs: dict[str, Any] = dict(
            model=model,
            temperature=0.1,
            timeout=_TIMEOUT_S,
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
        )
        try:
            resp = client.chat.completions.create(max_completion_tokens=700, **kwargs)
        except TypeError:
            resp = client.chat.completions.create(max_tokens=700, **kwargs)
        raw = (resp.choices[0].message.content or "").strip()
        data = json.loads(raw)
        if not isinstance(data, dict):
            data = {}
        data["source"] = "understand_phase2"
        data["latency_ms"] = int((time.time() - t0) * 1000)
        out = normalize_understand(data, question=q)
        out["ok"] = True
        out["question_raw"] = question_raw or q
        return out
    except Exception as exc:
        out = normalize_understand(
            {
                "branch": "engine",
                "domain": "general",
                "question_summary": "",
                "confidence": 0.4,
                "source": "understand_phase2_error",
                "latency_ms": int((time.time() - t0) * 1000),
            },
            question=q,
        )
        out["ok"] = False
        out["error"] = str(exc)[:200]
        return out
