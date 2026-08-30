"""Lightweight local retrieval over support_agent/knowledge/*.md — no vector DB."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Iterable

from support_agent.knowledge import KNOWLEDGE_FILES, knowledge_dir

_TOKEN = re.compile(r"[a-z0-9\u0900-\u097f]+", re.I)
_STOP = frozenset(
    {
        "a", "an", "the", "is", "are", "was", "were", "be", "to", "of", "and", "or",
        "in", "on", "for", "with", "what", "how", "where", "when", "why", "who",
        "do", "does", "did", "can", "me", "my", "i", "you", "your", "about", "tell",
        "please", "kya", "hai", "kaise", "kahan", "mera", "meri", "mujhe", "batao",
        "yeh", "woh", "this", "that", "every", "all",
        # keep: free, paid, cost, price, plan, pro, basic — product-critical
    }
)

# Synonym boosts so common client phrasing hits the right chunks
_SYNONYMS: dict[str, tuple[str, ...]] = {
    "radar": ("risk", "radar", "home", "alert"),
    "energy": (
        "energy",
        "today",
        "aaj",
        "score",
        "tara",
        "ashtakavarga",
        "forecast",
        "nakshatra",
    ),
    "today": ("today", "aaj", "energy", "score"),
    "aaj": ("aaj", "today", "energy", "score"),
    "forecast": ("forecast", "energy", "7", "day", "home"),
    "dosh": ("dosh", "analysis", "home", "kundli", "manglik"),
    "lucky": ("lucky", "colour", "color", "number", "elements", "home"),
    "numerology": ("numerology", "life", "path", "destiny", "soul"),
    "vastu": ("astrovastu", "vastu", "room", "floor", "plan"),
    "business": ("business", "vastu", "shop", "office", "factory"),
    "love": ("love", "reality", "relationship", "loyalty", "breakup"),
    "milan": ("milan", "kundli", "gun", "marriage", "compatibility"),
    "ask": ("ask", "pack", "v1", "v3", "engine", "chart", "live"),
    "ai": ("ai", "engine", "v1", "v3", "ask", "chatgpt"),
    "chatgpt": ("chatgpt", "ai", "engine", "v1", "v3", "ask"),
    "v3": ("v3", "live", "guide", "queue", "accept", "pack", "min", "session", "prices"),
    "live": ("live", "v3", "guide", "session", "queue", "min", "prices"),
    "session": ("session", "v3", "live", "min", "guide", "prices"),
    "guide": ("guide", "v3", "live", "session"),
    "hour": ("hour", "min", "v3", "live", "prices", "60"),
    "half": ("half", "30", "min", "v3", "live", "prices"),
    "minute": ("minute", "min", "v3", "live", "prices"),
    "minutes": ("minutes", "min", "v3", "live", "prices"),
    "pack": ("pack", "packs", "starter", "popular", "power", "ask", "questions", "prices"),
    "starter": ("starter", "pack", "sasta", "cheapest", "49", "ask", "prices"),
    "sasta": ("sasta", "cheapest", "starter", "pack", "price", "prices"),
    "cheapest": ("cheapest", "sasta", "starter", "pack", "price", "prices"),
    "popular": ("popular", "pack", "ask", "prices"),
    "power": ("power", "pack", "ask", "prices"),
    "report": ("report", "pdf", "my", "reports", "delivery", "priority"),
    "price": ("price", "cost", "rupee", "inr", "pay", "paid", "free", "pricing", "prices"),
    "pricing": ("pricing", "price", "cost", "rupee", "prices"),
    "prices": ("prices", "price", "cost", "rupee", "pack"),
    "kitne": ("kitne", "price", "cost", "rupee", "prices", "charge"),
    "kitna": ("kitna", "price", "cost", "rupee", "prices", "charge"),
    "kitni": ("kitni", "price", "cost", "rupee", "prices", "charge"),
    "charge": ("charge", "price", "cost", "rupee", "prices", "fee"),
    "costly": ("costly", "price", "cost", "rupee", "prices", "mehnga"),
    "mehnga": ("mehnga", "price", "cost", "rupee", "prices"),
    "rate": ("rate", "price", "cost", "rupee", "prices"),
    "fee": ("fee", "price", "cost", "rupee", "priority"),
    "free": ("free", "paid", "basic", "plan", "subscription"),
    "cost": ("cost", "price", "rupee", "inr", "report", "pdf", "prices"),
    "video": ("video", "personalized", "pdf", "pro", "explanation"),
    "personalized": ("personalized", "video", "pro", "pdf"),
    "delivery": ("delivery", "days", "priority", "report", "my", "reports"),
    "find": ("find", "my", "reports", "report", "where"),
    "plan": ("plan", "subscription", "basic", "pro", "trial"),
    "cancel": ("cancel", "renew", "subscription", "plan"),
    "refund": ("refund", "chargeback", "payment", "money", "return"),
    "cosmo": ("cosmo", "id", "profile", "account"),
    "refer": ("refer", "referral", "earn", "friend"),
    "face": ("face", "reading"),
    "palm": ("palmistry", "palm", "hand"),
    "palmistry": ("palmistry", "palm", "hand", "pro"),
    "kundli": ("kundli", "chart", "dasha", "planet", "birth"),
    "dasha": ("dasha", "mahadasha", "antardasha", "future", "timeline"),
    "panchang": ("panchang", "tithi", "nakshatra", "muhurat"),
    "muhurat": ("muhurat", "panchang", "wedding", "auspicious"),
    "gem": ("gemstone", "gem", "navratna", "whatsapp", "sapphire"),
    "gemstone": ("gemstone", "gem", "navratna", "whatsapp"),
    "rectification": ("rectification", "birth", "time", "tob", "milestone"),
    "birth": ("birth", "time", "rectification", "kundli", "onboarding"),
    "personalization": ("personalization", "personal", "kundli", "category", "trait", "home"),
    "career": ("career", "job", "profession", "lifemap", "unlock"),
    "quota": ("quota", "questions", "pack", "free", "daily", "ask"),
    "credit": ("credit", "credits", "room", "scan", "vastu", "pack"),
    "health": ("health", "body", "tridosha", "lifemap"),
    "finance": ("finance", "money", "wealth", "lifemap"),
    "future": ("future", "timeline", "dasha", "insights"),
    "notification": ("notification", "alert", "daily", "push"),
    "alert": ("alert", "daily", "notification", "energy"),
    "remedy": ("remedy", "remedies", "mantra", "daan", "upay"),
    "rashifal": ("rashifal", "horoscope", "daily", "weekly"),
    "founder": ("founder", "whatsapp", "talk", "instagram"),
    "divya": ("divya", "prashna", "prashna"),
    "delete": ("delete", "account", "remove"),
    "onboarding": ("onboarding", "kundli", "create", "signup"),
    "login": ("login", "otp", "google", "sign", "logout"),
    "otp": ("otp", "login", "sms", "resend", "phone"),
    "theme": ("theme", "dark", "light", "mode"),
    "welcome": ("welcome", "gift", "bonus", "free", "signup"),
    "gift": ("gift", "welcome", "bonus", "free", "questions"),
    "instagram": ("instagram", "reel", "answers"),
    "language": ("language", "lang", "profile", "hindi", "english", "hinglish"),
    "logout": ("logout", "login", "force", "stuck", "sign"),
    "farq": ("farq", "help", "ask", "difference"),
    "queue": ("queue", "accept", "v3", "live", "miss"),
    "book": ("book", "v3", "live", "pack", "accept"),
    "wallet": ("wallet", "balance", "transactions", "payment"),
    "family": ("family", "profile", "profiles", "member"),
    "transaction": ("transaction", "payment", "wallet", "order"),
    "razorpay": ("razorpay", "cashfree", "payment", "pay"),
    "cashfree": ("cashfree", "razorpay", "payment", "subscription"),
}

_PRICE_ASK = re.compile(
    r"(?i)\b(price|pricing|prices|cost|costly|charge|fee|rate|kitne|kitna|kitni|"
    r"sasta|sasti|cheapest|mehnga|mehngi|rupee|rs\.?|inr|padta|padega|costly)\b|₹"
)


@dataclass(frozen=True)
class KnowledgeChunk:
    id: str
    source: str
    title: str
    text: str
    tokens: frozenset[str]


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(text or "") if len(t) > 1]


def _query_tokens(question: str) -> set[str]:
    raw = _tokenize(question)
    out: set[str] = set()
    for t in raw:
        if t in _STOP:
            continue
        out.add(t)
        for key, syns in _SYNONYMS.items():
            if t == key or t in syns:
                out.update(syns)
                out.add(key)
    return out


def _split_file(source: str, body: str) -> list[tuple[str, str]]:
    """Split markdown into (title, body) chunks on ## headings."""
    text = (body or "").strip()
    if not text:
        return []
    parts = re.split(r"(?m)^(#{1,3}\s+.+)$", text)
    chunks: list[tuple[str, str]] = []
    if parts and parts[0].strip() and not parts[0].strip().startswith("#"):
        chunks.append((source.replace(".md", "").replace("_", " ").title(), parts[0].strip()))
    i = 1
    while i < len(parts):
        title = re.sub(r"^#+\s*", "", parts[i]).strip()
        body_part = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if body_part:
            chunks.append((title, body_part))
        i += 2
    if not chunks and text:
        chunks.append((source, text))
    return chunks


@lru_cache(maxsize=1)
def build_index() -> tuple[KnowledgeChunk, ...]:
    root = knowledge_dir()
    out: list[KnowledgeChunk] = []
    for name in KNOWLEDGE_FILES:
        path = root / name
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for idx, (title, body) in enumerate(_split_file(name, raw)):
            # Prefer smaller paragraphs inside a section
            paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
            if not paras:
                paras = [body]
            for j, para in enumerate(paras):
                if len(para) < 24:
                    continue
                blob = f"{title}\n{para}".strip()
                toks = frozenset(t for t in _tokenize(blob) if t not in _STOP)
                out.append(
                    KnowledgeChunk(
                        id=f"{name}:{idx}:{j}",
                        source=name,
                        title=title,
                        text=blob[:1200],
                        tokens=toks,
                    )
                )
    return tuple(out)


def _idf(df: int, n: int) -> float:
    return math.log(1.0 + (n - df + 0.5) / (df + 0.5))


def retrieve_chunks(
    question: str,
    *,
    top_k: int = 5,
    max_chars: int = 2200,
) -> list[KnowledgeChunk]:
    """Return top relevant client-facing knowledge chunks for the question."""
    q = _query_tokens(question)
    if not q:
        return []
    index = build_index()
    n = len(index) or 1
    # document frequency
    df: dict[str, int] = {}
    for ch in index:
        for t in ch.tokens:
            if t in q:
                df[t] = df.get(t, 0) + 1

    price_ask = bool(_PRICE_ASK.search(question or ""))
    q_lower = (question or "").lower()
    wants_milan = "milan" in q_lower
    wants_v3 = bool(re.search(r"(?i)\b(v3|live\s+guide|live\s+session)\b", question or ""))
    wants_pack = bool(
        re.search(r"(?i)\b(pack|starter|popular|power|sasta|cheapest)\b", question or "")
    ) and not wants_v3
    wants_wallet = bool(
        re.search(
            r"(?i)\b(wallet|transactions?|paise kahan|payments? show|payment kahan|dikhe)\b",
            question or "",
        )
    )
    wants_where_pdf = bool(
        re.search(r"(?i)\b(where|kahan|milega)\b", question or "")
        and re.search(r"(?i)\b(pdf|report)\b", question or "")
        and not price_ask
    )
    wants_language = bool(re.search(r"(?i)\b(language|lang)\b", question or ""))
    wants_career1 = bool(re.search(r"(?i)\bcareer\b", question or "") and re.search(r"(?i)\b(1|₹1|rupee|unlock)\b", question or ""))
    wants_birth_edit = bool(
        re.search(r"(?i)\b(galat|wrong|edit|daal)\b", question or "")
        and re.search(r"(?i)\b(birth|time|kundli)\b", question or "")
        and "rectif" not in q_lower
    )
    wants_help_vs_ask = bool(
        re.search(r"(?i)\bhelp\b", question or "") and re.search(r"(?i)\b(ask|farq|difference)\b", question or "")
    )
    wants_numero = "numerology" in q_lower
    wants_love = bool(re.search(r"(?i)\blove\s+reality|love reality\b", question or ""))
    wants_palm = bool(re.search(r"(?i)\bpalm", question or ""))
    wants_btr = bool(re.search(r"(?i)\brectif", question or ""))
    wants_biz_vastu = bool(re.search(r"(?i)\bbusiness\s+vastu|\bshop\b", question or "") and re.search(r"(?i)vastu|shop", question or ""))
    wants_forecast = bool(re.search(r"(?i)\b(forecast|7\s*day|7-day)\b", question or ""))
    v3_howto = wants_v3 and bool(re.search(r"(?i)\b(book|kaise|queue|miss|accept)\b", question or "")) and not price_ask

    scored: list[tuple[float, KnowledgeChunk]] = []
    for ch in index:
        score = 0.0
        overlap = ch.tokens.intersection(q)
        if not overlap:
            continue
        for t in overlap:
            score += _idf(df.get(t, 1), n)
        # Title hit boost
        title_toks = set(_tokenize(ch.title))
        title_l = (ch.title or "").lower()
        score += 1.5 * len(title_toks.intersection(q))
        # Source filename hint
        src = ch.source.replace(".md", "").replace("_", " ")
        score += 0.8 * len(set(_tokenize(src)).intersection(q))

        # Price questions: prefer ₹ / "prices" chunks; demote pure how-to
        if price_ask:
            has_rupee = "₹" in (ch.text or "") or "rs" in (ch.text or "").lower()
            if has_rupee or "price" in title_l:
                score += 3.2
            if "how it works" in title_l or title_l.endswith("what it is"):
                score -= 2.5
            if wants_v3 and ch.source == "ask_packs.md" and "v3" in title_l and "price" in title_l:
                score += 2.5
            if wants_pack and ch.source == "ask_packs.md" and "pack price" in title_l:
                score += 2.5
            if wants_milan and ch.source == "relationship.md" and "milan" in title_l:
                score += 3.0
            if wants_milan and "dosh" in title_l:
                score -= 4.0
            if wants_numero and ch.source == "numerology.md" and "pro" in title_l:
                score += 4.0
            if wants_love and ch.source == "relationship.md" and "love" in title_l:
                score += 4.0
            if wants_palm and ch.source == "vastu.md" and "palmistry pro" in title_l:
                score += 4.0
            if wants_btr and ch.source == "faq.md" and "rectif" in title_l:
                score += 4.5
            if wants_career1 and ch.source == "faq.md" and "career" in title_l and "₹1" in (ch.text or ""):
                score += 4.5
            if wants_career1 and "confirm prices" in title_l:
                score -= 4.0
            if wants_biz_vastu and ch.source == "vastu.md" and "business" in title_l:
                score += 4.0
            if (wants_numero or wants_love or wants_palm or wants_btr or wants_biz_vastu or wants_career1) and (
                ch.source == "ask_packs.md" and "pack price" in title_l
            ):
                score -= 5.0

        if wants_wallet and ch.source == "payments.md" and "wallet" in title_l:
            score += 5.0
        if wants_wallet and "processor" in title_l:
            score -= 4.0
        if wants_where_pdf and ch.source == "reports.md":
            score += 4.5
        if wants_where_pdf and "₹" in (ch.text or "") and ch.source == "relationship.md":
            score -= 4.0
        if wants_language and ch.source == "app.md" and "language" in title_l:
            score += 5.0
        if wants_language and "theme" in title_l:
            score -= 3.5
        if wants_birth_edit and ch.source == "faq.md" and "edit" in title_l:
            score += 5.0
        if wants_birth_edit and ch.source == "app.md" and "kundli and charts" in title_l:
            score -= 4.0
        if wants_help_vs_ask and ch.source == "app.md" and ("help vs ask" in title_l or "divya" in title_l):
            score += 5.0
        if wants_help_vs_ask and ch.source == "ask_packs.md":
            score -= 5.0
        if wants_forecast and "forecast" in title_l:
            score += 4.5
        if wants_forecast and "how today's energy works" in title_l:
            score -= 3.5
        if v3_howto and ch.source == "ask_packs.md" and "how it works" in title_l:
            score += 4.5
        if v3_howto and "price" in title_l:
            score -= 4.0
        if re.search(r"(?i)\b(logout|stuck|force-stop|force stop)\b", question or "") and "login" in title_l:
            score += 3.5

        scored.append((score, ch))

    scored.sort(key=lambda x: (-x[0], x[1].id))
    picked: list[KnowledgeChunk] = []
    used = 0
    for score, ch in scored:
        if score <= 0:
            continue
        if used + len(ch.text) > max_chars and picked:
            break
        picked.append(ch)
        used += len(ch.text)
        if len(picked) >= top_k:
            break
    return picked


def format_retrieved(chunks: Iterable[KnowledgeChunk]) -> str:
    blocks: list[str] = []
    for i, ch in enumerate(chunks, 1):
        blocks.append(f"[{i}] ({ch.source} · {ch.title})\n{ch.text}")
    return "\n\n".join(blocks)


def clear_index_cache() -> None:
    build_index.cache_clear()
