"""KP Planet Significator Scan — shared engine helper (Phase 2.5.11.17).

User mandate: "Har event ke planets ek separate section me rakho — sara
planet, unke nakshatra lord, unke sublord, sara systematic check karo,
travel kaun de raha hai woh planet filter karo, waise hi career, money,
marriage. Sab engine me check ho — agar planet engine ke filter me aaye
to good, agar nahi aaye phir bhi ek nazar dena."

For every domain (travel/health/finance/marriage/baby/career), this
helper scans ALL 9 vimshottari planets and returns:
  • The KP chain — Nakshatra-Lord → Sub-Lord → Sub-Sub-Lord names
  • Houses signified per layer (pl / sl / sb_houses / ss_houses)
  • Domain-house hits (intersection with CONCERN_HOUSES[domain])
  • DELIVERY verdict — STRONG / PARTIAL / WEAK / ABSENT
  • in_filter flag — whether the engine's STEP1 filter kept this planet

This lets the LLM (and audits) see WHICH planets are giving the event,
even when an engine's STEP1 filter dropped them. Output is engine-
agnostic and wired into every timing engine's response payload as
`kp_planet_scan`.

Compatible with both KP shapes seen in the repo:
  (a) DICT shape (Raj-style): {pl, sl, sb_houses, ss_houses, nl_lord,
                                sb_lord, ss_lord}
  (b) LIST shape (legacy):    [h1, h2, h3, ...]  (flat union)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

try:
    from .double_transit import CONCERN_HOUSES
except ImportError:  # standalone import path
    from event_timing._shared.double_transit import CONCERN_HOUSES  # type: ignore

_PLANETS_9 = ["Sun", "Moon", "Mars", "Mercury", "Jupiter",
               "Venus", "Saturn", "Rahu", "Ketu"]


def _to_int_house_list(raw: Any) -> List[int]:
    out: List[int] = []
    if not isinstance(raw, list):
        return out
    for v in raw:
        try:
            h = int(v)
        except (TypeError, ValueError):
            continue
        if 1 <= h <= 12:
            out.append(h)
    return out


def _verdict_for(score: int, total_domain_houses: int) -> str:
    """Map raw hit-count → categorical delivery verdict.

    score = number of unique domain houses signified across the
    planet's full KP chain (pl ∪ sl ∪ sb ∪ ss).

    STRONG  : ≥ 2 domain houses AND covers ≥ 50% of domain
    PARTIAL : ≥ 1 hit but below STRONG threshold
    ABSENT  : 0 hits
    """
    if score == 0:
        return "ABSENT"
    if total_domain_houses <= 0:
        return "PARTIAL"
    coverage = score / float(total_domain_houses)
    if score >= 2 and coverage >= 0.5:
        return "STRONG"
    return "PARTIAL"


def _scan_one_planet(kp: dict, planet: str,
                      domain_houses: List[int]) -> Dict[str, Any]:
    """Scan a single planet's KP chain against domain houses."""
    out: Dict[str, Any] = {
        "planet": planet,
        "nl_lord": None, "sb_lord": None, "ss_lord": None,
        "houses_pl": [], "houses_sl": [],
        "houses_sb": [], "houses_ss": [],
        "houses_signified": [],
        "domain_hits": [],
        "domain_score": 0,
        "delivers": "ABSENT",
        "layers_hit": [],
    }
    if not isinstance(kp, dict):
        return out
    sig_all = kp.get("significations") or kp.get("significators") or {}
    if not isinstance(sig_all, dict):
        return out
    sig = sig_all.get(planet) or sig_all.get(planet.lower())
    if sig is None:
        return out

    domain_set = set(domain_houses)
    all_houses: Set[int] = set()
    layers_hit: List[str] = []

    if isinstance(sig, dict):
        out["nl_lord"] = sig.get("nl_lord")
        out["sb_lord"] = sig.get("sb_lord")
        out["ss_lord"] = sig.get("ss_lord")
        layer_map = (
            ("pl",        "houses_pl"),
            ("sl",        "houses_sl"),
            ("sb_houses", "houses_sb"),
            ("ss_houses", "houses_ss"),
        )
        for src_key, dst_key in layer_map:
            houses = _to_int_house_list(sig.get(src_key))
            out[dst_key] = houses
            all_houses.update(houses)
            if any(h in domain_set for h in houses):
                layers_hit.append(src_key)
    elif isinstance(sig, list):
        # Legacy flat-list shape — collapse into pl-equivalent layer.
        flat = _to_int_house_list(sig)
        out["houses_pl"] = flat
        all_houses.update(flat)
        if any(h in domain_set for h in flat):
            layers_hit.append("flat")

    domain_hits = sorted(h for h in all_houses if h in domain_set)
    out["houses_signified"] = sorted(all_houses)
    out["domain_hits"] = domain_hits
    out["domain_score"] = len(domain_hits)
    out["layers_hit"] = layers_hit
    out["delivers"] = _verdict_for(len(domain_hits), len(domain_houses))
    return out


def compute_kp_planet_scan(kp: Optional[dict],
                            domain: str,
                            in_filter_set: Optional[Set[str]] = None,
                            ) -> Dict[str, Any]:
    """Scan all 9 vimshottari planets for the given domain.

    Args:
      kp:            engine's KP block (significations + cusps).
      domain:        one of CONCERN_HOUSES keys (travel/health/finance/...).
      in_filter_set: planets that survived the engine's STEP1 D1 filter.
                     Each scan entry will carry `in_filter: bool` so the
                     LLM can audit "filter dropped Moon but Moon
                     STRONGLY signifies travel — investigate".

    Returns:
      {
        "domain":         str,
        "domain_houses":  list[int],
        "planets":        list[scan_dict] — one per planet, sorted by
                          domain_score desc then by name (Sun → Ketu),
        "deliverers":     list[str] — planet names with delivers in
                          {STRONG, PARTIAL}, sorted desc by score,
        "missed_by_filter": list[str] — planets that DELIVER (STRONG/
                          PARTIAL) but were dropped by STEP1 — these
                          are the audit-flag candidates,
        "kp_available":   bool — False when KP data is empty/malformed,
      }
    """
    domain_houses = list(CONCERN_HOUSES.get(domain) or [])
    in_filter_set = in_filter_set or set()
    scans: List[Dict[str, Any]] = []
    kp_available = False

    for p in _PLANETS_9:
        scan = _scan_one_planet(kp or {}, p, domain_houses)
        scan["in_filter"] = p in in_filter_set
        if scan["houses_signified"]:
            kp_available = True
        scans.append(scan)

    scans.sort(key=lambda s: (-s["domain_score"], _PLANETS_9.index(s["planet"])))

    deliverers = [s["planet"] for s in scans
                   if s["delivers"] in ("STRONG", "PARTIAL")]
    missed = [s["planet"] for s in scans
                if s["delivers"] in ("STRONG", "PARTIAL")
                and not s["in_filter"]]

    return {
        "domain":           domain,
        "domain_houses":    domain_houses,
        "planets":          scans,
        "deliverers":       deliverers,
        "missed_by_filter": missed,
        "kp_available":     kp_available,
    }


def render_scan_lines(scan: Dict[str, Any], max_lines: int = 9) -> List[str]:
    """Render scan into compact human/LLM-readable lines for locked_facts.

    Format per planet:
      [✓F | DELIVERS-STRONG | hits=[3,9,12]] Moon → NL=Ketu/SB=Venus/SS=Moon
        | pl=[8,12] sl=[1,4,6,7,9,10,11] sb=[1,6,11] ss=[8,12]
    """
    domain = (scan.get("domain") or "").upper()
    houses = scan.get("domain_houses") or []
    out: List[str] = []
    out.append(f"▸ KP-PLANET-SCAN ({domain}) — domain houses {houses}")
    if not scan.get("kp_available"):
        out.append("  • (KP data unavailable for this chart — scan skipped)")
        return out
    missed = scan.get("missed_by_filter") or []
    if missed:
        out.append(f"  • AUDIT-FLAG: dropped-by-filter but DELIVERS → {', '.join(missed)}")
    for s in (scan.get("planets") or [])[:max_lines]:
        in_f = "✓F" if s.get("in_filter") else "—F"
        verdict = s.get("delivers", "ABSENT")
        hits = s.get("domain_hits") or []
        hits_str = f"hits={hits}" if hits else "no-hit"
        chain_bits = []
        if s.get("nl_lord"): chain_bits.append(f"NL={s['nl_lord']}")
        if s.get("sb_lord"): chain_bits.append(f"SB={s['sb_lord']}")
        if s.get("ss_lord"): chain_bits.append(f"SS={s['ss_lord']}")
        chain = "/".join(chain_bits) if chain_bits else "chain-NA"
        layer_bits = []
        for k, label in (("houses_pl", "pl"), ("houses_sl", "sl"),
                          ("houses_sb", "sb"), ("houses_ss", "ss")):
            v = s.get(k) or []
            if v:
                layer_bits.append(f"{label}={v}")
        layers = " ".join(layer_bits) if layer_bits else "layers-NA"
        out.append(f"  [{in_f}|{verdict:<7}|{hits_str}] "
                    f"{s['planet']} → {chain} | {layers}")
    return out
