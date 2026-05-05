"""Finance reply builder (3 modes).

Modes:
  - WARNING   -> locked template (0 LLM tokens)
  - DIRECT    -> format engine facts as Hinglish text (0 LLM tokens)
  - NARRATIVE -> engine facts + 60-80w LLM polish (cached after first call)

Public:
  handle_finance_money_question(question, kundli, birth) -> dict | None
    Returns { 'text', 'mode', 'route', 'scope', 'dimensions',
              'cache_hit', 'engine_facts' } or None if not finance Q.
"""
from __future__ import annotations
import os
from typing import Any, Dict, Optional

from finance_engine.finance_facts import compute_finance_facts
from finance_engine.finance_routing import (is_finance_question,
                                              route_finance_question)
from finance_engine.finance_warnings import WARNINGS
from finance_engine.answer_cache import make_cache_key, get_cached, put_cached


_PATH_EMOJI = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴"}
_DIM_LABEL = {
    "wealth_potential": "Wealth potential",
    "income_stability": "Income stability",
    "saving_ability":   "Saving ability",
    "risk_leak":        "Risk / leak",
}
# FIX (architect LOW): map engine codes to plain Hinglish for default
# DIRECT output. Project rule: no engine jargon unless explicitly asked.
_VERDICT_HINGLISH = {
    "GREEN":  "Strong",
    "YELLOW": "Mixed",
    "RED":    "Weak",
}
_TIER_HINGLISH = {
    "high":     "bharosa kar sakte ho",
    "moderate": "discipline ke saath OK",
    "low":      "kabhi-kabhi hi kaam karega",
    "none":     "abhi avoid karo",
}


# ── DIRECT formatters ──────────────────────────────────────────────
def _direct_wealth_verdict(facts: dict) -> str:
    dims = facts.get("dimensions") or {}
    yogas = facts.get("wealth_yogas") or []
    afflic = facts.get("afflictions") or []
    sub = facts.get("sub_flags") or {}

    lines = ["💰 Aapki finance picture (4 dimensions):"]
    for key in ("wealth_potential", "income_stability",
                 "saving_ability", "risk_leak"):
        d = dims.get(key) or {}
        v = d.get("verdict", "?")
        emoji = _PATH_EMOJI.get(v, "")
        tier = d.get("tier", "?")
        # Plain Hinglish; engine codes (GREEN/YELLOW/RED, tier names)
        # not exposed unless user explicitly asked technical detail.
        lines.append(f"  • {_DIM_LABEL[key]}: {emoji} "
                      f"{_VERDICT_HINGLISH.get(v, v)} — "
                      f"{_TIER_HINGLISH.get(tier, tier)}")
        if d.get("reason"):
            lines.append(f"      └ {d['reason']}")

    if yogas:
        lines.append(f"\nWealth yogas active: {', '.join(yogas)}")
    else:
        lines.append("\nKoi major dhan-yog active nahi mila.")

    if afflic:
        lines.append(f"\nDrain signals ({len(afflic)}):")
        for a in afflic[:3]:
            lines.append(f"  • {a}")

    # One-line takeaway from the dominant signal
    final = _wealth_one_liner(dims, sub)
    if final:
        lines.append(f"\n💡 Final: {final}")
    return "\n".join(lines)


def _wealth_one_liner(dims: dict, sub: dict) -> str:
    wp = dims.get("wealth_potential", {}).get("verdict", "")
    sa = dims.get("saving_ability", {}).get("verdict", "")
    rl = dims.get("risk_leak", {}).get("verdict", "")
    is_ = dims.get("income_stability", {}).get("verdict", "")
    if wp == "GREEN" and sa == "GREEN" and rl != "RED":
        return "Wealth banane aur tikane dono ki capacity strong — disciplined plan se rich potential real hai."
    if wp == "GREEN" and rl == "RED":
        return "Kamane ki capacity hai par leak active — pehle drain band karo, fir wealth banegi."
    if rl == "RED":
        return "Sabse pehle paisa nikalna band karo — wo pakda nahi to wealth nahi banegi."
    if sa == "RED":
        return "Saving discipline weak hai — automatic SIP/RD set karo, willpower pe mat chodo."
    if wp == "RED" and is_ == "GREEN":
        return "Income stable hai par mega-wealth ka yog limited — comfort possible, crorepati ka shortcut nahi."
    if wp == "RED":
        return "Mega-wealth ka chart-yog limited — earned income + saving discipline pe focus karo."
    return "Mixed picture — saving + leak control pehli priority, wealth uske baad."


def _direct_dhana_yoga_check(facts: dict) -> str:
    yogas = facts.get("wealth_yogas") or []
    sub = facts.get("sub_flags") or {}
    lines = ["✨ Dhana-yog audit (chart se):"]
    if yogas:
        for y in yogas:
            tag = " (recovery yog)" if y == "Vipreet-Raja" else ""
            lines.append(f"  ✓ {y}{tag}")
    else:
        lines.append("  Koi major dhan-yog active nahi.")

    missing = [y for y in ("Dhana", "Lakshmi", "Kubera", "Gaja-Kesari",
                            "Adhi", "Chandra-Mangal", "Vipreet-Raja")
               if y not in yogas]
    if missing:
        lines.append(f"\nNot active: {', '.join(missing)}")

    if sub.get("wealth_strong"):
        final = "Strong dhan-yog active hai — capacity real, ab discipline aur dasha sath de."
    elif yogas:
        final = "Kuch dhan-yog hain — par alone enough nahi, effort + planning chahiye."
    else:
        final = "Bina active dhan-yog ke wealth banegi to discipline + saving se, shortcut se nahi."
    lines.append(f"\n💡 Final: {final}")
    return "\n".join(lines)


def _direct_sudden_wealth(facts: dict) -> str:
    sub = facts.get("sub_flags") or {}
    yogas = facts.get("wealth_yogas") or []
    karakas = facts.get("karakas") or {}
    rahu_h = (karakas.get("Rahu") or {}).get("house")
    h8 = (facts.get("house_lords") or {}).get("h8") or {}

    lines = ["🎲 Sudden wealth check (windfall / inheritance / lottery yog):"]
    if sub.get("sudden_wealth_yog"):
        lines.append("  ✅ Sudden-wealth yog ka indication hai chart me")
    else:
        lines.append("  ❌ Strong sudden-wealth yog nahi mila")

    if "Vipreet-Raja" in yogas:
        lines.append("  + Vipreet-Rajyoga active — setback ke baad recovery yog")
    if h8.get("lord_house") in (1, 4, 7, 10):
        lines.append(f"  + H8 ka lord kendra (H{h8.get('lord_house')}) me hai")
    if rahu_h in (3, 6, 11):
        lines.append(f"  + Rahu upachaya house (H{rahu_h}) me hai — gain-house position")

    if sub.get("sudden_wealth_yog"):
        final = ("Possibility hai par lottery/satta nahi — inheritance, "
                 "unexpected gift, ya legal settlement type ka aa sakta. "
                 "Ticket pe paisa mat lagao.")
    else:
        final = ("Sudden wealth ka chart-support kam hai — earned income "
                 "pe focus karo, lottery/satta avoid.")
    lines.append(f"\n💡 Final: {final}")
    return "\n".join(lines)


_DIRECT_FORMATTERS = {
    "wealth_verdict":    _direct_wealth_verdict,
    "dhana_yoga_check":  _direct_dhana_yoga_check,
    "sudden_wealth":     _direct_sudden_wealth,
}


# ── NARRATIVE: build engine fact pack for LLM (lean) ────────────────
def _build_llm_fact_block(facts: dict, route: str) -> str:
    dims = facts.get("dimensions") or {}
    sub = facts.get("sub_flags") or {}
    lines = [
        "═══════════════════════════════════════════════",
        "🔒 FINANCE ENGINE — LOCKED FACTS (do not invent)",
        "═══════════════════════════════════════════════",
    ]
    for key in ("wealth_potential", "income_stability",
                 "saving_ability", "risk_leak"):
        d = dims.get(key) or {}
        lines.append(
            f"{_DIM_LABEL[key]}: {d.get('verdict','?')} "
            f"[reliability={d.get('tier','?')}] — {d.get('reason','')}"
        )
    lines.append(f"Sub-flags: {sub}")

    yogas = facts.get("wealth_yogas") or []
    lines.append(f"Wealth yogas: {', '.join(yogas) if yogas else 'NONE'}")

    cd = facts.get("current_dasha") or {}
    lines.append(f"Current MD-AD: {cd.get('md')}-{cd.get('ad')} "
                  f"(money_link={cd.get('md_money_link')}/{cd.get('ad_money_link')}, "
                  f"dusthana_link={cd.get('md_dusthana_link')}/{cd.get('ad_dusthana_link')})")

    afflic = facts.get("afflictions") or []
    if afflic:
        lines.append(f"Afflictions ({len(afflic)}):")
        for a in afflic[:5]:
            lines.append(f"  - {a}")

    lines.append("═══════════════════════════════════════════════")
    return "\n".join(lines)


_NARRATIVE_INSTRUCTIONS = {
    "saving_capacity": (
        "User asking 'saving kyun nahi hoti / kitni save hogi'. "
        "Use saving_ability dimension + leak signals + Saturn discipline. "
        "REQUIRED FORMAT (exactly):\n"
        "Line 1: 'Saving picture (chart se):'\n"
        "Line 2: '• Capacity: <one-phrase>'\n"
        "Line 3: '• Mukhya rukawat: <one-phrase>'\n"
        "Line 4: '• Practical fix: <one-phrase, automatic SIP / RD / "
        "expense audit etc>'\n"
        "Line 5: blank\n"
        "Line 6: 'Final: <one direct sentence in Hinglish>'.\n"
        "NO planet names, NO house numbers, NO dignity words."
    ),
    "expense_pattern": (
        "User asking 'kharcha control hoga ya nahi'. "
        "Use risk_leak + saving_ability dimensions + 12L active flag. "
        "REQUIRED FORMAT (exactly):\n"
        "Line 1: 'Kharcha pattern:'\n"
        "Line 2: '• Drain level: <one-phrase>'\n"
        "Line 3: '• Mukhya leak source: <one-phrase concrete behaviour>'\n"
        "Line 4: '• Sudhar plan: <one-phrase practical action>'\n"
        "Line 5: blank\n"
        "Line 6: 'Final: <one direct sentence>'.\n"
        "NO planet names, NO house numbers."
    ),
    "loan_debt": (
        "User asking about loan/debt — le sakta hu? clear kab hoga? "
        "Use H6 lord placement + saving_ability + risk_leak + dasha. "
        "Honest yes/no/conditional. 60-80 words Hinglish. Concrete "
        "action (budget audit, restructuring, prepay strategy). "
        "NO planet names, NO house numbers. End with 'Final: <one-line>'."
    ),
    "income_source": (
        "User asking which income source suits them — salary vs business "
        "vs trade vs teaching etc. Use income_affinity sub-flag list "
        "(top 2-3) + business_friendly flag + income_stability dim. "
        "60-80 words Hinglish. Recommend 1-2 concrete career flavours. "
        "NO planet names, NO house numbers, NO dignity words. "
        "End with 'Final: <one-line>'."
    ),
    "business_profit": (
        "User asking about business profit / partnership / startup. "
        "Use business_friendly flag + wealth_potential + income_stability "
        "+ H7 partnership angle. Honest yes/no with conditions. "
        "60-80 words Hinglish. NO planet names, NO house numbers. "
        "End with 'Final: <one-line>'."
    ),
    "loss_reasons": (
        "User asking 'paisa nahi tikta / ud jata / kharch ho jata'. "
        "CRITICAL: Convert chart signals into CONCRETE BEHAVIORAL "
        "MISTAKES. Do NOT say 'leak', 'H12', '8th lord', 'dusthana', "
        "'Rahu' — those are jargon. Translate into actions.\n\n"
        "MAPPING (use afflictions + sub_flags from facts):\n"
        "  - 12L active in dasha       → 'Wrong-time spending — "
        "                                  jab paisa aata hai, turant kharch'\n"
        "  - H2 lord weak/in dusthana  → 'Speech/contracts pe galat "
        "                                  decisions — wahan paisa nikalta'\n"
        "  - leak_active=True          → 'Profit hote hi reinvest "
        "                                  kar dete ho, hand me kuch nahi rukta'\n"
        "  - H6 lord on H2/H11         → 'EMI/loan ki bharti me income "
        "                                  ka bada hissa jata'\n"
        "  - Rahu on money house       → 'Showing-off / lifestyle "
        "                                  inflation — paisa dikhane me jata'\n\n"
        "REQUIRED FORMAT (exactly):\n"
        "Line 1: 'Paisa na tikne ke 3 main reasons (chart se):'\n"
        "Line 2: '1. <behavior 1 in Hinglish>'\n"
        "Line 3: '2. <behavior 2 in Hinglish>'\n"
        "Line 4: '3. <behavior 3 in Hinglish>'\n"
        "Line 5: blank\n"
        "Line 6: 'Final: <one direct sentence naming the 3 behaviors>'.\n\n"
        "NO planet names, NO house numbers, NO dignity words."
    ),
}


def _llm_narrative(facts: dict, route: str, question: str) -> str:
    try:
        import openai_helper  # type: ignore
        client = openai_helper._get_client()
        if client is None:
            return _direct_wealth_verdict(facts)
    except Exception:
        return _direct_wealth_verdict(facts)

    fact_block = _build_llm_fact_block(facts, route)
    instruction = _NARRATIVE_INSTRUCTIONS.get(
        route, "Summarise the engine multi-dim verdict in 60-80 words "
               "Hinglish. End with 'Final: <one-line>'.")

    sys_prompt = (
        "You are a Vedic astrology personal-finance translator.\n\n"
        "RULES:\n"
        "1. Use ONLY the LOCKED FACTS below. Never invent planets, "
        "houses, dignities, or yogas not listed.\n"
        "2. Reply in Hinglish, friendly and direct.\n"
        "3. End with a line starting 'Final: '.\n"
        "4. No 'Beta', 'Pranam', 'I sense', 'I understand'.\n"
        "5. NEVER write engine codes like 'RED', 'YELLOW', 'GREEN', "
        "'verdict', 'tier', 'sub_flags', 'composite_score', or any "
        "internal label. User-facing language only.\n"
        "6. NEVER mention specific planets, houses, signs, dignities "
        "(Saturn, Mars, Mercury, H2, Capricorn, debilitated, retro, "
        "Jupiter etc.) UNLESS the user explicitly asked WHY / "
        "technical detail / planet name in their question.\n"
        "7. NEVER predict exact rupee amounts or specific dates — "
        "this engine is NON-TIMING.\n"
        "8. Follow the per-route format EXACTLY.\n\n"
        f"{fact_block}\n\n"
        f"INSTRUCTION: {instruction}"
    )
    try:
        resp = client.chat.completions.create(
            model=os.environ.get("FINANCE_LLM_MODEL", "gpt-5.4"),
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": question},
            ],
            temperature=0.2,
            max_tokens=300,
        )
        text = (resp.choices[0].message.content or "").strip()
        if not text:
            return _direct_wealth_verdict(facts)
        return text
    except Exception as e:
        print(f"[finance_money.llm] narrative call failed: {e}", flush=True)
        return _direct_wealth_verdict(facts)


# ── Public entry point ──────────────────────────────────────────────
_ENGINE_SCOPE = "non_timing"


def handle_finance_money_question(question: str, kundli: dict,
                                    birth: dict | None = None
                                    ) -> Optional[Dict[str, Any]]:
    """Route + serve a NON-TIMING general finance/money question.

    Scope: WHAT / WHY / WHICH about wealth, income, saving, expense,
    loan, debt, business profit, sudden wealth, dhana yogas. Timing
    questions are NOT handled. Stock-market questions are NOT handled
    (those go to stock_engine).

    Returns None if not a finance question. Every non-None response
    carries scope='non_timing'.
    """
    if not is_finance_question(question or ""):
        return None
    if not isinstance(kundli, dict) or not kundli.get("planets"):
        return {
            "text": ("Beta, finance analysis aapki janm-kundli ke bina "
                      "possible nahi. Pehle birth details save karein.\n\n"
                      "Final: Pehle kundli, fir finance analysis."),
            "mode": "FAILSAFE", "route": "no_kundli",
            "scope": _ENGINE_SCOPE,
            "dimensions": None, "cache_hit": False, "engine_facts": None,
        }

    mode, route = route_finance_question(question)

    # WARNING mode — locked, no engine, no LLM, no cache
    if mode == "WARNING":
        text = WARNINGS.get(route, "")
        return {
            "text": text, "mode": mode, "route": route,
            "scope": _ENGINE_SCOPE,
            "dimensions": None, "cache_hit": False, "engine_facts": None,
        }

    # Cache check
    cache_key = make_cache_key(birth, kundli, "finance_money", route)
    cached = get_cached(cache_key)
    if cached:
        return {
            "text": cached["text"], "mode": mode, "route": route,
            "scope": _ENGINE_SCOPE,
            "dimensions": cached.get("meta", {}).get("dimensions"),
            "cache_hit": True, "engine_facts": None,
        }

    # Compute facts
    facts = compute_finance_facts(kundli)
    if facts.get("error"):
        return {
            "text": f"Engine error: {facts['error']}\n\nFinal: Kundli check karein.",
            "mode": "FAILSAFE", "route": route,
            "scope": _ENGINE_SCOPE,
            "dimensions": None, "cache_hit": False, "engine_facts": facts,
        }

    if mode == "DIRECT":
        formatter = _DIRECT_FORMATTERS.get(route, _direct_wealth_verdict)
        text = formatter(facts)
    else:
        text = _llm_narrative(facts, route, question)

    put_cached(cache_key, text, {
        "dimensions": facts.get("dimensions"),
        "composite": facts.get("composite_score"),
        "mode": mode, "route": route,
    })

    return {
        "text": text, "mode": mode, "route": route,
        "scope": _ENGINE_SCOPE,
        "dimensions": facts.get("dimensions"),
        "cache_hit": False, "engine_facts": facts,
    }
