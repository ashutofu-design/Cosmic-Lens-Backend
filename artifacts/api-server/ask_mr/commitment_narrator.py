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


def engine_result_to_commitment_json(result: EngineResult) -> dict[str, Any]:
    """Compact narrator JSON — mirrors the commitment engine contract."""
    checks = result.checks or {}
    explanation = checks.get("explanation") or {}
    if not isinstance(explanation, dict):
        explanation = {}

    level = str(
        checks.get("commitment_level") or checks.get("level") or ""
    ).strip().lower()
    verdict = _VERDICT_LABELS.get(level, level.title() if level else "Mixed")

    scorecard = checks.get("scorecard") or {}
    score = int(
        checks.get("primary_score")
        or (scorecard.get("primary") if isinstance(scorecard, dict) else 0)
        or 0
    )
    conf_label = (result.confidence or "medium").strip().title()

    strongest: list[str] = []
    sf = str(explanation.get("strongest_factor") or "").strip()
    if sf:
        strongest.append(_humanize_factor(sf))
    for item in explanation.get("why") or []:
        h = _humanize_factor(str(item))
        if h and h not in strongest:
            strongest.append(h)
    if not strongest:
        for item in (result.evidence_positive or [])[:3]:
            h = _humanize_factor(str(item))
            if h and h not in strongest:
                strongest.append(h)

    weakest: list[str] = []
    wf = str(explanation.get("weakest_factor") or "").strip()
    if wf:
        weakest.append(_humanize_factor(wf))
    for item in explanation.get("why_not") or []:
        h = _humanize_factor(str(item))
        if h and h not in weakest:
            weakest.append(h)
    if not weakest:
        for item in (result.evidence_negative or [])[:2]:
            h = _humanize_factor(str(item))
            if h and h not in weakest:
                weakest.append(h)

    warnings: list[str] = []
    if checks.get("contradiction"):
        warnings.append("Mixed signals — patience needed")
    for item in explanation.get("why_not") or []:
        w = _humanize_warning(str(item))
        if w and w not in warnings:
            warnings.append(w)
    if not warnings and weakest:
        warnings.append(_humanize_warning(weakest[0]))

    timing_window = _extract_timing_window(result, checks)
    timing_block: dict[str, str] | None = None
    if timing_window:
        timing_block = {"window": timing_window}

    payload: dict[str, Any] = {
        "verdict": verdict,
        "confidence": score,
        "confidence_label": conf_label,
        "strongest_factor": strongest[:3],
        "weakest_factor": weakest[:2],
        "warnings": warnings[:3],
    }
    if timing_block:
        payload["timing"] = timing_block
    payload["_meta"] = {
        "commitment_angle": checks.get("commitment_angle") or "general_commitment",
        "headline": (result.verdict or "").strip(),
        "mode": checks.get("mode") or "static",
    }
    return payload


def commitment_narrator_payload(
    result: EngineResult,
    *,
    wants_explain: bool = False,
) -> str:
    """Facts block for LLM — ENGINE_JSON only (no chart / kundli)."""
    data = engine_result_to_commitment_json(result)
    meta = data.pop("_meta", {})
    json_block = json.dumps(data, indent=2, ensure_ascii=False)

    lines = [
        "ARCHETYPE: commitment",
        "SOURCE_LOCK: ENGINE_JSON_ONLY — you do NOT see the birth chart or kundli.",
        "Narrate ONLY from ENGINE_JSON below. Never invent planets, houses, dasha, or dates.",
        "",
        "ENGINE_JSON:",
        json_block,
        "",
        f"QUESTION_ANGLE: {meta.get('commitment_angle', 'general_commitment')}",
        f"VERDICT_HEADLINE: {meta.get('headline', '')}",
    ]
    if wants_explain:
        lines.append(
            "OUTPUT: 4–6 short paragraphs (120–160 words). Expand each JSON field in plain life language."
        )
    else:
        lines.append(
            "OUTPUT: 3–5 short paragraphs (85–110 words). Flowing text — NO section headers, NO bullet lists."
        )
    lines.extend([
        "FLOW (strict order):",
        "1) Direct answer — haan / nahi / mixed matching verdict + question angle.",
        "2) Short explanation — why this verdict (one line).",
        "3) Strongest reasons — 1–2 items from strongest_factor in daily-life words.",
        "4) Caution — warnings / weakest_factor; clarify delay ≠ rejection.",
        "5) Timing — only if timing.window exists in JSON.",
        "6) One practical guidance line (clarity talk, patience, boundaries).",
        f"7) Final line: Confidence: {data.get('confidence_label', 'Medium')} ({data.get('confidence', 0)}%).",
        "BANNED: shayad, ho sakta hai, lagta hai, planet/house/sign/lord jargon, new predictions.",
    ])
    return "\n".join(lines)


COMMITMENT_NARRATOR_RULES = """
COMMITMENT NARRATOR (JSON-only):
• You receive ENGINE_JSON — never the chart. Explain ONLY what is in that JSON.
• Never add astrology beyond strongest_factor / weakest_factor / warnings / timing.
• Never use shayad, ho sakta hai, lagta hai, maybe, perhaps, might.
• Verdict ceiling: ready → positive; cautious → interested but needs clarity;
  mixed → haan lekin friction; low → hesitant / not ready tone.
• Translate technical factor names into plain relationship language (no planet/house words).
• If timing.window missing — skip timing paragraph entirely.
• End with: Confidence: {label} ({number}%).
""".strip()


def build_commitment_narrator_length_block(
    *,
    wants_explain: bool = False,
    concise: bool = False,
    extra_rules: str = "",
) -> str:
    """Commitment-specific narrator block — plain paragraphs, not Cosmo section headers."""
    from ask_cosmo_narrator import cosmo_ask_word_target

    lo, hi = cosmo_ask_word_target(wants_explain=wants_explain, concise=concise)
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
STRUCTURE (default — 3–5 short paragraphs, flowing text, NO section headers):
P1: Direct answer — haan/nahi/mixed per verdict; answer the exact commitment angle asked.
P2: Strongest reasons — name 1–2 factors from strongest_factor in plain words.
P3: Caution — weave warnings/weakest_factor; delay means slower process, not rejection.
P4 (only if timing.window in JSON): supportive period in plain words.
P5: One practical line (clear talk, patience, or boundaries).
Final line: Confidence: {label} ({score}%).
""".strip()

    return f"""
You are "Cosmo Ask" — warm, honest Hinglish (Roman unless Lang says Devanagari).
The commitment engine already decided — narrate ENGINE_JSON only; never recalculate.

{COMMITMENT_NARRATOR_RULES}

{structure}

LENGTH: {lo}–{hi} words total. Topic: commitment.{rules}
""".strip()
