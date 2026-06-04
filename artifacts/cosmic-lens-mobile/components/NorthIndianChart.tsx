import React, { useMemo } from "react";
import { StyleSheet, Text, useWindowDimensions, View } from "react-native";
import Svg, { G, Line, Rect, Text as SvgText } from "react-native-svg";

import { useC } from "@/context/ThemeContext";
import {
  degreeInSign,
  PLANET_CLR,
  signStatusFromSign,
  SIGNS_SHORT,
  type PlanetCardData,
} from "@/lib/planetPositionUtils";

const VB = 400;
const CX = 200;
const CY = 200;

const PLANET_SHORT: Record<string, string> = {
  Sun: "Su", Moon: "Mo", Mars: "Ma", Mercury: "Me",
  Jupiter: "Ju", Venus: "Ve", Saturn: "Sa", Rahu: "Ra", Ketu: "Ke",
};

const signNum = (idx: number) => ((idx % 12) + 12) % 12 + 1;

const HOUSE_CENTERS: Record<number, { x: number; y: number }> = {
  1:  { x: 200, y: 100 },
  2:  { x: 100, y: 50 },
  3:  { x: 50, y: 100 },
  4:  { x: 100, y: 200 },
  5:  { x: 50, y: 300 },
  6:  { x: 100, y: 350 },
  7:  { x: 200, y: 300 },
  8:  { x: 300, y: 350 },
  9:  { x: 350, y: 300 },
  10: { x: 300, y: 200 },
  11: { x: 350, y: 100 },
  12: { x: 300, y: 50 },
};

export type NorthIndianChartProps = {
  title: string;
  subtitle?: string;
  lagnaSignIndex: number;
  ascendantDeg?: number;
  planets: Pick<PlanetCardData, "name" | "house" | "retrograde" | "longitude">[];
  /** `full` = chart page (larger type, more padding). */
  variant?: "default" | "full";
  showHeader?: boolean;
};

type ChartTheme = {
  bg: string;
  stroke: string;
  signNum: string;
  muted: string;
  accent: string;
  wrapBg: string;
  wrapBorder: string;
  title: string;
  sub: string;
};

function chartTheme(isDark: boolean): ChartTheme {
  if (isDark) {
    return {
      bg: "#1a1510",
      stroke: "#e8a735",
      signNum: "#fde68a",
      muted: "#78716c",
      accent: "#fbbf24",
      wrapBg: "#12100e",
      wrapBorder: "rgba(232,167,53,0.35)",
      title: "#fcd34d",
      sub: "#a8a29e",
    };
  }
  return {
    bg: "#fffdf8",
    stroke: "#c2410c",
    signNum: "#92400e",
    muted: "#78716c",
    accent: "#d97706",
    wrapBg: "#fffefb",
    wrapBorder: "rgba(217,119,6,0.3)",
    title: "#c2410c",
    sub: "#78716c",
  };
}

function ChartGeometry({ T }: { T: ChartTheme }) {
  const sw = 2.2;
  return (
    <G>
      <Rect x={0} y={0} width={VB} height={VB} fill={T.bg} />
      <Rect x={0} y={0} width={VB} height={VB} fill="none" stroke={T.stroke} strokeWidth={sw} />
      <Line x1={0} y1={0} x2={VB} y2={VB} stroke={T.stroke} strokeWidth={sw} />
      <Line x1={VB} y1={0} x2={0} y2={VB} stroke={T.stroke} strokeWidth={sw} />
      <Line x1={CX} y1={0} x2={VB} y2={CY} stroke={T.stroke} strokeWidth={sw} />
      <Line x1={VB} y1={CY} x2={CX} y2={VB} stroke={T.stroke} strokeWidth={sw} />
      <Line x1={CX} y1={VB} x2={0} y2={CY} stroke={T.stroke} strokeWidth={sw} />
      <Line x1={0} y1={CY} x2={CX} y2={0} stroke={T.stroke} strokeWidth={sw} />
    </G>
  );
}

function HouseLabels({
  house,
  cx,
  cy,
  lagnaSignIndex,
  ascendantDeg,
  planets,
  T,
  full,
}: {
  house: number;
  cx: number;
  cy: number;
  lagnaSignIndex: number;
  ascendantDeg?: number;
  planets: NorthIndianChartProps["planets"];
  T: ChartTheme;
  full: boolean;
}) {
  const signIdx = (lagnaSignIndex + house - 1) % 12;
  const signShort = SIGNS_SHORT[signIdx] ?? "";
  const inHouse = planets.filter(p => p.house === house);
  const isLagna = house === 1;

  const rows: { label: string; fill: string }[] = [];
  if (isLagna && typeof ascendantDeg === "number") {
    rows.push({ label: `La ${degreeInSign(ascendantDeg)}`, fill: T.accent });
  }
  for (const p of inHouse) {
    const deg = typeof p.longitude === "number" ? degreeInSign(p.longitude) : "";
    const st = signStatusFromSign(p.name, signShort);
    const suffix =
      p.retrograde ? "*" :
      st.label.includes("Uchch") ? "↑" :
      st.label.includes("Neech") ? "↓" : "";
    rows.push({
      label: `${PLANET_SHORT[p.name] ?? p.name.slice(0, 2)}${suffix}${deg ? ` ${deg}` : ""}`,
      fill: PLANET_CLR[p.name] ?? T.signNum,
    });
  }

  const signFs = full ? 18 : 15;
  const planetFs = full ? 11.5 : 10;
  const lineH = full ? 13 : 11;
  const topY = cy - (full ? 16 : 14);
  const planetStartY = cy + (full ? 4 : 2);

  return (
    <G>
      <SvgText x={cx} y={topY} textAnchor="middle" fontSize={signFs} fontWeight="800" fill={T.signNum}>
        {String(signNum(signIdx))}
      </SvgText>
      {rows.map((row, i) => (
        <SvgText
          key={`${house}-${row.label}-${i}`}
          x={cx}
          y={planetStartY + i * lineH}
          textAnchor="middle"
          fontSize={planetFs}
          fontWeight="700"
          fill={row.fill}
        >
          {row.label}
        </SvgText>
      ))}
    </G>
  );
}

export function NorthIndianChart({
  title,
  subtitle,
  lagnaSignIndex,
  ascendantDeg,
  planets,
  variant = "default",
  showHeader = true,
}: NorthIndianChartProps) {
  const C = useC();
  const full = variant === "full";
  const { width: screenW } = useWindowDimensions();
  const T = chartTheme(C.isDark);
  const chartMaxW = full
    ? Math.min(480, screenW - 32)
    : Math.min(450, screenW - 32);

  const byHouse = useMemo(
    () => planets.filter(p => p.house >= 1 && p.house <= 12),
    [planets],
  );

  return (
    <View style={[s.wrap, full && s.wrapFull, { backgroundColor: T.wrapBg, borderColor: T.wrapBorder, maxWidth: chartMaxW }]}>
      {showHeader && (
        <View style={[s.titleBand, { backgroundColor: `${T.stroke}18`, borderColor: T.wrapBorder }]}>
          <Text style={[s.title, full && s.titleFull, { color: T.title }]}>{title}</Text>
          {subtitle ? (
            <Text style={[s.sub, { color: T.sub }]} numberOfLines={1}>
              North Indian · {subtitle}
            </Text>
          ) : null}
        </View>
      )}

      <View style={[s.svgContainer, full && s.svgContainerFull, { width: chartMaxW, height: chartMaxW }]}>
        <Svg width="100%" height="100%" viewBox={`0 0 ${VB} ${VB}`} preserveAspectRatio="xMidYMid meet">
          <ChartGeometry T={T} />
          {Object.entries(HOUSE_CENTERS).map(([h, { x, y }]) => (
            <HouseLabels
              key={h}
              house={Number(h)}
              cx={x}
              cy={y}
              lagnaSignIndex={lagnaSignIndex}
              ascendantDeg={Number(h) === 1 ? ascendantDeg : undefined}
              planets={byHouse}
              T={T}
              full={full}
            />
          ))}
        </Svg>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  wrap: {
    width: "100%",
    alignSelf: "center",
    alignItems: "center",
    borderRadius: 16,
    borderWidth: 1.5,
    overflow: "hidden",
    gap: 0,
  },
  wrapFull: {
    borderRadius: 20,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.35,
    shadowRadius: 16,
    elevation: 10,
  },
  titleBand: {
    width: "100%",
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderBottomWidth: 1,
    gap: 3,
    alignItems: "center",
  },
  title: { fontSize: 13, fontFamily: "Nunito_800ExtraBold", letterSpacing: 0.6 },
  titleFull: { fontSize: 15 },
  sub: { fontSize: 10, fontFamily: "Nunito_500Medium" },
  svgContainer: {
    alignSelf: "center",
    alignItems: "center",
    justifyContent: "center",
  },
  svgContainerFull: {
    marginVertical: 4,
  },
});
