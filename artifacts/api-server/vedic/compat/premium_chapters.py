"""
Premium 7-chapter polish for Kundli Milan Pro PDF (gpt-4o family).

LLM path (``polish_premium_chapters``): chart-backed JSON; user message carries
``<PARTNER_KOOT_GRID>`` + ``<STRUCTURED_CHART_DATA>`` + remedies.

**GPT-first (p79):** Successful OpenAI JSON is **sanitized in place**
(NUL strip + ReportLab codepoint ceilings). A **lightweight chapter depth gate**
(default on) may issue **batched, compact-prompt OpenAI regen** calls for shallow ``chapter_body``
strings before L1/L2 cache write; shallow cached entries are skipped like a miss.
The same depth lane can **regenerate** shallow ``special`` / ``damage`` / ``practical``
blocks (non-fatal if exhausted — the PDF still renders).
There is **no** deterministic soul substitution in the polish pipeline: total polish
failure still yields an **empty** ``pro_premium`` shell and the PDF renderer uses
its own placeholders. The ``_safe_fallback`` builder remains for unit tests / tooling only.

Model: gpt-4o (env ``COMPAT_PREMIUM_MODEL``, fallback gpt-4o-mini).
Toggle: env ``COMPAT_PREMIUM_POLISH=1`` (default off).

Reuses L1 + L2 cache infra from llm_polish.py (different fingerprint prefix).
Branding rule: never name AI/LLM. Defensive — never raises.
"""
from __future__ import annotations

import copy
import json
import hashlib
import logging
import os
import re
import time
from collections import Counter
from typing import Any

from .llm_polish import (
    _cache_get as _l1_get,
    _cache_put as _l1_put,
    _db_cache_get as _l2_get,
    _db_cache_put as _l2_put,
    ALLOWED_REMEDIES,
)
from .openai_pdf_telemetry import (
    PdfGenOpenAITelemetry,
    merge_pdf_generation_into_meta,
    publish_and_log_pdf_generation,
    stub_meta,
)

log = logging.getLogger(__name__)

_PREMIUM_VERSION = "p79"
_DEFAULT_MODEL = "gpt-4o"

CHAPTER_KEYS = ["ch1", "ch2", "ch3", "ch4", "ch5", "ch6", "ch7"]
# Legacy merged body; kept in sync with ``chapter_body`` for older readers.
CHAPTER_FULL_READ = "full_read"

# Structured premium chapter sections — legacy keys (soul/tests only); live PDF uses ``chapter_body``.
CHAPTER_SECTION_KEYS: tuple[str, ...] = (
    "core_dynamic",
    "lived_manifestation",
    "hidden_strength",
    "hidden_risk",
    "practical_marriage_pattern",
    "future_pattern",
    "chart_bridge",
)

# Single flowing narrative — primary field for Pro PDF chapter pages.
CHAPTER_BODY_KEY = "chapter_body"

# Max Unicode codepoints per chapter `grounding` (chart-to-prose bridge).
_PREMIUM_GROUNDING_MAX_CHARS = 900

# Legacy `full_read` cap when sections absent (migration / cache).
_PREMIUM_FULL_READ_MAX_CP = 12000

def _premium_env_int(name: str, default: int) -> int:
    raw = (os.environ.get(name) or "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _premium_env_float(name: str, default: float) -> float:
    raw = (os.environ.get(name) or "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


# Per-section ceiling / floor (structured chapter strings).
_PREMIUM_SECTION_MAX_CP = _premium_env_int("COMPAT_PREMIUM_SECTION_MAX_CP", 3600)
_PREMIUM_SECTION_MIN_CP = _premium_env_int("COMPAT_PREMIUM_SECTION_MIN_CP", 72)
_PREMIUM_CHAPTER_SUM_MIN_CP = _premium_env_int("COMPAT_PREMIUM_CHAPTER_SUM_MIN_CP", 560)

# Waive legacy p65 floors for tiny sections via ``[[SHORT]]``.
_PREMIUM_SECTION_SHORT_MAX_CP = _premium_env_int("COMPAT_PREMIUM_SECTION_SHORT_MAX_CP", 280)

# Meaningful paragraph blocks: each segment after ``\\n\\n`` must be at least this many
# codepoints to count toward the "≥2 meaningful breaks" rule.
_PREMIUM_STRUCT_MIN_BLOCK_CP = _premium_env_int("COMPAT_PREMIUM_STRUCT_MIN_BLOCK_CP", 14)

# Reject chapter when this many non-short sections lack ≥2 meaningful ``\\n\\n`` gaps (PDF blob).
_PREMIUM_STRUCT_DENSE_SECTION_THRESHOLD = _premium_env_int(
    "COMPAT_PREMIUM_STRUCT_DENSE_SECTION_THRESHOLD", 5
)

# Max Unicode codepoints for one chapter narrative (primary PDF body string).
_PREMIUM_CHAPTER_BODY_MAX_CP = _premium_env_int("COMPAT_PREMIUM_CHAPTER_BODY_MAX_CP", 24000)


def _premium_depth_regen_enabled() -> bool:
    """When True (default), shallow ``chapter_body`` after polish triggers targeted LLM regen.

    Disable with ``COMPAT_PREMIUM_DEPTH_REGEN=0`` (cache + primary-only behaviour).
    """
    return _premium_env_flag("COMPAT_PREMIUM_DEPTH_REGEN", "1")


def _premium_depth_regen_fatal() -> bool:
    """When True, depth regen that still fails lightweight floors aborts polish (empty shell).

    Default **False** — ship the primary + partial regen so cost stays bounded and the PDF still renders.
    Enable with ``COMPAT_PREMIUM_DEPTH_REGEN_FATAL=1`` for strict QA environments.
    """
    return _premium_env_flag("COMPAT_PREMIUM_DEPTH_REGEN_FATAL", "0")


# Lightweight depth floors (paragraph / length / chart + lived texture signals only).
_PREMIUM_DEPTH_MIN_MEANINGFUL_PARAS = _premium_env_int(
    "COMPAT_PREMIUM_DEPTH_MIN_MEANINGFUL_PARAS", 4
)
_PREMIUM_DEPTH_MEANINGFUL_PARA_MIN_CP = _premium_env_int(
    "COMPAT_PREMIUM_DEPTH_MEANINGFUL_PARA_MIN_CP", 42
)
_PREMIUM_DEPTH_MIN_BODY_WORDS_LATIN = _premium_env_int(
    "COMPAT_PREMIUM_DEPTH_MIN_BODY_WORDS_LATIN", 220
)
_PREMIUM_DEPTH_MIN_BODY_WORDS_INDIC = _premium_env_int(
    "COMPAT_PREMIUM_DEPTH_MIN_BODY_WORDS_INDIC", 160
)
_PREMIUM_DEPTH_MIN_BODY_CHARS_LATIN = _premium_env_int(
    "COMPAT_PREMIUM_DEPTH_MIN_BODY_CHARS_LATIN", 1750
)
_PREMIUM_DEPTH_MIN_BODY_CHARS_INDIC = _premium_env_int(
    "COMPAT_PREMIUM_DEPTH_MIN_BODY_CHARS_INDIC", 1250
)
_PREMIUM_DEPTH_MIN_CHART_SIGNALS = _premium_env_int(
    "COMPAT_PREMIUM_DEPTH_MIN_CHART_SIGNALS", 2
)
# Legacy per-chapter attempt cap (unused when batch rounds are enabled; kept for env compat).
_PREMIUM_DEPTH_REGEN_MAX_ATTEMPTS = max(
    1, min(5, _premium_env_int("COMPAT_PREMIUM_DEPTH_REGEN_MAX_ATTEMPTS", 3))
)
_PREMIUM_DEPTH_REGEN_MAX_ROUNDS = max(
    1, min(5, _premium_env_int("COMPAT_PREMIUM_DEPTH_REGEN_MAX_ROUNDS", 2))
)
_PREMIUM_SDP_DEPTH_REGEN_MAX_ROUNDS = max(
    1, min(5, _premium_env_int("COMPAT_PREMIUM_SDP_DEPTH_REGEN_MAX_ROUNDS", 2))
)
_PREMIUM_DEPTH_REGEN_MAX_TOKENS = max(
    800,
    min(12000, _premium_env_int("COMPAT_PREMIUM_DEPTH_REGEN_MAX_TOKENS", 3400)),
)
_PREMIUM_DEPTH_REGEN_TOKENS_PER_EXTRA_CHAPTER = max(
    0, min(2500, _premium_env_int("COMPAT_PREMIUM_DEPTH_REGEN_TOKENS_PER_EXTRA_CHAPTER", 750))
)
_PREMIUM_DEPTH_REGEN_MAX_TOKENS_CAP = max(
    2000, min(16384, _premium_env_int("COMPAT_PREMIUM_DEPTH_REGEN_MAX_TOKENS_CAP", 9600))
)
_PREMIUM_DEPTH_REGEN_EXCERPT_CHARS = max(
    200, min(8000, _premium_env_int("COMPAT_PREMIUM_DEPTH_REGEN_EXCERPT_CHARS", 1400))
)

# Lightweight depth for Pro-PDF ``special`` / ``damage`` / ``practical`` (each array element
# is its own consultation block, not a one-line bullet).
_PREMIUM_SDP_DEPTH_MIN_MEANINGFUL_PARAS = _premium_env_int(
    "COMPAT_PREMIUM_SDP_DEPTH_MIN_MEANINGFUL_PARAS", 2
)
_PREMIUM_SDP_DEPTH_MIN_WORDS_LATIN = _premium_env_int(
    "COMPAT_PREMIUM_SDP_DEPTH_MIN_WORDS_LATIN", 95
)
_PREMIUM_SDP_DEPTH_MIN_WORDS_INDIC = _premium_env_int(
    "COMPAT_PREMIUM_SDP_DEPTH_MIN_WORDS_INDIC", 72
)
_PREMIUM_SDP_DEPTH_MIN_CHARS_LATIN = _premium_env_int(
    "COMPAT_PREMIUM_SDP_DEPTH_MIN_CHARS_LATIN", 680
)
_PREMIUM_SDP_DEPTH_MIN_CHARS_INDIC = _premium_env_int(
    "COMPAT_PREMIUM_SDP_DEPTH_MIN_CHARS_INDIC", 500
)
_PREMIUM_SDP_DEPTH_MIN_CHART_SIGNALS = _premium_env_int(
    "COMPAT_PREMIUM_SDP_DEPTH_MIN_CHART_SIGNALS", 2
)
_PREMIUM_SDP_DEPTH_REGEN_MAX_TOKENS = max(
    1200,
    min(12000, _premium_env_int("COMPAT_PREMIUM_SDP_DEPTH_REGEN_MAX_TOKENS", 5200)),
)
_PREMIUM_SDP_PRACTICAL_RUBRIC_MIN_HITS = _premium_env_int(
    "COMPAT_PREMIUM_SDP_PRACTICAL_RUBRIC_MIN_HITS", 3
)

_PRACTICAL_MARRIED_RUBRIC_RES: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"\b(daily|weekly|routine|weekday|weekend|morning|evening|schedule|habit|"
        r"दिनचर्या|रोज|रोज़)\b",
        re.I,
    ),
    re.compile(
        r"\b(in-?law|mother-?in-?law|father-?in-?law|saas|saasu|saasu-?maa|joint family|"
        r"extended family|boundary|relatives|parent|saas|sasural|"
        r"सास|ससुराल|परिवार)\b",
        re.I,
    ),
    re.compile(
        r"\b(money|salary|income|budget|bill|rent|mortgage|savings|expense|accounts|"
        r"spender|saver|financial|bank|loan|"
        r"पैसा|खर्च|बचत|कमाई)\b",
        re.I,
    ),
    re.compile(
        r"\b(emotional labour|emotional labor|mental load|invisible work|who plans|"
        r"who remembers|caretaking|nurturing|reassurance|"
        r"भावनात्मक|थकान|जिम्मेदारी)\b",
        re.I,
    ),
    re.compile(
        r"\b(communicat|texting|tone|silent treatment|withdraw|repair|apolog|"
        r"cool-?off|debrief|listen|interrupt|"
        r"बात|चुप|सुनना)\b",
        re.I,
    ),
    re.compile(
        r"\b(conflict|fight|argument|gridlock|resent|scorekeeping|roles?|fairness|"
        r"chores?|housework|kitchen|division|balance|"
        r"झगड़ा|लड़ाई|काम|बंटवारा)\b",
        re.I,
    ),
)


def _sdp_practical_life_rubric_ok(body: str) -> bool:
    """True when ``practical`` blocks mention several distinct married-life axes."""
    t = body or ""
    hits = sum(1 for rx in _PRACTICAL_MARRIED_RUBRIC_RES if rx.search(t))
    return hits >= _PREMIUM_SDP_PRACTICAL_RUBRIC_MIN_HITS


def _sdp_meaningful_paragraph_count(body: str) -> int:
    mn = _PREMIUM_DEPTH_MEANINGFUL_PARA_MIN_CP
    parts = [p.strip() for p in re.split(r"\n\s*\n", (body or "").strip()) if p.strip()]
    return sum(1 for p in parts if len(p) >= mn)


def _sdp_section_depth_failure_reason(
    body: str,
    milan_facts: dict,
    lang: str,
    *,
    require_practical_rubric: bool,
    slot: str,
) -> str | None:
    """Shallow-content gate for one ``special`` / ``damage`` / ``practical`` string."""
    t = (body or "").strip()
    if not t:
        return f"{slot}:empty"
    blob = _validate_section_list_only_blob(t, "sdp", slot)
    if blob:
        return f"{slot}:list_blob"
    indic = _premium_body_has_indic_script(t)
    wc = _full_read_word_count(t)
    cpc = len(t)
    min_w = _PREMIUM_SDP_DEPTH_MIN_WORDS_INDIC if indic else _PREMIUM_SDP_DEPTH_MIN_WORDS_LATIN
    min_c = _PREMIUM_SDP_DEPTH_MIN_CHARS_INDIC if indic else _PREMIUM_SDP_DEPTH_MIN_CHARS_LATIN
    if wc < min_w:
        return f"{slot}:words:{wc}<{min_w}"
    if cpc < min_c:
        return f"{slot}:chars:{cpc}<{min_c}"
    mpc = _sdp_meaningful_paragraph_count(t)
    if mpc < _PREMIUM_SDP_DEPTH_MIN_MEANINGFUL_PARAS:
        return f"{slot}:paras:{mpc}<{_PREMIUM_SDP_DEPTH_MIN_MEANINGFUL_PARAS}"
    if _depth_chart_signal_tally(t) < _PREMIUM_SDP_DEPTH_MIN_CHART_SIGNALS:
        return f"{slot}:chart<{_PREMIUM_SDP_DEPTH_MIN_CHART_SIGNALS}"
    if not _depth_comparative_ok(t, milan_facts):
        return f"{slot}:compare"
    if not _depth_manifestation_ok(t):
        return f"{slot}:manifest"
    if require_practical_rubric and not _sdp_practical_life_rubric_ok(t):
        return f"{slot}:practical_rubric"
    _ = lang
    return None


def _premium_sdp_payload_depth_complete(
    parsed: dict,
    milan_facts: dict,
    lang: str,
) -> bool:
    """True when special (3), damage (2+), and practical (3) blocks pass the SDP gate."""
    _ = lang
    sp = [str(x).strip() for x in (parsed.get("special") or []) if str(x).strip()]
    if len(sp) < 3:
        return False
    for i, b in enumerate(sp[:3]):
        if _sdp_section_depth_failure_reason(
            b, milan_facts, lang, require_practical_rubric=False, slot=f"special_{i}"
        ):
            return False
    dm = [str(x).strip() for x in (parsed.get("damage") or []) if str(x).strip()]
    if len(dm) < 2:
        return False
    for i, b in enumerate(dm[:2]):
        if _sdp_section_depth_failure_reason(
            b, milan_facts, lang, require_practical_rubric=False, slot=f"damage_{i}"
        ):
            return False
    pr = [str(x).strip() for x in (parsed.get("practical") or []) if str(x).strip()]
    if len(pr) < 3:
        return False
    for i, b in enumerate(pr[:3]):
        if _sdp_section_depth_failure_reason(
            b, milan_facts, lang, require_practical_rubric=True, slot=f"practical_{i}"
        ):
            return False
    return True


def _premium_polish_cache_depth_ok(
    hit: dict,
    milan_facts: dict,
    lang: str,
) -> bool:
    """L1/L2 accept only when chapter + SDP narrative blocks meet lightweight depth."""
    return _premium_polish_payload_depth_complete(hit, milan_facts, lang) and _premium_sdp_payload_depth_complete(
        hit, milan_facts, lang
    )


_SDP_DEPTH_REGEN_SYSTEM_SUFFIX = """

═══ SDP CONSULTATION REGEN (server-requested) ═══
Return STRICT JSON: one root object whose ONLY top-level keys are `special`, `damage`,
and `practical` (include all three keys).

Shape:
- `special`: exactly **three** strings. Each string is a **standalone consultation arc** for the
  Pro-PDF page "What Makes This Bond Special": multiple **paragraphs** separated by \\n\\n inside
  the string; chart-led reasoning (houses, lords, D1/D9, synastry, KP where data supports);
  compare **both** kundlis; bridge to emotional and behavioural manifestations. Do **not** emit
  one-line bullets or slogans as the primary format; optional `•` / `-` highlight lines may appear
  inside a paragraph, never as the whole string.

- `damage`: exactly **two** strings for "What Can Quietly Damage This Bond". Same depth: multi-paragraph,
  chart-grounded, both partners, how distance accrues in ordinary weeks (not generic warnings).

- `practical`: exactly **three** strings for "Practical Married Life". Each block must weave **daily**
  domestic rhythm, family/in-law handling, money responsibilities, emotional labour, routines,
  communication habits, conflict/repair patterns, and role balancing — explicitly tied to chart
  combinations. Multi-paragraph per string (\\n\\n). Bullets only as optional in-prose highlights.

Ground every claim in <STRUCTURED_CHART_DATA> and <PARTNER_KOOT_GRID> from the user message.

Tone: lived scenes and chart causality — not therapy-column endings, not “should try harder” filler without a
planet/house story in the same paragraph.
"""


def _build_sdp_depth_regen_augment(parsed: dict, milan_facts: dict, lang: str) -> str:
    lines: list[str] = ["<SDP_DEPTH_REGEN_TARGETS>", "Reasons (machine):"]
    sp = [str(x).strip() for x in (parsed.get("special") or []) if str(x).strip()]
    dm = [str(x).strip() for x in (parsed.get("damage") or []) if str(x).strip()]
    pr = [str(x).strip() for x in (parsed.get("practical") or []) if str(x).strip()]
    for label, arr in (("special", sp), ("damage", dm), ("practical", pr)):
        for i, b in enumerate(arr[:6]):
            slot = f"{label}_{i}"
            need_rub = label == "practical"
            r = _sdp_section_depth_failure_reason(
                b, milan_facts, lang, require_practical_rubric=need_rub, slot=slot
            )
            if r:
                lines.append(f"  {r}")
            excerpt = b[:700].replace("\n", " ")
            lines.append(f"  {slot}_excerpt: {excerpt!r}")
    lines.append("</SDP_DEPTH_REGEN_TARGETS>")
    return "\n".join(lines)


def _openai_regen_sdp_depth(
    client: Any,
    tel: PdfGenOpenAITelemetry | None,
    model: str,
    lang: str,
    regen_user_prompt: str,
    parsed: dict,
    milan_facts: dict,
    oa_timeout: float,
) -> dict[str, list[str]] | None:
    """One completion: JSON with `special`, `damage`, `practical` only."""
    augment = _build_sdp_depth_regen_augment(parsed, milan_facts, lang)
    messages = [
        {
            "role": "system",
            "content": build_premium_regen_sdp_system_prompt(lang).strip(),
        },
        {"role": "user", "content": augment + "\n\n" + regen_user_prompt},
    ]
    kw: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "response_format": {"type": "json_object"},
        "max_tokens": _PREMIUM_SDP_DEPTH_REGEN_MAX_TOKENS,
        "timeout": oa_timeout,
    }
    if not model.lower().startswith("gpt-5"):
        kw["temperature"] = 0.52
    try:
        resp = client.chat.completions.create(**kw)
    except Exception as exc:
        log.warning("[premium_chapters] sdp_depth_regen openai fail: %s", exc)
        return None
    if tel is not None:
        try:
            tel.record(resp, "sdp_depth_regen")
        except Exception:
            pass
    raw = (resp.choices[0].message.content or "").strip()
    parsed_partial, _err = _parse_premium_llm_json(raw)
    if not isinstance(parsed_partial, dict):
        return None
    out: dict[str, list[str]] = {}
    for key in ("special", "damage", "practical"):
        v = parsed_partial.get(key)
        if not isinstance(v, list):
            continue
        cleaned = [str(x).strip() for x in v if str(x).strip()]
        if cleaned:
            out[key] = cleaned
    return out if out else None


def _apply_sdp_depth_regen_to_parsed(
    *,
    client: Any,
    tel: PdfGenOpenAITelemetry | None,
    model: str,
    lang: str,
    milan_facts: dict,
    regen_user_prompt: str,
    parsed: dict,
    oa_timeout: float,
) -> tuple[bool, dict[str, Any]]:
    """Try to deepen ``special``/``damage``/``practical``. Non-fatal: returns False if still shallow."""
    meta: dict[str, Any] = {
        "sdp_depth_regen_calls": 0,
        "sdp_depth_regen_last_reason": "",
    }
    max_r = int(_PREMIUM_SDP_DEPTH_REGEN_MAX_ROUNDS)
    for attempt in range(max_r):
        if _premium_sdp_payload_depth_complete(parsed, milan_facts, lang):
            meta["sdp_depth_ok"] = True
            return True, meta
        got = _openai_regen_sdp_depth(
            client,
            tel,
            model,
            lang,
            regen_user_prompt,
            parsed,
            milan_facts,
            oa_timeout,
        )
        meta["sdp_depth_regen_calls"] = int(meta["sdp_depth_regen_calls"]) + 1
        meta["sdp_depth_regen_last_reason"] = f"attempt_{attempt + 1}"
        if not got:
            continue
        if "special" in got:
            parsed["special"] = got["special"]
        if "damage" in got:
            parsed["damage"] = got["damage"]
        if "practical" in got:
            parsed["practical"] = got["practical"]
        _finalize_chapter_narrative_for_pdf(parsed)
        _sanitize_premium_parsed_dict_in_place(parsed, lang)
    ok = _premium_sdp_payload_depth_complete(parsed, milan_facts, lang)
    meta["sdp_depth_ok"] = bool(ok)
    if not ok:
        log.warning(
            "[premium_chapters] sdp depth regen exhausted calls=%s meta=%s",
            meta.get("sdp_depth_regen_calls"),
            meta,
        )
    return ok, meta


def _premium_legacy_structure_depth_validator() -> bool:
    """When True: enforce legacy strict p65 (paragraph/layer/bullet) + p66 (word/sentence) floors.

    Default **False** — validator acts as guardrails only (empties, caps, safety, catastrophes,
    extreme render walls, bullet-only blobs). Opt-in for old co-writer strictness.
    """
    return os.environ.get(
        "COMPAT_PREMIUM_LEGACY_STRUCTURE_DEPTH_VALIDATOR", "0"
    ).strip().lower() in ("1", "true", "yes", "on")


def _premium_struct_validate_enabled() -> bool:
    return _premium_legacy_structure_depth_validator()


def _premium_depth_validate_enabled() -> bool:
    return _premium_legacy_structure_depth_validator()


def _premium_remedy_tail_validate_enabled() -> bool:
    """When True: ch4/ch7 ``chart_bridge`` (and legacy ``full_read``) must end with a verbatim
    substring from ``ALLOWED_REMEDIES``. Default **False** — natural closings and flexible
    remedy wording are allowed; set ``COMPAT_PREMIUM_REMEDY_TAIL_VALIDATE=1`` to restore
    exact tail matching.
    """
    return os.environ.get(
        "COMPAT_PREMIUM_REMEDY_TAIL_VALIDATE", "0"
    ).strip().lower() in ("1", "true", "yes", "on")


_PREMIUM_SECTION_DEPTH_MIN_WORDS = _premium_env_int(
    "COMPAT_PREMIUM_SECTION_DEPTH_MIN_WORDS", 64
)
_PREMIUM_SECTION_DEPTH_MIN_SENTENCES = _premium_env_int(
    "COMPAT_PREMIUM_SECTION_DEPTH_MIN_SENTENCES", 4
)
# When a section has multiple ``\\n\\n`` blocks, each block must carry enough prose
# (rejects heading + 1–2 line micro-segments).
_PREMIUM_DEPTH_MIN_PARAGRAPH_WORDS = _premium_env_int(
    "COMPAT_PREMIUM_DEPTH_MIN_PARAGRAPH_WORDS", 20
)
# If bullet lines dominate without narrative glue, reject list-like “snippets”.
_PREMIUM_DEPTH_MIN_PROSE_WORDS_BULLET_HEAVY = _premium_env_int(
    "COMPAT_PREMIUM_DEPTH_MIN_PROSE_WORDS_BULLET_HEAVY", 38
)
_PREMIUM_DEPTH_BULLET_LINE_MIN = _premium_env_int(
    "COMPAT_PREMIUM_DEPTH_BULLET_LINE_MIN", 4
)


_PREMIUM_WALL_OF_TEXT_MIN_CP = _premium_env_int(
    "COMPAT_PREMIUM_WALL_OF_TEXT_MIN_CP", 3200
)
_PREMIUM_LIST_BLOB_BULLET_LINES_MIN = _premium_env_int(
    "COMPAT_PREMIUM_LIST_BLOB_BULLET_LINES_MIN", 8
)
_PREMIUM_LIST_BLOB_MAX_PROSE_WORDS = _premium_env_int(
    "COMPAT_PREMIUM_LIST_BLOB_MAX_PROSE_WORDS", 18
)


_P66_FLOW_CONNECTOR_RE = re.compile(
    r"(?:\b(because|while|when|after|before|although|though|so|yet|but|and|or|"
    r"therefore|meanwhile|instead|rather|until|unless|once|if|then|"
    r"kyunki|isliye|lekin|magar|jab|tab|phir|aur|ya|yani|matlab|isliye|taaki|agar|"
    r"warna|dheere|pehle|baad|kyun|kaise|kab|jahan|wahan|jabki)\b)",
    re.I,
)


def _p66_word_count(text: str) -> int:
    return len(((text or "").replace("\u00a0", " ")).split())


def _p66_sentence_tally(text: str) -> int:
    """Count sentence-like segments (filters ultra-short fragments)."""
    t = re.sub(r"\s+", " ", (text or "").strip())
    if not t:
        return 0
    parts = re.split(r"(?<=[.!?।])\s+", t)
    return sum(1 for p in parts if len(p.strip()) >= 14)


def _p66_bullet_vs_prose_words(body: str) -> tuple[int, int]:
    """Returns (prose_words, bullet_line_words) for list-skew heuristic."""
    prose_w = 0
    bul_w = 0
    for ln in (body or "").splitlines():
        s = ln.strip()
        if not s:
            continue
        w = len(s.split())
        if re.match(r"^[•\-\–\*]", s):
            bul_w += w
        else:
            prose_w += w
    return prose_w, bul_w


def _p66_bullet_only_lines(body: str) -> int:
    return sum(
        1
        for ln in (body or "").splitlines()
        if ln.strip() and re.match(r"^\s*[•\-\–\*]", ln.strip())
    )


def _validate_section_explanation_depth_legacy(
    body: str,
    chapter_key: str,
    section_key: str,
) -> str | None:
    """Legacy p66: word/sentence/micro-block/snippet/flow floors (opt-in via env)."""
    t = (body or "").strip()
    if not t:
        return f"p66_depth_empty:{chapter_key}:{section_key}"

    wc = _p66_word_count(t)
    if wc < _PREMIUM_SECTION_DEPTH_MIN_WORDS:
        return f"p66_depth_words:{chapter_key}:{section_key}:{wc}"

    st = _p66_sentence_tally(t)
    if st < _PREMIUM_SECTION_DEPTH_MIN_SENTENCES:
        return f"p66_depth_sentences:{chapter_key}:{section_key}:{st}"

    parts = [p.strip() for p in re.split(r"\n\s*\n", t) if p.strip()]
    if len(parts) >= 2:
        min_pw = min(_p66_word_count(p) for p in parts)
        if min_pw < _PREMIUM_DEPTH_MIN_PARAGRAPH_WORDS:
            return f"p66_depth_micro_block:{chapter_key}:{section_key}:{min_pw}"

    bl = _p66_bullet_only_lines(t)
    if bl >= _PREMIUM_DEPTH_BULLET_LINE_MIN:
        prose_w, bul_w = _p66_bullet_vs_prose_words(t)
        if prose_w < _PREMIUM_DEPTH_MIN_PROSE_WORDS_BULLET_HEAVY and bul_w > prose_w:
            return f"p66_depth_snippet_list:{chapter_key}:{section_key}:{prose_w}"

    if wc >= 90 and not _P66_FLOW_CONNECTOR_RE.search(t):
        return f"p66_depth_flow:{chapter_key}:{section_key}"

    return None


def _validate_section_list_only_blob(
    body: str,
    chapter_key: str,
    section_key: str,
) -> str | None:
    """Catastrophic bullet-list skeleton with almost no narrative glue (always-on guard)."""
    t = (body or "").strip()
    if not t:
        return None
    bl = _p66_bullet_only_lines(t)
    prose_w, bul_w = _p66_bullet_vs_prose_words(t)
    bmin = _PREMIUM_LIST_BLOB_BULLET_LINES_MIN
    pmax = _PREMIUM_LIST_BLOB_MAX_PROSE_WORDS
    if bl >= bmin and prose_w <= pmax and bul_w >= prose_w * 3:
        return f"p66_list_blob:{chapter_key}:{section_key}:{bl}:{prose_w}"
    return None


def _validate_chapter_explanation_depth(c: dict, key: str) -> str | None:
    """Soft: bullet-only blob. Legacy: full p66 depth when opt-in env is set."""
    if not _chapter_has_structured_sections(c):
        return None

    for sk in CHAPTER_SECTION_KEYS:
        raw = str(c.get(sk, "") or "")
        if _p65_section_structurally_short(raw):
            continue
        body, _mk = _premium_strip_short_marker(raw)
        blob = _validate_section_list_only_blob(body, str(key), sk)
        if blob:
            return blob
        if _premium_depth_validate_enabled():
            err = _validate_section_explanation_depth_legacy(body, str(key), sk)
            if err:
                return err
    return None


_CHART_VISIBILITY_RE = re.compile(
    r"\b(moon|sun|venus|mars|mercury|jupiter|saturn|rahu|ketu|"
    r"chandra|surya|mangal|budh|guru|shukra|shani|"
    r"navamsa|d9|d1|7th|synastry|lagna|nakshatra|house|lord|aspect|conjunct|"
    r"transit|vimshottari|kp|graha|kundli|milan|chart|bhava|guna|koot)\b",
    re.I,
)

# p65: lightweight signals that a section carries lived behavioural + practical + chart texture.
_P65_BEHAVIOURAL_RE = re.compile(
    r"(?:\b(react|reaction|repair|conflict|withdraw|silence|pace|tension|emotion|hurt|angry|"
    r"resent|avoid|trigger|behaviour|behavior|dismiss|shut|argument|mood)\b|"
    r"(?:andar|bahar|chup|ladai|jhagda|bhawna|guussa|naraaz|rishta|vyavhaar|vyavahar))",
    re.I,
)
_P65_PRACTICAL_RE = re.compile(
    r"(?:\b(money|bill|chore|in-?law|family|schedule|work|home|kitchen|rent|parent|child|"
    r"logistics|duty|dinner|calendar|office)\b|"
    r"(?:paisa|ghar|saas|saasu|bacc|kam|bills|office|inlaw))",
    re.I,
)

# ── Lightweight chapter depth (p76) — paragraph / length / chart / compare / manifest only.
_DEPTH_LIFE_DAILY_RE = re.compile(
    r"(?:\b(marriage|married|daily|home|together|family|money|life|pattern|feel|"
    r"weekend|bedroom|trust|intimacy|schedule|work|kitchen|parent|child|routine)\b|"
    r"(?:शादी|घर|रोज़|रोज|दिनचर्या|परिवार|पैसा|भरोसा))",
    re.I,
)
_DEPTH_CAUSAL_OR_MECHANISM_RE = re.compile(
    r"(?:\b(because|therefore|hence|isliye|matlab|jab|tab|phir|kyunki|lekin|so that|"
    r"which means|this is why|wajah|karan|vajah)\b)|"
    r"(?:\b(lord|house|nakshatra|navamsa|d9|d1|aspect|conjunct)\b.{0,200}\b"
    r"(feel|feels|behaviour|behavior|manifest|pattern|life|marriage|shaadi|ghar|daily)\b)",
    re.I | re.S,
)
_DEPTH_COMPARATIVE_SNIPPETS: tuple[str, ...] = (
    " each other",
    " both partners",
    " between ",
    " while one",
    "whereas ",
    " ek ",
    " दूसर",
    "दूसरा",
    " दोनों",
    "दोनों ",
    " dono ",
    "dusra ",
    " dusre ",
    " same moment different",
    " asymmetric",
    "asymmetry",
    " compared to ",
    " in contrast",
)

_PREMIUM_REGEN_CORE_SHRINK = """=== PREMIUM REGEN (compact) — same chart contract as full run ===
You are the same expert relationship astrologer. Ground every claim in the user message blocks only;
invent no nakshatra, koot line, planet, house, score, or date not present there.
Address the couple together (second-person plural); use partner names only to separate habits.
Weave D1/D9/synastry/KP **inside** lived marriage scenes — not academic lists or abstract “insight” labels.
Each paragraph must add **new** behavioural or chart detail; do not echo the same point in different wording across paragraphs.
Avoid therapy-app, SaaS brochure, or HR-coach cadence. Safety: no lifespan/death/children gender guarantees.
"""

_DEPTH_REGEN_SYSTEM_SUFFIX = """

═══ DEPTH REGENERATION MODE (server-requested) ═══
Return STRICT JSON: one root object whose ONLY top-level key is `chapters` (array).
Each element must include `key` (exactly one of the requested chapter keys) and
`chapter_body` (one long string, paragraphs separated by \\n\\n).

**Expand-and-deepen (required):** start from the provided `*_current_excerpt` / existing read for that key.
Preserve factual chart claims and partner-specific observations already stated; **extend** with missing
consultation depth (more paragraphs, clearer both-kundli contrast, lived domestic texture, causal links to
houses/lords/Moon/Venus/D9 vs D1/KP). Do **not** wipe good material for a generic rewrite; do **not** repeat the
same thesis in adjacent paragraphs with synonym swaps.

Ground additions in <STRUCTURED_CHART_DATA> and <PARTNER_KOOT_GRID>. No subsection slot keys (core_dynamic, …).
"""


def _premium_body_has_indic_script(text: str) -> bool:
    for ch in (text or "")[:16000]:
        o = ord(ch)
        if 0x0900 <= o <= 0x097F:
            return True
    return False


def _partner_first_tokens(milan_facts: dict) -> tuple[str, str]:
    p1 = (milan_facts.get("p1") or {}) or {}
    p2 = (milan_facts.get("p2") or {}) or {}
    def _first(nm: str) -> str:
        s = (nm or "").strip()
        if not s:
            return ""
        return s.split()[0].strip('.,\'"“”')
    return _first(str(p1.get("name") or "")), _first(str(p2.get("name") or ""))


def _meaningful_paragraph_count_depth(body: str) -> int:
    parts = [p.strip() for p in re.split(r"\n\s*\n", (body or "").strip()) if p.strip()]
    mn = _PREMIUM_DEPTH_MEANINGFUL_PARA_MIN_CP
    return sum(1 for p in parts if len(p) >= mn)


def _depth_chart_signal_tally(body: str) -> int:
    return len(_CHART_VISIBILITY_RE.findall(body or ""))


def _depth_comparative_ok(body: str, milan_facts: dict) -> bool:
    tl = (body or "").lower()
    a, b = _partner_first_tokens(milan_facts)
    if len(a) >= 2 and len(b) >= 2 and a.lower() in tl and b.lower() in tl:
        return True
    hits = sum(1 for m in _DEPTH_COMPARATIVE_SNIPPETS if m in tl)
    if hits >= 2:
        return True
    if hits >= 1 and _depth_chart_signal_tally(body) >= 4:
        return True
    return False


def _depth_manifestation_ok(body: str) -> bool:
    t = body or ""
    if _DEPTH_CAUSAL_OR_MECHANISM_RE.search(t):
        return True
    if _P65_BEHAVIOURAL_RE.search(t) or _P65_PRACTICAL_RE.search(t):
        return True
    return bool(_DEPTH_LIFE_DAILY_RE.search(t))


def _chapter_body_depth_failure_reason(
    body: str,
    milan_facts: dict,
    lang: str,
) -> str | None:
    """Return a short machine reason if ``chapter_body`` is too shallow; else None.

    Checks paragraph depth, length, chart vocabulary density, two-chart comparison
    signals, and lived-life / causal texture. Does **not** judge tone, style, or
    'AI-sounding' prose.
    """
    t = (body or "").strip()
    if not t:
        return "empty"
    indic = _premium_body_has_indic_script(t)
    wc = _full_read_word_count(t)
    cpc = len(t)
    min_w = _PREMIUM_DEPTH_MIN_BODY_WORDS_INDIC if indic else _PREMIUM_DEPTH_MIN_BODY_WORDS_LATIN
    min_c = _PREMIUM_DEPTH_MIN_BODY_CHARS_INDIC if indic else _PREMIUM_DEPTH_MIN_BODY_CHARS_LATIN
    if wc < min_w:
        return f"words:{wc}<{min_w}"
    if cpc < min_c:
        return f"chars:{cpc}<{min_c}"
    mpc = _meaningful_paragraph_count_depth(t)
    if mpc < _PREMIUM_DEPTH_MIN_MEANINGFUL_PARAS:
        return f"paras:{mpc}<{_PREMIUM_DEPTH_MIN_MEANINGFUL_PARAS}"
    if _depth_chart_signal_tally(t) < _PREMIUM_DEPTH_MIN_CHART_SIGNALS:
        return f"chart<{_PREMIUM_DEPTH_MIN_CHART_SIGNALS}"
    if not _depth_comparative_ok(t, milan_facts):
        return "compare"
    if not _depth_manifestation_ok(t):
        return "manifest"
    _ = lang  # reserved for future per-lane tuning
    return None


def _premium_chapter_bodies_map(parsed: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for c in parsed.get("chapters") or []:
        if not isinstance(c, dict):
            continue
        k = str(c.get("key") or "").strip().lower()
        if not k:
            continue
        out[k] = str(c.get(CHAPTER_BODY_KEY) or c.get(CHAPTER_FULL_READ) or "").strip()
    return out


def _premium_polish_payload_depth_complete(
    payload: dict,
    milan_facts: dict,
    lang: str,
) -> bool:
    """True iff every ``ch1``…``ch7`` chapter_body passes the lightweight depth gate."""
    bmap = _premium_chapter_bodies_map(payload)
    for k in CHAPTER_KEYS:
        if k not in bmap:
            return False
        if _chapter_body_depth_failure_reason(bmap[k], milan_facts, lang):
            return False
    return True


def _parsed_chapter_row_for_key(parsed: dict, fk: str) -> dict | None:
    for c in parsed.get("chapters") or []:
        if isinstance(c, dict) and str(c.get("key") or "").strip().lower() == fk:
            return c
    return None


def _failing_chapter_keys(parsed: dict, milan_facts: dict, lang: str) -> list[str]:
    """Chapter keys whose ``chapter_body`` fails the lightweight depth gate."""
    bmap = _premium_chapter_bodies_map(parsed)
    out: list[str] = []
    for k in CHAPTER_KEYS:
        body = bmap.get(k, "")
        if _chapter_body_depth_failure_reason(body, milan_facts, lang):
            out.append(k)
    return out


def _depth_regen_dynamic_max_tokens(n_keys: int) -> int:
    """Scale completion budget with how many chapters are repaired in one batch."""
    n = max(1, int(n_keys))
    base = int(_PREMIUM_DEPTH_REGEN_MAX_TOKENS)
    extra = max(0, n - 1) * int(_PREMIUM_DEPTH_REGEN_TOKENS_PER_EXTRA_CHAPTER)
    return min(int(_PREMIUM_DEPTH_REGEN_MAX_TOKENS_CAP), max(800, base + extra))


def _build_depth_regen_user_augment(keys: list[str], parsed: dict) -> str:
    ex_cap = int(_PREMIUM_DEPTH_REGEN_EXCERPT_CHARS)
    lines = [
        "<DEPTH_REGEN_TARGETS>",
        "Expand ONLY these chapter keys (consultation depth, not slot summaries): "
        + ", ".join(keys),
    ]
    for k in keys:
        row = _parsed_chapter_row_for_key(parsed, k)
        excerpt = str((row or {}).get(CHAPTER_BODY_KEY) or "")[:ex_cap]
        lines.append(f"{k}_current_excerpt: {excerpt!r}")
    lines.append("</DEPTH_REGEN_TARGETS>")
    return "\n".join(lines)


def _openai_regen_chapters_depth(
    client: Any,
    tel: PdfGenOpenAITelemetry | None,
    model: str,
    lang: str,
    regen_system_base: str,
    user_prompt: str,
    keys: list[str],
    parsed: dict,
    oa_timeout: float,
    *,
    max_tokens: int,
) -> dict[str, str] | None:
    """One completion: JSON root with `chapters` only, updating listed keys. Returns key→body."""
    if not keys:
        return {}
    augment = _build_depth_regen_user_augment(keys, parsed)
    sys_content = regen_system_base.rstrip() + _DEPTH_REGEN_SYSTEM_SUFFIX
    messages = [
        {"role": "system", "content": sys_content},
        {"role": "user", "content": augment + "\n\n" + user_prompt},
    ]
    kw: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "response_format": {"type": "json_object"},
        "max_tokens": max(800, min(int(_PREMIUM_DEPTH_REGEN_MAX_TOKENS_CAP), int(max_tokens))),
        "timeout": oa_timeout,
    }
    if not model.lower().startswith("gpt-5"):
        kw["temperature"] = 0.52
    try:
        resp = client.chat.completions.create(**kw)
    except Exception as exc:
        log.warning("[premium_chapters] depth_regen openai fail: %s", exc)
        return None
    if tel is not None:
        try:
            tel.record(resp, "depth_regen")
        except Exception:
            pass
    raw = (resp.choices[0].message.content or "").strip()
    parsed_partial, _err = _parse_premium_llm_json(raw)
    if not isinstance(parsed_partial, dict):
        return None
    chs = parsed_partial.get("chapters")
    if not isinstance(chs, list):
        return None
    keyset = {str(k).strip().lower() for k in keys}
    out: dict[str, str] = {}
    for c in chs:
        if not isinstance(c, dict):
            continue
        ck = str(c.get("key") or "").strip().lower()
        nb = str(c.get(CHAPTER_BODY_KEY) or "").strip()
        if ck in keyset and nb:
            out[ck] = nb
    return out if out else None


def _apply_depth_regen_to_parsed(
    *,
    client: Any,
    tel: PdfGenOpenAITelemetry | None,
    model: str,
    lang: str,
    milan_facts: dict,
    regen_system_base: str,
    regen_user_prompt: str,
    parsed: dict,
    oa_timeout: float,
) -> tuple[bool, dict[str, Any]]:
    """Batched depth repair: few rounds, all failing keys per OpenAI call when possible."""
    meta: dict[str, Any] = {
        "depth_regen_calls": 0,
        "depth_regen_keys_touched": [],
        "depth_regen_last_reason": "",
        "depth_regen_shallow_keys_after": [],
    }
    max_rounds = int(_PREMIUM_DEPTH_REGEN_MAX_ROUNDS)
    fatal = _premium_depth_regen_fatal()
    for round_i in range(max_rounds):
        failing = _failing_chapter_keys(parsed, milan_facts, lang)
        if not failing:
            meta["depth_regen_shallow_keys_after"] = []
            return True, meta
        meta["depth_regen_last_reason"] = f"batch_r{round_i + 1}:" + ",".join(failing)
        mt = _depth_regen_dynamic_max_tokens(len(failing))
        got = _openai_regen_chapters_depth(
            client,
            tel,
            model,
            lang,
            regen_system_base,
            regen_user_prompt,
            failing,
            parsed,
            oa_timeout,
            max_tokens=mt,
        )
        if not got:
            continue
        meta["depth_regen_calls"] = int(meta["depth_regen_calls"]) + 1
        for fk, nb in got.items():
            fk = str(fk).strip().lower()
            if fk not in failing:
                continue
            if fk not in meta["depth_regen_keys_touched"]:
                meta["depth_regen_keys_touched"].append(fk)
            row = _parsed_chapter_row_for_key(parsed, fk)
            if row is None:
                parsed.setdefault("chapters", []).append(
                    {
                        "key": fk,
                        CHAPTER_BODY_KEY: nb,
                        CHAPTER_FULL_READ: nb,
                        "grounding": "",
                    }
                )
            else:
                row[CHAPTER_BODY_KEY] = nb
                row[CHAPTER_FULL_READ] = nb
        _finalize_chapter_narrative_for_pdf(parsed)
        _sanitize_premium_parsed_dict_in_place(parsed, lang)

    shallow = _failing_chapter_keys(parsed, milan_facts, lang)
    meta["depth_regen_shallow_keys_after"] = shallow
    if shallow and fatal:
        meta["depth_regen_exhausted_key"] = shallow[0]
        return False, meta
    if shallow:
        log.warning(
            "[premium_chapters] chapter depth still shallow after regen (non-fatal): keys=%s",
            shallow,
        )
    return True, meta


_PREMIUM_SHORT_SECTION_PREFIX = "[[short]]"


def _premium_strip_short_marker(text: str) -> tuple[str, bool]:
    """Strip optional ``[[SHORT]]`` marker; returns (body, was_marked)."""
    s = (text or "").strip()
    low = s.lower()
    if low.startswith(_PREMIUM_SHORT_SECTION_PREFIX):
        rest = s[len(_PREMIUM_SHORT_SECTION_PREFIX) :].lstrip()
        return rest, True
    return s, False


def _p65_meaningful_paragraph_gaps(text: str) -> int:
    """Count ``\\n\\n`` boundaries where both adjacent blocks meet minimum size."""
    raw, _marked = _premium_strip_short_marker(text or "")
    parts = [p.strip() for p in re.split(r"\n\s*\n", raw) if p.strip()]
    if len(parts) < 2:
        return 0
    mn = _PREMIUM_STRUCT_MIN_BLOCK_CP
    gaps = 0
    for i in range(len(parts) - 1):
        if len(parts[i]) >= mn and len(parts[i + 1]) >= mn:
            gaps += 1
    return gaps


def _p65_bullet_line_count(text: str) -> int:
    n = 0
    for line in (text or "").splitlines():
        if re.match(r"^\s*[•\-\–\*](\s|\S)", line):
            n += 1
    return n


def _p65_section_structurally_short(text: str) -> bool:
    body, marked = _premium_strip_short_marker(text or "")
    if marked:
        return True
    return len(body) <= _PREMIUM_SECTION_SHORT_MAX_CP


def _validate_chapter_render_structure_legacy(c: dict, key: str) -> str | None:
    """Legacy p65: paragraph gaps, mandatory behavioural/practical/chart beats, rhythm."""
    if not _chapter_has_structured_sections(c):
        return None

    total_bullets = 0
    rich_sections = 0
    bad_gap_sections: list[tuple[str, int]] = []

    for sk in CHAPTER_SECTION_KEYS:
        raw = str(c.get(sk, "") or "")
        vs, _mk = _premium_strip_short_marker(raw)
        if not vs.strip():
            return f"p65_struct_empty:{key}:{sk}"

        short = _p65_section_structurally_short(raw)
        gaps = _p65_meaningful_paragraph_gaps(raw)
        total_bullets += _p65_bullet_line_count(raw)

        if not short and gaps < 2:
            bad_gap_sections.append((sk, gaps))
        elif not short and gaps >= 2:
            rich_sections += 1

    thr = _PREMIUM_STRUCT_DENSE_SECTION_THRESHOLD
    if len(bad_gap_sections) >= thr:
        return f"p65_struct_dense_chapter:{key}:{len(bad_gap_sections)}"
    if bad_gap_sections:
        sk0, g0 = bad_gap_sections[0]
        return f"p65_struct_paragraphs:{key}:{sk0}:{g0}"

    for sk in CHAPTER_SECTION_KEYS:
        raw = str(c.get(sk, "") or "")
        if _p65_section_structurally_short(raw):
            continue
        vs, _mk = _premium_strip_short_marker(raw)
        if not _P65_BEHAVIOURAL_RE.search(vs):
            return f"p65_struct_layers:{key}:{sk}:behavioural"
        if not _P65_PRACTICAL_RE.search(vs):
            return f"p65_struct_layers:{key}:{sk}:practical"
        if not _CHART_VISIBILITY_RE.search(vs):
            return f"p65_struct_layers:{key}:{sk}:chart"

    n_non_short = sum(
        1
        for sk in CHAPTER_SECTION_KEYS
        if not _p65_section_structurally_short(str(c.get(sk, "") or ""))
    )
    need_rich = min(4, n_non_short) if n_non_short else 0
    if n_non_short >= 4 and total_bullets < 2 and rich_sections < need_rich:
        return f"p65_struct_chapter_rhythm:{key}:bullets={total_bullets}:rich={rich_sections}"

    return None


def _validate_chapter_render_structure(c: dict, key: str) -> str | None:
    """Soft default: unreadable codepoint wall without ``\\\\n\\\\n``. Legacy p65 when opt-in."""
    if not _chapter_has_structured_sections(c):
        return None
    for sk in CHAPTER_SECTION_KEYS:
        raw = str(c.get(sk, "") or "")
        vs, marked = _premium_strip_short_marker(raw)
        if not vs.strip():
            return f"p65_struct_empty:{key}:{sk}"
        if marked:
            continue
        if "\n\n" not in vs and len(vs) >= _PREMIUM_WALL_OF_TEXT_MIN_CP:
            return f"p65_render_wall:{key}:{sk}:{len(vs)}"
    if _premium_struct_validate_enabled():
        return _validate_chapter_render_structure_legacy(c, key)
    return None


# Kundli Milan Pro PDF — supported polish + renderer langs only.
PRO_PDF_LANG_CODES = frozenset({"en", "hn", "hi"})


def normalize_pro_pdf_lang(lang: str | None) -> str:
    """Coerce any client-supplied code to en | hn | hi (default en)."""
    code = (lang or "en").strip().lower() or "en"
    return code if code in PRO_PDF_LANG_CODES else "en"


# Phase 2.5.11.23-soul: audit-report phrases that kill the soul of the
# report. Tests + prompts discourage these; **validator no longer rejects** them.
# All entries lowercase — tests match against lowered prose.
SOUL_BAN_PHRASES = [
    "engine driver", "engine drivers", "engine score",
    "based on engine score", "engine signals",
    "no significant friction", "natural baseline compatibility",
    "stable and well within", "drivers indicate practical compatibility",
    "detailed reading was not generated", "chapter not generated",
]

# Phase 2.5.11.23-soul-v2 + tone-hardening (May 2026): therapy / wellness /
# relationship-coaching pamphlet phrases. Validator rejects if ANY distinct
# entry appears anywhere in combined prose (zero tolerance — emotionally
# optimised advice-copy has no place in this PDF lane).
# Legacy brochure / compatibility-report phrasing (validator rejects).
LEGACY_COMPAT_CLICHES = [
    "strong match", "strong compatibility", "highly compatible",
    "lifelong partnership", "deeply fulfilling relationship",
    "perfect harmony", "emotional harmony", "relationship harmony",
    "communication is crucial", "communication is essential",
    "blossom together", "blossoms together", "blossoming together",
    "auspicious union", "auspicious match", "auspicious bond",
    "perfect match", "ideal match", "made for each other",
    "strong foundation", "healthy children", "mutual welfare",
    "destiny favours", "respect each other's space",
    "smooth married life", "smooth match astrologically",
    "cosmic forces", "stars align strongly", "harmonious union",
    # Milan / app-summary tone (p55)
    "ashtakoot score achha hai", "ashtakoot score achha", "ashtakoot score",
    "compatibility factor", "compatibility factors", "strong bond",
    "good understanding", "relationship stable rahega", "relationship stable",
    "great compatibility", "overall compatibility is good", "milan score achha",
    "guna milan achha", "guna score achha",
]

THERAPY_CLICHES = [
    "honest dialogue", "mutual respect", "consistent care",
    "open communication", "communicate openly", "communicate honestly",
    "openly discuss", "discuss openly", "communicate better",
    "better communication", "healthy communication", "improve communication",
    "communication is key", "communication skills",
    "build trust", "show appreciation", "active listening",
    "be patient with each other", "express your feelings",
    "be patient", "show patience", "practice patience", "have patience",
    "make time for each other",
    "nurture the bond", "nurture this bond", "support each other",
    "emotional support", "offer support", "be supportive",
    "maintain honesty", "understanding deepen", "deepen understanding",
    "mutual understanding", "emotional understanding",
    "understanding deepen karna", "deepen understanding karna",
    "patience rakhna hoga", "patience rakhna padega",
    "understanding deepen karna hoga",
    "emotional openness", "practice openness",
    "phone-free dialogue", "explicit conversation",
    "life-coach", "life coach", "couples counselling", "couples counseling",
    # Phase premium emotional-realism gate (May 2026): pamphlet / AI-wellness tone
    "healthy relationship", "healthy marriage",
    "deeply fulfilling", "lifelong partnership",
    "strong communication",
    "mutual understanding will improve",
    "understanding deepen hogi",
    "relationship coaching", "emotional coaching",
]

# Phase 2.5.11.23-soul-v2: perfect-balance language hides emotional
# asymmetry. Real relationships are uneven by nature — prompt + validator
# reject phrases that pretend both partners always feel the same thing.
PERFECT_BALANCE_PHRASES = [
    "dono naturally same", "both partners equally",
    "dono ko ek hi tarah", "perfectly aligned",
    "both feel the same", "both equally invested",
]

def _full_read_word_count(text: str) -> int:
    """Approximate word count for premium prose (whitespace-separated tokens)."""
    return len((text or "").strip().split())


def _chapter_sections_merged(c: dict) -> str:
    return "\n\n".join(
        str(c.get(sk, "")).strip()
        for sk in CHAPTER_SECTION_KEYS
        if str(c.get(sk, "")).strip()
    )


def _chapter_has_structured_sections(c: dict) -> bool:
    return any(str(c.get(sk, "")).strip() for sk in CHAPTER_SECTION_KEYS)


def _chapter_narrative_blob(c: dict) -> str:
    """Combined chapter prose for duplication / trope / rhythm guards."""
    cb = str(c.get(CHAPTER_BODY_KEY) or "").strip()
    if cb:
        return cb
    if _chapter_has_structured_sections(c):
        return " ".join(str(c.get(sk, "")).strip() for sk in CHAPTER_SECTION_KEYS)
    return (c.get(CHAPTER_FULL_READ) or "").strip()


def _finalize_chapter_narrative_for_pdf(parsed: dict) -> None:
    """Normalize each chapter to one narrative string: ``chapter_body`` (+ ``full_read``).

    Non-empty ``chapter_body`` from the LLM **wins**; legacy subsection keys are cleared
    so they cannot override or fragment the live PDF path. If only legacy keys exist, they
    are merged in order into one body.
    """
    chs = parsed.get("chapters")
    if not isinstance(chs, list):
        return
    for c in chs:
        if not isinstance(c, dict):
            continue
        cb_in = str(c.get(CHAPTER_BODY_KEY) or "").strip()
        if cb_in:
            narrative = cb_in
        else:
            bits = [str(c.get(sk) or "").strip() for sk in CHAPTER_SECTION_KEYS if str(c.get(sk) or "").strip()]
            narrative = "\n\n".join(bits) if bits else str(c.get(CHAPTER_FULL_READ) or "").strip()
        if len(narrative) > _PREMIUM_CHAPTER_BODY_MAX_CP:
            narrative = _truncate_pdf_safe_cp(narrative, _PREMIUM_CHAPTER_BODY_MAX_CP)
        c[CHAPTER_BODY_KEY] = narrative
        c[CHAPTER_FULL_READ] = narrative
        for sk in CHAPTER_SECTION_KEYS:
            c[sk] = ""


def _split_sents_for_premium_render(text: str) -> list[str]:
    return [
        s.strip()
        for s in re.split(r"(?<=[.!?।])\s+", (text or "").strip())
        if s.strip()
    ]


def _merge_sents_to_paragraphs(sents: list[str], n: int = 3) -> str:
    if not sents:
        return ""
    sents = list(sents)
    while len(sents) < n:
        sents.append(sents[-1])
    if len(sents) == n:
        return "\n\n".join(sents)
    groups = n
    per = len(sents) // groups
    rem = len(sents) % groups
    out_chunks: list[str] = []
    idx = 0
    for g in range(groups):
        take = per + (1 if g < rem else 0)
        chunk = sents[idx : idx + take]
        idx += take
        out_chunks.append(" ".join(chunk))
    return "\n\n".join(out_chunks)


def _normalize_premium_sections_render(sec: dict[str, str], *, p1n: str, p2n: str) -> None:
    """No-op for GPT-first: deterministic p65 prose shaping / filler disabled."""
    _ = (p1n, p2n)
    for sk in CHAPTER_SECTION_KEYS:
        v = str(sec.get(sk) or "").replace("\x00", "").strip()
        if len(v) > _PREMIUM_SECTION_MAX_CP:
            v = v[: _PREMIUM_SECTION_MAX_CP].rsplit(" ", 1)[0].strip()
        sec[sk] = v


def _ensure_premium_section_explanation_depth(sec: dict[str, str], *, p1n: str, p2n: str) -> None:
    """No-op for GPT-first: deterministic p66 list-blob / depth padding disabled."""
    _ = (p1n, p2n)
    for sk in CHAPTER_SECTION_KEYS:
        v = str(sec.get(sk) or "").replace("\x00", "").strip()
        if len(v) > _PREMIUM_SECTION_MAX_CP:
            v = v[: _PREMIUM_SECTION_MAX_CP].rsplit(" ", 1)[0].strip()
        sec[sk] = v


def _chart_bridge_with_remedy_tail(text: str) -> str:
    """Deterministic soul helper: optionally append a verbatim ``ALLOWED_REMEDIES`` tail.

    When ``COMPAT_PREMIUM_REMEDY_TAIL_VALIDATE`` is off (default), returns text unchanged.
    """
    t = (text or "").strip()
    if not _premium_remedy_tail_validate_enabled():
        return t
    if _remedy_tail_ok(t):
        return t
    pick = "joint daily prayers"
    return f"{t} {pick}".strip()


def _remedy_tail_ok(text: str) -> bool:
    ts = (text or "").strip()
    return any(ts.endswith(r) for r in ALLOWED_REMEDIES)


def _premium_narrative_word_count(out: dict) -> int:
    """Total words across all reader-facing narrative strings (diagnostics / meta)."""
    if not isinstance(out, dict):
        return 0
    parts: list[str] = [
        str(out.get("hidden_truth") or ""),
        str(out.get("verdict") or ""),
    ]
    for x in out.get("special") or []:
        parts.append(str(x))
    for x in out.get("damage") or []:
        parts.append(str(x))
    for x in out.get("practical") or []:
        parts.append(str(x))
    for c in out.get("chapters") or []:
        if not isinstance(c, dict):
            continue
        nb = _chapter_narrative_blob(c)
        parts.append(nb if nb else str(c.get(CHAPTER_FULL_READ) or ""))
        parts.append(str(c.get("grounding") or ""))
    mb = out.get("marriage_blueprint")
    if isinstance(mb, dict):
        for fld in (
            "p1_marriage_nature",
            "p2_marriage_nature",
            "interaction_dynamic",
            "what_p1_needs_from_p2",
            "what_p2_needs_from_p1",
            "blueprint_takeaway",
        ):
            parts.append(str(mb.get(fld) or ""))
    return _full_read_word_count(" ".join(parts))


def _catastrophic_duplicate_chapter_reads_ok(
    chapters: list[dict],
) -> tuple[bool, str]:
    """Reject when ≥5 chapters share the same substantial body (copy-paste)."""
    norms: list[str] = []
    for c in chapters:
        raw = _chapter_narrative_blob(c) or (c.get(CHAPTER_FULL_READ) or "").strip()
        norms.append(re.sub(r"\s+", " ", raw.lower()))
    long_norms = [n for n in norms if len(n) >= 100]
    if len(long_norms) < 5:
        return True, "ok"
    top_n = Counter(long_norms).most_common(1)[0][1]
    if top_n >= 5:
        return False, f"catastrophic_duplicate_chapters:{top_n}"
    return True, "ok"


def _truncate_full_read_to_max_words(text: str, max_words: int) -> str:
    parts = (text or "").strip().split()
    if len(parts) <= max_words:
        return (text or "").strip()
    return " ".join(parts[:max_words])


# Phase 2.5.11.23-soul-v4 — RHYTHM FORMULA PATTERNS
# ChatGPT critique: every chapter opens with the same "ek partner ... dusra ..."
# asymmetry pattern. Subconsciously the LLM/template signature becomes visible
# after a few pages. Validator counts how many chapters' full_read OPEN (first
# ~180 chars) with this formulaic asymmetry framing — if ≥5 of 7 chapters do,
# the response is rejected as "too rhythmically uniform". Asymmetry itself is
# still encouraged everywhere — but the OPENING delivery must vary across
# chapters: sometimes a metaphor, sometimes a concrete scene, sometimes a
# direct observation, sometimes a bittersweet truth.
_RHYTHM_FORMULA_OPENER_RE = re.compile(
    r"\bek\s+partner\b.{0,160}\b(?:dusr[aeio]|doosr[aeio])\b", re.I | re.S
)


def _rhythm_variation_ok(chapters: list[dict]) -> tuple[bool, int]:
    """Return (ok, formula_count). ok=True iff <5 of 7 chapters open with the
    'ek partner ... dusra ...' formula in the first ~180 chars of full_read."""
    formula = 0
    for c in chapters:
        head = ((c.get("core_dynamic") or c.get(CHAPTER_FULL_READ) or "") or "")[:180]
        if _RHYTHM_FORMULA_OPENER_RE.search(head):
            formula += 1
    return (formula < 5), formula


MULTILINGUAL_MASTER_SYSTEM = """LANGUAGE LOCK (read `language` from <USER_CONTEXT>):
- `en`: Latin English for all narrative JSON strings.
- `hn`: Roman Hindi / Hinglish only (no Devanagari in narrative strings).
- `hi`: देवनागरी for narrative strings; keep partner names, nakshatra/rashi spellings, koot labels, remedy phrases, and numeric totals exactly as Latin given in the chart data blocks.

CROSS-LANE NARRATIVE QUALITY (required — `en`, `hn`, and `hi`):
- The **Hinglish (`hn`) lane** is the **emotional-realism benchmark**: lived asymmetry, micro-behaviours, who goes quiet first, how fights restack, how fatigue shifts chemistry — that same grade of witnessed specificity must appear in **English** and **Hindi**; only script/register differs.
- **Parity of depth:** no lane may read thinner, safer, more brochure-like, or more “template polished” than another. If you would paint a sharper scene in Hinglish, paint it with equal sharpness in English or देवनागरी — do not replace it with generic SaaS reassurance.
- **Compose in the target lane:** do not mentally translate from another language; think and write directly in natural English or natural spoken Hindi so prose stays idiomatic and fluid.
- **Avoid in every lane:** corporate/product voice, therapy-app cadences, HR-coach checklists, repetitive symmetrical sentence rhythm, stock AI report openers (“It is important to note…”, “In today’s fast-paced world…”), and vague stakeholder abstractions.

Emit exactly one JSON object (no markdown fence, no preamble).
"""

# Layer 2 — register + voice (script rules stay in LANGUAGE LOCK above).
_ENGLISH_LANGUAGE_PERSONALITY_PROFILE = """
LANGUAGE=en — Premium **spoken** English: calm senior astrologer in the consultation room, not a SaaS onboarding deck.
- Sound human: varied sentence lengths, occasional shorter beats, natural rhythm — not every paragraph the same polished cadence.
- Prefer concrete relationship observation (habits, timing, silence, pursuit, money/in-law pressure) over abstract “insights” or product-y labels.
- Warm and modern register is fine; **never** startup brochure, wellness pamphlet, or generic executive-summary tone.
"""

_HINGLISH_LANGUAGE_PERSONALITY_PROFILE = """
LANGUAGE=hn — Natural Roman Hindi / Hinglish (Latin letters only): warm, modern, emotionally fluent — the **reference lane** for how specific and human this product should feel.
- Keep the same consultation honesty and behavioural detail you would bring in the best face-to-face milan read; avoid filler “samajhna hoga” lines unless chart-earned (per core AUTHORING rules).
"""

_HINDI_LANGUAGE_PERSONALITY_PROFILE = """
LANGUAGE=hi — देवनागरी Hindi: emotionally grounded, **traditional-human** astrologer voice — fluent, conversational Hindi for home and marriage (बोलचाल, गृहस्थी, रिश्तों की सहज शब्दावली), not administrative formal tone and not English translated word-by-word into stiff शुद्धisms.
- Let sentences breathe: natural connectors, lived scenes, asymmetry between partners — same emotional intelligence as the Hinglish lane, expressed in idiomatic Devanagari.
- Latin islands per Layer 1 rule (names, nakshatra/rashi spellings, koot labels, remedies, numbers) stay verbatim from the data blocks.
"""


def _language_personality_profile(lang: str) -> str:
    """Layer 2 — English / Hinglish / Hindi only (Pro PDF product lane)."""
    code = normalize_pro_pdf_lang(lang)
    header = "═══ LAYER 2 — OUTPUT REGISTER ═══\n"

    if code == "en":
        return header + _ENGLISH_LANGUAGE_PERSONALITY_PROFILE.strip()

    if code == "hn":
        return header + _HINGLISH_LANGUAGE_PERSONALITY_PROFILE.strip()

    return header + _HINDI_LANGUAGE_PERSONALITY_PROFILE.strip()


def build_premium_system_prompt(lang: str = "en") -> str:
    """Compose premium system prompt: language lock + JSON contract + minimal authoring."""
    lang_n = normalize_pro_pdf_lang(lang)
    return (
        MULTILINGUAL_MASTER_SYSTEM.strip()
        + "\n\n"
        + _language_personality_profile(lang_n).strip()
        + "\n\n"
        + SYSTEM_PROMPT_PREMIUM_CORE.strip()
    )


SYSTEM_PROMPT_PREMIUM_CORE = """=== PREMIUM PDF — MACHINE CONTRACT (chart data + JSON only) ===
Fill the JSON schema from the user message data blocks only. Do not invent koot lines, nakshatras,
planets, signs, houses, dates, or scores not supported by those blocks.

The `<STRUCTURED_CHART_DATA>` block is one compact JSON object (UTF-8): raw structured astrology for
both partners — typically `d1` (per-partner ascendant, planets with sign/house/nakshatra and relation
fields where computed), `d9_marriage`, `synastry_7l`, `kp_couple_promise`, and optional bundle fields.
Read the **entire** JSON before writing.

`<STRUCTURED_CHART_DATA>` is the **primary source of truth**. The Ashtakoot grid is **supporting
context only** — do not let Milan score or generic compatibility language **carry** the report.

=== AUTHORING (high intelligence, chart-grounded) ===
You are an expert relationship astrologer analyzing two complete kundlis together.

Your primary output shape is **one deep consultation chapter per JSON chapter**, not forty-nine
micro-answers. Each chapter must be a single string field `chapter_body`: one continuous,
chart-grounded reading in natural consultation voice — reasoning, synthesis, both kundlis compared,
practical married-life manifestation, emotional and behavioural texture. Use **`\\n\\n`** between
paragraphs so the prose breathes. Order matters for downstream PDF mapping: write **front to back**
as you would speak (opening dynamic → lived pattern → strengths/risks → practical marriage rhythm
→ forward-looking arc → closing bridge including any remedy-oriented close for stability / future
chapters when relevant).

Spend tokens on **depth and synthesis**, not on mentally filling seven labeled blanks.

**Cross-chapter parity (required):** All **seven** `chapter_body` strings must be **similarly deep and long**
— each is its own full consultation chapter for that theme (ch1…ch7). **Do not** spend most of the report on
one chapter and leave others as short summaries or afterthoughts. Before you finish the JSON, mentally
re-balance: if any `chapter_body` is much thinner than the others, **expand it** with chart-grounded reasoning,
both-kundli comparison, and practical married-life texture until every chapter feels comparably premium.

Deeply study the full structured chart data before writing.
Cross-read D1, D9, synastry, house lords, yogas, nakshatras, planetary strengths, emotional compatibility,
marriage stability, attraction, intimacy, conflict patterns, long-term sustainability, family dynamics,
finances, communication, and practical married life.

Do not give generic astrology summaries.
Explain why patterns follow from the charts you were given.
Connect placements to real-life manifestations naturally and intelligently.

Write like a highly experienced astrologer giving a real premium kundli-milan consultation to clients.

Use your own intelligence, reasoning, synthesis, and natural narrative flow.
Do not mechanically follow templates or forced emotional formulas.

The report should feel deeply insightful, human, detailed, premium, and grounded in the actual charts.

=== LONG-FORM PROSE TARGET (one illustration of depth; do not copy — ground every claim in the real JSON) ===
The block below is **synthetic** and only shows the weave you want: named placements → reasoning → how it
manifests → **both** charts compared → practical married-life outcome → emotional and behavioural texture.
In production strings, replace all specifics with facts from `<STRUCTURED_CHART_DATA>` for this couple.
**Voice:** the sample uses “Partner One / Two” labels for structure only — your real output must follow the
**second-person plural to the couple** rule in CONSULTATION VOICE (not sustained third-person “about them”).

Partner One’s Moon occupies the fourth house in the rashi map while the seventh lord carries a sobering aspect
from Saturn; Partner Two’s Venus sits in strong dignity yet the seventh-house story is fed more by exchange and
effort than by an effortless emotional shortcut from the lagna. Read together, the charts do not scream
incompatibility on paper — they show **different nervous systems for safety**: Partner One reaches for closeness
when domestic stress or boundary issues spike, while Partner Two reaches for harmony and affection but does not
automatically convert that into the same repair script after friction.

That asymmetry is quiet while dating and loud after marriage: the same fight returns because Partner One
experiences withdrawal as abandonment, while Partner Two experiences repeated debrief as pressure. The practical
pattern that works is explicit negotiation of **timing** (cooling hours versus same-evening resolution) and
anchoring reassurance in **behaviour**, not only words. Emotionally, both maps can support loyalty once trust is
earned; behaviourally, the growth edge is to name the lagna-side mismatch without keeping score over who was hurt
first — because triggers and default defences are not mirrored between the two kundlis.

=== DEPTH & COMPLETENESS (balanced) ===
Let **substance** set length: when the chart signal is rich, write **full paragraphs** and use **`\\n\\n`** inside
`chapter_body` so the server can map your rhythm into readable PDF blocks. No fixed paragraph counts — aim for
consultation-grade depth wherever the data supports it. The overall report should feel **complete, detailed, and
premium**, not thin placeholder filler.

**Even coverage:** every chapter theme deserves real chart synthesis — not a single “hero” chapter and six thin
companions. Length does not need to be identical to the character, but **depth and paragraph count should feel
in the same band** across all seven. The same rule applies to **`special`**, **`damage`**, and **`practical`**:
each must read like a real consultation block (multi-paragraph, chart-led, both kundlis compared), **not** thin
bullet slogans.

**Pro PDF page fill:** Cosmic Lens Pro renders **one A4 page per chapter** (title + optional chart bridge + your
`chapter_body`). When `chapter_body` is too short, that page looks half-empty to clients. Aim for **enough
substantive prose** that each chapter would **naturally fill most of that printed page** — as a rough guide,
about **≥ 2600–3200 characters** per `chapter_body` in typical Latin scripts (adjust for Devanagari density) and
**at least five** `\\n\\n` paragraph breaks when the chart supports it. Still chart-grounded: never pad with
generic filler sentences unrelated to this couple’s JSON.

Compare **both** kundlis together wherever the reading needs it — contrast, timing mismatch, complementary vs
clashing habits — in a **natural** voice, not a mechanical side-by-side checklist.

This is substance and readability guidance — not rigid quotas, emotional philosophy, or layout micromanagement.

=== CONSULTATION VOICE — LIVED MARRIAGE (not advice columns) ===
Readers paid for a **senior astrologer’s witnessed read** of two kundlis — prose should feel like **quiet
observation of how this marriage tends to move across years**: who goes quiet first, who chases same-evening
closure, where attraction softens or sharpens under fatigue, how money or in-laws borrow emotional bandwidth.

**Address the couple together (required):** write as if you are in the consultation room **speaking to both
partners at once** — default **second-person plural** (`you both` / `aap dono` / `tum dono`; Hindi: `आप दोनों`).
Do **not** sustain detached third-person “case file” narration aimed at an invisible reader (`X aur Y ke…`,
`unke/un dono vyaktiyon ke…` as the spine of every graf). Use first names **only** to separate who shows which
habit, then return quickly to dual address. The PDF is for the pair, not a report **about** them to someone else.

**Replace generic counselling glue** (“understand each other”, “communicate better”, “accept differences”,
Hinglish filler like “samajhna hoga / support karna hoga / differences accept karna hoga / baat karni chahiye”)
unless each such line is **immediately** tied to a **named chart mechanism** in the same breath (lord, house,
D9 vs D1 tension, synastry overlay, KP promise) so the advice is visibly **earned from the map**, not pasted on.

**Prefer behavioural micro-plots over slogans:** e.g. one partner withdraws while the other loops the same
topic; **emotional timing** clashes more than “lack of care”; the same quarrel **re-stacks quietly** after calm
weeks because the lagna/Moon/Venus pattern was never spoken in plain words.
Avoid repeating the same chart conclusion in adjacent paragraphs with synonym swaps — each paragraph should
advance the read with **new** detail (another house angle, a different lived scene, or a sharper both-kundli contrast).

**When the JSON gives signal, spell out HOW:** how the pattern lands in **daily married rhythm**; how small
repeats **accumulate** into distance; how fights **start, stall, and cool** for *this* pair; how chemistry
**shifts after early years** with workload or family load; how **duty + money + parents / in-laws** squeeze the
same nerve the navamsa or seventh-house story already sketched.

**Astrology stays visibly intelligent, not academic:** seventh-lord condition, Moon’s need for safety and habit,
Venus–Mars interplay, D9 marriage stability vs D1, synastry on partnership houses, KP couple promise — weave
these **inside** lived scenes so planets earn their place in the sentence, not as decoration after a pep talk.

**Calibrate weaker zones to `marriage_blueprint` quality:** `hidden_truth`, **ch5** (Physical + Emotional
Chemistry), **ch6** (Family + Practical Life), **ch7** (Long-Term Future Direction) and `verdict`, plus
`special`, `damage`, and `practical`, should feel as **specific and behavioural** as your strongest blueprint-style
blocks — never like a relationship magazine, a therapy worksheet, or a compressed “chapter summary slot”.

**Language-lane parity:** when `language` is `en` or `hi`, keep the **same witnessed emotional density and
micro-behavioural specificity** the Roman Hinglish lane is held to (see LANGUAGE LOCK + Layer 2) — do not substitute
brochure-polished English or stiff translation-style Hindi for the sharper, more human read you would have given in `hn`.

This block is **direction**, not a compliance rubric — vary language, stay human, avoid copy-paste moral closers
repeated across many strings.

=== OUTPUT SHAPE (required JSON) ===
Emit **one** root JSON object. Required top-level keys:

- `hidden_truth` — long-form narrative string (“Hidden Underneath” tone): same witnessed specificity as
  `marriage_blueprint` — chart-led, behaviour-first, accumulation of quiet patterns; not a generic compatibility
  essay.
- `chapters` — array of exactly **seven** objects, in order **ch1** … **ch7** (use each object’s `key` field).
- `special` — array of **three** strings for the Pro-PDF page **“What Makes This Bond Special.”** Each string is
  one **full consultation arc** (not a one-line praise bullet): use **multiple paragraphs** inside the string,
  separated by `\\n\\n`; explain chart reasoning (houses, lords, D1/D9, synastry, KP where the JSON supports it);
  compare **both** partners’ maps; show emotional + behavioural manifestations. Optional `•` / `-` highlight lines
  may appear **inside** prose — never as the only content.

- `damage` — array of **exactly two** strings for **“What Can Quietly Damage This Bond.”** Same consultation depth
  as `special`: multi-paragraph per string (`\\n\\n`), chart-grounded, both kundlis, how distance accrues in
  ordinary weeks — not generic warnings.

- `practical` — array of **three** strings for **“Practical Married Life.”** Each string is a **long** multi-paragraph
  block (`\\n\\n`) weaving **daily** home rhythm, family/in-law boundaries, money and duties, emotional labour,
  routines, communication habits, conflict/repair scripts, and role balance — always explained through **chart
  combinations** (not lifestyle platitudes). Bullets only as optional in-prose highlights, not the primary format.
- `verdict` — narrative string.
- `marriage_blueprint` — object with keys: `p1_marriage_nature`, `p2_marriage_nature`, `interaction_dynamic`,
  `what_p1_needs_from_p2`, `what_p2_needs_from_p1`, `blueprint_takeaway` (each a narrative string).

**Each chapter object** must include:
- `key` — exactly `ch1` … `ch7` matching the chapter theme row below.
- `chapter_body` — **one** non-empty string: the full chapter consultation (multiple paragraphs separated by
  `\\n\\n`). The server derives PDF subsection layout from this string; **do not** emit separate
  `core_dynamic`, `lived_manifestation`, etc.
  **Each** `chapter_body` must be a **long, multi-paragraph** chapter in its own right — comparable in richness to
  the other six, not a short stub — and long enough that the **printed Pro-PDF chapter page** reads as a full
  consultation sheet, not a short note floating in white space.

Optional per chapter: `grounding` (short factual chart bridge for the PDF “bridge” card; keep under ~900 chars
worth of content).

Chapter themes by `key`:
• ch1 — Emotional Compatibility
• ch2 — Trust & Loyalty
• ch3 — Communication & Conflict
• ch4 — Marriage Stability
• ch5 — Physical + Emotional Chemistry
• ch6 — Family + Practical Life
• ch7 — Long-Term Future Direction

**Extra calibration (ch5–ch7 + verdict):** **ch5** — attraction and intimacy as **time-varying rhythm** (stress,
tiredness, novelty vs safety), not textbook planet blurbs. **ch6** — family, in-laws, money, and domestic duty as
**felt pressure and negotiation**, not lifestyle bullet points. **ch7** + **`verdict`** — forward arc as **likely
recurring seasons** in the bond (chart-grounded), not motivational poster language.

All string values must stay within normal length expectations for a premium report; extreme overflow is
truncated server-side for PDF safety, not rejected.

**Milan tally:** include the total exactly as \"N out of M\" (same integers as in `<PARTNER_KOOT_GRID>`)
once in `verdict` or `hidden_truth`.

**Remedies:** only when the operator sets ``COMPAT_PREMIUM_REMEDY_TAIL_VALIDATE=1`` must the **closing portion**
of each **ch4** and **ch7** chapter (the tail of `chapter_body`, which maps to the last on-page subsection)
**end** with one verbatim substring from `<ALLOWED_REMEDIES>`. Otherwise natural closings.

**Safety:** do not assert lifespan, death, children gender, divorce, or guaranteed futures.

=== PDF + JSON SAFETY (minimal) ===
- Forbidden substrings in narrative: `(beat-`, `(mark-`, `pattern-` (layout-corruption markers).
- Readable PDF text: use `\\n\\n` inside long strings for paragraph breaks; no rigid layout quotas.
- Escape ASCII double-quote inside any string as \\".
- Escape backslash as \\\\.
- Use \\\\n only for intentional line breaks inside strings; no raw unescaped newlines inside quotes.
- Close all strings; no markdown fences; no text before or after the JSON object.

=== OUTPUT (JSON only, no markdown, no preamble) ===
Return a single valid JSON object matching the OUTPUT SHAPE above. Do not paste abbreviated example objects
with placeholder ellipses — write the real complete JSON for this couple.
"""


def build_premium_regen_chapter_system_prompt(lang: str) -> str:
    """Compact system stack for chapter depth regen (avoids re-sending full MACHINE CONTRACT)."""
    lang_n = normalize_pro_pdf_lang(lang)
    return (
        MULTILINGUAL_MASTER_SYSTEM.strip()
        + "\n\n"
        + _language_personality_profile(lang_n).strip()
        + "\n\n"
        + _PREMIUM_REGEN_CORE_SHRINK.strip()
    )


def build_premium_regen_sdp_system_prompt(lang: str) -> str:
    """Compact system stack + SDP JSON fragment contract."""
    return build_premium_regen_chapter_system_prompt(lang).rstrip() + _SDP_DEPTH_REGEN_SYSTEM_SUFFIX


SYSTEM_PROMPT_PREMIUM = build_premium_system_prompt("en")


def _empty_pro_premium_shell() -> dict[str, Any]:
    """Non-authoring payload when polish cannot produce LLM JSON — PDF uses renderer placeholders."""
    return {
        "hidden_truth": "",
        "verdict": "",
        "chapters": [],
        "special": [],
        "damage": [],
        "practical": [],
        "marriage_blueprint": {
            "p1_marriage_nature": "",
            "p2_marriage_nature": "",
            "interaction_dynamic": "",
            "what_p1_needs_from_p2": "",
            "what_p2_needs_from_p1": "",
            "blueprint_takeaway": "",
        },
    }


def _return_empty_polish_with_telemetry(pg: dict[str, Any]) -> dict[str, Any]:
    out = _empty_pro_premium_shell()
    out["_meta"] = {"version": _PREMIUM_VERSION}
    merge_pdf_generation_into_meta(out["_meta"], pg)
    publish_and_log_pdf_generation(pg)
    return out


def _mlf_embed_or_fallback(mlf: dict | None, key: str, fb: dict) -> dict:
    """Prefer `marriage_llm_facts[key]` when present so prompt matches bundled payload."""
    if isinstance(mlf, dict):
        v = mlf.get(key)
        if isinstance(v, dict) and v:
            return v
    return fb if isinstance(fb, dict) else {}


def _premium_llm_chart_bundle(
    marriage_llm_facts: dict | None,
    d9: dict,
    syn: dict,
    kp: dict,
) -> dict[str, Any]:
    """Merge full structured chart facts for the premium user prompt (no lossy digest)."""
    d9_c = _mlf_embed_or_fallback(marriage_llm_facts, "d9_marriage", d9)
    syn_c = _mlf_embed_or_fallback(marriage_llm_facts, "synastry_7l", syn)
    kp_c = _mlf_embed_or_fallback(marriage_llm_facts, "kp_couple_promise", kp)

    if isinstance(marriage_llm_facts, dict) and marriage_llm_facts:
        bundle: dict[str, Any] = copy.deepcopy(marriage_llm_facts)
    else:
        bundle = {}

    if isinstance(d9_c, dict) and d9_c:
        bundle["d9_marriage"] = d9_c
    if isinstance(syn_c, dict) and syn_c:
        bundle["synastry_7l"] = syn_c
    if isinstance(kp_c, dict) and kp_c:
        bundle["kp_couple_promise"] = kp_c

    return bundle


def _serialize_premium_chart_json(bundle: dict[str, Any], *, max_chars: int | None = None) -> str:
    """Compact JSON for ``<STRUCTURED_CHART_DATA>``.

    When ``max_chars`` is set, hard-cap serialized length (used for regen prompts).
    When ``None``, apply ``COMPAT_PREMIUM_CHART_JSON_MAX_CHARS`` if the operator set it.
    """
    try:
        raw = json.dumps(
            bundle,
            ensure_ascii=False,
            separators=(",", ":"),
            default=str,
        )
    except Exception as exc:
        log.warning("[premium_chapters] chart bundle json.dumps failed: %s", exc)
        return "{}"

    cap: int | None = max_chars
    if cap is None:
        cap_s = (os.environ.get("COMPAT_PREMIUM_CHART_JSON_MAX_CHARS") or "").strip()
        if not cap_s:
            return raw
        try:
            cap = int(cap_s)
        except ValueError:
            return raw
    if cap is None or cap <= 0 or len(raw) <= cap:
        return raw
    log.warning(
        "[premium_chapters] STRUCTURED_CHART_DATA JSON truncated "
        "(max_chars=%s raw_len=%s)",
        cap,
        len(raw),
    )
    return raw[:cap]


def _build_raw_marriage_facts_section(
    marriage_llm_facts: dict | None,
    d9: dict,
    syn: dict,
    kp: dict,
    *,
    chart_json_max_chars: int | None = None,
) -> str:
    bundle = _premium_llm_chart_bundle(marriage_llm_facts, d9, syn, kp)
    body = _serialize_premium_chart_json(bundle, max_chars=chart_json_max_chars)
    return f"<STRUCTURED_CHART_DATA>\n{body}\n</STRUCTURED_CHART_DATA>"


def _regen_chart_json_cap() -> int | None:
    """Optional tighter cap for regen user prompts (primary generation unchanged).

    ``COMPAT_PREMIUM_REGEN_CHART_JSON_MAX_CHARS`` — empty/unset defaults to **52000**.
    Set to ``0``, ``full``, or ``none`` to disable extra regen cap (only primary env cap applies).
    """
    raw = (os.environ.get("COMPAT_PREMIUM_REGEN_CHART_JSON_MAX_CHARS") or "").strip()
    rl = raw.lower()
    if rl in ("full", "none", "0", "-1"):
        return None
    if not raw:
        return 52_000
    try:
        return max(4000, int(raw))
    except ValueError:
        return 52_000


def _build_user_prompt(
    milan_facts: dict,
    chapter_scores: dict,
    d9: dict,
    syn: dict,
    kp: dict,
    lang: str,
    marriage_llm_facts: dict | None = None,
    *,
    chart_json_max_chars: int | None = None,
) -> str:
    _ = (chapter_scores or {}).get("overall_avg_0_10")  # caller contract; not sent to LLM
    p1 = milan_facts.get("p1", {}) or {}
    p2 = milan_facts.get("p2", {}) or {}
    koots = milan_facts.get("koots", []) or []

    koot_lines = []
    for k in koots:
        s, mx = k.get("score", 0), k.get("max", 0)
        koot_lines.append(f"  {k.get('label','?'):<8} {s} / {mx}")

    p1_mang = p1.get("manglik", False)
    p2_mang = p2.get("manglik", False)
    if p1_mang and p2_mang:
        mang = "manglik_status: both_manglik"
    elif p1_mang or p2_mang:
        mang = f"manglik_status: only_{'p1' if p1_mang else 'p2'}_manglik"
    else:
        mang = "manglik_status: neither"

    raw_marriage = _build_raw_marriage_facts_section(
        marriage_llm_facts, d9, syn, kp, chart_json_max_chars=chart_json_max_chars
    )

    return f"""<PARTNER_KOOT_GRID>
p1_name: {p1.get('name','Partner 1')}
p1_nakshatra: {p1.get('nakshatra','?')} (Pada {p1.get('pada','?')}, {p1.get('rashi','?')})
p1_manglik: {p1_mang}

p2_name: {p2.get('name','Partner 2')}
p2_nakshatra: {p2.get('nakshatra','?')} (Pada {p2.get('pada','?')}, {p2.get('rashi','?')})
p2_manglik: {p2_mang}

total_guna: {milan_facts.get('total','?')} / {milan_facts.get('max',36)}
{mang}

ashtakoot_scores:
{chr(10).join(koot_lines)}
</PARTNER_KOOT_GRID>

{raw_marriage}

<ALLOWED_REMEDIES>
{', '.join(ALLOWED_REMEDIES)}
</ALLOWED_REMEDIES>

<USER_CONTEXT>
language: {lang}
</USER_CONTEXT>

{_lang_script_directive(lang)}

CRITICAL — verbatim "{milan_facts.get('total','?')} out of {milan_facts.get('max',36)}" SHOULD appear in `verdict` or `hidden_truth` (reader expectation).
OPTIONAL — when the operator enables ``COMPAT_PREMIUM_REMEDY_TAIL_VALIDATE``, end **ch4** and **ch7** `chapter_body` with one verbatim substring from <ALLOWED_REMEDIES> (the closing maps to the last PDF subsection); default lane allows natural closings.

Each chapter must include one non-empty `chapter_body` string: the entire chapter as continuous consultation prose (paragraph breaks as \\n\\n). Do not emit per-subsection keys — the server maps `chapter_body` into PDF blocks.

CRITICAL — **Balanced depth across all seven chapters:** every `chapter_body` (ch1…ch7) must be **long and deeply developed** — multi-paragraph, chart-led, both partners compared where relevant. It is unacceptable for one chapter to read like a full consultation while others read like brief notes; **even out depth** before you emit the JSON.

CRITICAL — **Pro PDF layout:** each chapter maps to **one A4 page** in the client PDF — short `chapter_body` text leaves awkward empty space. Write each chapter so the narrative **fills that page** with real chart-led consultation (many `\\n\\n` paragraphs and consultation-grade length), not thin summaries.

CRITICAL — **`special` (3 strings), `damage` (2 strings), `practical` (3 strings):** each array element must be
**consultation-grade multi-paragraph prose** (`\\n\\n` inside the string), with the same chart depth, both-kundli
comparison, and lived-life texture as your chapters — **not** short summary lines or bullet lists as the main format.
`damage` must contain **two** deep strings (not one). For `practical`, explicitly weave daily married dynamics
(home rhythm, in-laws/family, money roles, emotional labour, routines, communication habits, conflict/repair,
role balance) through **chart combinations** from <STRUCTURED_CHART_DATA>.

QUALITY BAR — Match **`marriage_blueprint` specificity** in `hidden_truth`, **ch5–ch7**, `verdict`, and in
`special` / `damage` / `practical`: **lived behaviours first** (who withdraws, who pursues closure, how fights
re-stack, how money or in-laws borrow bandwidth), with **named chart levers** (7th lord, Moon, Venus/Mars, D9 vs
D1, synastry, KP) woven into those scenes. Minimise generic “should / must understand / accept differences /
communicate better” advice in **every** language unless each line is visibly **earned** from the JSON you were given.

Emit JSON only."""


# Phase 2.5.11.24-fix: per-lang strong script directive injected into the
# user prompt. Without this, gpt-5-mini sometimes writes "hi" prose in
# Roman/Hinglish characters instead of Devanagari. Naming the target script
# in its own characters + giving a 2-3 word self-example forces the model
# to switch input mode to that Unicode block from the first token.
_LANG_SCRIPT_DIRECTIVE = {
    "hi": "देवनागरी",
}

def _lang_script_directive(lang: str) -> str:
    code = (lang or "en").lower()
    if code in ("en", "hn"):
        return ""
    script = _LANG_SCRIPT_DIRECTIVE.get(code)
    if not script:
        return ""
    return (
        f"CRITICAL SCRIPT LOCK — For `language`=hi, all narrative JSON strings must use "
        f"the {script} script (not Roman/Latin prose). Keep partner names, nakshatra/rashi "
        f"spellings, koot labels, remedy phrases, and numeric totals in Latin as given in "
        f"the data blocks."
    )


def _marriage_llm_facts_cache_token(marriage_llm_facts: dict | None) -> str:
    """Digest bundled marriage facts so cache keys change when RAW prompt payload changes."""
    if not isinstance(marriage_llm_facts, dict) or not marriage_llm_facts:
        return "mlf=none"
    try:
        blob = json.dumps(
            marriage_llm_facts,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )
    except Exception:
        blob = repr(marriage_llm_facts)
    return "mlf=" + hashlib.sha1(blob.encode("utf-8")).hexdigest()[:24]


def _fingerprint(
    milan_facts: dict,
    chapter_scores: dict,
    kp: dict,
    lang: str,
    model: str,
    marriage_llm_facts: dict | None = None,
) -> str:
    p1 = milan_facts.get("p1", {}) or {}
    p2 = milan_facts.get("p2", {}) or {}
    parts = [
        f"prem={_PREMIUM_VERSION}",
        f"model={model}",
        f"lang={lang}",
        p1.get("nakshatra", ""), str(p1.get("pada", "")), p1.get("rashi", ""),
        p2.get("nakshatra", ""), str(p2.get("pada", "")), p2.get("rashi", ""),
        f"total={milan_facts.get('total','')}",
        f"mdosh={milan_facts.get('manglik_dosh','')}",
    ]
    for k in milan_facts.get("koots", []) or []:
        parts.append(f"{k.get('key','')}={k.get('score','')}")
    chs = (chapter_scores or {}).get("chapters", {}) or {}
    for key in CHAPTER_KEYS:
        parts.append(f"{key}={chs.get(key, {}).get('score_0_10', '')}")
    parts.append(f"kp={(kp or {}).get('couple_verdict','')}")
    parts.append(_marriage_llm_facts_cache_token(marriage_llm_facts))
    raw = "|".join(parts).encode("utf-8")
    return "prem_" + hashlib.sha1(raw).hexdigest()


_PREMIUM_LATIN_LANGS = frozenset({"en", "hn"})
# Practical married-life blocks: allow long multi-paragraph consultation strings per lane.
_PRACTICAL_LEN_LATIN = (320, 4800)
_PRACTICAL_LEN_INDIC = (120, 4200)


def _premium_lang_code(lang: str | None) -> str:
    return normalize_pro_pdf_lang(lang)


def _practical_length_bounds(lang_code: str) -> tuple[int, int]:
    return _PRACTICAL_LEN_LATIN if lang_code in _PREMIUM_LATIN_LANGS else _PRACTICAL_LEN_INDIC


def _hidden_truth_bounds(lang_code: str) -> tuple[int, int]:
    """Unicode codepoint ceiling only — P58 floor is **word** count (hidden_truth)."""
    return (16, 5200)


def _verdict_bounds(lang_code: str) -> tuple[int, int]:
    """Unicode codepoint ceiling — P58 floor is **word** count (verdict)."""
    return (32, 5200)


def _chapter_field_bounds(lang_code: str, field: str) -> tuple[int, int]:
    """`full_read` upper bound on codepoints; P57 length gate is **word count**."""
    hi = _PREMIUM_FULL_READ_MAX_CP
    if field != CHAPTER_FULL_READ:
        return (0, hi)
    return (0, hi)


def _blueprint_field_bounds(lang_code: str, field: str) -> tuple[int, int]:
    hi = 5200
    if lang_code in _PREMIUM_LATIN_LANGS:
        return (120, hi)
    if field == "blueprint_takeaway":
        return (100, hi)
    return (120, hi)


def _truncate_pdf_safe_cp(text: Any, max_cp: int) -> str:
    """Strip NULs and clamp Unicode codepoints for ReportLab-safe strings."""
    s = "" if text is None else str(text)
    s = s.replace("\x00", "")
    if max_cp <= 0:
        return ""
    if len(s) <= max_cp:
        return s
    cut = s[:max_cp].rsplit(" ", 1)[0].strip()
    return cut if cut else s[:max_cp].strip()


def _sanitize_premium_parsed_dict_in_place(parsed: dict, lang: str) -> None:
    """In-place: coerce chart-backed LLM JSON to PDF-safe string bounds (no prose rejection)."""
    lc = _premium_lang_code(lang)
    _, ht_hi = _hidden_truth_bounds(lc)
    _, vd_hi = _verdict_bounds(lc)
    _, pr_hi = _practical_length_bounds(lc)
    mb_hi = 5200

    parsed["hidden_truth"] = _truncate_pdf_safe_cp(parsed.get("hidden_truth"), ht_hi)
    parsed["verdict"] = _truncate_pdf_safe_cp(parsed.get("verdict"), vd_hi)

    chs = parsed.get("chapters")
    if not isinstance(chs, list):
        parsed["chapters"] = []
        chs = parsed["chapters"]
    for c in chs:
        if not isinstance(c, dict):
            continue
        c["grounding"] = _truncate_pdf_safe_cp(c.get("grounding"), _PREMIUM_GROUNDING_MAX_CHARS)
        cb = str(c.get(CHAPTER_BODY_KEY) or "").strip()
        if not cb:
            cb = str(c.get(CHAPTER_FULL_READ) or "").strip()
        if cb:
            cb = _truncate_pdf_safe_cp(cb, _PREMIUM_CHAPTER_BODY_MAX_CP)
        c[CHAPTER_BODY_KEY] = cb
        c[CHAPTER_FULL_READ] = cb
        for sk in CHAPTER_SECTION_KEYS:
            c.pop(sk, None)

    sp = parsed.get("special")
    if not isinstance(sp, list):
        sp = []
    parsed["special"] = [_truncate_pdf_safe_cp(x, 3200) for x in sp[:8]]

    dm = parsed.get("damage")
    if not isinstance(dm, list):
        dm = []
    parsed["damage"] = [_truncate_pdf_safe_cp(x, 3600) for x in dm[:8]]

    pr = parsed.get("practical")
    if not isinstance(pr, list):
        pr = []
    parsed["practical"] = [_truncate_pdf_safe_cp(x, pr_hi) for x in pr[:8]]

    mb = parsed.get("marriage_blueprint")
    if not isinstance(mb, dict):
        mb = {}
    for fld in (
        "p1_marriage_nature",
        "p2_marriage_nature",
        "interaction_dynamic",
        "what_p1_needs_from_p2",
        "what_p2_needs_from_p1",
        "blueprint_takeaway",
    ):
        mb[fld] = _truncate_pdf_safe_cp(mb.get(fld), mb_hi)
    parsed["marriage_blueprint"] = mb


def _validate_premium(
    out: Any,
    milan_facts: dict,
    chapter_scores: dict,
    lang: str = "en",
) -> tuple[bool, str]:
    """Technical shim only: root must be a dict. Prose/shape/tone gates removed (see ``_sanitize_…``)."""
    _ = (milan_facts, chapter_scores, lang)
    if not isinstance(out, dict):
        return False, "not_dict"
    return True, "ok"


def _premium_env_flag(name: str, default: str = "0") -> bool:
    """True for 1 / true / yes / on; strips whitespace and outer quotes from .env."""
    raw = (os.environ.get(name) or default).strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        raw = raw[1:-1].strip()
    return raw.lower() in ("1", "true", "yes", "on")


def _premium_trace_on() -> bool:
    return _premium_env_flag("COMPAT_PREMIUM_TRACE", "0")


def _prem_trace_file_path() -> str:
    """`premium_chapters.py` lives in …/api-server/vedic/compat/."""
    compat_dir = os.path.dirname(os.path.abspath(__file__))
    api_server_root = os.path.dirname(os.path.dirname(compat_dir))
    return os.path.join(api_server_root, "_prem_trace_last_run.txt")


def _prem_trace_reset() -> None:
    if not _premium_trace_on():
        return
    try:
        with open(_prem_trace_file_path(), "w", encoding="utf-8") as fh:
            fh.write("")
    except Exception:
        pass


def _prem_trace(msg: str) -> None:
    if _premium_trace_on():
        line = f"[prem_trace] {msg}"
        print(line, flush=True)
        try:
            with open(_prem_trace_file_path(), "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except Exception:
            pass


def _trace_l2_headline(system_prompt: str) -> str:
    for line in (system_prompt or "").splitlines():
        s = line.strip()
        if "OUTPUT REGISTER" in s:
            return s[:220]
    return "(missing L2 OUTPUT REGISTER headline)"


def _trace_sample_has_indic(text: str) -> bool:
    """Devanagari detector (Pro PDF native lane is Hindi only)."""
    if not text:
        return False
    for ch in text[:8000]:
        o = ord(ch)
        if 0x0900 <= o <= 0x097F:
            return True
    return False


def _trace_gpt_ch1_full_read(parsed: dict) -> str:
    for c in parsed.get("chapters") or []:
        if isinstance(c, dict) and (c.get("key") or "").strip().lower() == "ch1":
            cb = str(c.get(CHAPTER_BODY_KEY) or "").strip()
            if cb:
                return cb[:400]
            if _chapter_has_structured_sections(c):
                return str(c.get("core_dynamic") or "")[:400]
            return str(c.get(CHAPTER_FULL_READ) or "")[:400]
    return ""


_JSON_RETRY_SYSTEM_SUFFIX = """

═══ STRICT JSON RETRY MODE (non-negotiable) ═══
Return STRICT valid JSON only: one root object, UTF-8, RFC 8259 compliant.
Every string must fully escape internal \\ and \". No raw line breaks inside strings (use \\n).
No markdown. No preamble or trailing text. Complete every key and string — parsers must succeed unchanged.
"""

_JSON_RETRY_USER_TAIL = (
    "\n\nRemind yourself: respond with STRICT valid JSON only — "
    "a single complete JSON object, fully quoted strings, no truncation."
)


def _premium_json_raw_preview(raw: str, head: int = 650, tail: int = 420) -> str:
    """Head + tail repr for logs when bodies are huge or truncated."""
    r = raw or ""
    if len(r) <= head + tail + 24:
        return repr(r)
    return repr(r[:head]) + " …… " + repr(r[-tail:])


def _strip_markdown_json_fence(raw: str) -> str:
    s = (raw or "").strip()
    sl = s.lower()
    if sl.startswith("```json"):
        s = s[7:].lstrip("\r\n")
    elif sl.startswith("```"):
        s = s[3:].lstrip("\r\n")
    s = s.strip()
    if s.endswith("```"):
        s = s[:-3].strip()
    return s


def _extract_balanced_json_object(s: str) -> str | None:
    """Isolate outermost `{...}` using JSON-ish string rules (ASCII `\"` delimiters)."""
    start = s.find("{")
    if start < 0:
        return None
    depth = 0
    i = start
    in_string = False
    escaped = False
    while i < len(s):
        ch = s[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            i += 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return s[start : i + 1]
        i += 1
    return None


def _parse_premium_llm_json(raw: str) -> tuple[dict | None, json.JSONDecodeError | None]:
    """Best-effort parse: raw → fenced strip → balanced `{...}` extraction."""
    r0 = (raw or "").strip()
    variants: list[str] = []
    if r0:
        variants.append(r0)
    fenced = _strip_markdown_json_fence(r0)
    if fenced and fenced not in variants:
        variants.append(fenced)
    extracted = _extract_balanced_json_object(fenced)
    if extracted and extracted not in variants:
        variants.append(extracted)
    extracted2 = _extract_balanced_json_object(r0)
    if extracted2 and extracted2 not in variants:
        variants.append(extracted2)

    last_err: json.JSONDecodeError | None = None
    seen: set[str] = set()
    for cand in variants:
        if not cand or cand in seen:
            continue
        seen.add(cand)
        try:
            obj = json.loads(cand)
            if isinstance(obj, dict):
                return obj, None
            last_err = json.JSONDecodeError("JSON root must be an object", cand, 0)
        except json.JSONDecodeError as exc:
            last_err = exc
    return None, last_err


def polish_premium_chapters(
    milan_facts: dict,
    chapter_scores: dict,
    d9_marriage: dict,
    synastry: dict,
    kp_promise: dict,
    lang: str = "en",
    marriage_llm_facts: dict | None = None,
) -> dict[str, Any]:
    """Premium gpt-4o polish for Kundli Milan Pro PDF.

    Returns a dict with:
      hidden_truth (str), chapters (list), special, damage, practical, verdict

    On polish-toggle-off, missing OpenAI, JSON parse failure, or unexpected errors,
    returns an **empty** ``pro_premium`` shell (no deterministic soul prose); the PDF
    renderer fills chapter pages from its own placeholders.

    **GPT-first (p79):** Successful OpenAI JSON is sanitized (NUL strip + PDF codepoint ceilings).
    Optional **lightweight chapter depth gate** (default on) may run **batched compact regen** calls
    before cache write; shallow cached payloads are treated as cache misses.

    Never raises.
    """
    model = os.environ.get("COMPAT_PREMIUM_MODEL", _DEFAULT_MODEL)
    _prem_trace_reset()
    lang = normalize_pro_pdf_lang(lang)
    lang_norm = lang
    _prem_trace(
        "polish_premium_chapters entry "
        f"lang_arg={lang!r} lang_normalized={lang_norm!r} "
        f"COMPAT_PREMIUM_POLISH={os.environ.get('COMPAT_PREMIUM_POLISH')!r} "
        f"COMPAT_PREMIUM_CACHE_DISABLE={os.environ.get('COMPAT_PREMIUM_CACHE_DISABLE')!r}"
    )
    if not _premium_env_flag("COMPAT_PREMIUM_POLISH", "0"):
        log.warning(
            "[premium_chapters] polish off COMPAT_PREMIUM_POLISH=%r → empty pro_premium shell",
            os.environ.get("COMPAT_PREMIUM_POLISH"),
        )
        print(
            "[premium_chapters] model=empty_shell reason=COMPAT_PREMIUM_POLISH_off",
            flush=True,
        )
        _prem_trace(
            "OUTCOME=empty_shell STEP=early_return "
            "REASON=COMPAT_PREMIUM_POLISH_off"
        )
        pg = stub_meta(
            model,
            final_status="SKIPPED_OPENAI_POLISH_OFF",
            fallback_used=False,
            openai_skipped=True,
            reason="COMPAT_PREMIUM_POLISH_off",
        )
        return _return_empty_polish_with_telemetry(pg)

    tel: PdfGenOpenAITelemetry | None = None
    try:
        key = _fingerprint(
            milan_facts,
            chapter_scores,
            kp_promise,
            lang,
            model,
            marriage_llm_facts=marriage_llm_facts,
        )

        # Testing: COMPAT_PREMIUM_CACHE_DISABLE=1 bypasses L1/L2 read/write.
        cache_off = _premium_env_flag("COMPAT_PREMIUM_CACHE_DISABLE")
        _prem_trace(
            f"cache probe fingerprint_sha1={key} cache_off={cache_off} "
            f"prem_version={_PREMIUM_VERSION}"
        )
        if not cache_off:
            hit = _l1_get(key)
            if (
                hit is not None
                and _premium_depth_regen_enabled()
                and not _premium_polish_cache_depth_ok(hit, milan_facts, lang_norm)
            ):
                log.info("[premium_chapters] L1 cache rejected (lightweight chapter or SDP depth)")
                print(
                    f"[premium_chapters] model={model} reason=L1_cache_depth_miss",
                    flush=True,
                )
                hit = None
            if hit is not None:
                log.info("[premium_chapters] L1 cache hit → skip LLM")
                print(
                    f"[premium_chapters] model={(hit.get('_meta') or {}).get('model')} "
                    "reason=L1_cache",
                    flush=True,
                )
                hm = hit.get("hidden_truth") or ""
                _prem_trace(
                    "OUTCOME=cache_hit L1 skip_openai "
                    f"_meta.model={(hit.get('_meta') or {}).get('model')!r} "
                    f"_meta.version={(hit.get('_meta') or {}).get('version')!r} "
                    f"sample_indic={_trace_sample_has_indic(str(hm))} "
                    f"hidden_preview={str(hm)[:200]!r}"
                )
                pg = stub_meta(
                    str((hit.get("_meta") or {}).get("model") or model),
                    final_status="CACHE_HIT_L1",
                    fallback_used=False,
                    openai_skipped=True,
                    cache_hit=True,
                )
                snap = (hit.get("_meta") or {}).get("pdf_generation")
                if isinstance(snap, dict):
                    pg["cached_pdf_generation"] = snap
                publish_and_log_pdf_generation(pg)
                hit_out = dict(hit)
                hit_out["_meta"] = dict(hit.get("_meta") or {})
                merge_pdf_generation_into_meta(hit_out["_meta"], pg)
                return hit_out
            db_hit = _l2_get(key)
            if (
                db_hit is not None
                and _premium_depth_regen_enabled()
                and not _premium_polish_cache_depth_ok(db_hit, milan_facts, lang_norm)
            ):
                log.info("[premium_chapters] L2 cache rejected (lightweight chapter or SDP depth)")
                print(
                    f"[premium_chapters] model={model} reason=L2_cache_depth_miss",
                    flush=True,
                )
                db_hit = None
            if db_hit is not None:
                log.info("[premium_chapters] L2 cache hit → skip LLM")
                _l1_put(key, db_hit)
                print(
                    f"[premium_chapters] model={(db_hit.get('_meta') or {}).get('model')} "
                    "reason=L2_cache",
                    flush=True,
                )
                dh = db_hit.get("hidden_truth") or ""
                _prem_trace(
                    "OUTCOME=cache_hit L2 skip_openai "
                    f"_meta.model={(db_hit.get('_meta') or {}).get('model')!r} "
                    f"_meta.version={(db_hit.get('_meta') or {}).get('version')!r} "
                    f"sample_indic={_trace_sample_has_indic(str(dh))} "
                    f"hidden_preview={str(dh)[:200]!r}"
                )
                pg = stub_meta(
                    str((db_hit.get("_meta") or {}).get("model") or model),
                    final_status="CACHE_HIT_L2",
                    fallback_used=False,
                    openai_skipped=True,
                    cache_hit=True,
                )
                snap = (db_hit.get("_meta") or {}).get("pdf_generation")
                if isinstance(snap, dict):
                    pg["cached_pdf_generation"] = snap
                publish_and_log_pdf_generation(pg)
                out = dict(db_hit)
                out["_meta"] = dict(db_hit.get("_meta") or {})
                merge_pdf_generation_into_meta(out["_meta"], pg)
                return out

        try:
            from openai_helper import _get_client  # type: ignore
        except Exception as exc:
            log.warning("[premium_chapters] openai import failed: %s", exc)
            print(
                "[premium_chapters] model=empty_shell reason=openai_import_fail",
                flush=True,
            )
            _prem_trace(
                "OUTCOME=empty_shell STEP=early_return REASON=openai_import_fail "
                f"exc={exc!r}"
            )
            pg = stub_meta(
                model,
                final_status="FALLBACK_OPENAI_IMPORT_FAIL",
                fallback_used=False,
                openai_skipped=True,
                reason="openai_import_fail",
            )
            return _return_empty_polish_with_telemetry(pg)
        client = _get_client()
        if client is None:
            log.warning(
                "[premium_chapters] _get_client() None → empty pro_premium shell "
                "(check OPENAI_API_KEY / proxy env)"
            )
            print(
                "[premium_chapters] model=empty_shell reason=openai_client_none",
                flush=True,
            )
            _prem_trace(
                "OUTCOME=empty_shell STEP=early_return REASON=openai_client_none"
            )
            pg = stub_meta(
                model,
                final_status="FALLBACK_OPENAI_CLIENT_NONE",
                fallback_used=False,
                openai_skipped=True,
                reason="openai_client_none",
            )
            return _return_empty_polish_with_telemetry(pg)

        tel = PdfGenOpenAITelemetry(model)
        log.info(
            "[premium_chapters] OpenAI request model=%s cache_off=%s",
            model,
            cache_off,
        )

        user_prompt = _build_user_prompt(
            milan_facts,
            chapter_scores,
            d9_marriage,
            synastry,
            kp_promise,
            lang,
            marriage_llm_facts=marriage_llm_facts,
        )
        regen_chart_cap = _regen_chart_json_cap()
        regen_user_prompt = _build_user_prompt(
            milan_facts,
            chapter_scores,
            d9_marriage,
            synastry,
            kp_promise,
            lang,
            marriage_llm_facts=marriage_llm_facts,
            chart_json_max_chars=regen_chart_cap,
        )
        regen_chapter_system = build_premium_regen_chapter_system_prompt(lang)

        system_prompt_content = build_premium_system_prompt(lang)
        _prem_trace(
            "build_premium_system_prompt "
            f"called_with_lang={lang!r} "
            f"system_chars={len(system_prompt_content)} "
            f"L2_line={_trace_l2_headline(system_prompt_content)!r}"
        )
        _prem_trace(
            "system_prompt_preview "
            f"{system_prompt_content[:520]!r}"
        )

        kwargs: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt_content},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            # Long JSON: seven deep chapter_body narratives + blueprint + bullets.
            # Default completion budget targets even depth across chapters; cap 16k.
            # Override with COMPAT_PREMIUM_MAX_TOKENS.
            "max_tokens": min(
                max(
                    _premium_env_int("COMPAT_PREMIUM_MAX_TOKENS", 16000),
                    15500 if model.lower().startswith("gpt-5") else 15000,
                ),
                16384,
            ),
        }
        if not model.lower().startswith("gpt-5"):
            kwargs["temperature"] = 0.55

        _oa_timeout = float(os.environ.get("COMPAT_PREMIUM_OPENAI_TIMEOUT", "240"))
        kwargs["timeout"] = _oa_timeout
        _prompt_chars = len(system_prompt_content) + len(user_prompt)
        _regen_chars = len(regen_chapter_system) + len(regen_user_prompt)
        _t_req = time.perf_counter()
        print(
            "[premium_chapters] OPENAI_REQUEST_START "
            f"model={model} timeout_s={_oa_timeout} "
            f"max_tokens={kwargs['max_tokens']} lang={lang!r} "
            f"prompt_total_chars={_prompt_chars} "
            f"regen_prompt_chars={_regen_chars} regen_chart_cap={regen_chart_cap!r}",
            flush=True,
        )
        try:
            resp = client.chat.completions.create(**kwargs)
        except Exception as _oa_exc:
            _elapsed_ms = int((time.perf_counter() - _t_req) * 1000)
            print(
                "[premium_chapters] OPENAI_REQUEST_FAIL "
                f"elapsed_ms={_elapsed_ms} err={type(_oa_exc).__name__}:{_oa_exc}",
                flush=True,
            )
            raise
        _elapsed_ms = int((time.perf_counter() - _t_req) * 1000)
        print(
            "[premium_chapters] OPENAI_RESPONSE_RECEIVED "
            f"elapsed_ms={_elapsed_ms}",
            flush=True,
        )
        tel.record(resp, "primary")
        raw = (resp.choices[0].message.content or "").strip()
        _prem_trace(
            "openai_response_raw "
            f"chars={len(raw)} "
            f"preview={raw[:650]!r}"
        )
        # Phase 2.5.11.24-fix: gpt-5-mini intermittently returns an empty
        # body (reasoning eats all tokens, or proxy hiccup). One immediate
        # retry recovers most cases; without it gu/or fall back to Hinglish.
        if not raw:
            print(
                "[premium_chapters] OPENAI_RETRY_EMPTY_BODY "
                "reason=first_completion_empty",
                flush=True,
            )
            _t_retry = time.perf_counter()
            try:
                resp = client.chat.completions.create(**kwargs)
            except Exception as exc:
                _retry_ms = int((time.perf_counter() - _t_retry) * 1000)
                print(
                    "[premium_chapters] OPENAI_REQUEST_FAIL "
                    f"elapsed_ms={_retry_ms} phase=retry_empty err="
                    f"{type(exc).__name__}:{exc}",
                    flush=True,
                )
                log.warning("[premium_chapters] retry failed: %s", exc)
            else:
                _retry_ms = int((time.perf_counter() - _t_retry) * 1000)
                print(
                    "[premium_chapters] OPENAI_RESPONSE_RECEIVED "
                    f"elapsed_ms={_retry_ms} phase=retry_empty",
                    flush=True,
                )
                tel.record(resp, "primary_empty_body_retry")
                raw = (resp.choices[0].message.content or "").strip()
                log.info(
                    "[premium_chapters] retry-on-empty: lang=%s raw_len=%s",
                    lang,
                    len(raw),
                )

        parsed, parse_err = _parse_premium_llm_json(raw)
        if parsed is None:
            _exc_s = repr(parse_err) if parse_err else "unknown"
            log.warning(
                "[premium_chapters] premium_json_parse_fail attempt=primary exc=%s "
                "raw_len=%s raw_preview=%s",
                _exc_s,
                len(raw or ""),
                _premium_json_raw_preview(raw),
            )
            print(
                f"[premium_chapters] OPENAI_JSON_PARSE_RETRY exc={_exc_s} "
                f"raw_len={len(raw or '')}",
                flush=True,
            )
            _prem_trace(
                "premium_json_parse_fail_primary "
                f"exc={_exc_s} preview={_premium_json_raw_preview(raw)}"
            )

            retry_kw = dict(kwargs)
            retry_kw["messages"] = [
                {
                    "role": "system",
                    "content": system_prompt_content + _JSON_RETRY_SYSTEM_SUFFIX,
                },
                {"role": "user", "content": user_prompt + _JSON_RETRY_USER_TAIL},
            ]
            _t_jr = time.perf_counter()
            print(
                "[premium_chapters] OPENAI_JSON_RETRY_REQUEST "
                f"timeout_s={_oa_timeout}",
                flush=True,
            )
            try:
                resp_retry = client.chat.completions.create(**retry_kw)
            except Exception as jr_exc:
                _jr_ms = int((time.perf_counter() - _t_jr) * 1000)
                log.warning(
                    "[premium_chapters] premium_json_retry_openai_fail "
                    "elapsed_ms=%s err=%s:%s",
                    _jr_ms,
                    type(jr_exc).__name__,
                    jr_exc,
                )
                print(
                    "[premium_chapters] model=empty_shell "
                    f"reason=json_retry_openai_fail:{type(jr_exc).__name__}",
                    flush=True,
                )
                _prem_trace(
                    "OUTCOME=empty_shell STEP=json_retry_openai "
                    f"REASON={jr_exc!r}"
                )
                pg = tel.build_meta(
                    fallback_used=False,
                    final_status="FALLBACK_JSON_RETRY_OPENAI_FAIL",
                    validator_attempts=0,
                    last_validator_reason=f"{type(jr_exc).__name__}:{jr_exc}",
                )
                return _return_empty_polish_with_telemetry(pg)

            _jr_ms = int((time.perf_counter() - _t_jr) * 1000)
            print(
                f"[premium_chapters] OPENAI_JSON_RETRY_RESPONSE elapsed_ms={_jr_ms}",
                flush=True,
            )
            tel.record(resp_retry, "json_retry")
            raw_retry = (resp_retry.choices[0].message.content or "").strip()
            parsed, parse_err2 = _parse_premium_llm_json(raw_retry)
            if parsed is None:
                _exc2 = repr(parse_err2) if parse_err2 else "unknown"
                log.warning(
                    "[premium_chapters] premium_json_parse_fail attempt=json_retry "
                    "exc=%s raw_len=%s raw_preview=%s",
                    _exc2,
                    len(raw_retry or ""),
                    _premium_json_raw_preview(raw_retry),
                )
                print(
                    "[premium_chapters] model=empty_shell "
                    f"reason=json_parse_fail_after_retry exc={_exc2}",
                    flush=True,
                )
                _prem_trace(
                    "OUTCOME=empty_shell STEP=json_parse_retry "
                    f"REASON={_exc2} preview={_premium_json_raw_preview(raw_retry)}"
                )
                pg = tel.build_meta(
                    fallback_used=False,
                    final_status="FALLBACK_JSON_PARSE_AFTER_RETRY",
                    validator_attempts=0,
                    last_validator_reason=_exc2,
                )
                return _return_empty_polish_with_telemetry(pg)

            log.info(
                "[premium_chapters] premium_json_parse_retry_ok lang=%s raw_len=%s",
                lang,
                len(raw_retry or ""),
            )
            print(
                "[premium_chapters] OPENAI_JSON_PARSE_RETRY_SUCCESS "
                f"lang={lang!r} raw_len={len(raw_retry or '')}",
                flush=True,
            )
            _prem_trace("premium_json_parse_retry_success")
            resp = resp_retry
            raw = raw_retry

        _finalize_chapter_narrative_for_pdf(parsed)
        _sanitize_premium_parsed_dict_in_place(parsed, lang)
        depth_meta: dict[str, Any] = {}
        if _premium_depth_regen_enabled():
            if not _premium_polish_payload_depth_complete(parsed, milan_facts, lang_norm):
                d_ok, depth_meta = _apply_depth_regen_to_parsed(
                    client=client,
                    tel=tel,
                    model=model,
                    lang=lang_norm,
                    milan_facts=milan_facts,
                    regen_system_base=regen_chapter_system,
                    regen_user_prompt=regen_user_prompt,
                    parsed=parsed,
                    oa_timeout=_oa_timeout,
                )
                if not d_ok:
                    exk = depth_meta.get("depth_regen_exhausted_key", "?")
                    log.warning(
                        "[premium_chapters] chapter depth regen exhausted key=%s meta=%s",
                        exk,
                        depth_meta,
                    )
                    print(
                        "[premium_chapters] model=empty_shell "
                        f"reason=depth_regen_exhausted key={exk}",
                        flush=True,
                    )
                    _prem_trace(
                        "OUTCOME=empty_shell STEP=depth_regen "
                        f"meta={depth_meta!r}"
                    )
                    pg = tel.build_meta(
                        fallback_used=False,
                        final_status="FALLBACK_DEPTH_REGEN_EXHAUSTED",
                        validator_attempts=sum(
                            1
                            for p in (tel.phases or [])
                            if p.get("phase") in ("depth_regen", "sdp_depth_regen")
                        ),
                        last_validator_reason=str(depth_meta)[:800],
                    )
                    return _return_empty_polish_with_telemetry(pg)
        _finalize_chapter_narrative_for_pdf(parsed)
        _sanitize_premium_parsed_dict_in_place(parsed, lang_norm)
        sdp_meta: dict[str, Any] = {}
        if not _premium_sdp_payload_depth_complete(parsed, milan_facts, lang_norm):
            sdp_ok, sdp_meta = _apply_sdp_depth_regen_to_parsed(
                client=client,
                tel=tel,
                model=model,
                lang=lang_norm,
                milan_facts=milan_facts,
                regen_user_prompt=regen_user_prompt,
                parsed=parsed,
                oa_timeout=_oa_timeout,
            )
            if not sdp_ok:
                log.warning(
                    "[premium_chapters] sdp narrative depth still shallow after regen "
                    "(PDF will still render): meta=%s",
                    sdp_meta,
                )
            _finalize_chapter_narrative_for_pdf(parsed)
            _sanitize_premium_parsed_dict_in_place(parsed, lang_norm)
        ok, reason = _validate_premium(parsed, milan_facts, chapter_scores, lang=lang)
        validator_attempts = sum(
            1
            for p in (tel.phases or [])
            if p.get("phase") in ("depth_regen", "sdp_depth_regen")
        )
        sdp_regen_calls = int((sdp_meta or {}).get("sdp_depth_regen_calls") or 0)
        monitor = False
        strict_pass_final = bool(ok)

        ht0 = str(parsed.get("hidden_truth") or "")
        k1p = _trace_gpt_ch1_full_read(parsed)
        combo = ht0 + " " + k1p
        _prem_trace(
            "post_parse_surface "
            f"validator_ok={strict_pass_final} validator_reason={reason!r} "
            f"validator_attempts={validator_attempts} "
            f"validator_monitor_mode={monitor} "
            f"gpt_hidden_truth_preview={ht0[:260]!r} "
            f"gpt_ch1_full_read_preview={k1p[:260]!r} "
            f"sample_indic_script_detected={_trace_sample_has_indic(combo)} "
            f"lang_requested={lang_norm!r}"
        )

        # Inject engine-derived score into each chapter (LLM never produced it).
        chs_in = parsed.get("chapters", [])
        chs_engine = (chapter_scores or {}).get("chapters", {})
        chapters_clean = []
        for c in chs_in:
            ckey = c.get("key")
            engine = chs_engine.get(ckey, {})
            row: dict[str, Any] = {
                "key": ckey,
                "title": engine.get("title", ckey),
                "score_0_10": engine.get("score_0_10"),
                "grounding": str(c.get("grounding", "")).strip(),
            }
            nar = str(c.get(CHAPTER_BODY_KEY) or "").strip() or str(c.get(CHAPTER_FULL_READ) or "").strip()
            row[CHAPTER_BODY_KEY] = nar
            row[CHAPTER_FULL_READ] = nar
            chapters_clean.append(row)

        # Marriage blueprint (Phase soul-v3) — clean copy with str coercion.
        mb_in = parsed.get("marriage_blueprint") or {}
        marriage_blueprint = {
            "p1_marriage_nature":    str(mb_in.get("p1_marriage_nature", "")).strip(),
            "p2_marriage_nature":    str(mb_in.get("p2_marriage_nature", "")).strip(),
            "interaction_dynamic":   str(mb_in.get("interaction_dynamic", "")).strip(),
            "what_p1_needs_from_p2": str(mb_in.get("what_p1_needs_from_p2", "")).strip(),
            "what_p2_needs_from_p1": str(mb_in.get("what_p2_needs_from_p1", "")).strip(),
            "blueprint_takeaway":    str(mb_in.get("blueprint_takeaway", "")).strip(),
        }
        polished = {
            "hidden_truth": str(parsed.get("hidden_truth", "")).strip(),
            "chapters": chapters_clean,
            "special": [str(s).strip() for s in parsed.get("special", [])],
            "damage": [str(s).strip() for s in parsed.get("damage", [])],
            "practical": [str(s).strip() for s in parsed.get("practical", [])],
            "verdict": str(parsed.get("verdict", "")).strip(),
            "marriage_blueprint": marriage_blueprint,
            "_meta": {
                "model": model,
                "version": _PREMIUM_VERSION,
                "overall_avg": (chapter_scores or {}).get("overall_avg_0_10"),
                "kp_promise": _kp_couple_band(kp_promise),
                "hidden_signature": _kp_signature_line(kp_promise),
                "cache_disabled": cache_off,
                "validator_passed": strict_pass_final,
                "validator_monitor_mode": monitor,
                "validator_reason": reason,
                "validator_attempts": validator_attempts,
                "narrative_words": _premium_narrative_word_count(parsed),
                "depth_regen_calls": int((depth_meta or {}).get("depth_regen_calls") or 0),
                "depth_regen_keys_touched": (depth_meta or {}).get("depth_regen_keys_touched") or [],
                "depth_regen_shallow_keys_after": (depth_meta or {}).get(
                    "depth_regen_shallow_keys_after"
                )
                or [],
                "depth_regen_api_calls": sum(
                    1 for p in (tel.phases or []) if p.get("phase") == "depth_regen"
                ),
                "sdp_depth_regen_calls": sdp_regen_calls,
                "sdp_depth_ok": _premium_sdp_payload_depth_complete(parsed, milan_facts, lang_norm),
            },
        }
        _pdf_final_status = "SUCCESS"
        pg_ok = tel.build_meta(
            fallback_used=False,
            final_status=_pdf_final_status,
            validator_attempts=validator_attempts,
            last_validator_reason=str(reason)[:800],
            pdf_render_status="RENDER_PENDING",
        )
        merge_pdf_generation_into_meta(polished["_meta"], pg_ok)
        publish_and_log_pdf_generation(pg_ok)
        cache_ok = True
        if cache_ok and not cache_off:
            _l1_put(key, polished)
            _l2_put(key, polished, model)
        print(
            f"[premium_chapters] model={model} validator_strict_pass={1 if strict_pass_final else 0} "
            f"validator_monitor={1 if monitor else 0} cache_write={1 if cache_ok and not cache_off else 0} "
            f"attempts={validator_attempts}",
            flush=True,
        )
        ph = polished.get("hidden_truth") or ""
        _prem_trace(
            "OUTCOME=gpt_polish_accepted "
            f"_meta.model={polished.get('_meta', {}).get('model')!r} "
            f"_meta.version={polished.get('_meta', {}).get('version')!r} "
            f"final_hidden_preview={str(ph)[:220]!r} "
            f"final_sample_indic={_trace_sample_has_indic(str(ph))}"
        )
        try:
            from vedic.compat.milan_chart_facts import enrich_milan_bundle_for_pdf
            from vedic.compat.milan_premium_validate import apply_milan_premium_validation

            _val_bundle = enrich_milan_bundle_for_pdf(
                {
                    **milan_facts,
                    "chapter_scores": chapter_scores,
                    "d9_marriage": d9_marriage,
                    "synastry_7l": synastry,
                    "kp_couple_promise": kp_promise,
                },
                lang=lang_norm,
            )
            apply_milan_premium_validation(polished, _val_bundle, lang_norm)
        except Exception as _val_exc:
            log.warning("[premium_chapters] milan_premium_validate skipped: %s", _val_exc)
        return polished

    except Exception as exc:
        log.exception("[premium_chapters] unexpected failure, returning empty shell: %s", exc)
        print(
            f"[premium_chapters] model=empty_shell reason=exception:{type(exc).__name__}",
            flush=True,
        )
        _prem_trace(
            f"OUTCOME=empty_shell STEP=exception exc_type={type(exc).__name__!r} "
            f"exc_preview={str(exc)[:240]!r}"
        )
        if tel is not None:
            try:
                pgx = tel.build_meta(
                    fallback_used=False,
                    final_status=f"FALLBACK_EXCEPTION_{type(exc).__name__}",
                    validator_attempts=0,
                    last_validator_reason=str(exc)[:800],
                )
                return _return_empty_polish_with_telemetry(pgx)
            except Exception:
                log.exception("[premium_chapters] pdf_generation telemetry publish failed")
        pgx = stub_meta(
            model,
            final_status=f"FALLBACK_EXCEPTION_{type(exc).__name__}",
            fallback_used=False,
            openai_skipped=False,
            reason=str(exc)[:400],
        )
        return _return_empty_polish_with_telemetry(pgx)


# ─────────────────────────────────────────────────────────────────────────
#  SOUL FALLBACK (Phase 2.5.11.23-soul, May 8 2026)
# ─────────────────────────────────────────────────────────────────────────
#  Critique: the previous fallback dumped engine drivers verbatim and
#  emitted template phrases ("engine drivers are stable", "No significant
#  friction detected", "Based on engine score X/10"). That made the PDF
#  read like an audit report, not a relationship insight. The replacement
#  below produces 3-layer prose for every chapter:
#    Layer 1 (kya_dikh):   quiet emotional observation (witness tone)
#    Layer 2 (kya_matlab): day-to-day married-life manifestation
#    Layer 3 (kya_dhyan):  long-term emotional consequence (remedy clause only ch4+ch7)
#  Each block is ≥3 sentences, name-anchored, and band-aware (HIGH/MID/LOW).
#  No engine vocab, no template phrases, no negative-detection lines.
# ─────────────────────────────────────────────────────────────────────────

def _band(score: float | None) -> str:
    """Score → narrative band. ≥7 HIGH · 4–6.9 MID · <4 LOW · None MID."""
    try:
        s = float(score) if score is not None else 5.0
    except Exception:
        s = 5.0
    if s >= 7.0: return "HIGH"
    if s >= 4.0: return "MID"
    return "LOW"


# Per-chapter soul library: (kya_dikh, kya_matlab, kya_dhyan) per band.
# Tone May 2026: observational marriage realism — asymmetry, resentment timing,
# avoidance — not wellness homework. ch4 + ch7 `kya_dhyan` may reference conservative
# remedies from ALLOWED_REMEDIES when narrative fits (optional strict verbatim tail: env).
_CH_SOUL: dict[str, dict[str, dict[str, str]]] = {
    "ch1": {
        "HIGH": {
            "kya_dikh":   "Pyaar yahaan loud nahi hai — emotional language ek background hum ki tarah baji rehti hai. {p1} aur {p2} ke andar same emotion alag delivery times pe surface karta hai: kuch face pe pehle, kuch andar baad me. Same pyaar, do delivery rhythms. Jab thakaan zyada hoti hai tab ye chhota gap suddenly bada feel hota hai aur naam diye bina misunderstanding ban jaata hai.",
            "kya_matlab": "Real life me iska shape aisa hai — Sunday raat ko, jab dono thake hain, ek koi chhoti baat bolega aur dusra silent rahega. Silent waala 'naraz' nahi hai, woh actually andar feeling sort kar raha hai. Lekin bolne wala us silence ko reject samajh sakta hai. Ye misunderstanding fight nahi banti — ye dheere se distance banti hai jo agle din tak rehti hai.",
            "kya_dhyan":  "Jab gap barhta hai, problem kam emotion aur zyada timing hoti hai — ek bolne ke mood me hota hai jab dusra abhi andar sort kar raha hota hai; dono apni jagah reasonable lagte hain, phir bhi ek dusre ko 'cold' label ho jaata hai. Meri practice me yahi mismatch aksar 'napasand' ban ke save ho jaata hai — asli picture staggered nervous-system ki hai. Pattern yahi repeat hota hai jab thakaan peak pe ho.",
        },
        "MID": {
            "kya_dikh":   "Imagine 9 baje ki chai, dono sofa pe, ek bole 'main theek hoon' aur baat khatm. {p1} ke liye yeh line literal hoti hai — sach me theek hai. {p2} ke liye wahi line ka matlab hota hai 'mujhe gently dobara poochho.' Ye sirf style nahi hai — ye childhood me kaise express karna seekha tha uska imprint hai, aur dono apni truth me sahi hain.",
            "kya_matlab": "Iska matlab — ek partner zyada bar 'main thik hoon' suntega aur bharosa kar lega; dusre ko lagega 'tujhe parwah hi nahi ki main andar kya feel kar raha hoon.' Distance yahaan gusse se nahi banti, ek kaafi-na-poochhne aur ek zyada-poochhne ke loop se banti hai. Reassurance dono ko chahiye, bas alag languages me.",
            "kya_dhyan":  "'Main theek hoon' yahan do alag dialects me bola jaata hai — ek literal refuge, ek masked doorway; jab dialect ko universal maan liya jaata hai, same sentence ek ko closure lagti hai aur dusre ko neglect. Awkward affection kabhi isi sentence ke peeche chipka rehta hai — pyaar hai, par delivery itni flat hai ki dusra insulted feel karta hai. Yahi is rishte ka quietly uncomfortable sach hai.",
        },
        "LOW": {
            "kya_dikh":   "Sabse purane silent friction-points emotional speed se start hote hain, topic se nahi. {p1} aur {p2} ke andar do alag emotional clocks chal rahe hain — kabhi {p1} intense aur immediate hota hai (feeling aayi, abhi baat karni hai), kabhi {p2} delayed processor jo ek upset moment ko 12 ghante andar baith ke samajhta hai. Ye personality hai, dosh nahi — but jab tak naam nahi diya jaata, dono apni speed ko 'sahi' aur dusre ki ko 'galat' samajhte rehte hain.",
            "kya_matlab": "Roz ke jeevan me iska matlab — fast processor ko lagta hai 'tu avoid kar raha hai, tujhe parwah nahi'; slow processor ko lagta hai 'tu emotional pressure daal raha hai, mujhe saans lene de.' Dono apni jagah pe sahi hain, aur dono ek dusre ko 'galat' label kar dete hain. Ye sabse common silent friction-zone hai shaadi ke pehle 5 saalon me.",
            "kya_dhyan":  "Jab dono speed ko morality banate hain, fight ka headline kabhi woh hota hai jo actually hurt kar raha tha — delayed timing, overloaded silence, ya premature confrontation. 30 minute ka pause sirf tab kaam karta hai jab wapas aana routine hai; warna woh bhi avoidance ban jaata hai. Emotional speed trait hai, trophy fight nahi; jab tak ye samajh anonymous lagti hai, asli baat table pe nahi aati.",
        },
    },
    "ch2": {
        "HIGH": {
            "kya_dikh":   "{p1} aur {p2} ke beech jo trust hai, woh declarations se nahi banti — chhoti consistencies se banti hai jo dono ne ek dusre ko time ke saath di hain. Ek partner shayad zyada explicitly bolta hai 'I trust you', dusra silently dikhata hai — bina poochhe access dena, bina justify kiye decisions quietly back karna. Dono trust express kar rahe hain, bas alag volumes pe.",
            "kya_matlab": "Real life me iska faayda — bahut shaadiyan jis 'kya woh sach me reliable hai?' wale doubt me energy waste karti hain, woh sawaal tum dono ke beech almost background me hai. Lekin ek subtle risk hai — jab trust strong ho, log usse 'taken-for-granted' bhi treat karne lagte hain. Wahi point pe rishton me dheere se gap banta hai.",
            "kya_dhyan":  "Trust yahan slogan kam, repeat-pattern zyada hai — kis din follow-through dikha, kis din gayab ho gaye; jo partner kam bolta hai woh kabhi effort kam nahi kar raha hota, bas visibility kam hoti hai. Jab yeh uneven lagta hai, chhoti baatein bhi trial ban jaati hain — unfair, par predictable. Same scene repeats jab assumed reliability ko checking replace kar deti hai.",
        },
        "MID": {
            "kya_dikh":   "{p1} aur {p2} ke beech trust solid hai, lekin uske kuch specific test-points hain jo abhi tak seedhe naam se tie nahi hue. Ek partner ke liye trust = har plan ka detail milna; dusre ke liye trust = kuch cheezein wallet jaise rakhne ka haq. Dono frameworks valid hain, lekin same word 'trust' do alag definitions chhupa raha hai.",
            "kya_matlab": "Day-to-day me ye gap aise dikhega — ek partner ka akele plan banana, ya phone alag rakhna, ya ek doston ka group jisme dusra involved nahi hai — innocent autonomy hai un ke liye, aur thoda 'concerning' lagta hai dusre ke liye. Conflict yahaan loyalty ke baare me nahi hota, definition ke baare me hota hai. Aur jab tak yeh map spoken nahi, dono apni assumptions ke andar hurt hote rehte hain.",
            "kya_dhyan":  "Trust-tests kabhi conscious nahi hote — ek late message, ek gate-close timing, ek forgot-to-tell; innocent ho sakta hai, par purani jakdan par scrape lagta hai. Jab ek partner bar-bar explain karna thak jaata hai aur dusra bar-bar poochhna, silent resentment pile ho jaati hai — uncomfortable truth yeh hai ki dono fatigue real hai.",
        },
        "LOW": {
            "kya_dikh":   "{p1} aur {p2} ke beech jo trust banana hai, usme dono apne pichle anubhav saath laaye hain — apne family me dekhe gaye patterns, ya ek pichla rishta jismein bharosa toota tha. Ek partner shayad apni kahaani zyada bol ke dikhta hai; dusra quietly weight uthaye ghoomta hai bina headline diye. Ye ek hidden weight hai jo abhi tak seedha table pe nahi aaya.",
            "kya_matlab": "Iska practical impact roz dikhega — chhoti baatein bhi pehle scrutiny se gujarengi. Ek partner ka late aana, message late karna, plan badalna — innocent things bhi 'iske peeche kya wajah hai?' wala question silently trigger karengi. Aur jo poochhta hai, woh khud thak jaata hai poochhne se; jo poochha jaata hai, woh thak jaata hai justify karne se. Loop dono ko hara deta hai.",
            "kya_dhyan":  "Predictability yahan romance kam, damage-control zyada hai — late hone se pehle ek line, plan badalne se pehle ek heads-up; boring lagta hai, par worry-loop chhota rehta hai. gratitude practice ko mechanical mat samajhna — roz sirf ek minute yeh notice karna ki kis micro-moment pe body calm hui; woh chhoti noticing kabhi tension quietly tod deti hai.",
        },
    },
    "ch3": {
        "HIGH": {
            "kya_dikh":   "Is rishte ki sabse rare quality conflict ke time pe dikhti hai — issue ek third entity ban jaata hai jise {p1} aur {p2} milke dekh rahe hote hain, ek dusre ke against nahi. Defensive flash kabhi-kabhi aata hai aur soften ho jaata hai; final destination repair hai, attack nahi. Calmness ka matlab unaffected nahi — sirf processing alag jagah ho rahi hai.",
            "kya_matlab": "Real life me iska faayda — bade decisions (career change, city change, parenting timing) pe dono ek table pe baith sakte ho bina personal attack ke. Aur ek aur baat: jo calm dikhta hai woh actually argument ke 4 ghante baad bhi mind me conversation re-run kar raha hota hai. Calmness ka matlab unaffected nahi hai — sirf processing alag jagah ho rahi hai.",
            "kya_dhyan":  "Strength ka paradox — jab life overload ho, yahi calm sabse pehle rude lagne lagta hai; ek ko lagta hai stone-wall, dusre ko lagta hai self-preservation. Raat ko thake hue mind me locked decisions silent resentment bank karte hain — uncomfortable par common. Sunday morning walk jaise chhoti jagah jahan sirf pace dikhti hai, topic baad me aata hai.",
        },
        "MID": {
            "kya_dikh":   "Zyadatar arguments {p1} aur {p2} ke beech topic pe nahi, pace pe shuru hote hain. Kabhi {p1} 'abhi resolve karo' camp me hota hai — issues ko pending nahi rakh sakta, raat bhar weight uthata rehta hai. Kabhi {p2} 'pehle thanda hone do, kal subah baat' camp me — fresh head se baat karne ki adat hai. Real topic side me chhoot jaata hai aur fight pace pe ho jaati hai.",
            "kya_matlab": "Aam jhagde isi clash se start hote hain — 'tu avoid kar raha hai' bolne wala, aur 'tu pressure daal raha hai' sunne wala. Real topic side me chhoot jaata hai aur fight pace pe ho jaati hai. Funny baat — har fight ke baad dono apne friend ko kahenge 'argument was about X', actually X kabhi address hi nahi hua. Ye pattern jab tak dikha nahi jaata, ye repeat hota rehta hai.",
            "kya_dhyan":  "Peak anger me jo jawab turant diya jaata hai woh aksar purani disrespect ka repeat lagta hai — naya topic sirf cover hai. Cool-down deadline tabhi readable hai jab wapas aana shame-free ho; warna dusra avoidance register kar leta hai. Ghar ki friction ka zyada hissa pace mismatch se aata hai — chup-chap, baar-baar.",
        },
        "LOW": {
            "kya_dikh":   "Wahi Tuesday raat, wahi bartan, wahi line — fight ka topic surface pe naya lagta hai, andar same purana hurt khada hai jo {p1} aur {p2} ne abhi tak naam nahi diya. Shayad 'main hamesha akela sambhalta hoon' ka hurt, ya 'mujhe sach me suna nahi jaata' ka quiet resignation. Jab tak woh underground feeling label nahi hoti, fight surface pe roz dohrayi jaati hai.",
            "kya_matlab": "Iska matlab — fight 'jeetne' se raahat nahi aati, kyunki jeeti hui baat woh nahi thi jo actually hurt kar rahi thi. Ek partner ko lagega 'main har baar effort dikhata hoon, fir bhi enough nahi hota'; dusre ko lagega 'mujhe meri reasons sunne ka mauka hi nahi milta.' Dono apni truth me sahi hain. Lekin same shape ki fight 4 baar repeat hoti hai — woh signal hai ki real conversation kabhi hui hi nahi.",
            "kya_dhyan":  "Teen baar same silhouette wali fight = underground hurt abhi bhi unnamed hai; jawab awkward hoga aur headline se mismatch karega — isliye kabhi kabhi bahar ki framing zaroori lagti hai. consult a qualified Jyotishi sirf isliye ki timing/decision-frame ko third voice mile — neutral, non-performative. Pattern ka uncomfortable truth: tum log topic badal rahe ho, wound same hai.",
        },
    },
    "ch4": {
        "HIGH": {
            "kya_dikh":   "{p1} aur {p2} ke beech ek 'long-haul' instinct natural hai — dono unconsciously is bond ko temporary nahi maante. Commitment ek decision nahi hai, ek default state hai, jaise neend. Lekin ek baat dhyaan dene wali — ek partner shayad zyada seedha future ki baat karta hai (5 saal baad ghar, kids, retirement); dusra silently us future me khud ko dekh raha hai bina headline ke. Dono ka commitment same hai, declaration ka style alag.",
            "kya_matlab": "Real life me — bade structural decisions (ghar, career compromises, parenting timing) pe dono mostly same direction me feel karte hain. Crisis bhi 'shall we still be us' wala existential sawaal trigger nahi karta. Lekin jo silent waala hai — uska commitment dekhne ke liye, words mat dhundo, decisions dhundo. Woh apni har choice me tum dono ke 'us' ko already include kar raha hota hai.",
            "kya_dhyan":  "Long-haul me sabse unsettling lagta hai jab ek partner ka silence mature lagta hai aur dusre ko neglect — kabhi woh sirf different announcement-speed hai. Bade decision se pehle 5-minute joint silence awkward hai par ek chhoti pause ban jaati hai — bolne se pehle breath. joint daily prayers — chaar minute literal saath — kabhi is mismatch ko measurable kar dete hain jahan explanations fail ho jaate hain.",
        },
        "MID": {
            "kya_dikh":   "{p1} aur {p2} ke beech bond serious hai, lekin life-stage transitions (job change, parenting, parents' health crisis, financial stress) is bond ko test karenge. Ek partner shayad change ko pehle body-language me le leta hai; dusra change ke andar bhi continuity dhundta hai. Jab life shift hoti hai, ek partner naturally adjust karta hai aur dusra thoda lambit reh jaata hai — aur woh lag yahaan friction banta hai, change me nahi.",
            "kya_matlab": "Iska matlab — agar dono 'hamesha aisi hi rahegi shaadi' wali expectation rakhenge, har transition pe shock lagega. Real stability adjust karne ki capacity me hai, sthir rehne me nahi. Aur ek bittersweet sach — jo couples 5 saal baad survive karte hain, woh same couples nahi hote jo ek dusre se shaadi karte time the. Evolution kabhi optional nahi hota; sirf together evolve karna ya alag-alag, woh choice hoti hai.",
            "kya_dhyan":  "Transition pe jo lambit partner hai woh lazy nahi — kabhi overload me freeze hota hai; jo fast mover hai woh controlling nahi — kabhi anxiety loud hoti hai. Dono labels galat hain, par ghar me circulate ho jaate hain. joint daily prayers turbulent week me sirf ek fixed minute ban jaate hain — performance nahi, repetition — aur repetition kabhi softness ko quietly restore kar deta hai.",
        },
        "LOW": {
            "kya_dikh":   "{p1} aur {p2} ke beech jo bond hai, usme ek specific adjustment dono ko shuruat me resist hota hai — aur wahi adjustment long-term stability ka actual key hai. Ye 'ek cheez' har couple ke liye alag — kabhi work-life balance, kabhi family boundaries, kabhi emotional bandwidth. Dono ke andar ek voice hai jo bolti hai 'mera tarika sahi hai', aur jab tak woh voice softer nahi hoti, woh ek cheez baar baar surface pe aati rahegi.",
            "kya_matlab": "Real life me iska matlab — agar dono apni 'mera tarika' position pe atke rahe, friction har 3 mahine me ek baar major fight ban ke phootegi. Practical compromise zaroori dikhta hai tab jab dono ko apni dignity scrape hoti feel ho — isliye resist hota hai. Wahi scrape kabhi kabhi sabse seedha sach bol deta hai — healing slogan nahi, seedhi baat.",
            "kya_dhyan":  "Same-shaped fight ka ek pattern pakdo jo har baar repeat ho; trusted elder ya mediator sirf frame dete hain, sermon nahi. joint daily prayers yahan religion kam, synchronized breathing zyada hai — ek hi minute me dono ko paas laana jab words poison ho chuke hon. Drift silently tab grow karti hai jab mismatch ko hero-banaya jaata hai aur labour invisible rehta hai.",
        },
    },
    "ch5": {
        "HIGH": {
            "kya_dikh":   "Kuch chemistries time ke saath fade hoti hain; kuch deeper layer se khinchti hain, novelty se nahi. {p1} aur {p2} ke beech jo pull hai woh dusra type hai — physical aur emotional dono surface se jude. Kabhi {p1} ke liye chemistry zyada physical dimension me jeeti hai, kabhi {p2} ke liye zyada emotional safety me. Dono real hain, aur dono ek dusre ke without missing rehte hain.",
            "kya_matlab": "Real life me — long-distance phases, busy career years, parenting years me bhi connection survive karega. Touch, eye-contact, shared humor — easy aur consistent rahenge. Lekin ek subtle sach — jab life sabse busy hoti hai, ye chemistry pehli cheez hoti hai jo silently sideline ho jaati hai, kyunki dono assume kar lete hain ki 'ye to natural hai, ye nahi jaayegi.' Aur woh assumption hi sabse mehngi padti hai.",
            "kya_dhyan":  "Busy season me chemistry kabhi die nahi hoti — sirf dheere-dheere side pe chali jaati hai; jo partner zyada touch se regulate hota hai use shutdown dikhta hai, jo words se regulate hota hai use neglect. Same week me dono right feel kar sakte hain — phir bhi ek dusre ko wrong lag sakta hai. Pattern yahi hai jab novelty khatm ho chuki ho aur habit abhi sync nahi hui.",
        },
        "MID": {
            "kya_dikh":   "Connection real hai, lekin intimacy ki languages alag hain. {p1} ke liye intimacy = words, presence, baat-cheet ka time. {p2} ke liye intimacy = touch, action, silent saath. Dono valid hain — lekin jab ek apni language me dikhata hai, dusri language me woh translate nahi hota, aur 'enough' nahi feel hota dono ko.",
            "kya_matlab": "Iska matlab — kabhi-kabhi ek partner ko lagega 'isme woh feeling nahi hai jaisi hona chahiye'. Lekin partner is showing it — bas tumhari language me nahi, apni language me. Ye gap silently bahut shaadiyan distance me dhakelta hai. Naam diye bina ye nazar bhi nahi aata — dono apni wajah se hurt mehsoos karte hain bina samjhe ki dusra actually showing up hai.",
            "kya_dhyan":  "Yahan hurt ironic hota hai — dono 'present' hain, par ek dusre ke channel par tuned nahi; awkward affection isi gap me rehta hai jahan kiss formal lagta hai aur baat bhi formal. Calendar blocks kabhi is mismatch ko fix nahi karte, sirf schedule kar dete hain — uncomfortable truth yeh hai ki translation miss hone par effort bhi insult lag sakta hai.",
        },
        "LOW": {
            "kya_dikh":   "Bahut couples ke liye natural chemistry instant nahi hoti — woh waqt aur safety ke saath build hoti hai. {p1} aur {p2} abhi wahi build-up ke phase me hain. Kabhi {p1} isse 'mismatch' samajh ke internalize karta hai ki 'kuch galat hai humme'; kabhi {p2} zyada practical — 'theek hai, kaam karenge isko.' Dono interpretations dono ko weight de rahi hain.",
            "kya_matlab": "Real life me — agar dono assume karenge ki 'should be natural', frustration silently build hoga. Pressure chemistry ko kill karta hai — performance-expectation me body shrink ho jaati hai jab tak safe feeling clear nahi. Social feed ka comparison yahan poison hai kyunki wahan sirf best moments dikhte hain; real pull kabhi awkward aur slow start hoti hai.",
            "kya_dhyan":  "Yahan sabse uncomfortable observation simple hai — mismatch kabhi desire kam hone ka proof nahi hota, kabhi nervous-system timing ka proof hota hai. consult a qualified Jyotishi timing/decision-frame ke liye alag baat hai; chemistry yahan emotional safety se judi hoti hai. Jab shame naam ho jaata hai, awkward weeks kam theatrical lagte hain — bas kam readable.",
        },
    },
    "ch6": {
        "HIGH": {
            "kya_dikh":   "{p1} aur {p2} ke beech jo daily-life partnership hai, woh quietly efficient hai. Dono naturally apna apna lane samajhte hain — kaun kya sambhalta hai, kab haath badhana hai, kab peeche hatna hai. Family dynamics me bhi dono ek dusre ki side me khade dikhte hain. Lekin dekho — ek partner shayad zyada visible labor karta hai (jo dikhta hai), dusra zyada invisible labor (mental load, planning, remembering). Dono ke contributions equal hain, sirf visibility alag hai.",
            "kya_matlab": "Real life me iska faayda — chhoti chizein (bills, schedules, household, in-laws) silent rehti hain, energy bachi rehti hai bigger things ke liye. Ye couples ka 'silent superpower' hai. Lekin ek hidden risk — invisible labor karne wala dheere thakega, aur uski thakaan dikhegi nahi jab tak woh bahut baad me bahar nahi aati ek unexpected outburst ke shape me. Acknowledgment yahaan trust se zyada important hai.",
            "kya_dhyan":  "Invisible labour ka drama kam hota hai kyunki proof collect nahi hota — sirf thakaan collect hoti hai. Jo partner planning carry karta hai use lagta hai 'main hi dekh raha hoon'; jo execution carry karta hai use lagta hai 'main hi kar raha hoon' — dono partially true. Uneven emotional labour yahi silently split hoti hai jab tak baat spoken nahi. Same scene repeats jab thank-you absent ho aur exhaustion present ho.",
        },
        "MID": {
            "kya_dikh":   "{p1} aur {p2} ke beech daily life smoothly chal sakti hai, lekin family expectations dono pe alag pressure dalti hain. Dono apne parivaar ki rhythms se aaye hain — gift-giving, festival celebrating, parents ko visit karne ki frequency, even chhoti baatein jaise 'kaun kisko phone karta hai pehle'. Dono ke ghar me normal alag tha. Aur jab tak woh 'normal' explicitly compare nahi hota, dono assume karte hain ki dusra unka normal samajhta hai.",
            "kya_matlab": "Iska matlab — shaadi sirf tum dono ke beech nahi hoti, do families ke beech hoti hai. Jo expectations spoken nahi hain, woh built-in disappointment banti hain. Aur ek subtle baat — ek partner shayad apne family ke saath zyada loyalty feel karta hai (kyunki woh emotional anchor hai), dusra apni family se thoda distance pasand karta hai (kyunki freedom anchor hai). Dono valid, dono ek dusre ke truth ko 'cold' ya 'enmeshed' label kar dete hain.",
            "kya_dhyan":  "Family calendar pe jo events dikhte hain unke peeche prestige aur guilt dono hide ho sakte hain — ek partner ke liye attendance proof hai, dusre ke liye trap. Boundary yahan moral lecture kam, logistics zyada hai: kaun kis side ka sentence bolega, kab nahi. Jab yeh map unnamed rehta hai, festivals bhi quietly exhausting ban jaate hain — pattern yahi.",
        },
        "LOW": {
            "kya_dikh":   "{p1} aur {p2} ke daily life partnership ko deliberately design karna padega — auto-pilot pe ye nahi chalegi. Natural division of labour smooth nahi hai; small things (groceries, bills, who cooks, kis ke parents ka kaam pehle) chronic stress points ban sakte hain. Ek partner shayad zyada uthane lagta hai aur silently resentful hota jaata hai; dusra notice nahi karta, kyunki uske liye 'sab to chal raha hai.'",
            "kya_matlab": "Real life me iska impact — household tension grow karti hai jab unspoken expectations clash karti hain. Family side ke pressures bhi ek partner pe disproportionately gir sakte hain. Ye saalon me silently relationship ko khaata hai — fight ek bartan pe hoti hai, lekin actual feeling 'main akela sambhal raha hoon' wali hoti hai. Aur woh feeling jab tak labelled nahi, naya bartan har hafte phir wahi fight banayega.",
            "kya_dhyan":  "Silent resentment tab jam kar jaati hai jab fairness kabhi table pe nahi aati — sirf kitchen ke scene pe settle ho jaati hai; ek partner ka 'main adjust kar leta hoon' baad me weapon ban sakta hai bina intention ke. Written clarity awkward hai par boundary banati hai; honesty yahan motivational poster nahi, seedhi baat hai. Jo dikhta nahi hai wahi silent resentment ka bulk hai — is rishte ka chupchaap pattern.",
        },
    },
    "ch7": {
        "HIGH": {
            "kya_dikh":   "Paanch-dus saal ki tasveer me {p1} aur {p2} dono alag velocity pe grow hue dikhte hain — ek zyada bahar, measurable moves me; ek zyada andar, perspective aur calm me. Dono growth real hai. Agar sirf visible markers ko score maan liya jaaye, ek unfairly peeche feel ho jaata hai jab actually rhythm alag hai.",
            "kya_matlab": "Real life me career/social/spiritual heights mismatch ho sakti hai aur phir bhi bond tik sakta hai — par comparison ka ek casual sentence foundation crack kar deta hai. Pride yahan quietly expensive hai kyunki lagta hai metric ek hi hona chahiye. Future-direction friction aksar ambition kam, visibility zyada hoti hai.",
            "kya_dhyan":  "Comparison ka kick chhota hai, resentment lambi chal sakti hai — yeh pattern meri practice me baar dikhta hai. joint daily prayers yahan lecture kam, shared pause zyada hain: ek hi minute jahan success-story band ho jaati hai. Jab outward aur inward growth ko do alag professions jaise dekha jaaye, awkward jealousy kam readable lagti hai.",
        },
        "MID": {
            "kya_dikh":   "Future ki tasveer abhi {p1} aur {p2} ke beech fully aligned nahi hai. {p1} stability + steady growth chahta hai — predictable ghar, slow-build career. {p2} adventure + change chahta hai — naye experiences, bold moves. Dono valid life-paths hain, lekin same shaadi me alag direction me kheechte hain. Aur is mismatch ko dono abhi tak directly naam nahi de rahe — chhoti baaton me ye gap silently dikhta hai.",
            "kya_matlab": "Avoidance yahan gap shrink nahi karta, sirf rename karta hai — dinner table pe weather-tab tak safe hai jab tak city/kids/career unnamed hai. Mismatch publicly ugly lagta hai isliye log delay karte hain; delay dheere-dheere closeness khinch leta hai. Jab direction blurry hai to ek partner zyada anxious dikhta hai, dusra zyada numb — dono coping.",
            "kya_dhyan":  "Navigating mismatch moral victory kam, clear boundary zyada maangta hai — kis cheez pe flexibility hai, kis pe nahi. gratitude practice agar sirf ek minute ka 'kis assumption ne aaj pressure banaya' notice ho, silent drift visible ho jaati hai. consult a qualified Jyotishi kabhi sirf calendar-frame ke liye useful hai — neutral sentence jo ghar me tribal ho chuki hai.",
        },
        "LOW": {
            "kya_dikh":   "Long-term direction abhi blurry hai — aur ye fault kisi ka nahi, life-stage hai. {p1} aur {p2} dono apni individual clarity dhundh rahe hain — har koi apne baare me figure out kar raha hai. Shaadi me ek subtle 'kahaan jaa rahe hain hum' wala question silently chodta hai. Asymmetry ye hai ki kisi ek ko is uncertainty se kam comfort hota hai, kisi ko zyada — aur woh asymmetry bhi friction add karti hai.",
            "kya_matlab": "Shared decisions tough lagenge jab individual paths cloudy hon — ye morality ka trial kam, fog ka trial zyada hai. Drift silently tab grow karti hai jab 100 chhote unnamed turns ek hi ghar me alag maps ban jaate hain; realization dramatic kam, cumulative zyada hai.",
            "kya_dhyan":  "Individual maps overlap tab readable hote hain jab shame kam headline ban jaati hai — jo partner zyada numb hai woh lazy nahi, overloaded ho sakta hai. joint daily prayers divergent weeks me sirf ek synchronized breath ki tarah kaam karte hain — faith poster nahi, rhythm anchor. gratitude practice yahan simple notice hai: kis silent decision ne gap banaya — uncomfortable par baad me kam mahanga.",
        },
    },
}

def _soul_band_full_read(ch_key: str, band: str, ctx: dict) -> str:
    """Merge legacy 3-layer soul strings into one continuous `full_read` body."""
    soul = (_CH_SOUL.get(ch_key) or {}).get(band) or (_CH_SOUL.get(ch_key) or {}).get("MID") or {}
    parts: list[str] = []
    for layer in ("kya_dikh", "kya_matlab", "kya_dhyan"):
        raw = soul.get(layer) or ""
        try:
            txt = str(raw).format(**ctx).strip()
        except Exception:
            txt = str(raw).strip()
        if txt:
            parts.append(txt)
    return " ".join(parts)


def _safe_fallback(milan_facts: dict, chapter_scores: dict,
                   kp_promise: dict | None = None,
                   d9_marriage: dict | None = None) -> dict[str, Any]:
    """Soul-rich deterministic fallback. Each chapter ships one ``chapter_body`` narrative
    (``full_read`` kept in sync) plus optional ``grounding``.
    Always returns a valid PDF payload even if LLM polish is off
    or unavailable. Defensive against malformed inputs — never raises."""
    # Defensive normalization: never trust caller shape
    mf = milan_facts if isinstance(milan_facts, dict) else {}
    p1d = mf.get("p1") if isinstance(mf.get("p1"), dict) else {}
    p2d = mf.get("p2") if isinstance(mf.get("p2"), dict) else {}
    p1n = (p1d.get("name") if isinstance(p1d.get("name"), str) else None) or "Partner 1"
    p2n = (p2d.get("name") if isinstance(p2d.get("name"), str) else None) or "Partner 2"
    # Coerce numeric fields — caller may send strings
    def _num(v, dflt):
        try: return float(v) if isinstance(v, (int, float, str)) and str(v).strip() != "" else dflt
        except (TypeError, ValueError): return dflt
    total = int(_num(mf.get("total"), 0))
    mx = int(_num(mf.get("max"), 36))
    cs = chapter_scores if isinstance(chapter_scores, dict) else {}
    chs_engine = cs.get("chapters") if isinstance(cs.get("chapters"), dict) else {}
    kp_band = _kp_couple_band(kp_promise)
    ctx = {"p1": p1n, "p2": p2n, "total": total, "mx": mx}

    chapters_out = []
    high_chs: list[tuple[str, str]] = []   # (key, title) for special bullets
    low_chs:  list[tuple[str, str]] = []   # (key, title) for damage bullets
    for k in CHAPTER_KEYS:
        ch = chs_engine.get(k, {}) or {}
        score = ch.get("score_0_10")
        band = _band(score)
        title = ch.get("title", k)
        if band == "HIGH": high_chs.append((k, title))
        elif band == "LOW": low_chs.append((k, title))
        full_read = _soul_band_full_read(k, band, ctx)
        if len(full_read.strip()) < 80:
            full_read = (
                f"{p1n} aur {p2n} ke beech is chapter me rhythm uneven hai — ek partner zyada verbally sort karta hai, "
                f"dusra andar pal ke; dono apni jagah 'sahi' lagte hain. "
                f"Roz ke scene me closeness aur withdrawal ek hi hafte me alternate ho sakte hain bina headline ke; "
                f"mismatch kabhi moral failure nahi, delayed timing hota hai."
            )
        merged = full_read.strip()
        if k in ("ch4", "ch7"):
            merged = _chart_bridge_with_remedy_tail(merged)
        if len(merged) > _PREMIUM_CHAPTER_BODY_MAX_CP:
            merged = _truncate_pdf_safe_cp(merged, _PREMIUM_CHAPTER_BODY_MAX_CP)
        ch_obj: dict[str, Any] = {
            "key": k,
            "title": title,
            "score_0_10": score,
            CHAPTER_BODY_KEY: merged,
            CHAPTER_FULL_READ: merged,
            "grounding": (f"Reading anchored to {title} layer — band {band}, "
                          f"{p1n} & {p2n} chart cross-reference."),
        }
        chapters_out.append(ch_obj)

    # ── Hidden Truth (P3) — 5-7 sentences, total + names + KP plain prose ──
    kp_line = _kp_signature_line(kp_promise) or ""
    hidden = (
        f"{p1n} aur {p2n} ke beech Milan headline {total} out of {mx} hai — ye ek shutter hai; "
        f"andar ka scene alag lighting me chal raha hota hai. Strength friction ko quietly sponsor karti hai "
        f"aur friction strength ko blunt karti hai — duty kabhi love ki tarah dikhti hai jab thakaan zyada ho. {kp_line} "
        f"Meri practice me yeh jodi tab tak confusing lagti hai jab tak ek partner ka withdrawal insult samajh liya jaata hai "
        f"jab overload ki kahani ho — uncomfortable, par aksar accurate. "
        f"Aage ke chapters roz-marrah patterns ginenge jahan love uneven labour ban jaata hai. "
        f"Neeche har chapter me D1, D9, synastry, aur KP marriage texture don charts se cross-read ki gayi hai — "
        f"koot grid sirf supporting context hai; primary evidence structured chart JSON hi maana jaata hai. "
        f"Har chapter ke lambe chapter_body narrative me chart causality ko ghar ke behaviour me translate kiya gaya hai — generic compatibility "
        f"summary nahi, elite marriage observation lane hai. Remedies conservative whitelist se bandhe hain; "
        f"gemstone/tantra leaps yahan kabhi nahi aate."
    )

    # ── Special (P18) — derived from HIGH chapters; rich 2-3 sentence bullets ──
    special: list[str] = []
    if high_chs:
        for k, title in high_chs[:4]:
            special.append(_special_bullet(k, title, p1n, p2n))
    if len(special) < 3:
        special.append(
            f"{p1n} aur {p2n} ke beech jo trust dikhta hai woh manifesto me kam, "
            f"micro-consistency me zyada hai — time bolna, gate band karna, awkward pause tolerate karna."
        )
    if len(special) < 3:
        special.append(
            f"Jo surface pe ease dikhti hai kabhi kabhi debt hoti hai — kisi ek ne "
            f"zyada labour uthaya hai bina acknowledgement ke; compatibility kabhi tolerance ka tolerance bhi maangti hai."
        )
    if len(special) < 3:
        special.append(
            f"Score ({total}/{mx}) sirf headline hai — kabhi yeh batata hai ki kitna mismatch "
            f"culturally bardash ho sakta hai, kabhi ki kab tak avoidance chupke se chalti rahegi."
        )
    # ── Damage (P19) — rich, framed as patterns to manage; never "no friction" ──
    damage: list[str] = []
    if low_chs:
        for k, title in low_chs[:4]:
            damage.append(_damage_bullet(k, title, p1n, p2n))
    else:
        damage.append(
            f"Sabse common silent damage — assume karna ki {p1n} aur {p2n} ek hi inner headline "
            f"me sochte hain. Compatibility ke baad bhi dono ka ticker alag chal sakta hai; "
            f"jab mismatch unnamed rehta hai, chhoti baatein proof ban jaati hain."
        )
        damage.append(
            f"Doosra pattern — ease ko proof maan lena jab tak resentment quietly pile na ho jaaye. "
            f"Strong-looking bonds me bhi avoidance chup-chap chal sakti hai — visible effort aur felt effort "
            f"kabhi same scale par nahi lagte."
        )
    # ── Practical (P20) — 3-4 paragraphs, name-anchored, behavioral specificity ──
    practical = [
        f"{p1n} aur {p2n} ke ghar me jo tension sabse late naam leta hai woh aksar logistics hai "
        f"jo romance ki tarah chipka dikhta hai — bills, timing, kaun parents ko phone karega; "
        f"neeche exhaustion dikhti hai jo kabhi galat tarah se 'attitude' lagti hai.",

        f"Family calendar prestige aur guilt dono chhupa leta hai — {p1n} ke liye event attendance proof ho sakta hai, "
        f"{p2n} ke liye trap; boundary yahan moral lecture kam, sentence-assign kam zyada maangta hai "
        f"taaki festivals silently draining na ban jaayein.",

        f"Money aur bade decisions par mismatch publicly ugly lagta hai isliye delay hota hai — "
        f"delay dheere-dheere closeness khinch leta hai; baat clear tab hoti hai jab shame kam headline ban "
        f"aur map spoken ho, chahe jawab sync na ho.",
    ]
    # ── Verdict (P23) — closing letter with names, total, and a "remember this" line ──
    band_text = "strong" if total >= 28 else ("meaningful" if total >= 21 else "workable")
    verdict = (
        f"{p1n} aur {p2n}, Milan tally {total} out of {mx} hai — ek {band_text} headline numerically. "
        f"Meri taraf se jo quietly observe hota hai: numbers kabhi chemistry ki poori kahani nahi hote, "
        f"kabhi sirf batate hain ki kitna mismatch culturally bardash ho sakta hai bina scene banaye. "
        f"Jo chapters follow karte hain unme uneven rhythm, delayed timing, aur ghar ke andar dikhai na dene wala extra bojh ginaya gaya hai — "
        f"awkward sach ignore karna cheap nahi padta, sirf delayed."
    )

    blueprint = _safe_fallback_blueprint(d9_marriage, p1n, p2n)

    return {
        "hidden_truth": hidden,
        "chapters": chapters_out,
        "special": special,
        "damage": damage,
        "practical": practical,
        "verdict": verdict,
        "marriage_blueprint": blueprint,
        "_meta": {
            "model": "fallback-soul-v3",
            "version": _PREMIUM_VERSION,
            "kp_promise": kp_band,
            "hidden_signature": kp_line,
        },
    }


# ─────────────────────────────────────────────────────────────────────────
#  MARRIAGE BLUEPRINT (Phase 2.5.11.23-soul-v3)
# ─────────────────────────────────────────────────────────────────────────
# Translates D9 marriage-character signals into pure relational character
# language. The fallback NEVER quotes raw chart vocab — it interprets the
# lagna lord, Venus/Jupiter dignity, and marriage_maturity into the kind
# of marriage nature each partner brings, and the shape of the daily
# rhythm that emerges between them.
# ─────────────────────────────────────────────────────────────────────────

# Lagna-lord → innate marriage nature (interpreted, not raw)
_LORD_NATURE = {
    "Sun":     "leads with quiet authority — committed, principled, holds the centre when things get loud",
    "Moon":    "leads with emotional attunement — care-forward, reads the room before speaking",
    "Mars":    "leads with directness and protective energy — quick to act, slow to forgive, fiercely loyal",
    "Mercury": "leads with curiosity and adaptability — talks things through, loves shared ideas, reads people fast",
    "Jupiter": "leads with warmth and steady values — wants meaning in the relationship, not just routine",
    "Venus":   "leads with affection and aesthetic care — needs beauty, ease, and tender daily moments",
    "Saturn":  "leads with discipline and quiet patience — slow to open up, but once committed, deeply consistent",
}

# Maturity score → tone qualifier
def _maturity_word(score) -> str:
    try:
        s = float(score)
    except Exception:
        return "still finding its full depth"
    if s >= 7.5: return "carries marriage as a deeply mature space — knows how to hold a long bond"
    if s >= 5.5: return "is growing into the depth marriage asks for — capable, still learning"
    if s >= 3.5: return "approaches marriage with sincerity but still meets some tender, unfinished places"
    return "still meeting marriage as a teacher — every chapter here is part of becoming"


def _interaction_phrase(rel_lagna: str, rel_seven: str) -> str:
    """Couple's interaction shape from the deeper character relation."""
    if rel_lagna in ("same", "friendly") and rel_seven in ("same", "friendly"):
        return ("Their natures meet in quick mutual recognition — daily rhythm "
                "settles early; conflict pauses stay short. The risk is not drama "
                "but drift: calling ease 'proof' until resentments pile up quietly.")
    if rel_lagna == "hostile" or rel_seven == "hostile":
        return ("Their inner natures speak slightly different languages. One leads "
                "where the other waits, one moves where the other steadies. This is "
                "not incompatibility — it's the asymmetry that makes growth possible, "
                "but only if both name it instead of resenting it.")
    return ("Their natures meet in a workable mid-zone — not effortlessly aligned, "
            "not opposed. Daily rhythm builds through repetition and habit more than "
            "spark; awkward seasons come before anything feels obvious.")


def _blueprint_pad_total_words(mb: dict[str, str], p1n: str, p2n: str) -> dict[str, str]:
    """Pass-through: blueprint length is soft-targeted in prompts, not validator-padded."""
    _ = (p1n, p2n)
    return mb


def _safe_fallback_blueprint(d9: dict | None, p1n: str, p2n: str) -> dict[str, str]:
    """Generate the marriage_blueprint section from D9 signals.
    Always returns a valid dict — never raises. Uses generic-but-warm
    text when D9 is unavailable. NEVER quotes raw chart vocabulary."""
    d9 = d9 if isinstance(d9, dict) else {}
    p1d = d9.get("p1") if isinstance(d9.get("p1"), dict) else {}
    p2d = d9.get("p2") if isinstance(d9.get("p2"), dict) else {}
    sync = d9.get("sync") if isinstance(d9.get("sync"), dict) else {}

    p1_lord = p1d.get("d9_lagna_lord") or "Jupiter"
    p2_lord = p2d.get("d9_lagna_lord") or "Venus"
    p1_nature = _LORD_NATURE.get(p1_lord, _LORD_NATURE["Jupiter"])
    p2_nature = _LORD_NATURE.get(p2_lord, _LORD_NATURE["Venus"])
    p1_mat = _maturity_word(p1d.get("marriage_maturity_0_10"))
    p2_mat = _maturity_word(p2d.get("marriage_maturity_0_10"))

    rel_lagna = (sync.get("lagna_lord_relation") or "neutral").lower()
    rel_seven = (sync.get("seven_lord_relation") or "neutral").lower()

    p1_marriage_nature = (
        f"{p1n} ki marriage nature ek aisi hai jo {p1_nature}. "
        f"Andar se {p1n} {p1_mat}. Iska matlab — jab pressure aata hai, "
        f"{p1n} apne natural style se respond karta hai, koi performance nahi."
    )
    p2_marriage_nature = (
        f"{p2n} ki marriage nature alag energy carry karti hai — woh {p2_nature}. "
        f"Andar se {p2n} {p2_mat}. Yeh nature {p1n} ki nature se complementary hai, "
        f"identical nahi — aur shaadi me yahi diversity strength banti hai jab dono samjhein."
    )
    interaction_dynamic = (
        f"{p1n} aur {p2n} ke beech jo daily rhythm banegi, woh in dono ki "
        f"different inner natures ka product hai. {_interaction_phrase(rel_lagna, rel_seven)} "
        f"Ek partner shayad pehle bolega, dusra silently absorb karega — yeh natural hai, "
        f"galat nahi. Dono apne style me marriage ko honour kar rahe hain."
    )
    what_p1_needs_from_p2 = (
        f"{p1n} ko {p2n} se sabse zyada chahiye predictable warmth — "
        f"chhoti consistent gestures, na ki badi declarations. Jab {p1n} thoda "
        f"silent ho jaaye, woh withdrawal nahi hai — woh ek invitation hai gentle "
        f"presence ki. Force karne se peeche jaayega; quiet dene se kheechke aayega."
    )
    what_p2_needs_from_p1 = (
        f"{p2n} ko {p1n} se wo mahsoos karna padta hai jisme notice naam ke saath aata hai — "
        f"'tu ne ye sambhal liya, dekha maine' jaise line sirf praise nahi, counted gesture hai. "
        f"Agar {p1n} sirf silently kar deta hai, {p2n} kabhi kabhi sunta hi nahi — aur "
        f"dono galat feel karte hain jab mismatch actually visibility ka hota hai."
    )
    blueprint_takeaway = (
        f"{p1n} aur {p2n} ki shaadi do alag natures ka meeting hai — "
        f"complementary kabhi comfortable nahi hota pehle saalon me; awkward adjustment "
        f"ek realistic baseline hai jab tak dono mismatch ko moral drama banane chhod dete hain."
    )
    out = {
        "p1_marriage_nature":    p1_marriage_nature.strip(),
        "p2_marriage_nature":    p2_marriage_nature.strip(),
        "interaction_dynamic":   interaction_dynamic.strip(),
        "what_p1_needs_from_p2": what_p1_needs_from_p2.strip(),
        "what_p2_needs_from_p1": what_p2_needs_from_p1.strip(),
        "blueprint_takeaway":    blueprint_takeaway.strip(),
    }
    return _blueprint_pad_total_words(out, p1n, p2n)


# ── Bullet generators for special/damage (P18/P19) ──
_SPECIAL_BY_CH = {
    "ch1": "Emotional rhythm — {p1} aur {p2} ke nervous-system level pe ek quiet familiarity hai. Bahut log isko 'connection' bolte hain; tum dono ke liye ye default state hai.",
    "ch2": "Trust ka foundation — dono naturally apne word rakhne wale log ho. Ye chhoti sthirta hi long-term bonds ka asli stone hai.",
    "ch3": "Conflict maturity — disagreement personal attack me convert nahi hoti. Ye couples ki rare gift hai jo aksar tab dikhti hai jab pace clash ko pehle naam mil jaata hai.",
    "ch4": "Long-haul instinct — dono unconsciously is bond ko temporary nahi maante. Stress me bhi 'shall we still be us in 10 years' wala question aata hi nahi.",
    "ch5": "Chemistry — pull novelty se kam, safety aur repetition se zyada chipka hota hai; busy season me pehle sideline hone wala mismatch yahi hota hai.",
    "ch6": "Daily life partnership — silent efficiency hai. Chhoti chizein bina drama ke chal jaati hain, energy bachi rehti hai bigger moments ke liye.",
    "ch7": "Future direction — saath ka compass kabhi ek hi minute me align nahi hota; dono alag velocity pe badhte dikhte hain — aur kaafi compatibility us uneven pace ko bardash karne me chipka hota hai.",
}
_DAMAGE_BY_CH = {
    "ch1": "Emotional pacing — {p1} aur {p2} ki feeling-clocks alag speed pe chalti hain. Ek immediate hai, dusra delayed processor. Bina samjhe ye saalon ki chronic 'tu mujhe samajhta nahi' wali feeling banata hai.",
    "ch2": "Trust definitions — dono ke 'trust' ka definition slightly alag hai. Ek ke liye = full transparency, dusre ke liye = privacy ka respect. Jab tak map spoken nahi, silent grievances pile ho jaati hain.",
    "ch3": "Conflict pacing — {p1} aur {p2} me ek 'abhi solve karo' camp me hai, dusra 'thanda hone do' camp me. Real fight topic pe nahi, pace pe ho jaati hai. Yahi most-repeated argument ka shape hai.",
    "ch4": "Stability test point — {p1} aur {p2} ke beech ek specific adjustment hai jo dono shuruat me resist karenge — wahi adjustment long-term stability ka actual key hai. Ignore karoge to wahi recurring fight ban jaayegi.",
    "ch5": "Intimacy languages — needs alag tareeke se express hoti hain. Ek partner ko lagega 'isme us tarah ki feeling nahi hai jaisi honi chahiye', jab actually partner is showing it in their language. Naam diye bina ye gap silently bahut couples ko alag karta hai.",
    "ch6": "Family expectations — {p1} aur {p2}, donon side ke family ke unspoken rules clash karenge. Ye relationship ke andar tension nahi laata, lekin saalon me energy chusta hai.",
    "ch7": "Direction drift — {p1} aur {p2} agar individual clarity ke bina chalein, joint direction blurry rahegi. Drift ek silent risk hai — ek din realize hota hai 'hum bahut alag log ho gaye'.",
}

def _special_bullet(ch_key: str, title: str, p1n: str, p2n: str) -> str:
    tpl = _SPECIAL_BY_CH.get(ch_key) or "{p1} aur {p2} ke beech is area me natural strength hai jo time ke saath aur deeper hoti jaayegi."
    return tpl.format(p1=p1n, p2=p2n)

def _damage_bullet(ch_key: str, title: str, p1n: str, p2n: str) -> str:
    tpl = _DAMAGE_BY_CH.get(ch_key) or "{p1} aur {p2} ke beech is area me extra conscious effort chahiye — silent assumptions yahaan sabse mehngi padti hain."
    return tpl.format(p1=p1n, p2=p2n)


def _kp_couple_band(kp_promise: dict | None) -> str:
    """Resolve the couple-level promise band from the kp_promise dict.
    Accepts either the per-side or the couple wrapper shape; returns one of
    STRONG / PARTIAL / WEAK / UNAVAILABLE."""
    if not isinstance(kp_promise, dict):
        return "UNAVAILABLE"
    band = kp_promise.get("couple_verdict") or kp_promise.get("verdict")
    if isinstance(band, str) and band.upper() in ("STRONG", "PARTIAL", "WEAK", "UNAVAILABLE"):
        return band.upper()
    return "UNAVAILABLE"


def _kp_signature_line(kp_promise: dict | None) -> str:
    """Plain-language one-line signature for the P3 grounding card.
    Translates the hidden KP marriage-promise reading into everyday words —
    NEVER leaks jargon (no CSL/sub-lord/significator/house numbers).
    """
    if not isinstance(kp_promise, dict):
        return ""
    band = (kp_promise.get("couple_verdict") or kp_promise.get("verdict") or "").upper()
    plain = {
        "STRONG":  "Both charts carry a clear, supportive marriage signal underneath.",
        "PARTIAL": "Both charts carry a present but mixed marriage signal underneath — workable, not effortless.",
        "WEAK":    "The deeper marriage signal in both charts is faint — ordinary friction reads louder here until timing and temperament find a workable rhythm.",
    }
    return plain.get(band, "")
