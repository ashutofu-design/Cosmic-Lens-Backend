import { Feather } from "@expo/vector-icons";
import { BlurView } from "expo-blur";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router, useLocalSearchParams } from "expo-router";
import React, { useEffect, useRef } from "react";
import {
  Animated, Easing, Platform, Pressable, ScrollView,
  StatusBar, StyleSheet, Text, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Svg, { Circle } from "react-native-svg";
import { useC } from "@/context/ThemeContext";
import { useT } from "@/hooks/useT";
import { MilanResultStore } from "@/lib/milanResultStore";
import { useFeatureGate } from "@/components/FeatureGate";

const NAKSHATRAS=["Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishtha","Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati"];
const RASHIS=["Mesh","Vrishabh","Mithun","Kark","Simha","Kanya","Tula","Vrishchik","Dhanu","Makar","Kumbh","Meen"];
const EN2R:Record<string,string>={Aries:"Mesh",Taurus:"Vrishabh",Gemini:"Mithun",Cancer:"Kark",Leo:"Simha",Virgo:"Kanya",Libra:"Tula",Scorpio:"Vrishchik",Sagittarius:"Dhanu",Capricorn:"Makar",Aquarius:"Kumbh",Pisces:"Meen"};
const NADI=[0,1,2,2,1,0,0,1,2,2,1,0,0,1,2,2,1,0,0,1,2,2,1,0,0,1,2];
const NADI_N=["Vata (Adi)","Pitta (Madhya)","Kapha (Antya)"];
const GANA=[0,1,2,1,0,1,0,0,2,2,1,1,0,2,0,2,0,2,2,1,1,0,1,2,1,1,0];
const GANA_N=["Dev","Manushya","Raksha"];
const VARNA=[1,2,3,0,1,2,3,0,1,2,3,0];
const YONI=[0,1,2,3,4,5,6,7,8,9,10,2,11,12,13,14,14,13,5,12,11,10,3,7,4,9,0];
const YONI_E:[number,number][]=[[0,1],[2,3],[4,5],[6,7],[8,9],[10,11],[12,13],[14,0]];
const RLORD=[2,5,3,1,0,3,5,2,4,6,6,4];
const PLN:number[][]=[
  [1,2,2,1,2,0,0],[2,1,0,1,2,2,0],[2,0,1,1,2,0,2],
  [2,0,2,1,0,2,0],[2,1,2,1,1,0,0],[2,2,0,2,1,1,0],[0,0,2,2,2,0,1],
];
function yoniEnemy(a:number,b:number){return YONI_E.some(([x,y])=>(a===x&&b===y)||(a===y&&b===x));}
function maitri(r1:number,r2:number):number{
  const l1=RLORD[r1]??0,l2=RLORD[r2]??0;
  if(l1>=PLN.length||l2>=PLN.length)return 3;
  const t=(PLN[l1]?.[l2]??1)+(PLN[l2]?.[l1]??1);
  return t>=4?5:t===3?4:t===2?3:0;
}
function tara(n1:number,n2:number):number{
  const fwd=((n2-n1+27)%27)+1,rev=((n1-n2+27)%27)+1,bad=[3,5,7];
  return !bad.includes(fwd%9||9)&&!bad.includes(rev%9||9)?3:!bad.includes(fwd%9||9)||!bad.includes(rev%9||9)?1.5:0;
}
function bhakut(r1:number,r2:number):number{
  const d=Math.abs(r1-r2);
  return [[1,11],[4,8],[5,7]].some(([a,b])=>d===a||d===b)?0:7;
}
function vasya(r1:number,r2:number):number{
  if(r1===r2)return 2;
  const g=[[0,3,4],[1,6,7,9],[2,8],[5,10,11]];
  return g.findIndex(x=>x.includes(r1))===g.findIndex(x=>x.includes(r2))?2:1;
}

interface KootItem{score:number;max:number;label:string;detail:string;bad:boolean;}
interface Result{
  nadi:KootItem;gana:KootItem;bhakut:KootItem;maitri:KootItem;
  yoni:KootItem;tara:KootItem;vasya:KootItem;varna:KootItem;
  total:number;manglik:boolean;
}

// ────────────────────────────────────────────────────────────────
// DYNAMIC PRO HOOKS — signal-driven teasers (never static)
// ────────────────────────────────────────────────────────────────
interface ProSignals {
  karmic: boolean;
  emotionalGap: boolean;
  attraction: boolean;
  stability: boolean;
  conflict: boolean;
  breakup: "low" | "medium" | "high";
  marriage: "strong" | "average" | "weak";
  manglikImbalance: boolean;
  nameA: string;
  nameB: string;
  total: number;
  pct: number;
}

function extractSignals(r: Result, p1: string, p2: string, bd: any): ProSignals {
  const manglikA = bd?.p1?.manglik ?? false;
  const manglikB = bd?.p2?.manglik ?? false;
  const manglikImbalance = manglikA !== manglikB;
  const karmic = r.nadi.score === 0 || r.yoni.score === 0 || manglikImbalance || r.tara.score === 0;
  const emotionalGap = r.gana.score <= 1 || r.maitri.score < 3;
  const attraction = r.yoni.score >= 3 && r.maitri.score >= 4;
  const stability = r.bhakut.score === 7 && r.maitri.score >= 4 && r.total >= 27;
  const conflict = r.bhakut.score === 0 || r.gana.score === 0 || r.yoni.score === 0;
  const breakup: ProSignals["breakup"] =
    r.total < 18 || (r.nadi.bad && r.bhakut.bad) ? "high"
    : r.total < 24 ? "medium" : "low";
  const marriage: ProSignals["marriage"] =
    r.total >= 28 ? "strong" : r.total >= 21 ? "average" : "weak";
  return {
    karmic, emotionalGap, attraction, stability, conflict, breakup, marriage,
    manglikImbalance, nameA: p1, nameB: p2,
    total: r.total, pct: Math.round((r.total / 36) * 100),
  };
}

function pick<T>(arr: T[], seed: number): T {
  return arr[seed % arr.length]!;
}

function buildProHooks(s: ProSignals) {
  const seed = (s.total * 17 + s.nameA.length * 31 + s.nameB.length * 13) >>> 0;

  const emotional = s.emotionalGap && s.karmic
    ? pick([
        `${s.nameA} aur ${s.nameB} ke beech ek connection hai — par dono ki feelings ek hi taal par nahi chalti. Iska reason chhupa hai`,
        `Dono ka bond asli hai, lekin ek andekha gap hai jo baar-baar dil ko kheenchta hai — yeh sirf mood nahi,`,
      ], seed)
    : s.attraction
    ? pick([
        `Ek gehra emotional pull hai jo ${s.nameA} ko ${s.nameB} ki taraf khinchta rahta hai — aur yeh pull kisi aam vajah se nahi banta,`,
        `Dono ki Moon energy aapas me baat karti hai — yahan ek silent understanding hai jo words se zyada`,
      ], seed + 1)
    : s.emotionalGap
    ? pick([
        `Upar se sab theek lagta hai, par ek unspoken distance hai jo ${s.nameA} aur ${s.nameB} mehsoos to karte hain par`,
        `Ek feeling-gap chhupa hua hai — roz ke pyar me yeh nahi dikhta, lekin crucial moments me`,
      ], seed + 2)
    : pick([
        `${s.nameA} aur ${s.nameB} ka emotional rhythm surprisingly aligned hai — iska asli raaz aapki Chandra kundli me`,
        `Dono ke feelings ek hi frequency par hain — aur iski wajah sirf pyar nahi, kuch aur bhi`,
      ], seed + 3);

  const marriageFuture = s.marriage === "strong"
    ? pick([
        `Shaadi ke baad ka safar unusual tareeke se smooth dikhta hai — ek specific planetary support yahan kaam kar raha hai jo`,
        `Is jodi ka future marriage ek solid foundation par khada hai — par asli turning point kab aayega, woh`,
      ], seed + 4)
    : s.marriage === "average"
    ? pick([
        `Shaadi possible hai, lekin ek specific year me ek decision aapke rishte ki direction badal dega — woh`,
        `Marriage timing par ek important window khul rahi hai — miss kiya to wait badh sakta hai,`,
      ], seed + 5)
    : pick([
        `Shaadi ka rasta hai par usme ek hidden delay baitha hai — yeh kab clear hoga aur kaunsa remedy`,
        `Future marriage par ek particular dasha ka chhaya hai — agle 18 mahine critical hain,`,
      ], seed + 6);

  const strengths = s.stability
    ? pick([
        `Is rishte me ek silent force hai jo ise tootne nahi deti — chahe kitne bhi fights ho, ek ankahi`,
        `Aap dono ki combined kundli me ek rare yoga ban raha hai jo long-term loyalty ki`,
      ], seed + 7)
    : s.attraction
    ? pick([
        `Aap dono ki biggest taaqat physical ya emotional nahi — yeh kuch aur hai jo aapne shayad`,
        `Ek unexpected strength is bond me chhupi hai — zyadatar couples ise late realize karte hain,`,
      ], seed + 8)
    : pick([
        `Challenges ke bawajood ek hidden anchor hai jo is rishte ko stable rakhta hai — woh`,
        `Aapke chart me ek subtle planetary shield hai jo is bond ko crises me`,
      ], seed + 9);

  const riskAnalysis = s.breakup === "high"
    ? pick([
        `Agle 6–12 mahine me ek trigger-point aa sakta hai jo rishte ko hila de — yeh kab aur kaise`,
        `Ek repeating pattern exists yahan — aur yeh random nahi, iska root ek specific planetary clash`,
      ], seed + 10)
    : s.conflict
    ? pick([
        `Chhote-chhote jhagde random nahi lagte — ek cycle chal raha hai jo specific dates par`,
        `Ek friction pattern dikh raha hai jo aam couples me nahi hota — iska source aur fix`,
      ], seed + 11)
    : s.breakup === "medium"
    ? pick([
        `Risk medium level par hai — par ek choti si chook ise badha sakti hai, aur woh choti`,
        `Rishte me ek gray-zone hai jahan dono partners unknowingly distance banate hain,`,
      ], seed + 12)
    : pick([
        `Breakup risk bahut kam hai, par ek specific phase aata hai jab dono ko zyada`,
        `Natural risks minimal hain — sirf ek external influence se bachna hoga, aur woh`,
      ], seed + 13);

  const karmicBond = s.karmic
    ? pick([
        `Yeh connection normal nahi hai — ek purva-janma ka karmic thread yahan active hai jo`,
        `${s.nameA} aur ${s.nameB} ek karmic loan lekar mile hain — iska poora matlab aur resolution`,
      ], seed + 14)
    : s.manglikImbalance
    ? pick([
        `Mangal ki energy ek partner me strong hai doosre me nahi — yeh imbalance exactly kaise asar`,
        `Ek Mangal-based karmic pattern hai jo sirf married life me surface karta hai —`,
      ], seed + 15)
    : pick([
        `Karmic weight halka hai — par ek sookshm dhaaga dono ko jodta hai jiska source`,
        `Past-life bond subtle hai, fir bhi certain moments me aap dono ko ek strange familiarity`,
      ], seed + 16);

  const finalOutcome = s.marriage === "strong" && !s.conflict
    ? pick([
        `Long-term outcome positive hai, par ek specific choice jo aap 2 saal ke andar lenge woh`,
        `Is rishte ka destiny bright hai — sirf ek hidden warning point hai jise time par`,
      ], seed + 17)
    : s.breakup === "high"
    ? pick([
        `Current path par rishta critical hai — ek specific remedy is direction ko`,
        `Bina intervention ke trajectory risky hai — par ek mantra-based fix available hai jo`,
      ], seed + 18)
    : s.marriage === "average"
    ? pick([
        `Outcome aapke haath me hai — ek specific year me liya gaya decision next 20 saal`,
        `Middle-path hai — but 3 key actions jo agle 6 mahine me lene hain woh poori kahani`,
      ], seed + 19)
    : pick([
        `Rishta ek crossroad par khada hai — ek choti si guidance se yeh poori taraf badal sakta hai, aur woh`,
        `Final picture mixed hai — par ek specific jyotish remedy ise sharply positive taraf`,
      ], seed + 20);

  return [
    { key: "emotional",     emoji: "💗", title: "Emotional Compatibility", text: emotional },
    { key: "marriage",      emoji: "💍", title: "Marriage Future",         text: marriageFuture },
    { key: "strengths",     emoji: "✨", title: "Hidden Strengths",         text: strengths },
    { key: "risk",          emoji: "⚠️", title: "Risk Analysis",           text: riskAnalysis },
    { key: "karmic",        emoji: "🕉️", title: "Karmic Bond",             text: karmicBond },
    { key: "final",         emoji: "🔮", title: "Final Outcome",           text: finalOutcome },
  ];
}

function compute(p1n:string,p1r:string,p1m:boolean,p2n:string,p2r:string,p2m:boolean):Result{
  const n1=NAKSHATRAS.indexOf(p1n),n2=NAKSHATRAS.indexOf(p2n);
  const r1=RASHIS.indexOf(EN2R[p1r]??p1r),r2=RASHIS.indexOf(EN2R[p2r]??p2r);
  const nad1=NADI[n1]??0,nad2=NADI[n2]??0,nadiSc=nad1!==nad2?8:0;
  const g1=GANA[n1]??0,g2=GANA[n2]??0;
  let ganaSc=6;
  if((g1===0&&g2===2)||(g1===2&&g2===0))ganaSc=1;
  else if((g1===1&&g2===2)||(g1===2&&g2===1))ganaSc=0;
  const bhakutSc=bhakut(r1,r2);
  const maitriSc=maitri(r1,r2);
  const y1=YONI[n1]??0,y2=YONI[n2]??0;
  const yoniSc=y1===y2?4:yoniEnemy(y1,y2)?0:2;
  const taraSc=tara(n1,n2);
  const vasyaSc=vasya(r1,r2);
  const v1=VARNA[r1]??0,v2=VARNA[r2]??0,varnaSc=v1<=v2?1:0;
  return{
    nadi:  {score:nadiSc, max:8,label:"Nadi",         detail:nadiSc===8?`${NADI_N[nad1]} × ${NADI_N[nad2]}`:`Both ${NADI_N[nad1]}`,bad:nadiSc===0},
    gana:  {score:ganaSc, max:6,label:"Gana",         detail:`${GANA_N[g1]} + ${GANA_N[g2]}`,bad:ganaSc===0},
    bhakut:{score:bhakutSc,max:7,label:"Bhakut",      detail:bhakutSc===7?"Shubh":"Dosh present",bad:bhakutSc===0},
    maitri:{score:maitriSc,max:5,label:"Graha Maitri",detail:maitriSc>=4?"Friendly":maitriSc>=3?"Neutral":"Hostile",bad:maitriSc<3},
    yoni:  {score:yoniSc, max:4,label:"Yoni",         detail:yoniSc===4?"Same Yoni":yoniSc===2?"Moderate":"Hostile Yoni",bad:yoniSc===0},
    tara:  {score:taraSc, max:3,label:"Tara",         detail:taraSc===3?"Auspicious":taraSc>0?"Moderate":"Inauspicious",bad:taraSc===0},
    vasya: {score:vasyaSc,max:2,label:"Vasya",        detail:vasyaSc===2?"Strong":"Moderate",bad:false},
    varna: {score:varnaSc,max:1,label:"Varna",        detail:varnaSc?"Matched":"Mismatched",bad:varnaSc===0},
    total:nadiSc+ganaSc+bhakutSc+maitriSc+yoniSc+taraSc+vasyaSc+varnaSc,
    manglik:p1m!==p2m,
  };
}

function grade(total:number){
  if(total>=32)return{label:"Excellent Match",  col:"#22c55e",emoji:"🌟"};
  if(total>=27)return{label:"Very Good Match",  col:"#4ade80",emoji:"💚"};
  if(total>=21)return{label:"Average Match",    col:"#fbbf24",emoji:"💛"};
  if(total>=18)return{label:"Below Average",    col:"#f97316",emoji:"🧡"};
  return            {label:"Low Compatibility", col:"#ef4444",emoji:"❤️‍🩹"};
}

interface KootDisplay {
  key: string;
  name: string;
  emoji: string;
  color: string;
  getExplanation: (r: Result) => string;
  getScore: (r: Result) => { score: number; max: number };
}

const KOOT_DISPLAY: KootDisplay[] = [
  {
    key: "nadi", name: "Soul Sync", emoji: "🧬", color: "#a78bfa",
    getExplanation: (r) => r.nadi.score === 8
      ? "Your souls vibrate on different frequencies — perfect for balance and harmony"
      : "Same soul energy — deep empathy but needs awareness for health",
    getScore: (r) => ({ score: r.nadi.score, max: r.nadi.max }),
  },
  {
    key: "yoni", name: "Attraction Power", emoji: "🔥", color: "#f43f5e",
    getExplanation: (r) => r.yoni.score === 4
      ? "Magnetic physical and energetic attraction — deeply drawn to each other"
      : r.yoni.score > 0 ? "Complementary attraction — good chemistry with some differences"
      : "Different energies — patience strengthens this bond over time",
    getScore: (r) => ({ score: r.yoni.score, max: r.yoni.max }),
  },
  {
    key: "tara", name: "Destiny Link", emoji: "✨", color: "#fbbf24",
    getExplanation: (r) => r.tara.score === 3
      ? "Stars align in your favour — a destined and auspicious connection"
      : r.tara.score > 0 ? "Moderate cosmic alignment — steady growth ahead"
      : "Challenging star positions — mindful effort will help",
    getScore: (r) => ({ score: r.tara.score, max: r.tara.max }),
  },
  {
    key: "maitri", name: "Intimacy Match", emoji: "💜", color: "#c084fc",
    getExplanation: (r) => r.maitri.score >= 4
      ? "Strong mental and emotional intimacy — you truly understand each other"
      : r.maitri.score >= 3 ? "Decent understanding — communication builds deeper intimacy"
      : "Different wavelengths — effort needed to bridge the gap",
    getScore: (r) => ({ score: r.maitri.score, max: r.maitri.max }),
  },
  {
    key: "gana", name: "Emotional Bond", emoji: "💞", color: "#ec4899",
    getExplanation: (r) => r.gana.score >= 5
      ? "Deeply connected emotionally — your natures complement beautifully"
      : r.gana.score > 0 ? "Emotional bond exists but needs nurturing and patience"
      : "Different temperaments — active emotional effort needed",
    getScore: (r) => ({ score: r.gana.score, max: r.gana.max }),
  },
  {
    key: "bhakut", name: "Personality Energy", emoji: "⚡", color: "#f97316",
    getExplanation: (r) => r.bhakut.score === 7
      ? "Rashi energies flow well — personalities complement each other"
      : "Rashi conflict detected — awareness and adjustment will help",
    getScore: (r) => ({ score: r.bhakut.score, max: r.bhakut.max }),
  },
  {
    key: "vasya", name: "Life Alignment", emoji: "🤝", color: "#34d399",
    getExplanation: (r) => r.vasya.score === 2
      ? "Strong mutual influence — you naturally support each other's growth"
      : "Moderate alignment — intentional teamwork strengthens the bond",
    getScore: (r) => ({ score: r.vasya.score, max: r.vasya.max }),
  },
  {
    key: "varna", name: "Energy Flow", emoji: "🌊", color: "#38bdf8",
    getExplanation: (r) => r.varna.score === 1
      ? "Spiritual energies are balanced — natural flow between you both"
      : "Energy imbalance — spiritual practices together will harmonise you",
    getScore: (r) => ({ score: r.varna.score, max: r.varna.max }),
  },
];

function ScoreRing({ total, col }: { total: number; col: string }) {
  const R = 56, circ = 2 * Math.PI * R, pct = total / 36;
  return (
    <View style={{ width: 140, height: 140, alignItems: "center", justifyContent: "center" }}>
      <Svg width={140} height={140} style={{ position: "absolute" } as any}>
        <Circle cx={70} cy={70} r={R} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth={10} />
        <Circle cx={70} cy={70} r={R} fill="none" stroke={col} strokeWidth={10}
          strokeLinecap="round" strokeDasharray={`${circ * pct} ${circ}`}
          rotation={-90} originX={70} originY={70} />
      </Svg>
      <Text style={{ fontSize: 38, fontFamily: "Nunito_700Bold", color: col, lineHeight: 42 }}>{total}</Text>
      <Text style={{ fontSize: 12, color: "rgba(255,255,255,0.4)", fontFamily: "Nunito_500Medium" }}>/ 36</Text>
    </View>
  );
}

function KootCard({
  item, result, index, isDark,
}: {
  item: KootDisplay; result: Result; index: number; isDark: boolean;
}) {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(24)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, { toValue: 1, duration: 500, delay: 300 + index * 80, useNativeDriver: true }),
      Animated.spring(slideAnim, { toValue: 0, delay: 300 + index * 80, useNativeDriver: true, speed: 14, bounciness: 4 }),
    ]).start();
  }, []);

  const { score, max } = item.getScore(result);
  const pct = Math.round((score / max) * 100);
  const explanation = item.getExplanation(result);
  const isGood = pct >= 60;

  return (
    <Animated.View style={{ opacity: fadeAnim, transform: [{ translateY: slideAnim }] }}>
      <View style={[st.kootCard, {
        backgroundColor: isDark ? "rgba(255,255,255,0.04)" : "rgba(255,255,255,0.95)",
        borderColor: isDark ? `${item.color}30` : `${item.color}25`,
        shadowColor: item.color,
        shadowOpacity: isDark ? 0.15 : 0.08,
        shadowRadius: 12,
        shadowOffset: { width: 0, height: 4 },
        elevation: 4,
      }]}>
        <View style={st.kootTop}>
          <View style={[st.kootEmoji, { backgroundColor: isDark ? `${item.color}18` : `${item.color}12` }]}>
            <Text style={{ fontSize: 22 }}>{item.emoji}</Text>
          </View>
          <View style={{ flex: 1, gap: 3 }}>
            <Text style={[st.kootName, { color: isDark ? "#fff" : "#0F172A" }]}>{item.name}</Text>
            <View style={st.kootScoreRow}>
              <View style={[st.kootBarBg, { backgroundColor: isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)" }]}>
                <LinearGradient
                  colors={[item.color, `${item.color}88`]}
                  start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
                  style={[st.kootBarFill, { width: `${pct}%` as any }]}
                />
              </View>
              <Text style={[st.kootScoreText, { color: item.color }]}>{score}/{max}</Text>
            </View>
          </View>
          <View style={[st.kootStatus, {
            backgroundColor: isGood
              ? isDark ? "rgba(34,197,94,0.15)" : "rgba(34,197,94,0.1)"
              : isDark ? "rgba(251,191,36,0.15)" : "rgba(251,191,36,0.1)",
            borderColor: isGood
              ? isDark ? "rgba(34,197,94,0.3)" : "rgba(34,197,94,0.25)"
              : isDark ? "rgba(251,191,36,0.3)" : "rgba(251,191,36,0.25)",
          }]}>
            <Text style={{ fontSize: 11 }}>{isGood ? "✓" : "~"}</Text>
          </View>
        </View>
        <Text style={[st.kootExplanation, {
          color: isDark ? "rgba(203,213,225,0.65)" : "#64748B",
        }]}>{explanation}</Text>
      </View>
    </Animated.View>
  );
}

function ProHookCard({ emoji, title, text, isDark }: { emoji: string; title: string; text: string; isDark: boolean; }) {
  // Show ~65% visible, rest blurred
  const cut = Math.min(text.length, Math.max(40, Math.floor(text.length * 0.62)));
  const visible = text.slice(0, cut);
  const hidden = text.slice(cut) + " Iska poora matlab, timing, aur remedies aapke personalised Pro report me detail me milenge.";

  return (
    <View style={[hs.card, {
      backgroundColor: isDark ? "rgba(245,158,11,0.06)" : "rgba(124,58,237,0.05)",
      borderColor: isDark ? "rgba(245,158,11,0.28)" : "rgba(124,58,237,0.22)",
    }]}>
      <View style={hs.head}>
        <Text style={{ fontSize: 16 }}>{emoji}</Text>
        <Text style={[hs.title, { color: isDark ? "#fcd34d" : "#6d28d9" }]}>{title}</Text>
        <View style={{ flex: 1 }} />
        <View style={[hs.lockPill, {
          backgroundColor: isDark ? "rgba(245,158,11,0.15)" : "rgba(124,58,237,0.12)",
          borderColor: isDark ? "rgba(245,158,11,0.4)" : "rgba(124,58,237,0.3)",
        }]}>
          <Feather name="lock" size={9} color={isDark ? "#f59e0b" : "#7C3AED"} />
          <Text style={[hs.lockTxt, { color: isDark ? "#f59e0b" : "#7C3AED" }]}>PRO</Text>
        </View>
      </View>

      <Text style={[hs.visibleTxt, { color: isDark ? "rgba(226,232,240,0.88)" : "#1e293b" }]}>
        {visible}
      </Text>

      <View style={hs.hiddenWrap}>
        <Text style={[hs.hiddenTxt, { color: isDark ? "rgba(226,232,240,0.88)" : "#1e293b" }]} numberOfLines={3}>
          {hidden}
        </Text>
        <BlurView
          intensity={Platform.OS === "ios" ? 22 : 18}
          tint={isDark ? "dark" : "light"}
          style={StyleSheet.absoluteFillObject}
        />
        <LinearGradient
          colors={isDark
            ? ["rgba(8,14,30,0)", "rgba(8,14,30,0.55)"]
            : ["rgba(255,255,255,0)", "rgba(255,255,255,0.6)"]}
          style={StyleSheet.absoluteFillObject}
          pointerEvents="none"
        />
        <View style={hs.lockOverlay} pointerEvents="none">
          <Text style={{ fontSize: 18 }}>🔒</Text>
        </View>
      </View>
    </View>
  );
}

const hs = StyleSheet.create({
  card: { borderRadius: 16, borderWidth: 1, padding: 14, gap: 10, overflow: "hidden" },
  head: { flexDirection: "row", alignItems: "center", gap: 8 },
  title: { fontSize: 13.5, fontFamily: "Nunito_800ExtraBold", letterSpacing: 0.2 },
  lockPill: {
    flexDirection: "row", alignItems: "center", gap: 4,
    paddingHorizontal: 7, paddingVertical: 3, borderRadius: 10, borderWidth: 1,
  },
  lockTxt: { fontSize: 9, fontFamily: "Nunito_800ExtraBold", letterSpacing: 0.8 },
  visibleTxt: { fontSize: 12.5, fontFamily: "Nunito_400Regular", lineHeight: 20 },
  hiddenWrap: {
    position: "relative", borderRadius: 10, overflow: "hidden",
    minHeight: 46, justifyContent: "center",
  },
  hiddenTxt: { fontSize: 12.5, fontFamily: "Nunito_400Regular", lineHeight: 20, paddingHorizontal: 4 },
  lockOverlay: {
    ...StyleSheet.absoluteFillObject,
    alignItems: "center", justifyContent: "center",
  },
});

export default function KundliMilanResultScreen() {
  const C = useC();
  const { LockOverlay } = useFeatureGate("kundli_milan");
  const t = useT();
  const insets = useSafeAreaInsets();
  const androidSB = StatusBar.currentHeight ?? 24;
  const topPad = Platform.OS === "android" ? Math.max(insets.top, androidSB) : insets.top;
  const botPad = insets.bottom;
  const isDark = C.isDark;

  const params = useLocalSearchParams<{ p1Name?: string; p2Name?: string }>();

  // ── Backend result only (Swiss Ephemeris accurate) ──
  const backendData = MilanResultStore.get();

  let result: Result | null = null;
  let p1DisplayName = params.p1Name || "Person 1";
  let p2DisplayName = params.p2Name || "Person 2";
  let backendAnalysis: {
    compatibility_insight: string;
    strengths: string[];
    challenges: string[];
    marriage_outlook: string;
  } | null = null;

  if (backendData && backendData.koots) {
    // Transform backend shape → local Result shape
    const bk: Record<string, any> = {};
    for (const k of backendData.koots) bk[k.key] = k;
    result = {
      nadi:   bk.nadi   ?? { score:0, max:8,  label:"Nadi",        detail:"-", bad:true },
      gana:   bk.gana   ?? { score:0, max:6,  label:"Gana",        detail:"-", bad:true },
      bhakut: bk.bhakut ?? { score:0, max:7,  label:"Bhakut",      detail:"-", bad:true },
      maitri: bk.maitri ?? { score:0, max:5,  label:"Graha Maitri",detail:"-", bad:true },
      yoni:   bk.yoni   ?? { score:0, max:4,  label:"Yoni",        detail:"-", bad:true },
      tara:   bk.tara   ?? { score:0, max:3,  label:"Tara",        detail:"-", bad:true },
      vasya:  bk.vasya  ?? { score:0, max:2,  label:"Vasya",       detail:"-", bad:false},
      varna:  bk.varna  ?? { score:0, max:1,  label:"Varna",       detail:"-", bad:true },
      total:  backendData.total ?? 0,
      manglik:backendData.manglik_dosh ?? false,
    };
    p1DisplayName = backendData.p1?.name || params.p1Name || "Person 1";
    p2DisplayName = backendData.p2?.name || params.p2Name || "Person 2";
    backendAnalysis = backendData.analysis ?? null;
  }

  // ── Hooks must be declared before any conditional return ──
  const heroFade = useRef(new Animated.Value(0)).current;
  const heroScale = useRef(new Animated.Value(0.9)).current;

  useEffect(() => {
    if (!result) return;
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    Animated.parallel([
      Animated.timing(heroFade, { toValue: 1, duration: 700, useNativeDriver: true }),
      Animated.spring(heroScale, { toValue: 1, useNativeDriver: true, speed: 10, bounciness: 6 }),
    ]).start();
  }, []);

  // ── No backend data: show error screen ──
  if (!result) {
    return (
      <View style={{ flex:1, backgroundColor:C.bg, justifyContent:"center", alignItems:"center", padding:32 }}>
        <Text style={{ fontSize:40, marginBottom:16 }}>⚠️</Text>
        <Text style={{ color:C.text, fontSize:18, fontFamily:"Nunito_700Bold", textAlign:"center", marginBottom:8 }}>
          Result Not Found
        </Text>
        <Text style={{ color:C.textMuted, fontSize:14, fontFamily:"Nunito_400Regular", textAlign:"center", marginBottom:32 }}>
          Koi result nahi mila. Wapas jao aur dobara calculate karein.
        </Text>
        <Pressable
          onPress={() => router.back()}
          style={{ backgroundColor:C.isDark?"#f59e0b":"#7C3AED", paddingHorizontal:32, paddingVertical:14, borderRadius:14 }}
        >
          <Text style={{ color:"#fff", fontFamily:"Nunito_700Bold", fontSize:16 }}>Go Back</Text>
        </Pressable>
      </View>
    );
  }

  const g = grade(result.total);
  const pctTotal = Math.round((result.total / 36) * 100);

  const verdict = result.total >= 32
    ? "Stars align strongly. An exceptional and harmonious union."
    : result.total >= 27
    ? "Very positive match. With love and respect, great potential ahead."
    : result.total >= 21
    ? "Moderate match. Awareness and effort will help this bond grow."
    : "Challenging match. Remedies and guidance strongly recommended.";

  // ── Build detailed written analysis ──
  const strengths: string[] = [];
  const challenges: string[] = [];
  if (result.nadi.score === 8) strengths.push("Different Nadi types create natural physical and emotional balance — a strong foundation for healthy children and long life together.");
  else challenges.push("Same Nadi (Nadi Dosha) — both partners share the same constitutional energy. This can affect health and progeny; remedies like Maha Mrityunjaya Jaap are recommended.");
  if (result.gana.score >= 5) strengths.push("Gana harmony shows your inner natures are well-matched — temperaments flow together without friction in daily life.");
  else if (result.gana.score === 0) challenges.push("Major Gana mismatch (Dev–Rakshasa) — fundamentally different temperaments. Conscious patience and spiritual practice are essential.");
  if (result.bhakut.score === 7) strengths.push("Bhakut is auspicious — your Rashi positions promote prosperity, family growth, and mutual welfare.");
  else challenges.push("Bhakut Dosha present — Rashi placement may bring tension in finances, family, or progeny. Mantra remedies can offset this.");
  if (result.maitri.score >= 4) strengths.push("Strong Graha Maitri — the lords of your Moon signs are friendly, ensuring deep mental compatibility and shared values.");
  else if (result.maitri.score < 3) challenges.push("Graha Maitri is weak — the planetary lords of your Rashis are not naturally friendly, requiring effort to build mutual understanding.");
  if (result.yoni.score >= 3) strengths.push("Yoni match indicates strong physical attraction and intimate compatibility — chemistry comes naturally.");
  else if (result.yoni.score === 0) challenges.push("Hostile Yoni — instinctive natures clash. Open communication about needs and boundaries is crucial.");
  if (result.tara.score === 3) strengths.push("Tara Koot is auspicious — destiny favours this union; major life events tend to unfold positively.");
  if (result.manglik) challenges.push("Manglik Dosha imbalance detected — only one partner is Manglik. Performing Kumbh Vivah or Mangal Shanti before marriage is advised.");
  if (strengths.length === 0) strengths.push("Every relationship has hidden strengths. Focus on shared values, communication, and mutual respect to discover yours.");
  if (challenges.length === 0) challenges.push("No major doshas detected — this is a smooth match astrologically. Continue nurturing it with care and devotion.");

  const marriageOutlook = result.total >= 32
    ? "This is one of the highest-rated matches in Vedic astrology. Marriage between you is likely to bring lasting joy, prosperity, healthy progeny, and spiritual growth. Family harmony and emotional security will be natural to your bond. Sacred rituals and pujas will further elevate this beautiful connection."
    : result.total >= 27
    ? "A very promising marriage match. With love, communication, and respect for each other's space, this relationship can blossom into a deeply fulfilling lifelong partnership. Minor differences can be smoothed over through shared rituals like daily prayers and gratitude practice."
    : result.total >= 21
    ? "An average match that requires conscious effort. Focus on understanding each other's emotional needs, practice patience, and consider remedies like Vivah Yog rituals. With dedication, this bond can grow stronger over time."
    : "A challenging match in classical Vedic terms. Strongly recommend consulting a qualified astrologer before marriage. Remedies like Kumbh Vivah, Maha Mrityunjaya Jaap, and Navagraha Shanti can significantly improve outcomes. Love alone may not be enough — spiritual practice together is essential.";

  const compatibilityInsight = `Out of the maximum 36 Gunas in Ashtakoot Milan, your union scores ${result.total} (${pctTotal}% match). In Vedic tradition, scores above 18 are considered acceptable for marriage, above 24 are good, and above 28 are excellent. Your match falls in the "${g.label.toLowerCase()}" range, which means ${result.total >= 24 ? "the cosmic forces support your union and the foundation is solid" : "while astrological challenges exist, sincere effort and remedies can transform this relationship"}. Remember: astrology guides — love, respect, and commitment build the marriage.`;

  return (
    <View style={[st.root, { backgroundColor: C.bg }]}>
      <LinearGradient
        colors={isDark
          ? ["rgba(109,40,217,0.12)", "transparent", "rgba(0,0,0,0.2)"]
          : ["rgba(139,92,246,0.08)", "transparent", "rgba(255,255,255,0.1)"]}
        locations={[0, 0.4, 1]}
        style={StyleSheet.absoluteFill}
        pointerEvents="none"
      />

      <View style={[st.topBar, { paddingTop: topPad + 8 }]}>
        <Pressable
          onPress={() => {
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
            router.back();
          }}
          style={st.backBtn}
        >
          <View style={[st.backCircle, {
            backgroundColor: isDark ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.05)",
            borderColor: isDark ? "rgba(255,255,255,0.14)" : "rgba(0,0,0,0.08)",
          }]}>
            <Feather name="arrow-left" size={20} color={isDark ? "#fff" : "#0F172A"} />
          </View>
        </Pressable>
        <Text style={[st.headerTitle, { color: isDark ? "#f3e8ff" : "#0F172A" }]}>
          {t.milanResult}
        </Text>
        <View style={{ width: 42 }} />
      </View>

      <ScrollView
        contentContainerStyle={[st.scrollContent, { paddingTop: topPad + 64, paddingBottom: botPad + 40 }]}
        showsVerticalScrollIndicator={false}
      >
        <Animated.View style={[st.heroCard, {
          opacity: heroFade,
          transform: [{ scale: heroScale }],
          backgroundColor: isDark ? "rgba(20,10,40,0.7)" : "rgba(245,240,255,0.95)",
          borderColor: isDark ? `${g.col}35` : `${g.col}20`,
          shadowColor: g.col,
          shadowOpacity: isDark ? 0.25 : 0.12,
          shadowRadius: 20,
          shadowOffset: { width: 0, height: 8 },
          elevation: 10,
        }]}>
          <LinearGradient
            colors={isDark ? [`${g.col}15`, "transparent"] : [`${g.col}08`, "transparent"]}
            style={[StyleSheet.absoluteFill, { borderRadius: 24 }]}
          />

          <View style={st.namesRow}>
            <View style={st.nameChip}>
              <Text style={{ fontSize: 14 }}>👤</Text>
              <Text style={[st.nameText, { color: isDark ? "#e2d8ff" : "#3B0764" }]} numberOfLines={1}>
                {p1DisplayName}
              </Text>
            </View>
            <View style={[st.heartIcon, { backgroundColor: isDark ? "rgba(236,72,153,0.15)" : "rgba(236,72,153,0.1)" }]}>
              <Text style={{ fontSize: 14 }}>💕</Text>
            </View>
            <View style={st.nameChip}>
              <Text style={{ fontSize: 14 }}>💑</Text>
              <Text style={[st.nameText, { color: isDark ? "#fce7f3" : "#831843" }]} numberOfLines={1}>
                {p2DisplayName}
              </Text>
            </View>
          </View>

          <ScoreRing total={result.total} col={g.col} />

          <Text style={[st.gradeLabel, { color: g.col }]}>{g.label}</Text>
          <Text style={[st.pctText, { color: isDark ? "rgba(255,255,255,0.5)" : "#64748B" }]}>
            {pctTotal}% Compatible
          </Text>

          <View style={[st.heroBg, { backgroundColor: isDark ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)" }]}>
            <LinearGradient
              colors={[g.col, `${g.col}88`]}
              start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
              style={[st.heroFill, { width: `${pctTotal}%` as any }]}
            />
          </View>

          <Text style={[st.verdictText, { color: isDark ? "rgba(203,213,225,0.6)" : "#475569" }]}>
            {verdict}
          </Text>

          {result.manglik && (
            <View style={st.manglikChip}>
              <View style={st.manglikDot} />
              <Text style={{ color: "#ef4444", fontSize: 11, fontFamily: "Nunito_600SemiBold" }}>
                Manglik Dosh Detected
              </Text>
            </View>
          )}
        </Animated.View>

        {/* ── SOURCE BADGE ── */}
        {backendData && (
          <View style={{flexDirection:"row",alignItems:"center",gap:6,alignSelf:"center",
            backgroundColor:isDark?"rgba(34,197,94,0.1)":"rgba(34,197,94,0.07)",
            borderWidth:1,borderColor:isDark?"rgba(34,197,94,0.3)":"rgba(34,197,94,0.25)",
            borderRadius:20,paddingHorizontal:12,paddingVertical:5}}>
            <View style={{width:6,height:6,borderRadius:3,backgroundColor:"#22c55e"}}/>
            <Text style={{color:isDark?"#86efac":"#15803d",fontSize:10,fontFamily:"Nunito_700Bold",letterSpacing:0.5}}>
              Calculated via Swiss Ephemeris (Lahiri Ayanamsa)
            </Text>
          </View>
        )}

        {/* ── Backend nakshatra details ── */}
        {backendData?.p1 && (
          <View style={{flexDirection:"row",gap:8}}>
            <View style={{flex:1,backgroundColor:isDark?"rgba(255,255,255,0.04)":"rgba(0,0,0,0.03)",
              borderRadius:12,padding:10,borderWidth:1,borderColor:isDark?"rgba(255,255,255,0.08)":"rgba(0,0,0,0.06)"}}>
              <Text style={{color:isDark?"rgba(255,255,255,0.5)":"rgba(0,0,0,0.5)",fontSize:9,fontFamily:"Nunito_700Bold",letterSpacing:0.8,textTransform:"uppercase",marginBottom:3}}>
                {backendData.p1.name}
              </Text>
              <Text style={{color:isDark?"#c4b5fd":"#4f46e5",fontSize:11,fontFamily:"Nunito_700Bold"}}>
                {backendData.p1.nakshatra}
              </Text>
              <Text style={{color:isDark?"rgba(255,255,255,0.55)":"rgba(0,0,0,0.55)",fontSize:10,fontFamily:"Nunito_500Medium"}}>
                Pada {backendData.p1.pada} · {backendData.p1.rashi}
              </Text>
              {backendData.p1.manglik&&<Text style={{color:"#ef4444",fontSize:9,fontFamily:"Nunito_700Bold",marginTop:2}}>♂ Manglik</Text>}
            </View>
            <View style={{flex:1,backgroundColor:isDark?"rgba(255,255,255,0.04)":"rgba(0,0,0,0.03)",
              borderRadius:12,padding:10,borderWidth:1,borderColor:isDark?"rgba(255,255,255,0.08)":"rgba(0,0,0,0.06)"}}>
              <Text style={{color:isDark?"rgba(255,255,255,0.5)":"rgba(0,0,0,0.5)",fontSize:9,fontFamily:"Nunito_700Bold",letterSpacing:0.8,textTransform:"uppercase",marginBottom:3}}>
                {backendData.p2.name}
              </Text>
              <Text style={{color:isDark?"#f9a8d4":"#be185d",fontSize:11,fontFamily:"Nunito_700Bold"}}>
                {backendData.p2.nakshatra}
              </Text>
              <Text style={{color:isDark?"rgba(255,255,255,0.55)":"rgba(0,0,0,0.55)",fontSize:10,fontFamily:"Nunito_500Medium"}}>
                Pada {backendData.p2.pada} · {backendData.p2.rashi}
              </Text>
              {backendData.p2.manglik&&<Text style={{color:"#ef4444",fontSize:9,fontFamily:"Nunito_700Bold",marginTop:2}}>♂ Manglik</Text>}
            </View>
          </View>
        )}

        {/* ── Compatibility Insight (rich paragraph) ── */}
        <View style={[st.analysisCard, {
          backgroundColor: isDark ? "rgba(99,102,241,0.08)" : "rgba(99,102,241,0.05)",
          borderColor: isDark ? "rgba(139,92,246,0.25)" : "rgba(99,102,241,0.18)",
        }]}>
          <View style={st.analysisHead}>
            <Text style={{ fontSize: 18 }}>📜</Text>
            <Text style={[st.analysisTitle, { color: isDark ? "#c4b5fd" : "#4338ca" }]}>
              Astrological Insight
            </Text>
          </View>
          <Text style={[st.analysisBody, { color: isDark ? "rgba(226,232,240,0.78)" : "#334155" }]}>
            {backendAnalysis?.compatibility_insight ?? compatibilityInsight}
          </Text>
        </View>

        {/* ── Strengths ── */}
        <View style={[st.analysisCard, {
          backgroundColor: isDark ? "rgba(34,197,94,0.08)" : "rgba(34,197,94,0.05)",
          borderColor: isDark ? "rgba(34,197,94,0.25)" : "rgba(34,197,94,0.18)",
        }]}>
          <View style={st.analysisHead}>
            <Text style={{ fontSize: 18 }}>✨</Text>
            <Text style={[st.analysisTitle, { color: isDark ? "#86efac" : "#15803d" }]}>
              Your Strengths Together
            </Text>
          </View>
          {(backendAnalysis?.strengths ?? strengths).map((s, i) => (
            <View key={i} style={st.bulletRow}>
              <View style={[st.bulletDot, { backgroundColor: isDark ? "#86efac" : "#16a34a" }]} />
              <Text style={[st.bulletText, { color: isDark ? "rgba(226,232,240,0.78)" : "#334155" }]}>
                {s}
              </Text>
            </View>
          ))}
        </View>

        {/* ── Challenges ── */}
        <View style={[st.analysisCard, {
          backgroundColor: isDark ? "rgba(251,146,60,0.08)" : "rgba(251,146,60,0.05)",
          borderColor: isDark ? "rgba(251,146,60,0.25)" : "rgba(251,146,60,0.20)",
        }]}>
          <View style={st.analysisHead}>
            <Text style={{ fontSize: 18 }}>⚖️</Text>
            <Text style={[st.analysisTitle, { color: isDark ? "#fdba74" : "#c2410c" }]}>
              Areas to Be Mindful Of
            </Text>
          </View>
          {(backendAnalysis?.challenges ?? challenges).map((c, i) => (
            <View key={i} style={st.bulletRow}>
              <View style={[st.bulletDot, { backgroundColor: isDark ? "#fdba74" : "#ea580c" }]} />
              <Text style={[st.bulletText, { color: isDark ? "rgba(226,232,240,0.78)" : "#334155" }]}>
                {c}
              </Text>
            </View>
          ))}
        </View>

        {/* ── Marriage Outlook (long paragraph) ── */}
        <View style={[st.analysisCard, {
          backgroundColor: isDark ? "rgba(236,72,153,0.08)" : "rgba(236,72,153,0.05)",
          borderColor: isDark ? "rgba(236,72,153,0.25)" : "rgba(236,72,153,0.18)",
        }]}>
          <View style={st.analysisHead}>
            <Text style={{ fontSize: 18 }}>💍</Text>
            <Text style={[st.analysisTitle, { color: isDark ? "#f9a8d4" : "#be185d" }]}>
              Marriage Outlook
            </Text>
          </View>
          <Text style={[st.analysisBody, { color: isDark ? "rgba(226,232,240,0.78)" : "#334155" }]}>
            {backendAnalysis?.marriage_outlook ?? marriageOutlook}
          </Text>
        </View>

        <View style={st.sectionHeader}>
          <View style={[st.sectionLine, { backgroundColor: isDark ? "rgba(139,92,246,0.3)" : "rgba(99,102,241,0.2)" }]} />
          <Text style={[st.sectionTitle, { color: isDark ? "#c4b5fd" : "#4f46e5" }]}>
            Detailed Breakdown
          </Text>
          <View style={[st.sectionLine, { backgroundColor: isDark ? "rgba(139,92,246,0.3)" : "rgba(99,102,241,0.2)" }]} />
        </View>

        <View style={st.kootList}>
          {KOOT_DISPLAY.map((item, i) => (
            <KootCard key={item.key} item={item} result={result} index={i} isDark={isDark} />
          ))}
        </View>

        {/* ── PRO SECTION HEADER ── */}
        <View style={st.sectionHeader}>
          <View style={[st.sectionLine, { backgroundColor: isDark ? "rgba(245,158,11,0.35)" : "rgba(124,58,237,0.22)" }]} />
          <View style={{flexDirection:"row",alignItems:"center",gap:6}}>
            <Feather name="lock" size={11} color={isDark ? "#f59e0b" : "#7C3AED"} />
            <Text style={[st.sectionTitle, { color: isDark ? "#f59e0b" : "#7C3AED" }]}>
              PRO INSIGHTS
            </Text>
          </View>
          <View style={[st.sectionLine, { backgroundColor: isDark ? "rgba(245,158,11,0.35)" : "rgba(124,58,237,0.22)" }]} />
        </View>

        <View style={{ gap: 10 }}>
          {buildProHooks(extractSignals(result, p1DisplayName, p2DisplayName, backendData)).map((h) => (
            <ProHookCard key={h.key} emoji={h.emoji} title={h.title} text={h.text} isDark={isDark} />
          ))}
        </View>

        <View style={[st.upgradeCard, {
          backgroundColor: isDark ? "rgba(109,40,217,0.12)" : "rgba(99,102,241,0.06)",
          borderColor: isDark ? "rgba(139,92,246,0.25)" : "rgba(99,102,241,0.15)",
        }]}>
          <Text style={{ fontSize: 20 }}>✨</Text>
          <Text style={[st.upgradeTitle, { color: isDark ? "#c4b5fd" : "#4f46e5" }]}>
            Unlock all 6 personalised insights
          </Text>
          <Text style={[st.upgradeDesc, { color: isDark ? "rgba(203,213,225,0.5)" : "#64748B" }]}>
            Pro me full hook, Dosha analysis, Marriage timing, Remedies & 12+ advanced insights dikhenge.
          </Text>
          <Pressable
            onPress={() => {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
              router.push("/subscription");
            }}
            style={({ pressed }) => ({ opacity: pressed ? 0.8 : 1, width: "100%" })}
          >
            <LinearGradient
              colors={["#6366F1", "#8B5CF6", "#a855f7"]}
              start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
              style={st.upgradeBtn}
            >
              <Text style={{ color: "#fff", fontSize: 14, fontFamily: "Nunito_700Bold" }}>
                Unlock Pro Insights
              </Text>
            </LinearGradient>
          </Pressable>
        </View>

        <Pressable
          onPress={() => {
            Haptics.selectionAsync();
            router.back();
          }}
          style={[st.recalcBtn, {
            borderColor: isDark ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.08)",
            backgroundColor: isDark ? "rgba(255,255,255,0.04)" : "rgba(0,0,0,0.02)",
          }]}
        >
          <Feather name="refresh-cw" size={14} color={isDark ? "rgba(255,255,255,0.5)" : "#64748B"} />
          <Text style={{ color: isDark ? "rgba(255,255,255,0.5)" : "#64748B", fontSize: 13, fontFamily: "Nunito_500Medium" }}>
            Recalculate / Change Details
          </Text>
        </Pressable>
      </ScrollView>
      {LockOverlay}
    </View>
  );
}

const st = StyleSheet.create({
  root: { flex: 1 },

  topBar: {
    position: "absolute", top: 0, left: 0, right: 0, zIndex: 20,
    paddingHorizontal: 16, paddingBottom: 10,
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
  },
  backBtn: {},
  backCircle: {
    width: 42, height: 42, borderRadius: 21,
    alignItems: "center", justifyContent: "center", borderWidth: 1,
  },
  headerTitle: { fontSize: 18, fontFamily: "Nunito_700Bold" },

  scrollContent: { paddingHorizontal: 18 },

  heroCard: {
    borderRadius: 24, borderWidth: 1.5, padding: 24,
    alignItems: "center", gap: 14, overflow: "hidden",
  },
  namesRow: {
    flexDirection: "row", alignItems: "center", gap: 10,
    width: "100%", justifyContent: "center",
  },
  nameChip: {
    flexDirection: "row", alignItems: "center", gap: 6,
    maxWidth: "38%",
  },
  nameText: { fontSize: 13, fontFamily: "Nunito_700Bold" },
  heartIcon: {
    width: 32, height: 32, borderRadius: 16,
    alignItems: "center", justifyContent: "center",
  },
  gradeLabel: { fontSize: 20, fontFamily: "Nunito_700Bold", textAlign: "center" },
  pctText: { fontSize: 13, fontFamily: "Nunito_500Medium" },
  heroBg: { width: "100%", height: 6, borderRadius: 3, overflow: "hidden" },
  heroFill: { height: 6, borderRadius: 3 },
  verdictText: {
    fontSize: 12, fontFamily: "Nunito_400Regular", textAlign: "center",
    lineHeight: 18, maxWidth: 280,
  },
  manglikChip: {
    flexDirection: "row", alignItems: "center", gap: 6,
    backgroundColor: "rgba(239,68,68,0.1)", borderRadius: 12,
    paddingHorizontal: 12, paddingVertical: 5,
    borderWidth: 1, borderColor: "rgba(239,68,68,0.25)",
  },
  manglikDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: "#ef4444" },

  analysisCard: {
    borderRadius: 18, borderWidth: 1, padding: 18, gap: 12, marginTop: 16,
  },
  analysisHead: { flexDirection: "row", alignItems: "center", gap: 8 },
  analysisTitle: { fontSize: 15, fontFamily: "Nunito_800ExtraBold", letterSpacing: 0.3 },
  analysisBody: { fontSize: 13, fontFamily: "Nunito_400Regular", lineHeight: 21 },
  bulletRow: { flexDirection: "row", alignItems: "flex-start", gap: 10 },
  bulletDot: { width: 6, height: 6, borderRadius: 3, marginTop: 8 },
  bulletText: { flex: 1, fontSize: 12.5, fontFamily: "Nunito_400Regular", lineHeight: 19 },

  sectionHeader: {
    flexDirection: "row", alignItems: "center", gap: 12,
    marginTop: 28, marginBottom: 16,
  },
  sectionLine: { flex: 1, height: 1 },
  sectionTitle: { fontSize: 11, fontFamily: "Nunito_700Bold", letterSpacing: 1.5 },

  kootList: { gap: 12 },

  kootCard: { borderRadius: 18, borderWidth: 1, padding: 16, gap: 10 },
  kootTop: { flexDirection: "row", alignItems: "center", gap: 12 },
  kootEmoji: {
    width: 46, height: 46, borderRadius: 14,
    alignItems: "center", justifyContent: "center",
  },
  kootName: { fontSize: 15, fontFamily: "Nunito_700Bold" },
  kootScoreRow: { flexDirection: "row", alignItems: "center", gap: 8, marginTop: 2 },
  kootBarBg: { flex: 1, height: 6, borderRadius: 3, overflow: "hidden" },
  kootBarFill: { height: 6, borderRadius: 3 },
  kootScoreText: { fontSize: 12, fontFamily: "Nunito_700Bold", minWidth: 28 },
  kootStatus: {
    width: 28, height: 28, borderRadius: 14,
    alignItems: "center", justifyContent: "center", borderWidth: 1,
  },
  kootExplanation: { fontSize: 11.5, fontFamily: "Nunito_400Regular", lineHeight: 17 },

  upgradeCard: {
    borderRadius: 18, borderWidth: 1, padding: 20,
    alignItems: "center", gap: 8, marginTop: 24,
  },
  upgradeTitle: { fontSize: 15, fontFamily: "Nunito_700Bold" },
  upgradeDesc: { fontSize: 12, fontFamily: "Nunito_400Regular", textAlign: "center", lineHeight: 18 },
  upgradeBtn: { borderRadius: 14, height: 48, alignItems: "center", justifyContent: "center", marginTop: 4 },

  recalcBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 8, borderRadius: 14, borderWidth: 1, paddingVertical: 13, marginTop: 14,
  },
});
