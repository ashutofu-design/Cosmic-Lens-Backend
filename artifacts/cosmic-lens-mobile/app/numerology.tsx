import { Feather } from "@expo/vector-icons";
import { BlurView } from "expo-blur";
import * as FileSystem from "expo-file-system/legacy";
import { saveLocalReport } from "@/lib/localReports";
import * as Haptics from "expo-haptics";
import * as Linking from "expo-linking";
import { router } from "expo-router";
import * as Sharing from "expo-sharing";
import { LinearGradient } from "expo-linear-gradient";
import React, { useEffect, useMemo, useRef, useState } from "react";
import { API_BASE } from "@/lib/apiConfig";
import {
  Animated,
  Easing,
  Modal,
  Platform, Pressable, ScrollView, StyleSheet,
  Text, TextInput, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { FadeInView, staggerDelay } from "@/components/motion/FadeInView";
import { useC } from "@/context/ThemeContext";
import { useUser, type ProfileEntry } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import { getPYTheme } from "@/lib/i18nContent";
import {
  LIFE_MASTERY_CHECKOUT_CONFIG,
  LIFE_MASTERY_UI_PRICING,
  lifeMasteryOrderTotalInr,
  LIFE_MASTERY_PRIORITY_SURCHARGE_INR,
} from "@/lib/numerologyProOffer";
import { consumeNumerologyPaidReady, gateNumerologyReportAfterLangPick } from "@/lib/numerologyReportCheckoutFlow";
import { FOUNDER_PROFILE } from "@/lib/founderProfile";

const F = {
  regular: "Nunito_400Regular",
  medium:  "Nunito_500Medium",
  semi:    "Nunito_600SemiBold",
  bold:    "Nunito_700Bold",
  extra:   "Nunito_800ExtraBold",
} as const;

// ── Calculation helpers ───────────────────────────────────────────────────────
const PYTH: Record<string, number> = {
  a:1,b:2,c:3,d:4,e:5,f:6,g:7,h:8,i:9,
  j:1,k:2,l:3,m:4,n:5,o:6,p:7,q:8,r:9,
  s:1,t:2,u:3,v:4,w:5,x:6,y:7,z:8,
};
const VOWELS = new Set(["a","e","i","o","u"]);

function reduce(n: number): number {
  while (n > 9 && n !== 11 && n !== 22 && n !== 33) {
    n = String(n).split("").reduce((a, c) => a + parseInt(c, 10), 0);
  }
  return n;
}
function digitSum(x: number): number {
  return String(Math.abs(x)).split("").reduce((a, c) => a + parseInt(c, 10), 0);
}
function letterSum(name: string, vowelsOnly?: boolean, consonantsOnly?: boolean): number {
  const chars = name.toLowerCase().replace(/[^a-z]/g, "").split("");
  const filtered = chars.filter(c =>
    vowelsOnly    ? VOWELS.has(c) :
    consonantsOnly ? !VOWELS.has(c) : true
  );
  return filtered.reduce((a, c) => a + (PYTH[c] ?? 0), 0);
}

function calcLifePath(day: number, month: number, year: number) {
  return reduce(reduce(digitSum(day)) + reduce(digitSum(month)) + reduce(digitSum(year)));
}
function calcBirthDay(day: number) {
  return reduce(digitSum(day));
}
function calcDestiny(name: string) { return reduce(letterSum(name)); }
function calcSoulUrge(name: string) { return reduce(letterSum(name, true)); }
function calcPersonality(name: string) { return reduce(letterSum(name, false, true)); }
function calcMaturity(lp: number, dest: number) { return reduce(lp + dest); }
function calcPersonalYear(day: number, month: number) {
  const y = new Date().getFullYear();
  return reduce(digitSum(day) + digitSum(month) + digitSum(y));
}
function calcPersonalMonth(day: number, month: number) {
  const py  = calcPersonalYear(day, month);
  const now = new Date().getMonth() + 1;
  return reduce(py + now);
}

// ── Number interpretation data ────────────────────────────────────────────────
interface NumInfo {
  title: string; titleHindi: string;
  planet: string; planetEmoji: string;
  color: string;
  luckyNums: string; luckyColor: string; luckyColorHex: string;
  traits: string[]; traitsHindi: string[];
  desc: string;     descHn?: string;     descHi?: string;
  career: string;   careerHn?: string;   careerHi?: string;
  love: string;     loveHn?: string;     loveHi?: string;
  strength: string; strengthHn?: string; strengthHi?: string;
  weakness: string; weaknessHn?: string; weaknessHi?: string;
  remedy: string;   remedyHn?: string;   remedyHi?: string;
}

const NUM: Record<number, NumInfo> = {
  1: { title:"Leadership", titleHindi:"नेतृत्व", planet:"Surya", planetEmoji:"☀️",
       color:"#f59e0b", luckyNums:"1, 10, 19, 28", luckyColor:"Gold / Orange", luckyColorHex:"#f59e0b",
       traits:["Ambitious","Independent","Pioneering","Creative"],
       traitsHindi:["महत्त्वाकांक्षी","स्वतंत्र","अग्रणी","रचनात्मक"],
       desc:"You are a natural-born leader with iron willpower. Originality and independence define your path — you were born to blaze new trails.",
       descHn:"Aap ek janam-jaat leader ho lohe jaisi will-power ke saath. Originality aur independence aapka raasta define karte hain — aap naye raaste banane ke liye paida hue ho.",
       descHi:"आप लौह इच्छाशक्ति वाले जन्मजात नेता हैं। मौलिकता और स्वतंत्रता आपका मार्ग परिभाषित करती है — आप नए रास्ते बनाने के लिए जन्मे हैं।",
       career:"Politics, Management, Entrepreneurship, Military",
       careerHn:"Politics, Management, Business, Military",
       careerHi:"राजनीति, प्रबंधन, उद्यमिता, सेना",
       love:"You need a partner who respects your independence and admires your drive.",
       loveHn:"Aapko aisa partner chahiye jo aapki independence ka samman kare aur aapki drive ko sarahaye.",
       loveHi:"आपको ऐसा साथी चाहिए जो आपकी स्वतंत्रता का सम्मान करे और आपकी ऊर्जा की प्रशंसा करे।",
       strength:"Determination, Confidence", strengthHn:"Determination, Confidence", strengthHi:"दृढ़ संकल्प, आत्मविश्वास",
       weakness:"Ego, Stubbornness", weaknessHn:"Ego, Ziddi", weaknessHi:"अहंकार, हठ",
       remedy:"Offer water to the rising Sun each morning. Donate wheat on Sundays.",
       remedyHn:"Roz subah ugte Surya ko jal arpan karein. Ravivar ko gehu daan karein.",
       remedyHi:"प्रत्येक प्रातः उगते सूर्य को जल अर्पित करें। रविवार को गेहूँ का दान करें।" },
  2: { title:"Partnership", titleHindi:"सहयोग", planet:"Chandra", planetEmoji:"🌙",
       color:"#94a3b8", luckyNums:"2, 11, 20, 29", luckyColor:"White / Silver", luckyColorHex:"#e2e8f0",
       traits:["Sensitive","Cooperative","Diplomatic","Intuitive"],
       traitsHindi:["संवेदनशील","सहयोगी","कूटनीतिज्ञ","अंतर्ज्ञानी"],
       desc:"You are a peacemaker gifted with deep emotional intelligence. You thrive in partnerships and bring harmony to every relationship you touch.",
       descHn:"Aap ek shanti-doot ho jisme deep emotional intelligence hai. Aap partnerships me khilte ho aur har rishte me harmony lekar aate ho.",
       descHi:"आप गहरी भावनात्मक बुद्धिमत्ता वाले शांतिदूत हैं। आप साझेदारियों में फलते-फूलते हैं और हर रिश्ते में सामंजस्य लाते हैं।",
       career:"Counseling, Arts, Music, Nursing, Diplomacy",
       careerHn:"Counseling, Arts, Music, Nursing, Diplomacy",
       careerHi:"परामर्श, कला, संगीत, नर्सिंग, राजनयिक",
       love:"You are a deeply romantic and devoted partner who values emotional safety.",
       loveHn:"Aap ek deeply romantic aur devoted partner ho jise emotional safety bahut pyari hai.",
       loveHi:"आप गहरे रोमांटिक और समर्पित साथी हैं जो भावनात्मक सुरक्षा को महत्व देते हैं।",
       strength:"Empathy, Patience", strengthHn:"Empathy, Patience", strengthHi:"समानुभूति, धैर्य",
       weakness:"Over-sensitivity, Indecisiveness", weaknessHn:"Over-sensitivity, Indecisive nature", weaknessHi:"अति-संवेदनशीलता, अनिर्णय",
       remedy:"Fast on Mondays and donate white cloth or rice to a temple.",
       remedyHn:"Somvar ko vrat karein aur mandir me safed kapda ya chawal daan karein.",
       remedyHi:"सोमवार को व्रत करें और मंदिर में सफेद वस्त्र या चावल का दान करें।" },
  3: { title:"Creativity", titleHindi:"सृजनात्मकता", planet:"Guru", planetEmoji:"🪐",
       color:"#facc15", luckyNums:"3, 12, 21, 30", luckyColor:"Yellow / Purple", luckyColorHex:"#facc15",
       traits:["Joyful","Expressive","Optimistic","Social"],
       traitsHindi:["आनंदमय","अभिव्यक्तिशील","आशावादी","सामाजिक"],
       desc:"You radiate joy and creativity. Gifted with communication and charisma, you inspire and uplift everyone around you.",
       descHn:"Aap me khushi aur creativity bhari hui hai. Communication aur charisma ke gift ke saath, aap apne aas-paas sabko inspire karte ho.",
       descHi:"आप आनंद और रचनात्मकता बिखेरते हैं। संचार व करिश्मे के उपहार के साथ आप अपने आसपास सभी को प्रेरित और उत्साहित करते हैं।",
       career:"Writing, Entertainment, Teaching, Arts, Comedy",
       careerHn:"Writing, Entertainment, Teaching, Arts, Comedy",
       careerHi:"लेखन, मनोरंजन, शिक्षण, कला, हास्य",
       love:"You are a playful, fun-loving partner who never lets the spark fade.",
       loveHn:"Aap ek playful, fun-loving partner ho jo rishte ki chingari kabhi bujhne nahi dete.",
       loveHi:"आप एक चंचल, मस्ती-प्रेमी साथी हैं जो रिश्ते की चिंगारी कभी बुझने नहीं देते।",
       strength:"Optimism, Creativity", strengthHn:"Optimism, Creativity", strengthHi:"आशावाद, रचनात्मकता",
       weakness:"Scattered focus, Over-indulgence", weaknessHn:"Bikhra focus, Over-indulgence", weaknessHi:"बिखरा ध्यान, अति-भोग",
       remedy:"Worship Lord Vishnu on Thursdays. Donate yellow sweets or turmeric.",
       remedyHn:"Guruvar ko Bhagwan Vishnu ki puja karein. Peeli mithai ya haldi daan karein.",
       remedyHi:"गुरुवार को भगवान विष्णु की पूजा करें। पीली मिठाई या हल्दी का दान करें।" },
  4: { title:"Foundation", titleHindi:"स्थिरता", planet:"Rahu", planetEmoji:"🌑",
       color:"#8b5cf6", luckyNums:"4, 13, 22, 31", luckyColor:"Electric Blue / Grey", luckyColorHex:"#8b5cf6",
       traits:["Disciplined","Hardworking","Systematic","Reliable"],
       traitsHindi:["अनुशासित","मेहनती","व्यवस्थित","विश्वसनीय"],
       desc:"You are the builder — patient, dependable, and devoted to creating lasting structures through hard work and discipline.",
       descHn:"Aap nirmaata ho — patient, dependable, aur mehnat-discipline se lasting structures banane ke liye samarpit.",
       descHi:"आप निर्माता हैं — धैर्यवान, विश्वसनीय और कठिन परिश्रम तथा अनुशासन से दीर्घकालीन संरचनाएँ बनाने को समर्पित।",
       career:"Engineering, Architecture, Finance, Defense",
       careerHn:"Engineering, Architecture, Finance, Defense",
       careerHi:"इंजीनियरिंग, वास्तुकला, वित्त, रक्षा",
       love:"You are a loyal and stable partner who values commitment above all else.",
       loveHn:"Aap ek loyal aur stable partner ho jo commitment ko sabse upar rakhte ho.",
       loveHi:"आप एक वफ़ादार और स्थिर साथी हैं जो प्रतिबद्धता को सबसे ऊपर रखते हैं।",
       strength:"Discipline, Reliability", strengthHn:"Discipline, Reliability", strengthHi:"अनुशासन, विश्वसनीयता",
       weakness:"Rigidity, Resistance to change", weaknessHn:"Rigidity, Badlav me resistance", weaknessHi:"कठोरता, परिवर्तन का प्रतिरोध",
       remedy:"Donate blue clothes on Saturdays. Chant the Rahu Beej mantra.",
       remedyHn:"Shanivar ko neele kapde daan karein. Rahu Beej mantra ka jaap karein.",
       remedyHi:"शनिवार को नीले वस्त्र दान करें। राहु बीज मंत्र का जाप करें।" },
  5: { title:"Freedom", titleHindi:"स्वतंत्रता", planet:"Budha", planetEmoji:"☿️",
       color:"#10b981", luckyNums:"5, 14, 23", luckyColor:"Green / Light Blue", luckyColorHex:"#10b981",
       traits:["Adventurous","Versatile","Quick-witted","Energetic"],
       traitsHindi:["साहसी","बहुमुखी","तीक्ष्ण","ऊर्जावान"],
       desc:"You are a free spirit — curious, adaptable, and always seeking the next horizon. You thrive on change and new experiences.",
       descHn:"Aap free spirit ho — curious, adaptable, aur hamesha agle horizon ki talaash me. Badlav aur naye experiences me aap khilte ho.",
       descHi:"आप मुक्त आत्मा हैं — जिज्ञासु, अनुकूलनीय, और सदा नए क्षितिज की खोज में। परिवर्तन और नए अनुभवों में आप फलते-फूलते हैं।",
       career:"Journalism, Travel, Sales, Technology, Media",
       careerHn:"Journalism, Travel, Sales, Technology, Media",
       careerHi:"पत्रकारिता, यात्रा, बिक्री, तकनीक, मीडिया",
       love:"You need an adventurous partner who can match your restless energy.",
       loveHn:"Aapko adventurous partner chahiye jo aapki restless energy ka match kar sake.",
       loveHi:"आपको ऐसा साहसी साथी चाहिए जो आपकी बेचैन ऊर्जा से मेल खा सके।",
       strength:"Adaptability, Intelligence", strengthHn:"Adaptability, Intelligence", strengthHi:"अनुकूलनशीलता, बुद्धिमत्ता",
       weakness:"Restlessness, Inconsistency", weaknessHn:"Bechaini, Inconsistency", weaknessHi:"बेचैनी, असंगति",
       remedy:"Worship Lord Ganesha on Wednesdays. Donate green vegetables to the needy.",
       remedyHn:"Budhvar ko Bhagwan Ganesh ki puja karein. Zaroortmandon ko hari sabziyaan daan karein.",
       remedyHi:"बुधवार को भगवान गणेश की पूजा करें। ज़रूरतमंदों को हरी सब्ज़ियाँ दान करें।" },
  6: { title:"Love & Nurturing", titleHindi:"प्रेम और देखभाल", planet:"Shukra", planetEmoji:"♀️",
       color:"#f43f5e", luckyNums:"6, 15, 24", luckyColor:"Pink / Light Blue", luckyColorHex:"#f43f5e",
       traits:["Loving","Responsible","Artistic","Nurturing"],
       traitsHindi:["प्रेमपूर्ण","जिम्मेदार","कलात्मक","देखभाल करने वाला"],
       desc:"You are a caretaker with a boundless heart. Harmony, family, beauty, and service define your soul's mission in this lifetime.",
       descHn:"Aap ek caretaker ho aseem dil ke saath. Harmony, parivaar, sundarta, aur seva is janam me aapki aatma ka mission hain.",
       descHi:"आप असीम हृदय वाले देखभालकर्ता हैं। सामंजस्य, परिवार, सौंदर्य और सेवा इस जीवन में आपकी आत्मा का मिशन हैं।",
       career:"Medicine, Teaching, Art, Interior Design, Social Work",
       careerHn:"Medicine, Teaching, Art, Interior Design, Social Work",
       careerHi:"चिकित्सा, शिक्षण, कला, इंटीरियर डिज़ाइन, समाज सेवा",
       love:"You are a devoted, family-first partner with a deeply romantic soul.",
       loveHn:"Aap ek devoted, family-first partner ho jiski aatma deeply romantic hai.",
       loveHi:"आप समर्पित, परिवार-प्रथम साथी हैं जिसकी आत्मा गहरी रोमांटिक है।",
       strength:"Compassion, Responsibility", strengthHn:"Compassion, Responsibility", strengthHi:"करुणा, जिम्मेदारी",
       weakness:"Over-sacrifice, Jealousy", weaknessHn:"Over-sacrifice, Jealousy", weaknessHi:"अति-त्याग, ईर्ष्या",
       remedy:"Worship Goddess Lakshmi on Fridays. Donate sweets and white flowers.",
       remedyHn:"Shukravar ko Devi Lakshmi ki puja karein. Mithai aur safed phool daan karein.",
       remedyHi:"शुक्रवार को देवी लक्ष्मी की पूजा करें। मिठाई और सफेद फूल दान करें।" },
  7: { title:"Wisdom & Mysticism", titleHindi:"ज्ञान और रहस्य", planet:"Ketu", planetEmoji:"🌠",
       color:"#06b6d4", luckyNums:"7, 16, 25", luckyColor:"Violet / Indigo", luckyColorHex:"#8b5cf6",
       traits:["Analytical","Spiritual","Introspective","Mysterious"],
       traitsHindi:["विश्लेषणात्मक","आध्यात्मिक","अंतर्मुखी","रहस्यमय"],
       desc:"You are the seeker — drawn to hidden truths, deeper knowledge, and the mysteries of the cosmos. Solitude and reflection fuel your wisdom.",
       descHn:"Aap khoji ho — chhupe satya, gehre gyaan, aur brahmand ke rahasyon ki taraf khinche jaate ho. Ekant aur chintan se aapki buddhi badhti hai.",
       descHi:"आप खोजी हैं — छिपे सत्यों, गहन ज्ञान और ब्रह्माण्ड के रहस्यों की ओर आकर्षित। एकांत और चिंतन आपकी बुद्धि को पोषित करते हैं।",
       career:"Research, Philosophy, Science, Spiritual work, Psychology",
       careerHn:"Research, Philosophy, Science, Spiritual work, Psychology",
       careerHi:"शोध, दर्शन, विज्ञान, आध्यात्मिक कार्य, मनोविज्ञान",
       love:"You seek a deep intellectual and spiritual bond with your partner.",
       loveHn:"Aap apne partner ke saath deep intellectual aur spiritual bond chahte ho.",
       loveHi:"आप अपने साथी के साथ गहरा बौद्धिक और आध्यात्मिक बंधन चाहते हैं।",
       strength:"Insight, Wisdom", strengthHn:"Insight, Wisdom", strengthHi:"अंतर्दृष्टि, ज्ञान",
       weakness:"Aloofness, Over-analysis", weaknessHn:"Aloofness, Over-analysis", weaknessHi:"उदासीनता, अति-विश्लेषण",
       remedy:"Worship Lord Shiva on Mondays. Donate black sesame seeds on Saturdays.",
       remedyHn:"Somvar ko Bhagwan Shiv ki puja karein. Shanivar ko kale til daan karein.",
       remedyHi:"सोमवार को भगवान शिव की पूजा करें। शनिवार को काले तिल दान करें।" },
  8: { title:"Power & Abundance", titleHindi:"शक्ति और समृद्धि", planet:"Shani", planetEmoji:"🪐",
       color:"#6366f1", luckyNums:"8, 17, 26", luckyColor:"Dark Blue / Black", luckyColorHex:"#6366f1",
       traits:["Powerful","Ambitious","Strategic","Enduring"],
       traitsHindi:["शक्तिशाली","महत्त्वाकांक्षी","रणनीतिक","धैर्यवान"],
       desc:"You carry Saturn's immense power. Obstacles only make you stronger. Great material success and authority await your perseverance.",
       descHn:"Aap me Shani ki immense power hai. Mushkilein aapko aur strong banati hain. Aapki perseverance ka inaam bada material success aur authority hai.",
       descHi:"आप शनि की अपार शक्ति धारण करते हैं। बाधाएँ आपको और मज़बूत बनाती हैं। आपके धैर्य का पुरस्कार महान भौतिक सफलता और प्रभुत्व है।",
       career:"Business, Banking, Politics, Administration, Law",
       careerHn:"Business, Banking, Politics, Administration, Law",
       careerHi:"व्यवसाय, बैंकिंग, राजनीति, प्रशासन, क़ानून",
       love:"You are an intense, protective partner — loyalty is your non-negotiable.",
       loveHn:"Aap intense, protective partner ho — loyalty aapke liye non-negotiable hai.",
       loveHi:"आप तीव्र, रक्षात्मक साथी हैं — वफ़ादारी आपके लिए अनिवार्य है।",
       strength:"Determination, Resilience", strengthHn:"Determination, Resilience", strengthHi:"दृढ़ संकल्प, लचीलापन",
       weakness:"Materialism, Control issues", weaknessHn:"Materialism, Control issues", weaknessHi:"भौतिकवाद, नियंत्रण की समस्या",
       remedy:"Light a mustard-oil lamp on Saturdays. Donate black sesame to Lord Shani.",
       remedyHn:"Shanivar ko sarson ke tel ka deep jalayein. Bhagwan Shani ko kale til chadhayein.",
       remedyHi:"शनिवार को सरसों के तेल का दीप जलाएँ। भगवान शनि को काले तिल अर्पित करें।" },
  9: { title:"Compassion & Service", titleHindi:"करुणा और सेवा", planet:"Mangal", planetEmoji:"♂️",
       color:"#ef4444", luckyNums:"9, 18, 27", luckyColor:"Red / Crimson", luckyColorHex:"#ef4444",
       traits:["Courageous","Humanitarian","Passionate","Idealistic"],
       traitsHindi:["साहसी","मानवतावादी","जोशीला","आदर्शवादी"],
       desc:"You are the warrior with a golden heart — courageous in battle, compassionate in service. You fight fearlessly for truth and justice.",
       descHn:"Aap ek warrior ho sone jaise dil ke saath — yudh me bahadur, seva me karuna. Aap satya aur nyaay ke liye nirbhay ho ladte ho.",
       descHi:"आप स्वर्ण हृदय वाले योद्धा हैं — युद्ध में साहसी, सेवा में करुणामय। आप सत्य और न्याय के लिए निर्भय होकर लड़ते हैं।",
       career:"Medicine, Law, Military, Social Service, Spiritual Leadership",
       careerHn:"Medicine, Law, Military, Social Service, Spiritual Leadership",
       careerHi:"चिकित्सा, क़ानून, सेना, समाज सेवा, आध्यात्मिक नेतृत्व",
       love:"You love with fierce intensity and devotion. Your partner feels truly protected.",
       loveHn:"Aap fierce intensity aur devotion se pyaar karte ho. Aapka partner sach me protected feel karta hai.",
       loveHi:"आप तीव्र भावना और समर्पण से प्रेम करते हैं। आपके साथी को सच्ची सुरक्षा का अनुभव होता है।",
       strength:"Courage, Generosity", strengthHn:"Courage, Generosity", strengthHi:"साहस, उदारता",
       weakness:"Impulsiveness, Short temper", weaknessHn:"Impulsive nature, Short temper", weaknessHi:"उतावलापन, अल्प क्रोध",
       remedy:"Worship Lord Hanuman on Tuesdays. Donate red lentils and jaggery.",
       remedyHn:"Mangalvar ko Bhagwan Hanuman ki puja karein. Laal masoor aur gud daan karein.",
       remedyHi:"मंगलवार को भगवान हनुमान की पूजा करें। लाल मसूर और गुड़ का दान करें।" },
  11: { title:"Illumination", titleHindi:"प्रकाश", planet:"Chandra + Surya", planetEmoji:"✨",
        color:"#fbbf24", luckyNums:"11, 29, 2", luckyColor:"Silver / Gold", luckyColorHex:"#fbbf24",
        traits:["Intuitive","Inspirational","Visionary","Highly Sensitive"],
        traitsHindi:["अंतर्ज्ञानी","प्रेरणादायक","दूरदर्शी","संवेदनशील"],
        desc:"You carry the Master Number 11 — a vibration of divine illumination. You are a spiritual messenger born to uplift and inspire all of humanity.",
        descHn:"Aap me Master Number 11 hai — divya prakaash ka vibration. Aap ek spiritual messenger ho jo manavta ko uplift aur inspire karne ke liye paida hua hai.",
        descHi:"आप मास्टर अंक 11 धारण करते हैं — दिव्य प्रकाश का स्पंदन। आप एक आध्यात्मिक संदेशवाहक हैं, जो सम्पूर्ण मानवता को उन्नत और प्रेरित करने हेतु जन्मे हैं।",
        career:"Spiritual Leadership, Art, Healing, Counseling, Visionary Work",
        careerHn:"Spiritual Leadership, Art, Healing, Counseling, Visionary Work",
        careerHi:"आध्यात्मिक नेतृत्व, कला, उपचार, परामर्श, दूरदर्शी कार्य",
        love:"You seek a soul-level connection — deep, spiritual, and transformative.",
        loveHn:"Aap soul-level connection chahte ho — deep, spiritual, aur transformative.",
        loveHi:"आप आत्मा-स्तर का संबंध चाहते हैं — गहरा, आध्यात्मिक और परिवर्तनकारी।",
        strength:"Intuition, Inspiration", strengthHn:"Intuition, Inspiration", strengthHi:"अंतर्ज्ञान, प्रेरणा",
        weakness:"Anxiety, Over-idealism", weaknessHn:"Anxiety, Over-idealism", weaknessHi:"चिंता, अति-आदर्शवाद",
        remedy:"Meditate at sunrise every day. Chant 'Om Namah Shivaya' 108 times.",
        remedyHn:"Roz suryoday par meditation karein. 'Om Namah Shivaya' 108 baar jaap karein.",
        remedyHi:"प्रतिदिन सूर्योदय के समय ध्यान करें। 108 बार 'ॐ नमः शिवाय' का जाप करें।" },
  22: { title:"Master Builder", titleHindi:"महान निर्माता", planet:"Shani + Surya", planetEmoji:"🌍",
        color:"#a78bfa", luckyNums:"22, 4", luckyColor:"Deep Blue / Gold", luckyColorHex:"#a78bfa",
        traits:["Visionary","Disciplined","Powerful","Practical"],
        traitsHindi:["दूरदर्शी","अनुशासित","शक्तिशाली","व्यावहारिक"],
        desc:"You carry Master Number 22 — the most powerful of all numbers. You can bridge the spiritual and material to manifest extraordinary realities.",
        descHn:"Aap me Master Number 22 hai — saare numbers me sabse powerful. Aap spiritual aur material ko jod kar extraordinary realities manifest kar sakte ho.",
        descHi:"आप मास्टर अंक 22 धारण करते हैं — सभी अंकों में सबसे शक्तिशाली। आप आध्यात्मिक और भौतिक को जोड़कर असाधारण वास्तविकताएँ साकार कर सकते हैं।",
        career:"Architecture, Global Business, Politics, Large-scale Philanthropy",
        careerHn:"Architecture, Global Business, Politics, Large-scale Philanthropy",
        careerHi:"वास्तुकला, वैश्विक व्यवसाय, राजनीति, बड़े पैमाने का परोपकार",
        love:"You are a dedicated, visionary partner building a lasting legacy together.",
        loveHn:"Aap ek dedicated, visionary partner ho jo saath milkar lasting legacy banate ho.",
        loveHi:"आप समर्पित, दूरदर्शी साथी हैं जो साथ मिलकर दीर्घस्थायी विरासत बनाते हैं।",
        strength:"Vision, Execution", strengthHn:"Vision, Execution", strengthHi:"दूरदृष्टि, क्रियान्वयन",
        weakness:"Perfectionism, Overwhelm", weaknessHn:"Perfectionism, Overwhelm", weaknessHi:"पूर्णतावाद, अति-बोझ",
        remedy:"Practice deep meditation daily. Donate to orphanages on Saturdays.",
        remedyHn:"Roz deep meditation karein. Shanivar ko anaath aashram me daan karein.",
        remedyHi:"प्रतिदिन गहन ध्यान करें। शनिवार को अनाथालय में दान करें।" },
  33: { title:"Master Teacher", titleHindi:"महान गुरु", planet:"Guru + Shukra", planetEmoji:"💫",
        color:"#34d399", luckyNums:"33, 6", luckyColor:"Gold / Pink", luckyColorHex:"#34d399",
        traits:["Selfless","Nurturing","Creative","Enlightened"],
        traitsHindi:["निस्वार्थ","पालन-पोषण करने वाला","रचनात्मक","प्रबुद्ध"],
        desc:"You carry Master Number 33 — the purest vibration of divine love and healing. You are a rare teacher destined to uplift all of humanity.",
        descHn:"Aap me Master Number 33 hai — divya prem aur healing ka purest vibration. Aap ek rare teacher ho jo manavta ko uplift karne ke liye chuna gaya hai.",
        descHi:"आप मास्टर अंक 33 धारण करते हैं — दिव्य प्रेम और उपचार का शुद्धतम स्पंदन। आप एक दुर्लभ गुरु हैं जो समस्त मानवता को उन्नत करने के लिए नियुक्त हैं।",
        career:"Healing Arts, Spiritual Teaching, Creative Leadership, Service",
        careerHn:"Healing Arts, Spiritual Teaching, Creative Leadership, Service",
        careerHi:"उपचार कला, आध्यात्मिक शिक्षण, रचनात्मक नेतृत्व, सेवा",
        love:"You love unconditionally, serving your partner and family with pure devotion.",
        loveHn:"Aap unconditionally pyaar karte ho, apne partner aur parivaar ki shuddh devotion se seva karte ho.",
        loveHi:"आप बिना शर्त प्रेम करते हैं और शुद्ध समर्पण से अपने साथी और परिवार की सेवा करते हैं।",
        strength:"Unconditional Love, Wisdom", strengthHn:"Unconditional Love, Wisdom", strengthHi:"बिना शर्त प्रेम, ज्ञान",
        weakness:"Martyrdom, Self-neglect", weaknessHn:"Khud ko bhulna, Self-neglect", weaknessHi:"बलिदान-वृत्ति, आत्म-उपेक्षा",
        remedy:"Serve the underprivileged selflessly every week. Light a ghee lamp daily.",
        remedyHn:"Har hafte zaroortmandon ki nishkaam seva karein. Roz ghee ka deep jalayein.",
        remedyHi:"प्रति सप्ताह वंचितों की निष्काम सेवा करें। प्रतिदिन घी का दीप जलाएँ।" },
};

function getInfo(n: number): NumInfo {
  return NUM[n] ?? NUM[9];
}

function pickCareer(info: NumInfo, vlang: string): string {
  if (vlang === "hi") return info.careerHi || info.career;
  if (vlang === "hn") return info.careerHn || info.career;
  return info.career;
}

const BASIC_ACCENT = "#8b5cf6";
const PRO_ACCENT = "#f59e0b";

function PremiumOrb({ color }: { color: string }) {
  const pulse = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 1, duration: 2400, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 0, duration: 2400, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ]),
    );
    loop.start();
    return () => loop.stop();
  }, [pulse]);
  const scale = pulse.interpolate({ inputRange: [0, 1], outputRange: [1, 1.15] });
  const opacity = pulse.interpolate({ inputRange: [0, 1], outputRange: [0.28, 0.55] });
  return (
    <Animated.View
      pointerEvents="none"
      style={[ui.orb, { backgroundColor: color, transform: [{ scale }], opacity }]}
    />
  );
}

// ── Number badge component ─────────────────────────────────────────────────────
function NumberBadge({ num, color, size = 68 }: { num: number; color: string; size?: number }) {
  return (
    <View style={[nb.wrap, { width: size, height: size, borderRadius: size / 2,
      backgroundColor: `${color}18`, borderColor: `${color}45`, borderWidth: 2 }]}>
      <Text style={[nb.num, { color, fontSize: size * (num > 9 ? 0.30 : 0.40) }]}>{num}</Text>
    </View>
  );
}
const nb = StyleSheet.create({
  wrap: { alignItems:"center", justifyContent:"center", flexShrink:0 },
  num:  { fontFamily: F.extra },
});

// ── Free numerology card ───────────────────────────────────────────────────────
function NumCard({
  label, labelHindi, num, expanded, onToggle, delay = 0,
}: { label: string; labelHindi: string; num: number; expanded: boolean; onToggle: () => void; delay?: number }) {
  const C    = useC();
  const t    = useT();
  const info = getInfo(num);

  return (
    <FadeInView delay={delay}>
    <Pressable
      onPress={onToggle}
      style={({ pressed }) => [
        nc.card,
        {
          backgroundColor: C.bgCard,
          borderColor: `${info.color}45`,
          transform: [{ scale: pressed ? 0.99 : 1 }],
        },
      ]}
    >
      <LinearGradient
        colors={[`${info.color}12`, "transparent"]}
        style={StyleSheet.absoluteFill}
        pointerEvents="none"
      />
      {/* Top row */}
      <View style={nc.topRow}>
        <NumberBadge num={num} color={info.color} />
        <View style={{ flex:1 }}>
          <Text style={[nc.tag, { color: C.textDim }]}>{label}</Text>
          {labelHindi && labelHindi !== label && (
            <Text style={[nc.tagHindi, { color: C.textMuted }]}>{labelHindi}</Text>
          )}
          <Text style={[nc.titleTxt, { color: info.color }]}>{t.vlang === "hi" ? info.titleHindi : info.title}</Text>
          <View style={nc.planetRow}>
            <Text style={{ fontSize:12 }}>{info.planetEmoji}</Text>
            <Text style={[nc.planetTxt, { color: C.textMuted }]}>{info.planet}</Text>
          </View>
        </View>
        <Feather name={expanded ? "chevron-up" : "chevron-down"} size={16} color={C.textMuted} />
      </View>

      {/* Traits + details — expanded only */}
      {expanded && (
        <>
          <View style={nc.traits}>
            {info.traits.map((tr, i) => (
              <View key={tr} style={[nc.chip, { backgroundColor:`${info.color}12`, borderColor:`${info.color}28` }]}>
                <Text style={[nc.chipTxt, { color:info.color }]}>{t.vlang === "hi" ? (info.traitsHindi[i] || tr) : tr}</Text>
                {t.vlang !== "hi" && t.vlang !== "en" && info.traitsHindi[i] && (
                  <Text style={[nc.chipHindi, { color:info.color }]}> · {info.traitsHindi[i]}</Text>
                )}
              </View>
            ))}
          </View>

          <View style={nc.quickRow}>
            <View style={[nc.quickPill, { backgroundColor: "rgba(34,197,94,0.10)", borderColor: "rgba(34,197,94,0.25)" }]}>
              <Text style={[nc.quickLabel, { color: C.textDim }]}>{t.numStrength}</Text>
              <Text style={[nc.quickVal, { color: "#22c55e" }]}>
                {t.vlang === "hi" ? (info.strengthHi || info.strength) : t.vlang === "hn" ? (info.strengthHn || info.strength) : info.strength}
              </Text>
            </View>
            <View style={[nc.quickPill, { backgroundColor: "rgba(248,113,113,0.08)", borderColor: "rgba(248,113,113,0.22)" }]}>
              <Text style={[nc.quickLabel, { color: C.textDim }]}>{t.numWeakness}</Text>
              <Text style={[nc.quickVal, { color: "#f87171" }]}>
                {t.vlang === "hi" ? (info.weaknessHi || info.weakness) : t.vlang === "hn" ? (info.weaknessHn || info.weakness) : info.weakness}
              </Text>
            </View>
          </View>

          <LockedCareerRow career={pickCareer(info, t.vlang)} accent={info.color} />
        </>
      )}
    </Pressable>
    </FadeInView>
  );
}
const nc = StyleSheet.create({
  card:       { borderRadius:18, borderWidth:1.5, padding:16, gap:10, overflow:"hidden" },
  topRow:     { flexDirection:"row", alignItems:"flex-start", gap:12 },
  tag:        { fontSize:9, fontFamily:F.bold, letterSpacing:0.8, textTransform:"uppercase", marginBottom:1 },
  tagHindi:   { fontSize:9, fontFamily:F.medium, marginBottom:3 },
  titleTxt:   { fontSize:14, fontFamily:F.extra, letterSpacing:-0.2, marginBottom:2 },
  planetRow:  { flexDirection:"row", alignItems:"center", gap:4 },
  planetTxt:  { fontSize:11, fontFamily:F.medium },
  traits:     { flexDirection:"row", flexWrap:"wrap", gap:6 },
  chip:       { flexDirection:"row", paddingHorizontal:8, paddingVertical:4, borderRadius:8, borderWidth:1 },
  chipTxt:    { fontSize:10.5, fontFamily:F.bold },
  chipHindi:  { fontSize:10, fontFamily:F.medium },
  quickRow:   { flexDirection:"row", gap:10 },
  quickPill:  { flex:1, borderRadius:12, borderWidth:1, padding:12, gap:4 },
  quickLabel: { fontSize:9, fontFamily:F.extra, letterSpacing:1.1, textTransform:"uppercase" },
  quickVal:   { fontSize:12, lineHeight:18, fontFamily:F.semi },
  lockWrap:   { marginTop:2, borderRadius:12, borderWidth:1, overflow:"hidden", minHeight:52 },
  lockLabel:  { fontSize:9, fontFamily:F.extra, letterSpacing:1, textTransform:"uppercase", marginBottom:6 },
  lockText:   { fontSize:12, lineHeight:18, fontFamily:F.medium },
  lockOverlay:{ ...StyleSheet.absoluteFillObject, alignItems:"center", justifyContent:"center" },
});

function LockedCareerRow({ career, accent }: { career: string; accent: string }) {
  const C = useC();
  const t = useT();
  return (
    <View style={[nc.lockWrap, { borderColor: `${accent}30`, backgroundColor: C.isDark ? "rgba(255,255,255,0.03)" : "rgba(0,0,0,0.02)" }]}>
      <View style={{ padding:12 }}>
        <Text style={[nc.lockLabel, { color: C.textDim }]}>{t.numCareer}</Text>
        <Text style={[nc.lockText, { color: C.textMuted }]} numberOfLines={2}>{career}</Text>
      </View>
      {Platform.OS !== "web" ? (
        <BlurView intensity={28} tint={C.isDark ? "dark" : "light"} style={StyleSheet.absoluteFill} />
      ) : (
        <View style={[StyleSheet.absoluteFill, { backgroundColor: C.isDark ? "rgba(15,23,42,0.55)" : "rgba(248,250,252,0.72)" }]} />
      )}
      <View style={nc.lockOverlay}>
        <Feather name="lock" size={16} color={accent} />
      </View>
    </View>
  );
}

// ── Personal year mini card ───────────────────────────────────────────────────
function PersonalYearCard({ py, pm }: { py: number; pm: number }) {
  const C    = useC();
  const t    = useT();
  const info = getInfo(py);
  const pmInfo = getInfo(pm);
  const year = new Date().getFullYear();
  const month = new Date().toLocaleString("default", { month:"long" });

  return (
    <FadeInView delay={staggerDelay(4)}>
    <View style={[pyc.card, { backgroundColor: C.bgCard, borderColor: `${info.color}40`, overflow: "hidden" }]}>
      <LinearGradient colors={[`${info.color}10`, "transparent"]} style={StyleSheet.absoluteFill} pointerEvents="none" />
      <Text style={[pyc.title, { color: C.textDim }]}>{t.numPersonalYM}</Text>
      <View style={pyc.row}>
        <View style={[pyc.box, { borderColor:`${info.color}30`, backgroundColor:`${info.color}08` }]}>
          <Text style={[pyc.bigNum, { color: info.color }]}>{py}</Text>
          <Text style={[pyc.label, { color: C.textMuted }]}>{t.numYearPrefix} {year}</Text>
          <Text style={[pyc.theme, { color: C.textMuted }]}>{getPYTheme(t.lang, py)}</Text>
        </View>
        <View style={[pyc.box, { borderColor:`${pmInfo.color}30`, backgroundColor:`${pmInfo.color}08` }]}>
          <Text style={[pyc.bigNum, { color: pmInfo.color }]}>{pm}</Text>
          <Text style={[pyc.label, { color: C.textMuted }]}>{month}</Text>
          <Text style={[pyc.theme, { color: C.textMuted }]}>{getPYTheme(t.lang, pm)}</Text>
        </View>
      </View>
    </View>
    </FadeInView>
  );
}
const pyc = StyleSheet.create({
  card:   { borderRadius:18, borderWidth:1, padding:16, gap:10 },
  title:  { fontSize:9, fontFamily:F.extra, letterSpacing:1.1, textTransform:"uppercase" },
  row:    { flexDirection:"row", gap:10 },
  box:    { flex:1, borderRadius:12, borderWidth:1, padding:12, gap:4, alignItems:"center" },
  bigNum: { fontSize:36, fontFamily:F.extra },
  label:  { fontSize:10, fontFamily:F.bold },
  theme:  { fontSize:11, lineHeight:16, textAlign:"center", fontFamily:F.medium },
});

function CoreNumbersSummary({ items }: { items: { num: number; label: string }[] }) {
  const C = useC();
  const t = useT();
  return (
    <View style={[cs.card, { backgroundColor: C.bgCard, borderColor: `${BASIC_ACCENT}35`, overflow: "hidden" }]}>
      <LinearGradient colors={[`${BASIC_ACCENT}10`, "transparent"]} style={StyleSheet.absoluteFill} pointerEvents="none" />
      <Text style={[cs.title, { color: C.textDim }]}>{t.numCoreSummary}</Text>
      <View style={cs.row}>
        {items.map(item => {
          const info = getInfo(item.num);
          return (
            <View key={item.label} style={[cs.item, { borderColor: `${info.color}35`, backgroundColor: `${info.color}08` }]}>
              <Text style={[cs.num, { color: info.color }]}>{item.num}</Text>
              <Text style={[cs.lbl, { color: C.textMuted }]} numberOfLines={2}>{item.label}</Text>
            </View>
          );
        })}
      </View>
    </View>
  );
}
const cs = StyleSheet.create({
  card:  { borderRadius:18, borderWidth:1, padding:14, gap:10 },
  title: { fontSize:9, fontFamily:F.extra, letterSpacing:1.1, textTransform:"uppercase" },
  row:   { flexDirection:"row", gap:8 },
  item:  { flex:1, borderRadius:12, borderWidth:1, paddingVertical:10, paddingHorizontal:6, alignItems:"center", gap:4 },
  num:   { fontSize:22, fontFamily:F.extra },
  lbl:   { fontSize:8.5, fontFamily:F.bold, textAlign:"center", letterSpacing:0.2, textTransform:"uppercase" },
});

function BasicProCompare() {
  const C = useC();
  const t = useT();
  return (
    <View style={[bc.card, { backgroundColor: C.bgCard, borderColor: `${BASIC_ACCENT}30`, overflow: "hidden" }]}>
      <LinearGradient colors={[`${PRO_ACCENT}08`, "transparent"]} style={StyleSheet.absoluteFill} pointerEvents="none" />
      <Text style={[bc.title, { color: C.textDim }]}>{t.numBasicCompareTitle}</Text>
      <View style={bc.row}>
        <View style={[bc.col, { borderColor: C.border, backgroundColor: C.bgCard2 }]}>
          <Text style={[bc.colHead, { color: C.text }]}>{t.km_basic}</Text>
          <Text style={[bc.line, { color: C.textMuted }]}>{t.numBasicCompareBasicLine}</Text>
        </View>
        <View style={[bc.col, { borderColor: "rgba(245,158,11,0.35)", backgroundColor: "rgba(245,158,11,0.08)" }]}>
          <Text style={[bc.colHead, { color: "#f59e0b" }]}>{t.vu_tabPro}</Text>
          <Text style={[bc.line, { color: C.textMuted }]}>{t.numBasicCompareProLine}</Text>
        </View>
      </View>
    </View>
  );
}
const bc = StyleSheet.create({
  card:    { borderRadius:18, borderWidth:1, padding:14, gap:10 },
  title:   { fontSize:9, fontFamily:F.extra, letterSpacing:1.1, textTransform:"uppercase" },
  row:     { flexDirection:"row", gap:8 },
  col:     { flex:1, borderRadius:12, borderWidth:1, padding:12, gap:6 },
  colHead: { fontSize:13, fontFamily:F.extra },
  line:    { fontSize:11, lineHeight:16, fontFamily:F.medium },
});

function BasicProTease({ onOpenPro }: { onOpenPro: () => void }) {
  const C = useC();
  const t = useT();
  const price = LIFE_MASTERY_UI_PRICING.offerInr;
  return (
    <View style={{ gap:10 }}>
      <Text style={[bp.hint, { color: C.isDark ? "rgba(203,213,225,0.55)" : "rgba(100,116,139,0.75)" }]}>
        {t.numBasicLockedHint}
      </Text>
      <Pressable
        onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); onOpenPro(); }}
        style={({ pressed }) => ({ opacity: pressed ? 0.9 : 1 })}
      >
        <LinearGradient colors={["#d97706", "#f59e0b", "#fbbf24"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={bp.tease}>
          <Feather name="file-text" size={16} color="#fff" />
          <Text style={bp.teaseTxt}>{t.numProTeaseBtn} — ₹{price}</Text>
          <Feather name="chevron-right" size={16} color="#fff" />
        </LinearGradient>
      </Pressable>
      <Text style={[bp.foot, { color: C.textDim }]}>{t.numFooterNote}</Text>
    </View>
  );
}
const bp = StyleSheet.create({
  hint:    { fontSize:11.5, fontFamily:F.medium, lineHeight:17, textAlign:"center", paddingHorizontal:8 },
  tease:   { flexDirection:"row", alignItems:"center", justifyContent:"center", gap:8, paddingVertical:15, paddingHorizontal:14, borderRadius:16 },
  teaseTxt:{ flex:1, flexShrink:1, color:"#fff", fontSize:12.5, fontFamily:F.bold, textAlign:"center", lineHeight:17 },
  foot:    { fontSize:11, lineHeight:17, fontFamily:F.medium, textAlign:"center", paddingHorizontal:4 },
});

// ── Profile selector ──────────────────────────────────────────────────────────
function ProfileSelector({
  profiles, activeId, onSelect,
}: { profiles: ProfileEntry[]; activeId: string | null; onSelect: (id: string) => void }) {
  const C = useC();
  if (profiles.length <= 1) return null;
  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginHorizontal:-16 }}
      contentContainerStyle={{ paddingHorizontal:16, gap:8, flexDirection:"row" }}>
      {profiles.map(p => {
        const active = p.id === activeId;
        return (
          <Pressable key={p.id} onPress={() => { onSelect(p.id); Haptics.selectionAsync(); }}
            style={[ps.chip, { borderColor: active ? C.accent : C.border,
              backgroundColor: active ? `${C.accent}12` : C.bgCard2 }]}>
            <Text style={[ps.name, { color: active ? C.accent : C.textMuted }]}>{p.name}</Text>
            {p.relation && <Text style={[ps.rel, { color: C.textDim }]}>{p.relation}</Text>}
          </Pressable>
        );
      })}
    </ScrollView>
  );
}
const ps = StyleSheet.create({
  chip: { paddingHorizontal:12, paddingVertical:7, borderRadius:12, borderWidth:1.5, gap:1 },
  name: { fontSize:12, fontWeight:"700" },
  rel:  { fontSize:9 },
});

// ── PRO Report Panel ──────────────────────────────────────────────────────────
function ProReportPanel({ profile }: { profile: ProfileEntry }) {
  const C = useC();
  const t = useT();
  const { user } = useUser();
  const bd = profile.birthData;

  const [opening, setOpening] = useState(false);
  const [founderExpanded, setFounderExpanded] = useState(false);
  const [langOpen, setLangOpen] = useState(false);
  const [priorityDelivery, setPriorityDelivery] = useState(false);
  const [pdfLang, setPdfLang] = useState<"en" | "hn" | "hi">(
    (t.lang || "en").toLowerCase() === "hi"
      ? "hi"
      : ((t.lang || "en").toLowerCase() === "hn" ? "hn" : "en"),
  );

  // Pro+ Tools inputs
  const [mobile, setMobile] = useState("");
  const [err, setErr]         = useState<string | null>(null);

  const dobStr = bd
    ? `${bd.year}-${String(bd.month).padStart(2, "0")}-${String(bd.day).padStart(2, "0")}`
    : "";
  const tobStr = bd && bd.hour != null && bd.minute != null
    ? `${String(bd.hour).padStart(2, "0")}:${String(bd.minute).padStart(2, "0")}`
    : "12:00";

  // Download PDF in-app and offer Share sheet (works around localtunnel
  // interstitial that breaks Linking.openURL in Safari).
  const downloadAndShare = async (url: string, fileName: string) => {
    setErr(null);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setOpening(true);
    try {
      // ── Web (workspace iframe / browser) — FileSystem APIs unavailable.
      // Fetch as blob then trigger a download via anchor click. Falls back to
      // a new-tab open if blob fetch fails (e.g. CORS).
      if (Platform.OS === "web") {
        try {
          const r = await fetch(url, { headers: { "bypass-tunnel-reminder": "true" } });
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          const blob = await r.blob();
          const blobUrl = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = blobUrl;
          a.download = fileName;
          a.target = "_blank";
          a.rel = "noopener";
          document.body.appendChild(a);
          a.click();
          a.remove();
          setTimeout(() => URL.revokeObjectURL(blobUrl), 30_000);
        } catch {
          // Last-resort fallback: open URL in a new tab so the browser handles it.
          if (typeof window !== "undefined") window.open(url, "_blank", "noopener");
        }
        return;
      }

      // ── Native (iOS / Android) — download then Share sheet.
      const dest = `${FileSystem.cacheDirectory}${fileName}`;
      const res = await FileSystem.downloadAsync(url, dest, {
        headers: { "bypass-tunnel-reminder": "true" },
      });
      if (res.status !== 200) {
        throw new Error(`Server returned HTTP ${res.status}`);
      }
      // Auto-save into the local "My Reports" registry (silent).
      try {
        await saveLocalReport({
          kind: "numerology",
          title: fileName.replace(/\.pdf$/i, "").replace(/_/g, " "),
          subtitle: `Numerology Pro · ${new Date().toLocaleDateString()}`,
          sourceUri: res.uri,
          remoteUrl: url,
        });
      } catch { /* ignore */ }

      const canShare = await Sharing.isAvailableAsync();
      if (canShare) {
        await Sharing.shareAsync(res.uri, {
          mimeType: "application/pdf",
          dialogTitle: fileName,
          UTI: "com.adobe.pdf",
        });
      } else {
        // Fallback: open URL directly
        await Linking.openURL(url);
      }
    } catch (e: any) {
      setErr(`PDF download fail hua: ${e?.message || "unknown error"}. Internet check kare aur dobara try kare.`);
    } finally {
      setOpening(false);
    }
  };

  const openTools = async (langCode: "en" | "hn" | "hi") => {
    setErr(null);
    if (!bd) {
      setErr("Pehle Profile screen me Name aur Date of Birth bhar dijiye, phir wapas aaiye.");
      return;
    }
    if (!mobile.trim()) {
      setErr("Apna mobile number dijiye — PDF generate karne ke liye zaroori hai.");
      return;
    }
    const params = new URLSearchParams({
      name: bd.name, dob: dobStr,
      lang: langCode,
      ...(tobStr  ? { tob: tobStr } : {}),
      mobile: mobile.trim(),
      // ── Birth-place context for Tier 4 (doshas) + Tier 5 (compatibility) ──
      ...(typeof bd.lat === "number" ? { lat: String(bd.lat) } : {}),
      ...(typeof bd.lon === "number" ? { lon: String(bd.lon) } : {}),
      ...(typeof bd.tz  === "number" ? { tz:  String(bd.tz)  } : {}),
      ...(bd.place ? { place: bd.place } : {}),
    });
    const safeName = bd.name.replace(/[^a-zA-Z0-9]+/g, "_");
    await downloadAndShare(
      `${API_BASE}/api/numerology/pdf_pro?${params.toString()}`,
      `Numerology_Tools_${safeName}.pdf`,
    );
  };

  useEffect(() => {
    if (consumeNumerologyPaidReady()) {
      void openTools(pdfLang);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const startUnlock = () => {
    setErr(null);
    if (!bd) {
      setErr("Pehle Profile screen me Name aur Date of Birth bhar dijiye, phir wapas aaiye.");
      return;
    }
    if (!mobile.trim()) {
      setErr("Apna mobile number dijiye — PDF generate karne ke liye zaroori hai.");
      return;
    }
    setLangOpen(true);
  };

  const confirmUnlock = async () => {
    setLangOpen(false);
    const entitlementParams: Record<string, unknown> = {
      name: bd?.name,
      dob: dobStr,
      tob: tobStr || "12:00",
      mobile: mobile.trim(),
      ...(typeof bd?.lat === "number" ? { lat: bd.lat } : {}),
      ...(typeof bd?.lon === "number" ? { lon: bd.lon } : {}),
      ...(typeof bd?.tz  === "number" ? { tz:  bd.tz } : {}),
      ...(bd?.place ? { place: bd.place } : {}),
    };

    if (LIFE_MASTERY_CHECKOUT_CONFIG.bypassCheckoutForTesting) {
      await openTools(pdfLang);
      return;
    }

    await gateNumerologyReportAfterLangPick({
      user,
      params: entitlementParams,
      lang: pdfLang,
      label: "Numerology Pro Report",
      amountInr: lifeMasteryOrderTotalInr(priorityDelivery),
      bypassCheckout: false,
      onEntitled: () => {
        void openTools(pdfLang);
      },
    });
  };

  const toolSections = [
    { icon: "⭐", title: t.nm_wi1Title,  sub: t.nm_wi1Sub },
    { icon: "🌟", title: t.nm_wi2Title,  sub: t.nm_wi2Sub },
    { icon: "💼", title: t.nm_wi3Title,  sub: t.nm_wi3Sub },
    { icon: "🔤", title: t.nm_wi11Title, sub: t.nm_wi11Sub },
    { icon: "🍀", title: "Lucky Numbers & Colour", sub: "Personal lucky digits, colours and best days to act." },
    { icon: "📱", title: "Phone Number Numerology", sub: "Mobile digit vibration — support, blocks and simple fixes." },
  ];

  const answer3 = [
    "What is my core number pattern (Life Path / Destiny / Soul) and what it means?",
    "Which numbers amplify money/career outcomes and which create blocks?",
    "Which mobile number vibration is supportive for me right now?",
  ];

  const cardBg = C.isDark ? "rgba(255,255,255,0.04)" : "rgba(255,255,255,0.92)";
  const border = C.isDark ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.08)";
  const titleColor = C.isDark ? "#f8fafc" : "#0f172a";
  const bodyColor = C.isDark ? "rgba(226,232,240,0.72)" : "#64748b";

  return (
    <View style={{ gap: 12 }}>
      <FadeInView delay={0} resetKey="pro-hero">
      <View style={[np.heroCard, { borderColor: C.isDark ? "rgba(124,58,237,0.5)" : "rgba(124,58,237,0.35)" }]}>
        <LinearGradient
          colors={C.isDark ? ["rgba(124,58,237,0.22)", "rgba(99,102,241,0.14)"] : ["rgba(124,58,237,0.1)", "rgba(99,102,241,0.06)"]}
          style={StyleSheet.absoluteFill}
        />
        <Text style={np.heroEmoji}>🔢</Text>
        <View style={{ flex: 1, gap: 2 }}>
          <Text style={[np.heroTitle, { color: titleColor }]}>Numerology Pro Report</Text>
          <Text style={[np.heroLine, { color: bodyColor }]} numberOfLines={2}>
            #1 reason people order — clear money & career direction from your numbers.
          </Text>
        </View>
      </View>
      </FadeInView>

      <FadeInView delay={staggerDelay(1)}>
      <View style={[np.card, { backgroundColor: cardBg, borderColor: border }]}>
        <Pressable
          onPress={() => { setFounderExpanded(v => !v); Haptics.selectionAsync(); }}
          style={np.founderHead}
        >
          {FOUNDER_PROFILE.photoUri ? (
            <View style={[np.founderPhoto, { backgroundColor: "rgba(124,58,237,0.18)" }]} />
          ) : (
            <LinearGradient colors={["#6366f1", "#7c3aed"]} style={np.founderPhoto}>
              <Text style={np.founderInitials}>{FOUNDER_PROFILE.initials}</Text>
            </LinearGradient>
          )}
          <View style={{ flex: 1, gap: 2 }}>
            <Text style={[np.founderName, { color: titleColor }]}>{FOUNDER_PROFILE.displayName}</Text>
            <Text style={[np.founderRole, { color: bodyColor }]} numberOfLines={founderExpanded ? 3 : 1}>
              {founderExpanded ? FOUNDER_PROFILE.roleLine : "Personally prepared & reviewed"}
            </Text>
          </View>
          <Feather name={founderExpanded ? "chevron-up" : "chevron-down"} size={18} color={C.isDark ? "#a78bfa" : "#7c3aed"} />
        </Pressable>
        <View style={np.founderChipRow}>
          {["Founder-reviewed", "Saved in My Reports", "Secure payment"].map(b => (
            <View key={b} style={[np.founderBulletChip, { borderColor: border }]}>
              <Feather name="check" size={10} color="#22c55e" />
              <Text style={[np.founderBulletTxt, { color: titleColor }]} numberOfLines={1}>{b}</Text>
            </View>
          ))}
        </View>
      </View>
      </FadeInView>

      <FadeInView delay={staggerDelay(2)}>
      <View style={[np.card, { backgroundColor: cardBg, borderColor: border }]}>
        <Text style={[np.sectionTitle, { color: titleColor }]}>Your Report Answers These 3 Questions</Text>
        <View style={np.coreQChipRow}>
          {answer3.map((q, i) => (
            <View key={q} style={[np.coreQChip, { borderColor: border }]}>
              <Text style={[np.coreQChipNum, { color: C.isDark ? "#a78bfa" : "#7c3aed" }]}>{i + 1}</Text>
              <Text style={[np.coreQChipTxt, { color: titleColor }]} numberOfLines={1}>{q}</Text>
            </View>
          ))}
        </View>
      </View>
      </FadeInView>

      <FadeInView delay={staggerDelay(3)}>
      <View style={[np.card, { backgroundColor: cardBg, borderColor: border }]}>
        <Text style={[np.sectionTitle, { color: titleColor }]}>What's Inside Your Report</Text>
        <Text style={[np.reportSummary, { color: bodyColor }]}>{toolSections.length} things</Text>
        <View style={np.reportChipRow}>
          {toolSections.map(sec => (
            <View key={sec.title} style={[np.reportChip, { borderColor: border }]}>
              <Text style={np.reportChipEmoji}>{sec.icon}</Text>
              <Text style={[np.reportChipTxt, { color: titleColor }]}>{sec.title}</Text>
            </View>
          ))}
        </View>
      </View>
      </FadeInView>

      <FadeInView delay={staggerDelay(4)}>
      <View style={[np.card, { backgroundColor: cardBg, borderColor: border }]}>
        <Text style={[np.sectionTitle, { color: titleColor }]}>Standard Delivery</Text>
        <Text style={[np.deliveryStandardLine, { color: bodyColor }]} numberOfLines={1}>
          📁 My Reports · within 24 hours · ₹{LIFE_MASTERY_UI_PRICING.offerInr}
        </Text>
        <Pressable
          onPress={() => { setPriorityDelivery(!priorityDelivery); Haptics.selectionAsync(); }}
          style={[
            np.deliveryPriorityRow,
            {
              borderColor: priorityDelivery ? (C.isDark ? "#f59e0b" : "#d97706") : border,
              backgroundColor: priorityDelivery ? (C.isDark ? "rgba(245,158,11,0.08)" : "rgba(245,158,11,0.06)") : "transparent",
            },
          ]}
        >
          <View style={[np.priorityCheck, { borderColor: priorityDelivery ? "#f59e0b" : border, backgroundColor: priorityDelivery ? "#f59e0b" : "transparent" }]}>
            {priorityDelivery ? <Feather name="check" size={10} color="#fff" /> : null}
          </View>
          <Text style={[np.deliveryPriorityTxt, { color: titleColor }]} numberOfLines={1}>
            ⚡ Priority +₹{LIFE_MASTERY_PRIORITY_SURCHARGE_INR} · within 12 hours
          </Text>
        </Pressable>
        <View style={[np.priceDivider, { backgroundColor: border }]} />
        <Text style={[np.priceInline, { color: titleColor }]}>
          <Text style={[np.priceStrikeTiny, { color: bodyColor }]}>₹{LIFE_MASTERY_UI_PRICING.originalInr}</Text>
          <Text style={np.priceArrow}> → </Text>
          <Text style={np.priceTotalTiny}>₹{lifeMasteryOrderTotalInr(priorityDelivery)}</Text>
        </Text>
      </View>
      </FadeInView>

      <FadeInView delay={staggerDelay(5)}>
      <View style={[np.card, { backgroundColor: cardBg, borderColor: border }]}>
        <Text style={[np.sectionTitle, { color: titleColor }]}>Your numbers</Text>
        <Text style={[np.reportSummary, { color: bodyColor }]}>Mobile number required for your PDF report.</Text>
        <View style={{ gap: 10, marginTop: 10 }}>
          <View style={pp.inputBlock}>
            <Text style={[pp.inputLabel, { color: C.textDim }]}>📱 Mobile Number</Text>
            <TextInput
              value={mobile}
              onChangeText={setMobile}
              placeholder="9876543210"
              placeholderTextColor={C.textMuted}
              keyboardType="phone-pad"
              maxLength={15}
              style={[pp.input, { backgroundColor: C.bgCard, borderColor: C.border, color: C.text }]}
            />
          </View>
        </View>
        {err ? (
          <View style={[pp.errBox, { marginTop: 12 }]}>
            <Feather name="alert-circle" size={14} color="#dc2626" />
            <Text style={pp.errTxt}>{err}</Text>
          </View>
        ) : null}
      </View>
      </FadeInView>

      <Text style={[np.trustBar, { color: bodyColor }]}>🔒 Secure Payment • Founder Reviewed • Delivered in My Reports</Text>

      <Pressable
        onPress={startUnlock}
        disabled={opening}
        style={({ pressed }) => [{
          borderRadius: 14,
          backgroundColor: "#7c3aed",
          paddingVertical: 14,
          paddingHorizontal: 16,
          alignItems: "center",
          opacity: pressed || opening ? 0.85 : 1,
        }]}
      >
        <Text style={{ color: "#fff", fontSize: 14, fontFamily: "Nunito_800ExtraBold", textAlign: "center" }}>
          {opening ? "Opening…" : "Get My Report"}
        </Text>
      </Pressable>

          <Modal transparent visible={langOpen} animationType="fade" onRequestClose={() => setLangOpen(false)}>
            <View style={{
              flex: 1,
              backgroundColor: "rgba(0,0,0,0.55)",
              alignItems: "center",
              justifyContent: "center",
              padding: 18,
            }}>
              <View style={{
                width: "100%",
                maxWidth: 420,
                backgroundColor: C.bgCard,
                borderColor: C.border,
                borderWidth: 1,
                borderRadius: 16,
                padding: 14,
                gap: 10,
              }}>
                <Text style={{ color: C.text, fontWeight: "900", fontSize: 16 }}>
                  Choose PDF Language
                </Text>
                <View style={{ flexDirection: "row", gap: 10 }}>
                  {([
                    { id: "en", label: "English" },
                    { id: "hn", label: "Hinglish" },
                    { id: "hi", label: "Hindi" },
                  ] as const).map(opt => {
                    const active = pdfLang === opt.id;
                    return (
                      <Pressable
                        key={opt.id}
                        onPress={() => { setPdfLang(opt.id); Haptics.selectionAsync(); }}
                        style={{
                          flex: 1,
                          paddingVertical: 10,
                          borderRadius: 12,
                          borderWidth: 1.5,
                          borderColor: active ? "#7c3aed" : C.border,
                          backgroundColor: active ? "rgba(124,58,237,0.12)" : C.bgCard2,
                          alignItems: "center",
                        }}
                      >
                        <Text style={{ color: active ? "#7c3aed" : C.textMuted, fontWeight: "800", fontSize: 12 }}>
                          {opt.label}
                        </Text>
                      </Pressable>
                    );
                  })}
                </View>
                <View style={{ flexDirection: "row", gap: 10, marginTop: 6 }}>
                  <Pressable
                    onPress={() => setLangOpen(false)}
                    style={{
                      flex: 1,
                      paddingVertical: 11,
                      borderRadius: 12,
                      borderWidth: 1,
                      borderColor: C.border,
                      backgroundColor: C.bgCard2,
                      alignItems: "center",
                    }}
                  >
                    <Text style={{ color: C.textMid, fontWeight: "800" }}>Cancel</Text>
                  </Pressable>
                  <Pressable
                    onPress={() => { void confirmUnlock(); }}
                    style={{
                      flex: 1,
                      paddingVertical: 11,
                      borderRadius: 12,
                      backgroundColor: "#7c3aed",
                      alignItems: "center",
                    }}
                  >
                    <Text style={{ color: "#fff", fontWeight: "900" }}>Continue</Text>
                  </Pressable>
                </View>
                <Text style={{ color: C.textMuted, fontSize: 11, lineHeight: 16 }}>
                  Payment ke baad isi screen pe wapas aake download ho jayega.
                </Text>
              </View>
            </View>
          </Modal>
    </View>
  );
}
const pp = StyleSheet.create({
  hero:        { borderRadius: 16, borderWidth: 1.5, padding: 16 },
  heroRow:     { flexDirection: "row", alignItems: "center", gap: 14 },
  heroIcon:    { width: 56, height: 56, borderRadius: 16, alignItems: "center", justifyContent: "center" },
  tagRow:      { flexDirection: "row", gap: 6, marginBottom: 4 },
  tag:         { paddingHorizontal: 7, paddingVertical: 2, borderRadius: 6 },
  tagTxt:      { fontSize: 9, fontWeight: "900", color: "#fff", letterSpacing: 1 },
  heroTitle:   { fontSize: 16, fontWeight: "800" },
  heroSub:     { fontSize: 11, marginTop: 2 },
  sectionLabel:{ fontSize: 9, fontWeight: "800", letterSpacing: 2, marginTop: 4, marginBottom: -4 },
  row:         { flexDirection: "row", alignItems: "center", gap: 12, padding: 12, borderRadius: 12, borderWidth: 1 },
  rowTitle:    { fontSize: 13, fontWeight: "800" },
  rowSub:      { fontSize: 11, marginTop: 1, lineHeight: 15 },
  cta:         {
                 borderRadius: 16, overflow: "hidden", backgroundColor: "#f59e0b",
                 shadowColor: "#f59e0b", shadowOffset: { width: 0, height: 6 },
                 shadowOpacity: 0.4, shadowRadius: 12, elevation: 10,
                 alignItems: "center",
               },
  ctaInner:    { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 10, paddingTop: 16, paddingHorizontal: 16, paddingBottom: 4 },
  ctaTxt:      { color: "#fff", fontSize: 15, fontWeight: "900" },
  ctaPrice:    { color: "rgba(255,255,255,0.92)", fontSize: 13, fontWeight: "800", paddingBottom: 14 },
  note:        { borderRadius: 12, borderWidth: 1, padding: 12, flexDirection: "row", alignItems: "flex-start", gap: 8 },
  noteTxt:     { fontSize: 11, lineHeight: 16, flex: 1 },
  subTabBar:   { flexDirection: "row", padding: 4, borderRadius: 14, borderWidth: 1, gap: 4 },
  subTabBtn:   { flex: 1, flexDirection: "row", alignItems: "center", gap: 8,
                 paddingVertical: 10, paddingHorizontal: 10, borderRadius: 10 },
  subTabTitle: { fontSize: 12, fontWeight: "900" },
  subTabSub:   { fontSize: 10, marginTop: 1, fontWeight: "700" },
  inputBlock:  { gap: 6 },
  inputLabel:  { fontSize: 10, fontWeight: "800", letterSpacing: 1.2 },
  input:       { borderWidth: 1, borderRadius: 12, paddingHorizontal: 14,
                 paddingVertical: 12, fontSize: 15, fontWeight: "700",
                 letterSpacing: 0.5 },
  errBox:      { flexDirection: "row", alignItems: "center", gap: 6,
                 backgroundColor: "rgba(220,38,38,0.1)", borderRadius: 10,
                 padding: 10, borderWidth: 1, borderColor: "rgba(220,38,38,0.3)" },
  errTxt:      { fontSize: 12, color: "#dc2626", fontWeight: "700", flex: 1 },
  founderAvatarWrap: { width: 44, height: 44, borderRadius: 22, borderWidth: 1.5, alignItems: "center", justifyContent: "center", overflow: "hidden", marginTop: 2 },
  founderAvatar: { width: 40, height: 40, borderRadius: 20, alignItems: "center", justifyContent: "center" },
  founderAvatarTxt: { color: "#fff", fontSize: 12, fontWeight: "900" },
  expandBtn: { width: 34, height: 34, borderRadius: 10, borderWidth: 1, alignItems: "center", justifyContent: "center", marginTop: 2 },
  chip: { flexDirection: "row", alignItems: "center", gap: 5, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 10, borderWidth: 1, maxWidth: "90%" },
  chipTxt: { fontSize: 10, fontWeight: "800", flexShrink: 1 },
  answerRow: { flexDirection: "row", alignItems: "center", gap: 10, paddingVertical: 9, paddingHorizontal: 10, borderRadius: 12, borderWidth: 1 },
  answerNum: { width: 18, textAlign: "center", fontWeight: "900" },
  answerTxt: { flex: 1, fontSize: 12, fontWeight: "800" },
  priorityRow: { width: "100%", flexDirection: "row", alignItems: "center", gap: 8, marginTop: 10, paddingVertical: 9, paddingHorizontal: 10, borderRadius: 12, borderWidth: 1 },
  priorityCheck: { width: 16, height: 16, borderRadius: 4, borderWidth: 1.5, alignItems: "center", justifyContent: "center" },
  priorityTxt: { flex: 1, fontSize: 12, fontWeight: "800" },
  priceDivider: { width: "100%", height: 1, marginTop: 12, marginBottom: 8 },
  priceInline: { fontSize: 12, lineHeight: 17 },
  priceStrikeTiny: { fontSize: 12, fontWeight: "700", textDecorationLine: "line-through" },
  priceArrow: { fontSize: 12, fontWeight: "600", color: "rgba(148,163,184,0.9)" },
  priceTotalTiny: { fontSize: 14, fontWeight: "900" },
});

// Numerology Pro purchase styles (copied from MarriageCompatProPurchase layout)
const np = StyleSheet.create({
  card: { borderRadius: 18, borderWidth: 1, padding: 16 },
  founderHead: { flexDirection: "row", alignItems: "center", gap: 10 },
  founderPhoto: { width: 40, height: 40, borderRadius: 20, alignItems: "center", justifyContent: "center", overflow: "hidden" },
  founderInitials: { color: "#fff", fontSize: 13, fontFamily: "Nunito_800ExtraBold" },
  founderName: { fontSize: 13.5, fontFamily: "Nunito_800ExtraBold" },
  founderRole: { fontSize: 11, fontFamily: "Nunito_500Medium", lineHeight: 15 },
  founderChipRow: { flexDirection: "row", flexWrap: "wrap", gap: 6, marginTop: 8 },
  founderBulletChip: { flexDirection: "row", alignItems: "center", gap: 4, paddingVertical: 4, paddingHorizontal: 8, borderRadius: 8, borderWidth: 1, maxWidth: "48%", flexGrow: 1 },
  founderBulletTxt: { fontSize: 10, fontFamily: "Nunito_700Bold", flexShrink: 1 },
  heroCard: { flexDirection: "row", alignItems: "center", gap: 8, paddingVertical: 10, paddingHorizontal: 12, borderRadius: 14, borderWidth: 1, overflow: "hidden" },
  heroEmoji: { fontSize: 22 },
  heroTitle: { fontSize: 14.5, fontFamily: "Nunito_800ExtraBold", lineHeight: 19 },
  heroLine: { fontSize: 11.5, fontFamily: "Nunito_500Medium", lineHeight: 16 },
  sectionTitle: { fontSize: 15, fontFamily: "Nunito_800ExtraBold", letterSpacing: -0.2 },
  coreQChipRow: { gap: 6, marginTop: 10 },
  coreQChip: { flexDirection: "row", alignItems: "center", gap: 8, paddingVertical: 7, paddingHorizontal: 10, borderRadius: 9, borderWidth: 1 },
  coreQChipNum: { fontSize: 11, fontFamily: "Nunito_800ExtraBold", width: 14 },
  coreQChipTxt: { flex: 1, fontSize: 12, fontFamily: "Nunito_700Bold" },
  reportSummary: { fontSize: 11, fontFamily: "Nunito_500Medium", marginTop: 2 },
  reportChipRow: { gap: 6, marginTop: 10 },
  reportChip: { flexDirection: "row", alignItems: "center", gap: 6, paddingVertical: 8, paddingHorizontal: 10, borderRadius: 8, borderWidth: 1, width: "100%" },
  reportChipEmoji: { fontSize: 12 },
  reportChipTxt: { flex: 1, fontSize: 11, fontFamily: "Nunito_700Bold", lineHeight: 15 },
  deliveryStandardLine: { fontSize: 11.5, fontFamily: "Nunito_500Medium", marginTop: 6 },
  deliveryPriorityRow: { flexDirection: "row", alignItems: "center", gap: 7, marginTop: 6, paddingVertical: 7, paddingHorizontal: 9, borderRadius: 9, borderWidth: 1 },
  deliveryPriorityTxt: { flex: 1, fontSize: 11, fontFamily: "Nunito_700Bold" },
  priorityCheck: { width: 16, height: 16, borderRadius: 4, borderWidth: 1.5, alignItems: "center", justifyContent: "center" },
  priceDivider: { height: 1, marginTop: 10, marginBottom: 8 },
  priceInline: { fontSize: 12, lineHeight: 17 },
  priceStrikeTiny: { fontSize: 12, fontFamily: "Nunito_600SemiBold", textDecorationLine: "line-through" },
  priceArrow: { fontSize: 12, fontFamily: "Nunito_500Medium", color: "rgba(148,163,184,0.9)" },
  priceTotalTiny: { fontSize: 14, fontFamily: "Nunito_800ExtraBold" },
  trustBar: { fontSize: 11, fontFamily: "Nunito_600SemiBold", textAlign: "center", lineHeight: 16, paddingHorizontal: 4 },
});

// ── Main Screen ───────────────────────────────────────────────────────────────
export default function NumerologyScreen() {
  const C       = useC();
  const t       = useT();
  const insets  = useSafeAreaInsets();
  const { profiles, primaryProfileId, setPrimaryProfile } = useUser();
  const topPad  = Platform.OS === "web" ? 67 : insets.top;
  const botPad  = Platform.OS === "web" ? 34 : insets.bottom;

  // Local selected profile (for this screen; defaults to primary)
  const [selectedId, setSelectedId] = useState<string | null>(primaryProfileId);
  useEffect(() => { setSelectedId(primaryProfileId); }, [primaryProfileId]);

  const profile = profiles.find(p => p.id === selectedId) ?? profiles[0] ?? null;
  const bd      = profile?.birthData ?? null;

  // Expanded cards (compact basic: keep collapsed by default)
  const [expLP,   setExpLP]   = useState(false);
  const [expBD,   setExpBD]   = useState(false);
  const [expDest, setExpDest] = useState(false);
  const [expSoul, setExpSoul] = useState(false);

  // Pattern A — Free / PRO Report tab
  const [tab, setTab] = useState<"free" | "pro">("free");

  // All calculations — instant, no API call
  const nums = useMemo(() => {
    if (!bd) return null;
    const lp   = calcLifePath(bd.day, bd.month, bd.year);
    const bdNum = calcBirthDay(bd.day);
    const dest = calcDestiny(bd.name);
    const soul = calcSoulUrge(bd.name);
    const pers = calcPersonality(bd.name);
    const mat  = calcMaturity(lp, dest);
    const py   = calcPersonalYear(bd.day, bd.month);
    const pm   = calcPersonalMonth(bd.day, bd.month);
    return { lp, bdNum, dest, soul, pers, mat, py, pm };
  }, [bd]);

  // Format DOB for display
  const dobStr = bd
    ? `${String(bd.day).padStart(2,"0")} / ${String(bd.month).padStart(2,"0")} / ${bd.year}`
    : null;

  const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  const dobFull = bd
    ? `${bd.day} ${MONTHS[bd.month - 1]} ${bd.year}`
    : null;

  const accent = tab === "free" ? BASIC_ACCENT : PRO_ACCENT;

  return (
    <View style={[s.root, { backgroundColor: C.bg }]}>
      <View style={StyleSheet.absoluteFill} pointerEvents="none">
        <LinearGradient colors={[`${accent}14`, C.bg, C.bg]} style={StyleSheet.absoluteFill} />
        <PremiumOrb color={accent} />
      </View>

      <LinearGradient
        colors={[`${accent}24`, `${accent}08`, "transparent"]}
        style={[s.header, { paddingTop: topPad + 8, borderBottomColor: `${accent}22` }]}
      >
        <Pressable onPress={() => router.back()} style={({ pressed }) => [ui.glassBtn, { opacity: pressed ? 0.75 : 1 }]}>
          <Feather name="arrow-left" size={20} color={C.textMuted} />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={[ui.headerBadge, { color: accent }]}>
            {tab === "free" ? "NUMEROLOGY BASIC" : "NUMEROLOGY PRO"}
          </Text>
          <Text style={[s.title, { color: C.text }]}>{t.numerologyTitle}</Text>
          <Text style={[s.sub, { color: C.textMuted }]}>{t.numSubtitle}</Text>
        </View>
        <View style={{ width: 40 }} />
      </LinearGradient>

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={[s.content, { paddingBottom: botPad + 40 }]}
      >
        {!bd && (
          <FadeInView delay={0}>
          <View style={[ui.emptyPremium, { backgroundColor: C.bgCard, borderColor: `${BASIC_ACCENT}35` }]}>
            <View style={[ui.heroIconRing, { backgroundColor: `${BASIC_ACCENT}22`, borderColor: `${BASIC_ACCENT}55` }]}>
              <Text style={{ fontSize: 28 }}>🔢</Text>
            </View>
            <Text style={[s.emptyTitle, { color: C.text }]}>{t.numNoProfileTitle}</Text>
            <Text style={[s.emptyBody, { color: C.textMuted }]}>
              {t.numNoProfileBody}
            </Text>
            <Pressable
              onPress={() => router.push("/profile-edit" as any)}
              style={({ pressed }) => ({ opacity: pressed ? 0.9 : 1, width: "100%" })}
            >
              <LinearGradient colors={[BASIC_ACCENT, `${BASIC_ACCENT}BB`]} style={ui.emptyBtnGrad}>
                <Text style={s.emptyBtnTxt}>{t.numSetupProfile}</Text>
              </LinearGradient>
            </Pressable>
          </View>
          </FadeInView>
        )}

        {bd && (
          <FadeInView delay={staggerDelay(1)} resetKey={tab}>
          <View style={[ui.tabBarPremium, { backgroundColor: C.bgCard2, borderColor: `${accent}33` }]}>
            {([
              { key: "free" as const, icon: "hash" as const, label: t.km_basic, tabAccent: BASIC_ACCENT },
              { key: "pro" as const, icon: "file-text" as const, label: t.vu_tabPro, tabAccent: PRO_ACCENT },
            ]).map((m) => {
              const sel = tab === m.key;
              return (
                <Pressable
                  key={m.key}
                  onPress={() => { setTab(m.key); Haptics.selectionAsync(); }}
                  style={({ pressed }) => [
                    ui.tabBtnPremium,
                    {
                      borderColor: sel ? m.tabAccent : "transparent",
                      transform: [{ scale: pressed ? 0.98 : 1 }],
                    },
                  ]}
                >
                  {sel ? (
                    <LinearGradient
                      colors={[m.tabAccent, `${m.tabAccent}CC`]}
                      style={StyleSheet.absoluteFill}
                      start={{ x: 0, y: 0 }}
                      end={{ x: 1, y: 0 }}
                    />
                  ) : null}
                  <Feather name={m.icon} size={13} color={sel ? "#fff" : C.textMuted} />
                  <Text style={[s.tabTxt, { color: sel ? "#fff" : C.textMuted }]}>{m.label}</Text>
                </Pressable>
              );
            })}
          </View>
          </FadeInView>
        )}

        {bd && tab === "pro" && (
          <ProReportPanel profile={profile!} />
        )}

        {nums && tab === "free" && (
          <>
            <FadeInView delay={staggerDelay(2)} resetKey="basic">
              <View style={[ui.priceRibbon, { borderColor: `${BASIC_ACCENT}44`, backgroundColor: `${BASIC_ACCENT}12`, marginBottom: 4 }]}>
                <Feather name="hash" size={14} color={BASIC_ACCENT} />
                <View style={{ flex: 1 }}>
                  <Text style={[ui.priceRibbonText, { color: C.text }]}>{t.numFreeSection}</Text>
                  {profile?.name ? (
                    <Text style={{ color: C.textMuted, fontSize: 10, marginTop: 2 }}>
                      {t.numProfileFor.replace("{name}", profile.name)}
                    </Text>
                  ) : null}
                </View>
              </View>
            </FadeInView>

            <FadeInView delay={staggerDelay(3)}>
            <CoreNumbersSummary
              items={[
                { num: nums.lp,     label: t.numLifePathHi },
                { num: nums.bdNum,  label: t.numBirthDayHi },
                { num: nums.dest,   label: t.numDestinyHi },
                { num: nums.soul,   label: t.numSoulUrgeHi },
              ]}
            />
            </FadeInView>

            <PersonalYearCard py={nums.py} pm={nums.pm} />

            <NumCard
              label={t.numLifePathLbl} labelHindi={t.numLifePathHi}
              num={nums.lp} expanded={expLP}
              onToggle={() => { setExpLP(v => !v); Haptics.selectionAsync(); }}
              delay={staggerDelay(3)}
            />
            <NumCard
              label={t.numBirthDayLbl} labelHindi={t.numBirthDayHi}
              num={nums.bdNum} expanded={expBD}
              onToggle={() => { setExpBD(v => !v); Haptics.selectionAsync(); }}
              delay={staggerDelay(4)}
            />
            <NumCard
              label={t.numDestinyLbl} labelHindi={t.numDestinyHi}
              num={nums.dest} expanded={expDest}
              onToggle={() => { setExpDest(v => !v); Haptics.selectionAsync(); }}
              delay={staggerDelay(5)}
            />
            <NumCard
              label={t.numSoulUrgeLbl} labelHindi={t.numSoulUrgeHi}
              num={nums.soul} expanded={expSoul}
              onToggle={() => { setExpSoul(v => !v); Haptics.selectionAsync(); }}
              delay={staggerDelay(6)}
            />

            <FadeInView delay={staggerDelay(7)}>
              <BasicProCompare />
            </FadeInView>
            <FadeInView delay={staggerDelay(8)}>
              <BasicProTease onOpenPro={() => { setTab("pro"); Haptics.selectionAsync(); }} />
            </FadeInView>
          </>
        )}
      </ScrollView>
    </View>
  );
}

const s = StyleSheet.create({
  root:        { flex:1 },
  header:      { flexDirection:"row", alignItems:"center", gap:12, paddingHorizontal:16, paddingBottom:14, borderBottomWidth:1 },
  back:        { width:36, height:36, alignItems:"center", justifyContent:"center" },
  title:       { fontSize:17, fontFamily:F.bold, letterSpacing:-0.2 },
  sub:         { fontSize:11, fontFamily:F.medium, marginTop:1, letterSpacing:0.1 },
  content:     { paddingHorizontal:16, gap:12, paddingTop:14 },
  sectionLabel:{ fontSize:9, fontFamily:F.extra, letterSpacing:1.1, textTransform:"uppercase", marginBottom:-4 },
  sectionSub:  { fontSize:11, fontFamily:F.medium, marginTop:-8 },
  profileCtx:  { fontSize:12, fontFamily:F.medium, marginTop:-6, marginBottom:2 },

  emptyCard:   { borderRadius:18, borderWidth:1, padding:24, alignItems:"center", gap:14 },
  emptyTitle:  { fontSize:16, fontFamily:F.extra, textAlign:"center" },
  emptyBody:   { fontSize:13, fontFamily:F.medium, lineHeight:20, textAlign:"center" },
  emptyBtn:    { paddingHorizontal:24, paddingVertical:12, borderRadius:14 },
  emptyBtnTxt: { color:"#fff", fontSize:14, fontFamily:F.extra },

  profileCard: { borderRadius:14, borderWidth:1, padding:14 },
  profileRow:  { flexDirection:"row", alignItems:"center", gap:12 },
  avatar:      { width:48, height:48, borderRadius:16, borderWidth:1.5, alignItems:"center", justifyContent:"center", flexShrink:0 },
  profileName: { fontSize:15, fontWeight:"800" },
  profileDob:  { fontSize:12, marginTop:2 },
  profilePlace:{ fontSize:11, marginTop:1 },
  syncBadge:   { flexDirection:"row", alignItems:"center", gap:4, paddingHorizontal:7, paddingVertical:3, borderRadius:8 },
  syncTxt:     { fontSize:9, fontWeight:"700" },

  divider:     { flexDirection:"row", alignItems:"center", gap:10, borderTopWidth:0 },
  divLine:     { flex:1, height:1 },
  divBadge:    { flexDirection:"row", alignItems:"center", gap:5, paddingHorizontal:10, paddingVertical:4, borderRadius:12, borderWidth:1 },
  divTxt:      { fontSize:9, fontWeight:"800", letterSpacing:1 },

  teaserCard:  { borderRadius:16, borderWidth:1, padding:16, flexDirection:"row", alignItems:"flex-start", gap:12 },
  teaserTitle: { fontSize:14, fontWeight:"800" },
  teaserBody:  { fontSize:12, lineHeight:18 },

  ctaBtn: {
    borderRadius:18, overflow:"hidden",
    backgroundColor:"#f59e0b",
    shadowColor:"#f59e0b", shadowOffset:{ width:0, height:6 },
    shadowOpacity:0.4, shadowRadius:12, elevation:10,
  },
  ctaInner:  { flexDirection:"row", alignItems:"center", gap:12, padding:18 },
  ctaTitle:  { color:"#fff", fontSize:15, fontWeight:"900" },
  ctaSub:    { color:"rgba(255,255,255,0.8)", fontSize:11, marginTop:2 },

  footer:    { borderRadius:12, borderWidth:1, padding:12, flexDirection:"row", alignItems:"flex-start", gap:8 },
  footerTxt: { fontSize:11, lineHeight:17, flex:1 },

  tabBar:    { flexDirection:"row", padding:4, borderRadius:14, borderWidth:1, gap:4 },
  tabBtn:    { flex:1, flexDirection:"row", alignItems:"center", justifyContent:"center",
               gap:6, paddingVertical:10, borderRadius:10 },
  tabTxt:    { fontSize:12, fontFamily:F.extra, letterSpacing:0.3 },
});

const ui = StyleSheet.create({
  orb: {
    position: "absolute",
    top: -50,
    right: -30,
    width: 200,
    height: 200,
    borderRadius: 100,
  },
  glassBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(255,255,255,0.08)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.12)",
  },
  headerBadge: {
    fontSize: 10,
    fontFamily: F.extra,
    letterSpacing: 2,
    marginBottom: 2,
  },
  heroIconRing: {
    width: 52,
    height: 52,
    borderRadius: 26,
    borderWidth: 1.5,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 10,
  },
  emptyPremium: {
    borderRadius: 20,
    borderWidth: 1,
    padding: 24,
    alignItems: "center",
    gap: 12,
    overflow: "hidden",
  },
  emptyBtnGrad: {
    paddingHorizontal: 24,
    paddingVertical: 14,
    borderRadius: 14,
    alignItems: "center",
    width: "100%",
  },
  tabBarPremium: {
    flexDirection: "row",
    padding: 5,
    borderRadius: 16,
    borderWidth: 1,
    gap: 6,
    marginBottom: 4,
  },
  tabBtnPremium: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    paddingVertical: 12,
    borderRadius: 12,
    borderWidth: 1.5,
    overflow: "hidden",
  },
  priceRibbon: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 14,
    borderWidth: 1,
  },
  priceRibbonText: { fontSize: 12, fontFamily: F.bold },
});
