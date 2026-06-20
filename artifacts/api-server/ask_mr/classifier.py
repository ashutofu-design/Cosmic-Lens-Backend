from __future__ import annotations

import re


def classify_mr_archetype(question: str) -> str:
    """Return MR non-timing archetype id for routing."""
    q = (question or "").strip().lower()
    if not q:
        return "general_mr"

    # Spouse profession (partner's job field — not native career support)
    if re.search(r"\b(profession|job|work|business|naukri|kaam|field|line)\b", q) and re.search(
        r"\b(spouse|partner|husband|wife|pati|patni|jeevan\s*sathi)\b", q
    ):
        return "spouse_profession"

    # Spouse wealth / financial comfort (not native money topic)
    if re.search(
        r"\b(wealth|rich|affluent|dhan|paisa|money|prosper|samriddh|amir|comfortable)\b", q
    ) and re.search(r"\b(spouse|partner|husband|wife|pati|patni|jeevan\s*sathi)\b", q):
        return "spouse_wealth"

    # Multiple / parallel love pattern
    if re.search(
        r"\b(multiple\s*(love|relationship)|parallel\s*(love|relation)|do\s*rishte)\b", q
    ):
        return "secret_relationship"

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

    # Long-distance / door rehkar rishta
    if re.search(
        r"\b(long\s*distance|ldr|door\s*reh|dur\s*reh|alag\s*shahr|"
        r"different\s*city|dur\s*se\s*rishta)\b",
        q,
    ) and re.search(
        r"\b(relation|relationship|partner|marriage|pyaar|pyar|love|rishta|shaadi)\b", q
    ):
        return "long_distance"

    # Marriage quality / compatibility / strengths / growth (before emotional-only)
    if re.search(
        r"\b(shaadi\s*achhi|happy|khush|sukh|marriage\s*quality|compatible|"
        r"compatibility|match\s*making|rishta\s*achha|vivah\s*sukh|"
        r"strengths?|positive\s*changes?|major\s*challenges?|conflicts?|"
        r"kaam\s+karna\s+chahiye|gun\s*milan|36\s*gun)\b",
        q,
    ):
        return "general_mr"

    # Partner supports native career / life goals (not spouse profession axis)
    if re.search(
        r"\b(spouse|partner|husband|wife|pati|patni|jeevan\s*sathi|marriage\s*partner)\b",
        q,
    ) and re.search(
        r"\b(support|saath\s*deg[ei]|saath\s*dega)\b",
        q,
    ) and re.search(r"\b(career|goals?|sapne|dreams?|ambition|life\s*goals?|meri|mujhe|mere)\b", q):
        return "general_mr"

    # Loyalty / commitment / cheating / trust (before emotional attachment)
    if re.search(
        r"\b(cheat|cheating|dhokha|dhoka|betray|loyal\w*|faithful|trust|vishwas|"
        r"commitment|commit|nibha\w*|wafad\w*|vafad\w*|third\s+person)\b",
        q,
    ):
        return "loyalty_trust"

    # Emotional attachment / feelings (expressive vs reserved — not compatibility)
    if re.search(
        r"\b(emotional|attachment|attach|feelings?|dil\s*lag|lagav|pyaar\s*gehra)\b", q
    ) and not re.search(r"\b(compatible|compatibility)\b", q) and not re.search(
        r"\b(loyal\w*|commitment|commit|trust|vishwas)\b", q
    ):
        return "emotional_attachment"

    # Patchup / reconciliation / ex return
    if re.search(
        r"\b(patch\s*up|patchup|reconcile|reconciliation|wapas|return|laut|maan\s+jayega)\b", q
    ) or (
        re.search(r"\b(ex\b|purana\s*partner|former\s*partner|past\s*love)\b", q)
        and re.search(r"\b(wapas|return|laut|aayega|aayegi|patch)\b", q)
    ):
        return "patchup"

    # Chemistry / attraction (non-bed)
    if re.search(r"\b(chemistry|attraction|spark|passion|romance|romantic)\b", q):
        return "chemistry"

    # Spouse/partner family background (describe in-laws — not elders approving match)
    if re.search(
        r"\b(spouse|partner|husband|wife|pati|patni|jeevan\s*sathi)\b", q
    ) and re.search(
        r"\b(family\s*background|parivaar|parivar|khandaan|pariwar|"
        r"family\s*type|family\s*status|ghar\s*ki\s*background)\b",
        q,
    ):
        return "partner_nature"

    # Family approval (user's elders / intercaste — not spouse family profile)
    if re.search(
        r"\b(parents?|ghar\s*wal\w*|gharwal\w*|approval|intercaste|inter\s*caste|"
        r"religion|maanenge|manenge)\b",
        q,
    ) or (
        re.search(r"\bfamily\b", q)
        and not re.search(
            r"\b(spouse|partner|husband|wife|pati|patni|jeevan\s*sathi)\b", q
        )
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

    # Second marriage / remarriage (before breakup — divorce word may appear)
    if re.search(
        r"\b(second|dusri|doosri|2nd|twice|dubara|punah|remarri|do\s*bar)\b", q
    ) and re.search(r"\b(marriage|shaadi|shadi|vivah|vivahit|partner|husband|wife|rishta)\b", q):
        return "second_marriage"

    # Breakup / separation
    if re.search(r"\b(breakup|break\s*up|separation|divorce|talaq|door|dur|toot|tut)\b", q):
        return "breakup_risk"

    # Partner nature (after more specific buckets)
    if re.search(
        r"\b(partner|spouse|husband|wife|pati|patni|jeevan\s*sathi|"
        r"nature|kaisa|kaisi|kaise\s+honge|age\s*gap|umar)\b",
        q,
    ):
        return "partner_nature"

    return "general_mr"
