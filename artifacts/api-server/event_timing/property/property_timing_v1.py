"""Property timing engine v1 — 4H + Mars/Shani karakas; ghar/registry/dispute windows."""
from __future__ import annotations

import re
from typing import Any, Optional

from event_timing._shared.generic_timing_engine import DomainTimingConfig, compute_generic_timing_window

# Classical property: 4H axis + Mangal (bhumi/construction) + Shani (immovable/delay)
_PROPERTY_CFG = DomainTimingConfig(
    domain="property",
    engine_version="property_timing_v1.1",
    concern_houses=[
        (4, 20.0, "4H property axis (Mars/Shani)"),
        (11, 10.0, "11H property gain/fulfilment"),
    ],
    leak_houses=[
        (8, 8.0, "8H sudden property obstacle"),
        (12, 10.0, "12H legal/expense drain on property"),
    ],
    occupant_bumps=[
        (4, 12.0, "occupies 4H (home/property)"),
    ],
    aspect_target_houses=[
        (4, 8.0, "aspects 4H (property activation)"),
    ],
    karakas=[
        ("Mars", 14.0, "Mangal — bhumi, plot, construction karaka"),
        ("Saturn", 12.0, "Shani — immovable property, structure, delay karaka"),
    ],
    kp_cusps=[4],
    promote_tags=("4L", "4H", "Mars", "Saturn", "Mangal", "Shani", "occupies 4H"),
    obstruct_tags=("8L", "12L", "8H", "12H"),
    double_transit_houses=[4],
    promised_label="PROPERTY_WINDOW_OPEN",
    favourable_label="PROPERTY_WINDOW_MODERATE",
    caution_label="PROPERTY_DELAY",
    defer_label="PROPERTY_LOW_PROBABILITY",
    brand_safety=[
        "Sirf probability window — exact registry date / price / address guarantee nahi.",
        "Title, RERA, loan — practical verification zaroori.",
    ],
    llm_directives=[
        "NO_EXACT_PRICE",
        "NO_LEGAL_OUTCOME_CERTAINTY",
    ],
)

_RELEVANT_FACTOR = re.compile(
    r"(?ix)4H|4L|11H|11L|mars|saturn|mangal|shani|property|home|ghar|"
    r"registry|construction|bhumi|immovable|karaka",
)

_BUCKET_RX = [
    ("dispute", re.compile(
        r"(?ix)\b(vivaad|vivad|dispute|court\s+case|litigation|suljhega|suljhegi|"
        r"faisla|kabza|encroachment|stay\s+order|injunction|illegal\s+kabza|"
        r"property\s+fight|land\s+case|challenge\s+kar)\b",
    )),
    ("inheritance", re.compile(
        r"(?ix)\b(paitrik|pustaini|ancestral|virasat|inherit|inheritance|"
        r"vasiyat|will\b|hissa\s+(?:kab|milega|milegi|percent)|pitri\s+dhan|"
        r"parental\s+property|dowry\s+me)\b",
    )),
    ("loan", re.compile(
        r"(?ix)\b(home\s+loan|house\s+loan|property\s+loan|bank\s+loan|"
        r"loan\s+sanction|emi|griha\s*rin|mortgage)\b",
    )),
    ("registry", re.compile(r"(?ix)\b(registry|griha[\s-]?pravesh|registration)\b")),
    ("possession", re.compile(
        r"(?ix)\b(possession|handover|builder\s+possession|chaabi|chabi)\b",
    )),
    ("construction", re.compile(
        r"(?ix)\b(construction|build|ban[\s-]?(?:ega|egi|wana|wane)|makaan\s+ban|"
        r"renovation|repairing)\b",
    )),
    ("sell", re.compile(
        r"(?ix)\b(sell|bech|bechega|bechegi|bikega|bikegi|sale|grahak|buyer|"
        r"bik\s+nahi|liquidate|bayaana|agreement\s+sign)\b",
    )),
    ("buy", re.compile(
        r"(?ix)\b(buy|purchase|kharid|khareed|lena|ghar\s+len|makaan\s+len|"
        r"flat\s+len|down[\s-]?payment|token\s+money|dda|mhada|awas\s+yojna|"
        r"housing\s+scheme|invest)\b",
    )),
]


def classify_property_timing_bucket(question: str) -> str:
    q = question or ""
    for name, rx in _BUCKET_RX:
        if rx.search(q):
            return name
    return "buy"


def _mars_saturn_snapshot(kundli: dict) -> list[str]:
    lines: list[str] = []
    for p in kundli.get("planets") or []:
        if not isinstance(p, dict) or p.get("name") not in ("Mars", "Saturn"):
            continue
        name = p["name"]
        label = "Mangal" if name == "Mars" else "Shani"
        sign = p.get("sign") or "?"
        house = p.get("house")
        house_s = f"{house}H" if isinstance(house, int) else "?H"
        lines.append(f"{label} ({name}): {sign} · {house_s}")
    return lines


def _filter_property_factors(factors: list) -> list[str]:
    out: list[str] = []
    for f in factors or []:
        if isinstance(f, str) and _RELEVANT_FACTOR.search(f):
            out.append(f)
    return out[:5]


def compute_property_window(
    kundli: dict,
    intel: Optional[dict] = None,
    kp: Optional[dict] = None,
    birth: Any = None,
    question: str = "",
    bucket: str | None = None,
) -> dict:
    b = bucket or classify_property_timing_bucket(question)
    out = compute_generic_timing_window(
        kundli, _PROPERTY_CFG, intel, kp, birth, question, b,
    )
    karakas = _mars_saturn_snapshot(kundli)
    if karakas:
        out["property_karakas"] = karakas
    raw_factors = list(out.get("factors") or [])
    filtered = _filter_property_factors(raw_factors)
    if filtered:
        out["factors"] = filtered
    elif karakas:
        out["factors"] = karakas
    extra: list[str] = []
    if b == "dispute":
        extra.append("Property vivaad — court outcome guarantee nahi; legal + mediation parallel rakho.")
    elif b == "inheritance":
        extra.append("Ancestral/paitrik hissa — family settlement + legal heir certificate verify karo.")
    if extra:
        warnings = list(out.get("brand_safety_warnings") or [])
        warnings.extend(extra)
        out["brand_safety_warnings"] = warnings
    return out


def format_property_timing_for_prompt(v: dict, question: str = "") -> str:
    if not isinstance(v, dict) or not v:
        return ""
    lines = [
        "=== PROPERTY TIMING ENGINE v1 (LOCKED) — 4H · Mangal · Shani ===",
        f"Bucket: {v.get('bucket')} · Verdict: {v.get('verdict')} · Band: {v.get('band')}",
    ]
    for k in (v.get("property_karakas") or [])[:2]:
        lines.append(f"  KARAK: {k}")
    cw = v.get("current_window") or {}
    if cw.get("start_iso") and cw.get("end_iso"):
        lines.append(
            f"▸ Window: {cw.get('start_iso')} → {cw.get('end_iso')} "
            f"({cw.get('md', '?')}/{cw.get('ad', '?')})"
        )
    elif (v.get("next_3_windows") or [])[:1]:
        w = v["next_3_windows"][0]
        if isinstance(w, dict):
            lines.append(
                f"▸ Next window: {w.get('start_iso', '?')} → {w.get('end_iso', '?')} "
                f"({w.get('md', '?')}/{w.get('ad', '?')})"
            )
    for f in (v.get("factors") or [])[:4]:
        lines.append(f"  • {f}")
    dt = v.get("double_transit") or {}
    if dt.get("active") and dt.get("verdict"):
        lines.append(f"▸ Shani/Guru 4H transit: {dt.get('verdict')}")
    for g in (v.get("brand_safety_warnings") or [])[:3]:
        lines.append(f"  GUARD: {g}")
    lines.append("RULE: sirf 4H + Mars/Shani dasha window — exact date nahi.")
    return "\n".join(lines)
