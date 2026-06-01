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

# Classical KP marriage triplet + Krishnamurti negation set (H7 cusp rule).
MARRIAGE_PROMISE_HOUSES = frozenset({2, 7, 11})
MARRIAGE_NEGATION_HOUSES = frozenset({1, 6, 8, 10, 12})


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


def _kp_sig_for_planet(kp: dict, planet: str) -> Optional[dict]:
    if not isinstance(kp, dict):
        return None
    sig_all = kp.get("significations") or kp.get("significators") or {}
    if not isinstance(sig_all, dict):
        return None
    sig = sig_all.get(planet) or sig_all.get(planet.lower())
    return sig if isinstance(sig, dict) else None


def _verdict_from_promise_negation(
    promise_hits: List[int],
    negation_hits: List[int],
) -> str:
    """Krishnamurti gating: SB must signify promise; negation = obstruction."""
    if not promise_hits:
        return "DENIES"
    if negation_hits:
        return "PARTIAL"
    return "CONFIRMS"


def kp_marriage_planet_verdict(kp: Optional[dict], planet: str) -> Dict[str, Any]:
    """Marriage KP for a natal planet — **Sub-Lord houses decide**.

    Classical rule (K.S. Krishnamurti / kp_locked_facts H7):
      - NL (``sl``) and planet ``pl`` are informational only — not used to
        approve marriage delivery.
      - **Sub-Lord** significations (``sb_houses`` on this planet's row) are
        the fruit layer: must hit ≥1 of {2, 7, 11}.
      - Negation {1, 6, 8, 10, 12} on the SB layer → PARTIAL (delay/struggle)
        or DENIES when no promise house is signified.
    """
    out: Dict[str, Any] = {
        "planet": planet,
        "nl_lord": None,
        "sb_lord": None,
        "ss_lord": None,
        "houses_pl": [],
        "houses_nl": [],
        "houses_sb": [],
        "houses_ss": [],
        "promise_hits": [],
        "negation_hits": [],
        "verdict": "DENIES",
        "kp_valid": False,
        "kp_available": False,
    }
    sig = _kp_sig_for_planet(kp or {}, planet)
    if not sig:
        return out

    out["kp_available"] = True
    out["nl_lord"] = sig.get("nl_lord")
    out["sb_lord"] = sig.get("sb_lord")
    out["ss_lord"] = sig.get("ss_lord")
    out["houses_pl"] = _to_int_house_list(sig.get("pl"))
    out["houses_nl"] = _to_int_house_list(sig.get("sl"))
    out["houses_sb"] = _to_int_house_list(sig.get("sb_houses"))
    out["houses_ss"] = _to_int_house_list(sig.get("ss_houses"))

    sb_set = set(out["houses_sb"])
    promise = sorted(sb_set & MARRIAGE_PROMISE_HOUSES)
    negation = sorted(sb_set & MARRIAGE_NEGATION_HOUSES)
    out["promise_hits"] = promise
    out["negation_hits"] = negation
    verdict = _verdict_from_promise_negation(promise, negation)
    out["verdict"] = verdict
    out["kp_valid"] = verdict in ("CONFIRMS", "PARTIAL")
    return out


def kp_marriage_cusp_verdict(kp: Optional[dict], house: int = 7) -> Dict[str, Any]:
    """7th (or other) cusp sub-lord — uses **CSL planet's ``pl``** houses.

    Matches ``kp_locked_facts._verdict_for`` for marriage (H7).
    """
    out: Dict[str, Any] = {
        "house": house,
        "csl_planet": None,
        "houses_csl": [],
        "promise_hits": [],
        "negation_hits": [],
        "verdict": "UNKNOWN",
        "kp_available": False,
    }
    if not isinstance(kp, dict):
        return out
    csl: Optional[str] = None
    for c in kp.get("cusps") or []:
        if isinstance(c, dict) and c.get("house") == house:
            csl = c.get("sb")
            break
    if not isinstance(csl, str):
        return out
    sig = _kp_sig_for_planet(kp, csl)
    if not sig:
        out["csl_planet"] = csl
        return out

    out["kp_available"] = True
    out["csl_planet"] = csl
    csl_houses = _to_int_house_list(sig.get("pl"))
    out["houses_csl"] = csl_houses
    hset = set(csl_houses)
    promise = sorted(hset & MARRIAGE_PROMISE_HOUSES)
    negation = sorted(hset & MARRIAGE_NEGATION_HOUSES)
    out["promise_hits"] = promise
    out["negation_hits"] = negation
    if not promise:
        out["verdict"] = "DENIES"
    elif negation:
        out["verdict"] = "PARTIAL"
    else:
        out["verdict"] = "CONFIRMS"
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


def kp_promote_survivors(d1_map: Dict[str, Dict[str, Any]],
                          kp: Optional[dict],
                          domain: str,
                          threshold: int = 2,
                          ) -> List[str]:
    """Phase 2.5.11.18 — KP-driven promotion of STEP1 survivors.

    Mutates `d1_map` in place: any planet whose KP NL→SB→SS chain
    signifies ≥ `threshold` of the domain houses is promoted to
    `in_filter=True` with a `kp-promoted (hits=[...])` link tag.

    This replaces the hardcoded `_KARAKA_FLOOR_SURVIVORS` constant as
    primary signal — the engine-internal floor is retained ONLY as a
    safety-net for charts where KP data is missing/empty (otherwise
    the KP-driven promotion is data-adaptive per chart).

    Args:
      d1_map:    engine STEP1 output, shape {planet: {in_filter, links, ...}}.
      kp:        engine's KP block (significations + cusps).
      domain:    one of CONCERN_HOUSES keys.
      threshold: minimum domain-hit count to qualify (default 2 = at least
                 2 of the domain houses signified across the full chain).

    Returns:
      list of newly-promoted planet names (was filtered=False before this
      call). Used by orchestrators for trace/audit.
    """
    scan = compute_kp_planet_scan(kp, domain)
    if not scan.get("kp_available"):
        return []
    promoted: List[str] = []
    for s in scan.get("planets") or []:
        score = s.get("domain_score") or 0
        if score < threshold:
            continue
        p = s.get("planet")
        entry = d1_map.get(p)
        if not isinstance(entry, dict):
            continue
        if entry.get("in_filter"):
            continue  # already in filter — skip
        entry["in_filter"] = True
        links = entry.get("links") or []
        if not isinstance(links, list):
            links = []
        links.append(f"kp-promoted (hits={s.get('domain_hits') or []})")
        entry["links"] = links
        promoted.append(p)
    return promoted


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
