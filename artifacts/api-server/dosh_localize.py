"""Localize dosh-analysis API payloads to en / hn / hi only."""

from __future__ import annotations

from app_lang import coerce_app_lang
from i18n_summary import localize_text


def _localize_item_fields(it: dict, lang: str) -> dict:
    row = dict(it)
    en_name = row.get("name") or ""
    hi_name = row.get("name_hindi") or ""

    if lang == "hi":
        row["name"] = hi_name or en_name
    elif lang == "hn":
        row["name"] = localize_text(en_name, None, "hn")
    else:
        row["name"] = en_name

    if lang == "en":
        return row

    row["headline"] = localize_text(row.get("headline") or "", None, lang)
    row["description"] = localize_text(row.get("description") or "", None, lang)
    row["remedies"] = [
        localize_text(r, None, lang)
        for r in (row.get("remedies") or [])
        if isinstance(r, str) and r.strip()
    ]
    note = row.get("planet_note") or ""
    if note:
        row["planet_note"] = localize_text(note, None, lang)
    return row


def localize_dosh_result(result: dict, lang: str | None) -> dict:
    """Return a copy of analyze_doshas() output with localized text fields."""
    lang = coerce_app_lang(lang)
    if lang == "en" or not result:
        return result

    out = dict(result)
    items = []
    for item in result.get("dosh_list") or []:
        if isinstance(item, dict):
            items.append(_localize_item_fields(item, lang))
    out["dosh_list"] = items
    return out
