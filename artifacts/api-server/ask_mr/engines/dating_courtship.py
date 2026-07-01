"""Dating, courtship, true love, friend-to-lover, red/green flags — 5H + Venus/Mars."""
from __future__ import annotations

import re

from vedic.love_reality.scoring_core import KundliReader

from ..types import EngineResult
from ._chart_axes import dignity_word, house_axis_evidence, planet_line
from ._person_signals import build_person_signals, pick_notes


def _detect_focus(q: str) -> str:
    if re.search(r"(?ix)\b(true\s*love|sach+a\s*pyaar|sachchi\s*mohabbat)\b", q):
        return "true_love"
    if re.search(r"(?ix)\b(friend\s*to\s*lover|dost\s*se\s*pyaar|friend\s*se\s*love)\b", q):
        return "friend_to_lover"
    if re.search(r"(?ix)\b(online\s*relation|dating\s*app|virtual\s*love)\b", q):
        return "online_dating"
    if re.search(r"(?ix)\b(first\s*impression|pehli\s*nazar|pehla\s*impression)\b", q):
        return "first_impression"
    if re.search(r"(?ix)\b(flirt|flirting|mazaak|tease)\b", q):
        return "flirting"
    if re.search(r"(?ix)\b(dating\s*success|date\s*pe|dating)\b", q):
        return "dating_success"
    if re.search(r"(?ix)\b(red\s*flags?|warning\s*sign|khatre\s*ke\s*nishan)\b", q):
        return "red_flags"
    if re.search(r"(?ix)\b(green\s*flags?|positive\s*sign|achhe\s*signal)\b", q):
        return "green_flags"
    if re.search(r"(?ix)\b(attraction\s*pattern|pull|drawn\s*to)\b", q):
        return "attraction_pattern"
    return "dating_general"


def run_dating_courtship(kundli: dict, question: str, *, wants_explain: bool = False) -> EngineResult:
    k = dict(kundli or {})
    k.setdefault("name", "You")
    r = KundliReader(k)
    sig = build_person_signals(k)
    focus = _detect_focus(question or "")

    evidence: list[str] = [
        house_axis_evidence(r, 5, label="Romance/dating axis (5th house)"),
        house_axis_evidence(r, 7, label="Partnership outcome axis (7th house)"),
    ]
    ven_line = planet_line(r, "Venus", role="love/attraction karak")
    mars_line = planet_line(r, "Mars", role="passion/initiative in dating")
    if ven_line:
        evidence.append(ven_line)
    if mars_line:
        evidence.append(mars_line)

    if focus == "true_love":
        jup = r.planet("Jupiter") or {}
        occ5 = r.occupants(5)
        if "Venus" in occ5 or (r.planet("Venus") or {}).get("house") == 5:
            evidence.append(
                "True-love marker: Venus on 5th romance axis — deep heartfelt love capacity, not just infatuation."
            )
        if jup.get("house") in (5, 7, 9):
            evidence.append(
                f"Jupiter in house {jup.get('house')} — dharmic true love; bond grows with trust and blessing."
            )
        if "Jupiter" in occ5:
            evidence.append(
                "Benefic Jupiter in 5th house — growth-oriented romance; strong true-love support on romance axis."
            )
        sat = r.planet("Saturn") or {}
        if sat.get("house") == 5:
            sat_sign = sat.get("sign")
            sat_dig = dignity_word(r, "Saturn", str(sat_sign) if sat_sign else None)
            evidence.append(
                f"Saturn in 5th ({sat_sign or '?'}, dignity {sat_dig}) — love matures slowly; "
                "tests, delay, or seriousness before deep bond."
            )
            if "Saturn" in (r.aspects_house(7) or []):
                evidence.append(
                    "Saturn aspects 7th house — partnership cools or delays; patience needed for lasting love."
                )
        challenges = pick_notes(
            sig,
            [
                "Saturn on 7th",
                "Venus debilitated",
                "Venus in enemy",
                "Venus in dusthana",
                "Venus under nodal",
                "7th lord debilitated",
                "7th lord in dusthana",
                "Moon debilitated",
                "Moon under Saturn",
            ],
            limit=5,
        )
        for line in challenges:
            evidence.append(f"Love challenge: {line}")
        has_tests = bool(challenges) or sat.get("house") == 5 or sig.venus_afflicted or sig.venus_debil
        if sig.reconnection_yoga:
            evidence.append("Reconnection yoga — true love can deepen again after tests.")
        if has_tests:
            verdict = (
                "True love yog with tests: Jupiter/Venus support romance, but Saturn/afflictions "
                "add delay, emotional cooling, or inconsistency — mixed, not guaranteed instant."
            )
        else:
            verdict = "True love capacity: Venus + Jupiter on 5th/7th romance-partnership axis"

    elif focus == "friend_to_lover":
        evidence.append(house_axis_evidence(r, 11, label="Friendship/social circle axis (11th house)"))
        lord5 = r.house_lord(5)
        lord11 = r.house_lord(11)
        evidence.append(
            f"Friend-to-lover link: 5th lord {lord5} + 11th lord {lord11} — "
            "romance growing from friendship/social circle is chart-supported."
        )
        if (r.planet("Mercury") or {}).get("house") in (5, 7, 11):
            evidence.append(
                "Mercury on friendship/romance axis — talk and friendship easily turn into love."
            )
        verdict = "Friend-to-lover pattern: 11th house friendship + 5th house romance link"

    elif focus == "online_dating":
        rahu = r.planet("Rahu") or {}
        evidence.append(
            f"Online/unusual meeting: Rahu in house {rahu.get('house')} sign {rahu.get('sign')} — "
            "digital/distance/unconventional meeting channel for love."
        )
        evidence.append(
            "Mercury + Rahu on 3rd/5th/11th supports online chat, apps or long-distance courtship."
        )
        verdict = "Online relationship pattern: Rahu + Mercury on communication/romance houses"

    elif focus == "first_impression":
        occ7 = r.occupants(7)
        sign7 = evidence[1].split("sign ")[1].split(";")[0] if len(evidence) > 1 else "unknown"
        evidence.append(
            f"First-impression on others: 7th house sign {sign7} + occupants {occ7 or 'none'} — "
            "how you come across in one-to-one romantic settings."
        )
        if "Venus" in occ7:
            evidence.append("Venus in 7th — charming warm first impression in love contexts.")
        verdict = "First impression in love: 7th house partnership presentation + Venus tone"

    elif focus == "flirting":
        if sig.venus_mars_conjunct or sig.venus_mars_conjunct_tight:
            evidence.append(
                "Venus-Mars link — playful bold flirting style; spark comes naturally in conversation."
            )
        else:
            ven = r.planet("Venus") or {}
            evidence.append(
                f"Flirting style: Venus in house {ven.get('house')} sign {ven.get('sign')} — "
                "warmth/humour/charm style in early courtship."
            )
        if (r.planet("Mercury") or {}).get("house") in (3, 5, 7):
            evidence.append("Mercury active — witty verbal flirting, teasing talk, quick banter.")
        verdict = "Flirting style: Venus-Mars-Mercury on 5th/7th courtship axis"

    elif focus == "dating_success":
        lord5 = r.house_lord(5)
        p5l = r.planet(lord5) if lord5 else None
        if p5l:
            evidence.append(
                f"Dating success: 5th lord {lord5} in house {p5l.get('house')} sign {p5l.get('sign')} — "
                "how easily romance/dates convert to meaningful bonds."
            )
        if not sig.venus_afflicted:
            evidence.append("Venus not heavily afflicted — dating success improves with sincerity and timing.")
        verdict = "Dating success: strong 5th lord + healthy Venus on romance axis"

    elif focus == "red_flags":
        red = pick_notes(
            sig,
            [
                "Venus in dusthana",
                "Venus debilitated",
                "Venus under nodal pull",
                "Mars on 7th",
                "Saturn on 7th",
                "hidden ties",
                "parallel attention",
                "Moon under Saturn/Rahu",
                "7th lord in dusthana",
            ],
            limit=6,
        )
        for line in red:
            evidence.append(f"Red flag signal: {line}")
        if not red:
            evidence.append("Red flags: no dominant warning driver — still watch consistency and honesty.")
        verdict = "Relationship red flags: afflictions on 5th/7th/Venus axis"

    elif focus == "green_flags":
        green = pick_notes(
            sig,
            [
                "5th lord strong",
                "Jupiter in house",
                "Venus-Moon supportive",
                "Moon-Moon supportive",
                "Saturn as 7th lord in 7th",
            ],
            limit=5,
        )
        for line in green:
            evidence.append(f"Green flag signal: {line}")
        occ5 = r.occupants(5)
        if "Jupiter" in occ5:
            evidence.append("Jupiter in 5th — honest growth-oriented romance; strong green flag for love.")
        if "Venus" in occ5:
            evidence.append("Venus in 5th — affectionate sincere romance; positive dating signal.")
        verdict = "Relationship green flags: benefics on 5th/7th + strong Venus/Jupiter"

    elif focus == "attraction_pattern":
        if sig.venus_mars_conjunct_tight:
            evidence.append("Attraction pattern: intense Venus-Mars pull — passionate magnetic type attracts you.")
        elif sig.venus_mars_conjunct:
            evidence.append("Attraction pattern: Venus-Mars chemistry — lively passionate partners draw you.")
        else:
            ven = r.planet("Venus") or {}
            evidence.append(
                f"Attraction pattern: Venus in house {ven.get('house')} sign {ven.get('sign')} — "
                "defines what look/vibe/energy you find attractive."
            )
        verdict = "Attraction pattern: Venus-Mars + 5th house romance taste"

    else:
        sig_notes = pick_notes(
            sig,
            [
                "Venus debilitated",
                "Venus in dusthana",
                "Venus under nodal pull",
                "Mars on 7th",
                "Saturn on 7th",
                "7th lord debilitated",
                "7th lord in dusthana",
                "5th lord strong",
                "Jupiter in house",
            ],
            limit=3,
        )
        for line in sig_notes:
            evidence.append(f"Affliction/strength signal: {line}")
        verdict = "Dating/courtship pattern: 5th house romance + Venus/Mars initiative"

    return EngineResult(
        archetype="dating_courtship",
        verdict=verdict,
        confidence="medium",
        word_budget=95 if wants_explain else 70,
        answer_plan="2–3 sentences: direct answer → 2 evidence lines → one practical dating note.",
        summary=[
            f"QUESTION FOCUS: {focus}.",
            "Use 5th/7th/Venus/Mars evidence — this is courtship/love-life, not spouse profession.",
            "Narrator MUST give a MIXED honest answer: mention positives (Jupiter/Venus) AND "
            "challenges (Saturn debilitated in 5th, Venus enemy/debilitated, Saturn on/aspecting 7th) — "
            "never only optimistic haan.",
        ],
        evidence=evidence[:12],
        ignore=["timing dates/windows", "exact date of meeting", "spouse job title"],
        checks={
            "slice_type": "mr_engine_v1",
            "archetype": "dating_courtship",
            "question_focus": focus,
        },
    )
