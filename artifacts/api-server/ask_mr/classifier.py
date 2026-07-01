from __future__ import annotations



import re



_SPOUSE = r"\b(spouse|partner|husband|wife|pati|patni|biwi|jeevan\s*sathi)\b"

_NATIVE = r"\b(meri|mera|mere|my|mujhe|main|i\s*am)\b"





def _has_spouse(q: str) -> bool:

    return bool(re.search(_SPOUSE, q))





def _user_attachment(q: str) -> bool:

    """User's own emotional style — not partner's."""

    return bool(re.search(_NATIVE, q)) and re.search(

        r"\b(attachment|attach|emotional\s*needs?|mera\s*attachment)\b", q

    )





def classify_mr_archetype(question: str) -> str:

    """Return MR non-timing archetype id for routing (priority order matters)."""

    q = (question or "").strip().lower()

    if not q:

        return "general_mr"



    # Devanagari routing (scope gate already passed via _HINDI_MR_RX)
    if re.search(r"[\u0900-\u097F]", q):
        if re.search(r"मांगलिक|मंगल\s*दोष", q):
            return "manglik"
        if re.search(r"प्रेम\s*विवाह|love\s*marriage|arranged", q, re.I):
            return "love_vs_arranged"
        if re.search(r"विश्वास|वफादार|धोख", q) and not re.search(r"आत्मविश्वास", q):
            return "loyalty_trust"
        if re.search(r"आत्मविश्वास|सीमा|boundary", q, re.I):
            return "self_worth"
        if re.search(r"आकर्षण|रोमांस|प्रेम\s*और", q):
            return "chemistry"
        if re.search(r"वापस|पुराना\s*रिश्त", q):
            return "patchup"
        if re.search(r"माता-पिता|इंटरकास्ट|राजी|मंजूर", q):
            return "family_approval"
        if re.search(r"पेशा|पेशे", q):
            return "spouse_profession"
        if re.search(r"अमीर|धन|संपन्न", q):
            return "spouse_wealth"
        if re.search(r"शक्ल|आंख|रूप|दिख", q):
            return "spouse_appearance"
        if re.search(r"बच्च|संस्कार", q):
            return "children_parenting"
        if re.search(r"soulmate|soul\s*mate|कर्म", q, re.I):
            return "karmic_marriage"
        if re.search(r"विदेश|यात्र|घर\s*का\s*माहौल|लक्जरी", q):
            return "lifestyle_marriage"
        if re.search(r"सच्चा\s*प्यार|डेटिंग", q):
            return "dating_courtship"
        if re.search(r"दूसरी\s*शादी", q):
            return "second_marriage"
        if re.search(r"लॉन्ग\s*डिस्टेंस|दूर", q):
            return "long_distance"
        if re.search(r"एकतरफा", q):
            return "one_sided_love"
        if re.search(r"गुप्त", q):
            return "secret_relationship"
        if re.search(r"अति\s*लगाव|ईर्ष|obsess", q, re.I):
            return "obsession"
        if re.search(r"भावनात्मक|जुड़ाव", q):
            return "emotional_attachment"
        if re.search(r"शारीरिक\s*अनुकूल", q):
            return "bed_intimacy"
        if re.search(r"तलाक|टूट", q):
            return "breakup_risk"
        if re.search(r"खुश|संवाद|स्थिर|विवाह", q):
            return "general_mr"
        if re.search(r"स्वभाव|व्यक्तित्व", q):
            return "partner_nature"



    # --- Love language / affection style (native or partner) ---
    if re.search(r"\b(love\s*style|love\s*language|affection\s*style)\b", q):
        return "partner_nature"

    if re.search(r"\b(love\s*language|care\s*dikhane|affection\s*style)\b", q):
        return "partner_nature"

    # --- Manglik ---

    if re.search(r"\b(manglik|mangalik|mangal\s*dosh)\b", q):

        return "manglik"



    # --- Spouse physical appearance (before partner_nature) ---

    if _has_spouse(q) and re.search(

        r"(?ix)\b("

        r"height|tall\b|lamba[iy]?|complexion|rang|face|chehra|eyes?|aankh\w*|hair|baal|"

        r"body\s*type|figure|dress|dressing|voice|awaaz|aura|attract\w*|beautiful|"

        r"handsome|good\s*looking|physical\s*appear|shakl|surat|look\b|dikh\w*"

        r")\b",

        q,

    ):

        return "spouse_appearance"



    # --- Spouse profession (expanded: doctor, IT, gov, business without word 'profession') ---

    if _has_spouse(q) and re.search(

        r"(?ix)\b("

        r"profession|job|work|business|naukri|kaam|field|line|career|"

        r"doctor|medical|engineer|it\b|software|government|govt|private|"

        r"teacher|education|finance|bank|creative|artist|leadership|manager"

        r")\b",

        q,

    ) and not re.search(r"\b(support|saath\s*deg)\b", q):

        return "spouse_profession"



    # --- Spouse wealth (expanded) ---

    if _has_spouse(q) and re.search(

        r"(?ix)\b("

        r"wealth|rich|affluent|dhan|paisa|money|prosper|samriddh|amir|comfortable|"

        r"middle\s*class|self\s*made|self-made|saving|spending|wealthy\s*family|"

        r"financial|finance|income|salary|paisa\s*wal"

        r")\b",

        q,

    ):

        return "spouse_wealth"



    # --- Children / parenting / family values ---

    try:
        from ask_children.children_registry import (  # type: ignore
            is_children_static_question,
            is_mr_spouse_children_question,
        )

        if is_children_static_question(q) and not is_mr_spouse_children_question(q):
            pass
        elif re.search(

        r"(?ix)\b("

        r"parenting|parent\s*style|bachon|bacchon|children|kids?|"

        r"family\s*values?|sanskaar|bachch"

        r")\b",

        q,

    ) and (

        _has_spouse(q)

        or re.search(r"\b(marriage|shaadi|after\s*marriage|partner)\b", q)

        or re.search(r"\b(parenting|bachon|children|family\s*values)\b", q)

        ):

            return "children_parenting"
    except Exception:
        if re.search(

            r"(?ix)\b("

            r"parenting|parent\s*style|bachon|bacchon|children|kids?|"

            r"family\s*values?|sanskaar|bachch"

            r")\b",

            q,

        ) and (

            _has_spouse(q)

            or re.search(r"\b(marriage|shaadi|after\s*marriage|partner)\b", q)

            or re.search(r"\b(parenting|bachon|children|family\s*values)\b", q)

        ):

            return "children_parenting"



    # --- Karmic / soulmate / past life ---

    if re.search(

        r"(?ix)\b("

        r"soul\s*mate|soulmate|twin\s*flame|karmic|karma\s*debt|past\s*life|"

        r"pichle\s*janam|purva\s*janm|spiritual\s*growth.*marriage|"

        r"marriage.*spiritual\s*growth|aadhyatmik.*shaadi"

        r")\b",

        q,

    ):

        return "karmic_marriage"



    # --- Lifestyle after marriage ---

    if re.search(

        r"(?ix)\b("

        r"luxury|luxurious|travel|ghumna|social\s*life|home\s*environment|"

        r"ghar\s*ka\s*mahaul|abroad\s*settle|settle\s*abroad|foreign\s*settle|"

        r"lifestyle\s*after\s*marriage|shaadi\s*ke\s*baad.*(travel|luxury|ghar)"

        r")\b",

        q,

    ):

        return "lifestyle_marriage"



    if re.search(r"\b(red\s*flags?|green\s*flags?)\b", q):
        return "dating_courtship"

    # --- Patchup (before dating / ex-wapas) ---
    if re.search(
        r"\b(patch\s*up|patchup|reconcile|reconciliation|wapas|return|laut|maan\s+jayega)\b",
        q,
    ) or (
        re.search(r"\b(ex\b|purana\s*partner|former\s*partner|past\s*love)\b", q)
        and re.search(r"\b(wapas|return|laut|aayega|aayegi|patch|sakta|sakti)\b", q)
    ):
        return "patchup"

    # --- One-sided (before generic dating/pyaar+hoga) ---
    if re.search(
        r"\b(one\s*sided|ek\s*tarfa|ektarafa|crush|proposal|propose|"
        r"meri\s+taraf\s+se|us\s+ko\s+pasand|tarfa\s*pyaar|pyaar\s*tarfa)\b",
        q,
    ) or (
        re.search(r"\baccept\b", q)
        and re.search(r"\b(tarfa|crush|one\s*sided|ek\s*tarfa|pyaar|pyar)\b", q)
    ):
        return "one_sided_love"

    # --- Loyalty / trust / betrayal (before dating — love+milega must not steal dhoka Qs) ---
    if re.search(
        r"\b(cheat|cheating|dhokha|dhoka|betray|loyal\w*|faithful|trust|vishwas|"
        r"commitment|commit|nibha\w*|wafad\w*|vafad\w*|third\s+person|interference|beimaan)\b",
        q,
    ):
        return "loyalty_trust"

    # --- Dating / courtship / true love / flags ---

    if re.search(

        r"(?ix)\b("

        r"true\s*love|sachcha\s*pyaar|friend\s*to\s*lover|dost\s*se\s*pyaar|friend\s*se\s*lover|"

        r"dost\s*se\s*love|lover\s*ban|online\s*relation|dating|flirt\w*|first\s*impression|"

        r"red\s*flags?|green\s*flags?|attraction\s*pattern|dating\s*success|courtship|date\s*pe|"

        r"flirting\s*style"

        r")\b",

        q,

    ) or (
        re.search(r"\b(pyaar|pyar|love|rishta)\b", q)
        and re.search(r"\b(milega|milegi|hoga|hogi|sachcha|true)\b", q)
        and not re.search(r"\barrang", q)
        and not re.search(r"\b(patch\s*up|patchup|wapas|ex\b|ek\s*tarfa|tarfa\s*pyaar|one\s*sided)\b", q)
        and not re.search(
            r"(?ix)\b(dhokha|dhoka|betray|cheat|cheating|loyal|trust|vishwas|faithful|beimaan)\b",
            q,
        )
        and not _has_spouse(q)
    ):

        return "dating_courtship"



    # --- In-laws / spouse family-wale (8H) ---

    if not re.search(

        r"\b(?:mer[ei]|mere|my|parents?|ma\s*baap|papa|mummy)\b.{0,30}\b"

        r"(?:manenge|manzoor|accept|swikar|approval|manna|allow)\b",

        q,

    ) and (

        re.search(

            r"\b(?:wife|husband|spouse|partner|pati|patni|biwi)\b"

            r".{0,40}\b(?:"

            r"family\s*wal\w*|ghar\s*wal\w*|ghar\s*ke\s*log|in[\s-]?laws?|"

            r"saas|sasur|sasural|sasuraal|rishtedaar|"

            r"(?:parivaar|parivar|pariwar|family|relatives)\s*(?:kaise|kya|kaisa|kaisi)\b"

            r")\b",

            q,

        )

        or re.search(

            r"\b(?:family\s*wal\w*|ghar\s*wal\w*)\b"

            r".{0,30}\b(?:wife|husband|spouse|partner|pati|patni|biwi)\b",

            q,

        )

        or re.search(r"\b(?:saas|sasur|sasural|mother[\s-]?in[\s-]?law|father[\s-]?in[\s-]?law)\b", q)

        or re.search(r"\b(?:joint\s*family|nuclear\s*family|sasural\s*interference)\b", q)

    ):

        return "partner_nature"



    # --- Multiple / secret / affair ---

    if re.search(

        r"(?ix)\b("

        r"multiple\s*(?:love|relationships?|relations?|rishte)|parallel\s*(?:love|relations?|rishte)|"

        r"do\s*rishte|secret|hidden|chhup|chhupa|affair|chakkar|private\s*rishta|gupt"

        r")\b",

        q,

    ):

        return "secret_relationship"



    # --- One-sided / crush ---

    if re.search(

        r"\b(one\s*sided|ek\s*tarfa|ektarafa|crush|proposal|propose|"

        r"meri\s+taraf\s+se|us\s+ko\s+pasand)\b",

        q,

    ):

        return "one_sided_love"



    # --- Obsession / jealousy ---

    if re.search(r"\b(obsess|obsession|jealous|possessive|control|over\s*attach)\b", q):

        return "obsession"



    # --- Bed / intimacy ---

    if re.search(

        r"\b(bed|conjugal|sexual|sex\b|suhag\s*raat|private\s*life|physical\s*compat\w*|bedroom)\b", q

    ):

        return "bed_intimacy"



    # --- Self-worth ---

    if re.search(r"\b(self\s*worth|boundar\w*|insecure|insecurity|value\s*myself)\b", q):

        return "self_worth"



    # --- Long-distance + online relationship ---

    if re.search(

        r"(?ix)\b("

        r"long\s*distance|ldr|alag\s*shahr|different\s*city|dur\s*se\s*rishta|"

        r"online\s*relationship|online\s*rishta|virtual\s*love|internet\s*love"

        r")\b",

        q,

    ) or (

        re.search(r"(?:door\s*reh\w*|dur\s*reh\w*)", q)

        and re.search(r"\b(relation|relationship|partner|marriage|pyaar|pyar|love|rishta|shaadi)\b", q)

    ):

        return "long_distance"



    # --- Breakup / toxic / divorce / separation ---

    if re.search(

        r"(?ix)\b("

        r"breakup|break\s*up|separation|divorce|talaq|toot\w*|tut\w*|rishta\s*toot|"

        r"toxic|manipulat|ego\s*clash"

        r")\b",

        q,

    ):

        return "breakup_risk"



    # --- Second marriage ---

    if re.search(

        r"\b(second|dusri|doosri|2nd|twice|dubara|punah|remarri|do\s*bar)\b", q

    ) and re.search(r"\b(marriage|shaadi|shadi|vivah|vivahit|partner|husband|wife|rishta)\b", q):

        return "second_marriage"



    # --- Love vs arranged ---

    has_love = bool(re.search(r"\b(love|pyaar|pyar|prem|romance)\b", q))

    has_arr = bool(re.search(r"\barrang", q))

    has_marriage_word = bool(re.search(r"\b(marriage|shaadi|shadi|vivah|biyah|byah|rishta)\b", q))

    if (has_love and has_arr) or re.search(r"\b(love\s*marriage|prem\s*vivah)\b", q):

        return "love_vs_arranged"

    if has_arr and (has_marriage_word or has_love):

        return "love_vs_arranged"

    if has_arr and re.search(r"\b(khud|apni|choice|pasand|pyar\w*)\b", q):

        return "love_vs_arranged"

    if re.search(r"\b(khud|apni)\s*pasand\b", q) and re.search(r"\b(ghar\s*wal\w*|parents?|family)\b", q):

        return "love_vs_arranged"

    if re.search(r"\b(ghar\s*walon|ghar\s*wal\w*)\b", q) and re.search(r"\bpasand\b", q):

        return "love_vs_arranged"

    if re.search(r"\b(ghar\s*wal\w*|parents?)\s*choose\b", q) and re.search(

        r"\b(pasand|khud|apni|shaadi|shadi|marriage|vivah)\b", q

    ):

        return "love_vs_arranged"

    if re.search(r"\blove[\s-]?cum[\s-]?arrang", q):

        return "love_vs_arranged"



    # --- Family approval / inter-caste / court marriage ---

    if re.search(

        r"(?ix)\b("

        r"parents?|ghar\s*wal\w*|gharwal\w*|approval|inter[\s-]?caste|intercaste|"

        r"inter[\s-]?religion|interreligion|maanenge|manenge|court\s*marriage|"

        r"family\s*involve|ghar\s*walon\s*ka\s*role"

        r")\b",

        q,

    ) or (

        re.search(r"\bfamily\b", q)

        and not _has_spouse(q)

        and not re.search(r"\b(values?|sanskaar|parenting)\b", q)

    ):

        return "family_approval"



    # --- Marriage quality / compatibility / emotional compat / communication ---

    if re.search(

        r"(?ix)\b("

        r"shaadi\s*achhi|happy|khush|sukh|marriage\s*quality|compatible|compatibility|"

        r"match\s*making|rishta\s*achha|vivah\s*sukh|strengths?|positive\s*changes?|"

        r"major\s*challenges?|conflicts?|kaam\s+karna\s+chahiye|gun\s*milan|36\s*gun|"

        r"emotional\s*compat|samajh\s*payega|samajh\s*payegi|communication|teamwork|"

        r"stable|stability|growth|mutual\s*support|conflict\s*style|emotional\s*maturity|"

        r"understanding|shaadi\s*ke\s*baad.*(khush|sukh|achh)"

        r")\b",

        q,

    ) and not re.search(
        r"\b(bedroom|bed\b|conjugal|private\s*life|physical\s*compat|intimacy|suhag)\b", q
    ):

        return "general_mr"



    # --- Partner supports native career ---

    if _has_spouse(q) and re.search(r"\b(support|saath\s*deg[ei]|saath\s*dega)\b", q) and re.search(

        r"\b(career|goals?|sapne|dreams?|ambition|life\s*goals?|meri|mujhe|mere)\b", q

    ):

        return "general_mr"



    # --- Partner fit / mental match (before chemistry; blocks health stealing "mental") ---
    if re.search(r"\b(partner|spouse|pati|patni|husband|wife)\b", q) and re.search(
        r"(?ix)\b(suit|match|compatible|thinking|soch|mental|nature|swabhav|kaisa|kaisi|kaise|tarah)\b",
        q,
    ):
        return "partner_nature"

    # --- Partner personality (before chemistry / emotional_attachment) ---

    if _has_spouse(q) and re.search(

        r"(?ix)\b("

        r"nature|kaisa|kaisi|kaise\s+honge|express|reserved|emotion|feeling|"

        r"gussa|anger|temper|dominant|cooperative|romantic|caring|humor|humour|"

        r"honest|introvert|extrovert|spiritual|practical|ambitious|respect|izzat|"

        r"love\s*language|affection\s*style|background|culture|foreign|videsh|"

        r"family\s*background|khandaan|manipulat"

        r")\b",

        q,

    ):

        return "partner_nature"



    # --- Chemistry (native solo attraction) — not couple "hum dono ke beech" ---
    if re.search(r"\b(chemistry|attraction|spark|passion|romance|romantic)\b", q):
        try:
            from ask_intent_fidelity import is_dyadic_couple_question

            if is_dyadic_couple_question(q):
                return "general_mr"
        except Exception:
            pass
        if not re.search(
            r"(?ix)\b(true\s*love|sach+a\s*pyaar|sach+a\s*pyar|milne\s+ka\s+yog|yog\s+likha)\b",
            q,
        ):
            return "chemistry"



    # --- Reciprocal love / partner loves me back (before emotional_attachment) ---
    if re.search(
        r"(?ix)\b("
        r"kya\s+wo\s+bhi|does\s+(she|he|they)\s+love|love\s+me\s+back|"
        r"utna\s+hi\s+pyaar|jitna\s+main|reciproc|mutual\s+love|"
        r"wo\s+bhi\s+.*\b(pyaar|pyar|prem|love)\b"
        r")\b",
        q,
    ) and re.search(r"(?ix)\b(pyaar|pyar|prem|love|dil)\b", q):
        return "one_sided_love"

    # --- User emotional attachment only ---

    if re.search(r"\b(emotional|attachment|attach|feelings?|dil\s*lag|lagav|pyaar\s*gehra)\b", q) and not re.search(

        r"\b(compatible|compatibility)\b", q

    ) and not re.search(r"\b(loyal\w*|commitment|commit|trust|vishwas)\b", q) and (

        _user_attachment(q) or not _has_spouse(q)

    ):

        return "emotional_attachment"



    # --- Patchup ---

    if re.search(

        r"\b(patch\s*up|patchup|reconcile|reconciliation|wapas|return|laut|maan\s+jayega)\b", q

    ) or (

        re.search(r"\b(ex\b|purana\s*partner|former\s*partner|past\s*love)\b", q)

        and re.search(r"\b(wapas|return|laut|aayega|aayegi|patch)\b", q)

    ):

        return "patchup"



    # --- Foreign spouse (without lifestyle settle) ---

    if re.search(r"\b(foreign\s*spouse|videshi\s*partner|alag\s*culture)\b", q):

        return "partner_nature"



    # --- Partner nature catch-all ---

    if re.search(

        r"\b(partner|spouse|husband|wife|pati|patni|jeevan\s*sathi|age\s*gap|umar)\b", q

    ):

        return "partner_nature"



    return "general_mr"

