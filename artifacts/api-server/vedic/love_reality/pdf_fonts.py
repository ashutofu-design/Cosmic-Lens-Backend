"""Love Reality Pro — Devanagari font readiness (Noto on server)."""
from __future__ import annotations


class LoveRealityDevanagariFontError(RuntimeError):
    """Raised when lang=hi but Noto Sans Devanagari is not registered."""


def devanagari_fonts_ready() -> bool:
    from milan_pdf import _INDIC_REGISTERED, register_indic_fonts

    register_indic_fonts(force=True)
    return bool(_INDIC_REGISTERED.get("NotoDeva"))


def hindi_font_pair() -> tuple[str, str]:
    """Return (regular, bold) PostScript names after forced Noto register."""
    from milan_pdf import _font_pair, register_indic_fonts

    register_indic_fonts(force=True)
    return _font_pair("hi")


def require_devanagari_fonts(lang: str) -> None:
    """Fail before PDF render — avoids empty □□□ boxes in Hindi PDFs."""
    code = (lang or "en").strip().lower()
    if code != "hi":
        return
    if devanagari_fonts_ready():
        return
    raise LoveRealityDevanagariFontError(
        "Hindi PDF requires Noto Sans Devanagari fonts on the server. "
        "On VPS run: cd /root/Cosmic-Lens-Backend && "
        "python3 artifacts/api-server/scripts/download_noto_indic_for_milan_pdf.py "
        "then pm2 restart cosmic-api --update-env"
    )
