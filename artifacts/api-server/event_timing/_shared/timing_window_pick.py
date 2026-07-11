"""Pick PRIMARY (#1) vs next (#2) dasha window for any timing question."""
from __future__ import annotations

import re
from typing import Any

_MONTH_EN = {
    "01": "January",
    "02": "February",
    "03": "March",
    "04": "April",
    "05": "May",
    "06": "June",
    "07": "July",
    "08": "August",
    "09": "September",
    "10": "October",
    "11": "November",
    "12": "December",
}

# User wants the 2nd ranked dasha timeline (backup), not #1 PRIMARY.
_NEXT_TIMING_WINDOW_PATTERNS = [
    re.compile(p, re.I)
    for p in (
        r"\b(agar|if)\b.{0,70}\b(nahi|na|not|nhi|miss)\b.{0,50}\b(hoga|hogi|ho|milega|milegi|possible|sakta|sakti)\b",
        r"\b(aage|agla|agli|next|dusra|dusri|another|alternate|backup)\b.{0,40}\b("
        r"kab|when|time|window|period|samay|hoga|hogi|milega|milegi|ho\s+sakta|ho\s+sakti"
        r")\b",
        r"\b(kab|when)\b.{0,25}\b(aage|agla|agli|next|dusra|baad|later)\b",
        r"\b(aage|agla|agli)\s+(kab|kaun\s*sa|kya)\b",
        r"\b(dusra|alternate|backup|next)\s+(time|window|period|option|chance)\b",
        r"\bnext\s+time\b",
        r"\bnext\s+(?:kab|kaun\s*sa\s+time|period|window|chance|opportunity)\b",
        r"\b(kab|when)\b.{0,20}\b(ho\s+sakta|ho\s+sakti|possible|milega|milegi)\b",
        r"\b(ho\s+sakta|ho\s+sakti)\b.{0,25}\b(kab|when|hai)\b",
        r"\b(january|february|march|april|may|june|july|august|september|october|november|december|"
        r"jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)"
        r".{0,60}\b(nahi|na|not|nhi|miss)\b",
    )
]

_SHORT_NEXT_FOLLOWUP_RX = re.compile(
    r"(?ix)^\s*(aur|agla|aage|next|phir|uske\s+baad|dusra)\s*(kab|time|window|period)?\s*\??\s*$"
)

_MONTH_ALIAS: dict[str, str] = {
    "jan": "01", "january": "01", "feb": "02", "february": "02",
    "mar": "03", "march": "03", "apr": "04", "april": "04",
    "may": "05", "jun": "06", "june": "06", "jul": "07", "july": "07",
    "aug": "08", "august": "08", "sep": "09", "sept": "09", "september": "09",
    "oct": "10", "october": "10", "nov": "11", "november": "11",
    "dec": "12", "december": "12",
}

_AFTER_MONTH_CUTOFF_RX = re.compile(
    r"(?ix)"
    r"(?:\b(january|february|march|april|may|june|july|august|september|october|november|december|"
    r"jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\b.{0,20}\b(20\d{2})\b.{0,20}\b(baad|baad|after)\b"
    r"|\b(20\d{2})\b.{0,20}\b(january|february|march|april|may|june|july|august|september|october|november|december|"
    r"jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\b.{0,20}\b(baad|baad|after)\b"
    r"|\b(baad|baad|after)\b.{0,20}\b(january|february|march|april|may|june|july|august|september|october|november|december|"
    r"jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\b.{0,20}\b(20\d{2})\b"
    r")"
)

_LATER_WINDOW_RX = re.compile(
    r"(?ix)\b("
    r"aur\s+koi|uske\s+baad\s+aur|baad\s+me\s+aur|phir\s+aur|"
    r"teesra|teesri|third\s+window|3rd\s+window|"
    r"aur\s+(?:koi|ek)\s+(?:promotion|window|chance|mauka)"
    r")\b"
)


def _parse_cutoff_after_month(question: str) -> str | None:
    """Return YYYY-MM for 'dec 2026 ke baad' style cutoffs."""
    q = (question or "").strip()
    m = _AFTER_MONTH_CUTOFF_RX.search(q)
    if not m:
        return None
    groups = m.groups()
    # patterns alternate month/year ordering — find month token + year token
    month_tok = year_tok = None
    for g in groups:
        if not g or g.lower() in ("baad", "baad", "after"):
            continue
        if re.fullmatch(r"20\d{2}", g):
            year_tok = g
        elif g.lower() in _MONTH_ALIAS:
            month_tok = g.lower()
    if month_tok and year_tok:
        return f"{year_tok}-{_MONTH_ALIAS[month_tok]}"
    return None


def _count_timing_followups(history: Any) -> int:
    if not isinstance(history, (list, tuple)):
        return 0
    count = 0
    for item in history:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip().lower()
        if role not in ("user", "human"):
            continue
        text = str(item.get("text") or item.get("content") or "")
        if detect_next_timing_window_question(text):
            count += 1
    return count


def detect_later_timing_window_question(question: str) -> bool:
    """User wants a window after #2 — e.g. 'aur koi promotion', 'dec 2026 ke baad'."""
    q = (question or "").strip()
    if not q:
        return False
    if _parse_cutoff_after_month(q):
        return True
    return bool(_LATER_WINDOW_RX.search(q))


def detect_next_timing_window_question(question: str, history: Any = None) -> bool:
    """True when user asks for the next/alternate timing window (#2 in dasha list)."""
    q = (question or "").strip()
    if not q:
        return False
    for rx in _NEXT_TIMING_WINDOW_PATTERNS:
        if rx.search(q):
            return True
    if _SHORT_NEXT_FOLLOWUP_RX.search(q):
        return True
    if history and _last_assistant_had_timing_window(history):
        if re.search(r"(?ix)\b(aage|agla|agli|next|dusra|phir|aur)\b", q):
            return True
    return False


def _last_assistant_had_timing_window(history: Any) -> bool:
    if not isinstance(history, (list, tuple)):
        return False
    timing_kw = (
        "window", "period", "dasha", "mahadasha", "antardasha",
        "ke beech", "tak dikhta", "tak hai", "timing", "kab hogi", "kab hoga",
        "promotion", "shaadi", "marriage", "travel", "visa",
    )
    for item in reversed(history):
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip().lower()
        if role not in ("assistant", "ai", "model"):
            continue
        prev = (item.get("content") or item.get("text") or "").lower()
        return any(k in prev for k in timing_kw)
    return False


def timing_window_index(
    question: str,
    history: Any = None,
    windows: list[dict[str, Any]] | None = None,
) -> int:
    """0 = #1 PRIMARY, 1 = #2 next, 2 = #3 later — based on question depth."""
    win = windows or []
    max_idx = max(0, len(win) - 1)

    after_ym = _parse_cutoff_after_month(question or "")
    if after_ym and win:
        for i, w in enumerate(win):
            start = str(w.get("start") or "")[:7]
            if start and start > after_ym:
                return i
        return max_idx

    if detect_later_timing_window_question(question or ""):
        return min(2, max_idx)

    follow_ups = _count_timing_followups(history)
    if follow_ups >= 2 and win:
        return min(2, max_idx)
    if follow_ups >= 1 and win:
        return min(1, max_idx)

    if detect_next_timing_window_question(question, history):
        return min(1, max_idx)

    return 0


def _normalize_window_row(w: dict[str, Any], rank: int = 0) -> dict[str, Any]:
    start = w.get("start") or w.get("start_iso")
    end = w.get("end") or w.get("end_iso")
    md, ad, pd = w.get("md"), w.get("ad"), w.get("pd")
    lords = w.get("lords")
    if not lords:
        lords = "/".join(x for x in (md, ad, pd) if x)
    window = (w.get("window") or w.get("label") or "").strip()
    if not window and start and end:
        window = f"{str(start)[:7]} → {str(end)[:7]}"
    elif not window and start:
        window = str(start)[:7]
    return {
        "rank": w.get("rank") or rank,
        "md": md,
        "ad": ad,
        "pd": pd,
        "lords": lords,
        "start": str(start)[:7] if start else None,
        "end": str(end)[:7] if end else None,
        "window": window,
        "reason": w.get("reason"),
        "score": w.get("score"),
    }


def extract_ranked_timing_windows(engine_result: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect ordered dasha windows (#1, #2, #3) from any timing engine payload."""
    if not isinstance(engine_result, dict):
        return []

    promo = engine_result.get("promotion_engine")
    if isinstance(promo, dict):
        timing = promo.get("timing") if isinstance(promo.get("timing"), dict) else {}
        raw = timing.get("windows")
        if isinstance(raw, list) and raw:
            return [_normalize_window_row(w, i + 1) for i, w in enumerate(raw) if isinstance(w, dict)]

    sa = engine_result.get("step_audit")
    if isinstance(sa, dict):
        s8 = sa.get("step8")
        if isinstance(s8, dict):
            pw = s8.get("promotion_windows")
            if isinstance(pw, list) and pw:
                return [_normalize_window_row(w, i + 1) for i, w in enumerate(pw) if isinstance(w, dict)]

    top3 = engine_result.get("top_3_windows")
    if isinstance(top3, list) and top3:
        return [_normalize_window_row(w, i + 1) for i, w in enumerate(top3) if isinstance(w, dict)]

    next3 = engine_result.get("next_3_windows")
    if isinstance(next3, list) and next3:
        return [_normalize_window_row(w, i + 1) for i, w in enumerate(next3) if isinstance(w, dict)]

    viable = engine_result.get("viable_top_3")
    if isinstance(viable, list) and viable:
        return [_normalize_window_row(w, i + 1) for i, w in enumerate(viable) if isinstance(w, dict)]

    tw = engine_result.get("timing_window")
    if isinstance(tw, dict):
        rows: list[dict[str, Any]] = []
        nxt = tw.get("next_career")
        if isinstance(nxt, dict) and (nxt.get("start") or nxt.get("lords")):
            rows.append(_normalize_window_row(nxt, 1))
        rec = tw.get("recommended") or tw.get("current")
        if isinstance(rec, dict) and (rec.get("start") or rec.get("lords")):
            if not rows or rows[0].get("start") != _normalize_window_row(rec, 1).get("start"):
                rows.insert(0, _normalize_window_row(rec, 1))
        if rows:
            return rows

    primary = str(engine_result.get("primary_window") or "").strip()
    backup = str(engine_result.get("backup_window") or "").strip()
    rows = []
    if primary:
        rows.append({"rank": 1, "window": primary, "start": None, "end": None, "lords": None})
    if backup:
        rows.append({"rank": 2, "window": backup, "start": None, "end": None, "lords": None})
    if rows:
        return rows

    rec = engine_result.get("recommended_window")
    if isinstance(rec, dict) and (rec.get("start") or rec.get("lords")):
        return [_normalize_window_row(rec, 1)]

    return []


def pick_timing_answer_window(
    engine_result: dict[str, Any],
    question: str = "",
    history: Any = None,
) -> dict[str, Any] | None:
    """Return the window row the user-facing answer must use."""
    windows = extract_ranked_timing_windows(engine_result)
    if not windows:
        return None
    idx = timing_window_index(question, history, windows)
    if idx >= len(windows):
        idx = max(0, len(windows) - 1)
    return dict(windows[idx])


def window_range_label(w: dict[str, Any] | None) -> str:
    if not isinstance(w, dict):
        return ""
    if w.get("window"):
        return str(w["window"]).strip()
    return _format_range_label(w.get("start"), w.get("end"))


def _ym_to_label(ym: str) -> str:
    s = (ym or "").strip()[:7]
    if len(s) < 7 or s[4] != "-":
        return s
    year, mon = s[:4], s[5:7]
    return f"{_MONTH_EN.get(mon, mon)} {year}"


def _format_range_label(start: Any, end: Any) -> str:
    a = _ym_to_label(str(start or ""))
    b = _ym_to_label(str(end or ""))
    if a and b:
        return f"{a} se {b} tak"
    if a:
        return a
    return ""


def narrate_window_line(w: dict[str, Any] | None, rank: int) -> str:
    if not isinstance(w, dict):
        return ""
    label = window_range_label(w)
    lords = str(w.get("lords") or "").strip()
    prefix = f"#{rank}"
    if rank == 1:
        prefix += " PRIMARY (answer yahi — unless user asks next/alternate)"
    elif rank == 2:
        prefix += " NEXT (answer yahi jab user next/agla/agar-nahi puche)"
    elif rank >= 3:
        prefix += " LATER (answer yahi jab user 'ke baad aur' / 3rd window puche)"
    body = label
    if lords and label:
        body = f"{lords} · {label}"
    elif lords:
        body = lords
    return f"{prefix}: {body}".strip(": ") if body else prefix


def locked_window_instruction(
    engine_result: dict[str, Any],
    question: str = "",
    history: Any = None,
) -> str:
    """Prompt line telling LLM which ranked window to narrate."""
    windows = extract_ranked_timing_windows(engine_result)
    if not windows:
        return ""
    idx = timing_window_index(question, history, windows)
    if idx >= len(windows):
        idx = max(0, len(windows) - 1)
    picked = windows[idx]
    label = window_range_label(picked)
    if not label:
        return ""
    rank = idx + 1
    if idx == 0:
        return f">>> NARRATE THIS WINDOW EXACTLY AS (#1 PRIMARY): {label}"
    return (
        f">>> NARRATE THIS WINDOW EXACTLY AS (#{rank} — user asked next/alternate): {label}"
    )


def append_locked_window_to_prompt_block(block: str, engine_result: dict[str, Any], question: str = "") -> str:
    line = locked_window_instruction(engine_result, question)
    if not line or line in (block or ""):
        return block or ""
    return f"{(block or '').rstrip()}\n{line}\n"


def compose_timing_locked_reply(
    engine_result: dict[str, Any],
    question: str = "",
    *,
    topic: str = "event",
    lang: str = "hn",
    history: Any = None,
) -> str | None:
    """Generic Hinglish one-liner using the picked ranked dasha window."""
    _ = lang
    w = pick_timing_answer_window(engine_result, question, history)
    if not w:
        return None
    label = window_range_label(w)
    if not label:
        return None
    idx = timing_window_index(question, history, extract_ranked_timing_windows(engine_result))
    if idx >= 2:
        return f"Agar pehle windows miss hon, agla strong {topic} window {label} dikhta hai."
    if idx >= 1:
        return f"Agar pehla period miss ho, agla strong {topic} window {label} dikhta hai."
    lords = str(w.get("lords") or "").strip()
    if lords:
        return (
            f"Aapka sabse strong {topic} window {label} hai — "
            f"{lords} dasha is phase ko support karta hai."
        )
    return f"Aapka sabse strong {topic} window {label} hai."


def promotion_locked_window_label(verdict: dict[str, Any], question: str = "") -> str:
    return window_range_label(pick_timing_answer_window(verdict, question))


def window_dates_present_in_text(text: str, start: Any, end: Any) -> bool:
    body = (text or "").lower()
    if not body:
        return False
    for raw in (start, end):
        s = str(raw or "").strip()[:7]
        if not s:
            continue
        if s in body:
            return True
        year = s[:4]
        mon = s[5:7]
        if year and year in body:
            mon_name = _MONTH_EN.get(mon, "").lower()
            if mon_name and mon_name in body:
                return True
    return False
