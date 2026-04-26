import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Text, View, StyleSheet } from "react-native";
import { useT } from "@/hooks/useT";
import Animated, {
  Easing,
  runOnJS,
  useAnimatedProps,
  useAnimatedReaction,
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
  const t = useT();
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

  // ── Wandering threat blips ──────────────────────────────────────────────
  // Each slot has a pool of candidate positions. The dot fades in, glows,
  // fades out, then jumps to a different position in its pool — so it never
  // sits in one place. Each slot has its own rhythm so they don't sync.
  const POOL_SIZE = 6;
  const MAX_DOTS  = 3;

  const dotPools = useMemo(() => {
    return Array.from({ length: MAX_DOTS }, (_, slotIdx) => {
      const risk      = risks[slotIdx];
      const baseR     = severityRadius(risk?.level ?? "medium");
      const baseAngle = (slotIdx * 137.5 + 30) % 360;
      return Array.from({ length: POOL_SIZE }, (_, k) => {
        // Spread positions evenly around the circle but anchored at slot's
        // base angle — and add deterministic jitter so they don't look gridded.
        const offset    = (k * 360) / POOL_SIZE;
        const angJitter = ((slotIdx * 7 + k * 13) % 19) - 9;     // ±9°
        const radJitter = ((slotIdx * 11 + k * 17) % 21) - 10;   // ±10px
        const angle     = (baseAngle + offset + angJitter + 360) % 360;
        const radius    = Math.max(28, Math.min(RADAR_R - 18, baseR + radJitter));
        return polar(angle, radius);
      });
    });
  }, [risks]);

  // Per-slot lifecycle phases (0 → 1 cycle: fade in, glow, fade out, gap)
  const phase0 = useSharedValue(0);
  const phase1 = useSharedValue(0);
  const phase2 = useSharedValue(0);

  // Per-slot current position index (advances on each cycle)
  const [posIdx0, setPosIdx0] = useState(0);
  const [posIdx1, setPosIdx1] = useState(2);
  const [posIdx2, setPosIdx2] = useState(4);

  // Per-slot zero-arg JS handlers — never pass setters through runOnJS args
  // (Reanimated argument marshalling is only safe for serializable values).
  const advance0 = useCallback(() => {
    setPosIdx0(prev => (prev + 1 + Math.floor(Math.random() * (POOL_SIZE - 1))) % POOL_SIZE);
  }, []);
  const advance1 = useCallback(() => {
    setPosIdx1(prev => (prev + 1 + Math.floor(Math.random() * (POOL_SIZE - 1))) % POOL_SIZE);
  }, []);
  const advance2 = useCallback(() => {
    setPosIdx2(prev => (prev + 1 + Math.floor(Math.random() * (POOL_SIZE - 1))) % POOL_SIZE);
  }, []);

  useEffect(() => {
    phase0.value = withRepeat(
      withTiming(1, { duration: 4200, easing: Easing.linear }), -1, false,
    );
    phase1.value = withDelay(1400, withRepeat(
      withTiming(1, { duration: 4900, easing: Easing.linear }), -1, false,
    ));
    phase2.value = withDelay(2800, withRepeat(
      withTiming(1, { duration: 5400, easing: Easing.linear }), -1, false,
    ));
  }, [phase0, phase1, phase2]);

  // Detect cycle wrap (high → low) → jump to a new pool position
  useAnimatedReaction(
    () => phase0.value,
    (curr, prev) => {
      if (prev !== null && prev > 0.85 && curr < 0.15) runOnJS(advance0)();
    },
  );
  useAnimatedReaction(
    () => phase1.value,
    (curr, prev) => {
      if (prev !== null && prev > 0.85 && curr < 0.15) runOnJS(advance1)();
    },
  );
  useAnimatedReaction(
    () => phase2.value,
    (curr, prev) => {
      if (prev !== null && prev > 0.85 && curr < 0.15) runOnJS(advance2)();
    },
  );

  // Lifecycle opacity curve:
  //   0.00–0.15 fade in │ 0.15–0.55 visible │ 0.55–0.75 fade out │ 0.75–1.00 invisible
  const lifecycleStyle0 = useAnimatedStyle(() => {
    const p = phase0.value;
    let opacity = 0;
    if (p < 0.15)      opacity = p / 0.15;
    else if (p < 0.55) opacity = 1;
    else if (p < 0.75) opacity = 1 - (p - 0.55) / 0.20;
    return { opacity };
  });
  const lifecycleStyle1 = useAnimatedStyle(() => {
    const p = phase1.value;
    let opacity = 0;
    if (p < 0.15)      opacity = p / 0.15;
    else if (p < 0.55) opacity = 1;
    else if (p < 0.75) opacity = 1 - (p - 0.55) / 0.20;
    return { opacity };
  });
  const lifecycleStyle2 = useAnimatedStyle(() => {
    const p = phase2.value;
    let opacity = 0;
    if (p < 0.15)      opacity = p / 0.15;
    else if (p < 0.55) opacity = 1;
    else if (p < 0.75) opacity = 1 - (p - 0.55) / 0.20;
    return { opacity };
  });

  const slots = [
    { pos: dotPools[0][posIdx0], lifecycle: lifecycleStyle0, present: risks.length >= 1, idx: 1 },
    { pos: dotPools[1][posIdx1], lifecycle: lifecycleStyle1, present: risks.length >= 2, idx: 2 },
    { pos: dotPools[2][posIdx2], lifecycle: lifecycleStyle2, present: risks.length >= 3, idx: 3 },
  ];

  return (
    <View style={radarS.outerWrap}>
      {/* Status bar */}
      <View style={radarS.statusRow}>
        <Animated.View
          style={[radarS.statusDot, statusDotStyle, { backgroundColor: "#ef4444" }]}
        />
        <Text style={radarS.statusTxt}>{t.radarStatusActive}</Text>
        <View style={radarS.statusSpacer} />
        <Text style={radarS.statusMeta}>
          {risks.length} {risks.length === 1 ? t.radarSignalSingular : t.radarSignalPlural}
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

          {/* Sri Yantra Shatkona — faded to a whisper so it doesn't compete with red dots */}
          <Path d={HEX_UP}   stroke="#7f1d1d" strokeWidth={0.5}
            strokeOpacity={0.10} fill="none" />
          <Path d={HEX_DOWN} stroke="#7f1d1d" strokeWidth={0.5}
            strokeOpacity={0.08} fill="none" />

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

          {/* 27 Nakshatra rim markers — faded to dim red dust */}
          {NAKSHATRA_DOTS.map((n, i) => (
            <Circle key={`nak-${i}`}
              cx={n.x} cy={n.y}
              r={n.isMajor ? 1.2 : 0.7}
              fill={n.isMajor ? "#dc2626" : "#7f1d1d"}
              fillOpacity={n.isMajor ? 0.45 : 0.20} />
          ))}

          {/* Compass labels — single accent at North only, dim red */}
          <SvgText x={RADAR_C} y={20} fill="#dc2626"
            fillOpacity={0.55}
            fontSize="11" fontWeight="800" textAnchor="middle">N</SvgText>

          {/* Threat pings — RED, expanding outward */}
          <AnimatedCircle cx={RADAR_C} cy={RADAR_C}
            stroke="#ef4444" fill="none" animatedProps={ping1Props} />
          <AnimatedCircle cx={RADAR_C} cy={RADAR_C}
            stroke="#dc2626" fill="none" animatedProps={ping2Props} />

          {/* Center hub — small dark red core, no ॐ jewel */}
          <Circle cx={RADAR_C} cy={RADAR_C} r={6}
            fill="#7f1d1d" fillOpacity={0.55} />
          <Circle cx={RADAR_C} cy={RADAR_C} r={3}
            fill="#ef4444" />
          <Circle cx={RADAR_C} cy={RADAR_C} r={1.2}
            fill="#fff" />
        </Svg>

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
                <Stop offset="0%"   stopColor="#dc2626" stopOpacity="0.55" />
                <Stop offset="100%" stopColor="#7f1d1d" stopOpacity="0" />
              </RadialGradient>
            </Defs>
            <Path d={SWEEP_PATH} fill="url(#sweep)" />
            {/* Leading edge — RED warning blade */}
            <Line x1={RADAR_C} y1={RADAR_C} x2={RADAR_C} y2={RADAR_C - RADAR_R}
              stroke="#7f1d1d" strokeWidth={6} strokeOpacity={0.30}
              strokeLinecap="round" />
            <Line x1={RADAR_C} y1={RADAR_C} x2={RADAR_C} y2={RADAR_C - RADAR_R}
              stroke="#dc2626" strokeWidth={3} strokeOpacity={0.85}
              strokeLinecap="round" />
            <Line x1={RADAR_C} y1={RADAR_C} x2={RADAR_C} y2={RADAR_C - RADAR_R}
              stroke="#fca5a5" strokeWidth={1} strokeOpacity={0.90}
              strokeLinecap="round" />
            {/* Tip — small red bead, no flare */}
            <Circle cx={RADAR_C} cy={RADAR_C - RADAR_R + 6} r={6}
              fill="#dc2626" fillOpacity={0.35} />
            <Circle cx={RADAR_C} cy={RADAR_C - RADAR_R + 6} r={3}
              fill="#ef4444" />
          </Svg>
        </Animated.View>

        {/* THREAT BLIPS — wandering: appear, glow, fade, jump elsewhere */}
        {slots.map((s, i) => {
          if (!s.present) return null;
          const RED = "#ef4444";
          return (
            <Animated.View
              key={`dot-${i}`}
              pointerEvents="none"
              style={[
                {
                  position: "absolute",
                  left: HALO_PAD + s.pos.x - 28,
                  top:  HALO_PAD + s.pos.y - 28,
                  width: 56, height: 56,
                  alignItems: "center", justifyContent: "center",
                },
                s.lifecycle,
              ]}
            >
              {/* Outer pulsing ripple — wider, blood-red */}
              <Animated.View
                style={[
                  {
                    position: "absolute",
                    width: 56, height: 56, borderRadius: 28,
                    borderWidth: 2, borderColor: RED,
                  },
                  dotPulseStyle,
                ]}
              />
              {/* Mid glow halo — saturated red */}
              <View
                style={{
                  position: "absolute",
                  width: 42, height: 42, borderRadius: 21,
                  backgroundColor: RED, opacity: 0.32,
                }}
              />
              {/* Inner glow */}
              <View
                style={{
                  position: "absolute",
                  width: 30, height: 30, borderRadius: 15,
                  backgroundColor: RED, opacity: 0.55,
                  shadowColor: RED,
                  shadowOpacity: 1,
                  shadowRadius: 14,
                  shadowOffset: { width: 0, height: 0 },
                  elevation: 12,
                }}
              />
              {/* Solid red core blip */}
              <View
                style={{
                  position: "absolute",
                  width: 18, height: 18, borderRadius: 9,
                  backgroundColor: "#dc2626",
                  borderWidth: 1.5, borderColor: "#fef2f2",
                  alignItems: "center", justifyContent: "center",
                  shadowColor: RED,
                  shadowOpacity: 1,
                  shadowRadius: 8,
                  shadowOffset: { width: 0, height: 0 },
                  elevation: 10,
                }}
              >
                <Text style={radarS.dotIdx}>{s.idx}</Text>
              </View>
            </Animated.View>
          );
        })}

        {/* All Clear overlay */}
        {risks.length === 0 && (
          <View style={radarS.emptyOverlay} pointerEvents="none">
            <Text style={radarS.emptyTxt}>{t.radarAllClear}</Text>
            <Text style={radarS.emptySub}>{t.radarAllClearSub}</Text>
          </View>
        )}
      </View>
    </View>
  );
}

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
    shadowColor: "#ef4444",
    shadowOpacity: 1,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 0 },
    elevation: 4,
  },
  statusTxt: {
    color: "#ef4444",
    fontSize: 10,
    fontFamily: F.extra,
    letterSpacing: 2,
  },
  statusSpacer: { flex: 1 },
  statusMeta: {
    color: "rgba(252, 165, 165, 0.75)",
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

