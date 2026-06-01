"""
FaceSignalBundle — single compressed AI-facing object for Face Reading narration.

Replaces per-section _flatten_facts() + repeated _engine_highlights() in prompts.
Built once after engines run; stored on analysis snapshot + session report_payload.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

BUNDLE_VERSION = "sig_v1"


@dataclass
class Signal:
    value: str
    confidence: float = 0.65

    def to_dict(self) -> Dict[str, Any]:
        return {"value": self.value, "confidence": round(float(self.confidence), 2)}

    @classmethod
    def from_dict(cls, d: Any) -> "Signal":
        if isinstance(d, dict):
            return cls(
                value=str(d.get("value") or ""),
                confidence=float(d.get("confidence") or 0.5),
            )
        return cls(value=str(d or ""), confidence=0.5)


@dataclass
class FaceSignalBundle:
    version: str = BUNDLE_VERSION
    personality: Dict[str, Signal] = field(default_factory=dict)
    communication: Dict[str, Signal] = field(default_factory=dict)
    attachment: Dict[str, Signal] = field(default_factory=dict)
    motivation: Dict[str, Signal] = field(default_factory=dict)
    stress_response: Dict[str, Signal] = field(default_factory=dict)
    contradictions: List[Dict[str, Any]] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    blind_spots: List[str] = field(default_factory=list)
    social_energy: Dict[str, Signal] = field(default_factory=dict)
    work_style: Dict[str, Signal] = field(default_factory=dict)
    emotional_regulation: Dict[str, Signal] = field(default_factory=dict)
    confidence_levels: Dict[str, Any] = field(default_factory=dict)
    anchors: List[str] = field(default_factory=list)
    identity: Dict[str, Any] = field(default_factory=dict)
    disclaimers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        def _sig_map(m: Dict[str, Signal]) -> Dict[str, Any]:
            return {k: v.to_dict() for k, v in m.items()}

        return {
            "version": self.version,
            "personality": _sig_map(self.personality),
            "communication": _sig_map(self.communication),
            "attachment": _sig_map(self.attachment),
            "motivation": _sig_map(self.motivation),
            "stress_response": _sig_map(self.stress_response),
            "contradictions": self.contradictions,
            "strengths": self.strengths,
            "blind_spots": self.blind_spots,
            "social_energy": _sig_map(self.social_energy),
            "work_style": _sig_map(self.work_style),
            "emotional_regulation": _sig_map(self.emotional_regulation),
            "confidence_levels": self.confidence_levels,
            "anchors": self.anchors,
            "identity": self.identity,
            "disclaimers": self.disclaimers,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FaceSignalBundle":
        def _load_map(raw: Any) -> Dict[str, Signal]:
            if not isinstance(raw, dict):
                return {}
            return {k: Signal.from_dict(v) for k, v in raw.items()}

        b = cls(version=str(data.get("version") or BUNDLE_VERSION))
        b.personality = _load_map(data.get("personality"))
        b.communication = _load_map(data.get("communication"))
        b.attachment = _load_map(data.get("attachment"))
        b.motivation = _load_map(data.get("motivation"))
        b.stress_response = _load_map(data.get("stress_response"))
        b.contradictions = list(data.get("contradictions") or [])
        b.strengths = list(data.get("strengths") or [])
        b.blind_spots = list(data.get("blind_spots") or [])
        b.social_energy = _load_map(data.get("social_energy"))
        b.work_style = _load_map(data.get("work_style"))
        b.emotional_regulation = _load_map(data.get("emotional_regulation"))
        b.confidence_levels = dict(data.get("confidence_levels") or {})
        b.anchors = list(data.get("anchors") or [])
        b.identity = dict(data.get("identity") or {})
        b.disclaimers = list(data.get("disclaimers") or [])
        return b

    def fingerprint(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, default=str)
        return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]

    def to_prompt_json(self, compact: bool = True) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, separators=(",", ":"))

    def all_signals_flat(self) -> Dict[str, str]:
        """Flat map signal_id → value for validation."""
        out: Dict[str, str] = {}
        for cat_name, cat in (
            ("personality", self.personality),
            ("communication", self.communication),
            ("attachment", self.attachment),
            ("motivation", self.motivation),
            ("stress_response", self.stress_response),
            ("social_energy", self.social_energy),
            ("work_style", self.work_style),
            ("emotional_regulation", self.emotional_regulation),
        ):
            for k, sig in cat.items():
                if sig.value:
                    out[f"{cat_name}.{k}"] = sig.value
        for i, s in enumerate(self.strengths):
            out[f"strength.{i}"] = s
        for i, s in enumerate(self.blind_spots):
            out[f"blind_spot.{i}"] = s
        for i, c in enumerate(self.contradictions):
            t = c.get("tension") or c.get("note") or ""
            if t:
                out[f"tension.{i}"] = str(t)
        for a in self.anchors:
            out[f"anchor.{a}"] = a
        return out

    def anchor_terms(self) -> List[str]:
        """Terms/phrases prose must echo (fact-guard)."""
        terms: List[str] = []
        for v in self.all_signals_flat().values():
            v = (v or "").strip()
            if len(v) >= 4:
                terms.append(v.lower())
        for a in self.anchors:
            if a and len(a) >= 3:
                terms.append(a.lower())
        idn = self.identity.get("archetype") or ""
        if idn:
            terms.append(str(idn).lower())
        fs = self.identity.get("face_shape") or ""
        if fs:
            terms.append(str(fs).lower())
        return list(dict.fromkeys(terms))[:24]


# ── Section routing (anti-repetition) ───────────────────────────────────────
SECTION_GOALS: Dict[str, str] = {
    "section_1_power_summary": "Core pattern + first-impression impact in one arc",
    "section_2_psychological_type": "OCEAN-style type in plain behavioral language",
    "section_3_mask_vs_real": "Public presentation vs private emotional wiring",
    "section_4_first_impression": "How strangers read you in the first 10 seconds",
    "section_5_core_foundation": "Stable traits that rarely change",
    "section_6_feature_analysis": "Skip generic feature list — one cross-feature insight",
    "section_7_personality_synthesis": "Integrate top 3 patterns without repeating hook",
    "section_8_love_relationship_dna": "Attachment + intimacy friction + repair style",
    "section_9_career_money": "Work rhythm, ambition, money habits",
    "section_10_red_flags": "Gentle blind spots under stress",
    "section_11_attraction_charisma": "Presence and social magnetism",
    "section_12_decision_style": "Speed vs caution in choices",
    "section_13_archetype": "Archetype as behavior metaphor not destiny",
    "section_14_life_flow": "Past-present-future as tendencies not prophecy",
    "section_15_age_wise_map": "Life phases as energy windows",
    "section_16_health_scan": "Stress-vitality habits only — no diagnosis",
    "section_17_secret_markings": "Optional physical markers if present",
    "section_18_action_plan": "30-day experiments",
    "section_19_improvement_hacks": "Micro-habits",
    "section_20_compatibility": "Who complements vs drains you",
    "section_21_final_truth": "One contradiction + direction + closing",
    "faceread.hook_identity": "One precise identity line",
    "faceread.hook_shock": "One non-obvious merged pattern",
    "faceread.tldr": "Skimmer summary — 3 bullets worth",
    "block_01_screen": "Core pattern + how others read you in the first 10 seconds",
    "block_02_inner_drive": "Motivation and what actually energizes you",
    "block_03_emotional_wiring": "Mask vs real self + how feelings move under the surface",
    "block_04_strengths_stress": "What holds up when life gets heavy",
    "block_05_blind_spots": "Non-judgmental friction patterns — no diagnosis",
    "block_06_love_attachment": "Bonding style, repair, intimacy friction",
    "block_07_work_money": "Career pace, risk, money habits",
    "block_08_communication": "How you register in conversation",
    "block_09_contradictions": "Two true patterns that coexist",
    "block_10_experiments": "Five practical micro-experiments",
    "block_11_confidence_limits": "Signal strength + what this report cannot claim",
    "block_12_closing_truth": "One direction + grounded closing — no prophecy",
}

SECTION_FOCUS_KEYS: Dict[str, List[str]] = {
    "section_1_power_summary": [
        "personality.core_type", "social_energy.level", "motivation.primary",
        "strength.0", "tension.0",
    ],
    "section_3_mask_vs_real": [
        "communication.public_read", "attachment.style", "emotional_regulation.expression",
        "tension.0",
    ],
    "section_8_love_relationship_dna": [
        "attachment.style", "attachment.friction", "communication.warmth",
        "emotional_regulation.under_stress",
    ],
    "section_9_career_money": [
        "work_style.pace", "work_style.risk", "motivation.primary",
        "personality.conscientiousness_band",
    ],
    "section_21_final_truth": [
        "tension.0", "tension.1", "blind_spot.0", "personality.archetype",
    ],
    "faceread.hook_identity": [
        "personality.archetype", "personality.core_type", "social_energy.level",
    ],
    "faceread.hook_shock": [
        "tension.0", "motivation.primary", "social_energy.level",
    ],
    "faceread.tldr": [
        "personality.core_type", "strength.0", "blind_spot.0", "work_style.pace",
    ],
    # 12-block layout keys
    "block_01_screen": [
        "personality.core_type", "social_energy.level", "communication.public_read",
        "strength.0",
    ],
    "block_02_inner_drive": [
        "motivation.primary", "personality.core_type", "personality.archetype",
    ],
    "block_03_emotional_wiring": [
        "attachment.style", "communication.public_read", "emotional_regulation.expression",
        "tension.0",
    ],
    "block_04_strengths_stress": [
        "strength.0", "strength.1", "stress_response.pattern",
    ],
    "block_05_blind_spots": [
        "blind_spot.0", "blind_spot.1", "tension.0",
    ],
    "block_06_love_attachment": [
        "attachment.style", "attachment.friction", "communication.warmth",
    ],
    "block_07_work_money": [
        "work_style.pace", "work_style.risk", "motivation.primary",
    ],
    "block_08_communication": [
        "communication.public_read", "communication.warmth", "social_energy.level",
    ],
    "block_09_contradictions": [
        "tension.0", "tension.1", "motivation.primary",
    ],
    "block_10_experiments": [
        "blind_spot.0", "stress_response.pattern", "work_style.pace",
    ],
    "block_11_confidence_limits": [
        "personality.confidence_band", "blind_spot.0",
    ],
    "block_12_closing_truth": [
        "tension.0", "personality.archetype", "motivation.primary",
    ],
}

DEFAULT_FOCUS = [
    "personality.core_type", "communication.public_read", "motivation.primary",
    "stress_response.pattern",
]


def _g(d: Any, *path, default=None):
    cur = d
    for p in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(p)
        if cur is None:
            return default
    return cur


def _num(v: Any, default: float = 50.0) -> float:
    try:
        f = float(v)
        return default if f != f else f
    except (TypeError, ValueError):
        return default


def _band(score: float, low: float = 38.0, high: float = 62.0) -> str:
    if score < low:
        return "low"
    if score > high:
        return "high"
    return "moderate"


def _band_label(band: str, low_word: str, mid_word: str, high_word: str) -> str:
    if band == "low":
        return low_word
    if band == "high":
        return high_word
    return mid_word


def _conf_from_score(score: float, symmetry_ok: bool = True) -> float:
    dist = abs(score - 50.0) / 50.0
    c = 0.52 + dist * 0.35
    if not symmetry_ok:
        c *= 0.85
    return round(min(0.92, max(0.42, c)), 2)


def _trait_phrase(trait: str, score: float) -> str:
    b = _band(score)
    phrases = {
        "O": ("curious explorer", "balanced openness", "practical conventional"),
        "C": ("structured disciplined", "steady follow-through", "flexible spontaneous"),
        "E": ("outward energetic", "moderate social energy", "reserved inward"),
        "A": ("warm cooperative", "selectively warm", "direct competitive"),
        "N": ("emotionally reactive", "balanced sensitivity", "calm steady"),
    }
    opts = phrases.get(trait, ("variable", "balanced", "variable"))
    return _band_label(b, opts[0], opts[1], opts[2])


def _build_contradictions(
    ocean: Dict[str, float],
    pers: Dict[str, Any],
    sections: Dict[str, Any],
) -> List[Dict[str, Any]]:
    tensions: List[Dict[str, Any]] = []
    O, C, E, A, N = (
        _num(ocean.get("O")),
        _num(ocean.get("C")),
        _num(ocean.get("E")),
        _num(ocean.get("A")),
        _num(ocean.get("N")),
    )

    def add(tension: str, note: str, conf: float = 0.72):
        tensions.append({"tension": tension, "note": note, "confidence": conf})

    if E >= 62 and A <= 42:
        add("warm but guarded", "Social spark with selective trust — warmth shows, depth takes time.")
    if C >= 65 and N >= 62:
        add("ambitious but cautious", "High standards plus inner vigilance — progress with self-pressure.")
    if E >= 60 and N >= 58:
        add("social but easily drained", "People energize you briefly; recovery needs solitude.")
    if O >= 62 and C <= 42:
        add("creative but scattered", "Ideas arrive fast; finishing needs deliberate structure.")
    if A >= 62 and _num(_g(pers, "composites", "dominance", default=50)) >= 58:
        add("kind surface, firm core", "Agreeable tone with quiet assertiveness underneath.")

    for inc in pers.get("inter_trait_inconsistencies") or []:
        if isinstance(inc, dict) and inc.get("note"):
            add(
                str(inc.get("flag") or "trait_tension").replace("_", " "),
                str(inc["note"])[:120],
                0.68,
            )

    syn = sections.get("synthesis") if isinstance(sections, dict) else {}
    for shock in (syn.get("shock_insights") or [])[:2]:
        if isinstance(shock, dict):
            txt = shock.get("insight") or shock.get("text") or ""
            if txt and len(txt) > 12:
                add("pattern contrast", str(txt)[:100], 0.6)

    return tensions[:5]


def build_face_signal_bundle(
    engines: Dict[str, Any],
    sections: Optional[Dict[str, Any]] = None,
    *,
    person: Optional[Dict[str, Any]] = None,
    front_quality: Optional[Dict[str, Any]] = None,
    hook: Optional[Dict[str, Any]] = None,
    tldr: Optional[Dict[str, Any]] = None,
) -> FaceSignalBundle:
    """Compress raw engines + section summaries into one AI-safe bundle."""
    sections = sections or {}
    person = person or {}
    fq = front_quality or {}

    pers = engines.get("personality") or {}
    fi = engines.get("first_impression") or {}
    sym = engines.get("symmetry") or {}
    anth = engines.get("anthropometry") or {}
    samu = engines.get("samudrika") or {}
    fwhr = engines.get("fwhr") or {}
    health = engines.get("health") or {}
    fs = sections.get("final_scores") or engines.get("final_scores") or {}

    ocean = pers.get("ocean_summary_scores") or {}
    O, C, E, A, N = (
        _num(ocean.get("O")),
        _num(ocean.get("C")),
        _num(ocean.get("E")),
        _num(ocean.get("A")),
        _num(ocean.get("N")),
    )
    sym_score = _num(_g(sym, "overall", "score", default=_g(sym, "overall_score", default=55)))
    sym_ok = sym_score >= 50
    qual_score = _num(fq.get("score"), 70)

    archetype = (
        _g(pers, "archetype", "name")
        or _g(pers, "archetype", "label")
        or fs.get("archetype")
        or "balanced presence"
    )
    face_shape = _g(anth, "face_shape_7", "class", default="balanced")
    element = _g(samu, "element_profile", "dominant_element", default="balanced")

    dom_trait = pers.get("dominant_trait") or "C"
    core_type = f"{_trait_phrase(dom_trait, _num(ocean.get(dom_trait)))} leaning"

    bundle = FaceSignalBundle()
    bundle.identity = {
        "age": person.get("age"),
        "gender": person.get("gender"),
        "archetype": str(archetype),
        "face_shape": str(face_shape),
        "element": str(element),
    }

    bundle.personality = {
        "archetype": Signal(str(archetype), _conf_from_score(60, sym_ok)),
        "core_type": Signal(core_type, _conf_from_score(_num(ocean.get(dom_trait)), sym_ok)),
        "openness_band": Signal(_trait_phrase("O", O), _conf_from_score(O, sym_ok)),
        "conscientiousness_band": Signal(_trait_phrase("C", C), _conf_from_score(C, sym_ok)),
        "extraversion_band": Signal(_trait_phrase("E", E), _conf_from_score(E, sym_ok)),
        "agreeableness_band": Signal(_trait_phrase("A", A), _conf_from_score(A, sym_ok)),
        "neuroticism_band": Signal(_trait_phrase("N", N), _conf_from_score(N, sym_ok)),
    }

    valence = _num(_g(pers, "composites", "trustworthiness", default=50))
    dominance = _num(_g(pers, "composites", "dominance", default=50))
    bundle.communication = {
        "public_read": Signal(
            _band_label(
                _band(valence),
                "cautious first read",
                "neutral-readable",
                "approachable first read",
            ),
            _conf_from_score(valence, sym_ok),
        ),
        "warmth": Signal(_trait_phrase("A", A), _conf_from_score(A, sym_ok)),
        "assertiveness": Signal(
            _band_label(_band(dominance), "soft-spoken", "balanced tone", "direct commanding"),
            _conf_from_score(dominance, sym_ok),
        ),
    }

    bundle.attachment = {
        "style": Signal(
            _band_label(
                _band(A),
                "slow to open up",
                "selective depth",
                "bonds relatively easily",
            ),
            _conf_from_score(A, sym_ok),
        ),
        "friction": Signal(
            _band_label(
                _band(N),
                "low jealousy load",
                "occasional reassurance needs",
                "sensitivity under uncertainty",
            ),
            _conf_from_score(N, sym_ok),
        ),
    }

    bundle.motivation = {
        "primary": Signal(
            _band_label(_band(C), "freedom-led", "mixed drive", "mastery-led"),
            _conf_from_score(C, sym_ok),
        ),
        "recognition": Signal(
            _band_label(_band(E), "private wins", "balanced visibility", "visibility-motivated"),
            _conf_from_score(E, sym_ok),
        ),
    }

    vitality = _num(_g(health, "vitality_index", "score", default=_g(health, "vitality", default=55)))
    bundle.stress_response = {
        "pattern": Signal(
            _band_label(_band(N), "internalizes stress", "mixed stress style", "shows stress openly"),
            _conf_from_score(N, sym_ok),
        ),
        "recovery": Signal(
            _band_label(_band(vitality), "slow recharge", "moderate recharge", "fast recharge"),
            _conf_from_score(vitality, sym_ok),
        ),
    }

    bundle.social_energy = {
        "level": Signal(_trait_phrase("E", E), _conf_from_score(E, sym_ok)),
        "charisma": Signal(
            _band_label(
                _band(_num(fs.get("charisma") or _g(fi, "charisma", "score", default=50))),
                "subtle presence",
                "steady presence",
                "noticeable presence",
            ),
            _conf_from_score(_num(fs.get("charisma", 50)), sym_ok),
        ),
    }

    bundle.work_style = {
        "pace": Signal(
            _band_label(_band(C), "iterative experimenter", "steady pace", "structured planner"),
            _conf_from_score(C, sym_ok),
        ),
        "risk": Signal(
            _band_label(
                _band(_num(_g(fwhr, "dominance_z", default=0)) * 10 + 50),
                "risk-averse",
                "calculated risk",
                "comfortable risk-taker",
            ),
            0.58,
        ),
    }

    bundle.emotional_regulation = {
        "expression": Signal(
            _band_label(_band(N), "controlled expression", "balanced expression", "expressive"),
            _conf_from_score(N, sym_ok),
        ),
        "under_stress": Signal(
            _g(sections, "section_10_red_flags", "primary_pattern")
            or _band_label(_band(N), "withdraws", "mixed", "reacts quickly"),
            _conf_from_score(N, sym_ok),
        ),
    }

    bundle.contradictions = _build_contradictions(ocean, pers, sections)

    sg = pers.get("strengths_and_growth") or {}
    for trait_key in ("C", "A", "E", "O"):
        block = sg.get(trait_key) if isinstance(sg, dict) else None
        if isinstance(block, dict):
            for s in (block.get("strengths") or [])[:1]:
                if s and len(str(s)) > 8:
                    bundle.strengths.append(str(s)[:90])
    s1 = _g(sections, "section_1_power_summary", "biggest_strength")
    if s1:
        bundle.strengths.insert(0, str(s1)[:90])
    bundle.strengths = list(dict.fromkeys(bundle.strengths))[:4]

    w1 = _g(sections, "section_1_power_summary", "biggest_weakness") or _g(
        sections, "section_10_red_flags", "primary_risk"
    )
    if w1:
        bundle.blind_spots.append(str(w1)[:90])
    if _band(N) == "high":
        bundle.blind_spots.append("rumination under uncertainty")
    bundle.blind_spots = list(dict.fromkeys(bundle.blind_spots))[:4]

    overall_conf = round(min(0.9, max(0.45, (sym_score / 100.0 * 0.4 + qual_score / 100.0 * 0.35 + 0.2)), 2)
    bundle.confidence_levels = {
        "overall": overall_conf,
        "symmetry": round(sym_score / 100.0, 2),
        "photo_quality": round(qual_score / 100.0, 2),
        "note": "tentative" if overall_conf < 0.55 else "moderate" if overall_conf < 0.72 else "solid",
    }

    bundle.anchors = [
        str(archetype),
        str(face_shape),
        str(element),
        dom_trait,
        _g(fwhr, "class") or "",
    ]
    bundle.anchors = [a for a in bundle.anchors if a and str(a).strip()][:6]

    bundle.disclaimers = [
        "Self-reflection only — not medical or hiring advice.",
        "Pattern-based language — avoid certainty words.",
    ]
    if hook and hook.get("shock_line"):
        bundle.disclaimers.append(f"seed_shock:{str(hook['shock_line'])[:80]}")

    return bundle


def section_focus_signals(
    section_key: str,
    bundle: FaceSignalBundle,
    used: Optional[Set[str]] = None,
) -> Tuple[List[str], Dict[str, str]]:
    """
    Return (focus lines for prompt, facts dict for validation).
    Marks signal keys as used to reduce cross-section repetition.
    """
    used = used if used is not None else set()
    flat = bundle.all_signals_flat()
    keys = SECTION_FOCUS_KEYS.get(section_key) or DEFAULT_FOCUS
    lines: List[str] = []
    facts: Dict[str, str] = {"section": section_key}

    for fk in keys:
        if fk in used and not section_key.startswith("faceread."):
            continue
        val = flat.get(fk)
        if not val:
            continue
        used.add(fk)
        lines.append(f"{fk}: {val}")
        facts[fk.replace(".", "_")] = val

    if not lines:
        for fk in DEFAULT_FOCUS[:4]:
            val = flat.get(fk)
            if val:
                lines.append(f"{fk}: {val}")
                facts[fk.replace(".", "_")] = val

    goal = SECTION_GOALS.get(section_key, "Behavioral insight for this section.")
    facts["_goal"] = goal
    return lines, facts


def validate_prose_against_bundle(text: str, bundle: FaceSignalBundle) -> bool:
    """True if prose references at least one bundle anchor."""
    if not text.strip():
        return False
    tl = text.lower()
    hits = 0
    for term in bundle.anchor_terms():
        if len(term) >= 4 and term in tl:
            hits += 1
        if hits >= 1:
            return True
    for v in bundle.all_signals_flat().values():
        words = [w for w in v.lower().split() if len(w) >= 5]
        if any(w in tl for w in words[:3]):
            hits += 1
        if hits >= 1:
            return True
    return hits >= 1


def estimate_bundle_prompt_size(bundle: FaceSignalBundle, n_sections: int) -> int:
    """Shared bundle + per-section focus (~4 lines each)."""
    base = len(bundle.to_prompt_json())
    per = 120 * n_sections
    return base + per


def load_bundle_for_analysis(
    engines: Dict[str, Any],
    sections: Optional[Dict[str, Any]] = None,
    *,
    person: Optional[Dict] = None,
    front_quality: Optional[Dict] = None,
    snapshot: Optional[Dict] = None,
    hook: Optional[Dict] = None,
    tldr: Optional[Dict] = None,
) -> FaceSignalBundle:
    """Load from snapshot dict or build fresh."""
    if snapshot and snapshot.get("signal_bundle"):
        try:
            return FaceSignalBundle.from_dict(snapshot["signal_bundle"])
        except Exception:
            pass
    return build_face_signal_bundle(
        engines,
        sections,
        person=person,
        front_quality=front_quality,
        hook=hook,
        tldr=tldr,
    )
