import { Feather } from "@expo/vector-icons";
import * as FileSystem from "expo-file-system/legacy";
import * as Haptics from "expo-haptics";
import * as Linking from "expo-linking";
import { router } from "expo-router";
import * as Sharing from "expo-sharing";
import React, { useEffect, useMemo, useState } from "react";
import { API_BASE } from "@/lib/apiConfig";
import {
  Platform, Pressable, ScrollView, StyleSheet,
  Text, TextInput, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useC } from "@/context/ThemeContext";
import { useUser, type ProfileEntry } from "@/context/UserContext";
import { useT } from "@/hooks/useT";

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

const PY_THEME: Record<number, { en: string; hn: string; hi: string }> = {
  1:  { en:"New beginnings — a 9-year cycle begins. Plant the seeds of your dreams.",
        hn:"Nayi shuruaat — 9 saal ka cycle shuru. Apne sapnon ke beej boyein.",
        hi:"नई शुरुआत — 9 वर्ष का चक्र शुरू। अपने सपनों के बीज बोएँ।" },
  2:  { en:"Partnerships and patience. Let relationships deepen and blossom.",
        hn:"Saajhedari aur sabr. Rishton ko gehraai aur khilne ka mauka dein.",
        hi:"साझेदारी और धैर्य। रिश्तों को गहराई से खिलने दें।" },
  3:  { en:"Creativity, joy, and expression — let your inner light shine brightly.",
        hn:"Rachnatmakta, khushi, abhivyakti — apni andar ki roshni chamkayein.",
        hi:"रचनात्मकता, आनंद और अभिव्यक्ति — अपनी आंतरिक ज्योति चमकाएँ।" },
  4:  { en:"Hard work and foundation-building. Discipline is your greatest asset.",
        hn:"Mehnat aur neev banane ka samay. Anushashan aapki sabse badi taakat hai.",
        hi:"परिश्रम और आधार-निर्माण। अनुशासन आपकी सबसे बड़ी संपत्ति है।" },
  5:  { en:"Change, freedom, and travel. Embrace the unexpected with open arms.",
        hn:"Badlaav, azaadi, aur safar. Achanak hone wale ko khule dil se apnayein.",
        hi:"परिवर्तन, स्वतंत्रता और यात्रा। अप्रत्याशित को खुले मन से अपनाएँ।" },
  6:  { en:"Family, love, and responsibility. Nurture yourself and those around you.",
        hn:"Parivaar, prem, aur zimmedari. Khud ki aur apno ki dekhbhal karein.",
        hi:"परिवार, प्रेम और ज़िम्मेदारी। स्वयं की और अपनों की देखभाल करें।" },
  7:  { en:"Reflection, spirituality, and inner work. Seek deeper truth within.",
        hn:"Manan, adhyatma, aur antar manthan. Andar ki sachai khojein.",
        hi:"मनन, आध्यात्म और अंतर्मंथन। भीतर की गहरी सच्चाई खोजें।" },
  8:  { en:"Power, ambition, and finance. Your efforts will finally be rewarded.",
        hn:"Shakti, mahatvakaaksha, aur paisa. Aapki mehnat ka phal milega.",
        hi:"शक्ति, महत्वाकांक्षा और धन। आपकी मेहनत का फल मिलेगा।" },
  9:  { en:"Completion and release. Close old chapters; a new cycle approaches.",
        hn:"Samaapti aur mukti. Purane adhyay band karein; naya cycle aa raha hai.",
        hi:"समापन और मुक्ति। पुराने अध्याय बंद करें; नया चक्र आ रहा है।" },
  11: { en:"Spiritual awakening. Divine guidance is speaking — are you listening?",
        hn:"Adhyatmic jaagran. Divya margdarshan bol raha hai — sun rahe ho?",
        hi:"आध्यात्मिक जागरण। दिव्य मार्गदर्शन बोल रहा है — क्या आप सुन रहे हैं?" },
  22: { en:"Master year of manifestation. Think big. Build something legendary.",
        hn:"Manifestation ka master varsh. Bada socho. Kuch legendary banao.",
        hi:"साक्षात्कार का महावर्ष। बड़ा सोचें। कुछ अद्वितीय बनाएँ।" },
  33: { en:"Year of deep love and teaching. Serve humanity with your full heart.",
        hn:"Gehre prem aur shikshan ka varsh. Pure dil se manavata ki seva karein.",
        hi:"गहरे प्रेम और शिक्षण का वर्ष। पूरे मन से मानवता की सेवा करें।" },
};

function getInfo(n: number): NumInfo {
  return NUM[n] ?? NUM[9];
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
  num:  { fontWeight:"900" },
});

// ── Free numerology card ───────────────────────────────────────────────────────
function NumCard({
  label, labelHindi, num, expanded, onToggle,
}: { label: string; labelHindi: string; num: number; expanded: boolean; onToggle: () => void }) {
  const C    = useC();
  const t    = useT();
  const info = getInfo(num);

  return (
    <Pressable
      onPress={onToggle}
      style={[nc.card, { backgroundColor: C.bgCard, borderColor: `${info.color}35` }]}
    >
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

      {/* Traits */}
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

      {/* Description always visible */}
      <Text style={[nc.desc, { color: C.textMuted }]}>{t.vlang === "hi" ? (info.descHi || info.desc) : t.vlang === "hn" ? (info.descHn || info.desc) : info.desc}</Text>

      {/* Expanded detail */}
      {expanded && (
        <View style={{ gap:10, marginTop:4 }}>
          <View style={[nc.detailBlock, { borderColor: C.border }]}>
            <Text style={[nc.detailLabel, { color: C.textDim }]}>{t.numCareer}</Text>
            <Text style={[nc.detailVal, { color: C.textMid }]}>{t.vlang === "hi" ? (info.careerHi || info.career) : t.vlang === "hn" ? (info.careerHn || info.career) : info.career}</Text>
          </View>
          <View style={[nc.detailBlock, { borderColor: C.border }]}>
            <Text style={[nc.detailLabel, { color: C.textDim }]}>{t.numLove}</Text>
            <Text style={[nc.detailVal, { color: C.textMid }]}>{t.vlang === "hi" ? (info.loveHi || info.love) : t.vlang === "hn" ? (info.loveHn || info.love) : info.love}</Text>
          </View>
          <View style={[nc.detailBlock, { borderColor: C.border }]}>
            <Text style={[nc.detailLabel, { color: C.textDim }]}>{t.numStrength}</Text>
            <Text style={[nc.detailVal, { color: "#22c55e" }]}>{t.vlang === "hi" ? (info.strengthHi || info.strength) : t.vlang === "hn" ? (info.strengthHn || info.strength) : info.strength}</Text>
          </View>
          <View style={[nc.detailBlock, { borderColor: C.border }]}>
            <Text style={[nc.detailLabel, { color: C.textDim }]}>{t.numWeakness}</Text>
            <Text style={[nc.detailVal, { color: "#f87171" }]}>{t.vlang === "hi" ? (info.weaknessHi || info.weakness) : t.vlang === "hn" ? (info.weaknessHn || info.weakness) : info.weakness}</Text>
          </View>
          <View style={[nc.detailBlock, { borderColor: C.border, backgroundColor:`${info.color}06` }]}>
            <Text style={[nc.detailLabel, { color: info.color }]}>{t.numRemedy}</Text>
            <Text style={[nc.detailVal, { color: C.textMid }]}>{t.vlang === "hi" ? (info.remedyHi || info.remedy) : t.vlang === "hn" ? (info.remedyHn || info.remedy) : info.remedy}</Text>
          </View>
          <View style={nc.luckyRow}>
            <View style={[nc.luckyPill, { backgroundColor:`${info.color}12` }]}>
              <Text style={[nc.luckyLabel, { color: C.textDim }]}>{t.numLuckyNumbers}</Text>
              <Text style={[nc.luckyVal, { color: info.color }]}>{info.luckyNums}</Text>
            </View>
            <View style={[nc.luckyPill, { backgroundColor:`${info.luckyColorHex}12` }]}>
              <View style={[nc.colorDot, { backgroundColor: info.luckyColorHex }]} />
              <View>
                <Text style={[nc.luckyLabel, { color: C.textDim }]}>{t.numLuckyColor}</Text>
                <Text style={[nc.luckyVal, { color: info.color }]}>{info.luckyColor}</Text>
              </View>
            </View>
          </View>
        </View>
      )}
    </Pressable>
  );
}
const nc = StyleSheet.create({
  card:       { borderRadius:16, borderWidth:1.5, padding:16, gap:10 },
  topRow:     { flexDirection:"row", alignItems:"flex-start", gap:12 },
  tag:        { fontSize:9, fontWeight:"800", letterSpacing:1.8, marginBottom:1 },
  tagHindi:   { fontSize:9, marginBottom:3 },
  titleTxt:   { fontSize:15, fontWeight:"800", marginBottom:2 },
  planetRow:  { flexDirection:"row", alignItems:"center", gap:4 },
  planetTxt:  { fontSize:11 },
  traits:     { flexDirection:"row", flexWrap:"wrap", gap:6 },
  chip:       { flexDirection:"row", paddingHorizontal:8, paddingVertical:4, borderRadius:8, borderWidth:1 },
  chipTxt:    { fontSize:10, fontWeight:"700" },
  chipHindi:  { fontSize:10 },
  desc:       { fontSize:12, lineHeight:19 },
  detailBlock:{ borderTopWidth:1, paddingTop:8, gap:2 },
  detailLabel:{ fontSize:9, fontWeight:"800", letterSpacing:1.2 },
  detailVal:  { fontSize:12, lineHeight:19 },
  luckyRow:   { flexDirection:"row", gap:10 },
  luckyPill:  { flex:1, flexDirection:"row", alignItems:"center", gap:8, padding:10, borderRadius:12 },
  colorDot:   { width:14, height:14, borderRadius:7 },
  luckyLabel: { fontSize:9, fontWeight:"700", letterSpacing:0.8 },
  luckyVal:   { fontSize:12, fontWeight:"700", marginTop:1 },
});

// ── Personal year mini card ───────────────────────────────────────────────────
function PersonalYearCard({ py, pm }: { py: number; pm: number }) {
  const C    = useC();
  const t    = useT();
  const info = getInfo(py);
  const pmInfo = getInfo(pm);
  const year = new Date().getFullYear();
  const month = new Date().toLocaleString("default", { month:"long" });

  return (
    <View style={[pyc.card, { backgroundColor: C.bgCard, borderColor: `${info.color}30` }]}>
      <Text style={[pyc.title, { color: C.textDim }]}>{t.numPersonalYM}</Text>
      <View style={pyc.row}>
        <View style={[pyc.box, { borderColor:`${info.color}30`, backgroundColor:`${info.color}08` }]}>
          <Text style={[pyc.bigNum, { color: info.color }]}>{py}</Text>
          <Text style={[pyc.label, { color: C.textMuted }]}>{t.numYearPrefix} {year}</Text>
          <Text style={[pyc.theme, { color: C.textMuted }]}>{PY_THEME[py]?.[t.vlang] ?? PY_THEME[py]?.en ?? ""}</Text>
        </View>
        <View style={[pyc.box, { borderColor:`${pmInfo.color}30`, backgroundColor:`${pmInfo.color}08` }]}>
          <Text style={[pyc.bigNum, { color: pmInfo.color }]}>{pm}</Text>
          <Text style={[pyc.label, { color: C.textMuted }]}>{month}</Text>
          <Text style={[pyc.theme, { color: C.textMuted }]}>{PY_THEME[pm]?.[t.vlang] ?? PY_THEME[pm]?.en ?? ""}</Text>
        </View>
      </View>
    </View>
  );
}
const pyc = StyleSheet.create({
  card:   { borderRadius:16, borderWidth:1, padding:16, gap:10 },
  title:  { fontSize:9, fontWeight:"800", letterSpacing:1.8 },
  row:    { flexDirection:"row", gap:10 },
  box:    { flex:1, borderRadius:12, borderWidth:1, padding:12, gap:4, alignItems:"center" },
  bigNum: { fontSize:36, fontWeight:"900" },
  label:  { fontSize:10, fontWeight:"700" },
  theme:  { fontSize:11, lineHeight:16, textAlign:"center" },
});

// ── Locked premium card ───────────────────────────────────────────────────────
function LockedCard({ title, emoji, color }: { title: string; emoji: string; color: string }) {
  const C = useC();
  return (
    <View style={[lk.card, { backgroundColor: C.bgCard, borderColor: `${color}22` }]}>
      <View style={lk.row}>
        <View style={[lk.icon, { backgroundColor:`${color}15` }]}>
          <Text style={{ fontSize:18 }}>{emoji}</Text>
        </View>
        <View style={{ flex:1, gap:6 }}>
          <Text style={[lk.title, { color: C.text }]}>{title}</Text>
          <View style={lk.blurRow}>
            {["●●●●●●","●●●●●●●●","●●●●●"].map((b,i) => (
              <View key={i} style={[lk.blurChip, { backgroundColor:`${color}18` }]}>
                <Text style={{ color:`${color}40`, fontSize:9 }}>{b}</Text>
              </View>
            ))}
          </View>
          <Text style={[lk.preview, { color: C.textDim }]}>••••••••••••••••••••••••••••••••••</Text>
        </View>
        <View style={[lk.lockIcon, { backgroundColor:`${color}12` }]}>
          <Feather name="lock" size={14} color={color} />
        </View>
      </View>
    </View>
  );
}
const lk = StyleSheet.create({
  card:     { borderRadius:14, borderWidth:1, padding:12, opacity:0.75 },
  row:      { flexDirection:"row", alignItems:"flex-start", gap:10 },
  icon:     { width:40, height:40, borderRadius:12, alignItems:"center", justifyContent:"center", flexShrink:0 },
  title:    { fontSize:13, fontWeight:"700" },
  blurRow:  { flexDirection:"row", gap:6 },
  blurChip: { paddingHorizontal:8, paddingVertical:3, borderRadius:8 },
  preview:  { fontSize:10, letterSpacing:1 },
  lockIcon: { width:30, height:30, borderRadius:15, alignItems:"center", justifyContent:"center", flexShrink:0 },
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
  const bd = profile.birthData;

  // Single product: Life Mastery Report (Part 2) only — Standard removed.
  const lang: "english" | "hindi" | "hinglish" = "english";
  const [opening, setOpening] = useState(false);

  // Pro+ Tools inputs
  const [mobile, setMobile]   = useState("");
  const [vehicle, setVehicle] = useState("");
  const [house, setHouse]     = useState("");
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

  const openTools = async () => {
    setErr(null);
    if (!bd) {
      setErr("Pehle Profile screen me Name aur Date of Birth bhar dijiye, phir wapas aaiye.");
      return;
    }
    if (!mobile && !vehicle && !house) {
      setErr("Kam se kam ek number to dijiye — Mobile, Vehicle ya House.");
      return;
    }
    const params = new URLSearchParams({
      name: bd.name, dob: dobStr,
      lang,
      ...(tobStr  ? { tob: tobStr } : {}),
      ...(mobile  ? { mobile }  : {}),
      ...(vehicle ? { vehicle } : {}),
      ...(house   ? { house }   : {}),
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

  const toolSections = [
    { icon: "⭐", title: t.nm_wi1Title,  sub: t.nm_wi1Sub },
    { icon: "🌟", title: t.nm_wi2Title,  sub: t.nm_wi2Sub },
    { icon: "💼", title: t.nm_wi3Title,  sub: t.nm_wi3Sub },
    { icon: "💕", title: t.nm_wi4Title,  sub: t.nm_wi4Sub },
    { icon: "🩺", title: t.nm_wi5Title,  sub: t.nm_wi5Sub },
    { icon: "⚠️", title: t.nm_wi6Title,  sub: t.nm_wi6Sub },
    { icon: "📱", title: t.nm_wi7Title,  sub: t.nm_wi7Sub },
    { icon: "🚗", title: t.nm_wi8Title,  sub: t.nm_wi8Sub },
    { icon: "🏠", title: t.nm_wi9Title,  sub: t.nm_wi9Sub },
    { icon: "🤝", title: t.nm_wi10Title, sub: t.nm_wi10Sub },
    { icon: "🔤", title: t.nm_wi11Title, sub: t.nm_wi11Sub },
    { icon: "✍️", title: t.nm_wi12Title, sub: t.nm_wi12Sub },
  ];

  return (
    <View style={{ gap: 12 }}>
      {/* ── LIFE MASTERY REPORT (single product) ─────────────────── */}
      {true && (
        <>
          <View style={[pp.hero, { backgroundColor: C.bgCard, borderColor: "rgba(124,58,237,0.4)" }]}>
            <View style={pp.heroRow}>
              <View style={[pp.heroIcon, { backgroundColor: "rgba(124,58,237,0.15)" }]}>
                <Text style={{ fontSize: 28 }}>🛠️</Text>
              </View>
              <View style={{ flex: 1 }}>
                <View style={pp.tagRow}>
                  <View style={[pp.tag, { backgroundColor: "#7c3aed" }]}>
                    <Text style={pp.tagTxt}>PRO+ TOOLS</Text>
                  </View>
                  <View style={[pp.tag, { backgroundColor: "rgba(245,158,11,0.18)" }]}>
                    <Text style={[pp.tagTxt, { color: "#f59e0b" }]}>{t.nm_premium}</Text>
                  </View>
                </View>
                <Text style={[pp.heroTitle, { color: C.text }]}>{t.nm_lifeMastery}</Text>
                <Text style={[pp.heroSub, { color: C.textMuted }]}>
                  26-page deep report — Mobile, Vehicle, House + Career, Love, Money blueprint
                </Text>
              </View>
            </View>
          </View>

          {/* Profile shown (read-only) */}
          <View style={[pp.row, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <Feather name="user" size={18} color={C.accent} />
            <View style={{ flex: 1 }}>
              <Text style={[pp.rowTitle, { color: C.text }]}>{bd?.name || "—"}</Text>
              <Text style={[pp.rowSub, { color: C.textMuted }]}>DOB: {dobStr}</Text>
            </View>
          </View>

          {/* Inputs */}
          <Text style={[pp.sectionLabel, { color: C.textDim }]}>YOUR NUMBERS (kam se kam ek)</Text>

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

          <View style={pp.inputBlock}>
            <Text style={[pp.inputLabel, { color: C.textDim }]}>🚗 Vehicle Number (optional)</Text>
            <TextInput
              value={vehicle}
              onChangeText={(v) => setVehicle(v.toUpperCase())}
              placeholder="DL01AB1234"
              placeholderTextColor={C.textMuted}
              autoCapitalize="characters"
              maxLength={15}
              style={[pp.input, { backgroundColor: C.bgCard, borderColor: C.border, color: C.text }]}
            />
          </View>

          <View style={pp.inputBlock}>
            <Text style={[pp.inputLabel, { color: C.textDim }]}>🏠 House / Flat Number (optional)</Text>
            <TextInput
              value={house}
              onChangeText={(v) => setHouse(v.toUpperCase())}
              placeholder="B-204"
              placeholderTextColor={C.textMuted}
              autoCapitalize="characters"
              maxLength={15}
              style={[pp.input, { backgroundColor: C.bgCard, borderColor: C.border, color: C.text }]}
            />
          </View>

          {err && (
            <View style={[pp.errBox]}>
              <Feather name="alert-circle" size={14} color="#dc2626" />
              <Text style={pp.errTxt}>{err}</Text>
            </View>
          )}

          <Text style={[pp.sectionLabel, { color: C.textDim }]}>WHAT'S INSIDE</Text>
          {toolSections.map((sec, i) => (
            <View key={i} style={[pp.row, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <Text style={{ fontSize: 22 }}>{sec.icon}</Text>
              <View style={{ flex: 1 }}>
                <Text style={[pp.rowTitle, { color: C.text }]}>{sec.title}</Text>
                <Text style={[pp.rowSub, { color: C.textMuted }]}>{sec.sub}</Text>
              </View>
              <Feather name="check" size={16} color="#22c55e" />
            </View>
          ))}

          <Pressable onPress={openTools} disabled={opening}
            style={[pp.cta, { backgroundColor: "#7c3aed", shadowColor: "#7c3aed" },
                    opening && { opacity: 0.6 }]}>
            <View style={pp.ctaInner}>
              <Feather name={opening ? "loader" : "download"} size={18} color="#fff" />
              <Text style={pp.ctaTxt}>{opening ? t.nm_opening : t.nm_generateBtn}</Text>
            </View>
          </Pressable>
        </>
      )}

      {/* Foot note */}
      <View style={[pp.note, { backgroundColor: C.bgCard, borderColor: C.border }]}>
        <Feather name="info" size={12} color={C.textMuted} />
        <Text style={[pp.noteTxt, { color: C.textMuted }]}>
          Report opens in your browser. PDF can be saved or shared from there.
          All numbers are 100% deterministic — same inputs always give same result.
        </Text>
      </View>
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
               },
  ctaInner:    { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 10, padding: 16 },
  ctaTxt:      { color: "#fff", fontSize: 15, fontWeight: "900" },
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

  // Expanded cards
  const [expLP,   setExpLP]   = useState(true);
  const [expDest, setExpDest] = useState(false);
  const [expSoul, setExpSoul] = useState(false);

  // Pattern A — Free / PRO Report tab
  const [tab, setTab] = useState<"free" | "pro">("free");

  // All calculations — instant, no API call
  const nums = useMemo(() => {
    if (!bd) return null;
    const lp   = calcLifePath(bd.day, bd.month, bd.year);
    const dest = calcDestiny(bd.name);
    const soul = calcSoulUrge(bd.name);
    const pers = calcPersonality(bd.name);
    const mat  = calcMaturity(lp, dest);
    const py   = calcPersonalYear(bd.day, bd.month);
    const pm   = calcPersonalMonth(bd.day, bd.month);
    return { lp, dest, soul, pers, mat, py, pm };
  }, [bd]);

  // Format DOB for display
  const dobStr = bd
    ? `${String(bd.day).padStart(2,"0")} / ${String(bd.month).padStart(2,"0")} / ${bd.year}`
    : null;

  const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  const dobFull = bd
    ? `${bd.day} ${MONTHS[bd.month - 1]} ${bd.year}`
    : null;

  return (
    <View style={[s.root, { backgroundColor: C.bg }]}>
      {/* Header */}
      <View style={[s.header, { paddingTop: topPad + 8, borderBottomColor: C.border }]}>
        <Pressable onPress={() => router.back()} style={s.back}>
          <Feather name="arrow-left" size={20} color={C.textMuted} />
        </Pressable>
        <View style={{ flex:1 }}>
          <Text style={[s.title, { color: C.text }]}>{t.numerologyTitle}</Text>
          <Text style={[s.sub, { color: C.textMuted }]}>{t.numSubtitle}</Text>
        </View>
        <View style={[s.badge, { backgroundColor: `${C.accent}15` }]}>
          <Text style={[s.badgeTxt, { color: C.accent }]}>{t.numFreeBadge}</Text>
        </View>
      </View>

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={[s.content, { paddingBottom: botPad + 40 }]}
      >
        {/* Profile selector */}
        {profiles.length > 1 && (
          <View style={{ gap:6 }}>
            <Text style={[s.sectionLabel, { color: C.textDim }]}>{t.numSelectProfile}</Text>
            <ProfileSelector
              profiles={profiles} activeId={selectedId}
              onSelect={(id) => setSelectedId(id)}
            />
          </View>
        )}

        {/* No profile state */}
        {!bd && (
          <View style={[s.emptyCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <Text style={{ fontSize:40 }}>🔢</Text>
            <Text style={[s.emptyTitle, { color: C.text }]}>{t.numNoProfileTitle}</Text>
            <Text style={[s.emptyBody, { color: C.textMuted }]}>
              {t.numNoProfileBody}
            </Text>
            <Pressable
              onPress={() => router.push("/profile-edit" as any)}
              style={[s.emptyBtn, { backgroundColor: C.accent }]}
            >
              <Text style={s.emptyBtnTxt}>{t.numSetupProfile}</Text>
            </Pressable>
          </View>
        )}

        {/* Profile info card */}
        {bd && (
          <View style={[s.profileCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <View style={s.profileRow}>
              <View style={[s.avatar, { backgroundColor:`${C.accent}15`, borderColor:`${C.accent}30` }]}>
                <Text style={{ fontSize:20 }}>👤</Text>
              </View>
              <View style={{ flex:1 }}>
                <Text style={[s.profileName, { color: C.text }]}>{bd.name}</Text>
                <Text style={[s.profileDob, { color: C.textMuted }]}>🎂 {dobFull}</Text>
                {bd.place && <Text style={[s.profilePlace, { color: C.textDim }]}>📍 {bd.place}</Text>}
              </View>
              <View style={[s.syncBadge, { backgroundColor:`${C.accent}10` }]}>
                <Feather name="check-circle" size={11} color={C.accent} />
                <Text style={[s.syncTxt, { color: C.accent }]}>{t.numAutoSynced}</Text>
              </View>
            </View>
          </View>
        )}

        {/* Pattern A — Segmented tab toggle (Free | PRO Report) */}
        {bd && (
          <View style={[s.tabBar, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
            <Pressable
              onPress={() => { setTab("free"); Haptics.selectionAsync(); }}
              style={[
                s.tabBtn,
                tab === "free" && { backgroundColor: C.accent },
              ]}
            >
              <Feather name="hash" size={13} color={tab === "free" ? "#fff" : C.textMuted} />
              <Text style={[
                s.tabTxt,
                { color: tab === "free" ? "#fff" : C.textMuted },
              ]}>
                Free Numerology
              </Text>
            </Pressable>
            <Pressable
              onPress={() => { setTab("pro"); Haptics.selectionAsync(); }}
              style={[
                s.tabBtn,
                tab === "pro" && { backgroundColor: "#f59e0b" },
              ]}
            >
              <Feather name="file-text" size={13} color={tab === "pro" ? "#fff" : C.textMuted} />
              <Text style={[
                s.tabTxt,
                { color: tab === "pro" ? "#fff" : C.textMuted },
              ]}>
                PRO Report
              </Text>
            </Pressable>
          </View>
        )}

        {/* PRO Report tab */}
        {bd && tab === "pro" && (
          <ProReportPanel profile={profile!} />
        )}

        {/* Free section */}
        {nums && tab === "free" && (
          <>
            <Text style={[s.sectionLabel, { color: C.textDim }]}>{t.numFreeSection}</Text>
            <Text style={[s.sectionSub, { color: C.textMuted }]}>{t.numTapHint}</Text>

            <NumCard
              label={t.numLifePathLbl} labelHindi={t.numLifePathHi}
              num={nums.lp} expanded={expLP}
              onToggle={() => { setExpLP(v => !v); Haptics.selectionAsync(); }}
            />
            <NumCard
              label={t.numDestinyLbl} labelHindi={t.numDestinyHi}
              num={nums.dest} expanded={expDest}
              onToggle={() => { setExpDest(v => !v); Haptics.selectionAsync(); }}
            />
            <NumCard
              label={t.numSoulUrgeLbl} labelHindi={t.numSoulUrgeHi}
              num={nums.soul} expanded={expSoul}
              onToggle={() => { setExpSoul(v => !v); Haptics.selectionAsync(); }}
            />

            {/* Personal Year / Month */}
            <PersonalYearCard py={nums.py} pm={nums.pm} />

            {/* Divider + Advanced teaser */}
            <View style={[s.divider, { borderColor: C.border }]}>
              <View style={[s.divLine, { backgroundColor: C.border }]} />
              <View style={[s.divBadge, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                <Feather name="lock" size={10} color={C.isDark ? "#f59e0b" : "#92400E"} />
                <Text style={[s.divTxt, { color: C.isDark ? "#f59e0b" : "#92400E" }]}>{t.numPremiumDivider}</Text>
              </View>
              <View style={[s.divLine, { backgroundColor: C.border }]} />
            </View>

            {/* Teaser blurb */}
            <View style={[s.teaserCard, { backgroundColor: C.bgCard, borderColor:"rgba(245,158,11,0.25)" }]}>
              <Text style={{ fontSize:32 }}>🔐</Text>
              <View style={{ flex:1, gap:4 }}>
                <Text style={[s.teaserTitle, { color: C.text }]}>{t.numUnlockTitle}</Text>
                <Text style={[s.teaserBody, { color: C.textMuted }]}>
                  {t.numUnlockBody}
                </Text>
              </View>
            </View>

            {/* Locked cards preview */}
            <Text style={[s.sectionLabel, { color: C.textDim }]}>{t.numAdvancedSection}</Text>

            <LockedCard title={t.numLockPersonality} emoji="🎭" color="#8b5cf6" />
            <LockedCard title={t.numLockMaturity} emoji="🌱" color="#10b981" />
            <LockedCard title={t.numLockCareerFin} emoji="💼" color="#f59e0b" />
            <LockedCard title={t.numLockLoveCompat} emoji="❤️" color="#f43f5e" />
            <LockedCard title={t.numLockNameCorr} emoji="✍️" color="#06b6d4" />
            <LockedCard title={t.numLockChallenges} emoji="🙏" color="#f97316" />

            {/* CTA */}
            <Pressable
              onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); router.push("/subscription" as any); }}
              style={s.ctaBtn}
            >
              <View style={s.ctaInner}>
                <Text style={{ fontSize:22 }}>⭐</Text>
                <View style={{ flex:1 }}>
                  <Text style={s.ctaTitle}>{t.numCtaTitle}</Text>
                  <Text style={s.ctaSub}>{t.numCtaSub}</Text>
                </View>
                <Feather name="arrow-right" size={18} color="#fff" />
              </View>
            </Pressable>

            {/* Info footer */}
            <View style={[s.footer, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <Feather name="info" size={12} color={C.textMuted} />
              <Text style={[s.footerTxt, { color: C.textMuted }]}>
                {t.numFooterNote}
              </Text>
            </View>
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
  title:       { fontSize:17, fontWeight:"800" },
  sub:         { fontSize:10, marginTop:1 },
  badge:       { paddingHorizontal:8, paddingVertical:3, borderRadius:8 },
  badgeTxt:    { fontSize:9, fontWeight:"800", letterSpacing:1 },
  content:     { paddingHorizontal:16, gap:12, paddingTop:14 },
  sectionLabel:{ fontSize:9, fontWeight:"800", letterSpacing:2, marginBottom:-4 },
  sectionSub:  { fontSize:11, marginTop:-8 },

  emptyCard:   { borderRadius:18, borderWidth:1, padding:24, alignItems:"center", gap:14 },
  emptyTitle:  { fontSize:16, fontWeight:"800", textAlign:"center" },
  emptyBody:   { fontSize:13, lineHeight:20, textAlign:"center" },
  emptyBtn:    { paddingHorizontal:24, paddingVertical:12, borderRadius:14 },
  emptyBtnTxt: { color:"#fff", fontSize:14, fontWeight:"800" },

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
  tabTxt:    { fontSize:12, fontWeight:"800", letterSpacing:0.3 },
});
