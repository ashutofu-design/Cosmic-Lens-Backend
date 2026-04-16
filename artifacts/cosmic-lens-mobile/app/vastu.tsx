import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { Magnetometer } from "expo-sensors";
import { router } from "expo-router";
import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  Animated, Dimensions, Platform, Pressable, ScrollView,
  StyleSheet, Text, View,
} from "react-native";
import Svg, {
  Circle, Defs, G, Line, LinearGradient as SvgLinearGradient,
  Path, Polygon, RadialGradient, Stop, Text as SvgText,
} from "react-native-svg";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useC } from "@/context/ThemeContext";
import { useT } from "@/hooks/useT";

// ── Compass constants ──────────────────────────────────────────────────────────
const WW   = Dimensions.get("window").width;
const SIZE = Math.min(WW - 40, 320);
const CX   = SIZE / 2;
const CY   = SIZE / 2;

const BEZEL_OUTER_R  = SIZE * 0.490;
const BEZEL_RING_R   = SIZE * 0.477;
const BEZEL_INNER_R  = SIZE * 0.458;
const ROSE_OUTER_R   = SIZE * 0.435;
const ROSE_INNER_R   = SIZE * 0.178;
const CENTER_R       = SIZE * 0.148;
const LABEL_R        = SIZE * 0.370;
const HINDI_R        = SIZE * 0.285;

// ── Vastu direction data ───────────────────────────────────────────────────────
const DIRS = [
  { deg:   0, short: "N",  hindi: "उत्तर", sub: "Uttar",    elem: "Vaayu",  color: "#f59e0b" },
  { deg:  45, short: "NE", hindi: "ईशान",  sub: "Ishaan",   elem: "Divya",  color: "#a78bfa" },
  { deg:  90, short: "E",  hindi: "पूर्व",  sub: "Poorv",    elem: "Surya",  color: "#fbbf24" },
  { deg: 135, short: "SE", hindi: "अग्नि",  sub: "Agni",     elem: "Agni",   color: "#f97316" },
  { deg: 180, short: "S",  hindi: "दक्षिण", sub: "Dakshin",  elem: "Yama",   color: "#ef4444" },
  { deg: 225, short: "SW", hindi: "नैऋत्य", sub: "Nairitya", elem: "Prithvi",color: "#84cc16" },
  { deg: 270, short: "W",  hindi: "पश्चिम", sub: "Paschim",  elem: "Jal",    color: "#38bdf8" },
  { deg: 315, short: "NW", hindi: "वायव्य", sub: "Vaayu",    elem: "Vayu",   color: "#34d399" },
];

// Compass bearing → SVG angle in radians (0° bearing = top)
function toRad(bearing: number) { return ((bearing - 90) * Math.PI) / 180; }

// Arc path for a donut sector
function wedgePath(cx: number, cy: number, r1: number, r2: number, a0: number, a1: number) {
  const s0 = toRad(a0), s1 = toRad(a1);
  const laf = a1 - a0 > 180 ? 1 : 0;
  const x1 = cx + r1 * Math.cos(s0), y1 = cy + r1 * Math.sin(s0);
  const x2 = cx + r2 * Math.cos(s0), y2 = cy + r2 * Math.sin(s0);
  const x3 = cx + r2 * Math.cos(s1), y3 = cy + r2 * Math.sin(s1);
  const x4 = cx + r1 * Math.cos(s1), y4 = cy + r1 * Math.sin(s1);
  return `M${x1},${y1} L${x2},${y2} A${r2},${r2},0,${laf},1,${x3},${y3} L${x4},${y4} A${r1},${r1},0,${laf},0,${x1},${y1}Z`;
}

// ── Compass Rose (rotates) ─────────────────────────────────────────────────────
function CompassRose() {
  const innerR = ROSE_INNER_R;
  const outerR = ROSE_OUTER_R;

  return (
    <Svg width={SIZE} height={SIZE}>
      <Defs>
        {DIRS.map(d => (
          <SvgLinearGradient key={`g-${d.short}`} id={`g-${d.short}`} x1="0" y1="0" x2="1" y2="1">
            <Stop offset="0"   stopColor={d.color} stopOpacity="1"    />
            <Stop offset="1"   stopColor={d.color} stopOpacity="0.45" />
          </SvgLinearGradient>
        ))}
        <RadialGradient id="ring-shine" cx="38%" cy="32%" r="70%">
          <Stop offset="0"   stopColor="#f9d76b" stopOpacity="0.25" />
          <Stop offset="1"   stopColor="#f9d76b" stopOpacity="0"    />
        </RadialGradient>
      </Defs>

      {/* Direction sectors */}
      {DIRS.map(d => {
        const isCardinal = d.deg % 90 === 0;
        const mid        = toRad(d.deg);
        const lx         = CX + LABEL_R * Math.cos(mid);
        const ly         = CY + LABEL_R * Math.sin(mid);
        const hx         = CX + HINDI_R  * Math.cos(mid);
        const hy         = CY + HINDI_R  * Math.sin(mid);
        const path       = wedgePath(CX, CY, innerR, outerR, d.deg - 22.4, d.deg + 22.4);

        return (
          <G key={d.short}>
            {/* Sector fill */}
            <Path d={path} fill={`url(#g-${d.short})`} opacity={isCardinal ? 1 : 0.8} />
            {/* Sector border */}
            <Path d={path} fill="none" stroke="rgba(0,0,0,0.35)" strokeWidth="0.8" />

            {/* Cardinal arrow tip */}
            {isCardinal && (() => {
              const tip   = CX + (outerR + SIZE * 0.028) * Math.cos(mid);
              const tipY  = CY + (outerR + SIZE * 0.028) * Math.sin(mid);
              const bx1   = CX + outerR * Math.cos(mid - 0.16);
              const by1   = CY + outerR * Math.sin(mid - 0.16);
              const bx2   = CX + outerR * Math.cos(mid + 0.16);
              const by2   = CY + outerR * Math.sin(mid + 0.16);
              return (
                <Polygon
                  points={`${tip},${tipY} ${bx1},${by1} ${bx2},${by2}`}
                  fill={d.color}
                  stroke="#000"
                  strokeWidth="0.5"
                />
              );
            })()}

            {/* Short code (N / NE / etc.) */}
            <SvgText
              x={lx} y={ly}
              textAnchor="middle" alignmentBaseline="middle"
              fill={isCardinal ? "#fff" : "#ffffffdd"}
              fontSize={isCardinal ? SIZE * 0.062 : SIZE * 0.046}
              fontWeight="900"
            >
              {d.short}
            </SvgText>

            {/* Hindi name */}
            <SvgText
              x={hx} y={hy}
              textAnchor="middle" alignmentBaseline="middle"
              fill={d.color}
              fontSize={SIZE * 0.034}
              fontWeight="600"
            >
              {d.hindi}
            </SvgText>
          </G>
        );
      })}

      {/* Shine overlay */}
      <Circle cx={CX} cy={CY} r={outerR} fill="url(#ring-shine)" />

      {/* Inner separator ring */}
      <Circle cx={CX} cy={CY} r={innerR}  fill="none" stroke="#f9d76b" strokeWidth="1.5" opacity="0.6" />
      <Circle cx={CX} cy={CY} r={outerR}  fill="none" stroke="#f9d76b" strokeWidth="1"   opacity="0.3" />
    </Svg>
  );
}

// ── Compass Bezel (fixed outer ring) ──────────────────────────────────────────
function CompassBezel() {
  const ticks: React.ReactElement[] = [];
  for (let i = 0; i < 72; i++) {
    const bearing = i * 5;
    const isMajor = i % 9 === 0;      // every 45°
    const isHalf  = i % 9 === 4 || i % 9 === 5; // mid-way marks
    const ang     = toRad(bearing);
    const rOuter  = BEZEL_RING_R;
    const rInner  = isMajor ? BEZEL_INNER_R - SIZE * 0.038
                  : isHalf  ? BEZEL_INNER_R - SIZE * 0.018
                             : BEZEL_INNER_R - SIZE * 0.012;
    ticks.push(
      <Line
        key={i}
        x1={CX + rOuter * Math.cos(ang)} y1={CY + rOuter * Math.sin(ang)}
        x2={CX + rInner * Math.cos(ang)} y2={CY + rInner * Math.sin(ang)}
        stroke={isMajor ? "#f9d76b" : isHalf ? "#d4a017" : "#8a6020"}
        strokeWidth={isMajor ? 2.2 : isHalf ? 1.4 : 0.8}
      />
    );
  }

  return (
    <Svg width={SIZE} height={SIZE}>
      <Defs>
        {/* Background deep radial */}
        <RadialGradient id="bg" cx="50%" cy="38%" r="65%">
          <Stop offset="0"   stopColor="#18243d" />
          <Stop offset="1"   stopColor="#060e1c" />
        </RadialGradient>
        {/* Gold ring gradient */}
        <SvgLinearGradient id="gold" x1="0" y1="0" x2="1" y2="1">
          <Stop offset="0"   stopColor="#f9e17b" />
          <Stop offset="0.35" stopColor="#e8c84b" />
          <Stop offset="0.65" stopColor="#c07b27" />
          <Stop offset="1"   stopColor="#7a4800" />
        </SvgLinearGradient>
        {/* Highlight arc */}
        <SvgLinearGradient id="goldShine" x1="0" y1="0" x2="0.5" y2="1">
          <Stop offset="0"   stopColor="#fff8dc" stopOpacity="0.5" />
          <Stop offset="1"   stopColor="#fff8dc" stopOpacity="0" />
        </SvgLinearGradient>
      </Defs>

      {/* Background circle */}
      <Circle cx={CX} cy={CY} r={BEZEL_INNER_R} fill="url(#bg)" />

      {/* Outer gold ring */}
      <Circle
        cx={CX} cy={CY} r={BEZEL_OUTER_R}
        fill="none" stroke="url(#gold)"
        strokeWidth={SIZE * 0.024}
      />
      {/* Shine arc on top of ring */}
      <Circle
        cx={CX} cy={CY} r={BEZEL_OUTER_R}
        fill="none" stroke="url(#goldShine)"
        strokeWidth={SIZE * 0.014}
        strokeDasharray={`${BEZEL_OUTER_R * Math.PI * 0.55} ${BEZEL_OUTER_R * Math.PI * 1.45}`}
        strokeDashoffset={BEZEL_OUTER_R * Math.PI * 0.85}
      />
      {/* Inner bezel accent ring */}
      <Circle cx={CX} cy={CY} r={BEZEL_INNER_R} fill="none" stroke="#c49a2a" strokeWidth="1" opacity="0.55" />

      {/* Tick marks */}
      {ticks}

      {/* Degree labels at every 45° */}
      {DIRS.map(d => {
        const ang  = toRad(d.deg);
        const r    = BEZEL_INNER_R - SIZE * 0.054;
        const lx   = CX + r * Math.cos(ang);
        const ly   = CY + r * Math.sin(ang);
        return (
          <SvgText
            key={d.short}
            x={lx} y={ly}
            textAnchor="middle" alignmentBaseline="middle"
            fill="#f9d76b"
            fontSize={SIZE * 0.032}
            fontWeight="700"
            opacity="0.85"
          >
            {d.deg === 0 ? "000" : d.deg.toString().padStart(3, "0")}°
          </SvgText>
        );
      })}
    </Svg>
  );
}

// ── Center Jewel (fixed) ───────────────────────────────────────────────────────
function CompassCenter() {
  return (
    <Svg width={SIZE} height={SIZE} style={StyleSheet.absoluteFill}>
      <Defs>
        <RadialGradient id="jewel" cx="38%" cy="32%" r="70%">
          <Stop offset="0"   stopColor="#fff0a0" />
          <Stop offset="0.45" stopColor="#d4a017" />
          <Stop offset="1"   stopColor="#5a3200" />
        </RadialGradient>
        <SvgLinearGradient id="jewelRing" x1="0" y1="0" x2="1" y2="1">
          <Stop offset="0"   stopColor="#f9e17b" />
          <Stop offset="1"   stopColor="#7a4800" />
        </SvgLinearGradient>
      </Defs>

      {/* Outer glow */}
      <Circle cx={CX} cy={CY} r={CENTER_R + SIZE * 0.022} fill="#f59e0b" opacity="0.09" />
      <Circle cx={CX} cy={CY} r={CENTER_R + SIZE * 0.012} fill="#f59e0b" opacity="0.12" />

      {/* Jewel base */}
      <Circle cx={CX} cy={CY} r={CENTER_R}           fill="url(#jewel)"   />
      <Circle cx={CX} cy={CY} r={CENTER_R}           fill="none" stroke="url(#jewelRing)" strokeWidth="2.5" />
      <Circle cx={CX} cy={CY} r={CENTER_R - SIZE * 0.012} fill="none" stroke="#f9d76b66" strokeWidth="1" />

      {/* Om symbol */}
      <SvgText
        x={CX} y={CY + SIZE * 0.006}
        textAnchor="middle" alignmentBaseline="middle"
        fill="#060e1c"
        fontSize={SIZE * 0.092}
        fontWeight="900"
      >
        ॐ
      </SvgText>

      {/* Center pivot dot */}
      <Circle cx={CX} cy={CY} r={3.5} fill="#f9d76b" />
    </Svg>
  );
}

// ── North pointer (fixed red triangle at top) ──────────────────────────────────
function NorthPointer() {
  const tipY   = SIZE * 0.028;
  const baseY  = SIZE * 0.068;
  const halfW  = SIZE * 0.032;
  return (
    <Svg width={SIZE} height={SIZE} style={StyleSheet.absoluteFill}>
      <Defs>
        <SvgLinearGradient id="redArrow" x1="0" y1="0" x2="0" y2="1">
          <Stop offset="0"  stopColor="#ff6464" />
          <Stop offset="1"  stopColor="#b91c1c" />
        </SvgLinearGradient>
      </Defs>
      {/* Shadow */}
      <Polygon
        points={`${CX},${tipY + 2} ${CX - halfW + 2},${baseY + 2} ${CX + halfW + 2},${baseY + 2}`}
        fill="#00000044"
      />
      {/* Red arrow body */}
      <Polygon
        points={`${CX},${tipY} ${CX - halfW},${baseY} ${CX + halfW},${baseY}`}
        fill="url(#redArrow)"
      />
      {/* Gold outline */}
      <Polygon
        points={`${CX},${tipY} ${CX - halfW},${baseY} ${CX + halfW},${baseY}`}
        fill="none" stroke="#f9d76b" strokeWidth="1.2"
      />
    </Svg>
  );
}

// ── Magnetometer hook ──────────────────────────────────────────────────────────
function useMagnetometerHeading() {
  const [heading,  setHeading]  = useState(0);
  const [isLive,   setIsLive]   = useState(false);
  const contRef  = useRef(0);
  const animVal  = useRef(new Animated.Value(0)).current;

  const update = useCallback((raw: number) => {
    let diff = raw - (contRef.current % 360);
    if (diff >  180) diff -= 360;
    if (diff < -180) diff += 360;
    contRef.current += diff;
    setHeading(((raw % 360) + 360) % 360);
    Animated.spring(animVal, {
      toValue:         -contRef.current,
      tension:         22,
      friction:        7,
      useNativeDriver: true,
    }).start();
  }, [animVal]);

  useEffect(() => {
    if (Platform.OS === "web") return;
    Magnetometer.setUpdateInterval(120);
    const sub = Magnetometer.addListener(({ x, y }) => {
      let angle = Math.atan2(y, x) * (180 / Math.PI);
      angle = (360 - angle) % 360;
      setIsLive(true);
      update(angle);
    });
    return () => sub.remove();
  }, [update]);

  const rotateStyle = {
    transform: [{
      rotate: animVal.interpolate({
        inputRange:  [-36000, 36000],
        outputRange: ["-36000deg", "36000deg"],
        extrapolate: "extend",
      }),
    }],
  };

  return { heading, isLive, rotateStyle };
}

// ── Premium Vastu Compass ──────────────────────────────────────────────────────
function VastuCompass() {
  const C = useC();
  const { heading, isLive, rotateStyle } = useMagnetometerHeading();

  const currentDir = DIRS.reduce((best, d) => {
    const diffBest = Math.abs(((heading - best.deg + 540) % 360) - 180);
    const diffCurr = Math.abs(((heading - d.deg   + 540) % 360) - 180);
    return diffCurr < diffBest ? d : best;
  });

  return (
    <View style={[cp.outer, { backgroundColor: C.bgCard, borderColor: C.border }]}>
      {/* ── Header row ── */}
      <View style={cp.headerRow}>
        <View>
          <Text style={[cp.heading, { color: C.text }]}>Vastu Compass</Text>
          <Text style={[cp.subhead, { color: C.textMuted }]}>वास्तु कम्पास</Text>
        </View>
        <View style={[cp.badge, { backgroundColor: isLive ? (C.isDark ? "#16a34a18" : "#DCFCE7") : (C.isDark ? "#64748b18" : "#F1F5F9") }]}>
          <View style={[cp.dot, { backgroundColor: isLive ? "#22c55e" : "#64748b" }]} />
          <Text style={[cp.badgeTxt, { color: isLive ? "#22c55e" : "#94a3b8" }]}>
            {isLive ? "LIVE" : "STATIC"}
          </Text>
        </View>
      </View>

      {/* ── Heading display ── */}
      <View style={cp.hdgRow}>
        <Text style={[cp.hdgNum, { color: isLive ? currentDir.color : C.textMuted }]}>
          {isLive ? `${Math.round(heading).toString().padStart(3, "0")}°` : "---°"}
        </Text>
        <View>
          <Text style={[cp.hdgDir, { color: isLive ? currentDir.color : C.textMuted }]}>
            {isLive ? `${currentDir.short} · ${currentDir.sub}` : "Sensor inactive"}
          </Text>
          <Text style={[cp.hdgHindi, { color: C.textMuted }]}>
            {isLive ? currentDir.hindi : "Move device to activate"}
          </Text>
        </View>
      </View>

      {/* ── Compass graphic ── */}
      <View style={[cp.compassWrap, { width: SIZE, height: SIZE }]}>
        {/* Layer 1: Fixed outer bezel */}
        <View style={StyleSheet.absoluteFill}>
          <CompassBezel />
        </View>

        {/* Layer 2: Rotating rose */}
        <Animated.View style={[StyleSheet.absoluteFill, rotateStyle]}>
          <CompassRose />
        </Animated.View>

        {/* Layer 3: Fixed center jewel */}
        <View style={StyleSheet.absoluteFill}>
          <CompassCenter />
        </View>

        {/* Layer 4: Fixed north pointer */}
        <NorthPointer />
      </View>

      {/* ── Legend ── */}
      <View style={cp.legend}>
        {DIRS.filter(d => d.deg % 90 === 0).map(d => (
          <View key={d.short} style={cp.legendItem}>
            <View style={[cp.legendDot, { backgroundColor: d.color }]} />
            <Text style={[cp.legendTxt, { color: C.textMuted }]}>{d.short} · {d.sub}</Text>
          </View>
        ))}
      </View>
      <Text style={[cp.note, { color: C.textMuted }]}>
        🔴 Red arrow = North · Compass rose rotates with device · NE = Ishaan (most auspicious)
      </Text>
    </View>
  );
}

const cp = StyleSheet.create({
  outer:      { borderRadius: 20, borderWidth: 1, padding: 16, gap: 14, overflow: "hidden" },
  headerRow:  { flexDirection: "row", alignItems: "flex-start", justifyContent: "space-between" },
  heading:    { fontSize: 16, fontWeight: "800" },
  subhead:    { fontSize: 11, marginTop: 2 },
  badge:      { flexDirection: "row", alignItems: "center", gap: 5, paddingHorizontal: 10, paddingVertical: 4, borderRadius: 20 },
  dot:        { width: 6, height: 6, borderRadius: 3 },
  badgeTxt:   { fontSize: 10, fontWeight: "700", letterSpacing: 1.2 },
  hdgRow:     { flexDirection: "row", alignItems: "center", gap: 14 },
  hdgNum:     { fontSize: 36, fontWeight: "900", fontVariant: ["tabular-nums"] as any, minWidth: 80 },
  hdgDir:     { fontSize: 15, fontWeight: "700" },
  hdgHindi:   { fontSize: 12, marginTop: 2 },
  compassWrap:{ alignSelf: "center", position: "relative" },
  legend:     { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  legendItem: { flexDirection: "row", alignItems: "center", gap: 5 },
  legendDot:  { width: 8, height: 8, borderRadius: 4 },
  legendTxt:  { fontSize: 11 },
  note:       { fontSize: 11, lineHeight: 17, textAlign: "center" },
});

// ── Vastu Data ────────────────────────────────────────────────────────────────

interface VastuTip {
  icon: string;
  text: string;
}
interface VastuRoom {
  key: string;
  name: string;
  nameHindi: string;
  emoji: string;
  idealDir: string;
  color: string;
  bg: string;
  border: string;
  element: string;
  elementIcon: string;
  importance: string;
  dos: VastuTip[];
  donts: VastuTip[];
  remedies: string[];
}

const ROOMS: VastuRoom[] = [
  {
    key:"main-door",
    name:"Mukhya Dwar",
    nameHindi:"मुख्य द्वार",
    emoji:"🚪",
    idealDir:"North, East, or North-East (NE) — Best Directions",
    color:"#f59e0b",
    bg:"rgba(245,158,11,0.05)",
    border:"rgba(245,158,11,0.2)",
    element:"Vaayu",
    elementIcon:"🌬️",
    importance:"The main door is the gateway for positive energy and prosperity. Its direction is the most important Vastu factor for the entire home.",
    dos:[
      { icon:"✅", text:"North-East (NE) or North direction is the best for the main door" },
      { icon:"✅", text:"Use a solid, heavy wooden door" },
      { icon:"✅", text:"Place a Swastik or Om symbol above the entrance" },
      { icon:"✅", text:"The door should open inward" },
      { icon:"✅", text:"Keep the nameplate clean and clearly visible" },
      { icon:"✅", text:"Ensure the entrance is well-lit at all times" },
    ],
    donts:[
      { icon:"❌", text:"Avoid a column or pillar directly in front of the main door" },
      { icon:"❌", text:"Avoid placing the main door in the South (S) or South-West (SW)" },
      { icon:"❌", text:"Do not pile up footwear outside the main door" },
      { icon:"❌", text:"Never leave the door squeaky or broken — fix it promptly" },
      { icon:"❌", text:"Do not have a bathroom directly facing the main entrance" },
    ],
    remedies:[
      "Place a 'Shri' or Ganpati symbol on the door for blessings",
      "Draw rangoli or place fresh flowers at the entrance every morning",
      "Chant 'Om Namah Shivaya' when entering the home",
    ],
  },
  {
    key:"living",
    name:"Baithak / Drawing Room",
    nameHindi:"बैठक / ड्रॉइंग रूम",
    emoji:"🛋️",
    idealDir:"North or East wing of the home",
    color:"#fbbf24",
    bg:"rgba(251,191,36,0.05)",
    border:"rgba(251,191,36,0.2)",
    element:"Agni + Vaayu",
    elementIcon:"🔥",
    importance:"The living room is the center of a home's social energy. Guests are welcomed here and the family gathers in this space.",
    dos:[
      { icon:"✅", text:"Place sofa and furniture in the NW or SW corner" },
      { icon:"✅", text:"TV or entertainment unit should face East or North wall" },
      { icon:"✅", text:"East-facing windows let in beneficial morning sunlight" },
      { icon:"✅", text:"Use light colors — white, cream, or light yellow" },
      { icon:"✅", text:"Hang a clock on the North or East wall" },
    ],
    donts:[
      { icon:"❌", text:"Do not place the sofa directly facing the main door" },
      { icon:"❌", text:"Avoid dark colors like black or dark red" },
      { icon:"❌", text:"Remove broken or damaged furniture immediately" },
      { icon:"❌", text:"Do not place a mirror in the corner near the door" },
    ],
    remedies:[
      "Place a crystal ball in the North-East corner to enhance positivity",
      "Keep a Laughing Buddha on the North wall for wealth",
      "Place fresh flowers or plants in the NE or East corner",
    ],
  },
  {
    key:"kitchen",
    name:"Rasoi / Kitchen",
    nameHindi:"रसोई",
    emoji:"🍳",
    idealDir:"South-East (SE) — Agni (Fire) Zone",
    color:"#f97316",
    bg:"rgba(249,115,22,0.05)",
    border:"rgba(249,115,22,0.2)",
    element:"Agni",
    elementIcon:"🔥",
    importance:"The kitchen represents the fire element. A correctly placed kitchen promotes the health and prosperity of the entire family.",
    dos:[
      { icon:"✅", text:"Place the stove/gas burner in the SE corner — the Fire zone" },
      { icon:"✅", text:"Face East while cooking for positive energy" },
      { icon:"✅", text:"Place the sink near the NE or North wall" },
      { icon:"✅", text:"Use yellow, orange, or cream colors in the kitchen" },
      { icon:"✅", text:"Windows in the SE or East direction are ideal" },
    ],
    donts:[
      { icon:"❌", text:"Never have the kitchen directly facing or above a bathroom" },
      { icon:"❌", text:"Never place the stove in the NE corner" },
      { icon:"❌", text:"Avoid dark colors in the kitchen" },
      { icon:"❌", text:"Avoid building a kitchen in the North or North-East" },
    ],
    remedies:[
      "Occasionally offer the first roti to a cow for blessings",
      "Place a photo of Annapurna Mata (goddess of food) in the kitchen",
      "Burning camphor in the kitchen is considered auspicious",
    ],
  },
  {
    key:"master-bedroom",
    name:"Master Bedroom",
    nameHindi:"मुख्य शयनकक्ष",
    emoji:"🛏️",
    idealDir:"South-West (SW) — Best for the head of household",
    color:"#a78bfa",
    bg:"rgba(167,139,250,0.05)",
    border:"rgba(167,139,250,0.2)",
    element:"Prithvi",
    elementIcon:"🌍",
    importance:"The head of the household sleeps in the master bedroom. The South-West direction provides stability, strength, and prosperity.",
    dos:[
      { icon:"✅", text:"Place the bed near the SW or South wall" },
      { icon:"✅", text:"Sleep with your head pointing South or East" },
      { icon:"✅", text:"Keep wardrobes and heavy furniture on the South or West wall" },
      { icon:"✅", text:"Use light pink, beige, or lavender as room colors" },
      { icon:"✅", text:"Cover mirrors in the bedroom at night" },
    ],
    donts:[
      { icon:"❌", text:"Avoid sleeping with your head pointing North — it causes health issues" },
      { icon:"❌", text:"Do not place the bed directly under a beam" },
      { icon:"❌", text:"Avoid TV in the bedroom; cover it if present" },
      { icon:"❌", text:"Do not build the master bedroom in the NE corner" },
      { icon:"❌", text:"Do not sleep with feet pointing toward the door" },
    ],
    remedies:[
      "Keep rose quartz or amethyst crystals in the bedroom",
      "Place a bowl of sea salt under the bed to absorb negative energy",
      "Hang a couple's photo on the South wall for harmony",
    ],
  },
  {
    key:"children",
    name:"Bachon ka Kamra",
    nameHindi:"बच्चों का कमरा",
    emoji:"📚",
    idealDir:"West or North-West (NW)",
    color:"#4ade80",
    bg:"rgba(74,222,128,0.05)",
    border:"rgba(74,222,128,0.2)",
    element:"Vaayu",
    elementIcon:"🌬️",
    importance:"The direction of the children's room affects their studies, creativity, and overall health.",
    dos:[
      { icon:"✅", text:"Place the study desk facing East or North for focus" },
      { icon:"✅", text:"Keep the bed near the West or NW wall for good sleep" },
      { icon:"✅", text:"Store books on the East or North wall" },
      { icon:"✅", text:"Use green, yellow, or light blue as room colors" },
      { icon:"✅", text:"Keep a photo of Saraswati ji or a Vidya Yantra in the room" },
    ],
    donts:[
      { icon:"❌", text:"Do not place the study chair in the SE corner (Fire zone)" },
      { icon:"❌", text:"Avoid TV in children's rooms entirely" },
      { icon:"❌", text:"Do not keep a heavy wardrobe near the child's head" },
    ],
    remedies:[
      "Place a Saraswati Yantra on the study table to improve concentration",
      "Green plants in the room enhance creativity and fresh energy",
      "Recite Saraswati Chalisa in the morning before exams",
    ],
  },
  {
    key:"pooja",
    name:"Pooja Ghar",
    nameHindi:"पूजा घर",
    emoji:"🪔",
    idealDir:"North-East (NE) — Ishaan Zone (Most Sacred)",
    color:"#f59e0b",
    bg:"rgba(245,158,11,0.06)",
    border:"rgba(245,158,11,0.25)",
    element:"Jal + Aakash",
    elementIcon:"💧",
    importance:"The prayer room is the holiest space in the home. The North-East (Ishaan) corner is considered the abode of the divine.",
    dos:[
      { icon:"✅", text:"Always place the temple/altar in the NE or East direction" },
      { icon:"✅", text:"Face East or North while praying" },
      { icon:"✅", text:"Ensure deity idols are placed at eye level or higher" },
      { icon:"✅", text:"Keep the prayer space clean and well-lit at all times" },
      { icon:"✅", text:"White, yellow, or orange are the best colors for this room" },
    ],
    donts:[
      { icon:"❌", text:"Do not place the temple inside a bedroom" },
      { icon:"❌", text:"Never have a toilet above or below the prayer room" },
      { icon:"❌", text:"Do not keep broken or damaged idols" },
      { icon:"❌", text:"Avoid placing the temple in the South direction" },
    ],
    remedies:[
      "Light a ghee lamp in the temple every morning",
      "Burn camphor incense in the prayer room to amplify divine energy",
      "Offer marigold flowers every Friday for blessings",
    ],
  },
  {
    key:"bathroom",
    name:"Bathroom / Shauchalaya",
    nameHindi:"बाथरूम / शौचालय",
    emoji:"🚿",
    idealDir:"North-West (NW) or West — Ideal Placement",
    color:"#60a5fa",
    bg:"rgba(96,165,250,0.05)",
    border:"rgba(96,165,250,0.2)",
    element:"Jal",
    elementIcon:"💧",
    importance:"An incorrectly placed bathroom can bring negativity, health issues, and financial difficulties into the home.",
    dos:[
      { icon:"✅", text:"NW or West is the best location for bathrooms" },
      { icon:"✅", text:"Place the geyser or water heater in the SE corner" },
      { icon:"✅", text:"Exhaust fan or window should be in East or North" },
      { icon:"✅", text:"Toilet seat should face the South or West wall" },
      { icon:"✅", text:"Keep the bathroom clean and dry at all times" },
    ],
    donts:[
      { icon:"❌", text:"Never place a bathroom in the NE (Ishaan) corner" },
      { icon:"❌", text:"Avoid having a bathroom adjacent to the prayer room" },
      { icon:"❌", text:"Always keep the bathroom door closed" },
      { icon:"❌", text:"Fix leaking taps immediately — they drain wealth energy" },
    ],
    remedies:[
      "Place sea salt or a lemon outside the bathroom to absorb negativity",
      "Add a few drops of neem or eucalyptus oil to the bathroom water",
      "Place an Om sticker on the door if the bathroom is in the NE",
    ],
  },
  {
    key:"study",
    name:"Study / Office Room",
    nameHindi:"अध्ययन / कार्यालय",
    emoji:"💼",
    idealDir:"North — For Wealth and Career Growth",
    color:"#34d399",
    bg:"rgba(52,211,153,0.05)",
    border:"rgba(52,211,153,0.2)",
    element:"Vaayu + Aakash",
    elementIcon:"🌬️",
    importance:"Having the home office or study in the North boosts career growth, wealth, and focus.",
    dos:[
      { icon:"✅", text:"Place the desk facing a window or door for positive energy flow" },
      { icon:"✅", text:"Face North or East while working" },
      { icon:"✅", text:"Place a safe or locker in the SW corner for financial security" },
      { icon:"✅", text:"Keep a solid wall behind you for strong support" },
      { icon:"✅", text:"Green or blue are auspicious colors for an office" },
    ],
    donts:[
      { icon:"❌", text:"Do not place the desk in a corner — it blocks energy flow" },
      { icon:"❌", text:"Avoid sitting with your back to the door while working" },
      { icon:"❌", text:"Do not let the office door directly face a wall" },
      { icon:"❌", text:"Do not keep clutter or garbage in the office space" },
    ],
    remedies:[
      "Place a Kuber Yantra on the North wall for wealth and career growth",
      "Keep a green lucky bamboo plant in the North corner",
      "Chant 'Om Ganeshaya Namah' before beginning work each day",
    ],
  },
];

// ── Room Card ─────────────────────────────────────────────────────────────────
function RoomCard({ room }: { room: VastuRoom }) {
  const [open, setOpen] = useState(false);
  const [tab,  setTab]  = useState<"dos"|"donts"|"remedies">("dos");
  const C = useC();

  return (
    <Pressable
      style={[c.card, { borderColor: C.isDark ? room.border : `${room.color}30`, backgroundColor: C.isDark ? room.bg : C.bgCard }]}
      onPress={() => { setOpen(v => !v); Haptics.selectionAsync(); }}
    >
      {/* Header */}
      <View style={c.cardHeader}>
        <View style={[c.iconBubble, { backgroundColor:`${room.color}15` }]}>
          <Text style={{ fontSize:20 }}>{room.emoji}</Text>
        </View>
        <View style={{ flex:1 }}>
          <Text style={[c.roomName, { color:room.color }]}>{room.name}</Text>
          <Text style={[c.roomHindi, { color: C.textMuted }]}>{room.nameHindi}</Text>
        </View>
        <View style={[c.elemPill, { backgroundColor:`${room.color}10` }]}>
          <Text style={{ fontSize:10 }}>{room.elementIcon}</Text>
          <Text style={[c.elemText, { color:room.color }]}>{room.element}</Text>
        </View>
        <Feather name={open ? "chevron-up" : "chevron-down"} size={15} color={C.textMuted} style={{ marginLeft:8 }} />
      </View>

      {/* Direction bar */}
      <View style={c.dirRow}>
        <Feather name="compass" size={11} color={C.textMuted} />
        <Text style={[c.dirText, { color: C.textMuted }]}>{room.idealDir}</Text>
      </View>

      {/* Expanded content */}
      {open && (
        <View style={c.expanded}>
          <Text style={[c.importance, { color: C.textMuted }]}>{room.importance}</Text>
          <View style={c.tabRow}>
            {(["dos","donts","remedies"] as const).map(t => (
              <Pressable key={t} onPress={() => setTab(t)}
                style={[c.tabBtn, { borderColor: C.border, backgroundColor: C.bgCard2 },
                  tab===t && { backgroundColor:`${room.color}15`, borderColor:`${room.color}30` }]}>
                <Text style={[c.tabText, { color: C.textMuted }, tab===t && { color:room.color }]}>
                  {t==="dos" ? "Do ✅" : t==="donts" ? "Don't ❌" : "Remedies 🙏"}
                </Text>
              </Pressable>
            ))}
          </View>
          {tab === "dos" && (
            <View style={{ gap:8 }}>
              {room.dos.map((d,i) => (
                <View key={i} style={c.tipRow}>
                  <Text style={c.tipIcon}>{d.icon}</Text>
                  <Text style={[c.tipText, { color: C.textMuted }]}>{d.text}</Text>
                </View>
              ))}
            </View>
          )}
          {tab === "donts" && (
            <View style={{ gap:8 }}>
              {room.donts.map((d,i) => (
                <View key={i} style={c.tipRow}>
                  <Text style={c.tipIcon}>{d.icon}</Text>
                  <Text style={[c.tipText, { color:"#f87171" }]}>{d.text}</Text>
                </View>
              ))}
            </View>
          )}
          {tab === "remedies" && (
            <View style={{ gap:8 }}>
              {room.remedies.map((r,i) => (
                <View key={i} style={c.tipRow}>
                  <View style={[c.remedyNum, { backgroundColor: C.bgCard2 }]}>
                    <Text style={{ color:room.color, fontSize:10, fontWeight:"700" }}>{i+1}</Text>
                  </View>
                  <Text style={[c.tipText, { color: C.textMuted }]}>{r}</Text>
                </View>
              ))}
            </View>
          )}
        </View>
      )}
    </Pressable>
  );
}

// ── Main Screen ───────────────────────────────────────────────────────────────
export default function VastuScreen() {
  const insets = useSafeAreaInsets();
  const C      = useC();
  const t      = useT();
  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  return (
    <View style={[s.root, { backgroundColor: C.bg }]}>
      <View style={[s.header, { paddingTop: topPad + 8, borderBottomColor: C.border }]}>
        <Pressable onPress={() => router.back()} style={s.back}>
          <Feather name="arrow-left" size={20} color={C.textMuted} />
        </Pressable>
        <View style={{ flex:1 }}>
          <Text style={[s.title, { color: C.text }]}>{t.vastuTitle}</Text>
          <Text style={[s.titleHindi, { color: C.textMuted }]}>वास्तु शास्त्र — Room-wise Guidance</Text>
        </View>
      </View>

      <ScrollView
        contentContainerStyle={[s.content, { paddingBottom: botPad + 30 }]}
        showsVerticalScrollIndicator={false}
      >
        {/* Intro */}
        <View style={[s.introCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Text style={{ fontSize:24 }}>🏠</Text>
          <View style={{ flex:1 }}>
            <Text style={[s.introTitle, { color: C.text }]}>What is Vastu Shastra?</Text>
            <Text style={[s.introBody, { color: C.textMuted }]}>
              Vastu Shastra is an ancient Indian science of architecture. Correct directions bring
              positive energy, happiness, health, and prosperity to your home.
            </Text>
          </View>
        </View>

        {/* ── Premium Compass ── */}
        <VastuCompass />

        {/* Section label */}
        <Text style={[s.sectionLabel, { color: C.accent }]}>ROOM-WISE VASTU GUIDE</Text>
        <Text style={[s.sectionSub, { color: C.textMuted }]}>Tap any card to see dos, don'ts, and remedies</Text>

        {/* Room cards */}
        {ROOMS.map(room => <RoomCard key={room.key} room={room} />)}

        {/* General tips */}
        <View style={[s.genCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Text style={[s.genTitle, { color: C.text }]}>⚡ General Vastu Tips</Text>
          {[
            "Keep the home free of clutter — blocked spaces block energy flow",
            "Ensure your home is well-lit — darkness invites negativity",
            "Fix squeaky or broken doors promptly",
            "Keep indoor plants — they bring life energy into the home",
            "Remove broken or damaged items immediately",
            "A running water feature (fountain or aquarium) in the North is auspicious",
          ].map((tip,i) => (
            <View key={i} style={s.genRow}>
              <View style={[s.genDot, { backgroundColor: C.textDim }]} />
              <Text style={[s.genText, { color: C.textMuted }]}>{tip}</Text>
            </View>
          ))}
        </View>

        {/* Disclaimer */}
        <View style={[s.disclaimer, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Feather name="info" size={12} color={C.textMuted} />
          <Text style={[s.disclaimerText, { color: C.textMuted }]}>
            This is a general Vastu guide. For your home specifically, always consult a qualified
            Vastu expert for personalized advice.
          </Text>
        </View>
      </ScrollView>
    </View>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const s = StyleSheet.create({
  root:       { flex:1 },
  header:     { flexDirection:"row", alignItems:"center", gap:12, paddingHorizontal:16, paddingBottom:14, borderBottomWidth:1 },
  back:       { width:36, height:36, alignItems:"center", justifyContent:"center" },
  title:      { fontSize:17, fontWeight:"800" },
  titleHindi: { fontSize:10, marginTop:1 },
  content:    { paddingHorizontal:16, gap:12, paddingTop:14 },
  sectionLabel:{ fontSize:10, fontWeight:"800", letterSpacing:2.5, marginBottom:2 },
  sectionSub: { fontSize:11, marginBottom:4, marginTop:-6 },
  introCard:  { flexDirection:"row", alignItems:"flex-start", gap:12, borderRadius:14, borderWidth:1, padding:14 },
  introTitle: { fontSize:13, fontWeight:"700", marginBottom:5 },
  introBody:  { fontSize:12, lineHeight:19 },
  genCard:    { borderRadius:14, borderWidth:1, padding:14, gap:10 },
  genTitle:   { fontSize:13, fontWeight:"700", marginBottom:4 },
  genRow:     { flexDirection:"row", alignItems:"flex-start", gap:10 },
  genDot:     { width:6, height:6, borderRadius:3, marginTop:5, flexShrink:0 },
  genText:    { fontSize:12, lineHeight:19, flex:1 },
  disclaimer: { flexDirection:"row", alignItems:"flex-start", gap:8, borderRadius:10, padding:12, borderWidth:1 },
  disclaimerText: { fontSize:11, lineHeight:17, flex:1 },
});

const c = StyleSheet.create({
  card:       { borderRadius:14, borderWidth:1, padding:14, gap:8 },
  cardHeader: { flexDirection:"row", alignItems:"center", gap:10 },
  iconBubble: { width:44, height:44, borderRadius:12, alignItems:"center", justifyContent:"center", flexShrink:0 },
  roomName:   { fontSize:13, fontWeight:"700" },
  roomHindi:  { fontSize:10, marginTop:2 },
  elemPill:   { flexDirection:"row", alignItems:"center", gap:4, borderRadius:8, paddingHorizontal:7, paddingVertical:3 },
  elemText:   { fontSize:9, fontWeight:"700" },
  dirRow:     { flexDirection:"row", alignItems:"center", gap:6 },
  dirText:    { fontSize:11, flex:1 },
  importance: { fontSize:12, lineHeight:19 },
  expanded:   { gap:12 },
  tabRow:     { flexDirection:"row", gap:6 },
  tabBtn:     { flex:1, paddingVertical:6, alignItems:"center", borderRadius:8, borderWidth:1 },
  tabText:    { fontSize:11, fontWeight:"600" },
  tipRow:     { flexDirection:"row", alignItems:"flex-start", gap:8 },
  tipIcon:    { fontSize:13, marginTop:1, flexShrink:0 },
  tipText:    { fontSize:12, lineHeight:19, flex:1 },
  remedyNum:  { width:20, height:20, borderRadius:10, alignItems:"center", justifyContent:"center", flexShrink:0, marginTop:1 },
});
