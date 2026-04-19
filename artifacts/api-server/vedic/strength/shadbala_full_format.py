"""
Sprint 29 / Phase B — Full Shadbala sub-bala formatter
Surfaces ALL Sthana 5-sub + Kala 9-sub + Yuddha to LOCKED FACTS text.
The underlying calcs already exist in shadbala.py + bala_deep.py — this
just exposes them to AI-visible payload.
"""
from __future__ import annotations
from typing import Any


def format_shadbala_full(shadbala: dict[str, Any] | None,
                         bala_deep: dict[str, Any] | None) -> str:
    if not isinstance(shadbala, dict) and not isinstance(bala_deep, dict):
        return ""
    lines = ["── SHADBALA FULL SUB-BALAS (Sprint 29 / Phase B) ──"]

    # Sthana Bala 5-sub + Kala Bala from shadbala.py
    # Structure: {planet: {parts: {sthana, sthana_breakdown:{uchha,oja,kendra,drekkana},
    #                                dig, paksha, chesta, naisargika, drik}}}
    if isinstance(shadbala, dict):
        lines.append("Sthana Bala (5 sub-balas — uchha/oja/kendra/drekkana from shadbala, saptavargaja from bala_deep):")
        sap_map = {}
        if isinstance(bala_deep, dict):
            sap_data = bala_deep.get("saptavargaja_bala") or {}
            if isinstance(sap_data, dict):
                sap_map = sap_data

        for planet, info in shadbala.items():
            if not isinstance(info, dict):
                continue
            parts = info.get("parts") or {}
            br = parts.get("sthana_breakdown") or {}
            uch = br.get("uchha")
            oja = br.get("oja")
            ken = br.get("kendra")
            drk = br.get("drekkana")
            sap = sap_map.get(planet)
            row = []
            if uch is not None: row.append(f"Uchchabala={uch}v")
            if sap is not None: row.append(f"Saptavargaja={sap}v")
            if oja is not None: row.append(f"Ojayugma={oja}v")
            if ken is not None: row.append(f"Kendradi={ken}v")
            if drk is not None: row.append(f"Drekkana={drk}v")
            if row:
                lines.append(f"  {planet}: {', '.join(row)} → Sthana total={parts.get('sthana')}v")

        lines.append("Kala Bala (paksha/chesta/naisargika/drik + extended day-time balas):")
        for planet, info in shadbala.items():
            if not isinstance(info, dict):
                continue
            parts = info.get("parts") or {}
            pak = parts.get("paksha")
            che = parts.get("chesta")
            nai = parts.get("naisargika")
            dri = parts.get("drik")
            dig = parts.get("dig")
            row = []
            if pak is not None: row.append(f"Paksha={pak}v")
            if che is not None: row.append(f"Chesta={che}v")
            if nai is not None: row.append(f"Naisargika={nai}v")
            if dri is not None: row.append(f"Drik={dri}v")
            if dig is not None: row.append(f"DigBala={dig}v")
            if row:
                lines.append(f"  {planet}: {', '.join(row)}")

        lines.append("Shadbala totals (virupas / required → strength %):")
        for planet, info in shadbala.items():
            if not isinstance(info, dict):
                continue
            t = info.get("total"); rq = info.get("required"); pct = info.get("strength_pct")
            if t is not None:
                lines.append(f"  {planet}: {t}v / {rq}v → {pct}%")

    # Yuddha Bala from bala_deep
    if isinstance(bala_deep, dict):
        yb = bala_deep.get("yuddha_bala")
        if yb:
            lines.append("Yuddha Bala (Planetary War — within 1° in same sign):")
            if isinstance(yb, dict):
                for planet, val in yb.items():
                    lines.append(f"  {planet}: {val}")
            elif isinstance(yb, list) and yb:
                for entry in yb[:5]:
                    lines.append(f"  {entry}")
            else:
                lines.append(f"  (no planetary war active)")
        else:
            lines.append("Yuddha Bala: no planetary war active in current chart")

    return "\n".join(lines)
