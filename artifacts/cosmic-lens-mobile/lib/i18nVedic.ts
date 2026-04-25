// ══════════════════════════════════════════════════════════════════════════════
// COSMIC LENS — Vedic Vocabulary Translations
// Central lookup for rashi names, planets, days, gemstones, directions, etc.
// FULL 25-language support: en, hn, hi + 22 auto-translated langs.
// AUTO-GENERATED — edit scripts/i18n-translate/vedic-source.json + out-vedic/*.json,
// then run: node scripts/i18n-translate/gen-i18nVedic.mjs
// ══════════════════════════════════════════════════════════════════════════════

import type { UILang } from "./i18n";

// VLang stays as 3-bucket for legacy paragraph content (rashifal, remedies, etc).
export type VLang = "en" | "hn" | "hi";

// 25 → 3 bucket mapper for legacy 3-bucket dictionaries.
export function vedicLang(l: UILang): VLang {
  if (l === "en") return "en";
  if (l === "hn") return "hn";
  if (["hi","bn","mr","ta","te","gu","kn","ml","pa","or","as"].includes(l as string)) return "hi";
  return "en";
}

// LangMap = string for every UILang (full 25-lang Vedic vocabulary).
export type LangMap = Record<UILang, string>;
// Triplet kept for legacy 3-bucket content blocks (paragraphs/themes/etc).
export type Triplet = { en: string; hn: string; hi: string };

// pick() works with either LangMap OR Triplet:
// - If lang exists in object → return it (LangMap path: full 25-lang lookup)
// - Otherwise fall back via vedicLang() bucket (Triplet path: 3-bucket lookup)
// - Final fallback: en
export function pick(lang: UILang | VLang, t: LangMap | Partial<LangMap> | Triplet): string {
  const direct = (t as any)[lang as string];
  if (typeof direct === "string" && direct.length > 0) return direct;
  const bucket = vedicLang(lang as UILang);
  const bv = (t as any)[bucket];
  if (typeof bv === "string" && bv.length > 0) return bv;
  return (t as any).en ?? "";
}

// ── Rashi (zodiac signs) ─────────────────────────────────────────────────────
export type RashiKey =
  | "mesh" | "vrishabh" | "mithun" | "kark" | "simha" | "kanya"
  | "tula" | "vrishchik" | "dhanu" | "makar" | "kumbh" | "meen";

export const RASHI: Record<RashiKey, LangMap & { emoji: string; lord: string }> = {
  mesh      : { en: "Aries", hn: "Mesh", hi: "मेष", bn: "মেষ", mr: "मेष", ta: "மேஷம்", te: "మేష", gu: "મેષ", kn: "ಮೇಷ", ml: "മേടം", pa: "ਮੇਸ਼", or: "ମେଷ", as: "মেষ", zh: "白羊座", es: "Aries", ar: "الحمل", fr: "Bélier", pt: "Áries", de: "Widder", ru: "Овен", ja: "牡羊座", id: "Aries", ko: "양자리", tr: "Koç", emoji: "♈", lord: "mangal" },
  vrishabh  : { en: "Taurus", hn: "Vrishabh", hi: "वृषभ", bn: "বৃষ", mr: "वृषभ", ta: "வரிஷபம்", te: "వృషభ", gu: "વૃષભ", kn: "ವೃಷಭ", ml: "ഇടവം", pa: "ਵ੍ਰਿਸ਼ਭ", or: "ବୃଷଭ", as: "বৃষ", zh: "金牛座", es: "Tauro", ar: "الثور", fr: "Taureau", pt: "Touro", de: "Stier", ru: "Телец", ja: "牡牛座", id: "Taurus", ko: "황소자리", tr: "Boğa", emoji: "♉", lord: "shukra" },
  mithun    : { en: "Gemini", hn: "Mithun", hi: "मिथुन", bn: "মিথুন", mr: "मिथुन", ta: "மிதுனம்", te: "మిథున", gu: "મિથુન", kn: "ಮಿಥುನ", ml: "മിഥുനം", pa: "ਮਿਥੁਨ", or: "ମଥୁନ", as: "মিথুন", zh: "双子座", es: "Géminis", ar: "الجوزاء", fr: "Gémeaux", pt: "Gêmeos", de: "Zwillinge", ru: "Близнецы", ja: "双子座", id: "Gemini", ko: "쌍둥이자리", tr: "İkizler", emoji: "♊", lord: "budh" },
  kark      : { en: "Cancer", hn: "Kark", hi: "कर्क", bn: "কর্কট", mr: "कर्क", ta: "கடகம்", te: "కర్కాటక", gu: "કર્ક", kn: "ಕರ್ಕೋಟಕ", ml: "കർക്കടകം", pa: "ਕਰਕ", or: "କର୍କଟ", as: "কর্কট", zh: "巨蟹座", es: "Cáncer", ar: "السرطان", fr: "Cancer", pt: "Câncer", de: "Krebs", ru: "Рак", ja: "蟹座", id: "Cancer", ko: "게자리", tr: "Yengeç", emoji: "♋", lord: "chandra" },
  simha     : { en: "Leo", hn: "Simha", hi: "सिंह", bn: "সিংহ", mr: "सिंह", ta: "சிம்மம்", te: "సింహ", gu: "સિંહ", kn: "ಸಿಂಹ", ml: "സിംഹം", pa: "ਸਿੰਘ", or: "ସିଂହ", as: "সিংহ", zh: "狮子座", es: "Leo", ar: "الأسد", fr: "Lion", pt: "Leão", de: "Löwe", ru: "Лев", ja: "獅子座", id: "Leo", ko: "사자자리", tr: "Aslan", emoji: "♌", lord: "surya" },
  kanya     : { en: "Virgo", hn: "Kanya", hi: "कन्या", bn: "কন্যা", mr: "कन्या", ta: "கன்னி", te: "కన్యా", gu: "કન્યા", kn: "ಕನ್ಯಾ", ml: "കന്നി", pa: "ਕੰਯਾ", or: "କନ୍ୟା", as: "কন্যা", zh: "处女座", es: "Virgo", ar: "العذراء", fr: "Vierge", pt: "Virgem", de: "Jungfrau", ru: "Дева", ja: "乙女座", id: "Virgo", ko: "처녀자리", tr: "Başak", emoji: "♍", lord: "budh" },
  tula      : { en: "Libra", hn: "Tula", hi: "तुला", bn: "তুলা", mr: "तुळा", ta: "துலாம்", te: "తులా", gu: "તુલા", kn: "ತುಲಾ", ml: "തുലാം", pa: "ਤੁਲਾ", or: "ତୁଳା", as: "তুলা", zh: "天秤座", es: "Libra", ar: "الميزان", fr: "Balance", pt: "Libra", de: "Waage", ru: "Весы", ja: "天秤座", id: "Libra", ko: "천칭자리", tr: "Terazi", emoji: "♎", lord: "shukra" },
  vrishchik : { en: "Scorpio", hn: "Vrishchik", hi: "वृश्चिक", bn: "বৃশ্চিক", mr: "वृश्चिक", ta: "விருச்சிகம்", te: "వృష్చిక", gu: "વૃશ્ચિક", kn: "ವೃಶ್ಚಿಕ", ml: "വൃശ്ചികം", pa: "ਵ੍ਰਿਸ਼ਚਿਕ", or: "ବୃଶ୍ଚିକ", as: "বৃশ্চিক", zh: "天蝎座", es: "Escorpio", ar: "العقرب", fr: "Scorpion", pt: "Escorpião", de: "Skorpion", ru: "Скорпион", ja: "蠍座", id: "Scorpio", ko: "전갈자리", tr: "Akrep", emoji: "♏", lord: "mangal" },
  dhanu     : { en: "Sagittarius", hn: "Dhanu", hi: "धनु", bn: "ধনু", mr: "धनु", ta: "தனுசு", te: "ధనుస్సు", gu: "ધનુ", kn: "ಧನು", ml: "ധനു", pa: "ਧਨੁ", or: "ଧନୁ", as: "ধনু", zh: "人马座", es: "Sagitario", ar: "القوس", fr: "Sagittaire", pt: "Sagitário", de: "Schütze", ru: "Стрелец", ja: "射手座", id: "Sagittarius", ko: "궁수자리", tr: "Yay", emoji: "♐", lord: "guru" },
  makar     : { en: "Capricorn", hn: "Makar", hi: "मकर", bn: "মকর", mr: "मकर", ta: "மகரம்", te: "మకరం", gu: "મકર", kn: "ಮಕರ", ml: "മകരം", pa: "ਮਕਰ", or: "ମକର", as: "মকর", zh: "摩羯座", es: "Capricornio", ar: "الجدي", fr: "Capricorne", pt: "Capricórnio", de: "Steinbock", ru: "Козерог", ja: "山羊座", id: "Capricorn", ko: "염소자리", tr: "Oğlak", emoji: "♑", lord: "shani" },
  kumbh     : { en: "Aquarius", hn: "Kumbh", hi: "कुम्भ", bn: "কুম্ভ", mr: "कुंभ", ta: "கும்பம்", te: "కుంభ", gu: "કુંભ", kn: "ಕುಂಭ", ml: "കുംഭം", pa: "ਕੁੰਭ", or: "କୁମ୍ଭ", as: "কুম্ভ", zh: "宝瓶座", es: "Acuario", ar: "الدلو", fr: "Verseau", pt: "Aquário", de: "Wassermann", ru: "Водолей", ja: "水瓶座", id: "Aquarius", ko: "물병자리", tr: "Kova", emoji: "♒", lord: "shani" },
  meen      : { en: "Pisces", hn: "Meen", hi: "मीन", bn: "মীন", mr: "मीन", ta: "மீனம்", te: "మీనం", gu: "મીન", kn: "ಮೀನ", ml: "മീനം", pa: "ਮੀਨ", or: "ମୀନ", as: "মীন", zh: "双鱼座", es: "Piscis", ar: "الحوت", fr: "Poissons", pt: "Peixes", de: "Fische", ru: "Рыбы", ja: "魚座", id: "Pisces", ko: "물고기자리", tr: "Balık", emoji: "♓", lord: "guru" },
};

// ── Planets ──────────────────────────────────────────────────────────────────
export type PlanetKey =
  | "surya" | "chandra" | "mangal" | "budh" | "guru"
  | "shukra" | "shani" | "rahu" | "ketu";

export const PLANET: Record<PlanetKey, LangMap> = {
  surya   : { en: "Sun", hn: "Surya", hi: "सूर्य", bn: "সূর্য", mr: "सूर्य", ta: "சூரியன்", te: "సూర్యుడు", gu: "সূর્ય", kn: "ಸೂರ್ಯ", ml: "സൂര്യൻ", pa: "ਸੂਰਜ", or: "ସୂର୍ଯ୍ୟ", as: "সূর্য", zh: "太阳", es: "Sol", ar: "الشمس", fr: "Soleil", pt: "Sol", de: "Sonne", ru: "Солнце", ja: "太陽", id: "Matahari", ko: "태양", tr: "Güneş" },
  chandra : { en: "Moon", hn: "Chandra", hi: "चंद्र", bn: "চন্দ্র", mr: "चंद्र", ta: "சந்திரன்", te: "చంద్రుడు", gu: "ચંદ્ર", kn: "ಚಂದ್ರ", ml: "ചന്ദ്രൻ", pa: "ਚੰਦਰਮਾ", or: "ଚନ୍ଦ୍ର", as: "চন্দ্ৰ", zh: "月亮", es: "Luna", ar: "القمر", fr: "Lune", pt: "Lua", de: "Mond", ru: "Луна", ja: "月", id: "Bulan", ko: "달", tr: "Ay" },
  mangal  : { en: "Mars", hn: "Mangal", hi: "मंगल", bn: "মঙ্গল", mr: "मंगळ", ta: "செவ்வாய்", te: "మంగళ", gu: "મંગળ", kn: "ಮಂಗಳ", ml: "കുജം", pa: "ਮੰਗਲ", or: "ମଙ୍ଗଳ", as: "মঙ্গল", zh: "火星", es: "Marte", ar: "المريخ", fr: "Mars", pt: "Marte", de: "Mars", ru: "Марс", ja: "火星", id: "Mars", ko: "화성", tr: "Mars" },
  budh    : { en: "Mercury", hn: "Budh", hi: "बुध", bn: "বুধ", mr: "बुध", ta: "புதன்", te: "బుధుడు", gu: "બુધ", kn: "ಬುಧ", ml: "ബുധൻ", pa: "ਬੁੱਧ", or: "ବୁଧ", as: "বুধ", zh: "水星", es: "Mercurio", ar: "عطارد", fr: "Mercure", pt: "Mercúrio", de: "Merkur", ru: "Меркурий", ja: "水星", id: "Merkurius", ko: "수성", tr: "Merkür" },
  guru    : { en: "Jupiter", hn: "Guru", hi: "गुरु", bn: "বৃহস্পতি", mr: "गुरू", ta: "குரு", te: "బృహస్పతి", gu: "ગુરુ", kn: "ಗುರು", ml: "ഗുരു", pa: "ਗੁਰੂ", or: "ଗୁରୁ", as: "বৃহস্পতি", zh: "木星", es: "Júpiter", ar: "المشتري", fr: "Jupiter", pt: "Júpiter", de: "Jupiter", ru: "Юпитер", ja: "木星", id: "Yupiter", ko: "목성", tr: "Jüpiter" },
  shukra  : { en: "Venus", hn: "Shukra", hi: "शुक्र", bn: "শুক্র", mr: "शुक्र", ta: "சுக்கிரன்", te: "శుక్రుడు", gu: "શુક્ર", kn: "ಶುಕ್ರ", ml: "ശുക്രൻ", pa: "ਸ਼ੁੱਕ੍ਰ", or: "ଶୁକ୍ର", as: "শুক্ৰ", zh: "金星", es: "Venus", ar: "الزهرة", fr: "Vénus", pt: "Vênus", de: "Venus", ru: "Венера", ja: "金星", id: "Venus", ko: "금성", tr: "Venüs" },
  shani   : { en: "Saturn", hn: "Shani", hi: "शनि", bn: "শনি", mr: "शनि", ta: "சனி", te: "శని", gu: "શનિ", kn: "ಶನಿ", ml: "ശനി", pa: "ਸ਼ਨੀ", or: "ଶନି", as: "শনি", zh: "土星", es: "Saturno", ar: "زحل", fr: "Saturne", pt: "Saturno", de: "Saturn", ru: "Сатурн", ja: "土星", id: "Saturnus", ko: "토성", tr: "Satürn" },
  rahu    : { en: "Rahu", hn: "Rahu", hi: "राहु", bn: "রাহু", mr: "राहु", ta: "ராகு", te: "రాహు", gu: "રાહુ", kn: "ರಾಹು", ml: "റാഹു", pa: "ਰਾਹੂ", or: "ରାହୁ", as: "ৰাহু", zh: "拉胡", es: "Rahu", ar: "راحو", fr: "Rahu", pt: "Rāhu", de: "Rahu", ru: "Раху", ja: "ラーフ", id: "Rahu", ko: "라후", tr: "Rahu" },
  ketu    : { en: "Ketu", hn: "Ketu", hi: "केतु", bn: "কেতু", mr: "केतु", ta: "கேது", te: "కేతు", gu: "કેતુ", kn: "ಕೇತು", ml: "കേതു", pa: "ਕੇਤੂ", or: "କେତୁ", as: "কেতু", zh: "凯突", es: "Ketu", ar: "كيتو", fr: "Ketu", pt: "Ketu", de: "Ketu", ru: "Кету", ja: "ケートゥ", id: "Ketu", ko: "케투", tr: "Ketu" },
};

// ── Days of week ─────────────────────────────────────────────────────────────
export type DayKey = "sun" | "mon" | "tue" | "wed" | "thu" | "fri" | "sat";

export const DAY: Record<DayKey, LangMap> = {
  sun: { en: "Sunday", hn: "Ravivaar", hi: "रविवार", bn: "রবিবার", mr: "रविवार", ta: "ஞாயிறு", te: "ఆదివారం", gu: "રવિવાર", kn: "ಭಾನುವಾರ", ml: "ഞായറാഴ്ച", pa: "ਆਤਵਾਰ", or: "ରବିବାର", as: "দেওবাৰ", zh: "星期日", es: "domingo", ar: "الأحد", fr: "dimanche", pt: "domingo", de: "Sonntag", ru: "Воскресенье", ja: "日曜日", id: "Minggu", ko: "일요일", tr: "Pazar" },
  mon: { en: "Monday", hn: "Somvar", hi: "सोमवार", bn: "সোমবার", mr: "सोमवार", ta: "திங்கள்", te: "సోమవారం", gu: "સોમવાર", kn: "ಸೋಮವಾರ", ml: "തിങ്കള്‍", pa: "ਸੋਮਵਾਰ", or: "ସୋମବାର", as: "সোমবাৰ", zh: "星期一", es: "lunes", ar: "الاثنين", fr: "lundi", pt: "segunda-feira", de: "Montag", ru: "Понедельник", ja: "月曜日", id: "Senin", ko: "월요일", tr: "Pazartesi" },
  tue: { en: "Tuesday", hn: "Mangalvar", hi: "मंगलवार", bn: "মঙ্গলবার", mr: "मंगळवार", ta: "செவ்வாய்", te: "మంగళవారం", gu: "મંગળવાર", kn: "ಮಂಗಳವಾರ", ml: "ചൊവ്വ", pa: "ਮੰਗਲਵਾਰ", or: "ମଙ୍ଗଳବାର", as: "মঙ্গলবাৰ", zh: "星期二", es: "martes", ar: "الثلاثاء", fr: "mardi", pt: "terça-feira", de: "Dienstag", ru: "Вторник", ja: "火曜日", id: "Selasa", ko: "화요일", tr: "Salı" },
  wed: { en: "Wednesday", hn: "Budhavar", hi: "बुधवार", bn: "বুধবার", mr: "बुधवार", ta: "புதன்", te: "బుధవారం", gu: "બુધવાર", kn: "ಬುಧವಾರ", ml: "ബുധന്‍", pa: "ਬੁੱਧਵਾਰ", or: "ବୁଧବାର", as: "বুধবাৰ", zh: "星期三", es: "miércoles", ar: "الأربعاء", fr: "mercredi", pt: "quarta-feira", de: "Mittwoch", ru: "Среда", ja: "水曜日", id: "Rabu", ko: "수요일", tr: "Çarşamba" },
  thu: { en: "Thursday", hn: "Guruvaar", hi: "गुरुवार", bn: "বৃহস্পতিবার", mr: "गुरुवार", ta: "வியாழன்", te: "గురువారం", gu: "ગુરૂવાર", kn: "ಗುರುವಾರ", ml: "വ്യാഴം", pa: "ਵੀਰਵਾਰ", or: "ଗୁରୁବାର", as: "বৃহস্পতিবাৰ", zh: "星期四", es: "jueves", ar: "الخميس", fr: "jeudi", pt: "quinta-feira", de: "Donnerstag", ru: "Четверг", ja: "木曜日", id: "Kamis", ko: "목요일", tr: "Perşembe" },
  fri: { en: "Friday", hn: "Shukravar", hi: "शुक्रवार", bn: "শুক্রবার", mr: "शुक्रवार", ta: "வெள்ளி", te: "శుక్రవారం", gu: "શુક્રવાર", kn: "ಶುಕ್ರವಾರ", ml: "വെള്ളി", pa: "ਸ਼ੁੱਕਰਵਾਰ", or: "ଶୁକ୍ରବାର", as: "শুক্ৰবাৰ", zh: "星期五", es: "viernes", ar: "الجمعة", fr: "vendredi", pt: "sexta-feira", de: "Freitag", ru: "Пятница", ja: "金曜日", id: "Jumat", ko: "금요일", tr: "Cuma" },
  sat: { en: "Saturday", hn: "Shanivaar", hi: "शनिवार", bn: "শনিবার", mr: "शनिवार", ta: "சனி", te: "శనివారం", gu: "શનિવાર", kn: "ಶನಿವಾರ", ml: "ശനി", pa: "ਸ਼ਨੀਚਰਵਾਰ", or: "ଶନିବାର", as: "শনিবাৰ", zh: "星期六", es: "sábado", ar: "السبت", fr: "samedi", pt: "sábado", de: "Samstag", ru: "Суббота", ja: "土曜日", id: "Sabtu", ko: "토요일", tr: "Cumartesi" },
};

// ── Directions (8-way) ───────────────────────────────────────────────────────
export type DirKey = "N" | "S" | "E" | "W" | "NE" | "SE" | "SW" | "NW";

export const DIRECTION: Record<DirKey, LangMap> = {
  N : { en: "North", hn: "Uttar", hi: "उत्तर", bn: "উত্তর", mr: "उत्तर", ta: "வடக்கு", te: "ఉత్తరం", gu: "ઉત્તર", kn: "ಉತ್ತರ", ml: "ഉത്തരം", pa: "ਉੱਤਰ", or: "ଉତ୍ତର", as: "উত্তৰ", zh: "北", es: "Norte", ar: "شمال", fr: "Nord", pt: "Norte", de: "Norden", ru: "Север", ja: "北", id: "Utara", ko: "북", tr: "Kuzey" },
  S : { en: "South", hn: "Dakshin", hi: "दक्षिण", bn: "দক্ষিণ", mr: "दक्षिण", ta: "தெற்கு", te: "దక్షిణం", gu: "દક્ષિણ", kn: "ದಕ್ಷಿಣ", ml: "ദക്ഷിണം", pa: "ਦੱਖਣ", or: "ଦକ୍ଷିଣ", as: "দক্ষিণ", zh: "南", es: "Sur", ar: "جنوب", fr: "Sud", pt: "Sul", de: "Süden", ru: "Юг", ja: "南", id: "Selatan", ko: "남", tr: "Güney" },
  E : { en: "East", hn: "Purva", hi: "पूर्व", bn: "পূর্ব", mr: "पूर्व", ta: "கிழக்கு", te: "తూర్పు", gu: "પૂર્વ", kn: "ಪೂರ್ವ", ml: "കിഴക്ക്", pa: "ਪੂਰਬ", or: "ପূର୍ବ", as: "পূব", zh: "东", es: "Este", ar: "شرق", fr: "Est", pt: "Leste", de: "Osten", ru: "Восток", ja: "東", id: "Timur", ko: "동", tr: "Doğu" },
  W : { en: "West", hn: "Paschim", hi: "पश्चिम", bn: "পশ্চিম", mr: "पश्चिम", ta: "மேற்கு", te: "పడమర", gu: "પશ્ચિમ", kn: "ಪಶ್ಚಿಮ", ml: "പടിഞ്ഞാറ്", pa: "ਪੱਛਮ", or: "ପଶ୍ଚିମ", as: "পশ্চিম", zh: "西", es: "Oeste", ar: "غرب", fr: "Ouest", pt: "Oeste", de: "Westen", ru: "Запад", ja: "西", id: "Barat", ko: "서", tr: "Batı" },
  NE: { en: "Northeast", hn: "Ishaan", hi: "ईशान", bn: "উত্তর-পূর্ব", mr: "ईशान्य", ta: "வடகிழக்கு", te: "ఈశాన్యం", gu: "ઉત્તરપૂર્વ", kn: "ಉತ್ತರ ಪೂರ್ವ", ml: "വടക്കുകിഴക്ക്", pa: "ਉੱਤਰੀ ਪੂਰਬ", or: "ଉତ୍ତର ପୂର୍ବ", as: "উত্তৰ-পূব", zh: "东北", es: "Noreste", ar: "شمال شرق", fr: "Nord-est", pt: "Nordeste", de: "Nordost", ru: "Северо‑восток", ja: "北東", id: "Timur Laut", ko: "북동", tr: "Kuzeydoğu" },
  SE: { en: "Southeast", hn: "Agni", hi: "अग्नि", bn: "দক্ষিণ-পূর্ব", mr: "आग्नेय", ta: "தென்கிழக்கு", te: "ఆగ్నేయం", gu: "દક્ષિણપૂર્વ", kn: "ದಕ್ಷಿಣ ಪೂರ್ವ", ml: "തെക്കുകിഴക്ക്", pa: "ਦੱਖਣੀ ਪੂਰਬ", or: "ଦକ୍ଷିଣ ପୂର୍ବ", as: "দক্ষিণ-পূব", zh: "东南", es: "Sureste", ar: "جنوب شرق", fr: "Sud-est", pt: "Sudeste", de: "Südost", ru: "Юго‑восток", ja: "南東", id: "Tenggara", ko: "남동", tr: "Güneydoğu" },
  SW: { en: "Southwest", hn: "Niriti", hi: "नैऋत्य", bn: "দক্ষিণ-পশ্চিম", mr: "नैऋत्य", ta: "தென்மேற்கு", te: "నైరుతి", gu: "દક્ષિણપશ્ચિમ", kn: "ದಕ್ಷಿಣ ಪಶ್ಚಿಮ", ml: "തെക്കുപടിഞ്ഞാറ്", pa: "ਦੱਖਣੀ ਪੱਛਮ", or: "ଦକ୍ଷିଣ ପଶ୍ଚିମ", as: "দক্ষিণ-পশ্চিম", zh: "西南", es: "Suroeste", ar: "جنوب غرب", fr: "Sud-ouest", pt: "Sudoeste", de: "Südwest", ru: "Юго‑запад", ja: "南西", id: "Barat Daya", ko: "남서", tr: "Güneybatı" },
  NW: { en: "Northwest", hn: "Vayu", hi: "वायव्य", bn: "উত্তর-পশ্চিম", mr: "वायव्य", ta: "வடமேற்கு", te: "వాయవ్యం", gu: "ઉત્તરપશ્ચિમ", kn: "ಉತ್ತರ ಪಶ್ಚಿಮ", ml: "വടക്കുപടിഞ്ഞാറ്", pa: "ਉੱਤਰੀ ਪੱਛਮ", or: "ଉତ୍ତର ପଶ୍ଚିମ", as: "উত্তৰ-পশ্চিম", zh: "西北", es: "Noroeste", ar: "شمال غرب", fr: "Nord-ouest", pt: "Noroeste", de: "Nordwest", ru: "Северо‑запад", ja: "北西", id: "Barat Laut", ko: "북서", tr: "Kuzeybatı" },
};

// ── Colors ───────────────────────────────────────────────────────────────────
export const COLOR: Record<string, LangMap> = {
  red       : { en: "Red", hn: "Laal", hi: "लाल", bn: "লাল", mr: "लाल", ta: "சிகப்பு", te: "ఎరుపు", gu: "લાલ", kn: "ಕೆಂಪು", ml: "ചുവപ്പ്", pa: "ਲਾਲ", or: "ଲାଲ୍", as: "ৰঙা", zh: "红", es: "Rojo", ar: "أحمر", fr: "Rouge", pt: "Vermelho", de: "Rot", ru: "Красный", ja: "赤", id: "Merah", ko: "빨강", tr: "Kırmızı" },
  orange    : { en: "Orange", hn: "Narangi", hi: "नारंगी", bn: "কমলা", mr: "नारिंगी", ta: "ஆரஞ்சு", te: "నారింజ", gu: "નારંગી", kn: "ಕಿತ್ತಳೆ", ml: "ഓറഞ്ച്", pa: "ਸੰਤਰੀ", or: "କମଳା", as: "কমলা", zh: "橙", es: "Naranja", ar: "برتقالي", fr: "Orange", pt: "Laranja", de: "Orange", ru: "Оранжевый", ja: "オレンジ", id: "Oranye", ko: "주황", tr: "Turuncu" },
  white     : { en: "White", hn: "Safed", hi: "सफेद", bn: "সাদা", mr: "पांढरे", ta: "வெள்ளை", te: "తెలుపు", gu: "સફેદ", kn: "ಬಿಳಿ", ml: "വെളുപ്പ്", pa: "ਸਫੈਦ", or: "ଧଳା", as: "ধুৱা", zh: "白", es: "Blanco", ar: "أبيض", fr: "Blanc", pt: "Branco", de: "Weiß", ru: "Белый", ja: "白", id: "Putih", ko: "흰색", tr: "Beyaz" },
  pink      : { en: "Pink", hn: "Gulabi", hi: "गुलाबी", bn: "গোলাপি", mr: "गुलाबी", ta: "இலந்தை", te: "పింక్", gu: "ગુલાબી", kn: "ಗುಲಾಬಿ", ml: "പിങ്ക്", pa: "ਗੁਲਾਬੀ", or: "ଗୋଲାପୀ", as: "গোলাপী", zh: "粉", es: "Rosa", ar: "وردي", fr: "Rose", pt: "Rosa", de: "Rosa", ru: "Розовый", ja: "ピンク", id: "Merah Muda", ko: "분홍", tr: "Pembe" },
  yellow    : { en: "Yellow", hn: "Peela", hi: "पीला", bn: "হলুদ", mr: "पिवळा", ta: "மஞ்சள்", te: "పసుపు", gu: "પેલી", kn: "ಹಳದಿ", ml: "മഞ്ഞ", pa: "ਪੀਲਾ", or: "ହଳଦିଆ", as: "হালধীয়া", zh: "黄", es: "Amarillo", ar: "أصفر", fr: "Jaune", pt: "Amarelo", de: "Gelb", ru: "Желтый", ja: "黄色", id: "Kuning", ko: "노랑", tr: "Sarı" },
  green     : { en: "Green", hn: "Hari", hi: "हरा", bn: "সবুজ", mr: "हिरवा", ta: "பச்சை", te: "ఆకుపచ్చ", gu: "લીલો", kn: "ಹಸಿರು", ml: "ഹരിതം", pa: "ਹਰਾ", or: "ହରିତ", as: "সেউজী", zh: "绿", es: "Verde", ar: "أخضر", fr: "Vert", pt: "Verde", de: "Grün", ru: "Зеленый", ja: "緑", id: "Hijau", ko: "초록", tr: "Yeşil" },
  blue      : { en: "Blue", hn: "Neela", hi: "नीला", bn: "নীল", mr: "निळा", ta: "நீலம்", te: "ఆకాశ నీలం", gu: "વાદળી", kn: "ನೀಲಿ", ml: "നീല", pa: "ਨੀਲਾ", or: "ନୀଳ", as: "নীলা", zh: "蓝", es: "Azul", ar: "أزرق", fr: "Bleu", pt: "Azul", de: "Blau", ru: "Синий", ja: "青", id: "Biru", ko: "파랑", tr: "Mavi" },
  gold      : { en: "Gold", hn: "Sona", hi: "सोना", bn: "সোনা", mr: "सोन्याचा", ta: "பொன்", te: "సువర్ణం", gu: "સોનેરી", kn: "ಚಿನ್ನದ", ml: "സ്വര്‍ണം", pa: "ਸੋਨੇ ਦਾ", or: "ସୁନା", as: "সোণালী", zh: "金", es: "Dorado", ar: "ذهبي", fr: "Or", pt: "Dourado", de: "Gold", ru: "Золотой", ja: "金色", id: "Emas", ko: "금색", tr: "Altın" },
  silver    : { en: "Silver", hn: "Chandi", hi: "चांदी", bn: "রূপা", mr: "चाँदी", ta: "வெள்ளி", te: "వెండి", gu: "ચાંદી", kn: "ಬೆಳ್ಳಿ", ml: "വെളിവര്‍ണം", pa: "ਚਾਂਦੀ", or: "ଚାନ୍ଦୀ", as: "ৰূপালী", zh: "银", es: "Plateado", ar: "فضي", fr: "Argent", pt: "Prateado", de: "Silber", ru: "Серебряный", ja: "銀色", id: "Perak", ko: "은색", tr: "Gümüş" },
  black     : { en: "Black", hn: "Kaala", hi: "काला", bn: "কালো", mr: "काळा", ta: "கருப்பு", te: "నలుపు", gu: "કાળો", kn: "ಕಪ್ಪು", ml: "കറുപ്പ്", pa: "ਕਾਲਾ", or: "କଳା", as: "ক'লা", zh: "黑", es: "Negro", ar: "أسود", fr: "Noir", pt: "Preto", de: "Schwarz", ru: "Черный", ja: "黒", id: "Hitam", ko: "검정", tr: "Siyah" },
  maroon    : { en: "Maroon", hn: "Maroon", hi: "मैरून", bn: "গুরুচন্দ্রা", mr: "ओढा", ta: "ஆழக் சிவப்பு", te: "మరూన్", gu: "મેરુન", kn: "ಗಜ್ಜರಿ", ml: "മാരൂണ്‍", pa: "ਗੁਲਾਬੀ-ਬਾਖ਼ੀ", or: "ରଙ୍ଗଦାର", as: "মেরুঙা", zh: "栗", es: "Granate", ar: "أحمر غامق", fr: "Bordeaux", pt: "Bordô", de: "Dunkelrot", ru: "Бордовый", ja: "栗色", id: "Marun", ko: "갈색빛빨강", tr: "Bordo" },
  violet    : { en: "Violet", hn: "Baigani", hi: "बैंगनी", bn: "紫色", mr: "जांभळा", ta: "ஈர்படை நீலம்", te: "వైలెట్", gu: "બૈંગાણી", kn: "ನೀಲೋತ್ಪಲ", ml: "വയലറ്റ്", pa: "ਬੈਗਨੀ", or: "ବାଇଓଲେଟ୍", as: "জামনী", zh: "紫", es: "Violeta", ar: "بنفسجي", fr: "Violet", pt: "Violeta", de: "Violett", ru: "Фиолетовый", ja: "紫", id: "Ungu", ko: "보라", tr: "Eflatun" },
  lime      : { en: "Lime", hn: "Neebu", hi: "नींबू", bn: "লাইম", mr: "लिंबाचे हिरवे", ta: "லைம்", te: "లైమ్", gu: "લીમો", kn: "ಲೈಮ್", ml: "ലൈം", pa: "ਚੂਨਾ-ਹਰਾ", or: "ଲାଇମ୍", as: "লাইম", zh: "酸橙绿", es: "Lima", ar: "ليموني", fr: "Lime", pt: "Lima", de: "Limettengrün", ru: "Лаймовый", ja: "ライム", id: "Lime", ko: "라임", tr: "Fıstık Yeşili" },
  seagreen  : { en: "Sea Green", hn: "Sea Green", hi: "सी-ग्रीन", bn: "সমুদ্র-সবুজ", mr: "समुद्र हिरवा", ta: "கடல் பச்சை", te: "సీ గ్రీన్", gu: "સમુદ્ર લીલો", kn: "ಸೀ ಹಸಿರು", ml: "സീ ഗ്രീന്‍", pa: "ਸੀ ਗ੍ਰੀਨ", or: "ସୀ ଗ୍ରୀନ୍", as: "সমুদ্রীয় সেউজী", zh: "海绿", es: "Verde mar", ar: "أخضر بحري", fr: "Vert océan", pt: "Verde-mar", de: "Seegrün", ru: "Морская зелень", ja: "シーグリーン", id: "Hijau Laut", ko: "바다녹색", tr: "Deniz Yeşili" },
  skyblue   : { en: "Sky Blue", hn: "Aasmani", hi: "आसमानी", bn: "আকাশি", mr: "आकाशी निळा", ta: "வானிலநீலம்", te: "స్కై బ్లూ", gu: "આકાશી નિલું", kn: "ಆಕಾಶ ನೀಲಿ", ml: "ആകാശ നീലമ", pa: "ਆਸਮਾਨੀ ਨੀਲਾ", or: "ଆକାଶୀ", as: "আকাশী", zh: "天蓝", es: "Azul cielo", ar: "أزرق سماوي", fr: "Bleu ciel", pt: "Azul-céu", de: "Himmelblau", ru: "Голубой", ja: "スカイブルー", id: "Biru Langit", ko: "하늘색", tr: "Gökyüzü Mavisi" },
  brown     : { en: "Brown", hn: "Bhura", hi: "भूरा", bn: "বাদামি", mr: "तपकिरी", ta: "பழுப்பு", te: "ఎరుపు గట్టి", gu: "ભુરો", kn: "ಕಡೆಯಣ್ಣಬೆ", ml: "തവിട്ട്", pa: "ਭੂਰਾ", or: "ଖକୀ", as: "ক'ৰালি", zh: "褐", es: "Marrón", ar: "بني", fr: "Marron", pt: "Marrom", de: "Braun", ru: "Коричневый", ja: "茶色", id: "Cokelat", ko: "갈색", tr: "Kahverengi" },
};

// ── Metals ───────────────────────────────────────────────────────────────────
export const METAL: Record<string, LangMap> = {
  copper : { en: "Copper", hn: "Tamba", hi: "तांबा", bn: "তামা", mr: "तांबे", ta: "செம்பு", te: "తామ్రం", gu: "તાંબું", kn: "ಗಪ್ಪು", ml: "കോപ്പര്‍", pa: "ਤਾਮਬਾ", or: "ତାମ୍ବା", as: "তামা", zh: "铜", es: "Cobre", ar: "نحاس", fr: "Cuivre", pt: "Cobre", de: "Kupfer", ru: "Медь", ja: "銅", id: "Tembaga", ko: "구리", tr: "Bakır" },
  silver : { en: "Silver", hn: "Chandi", hi: "चांदी", bn: "রূপা", mr: "चांदी", ta: "வெள்ளி", te: "వెండి", gu: "ચાંદી", kn: "ಬೆಳ್ಳಿ", ml: "വെളുത്തുത്ത്", pa: "ਚਾਂਦੀ", or: "ଚାନ୍ଦୀ", as: "ৰূপা", zh: "银", es: "Plata", ar: "فضة", fr: "Argent", pt: "Prata", de: "Silber", ru: "Серебро", ja: "銀", id: "Perak", ko: "은", tr: "Gümüş" },
  gold   : { en: "Gold", hn: "Sona", hi: "सोना", bn: "স্বর্ণ", mr: "सोनं", ta: "தங்கம்", te: "బంగారం", gu: "સોનુ", kn: "ಚಿನ್ನ", ml: "സ്വര്‍ണ", pa: "ਸੋਨਾ", or: "ସୁନା", as: "সোণ", zh: "金", es: "Oro", ar: "ذهب", fr: "Or", pt: "Ouro", de: "Gold", ru: "Золото", ja: "金", id: "Emas", ko: "금", tr: "Altın" },
  iron   : { en: "Iron", hn: "Loha", hi: "लोहा", bn: "লোহা", mr: "लोखंड", ta: "இரும்பு", te: "ఇనుము", gu: "લોખંડ", kn: "ಇಸ್ಪಾತ್", ml: "ഇസ്പാത്ത്", pa: "ਲੋਹਾ", or: "ଲୋହା", as: "এইচ", zh: "铁", es: "Hierro", ar: "حديد", fr: "Fer", pt: "Ferro", de: "Eisen", ru: "Железо", ja: "鉄", id: "Besi", ko: "철", tr: "Demir" },
  bronze : { en: "Bronze", hn: "Kaansa", hi: "कांसा", bn: "কঁকাল", mr: "कांस्य", ta: "ப்ரான்சு", te: "కాపరా", gu: "કાંસુ", kn: "ಕಂಚು", ml: "ബ്രോൺസ്", pa: "ਕਾਂਸਾ", or: "କଞ୍ଚା", as: "কাঁচ", zh: "青铜", es: "Bronce", ar: "برونز", fr: "Bronze", pt: "Bronze", de: "Bronze", ru: "Бронза", ja: "青銅", id: "Perunggu", ko: "청동", tr: "Bronz" },
};

// ── 5 Elements (Pancha-mahabhuta) ─────────────────────────────────────────────
export const ELEMENT: Record<string, LangMap> = {
  fire  : { en: "Fire", hn: "Agni", hi: "अग्नि", bn: "অগ্নি", mr: "अग्नि", ta: "அகம்", te: "అగ్ని", gu: "આતશ", kn: "ಅಗ್ನಿ", ml: "നിര്‍ബാണം", pa: "ਅੱਗ", or: "ଅଗ୍ନି", as: "জুই", zh: "火", es: "Fuego", ar: "نار", fr: "Feu", pt: "Fogo", de: "Feuer", ru: "Огонь", ja: "火", id: "Api", ko: "불", tr: "Ateş" },
  earth : { en: "Earth", hn: "Prithvi", hi: "पृथ्वी", bn: "পৃথিবী", mr: "पृथ्वी", ta: "பூமி", te: "భూమి", gu: "પૃથ્વી", kn: "ಭೂಮಿ", ml: "ഭൂമി", pa: "ਧਰਤੀ", or: "ପୃଥିଭୀ", as: "পৃথিৱী", zh: "土", es: "Tierra", ar: "أرض", fr: "Terre", pt: "Terra", de: "Erde", ru: "Земля", ja: "地", id: "Bumi", ko: "흙", tr: "Toprak" },
  air   : { en: "Air", hn: "Vayu", hi: "वायु", bn: "বায়ু", mr: "वायू", ta: "காற்று", te: "వాయువు", gu: "પવન", kn: "ವಾಯು", ml: "വായു", pa: "ਹਵਾ", or: "ବାତାସ", as: "বায়ু", zh: "气", es: "Aire", ar: "هواء", fr: "Air", pt: "Ar", de: "Luft", ru: "Воздух", ja: "風", id: "Udara", ko: "공기", tr: "Hava" },
  water : { en: "Water", hn: "Jal", hi: "जल", bn: "জল", mr: "पाणी", ta: "நீர்", te: "జలము", gu: "પાણી", kn: "ಜಲ", ml: "ജലം", pa: "ਪਾਣੀ", or: "ଜଳ", as: "জল", zh: "水", es: "Agua", ar: "ماء", fr: "Eau", pt: "Água", de: "Wasser", ru: "Вода", ja: "水", id: "Air", ko: "물", tr: "Su" },
  ether : { en: "Ether", hn: "Akash", hi: "आकाश", bn: "আকাশ", mr: "आकाश", ta: "ஆகாசம்", te: "ఆకాశం", gu: "આકાશ", kn: "ಆಕಾಶ", ml: "ആകാശം", pa: "ਆਕਾਸ਼", or: "ଆକାଶ", as: "আকাশ", zh: "以太", es: "Éter", ar: "أثير", fr: "Éther", pt: "Éter", de: "Äther", ru: "Эфир", ja: "エーテル", id: "Eter", ko: "에테르", tr: "Eter" },
};

// ── Gemstones ────────────────────────────────────────────────────────────────
export const GEMSTONE: Record<string, LangMap> = {
  ruby           : { en: "Ruby", hn: "Manikya", hi: "माणिक्य", bn: "রুবি", mr: "रूबीन", ta: "முத்திரை", te: "రూబీ", gu: "રબર", kn: "ಮುಗ್ದಿ", ml: "രൂപി", pa: "ਮੁਣੀ", or: "ମଣିକ", as: "ৰুবী", zh: "红宝石", es: "Rubí", ar: "ياقوت", fr: "Rubis", pt: "Rubi", de: "Rubin", ru: "Рубин", ja: "ルビー", id: "Ruby", ko: "루비", tr: "Yakut" },
  pearl          : { en: "Pearl", hn: "Moti", hi: "मोती", bn: "মুক্তা", mr: "मोती", ta: "முத்து", te: "ముత్యము", gu: "મતિરા", kn: "ಮುತ್ತು", ml: "മുത്ത്", pa: "ਮੋਤੀ", or: "ମୋତୀ", as: "মুক্তা", zh: "珍珠", es: "Perla", ar: "لؤلؤ", fr: "Perle", pt: "Pérola", de: "Perle", ru: "Жемчуг", ja: "真珠", id: "Mutiara", ko: "진주", tr: "İnci" },
  coral          : { en: "Red Coral", hn: "Moonga", hi: "मूंगा", bn: "রেড কোরাল", mr: "लाल प्रवाळ", ta: "சிவப்பு கொரல்", te: "రెడ్ కొరల్", gu: "લાલ મણિ", kn: "ಕೆಂಪು ಮಾಂಗು", ml: "ലാൽ കൊറൽ", pa: "ਲਾਲ ਕੋਰਲ", or: "ଲାଲ୍ ମଙ୍ଗଣ", as: "ৰক্তমুক্তা", zh: "红珊瑚", es: "Coral rojo", ar: "مرجان أحمر", fr: "Corail", pt: "Coral vermelho", de: "Roter Korall", ru: "Коралл", ja: "レッドコーラル", id: "Koral Merah", ko: "적색 산호", tr: "Kırmızı Mercan" },
  emerald        : { en: "Emerald", hn: "Panna", hi: "पन्ना", bn: "পান্না", mr: "पन्ना", ta: "பச்சை ஹீரகம்", te: "పచ్చి రత్నం", gu: "પન્ના", kn: "ಪದ್ಮನಾಭ", ml: "പച്ചുനാഗരികം", pa: "ਪਲਾਸ", or: "ପନ୍ନା", as: "পাহাৰিক", zh: "祖母绿", es: "Esmeralda", ar: "زمرد", fr: "Émeraude", pt: "Esmeralda", de: "Smaragd", ru: "Изумруд", ja: "エメラルド", id: "Berlian Zamrud", ko: "에메랄드", tr: "Zümrüt" },
  yellowsapphire : { en: "Yellow Sapphire", hn: "Pukhraj", hi: "पुखराज", bn: "হলুদ নীলমণি", mr: "पिवळा नीलम", ta: "மஞ்சள் நீலகுமார்", te: "పసుపు నీలం రత్నం", gu: "પીળો નીલમ", kn: "ಹಳದಿ ನೀಲಮಣಿ", ml: "മഞ്ഞ നീലക്കൽ", pa: "ਪੀਲਾ ਨੀਲਮ", or: "ହଳଦିଆ ପୁખରା", as: "হলদীয়া নীলা পাথৰ", zh: "黄蓝宝", es: "Zafiro amarillo", ar: "ياقوت أصفر", fr: "Saphir jaune", pt: "Safira amarela", de: "Gelber Saphir", ru: "Желтый сапфир", ja: "イエローサファイア", id: "Safir Kuning", ko: "노란 사파이어", tr: "Sarı Safir" },
  diamond        : { en: "Diamond", hn: "Heera", hi: "हीरा", bn: "হীরক", mr: "हिरा", ta: "வர்‍ണி", te: "వజ్రం", gu: "હીરો", kn: "ವಜ್ರ", ml: "വജ്രം", pa: "ਹੀਰਾ", or: "ହୀରା", as: "হীৰা", zh: "钻石", es: "Diamante", ar: "ألماس", fr: "Diamant", pt: "Diamante", de: "Diamant", ru: "Алмаз", ja: "ダイヤモンド", id: "Berlian", ko: "다이아몬드", tr: "Elmas" },
  bluesapphire   : { en: "Blue Sapphire", hn: "Neelam", hi: "नीलम", bn: "নীল নীলমণি", mr: "नीलम", ta: "நீல நீலகரம்", te: "నీలం నెఫ్రైట్", gu: "વીરૂ નિલમ", kn: "ನೀಲಮಣಿ", ml: "നീലക്കൽ", pa: "ਨੀਲਮ", or: "ନୀଳ ନୀଲମ", as: "নীল নীলা পাথৰ", zh: "蓝宝石", es: "Zafiro azul", ar: "ياقوت أزرق", fr: "Saphir bleu", pt: "Safira azul", de: "Blauer Saphir", ru: "Синий сапфир", ja: "ブルーサファイア", id: "Safir Biru", ko: "청옥 사파이어", tr: "Mavi Safir" },
  hessonite      : { en: "Hessonite", hn: "Gomed", hi: "गोमेद", bn: "গার্নেট", mr: "गोमेद", ta: "ஹெசனிட்", te: "హెసోనైట్", gu: "ગહનિ", kn: "ಗೋಮೇಧ", ml: "ഹെസ്സൊണൈറ്റ്", pa: "ਗੋਮੂਖ", or: "ଗୋନ୍ଦକ", as: "হেসোনাইট", zh: "海桑子", es: "Hessonita", ar: "حِسونيت", fr: "Hessonite", pt: "Hessonita", de: "Hessonit", ru: "Гессонит", ja: "ヘソナイト", id: "Hessonite", ko: "헤손라이트", tr: "Hessonit" },
  catseye        : { en: "Cat's Eye", hn: "Lahsuniya", hi: "लहसुनिया", bn: "বিড়ালের-চোখ", mr: "बिल्ल्याचं डोळं", ta: "பூனைக் கண்", te: "క్యాట్స్ ఐ", gu: "બિલાડી આંખ", kn: "ವಳ್ಳೀಕುಣುಜ", ml: "കാറ്റ് ഐ", pa: "ਬਿੱਲੀ ਦੀ ਅੱਖ", or: "ବିଲାଇ ଆଖି", as: "বিড়াল-চকু", zh: "猫眼石", es: "Ojo de gato", ar: "عين القط", fr: "Œil de chat", pt: "Olho de gato", de: "Katzenauge", ru: "Кошачий глаз", ja: "キャッツアイ", id: "Mata Kucing", ko: "캣츠아이", tr: "Kedi Gözü" },
};

// ── Deities (transliterated across langs — sacred names kept phonetic) ──────
export const DEITY: Record<string, LangMap> = {
  hanuman   : { en: "Hanuman", hn: "Hanuman", hi: "हनुमान", bn: "হনুমান", mr: "हनुमान", ta: "ஹனுமான்", te: "హనుమాన్", gu: "હનુમાન", kn: "ಹನುಮಾನ", ml: "ഹനുമാൻ", pa: "ਹਨੁਮਾਨ", or: "ହନୁମାନ", as: "হনুমান", zh: "哈奴曼", es: "Hanuman", ar: "هانومان", fr: "Hanuman", pt: "Hanumãn", de: "Hanuman", ru: "Хануман", ja: "ハヌマーン", id: "Hanuman", ko: "하누만", tr: "Hanuman" },
  lakshmi   : { en: "Lakshmi", hn: "Lakshmi", hi: "लक्ष्मी", bn: "লক্ষ্মী", mr: "लक्ष्मी", ta: "லட்சுமி", te: "లక్ష్మి", gu: "લક્ષ્મી", kn: "ಲಕ್ಷ್ಮಿ", ml: "ലക്ഷ്മി", pa: "ਲਕ੍ਸ਼ਮੀ", or: "ଲକ୍ଷ୍ମୀ", as: "লক্ষ্মী", zh: "拉克希米", es: "Lakshmi", ar: "لاكشمي", fr: "Lakshmi", pt: "Lakshmi", de: "Lakshmi", ru: "Лакшми", ja: "ラクシュミー", id: "Lakshmi", ko: "락슈미", tr: "Lakshmi" },
  ganesh    : { en: "Ganesha", hn: "Ganesh", hi: "गणेश", bn: "গণেশ", mr: "गणेश", ta: "கணேஷ்", te: "గణేష్", gu: "ગણેશ", kn: "ಗಣೇಶ", ml: "ഗണേശ", pa: "ਗਣੇਸ਼", or: "ଗଣେଶ", as: "গনেশ", zh: "伽内什", es: "Ganesha", ar: "غانеша", fr: "Ganesha", pt: "Ganesha", de: "Ganesha", ru: "Ганеша", ja: "ガネーシャ", id: "Ganesha", ko: "가네샤", tr: "Ganesha" },
  shiva     : { en: "Shiva", hn: "Shiva", hi: "शिव", bn: "শিব", mr: "शिव", ta: "சிவன்", te: "శివ", gu: "શિવ", kn: "ಶಿವ", ml: "ശിവ", pa: "ਸ਼ਿਵ", or: "ଶିବ", as: "শিৱ", zh: "湿婆", es: "Shiva", ar: "شيفا", fr: "Shiva", pt: "Xiva", de: "Shiva", ru: "Шива", ja: "シヴァ", id: "Shiva", ko: "시바", tr: "Shiva" },
  surya     : { en: "Surya", hn: "Surya", hi: "सूर्य देव", bn: "সূর্য", mr: "सूर्य", ta: "சூர்ய", te: "సూర్య", gu: "સૂર્ય", kn: "ಸೂರ್ಯ", ml: "സൂര്യ", pa: "ਸੂਰਿਆ", or: "ସୂର୍ଯ୍ୟ", as: "সূৰ্য", zh: "苏利耶", es: "Surya", ar: "سوريا", fr: "Surya", pt: "Surya", de: "Surya", ru: "Сурья", ja: "スーリヤ", id: "Surya", ko: "수리야", tr: "Surya" },
  saraswati : { en: "Saraswati", hn: "Saraswati", hi: "सरस्वती", bn: "সরস্বতী", mr: "सरस्वती", ta: "சரஸ்வதி", te: "సరస్వతి", gu: "સારસ્વતી", kn: "ಸರಸ್ವತಿ", ml: "സരസ്വതി", pa: "ਸਰਸਵਤੀ", or: "ସରସ୍ୱତୀ", as: "সৰস্বতী", zh: "萨拉斯瓦蒂", es: "Saraswati", ar: "ساراسواتي", fr: "Saraswati", pt: "Sarasvati", de: "Saraswati", ru: "Сарасвати", ja: "サラスヴァティー", id: "Saraswati", ko: "사라스와티", tr: "Saraswati" },
  kali      : { en: "Kali", hn: "Kali", hi: "काली", bn: "কালী", mr: "काली", ta: "காளி", te: "కాలి", gu: "કાળી", kn: "ಕಾಳಿ", ml: "കാളി", pa: "ਕਾਲੀ", or: "କାଳୀ", as: "কালী", zh: "卡莉", es: "Kali", ar: "كالي", fr: "Kali", pt: "Kali", de: "Kali", ru: "Кали", ja: "カーリー", id: "Kali", ko: "칼리", tr: "Kali" },
  vishnu    : { en: "Vishnu", hn: "Vishnu", hi: "विष्णु", bn: "বিষ্ণু", mr: "विष्णू", ta: "விஷ்ணு", te: "విష్ణు", gu: "વિષ્ણુ", kn: "ವಿಷ್ಣು", ml: "വിഷ്ണു", pa: "ਵਿਸ਼ਨੂ", or: "ବିଷ୍ଣୁ", as: "বিষ্ণু", zh: "毗湿奴", es: "Vishnu", ar: "فشنو", fr: "Vishnu", pt: "Vishnu", de: "Vishnu", ru: "Вишну", ja: "ヴィシュヌ", id: "Vishnu", ko: "비슈누", tr: "Vishnu" },
  shani     : { en: "Shani Dev", hn: "Shani Dev", hi: "शनि देव", bn: "শনি দেব", mr: "शनी देव", ta: "சனிதேவர்", te: "శని దేవ్", gu: "શનિ દેવ", kn: "ಶನಿ ದೇವ", ml: "ശനി ദേവ്", pa: "ਸ਼ਨੀ ਦੇਵ", or: "ଶନି ଦେବ", as: "শনি দেব", zh: "沙尼德夫", es: "Shani Dev", ar: "شاني ديف", fr: "Shani Dev", pt: "Shani Dev", de: "Shani Dev", ru: "Шани Дев", ja: "シャニ・デーヴ", id: "Shani", ko: "샤니 데브", tr: "Shani Dev" },
  durga     : { en: "Durga", hn: "Durga", hi: "दुर्गा", bn: "দুর্গা", mr: "दुर्गा", ta: "துர்கா", te: "దుర్గా", gu: "દુર્ગા", kn: "ದುರ್ಗಾ", ml: "ദുർഗാ", pa: "ਦੁਰਗਾ", or: "ଦୁର୍ଗା", as: "দুৰ্গা", zh: "杜尔迦", es: "Durga", ar: "دورغا", fr: "Durga", pt: "Durga", de: "Durga", ru: "Дурга", ja: "ドゥルガー", id: "Durga", ko: "두르가", tr: "Durga" },
  parvati   : { en: "Parvati", hn: "Parvati", hi: "पार्वती", bn: "পার্বতী", mr: "पार्वती", ta: "பார்வதி", te: "పార్వతి", gu: "પર્વતી", kn: "ಪಾರ್ವತಿ", ml: "പര്വതി", pa: "ਪਾਰਵਤੀ", or: "ପାର୍ବତୀ", as: "পাৰ্বতী", zh: "帕尔瓦蒂", es: "Parvati", ar: "بارفاتي", fr: "Parvati", pt: "Parvati", de: "Parvati", ru: "Парвати", ja: "パールヴァティー", id: "Parvati", ko: "파르바티", tr: "Parvati" },
};

// ── Convenience helpers ──────────────────────────────────────────────────────
export function rashiName(key: RashiKey, lang: UILang): string {
  return pick(lang, RASHI[key]);
}
export function planetName(key: PlanetKey, lang: UILang): string {
  return pick(lang, PLANET[key]);
}
export function dayName(key: DayKey, lang: UILang): string {
  return pick(lang, DAY[key]);
}

// Map weekday number (0=Sun..6=Sat) → DayKey
export const WEEKDAY_KEYS: DayKey[] = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"];

// ── Nakshatra (27 lunar mansions, transliterated across langs) ──────────────
export const NAKSHATRA: LangMap[] = [
  { en: "Ashwini", hn: "Ashwini", hi: "अश्विनी", bn: "অশ্বিনী", mr: "अश्विनी", ta: "அஸ்வினி", te: "అశ్విని", gu: "અશ્વિની", kn: "ಅಶ್ವಿನಿ", ml: "അശ്വിനി", pa: "ਅਸ਼ਵਿਨੀ", or: "ଅଶ୍ୱିନୀ", as: "আশ্বিনী", zh: "阿什维尼", es: "Ashwini", ar: "أشْوِيني", fr: "Ashwini", pt: "Ashvini", de: "Ashwini", ru: "Ашвини", ja: "アシュヴィニー", id: "Ashwini", ko: "아슈비니", tr: "Ashwini" },
  { en: "Bharani", hn: "Bharani", hi: "भरणी", bn: "ভরণী", mr: "भराणी", ta: "பரணி", te: "భరణి", gu: "ભરણિ", kn: "ಭರಣಿ", ml: "ഭരണി", pa: "ਭਰਣੀ", or: "ଭରାଣୀ", as: "بھৰাণী", zh: "巴拉尼", es: "Bharani", ar: "بهاراني", fr: "Bharani", pt: "Bharani", de: "Bharani", ru: "Бхарани", ja: "バラーニー", id: "Bharani", ko: "바라니", tr: "Bharani" },
  { en: "Krittika", hn: "Krittika", hi: "कृत्तिका", bn: "কৃর্তিকা", mr: "कृत्तिका", ta: "க்ருத்திகா", te: "కృత్తిక", gu: "ક્રિતિકા", kn: "ಕ್ರಿತಿಕಾ", ml: "കർത്തിക", pa: "ਕ੍ਰਿਤਿਕਾ", or: "କୃତ୍ତିକା", as: "কৃত্তিকা", zh: "克里蒂卡", es: "Krittika", ar: "كريتتيكا", fr: "Krittika", pt: "Krittika", de: "Krittika", ru: "Криттика", ja: "クリッティカー", id: "Krittika", ko: "크리티카", tr: "Krittika" },
  { en: "Rohini", hn: "Rohini", hi: "रोहिणी", bn: "রোহিণী", mr: "रोहिणी", ta: "ரோஹிணி", te: "రోహిణి", gu: "રોહિણી", kn: "ರೋಹಿಣಿ", ml: "രോഹിണി", pa: "ਰੋਹिणੀ", or: "ରୋହିଣୀ", as: "রোহিণী", zh: "罗希尼", es: "Rohini", ar: "روهيني", fr: "Rohini", pt: "Rohini", de: "Rohini", ru: "Рохини", ja: "ローヒニー", id: "Rohini", ko: "로히니", tr: "Rohini" },
  { en: "Mrigashira", hn: "Mrigashira", hi: "मृगशिरा", bn: "মৃগশিরা", mr: "मृगशिरा", ta: "ம்ரிகஷீர்ஷ", te: "మృగశిర", gu: "મૃગશિરા", kn: "ಮೃಗಶಿರ", ml: "മൃഗശിര", pa: "ਮ੍ਰਿਗਸ਼ਿਰਾ", or: "ମୃଗଶିରା", as: "মৃগশীৰা", zh: "姆里加希拉", es: "Mrigashira", ar: "مريغاشيرا", fr: "Mrigashira", pt: "Mrigashira", de: "Mrigashira", ru: "Мригаширша", ja: "ムリガシラ", id: "Mrigashira", ko: "므리가시라", tr: "Mrigashira" },
  { en: "Ardra", hn: "Ardra", hi: "आर्द्रा", bn: "আদ্রা", mr: "आर्द्रा", ta: "அர்த்த்ரா", te: "ఆర్థ్ర", gu: "આર્દ્રા", kn: "ಅರ್ಡ್ರಾ", ml: "അർദ്ര", pa: "ਅਰਦਰਾ", or: "ଆର୍ଦ୍ରା", as: "আদ্রা", zh: "阿尔德拉", es: "Ardra", ar: "أردرا", fr: "Ardra", pt: "Ardra", de: "Ardra", ru: "Ардра", ja: "アルドラー", id: "Ardra", ko: "아르드라", tr: "Ardra" },
  { en: "Punarvasu", hn: "Punarvasu", hi: "पुनर्वसु", bn: "পুনর্বসু", mr: "पुनर्वसु", ta: "புனர்பர்வசு", te: "పునర్వసు", gu: "પુનર્વસુ", kn: "ಪುನರ್ವಸು", ml: "പുനർവसु", pa: "ਪੁਨਰਵਸੂ", or: "ପୁନର୍ବସୁ", as: "পুণাৰ্বসু", zh: "普那瓦苏", es: "Punarvasu", ar: "بونارواسو", fr: "Punarvasu", pt: "Punarvasu", de: "Punarvasu", ru: "Пунарвасу", ja: "プナルヴァス", id: "Punarvasu", ko: "푸나르바수", tr: "Punarvasu" },
  { en: "Pushya", hn: "Pushya", hi: "पुष्य", bn: "পুষ্যা", mr: "पुष्य", ta: "புஷ்யா", te: "పుష్య", gu: "ಪುಷ્ય", kn: "ಪುಷ್ಯ", ml: "പുഷ്യ", pa: "ਪੁਸ਼੍ਯਾ", or: "ପୁଷ୍ୟ", as: "পুষ্য", zh: "普修亚", es: "Pushya", ar: "بوشيا", fr: "Pushya", pt: "Pushya", de: "Pushya", ru: "Пушья", ja: "プシュヤ", id: "Pushya", ko: "푸샤", tr: "Pushya" },
  { en: "Ashlesha", hn: "Ashlesha", hi: "आश्लेषा", bn: "অশ্লেষা", mr: "अश्लेषा", ta: "அஷ்ளேஷா", te: "అశ్లేష", gu: "અશ્વેષા", kn: "ಅಶ್ಲೇಷಾ", ml: "അശ്ലേഷ", pa: "ਅਸ਼ਲੇਸ਼ਾ", or: "ଆଶ୍ଳେଷା", as: "আশ্লেষা", zh: "阿什莱沙", es: "Ashlesha", ar: "أشليشا", fr: "Ashlesha", pt: "Ashlesha", de: "Ashlesha", ru: "Ашлеша", ja: "アシュレーシャ", id: "Ashlesha", ko: "아슬레샤", tr: "Ashlesha" },
  { en: "Magha", hn: "Magha", hi: "मघा", bn: "মাঘা", mr: "मघा", ta: "மகா", te: "మఘ", gu: "મઘા", kn: "ಮಘ", ml: "മഘ", pa: "ਮਘਾ", or: "ମଘା", as: "মাঘা", zh: "玛嘎", es: "Magha", ar: "ماجها", fr: "Magha", pt: "Magha", de: "Magha", ru: "Мага", ja: "マガー", id: "Magha", ko: "마가", tr: "Magha" },
  { en: "Purva Phalguni", hn: "Purva Phalguni", hi: "पूर्व फाल्गुनी", bn: "পুর্ব ফল্গুনী", mr: "पूर्व फाल्गुनी", ta: "பூர்வபல்குனி", te: "పూర్వ ఫల్గుణి", gu: "પૂર્વ ફાલ્ગુની", kn: "ಪುರ್ವಫಲ್ಗುನಿ", ml: "പൂര്‍വ ഫല്ഗുണി", pa: "ਪੂਰਵਾ ਫਾਲਗੁਨੀ", or: "ପୂର୍ବଫଳ୍ଗୁନୀ", as: "পূৰ্ব ফল্গুনী", zh: "普尔瓦费尔古尼", es: "Purva Phalguni", ar: "بورفا فالغوني", fr: "Purva Phalguni", pt: "Purva Phalguni", de: "Purva Phalguni", ru: "Пурва Фалгуни", ja: "プールヴァパールグニー", id: "Purva Phalguni", ko: "푸르바팔구니", tr: "Purva Phalguni" },
  { en: "Uttara Phalguni", hn: "Uttara Phalguni", hi: "उत्तर फाल्गुनी", bn: "উত্তর ফল্গুনী", mr: "उत्तर फाल्गुनी", ta: "உத்தரபல்குனி", te: "ఉత్తర ఫల్గుణి", gu: "ઉત્તર ફાલ્ગુની", kn: "ಉತ್ತರಫಲ್ಗುನಿ", ml: "ഉത്തര ഫല്ഗുണി", pa: "ਉੱਤਰਾ ਫਾਲਗੁਨੀ", or: "ଉତ୍ତରଫଳ୍ଗୁନୀ", as: "উত্তৰ ফল্গুনী", zh: "乌塔拉费尔古尼", es: "Uttara Phalguni", ar: "أوتارا فالغوني", fr: "Uttara Phalguni", pt: "Uttara Phalguni", de: "Uttara Phalguni", ru: "Уттара Фалгуни", ja: "ウッタラパールグニー", id: "Uttara Phalguni", ko: "우타라팔구니", tr: "Uttara Phalguni" },
  { en: "Hasta", hn: "Hasta", hi: "हस्त", bn: "হস্ত", mr: "हस्ता", ta: "ஹஸ்த", te: "హస్త", gu: "હસ્ત", kn: "ಹಸ್ತ", ml: "ഹസ്ത", pa: "ਹਸਤਾ", or: "ହସ୍ତ", as: "হস্ত", zh: "哈斯塔", es: "Hasta", ar: "هاستا", fr: "Hasta", pt: "Hasta", de: "Hasta", ru: "Хаста", ja: "ハスタ", id: "Hasta", ko: "하스타", tr: "Hasta" },
  { en: "Chitra", hn: "Chitra", hi: "चित्रा", bn: "চিত্ত্রা", mr: "चित्रा", ta: "சித்ரா", te: "చిత్ర", gu: "ચિત્રા", kn: "ಚಿತ್ರ", ml: "ചിത്ര", pa: "ਚਿੱਤਰਾ", or: "ଚିତ୍ରା", as: "চিত্ৰা", zh: "奇特拉", es: "Chitra", ar: "شيترا", fr: "Chitra", pt: "Chitra", de: "Chitra", ru: "Читра", ja: "チトラー", id: "Chitra", ko: "치트라", tr: "Chitra" },
  { en: "Swati", hn: "Swati", hi: "स्वाति", bn: "স্বাতী", mr: "स्वाती", ta: "ஸ்வாதி", te: "స్వాతి", gu: "સ્વાતી", kn: "ಸ್ವಾತಿ", ml: "സ്വതി", pa: "ਸੁਆਤੀ", or: "ସ୍ୱାତୀ", as: "স্বাতী", zh: "斯瓦蒂", es: "Swati", ar: "سواتي", fr: "Swati", pt: "Swati", de: "Swati", ru: "Свати", ja: "スワーティー", id: "Swati", ko: "스와티", tr: "Swati" },
  { en: "Vishakha", hn: "Vishakha", hi: "विशाखा", bn: "বিশাখা", mr: "विशाखा", ta: "விசாகா", te: "విశాఖ", gu: "વિશ્વાખા", kn: "ವಿಶಾಖಾ", ml: "വിശാഖ", pa: "ਵਿਸ਼ਾਖਾ", or: "ବିଶାଖା", as: "বিশাখা", zh: "维沙卡", es: "Vishakha", ar: "فيشاكا", fr: "Vishakha", pt: "Vishakha", de: "Vishakha", ru: "Вишакха", ja: "ヴィシャーカー", id: "Vishakha", ko: "비샤카", tr: "Vishakha" },
  { en: "Anuradha", hn: "Anuradha", hi: "अनुराधा", bn: "অনুরাধা", mr: "अनुराधा", ta: "அனுராதா", te: "అనురాధ", gu: "અનુરાધા", kn: "ಅನುರಾಧಾ", ml: "അനുരാധ", pa: "ਅਨੁਰਾਧਾ", or: "ଅନୁରାଧା", as: "অনুৰাধা", zh: "阿努拉达", es: "Anuradha", ar: "أنوراده", fr: "Anuradha", pt: "Anuradha", de: "Anuradha", ru: "Анурада", ja: "アヌラーダ", id: "Anuradha", ko: "아누라다", tr: "Anuradha" },
  { en: "Jyeshtha", hn: "Jyeshtha", hi: "ज्येष्ठा", bn: "জ্যেষ্ঠা", mr: "ज्येष्ठा", ta: "ஜ்யேஷ்டா", te: "జ్యేష్ఠ", gu: "જયેષ્ઠા", kn: "ಜ್ಯೇಷ್ಠ", ml: "ജ്യेष्ठ", pa: "ਜੇਠਾ", or: "ଯେଷ୍ଠା", as: "জ্যেষ্ঠা", zh: "杰叶什特哈", es: "Jyeshtha", ar: "جيشثا", fr: "Jyeshtha", pt: "Jyeshtha", de: "Jyeshtha", ru: "Джйештха", ja: "ジェーシュター", id: "Jyeshtha", ko: "제샤", tr: "Jyeshtha" },
  { en: "Mula", hn: "Mula", hi: "मूल", bn: "মূলা", mr: "मूल", ta: "மூலா", te: "మూల", gu: "મુલા", kn: "ಮೂಲ", ml: "മൂല", pa: "ਮੂਲਾ", or: "ମୁଳା", as: "মূলা", zh: "穆拉", es: "Mula", ar: "مولا", fr: "Mula", pt: "Mula", de: "Mula", ru: "Мула", ja: "ムーラ", id: "Mula", ko: "물라", tr: "Mula" },
  { en: "Purva Ashadha", hn: "Purva Ashadha", hi: "पूर्वाषाढ़ा", bn: "পুর্বাষાઢা", mr: "पूर्वाषाढा", ta: "பூர்வாஷாடா", te: "పూర్వాషాఢ", gu: "પૂર્વ આશાઢા", kn: "ಪುರ್ವಾಷ್ಟಮ", ml: "പൂര്‍വാശാഢ", pa: "ਪੂਰਵਾ ਆਸ਼ਾਢਾ", or: "ପୂର୍ବାଷାଢା", as: "পূৰ্বাষাঢা", zh: "普尔瓦阿莎达", es: "Purva Ashadha", ar: "بورفا أشادا", fr: "Purva Ashadha", pt: "Purva Ashadha", de: "Purva Ashadha", ru: "Пурва Ашадха", ja: "プールヴァアシャーダ", id: "Purva Ashadha", ko: "푸르바아샤다", tr: "Purva Ashadha" },
  { en: "Uttara Ashadha", hn: "Uttara Ashadha", hi: "उत्तराषाढ़ा", bn: "উত্তরাষঢ়া", mr: "उत्तराषाढा", ta: "உத்தராஷாடா", te: "ఉత్తరాషాఢ", gu: "ઉત્તર આશાઢા", kn: "ಉತ್ತರಾಷ್ಟಮ", ml: "ഉത്തരാശാഢ", pa: "ਉੱਤਰਾ ਆਸ਼ਾਢਾ", or: "ଉତ୍ତରାଷାଢା", as: "উত্তৰাষাঢা", zh: "乌塔拉阿莎达", es: "Uttara Ashadha", ar: "أوتارا أشادا", fr: "Uttara Ashadha", pt: "Uttara Ashadha", de: "Uttara Ashadha", ru: "Уттара Ашадха", ja: "ウッタラアシャーダ", id: "Uttara Ashadha", ko: "우타라아샤다", tr: "Uttara Ashadha" },
  { en: "Shravana", hn: "Shravana", hi: "श्रवण", bn: "শ্রাবণ", mr: "श्रवण", ta: "ஶிரோவணம்", te: "శ్రవణ", gu: "શ્રાવણા", kn: "ಶ್ರವಣ", ml: "ശ്രവണ", pa: "ਸ਼੍ਰਵਣ", or: "ଶ୍ରବଣ", as: "শ্রবণ্য", zh: "施拉瓦纳", es: "Shravana", ar: "شرافانا", fr: "Shravana", pt: "Shravana", de: "Shravana", ru: "Шравана", ja: "シュラヴァナ", id: "Shravana", ko: "슈라바나", tr: "Shravana" },
  { en: "Dhanishtha", hn: "Dhanishtha", hi: "धनिष्ठा", bn: "ধানিষ্ঠা", mr: "धनिष्ठा", ta: "தனிஷ்டா", te: "ధనిష్ఠ", gu: "ધનಿಷ್ಠા", kn: "ಧನिष्ठಾ", ml: "ധനിഷ്ഠ", pa: "ਧਨੀਸ਼ਠਾ", or: "ଧନିଷ୍ଠା", as: "ধানিষ্ঠা", zh: "达尼什塔", es: "Dhanishtha", ar: "دانيشطا", fr: "Dhanishtha", pt: "Dhanishtha", de: "Dhanishtha", ru: "Дхаништха", ja: "ダニシュター", id: "Dhanishtha", ko: "다니슈타", tr: "Dhanishtha" },
  { en: "Shatabhisha", hn: "Shatabhisha", hi: "शतभिषा", bn: "শতভিষা", mr: "शतभिषा", ta: "சதாபிஷா", te: "శతభిష", gu: "શতભિષા", kn: "ಶತಭಿಷಾ", ml: "ശതഭിഷാ", pa: "ਸ਼ਤਭਿਸ਼ਾ", or: "ଶତଭିଷା", as: "শতভিষা", zh: "沙塔比沙", es: "Shatabhisha", ar: "شاتا بيشا", fr: "Shatabhisha", pt: "Shatabhisha", de: "Shatabhisha", ru: "Шатабхиша", ja: "シャタビシャー", id: "Shatabhisha", ko: "샤타비샤", tr: "Shatabhisha" },
  { en: "Purva Bhadrapada", hn: "Purva Bhadrapada", hi: "पूर्व भाद्रपद", bn: "পুর্ব ভাদ্রপদ", mr: "पूर्वभाद्रपदा", ta: "பூர்வபத்ரபடா", te: "పూర్వ భాద్రపద", gu: "પૂર્વਭાદ્રપદા", kn: "ಪುರ್ವಭಾದ್ರಪದ", ml: "പൂര്‍വഭാദ്രപദ", pa: "ਪੂਰਵਾ ਭਾਦ੍ਰਪਦ", or: "ପୂର୍ବଭାଦ୍ରପଦ", as: "পূর্বভাদ্রপদ", zh: "普尔瓦巴德拉帕达", es: "Purva Bhadrapada", ar: "بورفا بهادرابادا", fr: "Purva Bhadrapada", pt: "Purva Bhadrapada", de: "Purva Bhadrapada", ru: "Пурва Бхадрапада", ja: "プールヴァバドラパダ", id: "Purva Bhadrapada", ko: "푸르바바드라파다", tr: "Purva Bhadrapada" },
  { en: "Uttara Bhadrapada", hn: "Uttara Bhadrapada", hi: "उत्तर भाद्रपद", bn: "উত্তর ভাদ্রপদ", mr: "उत्तरभाद्रपदा", ta: "உத்தரபத்ரபடா", te: "ఉత్తర భాద్రపద", gu: "ઉત્તરભાદ્રપદા", kn: "ಉತ್ತರಭಾದ್ರಪದ", ml: "ഉത്തരഭാദ്രപദ", pa: "ਉੱਤਰਾ ਭਾਦ੍ਰਪਦ", or: "ଉତ୍ତରଭାଦ୍ରପଦ", as: "উত্তরভাদ্রপদ", zh: "乌塔拉巴德拉帕达", es: "Uttara Bhadrapada", ar: "أوتارا بهادرابادا", fr: "Uttara Bhadrapada", pt: "Uttara Bhadrapada", de: "Uttara Bhadrapada", ru: "Уттара Бхадрапада", ja: "ウッタラバドラパダ", id: "Uttara Bhadrapada", ko: "우타라바드라파다", tr: "Uttara Bhadrapada" },
  { en: "Revati", hn: "Revati", hi: "रेवती", bn: "রেভতী", mr: "रेवती", ta: "ரேவதி", te: "రేవతి", gu: "રેવતી", kn: "ರೆವತಿ", ml: "രേവതി", pa: "ਰੇਵਤੀ", or: "ରେବତୀ", as: "রেৱতী", zh: "雷伐蒂", es: "Revati", ar: "ريواتي", fr: "Revati", pt: "Revati", de: "Revati", ru: "Ревати", ja: "レーヴァティ", id: "Revati", ko: "레바티", tr: "Revati" },
];

export function nakshatraName(idx: number, lang: UILang | "en" | "hn" | "hi"): string {
  const n = NAKSHATRA[idx];
  if (!n) return "";
  return pick(lang, n);
}

// ── Rashi index helper (0=Mesh..11=Meen) ────────────────────────────────────
export const RASHI_KEYS: RashiKey[] = [
  "mesh","vrishabh","mithun","kark","simha","kanya",
  "tula","vrishchik","dhanu","makar","kumbh","meen",
];
export function rashiAt(idx: number, lang: UILang | "en" | "hn" | "hi"): string {
  const k = RASHI_KEYS[((idx % 12) + 12) % 12];
  return pick(lang, RASHI[k]);
}
