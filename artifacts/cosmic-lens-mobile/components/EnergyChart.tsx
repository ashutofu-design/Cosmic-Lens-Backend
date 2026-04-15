import React, { useEffect, useRef, useState } from "react";
import { View, StyleSheet } from "react-native";
import Svg, {
  Path, G, Circle, Text as SvgText, Rect, Line, Defs,
  LinearGradient, Stop,
} from "react-native-svg";
import { gradColor } from "@/lib/todayEnergyCalc";
import { useC } from "@/context/ThemeContext";

const N   = 12;
const VW  = 300;
const VH  = 300;
const PL  = 44;
const PR  = 12;
const PT  = 50;
const GW  = VW - PL - PR;
const GH  = 180;
const BOT = PT + GH;

const px = (i: number) => PL + (i / (N - 1)) * GW;
const py = (v: number) => PT + (1 - v / 100) * GH;

function sharpPath(vals: number[]): string {
  return vals.map((v, i) => `${i === 0 ? "M" : "L"} ${px(i).toFixed(1)},${py(v).toFixed(1)}`).join(" ");
}
function areaFill(vals: number[]): string {
  const line  = sharpPath(vals);
  const last  = px(N - 1).toFixed(1);
  const first = px(0).toFixed(1);
  return `${line} L ${last},${BOT} L ${first},${BOT} Z`;
}

const YGRID = [
  { v: 100, y: PT },
  { v:  75, y: PT + GH * 0.25 },
  { v:  25, y: PT + GH * 0.75 },
  { v:   0, y: BOT },
];

const BAR_MAX = 22;
const RISE_MS = 1200;

interface EnergyChartProps {
  targetPts: number[];
  labels: string[];
  finalEnergy: number | null;
  loading?: boolean;
  instant?: boolean;
}

export default function EnergyChart({ targetPts, labels, finalEnergy, loading, instant }: EnergyChartProps) {
  const C = useC();
  const [animPts, setAnimPts]   = useState<number[]>(instant && targetPts.length > 0 ? [...targetPts] : Array(N).fill(0));
  const [animate, setAnimate]   = useState(instant && targetPts.length > 0);
  const [areaVis, setAreaVis]   = useState(instant && targetPts.length > 0);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    if (targetPts.length === 0) {
      cancelAnimationFrame(rafRef.current);
      setAnimPts(Array(N).fill(0));
      setAnimate(false);
      setAreaVis(false);
      return;
    }

    if (instant) {
      setAnimPts([...targetPts]);
      setAnimate(true);
      setAreaVis(true);
      return;
    }

    cancelAnimationFrame(rafRef.current);
    setAnimPts(Array(N).fill(0));
    setAnimate(false);
    setAreaVis(false);

    let cancelled = false;
    const values = targetPts;

    const tid = setTimeout(() => {
      if (cancelled) return;
      setAnimate(true);
      let startTime = 0;
      const MAX_DELAY = (N - 1) * 0.08;

      function riseFrame(now: number) {
        if (cancelled) return;
        if (!startTime) startTime = now;
        const elapsed = now - startTime;
        const t = elapsed / RISE_MS;

        setAnimPts(values.map((v, i) => {
          const delay    = i * 0.08;
          let progress   = t - delay;
          if (progress < 0) progress = 0;
          if (progress > 1) progress = 1;
          const eased = 1 - Math.pow(1 - progress, 3);
          return v * eased;
        }));

        if (t < 1 + MAX_DELAY) {
          rafRef.current = requestAnimationFrame(riseFrame);
        } else {
          setAnimPts([...values]);
          setTimeout(() => { if (!cancelled) setAreaVis(true); }, 80);
        }
      }
      rafRef.current = requestAnimationFrame(riseFrame);
    }, 50);

    return () => {
      cancelled = true;
      cancelAnimationFrame(rafRef.current);
      clearTimeout(tid);
    };
  }, [targetPts, instant]);

  const linePath = sharpPath(animPts);
  const fillPath = areaFill(animPts);
  const lx       = px(N - 1);
  const ly       = py(animPts[N - 1] ?? 0);
  const finalClr = gradColor(1);

  // Theme-aware colors
  const gridLineStrong = C.isDark ? "#0d1e35" : "rgba(160,120,220,0.18)";
  const gridLineDash   = C.isDark ? "#0a1828" : "rgba(160,120,220,0.10)";
  const axisLabel      = C.isDark ? "#1a3050" : "#9f7aea";
  const headerLabel    = C.isDark ? "#3d5a7a" : "#9f7aea";
  const scoreText      = C.isDark ? "#dde8f4" : "#1e0a3c";
  const scoreSub       = C.isDark ? "#2a3f5a" : "#7c5cbf";
  const footerText     = C.isDark ? "#1a3050" : "#b4a0d8";
  const glowCircle     = C.isDark ? "#0050bb" : "#c4b5fd";
  const calloutFill    = C.isDark ? "#071a0e" : "rgba(255,255,255,0.92)";
  const cardBg         = C.isDark ? "#040e20" : "rgba(255,255,255,0.82)";
  const cardBorder     = C.isDark ? "rgba(0,200,255,0.18)" : "rgba(168,85,247,0.18)";

  return (
    <View style={[styles.card, { backgroundColor: cardBg, borderColor: cardBorder }]}>
      <Svg viewBox={`0 0 ${VW} ${VH}`} width="100%" height="100%" style={{ display: "flex" }}>
        <Defs>
          <LinearGradient id="lg" x1={PL} y1="0" x2={PL + GW} y2="0" gradientUnits="userSpaceOnUse">
            <Stop offset="0%"   stopColor="#ff3b3b" />
            <Stop offset="25%"  stopColor="#ff8c00" />
            <Stop offset="45%"  stopColor="#ffd700" />
            <Stop offset="60%"  stopColor="#f59e0b" />
            <Stop offset="100%" stopColor="#00ff99" />
          </LinearGradient>
          <LinearGradient id="af" x1="0" y1={PT} x2="0" y2={BOT} gradientUnits="userSpaceOnUse">
            <Stop offset="0%"   stopColor="#00a8d4" stopOpacity={areaVis ? 0.18 : 0} />
            <Stop offset="100%" stopColor="#00a8d4" stopOpacity="0" />
          </LinearGradient>
        </Defs>

        {/* Atmospheric glow */}
        <Circle cx={VW / 2} cy={BOT + 30} r={80} fill={glowCircle} opacity={C.isDark ? 0.14 : 0.08} />

        {/* Header */}
        <SvgText x={PL} y={14} fill={headerLabel} fontSize={7} fontWeight="500" letterSpacing={2.2}>
          TODAY'S ENERGY
        </SvgText>

        {/* Score number */}
        <SvgText x={PL} y={40} fill={scoreText} fontSize={28} fontWeight="200" letterSpacing={-1.5}>
          {loading ? "—" : (finalEnergy ?? "—")}
        </SvgText>
        <SvgText x={PL + 41} y={40} fill={scoreSub} fontSize={11} fontWeight="400">
          /100
        </SvgText>

        {/* Horizontal grid lines */}
        {YGRID.map(({ v, y: gy }) => (
          <G key={v}>
            <Line
              x1={PL} y1={gy} x2={PL + GW} y2={gy}
              stroke={v === 0 || v === 100 ? gridLineStrong : gridLineDash}
              strokeWidth={v === 0 || v === 100 ? 1 : 0.8}
              strokeDasharray={v === 0 || v === 100 ? undefined : "4,10"}
            />
            <SvgText x={PL - 7} y={gy + 3.5} textAnchor="end" fill={axisLabel} fontSize={8.5}>
              {v}
            </SvgText>
          </G>
        ))}

        {/* Vertical grid lines */}
        {[1, 2, 3, 4].map(j => (
          <Line
            key={j}
            x1={PL + (j / 5) * GW} y1={PT}
            x2={PL + (j / 5) * GW} y2={BOT}
            stroke={gridLineDash} strokeWidth={0.7} strokeDasharray="4,10"
          />
        ))}

        {/* Area fill */}
        {targetPts.length > 0 && (
          <Path d={fillPath} fill="url(#af)" opacity={areaVis ? 1 : 0} />
        )}

        {/* Bloom layer */}
        {targetPts.length > 0 && (
          <Path d={linePath} fill="none" stroke="url(#lg)" strokeWidth={16} opacity={0.12} strokeLinecap="butt" strokeLinejoin="miter" />
        )}

        {/* Core line */}
        {targetPts.length > 0 && (
          <Path d={linePath} fill="none" stroke="url(#lg)" strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round" />
        )}

        {/* Per-point colored dots */}
        {animPts.map((v, i) => {
          if (i === N - 1) return null;
          const t     = i / (N - 1);
          const color = gradColor(t);
          const x = px(i), y = py(v);
          const r = t >= 0.58 && t <= 0.65 ? 4 : 2.8;
          return (
            <G key={i} opacity={animate ? 1 : 0}>
              <Circle cx={x} cy={y} r={r + 3} fill={color} opacity={0.22} />
              <Circle cx={x} cy={y} r={r}     fill={color} />
            </G>
          );
        })}

        {/* Final point: green dot */}
        {targetPts.length > 0 && animate && (
          <G>
            <Circle cx={lx} cy={ly} r={7}   fill="none" stroke={finalClr} strokeWidth={1.5} opacity={0.45} />
            <Circle cx={lx} cy={ly} r={5}   fill={finalClr} opacity={0.9} />
            <Circle cx={lx} cy={ly} r={2.2} fill="white"    opacity={0.9} />
          </G>
        )}

        {/* Score callout */}
        {targetPts.length > 0 && animate && finalEnergy != null && (
          <G>
            <Rect x={lx - 54} y={ly - 15} width={40} height={22} rx={7}
              fill={calloutFill} stroke={finalClr} strokeOpacity={0.75} strokeWidth={1} />
            <SvgText x={lx - 34} y={ly + 2.5} textAnchor="middle" fill={finalClr} fontSize={12} fontWeight="800">
              {finalEnergy}
            </SvgText>
          </G>
        )}

        {/* Volume bars */}
        {animPts.map((v, i) => {
          const t     = i / (N - 1);
          const color = gradColor(t);
          const barH  = Math.max(4, (v / 100) * BAR_MAX);
          const bx    = px(i) - 3.5;
          const by    = BOT + 8 + (BAR_MAX - barH);
          return (
            <Rect key={i} x={bx} y={by} width={7} height={barH}
              fill={color} opacity={animate ? 0.22 : 0} rx={1.5} />
          );
        })}

        {/* Time labels */}
        {[0, 3, 6, 9, N - 1].map(idx => {
          const lbl = labels[idx];
          if (!lbl) return null;
          const isNow = idx === N - 1;
          return (
            <SvgText key={idx}
              x={px(idx)} y={BOT + BAR_MAX + 20}
              textAnchor="middle"
              fill={isNow ? finalClr : axisLabel}
              fontSize={isNow ? 8.5 : 7.5}
              fontWeight={isNow ? "700" : "400"}
              opacity={animate ? 1 : 0}
            >
              {isNow ? "Now" : lbl}
            </SvgText>
          );
        })}

        {/* Footer */}
        <SvgText x={VW / 2} y={VH - 8} textAnchor="middle" fill={footerText} fontSize={6.5} letterSpacing={2.5}>
          NAVATARA  •  MOON TRANSIT  •  ASHTAKAVARGA
        </SvgText>

        {/* Loading state */}
        {loading && (
          <SvgText x={VW / 2} y={VH / 2} textAnchor="middle" fill={headerLabel} fontSize={11}>
            Reading cosmic signals...
          </SvgText>
        )}
      </Svg>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    width: "100%",
    borderRadius: 20,
    borderWidth: 1,
    overflow: "hidden",
    shadowColor: "#006ec8",
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.25,
    shadowRadius: 30,
    elevation: 8,
  },
});
