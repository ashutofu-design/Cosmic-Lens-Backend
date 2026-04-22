"""
Report translator — converts the entire report dict into the user-selected
language with strict consistency.

Languages:
  - "hinglish"  (default — pass-through, no translation; current build is Hinglish)
  - "en"        (100% English, professional, clean tone)
  - "hi"        (100% Hindi in Devanagari, natural conversational)

Strategy:
  - Walk the dict; collect every translatable string by path
  - Filter: skip pure numbers, scores, single-word labels we want to keep
            (element names, archetype labels), short codes, etc.
  - Send batches to OpenAI in JSON mode → get back same-shape dict of translations
  - Substitute back; cache by hash for idempotence inside same call
"""
from __future__ import annotations
from typing import Any, Dict, List, Tuple
import json
import re

# Field-name allowlist: only translate values under these keys (anywhere in tree)
TRANSLATABLE_FIELDS = {
    # narrative / prose
    "narrative", "body", "summary", "insight", "prediction", "behaviour",
    "habit", "environment", "why", "for",
    # one-liners
    "biggest_strength", "biggest_weakness", "biggest_mistake_hi",
    "biggest_strength_hi", "brutal_truth", "closing_truth",
    "closing_truth_hi", "must_do", "behaviour_pattern",
    # hook
    "identity_line", "shock_line",
    # tldr extras
    "life_pattern", "desc",
    # final truth v2
    "direction",
    # synthesis
    "trait", "scenario",
    # section content text fields commonly seen
    "summary_hi", "summary_en", "intro_para",
    "heading_hi", "heading_en", "category", "area", "label",
    "expected_lift",
    # lists of strings (handled at parent level too)
    "strengths", "risks", "top_3_strengths", "top_3_weaknesses",
}

# Field keys to NEVER translate (keep canonical English/code values)
NEVER_TRANSLATE_VALUES = {
    "key", "kind", "engine", "version", "engine_version",
    "ref", "note", "source", "sources", "tag", "name",  # Big5 trait names stay
}

# Words/labels we keep verbatim across languages (brand, technical)
KEEP_VERBATIM = {
    "Cosmic Lens", "Cosmic Intelligence",
    "Big-5", "OCEAN", "Vedic", "Samudrika", "TL;DR",
}


def _get_client():
    """Build OpenAI client. Prefer Replit AI Integrations proxy (auto-billed,
    no quota issues); fall back to user's OPENAI_API_KEY."""
    import os
    try:
        from openai import OpenAI
    except Exception:
        return None

    proxy_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
    proxy_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
    if proxy_url and proxy_key:
        try:
            return OpenAI(api_key=proxy_key, base_url=proxy_url)
        except Exception:
            pass

    key = os.environ.get("OPENAI_API_KEY")
    if key:
        try:
            return OpenAI(api_key=key)
        except Exception:
            return None
    return None


# Model: prefer cheap+fast for translation. gpt-5-nano on proxy, fallback gpt-4o-mini direct.
def _translation_model() -> str:
    import os
    if os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL"):
        return "gpt-5-nano"
    return "gpt-4o-mini"


def _is_translatable_value(v: Any) -> bool:
    """Decide if a string value is worth translating."""
    if not isinstance(v, str):
        return False
    s = v.strip()
    if not s:
        return False
    # Skip very short codes / single labels handled separately
    if len(s) < 4:
        return False
    # Skip pure numerics, percentages, scores
    if re.fullmatch(r"[\d\s\./%\-:]+", s):
        return False
    # Skip ALL-UPPER short codes
    if s.isupper() and len(s) < 30:
        return False
    return True


def _collect_strings(node: Any, path: Tuple, out: List[Tuple[Tuple, str]],
                     parent_key: str = "") -> None:
    """Recursively collect (path, string) pairs that need translation.
    DENYLIST-based: translate every string that is `_is_translatable_value` AND
    not under a denylisted key. This catches section bodies regardless of field name."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k in NEVER_TRANSLATE_VALUES:
                continue
            new_path = path + (k,)
            if isinstance(v, str):
                if _is_translatable_value(v):
                    out.append((new_path, v))
            else:
                _collect_strings(v, new_path, out, parent_key=k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            new_path = path + (i,)
            if isinstance(v, str):
                if _is_translatable_value(v):
                    out.append((new_path, v))
            else:
                _collect_strings(v, new_path, out, parent_key=parent_key)


def _set_at_path(root: Any, path: Tuple, value: str) -> None:
    """Set value at nested path."""
    cur = root
    for p in path[:-1]:
        cur = cur[p]
    cur[path[-1]] = value


# Strict per-language system prompt
_SYS_PROMPTS = {
    "en": (
        "You are a professional translator. Convert the given JSON map of texts "
        "to 100% ENGLISH. Rules:\n"
        "1. Use professional, clean, concise tone (not academic, not casual).\n"
        "2. Keep the EXACT same JSON structure: same keys, translated values only.\n"
        "3. Do NOT change numbers, scores, percentages, or named entities.\n"
        "4. Keep these verbatim: Cosmic Lens, Cosmic Intelligence, OCEAN, Big-5, "
        "Vedic, Samudrika, TL;DR.\n"
        "5. Strip Hindi/Devanagari characters entirely. NO Hindi words.\n"
        "6. Short paragraphs (2-3 sentences max where possible).\n"
        "7. Preserve <b>...</b> HTML tags.\n"
        "Return ONLY the translated JSON object, no explanations."
    ),
    "hi": (
        "आप एक पेशेवर अनुवादक हैं। दिए गए JSON मैप के सभी टेक्स्ट को "
        "100% हिंदी (देवनागरी लिपि) में बदलें। नियम:\n"
        "1. प्राकृतिक, बातचीत वाली हिंदी (बहुत संस्कृतनिष्ठ नहीं)।\n"
        "2. JSON संरचना बिल्कुल वही रखें: वही keys, सिर्फ values अनुवाद करें।\n"
        "3. संख्या, स्कोर, प्रतिशत, और तकनीकी नाम न बदलें।\n"
        "4. ये verbatim रखें: Cosmic Lens, Cosmic Intelligence, OCEAN, Big-5, "
        "Vedic, Samudrika, TL;DR।\n"
        "5. कोई English शब्द नहीं (अनिवार्य तकनीकी छोड़कर)।\n"
        "6. छोटे पैराग्राफ (2-3 वाक्य अधिकतम)।\n"
        "7. <b>...</b> HTML टैग्स को preserve करें।\n"
        "केवल अनुवादित JSON object लौटाएं, कोई व्याख्या नहीं।"
    ),
    "hinglish": (
        "You are a Hinglish writer. Convert the given JSON map of texts to natural "
        "spoken Hinglish (Hindi-English mix in Roman script). Rules:\n"
        "1. India-friendly conversational tone (like 'tum balanced ho').\n"
        "2. NO Devanagari script — Roman letters only.\n"
        "3. Keep EXACT same JSON structure: same keys, translated values only.\n"
        "4. Do NOT change numbers, scores, percentages, or named entities.\n"
        "5. Keep verbatim: Cosmic Lens, Cosmic Intelligence, OCEAN, Big-5, "
        "Vedic, Samudrika, TL;DR.\n"
        "6. Short paragraphs (2-3 sentences max).\n"
        "7. Preserve <b>...</b> HTML tags.\n"
        "Return ONLY the translated JSON object, no explanations."
    ),
}


def _translate_batch(items: Dict[str, str], language: str) -> Dict[str, str]:
    """Single OpenAI call to translate a batch of {id: text} entries."""
    client = _get_client()
    if client is None:
        return items  # graceful: return originals

    sys_prompt = _SYS_PROMPTS.get(language, _SYS_PROMPTS["en"])
    user_payload = json.dumps(items, ensure_ascii=False)

    model = _translation_model()
    # gpt-5-* doesn't accept `temperature` and uses `max_completion_tokens`
    is_gpt5 = model.startswith("gpt-5")
    kwargs = {
        "model": model,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_payload},
        ],
    }
    if is_gpt5:
        kwargs["max_completion_tokens"] = 12000
        kwargs["reasoning_effort"] = "minimal"  # critical: skip reasoning for translation
    else:
        kwargs["temperature"] = 0.3
        kwargs["max_tokens"] = 12000

    try:
        resp = client.chat.completions.create(**kwargs, timeout=90)
        out = json.loads(resp.choices[0].message.content or "{}")
        if not isinstance(out, dict):
            return items
        # Ensure every key from input is present in output (fallback to original)
        return {k: out.get(k, v) for k, v in items.items()}
    except Exception as e:
        print(f"[translator] OpenAI call failed: {e}")
        return items


def translate_report(report: Dict, language: str) -> Dict:
    """
    Translate all user-visible string fields in report dict to target language.
    Returns the same dict (mutated in place) for convenience.
    Pass-through if language is 'hinglish' or invalid.
    """
    lang = (language or "").strip().lower()
    if lang in ("", "hinglish", "hg"):
        return report  # default — no translation, current build is Hinglish

    if lang not in _SYS_PROMPTS:
        # accept aliases
        if lang in ("english", "eng"): lang = "en"
        elif lang in ("hindi", "hin"): lang = "hi"
        else:
            return report

    # Collect all translatable strings with their paths
    collected: List[Tuple[Tuple, str]] = []
    # Walk the parts that have user-visible text
    for top_key in ("hook", "tldr", "final_truth_v2", "sections",
                    "synthesis", "footer_disclaimer"):
        node = report.get(top_key)
        if node is None:
            continue
        # Wrap top-level string into a fake dict so collector works uniformly
        if isinstance(node, str):
            if _is_translatable_value(node):
                collected.append(((top_key,), node))
            continue
        _collect_strings(node, (top_key,), collected, parent_key=top_key)

    if not collected:
        return report

    # Build batch dict {id: text} — use stable IDs per index
    items = {f"t{i}": text for i, (_p, text) in enumerate(collected)}

    # Chunk into batches of ~80 items / ~30KB per call to keep tokens manageable
    batch_size = 60
    translated_all: Dict[str, str] = {}
    keys = list(items.keys())
    for i in range(0, len(keys), batch_size):
        chunk_keys = keys[i:i + batch_size]
        chunk = {k: items[k] for k in chunk_keys}
        result = _translate_batch(chunk, lang)
        translated_all.update(result)

    # Substitute back at original paths
    for i, (path, _orig) in enumerate(collected):
        new_text = translated_all.get(f"t{i}")
        if new_text and isinstance(new_text, str):
            try:
                _set_at_path(report, path, new_text)
            except Exception:
                pass

    # Mark report with applied language
    report["_language"] = lang
    return report
