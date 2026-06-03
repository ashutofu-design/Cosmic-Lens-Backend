"""Localize dosh-analysis API payloads to the user's UI language."""

from __future__ import annotations

from i18n_summary import localize_text


def localize_dosh_result(result: dict, lang: str | None) -> dict:
    """Return a copy of analyze_doshas() output with localized text fields."""
    lang = (lang or "en").strip().lower()
    if lang == "en" or not result:
        return result

    out = dict(result)
    items = []
    for item in result.get("dosh_list") or []:
        if not isinstance(item, dict):
            continue
        it = dict(item)
        en_name = it.get("name") or ""
        hi_name = it.get("name_hindi") or ""

        if lang == "hi":
            it["name"] = hi_name or en_name
        else:
            it["name"] = localize_text(en_name, hi_name, lang)

        it["headline"] = localize_text(it.get("headline") or "", None, lang)
        it["description"] = localize_text(it.get("description") or "", None, lang)
        it["remedies"] = [
            localize_text(r, None, lang)
            for r in (it.get("remedies") or [])
            if isinstance(r, str) and r.strip()
        ]
        note = it.get("planet_note") or ""
        if note:
            it["planet_note"] = localize_text(note, None, lang)
        items.append(it)

    out["dosh_list"] = items
    return out
