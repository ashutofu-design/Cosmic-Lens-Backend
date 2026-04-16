import { Feather } from "@expo/vector-icons";
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

export default function KundliMilanResultScreen() {
  const C = useC();
  const insets = useSafeAreaInsets();
  const androidSB = StatusBar.currentHeight ?? 24;
  const topPad = Platform.OS === "android" ? Math.max(insets.top, androidSB) : insets.top;
  const botPad = insets.bottom;
  const isDark = C.isDark;

  const params = useLocalSearchParams<{
    p1Name: string; p1Nak: string; p1Moon: string; p1Mang: string;
    p2Name: string; p2Nak: string; p2Moon: string; p2Mang: string;
  }>();

  const result = compute(
    params.p1Nak ?? "", params.p1Moon ?? "", params.p1Mang === "true",
    params.p2Nak ?? "", params.p2Moon ?? "", params.p2Mang === "true",
  );
  const g = grade(result.total);
  const pctTotal = Math.round((result.total / 36) * 100);

  const heroFade = useRef(new Animated.Value(0)).current;
  const heroScale = useRef(new Animated.Value(0.9)).current;

  useEffect(() => {
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    Animated.parallel([
      Animated.timing(heroFade, { toValue: 1, duration: 700, useNativeDriver: true }),
      Animated.spring(heroScale, { toValue: 1, useNativeDriver: true, speed: 10, bounciness: 6 }),
    ]).start();
  }, []);

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
          Match Results
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
                {params.p1Name || "Person 1"}
              </Text>
            </View>
            <View style={[st.heartIcon, { backgroundColor: isDark ? "rgba(236,72,153,0.15)" : "rgba(236,72,153,0.1)" }]}>
              <Text style={{ fontSize: 14 }}>💕</Text>
            </View>
            <View style={st.nameChip}>
              <Text style={{ fontSize: 14 }}>💑</Text>
              <Text style={[st.nameText, { color: isDark ? "#fce7f3" : "#831843" }]} numberOfLines={1}>
                {params.p2Name || "Person 2"}
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
            {compatibilityInsight}
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
          {strengths.map((s, i) => (
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
          {challenges.map((c, i) => (
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
            {marriageOutlook}
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

        <View style={[st.upgradeCard, {
          backgroundColor: isDark ? "rgba(109,40,217,0.12)" : "rgba(99,102,241,0.06)",
          borderColor: isDark ? "rgba(139,92,246,0.25)" : "rgba(99,102,241,0.15)",
        }]}>
          <Text style={{ fontSize: 20 }}>✨</Text>
          <Text style={[st.upgradeTitle, { color: isDark ? "#c4b5fd" : "#4f46e5" }]}>
            Want deeper insights?
          </Text>
          <Text style={[st.upgradeDesc, { color: isDark ? "rgba(203,213,225,0.5)" : "#64748B" }]}>
            Switch to Pro for Dosha analysis, Marriage timing, Remedies & 12+ advanced insights.
          </Text>
          <Pressable
            onPress={() => {
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
              router.back();
            }}
            style={({ pressed }) => ({ opacity: pressed ? 0.8 : 1, width: "100%" })}
          >
            <LinearGradient
              colors={["#6366F1", "#8B5CF6", "#a855f7"]}
              start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
              style={st.upgradeBtn}
            >
              <Text style={{ color: "#fff", fontSize: 14, fontFamily: "Nunito_700Bold" }}>
                Try Pro Version
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
