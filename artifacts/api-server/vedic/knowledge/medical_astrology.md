# Medical Astrology — Body, Disease & Healing

Medical astrology (Vaidic Jyotish chikitsa) reads the chart for constitutional tendencies, organ susceptibility, timing of illness, and supportive remedies. The engine (`vedic/medical/*` + Sprint-46) handles the calculations; this file gives interpretive knowledge.

> RULE: Specific disease predictions or diagnostic dates come from the engine. AI must never invent a disease name or recovery date. AI may discuss tendencies and supportive measures based on engine-reported afflictions.

---

## Planet → Body Part / System

| Planet  | Body parts / systems |
|---------|----------------------|
| Sun     | Heart, spine, right eye (male)/left eye (female), bones, vitality, immune system |
| Moon    | Mind, brain, blood, lymph, breasts, stomach lining, left eye (male)/right eye (female), fluids |
| Mars    | Muscles, bone-marrow, blood-cells, head, sinuses, genitals (male), surgery wounds |
| Mercury | Skin, nervous system, lungs, voice, hands, intestines, speech |
| Jupiter | Liver, pancreas, fat tissue, hips, thighs, arteries, ear |
| Venus   | Reproductive organs (female), kidneys, throat, face, eyes (general), urinary, sweet-glands |
| Saturn  | Bones, joints, teeth, knees, chronic diseases, nerves, depression, slow degeneration |
| Rahu    | Skin diseases, allergies, mysterious/undiagnosed conditions, poisoning, addictions, foreign infections |
| Ketu    | Sudden infections, accidents, parasitic diseases, paranormal symptoms, mystery ailments, surgery scars |

---

## House → Body Part

| House | Body part |
|-------|-----------|
| 1     | Head, brain, overall vitality |
| 2     | Face, right eye, throat, mouth, teeth, neck |
| 3     | Arms, shoulders, ears, lungs (right) |
| 4     | Chest, breasts, lungs, heart-region |
| 5     | Stomach, upper abdomen, liver |
| 6     | Lower abdomen, intestines, kidneys, **disease itself** |
| 7     | Reproductive organs, lower back, hips |
| 8     | Genitals, anus, **chronic disease & longevity** |
| 9     | Thighs, hips, hepatic system |
| 10    | Knees, joints, spine |
| 11    | Calves, ankles, circulation in legs |
| 12    | Feet, left eye, sleep disorders, **hospitalisation** |

---

## Three Doshas (Ayurvedic mapping)

| Dosha | Element | Planets | Nature |
|-------|---------|---------|--------|
| Vata  | Air + Ether | Saturn, Rahu, Mercury (when dry) | Dry, cold, mobile, irregular |
| Pitta | Fire + Water | Sun, Mars, Ketu | Hot, sharp, intense |
| Kapha | Water + Earth | Moon, Jupiter, Venus | Heavy, slow, oily, stable |

The Moon's nakshatra-nadi at birth gives constitutional dosha:
- **Adi Nadi** (1st nadi) = Vata
- **Madhya Nadi** = Pitta
- **Antya Nadi** = Kapha

When the dasha-lord planet aligns with the user's natal nadi, that dosha rises in the body.

---

## Disease-prediction Rules of Thumb

### Trika houses (6, 8, 12) and their lords
- **6th house** = acute illness, debt, enemies. Planets here can give the disease but also strength to fight it.
- **8th house** = chronic illness, longevity. Most malefic for health if afflicted.
- **12th house** = hospital, sleep disorder, hidden illness, expenses on health.
- **6L–8L–12L** combinations create persistent illness; Vipareeta cancellation reverses the effect.

### Mars and Saturn
- **Mars in 6** = inflammatory disease, surgery; in 8 = accident; in 12 = blood pressure.
- **Saturn in 6** = chronic recovery (paradoxically good — gives strength against disease); in 8 = chronic illness.
- **Saturn–Mars conjunction** = surgery indication.

### Rahu placements
- **Rahu in 1** = headaches, mysterious symptoms, allergies.
- **Rahu in 5** = anxiety, addictions, education-stress symptoms.
- **Rahu in 6** = strange chronic ailment, foreign infection.
- **Rahu in 8** = hidden disease, mental complications, paranormal.
- **Rahu in 12** = sleep disorder, hospital admission abroad, hidden surgery.

### Ketu placements
- **Ketu in 1** = mysterious head/skin ailment, low immunity.
- **Ketu in 6** = quick infections, parasites, sudden disease cycles.
- **Ketu in 8** = sudden surgery, accident-prone.

---

## D6 (Shashtiamsha) and D30 (Trimshamsha)

The engine produces:
- **D6** for disease analysis — the 6th-house lord and planets occupying 6th in D6 reveal dormant disease karma.
- **D30** for misfortune & accidents — Mars/Saturn in D30 expose injury timing patterns.

Cross-referencing afflictions in both D1 and D6 confirms a real medical issue vs a passing influence.

---

## Common Combinations (engine-detected)

| Pattern | Likely tendency |
|---------|-----------------|
| Sun + Mars in 1/8 | Hypertension, heart strain |
| Moon + Saturn in 4/12 | Depression, mental heaviness |
| Mercury + Rahu | Anxiety, nervous-system, ADHD |
| Venus + Saturn afflicted | Reproductive issues, kidney/diabetes |
| Saturn in 6 with malefic | Chronic backache, joint disease |
| Mars in 7 | BP, marriage stress affecting health |
| Jupiter weak + 5 afflicted | Fertility concerns, liver-pancreas |
| 6L in 1 with Sun | Auto-immune, fevers, vitality drain |
| 8L in 1 | Longevity question; needs Vipareeta check |

---

## Timing of Disease

A disease typically manifests when:
1. The mahadasha-lord rules a malefic 6/8/12 house.
2. The antardasha activates the same.
3. Transit Saturn / Mars / Rahu hits the natal 6, 8, 12 or their lords.
4. Eclipse occurs on natal Moon or Lagna sign.

Engine reports these convergences as "health-risk window" with start/end dates. AI must use those dates verbatim — never invent.

---

## Supportive Remedies (planet-specific)

These are general tonic measures, not medical prescriptions. Always consult licensed practitioner for diagnosis/treatment.

- **Sun (heart/vitality)** — early-morning sunlight, Surya Namaskar, ruby (with caution if Sun afflicted), Aditya Hridaya Stotra.
- **Moon (mind/sleep)** — silver-vessel water, milk before sleep, pearl, Chandra mantra, Mondays' fast.
- **Mars (blood/inflammation)** — red lentils donation, Hanuman Chalisa, Tuesday fast, brisk exercise.
- **Mercury (skin/nerves)** — Vishnu Sahasranama, neem leaves, emerald, green vegetables, Wednesday fast.
- **Jupiter (liver/fat)** — Brihaspati Stotra, yellow foods (turmeric), saffron tilak, yellow sapphire, Thursday fast.
- **Venus (reproductive/kidney)** — white flowers, Lakshmi puja, hydration, diamond/white sapphire, Friday fast.
- **Saturn (bones/joints/chronic)** — Hanuman Chalisa daily, Shani Stotra, sesame oil massage, iron donation, Saturday fast.
- **Rahu (mysterious/skin/addictions)** — Rahu Beej mantra, multi-grain donation Saturdays, tobacco/alcohol cessation, regular sleep.
- **Ketu (sudden/parasitic)** — Ganesha worship, Ketu Beej mantra, donate two-coloured blanket, dog-feeding, surgical caution on weak transits.

---

## Three pillars of medical astrology answer

When user asks "what does my chart say about my health?", AI should structure the answer as:

1. **Constitution** — dosha (Vata/Pitta/Kapha) per Janma Nakshatra-nadi.
2. **Susceptibility** — planet/house-affliction tendencies (engine reports).
3. **Timing windows** — current dasha + transit health-risk windows (engine reports exact dates).

End with a *gentle reminder* that astrology indicates tendency, not certainty — qualified medical care remains primary.
