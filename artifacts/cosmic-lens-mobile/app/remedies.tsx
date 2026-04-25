import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { router } from "expo-router";
import React, { useState } from "react";
import {
  I18nManager,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";
import { useT } from "@/hooks/useT";
import { PLANET, DAY, GEMSTONE, DEITY, pick, type PlanetKey, type DayKey } from "@/lib/i18nVedic";

const F = {
  bold: "Nunito_700Bold", semibold: "Nunito_600SemiBold",
  medium: "Nunito_500Medium", regular: "Nunito_400Regular",
};

// ── Per-planet remedy content — translated to en/hn/hi ────────────────────────
type PlanetContent = {
  daan: string;
  mantraCount: string;
  upay: string[];
  weak_signs: string[];
};
type PlanetEntry = {
  id: string;
  key: PlanetKey;
  emoji: string;
  day: DayKey;
  color: string;
  gemstone: keyof typeof GEMSTONE;
  gemstoneColor: string;
  mantra: string;             // Sanskrit — kept Devanagari (sacred)
  deity: keyof typeof DEITY;
  deity_emoji: string;
  content: { en: PlanetContent; hn: PlanetContent; hi: PlanetContent };
};

const PLANETS: PlanetEntry[] = [
  {
    id:"surya", key:"surya", emoji:"☀️", day:"sun", color:"#f59e0b",
    gemstone:"ruby", gemstoneColor:"#ef4444",
    mantra:"ॐ ह्रां ह्रीं ह्रौं सः सूर्याय नमः",
    deity:"surya", deity_emoji:"☀️",
    content: {
      en: {
        daan: "Wheat, jaggery, copper vessels, red cloth",
        mantraCount: "108 times every Sunday",
        upay: [
          "Offer water (arghya) to the rising Sun every Sunday at sunrise",
          "Wear red-coloured clothes on Sundays",
          "Donate wheat and jaggery to a Brahmin",
          "Install a Surya Yantra at home",
        ],
        weak_signs: ["Saturn weakens — career obstacles", "Pitta disorders — eyes, stomach"],
      },
      hn: {
        daan: "Gehu, Gur, Tambe ka bartan, Lal kapda",
        mantraCount: "108 baar Ravivaar ke din",
        upay: [
          "Har Ravivaar suryoday ke samay Surya ko arghya den",
          "Lal rang ke kapde Ravivaar ko pahnen",
          "Gehu aur gur ka daan Brahmin ko karein",
          "Surya yantra sthaapit karein",
        ],
        weak_signs: ["Shani weak — career rukavat", "Pitta rog — aankhen, pet"],
      },
      hi: {
        daan: "गेहूँ, गुड़, तांबे का बर्तन, लाल कपड़ा",
        mantraCount: "हर रविवार 108 बार",
        upay: [
          "हर रविवार सूर्योदय के समय सूर्य को अर्घ्य दें",
          "रविवार को लाल रंग के कपड़े पहनें",
          "गेहूँ और गुड़ का दान ब्राह्मण को करें",
          "घर में सूर्य यंत्र स्थापित करें",
        ],
        weak_signs: ["शनि कमज़ोर — करियर में रुकावट", "पित्त रोग — आँखें, पेट"],
      },
    },
  },
  {
    id:"chandra", key:"chandra", emoji:"🌙", day:"mon", color:"#94a3b8",
    gemstone:"pearl", gemstoneColor:"#e2e8f0",
    mantra:"ॐ श्रां श्रीं श्रौं सः चंद्रमसे नमः",
    deity:"shiva", deity_emoji:"🔱",
    content: {
      en: {
        daan: "Rice, milk, silver vessels, white cloth",
        mantraCount: "11 or 108 times on Mondays",
        upay: [
          "View the Moon on the full-moon night (Purnima)",
          "Worship Lord Shiva on Mondays",
          "Donate milk and rice to the needy",
          "Wear white clothes on Mondays",
        ],
        weak_signs: ["Lack of mental peace", "Sleep disturbances", "Conflict with mother"],
      },
      hn: {
        daan: "Chawal, Dudh, Chandi ka bartan, Safed kapda",
        mantraCount: "11 baar ya 108 baar Somvar ko",
        upay: [
          "Chandra darshan karein Purnima ko",
          "Somvar ko Shiva puja karein",
          "Dudh aur chawal ka daan karein",
          "Safed rang ke kapde Somvar ko pahnen",
        ],
        weak_signs: ["Man ki shanti mein kami", "Neend ki takleef", "Mata se takraav"],
      },
      hi: {
        daan: "चावल, दूध, चाँदी का बर्तन, सफेद कपड़ा",
        mantraCount: "सोमवार को 11 या 108 बार",
        upay: [
          "पूर्णिमा के दिन चंद्र दर्शन करें",
          "सोमवार को शिव पूजा करें",
          "दूध और चावल का दान करें",
          "सोमवार को सफेद वस्त्र धारण करें",
        ],
        weak_signs: ["मन की शांति में कमी", "नींद की समस्या", "माता से तनाव"],
      },
    },
  },
  {
    id:"mangal", key:"mangal", emoji:"♂️", day:"tue", color:"#ef4444",
    gemstone:"coral", gemstoneColor:"#f87171",
    mantra:"ॐ क्रां क्रीं क्रौं सः भौमाय नमः",
    deity:"hanuman", deity_emoji:"🐒",
    content: {
      en: {
        daan: "Red lentils (masoor), red cloth, copper vessels, kheer",
        mantraCount: "108 times Tuesday morning",
        upay: [
          "Recite Hanuman Chalisa every Tuesday",
          "Wear red-coloured clothes on Tuesdays",
          "Donate red lentils (masoor dal)",
          "Install a Mangal Yantra at home",
        ],
        weak_signs: ["Mangal Dosh — obstacles in marriage", "Blood disorders"],
      },
      hn: {
        daan: "Masoor dal, Lal kapda, Tambe ka bartan, Kheer",
        mantraCount: "108 baar Mangalvar ke din subah",
        upay: [
          "Hanuman chalisa Mangalvar ko path karein",
          "Lal rang ke kapde Mangalvar ko pahnen",
          "Masoor dal ka daan karein",
          "Mangal yantra sthaapit karein",
        ],
        weak_signs: ["Mangal dosh — vivah mein baadha", "Rakt vikar — khoon ki problem"],
      },
      hi: {
        daan: "मसूर दाल, लाल कपड़ा, तांबे का बर्तन, खीर",
        mantraCount: "मंगलवार को सुबह 108 बार",
        upay: [
          "मंगलवार को हनुमान चालीसा का पाठ करें",
          "मंगलवार को लाल रंग के कपड़े पहनें",
          "मसूर दाल का दान करें",
          "मंगल यंत्र स्थापित करें",
        ],
        weak_signs: ["मंगल दोष — विवाह में बाधा", "रक्त विकार — रक्त संबंधी समस्या"],
      },
    },
  },
  {
    id:"budha", key:"budh", emoji:"☿️", day:"wed", color:"#10b981",
    gemstone:"emerald", gemstoneColor:"#34d399",
    mantra:"ॐ ब्रां ब्रीं ब्रौं सः बुधाय नमः",
    deity:"vishnu", deity_emoji:"🪷",
    content: {
      en: {
        daan: "Mung dal, green vegetables, bronze vessels, green books",
        mantraCount: "108 times every Wednesday",
        upay: [
          "Install Budh Yantra on Wednesday",
          "Eat green mung dal on Wednesday",
          "Recite Vishnu Sahasranama",
          "Perform Budh Graha Shanti Pooja",
        ],
        weak_signs: ["Speech disorders — difficulty speaking", "Underuse of intellect", "Loss in business"],
      },
      hn: {
        daan: "Moong dal, Hari sabzi, Kaansa bartan, Hari kitaaben",
        mantraCount: "108 baar Budhavar ke din",
        upay: [
          "Budh yantra Budhavar ko sthapit karein",
          "Hari mung dal Budhavar ko khayein",
          "Vishnu sahastranaam path karein",
          "Budh graha shanti puja karwayen",
        ],
        weak_signs: ["Vani dosha — bolne mein diqqat", "Buddhi ka kum upyog", "Vyapar mein haani"],
      },
      hi: {
        daan: "मूँग दाल, हरी सब्ज़ी, काँसे का बर्तन, हरी किताबें",
        mantraCount: "बुधवार को 108 बार",
        upay: [
          "बुधवार को बुध यंत्र स्थापित करें",
          "बुधवार को हरी मूँग दाल खाएँ",
          "विष्णु सहस्रनाम का पाठ करें",
          "बुध ग्रह शांति पूजा करवाएँ",
        ],
        weak_signs: ["वाणी दोष — बोलने में दिक्कत", "बुद्धि का कम उपयोग", "व्यापार में हानि"],
      },
    },
  },
  {
    id:"guru", key:"guru", emoji:"🪐", day:"thu", color:"#facc15",
    gemstone:"yellowsapphire", gemstoneColor:"#fde047",
    mantra:"ॐ ग्रां ग्रीं ग्रौं सः गुरवे नमः",
    deity:"vishnu", deity_emoji:"🌟",
    content: {
      en: {
        daan: "Chana dal, yellow cloth, gold, turmeric",
        mantraCount: "19,000 or 108 times on Thursdays",
        upay: [
          "Donate chana dal to a Brahmin every Thursday",
          "Wear yellow clothes on Thursdays",
          "Install a Guru Yantra at home",
          "Worship Vishnu and recite Guru Stotra",
        ],
        weak_signs: ["Difficulty with children", "Fading faith in dharma", "Delays in marriage"],
      },
      hn: {
        daan: "Chane ki dal, Peela kapda, Sona, Haldi",
        mantraCount: "19000 baar ya 108 baar Guruvaar ko",
        upay: [
          "Brahmin ko chane ki dal daan karein Guruvaar ko",
          "Peela kapda Guruvaar ko pahnen",
          "Guru Yantra sthaapit karein",
          "Vishnu puja aur Guru stotra path karein",
        ],
        weak_signs: ["Santaan sukh mein kami", "Dharm ke prati aastha ghati", "Vivah mein deri"],
      },
      hi: {
        daan: "चने की दाल, पीला कपड़ा, सोना, हल्दी",
        mantraCount: "गुरुवार को 19,000 या 108 बार",
        upay: [
          "गुरुवार को ब्राह्मण को चने की दाल दान करें",
          "गुरुवार को पीले कपड़े पहनें",
          "गुरु यंत्र स्थापित करें",
          "विष्णु पूजा और गुरु स्तोत्र का पाठ करें",
        ],
        weak_signs: ["संतान सुख में कमी", "धर्म में आस्था कम", "विवाह में देरी"],
      },
    },
  },
  {
    id:"shukra", key:"shukra", emoji:"♀️", day:"fri", color:"#f43f5e",
    gemstone:"diamond", gemstoneColor:"#e2e8f0",
    mantra:"ॐ द्रां द्रीं द्रौं सः शुक्राय नमः",
    deity:"lakshmi", deity_emoji:"🌸",
    content: {
      en: {
        daan: "White cloth, sugar, ghee, white flowers",
        mantraCount: "108 times every Friday",
        upay: [
          "Worship Goddess Lakshmi on Fridays",
          "Wear white-coloured clothes",
          "Feed fodder to a cow",
          "Recite Durga Saptashati",
        ],
        weak_signs: ["Trouble in love life", "Lack of aesthetic sense", "Obstacles in vehicle/property happiness"],
      },
      hn: {
        daan: "Safed kapda, Chini, Ghee, Safed phool",
        mantraCount: "108 baar Shukravar ke din",
        upay: [
          "Shukravar ko Lakshmi puja karein",
          "Safed rang ke kapde pahnen",
          "Gaay ko chara dein",
          "Durgasaptashati path karein",
        ],
        weak_signs: ["Prem jeevan mein takleef", "Saundaryabodh ki kami", "Vahaan-vastu sukh mein rukawat"],
      },
      hi: {
        daan: "सफेद कपड़ा, चीनी, घी, सफेद फूल",
        mantraCount: "शुक्रवार को 108 बार",
        upay: [
          "शुक्रवार को लक्ष्मी पूजा करें",
          "सफेद रंग के कपड़े पहनें",
          "गाय को चारा दें",
          "दुर्गासप्तशती का पाठ करें",
        ],
        weak_signs: ["प्रेम जीवन में समस्या", "सौंदर्यबोध की कमी", "वाहन-वस्तु सुख में रुकावट"],
      },
    },
  },
  {
    id:"shani", key:"shani", emoji:"⚖️", day:"sat", color:"#8b5cf6",
    gemstone:"bluesapphire", gemstoneColor:"#60a5fa",
    mantra:"ॐ प्रां प्रीं प्रौं सः शनये नमः",
    deity:"shani", deity_emoji:"⚖️",
    content: {
      en: {
        daan: "Black sesame, mustard oil, black cloth, iron",
        mantraCount: "108 times Saturday + Hanuman Chalisa",
        upay: [
          "Worship Shani Dev on Saturdays",
          "Donate black sesame seeds",
          "Offer water to a peepal tree on Saturdays",
          "Worship Lord Hanuman",
        ],
        weak_signs: ["Shani Dhaiya or Sade-Sati", "Obstacles in work", "Decline in health"],
      },
      hn: {
        daan: "Kala til, Sarson tel, Kaala kapda, Loha",
        mantraCount: "108 baar Shanivaar ke din, Hanuman Chalisa bhi",
        upay: [
          "Shanivaar ko Shani dev ki puja karein",
          "Kaale til ka daan karein",
          "Pippal ke ped ko Shanivaar ko jal chadhayein",
          "Hanuman ji ki aradhana karein",
        ],
        weak_signs: ["Shani dhaiya ya saadesaati", "Karya mein rukawat", "Sehat mein giraawat"],
      },
      hi: {
        daan: "काला तिल, सरसों का तेल, काला कपड़ा, लोहा",
        mantraCount: "शनिवार को 108 बार + हनुमान चालीसा",
        upay: [
          "शनिवार को शनि देव की पूजा करें",
          "काले तिल का दान करें",
          "शनिवार को पीपल के पेड़ को जल चढ़ाएँ",
          "हनुमान जी की आराधना करें",
        ],
        weak_signs: ["शनि ढैय्या या साढ़ेसाती", "कार्य में रुकावट", "स्वास्थ्य में गिरावट"],
      },
    },
  },
  {
    id:"rahu", key:"rahu", emoji:"🌑", day:"sat", color:"#6366f1",
    gemstone:"hessonite", gemstoneColor:"#fbbf24",
    mantra:"ॐ भ्रां भ्रीं भ्रौं सः राहवे नमः",
    deity:"durga", deity_emoji:"🗡️",
    content: {
      en: {
        daan: "Coconut, black cloth, mustard, radish",
        mantraCount: "18,000 or 108 times on Saturdays",
        upay: [
          "Perform Rahu Shanti pooja",
          "Worship Durga and Saraswati",
          "Donate black cloth on Saturdays",
          "Feed a Brahmin",
        ],
        weak_signs: ["Diseases and mental disorders", "Increase in enemies", "Sudden career setback"],
      },
      hn: {
        daan: "Nariyal, Kaala kapda, Sarson, Muli",
        mantraCount: "18000 baar ya 108 baar Shanivaar ko",
        upay: [
          "Rahu shanti puja karwayen",
          "Durga puja aur Saraswati ki aradhana karein",
          "Kaala kapda Shanivaar ko daan karein",
          "Bhojan Brahmin ko karwayen",
        ],
        weak_signs: ["Rog aur manorog", "Dushman badhna", "Career mein achanak giraaavat"],
      },
      hi: {
        daan: "नारियल, काला कपड़ा, सरसों, मूली",
        mantraCount: "शनिवार को 18,000 या 108 बार",
        upay: [
          "राहु शांति पूजा करवाएँ",
          "दुर्गा पूजा और सरस्वती की आराधना करें",
          "शनिवार को काला कपड़ा दान करें",
          "ब्राह्मण को भोजन कराएँ",
        ],
        weak_signs: ["रोग और मनोरोग", "शत्रु बढ़ना", "करियर में अचानक गिरावट"],
      },
    },
  },
  {
    id:"ketu", key:"ketu", emoji:"🌠", day:"tue", color:"#fb923c",
    gemstone:"catseye", gemstoneColor:"#d9f99d",
    mantra:"ॐ स्त्रां स्त्रीं स्त्रौं सः केतवे नमः",
    deity:"ganesh", deity_emoji:"🐘",
    content: {
      en: {
        daan: "Multi-coloured cloth, sesame, roti for dogs, black blanket",
        mantraCount: "7,000 or 108 times on Tuesdays",
        upay: [
          "Perform Ketu Shanti pooja",
          "Feed roti to dogs daily",
          "Worship Lord Ganesha",
          "Install a Ketu Yantra at home",
        ],
        weak_signs: ["Mysterious illnesses", "Spiritual unrest", "Fear of accidents"],
      },
      hn: {
        daan: "Chokh kapda, Bila til, Kutte ko roti, Kaala kambal",
        mantraCount: "7000 baar ya 108 baar Mangalvar ko",
        upay: [
          "Ketu shanti puja karwayen",
          "Kutte ko roz roti dein",
          "Ganesha aradhana karein",
          "Ketu yantra sthaapit karein",
        ],
        weak_signs: ["Rahasya rog", "Spiritual pareshani", "Accident ka darr"],
      },
      hi: {
        daan: "रंगीन कपड़ा, तिल, कुत्ते को रोटी, काला कंबल",
        mantraCount: "मंगलवार को 7,000 या 108 बार",
        upay: [
          "केतु शांति पूजा करवाएँ",
          "कुत्ते को रोज़ रोटी दें",
          "गणेश आराधना करें",
          "केतु यंत्र स्थापित करें",
        ],
        weak_signs: ["रहस्यमय रोग", "आध्यात्मिक परेशानी", "दुर्घटना का भय"],
      },
    },
  },
];

export default function RemediesScreen() {
  const C = useC();
  const t = useT();
  const insets = useSafeAreaInsets();
  const [selected, setSelected] = useState<string>("surya");
  const planet = PLANETS.find(p => p.id === selected)!;
  const v = t.vlang;
  const content = planet.content[v];
  const planetName = pick(v, PLANET[planet.key]);
  const dayName = pick(v, DAY[planet.day]);
  const gemstoneName = pick(v, GEMSTONE[planet.gemstone]);
  const deityName = pick(v, DEITY[planet.deity]);

  return (
    <View style={{ flex: 1 }}>
      <CosmicBg />
      <View style={[s.topBar, { paddingTop: insets.top + 10 }]}>
        <Pressable onPress={() => router.back()} style={s.backBtn}>
          <Feather name={I18nManager.isRTL ? "arrow-right" : "arrow-left"} size={20} color={C.text} />
        </Pressable>
        <View>
          <Text style={[s.title, { color: C.text }]}>{t.remediesTitle}</Text>
          <Text style={[s.sub, { color: C.textMuted }]}>{t.remSubtitle}</Text>
        </View>
        <View style={{ width: 36 }} />
      </View>

      {/* Planet pills */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={{ flexGrow: 0 }}
        contentContainerStyle={{ paddingHorizontal: 16, gap: 8, paddingBottom: 14 }}
      >
        {PLANETS.map(p => {
          const pName = pick(v, PLANET[p.key]);
          return (
            <Pressable
              key={p.id}
              onPress={() => { Haptics.selectionAsync(); setSelected(p.id); }}
              style={[
                s.pill,
                { backgroundColor: C.bgCard, borderColor: C.border },
                selected === p.id && { backgroundColor: `${p.color}18`, borderColor: `${p.color}60` },
              ]}
            >
              <Text style={{ fontSize: 16 }}>{p.emoji}</Text>
              <Text style={[s.pillText, { color: selected === p.id ? p.color : C.textMuted }]}>{pName}</Text>
            </Pressable>
          );
        })}
      </ScrollView>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: insets.bottom + 100, gap: 14 }}>

        {/* Hero */}
        <View style={[s.hero, { backgroundColor: `${planet.color}10`, borderColor: `${planet.color}30` }]}>
          <Text style={{ fontSize: 40 }}>{planet.emoji}</Text>
          <View>
            <Text style={[s.heroTitle, { color: planet.color }]}>{planetName}</Text>
            <Text style={[s.heroDev, { color: C.text }]}>{planet.deity_emoji} {deityName}</Text>
            <Text style={[s.heroDay, { color: C.textMuted }]}>{t.remPujaDay}: {dayName}</Text>
          </View>
        </View>

        {/* Gemstone */}
        <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Text style={[s.cardTitle, { color: C.textMuted }]}>{t.remGemstoneLbl}</Text>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 12 }}>
            <View style={[s.gemCircle, { backgroundColor: `${planet.gemstoneColor}20`, borderColor: `${planet.gemstoneColor}50` }]}>
              <Text style={{ fontSize: 24 }}>💎</Text>
            </View>
            <View>
              <Text style={[s.gemName, { color: C.text }]}>{gemstoneName}</Text>
              {v !== "en" && (
                <Text style={[s.gemEn, { color: C.textMuted }]}>{GEMSTONE[planet.gemstone].en}</Text>
              )}
              <Text style={[s.gemTip, { color: C.textMuted }]}>{t.remGemstoneTip}</Text>
            </View>
          </View>
        </View>

        {/* Mantra */}
        <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Text style={[s.cardTitle, { color: C.textMuted }]}>{t.remMantraLbl}</Text>
          <View style={[s.mantraBox, { backgroundColor: `${planet.color}08`, borderColor: `${planet.color}25` }]}>
            <Text style={[s.mantraText, { color: planet.color }]}>{planet.mantra}</Text>
          </View>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
            <Feather name="repeat" size={12} color={C.textDim} />
            <Text style={[s.mantraCount, { color: C.textMuted }]}>{content.mantraCount}</Text>
          </View>
        </View>

        {/* Daan */}
        <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Text style={[s.cardTitle, { color: C.textMuted }]}>{t.remDaanLbl}</Text>
          <Text style={[s.daanText, { color: C.textMid }]}>{content.daan}</Text>
          <View style={[s.tipBox, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
            <Feather name="info" size={12} color={C.textDim} />
            <Text style={[s.tipText, { color: C.textMuted }]}>{t.remDaanTip}</Text>
          </View>
        </View>

        {/* Upay */}
        <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Text style={[s.cardTitle, { color: C.textMuted }]}>{t.remUpayLbl}</Text>
          {content.upay.map((u, i) => (
            <View key={i} style={s.upayRow}>
              <View style={[s.upayDot, { backgroundColor: planet.color }]} />
              <Text style={[s.upayText, { color: C.textMid }]}>{u}</Text>
            </View>
          ))}
        </View>

        {/* Weak sign symptoms */}
        <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Text style={[s.cardTitle, { color: C.textMuted }]}>{t.remWeakSignsLbl.replace("{planet}", planetName.toUpperCase())}</Text>
          {content.weak_signs.map((w, i) => (
            <View key={i} style={[s.signRow, { borderBottomColor: C.border3 }, i === content.weak_signs.length - 1 && { borderBottomWidth: 0 }]}>
              <Text style={{ fontSize: 16 }}>🔴</Text>
              <Text style={[s.signText, { color: C.textMid }]}>{w}</Text>
            </View>
          ))}
        </View>
      </ScrollView>
    </View>
  );
}

const s = StyleSheet.create({
  topBar: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: 20, paddingBottom: 14,
  },
  backBtn: { width: 36, height: 36, alignItems: "center", justifyContent: "center" },
  title: { fontSize: 20, fontFamily: F.bold, letterSpacing: -0.3 },
  sub: { fontSize: 11, fontFamily: F.regular, marginTop: 1 },
  pill: {
    flexDirection: "row", alignItems: "center", gap: 6,
    paddingHorizontal: 12, paddingVertical: 8,
    borderRadius: 20, borderWidth: 1,
  },
  pillText: { fontSize: 12, fontFamily: F.semibold },
  hero: {
    flexDirection: "row", alignItems: "center", gap: 16,
    borderRadius: 16, borderWidth: 1, padding: 18,
  },
  heroTitle: { fontSize: 20, fontFamily: F.bold },
  heroDev: { fontSize: 13, fontFamily: F.medium, marginTop: 2 },
  heroDay: { fontSize: 11, fontFamily: F.regular, marginTop: 2 },
  card: { borderRadius: 16, borderWidth: 1, padding: 16, gap: 10 },
  cardTitle: { fontSize: 10, fontFamily: F.bold, letterSpacing: 1.5 },
  gemCircle: {
    width: 52, height: 52, borderRadius: 26,
    alignItems: "center", justifyContent: "center", borderWidth: 1.5,
  },
  gemName: { fontSize: 16, fontFamily: F.bold },
  gemEn:   { fontSize: 11, fontFamily: F.medium, marginTop: 1 },
  gemTip:  { fontSize: 11, fontFamily: F.regular, marginTop: 2 },
  mantraBox: {
    padding: 14, borderRadius: 12, borderWidth: 1,
  },
  mantraText: { fontSize: 15, fontFamily: F.semibold, textAlign: "center", lineHeight: 26 },
  mantraCount: { fontSize: 11, fontFamily: F.regular },
  daanText: { fontSize: 13, fontFamily: F.regular, lineHeight: 21 },
  tipBox: {
    flexDirection: "row", gap: 6, alignItems: "flex-start",
    padding: 10, borderRadius: 10, borderWidth: 1,
  },
  tipText: { flex: 1, fontSize: 11, fontFamily: F.regular, lineHeight: 17 },
  upayRow: { flexDirection: "row", alignItems: "flex-start", gap: 10 },
  upayDot: { width: 7, height: 7, borderRadius: 3.5, marginTop: 6 },
  upayText: { flex: 1, fontSize: 12, fontFamily: F.regular, lineHeight: 20 },
  signRow: {
    flexDirection: "row", alignItems: "center", gap: 10,
    paddingVertical: 9, borderBottomWidth: 1,
  },
  signText: { flex: 1, fontSize: 12, fontFamily: F.regular },
});
