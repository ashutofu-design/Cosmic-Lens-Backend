"""Commitment engine narrator — JSON-only facts → natural Hinglish answer.

LLM never sees the kundli. It receives a compact ENGINE_JSON block plus strict
narration rules (direct answer → reasons → caution → timing → practical).
"""
from __future__ import annotations

import json
import re
from typing import Any

from .types import EngineResult

_VERDICT_LABELS = {
    "ready": "Ready",
    "cautious": "Cautious",
    "mixed": "Mixed",
    "low": "Low",
}

_LEVEL_SCORE_FALLBACK = {
    "ready": 82,
    "cautious": 68,
    "mixed": 55,
    "low": 42,
}

_BANNED_NARRATOR_PHRASES = re.compile(
    r"(?i)\b("
    r"kehna mushkil|mushkil hai ki|ho sakta hai|ho sakti hai|shayad|lagta hai|lagti hai|"
    r"perhaps|maybe|might|possibly|"
    r"patience rakho|boundaries set|communication strong|emotional clarity|"
    r"emotional investment|trust challenge|clear talk se|honest check-in"
    r")\b",
)

_GENERIC_UNLESS_IN_JSON = (
    "communication",
    "boundaries",
    "patience",
    "clarity",
    "emotional",
    "trust challenge",
    "honesty",
)

_FACTOR_HUMANIZE: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"partnership/commitment axis", re.I), "Strong relationship promise"),
    (re.compile(r"\bvenus\b", re.I), "Supportive Venus"),
    (re.compile(r"\bjupiter\b", re.I), "Long-term growth support"),
    (re.compile(r"\bsaturn\b", re.I), "Saturn delay on commitment"),
    (re.compile(r"\bmoon\b", re.I), "Emotional ups and downs"),
    (re.compile(r"\bmercury\b", re.I), "Communication clarity factor"),
    (re.compile(r"\bmars\b", re.I), "Passion / impulse factor"),
    (re.compile(r"\bdasha\b", re.I), "Current dasha support"),
    (re.compile(r"\btransit\b", re.I), "Current transit influence"),
    (re.compile(r"\bjaimini\b", re.I), "Soulmate timing layer"),
    (re.compile(r"\bbcp\b", re.I), "Marriage linkage pattern"),
]

_TIMING_RX = re.compile(
    r"(?i)(late\s+20\d{2}|early\s+20\d{2}|mid\s+20\d{2}|"
    r"20\d{2}\s*(?:ke\s+)?(?:end|start|mid)|"
    r"timing[:\s]+[^.;]+|window[^.;]+|phase[^.;]+)"
)


def _humanize_factor(raw: str) -> str:
    s = (raw or "").strip()
    if not s:
        return ""
    if ":" in s:
        s = s.split(":", 1)[0].strip()
    s = re.sub(r"\([^)]*\)", "", s).strip()
    s = re.sub(r"\s{2,}", " ", s)
    for rx, label in _FACTOR_HUMANIZE:
        if rx.search(s):
            return label
    s = re.sub(r"\b(house|sign|lord|karak|axis|dignity|occupants)\b.*", "", s, flags=re.I)
    s = s.strip(" ,;—-")
    return s[:80] if s else ""


def _humanize_warning(raw: str) -> str:
    s = _humanize_factor(raw)
    if not s:
        return ""
    low = s.lower()
    if "saturn" in low or "delay" in low:
        return "Some delay or hesitation possible"
    if "moon" in low or "emotional" in low:
        return "Emotional distance phases possible"
    if "mixed" in low:
        return "Mixed signals — clarity needed"
    return s


def _extract_timing_window(result: EngineResult, checks: dict[str, Any]) -> str:
    timing_data = checks.get("timing") or {}
    windows = timing_data.get("windows") or []
    if windows:
        w0 = windows[0] if isinstance(windows[0], dict) else {}
        label = str(w0.get("label") or w0.get("window") or "").strip()
        if label:
            return label
    pool = list(result.evidence_positive or []) + list(result.evidence or [])
    for line in pool:
        m = _TIMING_RX.search(str(line))
        if m:
            return m.group(0).strip().rstrip(".")
    return ""


def _compact_evidence_line(raw: str, *, max_len: int = 96) -> str:
    """Keep engine evidence verbatim — first clause only, no humanize drift."""
    s = (raw or "").strip()
    if not s:
        return ""
    s = re.split(r"[;]\s*", s)[0].strip()
    s = re.sub(r"\s{2,}", " ", s)
    return s[:max_len]


def _evidence_from_rules(
    rules_fired: list[Any],
    *,
    polarity: str,
    limit: int = 3,
) -> list[str]:
    out: list[str] = []
    for rule in rules_fired:
        if not isinstance(rule, dict):
            continue
        if str(rule.get("polarity") or "").strip().lower() != polarity:
            continue
        note = str(rule.get("note") or rule.get("evidence") or rule.get("label") or "").strip()
        line = _compact_evidence_line(note)
        if line and line not in out:
            out.append(line)
        if len(out) >= limit:
            break
    return out


    return out


def _resolve_confidence(level: str, checks: dict[str, Any], scorecard: dict[str, Any]) -> tuple[int, str]:
    """Numeric score + certainty label — never 0% when engine ran."""
    score = 0
    try:
        score = int(
            checks.get("primary_score")
            or (scorecard.get("primary") if isinstance(scorecard, dict) else 0)
            or 0
        )
    except (TypeError, ValueError):
        score = 0
    if score <= 0:
        score = _LEVEL_SCORE_FALLBACK.get(level, 55)
    certainty = str(checks.get("confidence_certainty") or "").strip().title()
    if certainty not in ("High", "Medium", "Low"):
        certainty = "High" if score >= 78 else ("Medium" if score >= 52 else "Low")
    return score, certainty


def _question_angles(question: str, checks: dict[str, Any]) -> tuple[str, bool, bool]:
    from ask_intent_fidelity import infer_partner_commitment_angle

    angle = str(checks.get("commitment_angle") or infer_partner_commitment_angle(question) or "general_commitment")
    ql = (question or "").lower()
    timepass_q = bool(re.search(r"time\s*pass|timepass", ql)) or angle == "time_pass"
    genuine_q = bool(re.search(r"genuine|sachch", ql)) or angle == "genuine_intent"
    return angle, timepass_q, genuine_q


def _build_direct_answer(level: str, *, timepass_q: bool, genuine_q: bool) -> str:
    lv = (level or "mixed").strip().lower()
    if lv == "low":
        base = (
            "Is chart ke hisaab se abhi partner ki taraf se strong aur stable commitment ka support kam dikh raha hai."
        )
        if timepass_q and genuine_q:
            tail = (
                "Is stage par unhe fully serious ya long-term committed nahi maana ja sakta — "
                "genuine long-term intent abhi weak dikhta hai."
            )
        elif timepass_q:
            tail = "Is stage par unhe sirf timepass ya casual intent zyada maana ja sakta hai, fully serious nahi."
        else:
            tail = "Is stage par unhe fully serious ya long-term committed nahi maana ja sakta."
        return f"{base} {tail}"
    if lv == "ready":
        return (
            "Is chart ke hisaab se partner ki taraf se commitment support strong dikhta hai. "
            "Long-term serious intent ko chart backing milti hai."
        )
    if lv == "cautious":
        return (
            "Is chart ke hisaab se partner me interest hai lekin commitment abhi cautious / hesitant phase me hai. "
            "Full stability abhi develop ho rahi hai."
        )
    return (
        "Is chart ke hisaab se partner ke commitment signals mixed hain — interest hai "
        "lekin consistency aur long-term clarity abhi poori nahi."
    )


def _build_verdict_line(verdict_label: str) -> str:
    return f"Engine verdict: {verdict_label} commitment."


def _join_evidence_lines(items: list[str], *, prefix: str, fallback: str) -> str:
    lines = [str(x).strip() for x in items if str(x).strip()]
    if not lines:
        return fallback
    if len(lines) == 1:
        return f"{prefix} {lines[0]}."
    return f"{prefix} {lines[0]}, aur {lines[1]}." + (
        f" Saath hi {lines[2]}." if len(lines) > 2 else ""
    )


def _build_meaning_note(level: str, warnings: list[str]) -> str:
    lv = (level or "").strip().lower()
    warn_blob = " ".join(warnings).lower()
    if "cheat" in warn_blob or "affair" in warn_blob:
        return "Ye cheating ka direct indication nahi hai — chart commitment hesitation dikha raha hai."
    if lv == "low":
        return (
            "Ye cheating ka indication nahi hai. Iska matlab sirf itna hai ki commitment abhi "
            "hesitant ya unstable dikh raha hai."
        )
    if lv in ("cautious", "mixed"):
        return "Ye rejection nahi hai — matlab process slow ya mixed ho sakta hai, clarity actions se aayegi."
    return "Chart long-term potential support karta hai — consistency se verdict strong hota hai."


def _build_practical_guidance(strongest: list[str], weakest: list[str]) -> str:
    blob = " ".join(weakest + strongest).lower()
    if "7th" in blob or "dusthana" in blob or "12th" in blob or "6th" in blob:
        return "Partner ke words se zyada unke consistent actions aur future planning ko observe karein."
    if "venus" in blob or "rahu" in blob:
        return "Attraction aur warmth ko actions se verify karein — sirf words par depend mat karein."
    if "saturn" in blob or "delay" in blob:
        return "Slow progress normal ho sakta hai — lekin regular effort aur planning dekhein, sirf promises nahi."
    if "jupiter" in blob:
        return "Positive signs ko time dein, lekin long-term planning unke behaviour se match honi chahiye."
    return "Partner ke consistent behaviour aur long-term planning ko observe karein — words se zyada actions matter karte hain."


def render_commitment_template_answer(
    data: dict[str, Any],
    question: str = "",
    *,
    lang: str = "hn",
) -> str:
    """Deterministic production answer — 8-step flow, engine evidence only."""
    verdict = str(data.get("final_verdict") or data.get("verdict") or "Mixed")
    level = verdict.strip().lower()
    strongest = list(data.get("strongest") or data.get("strongest_factor") or [])
    weakest = list(data.get("weakest") or data.get("weakest_factor") or [])
    warnings = list(data.get("warnings") or [])
    score = int(data.get("confidence") or 0)
    conf_label = str(data.get("confidence_label") or "Medium")
    timing = data.get("timing") if isinstance(data.get("timing"), dict) else None

    angle, timepass_q, genuine_q = _question_angles(question, data.get("_checks") or {})

    p1 = str(data.get("direct_answer") or "").strip() or _build_direct_answer(
        level, timepass_q=timepass_q, genuine_q=genuine_q
    )
    p2 = _build_verdict_line(verdict)
    p3 = _join_evidence_lines(
        strongest,
        prefix="Strongest astrology evidence:",
        fallback="Strongest astrology evidence: chart me kuch supportive commitment signals hain.",
    )
    p4 = _join_evidence_lines(
        weakest,
        prefix="Weakest astrology evidence:",
        fallback="Weakest astrology evidence: kuch challenging commitment indicators bhi hain.",
    )
    p5 = (
        "Is verdict ke peeche wajah: "
        + str(data.get("reason_summary") or _build_reason_summary(strongest, weakest))
    )
    p6 = str(data.get("meaning_note") or _build_meaning_note(level, warnings))
    parts = [p1, p2, p3, p4, p5, p6]
    if timing and str(timing.get("window") or "").strip():
        parts.append(f"Timing: {str(timing.get('window')).strip()}.")
    parts.append(f"Practical guidance: {data.get('practical_guidance') or _build_practical_guidance(strongest, weakest)}")
    parts.append(f"Confidence: {conf_label} ({score}%).")

    body = "\n\n".join(parts)
    if (lang or "hn").strip().lower() == "hi":
        return body  # same facts; Devanagari polish optional later
    return body


def _build_reason_summary(strongest: list[str], weakest: list[str]) -> str:
    s = strongest[0] if strongest else "supportive factors"
    w = weakest[0] if weakest else "challenging factors"
    return (
        f"Relationship promise ko {s} support karta hai, lekin {w} commitment ko weak banata hai. "
        "Isi wajah se consistency aur long-term intention par sawal uthte hain."
    )


def validate_commitment_narrator_output(text: str, data: dict[str, Any]) -> tuple[bool, list[str]]:
    """Reject hedging, generic advice, missing evidence, wrong confidence."""
    issues: list[str] = []
    t = (text or "").strip()
    if not t:
        return False, ["empty"]

    level = str(data.get("final_verdict") or "").strip().lower()
    if level == "low" and re.search(r"(?i)(kehna mushkil|mushkil hai|ho sakta|shayad|serious hain ya sirf)", t):
        issues.append("contradiction_low_verdict")

    if _BANNED_NARRATOR_PHRASES.search(t):
        issues.append("banned_phrase")

    json_blob = json.dumps(data, ensure_ascii=False).lower()
    for generic in _GENERIC_UNLESS_IN_JSON:
        if generic in t.lower() and generic not in json_blob:
            issues.append(f"generic_{generic}")

    for item in (data.get("strongest") or [])[:2]:
        tokens = [w for w in re.findall(r"[a-zA-Z]{4,}", str(item)) if w.lower() not in ("strong", "lord", "house")]
        if tokens and not any(tok.lower() in t.lower() for tok in tokens[:3]):
            issues.append("missing_strongest_evidence")
            break

    score = int(data.get("confidence") or 0)
    label = str(data.get("confidence_label") or "Medium")
    if not re.search(rf"Confidence:\s*{re.escape(label)}\s*\(\s*{score}\s*%", t, re.I):
        issues.append("confidence_line")

    return len(issues) == 0, issues


def engine_result_to_commitment_json(result: EngineResult) -> dict[str, Any]:
    """Compact narrator JSON — engine evidence only (no chart / no humanize drift)."""
    checks = result.checks or {}
    explanation = checks.get("explanation") or {}
    if not isinstance(explanation, dict):
        explanation = {}

    level = str(
        checks.get("commitment_level") or checks.get("level") or ""
    ).strip().lower()
    verdict_label = _VERDICT_LABELS.get(level, level.title() if level else "Mixed")

    scorecard = checks.get("scorecard") or {}
    if not isinstance(scorecard, dict):
        scorecard = {}
    score, conf_label = _resolve_confidence(level, checks, scorecard)

    rules_fired = list(checks.get("rules_fired") or [])
    strongest = _evidence_from_rules(rules_fired, polarity="positive", limit=3)
    weakest = _evidence_from_rules(rules_fired, polarity="negative", limit=2)

    if not strongest:
        sf = str(explanation.get("strongest_factor") or "").strip()
        if sf:
            strongest.append(_compact_evidence_line(sf))
        for item in explanation.get("why") or []:
            line = _compact_evidence_line(str(item))
            if line and line not in strongest:
                strongest.append(line)
    if not strongest:
        for item in (result.evidence_positive or [])[:3]:
            line = _compact_evidence_line(str(item))
            if line and line not in strongest:
                strongest.append(line)

    if not weakest:
        wf = str(explanation.get("weakest_factor") or "").strip()
        if wf:
            weakest.append(_compact_evidence_line(wf))
        for item in explanation.get("why_not") or []:
            line = _compact_evidence_line(str(item))
            if line and line not in weakest:
                weakest.append(line)
    if not weakest:
        for item in (result.evidence_negative or [])[:2]:
            line = _compact_evidence_line(str(item))
            if line and line not in weakest:
                weakest.append(line)

    reasons: list[str] = []
    for item in explanation.get("why") or []:
        line = _compact_evidence_line(str(item))
        if line and line not in reasons:
            reasons.append(line)
    for item in explanation.get("why_not") or []:
        line = _compact_evidence_line(str(item))
        if line and line not in reasons:
            reasons.append(line)
    if not reasons:
        for item in (result.summary or [])[:2]:
            line = _compact_evidence_line(str(item))
            if line:
                reasons.append(line)

    warnings: list[str] = []
    for item in weakest[:2]:
        if item and item not in warnings:
            warnings.append(item)
    if checks.get("contradiction"):
        warnings.append("Mixed signals in chart")

    timing_window = _extract_timing_window(result, checks)
    timing_block: dict[str, str] | None = None
    if timing_window:
        timing_block = {"window": timing_window}

    angle = str(checks.get("commitment_angle") or "general_commitment")
    _, timepass_q, genuine_q = _question_angles("", {**checks, "commitment_angle": angle})
    direct_answer = _build_direct_answer(level, timepass_q=timepass_q, genuine_q=genuine_q)
    reason_summary = _build_reason_summary(strongest[:2], weakest[:2])
    practical = _build_practical_guidance(strongest, weakest)
    meaning_note = _build_meaning_note(level, warnings)

    payload: dict[str, Any] = {
        "question_type": "commitment",
        "final_verdict": verdict_label,
        "commitment_level": verdict_label,
        "direct_answer": direct_answer,
        "verdict_line": _build_verdict_line(verdict_label),
        "strongest": strongest[:3],
        "weakest": weakest[:2],
        "reason": reasons[:4],
        "reason_summary": reason_summary,
        "meaning_note": meaning_note,
        "practical_guidance": practical,
        "confidence": score,
        "confidence_label": conf_label,
        "forbidden_phrases": [
            "kehna mushkil",
            "ho sakta hai",
            "shayad",
            "patience rakho",
            "boundaries",
            "communication strong",
            "emotional clarity",
        ],
        # backward-compatible keys for admin / tests
        "verdict": verdict_label,
        "strongest_factor": strongest[:3],
        "weakest_factor": weakest[:2],
        "warnings": warnings[:3],
    }
    if timing_block:
        payload["timing"] = timing_block
    payload["_meta"] = {
        "commitment_angle": angle,
        "headline": (result.verdict or "").strip(),
        "mode": checks.get("mode") or "static",
    }
    payload["locked_template"] = render_commitment_template_answer(
        {k: v for k, v in payload.items()},
        question=str(checks.get("question") or ""),
    )
    return payload


def commitment_narrator_payload(
    result: EngineResult,
    *,
    wants_explain: bool = False,
    question: str = "",
) -> str:
    """Facts block for LLM — ENGINE_JSON + LOCKED_TEMPLATE (minimal rephrase only)."""
    data = engine_result_to_commitment_json(result)
    meta = data.pop("_meta", {})
    locked = data.pop("locked_template", "")
    json_block = json.dumps(data, indent=2, ensure_ascii=False)

    lines = [
        "ARCHETYPE: commitment",
        "SOURCE_LOCK: ENGINE_JSON_ONLY — you do NOT see the birth chart or kundli.",
        "Narrate ONLY from ENGINE_JSON + LOCKED_TEMPLATE. Never invent planets, houses, dasha, or dates.",
        "",
        "ENGINE_JSON:",
        json_block,
        "",
        f"QUESTION_ANGLE: {meta.get('commitment_angle', 'general_commitment')}",
        f"VERDICT_HEADLINE: {meta.get('headline', '')}",
        "",
        "LOCKED_TEMPLATE (mandatory structure — rephrase lightly in Hinglish, do NOT add/remove facts):",
        locked,
        "",
        "OUTPUT RULES (production — zero freedom):",
        "STEP 1: Direct answer — use direct_answer from JSON; verdict Low → NEVER say 'mushkil hai' / 'ho sakta hai'.",
        "STEP 2: Verdict line — use verdict_line.",
        "STEP 3: Strongest evidence — name ONLY strongest[] items verbatim meaning.",
        "STEP 4: Weakest evidence — name ONLY weakest[] items.",
        "STEP 5: Reason — use reason_summary.",
        "STEP 6: Meaning — use meaning_note (no cheating talk unless in warnings).",
        "STEP 7: Timing — ONLY if timing.window exists.",
        "STEP 8: Practical — use practical_guidance ONLY.",
        "FINAL LINE: Confidence: {confidence_label} ({confidence}%). — exact numbers from JSON.",
        "BANNED: any word in forbidden_phrases[]; communication; boundaries; patience; clarity unless in JSON.",
        "BANNED: new sentences not derived from LOCKED_TEMPLATE.",
        "Never change step order. Never contradict final_verdict.",
    ]
    if wants_explain:
        lines.append("LENGTH: expand each step to 1–2 sentences max (120–150 words total).")
    else:
        lines.append("LENGTH: keep LOCKED_TEMPLATE length (85–120 words). Same paragraphs, light Hinglish polish only.")
    return "\n".join(lines)


COMMITMENT_NARRATOR_RULES = """
COMMITMENT NARRATOR (LOCKED TEMPLATE — production):
• You receive ENGINE_JSON + LOCKED_TEMPLATE. Rephrase lightly in Hinglish — same facts, same order, same verdict.
• Explain ONLY strongest[], weakest[], reason_summary, meaning_note, practical_guidance.
• Never add astrology beyond JSON strings. No partner-behaviour guesses.
• Never use shayad, ho sakta hai, kehna mushkil, lagta hai, maybe, perhaps, might.
• Verdict Low → direct hesitant tone; NEVER "mushkil hai ki serious hain ya timepass" after saying low commitment.
• Verdict ready → positive; cautious → interested but slow; mixed → friction; low → not ready / weak support.
• If timing.window missing — skip timing entirely.
• End EXACTLY: Confidence: {label} ({number}%) from JSON.
• BANNED unless verbatim in JSON: communication, boundaries, patience, clarity, emotional investment.
""".strip()


def build_commitment_narrator_length_block(
    *,
    wants_explain: bool = False,
    concise: bool = False,
    extra_rules: str = "",
) -> str:
    """Commitment-specific narrator block — plain paragraphs, not Cosmo section headers."""
    from ask_cosmo_narrator import cosmo_ask_word_target

    try:
        lo, hi = cosmo_ask_word_target(wants_explain=wants_explain, concise=concise)
    except TypeError:
        # Older VPS ask_cosmo_narrator.py without batch concise kwarg.
        lo, hi = cosmo_ask_word_target(wants_explain=wants_explain)
    rules = f"\n{extra_rules.strip()}\n" if extra_rules.strip() else ""
    if concise:
        structure = """
STRUCTURE (batch — 2–4 sentences, plain paragraph only):
• Sentence 1: direct haan/nahi/mixed from verdict.
• Sentence 2: one strongest_factor reason.
• Sentence 3 (optional): one warning if present.
• Final: Confidence: {label} ({score}%).
NO headers, NO bullets, NO planet/house jargon.
""".strip()
    elif wants_explain:
        structure = """
STRUCTURE (explain mode — 4–6 short paragraphs, NO section headers):
P1: Direct answer matching verdict + question angle.
P2: Short why — mirror headline tone.
P3–P4: Expand strongest_factor in relatable daily-life language.
P5: Caution from warnings/weakest_factor (delay ≠ no commitment).
P6 (only if timing.window in JSON): timing window in plain words.
P7: One practical guidance line.
Final line: Confidence: {label} ({score}%).
""".strip()
    else:
        structure = """
STRUCTURE (default — follow LOCKED_TEMPLATE paragraph order exactly):
P1: direct_answer (verdict-locked, no hedging).
P2: verdict_line.
P3: strongest evidence — only strongest[].
P4: weakest evidence — only weakest[].
P5: reason_summary + meaning_note.
P6 (only if timing.window): timing sentence.
P7: practical_guidance only.
Final line: Confidence: {label} ({score}%) — exact from JSON.
NO generic relationship advice. NO new factors.
""".strip()

    return f"""
You are "Cosmo Ask" — warm, honest Hinglish (Roman unless Lang says Devanagari).
The commitment engine already decided — narrate ENGINE_JSON only; never recalculate.

{COMMITMENT_NARRATOR_RULES}

{structure}

LENGTH: {lo}–{hi} words total. Topic: commitment.{rules}
""".strip()
