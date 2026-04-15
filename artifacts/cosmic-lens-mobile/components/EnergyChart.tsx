import React, { useEffect, useMemo, useRef, useState } from "react";
import { View, StyleSheet } from "react-native";
import Svg, {
  Path, G, Circle, Text as SvgText, Line, Defs,
  LinearGradient, Stop, Rect,
} from "react-native-svg";
import { gradColor } from "@/lib/todayEnergyCalc";
import { useC } from "@/context/ThemeContext";

const N   = 12;
const VW  = 340;
const VH  = 260;
const PL  = 30;
const PR  = 14;
const PT  = 16;
const GW  = VW - PL - PR;
const GH  = 190;
const BOT = PT + GH;

const px = (i: number) => PL + (i / (N - 1)) * GW;
const py = (v: number) => PT + (1 - v / 100) * GH;

function smoothPath(vals: number[]): string {
  if (vals.length < 2) return "";
  let d = `M ${px(0).toFixed(1)},${py(vals[0]).toFixed(1)}`;
  for (let i = 1; i < vals.length; i++) {
    const x0 = px(i - 1), y0 = py(vals[i - 1]);
    const x1 = px(i),     y1 = py(vals[i]);
    const cpx = (x0 + x1) / 2;
    d += ` C ${cpx.toFixed(1)},${y0.toFixed(1)} ${cpx.toFixed(1)},${y1.toFixed(1)} ${x1.toFixed(1)},${y1.toFixed(1)}`;
  }
  return d;
}
function areaFill(vals: number[]): string {
  const line  = smoothPath(vals);
  const last  = px(N - 1).toFixed(1);
  const first = px(0).toFixed(1);
  return `${line} L ${last},${BOT} L ${first},${BOT} Z`;
}

function shapeJourney(rawPts: number[]): number[] {
  if (rawPts.length === 0) return [];
  const final = rawPts[rawPts.length - 1];
  const len = rawPts.length;
  const shaped: number[] = [];

  for (let i = 0; i < len; i++) {
    const t = i / (len - 1);

    const envelope = Math.pow(t, 1.4);

    const rawNorm = rawPts[i] / 100;
    const wiggle = (rawNorm - 0.5) * 0.35;

    const base = final * envelope;
    const startOffset = (1 - t) * 8;
    let val = base + wiggle * final - startOffset;

    val = Math.max(2, Math.min(98, val));

    if (i === len - 1) val = final;

    shaped.push(Math.round(val));
  }

  return shaped;
}

const YGRID = [
  { v: 100, y: PT },
  { v:  75, y: PT + GH * 0.25 },
  { v:  50, y: PT + GH * 0.50 },
  { v:  25, y: PT + GH * 0.75 },
  { v:   0, y: BOT },
];

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

  const journeyPts = useMemo(() => shapeJourney(targetPts), [targetPts]);

  const [animPts, setAnimPts]   = useState<number[]>(instant && journeyPts.length > 0 ? [...journeyPts] : Array(N).fill(0));
  const [animate, setAnimate]   = useState(instant && journeyPts.length > 0);
  const [areaVis, setAreaVis]   = useState(instant && journeyPts.length > 0);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    if (journeyPts.length === 0) {
      cancelAnimationFrame(rafRef.current);
      setAnimPts(Array(N).fill(0));
      setAnimate(false);
      setAreaVis(false);
      return;
    }

    if (instant) {
      setAnimPts([...journeyPts]);
      setAnimate(true);
      setAreaVis(true);
      return;
    }

    cancelAnimationFrame(rafRef.current);
    setAnimPts(Array(N).fill(0));
    setAnimate(false);
    setAreaVis(false);

    let cancelled = false;
    const values = journeyPts;

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
  }, [journeyPts, instant]);

  const linePath = smoothPath(animPts);
  const fillPath = areaFill(animPts);
  const lx       = px(N - 1);
  const ly       = py(animPts[N - 1] ?? 0);
  const finalClr = gradColor(1);

  const gridLine   = C.isDark ? "rgba(255,255,255,0.05)" : "rgba(140,100,200,0.08)";
  const gridStrong = C.isDark ? "rgba(255,255,255,0.07)" : "rgba(140,100,200,0.12)";
  const axisLabel  = C.isDark ? "rgba(255,255,255,0.18)" : "rgba(140,100,200,0.4)";
  const footerText = C.isDark ? "rgba(255,255,255,0.10)" : "rgba(140,100,200,0.35)";
  const calloutBg  = C.isDark ? "rgba(0,20,10,0.85)" : "rgba(255,255,255,0.92)";

  return (
    <View style={styles.card}>
      <Svg viewBox={`0 0 ${VW} ${VH}`} width="100%" height="100%" style={{ display: "flex" }}>
        <Defs>
          <LinearGradient id="lg" x1={PL} y1="0" x2={PL + GW} y2="0" gradientUnits="userSpaceOnUse">
            <Stop offset="0%"   stopColor="#ff3b3b" />
            <Stop offset="20%"  stopColor="#ff8c00" />
            <Stop offset="40%"  stopColor="#ffd700" />
            <Stop offset="60%"  stopColor="#f59e0b" />
            <Stop offset="100%" stopColor="#00ff99" />
          </LinearGradient>
          <LinearGradient id="af" x1="0" y1={PT} x2="0" y2={BOT} gradientUnits="userSpaceOnUse">
            <Stop offset="0%"   stopColor={C.isDark ? "#00ffcc" : "#9f7aea"} stopOpacity={areaVis ? 0.18 : 0} />
            <Stop offset="50%"  stopColor={C.isDark ? "#00ffcc" : "#9f7aea"} stopOpacity={areaVis ? 0.06 : 0} />
            <Stop offset="100%" stopColor={C.isDark ? "#00ffcc" : "#9f7aea"} stopOpacity="0" />
          </LinearGradient>
        </Defs>

        {YGRID.map(({ v, y: gy }) => (
          <G key={v}>
            <Line
              x1={PL} y1={gy} x2={PL + GW} y2={gy}
              stroke={v === 0 || v === 100 ? gridStrong : gridLine}
              strokeWidth={v === 0 || v === 100 ? 0.8 : 0.5}
              strokeDasharray={v === 0 || v === 100 ? undefined : "3,8"}
            />
            <SvgText x={PL - 6} y={gy + 3} textAnchor="end" fill={axisLabel} fontSize={7}>
              {v}
            </SvgText>
          </G>
        ))}

        {journeyPts.length > 0 && (
          <Path d={fillPath} fill="url(#af)" opacity={areaVis ? 1 : 0} />
        )}

        {journeyPts.length > 0 && (
          <Path d={linePath} fill="none" stroke="url(#lg)" strokeWidth={14} opacity={0.06} strokeLinecap="round" strokeLinejoin="round" />
        )}

        {journeyPts.length > 0 && (
          <Path d={linePath} fill="none" stroke="url(#lg)" strokeWidth={2.8} strokeLinecap="round" strokeLinejoin="round" />
        )}

        {animPts.map((v, i) => {
          if (i === N - 1) return null;
          const t     = i / (N - 1);
          const color = gradColor(t);
          const x = px(i), y = py(v);
          return (
            <G key={i} opacity={animate ? 1 : 0}>
              <Circle cx={x} cy={y} r={4} fill={color} opacity={0.10} />
              <Circle cx={x} cy={y} r={2} fill={color} />
            </G>
          );
        })}

        {journeyPts.length > 0 && animate && (
          <G>
            <Circle cx={lx} cy={ly} r={12}  fill={finalClr} opacity={0.07} />
            <Circle cx={lx} cy={ly} r={7}   fill={finalClr} opacity={0.14} />
            <Circle cx={lx} cy={ly} r={4.5} fill={finalClr} opacity={0.9} />
            <Circle cx={lx} cy={ly} r={1.8} fill="white"    opacity={0.95} />
          </G>
        )}

        {journeyPts.length > 0 && animate && finalEnergy != null && (
          <G>
            <Rect x={lx - 52} y={ly - 14} width={38} height={21} rx={7}
              fill={calloutBg} stroke={finalClr} strokeOpacity={0.5} strokeWidth={0.8} />
            <SvgText x={lx - 33} y={ly + 2.5} textAnchor="middle" fill={finalClr} fontSize={11} fontWeight="800">
              {finalEnergy}
            </SvgText>
          </G>
        )}

        {[0, 3, 6, 9, N - 1].map(idx => {
          const lbl = labels[idx];
          if (!lbl) return null;
          const isNow = idx === N - 1;
          return (
            <SvgText key={idx}
              x={px(idx)} y={BOT + 16}
              textAnchor="middle"
              fill={isNow ? finalClr : axisLabel}
              fontSize={isNow ? 8 : 7}
              fontWeight={isNow ? "700" : "400"}
              opacity={animate ? 1 : 0}
            >
              {isNow ? "Now" : lbl}
            </SvgText>
          );
        })}

        <SvgText x={VW / 2} y={VH - 4} textAnchor="middle" fill={footerText} fontSize={5.5} letterSpacing={2.5}>
          NAVATARA  ·  MOON TRANSIT  ·  ASHTAKAVARGA
        </SvgText>

        {loading && (
          <SvgText x={VW / 2} y={VH / 2} textAnchor="middle" fill={axisLabel} fontSize={11}>
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
    overflow: "hidden",
  },
});
