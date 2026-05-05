"""Phase 2.10.7 — Stock reply builder (3 modes).

Modes:
  - WARNING   -> locked template (0 LLM tokens)
  - DIRECT    -> format engine facts as Hinglish text (0 LLM tokens)
  - NARRATIVE -> engine facts + 60-80w LLM polish (cached after first call)

Public:
  handle_finance_question(question, kundli, birth) -> dict | None
    Returns { 'text', 'mode', 'route', 'verdict', 'cache_hit', 'engine_facts' }
    or None if question is not a stock/finance question.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from finance.stock_facts import compute_stock_facts, STOCK_SECTOR_MAP
from finance.stock_routing import is_stock_question, route_stock_question
from finance.stock_warnings import WARNINGS
from finance.answer_cache import make_cache_key, get_cached, put_cached


# ── DIRECT formatters (pure engine, no LLM) ─────────────────────────
_VERDICT_HINGLISH = {
    "GREEN_GO":     "🟢 GREEN — Stock market aapke liye favourable hai",
    "YELLOW_WAIT":  "🟡 YELLOW — Mixed yog, soch-samajh ke",
    "RED_AVOID":    "🔴 RED — Abhi avoid karo, chart support nahi",
}


_PATH_EMOJI = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴"}
_PATH_LABEL = {
    "GREEN":  "GREEN — Cautious GO",
    "YELLOW": "YELLOW — Mixed, disciplined only",
    "RED":    "RED — Avoid",
}

# P7: One-line takeaway based on (trading, longterm) verdict tuple
_SPLIT_FINAL = {
    ("GREEN",  "GREEN"):  "Trading aur long-term dono favourable — disciplined approach se profit possible.",
    ("GREEN",  "YELLOW"): "Trading achha, par long-term me selective rehna — mixed signals.",
    ("YELLOW", "GREEN"):  "Long-term investing strong, trading sirf disciplined size me.",
    ("YELLOW", "YELLOW"): "Dono paths me caution — small SIP + minimal trading.",
    ("RED",    "GREEN"):  "Trading se loss-prone, lekin long-term SIP / index se profit possible.",
    ("RED",    "YELLOW"): "Trading se loss hoga, lekin disciplined long-term investing se dheere profit possible hai.",
    ("RED",    "RED"):    "Stocks abhi nahi — chart neither trading na long-term ko support karta. SIP minimum, baaki avoid.",
    ("YELLOW", "RED"):    "Trading possible par long-term me leak — short hold prefer.",
    ("GREEN",  "RED"):    "Sirf disciplined trading — long-term hold me leak risk.",
}


def _direct_verdict_only(facts: dict) -> str:
    score = facts.get("score", 0)
    yogas = facts.get("wealth_yogas") or []
    afflic = facts.get("afflictions") or []

    v_trade = facts.get("verdict_trading", "")
    v_long  = facts.get("verdict_longterm", "")
    r_trade = facts.get("verdict_trading_reason", "")
    r_long  = facts.get("verdict_longterm_reason", "")

    lines = ["📊 Path-wise verdict (chart se):"]
    lines.append(
        f"  • Trading / Speculation: {_PATH_EMOJI.get(v_trade,'')} "
        f"{_PATH_LABEL.get(v_trade, v_trade)}"
    )
    if r_trade:
        lines.append(f"      └ {r_trade}")
    lines.append(
        f"  • Long-term Investing:   {_PATH_EMOJI.get(v_long,'')} "
        f"{_PATH_LABEL.get(v_long, v_long)}"
    )
    if r_long:
        lines.append(f"      └ {r_long}")

    lines.append(f"\nComposite score: {score}/15")

    # KP 5th-CSL line
    kp = facts.get("kp_5th_csl")
    if kp and isinstance(kp, dict):
        _kp_e = {"GREEN": "🟢", "AMBER": "🟡",
                  "NEUTRAL": "⚪", "RED": "🔴"}.get(kp.get("verdict", ""), "")
        lines.append(
            f"KP 5th-CSL ({kp.get('csl_planet','?')}): "
            f"{_kp_e} {kp.get('verdict','?')} "
            f"(weight {kp.get('score_weight',0):+d})"
        )

    if yogas:
        # P7: explicit recovery-yog tag for Vipreet-Rajyoga
        tagged = []
        for y in yogas:
            if y == "Vipreet-Raja":
                tagged.append(f"{y} (recovery yog)")
            else:
                tagged.append(y)
        lines.append(f"Wealth yogas: {', '.join(tagged)}")

    if afflic:
        lines.append(f"Afflictions ({len(afflic)}):")
        for a in afflic[:3]:
            lines.append(f"  • {a}")

    # Final one-line takeaway from split-verdict matrix
    final = _SPLIT_FINAL.get((v_trade, v_long))
    if final:
        lines.append(f"\n💡 Final: {final}")
    return "\n".join(lines)


def _direct_top_dhana_karakas(facts: dict) -> str:
    karakas = facts.get("karakas") or {}
    # Rank dhana karakas by dignity score
    rank = []
    for k in ("Jupiter", "Venus", "Mercury", "Moon", "Mars", "Saturn"):
        kd = karakas.get(k, {})
        if not kd:
            continue
        rank.append({
            "planet": k,
            "dignity": kd.get("dignity", "unknown"),
            "house": kd.get("house"),
            "retro": kd.get("retro"),
        })

    lines = ["💰 Aapki kundli ke top dhana karakas (wealth planets):"]
    score_map = {"exalted": 3, "own": 2, "friend": 1, "neutral": 0,
                 "enemy": -1, "debilitated": -2}
    rank.sort(key=lambda r: score_map.get(r["dignity"], -3), reverse=True)
    for i, r in enumerate(rank[:5], 1):
        retro = " (retro)" if r["retro"] else ""
        lines.append(f"  {i}. {r['planet']} — {r['dignity']}, "
                      f"H{r['house']}{retro}")

    top = rank[0] if rank else None
    if top:
        lines.append(f"\nFinal: Aapka strongest wealth-planet "
                      f"{top['planet']} hai ({top['dignity']}).")
    return "\n".join(lines)


def _direct_h5_h8_strength(facts: dict) -> str:
    sav = facts.get("sav") or {}
    sav_avail = facts.get("sav_available")
    occ = facts.get("house_occupants") or {}
    lords = facts.get("house_lords") or {}

    lines = ["📊 H5 (speculation) aur H8 (sudden gains) ki strength:"]
    for hn, role in [(5, "Speculation, share market, sudden gains"),
                      (8, "Sudden gains/losses, others' money"),
                      (11, "Profits, all gains")]:
        h = lords.get(f"h{hn}", {})
        sav_str = ""
        if sav_avail and sav.get(hn):
            band = ("VERY STRONG" if sav[hn] >= 32 else
                    "STRONG" if sav[hn] >= 28 else
                    "AVERAGE" if sav[hn] >= 25 else "WEAK")
            sav_str = f" | SAV={sav[hn]} ({band})"
        occupants = occ.get(str(hn)) or []
        occ_str = f", planets here: {', '.join(occupants)}" if occupants else ", empty"
        lines.append(f"  H{hn} ({role})")
        lines.append(f"    Lord: {h.get('lord','?')} in H{h.get('lord_house','?')} "
                      f"({h.get('lord_dignity','?')}){sav_str}{occ_str}")

    verdict = facts.get("verdict", "")
    lines.append(f"\nFinal: H5/H8 ke hisaab se overall verdict = "
                  f"{_VERDICT_HINGLISH.get(verdict, verdict)}")
    return "\n".join(lines)


def _direct_speculation_yogas(facts: dict) -> str:
    yogas = facts.get("wealth_yogas") or []
    sub = facts.get("sub_flags") or {}
    lines = ["🎰 Speculative gains check:"]
    if yogas:
        lines.append(f"  Wealth yogas present: {', '.join(yogas)}")
    else:
        lines.append("  Koi major wealth-yoga active nahi mila.")

    if sub.get("speculation_ok"):
        lines.append("  ✅ Speculation favourable yog hai (H5 + Rahu placement OK)")
        verdict = "Speculation thodi-bahut allowed hai (chart supports)."
    else:
        lines.append("  ❌ Speculation favourable nahi (H5 weak ya Rahu wrong house)")
        verdict = "Speculative gains aapki kundli me LIMITED hain."

    if sub.get("crypto_warning"):
        lines.append("  ⚠️ Crypto/F&O ke liye warning (Rahu in H8/H12)")

    lines.append(f"\nFinal: {verdict}")
    return "\n".join(lines)


def _direct_next_dasha_money(facts: dict) -> str:
    cd = facts.get("current_dasha") or {}
    lines = ["📅 Current dasha ka financial impact:"]
    for level, key in [("Mahadasha", "md"), ("Antardasha", "ad"),
                        ("Pratyantardasha", "pd")]:
        lord = cd.get(key, "?")
        money_link = cd.get(f"{key}_money_link")
        bad_link = cd.get(f"{key}_dusthana_link")
        money_r = cd.get(f"{key}_money_reasons") or []
        bad_r = cd.get(f"{key}_dusthana_reasons") or []
        sym = "✅" if money_link and not bad_link else (
            "⚠️" if bad_link else "—")
        reasons = []
        if money_r:
            reasons.append("money: " + ", ".join(money_r))
        if bad_r:
            reasons.append("dusthana: " + ", ".join(bad_r))
        rstr = f" ({'; '.join(reasons)})" if reasons else ""
        lines.append(f"  {sym} {level}: {lord}{rstr}")

    md_ok = cd.get("md_money_link") and not cd.get("md_dusthana_link")
    ad_ok = cd.get("ad_money_link") and not cd.get("ad_dusthana_link")
    if md_ok and ad_ok:
        verdict = "Current dasha financially favourable hai."
    elif md_ok or ad_ok:
        verdict = "Current dasha mixed hai — sambhal ke."
    else:
        verdict = "Current dasha financially weak hai."
    lines.append(f"\nFinal: {verdict}")
    return "\n".join(lines)


_DIRECT_FORMATTERS = {
    "verdict_only":       _direct_verdict_only,
    "top_dhana_karakas":  _direct_top_dhana_karakas,
    "h5_h8_strength":     _direct_h5_h8_strength,
    "speculation_yogas":  _direct_speculation_yogas,
    "next_dasha_money":   _direct_next_dasha_money,
}


# ── NARRATIVE: build engine fact pack for LLM (lean) ────────────────
def _build_llm_fact_block(facts: dict, route: str) -> str:
    """Compact facts block for LLM. <500 tokens."""
    # P7: Split verdicts shown FIRST + in plain words, composite hidden.
    # Engine codes (RED_AVOID etc) intentionally not exposed — user-flagged
    # leak source.
    _path_word = {"GREEN": "favourable", "YELLOW": "mixed/cautious",
                   "RED": "avoid"}
    vt = facts.get("verdict_trading", "?")
    vl = facts.get("verdict_longterm", "?")
    lines = [
        "═══════════════════════════════════════════════",
        "🔒 STOCK ENGINE — LOCKED FACTS (do not invent)",
        "═══════════════════════════════════════════════",
        f"TRADING path: {vt} ({_path_word.get(vt,'?')}) — "
        f"{facts.get('verdict_trading_reason','')}",
        f"LONG-TERM path: {vl} ({_path_word.get(vl,'?')}) — "
        f"{facts.get('verdict_longterm_reason','')}",
        f"Sub-flags: {facts.get('sub_flags',{})}",
        "",
    ]

    # House lords summary
    lords = facts.get("house_lords") or {}
    for hn in (2, 5, 8, 11, 12):
        h = lords.get(f"h{hn}", {})
        if not h:
            continue
        lines.append(f"H{hn}: lord={h.get('lord')} in H{h.get('lord_house')} "
                      f"({h.get('lord_dignity')})")

    # Karakas key only
    karakas = facts.get("karakas") or {}
    for k in ("Jupiter", "Venus", "Mercury", "Mars", "Saturn", "Rahu"):
        kd = karakas.get(k)
        if not kd:
            continue
        lines.append(f"{k}: H{kd.get('house')} {kd.get('sign')} "
                      f"({kd.get('dignity')})"
                      f"{' retro' if kd.get('retro') else ''}"
                      f"{' combust' if kd.get('combust') else ''}")

    # Yogas
    yogas = facts.get("wealth_yogas") or []
    lines.append(f"Wealth yogas: {', '.join(yogas) if yogas else 'NONE'}")

    # Dasha link
    cd = facts.get("current_dasha") or {}
    lines.append(f"Current MD-AD: {cd.get('md')}-{cd.get('ad')} "
                  f"(money_link={cd.get('md_money_link')}/{cd.get('ad_money_link')}, "
                  f"dusthana_link={cd.get('md_dusthana_link')}/{cd.get('ad_dusthana_link')})")

    # Afflictions
    afflic = facts.get("afflictions") or []
    if afflic:
        lines.append(f"Afflictions ({len(afflic)}):")
        for a in afflic[:5]:
            lines.append(f"  - {a}")

    # Top sectors (only for sector_recommendation route)
    if route == "sector_recommendation":
        top_sectors = facts.get("top3_sectors") or []
        if top_sectors:
            lines.append("Top sectors (by strongest planets):")
            for ts in top_sectors:
                lines.append(f"  {ts['planet']}: "
                              f"{', '.join(ts['sectors'][:4])}")

    lines.append("═══════════════════════════════════════════════")
    return "\n".join(lines)


# Map route -> per-question instruction for the LLM
_NARRATIVE_INSTRUCTIONS = {
    "leak_facts": (
        "User question: 'Paisa tikta nahi / aata par rukta nahi'. "
        "Use H2 lord state, H12 lord active dasha, leak/wealth-leak "
        "afflictions to explain WHY money isn't holding. "
        "60-80 words Hinglish. End with 'Final: <one-line>'."
    ),
    "trading_vs_longterm": (
        "User asking 'trading karu ya long-term?'. "
        "REQUIRED FORMAT (exactly):\n"
        "Line 1: '• Trading: <emoji> <one-phrase verdict>'\n"
        "Line 2: '• Long-term investing: <emoji> <one-phrase verdict>'\n"
        "Line 3: blank\n"
        "Line 4: ONE short sentence (max 20 words) explaining WHY one "
        "is better than the other — in everyday Hinglish, NO planet "
        "names, NO house numbers, NO dignity words.\n"
        "Line 5: 'Final: <one clean Hinglish line that gives the user "
        "a concrete decision>'.\n"
        "Emojis: 🟢 GREEN / 🟡 YELLOW / 🔴 RED based on TRADING path "
        "and LONG-TERM path verdicts above."
    ),
    "risk_capacity": (
        "User asking about risk capacity. Use H5 dignity + Rahu placement "
        "+ speculation_ok flag. State clearly: low/medium/high risk capacity. "
        "60-80 words Hinglish. End with 'Final: <one-line>'."
    ),
    "loss_reasons": (
        "User asking why repeated losses. List specific afflictions "
        "(8L position, 12L active, malefics on H2/H5/H11). "
        "60-80 words Hinglish. End with 'Final: <one-line>'."
    ),
    "blockage_check": (
        "User asking financial blockage hai kya. Use blockage_present + "
        "leak_present flags + specific afflictions. Yes/No clearly. "
        "60-80 words Hinglish. End with 'Final: <one-line>'."
    ),
    "intraday_check": (
        "User asking about intraday trading. Use intraday_warning flag + "
        "Mercury/Mars/H11 state. Recommend Yes/No clearly. "
        "60-80 words Hinglish. End with 'Final: <one-line>'."
    ),
    "loss_planets": (
        "User asking which planet causing losses. Identify malefics on "
        "H2/H5/H11 from afflictions list. Name 1-2 specific planets. "
        "60-80 words Hinglish. End with 'Final: <one-line>'."
    ),
    "rich_potential": (
        "User asking can I become rich from market. Use wealth_yogas "
        "count + dasha + verdict. Honest assessment. "
        "60-80 words Hinglish. End with 'Final: <one-line>'."
    ),
    "sector_recommendation": (
        "User asking which sector. Recommend top 2-3 sectors from "
        "top3_sectors mapping (use planet→sector list). "
        "60-80 words Hinglish. End with 'Final: <one-line>'."
    ),
    "business_plus_market": (
        "User asking business + market dono karna chahiye. Use H10 "
        "(career) state plus money houses. Honest yes/no/one-only. "
        "60-80 words Hinglish. End with 'Final: <one-line>'."
    ),
    "fulltime_trader": (
        "User asking should I become full-time trader. Use H10 + H5 + "
        "H11 + sub_flags.trading_ok. Honest yes/no with conditions. "
        "60-80 words Hinglish. End with 'Final: <one-line>'."
    ),
    "rahu_trading": (
        "User asking if Rahu strong helps trading. Use Rahu's actual "
        "house+dignity from karakas. Specific to THIS chart. "
        "60-80 words Hinglish. End with 'Final: <one-line>'."
    ),
}


def _llm_narrative(facts: dict, route: str, question: str) -> str:
    """Call LLM with engine facts. Returns narrative text."""
    try:
        # Lazy import to avoid circular import
        import openai_helper  # type: ignore
        client = openai_helper._get_client()
        if client is None:
            return _direct_verdict_only(facts)
    except Exception:
        return _direct_verdict_only(facts)

    fact_block = _build_llm_fact_block(facts, route)
    instruction = _NARRATIVE_INSTRUCTIONS.get(
        route, "Summarise the engine verdict in 60-80 words Hinglish. "
               "End with 'Final: <one-line>'.")

    sys_prompt = (
        "You are a Vedic astrology stock-market translator.\n\n"
        "RULES:\n"
        "1. Use ONLY the LOCKED FACTS below. Never invent planets, "
        "houses, dignities, or yogas not listed.\n"
        "2. Reply in Hinglish, friendly and direct.\n"
        "3. End with a line starting 'Final: '.\n"
        "4. No 'Beta', 'Pranam', 'I sense', 'I understand'.\n"
        "5. NEVER write engine codes like 'RED_AVOID', 'YELLOW_WAIT', "
        "'GREEN_GO', 'verdict', 'score X/15', 'sub_flags', or any "
        "internal label. User-facing language only.\n"
        "6. NEVER mention specific planets, houses, signs, dignities "
        "(Saturn, Mars, Mercury, H2, Capricorn, debilitated, retro, "
        "Jupiter etc.) UNLESS the user explicitly asked WHY / "
        "technical detail / planet name in their question. Default "
        "= keep it human.\n"
        "7. Follow the per-route format EXACTLY.\n\n"
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
            return _direct_verdict_only(facts)
        return text
    except Exception as e:
        print(f"[finance.llm] narrative call failed: {e}", flush=True)
        return _direct_verdict_only(facts)


import os  # noqa: E402  (used in _llm_narrative)


# ── Public entry point ──────────────────────────────────────────────
def handle_finance_question(question: str, kundli: dict,
                              birth: dict | None = None) -> Optional[Dict[str, Any]]:
    """Route + serve a finance/stock question.

    Returns None if not a stock question (caller should fall through to
    normal pipeline).
    """
    if not is_stock_question(question or ""):
        return None
    if not isinstance(kundli, dict) or not kundli.get("planets"):
        return {
            "text": ("Beta, stock/finance ka analysis aapki janm-kundli "
                      "ke bina possible nahi. Pehle birth details save karein.\n\n"
                      "Final: Pehle kundli, fir stock analysis."),
            "mode": "FAILSAFE", "route": "no_kundli",
            "verdict": None, "cache_hit": False, "engine_facts": None,
        }

    mode, route = route_stock_question(question)

    # WARNING mode — locked, no engine, no LLM, no cache (always same)
    if mode == "WARNING":
        text = WARNINGS.get(route, "")
        return {
            "text": text, "mode": mode, "route": route,
            "verdict": None, "cache_hit": False, "engine_facts": None,
        }

    # Cache check (DIRECT and NARRATIVE)
    cache_key = make_cache_key(birth, kundli, "stock", route)
    cached = get_cached(cache_key)
    if cached:
        return {
            "text": cached["text"], "mode": mode, "route": route,
            "verdict": cached.get("meta", {}).get("verdict"),
            "cache_hit": True, "engine_facts": None,
        }

    # Compute engine facts (deterministic, free)
    facts = compute_stock_facts(kundli)
    if facts.get("error"):
        return {
            "text": f"Engine error: {facts['error']}\n\nFinal: Kundli check karein.",
            "mode": "FAILSAFE", "route": route,
            "verdict": None, "cache_hit": False, "engine_facts": facts,
        }

    if mode == "DIRECT":
        formatter = _DIRECT_FORMATTERS.get(route, _direct_verdict_only)
        text = formatter(facts)
    else:  # NARRATIVE
        text = _llm_narrative(facts, route, question)

    # Save to cache
    put_cached(cache_key, text, {"verdict": facts.get("verdict"),
                                  "score": facts.get("score"),
                                  "mode": mode, "route": route})

    return {
        "text": text, "mode": mode, "route": route,
        "verdict": facts.get("verdict"), "cache_hit": False,
        "engine_facts": facts,
    }
