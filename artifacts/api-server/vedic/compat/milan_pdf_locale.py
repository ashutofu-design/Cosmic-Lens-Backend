"""Milan PDF UI strings — Roman Hindi (``hn`` lane) vs English default.

Only ``lang == "hn"`` switches these; ``en`` / ``hi`` keep English chrome for now
(``hi`` uses Devanagari body elsewhere). Brand name ``Cosmic Lens`` stays Latin
as a proper noun; all other PDF chrome for ``hn`` is Roman Hindi."""

from __future__ import annotations


def pdf_ui_hn(lang: str | None) -> bool:
    return (lang or "en").strip().lower() == "hn"


def tx(lang: str | None, en: str, hn: str) -> str:
    return hn if pdf_ui_hn(lang) else en


def chapter_prefix(lang: str | None) -> str:
    return tx(lang, "CHAPTER", "ADHYAY")


def page_footer_center(lang: str | None) -> str:
    return tx(lang, "Cosmic Lens  ·  Kundli Milan", "Cosmic Lens · Kundli Milan")


def page_footer_center_pro(lang: str | None) -> str:
    return tx(
        lang,
        "Cosmic Lens  ·  Cosmic Relationship Blueprint Pro",
        "Cosmic Lens · Cosmic Rishta Blueprint Pro",
    )


def page_footer_page_word(lang: str | None) -> str:
    return tx(lang, "Page", "Prishth")


# ── Cover ────────────────────────────────────────────────────────────────────
def cover_title(lang: str | None) -> str:
    return tx(lang, "Cosmic Relationship Blueprint", "Cosmic Rishta Blueprint")


def cover_subtitle(lang: str | None) -> str:
    return tx(
        lang,
        "A Vedic Relationship Intelligence Report",
        "Ek Vedic rishta-buddhi report — grah-ganit + practical marriage read",
    )


def cover_prepared_line(lang: str | None) -> str:
    return tx(lang, "Prepared by", "Tayyaar kiya")


def cover_powered_line(lang: str | None) -> str:
    return tx(
        lang,
        "Powered by Advanced Cosmic Intelligence Engine",
        "Advanced Cosmic Intelligence engine se powered",
    )


def cover_generated_prefix(lang: str | None) -> str:
    return tx(lang, "Generated", "Banane ki taarikh")


# ── Snapshot page ─────────────────────────────────────────────────────────────
def snap_eyebrow(lang: str | None) -> str:
    return tx(lang, "SNAPSHOT", "EK JHALAK")


def snap_title(lang: str | None) -> str:
    return tx(lang, "Relationship Snapshot", "Rishte ki ek tasveer")


def snap_subtitle(lang: str | None) -> str:
    return tx(lang, "How this bond actually feels in real life.", "Yeh rishta rozmarra me kaise feel hota hai — seedhi baat.")


def snap_tag_emotional_pull(lang: str | None) -> str:
    return tx(lang, "Emotional Pull", "Emotional kheench")


def snap_tag_marriage_potential(lang: str | None) -> str:
    return tx(lang, "Marriage Potential", "Shaadi potential")


def snap_tag_long_term(lang: str | None) -> str:
    return tx(lang, "Long-term Stability", "Lamba arsa stability")


def snap_ashtakoot_row_label(lang: str | None) -> str:
    return tx(lang, "ASHTAKOOT", "ASHTAKOOT")


def snap_pair_strength_title(lang: str | None) -> str:
    return tx(lang, "What strengthens this bond", "Is rishte ko mazboot kya banata hai")


def snap_pair_challenge_title(lang: str | None) -> str:
    return tx(lang, "Main long-term challenge", "Sabse bada lamba-choda challenge")


def partner_default(lang: str | None, which: int) -> str:
    if pdf_ui_hn(lang):
        return "Pehla partner" if which == 1 else "Doosra partner"
    return "Partner 1" if which == 1 else "Partner 2"


# Snapshot pill titles (display only — internal keys stay English in code)
def snap_pill_title(lang: str | None, internal: str) -> str:
    m = {
        "Deep Attachment": "Gehra lagav",
        "Steady Affection": "Seedha-saadha pyaar",
        "Quiet Pull": "Dheemi kheench",
        "Tone Clashes First": "Pehle tone takraate hain",
        "Delayed Stability": "Der se stability",
        "Steady Surface Weeks": "Upar se shaant hafte",
        "Uneven Rhythm": "Barabar na rhythm",
    }
    if pdf_ui_hn(lang):
        return m.get(internal, internal)
    return internal


# ── Pro chapter chrome (eyebrow / title / subtitle per slot) ────────────────
def pro_chapter_rows(lang: str | None) -> list[tuple[str, str, str, str]]:
    """Returns list of (internal_key, eyebrow, title, subtitle)."""
    if not pdf_ui_hn(lang):
        return [
            ("emotional_compatibility", "EMOTIONAL COMPATIBILITY",
             "Emotional Compatibility",
             "Mood, pace, and who feels what first — observed, not fixed."),
            ("trust_loyalty", "TRUST & LOYALTY", "Trust & Loyalty",
             "Where loyalty shows up in ordinary weeks — and where it thins."),
            ("communication_conflict", "COMMUNICATION & CONFLICT",
             "Communication & Conflict",
             "How fights start, go cold, and restart — pattern, not homework."),
            ("marriage_stability", "MARRIAGE STABILITY", "Marriage Stability",
             "What stiffens or softens across years — not a guarantee line."),
            ("physical_chemistry", "PHYSICAL + EMOTIONAL CHEMISTRY",
             "Physical + Emotional Chemistry",
             "Pull, awkwardness, intimacy timing — lived texture, not scoring."),
            ("family_practical", "FAMILY + PRACTICAL LIFE", "Family + Practical Life",
             "Money, in-laws, chores — who carries which invisible load."),
            ("future_direction", "LONG-TERM FUTURE DIRECTION", "Long-Term Future Direction",
             "Where momentum drifts if direction stays unnamed."),
        ]
    return [
        ("emotional_compatibility", "BHAVNATMAK MILAAP", "Bhavnatmak milaap",
         "Mood, raftaar, aur pehle kiska kya feel hota hai — fix nahi, gaur se padhna."),
        ("trust_loyalty", "VISHWAS AUR WAFADAARI", "Vishwas aur wafadaari",
         "Aam hafton me vishwas kahan dikhta hai — aur kahan patla pad sakta hai."),
        ("communication_conflict", "BAAT-CHEET AUR TAKRAR", "Baat-cheet aur takrar",
         "Ladai kaise shuru, thandi, phir dubara — pattern, homework nahi."),
        ("marriage_stability", "SHAADI KI STABILITY", "Shaadi ki stability",
         "Saalon me kya tight, kya narm — guarantee line nahi."),
        ("physical_chemistry", "SHAREERIK + BHAVNATMAK CHEMISTRY",
         "Shareerik + bhavnatmak chemistry",
         "Kheench, awkwardness, nazdeeki ka timing — real texture, score nahi."),
        ("family_practical", "PARIVAAR + PRACTICAL ZINDAGI", "Parivaar + practical zindagi",
         "Paise, sass-sasur, ghar ka bojh — kaun zyada uthata hai."),
        ("future_direction", "LAMBE SAMAY KI DIRECTION", "Lambe samay ki direction",
         "Jab direction naam se tie nahi, momentum kidhar drift karta hai."),
    ]


def basic_chapter_rows(lang: str | None) -> list[tuple[str, str, str, str]]:
    """Six deep-schema sections for non-Pro Milan PDF (``render_milan_pdf``)."""
    if not pdf_ui_hn(lang):
        return [
            ("emotional_alignment", "EMOTIONAL ALIGNMENT", "Emotional Alignment",
             "How both of you feel, express, and process love."),
            ("trust_loyalty", "TRUST & LOYALTY", "Trust & Loyalty",
             "What strengthens trust — and what quietly tests it."),
            ("conflict_patterns", "CONFLICT PATTERNS", "Conflict Patterns",
             "How arguments begin, escalate, and resolve between you."),
            ("commitment_strength", "COMMITMENT STRENGTH", "Commitment Strength",
             "Who commits faster, who hesitates, and why."),
            ("marriage_stability", "MARRIAGE STABILITY", "Marriage Stability",
             "Long-term potential measured with realism, not absolutes."),
            ("future_direction", "FUTURE DIRECTION", "Future Direction",
             "Where this relationship is heading over the next 2–3 years."),
        ]
    return [
        ("emotional_alignment", "BHAVNATMAK MILAAP", "Bhavnatmak milaap",
         "Pyaar feel, express, process — dono ka tareeka."),
        ("trust_loyalty", "VISHWAS AUR WAFADAARI", "Vishwas aur wafadaari",
         "Vishwas kahan mazboot, kahan chup-chap test hota hai."),
        ("conflict_patterns", "TAKRAR KE PATTERN", "Takrar ke pattern",
         "Ladai kaise shuru, badhe, aur suljhe — tum dono ke beech."),
        ("commitment_strength", "COMMITMENT KI TAAKAT", "Commitment ki taakat",
         "Kaun pehle commit, kaun hesitate — aur kyun."),
        ("marriage_stability", "SHAADI KI STABILITY", "Shaadi ki stability",
         "Lamba arsa — realisme ke saath, guarantee line nahi."),
        ("future_direction", "AANE WALE 2–3 SAAL", "Aane wale 2–3 saal",
         "Yeh rishta kidhar ja raha hai — agle 2–3 saal ki direction."),
    ]


def basic_placeholder_section(lang: str | None) -> str:
    return tx(
        lang,
        "Detailed analysis for this section was not available for this "
        "chart. The other sections of this report still cover the core "
        "Vedic compatibility findings between both partners.",
        "Is chart ke liye is hisse ka detail analysis uplabdh nahi tha. "
        "Report ke baaki hisse phir bhi dono partners ke beech core Vedic milaap dikhate hain.",
    )


def basic_bond_special_subtitle(lang: str | None) -> str:
    return tx(
        lang,
        "The quiet strengths most couples never realise they have.",
        "Woh chup-chap taakat jo zyada jode realise hi nahi karte.",
    )


def basic_damage_eyebrow(lang: str | None) -> str:
    return tx(
        lang,
        "WHAT CAN QUIETLY DAMAGE THIS RELATIONSHIP",
        "CHUP-CHAAP IS RISHTE KO KYA NUKSAN PAHUNCHA SAKTA HAI",
    )


def basic_practical_eyebrow(lang: str | None) -> str:
    return tx(lang, "PRACTICAL LIFE TOGETHER", "SAATH PRACTICAL ZINDAGI")


def basic_practical_title(lang: str | None) -> str:
    return tx(lang, "Practical Life Together", "Saath practical zindagi")


def basic_practical_subtitle(lang: str | None) -> str:
    return tx(
        lang,
        "Money, family pressure, and lifestyle compatibility — in real life.",
        "Paise, parivaar ka dabav, lifestyle — asli zindagi me.",
    )


def basic_final_outlook_eyebrow(lang: str | None) -> str:
    return tx(lang, "FINAL RELATIONSHIP OUTLOOK", "AKHIRI RISHTA OUTLOOK")


def basic_final_outlook_title(lang: str | None) -> str:
    return tx(lang, "Final Relationship Outlook", "Akhiri rishta outlook")


def basic_final_outlook_subtitle(lang: str | None) -> str:
    return tx(
        lang,
        "A measured, mature reading of where this bond stands.",
        "Samjhdari se, seedha — yeh rishta ab kahan khada hai.",
    )


# ── Hidden truth & promise strip ────────────────────────────────────────────
def hidden_eyebrow(lang: str | None) -> str:
    return tx(lang, "WHAT'S HIDDEN UNDERNEATH", "NEECHE KYA CHHUPA HAI")


def hidden_title(lang: str | None) -> str:
    return tx(lang, "What's Hidden Underneath", "Neeche kya chhupa hai")


def hidden_subtitle(lang: str | None) -> str:
    return tx(
        lang,
        "The deeper Vedic+KP signature most charts miss.",
        "Gehri Vedic+KP signature jo zyada tar charts miss kar dete hain.",
    )


def hidden_promise_label(lang: str | None) -> str:
    return tx(lang, "Marriage promise reading →", "Shaadi-waada padhna →")


def hidden_promise_tail(lang: str | None, p1: str, p2: str) -> str:
    if pdf_ui_hn(lang):
        return (
            f" — {p1} aur {p2} dono ke liye, dono kundliyon ka gehra marriage signal "
            f"ek saath padha gaya."
        )
    return (
        f" — for {p1} & {p2}, "
        f"the deeper marriage signal in both charts is read together."
    )


# ── Chart / grounding micro-labels ───────────────────────────────────────────
def chart_insight_arrow(lang: str | None) -> str:
    return tx(lang, "Chart insight →", "Kundli sanket →")


def grounding_why_title(lang: str | None) -> str:
    return tx(lang, "Why we say this →", "Aisa kyun kehte hain →")


def grounding_obs_title(lang: str | None) -> str:
    return tx(lang, "Observational notes →", "Nireekshan notes →")


# ── Special / damage / practical / koot / blueprint / verdict chrome ────────
def special_eyebrow(lang: str | None) -> str:
    return tx(lang, "WHAT MAKES THIS BOND SPECIAL", "IS RISHTE KO KHAAS KYA BANATA HAI")


def special_title(lang: str | None) -> str:
    return tx(lang, "What Makes This Bond Special", "Is rishte ko khaas kya banata hai")


def special_subtitle(lang: str | None) -> str:
    return tx(
        lang,
        "Patterns that repeat without being announced — not praise lines.",
        "Jo pattern chup-chap repeat hote hain — sirf taarif ki linein nahi.",
    )


def damage_eyebrow(lang: str | None) -> str:
    return tx(lang, "WHAT CAN QUIETLY DAMAGE THIS BOND", "CHUP-CHAAP IS RISHTE KO KYA KHARAAB KAR SAKTA HAI")


def damage_title(lang: str | None) -> str:
    return tx(lang, "What Can Quietly Damage This Bond", "Chup-chap is rishte ko kya nuksan pahuncha sakta hai")


def damage_subtitle(lang: str | None) -> str:
    return tx(
        lang,
        "Where distance accrues in ordinary weeks — rarely in one fight.",
        "Faasla aam hafton me dheere-dheere badhta hai — ek ladai se kam.",
    )


def practical_eyebrow(lang: str | None) -> str:
    return tx(lang, "PRACTICAL MARRIED LIFE", "PRACTICAL SHAADI-WALI ZINDAGI")


def practical_title(lang: str | None) -> str:
    return tx(lang, "Practical Married Life", "Practical shaadi-wali zindagi")


def practical_subtitle(lang: str | None) -> str:
    return tx(
        lang,
        "Money, family pressure, lifestyle — what daily life will actually feel like.",
        "Paise, parivaar ka dabav, lifestyle — rozmarra me asliyat me kaisa feel hoga.",
    )


def practical_empty_block(lang: str | None) -> str:
    return tx(
        lang,
        "Practical detail was not generated for this report.",
        "Is report ke liye practical detail generate nahi hui.",
    )


def consultation_empty(lang: str | None) -> str:
    return tx(
        lang,
        "Consultation detail was not generated for this section.",
        "Is hisse ke liye consultation detail generate nahi hui.",
    )


def koot_table_header_koot(lang: str | None) -> str:
    return tx(lang, "KOOT", "KOOT")


def koot_table_header_score(lang: str | None) -> str:
    return tx(lang, "SCORE", "ANK")


def koot_table_header_meaning(lang: str | None) -> str:
    return tx(lang, "WHAT IT MEANS", "MATLAB KYA")


def koot_meaning_fallback_strength(lang: str | None) -> str:
    return tx(lang, "supportive area", "saath dene wala zone")


def koot_meaning_fallback_mid(lang: str | None) -> str:
    return tx(lang, "needs gentle attention", "halka dhyan chahiye")


def koot_meaning_fallback_weak(lang: str | None) -> str:
    return tx(lang, "weakest area — needs care", "sabse kamzor zone — dhyan zaroori")


def koot_score_note_dosha(lang: str | None) -> str:
    return tx(lang, "dosha", "dosh")


def koot_score_note_low(lang: str | None) -> str:
    return tx(lang, "low score", "kam ankh")


def koot_label_this(lang: str | None) -> str:
    return tx(lang, "This koot", "Yeh koot")


def attraction_eyebrow(lang: str | None) -> str:
    return tx(lang, "WHAT DRAWS YOU · WHAT TESTS YOU", "KYA KHEENCHTA HAI · KYA TEST KARTA HAI")


def blueprint_eyebrow(lang: str | None) -> str:
    return tx(lang, "MARRIAGE BLUEPRINT", "SHAADI KA BLUEPRINT")


def verdict_eyebrow(lang: str | None) -> str:
    return tx(lang, "FINAL VERDICT", "AKHIRI FAISLA")


def weak_spots_hdr(lang: str | None) -> str:
    return tx(lang, "WEAK SPOTS", "KAMZOR JAGAH")


def practical_strip_hdr(lang: str | None) -> str:
    return tx(lang, "PRACTICAL", "PRACTICAL")


def charts_eyebrow(lang: str | None) -> str:
    return tx(lang, "CHARTS", "KUNDLIYAAN")


def charts_title(lang: str | None) -> str:
    return tx(lang, "Rāśi & Navāmśa", "Rashi aur Navamsa")


def charts_subtitle(lang: str | None) -> str:
    return tx(
        lang,
        "North Indian layout — houses fixed from lagna; graha abbreviations as on a handwritten kundli.",
        "North Indian layout — lagna se ghar fix; graha chhote naam jaise haath-se likhi kundli.",
    )


def charts_legend_note(lang: str | None) -> str:
    return tx(
        lang,
        "<b>H1</b> = lagna (marked <b>Lg</b>). Graha: Su Mo Ma Me Ju Ve Sa Ra Ke.",
        "<b>H1</b> = lagna (<b>Lg</b> se nishanit). Graha: Su Mo Ma Me Ju Ve Sa Ra Ke.",
    )


def pro_placeholder_grounding_bridge(lang: str | None) -> str:
    return tx(
        lang,
        "Placeholder bridge — medium-band chapter read when premium JSON is partial.",
        "Beech ka bridge — jab premium data adhura ho to medium-band adhyay read.",
    )


def damage_engine_fallback_bullet(lang: str | None) -> str:
    return tx(
        lang,
        "No single classical headline stacks here — still, low koots "
        "are usually where the same argument borrows its shape each month.",
        "Koi ek classical headline yahan stack nahi hoti — phir bhi kam koots "
        "par aksar wahi jhagda har mahine apna shape udhaar leta hai.",
    )


def score_breakdown_title(lang: str | None) -> str:
    return tx(lang, "How Your Guna Milan Score Was Built", "Guna Milan Score — Kaise Bana?")


def score_breakdown_subtitle(lang: str | None) -> str:
    return tx(
        lang,
        "Each koot adds gunas — this total is not random",
        "Har koot gunas jodta hai — yeh total random nahi hai",
    )


def chart_snapshot_title(lang: str | None) -> str:
    return tx(lang, "Chart Facts (Both Partners)", "Chart Facts (Aap Dono)")


def chart_snapshot_subtitle(lang: str | None) -> str:
    return tx(
        lang,
        "Degrees, houses, dasha, D9 — basis for chapters below",
        "Degrees, houses, dasha, D9 — neeche ke chapters ka basis",
    )


def timing_note_title(lang: str | None) -> str:
    return tx(lang, "Reading Note", "Padhne Ka Note")


def method_note_title(lang: str | None) -> str:
    return tx(lang, "How This Report Was Prepared", "Yeh Report Kaise Taiyar Hui")


def method_note_body(lang: str | None) -> str:
    return tx(
        lang,
        "This Kundli Milan Pro report is prepared by Cosmic Lens from both birth "
        "charts using Swiss Ephemeris (Lahiri), Ashtakoot guna milan (36-point grid), "
        "Navamsa marriage factors, 7th-lord synastry, and KP marriage-promise analysis. "
        "Chapter scores and narrative reflect advanced, chart-based Vedic rules — not random text. "
        "This is guidance for marriage understanding; it is not a substitute for medical, legal, "
        "therapeutic, or in-person counselling. Your choices and efforts always matter.",
        "Yeh Kundli Milan Pro report Cosmic Lens dwara dono janam charts par banayi gayi hai — "
        "Swiss Ephemeris (Lahiri), Ashtakoot guna milan (36 gun), Navamsa marriage factors, "
        "7th-lord synastry, aur KP marriage-promise analysis ke basis par. "
        "Chapter scores aur narrative advanced chart-based Vedic rules se aate hain. "
        "Yeh shaadi samajhne ke liye hai — doctor, lawyer, therapist ya face-to-face pandit "
        "consultation ki jagah nahi. Aapke choices aur mehnat hamesha matter karti hai.",
    )


def pro_chapter_placeholder(lang: str | None) -> str:
    return tx(
        lang,
        "This chapter draws on your combined chart signals for this marriage theme — "
        "the reading reflects placement logic measured for your bond.",
        "Yeh chapter is rishte ke combined chart signals par based hai — "
        "reading measured placement logic ko reflect karti hai.",
    )


def score_ledger_fallback(lang: str | None, total: int, mx: int) -> str:
    return tx(
        lang,
        f"Guna milan total: {total}/{mx}. A koot-by-koot breakdown appears when full koot data is present.",
        f"Guna milan total: {total}/{mx}. Koot-by-koot breakdown tab dikhega jab poora koot data ho.",
    )


def chart_snapshot_fallback(lang: str | None) -> str:
    return tx(
        lang,
        "Full chart details were not available — scores still use Vedic rules on birth data provided.",
        "Poori chart details available nahi thi — scores phir bhi diye gaye birth data par Vedic rules se compute hue.",
    )


def invpat_bh_weak_maitri_strong(lang: str | None) -> str:
    return tx(
        lang,
        "You click as friends almost effortlessly, yet two different "
        "long-term life maps sit underneath — neither of you names "
        "this out loud, but both feel it on slow Sundays.",
        "Dosti me click almost aasaan hai, phir bhi neeche do alag lambe-arze "
        "life maps baithe hain — zubaan par naam kam, slow Sunday par feel zyada.",
    )


def invpat_yoni_gana(lang: str | None) -> str:
    return tx(
        lang,
        "Emotionally you read each other quickly — physical rhythm "
        "and the timing of intimacy may not match the same way, "
        "and most couples mistake this for a deeper problem.",
        "Emotionally ek doosre ko jaldi padh lete ho — physical rhythm aur "
        "nazdeeki ka timing utna match nahi, aur zyada jode isko bade problem samajh baithte hain.",
    )


def invpat_nadi_outlier(lang: str | None) -> str:
    return tx(
        lang,
        "Both of you can be doing everything right and still feel a "
        "subtle, hard-to-name fatigue around each other — it behaves "
        "like an energetic mismatch that ritual steadiness softens; "
        "blame rarely helps.",
        "Sab sahi kar rahe ho phir bhi ek halki, naam-mushkil thakawat feel ho sakti hai — "
        "yeh energetic mismatch jaisa behave karta hai; ritual se thoda narm padta hai; "
        "ilzaam kam kaam aata hai.",
    )


def invpat_manglik_asym(lang: str | None) -> str:
    return tx(
        lang,
        "One of you carries Mars-driven intensity the other simply "
        "does not — during stress, this asymmetry becomes the "
        "invisible script behind almost every flare-up.",
        "Ek par Mangal-wali intensity hai, doosre par utna nahi — stress me "
        "yeh asymmetry har flare-up ke peeche invisible script ban jaati hai.",
    )


def invpat_default(lang: str | None) -> str:
    return tx(
        lang,
        "Neither of you likes emotional drama — yet both silently "
        "expect the other to understand without being asked. That "
        "single unspoken expectation runs underneath most of the "
        "small distances you'll feel over the years.",
        "Drama pasand nahi, phir bhi chup-chap umeed hai doosra bina kahe samajh le — "
        "yeh ek unspoken umeed saalon ke chhote faaslon ke neeche chalti rehti hai.",
    )


# ── Snapshot deterministic prose (Roman Hindi only when ``hn``) ───────────────

def snap_opening(
    lang: str | None,
    n1: str,
    n2: str,
    mood_band: str,
    tag_sentence: str,
    manglik: bool,
) -> str:
    """``mood_band`` is 'high' | 'mid' | 'low' from caller's ratio logic (``hn`` PDF lane)."""
    if mood_band == "high":
        mood = (
            "Classical tally generous range me hai — pyaar ko gehrai milne ki jagah hai, "
            "har hafta rishte par referendum nahi."
        )
    elif mood_band == "mid":
        mood = (
            "Classical tally workable beech me hai — yahan pyaar rozmarra stress ke baad "
            "sabr se prove hota hai, sirf peak moments me nahi."
        )
    else:
        mood = (
            "Paper par margin thoda tight hai — phir bhi kaafi enduring shaadiyan yahan "
            "tikti hain jab dono rhythms jaldi naam de dein, chup-chap dard archive na hone dein."
        )
    mars = ""
    if manglik:
        mars = (
            " Ek chart par Mars ka garm pulse hai — jab toofan shaant naam se aate hain, "
            "dramatise kam, stability zyada."
        )
    tail = (
        " Aage ke hisse inhi signals ko rozmarra marriage observation me translate karte hain — "
        "tone, timing, repair — abstract score nahi."
    )
    return f"{n1} aur {n2}: {mood} {tag_sentence}{mars}{tail}"


def snap_tag_sentence_empty(lang: str | None) -> str:
    return tx(
        lang,
        "The Ashtakoot row and the chapters that follow anchor this reading in "
        "chart-visible habits and lived marriage observation.",
        "Ashtakoot row aur aage ke adhyay is padhne ko chart-dikhne wali aadaton aur "
        "shaadi-wale nireekshan me baandhte hain.",
    )


def snap_tag_bit_pull(lang: str | None, pull: str) -> str:
    return tx(
        lang,
        f"Emotional pull reads as {pull.lower()}.",
        f"Emotional pull aise padhta hai: {pull.lower()}.",
    )


def snap_tag_bit_mp(lang: str | None, mp: str) -> str:
    return tx(
        lang,
        f"Marriage potential reads as {mp.lower()}.",
        f"Shaadi potential aise dikhta hai: {mp.lower()}.",
    )


def snap_tag_bit_stab(lang: str | None, stab: str) -> str:
    return tx(
        lang,
        f"Long-horizon stability reads as {stab.lower()}.",
        f"Lamba horizon stability aise padhti hai: {stab.lower()}.",
    )


_SNAP_MICRO_HN: dict[str, str] = {
    "Quiet Pull": (
        "Yeh aksar thandaapan nahi; bade emotional drama par narm throttle lagti hai — "
        "overload ke baad dheere garam hona, ya pehle consistency se care dikhana. "
        "Pace ko zubaan par laana chahiye warna chhoti rejection-wali kahaniyan ban jaati hain."
    ),
    "Delayed Stability": (
        "Horizon sukoon lightning se kam, adhyayon se zyada pak sakta hai — timing, life-direction, "
        "Mars pacing se pehle milestones bahar se obvious nahi lagte. "
        "Manglik skew late-night heavy baaton, neend, travel par extra garmi daal sakta hai — "
        "yeh headline fate verdict nahi."
    ),
    "Deep Attachment": (
        "Snapshot me emotional charge zyada dikhta hai — pyaar intensity, memory, aur mirror-hone ki "
        "bhook le ke aata hai. Kaam pyaar kam karna nahi; stress ke din pride ko vulnerable ghanton par "
        "hijack hone se bachana hai."
    ),
    "Steady Affection": (
        "Medium pull aksar unsung marriage band hota hai — kam fireworks, zyada dohraane layak meherbani. "
        "Rishta tab gehra hota hai jab micro-bids (nazar, check-in) aksar postpone se pehle jawab paate hain."
    ),
    "Tone Clashes First": (
        "Takraav pehle tone, thaki awaaz, timing se dikhta hai — asli topic poora bolne se pehle. "
        "Baat ke pehle minute ko sacred maanoge to pattern repair ho sakta hai."
    ),
    "Steady Surface Weeks": (
        "Rozmarra shaant dikh sakta hai jab andar planning abhi match ho rahi ho — shaant hafton ko "
        "finished alignment mat samajhna: paise, boundaries, extended family."
    ),
    "Uneven Rhythm": (
        "Achhe aur hilte hafte bina drama ke alternate ho sakte hain — timing aur touch hamesha saath nahi. "
        "Is beat ko naam doge to aam insaani variance par catastrophise kam hoga."
    ),
    "_default": (
        "Yeh chhota saar chart mix ka rhythm batata hai — number waale adhyayon me is label ke peeche "
        "ki zindagi-wali choreography khulti hai.",
    ),
}


def snap_microcopy_body_hn(tag: str) -> str:
    return _SNAP_MICRO_HN.get(tag, _SNAP_MICRO_HN["_default"])


def snap_ashtakoot_empty_koots(lang: str | None) -> str:
    return tx(
        lang,
        "The eight classical scores were not all available for this chart — "
        "the narrative chapters still carry the lived reading; use them together "
        "with what you already know from life.",
        "Aath classical score is chart ke liye poori tarah available nahi the — "
        "phir bhi kahani waale adhyay lived read le aate hain; unhe apni zindagi ke saath mila kar padho.",
    )


def snap_ashtakoot_open_piece(lang: str | None) -> str:
    return tx(
        lang,
        "Each badge is a domestic lens — who steers small plans, how apologies "
        "land after a bad day, whether fatigue mirrors — not a moral grade on love.",
        "Har badge ghar ka ek lens hai — chhote plan kaun chalata hai, bure din ke baad maafi kaise lagti hai, "
        "thakawat mirror hoti hai ya nahi — yeh pyaar par moral number nahi.",
    )


def snap_ashtakoot_high_total(lang: str | None) -> str:
    return tx(
        lang,
        "Your combined tally is high enough that friction is less likely to "
        "colonise the whole week — the edge shifts to humility during the rare hot days.",
        "Milakar tally itni upar hai ki takraav poore hafte par kabza kam karta — "
        "garm dinon par humility zyada mayne rakhti hai.",
    )


def snap_ashtakoot_low_total(lang: str | None) -> str:
    return tx(
        lang,
        "A modest total is not a verdict — it flags where explicit habits "
        "(timing of talks, money clarity, touch pace) earn outsized payoff.",
        "Thoda total faisla nahi — yeh batata hai kahan saaf aadatein (baat ka time, paise ki safai, touch ki raftaar) "
        "zyada asar laati hain.",
    )


def snap_ashtakoot_koot_suffix(lang: str | None, label: str, ln: str) -> str:
    return tx(lang, f"{label} at full marks: {ln}.", f"{label} full ankh par: {ln}.")


def snap_ashtakoot_damage_suffix(lang: str | None, label: str, mark: str, ln: str) -> str:
    return tx(
        lang,
        f"{label} ({mark}) maps to: {ln}.",
        f"{label} ({mark}) is hisse ko aise map karta hai: {ln}.",
    )


def snap_bond_strength_fallback(lang: str | None) -> str:
    return tx(
        lang,
        "Repeatable micro-kindness — eye contact after a long day, a soft "
        "check-in before problem-solving — quietly compounds when classical "
        "scores are only middling.",
        "Dohraane layak chhoti meherbani — lambe din ke baad eye contact, problem se pehle narm check-in — "
        "jab classical score beech me hon tab bhi dheere-jama hota hai.",
    )


def snap_bond_strength_wrap(lang: str | None, parts_joined: str) -> str:
    return tx(
        lang,
        f"What strengthens this bond is less about peak romance and more about {parts_joined}.",
        f"Is rishte ko mazboot banane wala peak romance se kam hai, zyada yeh: {parts_joined}.",
    )


def snap_bond_challenge_manglik_extra(lang: str | None) -> str:
    return tx(
        lang,
        "Mars heat on one chart can spike urgency — watch sleep, travel, "
        "and who initiates heavy talks after 10 p.m.",
        "Ek chart par Mars ki garmi urgency badha sakti hai — neend, travel, aur raat 10 ke baad "
        "bhaari baat kaun shuru karta hai, is par nazar rakho.",
    )


def snap_bond_challenge_fallback(lang: str | None) -> str:
    return tx(
        lang,
        "The main long-term risk is the universal kitchen pattern — unspoken "
        "labour, silent treatment after overload, and reading tired tone as "
        "withdrawal of love.",
        "Sabse bada lamba risk wahi kitchen pattern hai — bola na gaya bojh, overload ke baad silent treatment, "
        "aur thaki tone ko pyaar ki withdrawal samajh lena.",
    )


def snap_bond_challenge_wrap(lang: str | None, parts_joined: str) -> str:
    return tx(
        lang,
        f"The main long-term challenge to plan for: {parts_joined}.",
        f"Lambe arse ke liye sabse bada challenge jiska hisaab rakhna hai: {parts_joined}.",
    )


# ── Invisible patterns (under Hidden Truth) ───────────────────────────────────
def invisible_patterns_hn() -> list[str]:
    return [
        "Tum dono drama pasand nahi karte — phir bhi chup-chap umeed rakhte ho "
        "dusra bina kahe samajh le. Yeh ek unspoken umeed hi zyada tar chhote faaslon ki "
        "jad ban jaati hai.",
    ]


# ── Koot lived meaning pieces (Roman Hindi) ───────────────────────────────────
_KOOT_STRENGTH_HN: dict[str, str] = {
    "varna": "samajik chehra seedha rehta hai — mehmaan-nawazi me pehle kaun bolta hai is par chup-chap score kam",
    "vashya": "chhote plan kaun chalata hai — hafta bhar power-wali preamble kam",
    "tara": "bure din ka timing kam fisalta — maafi pehle lag jaati hai",
    "yoni": "nazdeeki ki raftaar zyada hairan kam — instinct zyada match",
    "graha": "stress me mood pehle decode — ajnabi jitna uljhan kam",
    "gana": "jhagde ka pattern aur 'shaam ko log' wala annoy kam",
    "bhakoot": "paise aur sass-sasur stress phir bhi atka loop kam",
    "nadi": "thakawat ka pattern mirror kam — ek thake to doosra catch-up zyada",
}
_KOOT_DAMAGE_HN: dict[str, str] = {
    "varna": "ego chot cold courtesy se dikhti hai, awaaz unchi nahi",
    "vashya": "roz ke micro-faisle ka naam-nihin jhagda ban sakta hai",
    "tara": "sahi baat galat ghante — chhoti miss stack ho jaati hai",
    "yoni": "touch aur chidchidaapan saath — pace mismatch, care ki kami nahi",
    "graha": "same stress week ek ko attack, ek ko shutdown pad sakta hai",
    "gana": "ek ko shaam ko shor, ek ko cave — same evening, do zaroorat",
    "bhakoot": "life-direction dheere alag — bachat, shehar, maa-baap ke expectation",
    "nadi": "dono same Tuesday thake — task blame se pehle energy mismatch",
}


def koot_decoded_eyebrow(lang: str | None) -> str:
    return tx(lang, "COMPATIBILITY NUMBERS DECODED", "COMPATIBILITY KE ANK SAMJHE")


def koot_decoded_title(lang: str | None) -> str:
    return tx(lang, "Compatibility Numbers Decoded", "Compatibility ke ank — seedhi zubaan")


def koot_decoded_subtitle(lang: str | None) -> str:
    return tx(
        lang,
        "Each of the 8 koots, explained in plain everyday language.",
        "Aath koot — rozmarra zubaan me, ek-ek samjha hua.",
    )


def blueprint_title(lang: str | None) -> str:
    return tx(lang, "Marriage Blueprint", "Shaadi ka blueprint")


def blueprint_subtitle(lang: str | None) -> str:
    return tx(
        lang,
        "How each of you arrives in marriage — and what daily rhythm "
        "naturally forms when those two natures meet.",
        "Shaadi me tum dono kaise aate ho — aur jab yeh do nature milte hain to roz ka rhythm naturally kaisa ban jata hai.",
    )


def attraction_title(lang: str | None) -> str:
    return tx(
        lang,
        "Why This Bond Formed — and the One Thing That Will Test It",
        "Yeh rishta kyun bana — aur ek cheez jo ise sabse zyada test karegi",
    )


def attraction_subtitle(lang: str | None) -> str:
    return tx(
        lang,
        "The two truths most reports skip. Both pulled from your charts.",
        "Do sach jo zyada report chhod dete hain — dono tumhari kundliyon se nikaale gaye.",
    )


def attraction_ground_card(lang: str | None) -> str:
    return tx(
        lang,
        "These two truths are derived from your strongest and "
        "weakest koot scores — engine-locked, not a guess.",
        "Yeh dono sach sabse mazboot aur sabse kamzor koot ankhon se nikale gaye — engine-lock, guess nahi.",
    )


_ATTRACT_KOOT_PHRASE_HN: dict[str, str] = {
    "gana": "andar ka emotional rhythm zyada match",
    "bhakoot": "lambe arse ki life-direction zyada ek line me",
    "yoni": "instinct wali physical comfort gehri",
    "graha": "stress me temperament naturally zyada friendly",
    "nadi": "biological energy complementary lagti hai",
    "varna": "ego respect seedha — dominance kam",
    "vashya": "asli magnetic pull aur influence dono taraf",
    "tara": "timing ek doosre ke liye naturally supportive",
}


def attraction_derived_body_hn(strong_canons: list[str]) -> str:
    lines = [_ATTRACT_KOOT_PHRASE_HN[c] for c in strong_canons if c in _ATTRACT_KOOT_PHRASE_HN]
    if not lines:
        return (
            "Yeh rishta pehle chhoti pehchaanon se banta hai — mugs, paani ki bottle, "
            "quiet din — score se pehle jo matter karta hai."
        )
    if len(lines) >= 2:
        body = f"ek chart me {lines[0]}, doosre me {lines[1]}"
    else:
        body = lines[0]
    return (
        "Yeh rishta isliye pakda hai kyunki dono kundliyan ek doosre ko woh cheez pakdaati hain "
        f"jo ghar jaisa half-remember hota hai — {body}. "
        "Pull yahan headline chemistry se kam, chhoti jagahon me bar-bar aasan feel se zyada hai."
    )


_CHALLENGE_HN: dict[str, tuple[str, str]] = {
    "bhakoot": (
        "life-direction ka dheere drift — loud fight se pehle chhote paise wale faisle me",
        "Same calendar year, do alag paanch-saal ke picture — gap pehle bachat/shehar me dikhta hai.",
    ),
    "nadi": (
        "chhupi energetic friction jo health/thakawat jaisa surface karti hai",
        "Dono same Tuesday thake, same week chidchide — mirror fatigue pehle attitude lagti hai.",
    ),
    "gana": (
        "andar ki fitrat mismatch — ek zyada masti, ek zyada serious",
        "Ek ko shaam ko shor, ek ko cave — TV volume par jhagda, asli maang naam ke bina.",
    ),
    "yoni": (
        "physical/emotional rhythm match kam",
        "Touch aur chidchidaapan saath — ek rejection samjhe, ek kehta slow day hai — same bed, do ghadi.",
    ),
    "graha": (
        "stress me temperament ka natural takraav",
        "Load me ek sharp, ek flat — topic pe fight dikhayi deti hai, asliyat neend track karti hai.",
    ),
    "vashya": (
        "kaun kheenche kaun follow — imbalance",
        "Micro-faisle ek side par jamte, doosra late drift — resentment schedule me, speech me kam.",
    ),
    "tara": (
        "galat ghante par sahi baat — mistimed pal",
        "Sahi sentence, galat hour — narm intent ke bavajood 'tu samjhta hi nahi' feel ho jaati hai.",
    ),
    "varna": (
        "ego friction jahan respect kam feel ho",
        "Pehle family-table — kaun introduce, kaun interrupt — living room se pehle.",
    ),
}

_CHALLENGE_HN_DEFAULT: tuple[str, str] = (
    "yeh report ne jo subtle pattern pakda hai woh baar-baar repeat hota hai",
    "Volume se pehle shape repeat — naya topic, purana shape.",
)


def core_challenge_fallback_kitchen_hn() -> str:
    return (
        "Sabse bada risk yahi unnamed kitchen ledger hai — bill kisne notice kiya, "
        "maafi pehle kisne uthayi — jab tak ek hi Tuesday dono thake na hon."
    )


def core_challenge_line_hn(canon: str | None) -> str:
    if not canon:
        return core_challenge_fallback_kitchen_hn()
    label, advice = _CHALLENGE_HN.get(canon, _CHALLENGE_HN_DEFAULT)
    return (
        "Shaadi ko chup-chap sabse zyada nuksan pahunchaane wali ek cheez yeh hai: "
        f"{label}. {advice}"
    )


def verdict_title(lang: str | None) -> str:
    return tx(lang, "Final Verdict", "Akhiri faisla")


def verdict_subtitle(lang: str | None, total: str | float | int, mx: str | float | int) -> str:
    t, m = str(total), str(mx)
    if pdf_ui_hn(lang):
        return f"Isko {t}/{m} headline score ke saath milkar padho."
    return f"Read together with the {t}/{m} headline score."


def verdict_body_default(lang: str | None) -> str:
    return tx(
        lang,
        "The score here is a headline, not a verdict on character. "
        "It maps tendencies — including the awkward weeks nobody posts — "
        "more than it promises ease.",
        "Yeh score headline hai, character par akhri faisla nahi. "
        "Yeh tendency map karta hai — un ajeeb hafton ko bhi jinko koi post nahi karta — "
        "asan zindagi ka vaada usse kam.",
    )


def verdict_grounding(lang: str | None) -> str:
    return tx(
        lang,
        "This verdict is a synthesis of all 7 chapters above plus the "
        "deeper KP marriage-promise reading — not a prediction.",
        "Yeh faisla upar ke saat adhyayon aur gehre KP marriage-waade ke padhne ka synthesis hai — bhavishyavani nahi.",
    )


def closing_thanks(lang: str | None) -> str:
    return tx(lang, "Thank You", "Dhanyavaad")


def closing_body(lang: str | None) -> str:
    return tx(
        lang,
        "Every chart is a beginning, not a verdict. "
        "May this reading help both of you walk into your shared life "
        "with clearer eyes and a softer heart.",
        "Har kundli ek shuruaat hai, akhri faisla nahi. "
        "Yeh padhna tum dono ko saath wali zindagi me zyada saaf nigaah aur narm dil se kadam rakhne me madad kare.",
    )


def closing_footer(lang: str | None) -> str:
    return tx(
        lang,
        "COSMIC LENS  ·  Cosmic Relationship Blueprint Pro",
        "COSMIC LENS · Cosmic Rishta Blueprint Pro",
    )


def pro_placeholder_chapter_blob(lang: str | None) -> str:
    if pdf_ui_hn(lang):
        return (
            "Yahan chart me signal medium range me pada hai — na headline jeet, na headline train wreck. "
            "Aise jodon me tension kabhi topic se kam, timing par zyada hoti hai: ek chhod deta hai, "
            "doosra usi din dubara chipkana chahta hai. Rozmarra me chehra aisa dikhta hai — subah ka mood alag, "
            "shaam ka 'sab normal' mask same. Beech ki silence agreement nahi hoti; thak ke pause hoti hai. "
            "Lamba arsa tab tak settle nahi jab tak repeat hone wale pattern ka naam nahi milta — "
            "chhote late replies, weekend par alag schedules. Yeh map hai, motivation poster nahi."
        )
    return (
        "Yahan chart me signal medium range me pada hai — "
        "na headline win, na headline train wreck. Aise "
        "jodon me tension kabhi topic pe kam, timing pe "
        "zyada hota hai: ek chhod deta hai, doosra usi din "
        "dubara chipka chahta hai. "
        "Rozmarra me chehra aisa dikhta hai — subah ka mood "
        "alag, shaam ka 'sab normal' mask same. Beech ki "
        "silence agreement nahi hoti; thak ke pause hoti hai. "
        "Lamba arsa tab tak settle nahi jab tak repeat hone "
        "wale pattern ka naam nahi milta — chhote late replies, "
        "weekend pe alag schedules. Yeh map hai, motivation poster nahi."
    )


def bp_heading_marriage_meaning(lang: str | None, p1: str, p2: str) -> str:
    if pdf_ui_hn(lang):
        return f"{p1} aur {p2} ke liye shaadi andar se kya alag-alag feel hoti hai"
    return f"What marriage means to {p1} vs {p2}"


def bp_heading_affection(lang: str | None) -> str:
    return tx(lang, "How affection actually shows up here", "Yahan pyaar practically kaise dikhta hai")


def bp_heading_conflict(lang: str | None) -> str:
    return tx(lang, "How conflict actually plays out", "Takraav yahan practically kaise chalta hai")


def bp_heading_daily_rhythm(lang: str | None) -> str:
    return tx(
        lang,
        "The daily emotional rhythm of this bond",
        "Is rishte ka rozmarra emotional rhythm",
    )


def blueprint_block_p1_nature(lang: str | None, p1: str) -> str:
    return tx(lang, f"{p1}'s marriage nature", f"{p1} ki shaadi-wali fitrat")


def blueprint_block_p2_nature(lang: str | None, p2: str) -> str:
    return tx(lang, f"{p2}'s marriage nature", f"{p2} ki shaadi-wali fitrat")


def blueprint_block_interaction(lang: str | None) -> str:
    return tx(lang, "How both of you interact day-to-day", "Rozmarra tum dono kaise interact karte ho")


def blueprint_block_p1_needs(lang: str | None, p1: str, p2: str) -> str:
    return tx(lang, f"What {p1} needs from {p2}", f"{p1} ko {p2} se kya chahiye")


def blueprint_block_p2_needs(lang: str | None, p1: str, p2: str) -> str:
    return tx(lang, f"What {p2} needs from {p1}", f"{p2} ko {p1} se kya chahiye")


# English fragments in mixed closers → pure Roman Hindi for ``hn`` lane
def verdict_closer_high(lang: str | None) -> str:
    return tx(
        lang,
        "Meri practice me is band me jo rishta stable dikhta hai woh "
        "rarely 'perfect harmony' se hota hai — silent resentment ko "
        "jaldi naam dena padta hai warna woh furniture ban jaata hai. "
        "The chart is naming that ledger, not decorating it.",
        "Meri practice me is band me jo rishta stable dikhta hai woh aksar 'perfect harmony' se kam, "
        "chup-chap naraazgi ko jaldi naam dena zyada hota hai warna woh furniture ban jaata hai. "
        "Kundli us ledger ko naam deti hai, sajati nahi.",
    )


def verdict_closer_mid(lang: str | None) -> str:
    return tx(
        lang,
        "Yahan compatibility ka matlab same-page hona kam hai — zyada "
        "awkward affection aur delayed timing ko bardash karna hai "
        "bina har mismatch ko moral lecture banana. "
        "That uneven rhythm is the marriage.",
        "Yahan compatibility ka matlab same-page hona kam hai — zyada ajeeb nazdeeki aur der se timing "
        "ko bardash karna hai bina har mismatch ko moral lecture banana. "
        "Woh uneven rhythm hi shaadi ka asli chehra hai.",
    )


def verdict_closer_low(lang: str | None) -> str:
    return tx(
        lang,
        "Yahan sabse uncomfortable truth simple hai: kaafi tension log "
        "agreement se solve karne ki koshish karte hain jab tak silent "
        "resentment already settle ho chuka hota hai — acknowledgement late "
        "ho to bhi kam hota hai nahi. "
        "This bond asks for that honesty without performance.",
        "Yahan sabse uncomfortable truth seedha hai: log agreement se tension solve karne lagte hain "
        "jab tak chup-chap naraazgi pehle hi settle ho chuki hoti hai — der se maanna bhi kabhi-kabhi kam pad jaata hai. "
        "Yeh rishta us imandaari maangta hai, performance ke bina.",
    )

