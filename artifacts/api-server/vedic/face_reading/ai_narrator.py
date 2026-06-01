"""
Face Reading — gpt-4o for selected prose blocks only (not the whole PDF).

Engines + narrative_writer build the report; OpenAI receives only sections
that still need richer copy (facts JSON per block — no images/tables/PDF bytes).

FACE_READING_AI_MODE=selective (default) | full | off
FACE_READING_AI_SECTIONS=section_1,faceread.hook_identity  # optional allowlist
FACE_READING_AI_NARRATOR=1
FACE_READING_AI_MODEL=gpt-4o
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from typing import Any, Dict, List, Optional

# Bump when face prompts/voice/batching change (disk cache namespace).
from .report_version import NARRATION_VERSION

FACE_CACHE_VERSION = NARRATION_VERSION

# PDF tables/scores/images are rendered locally — never sent to OpenAI.
_AI_NEVER = frozenset({
    "bonus_personality_score",  # score grid + short template is enough
})

# Cover hook + skim block — always eligible unless already excellent.
_AI_ALWAYS = frozenset({
    "faceread.hook_identity",
    "faceread.hook_shock",
    "faceread.tldr",
})

from .report_voice import (
    FACE_VOICE_ADDENDUM,
    passes_face_voice_combined,
    section_angle_hint,
)

# Concise, high-density targets (quality > word count; tables carry detail in PDF)
WORD_TARGETS: Dict[str, int] = {
    "section_1_power_summary": 210,
    "section_2_psychological_type": 170,
    "section_3_mask_vs_real": 170,
    "section_4_first_impression": 185,
    "section_5_core_foundation": 160,
    "section_6_feature_analysis": 175,
    "section_7_personality_synthesis": 210,
    "section_8_love_relationship_dna": 200,
    "section_9_career_money": 200,
    "section_10_red_flags": 165,
    "section_11_attraction_charisma": 165,
    "section_12_decision_style": 150,
    "section_13_archetype": 160,
    "section_14_life_flow": 185,
    "section_15_age_wise_map": 165,
    "section_16_health_scan": 175,
    "section_17_secret_markings": 140,
    "section_18_action_plan": 165,
    "section_19_improvement_hacks": 150,
    "section_20_compatibility": 160,
    "section_21_final_truth": 220,
    "bonus_personality_score": 120,
    "faceread.hook_identity": 40,
    "faceread.hook_shock": 38,
    "faceread.tldr": 110,
}

_EMOTIONAL_SECTIONS = frozenset({
    "section_3_mask_vs_real",
    "section_8_love_relationship_dna",
    "section_14_life_flow",
    "section_21_final_truth",
})

# High-impact prose — AI unless engine template already passes strict checks.
_AI_PRIORITY = _EMOTIONAL_SECTIONS | frozenset({
    "section_1_power_summary",
    "section_7_personality_synthesis",
})


def ai_enabled() -> bool:
    raw = (os.environ.get("FACE_READING_AI_NARRATOR", "1") or "1").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    return _get_client() is not None


def _default_model() -> str:
    return (os.environ.get("FACE_READING_AI_MODEL") or "gpt-4o").strip() or "gpt-4o"


def _get_client():
    try:
        from numerology.core.ai_narrator import _get_client as _nc
        return _nc()
    except Exception:
        return None


def _flatten_facts(obj: Any, prefix: str = "", depth: int = 0, out: Optional[Dict[str, Any]] = None,
                   limit: int = 40) -> Dict[str, Any]:
    if out is None:
        out = {}
    if len(out) >= limit or depth > 2:
        return out
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.startswith("_"):
                continue
            key = f"{prefix}.{k}" if prefix else str(k)
            if isinstance(v, (str, int, float, bool)) and str(v).strip():
                out[key] = v
            elif isinstance(v, dict):
                _flatten_facts(v, key, depth + 1, out, limit)
            elif isinstance(v, list) and v and isinstance(v[0], (str, int, float)):
                out[key] = ", ".join(str(x) for x in v[:8])
    return out


def _engines_fingerprint(engines: Dict[str, Any], bundle: Optional[Any] = None) -> str:
    """Stable id for narration cache (FaceSignalBundle preferred)."""
    if bundle is not None:
        try:
            return bundle.fingerprint()
        except Exception:
            pass
    payload = json.dumps(_engine_highlights(engines), sort_keys=True, default=str)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


def _cache_person_key(
    person: Dict[str, Any],
    engines: Dict[str, Any],
    session_id: Optional[str] = None,
    bundle: Optional[Any] = None,
) -> tuple[str, str]:
    """(name, dob-slot) for narration_cache — dob holds face fingerprint."""
    name = (person.get("name") or "").strip() or "face_user"
    fp = _engines_fingerprint(engines, bundle=bundle)
    if session_id:
        fp = f"{fp}:{session_id[:12]}"
    return name, fp


def _face_group_size(n_specs: int) -> int:
    """Default: one OpenAI call for the whole report (cost-optimal)."""
    raw = (os.environ.get("FACE_READING_AI_GROUP_SIZE") or "0").strip().lower()
    if raw in ("", "0", "all", "single", "one"):
        return max(1, n_specs)
    try:
        return max(1, int(raw))
    except ValueError:
        return max(1, n_specs)


def _engine_highlights(engines: Dict[str, Any]) -> Dict[str, Any]:
    anth = engines.get("anthropometry") or {}
    pers = engines.get("personality") or {}
    samu = engines.get("samudrika") or {}
    sym = engines.get("symmetry") or {}
    fi = engines.get("first_impression") or {}
    fs = engines.get("final_scores") or {}
    return {
        "face_shape": (anth.get("face_shape_7") or {}).get("class"),
        "fwhr_class": (engines.get("fwhr") or {}).get("class"),
        "archetype": (pers.get("archetype") or {}).get("name") or (pers.get("archetype") or {}).get("label"),
        "dominant_element": (samu.get("element_profile") or {}).get("dominant_element"),
        "symmetry_score": (sym.get("overall") or {}).get("score"),
        "charisma_score": fs.get("charisma") or (fi.get("charisma") or {}).get("score"),
        "vitality_score": fs.get("vitality"),
        "leadership_score": fs.get("leadership"),
        "ocean": pers.get("ocean_summary_scores"),
    }


def _facts_for_section(
    section_key: str,
    bundle: Any,
    person: Dict[str, Any],
    used_signals: Optional[set] = None,
    *,
    hook_seed: str = "",
) -> Dict[str, Any]:
    """Compact focus facts from FaceSignalBundle only (no engine dump)."""
    from .face_signal_bundle import section_focus_signals

    lines, facts = section_focus_signals(section_key, bundle, used_signals)
    facts["section"] = section_key
    if person.get("age") is not None:
        facts["age_band"] = str(person.get("age"))
    if hook_seed:
        facts["hook_seed"] = hook_seed[:80]
    facts["_focus_lines"] = lines
    return facts


def _has_fact(text: str, facts: Dict[str, Any], bundle: Optional[Any] = None) -> bool:
    """Require bundle anchor in prose (no generic filler)."""
    if not text.strip():
        return False
    if bundle is not None:
        try:
            from .face_signal_bundle import validate_prose_against_bundle
            if validate_prose_against_bundle(text, bundle):
                return True
        except Exception:
            pass
    tl = text.lower()
    for k, v in facts.items():
        if k.startswith("_") or v is None or v == "":
            continue
        sv = str(v).strip()
        if len(sv) >= 4 and sv.lower() in tl:
            return True
    for anchor_key in ("archetype", "face_shape", "hook_seed"):
        av = facts.get(anchor_key)
        if av and str(av).lower() in tl:
            return True
    return False


_FACE_ASTRO_BANNED = (
    "kundli", "mahadasha", "nakshatra", "rashi", "dasha", "gochar",
    "manglik", "kaal sarp", "horoscope", "zodiac", "graha", "mantra",
    "yantra", "gemstone", "bphs", "10th house", "12th house",
)


def _passes_face_scope(text: str, section_key: str) -> bool:
    sk = (section_key or "").lower()
    if not (sk.startswith("faceread.") or sk.startswith("section_")):
        return True
    low = text.lower()
    return not any(t in low for t in _FACE_ASTRO_BANNED)


def _ai_mode() -> str:
    """selective (default) | full | allowlist via FACE_READING_AI_SECTIONS."""
    return (os.environ.get("FACE_READING_AI_MODE") or "selective").strip().lower()


def _ai_allowlist() -> Optional[frozenset]:
    raw = (os.environ.get("FACE_READING_AI_SECTIONS") or "").strip()
    if not raw:
        return None
    return frozenset(x.strip() for x in raw.split(",") if x.strip())


def _template_is_strong(
    key: str, fallback: str, facts: Dict[str, Any], bundle: Optional[Any] = None
) -> bool:
    """True when engine-written template is long, fact-anchored, and voice-safe."""
    fb = (fallback or "").strip()
    if not fb:
        return False
    sec_key = key if key.startswith("faceread.") else f"faceread.{key}"
    if key.startswith("faceread."):
        return (
            len(fb) >= 55
            and _has_fact(fb, facts, bundle)
            and passes_face_voice_combined(fb, sec_key)
        )
    min_len = 380 if key in _AI_PRIORITY else 300
    return (
        len(fb) >= min_len
        and _has_fact(fb, facts, bundle)
        and passes_face_voice_combined(fb, sec_key)
        and _passes_face_scope(fb, sec_key)
    )


def _section_needs_ai(
    key: str, fallback: str, facts: Dict[str, Any], bundle: Optional[Any] = None
) -> bool:
    """
    Selective mode: only sections that still need gpt-4o prose go to OpenAI.
    PDF layout/tables/scores never enter the prompt — only this section's facts.
    """
    mode = _ai_mode()
    if mode in ("0", "off", "none"):
        return False
    if mode in ("full", "all", "every"):
        return key not in _AI_NEVER

    allow = _ai_allowlist()
    if allow is not None:
        return key in allow

    # selective (default)
    if key in _AI_NEVER:
        return False
    if _template_is_strong(key, fallback, facts, bundle):
        return False
    if key in _AI_ALWAYS:
        return True
    if key in _AI_PRIORITY:
        return True
    # Secondary sections: AI only when template is thin or weak
    fb = (fallback or "").strip()
    if len(fb) < 200:
        return True
    if not _has_fact(fb, facts, bundle):
        return True
    return not passes_face_voice_combined(fb, f"faceread.{key}")


def _legacy_facts_payload_size(
    engines: Dict[str, Any],
    ordered_sections: List[Dict],
    person: Dict[str, Any],
) -> int:
    """Bytes estimate of old flatten+highlights per section (logging only)."""
    total = len(json.dumps(_engine_highlights(engines), default=str))
    for sec in ordered_sections:
        key = sec.get("key") or ""
        content = sec.get("content") or {}
        if not key:
            continue
        facts = dict(_engine_highlights(engines))
        if isinstance(content, dict):
            facts.update(_flatten_facts(content, limit=28))
        total += len(json.dumps(facts, default=str))
    return total


def _build_specs(
    ordered_sections: List[Dict],
    engines: Dict,
    person: Dict,
    hook: Dict,
    tldr: Dict,
    lang: str,
    bundle: Any,
) -> List[Dict[str, Any]]:
    from .face_signal_bundle import SECTION_GOALS, estimate_bundle_prompt_size

    specs: List[Dict[str, Any]] = []
    skipped = 0
    used_signals: set = set()

    for sec in ordered_sections:
        key = sec.get("key") or ""
        if not key:
            continue
        facts = _facts_for_section(key, bundle, person, used_signals)
        fallback = (sec.get("narrative") or "").strip()
        if not _section_needs_ai(key, fallback, facts, bundle):
            skipped += 1
            continue
        wt = WORD_TARGETS.get(key, 190)
        mode = "emotional_insight" if key in _EMOTIONAL_SECTIONS else "consultation"
        goal = SECTION_GOALS.get(key, "Behavioral insight")
        focus_lines = facts.get("_focus_lines") or []
        specs.append({
            "key": key,
            "section_key": f"faceread.{key}",
            "lang": lang,
            "word_target": wt,
            "facts": facts,
            "fallback": fallback,
            "mode_hint": (
                f"MODE: {mode}\nGOAL: {goal}\n"
                f"USE ONLY THESE SIGNALS:\n"
                + "\n".join(f"  • {ln}" for ln in focus_lines)
                + f"\n{section_angle_hint(key)}"
            ),
        })
    if hook:
        for hk, hfallback, hint in (
            ("faceread.hook_identity", hook.get("identity_line", ""),
             "MODE: short_sharp — one precise identity observation; hedged; no hype"),
            ("faceread.hook_shock", hook.get("shock_line", ""),
             "MODE: short_sharp — one non-obvious pattern (merge 2+ signals); "
             "say 'pattern suggests' not 'shocking truth'"),
        ):
            facts = _facts_for_section(
                hk, bundle, person, used_signals,
                hook_seed=(hfallback or ""),
            )
            if not _section_needs_ai(hk, (hfallback or "").strip(), facts, bundle):
                skipped += 1
                continue
            focus_lines = facts.get("_focus_lines") or []
            specs.append({
                "key": hk,
                "section_key": hk,
                "lang": lang,
                "word_target": WORD_TARGETS[hk],
                "facts": facts,
                "fallback": (hfallback or "").strip(),
                "mode_hint": hint + "\nSIGNALS:\n" + "\n".join(f"  • {ln}" for ln in focus_lines),
            })
    if tldr:
        facts = _facts_for_section("faceread.tldr", bundle, person, used_signals)
        tfb = (tldr.get("summary_paragraph") or "").strip()
        if _section_needs_ai("faceread.tldr", tfb, facts, bundle):
            focus_lines = facts.get("_focus_lines") or []
            specs.append({
                "key": "faceread.tldr",
                "section_key": "faceread.tldr",
                "lang": lang,
                "word_target": WORD_TARGETS["faceread.tldr"],
                "facts": facts,
                "fallback": tfb,
                "mode_hint": (
                    "MODE: practical_guidance — TL;DR for skimmers\n"
                    + "\n".join(f"  • {ln}" for ln in focus_lines)
                ),
            })
        else:
            skipped += 1

    if specs:
        old_b = _legacy_facts_payload_size(engines, ordered_sections, person)
        new_b = estimate_bundle_prompt_size(bundle, len(specs))
        pct = int(100 * (1 - new_b / max(old_b, 1)))
        print(
            f"[face_ai] selective mode={_ai_mode()}: "
            f"{len(specs)} sections → OpenAI, {skipped} template; "
            f"prompt facts ~{new_b}B vs legacy ~{old_b}B (~{pct}% smaller)"
        )
    elif skipped:
        print(f"[face_ai] selective: all {skipped} blocks use engine template — 0 OpenAI calls")
    return specs


def _call_grouped(
    group: list, lang: str, model: str, bundle: Optional[Any] = None
) -> Dict[str, str]:
    from numerology.core.report_voice import (
        LANG_INSTRUCT,
        VOICE_GUIDE,
        passes_voice_quality,
        post_process_prose,
    )
    from .consistency_layer import clean_internal_labels

    client = _get_client()
    if not client:
        return {}

    # Narrator uses en | hi | hinglish; LANG_INSTRUCT keys are english | hindi | hinglish.
    _lang_norm = {
        "en": "english",
        "eng": "english",
        "english": "english",
        "hi": "hindi",
        "hin": "hindi",
        "hindi": "hindi",
        "hn": "hinglish",
        "hg": "hinglish",
        "hinglish": "hinglish",
    }.get((lang or "").strip().lower(), "hinglish")
    lang = _lang_norm if _lang_norm in LANG_INSTRUCT else "hinglish"
    lang_rule = LANG_INSTRUCT[lang]
    sys_prompt = (
        VOICE_GUIDE
        + FACE_VOICE_ADDENDUM
        + f"\n\nLANGUAGE RULE: {lang_rule}\n"
        + "\nOUTPUT FORMAT: Single JSON object; keys = exact section keys from user message.\n"
        + "FACE READING ONLY — no numerology, no kundli dasha, no nakshatra.\n"
        + "LENGTH: Honour each section word_target (±10%). Dense insight > filler.\n"
        + "BATCH RULE: Each section must use its unique ANGLE — do NOT reuse the same "
        + "adjectives (warm/balanced/emotional/thoughtful) across sections.\n"
        + "SIGNAL RULE: Use ONLY FaceSignalBundle + per-section SIGNALS. "
        + "Do not invent numbers, diagnoses, or astrology.\n"
    )

    bundle_block = ""
    if bundle is not None:
        try:
            conf = (bundle.confidence_levels or {}).get("note", "moderate")
            bundle_block = (
                "FACE_SIGNAL_BUNDLE (single source of truth — do not repeat raw metrics):\n"
                + bundle.to_prompt_json()
                + f"\noverall_confidence_note: {conf}\n\n"
            )
        except Exception:
            pass

    sections_text = []
    keys_list = []
    for spec in group:
        keys_list.append(spec["key"])
        sections_text.append(
            f"━━━ [{spec['key']}] ~{spec.get('word_target', 190)} words ━━━\n"
            f"{spec.get('mode_hint', '')}\n"
            f"STRUCTURE: observation → interpretation → practical implication → growth (woven, no headings)\n"
        )

    user_prompt = (
        bundle_block
        + f"Write {len(group)} psychologically responsible face-intelligence sections in {lang}.\n"
        f"Return JSON with keys: {json.dumps(keys_list)}\n"
        f"Sections: {', '.join(keys_list)} — each must add NEW information; cite bundle tensions where relevant.\n\n"
        + "\n\n".join(sections_text)
    )

    total_words = sum(int(s.get("word_target", 190)) for s in group)
    max_tok = min(16384, max(1200, int(total_words * 2.2) + 600))

    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.48,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tok,
            response_format={"type": "json_object"},
        )
        try:
            from .token_analytics import record_from_response

            record_from_response(
                resp,
                model,
                phase="batch",
                lang=lang,
            )
        except Exception:
            pass
        raw = (resp.choices[0].message.content or "").strip()
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            return {}
        out: Dict[str, str] = {}
        for spec in group:
            k = spec["key"]
            txt = clean_internal_labels(
                post_process_prose((parsed.get(k) or "").strip())
            )
            if not txt:
                continue
            if not _has_fact(txt, spec.get("facts") or {}, bundle):
                print(f"[face_ai] {k} failed fact-guard")
                continue
            if not passes_face_voice_combined(txt, spec.get("section_key", k)):
                print(f"[face_ai] {k} failed voice-quality")
                continue
            if not _passes_face_scope(txt, spec.get("section_key", k)):
                print(f"[face_ai] {k} failed scope (astro/kundli leak)")
                continue
            out[k] = txt
        return out
    except Exception as exc:
        print(f"[face_ai] grouped call failed ({len(group)} sections): {exc}")
        return {}


def narrate_face_batch(
    specs: List[Dict[str, Any]],
    lang: str = "hinglish",
    group_size: Optional[int] = None,
    *,
    person: Optional[Dict[str, Any]] = None,
    engines: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
    analysis_id: Optional[str] = None,
    bundle: Optional[Any] = None,
) -> Dict[str, str]:
    """
    Run grouped gpt-4o calls; return {key: prose} for AI successes only.

    Default: ONE API call for all sections (FACE_READING_AI_GROUP_SIZE=0).
    Disk cache + daily cap reuse numerology.core.narration_cache.
    On failure, splits into at most 2 half-batches (never 5+ duplicate calls).
    """
    if not specs:
        return {}

    nc = None
    try:
        from numerology.core import narration_cache as nc_mod
        nc = nc_mod
    except Exception:
        nc = None

    if nc and nc.is_daily_capped():
        print("[face_ai] daily OpenAI cap reached — using template fallbacks")
        return {}
    try:
        from .face_cache import is_daily_token_capped

        if is_daily_token_capped():
            print("[face_ai] Redis token cap reached — using template fallbacks")
            return {}
    except Exception:
        pass

    person = person or {}
    engines = engines or {}
    c_name, c_fp = _cache_person_key(person, engines, session_id, bundle=bundle)

    results: Dict[str, str] = {}
    pending: List[Dict[str, Any]] = []
    cache_hits = 0

    for spec in specs:
        k = spec["key"]
        sec_key = spec.get("section_key") or f"faceread.{k}"
        facts = spec.get("facts") or {}
        if nc:
            cached = nc.get(
                c_name, c_fp, lang, sec_key, facts, version=FACE_CACHE_VERSION
            )
            if cached:
                results[k] = cached
                cache_hits += 1
                continue
        pending.append(spec)

    if cache_hits:
        print(f"[face_ai] cache hits={cache_hits}/{len(specs)} lang={lang}")

    if not pending:
        return results

    model = _default_model()
    gs = group_size if group_size is not None else _face_group_size(len(pending))
    api_calls = 0

    def _apply_group(group: List[Dict[str, Any]]) -> None:
        nonlocal api_calls
        if not group:
            return
        api_calls += 1
        got = _call_grouped(group, lang, model, bundle=bundle)
        for spec in group:
            k = spec["key"]
            txt = (got.get(k) or "").strip()
            if not txt:
                continue
            results[k] = txt
            if nc:
                try:
                    nc.put(
                        c_name,
                        c_fp,
                        lang,
                        spec.get("section_key") or f"faceread.{k}",
                        spec.get("facts") or {},
                        txt,
                        version=FACE_CACHE_VERSION,
                    )
                except Exception:
                    pass

    def _pending_ok() -> int:
        return sum(1 for s in pending if results.get(s["key"]))

    # Prefer a single grouped call for the whole pending set.
    if gs >= len(pending):
        _apply_group(pending)
        min_ok = max(3, int(len(pending) * 0.35))
        if _pending_ok() >= min_ok:
            print(
                f"[face_ai] lang={lang}: {api_calls} OpenAI call(s), "
                f"{len(results)}/{len(specs)} sections OK"
            )
            return results
        # Truncated / failed — retry missing only, in two halves (max +2 calls).
        if len(pending) > 6 and os.environ.get("FACE_READING_AI_SPLIT_ON_FAIL", "1") == "1":
            missing = [s for s in pending if not results.get(s["key"])]
            if missing:
                mid = len(missing) // 2
                print(
                    f"[face_ai] single-call weak ({_pending_ok()}/{len(pending)}) "
                    f"— retry {len(missing)} sections in 2 halves"
                )
                _apply_group(missing[:mid])
                _apply_group(missing[mid:])
    else:
        for i in range(0, len(pending), gs):
            _apply_group(pending[i:i + gs])

    print(
        f"[face_ai] lang={lang}: {api_calls} OpenAI call(s), "
        f"{len(results)}/{len(specs)} sections OK"
    )
    return results


def enrich_face_narratives(
    ordered_sections: List[Dict],
    *,
    engines: Dict[str, Any],
    person: Dict[str, Any],
    hook: Optional[Dict[str, Any]] = None,
    tldr: Optional[Dict[str, Any]] = None,
    lang: str = "hinglish",
    session_id: Optional[str] = None,
    analysis_id: Optional[str] = None,
    legacy_sections: Optional[Dict[str, Any]] = None,
) -> bool:
    """Replace template narratives with gpt-4o prose. Returns True if any AI text applied."""
    if not ai_enabled():
        return False

    first_key = (ordered_sections[0].get("key") if ordered_sections else "") or ""
    if first_key.startswith("block_"):
        try:
            from .face_ai_orchestrator import enrich_12_blocks, use_two_pass

            if use_two_pass():
                return enrich_12_blocks(
                    ordered_sections,
                    engines=engines,
                    legacy_sections=legacy_sections or {
                        (s.get("key") or ""): (s.get("content") or {})
                        for s in ordered_sections
                    },
                    person=person,
                    hook=hook,
                    tldr=tldr,
                    lang=lang,
                    session_id=session_id,
                    analysis_id=analysis_id,
                )
        except Exception as exc:
            print(f"[face_ai] 12-block delegate failed, legacy path: {exc}")

    try:
        from .face_cache import is_daily_token_capped

        if is_daily_token_capped():
            print("[face_ai] face token daily cap — skipping OpenAI")
            return False
    except Exception:
        pass

    hook = hook or {}
    tldr = tldr or {}
    sections_map = {
        (s.get("key") or ""): (s.get("content") or {})
        for s in ordered_sections
        if s.get("key")
    }

    from .face_signal_bundle import build_face_signal_bundle, load_bundle_for_analysis

    snapshot = None
    if analysis_id:
        try:
            from .face_cache import get_analysis

            snapshot = get_analysis(analysis_id)
        except Exception:
            snapshot = None

    bundle = load_bundle_for_analysis(
        engines,
        sections_map,
        person=person,
        snapshot=snapshot,
        hook=hook,
        tldr=tldr,
    )

    specs = _build_specs(
        ordered_sections, engines, person, hook, tldr, lang, bundle
    )
    if not specs:
        return False

    print(
        f"[face_ai] OpenAI for {len(specs)} block(s) via FaceSignalBundle "
        f"model={_default_model()} lang={lang} fp={bundle.fingerprint()[:8]}"
    )
    texts = narrate_face_batch(
        specs,
        lang=lang,
        person=person,
        engines=engines,
        session_id=session_id,
        analysis_id=analysis_id,
        bundle=bundle,
    )

    applied = False
    for sec in ordered_sections:
        k = sec.get("key")
        ai_txt = (texts.get(k) or "").strip() if k else ""
        if ai_txt:
            sec["narrative"] = ai_txt
            applied = True

    if (texts.get("faceread.hook_identity") or "").strip():
        hook["identity_line"] = texts["faceread.hook_identity"].strip()
        applied = True
    if (texts.get("faceread.hook_shock") or "").strip():
        hook["shock_line"] = texts["faceread.hook_shock"].strip()
        applied = True
    if (texts.get("faceread.tldr") or "").strip():
        tldr["summary_paragraph"] = texts["faceread.tldr"].strip()
        applied = True

    return applied
