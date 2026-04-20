"""
Bulk translator for vedic/numerology/narratives.py

For each driver 2..9 in _NARRATIVES_HG, send the entry to OpenAI and
ask for a JSON object containing two parallel translations: a pure
English version and a pure Devanagari Hindi version. Driver 1 is
already hand-translated (used as the gold reference).

Output is written to scripts/_translations_out.py — a Python module
containing two dicts (_OUT_EN and _OUT_HI) that can be merged into
narratives.py.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from openai import OpenAI

from vedic.numerology.narratives import _NARRATIVES_HG, _NARRATIVES_EN

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
MODEL = "gpt-4o"

SYSTEM = """You are a professional translator specialising in Vedic
numerology / astrology content. You translate Hinglish (Roman-script
Hindi mixed with English) into TWO pure target languages:

- english  : natural, fluent, native English. NO transliteration of
             Hindi words. Keep proper nouns (Surya, Chandra, Mantra,
             Aditya Hridaya Stotra, Surya Namaskar, Lakshmi, Devi,
             Rahu, Ketu, Saturn, Jupiter etc.). Render numbers as
             numerals. Preserve the same paragraph structure, list
             length, and overall tone (warm, direct, slightly mystical
             but practical).

- hindi    : pure Devanagari Hindi. NO Roman characters at all except
             for proper-noun brand names if absolutely necessary.
             Numbers stay as Devanagari is not required — English digits
             1, 2, 3 are fine. Preserve the same structure, list length,
             tone, and depth.

Rules:
1. Output VALID JSON only. No prose, no markdown fences.
2. The output JSON must mirror the input JSON's shape exactly: same
   keys, same nesting, same list lengths.
3. Wrap the result as { "english": { ... full pack ... },
                        "hindi":   { ... full pack ... } }.
4. Where a value is a list of strings, return a list of the same length
   with each string translated.
5. Where a value is a single string, return a single string.
6. Preserve em-dashes (—) and quote characters.
7. Do not add or remove keys.
8. Astrology terminology accuracy matters more than literal word-for-word
   fidelity. Translate the *meaning* faithfully and naturally.
"""

# Use driver 1 as a few-shot reference so the model learns our register.
FEWSHOT_USER = json.dumps(_NARRATIVES_HG[1], ensure_ascii=False, indent=2)
FEWSHOT_ASSISTANT = json.dumps(
    {"english": _NARRATIVES_EN[1],
     "hindi": _NARRATIVES_EN[1]},  # placeholder; will overwrite below
    ensure_ascii=False, indent=2,
)


def translate_driver(driver: int) -> dict:
    src = _NARRATIVES_HG[driver]
    user_msg = (
        "Translate this driver-numerology pack into English and Hindi as "
        "specified. Return only the JSON object.\n\n"
        + json.dumps(src, ensure_ascii=False, indent=2)
    )
    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM},
            # Few-shot: show driver 1 input and our gold English so the model
            # mirrors our register. (We don't have a gold Hindi for driver 1
            # yet, so we let the model produce both.)
            {"role": "user", "content":
                "Example input (driver 1, Hinglish):\n\n"
                + json.dumps(_NARRATIVES_HG[1], ensure_ascii=False, indent=2)
                + "\n\nExample output (english half only — do the same quality):\n\n"
                + json.dumps({"english": _NARRATIVES_EN[1]},
                             ensure_ascii=False, indent=2)
            },
            {"role": "assistant", "content":
                "Understood. I will mirror that register and depth, and "
                "produce both english and hindi for the next driver."},
            {"role": "user", "content": user_msg},
        ],
    )
    txt = resp.choices[0].message.content
    return json.loads(txt)


def main() -> None:
    from concurrent.futures import ThreadPoolExecutor, as_completed
    out_en: dict = {}
    out_hi: dict = {}
    drivers = list(range(2, 10))
    t_start = time.time()
    with ThreadPoolExecutor(max_workers=8) as pool:
        futs = {pool.submit(translate_driver, d): d for d in drivers}
        for fut in as_completed(futs):
            d = futs[fut]
            try:
                pair = fut.result()
            except Exception as exc:  # noqa: BLE001
                print(f"  !! driver {d} failed: {exc}", flush=True)
                continue
            if "english" in pair:
                out_en[d] = pair["english"]
            if "hindi" in pair:
                out_hi[d] = pair["hindi"]
            print(f"  driver {d} done "
                  f"(en keys: {len(pair.get('english', {}))}, "
                  f"hi keys: {len(pair.get('hindi', {}))})", flush=True)
    print(f"all drivers in {time.time()-t_start:.1f}s")

    out_path = ROOT / "scripts" / "_translations_out.py"
    with out_path.open("w", encoding="utf-8") as f:
        f.write("# AUTO-GENERATED by scripts/translate_narratives.py\n")
        f.write("# Review and merge into vedic/numerology/narratives.py\n\n")
        f.write("_OUT_EN = ")
        f.write(repr(out_en))
        f.write("\n\n_OUT_HI = ")
        f.write(repr(out_hi))
        f.write("\n")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
