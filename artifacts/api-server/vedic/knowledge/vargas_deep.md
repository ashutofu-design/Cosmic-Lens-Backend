# Vargas — The 16 Divisional Charts (Shodashvarga)

Divisional charts (vargas) magnify specific life areas by sub-dividing each sign. Parashara prescribes 16 vargas; the engine computes all 16 (`vedic/varga/*`). Each varga has a "deity" / dignity scheme (Vargottama, Pushkar etc.) used in strength assessment.

> RULE: Engine computes the planet's sign in each varga. AI may interpret patterns in the divisional charts but must not recompute or invent placements.

---

## The 16 Vargas at a Glance

| #  | Name           | Division | Life-area focus |
|----|----------------|----------|-----------------|
| 1  | Rashi (D1)     | 1        | Body, overall life — base chart |
| 2  | Hora (D2)      | 2        | Wealth, financial flow |
| 3  | Drekkana (D3)  | 3        | Siblings, courage, short journeys |
| 4  | Chaturthamsha (D4) | 4    | Property, fortune, vehicles |
| 5  | Saptamsha (D7) | 7        | Children, progeny |
| 6  | Navamsha (D9)  | 9        | Spouse, dharma, post-marriage destiny |
| 7  | Dashamsha (D10)| 10       | Career, profession, public-life |
| 8  | Dwadashamsha (D12) | 12   | Parents, ancestral roots |
| 9  | Shodashamsha (D16) | 16   | Vehicles, comforts, accidents |
| 10 | Vimshamsha (D20) | 20     | Spiritual practice, devotion |
| 11 | Chaturvimshamsha (D24) | 24 | Education, learning, scholarship |
| 12 | Saptavimshamsha (D27) | 27 | Strength, weakness of mind |
| 13 | Trimshamsha (D30) | 30   | Misfortunes, accidents, evil influences |
| 14 | Khavedamsha (D40) | 40   | Maternal lineage karma |
| 15 | Akshavedamsha (D45) | 45 | Paternal lineage karma, character |
| 16 | Shashtiamsha (D60) | 60  | All past karmas, finest reading |

---

## Key Vargas Detailed

### D1 — Rashi (Birth Chart)
The base chart. All other vargas are read in conjunction with D1. A planet must be strong in D1 for any varga reading to deliver.

### D9 — Navamsha (most important after D1)
- Read for **marriage, spouse, post-50 life, dharma maturity**.
- Compare D1 and D9: if a planet sits in the same sign in D9 as D1 → **Vargottama** → very strong.
- Lord of D9 lagna is the Atmakaraka's dharma anchor.
- Marriage indicators: 7th house of D9 + its lord + Venus in D9.
- **D9 lagna lord** has equal strength to D1 lagna lord in many predictions.

### D10 — Dashamsha (Career)
- Read for **profession, career-peak, public reputation**.
- 10th house of D10 + its lord + Sun + Mercury in D10 = career signature.
- Atmakaraka in D10's 10th = soul-aligned profession.
- Strong planets in D10 kendras (1, 4, 7, 10) = career success.
- **A great career yoga in D1 collapses if planets are weak in D10**.

### D7 — Saptamsha (Children)
- Read for **children, fertility, parental joy**.
- 5th house of D7 + 5L of D7 + Jupiter in D7 = children indicators.
- Putra-karaka (Jupiter for father, Moon for mother) in D7 strong = healthy progeny.

### D12 — Dwadashamsha (Parents)
- 9th house of D12 + Sun = father.
- 4th house of D12 + Moon = mother.
- Affliction in either house in D12 = ancestral karma needing remedy.

### D16 — Shodashamsha (Vehicles & Comforts)
- 4th house of D16 = vehicles, luxury items.
- Venus in D16 strong = good cars/comforts; afflicted = vehicle accidents.
- Mars in D16 4th + malefic = recurring vehicle damage.

### D20 — Vimshamsha (Spiritual Practice)
- Reveals **devotion path** (which deity, which mantra resonates).
- Jupiter and Ketu in D20 are most important for spiritual progress.
- 5L of D20 = ishta-devata indication.

### D24 — Chaturvimshamsha (Education)
- 4th and 5th houses of D24 = academic capacity.
- Mercury and Jupiter in D24 strong = scholar.
- Saraswati Yoga must replicate in D24 for genuine learning success.

### D30 — Trimshamsha (Misfortunes)
- Specific to **accidents, illness, evil influences**.
- Only 5 planets count in D30 (no Sun/Moon mapping in classical D30).
- Mars and Saturn placement reveals injury timing patterns.

### D60 — Shashtiamsha (Past Karma)
- Most refined varga — **the finest reading** of past karma.
- Each 0°30′ arc of a sign maps to a deity (60 deities total).
- D60 lagna and 9th house = total karmic baggage.
- Planets in benefic D60 deity-arcs deliver gracefully; in malefic deity-arcs cause friction.
- **Use D60 only when D1 + D9 + relevant varga all converge** — D60 is the tie-breaker.

---

## Vargottama Status

A planet is **Vargottama** when it occupies the same sign in two charts (commonly D1 and D9). The classical extended definition:

- **Single Vargottama** (D1 = D9) — strong; planet delivers full house result.
- **Double Vargottama** (same sign in D1, D9, D10) — exceptional strength.
- **Triple Vargottama** (D1 = D9 = D10 = D12 etc) — rare; produces extraordinary success in that planet's domain.

Engine outputs Vargottama matrix across all 16 vargas; AI may quote the count and mention significance.

---

## Pushkara Navamsha

Specific navamshas considered "auspicious vessels": each sign has one Pushkara amsha (Aries → 11th amsha, Taurus → 8th amsha, etc.). A planet falling in its Pushkara amsha gains gentle benefic boost regardless of dignity.

---

## Shadbala in Vargas

Six-fold strength of a planet (Sthana, Dig, Kala, Cheshta, Naisargika, Drik) is most often computed for D1, but classical texts (Phaladeepika, Saravali) extend the analysis to D9 and D10 for marriage and career predictions respectively. The engine may output `dasha_score_in_d9`, `kendra_count_in_d10` etc.

---

## How to Read Multiple Vargas

The classical principle: **a yoga must replicate** to deliver fully.

| For | Check |
|-----|-------|
| Marriage | D1 + D9 (mandatory replication) |
| Career | D1 + D10 (mandatory) |
| Children | D1 + D7 + D9 |
| Wealth | D1 + D2 + D11-significance in D1 |
| Property | D1 + D4 + D16 |
| Education | D1 + D24 |
| Health | D1 + D6 + D30 |
| Spiritual progress | D1 + D20 + D60 |

A "raja yoga" present only in D1 but absent in D10 = tagline-level success without real career delivery. Replication is the test of authenticity.

---

## Common User Questions Mapped to Vargas

| User question | Primary vargas |
|---------------|----------------|
| "Will my marriage be happy?" | D9 — 7th house, Venus, 7L; cross-check D1 |
| "Will I get a government job?" | D10 — 10th house, Sun's strength, 10L's house |
| "Will I have children?" | D7 — 5th house & 5L, Jupiter |
| "Will I own a house?" | D4 — 4th house, 4L, Mars/Moon strength |
| "What will be my profession exactly?" | D10 — Atmakaraka's house in D10 |
| "Should I pursue spiritual path?" | D20 — Jupiter, Ketu, 9L of D20 |
| "Will I do well in studies?" | D24 — 4th/5th houses, Mercury, Jupiter |
| "Why do I keep having accidents?" | D30 — Mars/Saturn placements; cross-check 8th house |
| "What is my ultimate karma?" | D60 — lagna and 9L of D60 |

---

## A Word on Accuracy

Divisional chart accuracy depends critically on **birth time**:

- **D9 changes every ~3.5 minutes** of birth time.
- **D10 changes every ~3 minutes**.
- **D60 changes every ~30 seconds** — making it impossible to use without rectified birth time.

The engine performs **birth-time rectification** when the user provides reasonable bounds; if rectification is uncertain, AI must qualify divisional readings ("if your birth time is exact within 5 minutes, then…").
