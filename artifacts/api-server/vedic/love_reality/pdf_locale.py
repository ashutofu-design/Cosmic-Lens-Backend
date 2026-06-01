"""Love Reality Pro PDF — localized chrome (en / hn / hi)."""
from __future__ import annotations

from vedic.compat.milan_pdf_locale import pdf_ui_hn
from vedic.compat.premium_chapters import normalize_pro_pdf_lang


def normalize_love_reality_pdf_lang(lang: str | None) -> str:
    """Content + polish lane: en | hn | hi."""
    return normalize_pro_pdf_lang(lang)


def love_reality_pdf_render_lang(lang: str | None) -> str:
    """
    ReportLab font lane. Devanagari needs bundled Noto; map hi → hn (Roman Hindi)
    so chapter bodies stay readable when Noto is not on the server.
    """
    code = normalize_love_reality_pdf_lang(lang)
    return "hn" if code == "hi" else code


def cover_title(lang: str | None) -> str:
    if pdf_ui_hn(lang):
        return "Love Reality Check Pro"
    return "Love Reality Check Pro"


def cover_subtitle(lang: str | None) -> str:
    if pdf_ui_hn(lang):
        return "Aap aur aapke current partner — poori emotional truth ek report mein"
    return "You & your current partner — the full emotional truth in one report"


def cover_prepared_line(lang: str | None) -> str:
    if pdf_ui_hn(lang):
        return "Prepared by"
    return "Prepared by"


def cover_powered_line(lang: str | None) -> str:
    if pdf_ui_hn(lang):
        return "Powered by Advanced Cosmic Intelligence"
    return "Powered by Advanced Cosmic Intelligence"


def cover_generated_prefix(lang: str | None) -> str:
    if pdf_ui_hn(lang):
        return "Generated on"
    return "Generated on"


def chapter_prefix(lang: str | None) -> str:
    if pdf_ui_hn(lang):
        return "Chapter"
    return "CHAPTER"


def pro_chapter_rows(lang: str | None) -> list[tuple[str, str, str, str]]:
    """(internal_key, eyebrow, title, subtitle)"""
    if not pdf_ui_hn(lang):
        return [
            ("love_connection", "LOVE CONNECTION", "Love Compatibility",
             "How deep your emotional bond really runs — beyond the surface spark."),
            ("breakup", "BREAKUP CHANCES", "Breakup Chances",
             "What quietly strains the bond — and when pressure peaks."),
            ("loyalty", "LOYALTY CHECK", "Loyalty Check",
             "Trust on the surface vs consistency through hard phases."),
            ("will_return", "WILL THEY RETURN?", "Will X Return?",
             "Whether an unfinished emotional cycle still keeps this tie alive."),
            ("future_outcome", "FUTURE OUTCOME", "Future Outcome",
             "Where this relationship drifts in the next chapters of time."),
            ("red_flags", "HIDDEN RED FLAGS", "Hidden Red Flags",
             "Subtle warning signs that grow louder if unaddressed."),
        ]
    return [
        ("love_connection", "PYAAR KI GEHRAI", "Love Compatibility",
         "Emotional bond kitni gehri hai — surface spark se zyada."),
        ("breakup", "BREAKUP CHANCES", "Breakup Chances",
         "Bond ko chup-chap kya strain karta hai — pressure kab peak hoti hai."),
        ("loyalty", "LOYALTY CHECK", "Loyalty Check",
         "Surface trust vs mushkil phase me consistency."),
        ("will_return", "WAPAS AAYENGE?", "Will X Return?",
         "Adhoora emotional cycle ab bhi is rishte ko active rakhta hai ya nahi."),
        ("future_outcome", "FUTURE OUTCOME", "Future Outcome",
         "Aage ke time chapters me yeh rishta kidhar drift karega."),
        ("red_flags", "HIDDEN RED FLAGS", "Hidden Red Flags",
         "Halke warning signs jo address na ho to zor pakadte hain."),
    ]


def snapshot_title(lang: str | None) -> str:
    if pdf_ui_hn(lang):
        return "Relationship Snapshot"
    return "Relationship Snapshot"


def snapshot_subtitle(lang: str | None) -> str:
    if pdf_ui_hn(lang):
        return "Love score + quick read of where you both stand today"
    return "Love score + a quick read of where you both stand today"


def hidden_truth_title(lang: str | None) -> str:
    if pdf_ui_hn(lang):
        return "Hidden Truth"
    return "Hidden Truth"


def special_title(lang: str | None) -> str:
    if pdf_ui_hn(lang):
        return "What Makes This Bond Strong"
    return "What Makes This Bond Strong"


def damage_title(lang: str | None) -> str:
    if pdf_ui_hn(lang):
        return "What Can Quietly Damage"
    return "What Can Quietly Damage"


def practical_title(lang: str | None) -> str:
    if pdf_ui_hn(lang):
        return "Practical Love Life Together"
    return "Practical Love Life Together"


def verdict_title(lang: str | None) -> str:
    if pdf_ui_hn(lang):
        return "Final Verdict"
    return "Final Verdict"


def footer_label(lang: str | None) -> str:
    if pdf_ui_hn(lang):
        return "Cosmic Lens · Love Reality Pro"
    return "Cosmic Lens · Love Reality Pro"


def score_breakdown_title(lang: str | None) -> str:
    if pdf_ui_hn(lang):
        return "Love Score — Kaise Bana?"
    return "How Your Love Score Was Calculated"


def score_breakdown_subtitle(lang: str | None) -> str:
    if pdf_ui_hn(lang):
        return "Har line chart math se — yeh number random nahi hai"
    return "Each line comes from chart math — this number is not random"


def chart_snapshot_title(lang: str | None) -> str:
    if pdf_ui_hn(lang):
        return "Chart Facts (Aap Dono)"
    return "Chart Facts (Both Partners)"


def chart_snapshot_subtitle(lang: str | None) -> str:
    if pdf_ui_hn(lang):
        return "Degrees, houses, dasha — jis basis par chapters likhe gaye"
    return "Degrees, houses, dasha — the basis for every chapter below"


def timing_note_title(lang: str | None) -> str:
    if pdf_ui_hn(lang):
        return "Timing Note"
    return "Timing Note"


def method_note_title(lang: str | None) -> str:
    if pdf_ui_hn(lang):
        return "Yeh Report Kaise Taiyar Hui"
    return "How This Report Was Prepared"


def method_note_body(lang: str | None) -> str:
    if pdf_ui_hn(lang):
        return (
            "Yeh Love Reality report Cosmic Lens dwara aapke janam ke details par banayi gayi hai — "
            "Swiss Ephemeris (Lahiri) chart calculation aur advanced Vedic love-compatibility rules "
            "(ghar, dasha, Navamsa, dono charts ka milan) ke basis par. "
            "Jo scores aur chapters hain, woh chart-based analysis se aate hain; yeh advanced, "
            "placement-driven relationship guidance hai. "
            "Yeh self-understanding ke liye hai — doctor, lawyer, therapist ya face-to-face pandit "
            "consultation ki jagah nahi. Aapke choices hamesha matter karte hain."
        )
    return (
        "This Love Reality report is prepared by Cosmic Lens from your birth details using "
        "Swiss Ephemeris (Lahiri) chart calculation and advanced Vedic love-compatibility rules "
        "(houses, dasha, Navamsa, and couple synastry). Scores and chapters reflect chart-based "
        "analysis — advanced, placement-driven relationship guidance, not random text. "
        "This is for self-understanding only; it is not a substitute for medical, legal, "
        "therapeutic, or in-person counselling. Your choices always matter."
    )


def chapter_placeholder(lang: str | None) -> str:
    if pdf_ui_hn(lang):
        return (
            "Yeh chapter aap dono ke combined chart signals par based hai — "
            "theme ke liye jo placement logic measure hui, wahi reading neeche reflect hoti hai."
        )
    return (
        "This chapter draws on your combined chart signals for this theme — "
        "the reading below reflects the placement logic measured for your current bond."
    )


def score_ledger_fallback(lang: str | None, score: int) -> str:
    if pdf_ui_hn(lang):
        return (
            f"Final love compatibility score: {score}/100. "
            "Line-by-line breakdown tabhi dikhega jab full birth chart data available ho."
        )
    return (
        f"Final love compatibility score: {score}/100. "
        "A line-by-line breakdown appears when full birth chart data is available."
    )


def chart_snapshot_fallback(lang: str | None) -> str:
    if pdf_ui_hn(lang):
        return (
            "Poori chart details is run mein available nahi thi — "
            "scores phir bhi available birth data par Vedic rules se compute hue."
        )
    return (
        "Full chart details were not available for this run — "
        "scores still use Vedic rules on the birth data provided."
    )


def closing_thanks(lang: str | None) -> str:
    if pdf_ui_hn(lang):
        return "Dhanyavaad"
    return "Thank You"


def closing_body(lang: str | None) -> str:
    if pdf_ui_hn(lang):
        return (
            "Har chart ek shuruaat hai, final verdict nahi. "
            "Jo sach hai use naam do — clarity aage ka raasta khulti hai."
        )
    return (
        "Every chart is a beginning, not a final verdict. "
        "Name what is true — clarity opens the path ahead."
    )


def closing_footer(lang: str | None) -> str:
    if pdf_ui_hn(lang):
        return "COSMIC LENS  ·  Love Reality Pro"
    return "COSMIC LENS  ·  Love Reality Pro"
