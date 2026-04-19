"""
Sprint 43 / Phase R — Panchang Full
R1. Tithi (30) + lord + deity
R2. Nakshatra (27) + lord + pada + deity
R3. Yoga (27) + lord
R4. Karana (11) + lord
R5. Vaar + Hora summary
R6. Ritu (6 seasons), Ayana (2), Maasa (12)
R7. Samvatsara (60-yr cycle)
R8. Shaka year, Vikram Samvat year
"""
from __future__ import annotations
from datetime import datetime, date
from typing import Any

try:
    import swisseph as swe
    _SWE_OK = True
except Exception:
    _SWE_OK = False

# R1 — 30 Tithis
TITHI_NAMES = ["Pratipada","Dwitiya","Tritiya","Chaturthi","Panchami","Shashthi",
                "Saptami","Ashtami","Navami","Dashami","Ekadashi","Dwadashi",
                "Trayodashi","Chaturdashi","Purnima"] * 1  # repeat for Krishna
TITHI_LORD = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn",
               "Rahu","Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"]
TITHI_DEITY = ["Brahma","Vidhata","Vishnu","Yama","Chandra","Karttikeya","Indra",
                "Vasus","Naga","Dharma","Rudra","Aditya","Kama","Kali","Vishvedevas"]

# R2 — 27 Nakshatra
NAK_NAMES = ["Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra",
              "Punarvasu","Pushya","Ashlesha","Magha","P.Phalguni","U.Phalguni",
              "Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha",
              "Mula","P.Ashadha","U.Ashadha","Shravana","Dhanishta","Shatabhisha",
              "P.Bhadrapada","U.Bhadrapada","Revati"]
NAK_LORD = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"] * 3
NAK_DEITY = ["Ashwini Kumaras","Yama","Agni","Brahma/Prajapati","Soma","Rudra",
              "Aditi","Brihaspati","Sarpa (Nagas)","Pitris","Bhaga","Aryaman",
              "Surya/Savitr","Tvashtar/Vishvakarma","Vayu","Indra-Agni","Mitra","Indra",
              "Nirriti","Apah/Water","Vishvedevas","Vishnu","Vasus","Varuna",
              "Ajaikapada","Ahirbudhnya","Pushan"]

# R3 — 27 Yogas
YOGA_NAMES = ["Vishkambha","Preeti","Ayushman","Saubhagya","Shobhana","Atiganda",
               "Sukarma","Dhriti","Shoola","Ganda","Vriddhi","Dhruva","Vyaghata",
               "Harshana","Vajra","Siddhi","Vyatipata","Variyan","Parigha","Shiva",
               "Siddha","Sadhya","Shubha","Shukla","Brahma","Indra","Vaidhriti"]
# Yoga lords (deity-keyed; we use planet lord ruler for each)
YOGA_LORD = ["Saturn","Venus","Mercury","Moon","Jupiter","Saturn","Mercury","Sun",
              "Saturn","Mars","Sun","Earth","Mars","Vayu","Varuna","Ganesha","Rudra",
              "Kubera","Vishvakarma","Mitra","Kartikeya","Savita","Brahma","Vishnu",
              "Shiva","Indra","Vayu"]

# R4 — 11 Karanas (7 movable, 4 fixed)
KARANA_NAMES = ["Bava","Balava","Kaulava","Taitila","Garaja","Vanija","Vishti (Bhadra)",
                 "Shakuni","Chatushpada","Naga","Kimstughna"]
KARANA_LORD = ["Indra","Brahma","Mitra","Aryaman","Bhumi","Lakshmi","Yama",
                "Kalidasa","Brahma","Sarpa","Maruts"]

# R5 — Weekday lords
PY_WD_TO_LORD = {0:"Moon",1:"Mars",2:"Mercury",3:"Jupiter",4:"Venus",5:"Saturn",6:"Sun"}
WEEKDAY_NAME = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

# R6 — Ritus (6 seasons), Ayanas (2), Maasas (12)
RITU_BY_MONTH = {  # solar months → ritu
    1:"Shishira",2:"Vasanta",3:"Vasanta",4:"Grishma",5:"Grishma",6:"Varsha",
    7:"Varsha",8:"Sharad",9:"Sharad",10:"Hemanta",11:"Hemanta",12:"Shishira"}
LUNAR_MAASAS = ["Chaitra","Vaishakha","Jyeshtha","Ashadha","Shravana","Bhadrapada",
                 "Ashwina","Kartika","Margashirsha","Pausha","Magha","Phalguna"]

# R7 — 60-yr Samvatsara cycle
SAMVATSARA = [
    "Prabhava","Vibhava","Shukla","Pramoda","Prajapati","Angirasa","Shrimukha",
    "Bhava","Yuva","Dhata","Ishvara","Bahudhanya","Pramathi","Vikrama","Vrisha",
    "Chitrabhanu","Subhanu","Tarana","Parthiva","Vyaya","Sarvajit","Sarvadhari",
    "Virodhi","Vikriti","Khara","Nandana","Vijaya","Jaya","Manmatha","Durmukhi",
    "Hevilambi","Vilambi","Vikari","Sharvari","Plava","Shubhakrit","Shobhakrit",
    "Krodhi","Vishvavasu","Parabhava","Plavanga","Kilaka","Saumya","Sadharana",
    "Virodhakrit","Paridhavi","Pramadi","Ananda","Rakshasa","Nala","Pingala",
    "Kalayukti","Siddharthi","Raudri","Durmati","Dundubhi","Rudhirodgari",
    "Raktakshi","Krodhana","Akshaya"
]


def _moon_sun_lon(dt: datetime) -> tuple[float | None, float | None]:
    if not _SWE_OK: return None, None
    try:
        jd = swe.julday(dt.year, dt.month, dt.day,
                          dt.hour + dt.minute/60 + dt.second/3600)
        flag = swe.FLG_SIDEREAL | swe.FLG_SWIEPH
        swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
        sun, _ = swe.calc_ut(jd, swe.SUN, flag)
        moon, _ = swe.calc_ut(jd, swe.MOON, flag)
        return float(sun[0]) % 360, float(moon[0]) % 360
    except Exception:
        return None, None


def compute_phase_r(target: datetime | None = None) -> dict[str, Any]:
    if target is None: target = datetime.utcnow()
    sun_lon, moon_lon = _moon_sun_lon(target)

    out: dict[str, Any] = {"date": target.date().isoformat(),
                            "swisseph_available": _SWE_OK}

    if sun_lon is not None and moon_lon is not None:
        # R1 Tithi
        tithi_arc = (moon_lon - sun_lon) % 360
        tithi_idx = int(tithi_arc // 12)   # 0..29
        paksha = "Shukla" if tithi_idx < 15 else "Krishna"
        loc_idx = tithi_idx % 15
        tithi_name = TITHI_NAMES[loc_idx] if loc_idx < 15 else "Amavasya"
        if tithi_idx == 29: tithi_name = "Amavasya"
        if tithi_idx == 14: tithi_name = "Purnima"
        out["r1_tithi"] = {"tithi_idx_1to30": tithi_idx+1, "name": tithi_name,
                            "paksha": paksha, "lord": TITHI_LORD[loc_idx],
                            "deity": TITHI_DEITY[loc_idx],
                            "deg_in_tithi": round(tithi_arc - tithi_idx*12, 2)}
        # R2 Nakshatra of Moon
        nak_seg = 360.0/27.0
        nak_idx = int(moon_lon / nak_seg)
        if nak_idx > 26: nak_idx = 26
        deg_in_nak = moon_lon - nak_idx*nak_seg
        pada = int(deg_in_nak / (nak_seg/4)) + 1
        out["r2_nakshatra"] = {"name": NAK_NAMES[nak_idx], "pada": pada,
                                "lord": NAK_LORD[nak_idx],
                                "deity": NAK_DEITY[nak_idx],
                                "deg_in_nak": round(deg_in_nak,2)}
        # R3 Yoga = (sun + moon) / 13°20'
        yoga_arc = (sun_lon + moon_lon) % 360
        yoga_idx = int(yoga_arc / nak_seg)
        if yoga_idx > 26: yoga_idx = 26
        out["r3_yoga"] = {"name": YOGA_NAMES[yoga_idx], "lord": YOGA_LORD[yoga_idx],
                           "deg_in_yoga": round(yoga_arc - yoga_idx*nak_seg, 2)}
        # R4 Karana = half of tithi
        karana_pos = int(tithi_arc / 6)  # 0..59
        # Karanas 1-56 cycle Bava-Vishti repeating; 57=Shakuni, 58=Chatushpada, 59=Naga, 0=Kimstughna
        if karana_pos == 0:
            kn = "Kimstughna"; kl = "Maruts"
        elif karana_pos >= 57:
            ki = karana_pos - 57 + 7  # 7,8,9 → Shakuni/Chatushpada/Naga
            kn = KARANA_NAMES[ki+1]; kl = KARANA_LORD[ki+1]  # offset +1 because list[7]=Shakuni
        else:
            ki = (karana_pos - 1) % 7
            kn = KARANA_NAMES[ki]; kl = KARANA_LORD[ki]
        out["r4_karana"] = {"name": kn, "lord": kl, "karana_pos_1to60": karana_pos+1}
        # R6 Ritu / Ayana / Maasa
        sun_si = int(sun_lon // 30) + 1   # 1=Aries..12
        ritu = RITU_BY_MONTH.get(sun_si, "?")
        ayana = "Uttarayana" if sun_si in [10,11,12,1,2,3] else "Dakshinayana"
        # Lunar month = nakshatra of full moon (Purnima) closest to current.
        # Simpler: use solar-month-1 maps to Chaitra around April equinox approx.
        maasa_idx = (sun_si + 0) % 12   # solar→lunar approx
        maasa = LUNAR_MAASAS[maasa_idx]
        out["r6_ritu_ayana_maasa"] = {"ritu": ritu, "ayana": ayana, "maasa": maasa,
                                       "sun_sign_idx": sun_si}

    # R5 Vaar + Hora-day-lord
    wd = target.weekday()
    out["r5_vaar"] = {"weekday": WEEKDAY_NAME[wd],
                       "lord": PY_WD_TO_LORD[wd],
                       "first_hora_lord": PY_WD_TO_LORD[wd]}

    # R7 Samvatsara — start cycle at Prabhava in Kali year 12, 60-yr cycle.
    # Using common epoch: Vikrama 2080 (CE 2023-24) ~= Shobhakrit (idx 36).
    # samvatsara_idx = (CE_year - 1986) % 60 → CE 1987 = Prabhava.
    sv_idx = (target.year - 1987) % 60
    out["r7_samvatsara"] = {"name": SAMVATSARA[sv_idx], "cycle_idx_1to60": sv_idx+1}

    # R8 Shaka & Vikram years (CE = Shaka + 78; Vikram = CE + 57 if before Chaitra new year, else CE+56)
    out["r8_eras"] = {
        "Shaka_Samvat": target.year - 78,
        "Vikram_Samvat": target.year + 57,    # post Chaitra; pre = +56
        "Kali_Yuga": target.year + 3102,
        "Bengali_Sambat": target.year - 593,
    }
    return out


def format_phase_r(r: dict) -> str:
    if not r: return "▸ PHASE R PANCHANG: ❌ unavailable"
    L = [f"▸ PHASE R PANCHANG FULL (Sprint-43) — {r['date']}"]
    if "r1_tithi" in r:
        t = r["r1_tithi"]
        L.append(f"  R1 TITHI: {t['paksha']} {t['name']} (#{t['tithi_idx_1to30']}/30) "
                 f"— lord {t['lord']}, deity {t['deity']} "
                 f"({t['deg_in_tithi']}° elapsed in tithi)")
    if "r2_nakshatra" in r:
        n = r["r2_nakshatra"]
        L.append(f"  R2 NAKSHATRA (Moon): {n['name']} pada {n['pada']} "
                 f"— lord {n['lord']}, deity {n['deity']} ({n['deg_in_nak']}° in nak)")
    if "r3_yoga" in r:
        y = r["r3_yoga"]
        L.append(f"  R3 YOGA: {y['name']} — lord {y['lord']} ({y['deg_in_yoga']}° in yoga)")
    if "r4_karana" in r:
        k = r["r4_karana"]
        L.append(f"  R4 KARANA: {k['name']} — lord {k['lord']} (#{k['karana_pos_1to60']}/60)")
    v = r["r5_vaar"]
    L.append(f"  R5 VAAR: {v['weekday']} — day-lord {v['lord']}, "
             f"first-hora-lord {v['first_hora_lord']}")
    if "r6_ritu_ayana_maasa" in r:
        x = r["r6_ritu_ayana_maasa"]
        L.append(f"  R6 RITU/AYANA/MAASA: ritu={x['ritu']} (season), "
                 f"ayana={x['ayana']} (sun-half), maasa={x['maasa']} (lunar month)")
    s = r["r7_samvatsara"]
    L.append(f"  R7 SAMVATSARA: {s['name']} (year #{s['cycle_idx_1to60']}/60 of Brahaspatya cycle)")
    e = r["r8_eras"]
    L.append(f"  R8 ERAS: Shaka {e['Shaka_Samvat']} | Vikram {e['Vikram_Samvat']} | "
             f"Kali {e['Kali_Yuga']} | Bengali {e['Bengali_Sambat']}")
    return "\n".join(L)
