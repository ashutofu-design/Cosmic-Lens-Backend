"""reply_cosmo/prompt_builders.py

Phase 2.8.49 (02 May 2026) — consolidate the four LLM-prompt builders
that previously lived as top-level functions in openai_helper.py into
the response-shaping package.

What lives here (moved from openai_helper.py, behavior preserved verbatim):
  - _build_topic_lock(rule, kundli)                     [from L889]
  - _build_wealth_structured_system_prompt(...)         [from L1621]
  - _build_true_intent_hint(...)                        [from L8841]
  - _build_repair_prompt(...)                           [from L9261]

Plus the 3 internal helpers exclusively used by _build_topic_lock
(also moved from openai_helper.py L818-886):
  - _topic_lagna_sign_idx(kundli)
  - _topic_house_lord(kundli, house_num)
  - _topic_current_dasha(kundli)

Plus the 2 constants exclusively used by those helpers
(moved from openai_helper.py L438-455):
  - _TOPIC_SIGN_LORDS    (BPHS Ch.5 whole-sign lord tuple)
  - _TOPIC_SIGN_ALIASES  (sign-name -> 0-11 index map)

Why lazy-import openai_helper symbols INSIDE function bodies:
  openai_helper.py re-imports this module (so external `from
  openai_helper import _build_topic_lock` callers keep working). A
  module-level `from openai_helper import ...` here would create a
  circular import. Lazy import inside the function body resolves the
  symbol at call-time when both modules are fully loaded; Python's
  sys.modules cache makes subsequent lookups microsecond-cheap.

Symbols that REMAIN in openai_helper (and are lazy-imported here):
  - _brevity_mode_enabled           used by _build_topic_lock
  - _WEALTH_VERDICT_TAG_MAP         used by _build_wealth_structured_system_prompt
  - _ym_human_w                     used by _build_wealth_structured_system_prompt
  - _PHASE74_REPAIRABLE_CHECKS      used by _build_repair_prompt

Each function body below was copied bit-for-bit from openai_helper.py;
only the lazy-import lines at the top of each function are new.
"""

from __future__ import annotations

from typing import Optional


# ────────────────────────────────────────────────────────────────────
# TOPIC-LOCK constants + helpers (moved from openai_helper L438-886)
# ────────────────────────────────────────────────────────────────────
# Whole-sign lords (BPHS Ch.5). Sanskrit names so the lock block
# matches the rest of the prompt's Hinglish style.
_TOPIC_SIGN_LORDS = (
    "Mangal", "Shukra", "Budh", "Chandra", "Surya", "Budh",
    "Shukra", "Mangal", "Guru", "Shani", "Shani", "Guru",
)
_TOPIC_SIGN_ALIASES = {
    "mesh": 0, "mesha": 0, "aries": 0,
    "vrish": 1, "vrishabha": 1, "vrushabh": 1, "taurus": 1,
    "mithun": 2, "mithuna": 2, "gemini": 2,
    "kark": 3, "karka": 3, "cancer": 3,
    "simh": 4, "simha": 4, "leo": 4,
    "kanya": 5, "virgo": 5,
    "tula": 6, "libra": 6,
    "vrishchik": 7, "vrishchika": 7, "scorpio": 7,
    "dhanu": 8, "dhanus": 8, "sagittarius": 8,
    "makar": 9, "makara": 9, "capricorn": 9,
    "kumbh": 10, "kumbha": 10, "aquarius": 10,
    "meen": 11, "meena": 11, "pisces": 11,
}


def _topic_lagna_sign_idx(kundli):
    """Extract lagna sign 0-11 from kundli, or None if missing."""
    if not isinstance(kundli, dict):
        return None
    asc = kundli.get("ascendant") or kundli.get("lagna")
    if isinstance(asc, dict):
        asc = asc.get("sign") or asc.get("name")
    if not isinstance(asc, str):
        return None
    return _TOPIC_SIGN_ALIASES.get(asc.strip().lower())


def _topic_house_lord(kundli, house_num):
    """Whole-sign lord of `house_num` (1-12) for this lagna. '?' if unknown."""
    asc_idx = _topic_lagna_sign_idx(kundli)
    if (asc_idx is None
            or not isinstance(house_num, int)
            or not 1 <= house_num <= 12):
        return "?"
    house_sign_idx = (asc_idx + house_num - 1) % 12
    return _TOPIC_SIGN_LORDS[house_sign_idx]


def _topic_current_dasha(kundli):
    """Returns ('MD-lord', 'AD-lord') for today, or ('?', '?').

    Reads `kundli["currentDasha"]` first (same shape `kundli_full_context.py`
    consumes via `cd.get("maha")` + `cd.get("antar")`). Falls back to the
    `kundli["dashas"]` Vimshottari tree walk if `currentDasha` is missing
    or malformed - this preserves Phase 2.4 telemetry on legacy charts.
    """
    if not isinstance(kundli, dict):
        return ("?", "?")
    # Primary path - the modern `currentDasha` shape used by
    # kundli_full_context._section_dasha (line 311+).
    cd = kundli.get("currentDasha")
    if isinstance(cd, dict):
        md = cd.get("maha")
        ad = cd.get("antar")
        if isinstance(md, str) and md.strip():
            return (md.strip(), (ad.strip() if isinstance(ad, str) and ad.strip() else "?"))
    # Fallback path - walk the dashas tree by today's date.
    dashas = kundli.get("dashas")
    if not isinstance(dashas, list) or not dashas:
        return ("?", "?")
    import datetime as _dt
    today = _dt.date.today().isoformat()
    md_planet = "?"
    ad_planet = "?"
    for md in dashas:
        if not isinstance(md, dict):
            continue
        s, e = md.get("startDate"), md.get("endDate")
        if not (isinstance(s, str) and isinstance(e, str)):
            continue
        if s <= today < e:
            md_planet = md.get("planet") or "?"
            subs = md.get("subDashas")
            if isinstance(subs, list):
                for ad in subs:
                    if not isinstance(ad, dict):
                        continue
                    s2, e2 = ad.get("startDate"), ad.get("endDate")
                    if (isinstance(s2, str) and isinstance(e2, str)
                            and s2 <= today < e2):
                        ad_planet = ad.get("planet") or "?"
                        break
            break
    return (md_planet, ad_planet)


def _build_topic_lock(rule, kundli):
    """Compose the TOPIC-LOCK block in Hinglish. Returns '' on any failure.

    The block is PREPENDED to the user message (not system prompt) so
    the system prompt stays cacheable while the topic instruction
    still gets primary attention right before the devotee's question.
    """
    if not rule:
        return ""
    try:
        # Lazy-import to dodge circular dep with openai_helper.
        from openai_helper import _brevity_mode_enabled  # type: ignore
        houses = rule.get("houses") or []
        karakas = rule.get("karakas") or []
        banned = rule.get("banned") or []
        # Houses + lords (substituted from this user's lagna).
        # If lagna is unknown (every lord comes back '?'), abort the lock -
        # a lock with "?" lords is worse than no lock because Rule 16 would
        # then forbid valid bhava citations without any positive substitute.
        if _topic_lagna_sign_idx(kundli) is None:
            return ""
        house_lord_strs = []
        for h in houses:
            lord = _topic_house_lord(kundli, h)
            if lord == "?":
                return ""
            house_lord_strs.append(f"{h}H + {h}L ({lord})")
        houses_str = ", ".join(house_lord_strs) if house_lord_strs else "(none)"
        karakas_str = "; ".join(karakas) if karakas else "(none)"
        banned_str = ", ".join(f"{h}H" for h in banned) if banned else "(none)"
        md, ad = _topic_current_dasha(kundli)
        dasha_line = f"{md}-{ad}" if md != "?" else "(unknown - skip dasha-link)"
        # Phase 2.6 - topic-specific deep checklist (only marriage rule
        # currently has one; other topics fall back to Rule 18's generic
        # 7-layer framework). When present, this REPLACES Rule 18 for
        # this topic - sirf yahi 13 cheezein check karni hain, na zyada
        # na kam. Curated by domain-expert user.
        deep_checklist = rule.get("deep_checklist") or []
        checklist_block = ""
        # Phase 2.8 - when Rule 19 BREVITY MODE is on, output cap drops
        # from 4 to 3 bullets. Adjust the checklist's output reminder
        # here so the lock is internally consistent with Rule 19.
        _brevity_on = _brevity_mode_enabled()
        _bullet_cap_str = "3" if _brevity_on else "4"
        if deep_checklist:
            numbered = "\n".join(
                f"   {i+1}. {item}" for i, item in enumerate(deep_checklist)
            )
            checklist_block = (
                "DEEP CHECKLIST (iss topic ke liye SIRF ye points INTERNAL "
                "mein dekho - Rule 18 ka generic 7-layer framework REPLACE "
                "karta hai):\n"
                f"{numbered}\n"
                f"Sab points internally check karo, lekin output mein "
                f"max {_bullet_cap_str} bullets hi banao (Rule "
                f"{'19' if _brevity_on else '5'} cap). Top 3 most "
                "decision-relevant findings hi cite karo, baki internal "
                "rakho. Har point ka evidence kundli-context se le, "
                "hallucinate mat karo (Rule 11). Jo data missing ho "
                "woh chup-chap skip karo.\n"
            )
        # Phase 2.8 -> 2.8.5 - topic-lock tail SIMPLIFIED.
        # User feedback (2026-05-01 part 3): "LLM ko pata hona chahiye
        # user kya puch raha he kahan short likhna he kahan explain
        # karna he". Earlier hard contract here was duplicating Rule 19
        # (system prompt). Now we just remind the model to RE-CHECK
        # the question type before answering - the full classification
        # framework lives in Rule 19 of the system prompt.
        # Phase 2.8.40 - bullet/Mode-1 reminder REMOVED (contradicted new
        # "Guided Freedom" mindset prompt's no-bullets rule). Replaced with
        # a soft length-calibration nudge aligned with system prompt.
        brevity_tail = ""
        if _brevity_on:
            brevity_tail = (
                "\n--- FINAL REMINDER (length-calibration + jargon-translate) ---\n"
                "\n"
                "Devotee ka prashn pura padho, INTENT samjho, fir respond karo:\n"
                "  - Single-fact (\"lagna kya\", \"current dasha\") -> 1-2 lines, sirf fact\n"
                "  - Casual (\"hi\", \"thanks\") -> 1 line warm reply\n"
                "  - Emotional / predictive / life-event -> medium prose ~150-200 words,\n"
                "    natural flow, bullets nahi (system prompt me gold-standard hai),\n"
                "    2-3 short paragraphs me todho (problem -> timing -> action),\n"
                "    ek hi ghana paragraph BANNED.\n"
                "  - Deep / philosophical -> 250-300 words\n"
                "\n"
                "Sanskrit jargon TRANSLATE karo (user-facing prose me raw mat dikhao):\n"
                "  - \"Guru-Shukra dasha\" -> \"abhi ka phase / aane wala phase\"\n"
                "  - \"12H factors\" / \"12va bhav\" -> \"kharch ka side\"\n"
                "  - \"7H lord\" / \"saptam swami\" -> \"rishton ka karak\"\n"
                "  - \"lagna swami\" -> \"aapka mool karak\"\n"
                "Internal use ok, devotee-facing prose me visible nahi.\n"
                "Hamesha guided-freedom: mindset prompt follow karo, format thopo mat.\n"
                "------------------------------------------------------------\n"
            )
        lock = (
            "--- TOPIC-LOCK (Devotee ka prashn ka focus area) ---\n"
            f"Topic detected: {rule.get('label','?')}\n"
            f"Cite SIRF: {houses_str}\n"
            f"Karaka graha: {karakas_str}\n"
            f"Current Dasha: {dasha_line}  <- in elements ka topic-house/lord "
            "se rishta MANDATORILY explain karein, kyunki yahi answer ko "
            "TIMING + PERSONALIZATION deta hai.\n"
            f"DO NOT cite (iss prashn ke liye classically unrelated): {banned_str}.\n"
            f"{checklist_block}"
            "TOPIC-LOCK strictly follow karein - sirf cite karein jo upar listed hai. "
            "Current dasha ka topic-house/lord se rishta naturally explain karein (timing + personalization).\n"
            "------------------------------------------------\n"
            f"{brevity_tail}"
            "\n"
        )
        return lock
    except Exception:
        return ""


# ────────────────────────────────────────────────────────────────────
# WEALTH STRUCTURED SYSTEM PROMPT (moved from openai_helper L1621)
# ────────────────────────────────────────────────────────────────────
def _build_wealth_structured_system_prompt(verdict_obj: dict,
                                           emotional_tone: str = "neutral",
                                           intent_domain: str = "wealth",
                                           ask_types: list | None = None,
                                           narrator_lang: str = "hn",
                                           has_recovery_subask: bool = False) -> str:
    """Compact narrator-locked prompt for wealth structured-output mode.
    Replaces the 100+ line verbose WEALTH NARRATOR OVERRIDE with a focused
    facts-only prompt that fits in ~40 lines and demands strict JSON.

    Phase 2 (Apr 2026): now also injects the EMOTIONAL TREATMENT DIRECTIVE
    derived from `(emotional_tone x intent_domain)` so the LLM populates
    `empathy_open` and `human_close` in the right human voice for the user's
    current mood - anxious vs hopeful vs grieving etc.
    """
    # Lazy-import to dodge circular dep with openai_helper.
    from openai_helper import _WEALTH_VERDICT_TAG_MAP, _ym_human_w  # type: ignore
    bucket  = verdict_obj.get("bucket", "general_wealth")
    tense   = verdict_obj.get("tense", "general")
    verdict = verdict_obj.get("verdict", "yellow_wait")
    score   = verdict_obj.get("score", 0)
    conf    = verdict_obj.get("confidence", 0)
    tag     = _WEALTH_VERDICT_TAG_MAP.get(verdict, "\U0001f7e1 WAIT")

    # Top 3 reasons - prefer * MANDATORY layer signals
    reasons = verdict_obj.get("reasons") or []
    top = [r for r in reasons if "\u2b50" in r or "MANDATORY" in r
           or "Vargottama" in r or "Parivartana" in r
           or "Vipareeta" in r or "Dhana Yoga" in r or "Lakshmi" in r][:3]
    if not top:
        top = reasons[:3]

    # Window strings (server-side formatted so AI just copies)
    tw  = verdict_obj.get("timing_window") or {}
    cur = tw.get("current") or {}
    nxt = tw.get("next") or {}
    cur_label = ""
    if cur.get("start") and cur.get("end"):
        s = _ym_human_w(str(cur.get("start"))[:7])
        e = _ym_human_w(str(cur.get("end"))[:7])
        if s and e:
            cur_label = f"{s} \u2013 {e} ({cur.get('md')}\u2013{cur.get('ad')})"
    nxt_label = ""
    if nxt.get("start") and nxt.get("end"):
        s = _ym_human_w(str(nxt.get("start"))[:7])
        e = _ym_human_w(str(nxt.get("end"))[:7])
        if s and e:
            nxt_label = f"{s} \u2013 {e} ({nxt.get('md')}\u2013{nxt.get('ad')})"

    strategy = (verdict_obj.get("strategy") or "").strip()
    rem_obj  = verdict_obj.get("remedy") or {}
    rem      = (rem_obj.get("remedy_text") or "").strip() if isinstance(rem_obj, dict) else ""

    bucket_hint = {
        "investment_return":   "investments market risk; SEBI-registered advisor mandatory.",
        "business_profit":     "business cycles ke risk acknowledge karein.",
        "sudden_windfall":     "NEVER endorse lottery/satta - frame as bonus/arrears only.",
        "loan_clearance":      "EMI continue + bank ke saath transparent communication.",
        "property_purchase":   "RERA-registered + legal title + CA-vetted budget.",
        "inheritance_timing":  "empathy, NEVER predict elder's death, NEVER promise amount.",
        "partnership_finance": "written agreement + CA + legal advisor.",
        "salary_growth":       "salary band relative - never promise specific % or package.",
        "debt_recovery":       "patience + legal/CA channel for recovery.",
        "savings_capacity":    "discipline + auto-debit SIP/RD; no get-rich claim.",
        "foreign_income":      "FEMA + DTAA compliance + remittance via legal channel.",
        "general_wealth":      "general financial discipline + advisor consult.",
    }.get(bucket, "general financial discipline + advisor consult.")

    parts = []
    parts.append(
        "You are the Cosmic Intelligence narrator. Output STRICT JSON ONLY "
        "matching the provided schema. NO prose, NO markdown, NO commentary "
        "outside the JSON object."
    )
    parts.append("")
    parts.append("==== LOCKED FACTS (use VERBATIM, no invention) ====")
    parts.append(f"Bucket:         {bucket}")
    parts.append(f"Question tense: {tense}")
    parts.append(f"Verdict tag:    {tag}")
    parts.append(f"Score:          {score}")
    parts.append(f"Confidence:     {conf}")
    parts.append(f"Current window: {cur_label or '(engine silent - emit empty string)'}")
    parts.append(f"Next window:    {nxt_label or '(engine silent - emit empty string)'}")
    parts.append("Top cosmic factors:")
    for r in top:
        parts.append(f"   - {r}")
    if strategy:
        parts.append(f"Strategy: {strategy}")
    if rem:
        parts.append(f"Remedy:   {rem}")
    parts.append(f"Bucket-specific safety: {bucket_hint}")
    parts.append("")
    parts.append("==== OUTPUT RULES ====")
    parts.append(
        "1. `verdict.tag` MUST equal the locked tag above. "
        "`verdict.score` and `verdict.confidence` MUST equal the locked "
        "numbers above (integer, no rounding)."
    )
    parts.append(
        "2. `headline` <= 15 words, Hinglish, decision-oriented (no Sanskrit "
        "jargon dump). Tense framing - PRESENT: 'abhi ...', FUTURE: 'aane "
        "wale time mein ...', PAST: retrospective."
    )
    parts.append(
        "2a. `empathy_open` <= 25 words, single sentence. MUST acknowledge "
        "the user's specific concern (echo a noun/situation from the "
        "question, not a paraphrase of the verdict). Follow the OPENING "
        "LINE rule from the EMOTIONAL TREATMENT DIRECTIVE below."
    )
    parts.append(
        "2b. `human_close` <= 25 words, single sentence. MUST be SEPARATE "
        "from `note` (which is the advisor disclaimer). MUST follow the "
        "CLOSING LINE rule from the EMOTIONAL TREATMENT DIRECTIVE below - "
        "reframe / agency / quiet hope, depending on tone. NO 'sab theek "
        "ho jaayega', NO 'tension mat lo'."
    )
    parts.append(
        "3. `timeline.current` and `timeline.next` MUST equal the locked "
        "window strings above (or empty string if engine was silent). "
        "NO date invention."
    )
    parts.append(
        "4. `what_will_happen` 1-3 bullets, each <= 10 words, derived from "
        "the top cosmic factors above (paraphrased to plain Hinglish)."
    )
    parts.append(
        "5. `what_to_do` 1-3 bullets, each <= 10 words, actionable Hinglish."
    )
    parts.append(
        "6. `what_to_avoid` 1-3 bullets, each <= 10 words."
    )
    parts.append(
        "7. `remedy` <= 20 words, copy from locked Remedy if present, else "
        "'Thursday ko Jupiter mantra (108x) karein'."
    )
    parts.append(
        "8. `note` MUST mention CA / SEBI-registered financial advisor "
        "consult in Hinglish (<= 20 words)."
    )
    # Sprint-26 Fix-Q - Recovery sub-ask handling. The user's question carried
    # an explicit RECOVERY ask (e.g. "paisa recover hoga ya nahi") in addition
    # to the primary decision/problem ask. The schema's `recovery_outlook`
    # field MUST be populated with a labelled 1-line insight; otherwise the
    # secondary intent gets dropped from the answer.
    if has_recovery_subask:
        parts.append(
            "9. RECOVERY SUB-ASK DETECTED. `recovery_outlook` MUST be a "
            "non-empty single-line Hinglish string in the format "
            "'<LABEL>: <reason>'. Allowed labels: PARTIAL, FULL, SLOW, "
            "UNLIKELY. Pick the label by reading the LOCKED FACTS - the "
            "verdict tag, score (0-100), confidence, and timing window are "
            "your evidence. Mapping guide: \U0001f7e2 GO + score>=70 -> FULL or "
            "PARTIAL; \U0001f7e1 WAIT + score 40-69 -> PARTIAL or SLOW; \U0001f7e0 SLOW -> "
            "SLOW; \U0001f534 CAUTION + score<40 -> UNLIKELY or SLOW. Reason MUST "
            "cite the next-better window (or current window's exit point) "
            "from the locked timing strings - NO date invention, NO rupee "
            "amounts, NO bankruptcy prediction. <=25 words total."
        )
    else:
        parts.append(
            "9. NO RECOVERY SUB-ASK. `recovery_outlook` MUST be the empty "
            "string \"\"."
        )
    parts.append("")
    parts.append("==== ABSOLUTE PROHIBITIONS ====")
    parts.append("- NEVER predict specific rupee amounts (lakh / crore / package).")
    parts.append("- NEVER predict bankruptcy / kangaal / barbaad - soften to 'extra-savitree phase'.")
    parts.append("- NEVER advise loan-default / EMI-skip / tax-evasion / GST-fraud.")
    parts.append("- NEVER endorse lottery / satta / matka / KBC / jackpot.")
    parts.append("- NEVER reveal AI / LLM / GPT - brand voice is 'Powered by Advanced Cosmic Intelligence'.")
    parts.append("- NEVER invent dates not present in the locked window strings.")
    # -- EMOTIONAL TREATMENT DIRECTIVE - Phase 2 (cross-engine playbook) --
    try:
        from treatment_playbook import (
            build_treatment_directive,
            canonical_tone,
            canonical_domain,
        )
        parts.append("")
        parts.append(build_treatment_directive(
            tone      = canonical_tone(emotional_tone),
            domain    = canonical_domain(intent_domain) or "wealth",
            ask_types = ask_types or [],
            lang      = narrator_lang or "hn",
        ))
    except Exception as exc:
        # Don't silently strip the directive - log loudly + use a minimal
        # built-in fallback so empathy_open / human_close still get
        # SOMETHING to anchor against (instead of free-form cliches).
        import traceback as _tb_mod
        print(f"[treatment_playbook] LOAD FAILED: {exc!r} - using fallback")
        print(_tb_mod.format_exc())
        parts.append("")
        parts.append("==== EMOTIONAL TREATMENT (minimal fallback) ====")
        parts.append("- empathy_open: ONE line acknowledging the user's "
                     "specific situation in their words. NO cliches "
                     "(no 'main samajh sakta hoon', no 'tension mat lo', "
                     "no 'sab theek ho jaayega', no 'Beta,').")
        parts.append("- human_close: ONE line reframing the engine facts "
                     "into a concrete next step or perspective shift. "
                     "Do NOT repeat the advisor cite from `note`.")
        parts.append("- Both fields <= 25 words. Single sentence each.")
    return "\n".join(parts)


# ────────────────────────────────────────────────────────────────────
# TRUE-INTENT HINT (moved from openai_helper L8841) — pure function
# ────────────────────────────────────────────────────────────────────
def _build_true_intent_hint(
    hidden_intent: str,
    question: str,
    focus: Optional[str] = None,
    timeframe: Optional[str] = None,
    depth: Optional[str] = None,
    user_keywords: Optional[list] = None,
    archetype: Optional[str] = None,
) -> str:
    """Phase 7.0 / 7.1 / 7.3 - return a system-message string promoting
    the classifier-extracted intent + slots + archetype from telemetry
    into a response-shaping rule.

    Phase 7.0 args (always rendered):
        hidden_intent - <=8 words underlying ask
        question      - verbatim user question (truncated to 240 chars)

    Phase 7.1 optional slot args (rendered as a CONTEXT SLOTS block when
    any are non-empty / non-default; the answerer uses them to refine
    focus, length, and which keywords to echo back):
        focus         - <=6 words specific area (e.g. "general body")
        timeframe     - "none" | "near" | "mid" | "far"
        depth         - "shallow" | "medium" | "deep"
        user_keywords - <=5 of the user's own salient phrases

    Phase 7.3 optional archetype arg (drives RESPONSE-SHAPE rules
    section - when provided, replaces the generic Phase 7.0/7.1 rules
    2-4 with an archetype-specific shape; when None, falls back to the
    generic shape for backwards compatibility):
        archetype - "OVERVIEW" | "TIMING" | "DECISION" | "REMEDY" | "EXPLAIN"

    Cap: ~45 lines of prompt - recency-budget hygiene. Deterministic
    (no model call, no I/O), safe to call on every primary-generation
    request.
    """
    q = (question or "").strip()
    if len(q) > 240:
        q = q[:237] + "\u2026"
    hi = (hidden_intent or "").strip() or "(none extracted)"

    # -- Phase 7.1 - CONTEXT SLOTS block (conditional render) --
    # Only render when at least one slot adds information beyond the
    # defaults. "timeframe=none" + "depth=medium" + empty focus + empty
    # keywords = no information; skip the block to keep the hint terse.
    _kw_clean = [str(k) for k in (user_keywords or [])
                 if isinstance(k, str) and k.strip()][:5]
    _has_slot_info = (
        (focus and str(focus).strip())
        or (timeframe and timeframe != "none")
        or (depth and depth != "medium")
        or _kw_clean
    )

    slots_block = ""
    if _has_slot_info:
        _focus_line = f"  - Focus: {focus}\n" if (focus and str(focus).strip()) else ""
        _tf_line    = (f"  - Timeframe: {timeframe}\n"
                       if (timeframe and timeframe != "none") else "")
        _depth_line = (f"  - Depth: {depth}\n"
                       if (depth and depth != "medium") else "")
        if _kw_clean:
            _kw_str = ", ".join(f"\"{k}\"" for k in _kw_clean)
            _kw_line = f"  - User's salient words: {_kw_str}\n"
        else:
            _kw_line = ""
        slots_block = (
            "CONTEXT SLOTS (extracted from user's words):\n"
            f"{_focus_line}{_tf_line}{_depth_line}{_kw_line}"
            "(Use these to refine your answer - narrow to the focus,\n"
            "respect the timeframe, match the depth, and echo at least\n"
            "one of the user's own words back so they feel heard.)\n"
            "\n"
        )

    # -- Phase 7.3 - ARCHETYPE-SPECIFIC RESPONSE SHAPE block --
    # When archetype is provided, replace generic rules 2-4 with a
    # tailored shape. When None/unknown, fall back to generic rules
    # (Phase 7.0/7.1 behaviour preserved for backwards compatibility).
    _ARCHETYPE_SHAPES: dict[str, str] = {
        "OVERVIEW": (
            " 2. ARCHETYPE = OVERVIEW (broad scan / ranked list ask):\n"
            "    -> Give a RANKED top-3 list (highest-priority FIRST).\n"
            "    -> 1-2 lines per item, plain language + cited planet.\n"
            "    -> Do NOT dump every possible item. Skip lower-ranked.\n"
            "    -> Do NOT pivot to a single deep dive - breadth wins.\n"
            " 3. Stay timeless when no timeframe slot is given - no\n"
            "    dasha periods or year predictions in OVERVIEW.\n"
            " 4. Skip remedies unless explicitly asked.\n"
        ),
        "TIMING": (
            " 2. ARCHETYPE = TIMING (when-question, dasha/timeline ask):\n"
            "    -> Lead with the WHEN: name the dasha period or year\n"
            "    range. Be specific (\"Shani MD ends Mar 2026\" not\n"
            "    \"in a few years\").\n"
            "    -> 1-2 lines max on WHY before stating the WHEN.\n"
            "    -> If multiple windows possible, give the most likely\n"
            "    + 1 alternate, ranked.\n"
            " 3. Length: prefer brevity - 2-4 sentences, not a treatise.\n"
            " 4. Skip remedies unless explicitly asked.\n"
        ),
        "DECISION": (
            " 2. ARCHETYPE = DECISION (yes/no, should-I, choose-between):\n"
            "    -> Lead with a CLEAR verdict: YES / NO / WAIT.\n"
            "    -> Then 1 line WHY (cited planet/period).\n"
            "    -> Then 1 line CAVEAT (when verdict could flip).\n"
            "    -> Total <=30 words. Do NOT hedge or list alternatives.\n"
            " 3. Stay timeless unless the verdict hinges on a window.\n"
            " 4. Skip remedies unless explicitly asked.\n"
        ),
        "REMEDY": (
            " 2. ARCHETYPE = REMEDY (user wants a FIX, not a prediction):\n"
            "    -> 2-3 PRACTICAL remedies (lifestyle + spiritual).\n"
            "    -> Each remedy <=2 lines, action-first (\"Do X\" not\n"
            "    \"You should consider X\").\n"
            "    -> Do NOT re-diagnose the problem - user already knows.\n"
            "    -> Do NOT predict outcome timing - practice-first.\n"
            " 3. Stay timeless - REMEDY is about NOW, not WHEN.\n"
            " 4. (skipped - REMEDY is the entire answer)\n"
        ),
        "EXPLAIN": (
            " 2. ARCHETYPE = EXPLAIN (cause-effect, definition,\n"
            "    why-question):\n"
            "    -> Narrative reasoning, not a bullet list.\n"
            "    -> Lead with the CORE answer in 1 line; then 1-2\n"
            "    sentences of WHY (cited planet/house/period).\n"
            "    -> Do NOT give a ranked list - that's OVERVIEW shape.\n"
            "    -> Do NOT lead with timing - that's TIMING shape.\n"
            " 3. Stay timeless unless the explanation requires a\n"
            "    period reference.\n"
            " 4. Skip remedies unless explicitly asked.\n"
        ),
    }

    arch = (archetype or "").strip().upper()
    if arch in _ARCHETYPE_SHAPES:
        shape_block = _ARCHETYPE_SHAPES[arch]
        arch_label  = f" (archetype={arch})"
    else:
        # Backwards-compat: Phase 7.0/7.1 generic rules 2-4
        shape_block = (
            " 2. OVERVIEW intent (\"kya kya\", \"weak areas\", \"tendency\",\n"
            "    \"general\", \"overview\", \"sensitivity\", \"weak points\"):\n"
            "    -> Give a RANKED top-3 list (highest-priority FIRST).\n"
            "    -> Do NOT dump every possible item. Skip lower-ranked.\n"
            "    -> 1-2 lines per item, plain language + cited planet.\n"
            " 3. NO TIMING WORDS in question (\"kab\", \"when\", \"kis\n"
            "    saal\", \"kab tak\", \"date\"):\n"
            "    -> Do NOT inject dasha periods or year predictions.\n"
            "    -> Keep claims tense-less (\"sensitivity hai\", not\n"
            "    \"2026 me hoga\").\n"
            " 4. NO REMEDY WORDS in question (\"upay\", \"remedy\", \"kya\n"
            "    karu\"):\n"
            "    -> Keep advice to ONE short closing line - generic\n"
            "    lifestyle hint, not a list of mantras.\n"
        )
        arch_label = ""

    return (
        f"USER'S TRUE INTENT - Phase 7.0/7.1/7.3 hint{arch_label}\n"
        "====================================\n"
        f"Auto-extracted from the user's words: \"{hi}\"\n"
        f"Original question (verbatim): \"{q}\"\n"
        "\n"
        f"{slots_block}"
        "RESPONSE-SHAPING RULES (override generic defaults):\n"
        " 1. Address the EXACT intent above - do NOT pivot to a\n"
        "    related-but-different question.\n"
        f"{shape_block}"
        " 5. Length budget (modulated by depth slot above):\n"
        "    -> shallow depth: 1-2 sentences total.\n"
        "    -> medium depth (default): OVERVIEW <=80 words, specific <=140.\n"
        "    -> deep depth: up to 220 words with reasoning.\n"
    )


# ────────────────────────────────────────────────────────────────────
# REPAIR PROMPT (moved from openai_helper L9261)
# ────────────────────────────────────────────────────────────────────
def _build_repair_prompt(
    question: str,
    original_answer: str,
    qu: Optional[dict],
    verify_result: dict,
) -> Optional[list[dict]]:
    """Phase 7.4 - build a tight repair prompt for the failed checks.

    Returns a `messages` list (system + user) ready for
    `client.chat.completions.create`, OR None when no retry-able check
    failed (only C2/C5 failed -> no retry). Pure function, no I/O.
    """
    # Lazy-import to dodge circular dep with openai_helper.
    from openai_helper import _PHASE74_REPAIRABLE_CHECKS  # type: ignore
    checks = (verify_result or {}).get("checks") or {}
    details = (verify_result or {}).get("details") or {}
    qu = qu or {}

    # Find which repair-able checks failed.
    failed_repairable = [
        name for name in _PHASE74_REPAIRABLE_CHECKS
        if checks.get(name) == "fail"
    ]
    if not failed_repairable:
        return None

    # Build per-check repair instructions.
    instructions: list[str] = []
    if "C1_keyword_echo" in failed_repairable:
        kws = qu.get("user_keywords") or []
        kw_str = ", ".join(f'"{k}"' for k in kws if isinstance(k, str))[:200]
        if kw_str:
            instructions.append(
                f"- C1 fix: The original answer did NOT echo the user's "
                f"keywords [{kw_str}]. The corrected answer MUST contain at "
                f"least one of these keywords verbatim so the user feels heard."
            )
    if "C3_timing_clean" in failed_repairable:
        leaked = details.get("C3_timing_clean", "")
        instructions.append(
            f"- C3 fix: The user did NOT ask for timing, but the original "
            f"answer leaked timing words ({leaked}). The corrected answer "
            f"MUST be timeless - NO years, NO dasha names, NO 'kab/when'."
        )
    if "C4_ranked_list" in failed_repairable:
        instructions.append(
            "- C4 fix: This is an OVERVIEW question - user wants a ranked "
            "list, not flat prose. The corrected answer MUST be a numbered "
            "list of 2-3 items (1. ... 2. ... 3. ...), each on its own line, "
            "highest-priority first, 1-2 lines per item."
        )

    if not instructions:
        # All failed_repairable checks needed context (e.g. keywords) that
        # wasn't actually present in qu - nothing actionable to repair.
        return None

    # Truncate inputs for a tight repair prompt.
    q = (question or "").strip()
    if len(q) > 240:
        q = q[:237] + "\u2026"
    a = (original_answer or "").strip()
    if len(a) > 1200:
        a = a[:1197] + "\u2026"

    sys_msg = (
        "You are correcting a previous answer that violated specific quality "
        "checks. Output ONLY the corrected answer text - no preamble, no "
        "meta-commentary, no apologies. Match the original's language "
        "(Hinglish if Hinglish, English if English). Keep the same overall "
        "length unless a check explicitly requires shortening."
    )
    user_msg = (
        f"ORIGINAL USER QUESTION:\n\"{q}\"\n\n"
        f"ORIGINAL ANSWER (to be corrected):\n\"{a}\"\n\n"
        f"QUALITY CHECK FAILURES (you MUST fix these - do NOT introduce "
        f"new violations):\n" + "\n".join(instructions) + "\n\n"
        f"OUTPUT: Only the corrected answer text."
    )
    return [
        {"role": "system", "content": sys_msg},
        {"role": "user",   "content": user_msg},
    ]


__all__ = [
    # Constants
    "_TOPIC_SIGN_LORDS",
    "_TOPIC_SIGN_ALIASES",
    # Topic helpers
    "_topic_lagna_sign_idx",
    "_topic_house_lord",
    "_topic_current_dasha",
    # Prompt builders
    "_build_topic_lock",
    "_build_wealth_structured_system_prompt",
    "_build_true_intent_hint",
    "_build_repair_prompt",
]
