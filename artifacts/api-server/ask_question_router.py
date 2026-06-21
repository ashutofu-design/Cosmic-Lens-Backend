"""Ask route split — Engine (timing / kab?) vs Cosmo LLM (narrative / kya-kaisa).

Client may send ``ask_route`` = ``timing`` | ``narrative``. When absent we
auto-detect from the question text.
"""

from __future__ import annotations

import re
from typing import Literal, Optional, Tuple

AskRoute = Literal["timing", "narrative"]

_TIMING_RX = re.compile(
    r"(?ix)"
    r"\b("
    r"kab|kabhi[\s\-]?kab|kab[\s\-]?tak|kab[\s\-]?hoga|kab[\s\-]?hogi|"
    r"kab[\s\-]?milega|kab[\s\-]?milegi|kab[\s\-]?aayega|kab[\s\-]?aayegi|"
    r"kis[\s\-]?saal|kis[\s\-]?mahine|konse[\s\-]?saal|kaunse[\s\-]?mahine|"
    r"kitne[\s\-]?saal|kitne[\s\-]?mahine|kitne[\s\-]?din|"
    r"when|by[\s\-]?when|how[\s\-]?soon|how[\s\-]?long|"
    r"what[\s\-]?year|which[\s\-]?year|what[\s\-]?month|which[\s\-]?month|"
    r"timing|timeline|muhurat|muhurta|samay|window"
    r")\b"
)

_NARRATIVE_RX = re.compile(
    r"(?ix)"
    r"\b("
    r"kya\s+result|result\s+kya|kaisa|kaisi|kaise|kyun|kyu|"
    r"dikhe|dikhti|dikhne|nature|character|quality|direction|"
    r"strong|weak|effect|prabhav|favourable|unfavourable|"
    r"samjhao|explain|detail|meaning|matlab|"
    r"hoga\s+ya|possible|likely|chances|pattern|"
    r"\d{1,2}(?:st|nd|rd|th)?\s*(?:house|bhav|bhaav|ghar)\b|"
    r"\d{1,2}\s*h\b"
    r")\b"
)


def detect_ask_route(question: str) -> AskRoute:
    q = (question or "").strip()
    if not q:
        return "narrative"
    has_timing = bool(_TIMING_RX.search(q))
    has_narrative = bool(_NARRATIVE_RX.search(q))
    if has_timing and not has_narrative:
        return "timing"
    if has_narrative and not has_timing:
        return "narrative"
    if has_timing:
        return "timing"
    return "narrative"


def route_mismatch_message(requested: AskRoute, detected: AskRoute) -> str:
    if requested == "timing":
        return (
            "Yeh sawaal timing (Kab?) wala nahi lagta. Upar **Cosmo Analysis** "
            "tab choose karke dubara puchiye — wahan house, planet aur divisional "
            "chart se detail milti hai."
        )
    return (
        "Yeh sawaal timing (Kab?) wala hai. Upar **Event Timing** tab choose "
        "karke puchiye — engine dasha/transit se exact window batayega."
    )


def route_mismatch_response(requested: AskRoute, detected: AskRoute) -> dict:
    return {
        "text": route_mismatch_message(requested, detected),
        "topic": "route_hint",
        "confidence": 1.0,
        "source": "ask_route_mismatch",
        "engine_tag": "ans-cosmo",
        "follow_ups": [],
        "ask_route": requested,
        "ask_route_detected": detected,
    }


def resolve_ask_route(
    question: str,
    client_route: Optional[str] = None,
    *,
    strict_client: bool = True,
) -> Tuple[AskRoute, Optional[dict]]:
    """Return (route, mismatch_payload_or_None)."""
    detected = detect_ask_route(question)
    route = detected
    if client_route in ("timing", "narrative"):
        route = client_route  # type: ignore[assignment]
        if strict_client and route != detected:
            return route, route_mismatch_response(route, detected)
    return route, None


__all__ = [
    "AskRoute",
    "detect_ask_route",
    "resolve_ask_route",
    "route_mismatch_response",
    "route_mismatch_message",
]
