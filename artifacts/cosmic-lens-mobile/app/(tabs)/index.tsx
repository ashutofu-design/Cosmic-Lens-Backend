import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import * as Haptics from "expo-haptics";
import { Redirect, router } from "expo-router";
import React, { useEffect, useRef, useState } from "react";
import {
  Animated,
  Platform,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import EnergyChart from "@/components/EnergyChart";
import { useUser } from "@/context/UserContext";
import { getT, type UILang } from "@/lib/i18n";
import { getDemoLabels } from "@/lib/i18nContent";
import { useColors } from "@/hooks/useColors";
import { useTheme } from "@/context/ThemeContext";
import { computeTodayEnergy } from "@/lib/todayEnergyCalc";
import { fetchTodayEnergy, type EnergyResult, type EnergyFlag } from "@/lib/energyAPI";
import { computeActiveDasha, type ActiveDashaResult } from "@/lib/proInsightEngine";
import type { MoonHistoryPoint } from "@/types";

// ── Localized labels (vlang-bucketed: en/hn/hi) ───────────────────────────────
// ── Home-tab labels ──────────────────────────────────────────────────────────
// Switches on the FULL UILang code (not the 3-bucket VLang) so each Indian
// language renders in its OWN script. Previously every Indian language other
// than Hindi (Bangla, Marathi, Tamil, Telugu, Gujarati, Kannada, Malayalam,
// Punjabi, ODIA, Assamese) silently bucketed to Hindi via vedicLang() — Odia
// users saw Hindi text on the home tab. Global langs (zh/es/ar/fr/...) keep
// English fallback (matches the Vastu policy of "no Hinglish leak abroad").
type HomeLabels = {
  namaste:         string;
  hello:           string;
  forecastPill:    string;
  todaysEnergy:    string;
  demo:            string;
  forecast7day:    string;
  now:             string;
  doshTitle:       string;
  doshSub:         string;
  live:            string;
  riskTitle:       string;
  riskSubAhead:    string;
  riskDashaActive: (md: string, ad: string) => string;
  alert:           string;
  milanTitle:      string;
  milanSub:        string;
  pro:             string;
  insightStrong:   string;
  insightModerate: string;
  insightUnstable: string;
  insightLow:      string;
};

const HOME_EN: HomeLabels = {
  namaste:        "Namaste 🙏",
  hello:          "Hello",
  forecastPill:   "7 Day Energy Forecast",
  todaysEnergy:   "TODAY'S ENERGY",
  demo:           "DEMO",
  forecast7day:   "7-day forecast",
  now:            "Now",
  doshTitle:      "Dosh Analysis",
  doshSub:        "3 doshas detected in chart",
  live:           "LIVE",
  riskTitle:      "Risk Radar",
  riskSubAhead:   "Next 24h + 7-day signals",
  riskDashaActive:(_md, _ad) => "Next 24h + 7-day signals",
  alert:          "ALERT",
  milanTitle:     "Kundli Milan",
  milanSub:       "36 guna match · Vivah compatibility",
  pro:            "PRO",
  insightStrong:  "Strong positive energy today",
  insightModerate:"Moderate energy, stay focused",
  insightUnstable:"Energy unstable today",
  insightLow:     "Low energy — rest & introspect",
};

const HOME_LABELS: Partial<Record<UILang, HomeLabels>> = {
  en: HOME_EN,

  hn: {
    namaste:        "Namaste 🙏",
    hello:          "Hello",
    forecastPill:   "7 Din Energy Forecast",
    todaysEnergy:   "AAJ KI ENERGY",
    demo:           "DEMO",
    forecast7day:   "7-din forecast",
    now:            "Abhi",
    doshTitle:      "Dosh Analysis",
    doshSub:        "Kundli mein 3 dosh mile",
    live:           "LIVE",
    riskTitle:      "Risk Radar",
    riskSubAhead:   "Next 24h + 7-day signals",
    riskDashaActive:(_md, _ad) => "Next 24h + 7-day signals",
    alert:          "ALERT",
    milanTitle:     "Kundli Milan",
    milanSub:       "36 guna match · Vivah compatibility",
    pro:            "PRO",
    insightStrong:  "Aaj strong positive energy",
    insightModerate:"Moderate energy, focus rakhein",
    insightUnstable:"Aaj energy unstable hai",
    insightLow:     "Kam energy — aaram aur introspect",
  },

  hi: {
    namaste:        "नमस्ते 🙏",
    hello:          "नमस्ते",
    forecastPill:   "7 दिन का ऊर्जा पूर्वानुमान",
    todaysEnergy:   "आज की ऊर्जा",
    demo:           "डेमो",
    forecast7day:   "7 दिन का पूर्वानुमान",
    now:            "अभी",
    doshTitle:      "दोष विश्लेषण",
    doshSub:        "कुंडली में 3 दोष पाए गए",
    live:           "लाइव",
    riskTitle:      "जोखिम रडार",
    riskSubAhead:   "अगले 24 घंटे + 7 दिन के संकेत",
    riskDashaActive:(_md, _ad) => "अगले 24 घंटे + 7 दिन के संकेत",
    alert:          "अलर्ट",
    milanTitle:     "कुंडली मिलान",
    milanSub:       "36 गुण मिलान · विवाह संगति",
    pro:            "प्रो",
    insightStrong:  "आज प्रबल सकारात्मक ऊर्जा",
    insightModerate:"मध्यम ऊर्जा, ध्यान केंद्रित रखें",
    insightUnstable:"आज ऊर्जा अस्थिर है",
    insightLow:     "कम ऊर्जा — विश्राम व आत्मचिंतन",
  },

  bn: {
    namaste:        "নমস্কার 🙏",
    hello:          "নমস্কার",
    forecastPill:   "৭ দিনের শক্তি পূর্বাভাস",
    todaysEnergy:   "আজকের শক্তি",
    demo:           "ডেমো",
    forecast7day:   "৭ দিনের পূর্বাভাস",
    now:            "এখন",
    doshTitle:      "দোষ বিশ্লেষণ",
    doshSub:        "কুণ্ডলীতে ৩টি দোষ পাওয়া গেছে",
    live:           "লাইভ",
    riskTitle:      "ঝুঁকি রাডার",
    riskSubAhead:   "পরবর্তী ২৪ ঘন্টা + ৭ দিনের সংকেত",
    riskDashaActive:(_md, _ad) => "পরবর্তী ২৪ ঘন্টা + ৭ দিনের সংকেত",
    alert:          "সতর্কতা",
    milanTitle:     "কুণ্ডলী মিলন",
    milanSub:       "৩৬ গুণ মিল · বিবাহ সামঞ্জস্য",
    pro:            "প্রো",
    insightStrong:  "আজ প্রবল ইতিবাচক শক্তি",
    insightModerate:"মাঝারি শক্তি, মনোনিবেশ রাখুন",
    insightUnstable:"আজ শক্তি অস্থির",
    insightLow:     "কম শক্তি — বিশ্রাম ও আত্মচিন্তন",
  },

  mr: {
    namaste:        "नमस्कार 🙏",
    hello:          "नमस्कार",
    forecastPill:   "७ दिवसांचा ऊर्जा अंदाज",
    todaysEnergy:   "आजची ऊर्जा",
    demo:           "डेमो",
    forecast7day:   "७ दिवसांचा अंदाज",
    now:            "आता",
    doshTitle:      "दोष विश्लेषण",
    doshSub:        "कुंडलीत ३ दोष आढळले",
    live:           "थेट",
    riskTitle:      "जोखीम रडार",
    riskSubAhead:   "पुढील २४ तास + ७ दिवसांचे संकेत",
    riskDashaActive:(_md, _ad) => "पुढील २४ तास + ७ दिवसांचे संकेत",
    alert:          "सूचना",
    milanTitle:     "कुंडली मिलन",
    milanSub:       "३६ गुण मिलन · विवाह सुसंगती",
    pro:            "प्रो",
    insightStrong:  "आज प्रबळ सकारात्मक ऊर्जा",
    insightModerate:"मध्यम ऊर्जा, लक्ष केंद्रित ठेवा",
    insightUnstable:"आज ऊर्जा अस्थिर आहे",
    insightLow:     "कमी ऊर्जा — विश्रांती व आत्मचिंतन",
  },

  ta: {
    namaste:        "வணக்கம் 🙏",
    hello:          "வணக்கம்",
    forecastPill:   "7 நாள் ஆற்றல் முன்னறிவிப்பு",
    todaysEnergy:   "இன்றைய ஆற்றல்",
    demo:           "டெமோ",
    forecast7day:   "7 நாள் முன்னறிவிப்பு",
    now:            "இப்போது",
    doshTitle:      "தோஷ பகுப்பாய்வு",
    doshSub:        "ஜாதகத்தில் 3 தோஷங்கள் கண்டறியப்பட்டன",
    live:           "நேரடி",
    riskTitle:      "ஆபத்து ரேடார்",
    riskSubAhead:   "அடுத்த 24 மணி + 7 நாள் சமிக்ஞைகள்",
    riskDashaActive:(_md, _ad) => "அடுத்த 24 மணி + 7 நாள் சமிக்ஞைகள்",
    alert:          "எச்சரிக்கை",
    milanTitle:     "ஜாதக பொருத்தம்",
    milanSub:       "36 குணம் பொருத்தம் · திருமண இணக்கம்",
    pro:            "ப்ரோ",
    insightStrong:  "இன்று வலுவான நேர்மறை ஆற்றல்",
    insightModerate:"மிதமான ஆற்றல், கவனம் செலுத்துங்கள்",
    insightUnstable:"இன்று ஆற்றல் நிலையற்றது",
    insightLow:     "குறைந்த ஆற்றல் — ஓய்வு மற்றும் சிந்தனை",
  },

  te: {
    namaste:        "నమస్తే 🙏",
    hello:          "నమస్తే",
    forecastPill:   "7 రోజుల శక్తి సూచన",
    todaysEnergy:   "నేటి శక్తి",
    demo:           "డెమో",
    forecast7day:   "7 రోజుల సూచన",
    now:            "ఇప్పుడు",
    doshTitle:      "దోష విశ్లేషణ",
    doshSub:        "జాతకంలో 3 దోషాలు కనుగొనబడ్డాయి",
    live:           "లైవ్",
    riskTitle:      "రిస్క్ రాడార్",
    riskSubAhead:   "తదుపరి 24 గం + 7 రోజుల సంకేతాలు",
    riskDashaActive:(_md, _ad) => "తదుపరి 24 గం + 7 రోజుల సంకేతాలు",
    alert:          "హెచ్చరిక",
    milanTitle:     "జాతక మిలన్",
    milanSub:       "36 గుణాల పొంతన · వివాహ అనుకూలత",
    pro:            "ప్రో",
    insightStrong:  "నేడు బలమైన సానుకూల శక్తి",
    insightModerate:"మధ్యస్థ శక్తి, దృష్టి కేంద్రీకరించండి",
    insightUnstable:"నేడు శక్తి అస్థిరం",
    insightLow:     "తక్కువ శక్తి — విశ్రాంతి, ఆత్మచింతన",
  },

  gu: {
    namaste:        "નમસ્તે 🙏",
    hello:          "નમસ્તે",
    forecastPill:   "7 દિવસનું ઊર્જા પૂર્વાનુમાન",
    todaysEnergy:   "આજની ઊર્જા",
    demo:           "ડેમો",
    forecast7day:   "7 દિવસનું પૂર્વાનુમાન",
    now:            "હવે",
    doshTitle:      "દોષ વિશ્લેષણ",
    doshSub:        "કુંડળીમાં 3 દોષ મળ્યા",
    live:           "લાઇવ",
    riskTitle:      "જોખમ રડાર",
    riskSubAhead:   "આગામી 24 કલાક + 7 દિવસના સંકેત",
    riskDashaActive:(_md, _ad) => "આગામી 24 કલાક + 7 દિવસના સંકેત",
    alert:          "ચેતવણી",
    milanTitle:     "કુંડળી મિલન",
    milanSub:       "36 ગુણ મિલન · વિવાહ સુસંગતતા",
    pro:            "પ્રો",
    insightStrong:  "આજે પ્રબળ સકારાત્મક ઊર્જા",
    insightModerate:"મધ્યમ ઊર્જા, ધ્યાન કેન્દ્રિત રાખો",
    insightUnstable:"આજે ઊર્જા અસ્થિર છે",
    insightLow:     "ઓછી ઊર્જા — આરામ અને આત્મચિંતન",
  },

  kn: {
    namaste:        "ನಮಸ್ಕಾರ 🙏",
    hello:          "ನಮಸ್ಕಾರ",
    forecastPill:   "7 ದಿನಗಳ ಶಕ್ತಿ ಮುನ್ಸೂಚನೆ",
    todaysEnergy:   "ಇಂದಿನ ಶಕ್ತಿ",
    demo:           "ಡೆಮೋ",
    forecast7day:   "7-ದಿನಗಳ ಮುನ್ಸೂಚನೆ",
    now:            "ಈಗ",
    doshTitle:      "ದೋಷ ವಿಶ್ಲೇಷಣೆ",
    doshSub:        "ಜಾತಕದಲ್ಲಿ 3 ದೋಷಗಳು ಪತ್ತೆಯಾಗಿವೆ",
    live:           "ಲೈವ್",
    riskTitle:      "ಅಪಾಯ ರಾಡಾರ್",
    riskSubAhead:   "ಮುಂದಿನ 24 ಗಂ + 7 ದಿನಗಳ ಸಂಕೇತಗಳು",
    riskDashaActive:(_md, _ad) => "ಮುಂದಿನ 24 ಗಂ + 7 ದಿನಗಳ ಸಂಕೇತಗಳು",
    alert:          "ಎಚ್ಚರಿಕೆ",
    milanTitle:     "ಕುಂಡಲಿ ಮಿಲನ",
    milanSub:       "36 ಗುಣ ಹೊಂದಾಣಿಕೆ · ವಿವಾಹ ಹೊಂದಾಣಿಕೆ",
    pro:            "ಪ್ರೋ",
    insightStrong:  "ಇಂದು ಪ್ರಬಲ ಸಕಾರಾತ್ಮಕ ಶಕ್ತಿ",
    insightModerate:"ಮಧ್ಯಮ ಶಕ್ತಿ, ಗಮನ ಕೇಂದ್ರೀಕರಿಸಿ",
    insightUnstable:"ಇಂದು ಶಕ್ತಿ ಅಸ್ಥಿರ",
    insightLow:     "ಕಡಿಮೆ ಶಕ್ತಿ — ವಿಶ್ರಾಂತಿ ಮತ್ತು ಆತ್ಮಚಿಂತನೆ",
  },

  ml: {
    namaste:        "നമസ്കാരം 🙏",
    hello:          "നമസ്കാരം",
    forecastPill:   "7 ദിവസത്തെ ഊർജ്ജ പ്രവചനം",
    todaysEnergy:   "ഇന്നത്തെ ഊർജ്ജം",
    demo:           "ഡെമോ",
    forecast7day:   "7 ദിവസത്തെ പ്രവചനം",
    now:            "ഇപ്പോൾ",
    doshTitle:      "ദോഷ വിശകലനം",
    doshSub:        "കുണ്ഡലിയിൽ 3 ദോഷങ്ങൾ കണ്ടെത്തി",
    live:           "ലൈവ്",
    riskTitle:      "റിസ്ക് റഡാർ",
    riskSubAhead:   "അടുത്ത 24 മ + 7 ദിവസത്തെ സൂചനകൾ",
    riskDashaActive:(_md, _ad) => "അടുത്ത 24 മ + 7 ദിവസത്തെ സൂചനകൾ",
    alert:          "മുന്നറിയിപ്പ്",
    milanTitle:     "കുണ്ഡലി മിലൻ",
    milanSub:       "36 ഗുണ പൊരുത്തം · വിവാഹ പൊരുത്തം",
    pro:            "പ്രോ",
    insightStrong:  "ഇന്ന് ശക്തമായ പോസിറ്റീവ് ഊർജ്ജം",
    insightModerate:"മിതമായ ഊർജ്ജം, ശ്രദ്ധ കേന്ദ്രീകരിക്കുക",
    insightUnstable:"ഇന്ന് ഊർജ്ജം അസ്ഥിരം",
    insightLow:     "കുറഞ്ഞ ഊർജ്ജം — വിശ്രമവും ആത്മചിന്തനവും",
  },

  pa: {
    namaste:        "ਸਤ ਸ੍ਰੀ ਅਕਾਲ 🙏",
    hello:          "ਸਤ ਸ੍ਰੀ ਅਕਾਲ",
    forecastPill:   "7 ਦਿਨ ਦਾ ਊਰਜਾ ਅਨੁਮਾਨ",
    todaysEnergy:   "ਅੱਜ ਦੀ ਊਰਜਾ",
    demo:           "ਡੈਮੋ",
    forecast7day:   "7-ਦਿਨ ਦਾ ਅਨੁਮਾਨ",
    now:            "ਹੁਣ",
    doshTitle:      "ਦੋਸ਼ ਵਿਸ਼ਲੇਸ਼ਣ",
    doshSub:        "ਕੁੰਡਲੀ ਵਿੱਚ 3 ਦੋਸ਼ ਮਿਲੇ",
    live:           "ਲਾਈਵ",
    riskTitle:      "ਜੋਖਮ ਰਡਾਰ",
    riskSubAhead:   "ਅਗਲੇ 24 ਘੰਟੇ + 7 ਦਿਨਾਂ ਦੇ ਸੰਕੇਤ",
    riskDashaActive:(_md, _ad) => "ਅਗਲੇ 24 ਘੰਟੇ + 7 ਦਿਨਾਂ ਦੇ ਸੰਕੇਤ",
    alert:          "ਚੇਤਾਵਨੀ",
    milanTitle:     "ਕੁੰਡਲੀ ਮਿਲਾਨ",
    milanSub:       "36 ਗੁਣ ਮਿਲਾਨ · ਵਿਆਹ ਅਨੁਕੂਲਤਾ",
    pro:            "ਪ੍ਰੋ",
    insightStrong:  "ਅੱਜ ਮਜ਼ਬੂਤ ਸਕਾਰਾਤਮਕ ਊਰਜਾ",
    insightModerate:"ਦਰਮਿਆਨੀ ਊਰਜਾ, ਧਿਆਨ ਕੇਂਦਰਿਤ ਰੱਖੋ",
    insightUnstable:"ਅੱਜ ਊਰਜਾ ਅਸਥਿਰ ਹੈ",
    insightLow:     "ਘੱਟ ਊਰਜਾ — ਆਰਾਮ ਅਤੇ ਆਤਮ-ਚਿੰਤਨ",
  },

  or: {
    namaste:        "ନମସ୍କାର 🙏",
    hello:          "ନମସ୍କାର",
    forecastPill:   "୭ ଦିନର ଶକ୍ତି ପୂର୍ବାନୁମାନ",
    todaysEnergy:   "ଆଜିର ଶକ୍ତି",
    demo:           "ଡେମୋ",
    forecast7day:   "୭-ଦିନର ପୂର୍ବାନୁମାନ",
    now:            "ଏବେ",
    doshTitle:      "ଦୋଷ ବିଶ୍ଳେଷଣ",
    doshSub:        "କୁଣ୍ଡଳୀରେ ୩ଟି ଦୋଷ ମିଳିଲା",
    live:           "ଲାଇଭ",
    riskTitle:      "ଝୁଁକି ରାଡାର",
    riskSubAhead:   "ପରବର୍ତ୍ତୀ ୨୪ ଘଣ୍ଟା + ୭ ଦିନର ସଙ୍କେତ",
    riskDashaActive:(_md, _ad) => "ପରବର୍ତ୍ତୀ ୨୪ ଘଣ୍ଟା + ୭ ଦିନର ସଙ୍କେତ",
    alert:          "ସତର୍କତା",
    milanTitle:     "କୁଣ୍ଡଳୀ ମିଳନ",
    milanSub:       "୩୬ ଗୁଣ ମିଳନ · ବିବାହ ସୁସଙ୍ଗତତା",
    pro:            "ପ୍ରୋ",
    insightStrong:  "ଆଜି ଶକ୍ତିଶାଳୀ ସକାରାତ୍ମକ ଶକ୍ତି",
    insightModerate:"ମଧ୍ୟମ ଶକ୍ତି, ଧ୍ୟାନ କେନ୍ଦ୍ରୀଭୂତ ରଖନ୍ତୁ",
    insightUnstable:"ଆଜି ଶକ୍ତି ଅସ୍ଥିର",
    insightLow:     "କମ ଶକ୍ତି — ବିଶ୍ରାମ ଓ ଆତ୍ମଚିନ୍ତନ",
  },

  as: {
    namaste:        "নমস্কাৰ 🙏",
    hello:          "নমস্কাৰ",
    forecastPill:   "৭ দিনৰ শক্তি পূৰ্বানুমান",
    todaysEnergy:   "আজিৰ শক্তি",
    demo:           "ডেমো",
    forecast7day:   "৭-দিনৰ পূৰ্বানুমান",
    now:            "এতিয়া",
    doshTitle:      "দোষ বিশ্লেষণ",
    doshSub:        "কুণ্ডলীত ৩টা দোষ পোৱা গ'ল",
    live:           "লাইভ",
    riskTitle:      "বিপদ ৰাডাৰ",
    riskSubAhead:   "পৰৱৰ্তী ২৪ ঘণ্টা + ৭ দিনৰ সংকেত",
    riskDashaActive:(_md, _ad) => "পৰৱৰ্তী ২৪ ঘণ্টা + ৭ দিনৰ সংকেত",
    alert:          "সতৰ্কবাণী",
    milanTitle:     "কুণ্ডলী মিলন",
    milanSub:       "৩৬ গুণ মিল · বিবাহ সংগতি",
    pro:            "প্ৰো",
    insightStrong:  "আজি প্ৰবল ইতিবাচক শক্তি",
    insightModerate:"মধ্যমীয়া শক্তি, মনোনিৱেশ ৰাখক",
    insightUnstable:"আজি শক্তি অস্থিৰ",
    insightLow:     "কম শক্তি — বিশ্ৰাম আৰু আত্মচিন্তন",
  },
};

function getHomeLabels(lang: UILang): HomeLabels {
  return HOME_LABELS[lang] ?? HOME_EN;
}

// ── Font aliases ──────────────────────────────────────────────────────────────
const F = {
  regular:  "Nunito_400Regular",
  medium:   "Nunito_500Medium",
  semibold: "Nunito_600SemiBold",
  bold:     "Nunito_700Bold",
};

const N = 12;
const DEMO_PTS    = [12, 18, 25, 30, 28, 35, 42, 38, 50, 55, 48, 38];

import { API_BASE as BASE_URL, apiFetch } from "@/lib/apiConfig";

function energyInsight(energy: number, L: ReturnType<typeof getHomeLabels>): { icon: string; text: string; color: string } {
  if (energy >= 75) return { icon: "🔥", text: L.insightStrong,    color: "#22c55e" };
  if (energy >= 55) return { icon: "✨", text: L.insightModerate,  color: "#f59e0b" };
  if (energy >= 35) return { icon: "⚠️", text: L.insightUnstable,  color: "#f97316" };
  return             { icon: "🌑", text: L.insightLow,           color: "#ef4444" };
}

// ── Animation hooks ───────────────────────────────────────────────────────────
function usePulseScale(amplitude = 0.022, dur = 950) {
  const anim = useRef(new Animated.Value(1)).current;
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(anim, { toValue: 1 + amplitude, duration: dur, useNativeDriver: true }),
        Animated.timing(anim, { toValue: 1,             duration: dur, useNativeDriver: true }),
      ])
    ).start();
  }, []);
  return anim;
}

function useOpacityPulse(min = 0.4, max = 1.0, dur = 1100) {
  const anim = useRef(new Animated.Value(min)).current;
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(anim, { toValue: max, duration: dur, useNativeDriver: true }),
        Animated.timing(anim, { toValue: min, duration: dur, useNativeDriver: true }),
      ])
    ).start();
  }, []);
  return anim;
}

function useFadeSlideIn(delay = 0) {
  const opacity   = useRef(new Animated.Value(0)).current;
  const translateY = useRef(new Animated.Value(18)).current;
  useEffect(() => {
    Animated.parallel([
      Animated.timing(opacity,    { toValue: 1, duration: 500, delay, useNativeDriver: true }),
      Animated.timing(translateY, { toValue: 0, duration: 440, delay, useNativeDriver: true }),
    ]).start();
  }, []);
  return { opacity, transform: [{ translateY }] };
}

// ── Shimmer sweep — makes card feel live & active ─────────────────────────────
function useShimmer(cardWidth: number) {
  const anim = useRef(new Animated.Value(-cardWidth)).current;
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.delay(1800),
        Animated.timing(anim, { toValue: cardWidth * 2, duration: 800, useNativeDriver: true }),
        Animated.delay(300),
      ])
    ).start();
    return () => anim.stopAnimation();
  }, [cardWidth]);
  return anim;
}

// ── Blink — for live indicators ───────────────────────────────────────────────
function useBlink(onMs = 450, offMs = 450, pauseMs = 1100) {
  const anim = useRef(new Animated.Value(1)).current;
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(anim, { toValue: 0.1, duration: offMs, useNativeDriver: true }),
        Animated.timing(anim, { toValue: 1,   duration: onMs,  useNativeDriver: true }),
        Animated.delay(pauseMs),
      ])
    ).start();
  }, []);
  return anim;
}

// ── Score counter animation ───────────────────────────────────────────────────
function useCountUp(target: number, delay = 200) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    const timeout = setTimeout(() => {
      let start = 0;
      const step = Math.ceil(target / 30);
      const timer = setInterval(() => {
        start = Math.min(start + step, target);
        setDisplay(start);
        if (start >= target) clearInterval(timer);
      }, 30);
      return () => clearInterval(timer);
    }, delay);
    return () => clearTimeout(timeout);
  }, [target]);
  return display;
}

// ── Home Screen ───────────────────────────────────────────────────────────────
export default function HomeScreen() {
  const insets = useSafeAreaInsets();
  const colors = useColors();
  const { toggle: toggleTheme } = useTheme();
  const { kundli, todayEnergy, setTodayEnergy, setMoonData, moonData, user, isLoading, language } = useUser();
  const t = getT(language);
  // L (home-tab labels) uses the FULL UILang so Odia / Bangla / Marathi /
  // Tamil / Telugu / Gujarati / Kannada / Malayalam / Punjabi / Assamese
  // each render in their own script instead of silently bucketing to Hindi.
  const L = getHomeLabels(language);

  const [targetPts, setTargetPts] = useState<number[]>([]);
  const [labels,    setLabels]    = useState<string[]>([]);
  const [loading,   setLoading]   = useState(false);
  const [settled,   setSettled]   = useState(false);
  const cancelRef = useRef(false);

  const [backendEnergy, setBackendEnergy] = useState<EnergyResult | null>(null);

  useEffect(() => {
    if (!kundli) return;
    cancelRef.current = false;
    setLoading(true); setTargetPts([]); setLabels([]); setSettled(false);
    setBackendEnergy(null);

    // Parallel fetch: moon history (for chart line) + accurate backend energy.
    // Chart line uses the lightweight local calc (visual only), but the hero
    // number comes from the backend Shadbala/Shodhana engine for ~92% accuracy.
    const moonHistPromise = apiFetch(`${BASE_URL}/api/moon_history?count=${N}&interval=2`)
      .then(r => r.json())
      .catch(() => null) as Promise<{ points: MoonHistoryPoint[] } | null>;

    const backendEnergyPromise = fetchTodayEnergy(kundli);

    Promise.all([moonHistPromise, backendEnergyPromise])
      .then(([moonHist, backend]) => {
        if (cancelRef.current) return;

        // Stash full backend result for v3 UI surface (buckets/confidence/flags).
        if (backend) setBackendEnergy(backend);

        if (!moonHist?.points?.length) {
          setLoading(false);
          return;
        }

        // Build chart points from local calc (used for visual line only).
        const lastIdx = moonHist.points.length - 1;
        const values = moonHist.points.map((pt, idx) => {
          const localScore = computeTodayEnergy(pt.longitude, pt.rashiIndex, kundli) ?? 0;
          if (idx === lastIdx) {
            // Current point: prefer accurate backend score; fall back to local.
            const hero = backend?.energy_score ?? localScore;
            setTodayEnergy(hero);
            setMoonData({ longitude: pt.longitude, rashiIndex: pt.rashiIndex });
            return hero;
          }
          return localScore;
        });

        const lbls = moonHist.points.map((pt, idx) =>
          idx === lastIdx ? L.now : pt.label
        );
        setTargetPts(values); setLabels(lbls); setLoading(false);
        setTimeout(() => { if (!cancelRef.current) setSettled(true); }, 1400);
      })
      .catch(() => { if (!cancelRef.current) setLoading(false); });

    return () => { cancelRef.current = true; };
  }, [kundli]);

  // ── All hooks MUST come before any early return ───────────────────────────
  const greetAnim = useFadeSlideIn(0);
  const heroAnim  = useFadeSlideIn(120);
  const card1Anim = useFadeSlideIn(220);
  const card2Anim = useFadeSlideIn(310);
  const card3Anim = useFadeSlideIn(400);

  if (!isLoading && !user) return <Redirect href="/login" />;

  const androidStatusBar = StatusBar.currentHeight ?? 24;
  const topPad = Platform.OS === "web" ? 67 : Platform.OS === "android" ? Math.max(insets.top, androidStatusBar) : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  const showDemo    = !kundli;
  const chartPts    = showDemo ? DEMO_PTS    : targetPts;
  const chartLbls   = showDemo ? getDemoLabels(language) : labels;
  const chartEnergy = showDemo ? 38          : (todayEnergy ?? 0);
  const insight     = energyInsight(chartEnergy, L);

  const activeDasha: ActiveDashaResult | null =
    kundli && moonData ? computeActiveDasha(kundli, moonData.longitude) : null;

  return (
    <CosmicBg contentStyle={{ paddingTop: topPad, paddingBottom: botPad + 100 }}>

      {/* ── Greeting ── */}
      <Animated.View style={[styles.greetRow, greetAnim, { paddingHorizontal: 16, paddingVertical: 8 }]}>
        <View>
          <Text style={[styles.greetSub, { color: colors.mutedForeground }]}>
            {kundli ? L.namaste : L.hello}
          </Text>
          <Text style={[styles.greetTitle, { color: colors.foreground }]}>
            {kundli ? kundli.name : t.todayEnergy}
          </Text>
        </View>
        <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
          <Pressable
            onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/forecast"); }}
            style={[styles.themeToggleBtn, { backgroundColor: colors.C.bgCard2, borderColor: colors.C.border }]}
          >
            <Feather name="calendar" size={14} color={colors.C.textMuted} />
          </Pressable>
          <Pressable
            onPress={() => { toggleTheme(); Haptics.selectionAsync(); }}
            style={[styles.themeToggleBtn, { backgroundColor: colors.C.bgCard2, borderColor: colors.C.border }]}
          >
            <Feather name={colors.C.isDark ? "sun" : "moon"} size={15} color={colors.C.textMuted} />
          </Pressable>
        </View>
      </Animated.View>

      {/* ── Hero Energy Card — immersive ── */}
      <Animated.View style={[heroAnim, { flex: 6, paddingHorizontal: 8, paddingBottom: 6 }]}>
        <Pressable
          onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/daily-alerts"); }}
          style={({ pressed }) => [{ flex: 1, opacity: pressed ? 0.92 : 1, transform: [{ scale: pressed ? 0.988 : 1 }] }]}
        >
          <HeroEnergyCard
            chartPts={chartPts}
            chartLbls={chartLbls}
            chartEnergy={chartEnergy}
            insight={insight}
            showDemo={showDemo}
            loading={!showDemo && loading && targetPts.length === 0}
            L={L}
            backend={showDemo ? null : backendEnergy}
          />
        </Pressable>
      </Animated.View>

      {/* ── 3 Feature Rows — 35% ── */}
      <View style={{ flex: 4, paddingHorizontal: 12, paddingBottom: 6, justifyContent: "space-around" }}>

        <Animated.View style={card1Anim}>
          <DoshMini L={L} onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); router.push("/dosh"); }} />
        </Animated.View>

        <Animated.View style={card2Anim}>
          <BadTimeMini L={L} onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/dasha-risk"); }} activeDasha={activeDasha} />
        </Animated.View>

        <Animated.View style={card3Anim}>
          <MilanMini L={L} onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); router.push("/kundli-milan"); }} />
        </Animated.View>

      </View>

    </CosmicBg>
  );
}

// ── v3 helpers — confidence + flag → display + bucket meta ────────────────────
function confidenceMeta(c?: string): { color: string; label: string } | null {
  if (c === "high")   return { color: "#10b981", label: "high" };
  if (c === "medium") return { color: "#f59e0b", label: "med" };
  if (c === "low")    return { color: "#ef4444", label: "low" };
  return null;
}

function flagToDisplay(flag: EnergyFlag): { icon: string; text: string; color: string } {
  // Defensive fallbacks for every optional field — never render literal "undefined".
  switch (flag.type) {
    case "saturn":
      return { icon: "♄", text: String(flag.phase ?? "Saturn active"), color: "#a78bfa" };
    case "chandrashtama":
      return { icon: "🌑", text: "Chandrashtama — mind unsettled", color: "#ef4444" };
    case "tithi_rikta":
      return { icon: "📉", text: `${flag.tithi ?? "Rikta"} — energy drain`, color: "#f59e0b" };
    case "tithi_purna":
      return { icon: "✨", text: `${flag.tithi ?? "Purna"} — boost`, color: "#10b981" };
    case "tara":
      return { icon: "⭐", text: `${flag.name ?? "Tara"} Tara`, color: "#ef4444" };
    case "md_sandhi":
      return { icon: "🔄", text: "Mahadasha sandhi", color: "#f59e0b" };
    case "pd_retrograde":
      return { icon: "↺", text: `${flag.planet ?? "PD lord"} vakri`, color: "#8b5cf6" };
  }
  return { icon: "•", text: "Active flag", color: "#888" };
}

const BUCKET_META = {
  physical: { icon: "💪", short: "Phy", color: "#ef4444" },
  mental:   { icon: "🧘", short: "Mnd", color: "#3b82f6" },
  luck:     { icon: "🍀", short: "Luk", color: "#10b981" },
} as const;

function HeroEnergyCard({ chartPts, chartLbls, chartEnergy, insight, showDemo, loading, L, backend }: {
  chartPts: number[]; chartLbls: string[]; chartEnergy: number;
  insight: { icon: string; text: string; color: string };
  showDemo: boolean; loading: boolean;
  L: ReturnType<typeof getHomeLabels>;
  backend: EnergyResult | null;
}) {
  const { C: Ctheme } = useColors();
  const displayScore = useCountUp(chartEnergy, 350);

  const conf       = !showDemo ? confidenceMeta(backend?.confidence) : null;
  const buckets    = !showDemo ? backend?.buckets : null;
  const topFlag    = !showDemo && backend?.active_flags?.length
    ? flagToDisplay(backend.active_flags[0])
    : null;

  return (
    <View style={[hero.card, { flex: 1, backgroundColor: "#0f0a24", borderColor: `${insight.color}40`, borderWidth: 1, shadowColor: insight.color, shadowOpacity: 0.28, shadowRadius: 24, shadowOffset: { width: 0, height: 0 } } as any]}>

      {/* ── Centered score — single hero value ── */}
      <View style={hero.topRow}>
        <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
          <Text style={[hero.label, { color: "rgba(255,255,255,0.45)" }]}>{L.todaysEnergy}</Text>
          {showDemo && (
            <View style={[hero.demoBadge, { backgroundColor: Ctheme.bgCard2, borderColor: Ctheme.border }]}>
              <Feather name="lock" size={8} color={Ctheme.textDim} />
              <Text style={[hero.demoBadgeText, { color: Ctheme.textDim }]}>{L.demo}</Text>
            </View>
          )}
          {conf && (
            <View style={[hero.confChip, { borderColor: `${conf.color}55`, backgroundColor: `${conf.color}12` }]}>
              <View style={[hero.confDot, { backgroundColor: conf.color }]} />
              <Text style={[hero.confTxt, { color: conf.color }]}>{conf.label}</Text>
            </View>
          )}
        </View>
        <View style={{ flexDirection: "row", alignItems: "flex-end", gap: 2 }}>
          <Text style={[hero.score, { color: insight.color }]}>{displayScore}</Text>
          <Text style={[hero.scoreMax, { color: Ctheme.textDim }]}>/100</Text>
        </View>
      </View>

      {/* ── CHART — fills remaining space, immersive ── */}
      <View style={{ flex: 1 }}>
        <EnergyChart
          targetPts={chartPts}
          labels={chartLbls}
          finalEnergy={chartEnergy}
          loading={loading}
          instant={showDemo}
        />
      </View>

      {/* ── Bottom: insight (or top flag) ── */}
      <View style={{ flexDirection: "row", alignItems: "center" }}>
        {topFlag ? (
          <View style={[hero.insightPill, { backgroundColor: `${topFlag.color}10`, borderColor: `${topFlag.color}30` }]}>
            <Text style={hero.insightIcon}>{topFlag.icon}</Text>
            <Text style={[hero.insightText, { color: topFlag.color }]} numberOfLines={1}>{topFlag.text}</Text>
          </View>
        ) : (
          <View style={[hero.insightPill, { backgroundColor: `${insight.color}10`, borderColor: `${insight.color}20` }]}>
            <Text style={hero.insightIcon}>{insight.icon}</Text>
            <Text style={[hero.insightText, { color: insight.color }]}>{insight.text}</Text>
          </View>
        )}
      </View>
    </View>
  );
}

// ── Dosh Mini — full-width horizontal row ─────────────────────────────────────
function DoshMini({ onPress, L }: { onPress: () => void; L: ReturnType<typeof getHomeLabels> }) {
  const blinkDot = useBlink(400, 400, 1400);
  const shimmerX = useShimmer(360);
  const { C } = useColors();
  const grad = C.isDark
    ? (["#3b0a0a","#5c1111"] as const)
    : (["#fff0f0","#ffe2e6"] as const);
  const titleClr = C.isDark ? "#ffffff" : "#be123c";
  const subClr   = C.isDark ? "rgba(255,255,255,0.45)" : "rgba(190,18,60,0.6)";

  return (
    <Pressable onPress={onPress} style={({ pressed }) => [mini.row, pressed && mini.rowPressed]}>
      <LinearGradient colors={grad} start={{x:0,y:0}} end={{x:1,y:0}} style={mini.rowGrad}>
        <Animated.View style={[mini.shimmer, { transform: [{ translateX: shimmerX }] }]} />
        <View style={[mini.border, { borderColor: C.isDark ? "rgba(255,51,85,0.35)" : "rgba(255,51,85,0.20)" }]} />

        <View style={[mini.iconCircle, { backgroundColor:"rgba(255,34,68,0.18)", borderColor:"rgba(255,34,68,0.35)" }]}>
          <Text style={mini.iconEmoji}>☿</Text>
        </View>

        <View style={mini.textBlock}>
          <Text style={[mini.rowTitle, { color: titleClr }]}>{L.doshTitle}</Text>
          <Text style={[mini.rowSub, { color: subClr }]}>{L.doshSub}</Text>
        </View>

        <View style={mini.rightBlock}>
          <View style={[mini.badge, { backgroundColor:"rgba(255,34,68,0.18)", borderColor:"rgba(255,34,68,0.4)" }]}>
            <Animated.View style={[mini.badgeDot, { backgroundColor:"#ff2244", opacity: blinkDot }]} />
            <Text style={[mini.badgeTxt, { color:"#ff6b6b" }]}>{L.live}</Text>
          </View>
          <Feather name="chevron-right" size={14} color={C.isDark ? "rgba(255,107,107,0.5)" : "rgba(190,18,60,0.5)"} />
        </View>
      </LinearGradient>
    </Pressable>
  );
}

// ── Bad Time Mini — full-width horizontal row ─────────────────────────────────
function BadTimeMini({ onPress, activeDasha, L }: { onPress: () => void; activeDasha: ActiveDashaResult | null; L: ReturnType<typeof getHomeLabels> }) {
  const blinkDot = useBlink(350, 350, 1200);
  const shimmerX = useShimmer(360);
  const { C } = useColors();
  const grad = C.isDark
    ? (["#2d1005","#5c2208"] as const)
    : (["#fff5ec","#ffe8d0"] as const);
  const titleClr = C.isDark ? "#ffffff" : "#c2410c";
  const subClr   = C.isDark ? "rgba(255,255,255,0.45)" : "rgba(194,65,12,0.6)";

  return (
    <Pressable onPress={onPress} style={({ pressed }) => [mini.row, pressed && mini.rowPressed]}>
      <LinearGradient colors={grad} start={{x:0,y:0}} end={{x:1,y:0}} style={mini.rowGrad}>
        <Animated.View style={[mini.shimmer, { transform: [{ translateX: shimmerX }] }]} />
        <View style={[mini.border, { borderColor: C.isDark ? "rgba(249,115,22,0.35)" : "rgba(249,115,22,0.22)" }]} />

        <View style={[mini.iconCircle, { backgroundColor:"rgba(249,115,22,0.18)", borderColor:"rgba(249,115,22,0.35)" }]}>
          <Text style={mini.iconEmoji}>⚡</Text>
        </View>

        <View style={mini.textBlock}>
          <Text style={[mini.rowTitle, { color: titleClr }]}>{L.riskTitle}</Text>
          <Text style={[mini.rowSub, { color: subClr }]}>
            {activeDasha ? L.riskDashaActive(activeDasha.mdPlanet, activeDasha.adPlanet) : L.riskSubAhead}
          </Text>
        </View>

        <View style={mini.rightBlock}>
          <View style={[mini.badge, { backgroundColor:"rgba(249,115,22,0.18)", borderColor:"rgba(249,115,22,0.4)" }]}>
            <Animated.View style={[mini.badgeDot, { backgroundColor:"#f97316", opacity: blinkDot }]} />
            <Text style={[mini.badgeTxt, { color:"#fb923c" }]}>{L.alert}</Text>
          </View>
          <Feather name="chevron-right" size={14} color={C.isDark ? "rgba(251,146,60,0.5)" : "rgba(194,65,12,0.5)"} />
        </View>
      </LinearGradient>
    </Pressable>
  );
}

// ── Kundli Milan Mini — full-width horizontal row ─────────────────────────────
function MilanMini({ onPress, L }: { onPress: () => void; L: ReturnType<typeof getHomeLabels> }) {
  const shimmerX = useShimmer(360);
  const { C } = useColors();
  const grad = C.isDark
    ? (["#1e0a3d","#3b1570"] as const)
    : (["#f5f0ff","#ede0fe"] as const);
  const titleClr = C.isDark ? "#ffffff" : "#6d28d9";
  const subClr   = C.isDark ? "rgba(255,255,255,0.45)" : "rgba(109,40,217,0.6)";

  return (
    <Pressable onPress={onPress} style={({ pressed }) => [mini.row, pressed && mini.rowPressed]}>
      <LinearGradient colors={grad} start={{x:0,y:0}} end={{x:1,y:0}} style={mini.rowGrad}>
        <Animated.View style={[mini.shimmer, { transform: [{ translateX: shimmerX }] }]} />
        <View style={[mini.border, { borderColor: C.isDark ? "rgba(168,85,247,0.35)" : "rgba(168,85,247,0.22)" }]} />

        <View style={[mini.iconCircle, { backgroundColor:"rgba(168,85,247,0.18)", borderColor:"rgba(168,85,247,0.35)" }]}>
          <Text style={mini.iconEmoji}>♥</Text>
        </View>

        <View style={mini.textBlock}>
          <Text style={[mini.rowTitle, { color: titleClr }]}>{L.milanTitle}</Text>
          <Text style={[mini.rowSub, { color: subClr }]}>{L.milanSub}</Text>
        </View>

        <View style={mini.rightBlock}>
          <View style={[mini.badge, { backgroundColor:"rgba(168,85,247,0.18)", borderColor:"rgba(168,85,247,0.4)" }]}>
            <Feather name="lock" size={8} color="#c084fc" />
            <Text style={[mini.badgeTxt, { color:"#c084fc" }]}>{L.pro}</Text>
          </View>
          <Feather name="chevron-right" size={14} color={C.isDark ? "rgba(192,132,252,0.5)" : "rgba(109,40,217,0.5)"} />
        </View>
      </LinearGradient>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  root:    { flex: 1 },
  content: { paddingHorizontal: 14, gap: 9 },

  greetRow: {
    flexDirection: "row", alignItems: "center",
    justifyContent: "space-between", marginBottom: 2,
  },
  greetSub: {
    color: "#3d5a7a", fontSize: 11,
    fontFamily: F.semibold, letterSpacing: 0.2,
  },
  greetTitle: {
    color: "#dde8f4", fontSize: 17,
    fontFamily: F.bold, marginTop: 1, letterSpacing: -0.3,
  },
  forecastPill: {
    flexDirection: "row", alignItems: "center", gap: 5,
    backgroundColor: "rgba(245,158,11,0.07)", borderWidth: 1,
    borderColor: "rgba(245,158,11,0.22)", borderRadius: 20,
    paddingVertical: 7, paddingHorizontal: 11,
  },
  forecastPillText: {
    color: "#f59e0b", fontSize: 11, fontFamily: F.bold,
  },
  themeToggleBtn: {
    width: 32, height: 32, borderRadius: 16,
    alignItems: "center", justifyContent: "center",
    borderWidth: 1,
  },
});

const hero = StyleSheet.create({
  card: {
    backgroundColor: "#040e1e", borderRadius: 16, borderWidth: 1,
    borderColor: "rgba(255,255,255,0.06)", paddingHorizontal: 10,
    paddingTop: 10, paddingBottom: 8, overflow: "hidden", gap: 4,
    shadowColor: "#f59e0b", shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.1, shadowRadius: 18, elevation: 5,
  },
  topRow: {
    flexDirection: "row", alignItems: "center",
    justifyContent: "space-between",
  },
  label:    { fontSize: 8.5, fontFamily: F.bold, letterSpacing: 2 },
  score:    { fontSize: 28, fontFamily: F.bold, letterSpacing: -1, lineHeight: 32 },
  scoreMax: { fontSize: 12, fontFamily: F.semibold, paddingBottom: 3 },
  demoBadge: {
    flexDirection: "row", alignItems: "center", gap: 3,
    borderWidth: 1, paddingVertical: 2,
    paddingHorizontal: 6, borderRadius: 5,
  },
  demoBadgeText: { fontSize: 7, fontFamily: F.bold, letterSpacing: 1.2 },
  insightPill: {
    flexDirection: "row", alignItems: "center", gap: 5,
    borderWidth: 1, borderRadius: 7, paddingVertical: 4, paddingHorizontal: 8,
    flexShrink: 1, maxWidth: "70%",
  },
  insightIcon: { fontSize: 11 },
  insightText: { fontSize: 9.5, fontFamily: F.semibold, maxWidth: 160 },
  // v3 — confidence chip next to score label
  confChip: {
    flexDirection: "row", alignItems: "center", gap: 4,
    borderWidth: 1, borderRadius: 6, paddingVertical: 1.5, paddingHorizontal: 5,
  },
  confDot: { width: 5, height: 5, borderRadius: 2.5 },
  confTxt: { fontSize: 7.5, fontFamily: F.bold, letterSpacing: 0.5, textTransform: "uppercase" },
  // v3 — 3-bucket strip below chart
  bucketRow: {
    flexDirection: "row", gap: 6, paddingVertical: 2,
  },
  bucketChip: {
    flex: 1, flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 4, borderWidth: 1, borderRadius: 8,
    paddingVertical: 4, paddingHorizontal: 6,
  },
  bucketIcon:  { fontSize: 11 },
  bucketShort: { fontSize: 8.5, fontFamily: F.bold, letterSpacing: 0.6 },
  bucketScore: { fontSize: 11, fontFamily: F.bold, letterSpacing: -0.3 },
});

// ── Mini cards — full-width horizontal rows ────────────────────────────────────
const mini = StyleSheet.create({
  row: {
    borderRadius: 14, overflow: "hidden",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4, shadowRadius: 10, elevation: 6,
  },
  rowPressed: { opacity: 0.82 },
  rowGrad: {
    flexDirection: "row", alignItems: "center", gap: 12,
    paddingVertical: 13, paddingHorizontal: 14, overflow: "hidden",
  },
  shimmer: {
    position: "absolute", top: 0, bottom: 0, width: 60, zIndex: 2,
    backgroundColor: "rgba(255,255,255,0.06)",
    transform: [{ skewX: "-18deg" }],
  },
  border: {
    position: "absolute", inset: 0, borderRadius: 14,
    borderWidth: 1, zIndex: 1,
  },
  iconCircle: {
    width: 40, height: 40, borderRadius: 12,
    borderWidth: 1, alignItems: "center", justifyContent: "center",
  },
  iconEmoji: { fontSize: 18 },
  textBlock: { flex: 1, gap: 2 },
  rowTitle: { color: "#ffffff", fontSize: 13.5, fontFamily: F.bold, letterSpacing: -0.2 },
  rowSub:   { color: "rgba(255,255,255,0.45)", fontSize: 10.5, fontFamily: F.medium },
  rightBlock: { flexDirection: "row", alignItems: "center", gap: 8 },
  badge: {
    flexDirection: "row", alignItems: "center", gap: 4,
    borderWidth: 1, borderRadius: 20,
    paddingVertical: 3, paddingHorizontal: 8,
  },
  badgeDot: { width: 5, height: 5, borderRadius: 2.5 },
  badgeTxt: { fontSize: 8.5, fontFamily: F.bold, letterSpacing: 1 },
});

// ── Shared card layout ────────────────────────────────────────────────────────
const CARD_RADIUS   = 18;
const CARD_PADDING  = 14;

