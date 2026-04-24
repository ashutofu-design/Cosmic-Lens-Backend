import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { router, useLocalSearchParams } from "expo-router";
import React, { useState } from "react";
import {
  Pressable, ScrollView, StyleSheet, Text, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import { RASHI, PLANET, pick, type RashiKey } from "@/lib/i18nVedic";

const F = {
  bold: "Nunito_700Bold",
  semibold: "Nunito_600SemiBold",
  medium: "Nunito_500Medium",
  regular: "Nunito_400Regular",
};

// Static rashi visual metadata (color, dates) — names come from RASHI lookup
const RASHIS_META: Record<RashiKey, { color: string; dates: string }> = {
  mesh:      { color: "#ef4444", dates: "Mar 21–Apr 19" },
  vrishabh:  { color: "#10b981", dates: "Apr 20–May 20" },
  mithun:    { color: "#facc15", dates: "May 21–Jun 20" },
  kark:      { color: "#94a3b8", dates: "Jun 21–Jul 22" },
  simha:     { color: "#f59e0b", dates: "Jul 23–Aug 22" },
  kanya:     { color: "#22c55e", dates: "Aug 23–Sep 22" },
  tula:      { color: "#60a5fa", dates: "Sep 23–Oct 22" },
  vrishchik: { color: "#f43f5e", dates: "Oct 23–Nov 21" },
  dhanu:     { color: "#fb923c", dates: "Nov 22–Dec 21" },
  makar:     { color: "#8b5cf6", dates: "Dec 22–Jan 19" },
  kumbh:     { color: "#06b6d4", dates: "Jan 20–Feb 18" },
  meen:      { color: "#a78bfa", dates: "Feb 19–Mar 20" },
};
const RASHI_ORDER: RashiKey[] = [
  "mesh","vrishabh","mithun","kark","simha","kanya",
  "tula","vrishchik","dhanu","makar","kumbh","meen",
];

// ── Daily horoscope content — translated to en/hn/hi ─────────────────────────
type Phal = { aaj: string; hafta: string; lucky: string; savdhan: string };
const PHAL: Record<"en"|"hn"|"hi", Record<RashiKey, Phal>> = {
  en: {
    mesh:      { aaj: "Today will be wonderful for you. New successes are likely in business. Spend time with family. A piece of good news may come in the evening.", hafta: "Your hard work will pay off this week. Career advancement is indicated. A pleasant time with your partner. Watch your health.", lucky: "Red color, Tuesday, Number 9", savdhan: "Keep your temper in check." },
    vrishabh:  { aaj: "Financial position will be strong. You may meet an old friend. Domestic life will be peaceful. Auspicious to plan something new.", hafta: "Good prospects for monetary gains. A celebration may take place at home. Health stays good. Speak carefully with the boss.", lucky: "White color, Friday, Number 6", savdhan: "Watch your spending." },
    mithun:    { aaj: "Use intellect and discretion. Consider any new proposal carefully. Friends will be supportive. A short trip is possible.", hafta: "Foreign travel or a long journey is possible. New people you meet will prove useful. Honor and respect grow. Opportunities in communication.", lucky: "Yellow color, Wednesday, Number 5", savdhan: "Avoid talking too much." },
    kark:      { aaj: "An emotional day. Family matters get resolved. Take care of mother's health. Participation in a religious activity is likely.", hafta: "Peace and happiness reign at home. Stability in business. Good news about children possible. Financial situation improves.", lucky: "White/Yellow color, Monday, Number 2", savdhan: "Stay away from imagined fears." },
    simha:     { aaj: "You will be at the center today. Success in leadership tasks. People's attention will be on you. Honor and prestige rise.", hafta: "Success in official work. New heights in love affairs. Big decisions can be taken in business. Health stays good.", lucky: "Gold/Orange color, Sunday, Number 1", savdhan: "Avoid arrogance." },
    kanya:     { aaj: "Account-related matters go well. Good day for writers and teachers. Pay attention to small details. Perfection in work.", hafta: "Methodical work progresses in business. Be alert about health. New relationships form. A document or paperwork is completed.", lucky: "Green color, Wednesday, Number 5", savdhan: "Avoid excessive criticism." },
    tula:      { aaj: "Sweetness flows in relationships. Good day for big decisions. Art and beauty attract you. A sweet gift may come.", hafta: "Profit in partnerships. Romance blooms in love life. Legal matters get resolved. Good news in property matters.", lucky: "Blue color, Friday, Number 6", savdhan: "Don't delay decisions." },
    vrishchik: { aaj: "A day of secrecy and research. Time to peel back the layers of a deeper matter. Yogas of transformation are present. Recognize your power.", hafta: "Gains from inheritance or joint money. Success in research or investigation. Depth grows in love affairs. Health checkup beneficial.", lucky: "Red/Maroon color, Tuesday, Number 9", savdhan: "Avoid suspicion and jealousy." },
    dhanu:     { aaj: "An exciting day. Yoga of religious travel or temple visit. Success in higher education. People from afar will be remembered or met.", hafta: "Foreign-related works get completed. Jupiter's grace stays with you. New directions open in business. Yoga of property gain.", lucky: "Yellow color, Thursday, Number 3", savdhan: "Don't be too optimistic without thinking." },
    makar:     { aaj: "A day of work and discipline. Success earned through hard work bears fruit today. Seniors will recognize your work. Time to take responsibility.", hafta: "Yoga of advancement at workplace. Social prestige rises. Blessings of father or elders received. Financial planning succeeds.", lucky: "Blue/Black color, Saturday, Number 8", savdhan: "Don't ruin health by overworking." },
    kumbh:     { aaj: "A day of new ideas and innovation. Friends will be supportive. Mind engages in social service. Yoga of unexpected gain.", hafta: "Technical and scientific work moves forward. New friends bring new opportunities. Old relationships may break or remain. Time for independent decisions.", lucky: "Sky-blue color, Saturday, Number 4", savdhan: "Avoid abruptness." },
    meen:      { aaj: "A day of devotion and spirituality. Dreams may come true. Mind engages in art and music. Yoga of a spiritual experience.", hafta: "Spiritual progress occurs. Participation in charitable works. Time to turn imagination into reality. Take care of health.", lucky: "Yellow/Sea-Green color, Thursday, Number 3", savdhan: "Beware of deceitful people." },
  },
  hn: {
    mesh:      { aaj: "Aaj ka din aapke liye shandar rahega. Vyavsay mein nayi safaltaen milne ki sambhavana hai. Parivar ke saath samay bitaayen. Shaam ko koi khushkhabri mil sakti hai.", hafta: "Is hafte aapki mehnat rang laegi. Karyakshetra mein tarakki ke yog hain. Premi-premika ke beech suhana samay rahega. Swasthya dhyan rakhein.", lucky: "Lal rang, Mangalvar, Ank 9", savdhan: "Gusse par niyantran rakhein." },
    vrishabh:  { aaj: "Aarthik sthiti majboot hogi. Kisi purane dost se mulaqat ho sakti hai. Grihasth jeevan mein sukh ka vaas rahega. Nayi yojana banana auspicious hai.", hafta: "Dhan laabh ke achhe yog hain. Parivar mein koi mangal karya hone ki sambhavana. Swasthya uttar mein rahega. Sher ke saath baat sambhal kar karein.", lucky: "Safed rang, Shukravar, Ank 6", savdhan: "Kharche par nazar rakhein." },
    mithun:    { aaj: "Buddhi aur vivek se kaam lein. Kisi naye prastaav ko sochsamajh kar sweekar karein. Mitron ka saath milega. Sair-sapate ka yog banta hai.", hafta: "Videsh yatra ya door ka safar ho sakta hai. Naye log milenge jo upyogi sabit honge. Maan-samman mein vriddhi hogi. Sanchar ke kshetra mein avsar.", lucky: "Peela rang, Budhavar, Ank 5", savdhan: "Zyada bolne se bachein." },
    kark:      { aaj: "Bhaavnaatmak din hai aaj. Ghar-parivar ke mamle sulajhenge. Mata ki sehat ka dhyan rakhein. Kisi pooje ya dharmik kaarya mein bhaagidaari hogi.", hafta: "Ghar mein sukh-shanti ka vaas hoga. Vyavsay mein sthirta rahegi. Santan ki khushkhabri mil sakti hai. Aarthik sthiti sudhregr.", lucky: "Safed/Peela rang, Somvar, Ank 2", savdhan: "Maan ke vahem se door rahein." },
    simha:     { aaj: "Aaj aap kendra mein rahenge. Netatv ke kaarya mein safalta milegi. Logo ka dhyan aap par rahega. Samman aur pratishtha mein vriddhi hogi.", hafta: "Rajkiya kaaryon mein safalta milegi. Prem prasang mein nayi udaan aayegi. Vyavsay mein bade faisle le sakte hain. Swasthya achha rahega.", lucky: "Sona/Narangi rang, Ravivaar, Ank 1", savdhan: "Ahankar se bachein." },
    kanya:     { aaj: "Hisaab-kitaab ke mamle theek honge. Lekhak ya shikshak hain toh acha din hai. Choti-choti baaton par dhyan dena avashyak hai. Kaam mein perfection aayegi.", hafta: "Vyavsay mein methodical kaam aage badhega. Sehat ke prati satark rahein. Naye sambandh bante hain. Kisi document ya kaagaz ka kaam poora hoga.", lucky: "Hari rang, Budhavar, Ank 5", savdhan: "Zyada criticism se bachein." },
    tula:      { aaj: "Rishton mein meethas aayegi. Kisi bade faisle lene ka achi din hai. Kala aur sundar cheezen aapko akarshit karengi. Koi meetha tohfa milne ki sambhavana.", hafta: "Partnership mein fayda hoga. Prem jeevan mein romance ka vaas. Legal mamle sulajhenge. Sampatti ke mamle mein koi achhi khabar.", lucky: "Neela rang, Shukravar, Ank 6", savdhan: "Nirnay lene mein der na karein." },
    vrishchik: { aaj: "Guptata aur research ka cha din. Kisi gehri baat ki parat kholne ka samay. Transformation ke yog hain. Apni shakti ko pehchanen.", hafta: "Virasat ya joint money mein laabh ho sakta hai. Shodh ya anveshan mein safalta. Prem prasang mein gaharai aayegi. Health checkup faydemand.", lucky: "Lal/Maroon rang, Mangalvar, Ank 9", savdhan: "Shak aur eershya se bachein." },
    dhanu:     { aaj: "Uttejana se bhara din hai. Dharmik yatra ya mandir darshan ka yog. Uchch shiksha mein safalta milegi. Door ke log yaad aayenge ya milenge.", hafta: "Videsh sambandhi kaar karya poore honge. Guru ki kripa bani rahegi. Vyavsay mein nayi dishaayen khulengi. Sampatti laabh ke yog.", lucky: "Peela rang, Guruvaar, Ank 3", savdhan: "Zyada optimistic na rahen bina sochhe." },
    makar:     { aaj: "Karya aur anushasan ka din. Mehnat se mili safalta aaj phal degi. Uchchadhikari aapka kaam recognize karenge. Zimmedaari nibhaane ka samay.", hafta: "Karya sthaan par unnati ke yog. Samajik pratishtha badhegi. Pita ya bujurgon ka ashirvaad milega. Aarthik niyojan safal hoga.", lucky: "Neela/Kaala rang, Shanivaar, Ank 8", savdhan: "Zyada kaam se sehat na bigadein." },
    kumbh:     { aaj: "Naye vichar aur innovation ka din. Dosto ka saath milega. Samaj seva mein man lagega. Kisi apratyashit laabh ka yog.", hafta: "Technical aur scientific kaam aage badhega. Naye mitron se naye avsar. Puratan sambandh toot sakte ya bane bhi rahe. Swatantra nirnay lene ka samay.", lucky: "Aasmani neela rang, Shanivaar, Ank 4", savdhan: "Abruptness se bachein." },
    meen:      { aaj: "Bhakti aur spirituality ka din. Sapne sach ho sakte hain. Kala aur sangeet mein man lagega. Kisi roohaani anubhav ka yog.", hafta: "Aatmik unnati hogi. Dharmarth kaaryon mein bhaagidaari. Kalpana ko haaqikat mein badlne ka waqt. Swasthya ka dhyan rakhein.", lucky: "Peela/Sea Green rang, Guruvaar, Ank 3", savdhan: "Dhokhebaaz logon se sachait rahein." },
  },
  hi: {
    mesh:      { aaj: "आज का दिन आपके लिए शानदार रहेगा। व्यवसाय में नई सफलताएँ मिलने की संभावना है। परिवार के साथ समय बिताएँ। शाम को कोई खुशखबरी मिल सकती है।", hafta: "इस हफ्ते आपकी मेहनत रंग लाएगी। कार्यक्षेत्र में तरक्की के योग हैं। प्रेमी-प्रेमिका के बीच सुहाना समय रहेगा। स्वास्थ्य का ध्यान रखें।", lucky: "लाल रंग, मंगलवार, अंक 9", savdhan: "गुस्से पर नियंत्रण रखें।" },
    vrishabh:  { aaj: "आर्थिक स्थिति मजबूत होगी। किसी पुराने दोस्त से मुलाकात हो सकती है। गृहस्थ जीवन में सुख का वास रहेगा। नई योजना बनाना शुभ है।", hafta: "धन लाभ के अच्छे योग हैं। परिवार में कोई मंगल कार्य होने की संभावना। स्वास्थ्य उत्तम रहेगा। अधिकारी से बात संभल कर करें।", lucky: "सफेद रंग, शुक्रवार, अंक 6", savdhan: "खर्चे पर नज़र रखें।" },
    mithun:    { aaj: "बुद्धि और विवेक से काम लें। किसी नए प्रस्ताव को सोच-समझ कर स्वीकार करें। मित्रों का साथ मिलेगा। सैर-सपाटे का योग बनता है।", hafta: "विदेश यात्रा या दूर का सफर हो सकता है। नए लोग मिलेंगे जो उपयोगी साबित होंगे। मान-सम्मान में वृद्धि होगी। संचार के क्षेत्र में अवसर।", lucky: "पीला रंग, बुधवार, अंक 5", savdhan: "ज़्यादा बोलने से बचें।" },
    kark:      { aaj: "भावनात्मक दिन है आज। घर-परिवार के मामले सुलझेंगे। माता की सेहत का ध्यान रखें। किसी पूजा या धार्मिक कार्य में भागीदारी होगी।", hafta: "घर में सुख-शांति का वास होगा। व्यवसाय में स्थिरता रहेगी। संतान की खुशखबरी मिल सकती है। आर्थिक स्थिति सुधरेगी।", lucky: "सफेद/पीला रंग, सोमवार, अंक 2", savdhan: "मन के वहम से दूर रहें।" },
    simha:     { aaj: "आज आप केंद्र में रहेंगे। नेतृत्व के कार्य में सफलता मिलेगी। लोगों का ध्यान आप पर रहेगा। सम्मान और प्रतिष्ठा में वृद्धि होगी।", hafta: "राजकीय कार्यों में सफलता मिलेगी। प्रेम प्रसंग में नई उड़ान आएगी। व्यवसाय में बड़े फैसले ले सकते हैं। स्वास्थ्य अच्छा रहेगा।", lucky: "सोना/नारंगी रंग, रविवार, अंक 1", savdhan: "अहंकार से बचें।" },
    kanya:     { aaj: "हिसाब-किताब के मामले ठीक होंगे। लेखक या शिक्षक हैं तो अच्छा दिन है। छोटी-छोटी बातों पर ध्यान देना आवश्यक है। काम में पूर्णता आएगी।", hafta: "व्यवसाय में व्यवस्थित कार्य आगे बढ़ेगा। सेहत के प्रति सतर्क रहें। नए संबंध बनते हैं। किसी दस्तावेज़ का काम पूरा होगा।", lucky: "हरा रंग, बुधवार, अंक 5", savdhan: "अधिक आलोचना से बचें।" },
    tula:      { aaj: "रिश्तों में मिठास आएगी। किसी बड़े फैसले लेने का अच्छा दिन है। कला और सुंदर चीज़ें आपको आकर्षित करेंगी। कोई मीठा तोहफा मिलने की संभावना।", hafta: "साझेदारी में फायदा होगा। प्रेम जीवन में रोमांस का वास। कानूनी मामले सुलझेंगे। संपत्ति के मामले में कोई अच्छी खबर।", lucky: "नीला रंग, शुक्रवार, अंक 6", savdhan: "निर्णय लेने में देर न करें।" },
    vrishchik: { aaj: "गुप्तता और शोध का दिन। किसी गहरी बात की परत खोलने का समय। परिवर्तन के योग हैं। अपनी शक्ति को पहचानें।", hafta: "विरासत या साझा धन में लाभ हो सकता है। शोध या अन्वेषण में सफलता। प्रेम प्रसंग में गहराई आएगी। स्वास्थ्य जांच फायदेमंद।", lucky: "लाल/मैरून रंग, मंगलवार, अंक 9", savdhan: "शक और ईर्ष्या से बचें।" },
    dhanu:     { aaj: "उत्तेजना से भरा दिन है। धार्मिक यात्रा या मंदिर दर्शन का योग। उच्च शिक्षा में सफलता मिलेगी। दूर के लोग याद आएँगे या मिलेंगे।", hafta: "विदेश संबंधी कार्य पूरे होंगे। गुरु की कृपा बनी रहेगी। व्यवसाय में नई दिशाएँ खुलेंगी। संपत्ति लाभ के योग।", lucky: "पीला रंग, गुरुवार, अंक 3", savdhan: "बिना सोचे अति आशावादी न रहें।" },
    makar:     { aaj: "कार्य और अनुशासन का दिन। मेहनत से मिली सफलता आज फल देगी। उच्चाधिकारी आपका काम पहचानेंगे। ज़िम्मेदारी निभाने का समय।", hafta: "कार्यस्थल पर उन्नति के योग। सामाजिक प्रतिष्ठा बढ़ेगी। पिता या बुज़ुर्गों का आशीर्वाद मिलेगा। आर्थिक नियोजन सफल होगा।", lucky: "नीला/काला रंग, शनिवार, अंक 8", savdhan: "ज़्यादा काम से सेहत न बिगाड़ें।" },
    kumbh:     { aaj: "नए विचार और नवाचार का दिन। दोस्तों का साथ मिलेगा। समाज सेवा में मन लगेगा। किसी अप्रत्याशित लाभ का योग।", hafta: "तकनीकी और वैज्ञानिक कार्य आगे बढ़ेगा। नए मित्रों से नए अवसर। पुरातन संबंध टूट सकते या बने भी रहें। स्वतंत्र निर्णय का समय।", lucky: "आसमानी नीला रंग, शनिवार, अंक 4", savdhan: "अचानकता से बचें।" },
    meen:      { aaj: "भक्ति और आध्यात्मिकता का दिन। सपने सच हो सकते हैं। कला और संगीत में मन लगेगा। किसी आध्यात्मिक अनुभव का योग।", hafta: "आत्मिक उन्नति होगी। धर्मार्थ कार्यों में भागीदारी। कल्पना को हकीकत में बदलने का वक़्त। स्वास्थ्य का ध्यान रखें।", lucky: "पीला/सी-ग्रीन रंग, गुरुवार, अंक 3", savdhan: "धोखेबाज़ लोगों से सचेत रहें।" },
  },
};

// Map any sign name → rashi key
const SIGN_TO_RASHI: Record<string, RashiKey> = {
  aries: "mesh", mesh: "mesh", "मेष": "mesh",
  taurus: "vrishabh", vrishabh: "vrishabh", "वृषभ": "vrishabh",
  gemini: "mithun", mithun: "mithun", "मिथुन": "mithun",
  cancer: "kark", kark: "kark", "कर्क": "kark",
  leo: "simha", simha: "simha", "सिंह": "simha",
  virgo: "kanya", kanya: "kanya", "कन्या": "kanya",
  libra: "tula", tula: "tula", "तुला": "tula",
  scorpio: "vrishchik", vrishchik: "vrishchik", "वृश्चिक": "vrishchik",
  sagittarius: "dhanu", dhanu: "dhanu", "धनु": "dhanu",
  capricorn: "makar", makar: "makar", "मकर": "makar",
  aquarius: "kumbh", kumbh: "kumbh", "कुम्भ": "kumbh", "कुंभ": "kumbh",
  pisces: "meen", meen: "meen", "मीन": "meen",
};

function deriveRashiKey(moonSign?: string | null, planets?: Array<{ name: string; rashi?: string }>): RashiKey | null {
  if (moonSign) {
    const k = SIGN_TO_RASHI[moonSign.trim().toLowerCase()];
    if (k) return k;
  }
  const moon = planets?.find(p => p?.name === "Moon");
  if (moon?.rashi) {
    const k = SIGN_TO_RASHI[moon.rashi.trim().toLowerCase()];
    if (k) return k;
  }
  return null;
}

// Daily-rotating prefix — translated per language
const DAILY_PREFIX: Record<"en"|"hn"|"hi", string[]> = {
  en: [
    "Sun's influence is strong today. ",
    "The Moon's position is sweet. ",
    "With Mars's energy, ",
    "By Mercury's grace, ",
    "Under Jupiter's blessings, ",
    "Venus's influence is pleasant. ",
    "Saturn's gaze is deep. ",
  ],
  hn: [
    "Aaj Surya prabhav prabal hai. ",
    "Chandrama ki sthiti madhur hai. ",
    "Mangal ki urja ke saath, ",
    "Budh ki kripa se, ",
    "Guru ke ashirvaad mein, ",
    "Shukra ka prabhav suhana hai. ",
    "Shani ki drishti gehri hai. ",
  ],
  hi: [
    "आज सूर्य का प्रभाव प्रबल है। ",
    "चंद्रमा की स्थिति मधुर है। ",
    "मंगल की ऊर्जा के साथ, ",
    "बुध की कृपा से, ",
    "गुरु के आशीर्वाद में, ",
    "शुक्र का प्रभाव सुहाना है। ",
    "शनि की दृष्टि गहरी है। ",
  ],
};

export default function RashifalScreen() {
  const C = useC();
  const t = useT();
  const insets = useSafeAreaInsets();
  const params = useLocalSearchParams<{ tab?: string }>();
  const [tabIdx, setTabIdx] = useState(params.tab === "weekly" ? 1 : 0);
  const [expanded, setExpanded] = useState<string | null>(null);
  const { profiles, kundli } = useUser();
  const userRashi = deriveRashiKey(kundli?.moonSign, kundli?.planets);

  const v = t.vlang;
  const TABS = [t.daily, t.weekly, t.monthly];
  const todayPrefix = DAILY_PREFIX[v][new Date().getDay()];
  const phalSet = PHAL[v];

  return (
    <View style={{ flex: 1 }}>
      <CosmicBg />
      <View style={[s.topBar, { paddingTop: insets.top + 10 }]}>
        <Pressable onPress={() => router.back()} style={s.backBtn}>
          <Feather name="arrow-left" size={20} color={C.text} />
        </Pressable>
        <View>
          <Text style={[s.title, { color: C.text }]}>{t.rashifalTitle}</Text>
          <Text style={[s.subtitle, { color: C.textMuted }]}>{t.todaysRashifal}</Text>
        </View>
        <View style={{ width: 36 }} />
      </View>

      {/* Tab pills */}
      <View style={s.tabRow}>
        {TABS.map((tab, i) => (
          <Pressable
            key={tab}
            onPress={() => { Haptics.selectionAsync(); setTabIdx(i); }}
            style={[
              s.tabPill,
              { borderColor: C.border },
              tabIdx === i && { backgroundColor: "#f59e0b", borderColor: "#f59e0b" },
            ]}
          >
            <Text style={[s.tabText, { color: tabIdx === i ? "#fff" : C.textMuted }]}>{tab}</Text>
          </Pressable>
        ))}
      </View>

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: insets.bottom + 100, gap: 12 }}
      >
        {RASHI_ORDER.map(key => {
          const meta = RASHIS_META[key];
          const rashi = RASHI[key];
          const phal = phalSet[key];
          const isMe = userRashi === key;
          const isOpen = expanded === key;
          const text = tabIdx === 0 ? `${todayPrefix}${phal.aaj}` : phal.hafta;
          const displayName = pick(v, rashi);
          const englishName = rashi.en;
          const lordName = pick(v, PLANET[rashi.lord as keyof typeof PLANET]);

          return (
            <Pressable
              key={key}
              onPress={() => {
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                setExpanded(isOpen ? null : key);
              }}
              style={[
                s.rashiCard,
                {
                  backgroundColor: C.bgCard,
                  borderColor: isMe ? `${meta.color}60` : C.border,
                  borderWidth: isMe ? 1.5 : 1,
                },
              ]}
            >
              <View style={s.rashiRow}>
                <View style={[s.rashiEmoji, { backgroundColor: `${meta.color}18` }]}>
                  <Text style={{ fontSize: 22 }}>{rashi.emoji}</Text>
                </View>
                <View style={{ flex: 1 }}>
                  <View style={{ flexDirection: "row", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
                    <Text style={[s.rashiName, { color: C.text }]}>{displayName}</Text>
                    {v !== "en" && (
                      <Text style={[s.rashiEn, { color: C.textDim }]}>{englishName}</Text>
                    )}
                    {isMe && (
                      <View style={[s.meBadge, { backgroundColor: `${meta.color}20`, borderColor: `${meta.color}40` }]}>
                        <Text style={[s.meBadgeText, { color: meta.color }]}>{(t as any).yourSign ?? "Your Sign"}</Text>
                      </View>
                    )}
                  </View>
                  <Text style={[s.rashiLord, { color: C.textMuted }]}>{(t as any).lordLabel ?? "Lord"}: {lordName} · {meta.dates}</Text>
                </View>
                <Feather name={isOpen ? "chevron-up" : "chevron-down"} size={16} color={C.textDim} />
              </View>

              {isOpen && (
                <View style={{ marginTop: 12, gap: 10 }}>
                  <View style={[s.divider, { backgroundColor: C.border3 }]} />
                  <Text style={[s.phalText, { color: C.textMid }]}>{text}</Text>
                  <View style={s.luckRow}>
                    <View style={[s.luckChip, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
                      <Text style={{ fontSize: 12 }}>🍀</Text>
                      <Text style={[s.luckText, { color: C.textMuted }]}>{phal.lucky}</Text>
                    </View>
                  </View>
                  <View style={[s.savdhanBox, { backgroundColor: C.isDark ? "rgba(239,68,68,0.06)" : "#FEE2E2", borderColor: "rgba(239,68,68,0.2)" }]}>
                    <Feather name="alert-triangle" size={12} color="#ef4444" />
                    <Text style={[s.savdhanText, { color: "#ef4444" }]}>{(t as any).warningLabel ?? "Caution"}: {phal.savdhan}</Text>
                  </View>
                </View>
              )}
            </Pressable>
          );
        })}
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
  subtitle: { fontSize: 12, fontFamily: F.regular, marginTop: 1 },
  tabRow: {
    flexDirection: "row", gap: 8, paddingHorizontal: 16, marginBottom: 14,
  },
  tabPill: {
    paddingHorizontal: 16, paddingVertical: 7, borderRadius: 20,
    borderWidth: 1,
  },
  tabText: { fontSize: 12, fontFamily: F.semibold },
  rashiCard: {
    borderRadius: 14, borderWidth: 1, padding: 14,
  },
  rashiRow: { flexDirection: "row", alignItems: "center", gap: 12 },
  rashiEmoji: {
    width: 46, height: 46, borderRadius: 14,
    alignItems: "center", justifyContent: "center",
  },
  rashiName: { fontSize: 15, fontFamily: F.bold },
  rashiEn: { fontSize: 12, fontFamily: F.medium },
  rashiLord: { fontSize: 11, fontFamily: F.regular, marginTop: 2 },
  meBadge: {
    paddingHorizontal: 6, paddingVertical: 2,
    borderRadius: 8, borderWidth: 1,
  },
  meBadgeText: { fontSize: 9, fontFamily: F.bold },
  divider: { height: 1 },
  phalText: { fontSize: 13.5, fontFamily: F.regular, lineHeight: 21 },
  luckRow: { flexDirection: "row" },
  luckChip: {
    flexDirection: "row", alignItems: "center", gap: 6,
    paddingHorizontal: 10, paddingVertical: 6,
    borderRadius: 10, borderWidth: 1,
  },
  luckText: { fontSize: 11, fontFamily: F.medium },
  savdhanBox: {
    flexDirection: "row", alignItems: "center", gap: 6,
    paddingHorizontal: 10, paddingVertical: 7,
    borderRadius: 10, borderWidth: 1,
  },
  savdhanText: { fontSize: 11, fontFamily: F.medium, flex: 1 },
});
