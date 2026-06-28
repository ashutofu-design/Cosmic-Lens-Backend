"""Social image, fame & recognition timing — 1H/5H/10H WHEN questions."""
from __future__ import annotations

import re
from typing import Optional

_EXPLICIT_WHEN_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|kab\s+se|when|when\s+will|"
    r"kis\s+(?:mahine|saal|year|month|date|turning\s+point)|"
    r"kis\s+dasha|dasha\s+me|gochar|transit|muhurat|kitne\s+mahine|"
    r"trigger\s+hoga|active\s+hoga|active\s+honge|active\s+ho|"
    r"shuru\s+honge|shuru\s+hoga|approve\s+hoga|prapt\s+hogi|viral\s+hoga"
    r")\b|(?:कब|कितना\s+समय)"
)

_TIMING_RX = re.compile(
    r"(?ix)\b("
    r"kab|kab\s+tak|kab\s+se|when|when\s+will|kis\s+(?:mahine|saal|year|month|date|turning\s+point)|"
    r"milega|milegi|hoga|hogi|honge|aayega|aayegi|banega|banegi|"
    r"shuru\s+hoga|shuru\s+honge|khatam|band\s+hogi|theek\s+hogi|thik\s+hogi|"
    r"viral|trigger|celebrity|famous|recognition|award|"
    r"active|dasha|antardasha|gochar|transit|muhurat|timing|"
    r"turning\s+point|prapt|approve|lagenge|mehsoos|"
    r"kitne\s+mahine|entry|enter|win|jeet"
    r")\b|(?:कब|कितना\s+समय)"
)

_SCOPE_RX = re.compile(
    r"(?ix)\b("
    r"fame|famous|celebrity|viral|social\s+media|instagram|youtube|tiktok|"
    r"influencer|followers|subscribers|content|name\s+chalega|naam\s+chalega|"
    r"recognition|public\s+image|publicity|limelight|spotlight|popular|popularity|"
    r"award|honou?r|honor|padma|national\s+award|international\s+award|"
    r"nobel|oscar|filmfare|samman|puraskar|trophy|medal|prize|"
    r"reputation|bad\s+name|bad\s+naam|defamation|malign|bad\s+press|"
    r"khoyi\s+hui|naam\s+kharab|izzat|image\s+theek|galat\s+soch\w*|"
    r"politic|political|neta|minister|election|rajneeti|leadership|"
    r"public\s+office|party\s+ticket|parliament|loksabha|mla|mp\b|cm\b|"
    r"brand\s+face|media\s+attention|trending|mass\s+fame|public\s+figure|"
    r"celebrity\s+yoga|1st\s+house|5th\s+house|10th\s+house|"
    r"surya|rahu|social\s+image|fame\s+yoga"
    r")\b"
)

_CAREER_JOB_ONLY_RX = re.compile(
    r"(?ix)\b("
    r"promotion|naukri|job\s+change|salary|appraisal|interview|"
    r"government\s+job|sarkari\s+naukri|ips\s+officer|ias\s+officer|"
    r"become\s+doctor|become\s+engineer"
    r")\b",
)

_SPIRITUAL_RX = re.compile(
    r"(?ix)\b(guru|deeksha|meditation|dhyan|moksha|teerth|occult|jyotish)\b",
)


def is_fame_timing_question(
    question: str,
    llm_intent: Optional[dict] = None,
) -> bool:
    q = (question or "").strip()
    if not q:
        return False
    if re.search(r"(?ix)\bkya\b", q) and not _EXPLICIT_WHEN_RX.search(q):
        return False
    if _SPIRITUAL_RX.search(q) and not re.search(
        r"(?ix)\b(fame|viral|award|politic|reputation|celebrity|social\s+media)\b",
        q,
    ):
        return False
    if _CAREER_JOB_ONLY_RX.search(q) and not _SCOPE_RX.search(q):
        return False
    if _CAREER_JOB_ONLY_RX.search(q) and _SCOPE_RX.search(q):
        if not re.search(
            r"(?ix)\b(fame|viral|award|politic|reputation|celebrity|leadership|neta|recognition)\b",
            q,
        ):
            return False
    if isinstance(llm_intent, dict):
        dom = str(llm_intent.get("domain") or "").lower()
        if dom in ("fame", "recognition", "social_fame") and llm_intent.get("is_timing"):
            return True
    if not _SCOPE_RX.search(q):
        return False
    if not _TIMING_RX.search(q) and not _EXPLICIT_WHEN_RX.search(q):
        return False
    return True


def classify_fame_timing_bucket(question: str) -> str:
    from event_timing.fame.fame_timing_v1 import classify_fame_timing_bucket as _classify

    return _classify(question)
