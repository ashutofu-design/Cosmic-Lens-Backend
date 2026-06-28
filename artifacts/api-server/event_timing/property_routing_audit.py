"""Audit helper — map property/vehicle real-life Q → engine family."""
from __future__ import annotations

import re
from typing import Optional

from event_timing.timing_router import resolve_timing_domain

_TIMING_HINT = re.compile(
    r"(?ix)\b(kab|kab\s+tak|kis\s+(saal|mahine|month|year)|muhurat|banega|banegi|"
    r"milega|milegi|hoga|hogi|honge|aayega|pahuchegi|chuki|sanction|sign\s+hoga|"
    r"liquid|active|lagenge|rukhega|khali\s+hoga|faisla|poora\s+hoga)\b",
)
_PROPERTY_RX = re.compile(
    r"(?ix)\b(ghar|makaan|makan|property|flat|plot|zameen|registry|possession|"
    r"griha|construction|builder|bayaana|token|commercial\s+property|residential|"
    r"down[\s-]?payment|pustaini|ancestral|virasat|hissa|vivaad|vasiyat|kabza|"
    r"encroachment|grahak|buyer|bik|bech|sell|liquidate|renovation|vastu|broker|"
    r"dda|mhada|awas\s+yojna|housing\s+scheme|"
    r"parivaar|dhoka|dushman|compromise|mamle|police|afsar"
    r")\b",
)
_VEHICLE_RX = re.compile(
    r"(?ix)\b(car|bike|gaadi|gadi|scooter|vehicle|two[\s-]?wheeler|four[\s-]?wheeler|"
    r"audi|bmw|luxury\s+car|ev|electric\s+vehicle|commercial\s+vehicle|truck|taxi|"
    r"vip|fancy\s+plate|number\s+plate|driving|gaadiyon"
    r")\b",
)
_FINANCE_RX = re.compile(r"(?ix)\b(loan|emi|karz|debt|down[\s-]?payment|sanction|capital\s+gains|income\s+tax)\b")
_LIT_RX = re.compile(r"(?ix)\b(court\s+case|faisla|verdict|vakeel|injunction|stay\s+order|litigation|mukadma)\b")


def classify_engine_family(question: str) -> str:
    q = question or ""

    # Static vehicle before timing router (advice Qs use milega/hoga but are not kab)
    if _VEHICLE_RX.search(q) and not re.search(r"(?ix)\bbike\s+hue\b", q):
        try:
            from ask_vehicle.vehicle_registry import is_vehicle_static_question

            if is_vehicle_static_question(q):
                dom, _b, is_timing = resolve_timing_domain(q)
                if dom == "vehicle" and is_timing:
                    pass
                elif not re.search(r"(?ix)\b(kab|rukhega|road\s+trip)\b", q):
                    return "vehicle_static"
        except Exception:
            pass

    dom, _bkt, is_timing = resolve_timing_domain(q)

    if dom == "vehicle" and is_timing:
        return "vehicle_timing"
    if dom == "property" and is_timing:
        return "property_timing"
    if dom == "litigation" and is_timing:
        return "litigation"
    if dom == "finance" and is_timing:
        return "finance_timing"
    if dom == "travel" and is_timing and _VEHICLE_RX.search(q) and re.search(
        r"(?ix)\b(road\s+trip|gaadi|gadi|car|bike)\b", q
    ):
        return "vehicle_timing"

    # Static vehicle (colour, new vs used, safety, etc.)
    if _VEHICLE_RX.search(q) and not re.search(r"(?ix)\bbike\s+hue\b", q):
        try:
            from ask_vehicle.vehicle_registry import is_vehicle_static_question

            if is_vehicle_static_question(q) and not re.search(
                r"(?ix)\b(kab|road\s+trip|rukhega|maintenance)\b", q
            ):
                return "vehicle_static"
        except Exception:
            pass

    # Static litigation (outcome, lawyer, fees — no kab)
    if _LIT_RX.search(q) and not _TIMING_HINT.search(q):
        try:
            from ask_litigation.litigation_registry import is_litigation_static_question

            if is_litigation_static_question(q):
                return "litigation"
        except Exception:
            pass
        if not _PROPERTY_RX.search(q):
            return "litigation"

    if _PROPERTY_RX.search(q):
        if re.search(r"(?ix)\bbike\s+hue\b", q):
            return "property_static"
        if _LIT_RX.search(q) and _TIMING_HINT.search(q):
            return "property_timing"
        if _FINANCE_RX.search(q) and _TIMING_HINT.search(q) and (
            "ghar" in q.lower() or "home" in q.lower() or "property" in q.lower()
        ):
            return "property_timing"
        if _TIMING_HINT.search(q):
            return "property_timing"
        try:
            from ask_property.property_registry import is_property_static_question

            if is_property_static_question(q):
                return "property_static"
        except Exception:
            pass
        try:
            from property_static.property_routing import is_property_question

            if is_property_question(q):
                return "property_static"
        except Exception:
            pass
        return "property_static"

    if _FINANCE_RX.search(q) and _TIMING_HINT.search(q):
        return "finance_timing"
    if _LIT_RX.search(q) and _TIMING_HINT.search(q):
        return "litigation"
    if re.search(
        r"(?ix)\b(dhoka|chehra|compromise|dushman|parivaar|mamle|vivaad|hissa|pitrusti)\b",
        q,
    ) and _TIMING_HINT.search(q):
        return "property_timing"

    return "llm"
