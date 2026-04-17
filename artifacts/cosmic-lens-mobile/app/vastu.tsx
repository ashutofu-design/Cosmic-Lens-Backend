import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { Magnetometer } from "expo-sensors";
import { router } from "expo-router";
import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  Animated, Dimensions, Linking, Platform, Pressable, ScrollView,
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
  const midR   = (innerR + outerR) / 2;
  const petalR = outerR + SIZE * 0.018;

  return (
    <Svg width={SIZE} height={SIZE}>
      <Defs>
        {/* Jewel-tone sector gradients — color at low alpha over dark */}
        {DIRS.map(d => (
          <RadialGradient key={`jw-${d.short}`} id={`jw-${d.short}`} cx="50%" cy="50%" r="75%">
            <Stop offset="0"    stopColor={d.color} stopOpacity="0.32" />
            <Stop offset="0.55" stopColor={d.color} stopOpacity="0.12" />
            <Stop offset="1"    stopColor="#050914" stopOpacity="1"    />
          </RadialGradient>
        ))}
        {/* Sheen overlay on sectors */}
        <SvgLinearGradient id="sectorSheen" x1="0" y1="0" x2="0" y2="1">
          <Stop offset="0"   stopColor="#fff2b8" stopOpacity="0.18" />
          <Stop offset="0.5" stopColor="#fff2b8" stopOpacity="0.04" />
          <Stop offset="1"   stopColor="#000000" stopOpacity="0.25" />
        </SvgLinearGradient>
        {/* Gold ambient shine */}
        <RadialGradient id="ring-shine" cx="38%" cy="28%" r="80%">
          <Stop offset="0"   stopColor="#f9d76b" stopOpacity="0.22" />
          <Stop offset="0.6" stopColor="#f9d76b" stopOpacity="0.04" />
          <Stop offset="1"   stopColor="#f9d76b" stopOpacity="0"    />
        </RadialGradient>
        {/* Petal gradient */}
        <SvgLinearGradient id="petal" x1="0" y1="0" x2="0" y2="1">
          <Stop offset="0"   stopColor="#fff2b8" stopOpacity="0.8" />
          <Stop offset="1"   stopColor="#7a4800" stopOpacity="0.9" />
        </SvgLinearGradient>
      </Defs>

      {/* ── Layer 1: Jewel-tone sectors ── */}
      {DIRS.map(d => {
        const mid  = toRad(d.deg);
        const path = wedgePath(CX, CY, innerR, outerR, d.deg - 22.4, d.deg + 22.4);
        return (
          <G key={`s-${d.short}`}>
            <Path d={path} fill={`url(#jw-${d.short})`} />
            <Path d={path} fill="url(#sectorSheen)" opacity="0.7" />
            {/* gold radial divider line */}
            <Line
              x1={CX + innerR * Math.cos(toRad(d.deg - 22.4))}
              y1={CY + innerR * Math.sin(toRad(d.deg - 22.4))}
              x2={CX + outerR * Math.cos(toRad(d.deg - 22.4))}
              y2={CY + outerR * Math.sin(toRad(d.deg - 22.4))}
              stroke="#f9d76b" strokeWidth="0.7" opacity="0.45"
            />
          </G>
        );
      })}

      {/* Ambient gold shine overlay */}
      <Circle cx={CX} cy={CY} r={outerR} fill="url(#ring-shine)" />

      {/* ── Layer 2: 8-petal lotus ring (outer decoration) ── */}
      {DIRS.map(d => {
        const mid   = toRad(d.deg + 22.5); // between sectors
        const px    = CX + petalR * Math.cos(mid);
        const py    = CY + petalR * Math.sin(mid);
        const pLen  = SIZE * 0.052;
        const pWid  = SIZE * 0.022;
        // petal tangent vectors
        const tx    = -Math.sin(mid), ty = Math.cos(mid);
        const nx    = Math.cos(mid),  ny = Math.sin(mid);
        const tip1  = `${px + nx * pLen * 0.5},${py + ny * pLen * 0.5}`;
        const tip2  = `${px - nx * pLen * 0.5},${py - ny * pLen * 0.5}`;
        const side1 = `${px + tx * pWid},${py + ty * pWid}`;
        const side2 = `${px - tx * pWid},${py - ty * pWid}`;
        return (
          <G key={`pt-${d.deg}`} opacity="0.55">
            <Path
              d={`M ${tip1} Q ${side1} ${tip2} Q ${side2} ${tip1} Z`}
              fill="url(#petal)" stroke="#f9d76b" strokeWidth="0.6"
            />
          </G>
        );
      })}

      {/* ── Layer 3: Direction labels ── */}
      {DIRS.map(d => {
        const isCardinal = d.deg % 90 === 0;
        const mid = toRad(d.deg);
        const lx  = CX + LABEL_R * Math.cos(mid);
        const ly  = CY + LABEL_R * Math.sin(mid);
        const hx  = CX + HINDI_R * Math.cos(mid);
        const hy  = CY + HINDI_R * Math.sin(mid);
        const ex  = CX + elemR   * Math.cos(mid);
        const ey  = CY + elemR   * Math.sin(mid);
        return (
          <G key={`l-${d.short}`}>
            {/* Cardinal arrow tip — metallic gold */}
            {isCardinal && (() => {
              const tip  = CX + (outerR + SIZE * 0.030) * Math.cos(mid);
              const tipY = CY + (outerR + SIZE * 0.030) * Math.sin(mid);
              const bx1  = CX + outerR * Math.cos(mid - 0.14);
              const by1  = CY + outerR * Math.sin(mid - 0.14);
              const bx2  = CX + outerR * Math.cos(mid + 0.14);
              const by2  = CY + outerR * Math.sin(mid + 0.14);
              return (
                <Polygon
                  points={`${tip},${tipY} ${bx1},${by1} ${bx2},${by2}`}
                  fill="#f9d76b" stroke="#3a2404" strokeWidth="0.6"
                />
              );
            })()}

            {/* Short code */}
            <SvgText
              x={lx} y={ly}
              textAnchor="middle" alignmentBaseline="middle"
              fill={isCardinal ? "#fff8dc" : "#f9d76b"}
              fontSize={isCardinal ? SIZE * 0.064 : SIZE * 0.046}
              fontWeight="900"
              letterSpacing={1}
            >
              {d.short}
            </SvgText>

            {/* Hindi name — glowing color */}
            <SvgText
              x={hx} y={hy}
              textAnchor="middle" alignmentBaseline="middle"
              fill={d.color}
              fontSize={SIZE * 0.032}
              fontWeight="700"
              opacity={0.95}
            >
              {d.hindi}
            </SvgText>
          </G>
        );
      })}

      {/* ── Layer 4: Gold filigree separator rings ── */}
      <Circle cx={CX} cy={CY} r={outerR}  fill="none" stroke="#f9d76b" strokeWidth="1.2" opacity="0.55" />
      <Circle cx={CX} cy={CY} r={outerR - SIZE * 0.008} fill="none" stroke="#3a2404" strokeWidth="0.5" opacity="0.8" />
      <Circle cx={CX} cy={CY} r={midR}   fill="none" stroke="#f9d76b" strokeWidth="0.5" opacity="0.25" strokeDasharray="2 3" />
      <Circle cx={CX} cy={CY} r={innerR + SIZE * 0.010} fill="none" stroke="#3a2404" strokeWidth="0.5" opacity="0.7" />
      <Circle cx={CX} cy={CY} r={innerR} fill="none" stroke="#f9d76b" strokeWidth="1.4" opacity="0.7" />

      {/* 8 tiny rivet dots on inner gold ring */}
      {DIRS.map(d => {
        const ang = toRad(d.deg + 22.5);
        const rx  = CX + (innerR + SIZE * 0.005) * Math.cos(ang);
        const ry  = CY + (innerR + SIZE * 0.005) * Math.sin(ang);
        return (
          <G key={`rd-${d.deg}`}>
            <Circle cx={rx} cy={ry} r={SIZE * 0.007} fill="#3a2404" />
            <Circle cx={rx} cy={ry} r={SIZE * 0.005} fill="#f9d76b" />
            <Circle cx={rx - 0.4} cy={ry - 0.4} r={SIZE * 0.0018} fill="#fff8dc" opacity="0.9" />
          </G>
        );
      })}
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
    const rInner  = isMajor ? BEZEL_INNER_R - SIZE * 0.042
                  : isHalf  ? BEZEL_INNER_R - SIZE * 0.022
                             : BEZEL_INNER_R - SIZE * 0.014;
    ticks.push(
      <Line
        key={i}
        x1={CX + rOuter * Math.cos(ang)} y1={CY + rOuter * Math.sin(ang)}
        x2={CX + rInner * Math.cos(ang)} y2={CY + rInner * Math.sin(ang)}
        stroke={isMajor ? "#fff2b8" : isHalf ? "#e8c84b" : "#96690f"}
        strokeWidth={isMajor ? 2.6 : isHalf ? 1.6 : 0.9}
        strokeLinecap="round"
      />
    );
  }

  // 8 decorative rivets at cardinal/ordinal positions (between gold rings)
  const rivetR = SIZE * 0.462;
  const rivets = DIRS.map(d => {
    const ang = toRad(d.deg + 22.5); // between sectors
    const rx  = CX + rivetR * Math.cos(ang);
    const ry  = CY + rivetR * Math.sin(ang);
    return (
      <G key={`rv-${d.deg}`}>
        <Circle cx={rx} cy={ry} r={SIZE * 0.011} fill="#3a2404" />
        <Circle cx={rx} cy={ry} r={SIZE * 0.0085} fill="url(#rivetGold)" />
        <Circle cx={rx - SIZE * 0.002} cy={ry - SIZE * 0.002} r={SIZE * 0.003} fill="#fff8dc" opacity="0.85" />
      </G>
    );
  });

  return (
    <Svg width={SIZE} height={SIZE}>
      <Defs>
        {/* Background deep radial (obsidian-like) */}
        <RadialGradient id="bg" cx="50%" cy="35%" r="72%">
          <Stop offset="0"   stopColor="#1b2a4a" />
          <Stop offset="0.55" stopColor="#0a1428" />
          <Stop offset="1"   stopColor="#02060f" />
        </RadialGradient>
        {/* Primary gold ring — rich 24k look */}
        <SvgLinearGradient id="gold" x1="0.15" y1="0" x2="0.85" y2="1">
          <Stop offset="0"    stopColor="#fff2b8" />
          <Stop offset="0.20" stopColor="#ffd966" />
          <Stop offset="0.50" stopColor="#c89020" />
          <Stop offset="0.80" stopColor="#7a4800" />
          <Stop offset="1"    stopColor="#3a2404" />
        </SvgLinearGradient>
        {/* Inner gold ring — brushed metal */}
        <SvgLinearGradient id="goldInner" x1="0" y1="0" x2="1" y2="1">
          <Stop offset="0"    stopColor="#e8c84b" />
          <Stop offset="0.5"  stopColor="#f9d76b" />
          <Stop offset="1"    stopColor="#8a6020" />
        </SvgLinearGradient>
        {/* Highlight arc (sheen) */}
        <SvgLinearGradient id="goldShine" x1="0.2" y1="0" x2="0.8" y2="1">
          <Stop offset="0"   stopColor="#ffffff" stopOpacity="0.75" />
          <Stop offset="1"   stopColor="#ffffff" stopOpacity="0" />
        </SvgLinearGradient>
        {/* Rivet gold (small) */}
        <RadialGradient id="rivetGold" cx="35%" cy="30%" r="70%">
          <Stop offset="0"   stopColor="#fff2b8" />
          <Stop offset="1"   stopColor="#7a4800" />
        </RadialGradient>
      </Defs>

      {/* Background circle */}
      <Circle cx={CX} cy={CY} r={BEZEL_INNER_R} fill="url(#bg)" />

      {/* Outer deep gold ring */}
      <Circle
        cx={CX} cy={CY} r={BEZEL_OUTER_R}
        fill="none" stroke="url(#gold)"
        strokeWidth={SIZE * 0.034}
      />
      {/* Outer ring thin dark edge */}
      <Circle cx={CX} cy={CY} r={BEZEL_OUTER_R + SIZE * 0.017} fill="none" stroke="#2a1804" strokeWidth="0.8" opacity="0.9" />
      <Circle cx={CX} cy={CY} r={BEZEL_OUTER_R - SIZE * 0.017} fill="none" stroke="#2a1804" strokeWidth="0.8" opacity="0.9" />

      {/* Top sheen on gold ring (shine) */}
      <Circle
        cx={CX} cy={CY} r={BEZEL_OUTER_R}
        fill="none" stroke="url(#goldShine)"
        strokeWidth={SIZE * 0.016}
        strokeDasharray={`${BEZEL_OUTER_R * Math.PI * 0.42} ${BEZEL_OUTER_R * Math.PI * 1.58}`}
        strokeDashoffset={BEZEL_OUTER_R * Math.PI * 0.88}
      />

      {/* Rivets */}
      {rivets}

      {/* Inner gold accent ring */}
      <Circle cx={CX} cy={CY} r={BEZEL_INNER_R + SIZE * 0.005} fill="none" stroke="url(#goldInner)" strokeWidth={SIZE * 0.009} />
      <Circle cx={CX} cy={CY} r={BEZEL_INNER_R - SIZE * 0.002} fill="none" stroke="#3a2404" strokeWidth="0.7" opacity="0.85" />

      {/* Tick marks */}
      {ticks}

      {/* Degree labels only at cardinal positions (just inside bezel) */}
      {DIRS.filter(d => d.deg % 90 === 0).map(d => {
        const ang = toRad(d.deg);
        const r   = BEZEL_INNER_R - SIZE * 0.028;
        const lx  = CX + r * Math.cos(ang);
        const ly  = CY + r * Math.sin(ang);
        return (
          <SvgText
            key={`deg-${d.short}`}
            x={lx} y={ly}
            textAnchor="middle" alignmentBaseline="middle"
            fill="#f9d76b"
            fontSize={SIZE * 0.024}
            fontWeight="600"
            opacity="0.55"
          >
            {d.deg.toString().padStart(3, "0")}°
          </SvgText>
        );
      })}
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

// ── North pointer (fixed ruby+gold indicator at top) ───────────────────────────
function NorthPointer() {
  const tipY   = SIZE * 0.022;
  const baseY  = SIZE * 0.078;
  const halfW  = SIZE * 0.036;
  const midY   = (tipY + baseY) / 2;
  return (
    <Svg width={SIZE} height={SIZE} style={StyleSheet.absoluteFill}>
      <Defs>
        <SvgLinearGradient id="redArrow" x1="0" y1="0" x2="0" y2="1">
          <Stop offset="0"    stopColor="#ff8a8a" />
          <Stop offset="0.45" stopColor="#dc2626" />
          <Stop offset="1"    stopColor="#7f1d1d" />
        </SvgLinearGradient>
        <SvgLinearGradient id="redShine" x1="0" y1="0" x2="1" y2="1">
          <Stop offset="0"    stopColor="#ffffff" stopOpacity="0.65" />
          <Stop offset="0.6"  stopColor="#ffffff" stopOpacity="0" />
        </SvgLinearGradient>
      </Defs>
      {/* Shadow */}
      <Polygon
        points={`${CX + 1.5},${tipY + 2} ${CX - halfW + 1.5},${baseY + 2} ${CX + halfW + 1.5},${baseY + 2}`}
        fill="#00000066"
      />
      {/* Red arrow body */}
      <Polygon
        points={`${CX},${tipY} ${CX - halfW},${baseY} ${CX + halfW},${baseY}`}
        fill="url(#redArrow)"
      />
      {/* Shine on left side */}
      <Polygon
        points={`${CX},${tipY} ${CX - halfW * 0.7},${baseY - 2} ${CX - 1},${midY}`}
        fill="url(#redShine)"
      />
      {/* Gold outline */}
      <Polygon
        points={`${CX},${tipY} ${CX - halfW},${baseY} ${CX + halfW},${baseY}`}
        fill="none" stroke="#f9d76b" strokeWidth="1.4"
      />
      {/* Tip gold dot */}
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

      {/* ── Compass graphic with 3D premium frame ── */}
      <View style={cp.compassFrame}>
        <View style={cp.compassOuterRing}>
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
        </View>
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
    backgroundColor: "rgba(249,215,107,0.08)",
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
export default function VastuScreen() {
  const insets = useSafeAreaInsets();
  const C      = useC();
  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  const [section, setSection] = useState<"basic" | "pro">("basic");

  return (
    <View style={[s.root, { backgroundColor: C.bg }]}>
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
          <Text style={[s.titleHindi, { color: C.textMuted }]}>वास्तु शास्त्र · Compass + Room-wise Guidance</Text>
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
          <Text style={[s.tabPillSub, { color: section === "basic" ? C.accent : C.textDim }]}>FREE</Text>
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

      {/* CTA buttons */}
      <Pressable
        onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); router.push("/subscription" as any); }}
        style={s.ctaPrimary}
      >
        <Feather name="zap" size={16} color="#3a2404" />
        <Text style={s.ctaPrimaryText}>Upgrade to Pro — ₹499/mo</Text>
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
