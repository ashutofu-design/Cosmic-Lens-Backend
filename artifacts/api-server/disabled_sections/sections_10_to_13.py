def _section_arudha(kundli: dict, lagna_sign_idx: Optional[int]) -> str:
    if lagna_sign_idx is None:
        return ""
    try:
        from jaimini import compute_arudha_padas  # type: ignore
    except Exception:
        return ""

    planets = kundli.get("planets") or []
    if not planets:
        return ""

    # jaimini.compute_arudha_padas requires English sign names. Derive
    # canonical English from lagna_sign_idx instead of relying on the
    # caller's possibly-Hinglish `ascendant`/`lagna` field.
    try:
        lagna_en = _ENGLISH_SIGNS[int(lagna_sign_idx) % 12]
    except (TypeError, ValueError, IndexError):
        return ""

    try:
        result = compute_arudha_padas(planets, lagna_en)
    except Exception:
        return ""

    padas = (result or {}).get("padas") or {}
    if not padas:
        return ""

    show = [
        ("A1",  "AL — public image / how world sees native"),
        ("A7",  "perception of spouse / partnerships"),
        ("A10", "career image / public reputation"),
        ("A12", "UL — marriage / long-term commitment signature"),
    ]

    lines = ["## 10. ARUDHA PADAS (Image / Perception layer — Jaimini)"]
    for key, label in show:
        p = padas.get(key)
        if not isinstance(p, dict):
            continue
        sign_hi = _sign_name(p.get("sign"))
        lord = p.get("lord", "?")
        lord_in_hi = _sign_name(p.get("lord_in"))
        note = p.get("note") or ""
        note_str = f"  [{note}]" if note else ""
        lines.append(
            f"  \u2022 {key} ({label}): {sign_hi}, lord {lord} in "
            f"{lord_in_hi}{note_str}"
        )

    if len(lines) == 1:
        return ""

    lines.append("")
    lines.append("ARUDHA READING RULE:")
    lines.append(
        "  \u2022 Arudha = how world PERCEIVES that life area "
        "(vs natal house = inner reality)."
    )
    lines.append(
        "  \u2022 AL different from Lagna sign \u2192 outer image vs "
        "inner self can mismatch."
    )
    lines.append(
        "  \u2022 Planets in / aspecting an Arudha sign colour the "
        "perception of that life area."
    )

    return "\n".join(lines)


# ────────────────────────────────────────────────────────────────────
# Section 11 — ASHTAKAVARGA  (Item #27)
# SAV (Sarvashtakavarga) per house with strength verdicts. Reuses the
# existing ashtakavarga.compute_ashtakavarga + format_sav_summary so
# the BPHS contribution tables stay centralised in one module.
# ────────────────────────────────────────────────────────────────────
def _section_ashtakavarga(kundli: dict, lagna_sign_idx: Optional[int]) -> str:
    if lagna_sign_idx is None:
        return ""
    try:
        from ashtakavarga import (  # type: ignore
            compute_ashtakavarga,
            format_sav_summary,
        )
    except Exception:
        return ""

    planets = kundli.get("planets") or []
    if not planets:
        return ""

    try:
        av = compute_ashtakavarga(planets, lagna_sign_idx)
    except Exception:
        return ""
    if not av or "sav" not in av:
        return ""

    try:
        summary = format_sav_summary(av)
    except Exception:
        return ""
    if not summary:
        return ""

    lines = ["## 11. ASHTAKAVARGA (Point-system house strength — BPHS)"]
    lines.append(summary)
    lines.append("")
    lines.append("ASHTAKAVARGA READING RULE:")
    lines.append(
        "  \u2022 SAV per house = total bindus contributed by all 7 "
        "planets (max ~56, avg ~28). Total across 12 houses = 337."
    )
    lines.append(
        "  \u2022 Bands: 32+ VERY STRONG (effortless), 28-31 STRONG "
        "(reliable delivery), 25-27 AVERAGE (mixed/conditional), "
        "<25 WEAK (struggles, remedies indicated)."
    )
    lines.append(
        "  \u2022 Strong house \u2192 affairs of that bhava fructify with "
        "less obstruction during relevant dasha/transit; weak house "
        "\u2192 native struggles even with promising dasha lord."
    )
    lines.append(
        "  \u2022 Cross-check: an event-trigger transit through a HIGH-SAV "
        "house gives stronger results than the same transit through a LOW-SAV house."
    )

    return "\n".join(lines)


# ────────────────────────────────────────────────────────────────────
# Section 12 — SHADBALA  (Item #28)
# Per-planet 6-fold quantitative strength (in virupas). Sorts by
# strength% so LLM sees strongest \u2192 weakest at a glance. Highlights
# any planet below required minimum.
# ────────────────────────────────────────────────────────────────────
def _section_shadbala(kundli: dict, lagna_sign_idx: Optional[int]) -> str:
    if lagna_sign_idx is None:
        return ""
    try:
        from shadbala import compute_shadbala  # type: ignore
    except Exception:
        return ""

    planets = kundli.get("planets") or []
    if not planets:
        return ""

    # Normalise planet dicts for compute_shadbala which expects keys
    # `lon` and `house`. Our chart payload uses `longitude` for the
    # absolute ecliptic longitude, so map it across (without mutating
    # the caller's list).
    norm_planets: list[dict] = []
    for p in planets:
        if not isinstance(p, dict):
            continue
        np = dict(p)  # shallow copy — safe to add `lon`
        if "lon" not in np and isinstance(np.get("longitude"), (int, float)):
            np["lon"] = float(np["longitude"])
        norm_planets.append(np)

    try:
        sb = compute_shadbala(norm_planets, lagna_sign_idx)
    except Exception:
        return ""
    if not isinstance(sb, dict) or not sb:
        return ""

    # Sort planets by strength_pct desc (strongest first)
    rows: list[tuple[str, float, float, float]] = []
    for name, data in sb.items():
        if not isinstance(data, dict):
            continue
        try:
            total = float(data.get("total") or 0)
            req = float(data.get("required") or 0)
            pct = float(data.get("strength_pct") or 0)
        except (TypeError, ValueError):
            continue
        rows.append((name, total, req, pct))
    if not rows:
        return ""

    rows.sort(key=lambda r: r[3], reverse=True)

    lines = ["## 12. SHADBALA (Quantitative planet strength — 6-fold, in virupas)"]
    lines.append("  Planet  | Total  | Required | Str%   | Verdict")
    for name, total, req, pct in rows:
        if pct >= 100:
            verdict = "STRONG (meets minimum)"
        elif pct >= 80:
            verdict = "ADEQUATE (near minimum)"
        else:
            verdict = "WEAK (below minimum)"
        lines.append(
            f"  {name:<7} | {total:6.1f} | {req:8.1f} | {pct:5.1f}% | {verdict}"
        )

    weakest = [n for n, _, _, p in rows if p < 80]
    strongest = [n for n, _, _, p in rows if p >= 100]
    if strongest:
        lines.append(f"  STRONGEST grahas: {', '.join(strongest)}")
    if weakest:
        lines.append(f"  WEAK grahas (below 80%): {', '.join(weakest)}")

    lines.append("")
    lines.append("SHADBALA READING RULE:")
    lines.append(
        "  \u2022 Strength% \u2265 100 \u2192 graha meets classical minimum, "
        "can deliver own karaka themes during its dasha/transit."
    )
    lines.append(
        "  \u2022 80-100% \u2192 adequate; delivers with some effort/conditions."
    )
    lines.append(
        "  \u2022 < 80% \u2192 weak; struggles to deliver, results often delayed "
        "or partial; remedies indicated."
    )
    lines.append(
        "  \u2022 Note: Rahu/Ketu have no Shadbala in classical Parashari."
    )

    return "\n".join(lines)


# ────────────────────────────────────────────────────────────────────
# Section 13 — ARGALA / VIRODHARGALA  (Item #25)
# Jaimini intervention summary across general houses (1, 10, 7, 4) —
# the four most-cited bhavas. Also flags any STRONG-MALEFIC house
# across all 12 so LLM can warn of obstructive interventions on the
# fly when topic touches that bhava.
# ────────────────────────────────────────────────────────────────────
def _section_argala(kundli: dict, lagna_sign_idx: Optional[int]) -> str:
    if lagna_sign_idx is None:
        return ""
    try:
        from argala import compute_argala, format_argala_summary  # type: ignore
    except Exception:
        return ""

    planets = kundli.get("planets") or []
    if not planets:
        return ""

    # argala.compute_argala expects an English sign name (or dict
    # whose `sign`/`name` is English). Derive from lagna_sign_idx so
    # the call-site never silently skips on a Hinglish payload.
    try:
        lagna_en = _ENGLISH_SIGNS[int(lagna_sign_idx) % 12]
    except (TypeError, ValueError, IndexError):
        return ""

    try:
        argala = compute_argala(planets, lagna_en)
    except Exception:
        return ""
    if not isinstance(argala, dict) or not argala:
        return ""

    try:
        # general topic = houses 1, 10, 7, 4 (broadest coverage)
        summary = format_argala_summary(argala, topic="general", max_houses=4)
    except Exception:
        summary = ""

    lines = ["## 13. ARGALA / VIRODHARGALA (Jaimini intervention)"]
    if summary:
        lines.append(summary)

    # Cross-house scan — flag any STRONG-MALEFIC overall verdict
    # so LLM is warned regardless of topic.
    strong_malefic = [
        h for h, info in argala.items()
        if isinstance(info, dict) and info.get("overall") == "STRONG-MALEFIC"
    ]
    strong_benefic = [
        h for h, info in argala.items()
        if isinstance(info, dict) and info.get("overall") == "STRONG-BENEFIC"
    ]
    if strong_benefic:
        lines.append(
            "  \u25b8 STRONG-BENEFIC argala on houses: "
            + ", ".join(f"H{h}" for h in sorted(strong_benefic))
        )
    if strong_malefic:
        lines.append(
            "  \u25b8 STRONG-MALEFIC argala on houses: "
            + ", ".join(f"H{h}" for h in sorted(strong_malefic))
            + "  (obstruction in those bhava themes)"
        )

    if len(lines) == 1:  # only the header — no real data
        return ""

    lines.append("")
    lines.append("ARGALA READING RULE:")
    lines.append(
        "  \u2022 Argala = planets in 2nd / 4th / 5th / 11th from a "
        "house intervene in its affairs."
    )
    lines.append(
        "  \u2022 Virodhargala = counter-intervention from 12th / 10th "
        "/ 9th / 3rd cancels the corresponding Argala."
    )
    lines.append(
        "  \u2022 Net BENEFIC argala uncancelled \u2192 supportive "
        "intervention; net MALEFIC uncancelled \u2192 obstructive."
    )
    lines.append(
        "  \u2022 Use this layer to refine a bhava verdict beyond just "
        "occupants/aspects \u2014 it answers \u201cwho is meddling in this house?\u201d."
    )

    return "\n".join(lines)


def _section_kp(birth: dict | None) -> str:
