"""
Bulk translator for the auxiliary Hinglish dicts in narratives.py:
  FOCUS_2026         (inside life_summary_block)
  WHY / IMPACT / ACTION / HOUSE_ACTION   (inside why_impact_action_for_number)
  _LUCKY_COLOURS     (vehicle / business / gemstone_tone strings)
  _MONTH_THEMES

Output: scripts/_extras_out.py — Python module with EN and HI variants
ready for merge into narratives.py.
"""

from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from openai import OpenAI

from vedic.numerology.narratives import _LUCKY_COLOURS, _MONTH_THEMES

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
MODEL = "gpt-4o"

SYSTEM = """You translate Hinglish (Roman-script Hindi mixed with English)
into TWO pure target languages:

- english : natural fluent English. NO Hindi transliteration. Keep proper
            nouns (Surya, Chandra, Mangal, Brihaspati, Shukra, Shani, Rahu,
            Ketu, Budha, Mantra, Yantra, planet names). Numbers as digits.
            Tone is warm, direct, slightly mystical but practical.
- hindi   : pure Devanagari Hindi. NO Roman characters except brand-style
            proper nouns where unavoidable. Same tone.

Output VALID JSON only — no markdown fences, no commentary. The output
must mirror the input shape exactly: same keys, same nesting, same list
lengths. Wrap as { "english": {...}, "hindi": {...} } when so requested.
"""


def translate_obj(label: str, obj) -> dict:
    """Translate a JSON-serialisable object; return {english, hindi}."""
    user_msg = (
        f"Translate this {label} block into English and Hindi as specified. "
        "Preserve the exact key/list shape. Return only the JSON object "
        '{ "english": ..., "hindi": ... }.\n\n'
        + json.dumps(obj, ensure_ascii=False, indent=2)
    )
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user_msg},
        ],
    )
    return json.loads(resp.choices[0].message.content)


# --- Source dicts (the Hinglish source of truth) ---------------------------

FOCUS_2026_HG = {
    1: "Independent venture launch — apna kuch shuru karein. Authority figures se reconcile.",
    2: "Emotional boundaries strengthen. Health (especially mother-link) attention.",
    3: "Teaching/writing income stream build. Higher education ya certification consider.",
    4: "Tech/foreign opportunity capture. Stop job-hopping — ek field me deep go.",
    5: "Multiple income streams crystallize. Communication-based business expand.",
    6: "Family + creative project balance. Long-pending relationship decision.",
    7: "Spiritual study deepen. Solo retreat. Practical world ignore mat karein.",
    8: "Foundation work — slow + steady. Real estate ya asset build. Father-bond heal.",
    9: "Channel anger constructively — sports/exercise mandatory. Big move possible.",
}

WHY_HG = {
    "mobile_1": "Mobile number Surya energy carry karta hai — har call/message me leadership vibration jaati hai.",
    "mobile_2": "Moon energy emotional fluctuation laata hai — mood swings ke saath calls.",
    "mobile_3": "Jupiter wisdom + financial expansion deta hai — knowledge-based calls profitable.",
    "mobile_4": "Rahu sudden, unexpected calls — opportunities + disruptions dono.",
    "mobile_5": "Mercury speed + business — sales, deals, networking me magic.",
    "mobile_6": "Venus harmony + relationships — love + family ka strong center.",
    "mobile_7": "Ketu mystery + isolation — important calls aati hain par interaction kam.",
    "mobile_8": "Saturn slow growth + karmic — official, government, long-term work me favourable.",
    "mobile_9": "Mars energy + courage — bold conversations, but anger ka risk.",
    "vehicle_1": "Vehicle 1 — leadership feel, par solo travel pattern.",
    "vehicle_2": "Vehicle 2 — emotional, family-friendly, par maintenance demanding.",
    "vehicle_3": "Vehicle 3 — growth-oriented, money brings.",
    "vehicle_4": "Vehicle 4 — sudden tech issues + unexpected breakdowns common. Modern car tho ok, classic avoid.",
    "vehicle_5": "Vehicle 5 — versatile, multi-purpose, business travel acha.",
    "vehicle_6": "Vehicle 6 — luxury, beauty, comfort — aapko impress karega.",
    "vehicle_7": "Vehicle 7 — solo-friendly, quiet drives suit.",
    "vehicle_8": "Vehicle 8 — heavy-duty, long-life, par initial repair phase.",
    "vehicle_9": "Vehicle 9 — sports/SUV style suit, par accident risk avg se zyada.",
    "house_1": "Ghar 1 — leadership family, head of household empowered.",
    "house_2": "Ghar 2 — emotional, mother-energy strong, peace-oriented.",
    "house_3": "Ghar 3 — wealth + wisdom flow karta hai.",
    "house_4": "Ghar 4 — sudden changes (renovations, guests, news) frequent.",
    "house_5": "Ghar 5 — busy, social, business-friendly home.",
    "house_6": "Ghar 6 — family + romance + beauty — best for relationships.",
    "house_7": "Ghar 7 — quiet, spiritual, study-suited.",
    "house_8": "Ghar 8 — initial struggle phase, baad me wealth-anchored.",
    "house_9": "Ghar 9 — energy + arguments + passion — pet/sports-friendly.",
}

IMPACT_HG = {
    "mobile_1": "Aap har conversation me 'main pehle' wala feel project karte ho — yeh leaders attract karta hai par juniors thake-thake feel karte hain.",
    "mobile_2": "Calls me aap zyada listen karte ho — log apni problems aapke saamne kholte hain, aap free counsellor ban jaate ho.",
    "mobile_3": "Knowledge-based calls aate hain — log advice ya teaching ke liye contact karte hain. Direct income link possible.",
    "mobile_4": "Phone par sudden good ya bad news aati hai — kabhi job offer, kabhi accident — emotional rollercoaster.",
    "mobile_5": "Phone par log naye opportunities, deals, contacts laate hain — aap natural networker ban jaate ho.",
    "mobile_6": "Phone par love + family + creative collaboration ka flow rehta hai — relationship strengthening.",
    "mobile_7": "Important calls miss kar dete ho — phone par aap distant rehte ho, log notice karte hain.",
    "mobile_8": "Phone par official/government communication zyada — bureaucratic delays, paperwork, court matters connect.",
    "mobile_9": "Phone par arguments quick, anger explosions easy — relationship me stress.",
    "vehicle_1": "Vehicle aapko 'lone driver' me zyada comfortable rakhta hai — long solo road trips aapke favourites.",
    "vehicle_2": "Family trips ke liye perfect — par fuel + maintenance bill expected se zyada.",
    "vehicle_3": "Vehicle ke saath income generation possible — Uber/cab side ya business travel.",
    "vehicle_4": "Hidden electrical/electronic issues regular — yearly mech checkup MUST. Insurance comprehensive.",
    "vehicle_5": "Vehicle business + personal use dono — versatile, multiple purpose serve karta hai.",
    "vehicle_6": "Vehicle aapki personality statement banti hai — log judge karte hain. Maintenance priority.",
    "vehicle_7": "Long drives me clarity milti hai — solo driving aapki therapy ban jaati hai.",
    "vehicle_8": "Vehicle long lasting (10+ saal easily) — par initial 1-2 saal frustrating.",
    "vehicle_9": "Speed + power feel chahiye — par over-speeding ka risk avg se zyada. Defensive driving habit MUST.",
    "house_1": "Ghar me aap dominant ho — sab aapki maante hain. Par 'me-time' nahi milta — recharge mushkil.",
    "house_2": "Ghar emotional safe-haven hai sabke liye — par boundaries weak, koi bhi aake bana sakta hai.",
    "house_3": "Ghar me wealth flow hota hai — bills automatically manage, savings build.",
    "house_4": "Ghar me 6-12 mahine me kuch na kuch sudden change (renovation, member shift, repair) hota rehta hai.",
    "house_5": "Ghar party-house ban jaata hai — log freely aate hain. Productivity ke liye dedicated quiet space chahiye.",
    "house_6": "Ghar romance + family bonding ka center hai — sundar interior + happy memories.",
    "house_7": "Ghar spiritual energy carry karta hai — meditation + study yahan productive.",
    "house_8": "Ghar me initial phase financial struggle, par 5+ saal me wealth crystallize.",
    "house_9": "Ghar me energy zyada hoti hai — arguments + makeup cycle. Pet ya sport equipment fit.",
}

ACTION_HG = {
    "mobile_1": "Important calls Sunday subah karein. Number ke saath red mobile cover use kare.",
    "mobile_2": "Important calls Monday karein. White ya silver cover. Late-night calls avoid (Moon weak).",
    "mobile_3": "Thursday subah important deal calls. Yellow cover. Hora time use karein.",
    "mobile_4": "Mobile ko 'silent + DND' raat me — Rahu raat me mind disturb karta hai. Tech calls Saturday.",
    "mobile_5": "Wednesday subah deals + sales calls. Green cover. Multi-tasking phone karte waqt avoid.",
    "mobile_6": "Friday important relationship/love calls. White ya pink cover. Music + harmony tones.",
    "mobile_7": "Tuesday/Saturday important spiritual calls. Multi-color cover. Solo time jaroori.",
    "mobile_8": "Saturday subah official + government calls. Black cover. Patience + structured talk.",
    "mobile_9": "Tuesday subah strategic calls. Red cover. 24-hour rule before angry response.",
    "vehicle_1": "Sunday subah vehicle pooja. Red ribbon. Red dashboard mat. Owner solo drive priority.",
    "vehicle_2": "Monday subah pooja. White flowers. Family trips Monday/Friday.",
    "vehicle_3": "Thursday pooja. Yellow ribbon. Business travel Thursday lucky.",
    "vehicle_4": "Saturday pooja. Tech check har 6 mahine. Comprehensive insurance MUST.",
    "vehicle_5": "Wednesday pooja. Green/yellow ribbon. Long drives Wednesday productive.",
    "vehicle_6": "Friday pooja. White flowers. Vehicle clean + perfumed always.",
    "vehicle_7": "Tuesday pooja. Solo time vehicle me allow karein.",
    "vehicle_8": "Saturday pooja. Black umbrella keep. Annual full service NEVER skip.",
    "vehicle_9": "Tuesday pooja. Red flag/sticker. Defensive driving course recommended.",
}

HOUSE_ACTION_HG = {
    1: "Sunday subah ghar pooja, Surya namaskar terrace par, red rangoli at entrance.",
    2: "Monday Chandra pooja, white flowers entrance par, water-fountain (north) consider.",
    3: "Thursday Brihaspati pooja, yellow paint accents, wisdom books visible.",
    4: "Saturday Rahu pacification, tech corner kept clean, blue lights bedroom avoid.",
    5: "Wednesday Budha pooja, green plants, study/work corner dedicated.",
    6: "Friday Shukra pooja, fresh flowers daily, art on walls, mirror placement north-east.",
    7: "Tuesday/Saturday meditation corner, multi-color decor, quiet zone protected.",
    8: "Saturday Shani pooja, black-stone entrance, structured + minimal interior.",
    9: "Tuesday Mangal pooja, red curtains south-room, kitchen + fire-area south-east.",
}

# Lucky-colours: vehicle/business/gemstone_tone strings only (colour names stay)
LUCKY_COLOUR_STRINGS_HG = {
    d: {
        "vehicle":   _LUCKY_COLOURS[d]["vehicle"],
        "business":  _LUCKY_COLOURS[d]["business"],
        "gemstone_tone": _LUCKY_COLOURS[d]["gemstone_tone"],
    }
    for d in range(1, 10)
}

MONTH_THEMES_HG = dict(_MONTH_THEMES)


JOBS = [
    ("FOCUS_2026", FOCUS_2026_HG),
    ("WHY",        WHY_HG),
    ("IMPACT",     IMPACT_HG),
    ("ACTION",     ACTION_HG),
    ("HOUSE_ACTION", HOUSE_ACTION_HG),
    ("LUCKY_COLOUR_STRINGS", LUCKY_COLOUR_STRINGS_HG),
    ("MONTH_THEMES", MONTH_THEMES_HG),
]


def main() -> None:
    results: dict = {}
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = {pool.submit(translate_obj, name, src): name
                for name, src in JOBS}
        for fut in as_completed(futs):
            name = futs[fut]
            try:
                pair = fut.result()
            except Exception as exc:  # noqa: BLE001
                print(f"  !! {name} failed: {exc}", flush=True)
                continue
            results[name] = pair
            print(f"  {name} done", flush=True)
    print(f"all extras in {time.time()-t0:.1f}s")

    out = ROOT / "scripts" / "_extras_out.py"
    with out.open("w", encoding="utf-8") as f:
        f.write("# AUTO-GENERATED by scripts/translate_extras.py\n\n")
        for name, pair in results.items():
            f.write(f"{name}_EN = {pair.get('english')!r}\n\n")
            f.write(f"{name}_HI = {pair.get('hindi')!r}\n\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
