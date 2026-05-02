"""Sprint-26 — AI-only Question Understanding.

ONE LLM call → {intent, topic, confidence}.
This is the SOLE source of truth for routing every user question.
No regex pipeline, no AI-Ear merge, no multi-source override layers.

Fallback:
    If AI confidence < 0.6 OR the call fails, a minimal regex fires
    purely as a safety-net so the request still lands somewhere sane.

Routing contract:
    intent ∈ {problem, timing, decision, planet, analysis}
    topic  ∈ {finance, career, marriage, love, health, general}

Downstream code maps `intent` → narrator supertype via `supertype_for(intent)`.
Topic carries domain flavour but does NOT pick the engine.
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Optional


# ── Allowed values ──────────────────────────────────────────────────────────
INTENTS = ("problem", "timing", "decision", "planet", "analysis")
TOPICS  = ("finance", "career", "marriage", "love", "health", "general")


# Phase 6.2 (Apr 29, 2026) — defensive timeout for the classifier LLM call.
# The classifier runs BEFORE the main answer call; if it hangs (network
# blip, 503, queueing) the whole pipeline blocks and the user stares at
# a blank screen. 5s gives ~3s headroom over the typical 1.5-2s response
# time. On timeout, the existing exception handler in `_understand_
# question_inner` falls back to `_fallback_classify` (regex). Override
# via env: QU_TIMEOUT_S=<float>.
try:
    _QU_TIMEOUT_S = float(os.environ.get("QU_TIMEOUT_S", "5.0"))
except (TypeError, ValueError):
    _QU_TIMEOUT_S = 5.0


# ── Prompt ──────────────────────────────────────────────────────────────────
# Sprint-26 base prompt + boundary definitions added after empirical
# evaluation showed the AI confused: (a) planet-status questions naming
# "vargottam"/"exalted"/etc as decisions, (b) "bachhe" (children) as a
# marriage topic, (c) "dosh" (defect) as analysis instead of problem.
# The base structure (input shape, output shape, rules block) is unchanged
# — we only added two short DEFINITIONS sections and three EDGE-CASE
# examples. Output budget (max_tokens=80) is untouched.
_PROMPT_TEMPLATE = (
    "You are a question understanding module.\n\n"
    "Your job is ONLY to understand what the user is asking.\n\n"
    "User question:\n"
    "\"{question}\"\n\n"
    "Return STRICT JSON only:\n\n"
    "{{\n"
    "  \"intent\": \"problem | timing | decision | planet | analysis\",\n"
    "  \"topic\": \"finance | career | marriage | love | health | general\",\n"
    "  \"intents_ranked\": [\"<primary>\", \"<secondary?>\", \"<tertiary?>\"],\n"
    "  \"topics_all\": [\"<primary>\", \"<secondary?>\"],\n"
    "  \"hidden_intent\": \"<≤8 words underlying ask, no psychology guessing>\",\n"
    "  \"cross_domain_root_cause\": true | false,\n"
    "  \"focus\": \"<≤6 words specific area, or null>\",\n"
    "  \"timeframe\": \"none | near | mid | far\",\n"
    "  \"depth\": \"shallow | medium | deep\",\n"
    "  \"user_keywords\": [\"<≤5 user's own salient phrases>\"],\n"
    "  \"archetype\": \"OVERVIEW | TIMING | DECISION | REMEDY | EXPLAIN\",\n"
    "  \"subtopic\": \"<≤3 words sub-area within topic, or null>\",\n"
    "  \"needs_engine\": true | false,\n"
    "  \"emotion\": \"neutral | anxiety | anger | sadness | confusion | excitement | frustration\",\n"
    "  \"urgency\": \"high | medium | low\",\n"
    "  \"cleaned_q\": \"<typo-corrected concise version, ≤15 words>\",\n"
    "  \"confidence\": 0.0 to 1.0\n"
    "}}\n\n"
    "MULTI-INTENT RANKING (intents_ranked):\n"
    "- Always include the PRIMARY intent first (same value as the `intent` field).\n"
    "- Add SECONDARY only if the question genuinely carries a second ask "
    "(e.g. 'why is this happening AND when will it end' = problem + timing).\n"
    "- Add TERTIARY only if a third ask is clearly present.\n"
    "- Pick the PRIMARY by what the user MOST wants answered:\n"
    "  • analysis > problem when the user asks 'same reason or different' / "
    "'kya dono ek hi reason se' / 'compare these two' (the comparison IS the ask).\n"
    "  • problem > timing when the user is venting frustration first and asking "
    "'kab' as a follow-on (e.g. 'paisa nahi ruk raha, kab control hoga' → "
    "primary=problem, secondary=timing).\n"
    "  • timing > problem when 'kab' is the lead and the problem is just context.\n"
    "  • decision is always primary when 'should I X or Y' is the lead.\n\n"
    "MULTI-DOMAIN (topics_all):\n"
    "- Include EVERY domain the question genuinely spans (max 2). Do NOT add a "
    "second domain just because a word brushes past it — the user must be "
    "actually asking about both areas.\n"
    "- 'finance + career', 'marriage + love', 'health + career' are common pairs.\n"
    "- IMPORTANT: the singular `topic` field MUST be ONE single value (the "
    "PRIMARY domain — same as topics_all[0]). Never put 'finance | career' or "
    "any combined string in `topic` — that field accepts ONE enum value only.\n"
    "- Same rule for the singular `intent`: ONE value (= intents_ranked[0]).\n\n"
    "HIDDEN INTENT (hidden_intent):\n"
    "- ≤8 words capturing the underlying ASK in plain language. NO psychology, "
    "NO behavioural guessing, NO speculation about user's mindset.\n"
    "- Good: 'savings/retention issue', 'common root cause vs separate', "
    "'phase exit timing', 'compatibility check'.\n"
    "- Bad: 'user wants validation', 'looking for external fix', "
    "'avoiding accountability'.\n"
    "- If no hidden layer beyond the surface ask, return null (JSON null).\n\n"
    "CROSS-DOMAIN ROOT CAUSE (cross_domain_root_cause):\n"
    "- TRUE only when topics_all has ≥2 entries AND the user explicitly asks "
    "whether the two issues share a single cause — phrases like 'ek hi reason "
    "se', 'same reason', 'connected hai', 'related hain', 'dono ek saath', "
    "'because of the same thing'.\n"
    "- Otherwise FALSE.\n\n"
    "FOCUS (focus):\n"
    "- ≤6 words narrowing the topic to a SPECIFIC area inside the domain.\n"
    "- Health examples: 'general body', 'digestion', 'mental stress', "
    "'bones/joints', 'reproductive system', 'eyes/vision'.\n"
    "- Career examples: 'job switch', 'business growth', 'promotion', "
    "'salary'.\n"
    "- Marriage examples: 'spouse compatibility', 'wedding timing', "
    "'marital harmony'.\n"
    "- If the user is asking GENERALLY without narrowing (e.g. 'kaisa hai', "
    "'kya kya issue'), use 'general' + the topic word (e.g. 'general body', "
    "'general career'). Return null ONLY when topic itself is 'general'.\n\n"
    "TIMEFRAME (timeframe):\n"
    "- 'none' → no time-window asked (default for overview / definitional / "
    "diagnostic questions). Most questions land here.\n"
    "- 'near' → next 0-12 months ('jaldi', 'ab', 'soon', 'is saal').\n"
    "- 'mid'  → 1-3 years ('agle 2 saal', 'next year', 'kuch saal').\n"
    "- 'far'  → 3+ years or lifetime ('zindagi bhar', 'long term', "
    "'lifetime', 'kabhi bhi').\n\n"
    "DEPTH (depth):\n"
    "- 'shallow' → user wants a one-line YES/NO/quick-take. Single sentence "
    "asks, 'haan ya na', 'bata do bas'.\n"
    "- 'medium'  → DEFAULT. User wants 2-4 sentences with reason + outcome.\n"
    "- 'deep'    → user explicitly asks for explanation, deep dive, full "
    "analysis ('vistar se', 'detail me', 'sab kuch bata', 'explain', 'why').\n\n"
    "USER_KEYWORDS (user_keywords):\n"
    "- ≤5 of the user's OWN salient words/phrases — verbatim from the "
    "question (do NOT translate, do NOT paraphrase). These are the words "
    "the answerer MUST echo back so the user feels heard.\n"
    "- Skip stop-words ('hai', 'mein', 'ko', 'is', 'a'). Skip personal "
    "possessives ('mera', 'mujhe', 'my').\n"
    "- Examples: 'kya kya', 'weak areas', 'tendency', 'kab tak', 'jaldi'.\n"
    "- Empty array [] is acceptable when nothing salient stands out.\n\n"
    "ARCHETYPE (archetype) — RESPONSE-SHAPE category:\n"
    "- Pick ONE of 5 fixed archetypes that controls the SHAPE of the answer "
    "(not the topic). This is orthogonal to `intent` — multiple intents can "
    "map to the same archetype. Choose by priority order below:\n"
    "- OVERVIEW → user wants a broad scan / ranked list / 'what are the "
    "main things' answer. Cues: 'kya kya', 'weak areas', 'tendency', "
    "'overall', 'general state', 'sab kuch bata', 'main issues'. Even when "
    "intent=problem or intent=analysis, if the user's ASK is breadth "
    "rather than depth, this is OVERVIEW.\n"
    "- TIMING → user wants a WHEN answer (timeline, dasha periods, year "
    "ranges). Cues: 'kab', 'when', 'kis saal', 'kab tak', 'kab hoga', "
    "'how long'. Almost always lines up with intent=timing.\n"
    "- DECISION → user wants a YES/NO + 1-line reason. Cues: 'haan ya na', "
    "'should I', 'karu ya nahi', 'sahi hai kya', 'X chahiye?'. Almost "
    "always lines up with intent=decision.\n"
    "- REMEDY → user already knows the issue, wants a FIX. Cues: 'upay', "
    "'remedy', 'kya karu', 'kaise theek karu', 'kaise sudharu', 'remedy "
    "bata'. NOT a prediction — practical lifestyle/spiritual practices.\n"
    "- EXPLAIN → DEFAULT. Narrative reasoning, cause-effect, definitions. "
    "Cues: 'kyon', 'kaise', 'iska matlab', 'X kya hai', 'samjhao', "
    "'explain', 'what is X'. Also the fallback when none of the above "
    "clearly fits. Most intent=problem (why-questions) and intent=analysis "
    "(definitional/conditional) map here.\n"
    "- IMPORTANT: archetype is ALWAYS one of the 5 enums. Never null, "
    "never empty. When in doubt, pick EXPLAIN.\n\n"
    "SUBTOPIC (subtopic):\n"
    "- ≤3 words narrowing further INSIDE the chosen `topic`. More specific "
    "than `focus` and meant for engine routing.\n"
    "- Marriage examples: 'timing', 'love_vs_arrange', 'spouse_quality', "
    "'delay_reason', 'remedy', 'compatibility'.\n"
    "- Career examples: 'timing', 'switch', 'promotion', "
    "'business_vs_job', 'salary'.\n"
    "- Finance examples: 'timing', 'loan', 'investment', 'debt', "
    "'savings'.\n"
    "- Health examples: 'general_body', 'mental', 'chronic', 'remedy'.\n"
    "- Return null only when no clear sub-area applies.\n\n"
    "NEEDS_ENGINE (needs_engine):\n"
    "- TRUE when the answer needs the user's actual chart computation: "
    "predictions ('kab'), strength readings, dosha presence, divisional "
    "placements, timing of life events, dasha-based forecasts, "
    "compatibility analysis, personalised remedy.\n"
    "- FALSE for concept-only questions ('X kya hai', 'explain dasha', "
    "'what is navamsa'), pure greetings ('namaste', 'hi'), generic info "
    "that doesn't need the user's chart, or simple lookup ('mera lagna "
    "kya hai' is a pure data lookup, not engine compute).\n"
    "- When in doubt, prefer TRUE — better to compute facts than miss them.\n\n"
    "EMOTION (emotion):\n"
    "- The DOMINANT emotional tone in the question text. Choose ONE:\n"
    "  • anxiety     → 'stress', 'pareshan', 'tension', 'darr', worry tone.\n"
    "  • anger       → 'gussa', 'tang aa gaya', 'fed up', frustration vent.\n"
    "  • sadness     → 'dukhi', 'akela', 'depressed', 'mann nahi lagta'.\n"
    "  • confusion   → 'samajh nahi', 'kya karoon', mixed signals.\n"
    "  • excitement  → 'khush', 'amazing', 'great news'.\n"
    "  • frustration → 'kab tak yaar', 'thak gaya', 'bahut ho gaya'.\n"
    "  • neutral     → DEFAULT. Plain factual ask, no emotional charge.\n\n"
    "URGENCY (urgency):\n"
    "- HIGH   → 'abhi', 'jaldi', 'kab tak', 'urgent', desperate tone, "
    "hard deadline mentioned, repeated 'kab kab'.\n"
    "- MEDIUM → DEFAULT. Standard predictive or analytical question with "
    "no explicit urgency cue.\n"
    "- LOW    → casual curiosity, 'kabhi', 'future me', 'long term', "
    "educational concept, 'just asking'.\n\n"
    "CLEANED_Q (cleaned_q):\n"
    "- Typo-corrected, grammar-normalised version of the question. "
    "≤15 words.\n"
    "- Preserve language (Hindi/English/Hinglish/Devanagari). Do NOT "
    "translate.\n"
    "- Strip filler ('yaar', 'bhai', 'na') but keep meaning intact.\n"
    "- Example: 'shadii kbb hgi yarrr' → 'shaadi kab hogi'.\n"
    "- Example: 'merry kab hoga' → 'marriage kab hoga'.\n"
    "- If question is already clean, return it unchanged.\n\n"
    "INTENT definitions (pick the most specific that fits):\n"
    "- planet   → ANY question that NAMES a graha (Sun, Moon, Mars, Mercury, "
    "Jupiter, Venus, Saturn, Rahu, Ketu / Surya, Chandra, Mangal, Budh, Guru, "
    "Shukra, Shani) — even if phrased as 'X kaisa hai' or 'X mera kaisi hai' "
    "(asking about a single named graha = planet intent, not analysis). "
    "ALSO planet: strong / weak / strongest / weakest / vargottam / exalted "
    "/ debilitated / combust / retrograde status. Words like 'kaunsa planet', "
    "'konsa graha', 'sabse powerful grah' ALWAYS mean planet — NOT decision.\n"
    "- problem  → dosha / dosh / defect / affliction, 'kyun nahi', 'why not', "
    "delay, stuck, suffering, complaint, kharab, bura. 'X dosh hai kya' is "
    "ALWAYS problem — NOT analysis.\n"
    "- timing   → 'when', 'kab', 'kab hoga', 'kitne saal', 'how long', a "
    "future date or period.\n"
    "- decision → 'should I', 'karu ya nahi', 'chahiye', 'sahi hai kya', "
    "choosing between options or asking for a recommendation.\n"
    "- analysis → THREE flavours, all map here:\n"
    "    (a) general overview / lifecycle questions — 'kaisa hai', "
    "'kaisi rahegi', overall theme.\n"
    "    (b) DEFINITIONAL or EXPLANATORY questions — 'X kya hai', "
    "'X ka matlab kya hai', 'X ke baare mein bata', 'X samjhao', "
    "'remedy bata', 'kya farak hai', concept / comparison. CRITICAL: "
    "'X kya hai' / 'what is X' is ALWAYS analysis even when X is a "
    "doshic or problem-flavoured noun (e.g. 'Kaal sarp dosh kya hai', "
    "'Manglik kya hai', 'Pitra dosh kya hai' — all analysis, NOT problem).\n"
    "    (c) CONDITIONAL or IMPLICATION questions — 'X hai to Y ho "
    "jayega?', 'Agar A hai to B hoga?', 'X strong hai to Y automatically "
    "strong?' (even when a graha is named in the condition — the "
    "QUESTION is about the implication, not the planet status).\n"
    "  Also the fallback when none of intent above fits.\n\n"
    "TOPIC definitions (be strict — do NOT bleed across topics):\n"
    "- marriage → ONLY spouse / wedding / partner / vivah / shaadi / "
    "kalatra. Children, parents, family in general → 'general', NOT marriage.\n"
    "- career   → job, business, work, promotion, profession, naukri, kaam.\n"
    "- finance  → money, paisa, wealth, savings, loan, income, dhan.\n"
    "- love     → romantic relationship, girlfriend / boyfriend / crush "
    "(NOT marriage).\n"
    "- health   → illness, body, disease, bimari, sehat.\n"
    "- general  → anything not in the above five (children, parents, life "
    "overview, concepts, planet status without a domain).\n\n"
    "Rules:\n"
    "- Do NOT answer the question\n"
    "- Do NOT explain anything\n"
    "- No extra text, only JSON\n"
    "- Choose the closest intent even if question is vague\n"
    "- Keep it simple and accurate"
)


# ── Minimal regex fallback (only used when AI fails / low conf) ─────────────
# Order matters — first-match wins. Patterns kept short on purpose; this is
# a safety-net, NOT a routing layer.
_FALLBACK_INTENT_RX: tuple[tuple[str, "re.Pattern[str]"], ...] = (
    ("planet",   re.compile(
        r"\b(strong|weak|powerful|kamzor|kamjor|vargottam|"
        r"shakti|balwan|exalt|debilit|planet|grah|graha)\b", re.I)),
    ("timing",   re.compile(
        r"\b(when|kab|kab tak|kitne din|kitne saal|timing|date|year|month|"
        r"saal|mahina|samay)\b", re.I)),
    ("problem",  re.compile(
        r"\b(problem|dosh|dosha|bura|kharab|delay|stuck|why.*not|"
        r"kyun|kyu|nahi ho|nahi mil)\b", re.I)),
    ("decision", re.compile(
        r"\b(should i|kya karu|kya karoon|chahiye|sahi hai|right time|"
        r"karna chahi|sahi rahega)\b", re.I)),
    # 'analysis' is the implicit default
)

_FALLBACK_TOPIC_RX: tuple[tuple[str, "re.Pattern[str]"], ...] = (
    ("marriage", re.compile(
        r"\b(shaadi|shadi|vivah|marriage|spouse|wife|husband|patni|pati)\b", re.I)),
    ("career",   re.compile(
        r"\b(career|naukri|job|business|kaam|work|profession|promotion)\b", re.I)),
    ("finance",  re.compile(
        r"\b(money|paisa|paise|wealth|finance|dhan|loan|kamai|income|salary)\b", re.I)),
    ("health",   re.compile(
        r"\b(health|sehat|swasth|illness|disease|bimari|rog)\b", re.I)),
    ("love",     re.compile(
        # Sprint-26 Step 4 Phase 2 (architect-recommended fix): added
        # rishta / rishtey / rishton / partner / breakup so the topic
        # recovery post-pass can lift these out of 'general' to match
        # what detect_domain_anchor() already recognises. Without these,
        # a question like "rishtey mein problem hi problem" correctly
        # bypasses the clarification gate (anchor found) but its topic
        # would stay 'general' downstream — inconsistent.
        r"\b(love|pyaar|pyar|relationship|girlfriend|boyfriend|crush|ishq|"
        r"rishta|rishtey|rishton|partner|breakup)\b", re.I)),
)


def _fallback_classify(question: str) -> dict:
    """Last-resort regex classification. Returns confidence=0.5."""
    q = question or ""
    intent = "analysis"
    topic  = "general"
    for name, rx in _FALLBACK_INTENT_RX:
        if rx.search(q):
            intent = name
            break
    for name, rx in _FALLBACK_TOPIC_RX:
        if rx.search(q):
            topic = name
            break
    # Sprint-26 Fix-M: minimal multi-intent shape so downstream code can rely
    # on the new fields even when the LLM call failed. We only seed the
    # primary entries — the AI is the one that ranks secondaries.
    # Sprint-26 Fix-Q (post-architect-review): `has_recovery_subask` is now
    # part of the canonical contract emitted by every code path of
    # understand_question() (AI success, AI low-conf, AI error, regex
    # fallback, empty input). Putting it inside the function instead of
    # only in ai_ask() removes the silent-failure risk where a future
    # refactor of question_understanding callers would lose the flag.
    # Sprint-26 Step 4 Phase 2 — emit the deterministic safety flags from
    # the regex fallback path too, so downstream gate logic in
    # openai_helper.py never sees a missing key regardless of which return
    # path fired.
    _fb_anchor    = detect_domain_anchor(q) if q else False
    _fb_sustained = detect_sustained_problem(q) if q else False
    return {
        "intent":     intent,
        "topic":      topic,
        "intents_ranked":          [intent],
        "topics_all":              [topic],
        "hidden_intent":           None,
        "cross_domain_root_cause": False,
        "has_recovery_subask":     bool(_RECOVERY_SUBASK_RX.search(q)) if q else False,
        "domain_anchor_found":      _fb_anchor,
        "sustained_problem_pattern": _fb_sustained,
        "clarification_needed":      _fb_sustained and not _fb_anchor,
        # Phase 7.1 — slot defaults emitted from regex fallback so downstream
        # consumers never KeyError regardless of which return path fired.
        # Regex can't intelligently extract focus/keywords; use safe nulls.
        "focus":                    None,
        "timeframe":                "none",
        "depth":                    "medium",
        "user_keywords":            [],
        # Phase 7.3 — archetype derived from question text via regex
        # heuristic; defaults EXPLAIN when no cue matches.
        "archetype":                _archetype_from_text(q) if q else "EXPLAIN",
        # Phase 2.8.41 — SQU extension defaults (no LLM available, use
        # safest values). `needs_engine=True` keeps chart computation on
        # for predictive Qs even when the AI call fails. `final_topic_lock`
        # mirrors the regex-derived topic so engine + narrator stay aligned.
        "subtopic":                 None,
        "needs_engine":             True,
        "emotion":                  "neutral",
        "urgency":                  "medium",
        "cleaned_q":                None,
        "final_topic_lock":         topic,
        "confidence":              0.5,
        "source":                  "regex_fallback",
    }


def _normalise_multi_fields(data: dict, intent: str, topic: str) -> dict:
    """Sanitise the new multi-intent fields against the allowed enums.
    Falls back to the primary intent/topic if the AI emitted garbage."""
    raw_intents = data.get("intents_ranked")
    if isinstance(raw_intents, list):
        cleaned: list[str] = []
        for v in raw_intents[:3]:
            if isinstance(v, str):
                vv = v.strip().lower()
                if vv in INTENTS and vv not in cleaned:
                    cleaned.append(vv)
        intents_ranked = cleaned or [intent]
    else:
        intents_ranked = [intent]
    if intent not in intents_ranked:
        intents_ranked = [intent] + [x for x in intents_ranked if x != intent]
        intents_ranked = intents_ranked[:3]

    raw_topics = data.get("topics_all")
    if isinstance(raw_topics, list):
        cleaned_t: list[str] = []
        for v in raw_topics[:2]:
            if isinstance(v, str):
                vv = v.strip().lower()
                if vv in TOPICS and vv not in cleaned_t:
                    cleaned_t.append(vv)
        topics_all = cleaned_t or [topic]
    else:
        topics_all = [topic]
    if topic not in topics_all:
        topics_all = [topic] + [x for x in topics_all if x != topic]
        topics_all = topics_all[:2]

    raw_hidden = data.get("hidden_intent")
    if isinstance(raw_hidden, str):
        hidden = raw_hidden.strip()
        # Cap at 12 words, drop when empty/null-ish or when AI hallucinated
        # psychology language we explicitly told it to avoid.
        if hidden.lower() in ("", "null", "none", "n/a"):
            hidden = None
        else:
            hidden = " ".join(hidden.split()[:12])
    else:
        hidden = None

    raw_cross = data.get("cross_domain_root_cause")
    cross = bool(raw_cross) and len(topics_all) >= 2

    # ── Phase 7.1 (Apr 30, 2026) — slot extraction sanitisation ──
    # Four new optional slots feed `_build_true_intent_hint` so the
    # answerer gets richer context than `hidden_intent` alone. Each
    # slot is defensively normalised; bad values become safe defaults
    # (None / "medium" / []) so downstream consumers never KeyError
    # and the prompt-builder can decide whether to render a slot block.
    raw_focus = data.get("focus")
    if isinstance(raw_focus, str):
        focus = raw_focus.strip()
        if focus.lower() in ("", "null", "none", "n/a"):
            focus = None
        else:
            focus = " ".join(focus.split()[:6])  # cap at 6 words
    else:
        focus = None

    raw_tf = data.get("timeframe")
    _TIMEFRAMES = ("none", "near", "mid", "far")
    if isinstance(raw_tf, str):
        tf = raw_tf.strip().lower()
        timeframe = tf if tf in _TIMEFRAMES else "none"
    else:
        timeframe = "none"

    raw_depth = data.get("depth")
    _DEPTHS = ("shallow", "medium", "deep")
    if isinstance(raw_depth, str):
        d = raw_depth.strip().lower()
        depth = d if d in _DEPTHS else "medium"
    else:
        depth = "medium"

    raw_kw = data.get("user_keywords")
    if isinstance(raw_kw, list):
        cleaned_kw: list[str] = []
        for v in raw_kw[:5]:
            if isinstance(v, str):
                vv = v.strip()
                if vv and len(vv) <= 30 and vv not in cleaned_kw:
                    cleaned_kw.append(vv)
        user_keywords = cleaned_kw
    else:
        user_keywords = []

    # Phase 7.3 — archetype slot (5-way response-shape category).
    # Always normalised to one of the 5 enums; default EXPLAIN.
    raw_arch = data.get("archetype")
    if isinstance(raw_arch, str):
        a = raw_arch.strip().upper()
        archetype = a if a in _ARCHETYPES else "EXPLAIN"
    else:
        archetype = "EXPLAIN"

    return {
        "intents_ranked":          intents_ranked,
        "topics_all":              topics_all,
        "hidden_intent":           hidden,
        "cross_domain_root_cause": cross,
        # Phase 7.1 — slot expansion (richer context for hint builder)
        "focus":                   focus,
        "timeframe":               timeframe,
        "depth":                   depth,
        "user_keywords":           user_keywords,
        # Phase 7.3 — archetype (response-shape category)
        "archetype":               archetype,
    }


# Phase 7.3 — archetype enum (5 fixed response-shape categories).
# Order chosen by selection priority in the regex-fallback heuristic
# (more specific cues first; EXPLAIN is the catch-all default).
_ARCHETYPES: tuple[str, ...] = (
    "OVERVIEW", "TIMING", "DECISION", "REMEDY", "EXPLAIN",
)

# Phase 2.8.41 (May 02, 2026) — Smart Query Understanding extension.
# Five additive output fields used by downstream routing (`needs_engine`,
# `subtopic`) and narrator tone (`emotion`, `urgency`, `cleaned_q`).
# All five are emitted by EVERY return path of understand_question() so
# consumers never KeyError. final_topic_lock mirrors `topic` after sanity
# / recovery so the narrator and engine stay aligned. clarification_text
# is non-null only when SQU genuinely cannot route the question.
_EMOTIONS: tuple[str, ...] = (
    "neutral", "anxiety", "anger", "sadness",
    "confusion", "excitement", "frustration",
)
_URGENCIES: tuple[str, ...] = ("high", "medium", "low")


def _normalise_new_squ_fields(data: dict) -> dict:
    """Phase 2.8.41 — sanitise the 5 new SQU fields with safe defaults.

    Inputs are LLM-emitted JSON values (any shape); outputs are guaranteed
    to be one of the canonical types/enums or a safe default. Never raises.
    Caller is responsible for setting `final_topic_lock` (= post-recovery
    topic) since topic recovery happens AFTER this normaliser runs.
    """
    raw_subtopic = data.get("subtopic") if isinstance(data, dict) else None
    if isinstance(raw_subtopic, str):
        s = raw_subtopic.strip()
        if s.lower() in ("", "null", "none", "n/a"):
            subtopic = None
        else:
            subtopic = " ".join(s.split()[:3]).lower()
    else:
        subtopic = None

    raw_needs = data.get("needs_engine") if isinstance(data, dict) else None
    if isinstance(raw_needs, bool):
        needs_engine = raw_needs
    elif isinstance(raw_needs, str):
        needs_engine = raw_needs.strip().lower() in (
            "true", "yes", "1", "y", "t",
        )
    elif isinstance(raw_needs, (int, float)):
        # Phase 2.8.41 hardening (architect feedback): accept numeric 0/1.
        # LLMs sometimes emit JSON booleans as numbers; treat 0 as False,
        # any other number as True. Avoids silently forcing compute when
        # model intended to skip it.
        needs_engine = bool(raw_needs)
    else:
        needs_engine = True   # safe default — better to compute than miss

    raw_emotion = data.get("emotion") if isinstance(data, dict) else None
    if isinstance(raw_emotion, str):
        e = raw_emotion.strip().lower()
        emotion = e if e in _EMOTIONS else "neutral"
    else:
        emotion = "neutral"

    raw_urgency = data.get("urgency") if isinstance(data, dict) else None
    if isinstance(raw_urgency, str):
        u = raw_urgency.strip().lower()
        urgency = u if u in _URGENCIES else "medium"
    else:
        urgency = "medium"

    raw_cleaned = data.get("cleaned_q") if isinstance(data, dict) else None
    if isinstance(raw_cleaned, str):
        c = raw_cleaned.strip()
        # Phase 2.8.41 hardening (architect feedback): null-map LLM
        # literals like "null"/"none"/"n/a" the same way subtopic does,
        # so garbage placeholders don't leak as text into the narrator.
        if c.lower() in ("", "null", "none", "n/a", "na"):
            cleaned_q = None
        else:
            cleaned_q = " ".join(c.split()[:15])
    else:
        cleaned_q = None

    return {
        "subtopic":     subtopic,
        "needs_engine": needs_engine,
        "emotion":      emotion,
        "urgency":      urgency,
        "cleaned_q":    cleaned_q,
    }


# Phase 2.8.41 — readable Hinglish topic labels for the clarification probe.
_TOPIC_LABEL_HI = {
    "marriage": "shaadi",
    "career":   "career",
    "finance":  "paisa",
    "love":     "rishta",
    "health":   "sehat",
}


def _build_clarification_text(out: dict) -> Optional[str]:
    """Phase 2.8.41 — Human-tone Hinglish clarification probe.

    Returns a warm probe string only when SQU genuinely cannot route the
    question — i.e. confidence is low AND no domain anchor was detected
    AND topic stayed at the catch-all 'general'. In all other cases
    returns None (caller skips the probe).
    """
    if not isinstance(out, dict):
        return None
    try:
        conf = float(out.get("confidence") or 0.0)
    except (TypeError, ValueError):
        conf = 0.0
    if conf >= 0.6:
        return None
    if out.get("domain_anchor_found"):
        return None
    if (out.get("topic") or "general") != "general":
        return None
    topics_all = out.get("topics_all") or []
    readable = [
        _TOPIC_LABEL_HI[t] for t in topics_all[:2]
        if t in _TOPIC_LABEL_HI
    ]
    if readable:
        joined = " ya ".join(readable)
        return (
            f"Lag raha hai {joined} ka sawal hai — main sahi samajh lu, "
            f"isliye pooch raha hoon. Thoda clear karoge?"
        )
    return (
        "Aapka sawal poori tarah samjha nahi — thoda aur bata sakte? "
        "Kis baare me jaanna chahte (shaadi / career / sehat / paisa)?"
    )

# Phase 7.3 — regex-fallback archetype heuristic. Used when the AI
# classifier fails and we drop to the regex safety-net (which previously
# couldn't emit archetype at all). First-match wins in the order below.
_FALLBACK_ARCHETYPE_RX: tuple[tuple[str, "re.Pattern[str]"], ...] = (
    ("REMEDY", re.compile(
        r"\b(upay|upaay|remedy|remedies|kya karu|kya karoon|"
        r"kaise theek|kaise sudhar|kaise sudharu|how to fix|how do i fix)\b",
        re.I)),
    ("TIMING", re.compile(
        r"\b(when|kab|kab tak|kab hoga|kis saal|kitne saal|kitne din|"
        r"how long|kab milega|kab band)\b", re.I)),
    ("DECISION", re.compile(
        r"\b(should i|haan ya na|haan ya nahi|karu ya nahi|karoon ya nahi|"
        r"chahiye ya nahi|sahi hai kya|right time|sahi rahega)\b", re.I)),
    ("OVERVIEW", re.compile(
        r"\b(kya kya|weak areas|main areas|main issues|overall|"
        r"general state|sab kuch bata|tendency|tendencies|main problems)\b",
        re.I)),
    # EXPLAIN is the implicit default when nothing matches.
)


def _archetype_from_text(text: str) -> str:
    """Pure-regex archetype derivation for the regex-fallback path.
    Returns one of the 5 enum values; defaults to EXPLAIN."""
    if not isinstance(text, str) or not text.strip():
        return "EXPLAIN"
    for name, rx in _FALLBACK_ARCHETYPE_RX:
        if rx.search(text):
            return name
    return "EXPLAIN"


# ── Sprint-26 Fix-N — "Why-leading" intent promoter ──────────────────────────
# When a question explicitly asks WHY (kyun/why) or names a CONTRADICTION /
# MISMATCH between expectation and reality, the user is asking for
# root-cause REASONING, not just complaint description. The classifier
# sometimes picks `problem` (the surface complaint) as primary; we must
# promote `analysis` to PRIMARY in that case so the narrator routes through
# GENERAL_ANALYSIS and explains MD/AD/transit reasoning instead of just
# acknowledging the pain.
import re as _re_why
_WHY_LEADING_RX = _re_why.compile(
    r"\b(kyun|kyo+n|kyu+|why|क्यों|क्यूँ|"
    r"contradiction|contradict|"
    r"mismatch|mismatched|"
    r"opposite|ulta|ulti|"
    r"clash(?:ing)?|conflict(?:ing)?)\b",
    _re_why.IGNORECASE,
)


# ── Sprint-26 Fix-O — Personal-chart-anchor detector ─────────────────────────
# When a question contains a personal possessive ("mera/meri/mere/my") next
# to a chart-anchor noun (dasha/kundli/lagna/chart/horoscope/etc.), it is
# UNAMBIGUOUSLY a personal astrology question that MUST go through the chart
# pipeline — even when the AI classifier marks topic=general (which would
# normally route to concept-explainer mode and skip the chart entirely).
# Without this override, "Mera dasha bolte hain achha chal raha hai…" loses
# access to the user's actual MD/AD lord names and the answer goes shallow.
# Sprint-26 Fix-O hardening (architect-found regression):
# DO NOT allow arbitrary filler words between possessive and anchor — that
# matched third-person ownership chains ("mere dost ki kundli", "meri maa
# ki dasha", "मेरी माँ की कुंडली") which are NOT the user's own chart and
# must not force astro mode. Instead, require either:
#   (a) direct adjacency: possessive + chart-noun, OR
#   (b) an OPTIONAL astro-qualifier word between them (janma/janam/navamsa/
#       navmansh/chalit/moon/sun/birth) — these are pure astrology vocabulary
#       and cannot be mistaken for relationship nouns ("dost", "maa", "pati").
# Roman compound forms (janamkundli, janmakundli, janampatri/patrika) are
# added explicitly to the anchor list so they remain detectable.
_PERSONAL_CHART_RX = _re_why.compile(
    r"\b(?:mera|meri|mere|apna|apni|apne|my)\s+"
    r"(?:(?:janma|janam|navamsa|navmansh|chalit|moon|sun|birth)\s+)?"
    r"(?:dasha|maha\s*dasha|mahadasha|antar\s*dasha|antardasha|"
    r"pratyantar|bhukti|"
    r"kundli|kundali|kundli|chart|"
    r"janamkundli|janmakundli|janampatri|janampatrika|"
    r"lagna|ascendant|"
    r"rashi|moon\s*sign|sun\s*sign|"
    r"nakshatra|"
    r"janma|janm|birth\s*chart|birth|horoscope|"
    r"saturn|shani|mars|mangal|jupiter|guru|brihaspati|"
    r"venus|shukra|mercury|budh|rahu|ketu|sun|surya|moon|chandra)\b",
    _re_why.IGNORECASE,
)
# Devanagari forms — same hardening: direct adjacency or optional
# astro-qualifier (जन्म/जनम/नवमांश), no arbitrary fillers, so genitive
# ownership chains like "मेरे दोस्त की कुंडली" / "मेरी माँ की कुंडली"
# (which contain "की" + a kinship noun before the anchor) do NOT match.
_PERSONAL_CHART_DEVA_RX = _re_why.compile(
    r"(?:मेरा|मेरी|मेरे|अपना|अपनी|अपने)\s+"
    r"(?:(?:जन्म|जनम|नवमांश|चलित)\s+)?"
    r"(?:दशा|महादशा|अंतरदशा|अन्तर्दशा|कुंडली|कुण्डली|"
    r"जन्मकुंडली|जन्मकुण्डली|जन्मपत्री|जन्मपत्रिका|"
    r"लग्न|राशि|नक्षत्र|जन्म|चार्ट|"
    r"शनि|मंगल|गुरु|बृहस्पति|शुक्र|बुध|राहु|केतु|सूर्य|चंद्र|चन्द्र)"
)


def is_personal_chart_question(question: str) -> bool:
    """True when the question has a personal-possessive next to a chart noun.
    Used by openai_helper to FORCE mode=astro even when topic=general."""
    if not question:
        return False
    return bool(_PERSONAL_CHART_RX.search(question)
                or _PERSONAL_CHART_DEVA_RX.search(question))


# ── Sprint-26 Fix-Q — Recovery sub-ask detector ──────────────────────────────
# Some questions carry a SECONDARY ask about whether the loss / damage / drop
# can be RECOVERED — independent of the primary intent (which is usually
# decision or problem). Examples:
#   • decision + recovery: "exit karu ya continue? agar continue karu to paisa
#                           recover hoga ya nahi?"
#   • problem  + recovery: "paisa stuck hai, kya wapas milega?"
#   • timing   + recovery: "kab tak nuksan recover hoga?"
# Until Fix-Q, the classifier collapsed these into [decision, problem] and
# the wealth/narrator output answered only the primary, dropping the
# recovery sub-question entirely.
#
# Fix-Q is a deterministic regex post-pass — does NOT add a new INTENTS enum
# value (which would ripple through supertype routing, fallback regex, etc.).
# Instead it sets a separate boolean flag `has_recovery_subask` on the
# returned dict so downstream code can:
#   • inject a `recovery_outlook` field into the wealth structured-output
#     schema and prompt, and
#   • add a "Recovery line" instruction to the GENERAL_ANALYSIS narrator
#     contract so V→Recovery→Timing replaces V→Reason→Timing for these
#     questions.
_RECOVERY_SUBASK_RX = _re_why.compile(
    # English / Hinglish recovery vocabulary — direct verbs and noun forms.
    # Anchored on "recover", "recoup", "vasool" so we don't false-positive
    # on every "wapas" (which can also mean "back" in non-money contexts —
    # we restrict it to combos like "wapas aayega/milega/aana/milna").
    #
    # Sprint-26 Fix-Q (post-architect-review patch) — added the following
    # high-frequency Hinglish phrasings flagged as missed by the architect:
    #   • "paisa kab tak aayega"      → "(paisa|paise|amount|funds) kab tak"
    #   • "loss/nuksan bharne mein"   → "(loss|nuksan|nuksaan) bharne"
    #   • "wapis" (vs only "wapas")   → added "wapis" alongside "wapas"
    #   • "vasooli kab"               → "vasooli|vasuli" already covered by
    #                                   the existing "vasool(?:i|na)?" stem
    #                                   but added "kab" trigger pair to be
    #                                   exhaustive on the timing-asking form.
    #   • "kitna time lagega" + loss / paise context → covered by the new
    #     "kab tak" + "(paisa|loss|nuksan|funds)" combos.
    r"\b("
    r"recover(?:y|ed|ing)?|recoup(?:ed|ing)?|"
    r"recoverable|recovery|"
    r"vasool(?:i|na)?|vasul(?:i|na)?|vasooli|vasuli|"
    r"(?:wapas|wapis)\s+(?:aayega|aana|aaye(?:gi|ga)?|milega|milegi|milna|"
    r"paayega|laana|le(?:na|kar))|"
    r"(?:paisa|paise|paisey|amount|funds?)\s+(?:wapas|wapis|laut|return|"
    r"aayega|aayegi|recover|vasool|kab\s+tak)|"
    r"(?:loss|nuksan|nuksaan)\s+(?:cover|recover|wapas|wapis|recoup|"
    r"patega|patta|bhar(?:ne|ega|egi|ne\s+me(?:in)?)?)|"
    r"(?:loss|nuksan|nuksaan)\s+(?:bharne|recover|cover)\s+"
    r"(?:me(?:in)?|mein)\s+kitna(?:\s+time|\s+samay)?|"
    r"vasooli\s+kab|"
    r"recoup|"
    # Devanagari forms
    r"वसूल(?:ी|ना)?|वापस\s+(?:आएगा|आना|मिलेगा|मिलना|पाएगा)|"
    r"नुकसान\s+(?:भर|वापस|कवर)"
    r")\b",
    _re_why.IGNORECASE,
)


def has_recovery_subask(question: str) -> bool:
    """True when the question carries a secondary recovery ask.
    Used by openai_helper to inject `recovery_outlook` into wealth
    structured output and to add a Recovery line in the GENERAL_ANALYSIS
    narrator contract."""
    if not question:
        return False
    return bool(_RECOVERY_SUBASK_RX.search(question))


# ── Sprint-26 Step 4 Phase 2 (Apr 28 2026) — DETERMINISTIC SAFETY DETECTORS ─
# Phase 1 (prompt-side) failed to make the model ask for clarification on
# domain-ambiguous "problem hi problem" questions — even with verbatim-MUST +
# explicit override of "open with answer" + ban on domain inference, the LLM
# still inferred relationship from KP cusp signals. Phase 2 makes the
# detection deterministic so the gate in openai_helper.py can short-circuit
# to a clarification template BEFORE calling the LLM. The classifier surfaces
# three new flags that downstream consumers (gate, narrator, validators) can
# trust without recomputing.
#
# Anchor list mirrors GUARD-2 wording in _NARRATOR_SAFE_FALLBACK at
# openai_helper.py:5685 — keeping the two in sync is critical: if a word
# becomes an anchor here, the prompt-side guard must also recognise it,
# otherwise a fall-through to the LLM (e.g. when the gate is bypassed) would
# get inconsistent behaviour.
_DOMAIN_ANCHOR_RX = re.compile(
    r"\b("
    # Career / work
    r"career|job|naukri|nokri|kaam|work|business|biznes|profession|"
    r"promotion|interview|office|"
    # Money / finance
    r"paisa|paise|paisey|money|wealth|finance|financial|dhan|loan|"
    r"income|salary|kamai|savings|investment|stock|share|trading|"
    r"property|investment|mutual\s*fund|"
    # Relationships (non-marriage)
    r"rishta|rishtey|rishton|relationship|partner|breakup|"
    # Marriage
    r"shaadi|shadi|vivah|marriage|spouse|wife|husband|patni|pati|"
    r"kalatra|engagement|engaged|"
    # Romantic
    r"love|pyar|pyaar|girlfriend|boyfriend|crush|ishq|"
    # Health
    r"sehat|swasth|health|illness|disease|bimari|rog|body|"
    r"medical|hospital|doctor|"
    # Home / property
    r"ghar|home|makaan|makan|"
    # Children / family
    r"child|children|santaan|santan|bachhe|bachche|bachhon|baby|"
    r"family|parents|maa|maan|baap|pita|mata|"
    # Education
    r"study|studies|education|exam|padhai|college|university|school"
    r")\b",
    re.IGNORECASE,
)


# Sustained-problem pattern — the exact triggers GUARD-2 was supposed to
# catch. Keeping it tight on purpose: false positives here would over-fire
# the clarification gate on perfectly clear questions, which would feel
# more annoying than helpful.
_SUSTAINED_PROBLEM_RX = re.compile(
    r"("
    # "problem hi problem" / "samasya hi samasya"
    r"problem\s+hi\s+problem|samasya\s+hi\s+samasya|"
    # "sab kuch ulta" / "sab kuch galat" / "sab kuch bura"
    r"sab\s+(?:kuch\s+)?(?:ulta|galat|bura|kharab)|"
    # "kuch theek nahi" / "kuch bhi theek nahi"
    r"kuch\s+(?:bhi\s+)?theek\s+nahi|"
    # "X-Y mahine" or "X-Y months" or "X to Y mahine"
    r"\d+\s*(?:[-–to]+\s*)\d+\s+(?:mahine|months?|saal|years?)\s+se|"
    # "pichle X mahine" / "last X months"
    r"(?:pichle|pichhle|piche|last)\s+\d+\s+(?:mahine|months?|saal|years?)|"
    # Explicit contradiction wording
    r"contradiction|paradox|inconsistency|virodhabhas|"
    # "phir bhi" + negative — classic Hinglish contradiction marker
    r"phir\s+bhi.+?(?:problem|nahi|nahin|kharab|galat|bura|stuck)"
    r")",
    re.IGNORECASE,
)


def detect_domain_anchor(question: str) -> bool:
    """True when the question explicitly names a life-area anchor.

    Used by the Phase-2 safe-narration gate to decide whether the GUARD-2
    domain-clarification short-circuit should fire. A `True` here means the
    user told us where to look (career / paisa / rishtey / sehat / ghar /
    child / study / etc.) — no clarification needed.
    """
    return bool(_DOMAIN_ANCHOR_RX.search(question or ""))


def detect_sustained_problem(question: str) -> bool:
    """True when the question describes a sustained / recurring negative
    state pattern. Tight on purpose — false positives over-fire the
    clarification gate."""
    return bool(_SUSTAINED_PROBLEM_RX.search(question or ""))


def needs_domain_clarification(question: str) -> bool:
    """Composite signal — sustained problem AND no explicit domain anchor.
    This is the precondition the Phase-2 gate uses to short-circuit to a
    clarification template instead of calling the LLM."""
    if not question:
        return False
    return (detect_sustained_problem(question)
            and not detect_domain_anchor(question))


def _maybe_promote_analysis_for_why(question: str,
                                    intents_ranked: list[str],
                                    intent: str) -> tuple[list[str], str, bool]:
    """If the question is WHY-leading or describes a contradiction, promote
    `analysis` to PRIMARY. Demote whatever was primary down to secondary.
    Returns (new_intents_ranked, new_intent, promoted_flag).
    """
    if not question or not _WHY_LEADING_RX.search(question):
        return intents_ranked, intent, False
    if not intents_ranked:
        intents_ranked = [intent] if intent in INTENTS else ["analysis"]
    # Already analysis-primary? Nothing to do.
    if intents_ranked[0] == "analysis":
        return intents_ranked, intent, False
    # Build new ranking: analysis first, then keep the rest in order
    # (de-duped). Cap at 3.
    new_ranked = ["analysis"] + [i for i in intents_ranked if i != "analysis"]
    new_ranked = new_ranked[:3]
    return new_ranked, "analysis", True


# ── Main API ────────────────────────────────────────────────────────────────
# ── Phase 4.1 Fix-P: Classifier Sanity Layer ───────────────────────────────
# Deterministic post-classification override. The AI sometimes returns
# `intent="timing"` with confidence ≥ 0.9 for questions that are pure
# CHART-FACT lookups ("Nth house ka swami kaun hai", "Mangal dosh hai
# kya"). These questions have no temporal answer; routing them through the
# TIMING_QUERY narrator forces the model to invent dates. This sanity
# layer detects unambiguous lookup/yes-no patterns and re-tags such
# requests as `analysis` (the most flexible factual narrator). It runs
# AFTER the AI verdict and is confidence-blind — even 0.95 verdicts get
# corrected when the pattern is decisive. Every override is recorded on
# the returned dict (`intent_overridden_from`, `intent_override_reason`,
# `intent_override_phase`) so callers can trace it via the `1b.CLASSIFIER
# _OVERRIDE` telemetry hook in openai_helper.py.

# "Nth house ka swami / lord / malik / adhipati / owner"
_LOOKUP_LORD_RX = re.compile(
    r"\b\d{1,2}(?:st|nd|rd|th)?\s+(?:house|ghar|bhava|bhav)\s+"
    r"(?:k[ae]\s+)?(?:swami|lord|malik|adhipati|owner)\b",
    re.IGNORECASE,
)
# Karaka lookups
_LOOKUP_KARAKA_RX = re.compile(
    r"\b(?:atmakaraka|amatyakaraka|yogakaraka|darakaraka|"
    r"bhratrukaraka|matrukaraka|putrakaraka|gnati[\s\-]?karaka)\b",
    re.IGNORECASE,
)
# Yes/no dosha questions
_LOOKUP_DOSHA_YESNO_RX = re.compile(
    r"\b(?:manglik|mangal\s+dosh[ai]?|mangalik|nadi\s+dosh[ai]?|"
    r"bhakoot\s+dosh[ai]?|kaal\s+sarp|kalsarp|sade\s+sati|"
    r"kemdrum|chandal|guru\s+chandal|grahan\s+dosh)\b"
    r"[^.?!\n]{0,40}?\b(?:hai|hu|hain|ho|kya|hoon|hain\s+kya|hai\s+kya)\b",
    re.IGNORECASE,
)
# Generic yes/no chart-fact lookups ("kya mera 5th house strong hai", "5th
# house strong hai kya"). Phase 4.1 architect-required tightening: the
# bare "hai kya" / "kya mera" trigger was over-broad and would misroute
# legitimate decision asks like "ye decision sahi hai kya" or "invest
# karu ya nahi, sahi hai kya". The pattern now requires a CHART-FACT
# anchor (house/ghar/bhav, lord/swami/malik, graha/planet, dosh, karaka,
# rashi, nakshatra, dasha, lagna, kundli/kundali, bhagya, nadi, bhakoot,
# ascendant, horoscope, chart) within ±50 chars of the yes/no marker
# before the override is allowed to fire.
#
# Architect review-2 refinements:
#   - bare "yoga|yog" REMOVED — collided with non-astro usage ("yoga
#     class sahi hai kya"). Astrology yoga lookups ALWAYS pair with a
#     chart noun (kundli, house, lagna, dasha, planet, raj+yog compound)
#     so other anchors still catch them. The qualified compound forms
#     `rajyog|rajyoga|dhanyog|dhanyoga|gajakesari` are kept as discrete
#     tokens because they're unambiguously astrological.
#   - Added "kundali" spelling variant alongside "kundli" (also "janam
#     kundali") to recover Hindi-spelling lookup recall.
_LOOKUP_ANCHORS = (
    r"\b(?:house|ghar|bhav[ae]?|lord|swami|malik|adhipati|graha|grah|"
    r"planet|dosh[ai]?|karaka|rashi|nakshatra|dasha|antardasha|"
    r"mahadasha|lagna|kundli|kundali|bhagya|nadi|bhakoot|ascendant|"
    r"horoscope|chart|"
    r"raj\s*yog[a]?|dhan\s*yog[a]?|gajakesari|gaja\s*kesari)\b"
)
_LOOKUP_YESNO_MARKERS = (
    r"(?:\bkya\s+mer[ae]\b|\bkya\s+meri\b|"
    r"\b(?:hu|hoon|hai|hain|ho)\s+kya\b)"
)
_LOOKUP_GENERIC_YESNO_RX = re.compile(
    # anchor-then-yesno OR yesno-then-anchor, both within ±50 chars
    r"(?:" + _LOOKUP_ANCHORS + r"[^.?!\n]{0,50}?" + _LOOKUP_YESNO_MARKERS
    + r"|" + _LOOKUP_YESNO_MARKERS + r"[^.?!\n]{0,50}?" + _LOOKUP_ANCHORS
    + r")",
    re.IGNORECASE,
)


def _apply_classifier_sanity_layer(out: dict, question: str) -> dict:
    """Phase 4.1 Fix-P. Mutates and returns `out`.

    Override rule (conservative):
      - Trigger ONLY when the question matches a hard lookup pattern AND
        the AI returned `intent in {"timing", "decision"}` (the two most
        common false positives for lookup queries). Other intents are
        left alone — they're either already correct (`analysis`,
        `planet`) or domain-meaningful (`problem`).
      - Override target is always `analysis` (GENERAL_ANALYSIS narrator
        — flexible, doesn't force date prediction or remedy commitment).
      - Diagnostic fields added on the dict for telemetry tracing.
    """
    if not isinstance(out, dict) or not question:
        return out
    intent = (out.get("intent") or "").lower()
    if intent not in ("timing", "decision"):
        return out

    matched = None
    if _LOOKUP_LORD_RX.search(question):
        matched = "lookup_lord"
    elif _LOOKUP_KARAKA_RX.search(question):
        matched = "lookup_karaka"
    elif _LOOKUP_DOSHA_YESNO_RX.search(question):
        matched = "lookup_dosha_yesno"
    elif _LOOKUP_GENERIC_YESNO_RX.search(question):
        matched = "lookup_generic_yesno"

    if not matched:
        return out

    out["intent_overridden_from"] = intent
    out["intent_override_reason"] = matched
    out["intent_override_phase"]  = "4.1_fix_p"
    out["intent"] = "analysis"
    # Keep intents_ranked consistent so downstream multi-intent logic
    # doesn't see a stale primary at index 0.
    ranked = list(out.get("intents_ranked") or [])
    if not ranked or ranked[0] != "analysis":
        # Demote the original primary to secondary; promote analysis.
        new_ranked = ["analysis"] + [r for r in ranked if r != "analysis"]
        out["intents_ranked"] = new_ranked[:3]
    return out


def understand_question(question: str,
                        *,
                        client: Any = None,
                        model: Optional[str] = None) -> dict:
    """Public entry — Phase 4.1: applies classifier sanity layer (Fix-P)
    on top of the inner AI/regex classifier. Always returns the same dict
    shape; adds `intent_overridden_from`, `intent_override_reason`,
    `intent_override_phase` keys when an override fires.

    Phase 2.8.41 (May 02, 2026): also guarantees the 5 new SQU fields
    (subtopic, needs_engine, emotion, urgency, cleaned_q) plus
    final_topic_lock + clarification_text on every return path, even
    when an inner code path forgot to emit them.
    """
    q = (question or "").strip()
    out = _understand_question_inner(question, client=client, model=model)
    out = _apply_classifier_sanity_layer(out, q)
    # Phase 2.8.41 — defence-in-depth: every public-entry return guarantees
    # the new SQU fields. setdefault() keeps inner-path values intact when
    # they were already emitted; only fills missing ones.
    out.setdefault("subtopic", None)
    out.setdefault("needs_engine", True)
    out.setdefault("emotion", "neutral")
    out.setdefault("urgency", "medium")
    out.setdefault("cleaned_q", None)
    out.setdefault("final_topic_lock", out.get("topic") or "general")
    # clarification_text is computed every call — it depends on the FINAL
    # post-sanity-layer state of `out`, not the inner-path snapshot.
    out["clarification_text"] = _build_clarification_text(out)
    return out


def _understand_question_inner(question: str,
                        *,
                        client: Any = None,
                        model: Optional[str] = None) -> dict:
    """Single source of truth for question routing.

    Args:
        question: raw user text (1 line to a long paragraph).
        client:   optional pre-built OpenAI client (else we lazy-import).
        model:    optional model override (else env OPENAI_MODEL or 4.1-mini).

    Returns:
        {
          "intent":     one of INTENTS,
          "topic":      one of TOPICS,
          "confidence": float ∈ [0.0, 1.0],
          "source":     "ai" | "ai_low_conf_regex_fallback" |
                        "ai_error_regex_fallback" | "regex_fallback" | "empty",
          "latency_ms": int (when AI was called),
          # plus diagnostic echo when we fell back from AI:
          "ai_intent": ..., "ai_topic": ..., "ai_confidence": ..., "error": ...
        }

    Never raises — the caller can always trust the dict shape.
    """
    q = (question or "").strip()
    if not q:
        return {
            "intent":     "analysis",
            "topic":      "general",
            "confidence": 0.0,
            "source":     "empty",
            # Sprint-26 Fix-Q (post-architect-review): always emit the flag
            # so callers never see KeyError on the canonical contract.
            "has_recovery_subask": False,
            # Phase 7.1 — slot defaults emitted on empty-question path so
            # downstream consumers never KeyError. All slots are nulls /
            # safe defaults — there's nothing to extract from empty input.
            "focus":         None,
            "timeframe":     "none",
            "depth":         "medium",
            "user_keywords": [],
            # Phase 2.8.41 — SQU extension defaults on empty-question path.
            # No question to analyse → no engine work needed, neutral tone.
            "subtopic":         None,
            "needs_engine":     False,
            "emotion":          "neutral",
            "urgency":          "low",
            "cleaned_q":        None,
            "final_topic_lock": "general",
        }

    if model is None:
        model = os.environ.get("QU_MODEL") or os.environ.get(
            "OPENAI_MODEL", "gpt-4.1-mini")

    # Lazy-import the shared OpenAI client from openai_helper so we don't
    # double-init proxies / API-keys.
    if client is None:
        try:
            from openai_helper import _get_client  # type: ignore
            client = _get_client()
        except Exception:
            client = None

    if client is None:
        return _fallback_classify(q)

    t0 = time.time()
    try:
        # Phase 2.8.41 — gpt-5 series (and several proxy targets) renamed
        # `max_tokens` to `max_completion_tokens` and reject the legacy
        # name with HTTP 400. Try the new name first, fall back to the
        # legacy name for older models. Without this guard, EVERY SQU
        # call silently dropped to `_fallback_classify` (regex) — losing
        # all LLM-derived fields (subtopic, emotion, urgency, cleaned_q,
        # multi-intent) for the entire request.
        _create_kwargs = dict(
            model=model,
            temperature=0.1,
            timeout=_QU_TIMEOUT_S,
            response_format={"type": "json_object"},
            messages=[
                {"role": "user", "content": _PROMPT_TEMPLATE.format(question=q)}
            ],
        )
        try:
            resp = client.chat.completions.create(
                max_completion_tokens=380, **_create_kwargs
            )
        except TypeError:
            # SDK is too old to recognise the new kwarg.
            resp = client.chat.completions.create(
                max_tokens=380, **_create_kwargs
            )
        except Exception as exc:
            # Some servers raise BadRequestError instead of TypeError when
            # the kwarg is unknown — sniff the message for the rename hint
            # and retry with the legacy name. Anything else propagates.
            _msg = str(exc).lower()
            if ("max_tokens" in _msg and "max_completion_tokens" in _msg) \
                    or "use 'max_tokens'" in _msg:
                resp = client.chat.completions.create(
                    max_tokens=380, **_create_kwargs
                )
            else:
                raise
        latency_ms = int((time.time() - t0) * 1000)
        raw = (resp.choices[0].message.content or "").strip()
        data = json.loads(raw)

        intent = (data.get("intent") or "").strip().lower()
        topic  = (data.get("topic")  or "").strip().lower()
        try:
            conf = float(data.get("confidence") or 0.0)
        except (TypeError, ValueError):
            conf = 0.0
        # Clamp
        if conf < 0.0:
            conf = 0.0
        if conf > 1.0:
            conf = 1.0

        # Schema validation — bad enum value normally = fallback.
        # BUT if the AI returned a malformed singular `intent` / `topic`
        # (e.g. "finance | career") AND the corresponding ranked list has a
        # valid first element, recover from that. This keeps multi-intent
        # answers usable when the AI just confuses the singular field.
        if intent not in INTENTS:
            raw_ir = data.get("intents_ranked") or []
            for v in raw_ir:
                if isinstance(v, str) and v.strip().lower() in INTENTS:
                    intent = v.strip().lower()
                    break
        if topic not in TOPICS:
            raw_tp = data.get("topics_all") or []
            for v in raw_tp:
                if isinstance(v, str) and v.strip().lower() in TOPICS:
                    topic = v.strip().lower()
                    break
        if intent not in INTENTS or topic not in TOPICS:
            fb = _fallback_classify(q)
            fb["source"] = "ai_error_regex_fallback"
            fb["error"] = f"bad enum: intent={intent!r} topic={topic!r}"
            fb["latency_ms"] = latency_ms
            return fb

        # Confidence floor — under 0.6 we still return AI's view but mark it
        # as fallback so any threshold checks downstream can act.
        if conf < 0.6:
            fb = _fallback_classify(q)
            fb["source"] = "ai_low_conf_regex_fallback"
            fb["ai_intent"] = intent
            fb["ai_topic"] = topic
            fb["ai_confidence"] = conf
            fb["latency_ms"] = latency_ms
            # Keep AI's ranked extras even at low confidence — they're useful
            # diagnostics even if the engine routing uses regex primaries.
            fb.update(_normalise_multi_fields(data, intent, topic))
            # Phase 2.8.41 — also keep the AI's SQU-extension fields when
            # the call succeeded but confidence was below the floor. The
            # 5 new fields are independent of intent/topic accuracy, so
            # the AI's emotion / urgency / cleaned_q reads are still
            # useful for the narrator. final_topic_lock follows the
            # regex-derived `topic` already set in `fb` above.
            fb.update(_normalise_new_squ_fields(data))
            fb["final_topic_lock"] = fb.get("topic") or "general"
            return fb

        out = {
            "intent":     intent,
            "topic":      topic,
            "confidence": conf,
            "source":     "ai",
            "latency_ms": latency_ms,
        }
        out.update(_normalise_multi_fields(data, intent, topic))
        # Phase 2.8.41 — merge the 5 new SQU fields (subtopic, needs_engine,
        # emotion, urgency, cleaned_q). final_topic_lock is set further
        # below AFTER topic-recovery so engine + narrator align on the
        # final, post-override topic.
        out.update(_normalise_new_squ_fields(data))
        # Sprint-26 Fix-N: deterministic post-pass — promote `analysis` to
        # PRIMARY when the question is WHY-leading or names a contradiction.
        new_ranked, new_intent, promoted = _maybe_promote_analysis_for_why(
            q, out.get("intents_ranked") or [], out["intent"])
        if promoted:
            out["intents_ranked"] = new_ranked
            out["intent"] = new_intent
            out["why_promoted"] = True
        # Sprint-26 Fix-Q (post-architect-review): canonical recovery
        # sub-ask flag — emitted by every successful AI return path so
        # downstream consumers (wealth structured-output prompt, narrator
        # contract, post-validator) can rely on it without re-computing.
        out["has_recovery_subask"] = bool(_RECOVERY_SUBASK_RX.search(q))
        # ── Sprint-26 Step 4 Phase 2 — deterministic safety detectors ──
        # Three new flags surfaced on every AI-success return so the
        # downstream gate in openai_helper.py can short-circuit without
        # recomputing. Names are stable across all return paths (AI ok,
        # AI low-conf fallback, AI error fallback, regex fallback, empty).
        domain_anchor = detect_domain_anchor(q)
        sustained = detect_sustained_problem(q)
        out["domain_anchor_found"]      = domain_anchor
        out["sustained_problem_pattern"] = sustained
        out["clarification_needed"]      = sustained and not domain_anchor
        # Topic recovery — when the AI returned topic="general" but the
        # question text contains a clear life-area anchor, override using
        # the regex fallback so downstream domain-specific paths fire.
        # ONLY applies when topic was the catch-all 'general' AND a
        # specific anchor is found — never overrides an explicit AI
        # choice between two specific topics.
        if out.get("topic") == "general" and domain_anchor:
            for tname, rx in _FALLBACK_TOPIC_RX:
                if rx.search(q):
                    out["topic_recovered_from_general"] = True
                    out["topic_original_ai"] = "general"
                    out["topic"] = tname
                    existing = [t for t in (out.get("topics_all") or [])
                                if t != tname and t != "general"]
                    out["topics_all"] = [tname] + existing
                    break
        # Phase 2.8.41 — final_topic_lock is the canonical post-recovery
        # topic. Engine routing + narrator topic-context both read this
        # so they never drift apart from the AI's original `topic` field.
        out["final_topic_lock"] = out.get("topic") or "general"
        return out
    except Exception as exc:
        latency_ms = int((time.time() - t0) * 1000)
        fb = _fallback_classify(q)
        fb["source"] = "ai_error_regex_fallback"
        fb["error"] = str(exc)[:200]
        fb["latency_ms"] = latency_ms
        return fb


# ── intent → narrator supertype mapping ─────────────────────────────────────
# Drives which strict contract block is injected into the system prompt.
# Keys MUST match the canonical supertype identifiers used by
# `_SUPERTYPE_CONTRACT_BLOCKS` and `_validate_supertype_contract` in
# openai_helper.py — i.e. the `*_QUERY` suffix for timing/problem/decision.
_INTENT_TO_SUPERTYPE = {
    "planet":   "STRENGTH_SUMMARY",   # strong/weak/vargottam grounded answer
    "timing":   "TIMING_QUERY",       # when / kab / how-long
    "problem":  "PROBLEM_QUERY",      # dosha / why-not-working
    "decision": "DECISION_QUERY",     # should-I / chahiye / muhurat
    "analysis": "GENERAL_ANALYSIS",   # default narrator
}


def supertype_for(intent: str) -> str:
    """Map AI intent → narrator supertype used by the contract system."""
    return _INTENT_TO_SUPERTYPE.get((intent or "").lower(), "GENERAL_ANALYSIS")
