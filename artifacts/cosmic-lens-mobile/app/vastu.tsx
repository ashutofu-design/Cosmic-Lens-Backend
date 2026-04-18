import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { Image } from "expo-image";
import * as ImagePicker from "expo-image-picker";
import { LinearGradient } from "expo-linear-gradient";
import { Magnetometer } from "expo-sensors";
import { router } from "expo-router";
import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Animated, Dimensions, Linking, Modal, Platform, Pressable, ScrollView,
  StyleSheet, Text, View,
} from "react-native";
import Svg, {
  Circle, Defs, G, Line, LinearGradient as SvgLinearGradient,
  Path, Polygon, RadialGradient, Stop, Text as SvgText,
} from "react-native-svg";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useC } from "@/context/ThemeContext";
import { useT } from "@/hooks/useT";
import { useUser } from "@/context/UserContext";
import { API_BASE } from "@/lib/apiConfig";

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
const LABEL_R        = SIZE * 0.400; // octagon outer-edge zone (short code)
const HINDI_R        = SIZE * 0.300; // octagon mid-sector zone (deity name)

// Octagon helpers — 8 vertices with vertex-at-top
function octagonPoints(r: number): [number, number][] {
  const pts: [number, number][] = [];
  for (let i = 0; i < 8; i++) {
    const a = (-Math.PI / 2) + (i * Math.PI * 2) / 8;
    pts.push([CX + r * Math.cos(a), CY + r * Math.sin(a)]);
  }
  return pts;
}
function octagonPointsStr(r: number): string {
  return octagonPoints(r).map(p => `${p[0]},${p[1]}`).join(" ");
}
// Triangular wedge slice for one of 8 sectors
function octSlice(idx: number, rOut: number, rIn: number): string {
  const a0 = (-Math.PI / 2) + ((idx - 0.5) * Math.PI * 2) / 8;
  const a1 = (-Math.PI / 2) + ((idx + 0.5) * Math.PI * 2) / 8;
  const x1 = CX + rIn  * Math.cos(a0), y1 = CY + rIn  * Math.sin(a0);
  const x2 = CX + rOut * Math.cos(a0), y2 = CY + rOut * Math.sin(a0);
  const x3 = CX + rOut * Math.cos(a1), y3 = CY + rOut * Math.sin(a1);
  const x4 = CX + rIn  * Math.cos(a1), y4 = CY + rIn  * Math.sin(a1);
  return `M${x1},${y1} L${x2},${y2} L${x3},${y3} L${x4},${y4} Z`;
}

// ── Vastu direction data ───────────────────────────────────────────────────────
// Gold & Black premium palette — alternating bright gold (cardinals) and antique gold (inter-cardinals)
const GOLD_BRIGHT  = "#f9d76b"; // 24k bright
const GOLD_ANTIQUE = "#b8893a"; // aged bronze-gold
const DIRS = [
  { deg:   0, short: "N",  hindi: "उत्तर", sub: "North",     deity: "Kubera", meaning: "WEALTH",   elem: "Vaayu",  color: GOLD_BRIGHT  },
  { deg:  45, short: "NE", hindi: "ईशान",  sub: "Ishaan",    deity: "Ishaan", meaning: "DIVINITY", elem: "Divya",  color: GOLD_ANTIQUE },
  { deg:  90, short: "E",  hindi: "पूर्व",  sub: "East",      deity: "Surya",  meaning: "ENERGY",   elem: "Surya",  color: GOLD_BRIGHT  },
  { deg: 135, short: "SE", hindi: "अग्नि",  sub: "Agni",      deity: "Agni",   meaning: "FIRE",     elem: "Agni",   color: GOLD_ANTIQUE },
  { deg: 180, short: "S",  hindi: "दक्षिण", sub: "South",     deity: "Yama",   meaning: "HONOR",    elem: "Yama",   color: GOLD_BRIGHT  },
  { deg: 225, short: "SW", hindi: "नैऋत्य", sub: "Niriti",    deity: "Niriti", meaning: "EARTH",    elem: "Prithvi",color: GOLD_ANTIQUE },
  { deg: 270, short: "W",  hindi: "पश्चिम", sub: "West",      deity: "Varuna", meaning: "WATER",    elem: "Jal",    color: GOLD_BRIGHT  },
  { deg: 315, short: "NW", hindi: "वायव्य", sub: "Vayu",      deity: "Vayu",   meaning: "AIR",      elem: "Vayu",   color: GOLD_ANTIQUE },
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

// ── Compass Rose (rotates) — Octagon Dial ─────────────────────────────────────
function CompassRose() {
  const R_OUT_OCT  = SIZE * 0.48;
  const R_INNER_OCT = SIZE * 0.17;

  return (
    <Svg width={SIZE} height={SIZE}>
      <Defs>
        {/* Per-sector vertical gradient — color fades to BG */}
        {DIRS.map((d, i) => (
          <SvgLinearGradient key={`og-${i}`} id={`og-${i}`} x1="0.5" y1="0" x2="0.5" y2="1">
            <Stop offset="0" stopColor={d.color} stopOpacity={d.color === GOLD_BRIGHT ? "0.22" : "0.10"} />
            <Stop offset="1" stopColor="#05070d" stopOpacity="1" />
          </SvgLinearGradient>
        ))}
      </Defs>

      {/* 8 triangular sector slices */}
      {DIRS.map((d, i) => {
        const a0 = (-Math.PI / 2) + ((i - 0.5) * Math.PI * 2) / 8;
        const x1 = CX + R_INNER_OCT * Math.cos(a0), y1 = CY + R_INNER_OCT * Math.sin(a0);
        const x2 = CX + R_OUT_OCT * 0.94 * Math.cos(a0), y2 = CY + R_OUT_OCT * 0.94 * Math.sin(a0);
        return (
          <G key={`s-${i}`}>
            <Path d={octSlice(i, R_OUT_OCT * 0.94, R_INNER_OCT)} fill={`url(#og-${i})`} />
            {/* radial divider line */}
            <Line x1={x1} y1={y1} x2={x2} y2={y2} stroke="#f9d76b" strokeWidth="0.7" opacity="0.5" />
          </G>
        );
      })}

      {/* Direction labels — short code + deity name */}
      {DIRS.map((d, i) => {
        const a = (-Math.PI / 2) + (i * Math.PI * 2) / 8;
        const lx = CX + LABEL_R * Math.cos(a), ly = CY + LABEL_R * Math.sin(a);
        const dx = CX + HINDI_R * Math.cos(a), dy = CY + HINDI_R * Math.sin(a);
        const isCard = d.deg % 90 === 0;
        return (
          <G key={`l-${i}`}>
            <SvgText
              x={lx} y={ly}
              textAnchor="middle" alignmentBaseline="middle"
              fill={isCard ? "#fff8dc" : "#f9d76b"}
              fontSize={isCard ? SIZE * 0.062 : SIZE * 0.044}
              fontWeight="900"
              letterSpacing={1}
            >
              {d.short}
            </SvgText>
            <SvgText
              x={dx} y={dy + (isCard ? SIZE * 0.036 : SIZE * 0.030)}
              textAnchor="middle" alignmentBaseline="middle"
              fill={d.color}
              fontSize={SIZE * 0.026}
              fontWeight="700"
              letterSpacing={1.3}
            >
              {d.deity.toUpperCase()}
            </SvgText>
          </G>
        );
      })}

      {/* Inner octagon outline (separator) */}
      <Polygon
        points={octagonPointsStr(R_INNER_OCT)}
        fill="none"
        stroke="#f9d76b"
        strokeWidth="1.4"
        opacity="0.85"
      />
      {/* 8 rivets on inner octagon vertices */}
      {octagonPoints(R_INNER_OCT).map((p, i) => (
        <G key={`rv-${i}`}>
          <Circle cx={p[0]} cy={p[1]} r={SIZE * 0.010} fill="#3a2404" />
          <Circle cx={p[0]} cy={p[1]} r={SIZE * 0.007} fill="#f9d76b" />
          <Circle cx={p[0] - 0.6} cy={p[1] - 0.6} r={SIZE * 0.0025} fill="#fff8dc" opacity="0.9" />
        </G>
      ))}
    </Svg>
  );
}

// ── Compass Bezel (fixed octagon frame) ───────────────────────────────────────
function CompassBezel() {
  const R_OUT_OCT = SIZE * 0.48;
  const outerPts  = octagonPointsStr(R_OUT_OCT);
  const innerPts  = octagonPoints(R_OUT_OCT * 0.96);

  return (
    <Svg width={SIZE} height={SIZE}>
      <Defs>
        {/* Deep obsidian radial background */}
        <RadialGradient id="bg-oct" cx="50%" cy="35%" r="75%">
          <Stop offset="0"    stopColor="#1a1208" />
          <Stop offset="0.55" stopColor="#0a0604" />
          <Stop offset="1"    stopColor="#020100" />
        </RadialGradient>
        {/* Rich 24k gold diagonal gradient for outer octagon */}
        <SvgLinearGradient id="oct-gold" x1="0" y1="0" x2="1" y2="1">
          <Stop offset="0"    stopColor="#fff2b8" />
          <Stop offset="0.30" stopColor="#ffd966" />
          <Stop offset="0.55" stopColor="#c89020" />
          <Stop offset="0.80" stopColor="#7a4800" />
          <Stop offset="1"    stopColor="#3a2404" />
        </SvgLinearGradient>
        {/* Rivet gold */}
        <RadialGradient id="rivetGold" cx="35%" cy="30%" r="70%">
          <Stop offset="0" stopColor="#fff2b8" />
          <Stop offset="1" stopColor="#7a4800" />
        </RadialGradient>
      </Defs>

      {/* Outer octagon gold frame */}
      <Polygon points={outerPts} fill="url(#oct-gold)" />
      {/* Inner octagon — background fill + thin gold stroke */}
      <Polygon
        points={octagonPointsStr(R_OUT_OCT * 0.94)}
        fill="url(#bg-oct)"
        stroke="#f9d76b"
        strokeWidth="0.8"
        opacity="0.95"
      />
      {/* Subtle inner gold highlight line */}
      <Polygon
        points={octagonPointsStr(R_OUT_OCT * 0.92)}
        fill="none"
        stroke="#3a2404"
        strokeWidth="0.6"
        opacity="0.8"
      />

      {/* 8 decorative rivets at octagon vertices (on inner edge) */}
      {innerPts.map((p, i) => (
        <G key={`bz-rv-${i}`}>
          <Circle cx={p[0]} cy={p[1]} r={SIZE * 0.012} fill="#3a2404" />
          <Circle cx={p[0]} cy={p[1]} r={SIZE * 0.009} fill="url(#rivetGold)" />
          <Circle cx={p[0] - 0.8} cy={p[1] - 0.8} r={SIZE * 0.003} fill="#fff8dc" opacity="0.9" />
        </G>
      ))}
    </Svg>
  );
}

// ── Energy Core (glowing pulsing core — no religious symbol) ──────────────────
function EnergyCore() {
  const pulse1 = useRef(new Animated.Value(0)).current;
  const pulse2 = useRef(new Animated.Value(0)).current;
  const pulse3 = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const make = (v: Animated.Value, delay: number) =>
      Animated.loop(
        Animated.sequence([
          Animated.delay(delay),
          Animated.timing(v, { toValue: 1, duration: 2400, useNativeDriver: true }),
        ]),
      );
    const a = make(pulse1, 0);
    const b = make(pulse2, 800);
    const c = make(pulse3, 1600);
    a.start(); b.start(); c.start();
    return () => { a.stop(); b.stop(); c.stop(); };
  }, [pulse1, pulse2, pulse3]);

  const ring = (v: Animated.Value, baseSize: number, color: string) => {
    const scale   = v.interpolate({ inputRange: [0, 1], outputRange: [0.6, 1.9] });
    const opacity = v.interpolate({ inputRange: [0, 0.15, 1], outputRange: [0, 0.55, 0] });
    return (
      <Animated.View
        pointerEvents="none"
        style={{
          position: "absolute",
          width: baseSize, height: baseSize, borderRadius: baseSize / 2,
          borderWidth: 1.2, borderColor: color,
          transform: [{ scale }], opacity,
        }}
      />
    );
  };

  const coreSize = SIZE * 0.14;
  const dotSize  = SIZE * 0.048;

  return (
    <View
      pointerEvents="none"
      style={[
        StyleSheet.absoluteFill,
        { alignItems: "center", justifyContent: "center" },
      ]}
    >
      {/* Ambient radial glow (static layers, soft) */}
      <View style={{
        position: "absolute", width: coreSize * 3.2, height: coreSize * 3.2,
        borderRadius: coreSize * 1.6, backgroundColor: "#f9d76b", opacity: 0.05,
      }} />
      <View style={{
        position: "absolute", width: coreSize * 2.3, height: coreSize * 2.3,
        borderRadius: coreSize * 1.15, backgroundColor: "#f9d76b", opacity: 0.10,
      }} />
      <View style={{
        position: "absolute", width: coreSize * 1.6, height: coreSize * 1.6,
        borderRadius: coreSize * 0.8, backgroundColor: "#ffd966", opacity: 0.16,
      }} />

      {/* Pulsing expanding rings */}
      {ring(pulse1, coreSize, "#f9d76b")}
      {ring(pulse2, coreSize, "#ffd966")}
      {ring(pulse3, coreSize, "#fff2b8")}

      {/* Static thin gold rings */}
      <View style={{
        position: "absolute", width: coreSize * 1.55, height: coreSize * 1.55,
        borderRadius: coreSize * 0.775,
        borderWidth: 0.6, borderColor: "#f9d76b44",
      }} />
      <View style={{
        position: "absolute", width: coreSize * 1.15, height: coreSize * 1.15,
        borderRadius: coreSize * 0.575,
        borderWidth: 0.8, borderColor: "#f9d76b66",
      }} />

      {/* Yantra (8-pointed star) sacred geometry overlay */}
      {(() => {
        const yR  = coreSize * 1.35;
        const yCX = yR, yCY = yR;
        const starPts: string[] = [];
        for (let k = 0; k < 16; k++) {
          const ang = (k * Math.PI) / 8 - Math.PI / 2;
          const r   = k % 2 === 0 ? yR * 0.95 : yR * 0.48;
          starPts.push(`${yCX + r * Math.cos(ang)},${yCY + r * Math.sin(ang)}`);
        }
        const tri1: string[] = [];
        const tri2: string[] = [];
        for (let k = 0; k < 3; k++) {
          const a1 = (k * 2 * Math.PI) / 3 - Math.PI / 2;
          const a2 = a1 + Math.PI / 3;
          tri1.push(`${yCX + yR * 0.85 * Math.cos(a1)},${yCY + yR * 0.85 * Math.sin(a1)}`);
          tri2.push(`${yCX + yR * 0.85 * Math.cos(a2)},${yCY + yR * 0.85 * Math.sin(a2)}`);
        }
        return (
          <Svg
            width={yR * 2}
            height={yR * 2}
            style={{ position: "absolute" }}
            pointerEvents="none"
          >
            <Defs>
              <RadialGradient id="yantraFill" cx="50%" cy="50%" r="50%">
                <Stop offset="0"   stopColor="#f9d76b" stopOpacity="0.22" />
                <Stop offset="1"   stopColor="#f9d76b" stopOpacity="0.04" />
              </RadialGradient>
            </Defs>
            {/* Fill star (octagram base) */}
            <Polygon points={starPts.join(" ")} fill="url(#yantraFill)" />
            {/* Two interlocking triangles (shatkona / star of David feel) */}
            <Polygon points={tri1.join(" ")} fill="none" stroke="#f9d76b" strokeWidth="0.7" opacity="0.55" />
            <Polygon points={tri2.join(" ")} fill="none" stroke="#fff2b8" strokeWidth="0.7" opacity="0.55" />
            {/* Octagram outline */}
            <Polygon points={starPts.join(" ")} fill="none" stroke="#f9d76b" strokeWidth="0.9" opacity="0.85" />
            {/* 8 gold dots at star tips */}
            {Array.from({ length: 8 }).map((_, k) => {
              const ang = (k * Math.PI) / 4 - Math.PI / 2;
              const dx  = yCX + yR * 0.95 * Math.cos(ang);
              const dy  = yCY + yR * 0.95 * Math.sin(ang);
              return <Circle key={k} cx={dx} cy={dy} r={1.8} fill="#fff8dc" opacity={0.95} />;
            })}
            {/* Inner bindu circle */}
            <Circle cx={yCX} cy={yCY} r={yR * 0.22} fill="none" stroke="#f9d76b" strokeWidth="0.8" opacity="0.7" />
          </Svg>
        );
      })()}

      {/* Bright core dot with halo */}
      <View style={{
        width: coreSize * 0.72, height: coreSize * 0.72, borderRadius: coreSize * 0.36,
        backgroundColor: "#1a0e02",
        alignItems: "center", justifyContent: "center",
        borderWidth: 1, borderColor: "#f9d76b",
        shadowColor: "#f9d76b", shadowOpacity: 0.9, shadowRadius: 14,
        shadowOffset: { width: 0, height: 0 },
      }}>
        <View style={{
          width: dotSize, height: dotSize, borderRadius: dotSize / 2,
          backgroundColor: "#fff8dc",
          shadowColor: "#fff2b8", shadowOpacity: 1, shadowRadius: 10,
          shadowOffset: { width: 0, height: 0 },
        }} />
      </View>
    </View>
  );
}

// ── North pointer (fixed gold indicator at top) ───────────────────────────
function NorthPointer() {
  const tipY   = SIZE * 0.022;
  const baseY  = SIZE * 0.078;
  const halfW  = SIZE * 0.036;
  const midY   = (tipY + baseY) / 2;
  return (
    <Svg width={SIZE} height={SIZE} style={StyleSheet.absoluteFill}>
      <Defs>
        <SvgLinearGradient id="goldArrow" x1="0" y1="0" x2="0" y2="1">
          <Stop offset="0"    stopColor="#fff2b8" />
          <Stop offset="0.45" stopColor="#f9d76b" />
          <Stop offset="1"    stopColor="#7a4800" />
        </SvgLinearGradient>
        <SvgLinearGradient id="goldShine" x1="0" y1="0" x2="1" y2="1">
          <Stop offset="0"    stopColor="#ffffff" stopOpacity="0.65" />
          <Stop offset="0.6"  stopColor="#ffffff" stopOpacity="0" />
        </SvgLinearGradient>
      </Defs>
      {/* Shadow */}
      <Polygon
        points={`${CX + 1.5},${tipY + 2} ${CX - halfW + 1.5},${baseY + 2} ${CX + halfW + 1.5},${baseY + 2}`}
        fill="#00000066"
      />
      {/* Gold arrow body */}
      <Polygon
        points={`${CX},${tipY} ${CX - halfW},${baseY} ${CX + halfW},${baseY}`}
        fill="url(#goldArrow)"
      />
      {/* Shine on left side */}
      <Polygon
        points={`${CX},${tipY} ${CX - halfW * 0.7},${baseY - 2} ${CX - 1},${midY}`}
        fill="url(#goldShine)"
      />
      {/* Dark gold outline */}
      <Polygon
        points={`${CX},${tipY} ${CX - halfW},${baseY} ${CX + halfW},${baseY}`}
        fill="none" stroke="#3a2404" strokeWidth="1.2"
      />
      {/* Tip cream dot */}
      <Circle cx={CX} cy={tipY + 0.5} r="1.6" fill="#fff2b8" />
      {/* "N" label above arrow */}
      <SvgText
        x={CX} y={tipY - SIZE * 0.010}
        textAnchor="middle" alignmentBaseline="middle"
        fill="#f9d76b" fontSize={SIZE * 0.032} fontWeight="900"
      >
        N
      </SvgText>
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
    Magnetometer.setUpdateInterval(100);
    const sub = Magnetometer.addListener(({ x, y }) => {
      // Correct compass heading for portrait mode:
      // - device top pointing North  → Mx=0,  My>0  → heading = 0
      // - device top pointing East   → Mx<0,  My=0  → heading = 90
      // - device top pointing South  → Mx=0,  My<0  → heading = 180
      // - device top pointing West   → Mx>0,  My=0  → heading = 270
      let angle = Math.atan2(-x, y) * (180 / Math.PI);
      if (angle < 0) angle += 360;
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
    <View style={[cp.outer, { backgroundColor: C.isDark ? "#131c2e" : C.bgCard, borderColor: C.isDark ? "#1e2a44" : C.border }]}>
      {/* ── Header row ── */}
      <View style={cp.headerRow}>
        <View>
          <Text style={[cp.heading, { color: C.text }]}>Vastu Compass</Text>
          <Text style={[cp.subhead, { color: C.textMuted }]}>Sacred Direction Finder</Text>
        </View>
        <View style={[cp.badge, { backgroundColor: isLive ? "rgba(249,215,107,0.10)" : "rgba(148,163,184,0.10)", borderWidth: 1, borderColor: isLive ? "rgba(249,215,107,0.4)" : "rgba(148,163,184,0.3)" }]}>
          <View style={[cp.dot, { backgroundColor: isLive ? "#f9d76b" : "#94a3b8" }]} />
          <Text style={[cp.badgeTxt, { color: isLive ? "#f9d76b" : "#94a3b8" }]}>
            {isLive ? "SENSOR ACTIVE" : "ALIGNING…"}
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

      {/* ── Compass graphic (no frame — octagon stands alone) ── */}
      <View style={[cp.compassWrap, { width: SIZE, height: SIZE }]}>
        {/* Layer 1: Fixed outer bezel */}
        <View style={StyleSheet.absoluteFill}>
          <CompassBezel />
        </View>

        {/* Layer 2: Rotating rose */}
        <Animated.View style={[StyleSheet.absoluteFill, rotateStyle]}>
          <CompassRose />
        </Animated.View>

        {/* Layer 3: Energy Core (replaces Om) */}
        <EnergyCore />

        {/* Layer 4: Fixed north pointer */}
        <NorthPointer />
      </View>

      {/* ── Glassmorphism pill: Ideal Direction ── */}
      <View style={cp.pillWrap}>
        <View style={cp.pill}>
          <View style={cp.pillGlow} />
          <Text style={cp.pillText}>
            ✨  Ideal Direction: <Text style={cp.pillAccent}>North-East</Text>
          </Text>
        </View>
      </View>
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
  compassFrame: {
    alignSelf: "center",
    padding: 10,
    borderRadius: (SIZE + 40) / 2,
    backgroundColor: "#0a0a0a",
    shadowColor: "#f9d76b",
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.35,
    shadowRadius: 18,
    elevation: 14,
    borderWidth: 1.5,
    borderColor: "#3a2404",
  },
  compassOuterRing: {
    padding: 5,
    borderRadius: (SIZE + 20) / 2,
    backgroundColor: "#1a0e02",
    borderWidth: 1,
    borderColor: "#7a4800",
  },
  pillWrap:   { alignItems: "center", marginTop: 4 },
  pill: {
    paddingHorizontal: 20,
    paddingVertical: 11,
    borderRadius: 999,
    backgroundColor: "#0c1426",
    borderWidth: 1,
    borderColor: "rgba(249,215,107,0.45)",
    overflow: "hidden",
    shadowColor: "#f9d76b",
    shadowOpacity: 0.35,
    shadowRadius: 14,
    shadowOffset: { width: 0, height: 4 },
  },
  pillGlow: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(249,215,107,0.04)",
  },
  pillText:   { color: "#f5e4a3", fontSize: 13, fontWeight: "600", letterSpacing: 0.4 },
  pillAccent: { color: "#fff8dc", fontWeight: "800" },
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
// ── Vastu Drishti Scan Card ──────────────────────────────────────────────────
const ROOM_TYPES: { key: string; emoji: string; label: string }[] = [
  { key: "bedroom",     emoji: "🛏️", label: "Bedroom"      },
  { key: "kitchen",     emoji: "🍳", label: "Kitchen"      },
  { key: "pooja room",  emoji: "🪔", label: "Pooja Room"   },
  { key: "living room", emoji: "🛋️", label: "Living Room" },
  { key: "main door",   emoji: "🚪", label: "Main Door"    },
  { key: "bathroom",    emoji: "🚿", label: "Bathroom"     },
  { key: "study room",  emoji: "📚", label: "Study Room"   },
  { key: "office",      emoji: "💼", label: "Office"       },
];

// ── Strict structured response from /api/vastu-scan (Phase 1) ──────────────
type VastuScanResponse = {
  scan_inconclusive:        boolean;
  inconclusive_reason:      string;
  room_detected:            string;
  compliance_score:         number;
  compliance_score_llm?:    number;
  compliance_score_method?: string;
  energy_status:            "Excellent" | "Optimal" | "Mild Disturbance" | "Moderate Dosh" | "Significant Dosh";
  direction_basis:          "magnetometer" | "visual_inference" | "assumed";
  camera_facing_direction:  string;
  observations: Array<{
    text: string; direction: string;
    severity: "positive" | "neutral" | "warning" | "critical";
    classical_rule_ref: string;
  }>;
  dosh: Array<{
    name: string; description: string;
    classical_source: string;
    severity: "minor" | "moderate" | "major";
  }>;
  remedies: Array<{
    action: string;
    priority: "high" | "medium" | "low";
    classical_source: string;
  }>;
  energy_forecast: string;
  confidence:      number;
  room?:           string;
  source?:         string;
  model?:          string;
  heading_deg_input?: number;
  quota?:          { used: number; limit: number };
  plan?:           string;
};

// Lightweight magnetometer heading reader — captured at scan time.
// `getHeading()` returns instantaneous raw value (precise capture); `displayHeading`
// is EMA-smoothed state for jitter-free pinpoint UI display.
function useScanHeading() {
  const headingRef = useRef<number | null>(null);
  const [hasFix, setHasFix] = useState(false);
  const [displayHeading, setDisplayHeading] = useState<number | null>(null);

  useEffect(() => {
    if (Platform.OS === "web") return;
    Magnetometer.setUpdateInterval(120);
    const sub = Magnetometer.addListener(({ x, y }) => {
      let raw = Math.atan2(-x, y) * (180 / Math.PI);
      if (raw < 0) raw += 360;
      headingRef.current = raw;             // raw for capture precision
      if (!hasFix) setHasFix(true);
      setDisplayHeading(prev => {           // smoothed for display
        if (prev == null) return raw;
        const d = ((raw - prev + 540) % 360) - 180;
        let next = prev + 0.28 * d;
        if (next < 0)     next += 360;
        if (next >= 360)  next -= 360;
        return next;
      });
    });
    return () => sub.remove();
  }, [hasFix]);

  return { getHeading: () => headingRef.current, hasFix, displayHeading };
}

function VastuScanCard({ C }: { C: any }) {
  const { user, language } = useUser();
  const [imageUri, setImageUri]   = useState<string | null>(null);
  const [imageB64, setImageB64]   = useState<string | null>(null);
  const [room, setRoom]           = useState<string>("bedroom");
  const [picking, setPicking]     = useState(false);
  const [scanning, setScanning]   = useState(false);
  const [result, setResult]       = useState<VastuScanResponse | null>(null);
  const [showRoomPicker, setShowRoomPicker] = useState(false);
  const { getHeading, hasFix, displayHeading } = useScanHeading();

  const pickFromLibrary = async () => {
    try {
      setPicking(true);
      const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!perm.granted) {
        Alert.alert("Permission needed", "Photo gallery access dijiye taaki Vastu Drishti aapka room dekh sake.");
        return;
      }
      const r = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        quality: 0.7,
        base64: true,
        allowsEditing: false,
      });
      if (!r.canceled && r.assets?.[0]) {
        const a = r.assets[0];
        setImageUri(a.uri);
        setImageB64(a.base64 ?? null);
        setResult(null);
        Haptics.impactAsync?.(Haptics.ImpactFeedbackStyle.Light);
      }
    } catch (e: any) {
      Alert.alert("Error", e?.message ?? "Photo nahi le payi.");
    } finally {
      setPicking(false);
    }
  };

  const pickFromCamera = async () => {
    try {
      setPicking(true);
      const perm = await ImagePicker.requestCameraPermissionsAsync();
      if (!perm.granted) {
        Alert.alert("Permission needed", "Camera access dijiye taaki turant photo le sakein.");
        return;
      }
      const r = await ImagePicker.launchCameraAsync({
        quality: 0.7,
        base64: true,
        allowsEditing: false,
      });
      if (!r.canceled && r.assets?.[0]) {
        const a = r.assets[0];
        setImageUri(a.uri);
        setImageB64(a.base64 ?? null);
        setResult(null);
        Haptics.impactAsync?.(Haptics.ImpactFeedbackStyle.Light);
      }
    } catch (e: any) {
      Alert.alert("Error", e?.message ?? "Camera khol nahi payi.");
    } finally {
      setPicking(false);
    }
  };

  const runScan = async () => {
    if (!imageB64) {
      Alert.alert("Photo missing", "Pehle ek room ka photo lijiye ya gallery se chuniye.");
      return;
    }
    setScanning(true);
    setResult(null);
    Haptics.impactAsync?.(Haptics.ImpactFeedbackStyle.Medium);
    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (user?.api_key) headers["X-API-Key"] = user.api_key;

      // Capture REAL device compass heading at scan moment — single biggest
      // accuracy lever for backend Vastu analysis.
      const heading_deg = getHeading();

      const dataUrl = `data:image/jpeg;base64,${imageB64}`;
      const resp = await fetch(`${API_BASE}/api/vastu-scan`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          image:   dataUrl,
          room,
          lang:    language,
          user_id: user?.id,
          heading_deg,
        }),
      });
      const d = await resp.json();
      if (!resp.ok) {
        if (resp.status === 402) {
          Alert.alert(
            "Daily limit poora",
            d?.message ?? "Aaj ka free limit poora ho gaya — kal phir try karein ya Pro le lijiye."
          );
        } else {
          Alert.alert("Scan failed", d?.message ?? "Photo analyze nahi ho payi. Acchi roshni mein dobara try karein.");
        }
        return;
      }
      setResult(d as VastuScanResponse);
      Haptics.notificationAsync?.(Haptics.NotificationFeedbackType.Success);
    } catch (e: any) {
      Alert.alert("Network error", e?.message ?? "Internet connection check kijiye.");
    } finally {
      setScanning(false);
    }
  };

  const reset = () => {
    setImageUri(null);
    setImageB64(null);
    setResult(null);
  };

  const selectedRoom = ROOM_TYPES.find(r => r.key === room) ?? ROOM_TYPES[0];

  return (
    <View style={[vs.card, { backgroundColor: C.bgCard, borderColor: "#a78bfa55" }]}>
      <LinearGradient
        colors={["#a78bfa15", "transparent"]}
        start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
        style={StyleSheet.absoluteFill}
        pointerEvents="none"
      />

      <View style={vs.headerRow}>
        <View style={vs.iconBox}>
          <Text style={{ fontSize: 22 }}>📡</Text>
        </View>
        <View style={{ flex: 1 }}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
            <Text style={[vs.title, { color: C.text }]}>Vastu Drishti Scanner</Text>
            <View style={vs.newBadge}>
              <Text style={vs.newBadgeText}>NEW</Text>
            </View>
          </View>
          <Text style={[vs.sub, { color: C.textMuted }]}>
            Room ka photo upload karein — advanced spatial-energy scan + dosh detection + remedies
          </Text>
        </View>
      </View>

      {/* Room type selector */}
      <Pressable
        onPress={() => setShowRoomPicker(true)}
        style={[vs.roomBtn, { backgroundColor: C.bgCard2, borderColor: C.border }]}
      >
        <Text style={{ fontSize: 16 }}>{selectedRoom.emoji}</Text>
        <Text style={[vs.roomBtnText, { color: C.text }]}>{selectedRoom.label}</Text>
        <Feather name="chevron-down" size={14} color={C.textMuted} />
      </Pressable>

      {/* Photo preview / pickers */}
      {imageUri ? (
        <View style={vs.previewWrap}>
          <Image source={{ uri: imageUri }} style={vs.preview} contentFit="cover" />
          {!result && !scanning && (
            <Pressable onPress={reset} style={vs.previewClear}>
              <Feather name="x" size={14} color="#fff" />
            </Pressable>
          )}
        </View>
      ) : (
        <View style={vs.pickerRow}>
          <Pressable
            onPress={pickFromCamera}
            disabled={picking}
            style={[vs.pickBtn, { backgroundColor: C.bgCard2, borderColor: "#a78bfa55", opacity: picking ? 0.5 : 1 }]}
          >
            <Feather name="camera" size={20} color="#a78bfa" />
            <Text style={[vs.pickBtnText, { color: C.text }]}>Camera</Text>
            <Text style={[vs.pickBtnSub, { color: C.textMuted }]}>Turant photo lein</Text>
          </Pressable>
          <Pressable
            onPress={pickFromLibrary}
            disabled={picking}
            style={[vs.pickBtn, { backgroundColor: C.bgCard2, borderColor: "#a78bfa55", opacity: picking ? 0.5 : 1 }]}
          >
            <Feather name="image" size={20} color="#a78bfa" />
            <Text style={[vs.pickBtnText, { color: C.text }]}>Gallery</Text>
            <Text style={[vs.pickBtnSub, { color: C.textMuted }]}>Saved photo chuniye</Text>
          </Pressable>
        </View>
      )}

      {/* Scan button */}
      {imageUri && !result && (
        <Pressable onPress={runScan} disabled={scanning} style={({ pressed }) => [{ opacity: pressed ? 0.85 : 1 }]}>
          <LinearGradient
            colors={["#a78bfa", "#7c3aed"]}
            start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
            style={vs.scanBtn}
          >
            {scanning ? (
              <>
                <ActivityIndicator size="small" color="#fff" />
                <Text style={vs.scanBtnText}>Scanning spatial energy field...</Text>
              </>
            ) : (
              <>
                <Feather name="zap" size={16} color="#fff" />
                <Text style={vs.scanBtnText}>Initiate Vastu Drishti Scan</Text>
              </>
            )}
          </LinearGradient>
        </Pressable>
      )}

      {/* Heading-fix indicator (shown only before scan) */}
      {imageUri && !result && !scanning && (
        <View style={[vs.headingChip, { borderColor: hasFix ? "#10b98155" : "#94a3b855", backgroundColor: hasFix ? "#10b98115" : "#94a3b815" }]}>
          <Feather name="compass" size={12} color={hasFix ? "#10b981" : "#94a3b8"} />
          <Text style={[vs.headingChipText, { color: hasFix ? "#10b981" : "#94a3b8" }]}>
            {hasFix
              ? `Compass live · ${displayHeading != null ? displayHeading.toFixed(1) : "--"}° · pinpoint`
              : "Compass calibrating… move phone in figure-8 motion"}
          </Text>
        </View>
      )}

      {/* Result — structured Vastu Drishti report (Phase 1 v3.0) */}
      {result && <VastuScanReport C={C} data={result} onReset={reset} />}

      {!user?.id && !result && (
        <Text style={[vs.note, { color: C.textMuted }]}>
          ✨ Free mein 3 scans har din. Pro mein unlimited.
        </Text>
      )}

      {/* Room picker modal */}
      <Modal visible={showRoomPicker} transparent animationType="fade" onRequestClose={() => setShowRoomPicker(false)}>
        <Pressable style={vs.modalBackdrop} onPress={() => setShowRoomPicker(false)}>
          <Pressable style={[vs.modalCard, { backgroundColor: C.bgCard, borderColor: C.border }]} onPress={(e) => e.stopPropagation?.()}>
            <Text style={[vs.modalTitle, { color: C.text }]}>Room type chuniye</Text>
            <ScrollView style={{ maxHeight: 360 }}>
              {ROOM_TYPES.map(rt => (
                <Pressable
                  key={rt.key}
                  onPress={() => { setRoom(rt.key); setShowRoomPicker(false); Haptics.selectionAsync?.(); }}
                  style={[vs.modalRow, room === rt.key && { backgroundColor: "#a78bfa20" }]}
                >
                  <Text style={{ fontSize: 18 }}>{rt.emoji}</Text>
                  <Text style={[vs.modalRowText, { color: C.text }]}>{rt.label}</Text>
                  {room === rt.key && <Feather name="check" size={16} color="#a78bfa" />}
                </Pressable>
              ))}
            </ScrollView>
          </Pressable>
        </Pressable>
      </Modal>
    </View>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// PHASE 2 — DEEP SCAN: 4-wall guided multi-photo capture
// ─────────────────────────────────────────────────────────────────────────────

type WallStep = {
  key:        "N" | "E" | "S" | "W";
  label:      string;
  hindi:      string;
  target_deg: number;
};

const WALL_STEPS: WallStep[] = [
  { key: "N", label: "North Wall", hindi: "Uttar (उत्तर)", target_deg: 0   },
  { key: "E", label: "East Wall",  hindi: "Poorv (पूर्व)",  target_deg: 90  },
  { key: "S", label: "South Wall", hindi: "Dakshin (दक्षिण)",target_deg: 180 },
  { key: "W", label: "West Wall",  hindi: "Paschim (पश्चिम)",target_deg: 270 },
];

const ALIGN_TOLERANCE_DEG = 15;

// Smallest signed angular delta (current → target) in degrees, range [-180, 180]
function angularDelta(current: number, target: number): number {
  let d = ((target - current + 540) % 360) - 180;
  return d;
}

// Smoothing factor for EMA (low-pass filter). Higher = more responsive, more jitter.
// 0.25 = comfy "settles in 4-5 frames", removes raw sensor noise (~±2°).
const HEADING_EMA_ALPHA = 0.28;

// Live continuously-updating compass heading (state, not ref) — used by wizard.
// Gated by `enabled` so the sensor isn't draining battery while the wizard
// modal is mounted-but-hidden. Smoothed with EMA for pinpoint, jitter-free
// readout — handles 0/360° wrap-around correctly via shortest-arc interpolation.
function useLiveHeading(enabled: boolean) {
  const [heading, setHeading] = useState<number | null>(null);
  useEffect(() => {
    if (!enabled) { setHeading(null); return; }
    if (Platform.OS === "web") return;
    Magnetometer.setUpdateInterval(80);
    const sub = Magnetometer.addListener(({ x, y }) => {
      let raw = Math.atan2(-x, y) * (180 / Math.PI);
      if (raw < 0) raw += 360;
      setHeading(prev => {
        if (prev == null) return raw;
        const d = angularDelta(prev, raw);   // shortest-arc delta
        let next = prev + HEADING_EMA_ALPHA * d;
        if (next < 0)     next += 360;
        if (next >= 360)  next -= 360;
        return next;
      });
    });
    return () => sub.remove();
  }, [enabled]);
  return heading;
}

type CapturedPhoto = {
  uri:         string;
  base64:      string;
  heading_deg: number;
};

// ── Compact alignment indicator (north-up arc with target marker) ─────────
function AlignmentDial({ current, target }: { current: number | null; target: number }) {
  const size = 220;
  const cx = size / 2;
  const cy = size / 2;
  const r  = size / 2 - 14;
  const delta = current == null ? null : angularDelta(current, target);
  const aligned = delta != null && Math.abs(delta) <= ALIGN_TOLERANCE_DEG;
  const ringColor = current == null ? "#64748b" : aligned ? "#10b981" : Math.abs(delta!) < 35 ? "#f59e0b" : "#ef4444";

  // Target marker at top (12 o'clock = target direction). Arrow indicates how far phone heading is from target.
  // Phone-relative arrow rotation: -delta (positive delta = need to rotate phone clockwise toward target,
  // so the arrow points right; equivalently, the arrow direction = -delta from up).
  const arrowAngle = delta == null ? 0 : -delta;
  return (
    <View style={{ width: size, height: size, alignItems: "center", justifyContent: "center" }}>
      <Svg width={size} height={size}>
        {/* Outer ring */}
        <Circle cx={cx} cy={cy} r={r} stroke="#ffffff15" strokeWidth={2} fill="none" />
        {/* Tolerance arc at top */}
        <Path
          d={`M ${cx + r * Math.cos((-90 - ALIGN_TOLERANCE_DEG) * Math.PI / 180)} ${cy + r * Math.sin((-90 - ALIGN_TOLERANCE_DEG) * Math.PI / 180)} A ${r} ${r} 0 0 1 ${cx + r * Math.cos((-90 + ALIGN_TOLERANCE_DEG) * Math.PI / 180)} ${cy + r * Math.sin((-90 + ALIGN_TOLERANCE_DEG) * Math.PI / 180)}`}
          stroke="#10b98166"
          strokeWidth={6}
          fill="none"
          strokeLinecap="round"
        />
        {/* Target tick at top */}
        <Line x1={cx} y1={cy - r - 4} x2={cx} y2={cy - r + 8} stroke="#10b981" strokeWidth={3} />
        {/* Arrow showing where phone is currently pointing relative to target */}
        {delta != null && (
          <G transform={`rotate(${arrowAngle} ${cx} ${cy})`}>
            <Polygon
              points={`${cx},${cy - r + 12} ${cx - 12},${cy - r + 38} ${cx + 12},${cy - r + 38}`}
              fill={ringColor}
            />
            <Line x1={cx} y1={cy - r + 38} x2={cx} y2={cy + r * 0.35} stroke={ringColor} strokeWidth={3} strokeLinecap="round" />
          </G>
        )}
        {/* Center dot */}
        <Circle cx={cx} cy={cy} r={6} fill={ringColor} />
      </Svg>
      {/* Big live degree readout — pinpoint single-decimal precision */}
      <View style={{ position: "absolute", alignItems: "center" }}>
        <Text style={{ fontSize: 9, color: "#94a3b8", letterSpacing: 1.5, fontWeight: "800" }}>LIVE COMPASS</Text>
        <Text style={{
          fontSize: 32, fontWeight: "900", color: ringColor,
          fontVariant: ["tabular-nums"],
          fontFamily: Platform.OS === "ios" ? "Menlo" : "monospace",
        }}>
          {current == null ? "--" : current.toFixed(1)}°
        </Text>
        <Text style={{ fontSize: 10, color: "#94a3b8", letterSpacing: 0.8, marginTop: 2 }}>
          target {target.toFixed(1)}°
          {delta != null && (
            <Text style={{ color: ringColor, fontWeight: "800" }}>
              {"  ·  "}Δ {delta > 0 ? "+" : ""}{delta.toFixed(1)}°
            </Text>
          )}
        </Text>
      </View>
    </View>
  );
}

// ── Deep-scan capture wizard (modal) ──────────────────────────────────────
function DeepScanWizard({
  C,
  visible,
  onClose,
  onComplete,
}: {
  C:          any;
  visible:    boolean;
  onClose:    () => void;
  onComplete: (photos: CapturedPhoto[], floorPlan: { uri: string; base64: string } | null) => void;
}) {
  const heading = useLiveHeading(visible);
  const [stepIndex, setStepIndex] = useState(0); // 0..3 = walls, 4 = floor plan, 5 = review
  const [captured, setCaptured]   = useState<(CapturedPhoto | null)[]>([null, null, null, null]);
  const [floorPlan, setFloorPlan] = useState<{ uri: string; base64: string } | null>(null);
  const [busy, setBusy]           = useState(false);

  const reset = useCallback(() => {
    setStepIndex(0);
    setCaptured([null, null, null, null]);
    setFloorPlan(null);
    setBusy(false);
  }, []);

  useEffect(() => { if (!visible) reset(); }, [visible, reset]);

  const isWallStep = stepIndex >= 0 && stepIndex < 4;
  const wallStep   = isWallStep ? WALL_STEPS[stepIndex] : null;
  const delta      = wallStep && heading != null ? angularDelta(heading, wallStep.target_deg) : null;
  const aligned    = delta != null && Math.abs(delta) <= ALIGN_TOLERANCE_DEG;

  const captureCurrentWall = async (useCamera: boolean) => {
    if (!wallStep) return;
    if (heading == null) {
      Alert.alert("Compass calibrating", "Phone ko hawa mein ek '∞' shape mein ghoomayein, fir compass ready ho jayega.");
      return;
    }
    if (useCamera && !aligned) {
      Alert.alert("Phone ko sahi direction mein karein", `${wallStep.label} (${Math.round(wallStep.target_deg)}°) ki taraf face karein. Tolerance ±${ALIGN_TOLERANCE_DEG}° hai.`);
      return;
    }
    setBusy(true);
    try {
      let r;
      if (useCamera) {
        const perm = await ImagePicker.requestCameraPermissionsAsync();
        if (!perm.granted) { Alert.alert("Camera permission needed"); return; }
        r = await ImagePicker.launchCameraAsync({ mediaTypes: ImagePicker.MediaTypeOptions.Images, quality: 0.7, base64: true });
      } else {
        const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
        if (!perm.granted) { Alert.alert("Gallery permission needed"); return; }
        r = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ImagePicker.MediaTypeOptions.Images, quality: 0.7, base64: true });
      }
      if (r.canceled || !r.assets?.[0]) return;
      const a = r.assets[0];
      if (!a.base64) { Alert.alert("Photo nahi padh sake"); return; }
      // Capture heading at the moment of taking photo (camera) or current heading (library override).
      const headingAtCapture = heading; // already validated above
      const next = [...captured];
      next[stepIndex] = { uri: a.uri, base64: a.base64, heading_deg: headingAtCapture! };
      setCaptured(next);
      Haptics.notificationAsync?.(Haptics.NotificationFeedbackType.Success);
    } catch (e: any) {
      Alert.alert("Error", e?.message ?? "Photo capture nahi ho payi.");
    } finally {
      setBusy(false);
    }
  };

  const pickFloorPlan = async () => {
    setBusy(true);
    try {
      const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!perm.granted) { Alert.alert("Gallery permission needed"); return; }
      const r = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ImagePicker.MediaTypeOptions.Images, quality: 0.7, base64: true });
      if (r.canceled || !r.assets?.[0]) return;
      const a = r.assets[0];
      if (!a.base64) return;
      setFloorPlan({ uri: a.uri, base64: a.base64 });
      Haptics.impactAsync?.(Haptics.ImpactFeedbackStyle.Light);
    } catch (e: any) {
      Alert.alert("Error", e?.message ?? "Floor plan upload nahi ho paya.");
    } finally {
      setBusy(false);
    }
  };

  const goNext = () => {
    if (isWallStep && !captured[stepIndex]) {
      Alert.alert("Pehle is wall ki photo lijiye");
      return;
    }
    Haptics.selectionAsync?.();
    setStepIndex(stepIndex + 1);
  };
  const goBack = () => {
    if (stepIndex === 0) { onClose(); return; }
    setStepIndex(stepIndex - 1);
  };
  const submitAll = () => {
    const photos = captured.filter(Boolean) as CapturedPhoto[];
    if (photos.length < 2) { Alert.alert("Kam se kam 2 walls capture karein"); return; }
    onComplete(photos, floorPlan);
  };

  const totalSteps = 5;
  const stepHuman  = stepIndex < 4 ? `${stepIndex + 1}/4` : stepIndex === 4 ? "Optional" : "Review";

  // Status banner color/text
  let statusColor = "#94a3b8";
  let statusText  = "Compass calibrating…";
  if (heading != null && wallStep) {
    if (aligned)            { statusColor = "#10b981"; statusText = "PERFECT — Capture now ✓"; }
    else if (Math.abs(delta!) < 35) { statusColor = "#f59e0b"; statusText = `Almost there — ${Math.round(Math.abs(delta!))}° ${delta! > 0 ? "right" : "left"}`; }
    else                    { statusColor = "#ef4444"; statusText = `Turn ${Math.round(Math.abs(delta!))}° ${delta! > 0 ? "right ➡" : "⬅ left"}`; }
  }

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
      <View style={{ flex: 1, backgroundColor: C.bgScreen ?? "#0a0a0f" }}>
        <SafeAreaTopSpacer />
        {/* Header */}
        <View style={ds.header}>
          <Pressable onPress={goBack} hitSlop={10} style={ds.headerBtn}>
            <Feather name="chevron-left" size={22} color={C.text} />
          </Pressable>
          <View style={{ flex: 1, alignItems: "center" }}>
            <Text style={[ds.headerTitle, { color: C.text }]}>Cosmic Vastu Deep Scan</Text>
            <Text style={[ds.headerSub,   { color: C.textMuted }]}>Step {stepHuman} of {totalSteps}</Text>
          </View>
          <Pressable onPress={onClose} hitSlop={10} style={ds.headerBtn}>
            <Feather name="x" size={20} color={C.textMuted} />
          </Pressable>
        </View>

        {/* Step indicator dots */}
        <View style={ds.dotsRow}>
          {[0, 1, 2, 3, 4].map(i => {
            const done   = i < 4 ? !!captured[i] : !!floorPlan;
            const active = i === stepIndex;
            return (
              <View
                key={i}
                style={[
                  ds.dot,
                  { backgroundColor: done ? "#10b981" : active ? "#a78bfa" : "#ffffff15" },
                ]}
              />
            );
          })}
        </View>

        <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: 40 }}>
          {isWallStep && wallStep && (
            <>
              <Text style={[ds.stepTitle, { color: C.text }]}>{wallStep.label}</Text>
              <Text style={[ds.stepSub,   { color: C.textMuted }]}>{wallStep.hindi} • Target {Math.round(wallStep.target_deg)}°</Text>

              <View style={ds.dialWrap}>
                <AlignmentDial current={heading} target={wallStep.target_deg} />
              </View>

              <View style={[ds.statusPill, { backgroundColor: statusColor + "20", borderColor: statusColor + "66" }]}>
                <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: statusColor }} />
                <Text style={{ color: statusColor, fontWeight: "800", fontSize: 12, letterSpacing: 0.4 }}>{statusText}</Text>
              </View>

              <Text style={[ds.helper, { color: C.textMuted }]}>
                Stand in the centre of the room and rotate your body so the camera faces the {wallStep.label.toLowerCase()}. Tap the capture button when the dial is green.
              </Text>

              {captured[stepIndex] && (
                <View style={ds.thumbWrap}>
                  <Image source={{ uri: captured[stepIndex]!.uri }} style={ds.thumbImg} contentFit="cover" />
                  <View style={ds.thumbBadge}>
                    <Feather name="check-circle" size={14} color="#10b981" />
                    <Text style={ds.thumbBadgeText}>Captured at {captured[stepIndex]!.heading_deg.toFixed(1)}°</Text>
                  </View>
                </View>
              )}

              <View style={ds.btnRow}>
                <Pressable
                  onPress={() => captureCurrentWall(true)}
                  disabled={busy || !aligned}
                  style={[ds.bigBtn, { backgroundColor: aligned ? "#10b981" : "#374151", opacity: busy ? 0.6 : 1 }]}
                >
                  <Feather name="camera" size={18} color="#fff" />
                  <Text style={ds.bigBtnText}>{aligned ? "Capture Now" : "Align First"}</Text>
                </Pressable>
                <Pressable
                  onPress={() => captureCurrentWall(false)}
                  disabled={busy}
                  style={[ds.smallBtn, { borderColor: C.border }]}
                >
                  <Feather name="image" size={14} color={C.textMuted} />
                  <Text style={[ds.smallBtnText, { color: C.textMuted }]}>From Gallery</Text>
                </Pressable>
              </View>

              <Pressable
                onPress={goNext}
                disabled={!captured[stepIndex]}
                style={[ds.nextBtn, { backgroundColor: captured[stepIndex] ? "#a78bfa" : "#37415180" }]}
              >
                <Text style={ds.nextBtnText}>Next: {stepIndex < 3 ? WALL_STEPS[stepIndex + 1].label : "Floor Plan (optional)"}</Text>
                <Feather name="chevron-right" size={16} color="#fff" />
              </Pressable>
            </>
          )}

          {stepIndex === 4 && (
            <>
              <Text style={[ds.stepTitle, { color: C.text }]}>Floor Plan (Optional)</Text>
              <Text style={[ds.stepSub, { color: C.textMuted }]}>
                Top-down view of your room — adds spatial context. Skip if you don't have one.
              </Text>

              <View style={[ds.uploadCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                {floorPlan ? (
                  <Image source={{ uri: floorPlan.uri }} style={ds.fpImg} contentFit="contain" />
                ) : (
                  <>
                    <Feather name="map" size={36} color={C.textDim} />
                    <Text style={[ds.uploadHint, { color: C.textMuted }]}>No floor plan added</Text>
                  </>
                )}
              </View>

              <View style={ds.btnRow}>
                <Pressable onPress={pickFloorPlan} disabled={busy} style={[ds.bigBtn, { backgroundColor: "#a78bfa" }]}>
                  <Feather name={floorPlan ? "refresh-cw" : "upload"} size={16} color="#fff" />
                  <Text style={ds.bigBtnText}>{floorPlan ? "Replace" : "Upload Floor Plan"}</Text>
                </Pressable>
                {floorPlan && (
                  <Pressable onPress={() => setFloorPlan(null)} style={[ds.smallBtn, { borderColor: C.border }]}>
                    <Feather name="x" size={14} color={C.textMuted} />
                    <Text style={[ds.smallBtnText, { color: C.textMuted }]}>Remove</Text>
                  </Pressable>
                )}
              </View>

              <Pressable onPress={goNext} style={[ds.nextBtn, { backgroundColor: "#a78bfa" }]}>
                <Text style={ds.nextBtnText}>Next: Review & Scan</Text>
                <Feather name="chevron-right" size={16} color="#fff" />
              </Pressable>
            </>
          )}

          {stepIndex === 5 && (
            <>
              <Text style={[ds.stepTitle, { color: C.text }]}>Review & Submit</Text>
              <Text style={[ds.stepSub, { color: C.textMuted }]}>Confirm your captures, then run Deep Scan.</Text>

              <View style={ds.reviewGrid}>
                {WALL_STEPS.map((w, i) => {
                  const ph = captured[i];
                  return (
                    <View key={w.key} style={[ds.reviewCell, { borderColor: C.border, backgroundColor: C.bgCard }]}>
                      {ph ? (
                        <Image source={{ uri: ph.uri }} style={ds.reviewImg} contentFit="cover" />
                      ) : (
                        <View style={[ds.reviewImg, { alignItems: "center", justifyContent: "center" }]}>
                          <Feather name="alert-triangle" size={20} color="#94a3b8" />
                        </View>
                      )}
                      <Text style={[ds.reviewLabel, { color: C.text }]}>{w.key} • {w.label}</Text>
                      <Text style={[ds.reviewMeta,  { color: C.textMuted }]}>
                        {ph ? `${ph.heading_deg.toFixed(1)}° captured` : "Skipped"}
                      </Text>
                    </View>
                  );
                })}
                {floorPlan && (
                  <View style={[ds.reviewCell, { borderColor: "#a78bfa55", backgroundColor: C.bgCard, width: "100%" }]}>
                    <Image source={{ uri: floorPlan.uri }} style={[ds.reviewImg, { height: 120 }]} contentFit="contain" />
                    <Text style={[ds.reviewLabel, { color: C.text }]}>📐 Floor Plan</Text>
                  </View>
                )}
              </View>

              <Pressable onPress={submitAll} style={[ds.nextBtn, { backgroundColor: "#10b981", marginTop: 18 }]}>
                <Feather name="zap" size={16} color="#fff" />
                <Text style={ds.nextBtnText}>Run Cosmic Deep Scan</Text>
              </Pressable>
              <Text style={[ds.fineprint, { color: C.textMuted }]}>
                Uses 1 daily quota unit • Powered by Advanced Cosmic Intelligence
              </Text>
            </>
          )}
        </ScrollView>
      </View>
    </Modal>
  );
}

function SafeAreaTopSpacer() {
  const ins = useSafeAreaInsets();
  return <View style={{ height: ins.top }} />;
}

// ── Deep Scan entry card (replaces hidden until expanded) ─────────────────
type VastuDeepScanResponse = VastuScanResponse & {
  wall_analyses?: Array<{
    wall_direction:    string;
    wall_heading_deg:  number;
    elements_detected: string[];
    wall_status:       "auspicious" | "neutral" | "concern" | "dosh";
    wall_compliance:   number;
    notes:             string;
  }>;
  spatial_map?: {
    bed_or_seating: string;
    main_door:      string;
    brahmasthan:    string;
    ne_corner:      string;
    sw_corner:      string;
    se_corner:      string;
    nw_corner:      string;
  };
  photos_input_count?:  number;
  floor_plan_provided?: boolean;
};

function VastuDeepScanCard({ C }: { C: any }) {
  const { user, language } = useUser();
  const [room, setRoom]               = useState<string>("bedroom");
  const [showRoomPicker, setShowPick] = useState(false);
  const [wizardOpen, setWizardOpen]   = useState(false);
  const [scanning, setScanning]       = useState(false);
  const [result, setResult]           = useState<VastuDeepScanResponse | null>(null);

  const startWizard = () => {
    if (!user?.id) {
      Alert.alert("Login required", "Deep Scan ke liye login zaroori hai — yeh advanced multi-photo analysis hai.");
      return;
    }
    setResult(null);
    setWizardOpen(true);
  };

  const handleComplete = async (photos: CapturedPhoto[], floorPlan: { uri: string; base64: string } | null) => {
    setWizardOpen(false);
    setScanning(true);
    try {
      const body: any = {
        room,
        lang:    language || "en",
        user_id: user?.id,
        photos:  photos.map(p => ({
          image:       `data:image/jpeg;base64,${p.base64}`,
          heading_deg: p.heading_deg,
          label:       `wall_${Math.round(p.heading_deg)}deg`,
        })),
      };
      if (floorPlan) body.floor_plan = `data:image/jpeg;base64,${floorPlan.base64}`;

      const r = await fetch(`${API_BASE}/api/vastu-deep-scan`, {
        method:  "POST",
        headers: {
          "Content-Type": "application/json",
          ...(user?.api_key ? { "X-API-Key": user.api_key } : {}),
        },
        body: JSON.stringify(body),
      });
      const j = await r.json();
      if (!r.ok) {
        Alert.alert(j.error === "daily_limit_reached" ? "Daily limit poora" : "Deep scan failed", j.message ?? "Try again.");
        return;
      }
      setResult(j as VastuDeepScanResponse);
      Haptics.notificationAsync?.(Haptics.NotificationFeedbackType.Success);
    } catch (e: any) {
      Alert.alert("Network error", e?.message ?? "Server se baat nahi ho payi.");
    } finally {
      setScanning(false);
    }
  };

  const reset = () => setResult(null);

  return (
    <View style={[vds.card, { backgroundColor: C.bgCard, borderColor: "#a78bfa55" }]}>
      <View style={vds.glow} />
      <View style={vds.header}>
        <View style={vds.badge}>
          <Feather name="zap" size={10} color="#fff" />
          <Text style={vds.badgeText}>DEEP SCAN</Text>
        </View>
        <Text style={[vds.title, { color: C.text }]}>4-Wall Cosmic Drishti</Text>
        <Text style={[vds.sub,   { color: C.textMuted }]}>
          Photograph each wall with the compass guide — get a complete spatial energy map of the room.
        </Text>
      </View>

      {!result && !scanning && (
        <>
          <Pressable
            onPress={() => setShowPick(true)}
            style={[vds.roomChip, { borderColor: C.border, backgroundColor: C.bgCardElev ?? "#ffffff08" }]}
          >
            <Text style={{ fontSize: 16 }}>{ROOM_TYPES.find(r => r.key === room)?.emoji ?? "🏠"}</Text>
            <Text style={[vds.roomChipText, { color: C.text }]}>{ROOM_TYPES.find(r => r.key === room)?.label ?? "Room"}</Text>
            <Feather name="chevron-down" size={14} color={C.textMuted} />
          </Pressable>

          <View style={vds.featureRow}>
            <DeepFeature icon="compass"    text="Live compass alignment ±15°" />
            <DeepFeature icon="grid"       text="Per-wall analysis" />
            <DeepFeature icon="map"        text="Spatial Brahmasthan map" />
            <DeepFeature icon="book-open"  text="80+ classical rules" />
          </View>

          <Pressable onPress={startWizard} style={vds.startBtn}>
            <LinearGradient
              colors={["#a78bfa", "#7c3aed"]}
              start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
              style={vds.startBtnInner}
            >
              <Feather name="zap" size={16} color="#fff" />
              <Text style={vds.startBtnText}>Start Deep Scan</Text>
            </LinearGradient>
          </Pressable>

          {!user?.id && (
            <Text style={[vds.note, { color: C.textMuted }]}>🔒 Login required • Uses 1 daily quota unit</Text>
          )}
        </>
      )}

      {scanning && (
        <View style={{ alignItems: "center", paddingVertical: 24 }}>
          <ActivityIndicator size="large" color="#a78bfa" />
          <Text style={{ color: C.textMuted, marginTop: 12, fontSize: 12, textAlign: "center" }}>
            Cosmic Drishti Engine analyzing all walls and synthesizing spatial map…{"\n"}
            (10–30 seconds)
          </Text>
        </View>
      )}

      {result && (
        <VastuScanReport C={C} data={result} onReset={reset} extras={{
          wall_analyses: result.wall_analyses,
          spatial_map:   result.spatial_map,
          photos_count:  result.photos_input_count,
          floor_plan:    result.floor_plan_provided,
        }} />
      )}

      {/* Wizard */}
      <DeepScanWizard
        C={C}
        visible={wizardOpen}
        onClose={() => setWizardOpen(false)}
        onComplete={handleComplete}
      />

      {/* Room picker (reuses same modal styles as basic) */}
      <Modal visible={showRoomPicker} transparent animationType="fade" onRequestClose={() => setShowPick(false)}>
        <Pressable style={vs.modalBackdrop} onPress={() => setShowPick(false)}>
          <Pressable style={[vs.modalCard, { backgroundColor: C.bgCard, borderColor: C.border }]} onPress={(e) => e.stopPropagation?.()}>
            <Text style={[vs.modalTitle, { color: C.text }]}>Room type chuniye</Text>
            <ScrollView style={{ maxHeight: 360 }}>
              {ROOM_TYPES.map(rt => (
                <Pressable
                  key={rt.key}
                  onPress={() => { setRoom(rt.key); setShowPick(false); Haptics.selectionAsync?.(); }}
                  style={[vs.modalRow, room === rt.key && { backgroundColor: "#a78bfa20" }]}
                >
                  <Text style={{ fontSize: 18 }}>{rt.emoji}</Text>
                  <Text style={[vs.modalRowText, { color: C.text }]}>{rt.label}</Text>
                  {room === rt.key && <Feather name="check" size={16} color="#a78bfa" />}
                </Pressable>
              ))}
            </ScrollView>
          </Pressable>
        </Pressable>
      </Modal>
    </View>
  );
}

function DeepFeature({ icon, text }: { icon: any; text: string }) {
  return (
    <View style={vds.feat}>
      <Feather name={icon} size={11} color="#a78bfa" />
      <Text style={vds.featText}>{text}</Text>
    </View>
  );
}

// ── Wall analyses + spatial map blocks (rendered inside VastuScanReport) ──
function WallAnalysisBlock({ C, walls }: { C: any; walls: NonNullable<VastuDeepScanResponse["wall_analyses"]> }) {
  if (!walls?.length) return null;
  return (
    <View style={{ gap: 8 }}>
      <Text style={{ color: C.accent, fontWeight: "900", fontSize: 11, letterSpacing: 1.2 }}>WALL-BY-WALL ANALYSIS</Text>
      {walls.map((w, i) => {
        const sev = w.wall_status === "auspicious" ? SEV_OBS.positive
                  : w.wall_status === "neutral"    ? SEV_OBS.neutral
                  : w.wall_status === "concern"    ? SEV_OBS.warning
                                                   : SEV_OBS.critical;
        const compClr = w.wall_compliance >= 75 ? "#10b981" : w.wall_compliance >= 50 ? "#f59e0b" : "#ef4444";
        return (
          <View key={i} style={{ borderRadius: 10, borderWidth: 1, padding: 11, backgroundColor: sev.bg, borderColor: sev.border, gap: 6 }}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
              <Feather name={sev.icon} size={14} color={sev.color} />
              <Text style={{ color: C.text, fontWeight: "800", fontSize: 13, flex: 1 }}>
                {w.wall_direction} <Text style={{ color: C.textMuted, fontWeight: "600", fontSize: 11 }}>· {w.wall_heading_deg.toFixed(1)}°</Text>
              </Text>
              <View style={{ paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4, backgroundColor: compClr + "30", borderWidth: 1, borderColor: compClr + "66" }}>
                <Text style={{ color: compClr, fontWeight: "900", fontSize: 10 }}>{w.wall_compliance}/100</Text>
              </View>
            </View>
            {w.elements_detected?.length > 0 && (
              <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 4 }}>
                {w.elements_detected.map((el, k) => (
                  <View key={k} style={{ paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4, backgroundColor: "#ffffff10" }}>
                    <Text style={{ color: C.textMuted, fontSize: 10, fontWeight: "600" }}>{el}</Text>
                  </View>
                ))}
              </View>
            )}
            {!!w.notes && <Text style={{ color: C.text, fontSize: 12, lineHeight: 17 }}>{w.notes}</Text>}
          </View>
        );
      })}
    </View>
  );
}

function SpatialMapBlock({ C, map }: { C: any; map: NonNullable<VastuDeepScanResponse["spatial_map"]> }) {
  const rows: { k: string; label: string; emoji: string }[] = [
    { k: "bed_or_seating", label: "Bed / Seating",     emoji: "🛏️" },
    { k: "main_door",      label: "Main Door",         emoji: "🚪" },
    { k: "brahmasthan",    label: "Brahmasthan (centre)", emoji: "🕉️" },
    { k: "ne_corner",      label: "NE Corner (Ishanya)",   emoji: "🌅" },
    { k: "se_corner",      label: "SE Corner (Agni)",      emoji: "🔥" },
    { k: "sw_corner",      label: "SW Corner (Nairutya)",  emoji: "🪨" },
    { k: "nw_corner",      label: "NW Corner (Vayavya)",   emoji: "💨" },
  ];
  return (
    <View style={{ gap: 8 }}>
      <Text style={{ color: C.accent, fontWeight: "900", fontSize: 11, letterSpacing: 1.2 }}>SPATIAL ENERGY MAP</Text>
      <View style={{ borderRadius: 10, borderWidth: 1, borderColor: C.border, backgroundColor: "#ffffff05", padding: 10, gap: 8 }}>
        {rows.map(r => {
          const v = (map as any)[r.k] || "";
          if (!v || /not\s*clearly\s*visible/i.test(v)) return null;
          return (
            <View key={r.k} style={{ flexDirection: "row", gap: 8, alignItems: "flex-start" }}>
              <Text style={{ fontSize: 14, marginTop: 1 }}>{r.emoji}</Text>
              <View style={{ flex: 1 }}>
                <Text style={{ color: C.text, fontWeight: "800", fontSize: 11 }}>{r.label}</Text>
                <Text style={{ color: C.textMuted, fontSize: 12, lineHeight: 17, marginTop: 1 }}>{v}</Text>
              </View>
            </View>
          );
        })}
      </View>
    </View>
  );
}

// ── Score gauge (SVG arc) ──────────────────────────────────────────────────
function ScoreGauge({ score }: { score: number }) {
  const size = 120;
  const stroke = 10;
  const radius = (size - stroke) / 2;
  const circ = 2 * Math.PI * radius;
  const pct = Math.max(0, Math.min(100, score)) / 100;
  const offset = circ * (1 - pct);
  const color =
    score >= 85 ? "#10b981" :
    score >= 70 ? "#84cc16" :
    score >= 55 ? "#f59e0b" :
    score >= 40 ? "#f97316" : "#ef4444";

  return (
    <View style={{ width: size, height: size, alignItems: "center", justifyContent: "center" }}>
      <Svg width={size} height={size} style={{ transform: [{ rotate: "-90deg" }] }}>
        <Circle cx={size / 2} cy={size / 2} r={radius} stroke="#ffffff15" strokeWidth={stroke} fill="none" />
        <Circle
          cx={size / 2} cy={size / 2} r={radius}
          stroke={color} strokeWidth={stroke} fill="none"
          strokeDasharray={`${circ} ${circ}`}
          strokeDashoffset={offset}
          strokeLinecap="round"
        />
      </Svg>
      <View style={{ position: "absolute", alignItems: "center" }}>
        <Text style={{ fontSize: 28, fontWeight: "900", color }}>{score}</Text>
        <Text style={{ fontSize: 9, fontWeight: "700", color: "#94a3b8", letterSpacing: 1 }}>/ 100</Text>
      </View>
    </View>
  );
}

// ── Severity color helpers ─────────────────────────────────────────────────
const SEV_OBS = {
  positive: { bg: "#10b98115", border: "#10b98155", color: "#10b981", icon: "check-circle" as const },
  neutral:  { bg: "#94a3b815", border: "#94a3b855", color: "#94a3b8", icon: "info"         as const },
  warning:  { bg: "#f59e0b15", border: "#f59e0b55", color: "#f59e0b", icon: "alert-circle" as const },
  critical: { bg: "#ef444415", border: "#ef444455", color: "#ef4444", icon: "alert-octagon"as const },
};
const SEV_DOSH = {
  minor:    { bg: "#f59e0b15", border: "#f59e0b66", color: "#f59e0b", label: "MINOR"    },
  moderate: { bg: "#f9731615", border: "#f9731666", color: "#f97316", label: "MODERATE" },
  major:    { bg: "#ef444415", border: "#ef444466", color: "#ef4444", label: "MAJOR"    },
};
const PRIORITY_COLOR = {
  high:   "#ef4444",
  medium: "#f59e0b",
  low:    "#10b981",
};

function VastuScanReport({ C, data: raw, onReset, extras }: {
  C:       any;
  data:    VastuScanResponse;
  onReset: () => void;
  extras?: {
    wall_analyses?: VastuDeepScanResponse["wall_analyses"];
    spatial_map?:   VastuDeepScanResponse["spatial_map"];
    photos_count?:  number;
    floor_plan?:    boolean;
  };
}) {
  // Defensive normalization — protect render against malformed/partial JSON.
  const data: VastuScanResponse = {
    scan_inconclusive:       Boolean(raw?.scan_inconclusive),
    inconclusive_reason:     typeof raw?.inconclusive_reason === "string" ? raw.inconclusive_reason : "",
    room_detected:           typeof raw?.room_detected       === "string" ? raw.room_detected       : "room",
    compliance_score:        Number.isFinite(raw?.compliance_score) ? Math.max(0, Math.min(100, Math.round(Number(raw.compliance_score)))) : 0,
    compliance_score_llm:    Number.isFinite(raw?.compliance_score_llm) ? Number(raw.compliance_score_llm) : undefined,
    compliance_score_method: typeof raw?.compliance_score_method === "string" ? raw.compliance_score_method : undefined,
    energy_status:           (["Excellent","Optimal","Mild Disturbance","Moderate Dosh","Significant Dosh"] as const).includes(raw?.energy_status as any) ? raw.energy_status : "Optimal",
    direction_basis:         (["magnetometer","visual_inference","assumed"] as const).includes(raw?.direction_basis as any) ? raw.direction_basis : "assumed",
    camera_facing_direction: typeof raw?.camera_facing_direction === "string" ? raw.camera_facing_direction : "Unknown",
    observations:            Array.isArray(raw?.observations) ? raw.observations.filter(Boolean) : [],
    dosh:                    Array.isArray(raw?.dosh)         ? raw.dosh.filter(Boolean)         : [],
    remedies:                Array.isArray(raw?.remedies)     ? raw.remedies.filter(Boolean)     : [],
    energy_forecast:         typeof raw?.energy_forecast === "string" ? raw.energy_forecast : "",
    confidence:              Number.isFinite(raw?.confidence) ? Math.max(0, Math.min(100, Math.round(Number(raw.confidence)))) : 0,
    heading_deg_input:       Number.isFinite(raw?.heading_deg_input) ? Number(raw.heading_deg_input) : undefined,
  };

  // Inconclusive scan — friendly empty state
  if (data.scan_inconclusive) {
    return (
      <View style={[vs.resultCard, { backgroundColor: C.bgCard2, borderColor: "#f59e0b55" }]}>
        <View style={vs.resultHeader}>
          <View style={[vs.resultAvatar, { backgroundColor: "#f59e0b20", borderColor: "#f59e0b55" }]}>
            <Feather name="alert-triangle" size={14} color="#f59e0b" />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={[vs.resultName, { color: C.text }]}>SCAN INCONCLUSIVE</Text>
            <Text style={[vs.resultSub, { color: C.textMuted }]}>Image clarity insufficient</Text>
          </View>
        </View>
        <View style={vs.divider} />
        <Text style={[vs.resultText, { color: C.textMid, fontFamily: undefined }]}>
          {data.inconclusive_reason}
        </Text>
        <Pressable onPress={onReset} style={[vs.againBtn, { borderColor: "#f59e0b55" }]}>
          <Feather name="refresh-ccw" size={13} color="#f59e0b" />
          <Text style={[vs.againText, { color: "#f59e0b" }]}>Recapture and scan again</Text>
        </Pressable>
      </View>
    );
  }

  const isReal = data.direction_basis === "magnetometer";

  return (
    <View style={[vs.resultCard, { backgroundColor: C.bgCard2, borderColor: "#a78bfa55" }]}>
      {/* Header */}
      <View style={vs.resultHeader}>
        <View style={vs.resultAvatar}>
          <Feather name="zap" size={14} color="#a78bfa" />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={[vs.resultName, { color: C.text }]}>COSMIC VASTU DRISHTI</Text>
          <Text style={[vs.resultSub, { color: C.textMuted }]}>
            v3.0 · {data.room_detected || "room"} · confidence {data.confidence}%
          </Text>
        </View>
        <View style={vs.statusDot}>
          <View style={vs.statusDotInner} />
          <Text style={vs.statusText}>SCAN OK</Text>
        </View>
      </View>

      <View style={vs.divider} />

      {/* Score + Status block */}
      <View style={vs.scoreRow}>
        <ScoreGauge score={data.compliance_score} />
        <View style={{ flex: 1, gap: 6 }}>
          <Text style={[vs.scoreLabel, { color: C.textMuted }]}>VASTU COMPLIANCE</Text>
          <Text style={[vs.scoreStatus, { color: C.text }]}>{data.energy_status}</Text>
          <View style={[vs.dirChip, { borderColor: isReal ? "#10b98166" : "#94a3b866", backgroundColor: isReal ? "#10b98115" : "#94a3b815" }]}>
            <Feather name="compass" size={11} color={isReal ? "#10b981" : "#94a3b8"} />
            <Text style={[vs.dirChipText, { color: isReal ? "#10b981" : "#94a3b8" }]}>
              {isReal
                ? `${data.camera_facing_direction} · ${data.heading_deg_input?.toFixed(1)}° (real sensor)`
                : `${data.camera_facing_direction} · ${data.direction_basis}`}
            </Text>
          </View>
          {data.compliance_score_method && (
            <Text style={[vs.scoreMethod, { color: C.textDim }]} numberOfLines={2}>
              {data.compliance_score_method}
            </Text>
          )}
        </View>
      </View>

      {/* Deep-scan extras: per-wall analysis + spatial map (rendered above observations when present) */}
      {extras?.wall_analyses && extras.wall_analyses.length > 0 && (
        <WallAnalysisBlock C={C} walls={extras.wall_analyses} />
      )}
      {extras?.spatial_map && (
        <SpatialMapBlock C={C} map={extras.spatial_map} />
      )}
      {(extras?.photos_count || extras?.floor_plan) && (
        <Text style={{ color: C.textDim, fontSize: 10, fontStyle: "italic" }}>
          Synthesized from {extras.photos_count ?? 0} directional photo{extras.photos_count === 1 ? "" : "s"}
          {extras.floor_plan ? " + floor plan" : ""}
        </Text>
      )}

      {/* Observations */}
      {data.observations.length > 0 && (
        <View style={{ gap: 8 }}>
          <Text style={[vs.sectionLabel, { color: C.textMuted }]}>🔍 KEY OBSERVATIONS</Text>
          {data.observations.map((o, i) => {
            const sev = SEV_OBS[o.severity] ?? SEV_OBS.neutral;
            return (
              <View key={i} style={[vs.obsCard, { backgroundColor: sev.bg, borderColor: sev.border }]}>
                <Feather name={sev.icon} size={14} color={sev.color} style={{ marginTop: 2 }} />
                <View style={{ flex: 1, gap: 3 }}>
                  <Text style={[vs.obsText, { color: C.text }]}>{o.text}</Text>
                  <View style={vs.obsMeta}>
                    <Text style={[vs.obsTag, { color: sev.color, borderColor: sev.border }]}>{o.direction.toUpperCase()}</Text>
                    <Text style={[vs.obsCite, { color: C.textDim }]}>📜 {o.classical_rule_ref}</Text>
                  </View>
                </View>
              </View>
            );
          })}
        </View>
      )}

      {/* Dosh detected */}
      {data.dosh.length > 0 && (
        <View style={{ gap: 8 }}>
          <Text style={[vs.sectionLabel, { color: "#ef4444" }]}>⚠️ DETECTED IMBALANCES ({data.dosh.length})</Text>
          {data.dosh.map((d, i) => {
            const sev = SEV_DOSH[d.severity] ?? SEV_DOSH.moderate;
            return (
              <View key={i} style={[vs.doshCard, { backgroundColor: sev.bg, borderColor: sev.border }]}>
                <View style={vs.doshHead}>
                  <Text style={[vs.doshName, { color: C.text }]}>{d.name}</Text>
                  <View style={[vs.doshBadge, { backgroundColor: sev.color }]}>
                    <Text style={vs.doshBadgeText}>{sev.label}</Text>
                  </View>
                </View>
                <Text style={[vs.doshDesc, { color: C.textMid }]}>{d.description}</Text>
                <Text style={[vs.doshCite, { color: C.textDim }]}>📜 {d.classical_source}</Text>
              </View>
            );
          })}
        </View>
      )}

      {/* Remedies */}
      {data.remedies.length > 0 && (
        <View style={{ gap: 8 }}>
          <Text style={[vs.sectionLabel, { color: "#10b981" }]}>🛠️ PRESCRIBED CALIBRATIONS</Text>
          {data.remedies.map((r, i) => (
            <View key={i} style={[vs.remCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <View style={[vs.remDot, { backgroundColor: PRIORITY_COLOR[r.priority] }]} />
              <View style={{ flex: 1, gap: 3 }}>
                <Text style={[vs.remText, { color: C.text }]}>{r.action}</Text>
                <View style={vs.remMeta}>
                  <Text style={[vs.remPriority, { color: PRIORITY_COLOR[r.priority] }]}>
                    {r.priority.toUpperCase()} PRIORITY
                  </Text>
                  <Text style={[vs.remCite, { color: C.textDim }]}>📜 {r.classical_source}</Text>
                </View>
              </View>
            </View>
          ))}
        </View>
      )}

      {/* Forecast */}
      {data.energy_forecast && (
        <View style={[vs.forecastCard, { borderColor: "#a78bfa55", backgroundColor: "#a78bfa10" }]}>
          <Text style={vs.forecastLabel}>🌟 ENERGY FORECAST</Text>
          <Text style={[vs.forecastText, { color: C.text }]}>{data.energy_forecast}</Text>
        </View>
      )}

      <Pressable onPress={onReset} style={[vs.againBtn, { borderColor: "#a78bfa55" }]}>
        <Feather name="refresh-ccw" size={13} color="#a78bfa" />
        <Text style={[vs.againText, { color: "#a78bfa" }]}>Run new scan</Text>
      </Pressable>
    </View>
  );
}

const vs = StyleSheet.create({
  card: {
    borderRadius: 16, borderWidth: 1.5, padding: 14, gap: 12,
    overflow: "hidden", position: "relative",
  },
  // Phase 1 structured-report styles
  headingChip: {
    flexDirection: "row", alignItems: "center", gap: 6,
    paddingHorizontal: 10, paddingVertical: 7,
    borderRadius: 8, borderWidth: 1, alignSelf: "flex-start",
  },
  headingChipText: { fontSize: 10, fontWeight: "700", letterSpacing: 0.3 },

  scoreRow: { flexDirection: "row", alignItems: "center", gap: 14 },
  scoreLabel:  { fontSize: 9, fontWeight: "800", letterSpacing: 1.5 },
  scoreStatus: { fontSize: 16, fontWeight: "900" },
  scoreMethod: { fontSize: 9, fontStyle: "italic", marginTop: 2 },
  dirChip: {
    flexDirection: "row", alignItems: "center", gap: 5,
    paddingHorizontal: 8, paddingVertical: 4,
    borderRadius: 6, borderWidth: 1, alignSelf: "flex-start",
  },
  dirChipText: { fontSize: 10, fontWeight: "700", letterSpacing: 0.3 },

  sectionLabel: { fontSize: 10, fontWeight: "900", letterSpacing: 1.5, marginTop: 4 },

  obsCard: {
    flexDirection: "row", gap: 10,
    padding: 10, borderRadius: 10, borderWidth: 1,
  },
  obsText: { fontSize: 12, lineHeight: 17, fontWeight: "600" },
  obsMeta: { flexDirection: "row", alignItems: "center", gap: 8, flexWrap: "wrap" },
  obsTag: {
    fontSize: 9, fontWeight: "900", letterSpacing: 0.8,
    paddingHorizontal: 6, paddingVertical: 2,
    borderRadius: 4, borderWidth: 1,
  },
  obsCite: { fontSize: 9, fontWeight: "600", fontStyle: "italic" },

  doshCard: { padding: 11, borderRadius: 10, borderWidth: 1, gap: 5 },
  doshHead: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: 8 },
  doshName: { fontSize: 13, fontWeight: "800", flex: 1 },
  doshBadge: { paddingHorizontal: 7, paddingVertical: 2.5, borderRadius: 4 },
  doshBadgeText: { fontSize: 8, fontWeight: "900", color: "#fff", letterSpacing: 1 },
  doshDesc: { fontSize: 12, lineHeight: 17 },
  doshCite: { fontSize: 9, fontWeight: "600", fontStyle: "italic", marginTop: 2 },

  remCard: { flexDirection: "row", gap: 10, padding: 11, borderRadius: 10, borderWidth: 1 },
  remDot:  { width: 8, height: 8, borderRadius: 4, marginTop: 6 },
  remText: { fontSize: 12, lineHeight: 17, fontWeight: "600" },
  remMeta: { flexDirection: "row", alignItems: "center", gap: 8, flexWrap: "wrap" },
  remPriority: { fontSize: 9, fontWeight: "900", letterSpacing: 0.8 },
  remCite:  { fontSize: 9, fontWeight: "600", fontStyle: "italic" },

  forecastCard: { padding: 12, borderRadius: 10, borderWidth: 1, gap: 5 },
  forecastLabel: { fontSize: 9, fontWeight: "900", letterSpacing: 1.5, color: "#a78bfa" },
  forecastText:  { fontSize: 13, lineHeight: 19, fontWeight: "600" },
  headerRow: { flexDirection: "row", alignItems: "center", gap: 12 },
  iconBox: {
    width: 44, height: 44, borderRadius: 12,
    backgroundColor: "#a78bfa20", borderWidth: 1, borderColor: "#a78bfa55",
    alignItems: "center", justifyContent: "center",
  },
  title:    { fontSize: 15, fontWeight: "800" },
  sub:      { fontSize: 11, lineHeight: 15, marginTop: 2 },
  newBadge: {
    backgroundColor: "#a78bfa", paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4,
  },
  newBadgeText: { fontSize: 8, fontWeight: "900", color: "#fff", letterSpacing: 1 },

  roomBtn: {
    flexDirection: "row", alignItems: "center", gap: 8,
    paddingHorizontal: 12, paddingVertical: 9,
    borderRadius: 10, borderWidth: 1, alignSelf: "flex-start",
  },
  roomBtnText: { fontSize: 13, fontWeight: "700" },

  pickerRow: { flexDirection: "row", gap: 10 },
  pickBtn: {
    flex: 1, alignItems: "center", gap: 4,
    paddingVertical: 16, borderRadius: 12, borderWidth: 1, borderStyle: "dashed",
  },
  pickBtnText: { fontSize: 13, fontWeight: "700", marginTop: 4 },
  pickBtnSub:  { fontSize: 10 },

  previewWrap: { borderRadius: 12, overflow: "hidden", position: "relative" },
  preview:     { width: "100%", height: 200, backgroundColor: "#0a0a0a" },
  previewClear: {
    position: "absolute", top: 8, right: 8,
    width: 28, height: 28, borderRadius: 14,
    backgroundColor: "rgba(0,0,0,0.6)",
    alignItems: "center", justifyContent: "center",
  },

  scanBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8,
    paddingVertical: 13, borderRadius: 12,
    shadowColor: "#a78bfa", shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4, shadowRadius: 10, elevation: 6,
  },
  scanBtnText: { fontSize: 13, fontWeight: "800", color: "#fff", letterSpacing: 0.3 },

  resultCard: { borderRadius: 12, borderWidth: 1, padding: 14, gap: 10 },
  resultHeader: { flexDirection: "row", alignItems: "center", gap: 10 },
  resultAvatar: {
    width: 32, height: 32, borderRadius: 16,
    backgroundColor: "#a78bfa20", borderWidth: 1, borderColor: "#a78bfa55",
    alignItems: "center", justifyContent: "center",
  },
  resultName: { fontSize: 12, fontWeight: "900", letterSpacing: 1.2 },
  resultSub:  { fontSize: 9, marginTop: 1, fontFamily: Platform.OS === "ios" ? "Menlo" : "monospace" },
  resultText: { fontSize: 13, lineHeight: 21, fontFamily: Platform.OS === "ios" ? "Menlo" : "monospace" },
  statusDot: {
    flexDirection: "row", alignItems: "center", gap: 5,
    paddingHorizontal: 7, paddingVertical: 3,
    borderRadius: 6,
    backgroundColor: "#10b98120",
    borderWidth: 1, borderColor: "#10b98166",
  },
  statusDotInner: { width: 6, height: 6, borderRadius: 3, backgroundColor: "#10b981" },
  statusText: { fontSize: 9, fontWeight: "900", color: "#10b981", letterSpacing: 1 },
  divider: { height: 1, backgroundColor: "#a78bfa30", marginVertical: 2 },
  againBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6,
    paddingVertical: 9, borderRadius: 10, borderWidth: 1, marginTop: 4,
  },
  againText: { fontSize: 11, fontWeight: "700" },

  note: { fontSize: 10, textAlign: "center", marginTop: 2 },

  modalBackdrop: {
    flex: 1, backgroundColor: "rgba(0,0,0,0.6)",
    alignItems: "center", justifyContent: "center", padding: 20,
  },
  modalCard: {
    width: "100%", maxWidth: 360, borderRadius: 16, borderWidth: 1, padding: 14, gap: 8,
  },
  modalTitle: { fontSize: 14, fontWeight: "800", marginBottom: 4 },
  modalRow: {
    flexDirection: "row", alignItems: "center", gap: 12,
    paddingHorizontal: 10, paddingVertical: 11, borderRadius: 8,
  },
  modalRowText: { fontSize: 13, fontWeight: "600", flex: 1 },
});

// ── Deep Scan card styles ─────────────────────────────────────────────────
const vds = StyleSheet.create({
  card: {
    borderRadius: 16, borderWidth: 1.5, padding: 14, gap: 12,
    overflow: "hidden", position: "relative",
    shadowColor: "#a78bfa", shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.25, shadowRadius: 14, elevation: 4,
    marginTop: 12,
  },
  glow: {
    position: "absolute", top: -40, right: -40,
    width: 140, height: 140, borderRadius: 70,
    backgroundColor: "#a78bfa20",
  },
  header: { gap: 4 },
  badge: {
    flexDirection: "row", alignItems: "center", gap: 4,
    alignSelf: "flex-start",
    paddingHorizontal: 7, paddingVertical: 3,
    borderRadius: 5,
    backgroundColor: "#7c3aed",
  },
  badgeText: { color: "#fff", fontSize: 9, fontWeight: "900", letterSpacing: 1.2 },
  title: { fontSize: 17, fontWeight: "900", marginTop: 4 },
  sub:   { fontSize: 12, lineHeight: 17 },
  roomChip: {
    flexDirection: "row", alignItems: "center", gap: 8,
    paddingHorizontal: 11, paddingVertical: 8,
    borderRadius: 10, borderWidth: 1, alignSelf: "flex-start",
  },
  roomChipText: { fontSize: 13, fontWeight: "700" },
  featureRow: { flexDirection: "row", flexWrap: "wrap", gap: 6 },
  feat: {
    flexDirection: "row", alignItems: "center", gap: 4,
    paddingHorizontal: 8, paddingVertical: 5,
    borderRadius: 6,
    backgroundColor: "#a78bfa15",
    borderWidth: 1, borderColor: "#a78bfa33",
  },
  featText: { color: "#cbb8ff", fontSize: 10, fontWeight: "700" },
  startBtn: { borderRadius: 12, overflow: "hidden" },
  startBtnInner: {
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8,
    paddingVertical: 14,
  },
  startBtnText: { color: "#fff", fontSize: 14, fontWeight: "900", letterSpacing: 0.5 },
  note: { fontSize: 10, textAlign: "center", marginTop: 2 },
});

// ── Wizard styles ─────────────────────────────────────────────────────────
const ds = StyleSheet.create({
  header: {
    flexDirection: "row", alignItems: "center",
    paddingHorizontal: 12, paddingVertical: 8,
    borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: "#ffffff15",
  },
  headerBtn: { padding: 6 },
  headerTitle: { fontSize: 14, fontWeight: "800" },
  headerSub:   { fontSize: 10, marginTop: 1, letterSpacing: 0.5 },
  dotsRow: {
    flexDirection: "row", justifyContent: "center", gap: 8, paddingVertical: 10,
  },
  dot: { width: 28, height: 4, borderRadius: 2 },
  stepTitle: { fontSize: 22, fontWeight: "900", marginTop: 4 },
  stepSub:   { fontSize: 12, marginTop: 4 },
  dialWrap:  { alignItems: "center", marginVertical: 18 },
  statusPill: {
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6,
    alignSelf: "center",
    paddingHorizontal: 14, paddingVertical: 9,
    borderRadius: 999, borderWidth: 1,
    marginBottom: 12,
  },
  helper: {
    fontSize: 12, lineHeight: 17, textAlign: "center", marginBottom: 14,
  },
  thumbWrap: {
    borderRadius: 12, overflow: "hidden", marginBottom: 14,
    borderWidth: 1, borderColor: "#10b98166",
  },
  thumbImg: { width: "100%", height: 160 },
  thumbBadge: {
    position: "absolute", top: 8, left: 8,
    flexDirection: "row", alignItems: "center", gap: 5,
    paddingHorizontal: 8, paddingVertical: 4,
    borderRadius: 6,
    backgroundColor: "rgba(0,0,0,0.7)",
  },
  thumbBadgeText: { color: "#10b981", fontSize: 10, fontWeight: "800" },
  btnRow: { flexDirection: "row", gap: 8, marginBottom: 12 },
  bigBtn: {
    flex: 1,
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8,
    paddingVertical: 14, borderRadius: 12,
  },
  bigBtnText: { color: "#fff", fontSize: 14, fontWeight: "800" },
  smallBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6,
    paddingHorizontal: 14, paddingVertical: 14,
    borderRadius: 12, borderWidth: 1,
  },
  smallBtnText: { fontSize: 12, fontWeight: "700" },
  nextBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6,
    paddingVertical: 14, borderRadius: 12,
  },
  nextBtnText: { color: "#fff", fontSize: 14, fontWeight: "900" },
  uploadCard: {
    height: 180, borderRadius: 12, borderWidth: 1, borderStyle: "dashed",
    alignItems: "center", justifyContent: "center", gap: 8,
    marginVertical: 14, overflow: "hidden",
  },
  fpImg: { width: "100%", height: "100%" },
  uploadHint: { fontSize: 12 },
  reviewGrid: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginTop: 8 },
  reviewCell: {
    width: "48%",
    borderRadius: 10, borderWidth: 1, padding: 8, gap: 4,
    overflow: "hidden",
  },
  reviewImg: { width: "100%", height: 90, borderRadius: 6, backgroundColor: "#0a0a0f" },
  reviewLabel: { fontSize: 11, fontWeight: "800" },
  reviewMeta:  { fontSize: 9 },
  fineprint: { fontSize: 10, textAlign: "center", marginTop: 10 },
});


export default function VastuScreen() {
  const insets = useSafeAreaInsets();
  const C      = useC();
  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  const [section, setSection] = useState<"basic" | "pro">("basic");

  return (
    <View style={[s.root, { backgroundColor: C.isDark ? "#050709" : C.bg }]}>
      {/* Premium dark gradient backdrop (black → deep brown) — dark mode only */}
      {C.isDark && (
        <LinearGradient
          colors={["#050709", "#0a0604", "#1a0e02"]}
          locations={[0, 0.55, 1]}
          style={StyleSheet.absoluteFill}
          pointerEvents="none"
        />
      )}
      <View style={[s.header, { paddingTop: topPad + 8, borderBottomColor: C.border }]}>
        <Pressable onPress={() => router.back()} style={s.back}>
          <Feather name="arrow-left" size={20} color={C.textMuted} />
        </Pressable>
        <View style={{ flex:1 }}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
            <Text style={[s.title, { color: C.text }]}>AstroVastu</Text>
            <View style={s.premiumBadge}>
              <Feather name="star" size={9} color="#3a2404" />
              <Text style={s.premiumBadgeText}>PREMIUM</Text>
            </View>
          </View>
          <Text style={[s.titleHindi, { color: C.textMuted }]}>Sacred Compass · Room-wise Guidance</Text>
        </View>
      </View>

      {/* ── Basic / Pro Tab Selector ── */}
      <View style={[s.tabBar, { borderBottomColor: C.border, backgroundColor: C.bg }]}>
        <Pressable
          onPress={() => { Haptics.selectionAsync?.(); setSection("basic"); }}
          style={[s.tabPill, section === "basic" && { backgroundColor: C.bgCard2, borderColor: C.accent }]}
        >
          <Feather name="home" size={13} color={section === "basic" ? C.accent : C.textMuted} />
          <Text style={[s.tabPillText, { color: section === "basic" ? C.accent : C.textMuted, fontWeight: section === "basic" ? "800" : "600" }]}>
            Basic
          </Text>
          <Text style={[s.tabPillSub, { color: section === "basic" ? C.accent : C.textDim }]}>BASIC</Text>
        </Pressable>
        <Pressable
          onPress={() => { Haptics.selectionAsync?.(); setSection("pro"); }}
          style={[s.tabPill, section === "pro" && { backgroundColor: "#f9d76b18", borderColor: "#f9d76b" }]}
        >
          <Feather name="award" size={13} color={section === "pro" ? "#f9d76b" : C.textMuted} />
          <Text style={[s.tabPillText, { color: section === "pro" ? "#f9d76b" : C.textMuted, fontWeight: section === "pro" ? "800" : "600" }]}>
            Pro
          </Text>
          <Text style={[s.tabPillSub, { color: section === "pro" ? "#f9d76b" : C.textDim }]}>🔒</Text>
        </Pressable>
      </View>

      <ScrollView
        contentContainerStyle={[s.content, { paddingBottom: botPad + 30 }]}
        showsVerticalScrollIndicator={false}
      >
        {section === "basic" ? (
          <>
            {/* ── AstroVastu Quick Check (kundli-personalized single-room) ── */}
            <Pressable
              onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); router.push("/astrovastu-basic" as any); }}
              style={[s.heroCard, { borderColor: C.accent, backgroundColor: C.isDark ? "#0c1722" : C.bgCard }]}
            >
              <View style={[s.heroBadge, { backgroundColor: `${C.accent}22`, borderColor: C.accent }]}>
                <Text style={{ fontSize: 9, fontWeight: "900", color: C.accent, letterSpacing: 1.4 }}>NEW · BASIC</Text>
              </View>
              <View style={{ flexDirection: "row", alignItems: "center", gap: 12 }}>
                <Text style={{ fontSize: 30 }}>🔮</Text>
                <View style={{ flex: 1 }}>
                  <Text style={[s.heroTitle, { color: C.text }]}>AstroVastu Quick Check</Text>
                  <Text style={[s.heroSub, { color: C.textMuted }]}>
                    Apni kundli ke hisaab se ek room ka Vastu — instant verdict & remedies
                  </Text>
                </View>
                <Feather name="chevron-right" size={18} color={C.accent} />
              </View>
            </Pressable>

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

            {/* ── Vastu Drishti Scan (single-photo Acharya analysis) ── */}
            <VastuScanCard C={C} />

            {/* ── Deep Scan (Phase 2 — 4-wall guided multi-photo + spatial map) ── */}
            <VastuDeepScanCard C={C} />

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

            {/* Upsell teaser → Pro */}
            <Pressable
              onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); setSection("pro"); }}
              style={s.upsellCard}
            >
              <View style={s.upsellGlow} />
              <Feather name="award" size={18} color="#f9d76b" />
              <View style={{ flex: 1 }}>
                <Text style={s.upsellTitle}>Unlock AstroVastu Pro</Text>
                <Text style={s.upsellSub}>Personal home analysis, kundli-matched directions, yantra remedies & expert consultation</Text>
              </View>
              <Feather name="chevron-right" size={16} color="#f9d76b" />
            </Pressable>

            {/* Disclaimer */}
            <View style={[s.disclaimer, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <Feather name="info" size={12} color={C.textMuted} />
              <Text style={[s.disclaimerText, { color: C.textMuted }]}>
                This is a general Vastu guide. For your home specifically, always consult a qualified
                Vastu expert for personalized advice.
              </Text>
            </View>
          </>
        ) : (
          <ProSection C={C} />
        )}
      </ScrollView>
    </View>
  );
}

// ── Pro Section ──────────────────────────────────────────────────────────────
function ProSection({ C }: { C: any }) {
  const PRO_FEATURES = [
    {
      icon: "📐",
      title: "Home Blueprint Vastu Scan",
      desc: "Apne ghar ka photo ya map upload karein — AI direction-wise dosh & remedy report banayega",
      color: "#a78bfa",
    },
    {
      icon: "🎯",
      title: "Kundli + Vastu Match",
      desc: "Aap ki kundli ke hisaab se personal lucky directions, colors, aur yantra placement",
      color: "#f59e0b",
    },
    {
      icon: "💎",
      title: "Direction-wise Gem & Yantra Guide",
      desc: "Har dish ke liye sahi crystal, ratna, aur yantra — with placement instructions",
      color: "#22c55e",
    },
    {
      icon: "🔮",
      title: "Vastu Dosh Detection",
      desc: "11+ common Vastu defects identify karein with step-by-step remedies (no demolition)",
      color: "#ef4444",
    },
    {
      icon: "🪔",
      title: "Pooja Room Deep Analysis",
      desc: "Mandir placement, deity direction, colors, ingredient list — complete guide",
      color: "#fbbf24",
    },
    {
      icon: "🏢",
      title: "Office & Business Vastu",
      desc: "Career & wealth-focused direction analysis for desk, cash locker, main door",
      color: "#06b6d4",
    },
    {
      icon: "👨‍🏫",
      title: "1-on-1 Expert Consultation",
      desc: "Certified Vastu expert se 30-min video call (monthly included in Pro plan)",
      color: "#ec4899",
    },
    {
      icon: "📅",
      title: "Griha Pravesh Muhurat",
      desc: "Shubh date & time for home entry, kitchen opening, foundation laying",
      color: "#8b5cf6",
    },
  ];

  async function openWhatsApp() {
    const msg = encodeURIComponent("Namaste 🙏 Mujhe AstroVastu Pro ke baare mein jaankari chahiye — personal Vastu consultation kaise book karun?");
    const url = `https://wa.me/919040524394?text=${msg}`;
    if (Platform.OS === "web") {
      if (typeof window !== "undefined") window.open(url, "_blank");
    } else {
      try { await Linking.openURL(url); } catch {}
    }
  }

  return (
    <>
      {/* Pro Hero Banner */}
      <View style={s.proHero}>
        <View style={s.proHeroGlow} />
        <View style={s.proCrown}>
          <Text style={{ fontSize: 34 }}>👑</Text>
        </View>
        <Text style={s.proHeroTitle}>AstroVastu Pro</Text>
        <Text style={s.proHeroSub}>Personalized premium Vastu analysis</Text>
        <View style={s.proHeroBadgeRow}>
          <View style={s.proHeroBadge}>
            <Text style={s.proHeroBadgeText}>₹499/mo</Text>
          </View>
          <View style={[s.proHeroBadge, { backgroundColor: "#fff2b820", borderColor: "#fff2b855" }]}>
            <Text style={[s.proHeroBadgeText, { color: "#fff2b8" }]}>Cancel anytime</Text>
          </View>
        </View>
      </View>

      <Text style={[s.sectionLabel, { color: "#f9d76b" }]}>✨ PREMIUM FEATURES</Text>
      <Text style={[s.sectionSub, { color: C.textMuted }]}>Everything in Basic + advanced personal analysis</Text>

      {/* Feature list */}
      {PRO_FEATURES.map((f, i) => (
        <View key={i} style={[s.proFeature, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <View style={[s.proFeatureIcon, { backgroundColor: `${f.color}18`, borderColor: `${f.color}40` }]}>
            <Text style={{ fontSize: 22 }}>{f.icon}</Text>
          </View>
          <View style={{ flex: 1 }}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
              <Text style={[s.proFeatureTitle, { color: C.text }]}>{f.title}</Text>
              <View style={s.proPill}>
                <Feather name="lock" size={7} color="#f9d76b" />
                <Text style={s.proPillText}>PRO</Text>
              </View>
            </View>
            <Text style={[s.proFeatureDesc, { color: C.textMuted }]}>{f.desc}</Text>
          </View>
        </View>
      ))}

      {/* ── Open AstroVastu Deep Scan (server-side gated for Pro plan) ── */}
      <Pressable
        onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); router.push("/astrovastu-pro" as any); }}
        style={s.ctaPrimary}
      >
        <Feather name="award" size={16} color="#3a2404" />
        <Text style={s.ctaPrimaryText}>🌟 Open AstroVastu Deep Scan</Text>
      </Pressable>

      {/* Upgrade fallback (for users without Pro plan) */}
      <Pressable
        onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); router.push("/subscription" as any); }}
        style={[s.ctaSecondary, { borderColor: "#f9d76b66", backgroundColor: "#f9d76b12" }]}
      >
        <Feather name="zap" size={15} color="#f9d76b" />
        <Text style={[s.ctaSecondaryText, { color: "#f9d76b" }]}>Upgrade to Pro — ₹499/mo</Text>
      </Pressable>

      <Pressable onPress={openWhatsApp} style={[s.ctaSecondary, { borderColor: C.border, backgroundColor: C.bgCard }]}>
        <Feather name="message-circle" size={15} color="#25D366" />
        <Text style={[s.ctaSecondaryText, { color: C.text }]}>Talk to Vastu Expert on WhatsApp</Text>
      </Pressable>

      <View style={[s.disclaimer, { backgroundColor: C.bgCard, borderColor: C.border }]}>
        <Feather name="info" size={12} color={C.textMuted} />
        <Text style={[s.disclaimerText, { color: C.textMuted }]}>
          Pro features require an active AstroVastu Pro subscription. Cancel anytime from your profile.
        </Text>
      </View>
    </>
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
  heroCard:   { borderRadius:16, borderWidth:2, padding:14, gap:10, position:"relative" },
  heroBadge:  { alignSelf:"flex-start", paddingHorizontal:8, paddingVertical:3, borderRadius:6, borderWidth:1 },
  heroTitle:  { fontSize:15, fontWeight:"800", marginBottom:3 },
  heroSub:    { fontSize:11, lineHeight:16 },
  introTitle: { fontSize:13, fontWeight:"700", marginBottom:5 },
  introBody:  { fontSize:12, lineHeight:19 },
  genCard:    { borderRadius:14, borderWidth:1, padding:14, gap:10 },
  genTitle:   { fontSize:13, fontWeight:"700", marginBottom:4 },
  genRow:     { flexDirection:"row", alignItems:"flex-start", gap:10 },
  genDot:     { width:6, height:6, borderRadius:3, marginTop:5, flexShrink:0 },
  genText:    { fontSize:12, lineHeight:19, flex:1 },
  disclaimer: { flexDirection:"row", alignItems:"flex-start", gap:8, borderRadius:10, padding:12, borderWidth:1 },
  disclaimerText: { fontSize:11, lineHeight:17, flex:1 },

  // Premium badge in header
  premiumBadge: {
    flexDirection: "row", alignItems: "center", gap: 3,
    backgroundColor: "#f9d76b",
    paddingHorizontal: 6, paddingVertical: 2,
    borderRadius: 4,
    borderWidth: 1, borderColor: "#c89020",
  },
  premiumBadgeText: {
    fontSize: 8, fontWeight: "900", color: "#3a2404",
    letterSpacing: 1,
  },

  // Tab bar (Basic / Pro)
  tabBar: {
    flexDirection: "row",
    gap: 8,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderBottomWidth: 1,
  },
  tabPill: {
    flex: 1,
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 6,
    paddingVertical: 9,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "transparent",
  },
  tabPillText: { fontSize: 13, letterSpacing: 0.2 },
  tabPillSub: { fontSize: 9, fontWeight: "700", letterSpacing: 0.5 },

  // Upsell banner on Basic tab
  upsellCard: {
    flexDirection: "row", alignItems: "center", gap: 10,
    padding: 14,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#f9d76b55",
    backgroundColor: "#1a1408",
    overflow: "hidden",
    position: "relative",
  },
  upsellGlow: {
    position: "absolute",
    top: -30, right: -30,
    width: 120, height: 120,
    borderRadius: 60,
    backgroundColor: "#f9d76b12",
  },
  upsellTitle: {
    fontSize: 14, fontWeight: "800",
    color: "#f9d76b",
    marginBottom: 2,
  },
  upsellSub: {
    fontSize: 11, lineHeight: 16,
    color: "#e0c080",
  },

  // Pro hero banner
  proHero: {
    alignItems: "center",
    padding: 24,
    borderRadius: 18,
    borderWidth: 1.5,
    borderColor: "#f9d76b66",
    backgroundColor: "#0f0a02",
    overflow: "hidden",
    position: "relative",
    gap: 6,
  },
  proHeroGlow: {
    position: "absolute",
    top: -60, left: "50%",
    width: 260, height: 260,
    borderRadius: 130,
    backgroundColor: "#f9d76b1a",
    marginLeft: -130,
  },
  proCrown: {
    width: 60, height: 60, borderRadius: 30,
    backgroundColor: "#f9d76b20",
    borderWidth: 1, borderColor: "#f9d76b66",
    alignItems: "center", justifyContent: "center",
    marginBottom: 4,
  },
  proHeroTitle: {
    fontSize: 22, fontWeight: "900",
    color: "#f9d76b",
    letterSpacing: -0.4,
  },
  proHeroSub: {
    fontSize: 12,
    color: "#c4a050",
    marginBottom: 8,
  },
  proHeroBadgeRow: {
    flexDirection: "row", gap: 8,
  },
  proHeroBadge: {
    backgroundColor: "#f9d76b25",
    borderWidth: 1, borderColor: "#f9d76b80",
    paddingHorizontal: 12, paddingVertical: 5,
    borderRadius: 20,
  },
  proHeroBadgeText: {
    fontSize: 11, fontWeight: "800",
    color: "#f9d76b",
    letterSpacing: 0.3,
  },

  // Pro feature card
  proFeature: {
    flexDirection: "row", alignItems: "center", gap: 12,
    padding: 14,
    borderRadius: 14,
    borderWidth: 1,
  },
  proFeatureIcon: {
    width: 46, height: 46, borderRadius: 12,
    alignItems: "center", justifyContent: "center",
    borderWidth: 1,
  },
  proFeatureTitle: {
    fontSize: 13, fontWeight: "700",
  },
  proFeatureDesc: {
    fontSize: 11, lineHeight: 16,
    marginTop: 3,
  },
  proPill: {
    flexDirection: "row", alignItems: "center", gap: 2,
    backgroundColor: "#f9d76b15",
    borderWidth: 1, borderColor: "#f9d76b55",
    paddingHorizontal: 5, paddingVertical: 1,
    borderRadius: 5,
  },
  proPillText: {
    fontSize: 8, fontWeight: "800",
    color: "#f9d76b",
    letterSpacing: 0.5,
  },

  // CTA buttons
  ctaPrimary: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 8,
    paddingVertical: 14,
    borderRadius: 12,
    backgroundColor: "#f9d76b",
    shadowColor: "#f9d76b",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.4,
    shadowRadius: 10,
    elevation: 8,
    marginTop: 6,
  },
  ctaPrimaryText: {
    fontSize: 14, fontWeight: "900",
    color: "#3a2404",
    letterSpacing: 0.3,
  },
  ctaSecondary: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 8,
    paddingVertical: 13,
    borderRadius: 12,
    borderWidth: 1,
  },
  ctaSecondaryText: {
    fontSize: 13, fontWeight: "700",
  },
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
