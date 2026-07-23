"""DNA / bucket-aware follow-up suggestion chips (same-domain only)."""
from __future__ import annotations

from typing import Any

# domain → lang → chips (same thread, never cross-domain)
_CHIPS: dict[str, dict[str, list[str]]] = {
    "love": {
        "hn": [
            "Kab trust improve hoga?",
            "Kya commitment strong hai?",
            "Is relationship ka upay batao",
        ],
        "hi": [
            "कब विश्वास सुधरेगा?",
            "क्या commitment मजबूत है?",
            "इस रिश्ते का उपाय बताइए",
        ],
        "en": [
            "When will trust improve?",
            "Is commitment strong?",
            "Suggest a remedy for this bond",
        ],
    },
    "marriage": {
        "hn": [
            "Shaadi ka exact time window?",
            "Future partner kaisa hoga?",
            "Delay kyun dikh rahi hai?",
        ],
        "hi": [
            "शादी का सही समय?",
            "जीवनसाथी कैसे होंगे?",
            "देरी क्यों दिख रही है?",
        ],
        "en": [
            "Exact marriage timing window?",
            "What will my spouse be like?",
            "Why does delay show?",
        ],
    },
    "career": {
        "hn": [
            "Promotion kab hogi?",
            "Job change ka sahi time?",
            "Best field mere liye?",
        ],
        "hi": [
            "पदोन्नति कब होगी?",
            "नौकरी बदलने का समय?",
            "मेरे लिए सर्वश्रेष्ठ क्षेत्र?",
        ],
        "en": [
            "When is promotion likely?",
            "Best time to switch jobs?",
            "Best career field for me?",
        ],
    },
    "finance": {
        "hn": [
            "Dhan yog kab khulega?",
            "Loan kab utrega?",
            "Investment ka shubh time?",
        ],
        "hi": [
            "धन योग कब खुलेगा?",
            "कर्ज़ कब उतरेगा?",
            "निवेश का शुभ समय?",
        ],
        "en": [
            "When does wealth yoga open?",
            "When will debt clear?",
            "Auspicious time to invest?",
        ],
    },
    "health": {
        "hn": [
            "Kab health improve hogi?",
            "Kis ang mein dosh hai?",
            "Swasthya ka upay batao",
        ],
        "hi": [
            "कब स्वास्थ्य सुधरेगा?",
            "किस अंग में दोष है?",
            "स्वास्थ्य का उपाय बताइए",
        ],
        "en": [
            "When will health improve?",
            "Which body area is afflicted?",
            "Suggest a health remedy",
        ],
    },
    "education": {
        "hn": ["Padhai mein safalta kab?", "Foreign study yog?", "Vidya ka upay?"],
        "hi": ["पढ़ाई में सफलता कब?", "विदेश अध्ययन योग?", "विद्या का उपाय?"],
        "en": ["Study success timing?", "Foreign study yoga?", "Remedy for studies?"],
    },
    "property": {
        "hn": ["Ghar kab banega / milega?", "Property deal sahi hai?", "Vastu tip?"],
        "hi": ["घर कब बनेगा/मिलेगा?", "प्रॉपर्टी डील सही है?", "वास्तु सुझाव?"],
        "en": ["When will I get a home?", "Is this property deal good?", "Vastu tip?"],
    },
    "travel": {
        "hn": ["Videsh kab yog?", "Travel delay kyun?", "Safar ka upay?"],
        "hi": ["विदेश कब योग?", "यात्रा में देरी क्यों?", "सफ़र का उपाय?"],
        "en": ["Foreign travel timing?", "Why travel delay?", "Travel remedy?"],
    },
    "children": {
        "hn": ["Santan yog kab?", "Pregnancy timing?", "Children ke liye upay?"],
        "hi": ["संतान योग कब?", "गर्भधारण समय?", "संतान का उपाय?"],
        "en": ["Children yoga timing?", "Pregnancy window?", "Remedy for children?"],
    },
    "general": {
        "hn": ["Aur detail mein batao", "Iska upay batao", "Exact timing batao"],
        "hi": ["और विस्तार से बताइए", "इसका उपाय बताइए", "सही समय बताइए"],
        "en": ["Tell me in more detail", "Suggest a remedy", "Give exact timing"],
    },
}

# bucket-specific overrides (love / MR)
_BUCKET_CHIPS: dict[str, dict[str, list[str]]] = {
    "trust_loyalty": {
        "hn": ["Kab vishwas wapas aayega?", "Cheat yog kitna strong?", "Loyalty improve ka upay?"],
        "en": ["When will trust return?", "How strong is cheat yoga?", "Remedy to improve loyalty?"],
        "hi": ["कब विश्वास वापस आएगा?", "धोखा योग कितना मजबूत?", "निष्ठा सुधार का उपाय?"],
    },
    "loyalty_trust": {
        "hn": ["Kab vishwas wapas aayega?", "Cheat yog kitna strong?", "Loyalty improve ka upay?"],
        "en": ["When will trust return?", "How strong is cheat yoga?", "Remedy to improve loyalty?"],
        "hi": ["कब विश्वास वापस आएगा?", "धोखा योग कितना मजबूत?", "निष्ठा सुधार का उपाय?"],
    },
    "commitment": {
        "hn": ["Serious hai ya time-pass?", "Shaadi tak jayega?", "Commitment kab strong hoga?"],
        "en": ["Serious or time-pass?", "Will this lead to marriage?", "When will commitment strengthen?"],
        "hi": ["सीरियस है या टाइमपास?", "शादी तक जाएगा?", "प्रतिबद्धता कब मजबूत होगी?"],
    },
    "relationship_future": {
        "hn": ["Agle 1 saal me kya hoga?", "Breakup risk kitna?", "Future strong hai?"],
        "en": ["What happens in next 1 year?", "Breakup risk level?", "Is the future strong?"],
        "hi": ["अगले 1 साल में क्या होगा?", "ब्रेकअप जोखिम?", "भविष्य मजबूत है?"],
    },
    "dating_courtship": {
        "hn": ["Proposal kab?", "Accept karegi/karega?", "Approach ka sahi time?"],
        "en": ["When to propose?", "Will they accept?", "Best time to approach?"],
        "hi": ["प्रस्ताव कब?", "स्वीकार करेंगे?", "अप्रोच का सही समय?"],
    },
    "wealth_potential": {
        "hn": ["Paisa kab badhega?", "Loss kab rukega?", "Savings kaise badhe?"],
        "en": ["When will money grow?", "When do losses stop?", "How to grow savings?"],
        "hi": ["पैसा कब बढ़ेगा?", "नुकसान कब रुकेगा?", "बचत कैसे बढ़े?"],
    },
    "career_milestones": {
        "hn": ["Promotion kab?", "Appraisal strong hai?", "Boss support milega?"],
        "en": ["Promotion timing?", "Is appraisal strong?", "Will boss support me?"],
        "hi": ["पदोन्नति कब?", "एप्रैज़ल मजबूत है?", "बॉस सपोर्ट मिलेगा?"],
    },
}


def _lang_key(lang: str) -> str:
    l = (lang or "hn").lower()
    if l.startswith("hi"):
        return "hi"
    if l.startswith("en"):
        return "en"
    return "hn"


def derive_follow_up_chips(
    *,
    topic: str = "",
    domain: str = "",
    bucket: str = "",
    lang: str = "hn",
    is_timing: bool = False,
) -> list[str]:
    """Return ≤3 same-domain chips. Never cross into another life area."""
    lk = _lang_key(lang)
    dom = (domain or topic or "general").strip().lower()
    if dom in ("relationship", "mr", "static"):
        dom = "love" if dom != "static" else "general"
    if dom == "timing":
        dom = domain.strip().lower() if domain else "general"
    buck = (bucket or "").strip().lower()

    chips: list[str] = []
    if buck and buck in _BUCKET_CHIPS:
        by_lang = _BUCKET_CHIPS[buck]
        chips = list(by_lang.get(lk) or by_lang.get("hn") or [])
    if not chips:
        by_dom = _CHIPS.get(dom) or _CHIPS["general"]
        chips = list(by_dom.get(lk) or by_dom.get("hn") or [])

    if is_timing and chips:
        # Prefer timing-flavored first chip when answering a timing Q
        timing_chip = {
            "hn": "Exact month / window batao",
            "hi": "सही महीना / समय बताइए",
            "en": "Give the exact month / window",
        }.get(lk, "Exact month / window batao")
        if timing_chip not in chips:
            chips = [timing_chip] + [c for c in chips if c != timing_chip]

    return chips[:3]


def enrich_ask_result_followups(
    result: dict[str, Any] | None,
    *,
    lang: str = "hn",
    admin: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fill follow_ups + domain/bucket on an Ask result dict (in-place)."""
    if not isinstance(result, dict):
        return {}
    admin = admin if isinstance(admin, dict) else {}
    dna = admin.get("question_dna") if isinstance(admin.get("question_dna"), dict) else {}
    items = dna.get("questions") if isinstance(dna.get("questions"), list) else []
    item = items[0] if items and isinstance(items[0], dict) else {}

    domain = str(
        result.get("domain")
        or admin.get("routed_domain")
        or admin.get("domain")
        or item.get("domain")
        or ""
    ).strip().lower()
    bucket = str(
        result.get("bucket")
        or admin.get("bucket")
        or item.get("bucket")
        or admin.get("dna_engine_archetype")
        or ""
    ).strip().lower()
    topic = str(result.get("topic") or domain or "general").strip().lower()
    is_timing = bool(
        result.get("question_type") == "TIMING"
        or admin.get("routed_timing")
        or admin.get("is_timing")
        or item.get("timing")
    )
    archetype = str(
        result.get("archetype")
        or admin.get("dna_engine_archetype")
        or admin.get("routed_archetype")
        or bucket
        or ""
    ).strip().lower()

    if domain:
        result["domain"] = domain
    if bucket:
        result["bucket"] = bucket
    if archetype:
        result["archetype"] = archetype
    if admin.get("subject") or item.get("subject"):
        result["subject"] = admin.get("subject") or item.get("subject")

    existing = result.get("follow_ups")
    if not (isinstance(existing, list) and any(str(x).strip() for x in existing)):
        result["follow_ups"] = derive_follow_up_chips(
            topic=topic,
            domain=domain or topic,
            bucket=bucket or archetype,
            lang=lang,
            is_timing=is_timing,
        )
    return result
