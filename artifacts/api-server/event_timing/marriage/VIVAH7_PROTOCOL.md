# VIVAH-7 Protocol

**Marriage Timing Engine — User's Custom Methodology**

---

## Status

- **DRAFT** — capturing user's setup one-by-one (ADD-ONLY)
- **NO code changes yet** — `event_timing/marriage/` DO NOT TOUCH rule active
- Ship only on explicit user override
- When user says "VIVAH-7 me X add karo" → append to this file
- When user says "VIVAH-7 ship karo" → implement per this exact spec

---

## EXCLUSIONS (explicit user direction)

- **NO Jaimini rules** — UL (Upapada Lagna), Char dasha, Atmakaraka, Sahams excluded
- Do not over-classical-ify (lean reality-first approach, not academic completeness)
- Avoid stacked-system madness (KP + Parashari + Tajik + Jaimini all together = noise)

---

## ARCHITECTURAL DIRECTION

**Replace current "Parashari-first" flow with "KP-first" flow:**

```
STEP 0: Late vs Early Marriage Tendency Check    ← FIRST priority
STEP 1: KP Filter (sublord-based 2/7/11 vs 6/8/12)
STEP 2: D1 + D9 Cross-Validation (candidate planets only)
STEP 3: Redemption Check (rejected planets via D1/D9 strength)
STEP 4: Dasha + Triple Confluence Timing (with Ashtakavarga + aspects + double transit)
STEP 5: Reality Filter (age, adjusted by STEP 0 tendency)
STEP 6: Critical Enhancements (Eclipse + Dasha Strength + AD/PD max power)
```

---

## EXECUTION CHECKLIST — Single Line Serial (kya kya karna hai)

### STEP 0 — Late vs Early Marriage Tendency Check (FIRST)
1. L1: Saturn-Venus conjunction kahin bhi chart me check karo.
2. L2: Saturn ka 3/7/10 aspect 7H ya 7L ya Venus pe check karo.
3. L3: 7L 6/8/12 me hai check karo.
4. L11: Saturn 1H ya 7H me hai check karo.
5. E1: Venus + Jupiter aspect/conjunction 7H pe check karo.
6. E2: 7L kendra (1/4/7/10) ya trikona (5/9) me strong hai check karo.
7. E5: 5L-7L parivartana ya conjunction check karo.
8. E6: Venus exalted/own sign + 7L strong check karo.
9. G1/G2: Female chart Jupiter karaka, Male chart Venus karaka — gender modifier set karo.
10. Late count + Early count compute karo, tendency assign karo (EARLY/STANDARD/LATE/VERY_LATE/MIXED).
11. step0_result dict output karo with active indicators + explanation.

### STEP 1 — KP Filter
12. Har planet ke 3 levels nikalo: Planet + Nakshatra Lord + Sublord.
13. Sublord ko FINAL ARBITER treat karo (Planet < Nakshatra Lord < Sublord hierarchy).
14. Har planet ke sublord ki significations check karo (kaunse houses signify karta).
15. Agar signify {2, 7, 11} → CANDIDATE list me daalo.
16. Agar signify {6, 8, 12} → REJECTED list me daalo (parked, deleted nahi).
17. 7th Cusp Sub Lord (CSL) separately nikalo + uske significations check karo.
18. 7th Cusp Star Lord bhi nikalo (currently engine me missing) + significations check karo.
19. Output: candidates list + rejected list + 7CSL verdict + 7CStarLord verdict.

### STEP 2 — D1 + D9 Cross-Validation (candidates only)
20. Har CANDIDATE planet ka D1 me 7H ke saath link check karo (placement/aspect/ownership).
21. Same planet ka D1 me 7L ke saath link check karo (conjunction/aspect).
22. Same checks D9 me karo (D9 weight = 2x D1).
23. D1 + D9 link strength score nikalo per candidate.
24. Strong link wale candidates ko "validated" mark karo.

### STEP 3 — Redemption Check (rejected only)
25. Har REJECTED planet ka D1 me 7H/7L link check karo.
26. Same planet ka D9 me 7H/7L link check karo (vargottama bonus).
27. Agar bahut strong (e.g. khud 7L hai aur D9 me vargottama) → promote back to candidate.
28. Promoted candidate ko delay_flag ke saath candidates list me add karo.

### STEP 4 — Dasha + Triple Confluence + Ashtakavarga
29. Har validated candidate ke liye upcoming MD/AD/PD windows scan karo.
30. cluster_hit compute karo (AD/PD lord = target lord) — weight 3 (DOMINANT, not 1-2).
31. Dasha lord ki dignity check karo (own/exalted/friend/neutral/enemy/debilitated/combust).
32. Dignity multiplier apply karo (×1.3 exalted/own, ×1.1 friend, ×1.0 neutral, ×0.8 enemy, ×0.5 debilitated/combust).
33. Jupiter ka 7H/7L/Venus pe conjunction check karo (+2 score).
34. Jupiter ka 7H/7L/Venus pe aspect (5/7/9) check karo (+1 score, only if no conjunction).
35. Saturn ka 7H/7L/Venus pe conjunction check karo (+2 score).
36. Saturn ka 7H/7L/Venus pe aspect (3/7/10) check karo (+1 score, only if no conjunction).
37. Double Transit bonus: Jupiter AND Saturn dono same target touch karein → +1 (Yugma Drishti).
38. ashtakavarga.py module import karo aur compute_ashtakavarga(planets, lagna_si) call karo.
39. Transit planet ka BAV bindu count nikalo us sign me — ≥5/8 = +1, ≤2/8 = -1.
40. 7H ka SAV total check karo — ≥30 = +0.5, <25 = -0.5.
41. Eclipse check: next 6 months me Solar/Lunar eclipse 7H ya 7L sign me hai? → delay flag.
41a. **Dasha Sandhi check**: Window MD/AD transition ke ±3 months me hai? → +1.5 boost (HIGH WEIGHT — second most important factor).
41b. **Mars trigger check**: Mars exact transit hit on 7H/7L/Venus during window? → +1 activation boost (NOT base scoring, only accelerator).
41c. **Mars+Saturn conflict check**: Dono active on marriage axis simultaneously? → raise `conflict_risk` flag.
41d. **Retrograde penalty**: 7L / Venus / Jupiter retrograde during window? → −1 score (delay flag, window NOT cancelled).
42. Final window score compute karo (sum of all above with multipliers + sandhi boost − retrograde penalty).
43. Score ≥5 = STRONG, 3-4 = MEDIUM, 1-2 = LOW (windows include karo with confidence label).

### STEP 5 — Reality Filter (age, STEP 0-adjusted)
44. _get_current_age() + _extract_birth_year() se current age + birth year nikalo.
45. Har candidate window ke liye predicted_age = (window_year − birth_year) calculate karo.
46. STEP 0 tendency dekho aur uske hisaab se age threshold table apply karo.
47. EARLY tendency: 18-22 normal, 30+ "slightly late" flag.
48. STANDARD tendency: 18-21 soft early flag, 22-30 normal, 35+ late flag.
49. LATE tendency: 18-22 PUSH_LATER, 22-30 "uncommon", 30+ normal.
50. VERY_LATE tendency: <22 BLOCK, 22-30 PUSH_LATER, 30+ normal.
51. Block/flag windows according to tendency-adjusted thresholds.
52. Agar saare windows blocked + final verdict = PROMISED → downgrade to PREMATURE.

### OUTPUT ASSEMBLY
53. Valid windows ko (score desc, start asc) sort karo.
54. primary_window = top scorer assign karo.
55. backup_window = next valid window from different AD assign karo.
56. Top-3 windows ranked output karo (currently primary+backup only — extend to top 3).
57. Har window ke saath confidence band attach karo (STRONG/MEDIUM/LOW).
58. Har window ke saath reasons array attach karo (top 3 contributing factors).
59. early_late_tendency field attach karo (from STEP 0).
60. Risk flags collect karo (Manglik / 7L afflicted / KP DENIED / eclipse hit / Saturn over 7H).
61. Final dict return karo: {verdict, band, primary_window, backup_window, top3_windows, key_trigger, confluence_strength, tendency, risk_flags, reasons, factors[]}.

### LLM INTEGRATION (format_verdict_for_prompt)
62. Final dict ko 68-char "═" separator se wrap karke LOCKED FACTS block banao.
63. Mode awareness add karo (PREDICT/EXPLAIN/VERIFY/GENERAL).
64. Trust Layer 4 (Sannyasi Yoga), 5 (Multi-marriage), 6 (Era cohort) flags surface karo.
65. AUTHORITY directive add karo (verdict restate karo, apni reasoning add mat karo).

---

## STEP 0 — LATE vs EARLY MARRIAGE TENDENCY CHECK ⭐ FIRST

**Maqsad:** Determine native's marriage tendency BEFORE pipeline runs. Output sets context for STEP 5 (age filter).

### LATE Indicators

- **L1 — Saturn-Venus conjunction** (anywhere in chart) [KN Rao #1 rule, near-100% reliability]
- **L2 — Saturn aspect on 7H, 7L, OR Venus** (3rd, 7th, 10th aspects)
- **L3 — 7L in 6/8/12** (dusthana placement)
- **L11 — Saturn in 1H or 7H** [BV Raman + Quora empirical, most reliable single marker]

### EARLY Indicators

- **E1 — Venus + Jupiter aspect/conjunction on 7H** [strongest early indicator]
- **E2 — 7L in kendra (1/4/7/10) or trikona (5/9), strong**
- **E5 — 5L-7L parivartana (exchange) OR conjunction** [love marriage signature]
- **E6 — Venus exalted/own sign + 7L strong**

### Gender Modifier

- **G1 — Female chart**: Jupiter = husband karaka → Jupiter dasha trigger weighted higher
- **G2 — Male chart**: Venus = wife karaka → Venus dasha trigger weighted higher

### Verdict Logic

```
late_count   = count of {L1, L2, L3, L11} active
early_count  = count of {E1, E2, E5, E6} active

if late_count >= 4:                   tendency = "VERY_LATE"
elif late_count >= 2 and early_count == 0:  tendency = "LATE"
elif early_count >= 2 and late_count == 0:  tendency = "EARLY"
elif late_count >= 2 and early_count >= 2:  tendency = "MIXED"
else:                                  tendency = "STANDARD"
```

### STEP 5 (Age Filter) Adjustment Based on STEP 0

| tendency | 18-22 window | 22-30 window | 30-35 window | 35+ window |
|---|---|---|---|---|
| EARLY | Normal (no PUSH_LATER) | Normal | "Slightly late, possible" | Late flag |
| STANDARD | Soft early flag | Normal | Normal | Late flag |
| LATE | PUSH_LATER | "Possible but uncommon" | Normal | Normal |
| VERY_LATE | Block | PUSH_LATER | "Possible" | Normal |
| MIXED | Soft early flag | Normal | Normal | Soft late flag |

### Output Field

```python
step0_result = {
    "tendency": "EARLY|STANDARD|LATE|VERY_LATE|MIXED",
    "late_indicators_active": ["L1", "L11"],   # which fired
    "early_indicators_active": [],
    "gender_karaka": "Jupiter" | "Venus",       # G1/G2
    "explanation": "Saturn-Venus conjunction in 5H + Saturn in 7H detected — strong late tendency",
}
```

---

## STEPS 1–5 (PIPELINE CORE)

To be defined by user one-by-one. Skeleton from prior discussion captured below for context.

### Pending User Setup
- STEP 1: KP Filter rules
- STEP 2: D1 + D9 cross-validation rules
- STEP 3: Redemption check rules
- STEP 4: Dasha + Triple Confluence + Ashtakavarga + aspect + double transit rules
- STEP 5: Reality filter (age, adjusted by STEP 0)

---

## STEP 6 — CRITICAL ENHANCEMENTS (user-curated subset)

**User has explicitly chosen which critical pieces to include vs drop.**

### ✅ INCLUDED

#### 6.1 — Eclipse Impact Check
- Scan upcoming Solar/Lunar eclipses (next 6 months from query date)
- If eclipse sign == 7H sign OR eclipse sign == 7L sign → **delay/cancellation flag** for windows in next 6 months
- KN Rao + Quora empirically validated rule
- Implementation: ephemeris eclipse dates + sign overlap check (~20 lines)

#### 6.2 — Dasha Lord Strength Check
- Currently engine only checks `cluster_hit` (PD lord = target lord) — strength of dasha lord IGNORED
- Add: dasha lord ka **dignity score** (own/exalted/friend/neutral/enemy/debilitated/combust)
- Multiplier on window strength:
  - Exalted/own = ×1.3
  - Friend's sign = ×1.1
  - Neutral = ×1.0
  - Enemy = ×0.8
  - Debilitated/combust = ×0.5
- "Venus AD chal raha but Venus combust hai" → window weak

#### 6.3 — AD/PD = MAXIMUM Power in Scoring (architectural rule)
- **AD (Antardasha) + PD (Pratyantar dasha) lord match with target lords = DOMINANT factor**
- Transits = SECONDARY confirmation, NOT primary trigger
- Revised scoring weight:
  ```
  cluster_hit (AD/PD lord = target) → weight 3 (was 1-2)
  dasha_lord_strength multiplier   → weight ×0.5 to ×1.3
  jupiter_transit                   → weight 1 (was 1)
  saturn_transit                    → weight 1 (was 1)
  mars_transit (if added)           → weight 1
  ```
- Logic: real-world prediction me **dasha = WHAT/WHEN, transit = CONFIRM/TRIGGER**
- Without strong dasha, transit alone never fires marriage event

### ❌ DROPPED (user's explicit decision)

#### Birth Time Accuracy / Rectification Awareness
- User decision: use whatever birth details are given as-is
- No rectification module, no confidence-based weight shifting
- Accept that ±4 min KP cusp shift may cause noise in some cases

### ✅ INCLUDED (continued — finalized after reviewer audit)

#### 6.4 — Retrograde Handling (controlled weight, NOT cancel)
- If 7L / Venus / Jupiter is retrograde during the window → **score −1 (delay penalty)**
- Window NOT cancelled, just downgraded
- Logic: retrograde = rethink/repeat/delay → marriage hoti hai par seedhi nahi
- Implementation: ephemeris already provides `retrograde` flag, 1-line check
- Importance: **MEDIUM**

#### 6.5 — Mars Trigger Transit (activation, NOT base scoring)
- Mars exact transit hit on 7H / 7L / Venus → **+1 activation boost**
- Mars used ONLY as accelerator/trigger, never base scoring factor
- Logic: Mars = speed, impulse → fast development / sudden decision
- **Conflict flag**: If Mars AND Saturn both active simultaneously on marriage axis → raise `conflict_risk` flag
- Importance: **LOW–MEDIUM**

#### 6.6 — Dasha Sandhi (Junction Transition Boost)
- ±3 months from MD/AD transition point → **+1.5 boost (HIGH WEIGHT)**
- Reviewer's reframe: sandhi NOT as "inhibition zone" but as "life shift catalyst"
- Logic: Old phase ending + new phase starting = life shift = marriage trigger
- Empirically: KN Rao + multiple practitioners cite dasha transitions as event peaks
- Importance: **HIGH 🔥**

### PRIORITY ORDER (architectural — applies to STEP 4 scoring)

```
1. Dasha (main driver)        — DOMINANT factor
2. Sandhi (high trigger)      — +1.5 if within ±3 months of transition
3. Transit (Jupiter primary)  — +2 conjunction, +1 aspect
4. Mars (secondary trigger)   — +1 activation only on exact hit
5. Retrograde (delay modifier)— −1 penalty
```

### ONE-LINE TRUTH (memorize this)

> **"Dasha decide karta hai, Sandhi activate karta hai, Mars accelerate karta hai, Retrograde delay karta hai."**

---

## REFERENCE — 30 Surgical Points (from prior audit + design discussion)

For context. Final implementation order = user's STEP 1-5 specs above.

### A. Flow Refactor
1. Parashari-first → KP-first flow
2. Rejected (6/8/12) planets: D1/D9 redemption check, not hard skip
3. Sublord = final arbiter (3-tier: Planet < Nakshatra Lord < Sublord)

### B. D1 Layer Strengthening
4. D1 dignity weighting: 7L exalted/own = +1, combust/debilitated = -1
5. Venus combust check (±10° from Sun) = hard FLAG

### C. Reject Filter (mini-layer)
6. Saturn 8th-from-Moon (Sade Sati phase 1) = hard delay flag
7. Venus combust + Manglik active uncancelled = hard reject flags

### D. Transit Logic Overhaul
8. Aspect support: Jupiter 5/7/9, Saturn 3/7/10 on 7H/7L/Venus
9. Double Transit detection (Jupiter AND Saturn on same target = +1 bonus)
10. 7L pe transit add (currently missing, only 7H + Venus checked)
11. Jupiter conjunction = +2, aspect = +1 (currently both +1)

### E. Ashtakavarga Plug-in
12. `ashtakavarga.py` import in marriage_timing (already exists, used by career_timing)
13. Transit planet's BAV bindu in transit sign: ≥5/8 = +1, ≤2/8 = -1
14. 7H SAV ≥30 = +0.5, <25 = -0.5

### F. KP Refinement
15. KP DENIED soften: keep PROMISED with delay flag if D1+D9 STRONG, demote only if D1+D9 weak
16. 7th Cusp Star Lord (CSL) add (currently only Sub Lord checked)

### G. Age Filter Soften
17. Remove "Compromise/fast-arranged typical" wording
18. 18-21 PUSH_LATER → soft early flag (modern context)

### H. Window Selection
19. Score=1 windows include with "LOW confidence" label (currently dropped)
20. Backup window same AD allow if PD significantly stronger

### I. Output Enrichment
21. Confidence band per window: STRONG (≥5), MEDIUM (3-4), LOW (1-2)
22. Reasons array: top 3 contributing factors per window

---

## ESTIMATED IMPACT

| Group | Effort | Accuracy gain |
|---|---|---|
| STEP 0 (late/early check) | LOW | +0.3 (sets context for all later layers) |
| A (flow refactor) | HIGH | +0.5 |
| B (D1 dignity) | LOW | +0.3 |
| C (reject filter) | LOW | +0.2 |
| D (transit overhaul) | MED | +0.5 |
| E (Ashtakavarga plug) | LOW | +0.4 |
| F (KP refinement) | LOW | +0.2 |
| G (age wording) | TRIVIAL | UX win |
| H (window selection) | LOW | +0.1 |
| I (output enrichment) | LOW | LLM narration win |

**Target: current 8.0/10 → 9.5/10** for month+year window prediction.

**HARD CEILING:** Exact day/hour/minute prediction NOT achievable from natal chart alone. Requires Prashna (Horary) at moment-of-question — separate `prashna_engine/` for future Phase.

---

## FILES TOUCHED (when ship time comes)

- `artifacts/api-server/event_timing/marriage/marriage_timing.py` (893L) — main pipeline
- `artifacts/api-server/event_timing/marriage/__init__.py` — orchestrator + format_verdict_for_prompt
- `artifacts/api-server/event_timing/marriage/love_or_arrange.py` (1415L) — keep as-is unless user says otherwise
- `artifacts/api-server/ashtakavarga.py` — import only, no edit
- New optional: `artifacts/api-server/event_timing/marriage/REDESIGN_KP_FIRST.md` — design doc

**DO NOT TOUCH** rule must be lifted before any code edit. Recommended: surgical in-place vs parallel `marriage_v2/` — to be decided when shipping.

---

## CHANGELOG

- **2026-05-02 (v1)**: File created. STEP 0 (Late vs Early check) defined. Jaimini excluded per user direction. Architectural direction (KP-first) captured. STEP 1-5 pending user setup.
- **2026-05-02 (v2)**: STEP 6 confirmed items (6.1 Eclipse, 6.2 Dasha Strength, 6.3 AD/PD max power) added. Birth time rectification dropped per user. Execution Checklist (65 single-line steps) added.
- **2026-05-02 (v3)**: STEP 6 finalized after second reviewer audit. **6.4 Retrograde** (−1 delay penalty), **6.5 Mars trigger** (+1 activation only, with Mars+Saturn conflict flag), **6.6 Dasha Sandhi** (+1.5 HIGH WEIGHT boost) all locked. Priority order architecturally defined: Dasha > Sandhi > Transit > Mars > Retrograde. One-line truth: "Dasha decide karta hai, Sandhi activate karta hai, Mars accelerate karta hai, Retrograde delay karta hai." Execution checklist STEP 4 extended with lines 41a-41d.
