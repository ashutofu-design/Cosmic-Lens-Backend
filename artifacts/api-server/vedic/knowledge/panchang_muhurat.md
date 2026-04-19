# Panchang & Muhurat — The Vedic Calendar System

Panchang ("five-limbs") is the daily Vedic calendar describing the quality of a moment via 5 elements. Muhurat is the science of selecting the right moment for any action. The engine computes both (`vedic/panchang/*` Sprint-43 and `vedic/muhurta/*` Sprint-42).

> RULE: Specific Tithi/Nakshatra/Yoga/Karana for any date, and exact muhurat windows, come from the engine. AI must never invent or approximate dates/timings.

---

## The 5 Limbs of Panchang

### 1. Tithi (Lunar day)
The angular distance between Moon and Sun divided into 30 tithis (12° each). One tithi ≈ 19-26 hours.

- 15 tithis in **Shukla Paksha** (waxing fortnight, new-moon → full-moon)
- 15 tithis in **Krishna Paksha** (waning fortnight, full-moon → new-moon)

| Tithi | Name | Quality |
|-------|------|---------|
| 1 | Pratipada | Auspicious for new beginnings (especially Shukla) |
| 2 | Dwitiya | Travel, vehicles |
| 3 | Tritiya | Education, arts |
| 4 | Chaturthi | Ganesha, removing obstacles (Sankashti — Krishna 4) |
| 5 | Panchami | Snake worship, learning |
| 6 | Shashthi | Skanda/Kartikeya, military, child-protection |
| 7 | Saptami | Sun worship, health |
| 8 | Ashtami | Durga/Krishna birth, intense karmic day |
| 9 | Navami | Rama Navami (Shukla Chaitra), Durga Navratri |
| 10 | Dashami | Vijaya Dashami (Shukla Ashwin), success |
| 11 | Ekadashi | Vishnu fasting, spiritual |
| 12 | Dwadashi | Vishnu, abundance |
| 13 | Trayodashi | Shiva, Pradosha (evening twilight worship) |
| 14 | Chaturdashi | Shiva (Krishna 14 = Maha-Shivratri prep), demonic on Krishna |
| 15 | Purnima (full)/Amavasya (new) | Purnima = peak benefic; Amavasya = ancestor worship |

### Rikta Tithis (avoid for new starts)
4, 9, 14 — known as Rikta ("empty"); avoid major launches, marriage, journey.

### Nanda / Bhadra / Jaya / Rikta / Purna cycle
- 1, 6, 11 = Nanda (joy)
- 2, 7, 12 = Bhadra (welfare)
- 3, 8, 13 = Jaya (victory)
- 4, 9, 14 = Rikta (empty)
- 5, 10, 15 = Purna (full)

### 2. Vaar (Weekday)
Each weekday is ruled by a planet and carries that planet's nature.

| Day | Ruler | Best for |
|-----|-------|----------|
| Sunday | Sun | Government work, leadership, father-related |
| Monday | Moon | Mother, water-business, pearls, wedding |
| Tuesday | Mars | Property, surgery, court (avoid soft starts) |
| Wednesday | Mercury | Business, contracts, communication, education |
| Thursday | Jupiter | Religion, dharma, marriage, gold purchase |
| Friday | Venus | Love, art, cosmetics, vehicle (cars best) |
| Saturday | Saturn | Iron, hard labour, long-term contracts (avoid travel) |

### 3. Nakshatra (covered in `nakshatras.md`)

### 4. Yoga (Sun-Moon longitude sum, 27 types)
The Yoga is a measure of Sun-Moon harmony. 27 yogas of 13°20′ each. Some are auspicious, some not.

**Auspicious yogas** (good for major work):
Vishkambha (carefully), Preeti, Ayushman, Saubhagya, Shobhana, Sukarma, Dhriti, Harshana, Vajra (mixed), Siddhi, Variyan, Shiva, Siddha, Sadhya, Shubha, Sukla, Brahma, Indra.

**Inauspicious yogas** (avoid important work):
- **Vyatipata** — extreme imbalance, accidents.
- **Vaidhriti** — separation, loss.
- **Parigha** — obstacles, blocked progress.
- **Vajra (last 5 ghati)** — sharp negativity.
- **Ganda** — knot, karmic block.
- **Atiganda** — heavy karmic block.
- **Vishkambha (first 3 ghati)** — pillar of opposition.
- **Shoola** — sharp pain.
- **Vyaghata** — destruction.

### 5. Karana (half of a Tithi)
Each tithi has 2 karanas. 11 karanas total: 7 movable repeating, 4 fixed.

- **Movable**: Bava, Balava, Kaulava, Taitila, Garaja, Vanija, Vishti (Bhadra).
- **Fixed**: Shakuni, Chatushpada, Naga, Kimstughna.

**Vishti Karana (also called Bhadra)** is the most inauspicious karana — avoid all major work during Bhadra. Rises about every alternate day.

---

## Muhurat — Choosing the Right Moment

A perfect muhurat is one where:
1. Tithi favourable (avoid Rikta tithis 4/9/14 unless event matches).
2. Vaar favourable (event matches the day-lord).
3. Nakshatra favourable for the event.
4. Yoga benefic (not Vyatipata/Vaidhriti/Parigha etc).
5. Karana not Vishti (Bhadra).
6. Lagna at the muhurat moment is strong, with benefics in kendra.
7. Moon is not in 6/8/12 from the lagna of the moment.
8. No planetary war / eclipse / pitru paksha (unless ancestor-related).

The engine returns the best windows for the user's specific event.

---

## Common Muhurta Categories

| Event | Best nakshatra | Avoid |
|-------|----------------|-------|
| Marriage | Rohini, Mrigashira, Magha, Uttara Phalguni, Hasta, Swati, Anuradha, Mula, Uttara Ashadha, Uttara Bhadrapada, Revati | Bharani, Krittika, Ashlesha, Vishakha, Jyeshtha, Purva Phalguni (mixed) |
| Griha-pravesha (house entry) | Anuradha, Hasta, Mrigashira, Pushya, Uttara series, Revati | Bharani, Ashlesha, Magha, Krittika |
| New business | Pushya, Hasta, Anuradha, Uttara series, Revati | Bharani, Ashlesha, Magha, Mula, Vishakha |
| Vehicle purchase | Friday + Pushya/Hasta/Anuradha (Pushya-on-Thursday is best annual day) | Tuesday, Saturday, Bhadra |
| Surgery | Tuesday/Saturday + waning Moon + Mrigashira/Ardra/Mula/Jyeshtha (Mars-ruled) | Thursday, Shukla Paksha |
| Travel | East: Monday/Saturday avoid; West: Friday/Sunday avoid; North: Tuesday/Wednesday avoid; South: Thursday/Friday avoid | (Disha-shoola days) |
| Education start | Wednesday/Thursday + Saraswati nakshatras (Hasta, Mrigashira, Pushya) | Mula, Jyeshtha, Ashlesha |
| Naming ceremony | 11th, 12th, 16th, 27th day after birth in benefic nakshatra | Ashlesha-Magha gandanta day |

---

## Daily Auspicious / Inauspicious Windows

### Auspicious
- **Brahma Muhurta** — 1.5 hours before sunrise (best for meditation, study).
- **Abhijit Muhurta** — middle ~48 minutes of the day, centred on solar noon. Universal "good luck" window for any work except those forbidden on the day.
- **Godhuli Muhurta** — twilight at sunset; auspicious for marriage, lighting lamps.
- **Amrita Kaal** — engine-computed daily window of ~96 minutes when energy is most conducive.

### Inauspicious
- **Rahu Kaal** — 1.5 hour daily Rahu-window (varies by weekday and sunrise time). Avoid new starts.
- **Yama Ghantam** — 1.5 hour daily Yama-window. Same caution.
- **Gulika Kaal** — 1.5 hour daily window of son-of-Saturn. Avoid auspicious work; suitable for tantric/death rituals.
- **Dur Muhurta** — 2 short windows daily, varies by weekday. Avoid starts.
- **Varjyam** — engine-computed 96-minute "rejected" window each day; avoid travel.
- **Bhadra (Vishti Karana)** — ~12 hour window every 1-2 days; AVOID all major work.

### Rahu Kaal weekly schedule (1.5 hr)
| Day | Position in day (start sunrise count) |
|-----|---------------------------------------|
| Sunday | 4.5 – 6 (4th window) — afternoon |
| Monday | 1.5 – 3 (2nd) |
| Tuesday | 3 – 4.5 (3rd) |
| Wednesday | 6 – 7.5 (5th) |
| Thursday | 7.5 – 9 (6th) |
| Friday | 9 – 10.5 (7th) — late afternoon |
| Saturday | 0 – 1.5 (1st) — morning |

(Day = sunrise to sunset, divided into 8 equal parts; engine computes exact local time per latitude/season.)

---

## Choghadiya & Hora (intra-day windows)

**Choghadiya** — divides day and night into 8 windows of ~96 minutes each, labeled:
- **Amrita** — best universal
- **Shubha** — auspicious
- **Labh** — gain (excellent for business)
- **Char** — movement (good for travel)
- **Rog** — disease (avoid)
- **Kal** — death-time (avoid for benefic, ok for severance)
- **Kal-Vela** — extreme caution
- **Udveg** — anxiety (avoid)

**Hora** — 24 one-hour windows ruled by 7 planets in fixed sequence (Sun-Venus-Mercury-Moon-Saturn-Jupiter-Mars). Schedule any planet-aligned task in that planet's hora (e.g., learning during Jupiter-hora, business during Mercury-hora).

The engine returns the day's full Choghadiya + Hora schedule.

---

## Special Days & Periods

| Period | Significance |
|--------|--------------|
| Pitru Paksha (Krishna Paksha of Bhadrapada, ~mid-Sept) | Ancestor worship; avoid new starts, weddings |
| Adhik Maas (extra month every 3 years) | Spiritual practice peaks; avoid major worldly starts |
| Khar Maas (Sun in Sagittarius/Pisces, ~mid-Dec & mid-Mar each ~30 days) | Avoid weddings, griha-pravesha |
| Sade Sati / Dhaiya | Personal — engine reports |
| Eclipses | Avoid starts ±3 days; meditate, fast |
| Pradosham (Trayodashi evening) | Shiva worship best |
| Sankashti Chaturthi (Krishna 4) | Ganesha worship for obstacle removal |
| Ekadashi (both Pakshas) | Vishnu fasting day |

---

## How AI Should Answer "When should I…?"

1. Engine returns the user's chart-aligned best-nakshatra list.
2. Engine returns the next available muhurat dates within the user's window.
3. AI presents the dates with start/end times exactly as engine reports, plus the panchang-quality of each option.
4. Never propose a custom date — only choose from engine output.
5. If no good muhurat exists in the user's window, ask whether they can extend, OR propose Abhijit Muhurta on a relatively-clean day as the universal fallback.
