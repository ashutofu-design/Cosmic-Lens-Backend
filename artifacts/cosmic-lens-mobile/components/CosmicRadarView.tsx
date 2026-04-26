import React, { useEffect, useMemo } from "react";
import { Text, View, StyleSheet } from "react-native";
import Animated, {
  Easing,
  useAnimatedProps,
  useAnimatedStyle,
  useSharedValue,
  withDelay,
  withRepeat,
  withTiming,
} from "react-native-reanimated";
import Svg, {
  Circle,
  Defs,
  Line,
  LinearGradient as SvgLinearGradient,
  Path,
  RadialGradient,
  Stop,
  Text as SvgText,
} from "react-native-svg";

const F = {
  regular: "Nunito_400Regular",
  semi:    "Nunito_600SemiBold",
  bold:    "Nunito_700Bold",
  extra:   "Nunito_800ExtraBold",
} as const;

type RiskLevel = "low" | "medium" | "high";

interface Risk24h {
  level:   RiskLevel;
  title:   string;
  reason:  string;
  advice:  string;
  timing?: string;
}

export type { Risk24h, RiskLevel };

function levelColor(l: RiskLevel): string {
  if (l === "high")   return "#ef4444";
  if (l === "medium") return "#f59e0b";
  return "#22c55e";
}

}

// ── Radar geometry helpers ────────────────────────────────────────────────────
const RADAR_SIZE = 280;
const RADAR_R    = RADAR_SIZE / 2 - 6;
const RADAR_C    = RADAR_SIZE / 2;

function polar(angleDeg: number, radius: number) {
  const rad = (angleDeg - 90) * Math.PI / 180;
  return {
    x: RADAR_C + Math.cos(rad) * radius,
    y: RADAR_C + Math.sin(rad) * radius,
  };
}

function severityRadius(level: RiskLevel): number {
  if (level === "high")   return RADAR_R * 0.35;
  if (level === "medium") return RADAR_R * 0.62;
  return RADAR_R * 0.85;
}

function buildWedgePath(startAngle: number, endAngle: number): string {
  const start = polar(startAngle, RADAR_R);
  const end   = polar(endAngle,   RADAR_R);
  const largeArc = endAngle - startAngle > 180 ? 1 : 0;
  return `M ${RADAR_C} ${RADAR_C} L ${start.x} ${start.y} A ${RADAR_R} ${RADAR_R} 0 ${largeArc} 1 ${end.x} ${end.y} Z`;
}

const SWEEP_PATH = buildWedgePath(-70, 0); // 70° trailing wedge — wider, more dramatic

// Halo padding around the radar so the outer glow can bleed
const HALO_PAD  = 22;
const WRAP_SIZE = RADAR_SIZE + HALO_PAD * 2;

// Pre-computed background "stars" inside the radar (stable, deterministic)
const BG_STARS = Array.from({ length: 32 }, (_, i) => {
  const angle  = (i * 53.7) % 360;
  const radius = ((i * 17 + 11) % (RADAR_R - 24)) + 14;
  const p      = polar(angle, radius);
  return {
    x: p.x,
    y: p.y,
    r: 0.5 + ((i * 3) % 4) * 0.3,
    op: 0.25 + ((i * 11) % 6) / 14,
  };
});

// 6 of those stars get a twinkle phase offset (animated)
const TWINKLE_INDICES = new Set(
  Array.from({ length: 6 }, (_, i) => (i * 5 + 1) % 32),
);
const TWINKLE_STARS = Array.from({ length: 6 }, (_, i) => {
  const baseIdx = i * 5 + 1;
  const star    = BG_STARS[baseIdx % BG_STARS.length];
  return {
    x:     star.x,
    y:     star.y,
    r:     star.r + 0.4,
    phase: i / 6, // 0..1 stagger
  };
});

// Tick marks around the outer ring (every 15°, longer at cardinals)
const TICKS = Array.from({ length: 24 }, (_, i) => {
  const angle      = i * 15;
  const isCardinal = i % 6 === 0;
  const innerR     = RADAR_R - (isCardinal ? 14 : 7);
  const outerR     = RADAR_R - 2;
  const p1         = polar(angle, innerR);
  const p2         = polar(angle, outerR);
  return { x1: p1.x, y1: p1.y, x2: p2.x, y2: p2.y, isCardinal };
});

// 12 Vedic house markers in Devanagari numerals (replaces "tactical" degree labels)
const DEVANAGARI_NUMS = ["१","२","३","४","५","६","७","८","९","१०","११","१२"];
const HOUSE_GLYPHS = DEVANAGARI_NUMS.map((sym, i) => {
  const angle = i * 30;
  const r     = RADAR_R - 16;
  const p     = polar(angle, r);
  return { x: p.x, y: p.y + 4, label: sym };
});

// 27 Nakshatra micro-dots on outer rim (every 9th = navatara group head, slightly larger)
const NAKSHATRA_DOTS = Array.from({ length: 27 }, (_, i) => {
  const angle = (i * 360) / 27;
  const p     = polar(angle, RADAR_R + 1);
  return { x: p.x, y: p.y, isMajor: i % 9 === 0 };
});

// Sri Yantra style hexagram — two interlocking triangles (Shatkona), faint, behind everything
const HEXAGRAM_R = RADAR_R * 0.62;
function _triPath(offset: number) {
  const pts = [0, 120, 240].map(a => polar(a + offset, HEXAGRAM_R));
  return `M ${pts[0].x} ${pts[0].y} L ${pts[1].x} ${pts[1].y} L ${pts[2].x} ${pts[2].y} Z`;
}
const HEX_UP   = _triPath(0);   // ▲ apex top
const HEX_DOWN = _triPath(60);  // ▼ apex bottom

// Inner sacred geometry — a smaller hexagram for layered depth
const HEXAGRAM_R_INNER = RADAR_R * 0.28;
function _triPathInner(offset: number) {
  const pts = [0, 120, 240].map(a => polar(a + offset, HEXAGRAM_R_INNER));
  return `M ${pts[0].x} ${pts[0].y} L ${pts[1].x} ${pts[1].y} L ${pts[2].x} ${pts[2].y} Z`;
}
const HEX_UP_INNER   = _triPathInner(0);
const HEX_DOWN_INNER = _triPathInner(60);

// 8-point starburst polygon (used for risk dots — gemstone facet effect)
function starPath(cx: number, cy: number, outerR: number, innerR: number, points: number = 8) {
  const segs: string[] = [];
  for (let i = 0; i < points * 2; i++) {
    const r = i % 2 === 0 ? outerR : innerR;
    const a = (i * 180 / points - 90) * Math.PI / 180;
    const x = cx + Math.cos(a) * r;
    const y = cy + Math.sin(a) * r;
    segs.push(`${i === 0 ? "M" : "L"} ${x.toFixed(2)} ${y.toFixed(2)}`);
  }
  return segs.join(" ") + " Z";
}

// Pre-computed starburst path centered at (14, 14) for a 28×28 dot canvas
const RISK_STAR_PATH = starPath(14, 14, 13, 5, 8);

// 8-spoke lens-flare ray endpoints (relative to the sweep tip)
const FLARE_SPOKES = Array.from({ length: 8 }, (_, i) => {
  const a   = (i * 45) * Math.PI / 180;
  const len = i % 2 === 0 ? 14 : 8;
  return {
    dx: Math.cos(a) * len,
    dy: Math.sin(a) * len,
  };
});

// Orbital particles outside the bezel (different radii + speeds)
const ORBITS = [
  { radius: RADAR_R + 14, duration: 9000,  size: 3,   color: "#FFD700" },
  { radius: RADAR_R + 18, duration: 13000, size: 2.5, color: "#a78bfa" },
  { radius: RADAR_R + 12, duration: 7000,  size: 2,   color: "#67e8f9" },
  { radius: RADAR_R + 22, duration: 16000, size: 2.5, color: "#ff9933" },
];

const AnimatedCircle = Animated.createAnimatedComponent(Circle);

export function CosmicRadarView({ risks }: { risks: Risk24h[] }) {
  const sweep    = useSharedValue(0);
  const halo     = useSharedValue(0);
  const dotPulse = useSharedValue(0);
  const ping1    = useSharedValue(0);
  const ping2    = useSharedValue(0);
  const twinkle  = useSharedValue(0);
  const orbit0   = useSharedValue(0);
  const orbit1   = useSharedValue(0);
  const orbit2   = useSharedValue(0);
  const orbit3   = useSharedValue(0);
  const shimmer  = useSharedValue(0);

  useEffect(() => {
    sweep.value = withRepeat(
      withTiming(360, { duration: 5000, easing: Easing.linear }),
      -1,
      false,
    );
    halo.value = withRepeat(
      withTiming(1, { duration: 2800, easing: Easing.inOut(Easing.ease) }),
      -1,
      true,
    );
    dotPulse.value = withRepeat(
      withTiming(1, { duration: 1400, easing: Easing.inOut(Easing.ease) }),
      -1,
      true,
    );
    ping1.value = withRepeat(
      withTiming(1, { duration: 3500, easing: Easing.out(Easing.cubic) }),
      -1,
      false,
    );
    ping2.value = withDelay(
      1750,
      withRepeat(
        withTiming(1, { duration: 3500, easing: Easing.out(Easing.cubic) }),
        -1,
        false,
      ),
    );
    twinkle.value = withRepeat(
      withTiming(1, { duration: 2200, easing: Easing.linear }),
      -1,
      false,
    );
    shimmer.value = withRepeat(
      withTiming(360, { duration: 22000, easing: Easing.linear }),
      -1,
      false,
    );
    // Orbital particles — each independently rotating
    orbit0.value = withRepeat(
      withTiming(360, { duration: ORBITS[0].duration, easing: Easing.linear }),
      -1,
      false,
    );
    orbit1.value = withDelay(800, withRepeat(
      withTiming(-360, { duration: ORBITS[1].duration, easing: Easing.linear }),
      -1,
      false,
    ));
    orbit2.value = withDelay(1600, withRepeat(
      withTiming(360, { duration: ORBITS[2].duration, easing: Easing.linear }),
      -1,
      false,
    ));
    orbit3.value = withDelay(400, withRepeat(
      withTiming(-360, { duration: ORBITS[3].duration, easing: Easing.linear }),
      -1,
      false,
    ));
  }, [sweep, halo, dotPulse, ping1, ping2, twinkle, shimmer, orbit0, orbit1, orbit2, orbit3]);

  const sweepStyle = useAnimatedStyle(() => ({
    transform: [{ rotate: `${sweep.value}deg` }],
  }));

  const haloStyle = useAnimatedStyle(() => ({
    opacity: 0.30 + halo.value * 0.40,
    transform: [{ scale: 0.96 + halo.value * 0.06 }],
  }));

  const haloInnerStyle = useAnimatedStyle(() => ({
    opacity: 0.5 + (1 - halo.value) * 0.4,
  }));

  const dotPulseStyle = useAnimatedStyle(() => ({
    opacity: 0.20 + dotPulse.value * 0.55,
    transform: [{ scale: 0.8 + dotPulse.value * 0.55 }],
  }));

  const statusDotStyle = useAnimatedStyle(() => ({
    opacity: 0.5 + dotPulse.value * 0.5,
  }));

  const ping1Props = useAnimatedProps(() => ({
    r: 6 + ping1.value * (RADAR_R - 8),
    opacity: 0.55 * (1 - ping1.value),
    strokeWidth: 1.5 - ping1.value * 0.8,
  }));
  const ping2Props = useAnimatedProps(() => ({
    r: 6 + ping2.value * (RADAR_R - 8),
    opacity: 0.45 * (1 - ping2.value),
    strokeWidth: 1.5 - ping2.value * 0.8,
  }));

  // Holographic bezel rotates very slowly
  const shimmerStyle = useAnimatedStyle(() => ({
    transform: [{ rotate: `${shimmer.value}deg` }],
  }));

  // Orbital particle transforms (full-radar-sized rotating wrappers)
  const orbit0Style = useAnimatedStyle(() => ({
    transform: [{ rotate: `${orbit0.value}deg` }],
  }));
  const orbit1Style = useAnimatedStyle(() => ({
    transform: [{ rotate: `${orbit1.value}deg` }],
  }));
  const orbit2Style = useAnimatedStyle(() => ({
    transform: [{ rotate: `${orbit2.value}deg` }],
  }));
  const orbit3Style = useAnimatedStyle(() => ({
    transform: [{ rotate: `${orbit3.value}deg` }],
  }));
  const orbitStyles = [orbit0Style, orbit1Style, orbit2Style, orbit3Style];

  // Twinkle stars — each star phases through opacity
  const twinkleProps0 = useAnimatedProps(() => {
    const t = (twinkle.value + TWINKLE_STARS[0].phase) % 1;
    return { opacity: 0.2 + Math.abs(0.5 - t) * 1.6 };
  });
  const twinkleProps1 = useAnimatedProps(() => {
    const t = (twinkle.value + TWINKLE_STARS[1].phase) % 1;
    return { opacity: 0.2 + Math.abs(0.5 - t) * 1.6 };
  });
  const twinkleProps2 = useAnimatedProps(() => {
    const t = (twinkle.value + TWINKLE_STARS[2].phase) % 1;
    return { opacity: 0.2 + Math.abs(0.5 - t) * 1.6 };
  });
  const twinkleProps3 = useAnimatedProps(() => {
    const t = (twinkle.value + TWINKLE_STARS[3].phase) % 1;
    return { opacity: 0.2 + Math.abs(0.5 - t) * 1.6 };
  });
  const twinkleProps4 = useAnimatedProps(() => {
    const t = (twinkle.value + TWINKLE_STARS[4].phase) % 1;
    return { opacity: 0.2 + Math.abs(0.5 - t) * 1.6 };
  });
  const twinkleProps5 = useAnimatedProps(() => {
    const t = (twinkle.value + TWINKLE_STARS[5].phase) % 1;
    return { opacity: 0.2 + Math.abs(0.5 - t) * 1.6 };
  });
  const twinkleAll = [
    twinkleProps0, twinkleProps1, twinkleProps2,
    twinkleProps3, twinkleProps4, twinkleProps5,
  ];

  // Stable angles per risk: golden angle so they spread nicely
  const dots = useMemo(() => {
    return risks.map((r, i) => {
      const angle  = (i * 137.5 + 30) % 360;
      const radius = severityRadius(r.level);
      const p      = polar(angle, radius);
      return {
        ...p,
        color: levelColor(r.level),
        level: r.level,
        idx:   i + 1,
      };
    });
  }, [risks]);

  return (
    <View style={radarS.outerWrap}>
      {/* Status bar */}
      <View style={radarS.statusRow}>
        <Animated.View
          style={[radarS.statusDot, statusDotStyle, { backgroundColor: "#22d3ee" }]}
        />
        <Text style={radarS.statusTxt}>SCANNING • LIVE</Text>
        <View style={radarS.statusSpacer} />
        <Text style={radarS.statusMeta}>
          {risks.length} {risks.length === 1 ? "SIGNAL" : "SIGNALS"}
        </Text>
      </View>

      <View style={radarS.wrap}>
        {/* Outer pulsing halo */}
        <Animated.View style={[radarS.haloOuter, haloStyle]} />
        <Animated.View style={[radarS.haloInner, haloInnerStyle]} />

        {/* Static base layer */}
        <Svg
          width={RADAR_SIZE}
          height={RADAR_SIZE}
          style={{ position: "absolute", left: HALO_PAD, top: HALO_PAD }}
        >
          <Defs>
            <RadialGradient id="bg" cx="50%" cy="50%" r="50%">
              <Stop offset="0%"   stopColor="#1f2a55" stopOpacity="1" />
              <Stop offset="55%"  stopColor="#0a1430" stopOpacity="1" />
              <Stop offset="100%" stopColor="#02060f" stopOpacity="1" />
            </RadialGradient>
            <RadialGradient id="centerGlow" cx="50%" cy="50%" r="50%">
              <Stop offset="0%"   stopColor="#a5f3fc" stopOpacity="0.6" />
              <Stop offset="100%" stopColor="#22d3ee" stopOpacity="0" />
            </RadialGradient>
          </Defs>

          {/* Background disc */}
          <Circle cx={RADAR_C} cy={RADAR_C} r={RADAR_R + 4} fill="url(#bg)" />
          {/* Soft center glow (radial) */}
          <Circle cx={RADAR_C} cy={RADAR_C} r={RADAR_R * 0.45}
            fill="url(#centerGlow)" />

          {/* Tick marks */}
          {TICKS.map((t, i) => (
            <Line key={`tick-${i}`}
              x1={t.x1} y1={t.y1} x2={t.x2} y2={t.y2}
              stroke="#67e8f9"
              strokeWidth={t.isCardinal ? 1.8 : 1}
              strokeOpacity={t.isCardinal ? 0.85 : 0.38} />
          ))}

          {/* Cosmic background stars (excluding twinkle positions) */}
          {BG_STARS.map((s, i) => {
            if (TWINKLE_INDICES.has(i)) return null;
            return (
              <Circle key={`star-${i}`}
                cx={s.x} cy={s.y} r={s.r}
                fill="#fff" fillOpacity={s.op} />
            );
          })}

          {/* Twinkling stars (animated) */}
          {TWINKLE_STARS.map((s, i) => (
            <AnimatedCircle key={`tw-${i}`}
              cx={s.x} cy={s.y} r={s.r}
              fill="#a5f3fc"
              animatedProps={twinkleAll[i]} />
          ))}

          {/* Concentric rings (severity zones) */}
          {[0.85, 0.62, 0.4].map((p, i) => (
            <Circle key={`ring-${i}`}
              cx={RADAR_C} cy={RADAR_C} r={RADAR_R * p}
              stroke="rgba(34,211,238,0.25)" strokeWidth={1} fill="none"
              strokeDasharray={i === 1 ? "3 5" : undefined} />
          ))}

          {/* Sri Yantra Shatkona (sacred hexagram, faint, behind everything) */}
          <Path d={HEX_UP}   stroke="#FFD700" strokeWidth={0.7}
            strokeOpacity={0.32} fill="none" />
          <Path d={HEX_DOWN} stroke="#a78bfa" strokeWidth={0.7}
            strokeOpacity={0.30} fill="none" />
          <Path d={HEX_UP_INNER}   stroke="#FFD700" strokeWidth={0.6}
            strokeOpacity={0.40} fill="none" />
          <Path d={HEX_DOWN_INNER} stroke="#67e8f9" strokeWidth={0.6}
            strokeOpacity={0.40} fill="none" />

          {/* Spokes — 4 cardinal + 4 diagonal */}
          {[0, 45, 90, 135].map((angle, i) => {
            const p1 = polar(angle, RADAR_R - 4);
            const p2 = polar(angle + 180, RADAR_R - 4);
            const isCardinal = angle % 90 === 0;
            return (
              <Line key={`spoke-${i}`}
                x1={p1.x} y1={p1.y} x2={p2.x} y2={p2.y}
                stroke="#22d3ee"
                strokeWidth={isCardinal ? 1 : 0.6}
                strokeOpacity={isCardinal ? 0.20 : 0.12} />
            );
          })}

          {/* 27 Nakshatra micro-markers on outer rim (every 9th highlighted = navatara) */}
          {NAKSHATRA_DOTS.map((n, i) => (
            <Circle key={`nak-${i}`}
              cx={n.x} cy={n.y}
              r={n.isMajor ? 1.6 : 0.9}
              fill={n.isMajor ? "#FFD700" : "#67e8f9"}
              fillOpacity={n.isMajor ? 0.95 : 0.55} />
          ))}

          {/* 12 Vedic house markers in Devanagari (gold) */}
          {HOUSE_GLYPHS.map((g, i) => (
            <SvgText key={`house-${i}`}
              x={g.x} y={g.y}
              fill="#FFD700"
              fillOpacity={0.78}
              fontSize="9"
              fontWeight="700"
              fontFamily="System"
              textAnchor="middle">{g.label}</SvgText>
          ))}

          {/* Compass labels (gold accent) */}
          <SvgText x={RADAR_C} y={20} fill="#FFD700"
            fontSize="12" fontWeight="800" textAnchor="middle">N</SvgText>
          <SvgText x={RADAR_SIZE - 8} y={RADAR_C + 4} fill="#FFD700"
            fontSize="12" fontWeight="800" textAnchor="end">E</SvgText>
          <SvgText x={RADAR_C} y={RADAR_SIZE - 8} fill="#FFD700"
            fontSize="12" fontWeight="800" textAnchor="middle">S</SvgText>
          <SvgText x={8} y={RADAR_C + 4} fill="#FFD700"
            fontSize="12" fontWeight="800" textAnchor="start">W</SvgText>

          {/* Sonar pings */}
          <AnimatedCircle cx={RADAR_C} cy={RADAR_C}
            stroke="#22d3ee" fill="none" animatedProps={ping1Props} />
          <AnimatedCircle cx={RADAR_C} cy={RADAR_C}
            stroke="#67e8f9" fill="none" animatedProps={ping2Props} />

          {/* Premium center — ॐ on a jewel hub */}
          <Circle cx={RADAR_C} cy={RADAR_C} r={14}
            fill="#FFD700" fillOpacity={0.10} />
          <Circle cx={RADAR_C} cy={RADAR_C} r={10}
            fill="#FFD700" fillOpacity={0.22} />
          <Circle cx={RADAR_C} cy={RADAR_C} r={7}
            fill="#1f2a55" stroke="#FFD700" strokeWidth={1} strokeOpacity={0.85} />
          <SvgText x={RADAR_C} y={RADAR_C + 4}
            fill="#FFD700" fillOpacity={0.95}
            fontSize="11" fontWeight="800"
            fontFamily="System"
            textAnchor="middle">ॐ</SvgText>
        </Svg>

        {/* Holographic shimmer bezel (slowly rotating) */}
        <Animated.View
          style={[
            {
              position: "absolute",
              left:   HALO_PAD,
              top:    HALO_PAD,
              width:  RADAR_SIZE,
              height: RADAR_SIZE,
            },
            shimmerStyle,
          ]}
          pointerEvents="none"
        >
          <Svg width={RADAR_SIZE} height={RADAR_SIZE}>
            <Defs>
              <SvgLinearGradient id="bezelGrad" x1="0" y1="0" x2="1" y2="1">
                <Stop offset="0%"   stopColor="#FFD700" stopOpacity="0.95" />
                <Stop offset="25%"  stopColor="#22d3ee" stopOpacity="0.95" />
                <Stop offset="50%"  stopColor="#a78bfa" stopOpacity="0.85" />
                <Stop offset="75%"  stopColor="#67e8f9" stopOpacity="0.95" />
                <Stop offset="100%" stopColor="#ff9933" stopOpacity="0.7" />
              </SvgLinearGradient>
            </Defs>
            {/* Gold filigree outer ring (dashed) */}
            <Circle cx={RADAR_C} cy={RADAR_C} r={RADAR_R + 8}
              stroke="#FFD700" strokeWidth={1} fill="none"
              strokeOpacity={0.55} strokeDasharray="2 4" />
            {/* Outer holographic bezel (gold → cyan → violet → saffron) */}
            <Circle cx={RADAR_C} cy={RADAR_C} r={RADAR_R + 4}
              stroke="url(#bezelGrad)" strokeWidth={2.5} fill="none" />
            {/* Inner soft accent ring */}
            <Circle cx={RADAR_C} cy={RADAR_C} r={RADAR_R}
              stroke="url(#bezelGrad)" strokeWidth={1} fill="none" strokeOpacity={0.55} />
          </Svg>
        </Animated.View>

        {/* Animated sweep beam (rotating wedge) */}
        <Animated.View
          style={[
            {
              position: "absolute",
              left:   HALO_PAD,
              top:    HALO_PAD,
              width:  RADAR_SIZE,
              height: RADAR_SIZE,
            },
            sweepStyle,
          ]}
          pointerEvents="none"
        >
          <Svg width={RADAR_SIZE} height={RADAR_SIZE}>
            <Defs>
              <RadialGradient id="sweep" cx="50%" cy="50%" r="50%">
                <Stop offset="0%"   stopColor="#22d3ee" stopOpacity="0.7" />
                <Stop offset="100%" stopColor="#22d3ee" stopOpacity="0" />
              </RadialGradient>
            </Defs>
            <Path d={SWEEP_PATH} fill="url(#sweep)" />
            {/* Leading edge — 4-line glow stack */}
            <Line x1={RADAR_C} y1={RADAR_C} x2={RADAR_C} y2={RADAR_C - RADAR_R}
              stroke="#22d3ee" strokeWidth={6} strokeOpacity={0.22}
              strokeLinecap="round" />
            <Line x1={RADAR_C} y1={RADAR_C} x2={RADAR_C} y2={RADAR_C - RADAR_R}
              stroke="#67e8f9" strokeWidth={4} strokeOpacity={0.50}
              strokeLinecap="round" />
            <Line x1={RADAR_C} y1={RADAR_C} x2={RADAR_C} y2={RADAR_C - RADAR_R}
              stroke="#a5f3fc" strokeWidth={2} strokeOpacity={0.95}
              strokeLinecap="round" />
            <Line x1={RADAR_C} y1={RADAR_C} x2={RADAR_C} y2={RADAR_C - RADAR_R}
              stroke="#fff" strokeWidth={0.8} strokeOpacity={0.85}
              strokeLinecap="round" />
            {/* Tip glow stack */}
            <Circle cx={RADAR_C} cy={RADAR_C - RADAR_R + 6} r={10}
              fill="#FFD700" fillOpacity={0.18} />
            <Circle cx={RADAR_C} cy={RADAR_C - RADAR_R + 6} r={8}
              fill="#22d3ee" fillOpacity={0.30} />
            <Circle cx={RADAR_C} cy={RADAR_C - RADAR_R + 6} r={5}
              fill="#a5f3fc" fillOpacity={0.90} />
            <Circle cx={RADAR_C} cy={RADAR_C - RADAR_R + 6} r={2.5}
              fill="#fff" />
            {/* 8-spoke lens flare on the tip — alternating long/short rays */}
            {FLARE_SPOKES.map((s, i) => {
              const tipY = RADAR_C - RADAR_R + 6;
              return (
                <Line key={`flare-${i}`}
                  x1={RADAR_C} y1={tipY}
                  x2={RADAR_C + s.dx} y2={tipY + s.dy}
                  stroke={i % 2 === 0 ? "#FFD700" : "#a5f3fc"}
                  strokeWidth={i % 2 === 0 ? 1 : 0.7}
                  strokeOpacity={i % 2 === 0 ? 0.85 : 0.65}
                  strokeLinecap="round" />
              );
            })}
          </Svg>
        </Animated.View>

        {/* Orbital particles (outside bezel) */}
        {ORBITS.map((orb, i) => {
          const startPos = polar(0, orb.radius); // top of radar
          return (
            <Animated.View
              key={`orbit-${i}`}
              pointerEvents="none"
              style={[
                {
                  position: "absolute",
                  left:   HALO_PAD,
                  top:    HALO_PAD,
                  width:  RADAR_SIZE,
                  height: RADAR_SIZE,
                },
                orbitStyles[i],
              ]}
            >
              <View
                style={{
                  position: "absolute",
                  left: startPos.x - orb.size,
                  top:  startPos.y - orb.size,
                  width:  orb.size * 2,
                  height: orb.size * 2,
                  borderRadius: orb.size,
                  backgroundColor: orb.color,
                  shadowColor: orb.color,
                  shadowOpacity: 0.7,
                  shadowRadius: 4,
                  shadowOffset: { width: 0, height: 0 },
                  elevation: 3,
                }}
              />
            </Animated.View>
          );
        })}

        {/* Risk dots (with ripple halos) */}
        {dots.map((d, i) => (
          <View
            key={`dot-${i}`}
            pointerEvents="none"
            style={{
              position: "absolute",
              left: HALO_PAD + d.x - 20,
              top:  HALO_PAD + d.y - 20,
              width: 40, height: 40,
              alignItems: "center", justifyContent: "center",
            }}
          >
            {/* Outer ripple ring */}
            <Animated.View
              style={[
                {
                  position: "absolute",
                  width: 40, height: 40, borderRadius: 20,
                  borderWidth: 1.5, borderColor: d.color,
                },
                dotPulseStyle,
              ]}
            />
            {/* Soft outer halo */}
            <View
              style={{
                position: "absolute",
                width: 32, height: 32, borderRadius: 16,
                backgroundColor: d.color, opacity: 0.22,
              }}
            />
            {/* Starburst gemstone (8-point) with golden rim */}
            <Svg width={28} height={28} style={{ position: "absolute" }}>
              <Defs>
                <RadialGradient id={`dotGrad-${i}`} cx="50%" cy="50%" r="50%">
                  <Stop offset="0%"  stopColor="#fff"   stopOpacity="1" />
                  <Stop offset="45%" stopColor={d.color} stopOpacity="1" />
                  <Stop offset="100%" stopColor={d.color} stopOpacity="0.65" />
                </RadialGradient>
              </Defs>
              <Path d={RISK_STAR_PATH}
                fill={`url(#dotGrad-${i})`}
                stroke="#FFD700" strokeWidth={1} strokeOpacity={0.9} />
            </Svg>
            {/* Number badge (white, on top of gemstone) */}
            <View
              style={{
                width: 14, height: 14, borderRadius: 7,
                backgroundColor: "rgba(15, 23, 42, 0.85)",
                borderWidth: 1, borderColor: "#FFD700",
                alignItems: "center", justifyContent: "center",
                shadowColor: d.color,
                shadowOpacity: 0.9,
                shadowRadius: 5,
                shadowOffset: { width: 0, height: 0 },
                elevation: 4,
              }}
            >
              <Text style={radarS.dotIdx}>{d.idx}</Text>
            </View>
          </View>
        ))}

        {/* All Clear overlay */}
        {risks.length === 0 && (
          <View style={radarS.emptyOverlay} pointerEvents="none">
            <Text style={radarS.emptyTxt}>ALL CLEAR</Text>
            <Text style={radarS.emptySub}>Aaj koi major signal nahi</Text>
          </View>
        )}
      </View>
    </View>
  );

const radarS = StyleSheet.create({
  outerWrap: {
    alignSelf: "center",
    alignItems: "center",
    marginTop: 4,
    marginBottom: 12,
  },

  statusRow: {
    flexDirection: "row",
    alignItems: "center",
    width: WRAP_SIZE - 16,
    paddingHorizontal: 4,
    marginBottom: 6,
    gap: 8,
  },
  statusDot: {
    width: 8, height: 8, borderRadius: 4,
    shadowColor: "#22d3ee",
    shadowOpacity: 1,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 0 },
    elevation: 4,
  },
  statusTxt: {
    color: "#67e8f9",
    fontSize: 10,
    fontFamily: F.extra,
    letterSpacing: 2,
  },
  statusSpacer: { flex: 1 },
  statusMeta: {
    color: "rgba(167, 243, 252, 0.7)",
    fontSize: 10,
    fontFamily: F.bold,
    letterSpacing: 1.5,
  },

  wrap: {
    width:  WRAP_SIZE,
    height: WRAP_SIZE,
    alignItems: "center",
    justifyContent: "center",
  },

  // Outer pulsing halo (soft ring outside the bezel)
  haloOuter: {
    position: "absolute",
    width: WRAP_SIZE - 4,
    height: WRAP_SIZE - 4,
    borderRadius: (WRAP_SIZE - 4) / 2,
    borderWidth: 16,
    borderColor: "rgba(34, 211, 238, 0.18)",
  },
  // Inner sharper halo glow against the bezel
  haloInner: {
    position: "absolute",
    width: RADAR_SIZE + 14,
    height: RADAR_SIZE + 14,
    borderRadius: (RADAR_SIZE + 14) / 2,
    borderWidth: 2,
    borderColor: "rgba(103, 232, 249, 0.45)",
  },

  dotIdx: {
    color: "#fff",
    fontSize: 10,
    fontFamily: F.extra,
    lineHeight: 12,
  },

  emptyOverlay: {
    ...StyleSheet.absoluteFillObject,
    alignItems: "center",
    justifyContent: "center",
  },
  emptyTxt: {
    color: "#22c55e",
    fontFamily: F.extra,
    fontSize: 22,
    letterSpacing: 3,
    textShadowColor: "rgba(34, 197, 94, 0.55)",
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 12,
  },
  emptySub: {
    color: "rgba(255,255,255,0.65)",
    fontFamily: F.semi,
    fontSize: 11,
    marginTop: 4,
    letterSpacing: 0.5,
  },
});

