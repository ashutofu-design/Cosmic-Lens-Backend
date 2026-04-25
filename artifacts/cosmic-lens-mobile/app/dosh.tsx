import { Feather } from "@expo/vector-icons";
import { router } from "expo-router";
import * as Haptics from "expo-haptics";
import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Animated,
  I18nManager,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import type { DoshItem } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import type { VLang } from "@/lib/i18nVedic";
import Svg, { Circle } from "react-native-svg";

// ── Status config ─────────────────────────────────────────────────────────────
const STATUS_CONFIG = {
  Active: { color: "#ef4444", bg: "rgba(239,68,68,0.12)",   dot: "#ef4444", label: "Active",  emoji: "🔴" },
  Mild:   { color: "#f97316", bg: "rgba(249,115,22,0.10)",  dot: "#f97316", label: "Mild",    emoji: "🟠" },
  None:   { color: "#22c55e", bg: "rgba(34,197,94,0.08)",   dot: "#22c55e", label: "Clear",   emoji: "🟢" },
};

// ── Demo data (16 doshas) shown when no kundli ────────────────────────────────
function getDemoDoshList(v: VLang): DoshItem[] {
  if (v === "hi") return [
    { key:"manglik",        name:"Manglik Dosh",         name_hindi:"मांगलिक दोष",       icon:"🔴", status:"Active", headline:"मंगल चौथे भाव में — प्रबल मांगलिक दोष",                description:"मंगल यदि 1, 4, 7, 8 या 12 भाव में हो तो मांगलिक दोष बनता है, जो विवाह व रिश्तों पर प्रभाव डालता है।",  remedies:["विवाह से पूर्व कुम्भ विवाह करें","मंगलवार को हनुमान जी को सिंदूर अर्पित करें","घर में मंगल यंत्र रखें"], planet_note:"मंगल → भाव 4" },
    { key:"kaal_sarp",      name:"Kaal Sarp Dosh",       name_hindi:"कालसर्प दोष",       icon:"🐍", status:"Active", headline:"कालसर्प दोष (विषधर) — सभी ग्रह राहु–केतु अक्ष में",       description:"सभी सात मुख्य ग्रह राहु–केतु अक्ष के भीतर हैं (राहु भाव 11 → विषधर प्रकार)। बाधाएँ, विलंब, तीव्र स्वप्न और अचानक उलट-फेर का योग।",          remedies:["त्र्यंबकेश्वर में कालसर्प पूजा करें","नागपंचमी पर सर्प प्रतिमा को दूध अर्पित करें","प्रतिदिन महामृत्युंजय मंत्र 108 बार जपें"], planet_note:"राहु → भाव 11 | केतु → भाव 5 | प्रकार: विषधर" },
    { key:"pitru",          name:"Pitru Dosh",           name_hindi:"पितृ दोष",           icon:"👣", status:"None",   headline:"पितृ दोष नहीं — पूर्वज शांत",                              description:"सूर्य राहु/केतु से युत नहीं है। पितृ दोष नहीं मिला।",                                                            remedies:[], planet_note:"सूर्य → भाव 11" },
    { key:"guru_chandal",   name:"Guru Chandal Dosh",    name_hindi:"गुरु चांडाल दोष",   icon:"🪐", status:"None",   headline:"गुरु चांडाल दोष नहीं — बृहस्पति निर्दोष",                 description:"बृहस्पति राहु/केतु के प्रभाव से मुक्त है। ज्ञान व धर्म स्पष्ट।",                                                  remedies:[], planet_note:"बृहस्पति → भाव 10" },
    { key:"grahan",         name:"Grahan Dosh",          name_hindi:"ग्रहण दोष",          icon:"🌑", status:"None",   headline:"ग्रहण दोष नहीं — सूर्य–चंद्र शुद्ध",                       description:"सूर्य और चंद्र राहु/केतु से पीड़ित नहीं हैं। ग्रहण दोष नहीं।",                                                    remedies:[], planet_note:"सूर्य → भाव 11 | चंद्र → भाव 11" },
    { key:"daridra",        name:"Daridra Dosh",         name_hindi:"दरिद्र दोष",         icon:"💰", status:"Mild",   headline:"शुक्र दु:स्थान (भाव 12) में — हल्का दरिद्र",               description:"शुक्र 12वें भाव (दु:स्थान) में होने से हल्की आर्थिक तंगी व विलासिता में कमी।",                                  remedies:["शुक्रवार को माँ लक्ष्मी की उपासना","कनकधारा स्तोत्र का पाठ"], planet_note:"शुक्र → भाव 12" },
    { key:"angarak",        name:"Angarak Dosh",         name_hindi:"अंगारक दोष",         icon:"🔥", status:"None",   headline:"अंगारक दोष नहीं — मंगल–राहु अलग",                          description:"मंगल और राहु अलग-अलग स्थानों पर हैं। अंगारक दोष नहीं।",                                                          remedies:[], planet_note:"मंगल → भाव 4 | राहु → भाव 11" },
    { key:"shrapit",        name:"Shrapit Dosh",         name_hindi:"श्रापित दोष",        icon:"⛓",  status:"None",   headline:"श्रापित दोष नहीं — शनि–राहु अलग",                          description:"शनि और राहु कुंडली में अलग-अलग स्थित हैं। श्रापित दोष नहीं।",                                                    remedies:[], planet_note:"शनि → भाव 7 | राहु → भाव 11" },
    { key:"kemadruma",      name:"Kemadruma Dosh",       name_hindi:"केमद्रुम दोष",       icon:"🌙", status:"Active", headline:"चंद्र भाव 11 में अकेला — केमद्रुम दोष",                     description:"चंद्र के दोनों ओर (2 व 12 भाव) कोई ग्रह नहीं है। भावनात्मक अकेलापन व असहाय अनुभव।",                          remedies:["सोमवार को शिव जी की पूजा","चंद्र मंत्र का 108 बार जप","घर में सफेद फूल रखें"], planet_note:"चंद्र → भाव 11 | भाव 10: रिक्त | भाव 12: रिक्त" },
    { key:"vish_yoga",      name:"Vish Yoga",            name_hindi:"विष योग",            icon:"🦂", status:"Active", headline:"शनि–चंद्र युति भाव 7 में — विष योग",                       description:"शनि का चंद्र से मेल मन में भारीपन डालता है — चिंता, अवसाद और मानसिक थकान।",                                          remedies:["प्रतिदिन महामृत्युंजय मंत्र 108 बार","सोमवार को शिव अभिषेक","सफेद वस्तुएँ दान करें"], planet_note:"शनि → भाव 7 | चंद्र → भाव 7" },
    { key:"sakat_yoga",     name:"Sakat Yoga",           name_hindi:"शकट योग",            icon:"🛒", status:"None",   headline:"शकट योग नहीं — चंद्र व बृहस्पति शुभ स्थिति में",            description:"चंद्र और बृहस्पति 6/8 अक्ष पर नहीं हैं। धन प्रवाह स्थिर रहेगा।",                                                  remedies:[], planet_note:"चंद्र → भाव 11 | बृहस्पति → भाव 10" },
    { key:"putra",          name:"Putra Dosh",           name_hindi:"पुत्र दोष",           icon:"👶", status:"Mild",   headline:"पंचम भाव में हल्का दोष — आंशिक पुत्र दोष",                  description:"पंचम भाव या बृहस्पति पर हल्की पीड़ा। संतान सम्बन्धी विषयों के लिए चिकित्सक से अवश्य परामर्श लें।",            remedies:["संतान गोपाल मंत्र का साप्ताहिक जप","कृष्ण जन्माष्टमी पर बच्चों को मिठाई दान"], planet_note:"पंचम भाव: शनि | बृहस्पति → भाव 10" },
    { key:"gandanta",       name:"Gandanta Dosh",        name_hindi:"गण्डान्त दोष",        icon:"🌊", status:"None",   headline:"गण्डान्त दोष नहीं — चंद्र स्थिर क्षेत्र में",                description:"चंद्र किसी जल-अग्नि सन्धि पर नहीं है। गण्डान्त की संवेदनशीलता नहीं।",                                              remedies:[], planet_note:"चंद्र → वृश्चिक 10.0°" },
    { key:"punar_phoo",     name:"Punar Phoo Dosh",      name_hindi:"पुनः फू दोष",        icon:"💔", status:"None",   headline:"पुनः फू दोष नहीं — विवाह भाव स्थिर",                       description:"शनि व शुक्र सप्तम भाव के लिए प्रतिकूल नहीं हैं। विवाह सूचक स्थिर हैं।",                                            remedies:[], planet_note:"शनि → भाव 7 | शुक्र → भाव 12" },
    { key:"ekadhipatya",    name:"Ekadhipatya Dosh",     name_hindi:"एकाधिपत्य दोष",      icon:"👑", status:"None",   headline:"एकाधिपत्य दोष नहीं — भाव स्वामित्व संतुलित",                description:"किसी ग्रह की दोहरी स्वामिता से संरचनात्मक कमज़ोरी नहीं बन रही।",                                                   remedies:[], planet_note:"लग्न राशि: 8" },
  ];
  if (v === "hn") return [
    { key:"manglik",        name:"Manglik Dosh",         name_hindi:"मांगलिक दोष",       icon:"🔴", status:"Active", headline:"Mars 4th house mein — Strong Manglik Dosh",              description:"Mars agar 1, 4, 7, 8 ya 12 house mein ho to Manglik Dosh banta hai, jo shaadi aur rishton par strong asar daalta hai.", remedies:["Shaadi se pehle Kumbh Vivah karwayein","Mangalwar ko Hanuman ji ko sindoor chadhayein","Ghar mein Mangal Yantra rakhein"], planet_note:"Mars → House 4" },
    { key:"kaal_sarp",      name:"Kaal Sarp Dosh",       name_hindi:"कालसर्प दोष",       icon:"🐍", status:"Active", headline:"Kaal Sarp Dosh (Vishdhar) — Saare grah Rahu–Ketu axis mein", description:"Saat mukhya grah Rahu–Ketu axis ke andar hain (Rahu H11 → Vishdhar variant). Rukawatein, delays, tez sapne aur sudden reversals ka yog.",  remedies:["Trimbakeshwar mein Kaal Sarp Pooja","Nagpanchami par sarp pratima ko doodh chadhayein","Daily Mahamrityunjay mantra 108 baar jaap"], planet_note:"Rahu → House 11 | Ketu → House 5 | Variant: Vishdhar" },
    { key:"pitru",          name:"Pitru Dosh",           name_hindi:"पितृ दोष",           icon:"👣", status:"None",   headline:"Pitru Dosh nahi — Purvaj shaant",                          description:"Sun par Rahu/Ketu ka asar nahi. Pitru Dosh detect nahi hua.",                                                                  remedies:[], planet_note:"Sun → House 11" },
    { key:"guru_chandal",   name:"Guru Chandal Dosh",    name_hindi:"गुरु चांडाल दोष",   icon:"🪐", status:"None",   headline:"Guru Chandal Dosh nahi — Jupiter clear",                   description:"Jupiter par Rahu/Ketu ka koi influence nahi. Gyaan aur dharm clear.",                                                          remedies:[], planet_note:"Jupiter → House 10" },
    { key:"grahan",         name:"Grahan Dosh",          name_hindi:"ग्रहण दोष",          icon:"🌑", status:"None",   headline:"Grahan Dosh nahi — Sun–Moon clear",                        description:"Sun aur Moon Rahu/Ketu se affected nahi hain. Grahan Dosh nahi.",                                                              remedies:[], planet_note:"Sun → House 11 | Moon → House 11" },
    { key:"daridra",        name:"Daridra Dosh",         name_hindi:"दरिद्र दोष",         icon:"💰", status:"Mild",   headline:"Venus 12th house (Dusthana) mein — Halka Daridra",         description:"Venus 12th house (dusthana) mein hone se halki financial tightness aur luxury kam hoti hai.",                                 remedies:["Shukravar ko Maa Lakshmi ki pooja","Kanakdhara Stotra ka paath"], planet_note:"Venus → House 12" },
    { key:"angarak",        name:"Angarak Dosh",         name_hindi:"अंगारक दोष",         icon:"🔥", status:"None",   headline:"Angarak Dosh nahi — Mars–Rahu alag",                       description:"Mars aur Rahu alag-alag positions par hain. Angarak Dosh nahi.",                                                               remedies:[], planet_note:"Mars → House 4 | Rahu → House 11" },
    { key:"shrapit",        name:"Shrapit Dosh",         name_hindi:"श्रापित दोष",        icon:"⛓",  status:"None",   headline:"Shrapit Dosh nahi — Saturn–Rahu alag",                     description:"Saturn aur Rahu kundli mein alag-alag rakhe hain. Shrapit Dosh nahi.",                                                         remedies:[], planet_note:"Saturn → House 7 | Rahu → House 11" },
    { key:"kemadruma",      name:"Kemadruma Dosh",       name_hindi:"केमद्रुम दोष",       icon:"🌙", status:"Active", headline:"Moon House 11 mein akela — Kemadruma Dosh",                description:"Moon ke dono taraf (2nd aur 12th house) koi grah nahi. Emotional akelapan aur unsupported feeling.",                          remedies:["Somwar ko Lord Shiva ki pooja","Chandra mantra 108× jaap","Ghar mein safed phool rakhein"], planet_note:"Moon → House 11 | H10: empty | H12: empty" },
    { key:"vish_yoga",      name:"Vish Yoga",            name_hindi:"विष योग",            icon:"🦂", status:"Active", headline:"Saturn–Moon Conjunction in H7 — Vish Yoga",                description:"Saturn ka Moon ke saath conjunction mind par bhaaripan daalta hai — chinta, depression aur mental thakaan ka indicator.",        remedies:["Daily Mahamrityunjay mantra 108 baar","Somwar ko Shiva abhishek","Safed cheezein daan karein"], planet_note:"Saturn → H7 | Moon → H7" },
    { key:"sakat_yoga",     name:"Sakat Yoga",           name_hindi:"शकट योग",            icon:"🛒", status:"None",   headline:"Sakat Yoga nahi — Moon aur Jupiter shubh sthiti mein",     description:"Moon aur Jupiter 6/8 axis par nahi hain. Wealth flow stable rahega.",                                                          remedies:[], planet_note:"Moon → H11 | Jupiter → H10" },
    { key:"putra",          name:"Putra Dosh",           name_hindi:"पुत्र दोष",           icon:"👶", status:"Mild",   headline:"5th House par halki affliction — Partial Putra Dosh",     description:"5th house ya Jupiter par halki peeda. Santaan-related vishayon ke liye medical professional se zaroor consult karein.",     remedies:["Santan Gopal mantra weekly jaap","Krishna Janmashtami par bachchon ko sweets daan"], planet_note:"5th House: Saturn | Jupiter → H10" },
    { key:"gandanta",       name:"Gandanta Dosh",        name_hindi:"गण्डान्त दोष",        icon:"🌊", status:"None",   headline:"Gandanta Dosh nahi — Moon stable zone mein",               description:"Moon kisi water-fire junction par nahi hai. Gandanta sensitivity nahi.",                                                       remedies:[], planet_note:"Moon → Scorpio 10.0°" },
    { key:"punar_phoo",     name:"Punar Phoo Dosh",      name_hindi:"पुनः फू दोष",        icon:"💔", status:"None",   headline:"Punar Phoo Dosh nahi — Marriage house stable",             description:"Saturn aur Venus 7th house ke liye adverse position par nahi hain. Marriage indicators stable.",                              remedies:[], planet_note:"Saturn → H7 | Venus → H12" },
    { key:"ekadhipatya",    name:"Ekadhipatya Dosh",     name_hindi:"एकाधिपत्य दोष",      icon:"👑", status:"None",   headline:"Ekadhipatya Dosh nahi — House lordships balanced",         description:"Kisi planet ki dual-rulership se structural weakening nahi ban rahi.",                                                         remedies:[], planet_note:"Lagna sign: 8" },
  ];
  return [
    { key:"manglik",        name:"Manglik Dosh",         name_hindi:"मांगलिक दोष",       icon:"🔴", status:"Active", headline:"Mars in 4th House — Strong Manglik Dosh",                    description:"Mars in houses 1, 4, 7, 8, or 12 creates Manglik Dosh, strongly affecting marriage and relationships.",                        remedies:["Perform Kumbh Vivah before marriage","Offer sindoor to Hanuman ji on Tuesdays","Wear or keep a Mangal Yantra at home"],         planet_note:"Mars → House 4" },
    { key:"kaal_sarp",      name:"Kaal Sarp Dosh",       name_hindi:"कालसर्प दोष",       icon:"🐍", status:"Active", headline:"Kaal Sarp Dosh (Vishdhar) — All Planets in Rahu–Ketu Arc",   description:"All seven core planets fall within the Rahu–Ketu axis (Rahu in House 11 → Vishdhar variant). Creates obstacles, delays, vivid dreams, and sudden reversals.", remedies:["Perform Kaal Sarp Pooja at Trimbakeshwar","Offer milk to a serpent idol on Nagpanchami","Chant Mahamrityunjay mantra 108 times daily"],          planet_note:"Rahu → House 11 | Ketu → House 5 | Variant: Vishdhar" },
    { key:"pitru",          name:"Pitru Dosh",           name_hindi:"पितृ दोष",           icon:"👣", status:"None",   headline:"No Pitru Dosh — Ancestors at Peace",                         description:"Sun is free from Rahu/Ketu conjunction. No Pitru Dosh detected.",                                                              remedies:[], planet_note:"Sun → House 11" },
    { key:"guru_chandal",   name:"Guru Chandal Dosh",    name_hindi:"गुरु चांडाल दोष",   icon:"🪐", status:"None",   headline:"No Guru Chandal Dosh — Jupiter Unafflicted",                 description:"Jupiter is free from Rahu/Ketu influence. Wisdom and dharma are clear.",                                                       remedies:[], planet_note:"Jupiter → House 10" },
    { key:"grahan",         name:"Grahan Dosh",          name_hindi:"ग्रहण दोष",          icon:"🌑", status:"None",   headline:"No Grahan Dosh — Luminaries Clear",                          description:"Sun and Moon are free from Rahu/Ketu nodal affliction. No Grahan Dosh.",                                                       remedies:[], planet_note:"Sun → House 11 | Moon → House 11" },
    { key:"daridra",        name:"Daridra Dosh",         name_hindi:"दरिद्र दोष",         icon:"💰", status:"Mild",   headline:"Venus in Dusthana (House 12) — Mild Daridra",                description:"Venus in the 12th house (dusthana) creates mild financial constraints and luxury deprivation.",                                  remedies:["Worship Goddess Lakshmi on Fridays","Recite Kanakdhara Stotra"],                                                                  planet_note:"Venus → House 12" },
    { key:"angarak",        name:"Angarak Dosh",         name_hindi:"अंगारक दोष",         icon:"🔥", status:"None",   headline:"No Angarak Dosh — Mars–Rahu Well Separated",                 description:"Mars and Rahu are in separate positions. No Angarak Dosh.",                                                                    remedies:[], planet_note:"Mars → House 4 | Rahu → House 11" },
    { key:"shrapit",        name:"Shrapit Dosh",         name_hindi:"श्रापित दोष",        icon:"⛓",  status:"None",   headline:"No Shrapit Dosh — Saturn–Rahu Separated",                    description:"Saturn and Rahu are well-separated in the chart. No Shrapit Dosh.",                                                             remedies:[], planet_note:"Saturn → House 7 | Rahu → House 11" },
    { key:"kemadruma",      name:"Kemadruma Dosh",       name_hindi:"केमद्रुम दोष",       icon:"🌙", status:"Active", headline:"Moon Isolated in House 11 — Kemadruma Dosh",                  description:"No planets occupy houses adjacent to Moon (2nd and 12th). Creates emotional isolation and feeling unsupported.",               remedies:["Worship Lord Shiva on Mondays","Chant Chandra mantra 108×","Keep white flowers at home"],                                         planet_note:"Moon → House 11 | H10: empty | H12: empty" },
    { key:"vish_yoga",      name:"Vish Yoga",            name_hindi:"विष योग",            icon:"🦂", status:"Active", headline:"Saturn–Moon Conjunction in House 7 — Vish Yoga",             description:"Saturn conjunct Moon infuses the mind with heaviness — chronic worry, low mood and emotional fatigue, especially in their dashas.", remedies:["Chant Mahamrityunjay mantra 108 times daily","Worship Lord Shiva on Mondays with milk abhishekam","Donate white items on Mondays"], planet_note:"Saturn → H7 | Moon → H7" },
    { key:"sakat_yoga",     name:"Sakat Yoga",           name_hindi:"शकट योग",            icon:"🛒", status:"None",   headline:"No Sakat Yoga — Moon and Jupiter Well Placed",               description:"Moon and Jupiter are not in adverse 6/8 mutual position. Wealth flow is stable.",                                              remedies:[], planet_note:"Moon → H11 | Jupiter → H10" },
    { key:"putra",          name:"Putra Dosh",           name_hindi:"पुत्र दोष",           icon:"👶", status:"Mild",   headline:"Mild Affliction on Children House — Partial Putra Dosh",     description:"Mild affliction in the 5th house or on Jupiter (significator of children). Always consult medical professionals for fertility concerns.", remedies:["Chant Santan Gopal mantra weekly on Wednesdays","Donate sweets to children on Krishna Janmashtami"], planet_note:"5th House: Saturn | Jupiter → H10" },
    { key:"gandanta",       name:"Gandanta Dosh",        name_hindi:"गण्डान्त दोष",        icon:"🌊", status:"None",   headline:"No Gandanta Dosh — Moon in Stable Zone",                     description:"Moon is not at a sign-junction. No Gandanta sensitivity present.",                                                             remedies:[], planet_note:"Moon → Scorpio 10.0°" },
    { key:"punar_phoo",     name:"Punar Phoo Dosh",      name_hindi:"पुनः फू दोष",        icon:"💔", status:"None",   headline:"No Punar Phoo Dosh — Marriage House Stable",                 description:"Saturn and Venus are not in adverse position relative to the 7th house. Marriage indicators are stable.",                       remedies:[], planet_note:"Saturn → H7 | Venus → H12" },
    { key:"ekadhipatya",    name:"Ekadhipatya Dosh",     name_hindi:"एकाधिपत्य दोष",      icon:"👑", status:"None",   headline:"No Ekadhipatya Dosh — House Lordships Balanced",             description:"No planet's dual-rulership creates structural weakening in this chart.",                                                       remedies:[], planet_note:"Lagna sign: 8" },
  ];
}

// ── Pulse animation ───────────────────────────────────────────────────────────
function usePulse(active: boolean) {
  const anim = React.useRef(new Animated.Value(1)).current;
  useEffect(() => {
    if (!active) return;
    const loop = Animated.loop(Animated.sequence([
      Animated.timing(anim, { toValue: 1.6, duration: 700, useNativeDriver: true }),
      Animated.timing(anim, { toValue: 1,   duration: 700, useNativeDriver: true }),
    ]));
    loop.start();
    return () => loop.stop();
  }, [active]);
  return anim;
}

// ── Single Dosh Card ──────────────────────────────────────────────────────────
function DoshCard({ item, defaultOpen }: { item: DoshItem; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen ?? false);
  const C = useC();
  const t = useT();
  const cfg = STATUS_CONFIG[item.status];
  const pulse = usePulse(item.status === "Active");
  const v = t.vlang;
  // Status label translation
  const statusLabel =
    item.status === "Active" ? (v === "hi" ? "सक्रिय" : v === "hn" ? "Active" : "Active") :
    item.status === "Mild"   ? (v === "hi" ? "हल्का"  : v === "hn" ? "Mild"   : "Mild")   :
                               (v === "hi" ? "स्पष्ट" : v === "hn" ? "Clear"  : "Clear");
  // Primary name = English in en/hn modes, Devanagari in hi mode
  // Secondary name only shown in hi mode (Roman as reference) — en/hn never show Devanagari
  const primaryName = v === "hi" ? (item.name_hindi || item.name) : item.name;
  const secondaryName = v === "hi" ? item.name : null;
  const remediesLabel = v === "hi" ? "उपाय" : v === "hn" ? "UPAY (REMEDIES)" : "REMEDIES";

  return (
    <Pressable
      style={[d.card, { backgroundColor: C.bgCard, borderColor: C.border, borderLeftColor: cfg.color }]}
      onPress={() => { setOpen(v => !v); Haptics.selectionAsync(); }}
    >
      {/* Row header */}
      <View style={d.cardHeader}>
        <View style={[d.iconBubble, { backgroundColor: cfg.bg }]}>
          <Text style={{ fontSize: 16 }}>{item.icon}</Text>
        </View>

        <View style={{ flex: 1, gap: 1 }}>
          <Text style={[d.doshName, { color: C.text }]}>{primaryName}</Text>
          {secondaryName && primaryName !== secondaryName && (
            <Text style={[d.doshHindi, { color: C.textMuted }]}>{secondaryName}</Text>
          )}
        </View>

        {/* Status badge */}
        <View style={[d.statusPill, { backgroundColor: cfg.bg }]}>
          {item.status === "Active" && (
            <Animated.View style={[d.statusDot, { backgroundColor: cfg.dot, transform: [{ scale: pulse }], opacity: pulse.interpolate({ inputRange: [1, 1.6], outputRange: [1, 0.5] }) }]} />
          )}
          {item.status !== "Active" && (
            <View style={[d.statusDot, { backgroundColor: cfg.dot }]} />
          )}
          <Text style={[d.statusText, { color: cfg.color }]}>{statusLabel}</Text>
        </View>

        <Feather name={open ? "chevron-up" : "chevron-down"} size={14} color={C.textMuted} style={{ marginLeft: 6 }} />
      </View>

      {/* Headline — always visible */}
      <Text style={[d.headline, { color: cfg.color }]} numberOfLines={open ? undefined : 2}>
        {item.headline}
      </Text>

      {/* Expanded content — only remedies */}
      {open && item.remedies.length > 0 && (
        <View style={d.expanded}>
          <Text style={[d.remediesTitle, { color: C.textMuted }]}>{remediesLabel}</Text>
          {item.remedies.map((r, i) => (
            <View key={i} style={d.remedyRow}>
              <View style={[d.remedyBullet, { backgroundColor: `${cfg.color}20` }]}>
                <Text style={[d.remedyNum, { color: cfg.color }]}>{i + 1}</Text>
              </View>
              <Text style={[d.remedyText, { color: C.textMuted }]}>{r}</Text>
            </View>
          ))}
        </View>
      )}
    </Pressable>
  );
}

// ── Summary Ring ──────────────────────────────────────────────────────────────
function SummaryRing({ active, mild, total, labels }: { active: number; mild: number; total: number; labels: { analysis: string; active: string; mild: string; clear: string; detected: string } }) {
  const C = useC();
  const safeTotal = Math.max(total, 1);
  const clear = Math.max(safeTotal - active - mild, 0);
  const pct = Math.round((clear / safeTotal) * 100);
  const R = 40, circ = 2 * Math.PI * R;
  const scoreColor = active === 0 && mild <= 1 ? "#22c55e" : active > 1 ? "#ef4444" : "#f97316";

  return (
    <View style={[d.summaryCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
      {/* Ring */}
      <View style={{ width: 90, height: 90, position: "relative" }}>
        <Svg width={90} height={90} style={{ position: "absolute" } as any}>
          <Circle cx={45} cy={45} r={R} fill="none" stroke={C.border ?? "#1E293B"} strokeWidth={7} />
          <Circle cx={45} cy={45} r={R} fill="none"
            stroke={scoreColor} strokeWidth={7}
            strokeLinecap="round"
            strokeDasharray={`${circ * pct / 100} ${circ}`}
            rotation={-90} originX={45} originY={45}
          />
        </Svg>
        <View style={{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0, alignItems: "center", justifyContent: "center" }}>
          <Text style={{ color: scoreColor, fontSize: 18, fontFamily: "Nunito_700Bold", lineHeight: 22 }}>{clear}</Text>
          <Text style={{ color: C.textDim, fontSize: 9 }}>/ {safeTotal}</Text>
        </View>
      </View>

      {/* Stats */}
      <View style={{ flex: 1, gap: 8 }}>
        <Text style={[d.summaryTitle, { color: C.text }]}>{labels.analysis}</Text>
        <View style={{ flexDirection: "row", gap: 12 }}>
          <View style={d.statItem}>
            <Text style={[d.statNum, { color: "#ef4444" }]}>{active}</Text>
            <Text style={[d.statLabel, { color: C.textMuted }]}>{labels.active}</Text>
          </View>
          <View style={[d.statDivider, { backgroundColor: C.border }]} />
          <View style={d.statItem}>
            <Text style={[d.statNum, { color: "#f97316" }]}>{mild}</Text>
            <Text style={[d.statLabel, { color: C.textMuted }]}>{labels.mild}</Text>
          </View>
          <View style={[d.statDivider, { backgroundColor: C.border }]} />
          <View style={d.statItem}>
            <Text style={[d.statNum, { color: "#22c55e" }]}>{clear}</Text>
            <Text style={[d.statLabel, { color: C.textMuted }]}>{labels.clear}</Text>
          </View>
        </View>
        <Text style={{ fontSize: 10, color: C.textDim, fontFamily: "Nunito_400Regular" }}>
          {labels.detected}
        </Text>
      </View>
    </View>
  );
}

// ── Main Screen ───────────────────────────────────────────────────────────────
export default function DoshScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const t = useT();
  const { kundli, doshData, doshLoading } = useUser();
  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  const showDemo = !kundli;
  const v = t.vlang;
  const demoList = React.useMemo(() => getDemoDoshList(v), [v]);
  const list: DoshItem[] = showDemo
    ? demoList
    : (doshData?.dosh_list ?? demoList);

  const total = list.length;
  const active = showDemo
    ? list.filter(it => it.status === "Active").length
    : (doshData?.active_count ?? 0);
  const mild = showDemo
    ? list.filter(it => it.status === "Mild").length
    : (doshData?.mild_count ?? 0);
  const clear = Math.max(total - active - mild, 0);

  // Localized labels
  const LBL =
    v === "hi" ? {
      subtitle:   `सम्पूर्ण दोष विश्लेषण (${total} दोष)`,
      demo:       "डेमो",
      totalDosh:  "कुल दोष",
      present:    "उपस्थित",
      notPresent: "अनुपस्थित",
      scanning:   "जाँच…",
      analyzing:  "आपकी कुंडली का विश्लेषण…",
      checking:   `सभी ${total} दोषों की जाँच`,
      analysis:   "दोष विश्लेषण",
      active:     "सक्रिय",
      mild:       "हल्का",
      clear:      "स्पष्ट",
      detected:   `${total} में से ${active + mild} दोष पाए गए`,
      disclaimer: "दोष विश्लेषण शास्त्रीय वैदिक ज्योतिष के सिद्धांतों पर आधारित है। महत्वपूर्ण निर्णयों के लिए योग्य ज्योतिषी से सलाह लें।",
    } : v === "hn" ? {
      subtitle:   `Sampoorna Dosh Vishleshan (${total} Doshas)`,
      demo:       "Demo",
      totalDosh:  "Kul Dosh",
      present:    "Hai",
      notPresent: "Nahi",
      scanning:   "Scanning…",
      analyzing:  "Aapki kundli analyse ho rahi hai…",
      checking:   `Sabhi ${total} dosh check ho rahe hain`,
      analysis:   "Dosh Vishleshan",
      active:     "Active",
      mild:       "Mild",
      clear:      "Clear",
      detected:   `${active + mild} of ${total} doshas detected`,
      disclaimer: "Dosh analysis classical Vedic astrology par based hai. Important faisle ke liye qualified Jyotishi se consult karein.",
    } : {
      subtitle:   `Complete Dosha Analysis (${total} Doshas)`,
      demo:       "Demo",
      totalDosh:  "Total Dosh",
      present:    "Present",
      notPresent: "Not Present",
      scanning:   "Scanning…",
      analyzing:  "Analysing your kundli…",
      checking:   `Checking all ${total} dosh conditions`,
      analysis:   "Dosh Analysis",
      active:     "Active",
      mild:       "Mild",
      clear:      "Clear",
      detected:   `${active + mild} of ${total} doshas detected`,
      disclaimer: "Dosh analysis is based on classical Vedic astrology principles. Always consult a qualified Jyotishi for important life decisions.",
    };

  return (
    <ScrollView
      style={[d.root, { backgroundColor: C.bg }]}
      contentContainerStyle={{ paddingBottom: botPad + 20 }}
      showsVerticalScrollIndicator={false}
    >
      {/* ── Header ── */}
      <View style={[d.header, { paddingTop: topPad, borderBottomColor: C.border }]}>
        <Pressable style={d.backBtn} onPress={() => router.back()}>
          <Feather name={I18nManager.isRTL ? "arrow-right" : "arrow-left"} size={20} color={C.text} />
        </Pressable>
        <View style={{ flex: 1 }}>
          <Text style={[d.title, { color: C.text }]}>{t.doshTitle}</Text>
          <Text style={[d.subtitle, { color: C.textMuted }]}>{LBL.subtitle}</Text>
        </View>
        <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
          {doshLoading && <ActivityIndicator size="small" color="#f59e0b" />}
          {showDemo && (
            <View style={[d.demoBadge, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
              <Text style={[d.demoBadgeText, { color: C.textMuted }]}>{LBL.demo}</Text>
            </View>
          )}
        </View>
      </View>

      {/* ── Stats bar ── */}
      <View style={[d.statsBar, { backgroundColor: C.bgCard, borderBottomColor: C.border }]}>
        <View style={d.statTab}>
          <Text style={[d.statTabNum, { color: C.text }]}>{total}</Text>
          <Text style={[d.statTabLabel, { color: C.textMuted }]}>{LBL.totalDosh}</Text>
        </View>
        <View style={[d.statTabDivider, { backgroundColor: C.border }]} />
        <View style={d.statTab}>
          <Text style={[d.statTabNum, { color: active + mild > 0 ? "#ef4444" : "#22c55e" }]}>
            {active + mild}
          </Text>
          <Text style={[d.statTabLabel, { color: C.textMuted }]}>{LBL.present}</Text>
        </View>
        <View style={[d.statTabDivider, { backgroundColor: C.border }]} />
        <View style={d.statTab}>
          <Text style={[d.statTabNum, { color: "#22c55e" }]}>{clear}</Text>
          <Text style={[d.statTabLabel, { color: C.textMuted }]}>{LBL.notPresent}</Text>
        </View>
        {doshLoading && (
          <>
            <View style={[d.statTabDivider, { backgroundColor: C.border }]} />
            <View style={[d.statTab, { flexDirection: "row", gap: 5 }]}>
              <ActivityIndicator size="small" color="#f59e0b" />
              <Text style={[d.statTabLabel, { color: "#f59e0b" }]}>{LBL.scanning}</Text>
            </View>
          </>
        )}
      </View>

      <View style={d.content}>
        {/* ── Summary ring ── */}
        <SummaryRing active={active} mild={mild} total={total} labels={{ analysis: LBL.analysis, active: LBL.active, mild: LBL.mild, clear: LBL.clear, detected: LBL.detected }} />

        {/* ── Loading skeleton or cards ── */}
        {!showDemo && doshLoading && !doshData && (
          <View style={[d.loadingCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <ActivityIndicator size="large" color="#f59e0b" />
            <Text style={{ color: C.textMuted, marginTop: 12, fontFamily: "Nunito_500Medium", fontSize: 13 }}>
              {LBL.analyzing}
            </Text>
            <Text style={{ color: C.textDim, marginTop: 4, fontSize: 11, fontFamily: "Nunito_400Regular" }}>
              {LBL.checking}
            </Text>
          </View>
        )}

        {/* ── Dosh cards — Active first, then Mild, then Clear ── */}
        {list
          .slice()
          .sort((a, b) => {
            const order = { Active: 0, Mild: 1, None: 2 };
            return order[a.status] - order[b.status];
          })
          .map((item, i) => (
            <DoshCard key={item.key} item={item} defaultOpen={i === 0 && item.status !== "None"} />
          ))
        }

        {/* ── Bottom disclaimer ── */}
        <View style={[d.disclaimer, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
          <Feather name="info" size={11} color={C.textDim} />
          <Text style={{ color: C.textDim, fontSize: 10, fontFamily: "Nunito_400Regular", flex: 1, lineHeight: 14 }}>
            {LBL.disclaimer}
          </Text>
        </View>
      </View>
    </ScrollView>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const d = StyleSheet.create({
  root:    { flex: 1 },
  header:  {
    flexDirection: "row", alignItems: "center", gap: 12,
    paddingHorizontal: 16, paddingBottom: 14,
    borderBottomWidth: 1,
  },
  backBtn:  { width: 36, height: 36, alignItems: "center", justifyContent: "center" },
  title:    { fontSize: 17, fontFamily: "Nunito_700Bold" },
  subtitle: { fontSize: 11, fontFamily: "Nunito_400Regular", marginTop: 1 },
  demoBadge: {
    paddingHorizontal: 10, paddingVertical: 4,
    borderRadius: 12, borderWidth: 1,
  },
  demoBadgeText: { fontSize: 11, fontFamily: "Nunito_500Medium" },

  content: { paddingHorizontal: 16, paddingTop: 16, gap: 10 },

  // Summary card
  summaryCard: {
    borderRadius: 18, borderWidth: 1, padding: 16,
    flexDirection: "row", alignItems: "center", gap: 16,
  },
  summaryTitle: { fontSize: 15, fontFamily: "Nunito_700Bold" },
  statItem:  { alignItems: "center", gap: 2 },
  statNum:   { fontSize: 20, fontFamily: "Nunito_700Bold", lineHeight: 24 },
  statLabel: { fontSize: 9, fontFamily: "Nunito_400Regular", textTransform: "uppercase", letterSpacing: 0.8 },
  statDivider: { width: 1, height: 28 },

  // Loading
  loadingCard: {
    borderRadius: 18, borderWidth: 1, padding: 32,
    alignItems: "center", justifyContent: "center",
  },

  // Dosh card
  card: {
    borderRadius: 16, borderWidth: 1, borderLeftWidth: 3,
    padding: 14, gap: 6,
  },
  cardHeader: { flexDirection: "row", alignItems: "center", gap: 10 },
  iconBubble: {
    width: 38, height: 38, borderRadius: 10,
    alignItems: "center", justifyContent: "center",
  },
  doshName:  { fontSize: 13, fontFamily: "Nunito_700Bold" },
  doshHindi: { fontSize: 10, fontFamily: "Nunito_400Regular" },
  statusPill: {
    flexDirection: "row", alignItems: "center", gap: 4,
    paddingHorizontal: 8, paddingVertical: 4, borderRadius: 8,
  },
  statusDot:  { width: 6, height: 6, borderRadius: 3 },
  statusText: { fontSize: 10, fontFamily: "Nunito_700Bold" },
  headline:  { fontSize: 11, fontFamily: "Nunito_600SemiBold", marginLeft: 48, lineHeight: 16 },

  expanded: { marginTop: 4, gap: 10 },
  desc:     { fontSize: 12, fontFamily: "Nunito_400Regular", lineHeight: 18 },
  noteRow:  { flexDirection: "row", alignItems: "center", gap: 4 },
  noteText: { fontSize: 10, fontFamily: "Nunito_400Regular", flex: 1 },

  remediesWrap:  { gap: 6 },
  remediesTitle: { fontSize: 9, fontFamily: "Nunito_700Bold", letterSpacing: 1.5 },
  remedyRow:     { flexDirection: "row", gap: 10, alignItems: "flex-start" },
  remedyBullet:  {
    width: 18, height: 18, borderRadius: 9,
    alignItems: "center", justifyContent: "center",
  },
  remedyNum:  { fontSize: 9, fontFamily: "Nunito_700Bold" },
  remedyText: { flex: 1, fontSize: 11, fontFamily: "Nunito_400Regular", lineHeight: 16 },

  disclaimer: {
    borderRadius: 14, borderWidth: 1, padding: 12,
    flexDirection: "row", gap: 8, alignItems: "flex-start",
  },

  // Stats bar
  statsBar: {
    flexDirection: "row", alignItems: "stretch",
    borderBottomWidth: 1, paddingVertical: 0,
  },
  statTab: {
    flex: 1, alignItems: "center", justifyContent: "center",
    paddingVertical: 14, gap: 3,
  },
  statTabNum:   { fontSize: 26, fontFamily: "Nunito_700Bold", lineHeight: 30 },
  statTabLabel: { fontSize: 10, fontFamily: "Nunito_500Medium", textTransform: "uppercase", letterSpacing: 0.8 },
  statTabDivider: { width: 1, marginVertical: 12 },
});
