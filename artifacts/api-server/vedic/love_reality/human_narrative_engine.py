"""
Love Reality Pro — engine-side human narrative package.

Builds story cards, wrong-story pairs, combined placement lines, and micro-scenes
BEFORE the LLM runs so output reads like a consultation, not a placement list.
"""
from __future__ import annotations

import re
from typing import Any

from vedic.love_reality.pdf_text_safe import polish_content_lang

FRICTION_IDS = (
    "emotional_timing",
    "communication_style",
    "trust_consistency",
    "commitment_pace",
    "conflict_escalation",
)

# Each section owns one narrative angle — other sections must not steal it.
SECTION_THEME_OWNER: dict[str, str] = {
    "verdict": "hook",
    "blueprint_reality": "commitment",
    "breakup": "root_why",
    "loyalty": "trust",
    "moon_sync": "rhythm",
    "red_flags": "conflict",
    "harmony": "long_term",
    "dasha": "cycles",
    "roadmap": "future_arc",
    "remedies_action": "repair",
}

FRICTION_TO_THEME: dict[str, str] = {
    "emotional_timing": "timing",
    "communication_style": "communication",
    "trust_consistency": "trust",
    "commitment_pace": "commitment",
    "conflict_escalation": "conflict",
}

_AIR_SIGNS = frozenset({"gemini", "libra", "aquarius", "mithun", "tula", "kumbh"})
_EARTH_SIGNS = frozenset({"taurus", "virgo", "capricorn", "vrishabh", "kanya", "makar"})
_FIRE_SIGNS = frozenset({"aries", "leo", "sagittarius", "mesh", "singh", "dhanu"})
_WATER_SIGNS = frozenset({"cancer", "scorpio", "pisces", "kark", "vrishchik", "meen"})


def _norm_sign(raw: Any) -> str:
    return re.sub(r"[^a-z]", "", str(raw or "").strip().lower())


def _person_name(bundle: dict, key: str, fallback: str) -> str:
    p = bundle.get(key) or {}
    return str(p.get("name") or fallback).strip()


def _person_sign(bundle: dict, key: str, field: str) -> str:
    p = bundle.get(key) or {}
    return _norm_sign(p.get(field) or p.get("rashi") or "")


def _score_int(block: dict | None, *keys: str) -> int | None:
    if not isinstance(block, dict):
        return None
    for k in keys:
        v = block.get(k)
        if v is not None:
            try:
                return int(v)
            except (TypeError, ValueError):
                continue
    return None


def _reason_blob(bundle: dict) -> str:
    parts: list[str] = []
    for block_key in ("breakup_chances", "hidden_red_flags", "loyalty_check", "love_compatibility"):
        block = bundle.get(block_key) or {}
        parts.append(str(block.get("emotional_summary") or ""))
        for r in block.get("reasons") or []:
            parts.append(str(r))
    sig = bundle.get("couple_signals") or {}
    for n in sig.get("synastry_notes") or []:
        parts.append(str(n))
    return " ".join(parts).lower()


def pick_primary_friction(bundle: dict) -> str:
    """Lock one root friction for the whole report."""
    scores = {fid: 0 for fid in FRICTION_IDS}
    blob = _reason_blob(bundle)
    sig = bundle.get("couple_signals") or {}

    if sig.get("moon_mismatch"):
        scores["emotional_timing"] += 4
    loyalty = _score_int(bundle.get("loyalty_check"), "loyalty_score", "score")
    if loyalty is not None and loyalty < 52:
        scores["trust_consistency"] += 5
    breakup = _score_int(bundle.get("breakup_chances"), "breakup_score", "score")
    if breakup is not None and breakup > 58:
        scores["conflict_escalation"] += 4
    love = _score_int(bundle.get("love_compatibility"), "love_score", "score")
    if love is not None and love < 50:
        scores["commitment_pace"] += 3

    kw_map = {
        "communication_style": (
            "communication", "reply", "text", "message", "silent", "chup", "bolna", "sunna",
        ),
        "trust_consistency": (
            "trust", "loyal", "doubt", "bharosa", "consistent", "faith", "secret",
        ),
        "emotional_timing": (
            "timing", "fast", "slow", "pace", "delay", "jaldi", "wait", "rhythm", "space",
        ),
        "commitment_pace": (
            "commitment", "marriage", "shaadi", "future", "long-term", "stability", "bond",
        ),
        "conflict_escalation": (
            "fight", "argument", "ultimatum", "gussa", "conflict", "break", "separation",
        ),
    }
    for fid, words in kw_map.items():
        for w in words:
            if w in blob:
                scores[fid] += 1

    best = max(scores, key=lambda k: scores[k])
    if scores[best] <= 0:
        return "emotional_timing"
    return best


def _friction_label(friction_id: str, lang: str) -> str:
    lane = polish_content_lang(lang)
    table = {
        "emotional_timing": {
            "en": "emotional timing mismatch",
            "hn": "emotional timing ka mismatch",
            "hi": "भावनात्मक समय का मेल न होना",
        },
        "communication_style": {
            "en": "different communication rhythms",
            "hn": "alag communication rhythm",
            "hi": "अलग संवाद की लय",
        },
        "trust_consistency": {
            "en": "trust read through consistency",
            "hn": "trust consistency se measure hota hai",
            "hi": "भरोसा निरंतरता से जुड़ा है",
        },
        "commitment_pace": {
            "en": "different commitment pace",
            "hn": "commitment ki alag speed",
            "hi": "प्रतिबद्धता की अलग गति",
        },
        "conflict_escalation": {
            "en": "conflict escalation pattern",
            "hn": "jhagde tezi se badhne ka pattern",
            "hi": "झगड़े तेज़ी से बढ़ने का पैटर्न",
        },
    }
    return table.get(friction_id, {}).get(lane, table.get(friction_id, {}).get("en", friction_id))


def _element_of(sign: str) -> str:
    if sign in _AIR_SIGNS:
        return "air"
    if sign in _EARTH_SIGNS:
        return "earth"
    if sign in _FIRE_SIGNS:
        return "fire"
    if sign in _WATER_SIGNS:
        return "water"
    return "mixed"


def build_combined_placement_story(bundle: dict, lang: str) -> str:
    """One synthesized line — placements combined, not listed."""
    lane = polish_content_lang(lang)
    p1n = _person_name(bundle, "p1", "You")
    p2n = _person_name(bundle, "p2", "Partner")
    m1 = _person_sign(bundle, "p1", "moonSign")
    m2 = _person_sign(bundle, "p2", "moonSign")
    e1, e2 = _element_of(m1), _element_of(m2)

    if lane == "hn":
        if e1 == "air" and e2 == "earth":
            return (
                f"{p1n} ka mind jaldi react karta hai (air Moon), {p2n} ka heart stability "
                f"chahta hai (earth Moon) — attraction strong hai par jab tum jawab maangte ho "
                f"aur woh andar settle karte hain, wahi loop repeat hota hai."
            )
        if e1 == "fire" and e2 == "water":
            return (
                f"{p1n} jaldi move karte ho (fire Moon), {p2n} pehle feel karte hain phir bolte hain "
                f"(water Moon) — tum speed samajhte ho care, woh pause samajhte hain respect."
            )
        return (
            f"{p1n} aur {p2n} ke Moon alag rhythm me chalte hain — tum jaldi clear karna chahte ho, "
            f"woh pehle andar process karte hain. Yeh galti nahi, pattern hai."
        )
    if lane == "hi":
        return (
            f"{p1n} का मन जल्दी प्रतिक्रिया देता है, {p2n} को पहले भीतर संभलने का समय चाहिए — "
            f"आकर्षण सच्चा है, पर जब आप जवाब माँगते हैं और वे चुप रहते हैं, वही लूप दोहराता है।"
        )
    if e1 == "air" and e2 == "earth":
        return (
            f"{p1n}'s mind moves fast (air Moon) while {p2n}'s heart wants stability "
            f"(earth Moon) — attraction is real, but when you chase clarity and they need "
            f"inner settle time, the same loop returns."
        )
    if e1 == "fire" and e2 == "water":
        return (
            f"{p1n} moves quickly (fire Moon); {p2n} feels first and speaks later (water Moon) — "
            f"you read speed as care, they read pause as respect."
        )
    return (
        f"{p1n} and {p2n} run on different emotional rhythms — you want clarity sooner, "
        f"they process inside first. That is pattern, not fault."
    )


def build_wrong_story_pair(bundle: dict, friction_id: str, lang: str) -> dict[str, str]:
    lane = polish_content_lang(lang)
    p1n = _person_name(bundle, "p1", "You")
    p2n = _person_name(bundle, "p2", "Partner")
    pairs = {
        "emotional_timing": {
            "en": (
                f"When {p2n} goes quiet, {p1n} reads it as 'they don't care.' "
                f"When {p1n} pushes for an answer, {p2n} reads it as control."
            ),
            "hn": (
                f"Jab {p2n} chup hote hain, {p1n} padhte hain 'unhe farak nahi.' "
                f"Jab {p1n} jawab maangte hain, {p2n} padhte hain 'control ho raha hai.'"
            ),
            "hi": (
                f"जब {p2n} चुप होते हैं, {p1n} पढ़ते हैं 'उन्हें फर्क नहीं।' "
                f"जब {p1n} जवाब माँगते हैं, {p2n} पढ़ते हैं 'दबाव बन रहा है।'"
            ),
        },
        "communication_style": {
            "en": (
                f"{p1n} expects a reply to mean respect; {p2n} expects space to mean trust."
            ),
            "hn": (
                f"{p1n} reply ko respect samajhte hain; {p2n} space ko trust samajhte hain."
            ),
            "hi": (
                f"{p1n} जवाब को सम्मान मानते हैं; {p2n} जगह को भरोसा मानते हैं।"
            ),
        },
        "trust_consistency": {
            "en": (
                f"{p1n} measures love through consistency; {p2n} measures freedom through flexibility — "
                f"both think the other is changing the rules."
            ),
            "hn": (
                f"{p1n} love ko consistency se measure karte hain; {p2n} freedom ko flexibility se — "
                f"dono sochte hain saamne wala rules badal raha hai."
            ),
            "hi": (
                f"{p1n} प्रेम को निरंतरता से मापते हैं; {p2n} आज़ादी को लचीलेपन से — "
                f"दोनों सोचते हैं सामने वाला नियम बदल रहा है।"
            ),
        },
        "commitment_pace": {
            "en": (
                f"{p1n} wants the next step named; {p2n} wants the present to feel safe first — "
                f"one reads delay as rejection, the other reads rush as pressure."
            ),
            "hn": (
                f"{p1n} agla step clear chahte hain; {p2n} pehle present safe feel karna chahte hain — "
                f"ek delay ko rejection padhte hain, doosra rush ko pressure."
            ),
            "hi": (
                f"{p1n} अगला कदम साफ चाहते हैं; {p2n} पहले वर्तमान सुरक्षित महसूस करना चाहते हैं — "
                f"एक देरी को अस्वीकार समझते हैं, दूसरा जल्दबाज़ी को दबाव।"
            ),
        },
        "conflict_escalation": {
            "en": (
                f"{p1n} wants to fix the fight tonight; {p2n} needs cooldown before talk — "
                f"by morning both remember the wound, not the repair."
            ),
            "hn": (
                f"{p1n} fight same raat solve karna chahte hain; {p2n} pehle cool down chahte hain — "
                f"subah dono wound yaad rakhte hain, repair nahi."
            ),
            "hi": (
                f"{p1n} झगड़ा उसी रात सुलझाना चाहते हैं; {p2n} पहले शांत होना चाहते हैं — "
                f"सुबह दोनों घाव याद रखते हैं, मरम्मत नहीं।"
            ),
        },
    }
    block = pairs.get(friction_id) or pairs["emotional_timing"]
    return {"pair_line": block.get(lane, block["en"])}


_SCENE_BANK: dict[str, dict[str, list[str]]] = {
    "timing": {
        "en": [
            "You send a message and check if they saw it — when the reply comes hours later, your mind fills the worst story.",
            "A small argument at night becomes 'they don't care' by morning because repair waited too long.",
        ],
        "hn": [
            "Tum message bhejte ho aur dekhte ho seen hua ya nahi — reply late aaye to dimaag sabse bura assume kar leta hai.",
            "Raat ki chhoti baat subah 'unhe farak nahi' ban jati hai jab repair 48 ghante delay ho.",
        ],
        "hi": [
            "आप मैसेज भेजकर देखते हैं seen हुआ या नहीं — जवाब देर से आए तो दिमाग सबसे बुरा मान लेता है।",
            "रात की छोटी बात सुबह 'उन्हें फर्क नहीं' बन जाती है जब मरम्मत में देरी हो।",
        ],
    },
    "communication": {
        "en": [
            "One of you expects a reply within minutes; the other replies after they have fully thought it through.",
            "WhatsApp 'typing…' then silence — that pause hurts one of you more than the actual fight.",
        ],
        "hn": [
            "Ek partner minutes me reply expect karta hai; doosra poora soch kar baad me likhta hai.",
            "WhatsApp par typing dikhe phir chup — woh pause asli fight se zyada chubhta hai.",
        ],
        "hi": [
            "एक साथी मिनटों में जवाब चाहता है; दूसरा पूरा सोचकर बाद में लिखता है।",
            "व्हाट्सऐप पर टाइपिंग दिखे फिर चुप्पी — वह ठहराव असली झगड़े से ज़्यादा चुभता है।",
        ],
    },
    "trust": {
        "en": [
            "When they put the phone face-down, you start checking trust instead of asking what they need.",
            "They cancel one plan and you replay every past promise — the chart flags consistency stress, not cruelty.",
        ],
        "hn": [
            "Jab woh phone ulta rakhte hain, tum trust check karne lagte ho — seedha puchna band ho jata hai.",
            "Ek plan cancel hua aur purani saari baatein yaad aa jati hain — chart consistency stress dikhata hai, cruelty nahi.",
        ],
        "hi": [
            "जब वे फ़ोन उलटा रखते हैं, आप भरोसा जाँचने लगते हैं — सीधा पूछना बंद हो जाता है।",
            "एक योजना रद्द हुई और पुरानी सारी बातें याद आ जाती हैं — चार्ट निरंतरता का तनाव दिखाता है।",
        ],
    },
    "conflict": {
        "en": [
            "At peak anger one of you threatens to leave; the other goes silent — both think they were the reasonable one.",
            "The same fight returns every 6–8 weeks with the same trigger, only the details change.",
        ],
        "hn": [
            "Gusse ke peak par ek 'chhod dunga/chhod dungi' bol deta hai; doosra chup — dono sochte hain main reasonable tha.",
            "Wahi fight har 6–8 hafte repeat hoti hai — trigger same, detail alag.",
        ],
        "hi": [
            "गुस्से के चरम पर एक 'छोड़ दूँगा/दूँगी' कह देता है; दूसरा चुप — दोनों सोचते हैं मैं उचित था।",
            "वही झगड़ा हर ६–८ हफ़्ते दोहराता है — ट्रिगर वही, बस विवरण बदलते हैं।",
        ],
    },
    "commitment": {
        "en": [
            "Family asks 'when is the next step?' and you two answer with different timelines in your head.",
            "You feel ready to name the future; they want one more month of stability before any big talk.",
        ],
        "hn": [
            "Ghar wale puchte hain 'agla step kab?' — tum dono ke dimaag me alag timeline hoti hai.",
            "Tum future clear karna chahte ho; unhe badi baat se pehle ek mahina aur stability chahiye.",
        ],
        "hi": [
            "घर वाले पूछते हैं 'अगला कदम कब?' — आप दोनों के मन में अलग समयरेखा होती है।",
            "आप भविष्य साफ करना चाहते हैं; उन्हें बड़ी बात से पहले एक महीना और स्थिरता चाहिए।",
        ],
    },
}


def pick_micro_scenes(friction_id: str, section_key: str, lang: str) -> list[str]:
    lane = polish_content_lang(lang)
    theme = FRICTION_TO_THEME.get(friction_id, "timing")
    owner = SECTION_THEME_OWNER.get(section_key, "")
    if owner == "trust":
        theme = "trust"
    elif owner == "conflict":
        theme = "conflict"
    elif owner == "commitment":
        theme = "commitment"
    elif owner in ("rhythm", "cycles", "hook", "root_why"):
        theme = FRICTION_TO_THEME.get(friction_id, "timing")
    bank = _SCENE_BANK.get(theme) or _SCENE_BANK["timing"]
    scenes = bank.get(lane) or bank["en"]
    return scenes[:2]


def forbidden_theme_words(section_key: str, friction_id: str) -> list[str]:
    """Themes this section must NOT lean on (owned by other sections)."""
    if section_key in ("breakup", "verdict"):
        return []

    primary_theme = FRICTION_TO_THEME.get(friction_id, "timing")
    my_owner = SECTION_THEME_OWNER.get(section_key, "")
    owner_to_theme: dict[str, str | None] = {
        "trust": "trust",
        "conflict": "conflict",
        "commitment": "commitment",
        "rhythm": "timing",
        "cycles": "timing",
        "repair": "communication",
        "long_term": "commitment",
        "future_arc": "commitment",
        "root_why": primary_theme,
        "hook": None,
    }
    my_theme = owner_to_theme.get(my_owner)
    theme_words = {
        "communication": ("communication", "reply", "text", "message", "whatsapp", "silent", "chup"),
        "timing": ("timing", "fast", "slow", "pace", "delay", "jaldi", "wait"),
        "trust": ("trust", "loyal", "consistency", "doubt", "bharosa"),
        "conflict": ("ultimatum", "fight", "argument", "gussa", "conflict"),
        "commitment": ("marriage", "shaadi", "commitment", "long-term"),
    }
    forbid: list[str] = []
    for sec, sec_owner in SECTION_THEME_OWNER.items():
        if sec == section_key:
            continue
        other_theme = owner_to_theme.get(sec_owner)
        if other_theme and other_theme != my_theme:
            forbid.extend(theme_words.get(other_theme, ()))
    seen: set[str] = set()
    out: list[str] = []
    for w in forbid:
        k = w.lower()
        if k not in seen:
            seen.add(k)
            out.append(w)
    return out[:12]


def build_story_cards(bundle: dict, lang: str) -> dict[str, Any]:
    friction_id = pick_primary_friction(bundle)
    lane = polish_content_lang(lang)
    wrong = build_wrong_story_pair(bundle, friction_id, lang)
    return {
        "friction_id": friction_id,
        "primary_label": _friction_label(friction_id, lang),
        "primary_theme": FRICTION_TO_THEME.get(friction_id, "timing"),
        "combined_story": build_combined_placement_story(bundle, lang),
        "wrong_story": wrong["pair_line"],
        "p1_name": _person_name(bundle, "p1", "You"),
        "p2_name": _person_name(bundle, "p2", "Partner"),
        "lang": lane,
    }


def format_global_story_block(cards: dict[str, Any]) -> str:
    return (
        "HUMAN NARRATIVE ENGINE (mandatory — placements explain mat karo, story explain karo):\n"
        f"SINGLE ROOT CAUSE (poori report isi ke around): {cards['primary_label']}\n"
        f"COMBINED CHART STORY (use as spine — do NOT list Moon/Venus/Mercury separately):\n"
        f"{cards['combined_story']}\n\n"
        f"WRONG STORY BOTH READ (mirror this once per section where natural):\n"
        f"{cards['wrong_story']}\n\n"
        "RULES:\n"
        "- Planet/house list dump forbidden — weave combined story instead.\n"
        "- Open with a real-life scene, not theory.\n"
        "- p1-first voice — reader must feel 'ye mere saath hota hai'.\n"
        "- No hedge words (may, might, potentially, mutual understanding).\n"
        "- No Key Takeaway / What To Do Next blocks — end on one sharp observation.\n"
        "- Scores at most twice in this section — prefer 'this phase' / 'this band'.\n"
    )


def format_section_story_block(cards: dict[str, Any], section_key: str) -> str:
    scenes = pick_micro_scenes(cards["friction_id"], section_key, cards["lang"])
    forbid = forbidden_theme_words(section_key, cards["friction_id"])
    scene_lines = "\n".join(f"- {s}" for s in scenes)
    forbid_line = ", ".join(forbid) if forbid else "(none)"
    owner = SECTION_THEME_OWNER.get(section_key, "angle")
    return (
        f"SECTION SCENES (weave at least ONE into prose — do not copy as bullets):\n"
        f"{scene_lines}\n\n"
        f"THIS SECTION OWNS: {owner}\n"
        f"DO NOT REPEAT THESE THEMES (other sections own them): {forbid_line}"
    )


def enrich_bundle_for_section(bundle: dict, section_key: str, cards: dict[str, Any]) -> dict:
    """Per-section bundle copy for parallel LLM jobs."""
    out = dict(bundle)
    out["_lr_section_key"] = section_key
    out["_lr_story_cards"] = cards
    blocks = [format_global_story_block(cards), format_section_story_block(cards, section_key)]
    out["_lr_story_block"] = "\n\n".join(blocks)
    out["_lr_forbidden_themes"] = forbidden_theme_words(section_key, cards["friction_id"])
    return out


def build_root_cause_anchor_text(bundle: dict, lang: str, cards: dict[str, Any] | None = None) -> str:
    if cards is None:
        cards = build_story_cards(bundle, lang)
    lane = polish_content_lang(lang)
    primary = cards["primary_label"]
    if lane == "hn":
        return (
            "ROOT_CAUSE (poori report isi ek reason ke around — har chapter alag angle):\n"
            f"Primary friction: {primary}\n"
            f"Combined story: {cards['combined_story']}\n"
            f"Wrong story: {cards['wrong_story']}\n\n"
            "Breakup chapter = root cause KYUN exist karta hai. "
            "Baaki chapters = naya angle — same warning / score / communication repeat mat."
        )
    if lane == "hi":
        return (
            "ROOT_CAUSE (पूरी रिपोर्ट इसी एक कारण के इर्द-गिर्द):\n"
            f"मुख्य घर्षण: {primary}\n"
            f"संयुक्त कथा: {cards['combined_story']}\n"
            f"गलत कहानी: {cards['wrong_story']}\n\n"
            "ब्रेकअप अध्याय = मूल कारण क्यों है। अन्य अध्याय = नया कोण — दोहराव नहीं।"
        )
    return (
        "ROOT_CAUSE (entire report orbits this one friction — each chapter a new angle):\n"
        f"Primary friction: {primary}\n"
        f"Combined story: {cards['combined_story']}\n"
        f"Wrong story: {cards['wrong_story']}\n\n"
        "Breakup chapter OWNS why this root cause exists. "
        "Other chapters extend it — never repeat the same warning or score."
    )
