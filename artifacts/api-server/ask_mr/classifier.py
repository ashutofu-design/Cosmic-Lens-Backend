from __future__ import annotations

import re


def classify_mr_archetype(question: str) -> str:
    """Return MR non-timing archetype id for routing."""
    q = (question or "").strip().lower()
    if not q:
        return "general_mr"

    # Spouse profession (before generic partner)
    if re.search(r"\b(profession|job|work|business|naukri|kaam|field|line)\b", q) and re.search(
        r"\b(spouse|partner|husband|wife|pati|patni|jeevan\s*sathi)\b", q
    ):
        return "spouse_profession"

    # Secret / hidden relationship
    if re.search(
        r"\b(secret|hidden|chhup|chhupa|affair|chakkar|private\s*rishta|gupt)\b", q
    ):
        return "secret_relationship"

    # One-sided / crush / proposal
    if re.search(
        r"\b(one\s*sided|ek\s*tarfa|ektarafa|crush|proposal|propose|"
        r"meri\s+taraf\s+se|us\s+ko\s+pasand)\b",
        q,
    ):
        return "one_sided_love"

    # Obsession / jealousy / possessive
    if re.search(
        r"\b(obsess|obsession|jealous|possessive|control|over\s*attach)\b", q
    ):
        return "obsession"

    # Bed / intimacy (before generic chemistry)
    if re.search(
        r"\b(bed|conjugal|sexual|sex\b|suhag\s*raat|private\s*life|"
        r"physical\s*compat)\b",
        q,
    ):
        return "bed_intimacy"

    # Self-worth / boundaries
    if re.search(
        r"\b(self\s*worth|boundar|respect|insecure|insecurity|value\s*myself)\b", q
    ):
        return "self_worth"

    # Emotional attachment / feelings (not loyalty/commitment)
    if re.search(
        r"\b(emotional|attachment|attach|feelings?|dil\s*lag|lagav|pyaar\s*gehra)\b", q
    ) and not re.search(r"\b(loyal\w*|commitment|commit|trust|vishwas)\b", q):
        return "emotional_attachment"

    # Loyalty / commitment / cheating / trust (before emotional attachment)
    if re.search(
        r"\b(cheat|cheating|dhokha|dhoka|betray|loyal\w*|faithful|trust|vishwas|"
        r"commitment|commit|nibha\w*|wafad\w*|vafad\w*|third\s+person)\b",
        q,
    ):
        return "loyalty_trust"

    # Patchup / reconciliation
    if re.search(
        r"\b(patch\s*up|patchup|reconcile|reconciliation|wapas|return|laut|maan\s+jayega)\b", q
    ):
        return "patchup"

    # Chemistry / attraction (non-bed)
    if re.search(r"\b(chemistry|attraction|spark|passion|romance|romantic)\b", q):
        return "chemistry"

    # Family approval
    if re.search(
        r"\b(family|parents?|ghar\s*wal\w*|gharwal\w*|approval|intercaste|inter\s*caste|religion|maanenge|manenge)\b",
        q,
    ):
        return "family_approval"

    # Manglik
    if re.search(r"\b(manglik|mangalik|mangal\s*dosh)\b", q):
        return "manglik"

    # Love vs arranged (direct comparison, marriage+arrange, Hinglish typos)
    has_love = bool(re.search(r"\b(love|pyaar|pyar|prem|romance)\b", q))
    has_arr = bool(re.search(r"\barrang", q))
    has_marriage_word = bool(
        re.search(r"\b(marriage|shaadi|shadi|shaddi|vivah|biyah|byah|rishta)\b", q)
    )
    if (has_love and has_arr) or re.search(r"\b(love\s*marriage|prem\s*vivah)\b", q):
        return "love_vs_arranged"
    if has_arr and (has_marriage_word or has_love):
        return "love_vs_arranged"
    if has_arr and re.search(r"\b(khud|apni|choice|pasand|pyar\w*)\b", q):
        return "love_vs_arranged"

    # Breakup / separation
    if re.search(r"\b(breakup|break\s*up|separation|divorce|talaq|door|dur|toot|tut)\b", q):
        return "breakup_risk"

    # Marriage quality / happiness (explicit general)
    if re.search(
        r"\b(shaadi\s*achhi|happy|khush|sukh|marriage\s*quality|compatible|"
        r"compatibility|match\s*making|rishta\s*achha|vivah\s*sukh)\b",
        q,
    ):
        return "general_mr"

    # Partner nature (after more specific buckets)
    if re.search(
        r"\b(partner|spouse|husband|wife|pati|patni|jeevan\s*sathi|"
        r"nature|kaisa|kaisi|kaise\s+honge)\b",
        q,
    ):
        return "partner_nature"

    return "general_mr"
