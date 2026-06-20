from __future__ import annotations

from vedic.love_reality.relationship_signals import PersonSignals, _analyze_person  # type: ignore
from vedic.love_reality.scoring_core import KundliReader


def build_person_signals(kundli: dict, *, default_name: str = "You") -> PersonSignals:
    k = dict(kundli or {})
    k.setdefault("name", default_name)
    r = KundliReader(k)
    return _analyze_person(r)


def clean_note(note: str, name: str = "You") -> str:
    return (note or "").replace(f"{name}'s ", "").replace(f"{name}: ", "").strip()


def pick_notes(sig: PersonSignals, keywords: list[str], *, limit: int = 6) -> list[str]:
    """Pick evidence lines whose notes match any keyword (planet+meaning embedded)."""
    out: list[str] = []
    for key in keywords:
        for n in sig.notes or []:
            if len(out) >= limit:
                return out
            if key.lower() in n.lower():
                c = clean_note(n, sig.name)
                if c and c not in out:
                    out.append(c)
    return out

