"""Per-engine template configs — astrology rules differ; pipeline is identical."""
from __future__ import annotations

from typing import Any

from ..engine_spec import EngineSpec
from ..schema import EngineOutputV2
from .commitment_spec import commitment_spec
from .loyalty_spec import loyalty_spec


def _compat_post_process(output: EngineOutputV2, kundli: dict, sig: Any) -> EngineOutputV2:
    try:
        from ask_mr.engines.compatibility import (
            _synthesize_emotional_compatibility,
            _synthesize_gun_milan,
            _synthesize_intellectual_compatibility,
            _synthesize_mental_compatibility,
            _synthesize_values_goals_compatibility,
        )

        intent = (output.question_intent or output.checks.get("compat_intent") or "").strip()
        if not intent or intent == "general_compatibility":
            return output
        output.checks["question_intent"] = intent
        label = {
            "emotional_compatibility": "Emotional compatibility",
            "mental_compatibility": "Mental compatibility",
            "intellectual_compatibility": "Intellectual compatibility",
            "values_goals_compatibility": "Values and life-goals fit",
            "gun_milan": "Gun milan / traditional match",
            "general_compatibility": "Overall compatibility",
        }.get(intent, "Overall compatibility")
        _, _, tail = output.verdict.headline.partition(":")
        output.verdict.headline = f"{label}:{tail or ' mixed — communication and respect matter'}"
        if intent == "emotional_compatibility":
            extra = _synthesize_emotional_compatibility(kundli, sig)
        elif intent == "mental_compatibility":
            extra = _synthesize_mental_compatibility(kundli, sig)
        elif intent == "intellectual_compatibility":
            extra = _synthesize_intellectual_compatibility(kundli, sig)
        elif intent == "values_goals_compatibility":
            extra = _synthesize_values_goals_compatibility(kundli, sig)
        elif intent == "gun_milan":
            extra = _synthesize_gun_milan(kundli, sig)
        else:
            extra = []
        for line in extra[:3]:
            if line not in output.evidence["neutral"]:
                output.evidence["neutral"].append(line)
    except Exception:
        pass
    return output


def _compat_context(question: str, kundli: dict, sig: Any) -> dict[str, Any]:
    try:
        from ask_mr.engines.compatibility import _compatibility_intent

        return {"question": question, "compat_intent": _compatibility_intent(question)}
    except Exception:
        return {}


def _compat_intent(question: str) -> str:
    try:
        from ask_mr.engines.compatibility import _compatibility_intent

        return _compatibility_intent(question)
    except Exception:
        return "compatibility"


_ENGINE_SPECS: dict[str, EngineSpec] = {
    "commitment": commitment_spec(),
    "loyalty_trust": loyalty_spec(),
    "compatibility": EngineSpec(
        engine_id="compatibility",
        rule_prefix="COMP",
        base_score=58,
        levels=((75, "supportive"), (62, "moderate"), (48, "mixed"), (0, "strained")),
        headlines={
            "supportive": "Overall compatibility: supportive — bond can grow with respect and care",
            "moderate": "Overall compatibility: moderate — mel hai, patience aur clear talk chahiye",
            "mixed": "Overall compatibility: mixed — alignment hai par friction points active hain",
            "strained": "Overall compatibility: strained patterns — effort and boundaries are important",
        },
        positive_signal_keys=("5th lord strong", "Moon-Moon supportive", "emotional reopening"),
        negative_signal_keys=("saturn_on_7th", "mars_on_7th", "moon_afflicted", "rahu_on_7th_axis"),
        resolve_intent=_compat_intent,
        build_context=_compat_context,
        post_process=_compat_post_process,
    ),
    "breakup_risk": EngineSpec(
        engine_id="breakup_risk",
        rule_prefix="BREAKUP",
        base_score=52,
        levels=((75, "low"), (60, "moderate"), (45, "elevated"), (0, "high")),
        headlines={
            "low": "Breakup/separation risk: low — repair capacity can hold the bond",
            "moderate": "Breakup/separation risk: moderate — friction needs timely repair",
            "elevated": "Breakup/separation risk: elevated — distance themes need boundaries",
            "high": "Breakup/separation risk: high — repeated friction can weaken the bond",
        },
        positive_signal_keys=("reconnection_yoga",),
        negative_signal_keys=("separation_yoga", "saturn_on_7th", "mars_on_7th", "third_person_risk"),
    ),
    "patchup": EngineSpec(
        engine_id="patchup",
        rule_prefix="PATCH",
        base_score=55,
        levels=((75, "favorable"), (60, "possible"), (45, "weak"), (0, "unlikely")),
        headlines={
            "favorable": "Patch-up/reconciliation: favorable — reconnection support is visible",
            "possible": "Patch-up/reconciliation: possible — effort and honest talk matter",
            "weak": "Patch-up/reconciliation: weak right now — distance themes are active",
            "unlikely": "Patch-up/reconciliation: unlikely without real repair and clarity",
        },
        positive_signal_keys=("reconnection_yoga", "5th lord strong", "emotional reopening"),
        negative_signal_keys=("separation_yoga", "saturn_on_7th", "mars_on_7th", "moon_afflicted"),
    ),
    "partner_nature": EngineSpec(
        engine_id="partner_nature",
        rule_prefix="PNAT",
        base_score=58,
        levels=((75, "balanced"), (62, "mixed"), (48, "complex"), (0, "challenging")),
        headlines={
            "balanced": "Partner nature: balanced — steady temperament with room to grow",
            "mixed": "Partner nature: mixed traits — patience helps decode their style",
            "complex": "Partner nature: complex — strong pulls need clear boundaries",
            "challenging": "Partner nature: challenging patterns — realism beats fantasy",
        },
        positive_signal_keys=("5th lord strong", "jupiter_supportive"),
        negative_signal_keys=("mars_on_7th", "rahu_on_7th_axis", "venus_mars_conjunct_tight"),
        narrator_plan="2–3 sentences: partner temperament → one strength → one watch-out",
        ignore=("timing dates unless asked", "breakup risk", "manglik unless asked"),
    ),
    "communication": EngineSpec(
        engine_id="communication",
        rule_prefix="COMM",
        base_score=57,
        levels=((75, "clear"), (62, "uneven"), (48, "strained"), (0, "blocked")),
        headlines={
            "clear": "Communication: mostly clear — honest talk can bridge gaps",
            "uneven": "Communication: uneven — timing and tone matter a lot",
            "strained": "Communication: strained — misunderstandings need patience",
            "blocked": "Communication: blocked pattern — ego or distance may mute clarity",
        },
        positive_signal_keys=("mercury_strong", "5th lord strong"),
        negative_signal_keys=("mercury_afflicted", "saturn_on_7th", "mars_on_7th"),
    ),
    "emotional_attachment": EngineSpec(
        engine_id="emotional_attachment",
        rule_prefix="EMOT",
        base_score=56,
        levels=((75, "secure"), (62, "mixed"), (48, "anxious"), (0, "volatile")),
        headlines={
            "secure": "Emotional attachment: secure — bond can deepen with care",
            "mixed": "Emotional attachment: mixed — reassurance helps stability",
            "anxious": "Emotional attachment: anxious — fear of loss may spike reactions",
            "volatile": "Emotional attachment: volatile — highs and lows need grounding",
        },
        positive_signal_keys=("emotional reopening", "5th lord strong"),
        negative_signal_keys=("moon_afflicted", "separation_yoga", "obsession_pull"),
    ),
    "secret_relationship": EngineSpec(
        engine_id="secret_relationship",
        rule_prefix="SECR",
        base_score=50,
        levels=((70, "low"), (55, "possible"), (40, "likely"), (0, "high")),
        headlines={
            "low": "Secret/third-person risk: low — transparency themes look manageable",
            "possible": "Secret/third-person risk: possible — hidden attention needs clarity",
            "likely": "Secret/third-person risk: likely — secrecy patterns are active",
            "high": "Secret/third-person risk: high — parallel attention weakens trust",
        },
        positive_signal_keys=(),
        negative_signal_keys=(
            "third_person_risk", "loyalty_risk_high", "hidden_ties", "parallel_attention",
        ),
        narrator_plan="2–3 sentences: secrecy risk level → evidence → boundary advice",
        ignore=("timing dates unless asked", "marriage promise", "spouse profession"),
    ),
    "family_approval": EngineSpec(
        engine_id="family_approval",
        rule_prefix="FAM",
        base_score=54,
        levels=((75, "supportive"), (60, "mixed"), (45, "resistant"), (0, "unlikely")),
        headlines={
            "supportive": "Family approval: supportive — elders may soften with respect",
            "mixed": "Family approval: mixed — patience and diplomacy matter",
            "resistant": "Family approval: resistant — social/family friction is active",
            "unlikely": "Family approval: unlikely soon — expectations clash strongly",
        },
        positive_signal_keys=("jupiter_supportive", "5th lord strong"),
        negative_signal_keys=("saturn_on_7th", "rahu_on_7th_axis"),
        narrator_plan="2–3 sentences: family stance → strongest social factor → practical step",
    ),
    "long_distance": EngineSpec(
        engine_id="long_distance",
        rule_prefix="LDIST",
        base_score=55,
        levels=((75, "sustainable"), (62, "mixed"), (48, "fragile"), (0, "strained")),
        headlines={
            "sustainable": "Long-distance: sustainable — trust and rhythm can hold",
            "mixed": "Long-distance: mixed — distance tests consistency",
            "fragile": "Long-distance: fragile — gaps may widen without effort",
            "strained": "Long-distance: strained — reunion or clarity may be needed",
        },
        positive_signal_keys=("reconnection_yoga", "5th lord strong"),
        negative_signal_keys=("separation_yoga", "moon_afflicted", "third_person_risk"),
    ),
    "toxicity": EngineSpec(
        engine_id="toxicity",
        rule_prefix="TOX",
        base_score=48,
        levels=((70, "low"), (55, "moderate"), (40, "elevated"), (0, "high")),
        headlines={
            "low": "Toxicity/red flags: low — friction looks repairable",
            "moderate": "Toxicity/red flags: moderate — patterns need honest boundaries",
            "elevated": "Toxicity/red flags: elevated — control or hurt themes active",
            "high": "Toxicity/red flags: high — self-protection comes first",
        },
        positive_signal_keys=(),
        negative_signal_keys=(
            "mars_on_7th", "rahu_on_7th_axis", "moon_afflicted", "obsession_pull",
        ),
        narrator_plan="2–3 sentences: toxicity level → strongest red flag → boundary advice",
    ),
    "one_sided_love": EngineSpec(
        engine_id="one_sided_love",
        rule_prefix="ONESD",
        base_score=52,
        levels=((75, "reciprocal"), (60, "unclear"), (45, "one_sided"), (0, "unlikely")),
        headlines={
            "reciprocal": "One-sided love: reciprocal potential — mutual effort can grow",
            "unclear": "One-sided love: unclear — mixed signals need honest talk",
            "one_sided": "One-sided love: one-sided pull — your effort may outweigh theirs",
            "unlikely": "One-sided love: unlikely reciprocity — realism protects peace",
        },
        positive_signal_keys=("emotional reopening", "5th lord strong"),
        negative_signal_keys=("moon_afflicted", "separation_yoga", "third_person_risk"),
    ),
    "chemistry": EngineSpec(
        engine_id="chemistry",
        rule_prefix="CHEM",
        base_score=60,
        levels=((75, "strong"), (62, "moderate"), (48, "uneven"), (0, "low")),
        headlines={
            "strong": "Chemistry/attraction: strong — spark is visible in the chart",
            "moderate": "Chemistry/attraction: moderate — attraction grows with comfort",
            "uneven": "Chemistry/attraction: uneven — pull fluctuates",
            "low": "Chemistry/attraction: low — emotional bond may matter more",
        },
        positive_signal_keys=("venus_mars_conjunct_tight", "5th lord strong"),
        negative_signal_keys=("venus_afflicted", "mars_on_7th"),
        ignore=("timing dates unless asked", "breakup risk", "family approval"),
    ),
    "bed_intimacy": EngineSpec(
        engine_id="bed_intimacy",
        rule_prefix="INTIM",
        base_score=58,
        levels=((75, "harmonious"), (62, "mixed"), (48, "sensitive"), (0, "strained")),
        headlines={
            "harmonious": "Physical intimacy: harmonious — comfort and consent align",
            "mixed": "Physical intimacy: mixed — communication about needs helps",
            "sensitive": "Physical intimacy: sensitive — stress or distance may affect closeness",
            "strained": "Physical intimacy: strained — emotional safety comes first",
        },
        positive_signal_keys=("venus_mars_conjunct_tight", "5th lord strong"),
        negative_signal_keys=("mars_on_7th", "saturn_on_7th", "moon_afflicted"),
        ignore=("timing dates unless asked", "third-person affairs", "spouse profession"),
    ),
    "karmic_marriage": EngineSpec(
        engine_id="karmic_marriage",
        rule_prefix="KARM",
        base_score=55,
        levels=((75, "strong"), (62, "present"), (48, "mixed"), (0, "weak")),
        headlines={
            "strong": "Karmic marriage bond: strong — lessons and depth are highlighted",
            "present": "Karmic marriage bond: present — growth through patience",
            "mixed": "Karmic marriage bond: mixed — fate and free will both matter",
            "weak": "Karmic marriage bond: weak signal — practical compatibility still counts",
        },
        positive_signal_keys=("nodes_on_7th", "saturn_moon_link"),
        negative_signal_keys=("separation_yoga",),
    ),
    "relationship_future": EngineSpec(
        engine_id="relationship_future",
        rule_prefix="RFUT",
        base_score=57,
        levels=((75, "promising"), (62, "mixed"), (48, "uncertain"), (0, "weak")),
        headlines={
            "promising": "Relationship future: promising — bond can mature with effort",
            "mixed": "Relationship future: mixed — direction needs clarity",
            "uncertain": "Relationship future: uncertain — patience before big decisions",
            "weak": "Relationship future: weak signal — realism protects you",
        },
        positive_signal_keys=("5th lord strong", "reconnection_yoga"),
        negative_signal_keys=("separation_yoga", "saturn_on_7th", "third_person_risk"),
    ),
    "relationship_decisions": EngineSpec(
        engine_id="relationship_decisions",
        rule_prefix="RDEC",
        base_score=56,
        levels=((75, "favorable"), (62, "wait"), (48, "cautious"), (0, "avoid")),
        headlines={
            "favorable": "Relationship decision: favorable — clarity supports a forward step",
            "wait": "Relationship decision: wait — more information or timing helps",
            "cautious": "Relationship decision: cautious — don't rush under pressure",
            "avoid": "Relationship decision: avoid impulse — boundaries protect peace",
        },
        positive_signal_keys=("5th lord strong", "jupiter_supportive"),
        negative_signal_keys=("separation_yoga", "third_person_risk", "loyalty_risk_high"),
    ),
    "relationship_verification": EngineSpec(
        engine_id="relationship_verification",
        rule_prefix="RVER",
        base_score=54,
        levels=((75, "consistent"), (62, "mixed"), (48, "inconsistent"), (0, "unreliable")),
        headlines={
            "consistent": "Relationship verification: consistent — words and actions align",
            "mixed": "Relationship verification: mixed — cross-check before trusting fully",
            "inconsistent": "Relationship verification: inconsistent — gaps need honest talk",
            "unreliable": "Relationship verification: unreliable — proof over promises",
        },
        positive_signal_keys=("5th lord strong", "Saturn-Moon link"),
        negative_signal_keys=("third_person_risk", "loyalty_risk_high", "hidden_ties"),
        narrator_plan="2–3 sentences: consistency level → strongest proof gap → practical check",
    ),
    "relationship_remedies": EngineSpec(
        engine_id="relationship_remedies",
        rule_prefix="REM",
        base_score=55,
        levels=((75, "supportive"), (62, "moderate"), (48, "cautious"), (0, "limited")),
        headlines={
            "supportive": "Relationship remedies: supportive — gentle upay may help harmony",
            "moderate": "Relationship remedies: moderate — behavior and prayer over shortcuts",
            "cautious": "Relationship remedies: cautious — fix the pattern, not just symptoms",
            "limited": "Relationship remedies: limited — remedies can't replace toxic dynamics",
        },
        positive_signal_keys=("jupiter_supportive", "5th lord strong"),
        negative_signal_keys=("mars_on_7th", "rahu_on_7th_axis"),
        narrator_plan="2–3 sentences: remedy scope → affliction evidence → safe practical upay",
        ignore=(
            "expensive gemstone without multi-module proof",
            "guaranteed miracle claims",
            "spouse profession",
        ),
    ),
}


def get_engine_spec(engine_id: str) -> EngineSpec | None:
    return _ENGINE_SPECS.get((engine_id or "").strip().lower())


def all_engine_specs() -> dict[str, EngineSpec]:
    return dict(_ENGINE_SPECS)
