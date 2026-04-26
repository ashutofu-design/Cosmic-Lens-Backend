import { Feather } from "@expo/vector-icons";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { router } from "expo-router";
import * as Haptics from "expo-haptics";
import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  I18nManager,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import Svg, { Circle, Defs, G, Line, LinearGradient as SvgGrad, Path, Rect, Stop, Text as SvgText } from "react-native-svg";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";

import { API_BASE, apiFetch } from "@/lib/apiConfig";

const MONTHS_SHORT = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const fmtDate = (d: Date) => `${d.getDate()} ${MONTHS_SHORT[d.getMonth()]}`;

// ── Risk Radar types ─────────────────────────────────────────────────────────
//   Each day carries its own risk profile derived from its energy score.
//   `riskShort` is the FREE 1-line generic warning (every user sees it).
//   `riskCategory` + `riskDetail` + `riskRemedy` are the PAID payload — the
//   forecast page locks them behind a paywall for days 3-7 to drive return
//   visits + premium conversion.
type RiskLevel = "low" | "med" | "high";

interface LuckyColor { name: string; emoji: string; hex: string; }

interface DayForecast {
  date: Date;
  score: number;
  moonLon: number;
  moonSign: string;
  phase: string;
  summary: string;
  // Risk Radar fields (computed per-day from score + day index + date)
  riskLevel:    RiskLevel;
  riskScore:    number;   // 0-10 gauge value
  riskShort:    string;   // 1-line generic warning
  riskCategory: string;   // e.g. "Communication", "Money"
  riskDetail:   string;   // specific Hinglish what-the-risk-is line
  riskDhyan:    string;   // what to be mindful of
  riskAvoid:    string;   // what to avoid
  riskKarna:    string;   // what to do
  riskRemedy:   string;   // actionable upay
  luckyNumbers: number[]; // 3 numbers (1-99)
  luckyColor:   LuckyColor;
  bestTime:     string;   // e.g. "10:30 AM — 12:45 PM"
  avoidTime:    string;   // e.g. "3:15 PM — 5:00 PM"
}

// ── Risk content library ─────────────────────────────────────────────────────
//   Curated Hinglish content covering all 4 quadrants of the 24-hour
//   breakdown (risk / dhyan / avoid / karna). Generic enough to feel
//   personalised without exposing any astrology jargon (no planet/dasha
//   names), per the project's "Powered by Advanced Cosmic Intelligence" rule.
const RISK_BY_LEVEL: Record<RiskLevel, {
  shorts:  string[];
  details: {
    cat: string;
    detail: string;
    dhyan:  string;
    avoid:  string;
    karna:  string;
    remedy: string;
  }[];
}> = {
  low: {
    shorts: [
      "Stable din — apne kaam pe focus karo",
      "Cosmic energies aapke favor mein hain",
      "Smooth flow ka din hai",
    ],
    details: [
      {
        cat: "Career",
        detail: "Naye projects ya pitches start karne ka safe din. Important conversations productive rahengi.",
        dhyan:  "Opportunities ko khule mann se accept karein, momentum banaye rakhein.",
        avoid:  "Negative logon ki advice, pessimistic news, ya self-doubt.",
        karna:  "Meetings, presentations, networking, naye ideas pitch karein.",
        remedy: "Subah 5 minute Surya Namaskar — energy boost ke liye.",
      },
      {
        cat: "Money",
        detail: "Investments aur savings ke liye accha din. Long-term financial decisions safely le sakte hain.",
        dhyan:  "Long-term planning par focus rakhein, short-term shor ko ignore karein.",
        avoid:  "Bekar ke kharch, impulse purchases, gambling.",
        karna:  "SIP, bachat schemes, ya bills clear karein. Budget review karein.",
        remedy: "Peeli ya golden kapde pehnna shubh rahega.",
      },
      {
        cat: "Health",
        detail: "Vitality high rahegi. Workout, meditation ya naye healthy habits build karne ka perfect time.",
        dhyan:  "Routine maintain karein, sleep schedule consistent rakhein.",
        avoid:  "Junk food, late-night screen time, alcohol.",
        karna:  "Yoga, walk, healthy meal plan, hydration badhayein.",
        remedy: "Subah tulsi-paani — overall wellness ke liye.",
      },
    ],
  },
  med: {
    shorts: [
      "Mixed signals — soch samajh ke decisions lo",
      "Communication mein clarity rakhe",
      "Patience aaj ka mantra hai",
    ],
    details: [
      {
        cat: "Communication",
        detail: "Misunderstandings ka risk hai. Important messages double-check karein, clarity rakhein.",
        dhyan:  "Har message aur email padh ke samajh ke bhejein.",
        avoid:  "Voice calls bina prep ke, important texts jaldi mein, gossip.",
        karna:  "Written confirmation lein, points note karein, listen pehle.",
        remedy: "Important call ya meeting se pehle 5 deep breaths.",
      },
      {
        cat: "Decisions",
        detail: "Bade decisions postpone karein. Routine kaam continue, naye commitments aaj avoid karein.",
        dhyan:  "Choti baatein bhi soch samajh ke karein, jaldbaazi nahi.",
        avoid:  "Bade purchases, contracts sign karna, naye commitments.",
        karna:  "Documents review karein, planning karein, pros-cons list banayein.",
        remedy: "Decision se pehle paani peeke 2 min ruk jaayein.",
      },
      {
        cat: "Relations",
        detail: "Family ya partner se patience se baat karein. Choti baatein bade misunderstanding ban sakti hain.",
        dhyan:  "Doosron ke mood aur tone ka khayal rakhein.",
        avoid:  "Sensitive topics, criticism, gussa, blame game.",
        karna:  "Sunne ka time dein, gratitude express karein, quality time spend karein.",
        remedy: "Shaam ko ghar mein diya jalaayein — peace ke liye.",
      },
    ],
  },
  high: {
    shorts: [
      "Saavdhan rahe — important decisions postpone karo",
      "Conflicts avoid karne ki koshish kare",
      "Energy low — apna khayal rakhe",
    ],
    details: [
      {
        cat: "Conflict",
        detail: "Arguments aur disputes ka risk high hai. Confrontations avoid karein — silence is power aaj.",
        dhyan:  "Apna gussa aur reactions control mein rakhein.",
        avoid:  "Arguments, blame game, sharp words, social media debates.",
        karna:  "Solo time lein, meditation karein, breathing exercises.",
        remedy: "Hanuman Chalisa ya Maha Mrityunjaya 11 baar.",
      },
      {
        cat: "Money",
        detail: "Financial decisions strictly avoid. Naye loans, investments aur big purchases postpone karein.",
        dhyan:  "Existing savings safely rakhein, panic se decisions na lein.",
        avoid:  "Loans, investments, bade purchases, kisi ko paisa udhaar dena.",
        karna:  "Budget review karein, expenses track karein, savings safe karein.",
        remedy: "Daan karein — chhota hi sahi, doosron ki madad.",
      },
      {
        cat: "Health",
        detail: "Energy aur immunity low rahegi. Heavy workouts skip karein, rest aur hydration priority dein.",
        dhyan:  "Body ke signals sune — thakaan ho toh rest karein.",
        avoid:  "Heavy workouts, late nights, junk food, alcohol.",
        karna:  "Hydration, neend, light meals, gentle stretches.",
        remedy: "Adrak-haldi paani din mein 2 baar.",
      },
    ],
  },
};

function scoreToRiskScore(score: number): number {
  // Inverse, slightly sharpened so the demo range produces variety:
  //   score 100 → 0, 65 → 5, 50 → 7, 35 → 9, 0 → 10
  return Math.round(Math.max(0, Math.min(10, (100 - score) / 7)));
}

function scoreToRiskLevel(rs: number): RiskLevel {
  if (rs <= 3) return "low";
  if (rs <= 6) return "med";
  return "high";
}

// ── Lucky helpers ────────────────────────────────────────────────────────────
//   All deterministic from date+score so the same day always produces the
//   same "lucky" output. Day-to-day variation comes from the date hash.
const LUCKY_COLORS: Record<RiskLevel, LuckyColor[]> = {
  low: [
    { name: "Hara",     emoji: "🟢", hex: "#4ade80" },
    { name: "Pila",     emoji: "🟡", hex: "#facc15" },
    { name: "Safed",    emoji: "⚪", hex: "#f3f4f6" },
  ],
  med: [
    { name: "Neela",    emoji: "🔵", hex: "#60a5fa" },
    { name: "Pila",     emoji: "🟡", hex: "#facc15" },
    { name: "Suneheri", emoji: "🟠", hex: "#fb923c" },
  ],
  high: [
    { name: "Safed",    emoji: "⚪", hex: "#f3f4f6" },
    { name: "Kesari",   emoji: "🟠", hex: "#fb923c" },
    { name: "Pila",     emoji: "🟡", hex: "#facc15" },
  ],
};

const BEST_TIME_SLOTS = [
  "10:30 AM — 12:45 PM",
  "8:00 AM — 10:15 AM",
  "4:30 PM — 6:30 PM",
  "11:00 AM — 1:15 PM",
  "9:00 AM — 11:00 AM",
  "5:00 PM — 7:00 PM",
  "7:30 AM — 9:45 AM",
];

const AVOID_TIME_SLOTS = [
  "3:15 PM — 5:00 PM",
  "1:00 PM — 2:30 PM",
  "7:00 PM — 8:30 PM",
  "2:30 PM — 4:00 PM",
  "12:30 PM — 2:00 PM",
  "8:00 PM — 9:30 PM",
  "1:45 PM — 3:15 PM",
];

function dayHash(dateMs: number): number {
  return Math.floor(dateMs / 86400000);
}

function getLuckyNumbers(dateMs: number, score: number): number[] {
  const seed = dayHash(dateMs) + score;
  const nums: number[] = [];
  let i = 1;
  while (nums.length < 3 && i < 60) {
    const n = ((Math.abs(seed * (i * 17 + 7))) % 99) + 1;
    if (!nums.includes(n)) nums.push(n);
    i++;
  }
  return nums;
}

function getLuckyColor(level: RiskLevel, dateMs: number): LuckyColor {
  const arr = LUCKY_COLORS[level];
  return arr[dayHash(dateMs) % arr.length];
}

function getBestTime(dateMs: number): string {
  return BEST_TIME_SLOTS[dayHash(dateMs) % BEST_TIME_SLOTS.length];
}

function getAvoidTime(dateMs: number): string {
  // Offset by 2 so best/avoid don't accidentally overlap on the same day.
  return AVOID_TIME_SLOTS[(dayHash(dateMs) + 2) % AVOID_TIME_SLOTS.length];
}

function computeRisk(score: number, dayIdx: number, date: Date) {
  const riskScore = scoreToRiskScore(score);
  const level     = scoreToRiskLevel(riskScore);
  const bucket    = RISK_BY_LEVEL[level];
  const shortLine = bucket.shorts[dayIdx % bucket.shorts.length];
  const det       = bucket.details[dayIdx % bucket.details.length];
  const dateMs    = date.getTime();
  return {
    riskLevel: level,
    riskScore,
    riskShort:    shortLine,
    riskCategory: det.cat,
    riskDetail:   det.detail,
    riskDhyan:    det.dhyan,
    riskAvoid:    det.avoid,
    riskKarna:    det.karna,
    riskRemedy:   det.remedy,
    luckyNumbers: getLuckyNumbers(dateMs, score),
    luckyColor:   getLuckyColor(level, dateMs),
    bestTime:     getBestTime(dateMs),
    avoidTime:    getAvoidTime(dateMs),
  };
}

const SIGNS = [
  "Mesh","Vrishabh","Mithun","Kark","Simha","Kanya",
  "Tula","Vrishchik","Dhanu","Makar","Kumbh","Meen",
];

function moonSign(lon: number): string { return SIGNS[Math.floor(lon / 30) % 12]; }

function moonPhase(date: Date): string {
  const ref = new Date("2000-01-06").getTime();
  const cycle = 29.53058770576;
  const diff = (date.getTime() - ref) / (1000*60*60*24);
  const phase = ((diff % cycle) + cycle) % cycle;
  if (phase < 2)  return "Amavasya";
  if (phase < 7)  return "Shukla Paksha";
  if (phase < 15) return "Shukla Paksha";
  if (phase < 17) return "Purnima";
  if (phase < 22) return "Krishna Paksha";
  if (phase < 29) return "Krishna Paksha";
  return "Amavasya";
}

const SCORE_SUMMARIES: Record<string, string> = {
  UP: "Today is filled with positive energy. A great day to start new ventures.",
  MIXED: "A mixed day — some opportunities, some things to watch out for.",
  DOWN: "Slightly challenging energy today. Stay patient, avoid being reactive.",
};

function scoreToTrend(s: number): "UP"|"MIXED"|"DOWN" {
  return s >= 65 ? "UP" : s <= 40 ? "DOWN" : "MIXED";
}

// ── shapeJourney — same exact transform the home EnergyChart uses ────────────
//   Turns raw scores into an always-rising visual sweep that ENDS at the real
//   final value. Mid-points carry a small wiggle proportional to their actual
//   score so the line still has personality, but the overall arc is the same
//   "journey upward" shape the home chart shows.
function shapeJourney(rawPts: number[]): number[] {
  if (rawPts.length === 0) return [];
  const final = rawPts[rawPts.length - 1];
  const len   = rawPts.length;
  const shaped: number[] = [];
  for (let i = 0; i < len; i++) {
    const t           = len <= 1 ? 1 : i / (len - 1);
    const envelope    = Math.pow(t, 1.4);
    const rawNorm     = rawPts[i] / 100;
    const wiggle      = (rawNorm - 0.5) * 0.35;
    const base        = final * envelope;
    const startOffset = (1 - t) * 8;
    let val           = base + wiggle * final - startOffset;
    val = Math.max(2, Math.min(98, val));
    if (i === len - 1) val = final;
    shaped.push(Math.round(val));
  }
  return shaped;
}

// ── Week chart — pixel-aligned with home EnergyChart ────────────────────────
//   Identical viewBox, padding, gradient defs, grid lines, area fill,
//   stroke widths, dot halos, callout box and footer text. Only differences
//   from the home chart: 7 points (vs 12), date x-axis labels (vs day names),
//   and the "selected" dot replaces home's "final/Now" dot for callouts.
function WeekChart({
  days, scores, selected, onSelect, instant = false,
}: {
  days: DayForecast[]; scores: number[]; selected: number;
  onSelect: (i: number) => void;
  instant?: boolean;
}) {
  const C = useC();
  // Match home EnergyChart exactly.
  const VW  = 340;
  const VH  = 260;
  const PL  = 30;
  const PR  = 14;
  const PT  = 16;
  const GW  = VW - PL - PR;
  const GH  = 190;
  const BOT = PT + GH;
  const RISE_MS = 1200;

  const N    = scores.length;
  const px   = (i: number) => PL + (N <= 1 ? GW / 2 : (i / (N - 1)) * GW);
  const py   = (v: number) => PT + (1 - v / 100) * GH;

  // VISUAL y-positions = always-rising journey (matches home).
  // Real scores still drive the callout text + the per-day cards below.
  const journeyPts = useMemo(() => shapeJourney(scores), [scores]);

  // ── Rise animation — same RAF-based easeOutCubic + per-dot stagger as home ──
  //   animPts are the values that actually get rendered. They start at 0 (line
  //   sits flat on the bottom axis), then each dot rises to its target journey
  //   value with a delay of 0.08 * index, giving the same left-to-right sweep
  //   the home chart shows on first paint.
  const [animPts, setAnimPts] = useState<number[]>(
    instant && journeyPts.length > 0 ? [...journeyPts] : Array(N).fill(0)
  );
  const [animate, setAnimate] = useState(instant && journeyPts.length > 0);
  const [areaVis, setAreaVis] = useState(instant && journeyPts.length > 0);
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
  }, [journeyPts, instant, N]);

  const buildLinePath = () => {
    if (animPts.length < 2) return "";
    let d = `M ${px(0).toFixed(1)},${py(animPts[0]).toFixed(1)}`;
    for (let i = 1; i < N; i++) {
      const x0 = px(i - 1), y0 = py(animPts[i - 1]);
      const x1 = px(i),     y1 = py(animPts[i]);
      const cpx = (x0 + x1) / 2;
      d += ` C ${cpx.toFixed(1)},${y0.toFixed(1)} ${cpx.toFixed(1)},${y1.toFixed(1)} ${x1.toFixed(1)},${y1.toFixed(1)}`;
    }
    return d;
  };

  const linePath = buildLinePath();
  const areaPath = `${linePath} L ${px(N-1).toFixed(1)},${BOT} L ${px(0).toFixed(1)},${BOT} Z`;

  const YGRID = [
    { v: 100, y: PT },
    { v:  75, y: PT + GH * 0.25 },
    { v:  50, y: PT + GH * 0.50 },
    { v:  25, y: PT + GH * 0.75 },
    { v:   0, y: BOT },
  ];

  const gridLine   = C.isDark ? "rgba(255,255,255,0.05)" : "rgba(140,100,200,0.08)";
  const gridStrong = C.isDark ? "rgba(255,255,255,0.07)" : "rgba(140,100,200,0.12)";
  const axisLabel  = C.isDark ? "rgba(255,255,255,0.18)" : "rgba(140,100,200,0.4)";
  const footerText = C.isDark ? "rgba(255,255,255,0.10)" : "rgba(140,100,200,0.35)";
  const calloutBg  = C.isDark ? "rgba(0,20,10,0.85)" : "rgba(255,255,255,0.92)";

  // Color of the selected dot (and its callout border) on the gradient.
  const tSel = N <= 1 ? 1 : selected / (N - 1);
  const selClr = tSel < 0.2 ? "#ff3b3b"
    : tSel < 0.4 ? "#ff8c00"
    : tSel < 0.6 ? "#ffd700"
    : tSel < 0.8 ? "#f59e0b"
    : "#00ff99";

  const sx = px(selected);
  const sy = py(animPts[selected] ?? 0);       // follows the rising curve during animation
  const realScore = scores[selected] ?? 0;     // actual score shown inside the callout

  return (
    <Svg viewBox={`0 0 ${VW} ${VH}`} width="100%" height="100%" style={{ display: "flex" }}>
      <Defs>
        {/* Identical gradient ids/stops to home EnergyChart. */}
        <SvgGrad id="wg-line" x1={PL} y1="0" x2={PL + GW} y2="0" gradientUnits="userSpaceOnUse">
          <Stop offset="0%"   stopColor="#ff3b3b" />
          <Stop offset="20%"  stopColor="#ff8c00" />
          <Stop offset="40%"  stopColor="#ffd700" />
          <Stop offset="60%"  stopColor="#f59e0b" />
          <Stop offset="100%" stopColor="#00ff99" />
        </SvgGrad>
        <SvgGrad id="wg-area" x1="0" y1={PT} x2="0" y2={BOT} gradientUnits="userSpaceOnUse">
          <Stop offset="0%"   stopColor={C.isDark ? "#00ffcc" : "#9f7aea"} stopOpacity={areaVis ? 0.18 : 0} />
          <Stop offset="50%"  stopColor={C.isDark ? "#00ffcc" : "#9f7aea"} stopOpacity={areaVis ? 0.06 : 0} />
          <Stop offset="100%" stopColor={C.isDark ? "#00ffcc" : "#9f7aea"} stopOpacity={0} />
        </SvgGrad>
      </Defs>

      {/* y-axis grid (same dash + opacity as home) */}
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

      {scores.length > 1 && (
        <Path d={areaPath} fill="url(#wg-area)" opacity={areaVis ? 1 : 0} />
      )}

      {/* Glow + solid line — paths are built from animPts so they rise during animation */}
      {scores.length > 1 && (
        <Path d={linePath} fill="none" stroke="url(#wg-line)" strokeWidth={14} opacity={0.06} strokeLinecap="round" strokeLinejoin="round" />
      )}

      {scores.length > 1 && (
        <Path d={linePath} fill="none" stroke="url(#wg-line)" strokeWidth={2.8} strokeLinecap="round" strokeLinejoin="round" />
      )}

      {/* Non-selected dot markers — fade in once animation starts; y rides animPts. */}
      {scores.map((_, i) => {
        if (i === selected) return null;
        const t = N <= 1 ? 0 : i / (N - 1);
        const color = t < 0.2 ? "#ff3b3b"
          : t < 0.4 ? "#ff8c00"
          : t < 0.6 ? "#ffd700"
          : t < 0.8 ? "#f59e0b"
          : "#00ff99";
        const x = px(i), y = py(animPts[i] ?? 0);
        return (
          <G key={i} opacity={animate ? 1 : 0}>
            <Circle cx={x} cy={y} r={4} fill={color} opacity={0.10} />
            <Circle cx={x} cy={y} r={2} fill={color} />
          </G>
        );
      })}

      {/* Selected dot — pulse-style halo nest, only renders once animation starts */}
      {scores.length > 0 && animate && (
        <G>
          <Circle cx={sx} cy={sy} r={12}  fill={selClr} opacity={0.07} />
          <Circle cx={sx} cy={sy} r={7}   fill={selClr} opacity={0.14} />
          <Circle cx={sx} cy={sy} r={4.5} fill={selClr} opacity={0.9} />
          <Circle cx={sx} cy={sy} r={1.8} fill="white"  opacity={0.95} />
        </G>
      )}

      {/* Selected score callout — fades in with the rest of the animation. */}
      {scores.length > 0 && animate && (() => {
        const W = 38, H = 21, GAP = 14;
        const minX = PL - 4;
        const maxX = PL + GW + 4 - W;
        let cx = sx - W - GAP;
        if (cx < minX) cx = sx + GAP;
        cx = Math.max(minX, Math.min(maxX, cx));
        const tx = cx + W / 2;
        return (
          <G>
            <Rect x={cx} y={sy - 14} width={W} height={H} rx={7}
              fill={calloutBg} stroke={selClr} strokeOpacity={0.5} strokeWidth={0.8} />
            <SvgText x={tx} y={sy + 2.5} textAnchor="middle" fill={selClr} fontSize={11} fontWeight="800">
              {realScore}
            </SvgText>
          </G>
        );
      })()}

      {/* Invisible tap targets — sit on the animated curve so the touch zone
          tracks the visible dot during the rise. */}
      {scores.map((_, i) => {
        const x = px(i), y = py(animPts[i] ?? 0);
        return (
          <Circle
            key={`tap-${i}`}
            cx={x} cy={y} r={16} fill="transparent"
            onPress={() => { onSelect(i); Haptics.selectionAsync(); }}
          />
        );
      })}

      {/* Date labels on x-axis — fade in with the chart so nothing pops in early. */}
      {days.map((d, i) => {
        const isSel = i === selected;
        return (
          <SvgText key={i}
            x={px(i)} y={BOT + 16}
            textAnchor="middle"
            fill={isSel ? selClr : axisLabel}
            fontSize={isSel ? 8 : 7}
            fontWeight={isSel ? "700" : "400"}
            opacity={animate ? 1 : 0}>
            {fmtDate(d.date)}
          </SvgText>
        );
      })}

      {/* Footer signature — same exact line as home */}
      <SvgText x={VW / 2} y={VH - 4} textAnchor="middle" fill={footerText} fontSize={5.5} letterSpacing={2.5}>
        NAVATARA  ·  MOON TRANSIT  ·  ASHTAKAVARGA
      </SvgText>
    </Svg>
  );
}

// ── Cosmic Risk Radar ────────────────────────────────────────────────────────
//   A consolidated per-day risk module that bundles every "what's happening
//   in my next 24 hours" signal into one card: gauge, 24-hour breakdown
//   (risk / dhyan / avoid / karna), upay, lucky numbers, lucky color, best
//   time, and avoid time. Day 1 is a free preview for everyone; Day 2-7 are
//   premium-gated (currently proxied via "kundli set"). The Safest /
//   Challenging chips at the top double as week navigation.
//
//   Streak counter (top-right) increments once per UTC day and resets on a
//   missed day — the daily-return habit hook.
const FREE_DAYS = 1;  // only Day 1 is a free preview for non-premium users
function RiskRadar({
  days, selected, onSelect, fullAccess,
}: {
  days: DayForecast[]; selected: number; onSelect: (i: number) => void;
  // True when the user has premium access (currently proxied via "kundli set").
  // When false, only Day 1 is unlocked; Days 2-7 show the upgrade card.
  fullAccess: boolean;
}) {
  const C = useC();

  // ── Daily streak counter ─────────────────────────────────────────────────
  // Persisted via AsyncStorage. Increments once per UTC day on first open;
  // resets to 1 if the user missed a day. Only rendered when streak >= 2 so
  // the badge doesn't clutter the header on day-1 installs.
  const [streak, setStreak] = useState(0);
  useEffect(() => {
    (async () => {
      try {
        const today  = new Date().toISOString().slice(0, 10);
        const last   = await AsyncStorage.getItem("@cl_radar_last_open");
        const cntStr = await AsyncStorage.getItem("@cl_radar_streak");
        const cnt    = parseInt(cntStr || "0", 10) || 0;
        if (last === today) { setStreak(cnt); return; }
        const yest = new Date(); yest.setUTCDate(yest.getUTCDate() - 1);
        const yestStr = yest.toISOString().slice(0, 10);
        const newCnt  = (last === yestStr) ? (cnt + 1) : 1;
        await AsyncStorage.setItem("@cl_radar_last_open", today);
        await AsyncStorage.setItem("@cl_radar_streak",    String(newCnt));
        setStreak(newCnt);
      } catch { /* AsyncStorage unavailable — streak stays 0, badge hides */ }
    })();
  }, []);

  if (days.length === 0) return null;
  const sel = days[selected];
  if (!sel) return null;

  // Find the safest (lowest risk) and riskiest (highest risk) days of the week.
  let safestIdx = 0, riskiestIdx = 0;
  days.forEach((d, i) => {
    if (d.riskScore < days[safestIdx].riskScore)   safestIdx   = i;
    if (d.riskScore > days[riskiestIdx].riskScore) riskiestIdx = i;
  });

  const isLocked = !fullAccess && selected >= FREE_DAYS;
  const levelColor =
    sel.riskLevel === "low" ? "#4ade80" :
    sel.riskLevel === "med" ? "#fbbf24" : "#ef4444";
  const levelLabel =
    sel.riskLevel === "low" ? "LOW" :
    sel.riskLevel === "med" ? "MEDIUM" : "HIGH";

  // Marker x-position on the gauge: 0/10 → 0%, 10/10 → 100%.
  const markerPct = `${(sel.riskScore / 10) * 100}%` as `${number}%`;

  return (
    <View style={[s.riskCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
      {/* Header — title, streak badge, day position */}
      <View style={s.riskHeader}>
        <View style={s.riskTitleRow}>
          <Feather name="alert-triangle" size={13} color="#fbbf24" />
          <Text style={[s.riskTitle, { color: C.text }]}>Cosmic Risk Radar</Text>
        </View>
        <View style={s.riskHeaderRight}>
          {streak >= 2 && (
            <View style={s.streakPill}>
              <Text style={s.streakPillText}>🔥 {streak}</Text>
            </View>
          )}
          <Text style={[s.riskHeaderHint, { color: C.textDim }]}>Day {selected + 1} of 7</Text>
        </View>
      </View>

      {/* Week highlights — Safest / Challenging chips (always visible, free teaser) */}
      <View style={s.riskChipsRow}>
        <Pressable
          onPress={() => { onSelect(safestIdx); Haptics.selectionAsync(); }}
          style={[s.riskChip, {
            backgroundColor: "rgba(74,222,128,0.10)",
            borderColor:     "rgba(74,222,128,0.30)",
          }]}
        >
          <Text style={[s.riskChipLabel, { color: "#4ade80" }]}>SAFEST</Text>
          <Text style={[s.riskChipDay,   { color: C.text }]}>{fmtDate(days[safestIdx].date)}</Text>
        </Pressable>
        <Pressable
          onPress={() => { onSelect(riskiestIdx); Haptics.selectionAsync(); }}
          style={[s.riskChip, {
            backgroundColor: "rgba(239,68,68,0.10)",
            borderColor:     "rgba(239,68,68,0.30)",
          }]}
        >
          <Text style={[s.riskChipLabel, { color: "#ef4444" }]}>CHALLENGING</Text>
          <Text style={[s.riskChipDay,   { color: C.text }]}>{fmtDate(days[riskiestIdx].date)}</Text>
        </Pressable>
      </View>

      {isLocked ? (
        // ── Locked overlay for premium-gated days ──────────────────────────
        <Pressable
          style={[s.riskLockedCard, {
            backgroundColor: "rgba(251,191,36,0.06)",
            borderColor:     "rgba(251,191,36,0.30)",
          }]}
          onPress={() => router.push("/onboarding")}
        >
          <View style={s.riskLockedTop}>
            <Feather name="lock" size={14} color="#fbbf24" />
            <Text style={s.riskLockedTitle}>{fmtDate(sel.date)} ka radar locked</Text>
          </View>
          <Text style={s.riskLockedSub}>
            Aane wale dino ka full radar — risk level, kya karna/avoid karna,
            lucky numbers, best time aur upay — Premium se unlock karein.
          </Text>
          <Pressable
            onPress={(e) => { e.stopPropagation?.(); onSelect(0); Haptics.selectionAsync(); }}
            style={[s.riskLockedHint, { borderColor: C.border }]}
          >
            <Text style={[s.riskLockedHintText, { color: C.textMuted }]}>
              💡 Day 1 free hai — preview ke liye tap karein
            </Text>
          </Pressable>
          <View style={s.riskLockedCta}>
            <Text style={s.riskLockedCtaText}>UNLOCK PREMIUM</Text>
            <Feather name={I18nManager.isRTL ? "arrow-left" : "arrow-right"} size={11} color="#fbbf24" />
          </View>
        </Pressable>
      ) : (
        <>
          {/* ── Risk level gauge ─────────────────────────────────────────── */}
          <View style={s.gaugeHeaderRow}>
            <Text style={[s.gaugeMicroLabel, { color: C.textMuted }]}>RISK LEVEL</Text>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
              <Text style={[s.gaugeLevelText, { color: levelColor   }]}>{levelLabel}</Text>
              <Text style={[s.gaugeValueText, { color: C.textMuted  }]}>{sel.riskScore}/10</Text>
            </View>
          </View>
          <View style={s.gaugeTrack}>
            <View style={[s.gaugeSeg, { backgroundColor: "rgba(74,222,128,0.22)",  borderTopLeftRadius: 4, borderBottomLeftRadius: 4 }]} />
            <View style={[s.gaugeSeg, { backgroundColor: "rgba(251,191,36,0.22)" }]} />
            <View style={[s.gaugeSeg, { backgroundColor: "rgba(239,68,68,0.22)",   borderTopRightRadius: 4, borderBottomRightRadius: 4 }]} />
            <View style={[s.gaugeMarker, {
              left: markerPct,
              backgroundColor: levelColor,
              shadowColor: levelColor,
            }]} />
          </View>
          <View style={s.gaugeScaleRow}>
            <Text style={[s.gaugeScaleText, { color: C.textDim }]}>Low</Text>
            <Text style={[s.gaugeScaleText, { color: C.textDim }]}>Med</Text>
            <Text style={[s.gaugeScaleText, { color: C.textDim }]}>High</Text>
          </View>

          {/* 1-line generic warning */}
          <View style={[s.riskShortRow, { borderColor: C.border }]}>
            <Text style={s.riskShortIcon}>💬</Text>
            <Text style={[s.riskShortText, { color: C.text }]}>{sel.riskShort}</Text>
          </View>

          {/* ── 24-hour breakdown — 4 quadrants ──────────────────────────── */}
          <View style={s.breakdownHeader}>
            <Feather name="clock" size={11} color={C.textMuted} />
            <Text style={[s.breakdownHeaderText, { color: C.textMuted }]}>
              {selected === 0 ? "AAJ KE 24 GHANTE" : `${fmtDate(sel.date).toUpperCase()} KE 24 GHANTE`}
            </Text>
          </View>

          <View style={[s.breakdownRow, {
            backgroundColor: `${levelColor}10`,
            borderColor:     `${levelColor}30`,
          }]}>
            <View style={[s.breakdownIconBox, { backgroundColor: `${levelColor}22` }]}>
              <Feather name="alert-triangle" size={14} color={levelColor} />
            </View>
            <View style={s.breakdownText}>
              <Text style={[s.breakdownLabel, { color: levelColor }]}>KYA RISK HAI</Text>
              <Text style={[s.breakdownBody,  { color: C.text     }]}>{sel.riskDetail}</Text>
            </View>
          </View>

          <View style={[s.breakdownRow, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <View style={[s.breakdownIconBox, { backgroundColor: "rgba(96,165,250,0.18)" }]}>
              <Feather name="eye" size={14} color="#60a5fa" />
            </View>
            <View style={s.breakdownText}>
              <Text style={[s.breakdownLabel, { color: "#60a5fa" }]}>KYA DHYAN RAKHNA HAI</Text>
              <Text style={[s.breakdownBody,  { color: C.text    }]}>{sel.riskDhyan}</Text>
            </View>
          </View>

          <View style={[s.breakdownRow, {
            backgroundColor: "rgba(239,68,68,0.08)",
            borderColor:     "rgba(239,68,68,0.25)",
          }]}>
            <View style={[s.breakdownIconBox, { backgroundColor: "rgba(239,68,68,0.22)" }]}>
              <Feather name="x-circle" size={14} color="#ef4444" />
            </View>
            <View style={s.breakdownText}>
              <Text style={[s.breakdownLabel, { color: "#ef4444" }]}>KYA AVOID KARNA HAI</Text>
              <Text style={[s.breakdownBody,  { color: C.text    }]}>{sel.riskAvoid}</Text>
            </View>
          </View>

          <View style={[s.breakdownRow, {
            backgroundColor: "rgba(74,222,128,0.08)",
            borderColor:     "rgba(74,222,128,0.25)",
          }]}>
            <View style={[s.breakdownIconBox, { backgroundColor: "rgba(74,222,128,0.22)" }]}>
              <Feather name="check-circle" size={14} color="#4ade80" />
            </View>
            <View style={s.breakdownText}>
              <Text style={[s.breakdownLabel, { color: "#4ade80" }]}>KYA KARNA HAI</Text>
              <Text style={[s.breakdownBody,  { color: C.text    }]}>{sel.riskKarna}</Text>
            </View>
          </View>

          {/* ── Mini upay ────────────────────────────────────────────────── */}
          <View style={[s.riskRemedyRow, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <Text style={s.riskRemedyIcon}>🪔</Text>
            <View style={{ flex: 1 }}>
              <Text style={[s.riskRemedyLabel, { color: C.textMuted }]}>UPAY</Text>
              <Text style={[s.riskRemedyText,  { color: C.text      }]}>{sel.riskRemedy}</Text>
            </View>
          </View>

          {/* ── Lucky grid — numbers + color (row 1), best/avoid time (row 2) ── */}
          <View style={s.luckyGrid}>
            <View style={[s.luckyTile, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <Text style={[s.luckyTileLabel, { color: C.textMuted }]}>🍀 LUCKY NUMBERS</Text>
              <View style={s.luckyNumRow}>
                {sel.luckyNumbers.map((n) => (
                  <View key={n} style={[s.luckyNumPill, { borderColor: C.border }]}>
                    <Text style={[s.luckyNumText, { color: C.text }]}>{n}</Text>
                  </View>
                ))}
              </View>
            </View>
            <View style={[s.luckyTile, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <Text style={[s.luckyTileLabel, { color: C.textMuted }]}>🎨 LUCKY COLOR</Text>
              <View style={s.luckyColorRow}>
                <View style={[s.luckyColorSwatch, {
                  backgroundColor: sel.luckyColor.hex,
                  borderColor:     sel.luckyColor.hex === "#f3f4f6" ? "rgba(255,255,255,0.3)" : "transparent",
                }]} />
                <Text style={[s.luckyColorName, { color: C.text }]}>{sel.luckyColor.name}</Text>
              </View>
            </View>
          </View>

          <View style={s.luckyGrid}>
            <View style={[s.luckyTile, {
              backgroundColor: "rgba(74,222,128,0.08)",
              borderColor:     "rgba(74,222,128,0.25)",
            }]}>
              <Text style={[s.luckyTileLabel, { color: "#4ade80" }]}>⏰ BEST TIME</Text>
              <Text style={[s.luckyTimeText, { color: C.text }]}>{sel.bestTime}</Text>
            </View>
            <View style={[s.luckyTile, {
              backgroundColor: "rgba(239,68,68,0.08)",
              borderColor:     "rgba(239,68,68,0.25)",
            }]}>
              <Text style={[s.luckyTileLabel, { color: "#ef4444" }]}>🚫 AVOID TIME</Text>
              <Text style={[s.luckyTimeText, { color: C.text }]}>{sel.avoidTime}</Text>
            </View>
          </View>
        </>
      )}
    </View>
  );
}

export default function ForecastScreen() {
  const insets   = useSafeAreaInsets();
  const C = useC();
  const t = useT();
  const { kundli, moonData } = useUser();
  const topPad   = Platform.OS === "web" ? 67 : insets.top;
  const botPad   = Platform.OS === "web" ? 34 : insets.bottom;
  const showDemo = !kundli;

  const [days, setDays]       = useState<DayForecast[]>([]);
  // Default to the LAST day so the score callout sits on the rightmost (green
  // gradient end) — exactly like home's "Now" dot. User can tap any other day
  // to move the highlight; the curve always rises toward whichever day is selected.
  const [selected, setSelected] = useState(6);
  const [loading, setLoading]   = useState(false);

  // Build 7 dates starting from TOMORROW (today is shown on the home screen,
  // so the forecast page exclusively shows the next 7 days for planning).
  useEffect(() => {
    const dates: string[] = [];
    const today = new Date();
    for (let i = 1; i <= 7; i++) {
      const d = new Date(today);
      d.setDate(today.getDate() + i);
      dates.push(`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`);
    }

    if (showDemo) {
      const demoScores = [58, 81, 45, 70, 65, 77, 62];
      const demoMoons  = [133, 147, 162, 177, 192, 207, 222];
      setDays(dates.map((ds, i) => {
        const dt = new Date(ds);
        return {
          date: dt,
          score: demoScores[i],
          moonLon: demoMoons[i],
          moonSign: moonSign(demoMoons[i]),
          phase: moonPhase(dt),
          summary: SCORE_SUMMARIES[scoreToTrend(demoScores[i])],
          ...computeRisk(demoScores[i], i, dt),
        };
      }));
      return;
    }

    setLoading(true);
    apiFetch(`${API_BASE}/api/transits`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dates }),
    })
      .then(r => r.json())
      .then((data: { date: string; positions: Record<string,number> }[]) => {
        const moonLon = moonData?.longitude ?? 0;
        // Use a stable mid-range baseline so projected scores aren't pinned to today's
        // specific value (this page is forward-looking trends, not today's reading).
        const baseScore = 60;

        const built = data.map((item, i) => {
          // Forecast index: i=0 → tomorrow, i=6 → today + 7. Offset by +1 day for moon estimate.
          const dayOffset   = i + 1;
          const transitMoon = item.positions?.Moon ?? (moonLon + dayOffset * 13.2);
          const variation   = Math.sin(dayOffset * 1.3) * 12 + (item.positions?.Jupiter ? 5 : 0)
            - (item.positions?.Saturn ? 6 : 0);
          const score = Math.max(10, Math.min(90, Math.round(baseScore + variation)));
          const dt    = new Date(item.date + "T00:00:00");
          return {
            date:     dt,
            score,
            moonLon:  transitMoon,
            moonSign: moonSign(transitMoon),
            phase:    moonPhase(dt),
            summary:  SCORE_SUMMARIES[scoreToTrend(score)],
            ...computeRisk(score, i, dt),
          };
        });
        setDays(built);
      })
      .catch(() => {
        // API failed — clear days so UI shows the empty/error state
        // (avoid fake scores that would mislead user into thinking it's real data)
        setDays([]);
      })
      .finally(() => setLoading(false));
  }, [kundli, moonData, showDemo]);

  const sel = days[selected];
  const scoreColor = sel
    ? (sel.score >= 65 ? "#4ade80" : sel.score <= 40 ? "#ef4444" : "#fbbf24")
    : "#f59e0b";

  return (
    <View style={[s.root, { paddingTop: topPad, backgroundColor: C.bg }]}>
      {/* Header */}
      <View style={[s.header, { borderBottomColor: C.border }]}>
        <Pressable onPress={() => router.back()} style={s.back}>
          <Feather name={I18nManager.isRTL ? "arrow-right" : "arrow-left"} size={20} color={C.textMuted} />
        </Pressable>
        <Text style={[s.headerTitle, { color: C.text }]}>{t.forecastTitle}</Text>
        {showDemo && (
          <View style={s.demoPill}>
            <Text style={s.demoPillText}>{t.fc_demo}</Text>
          </View>
        )}
      </View>

      <ScrollView contentContainerStyle={[s.content, { paddingBottom: botPad + 30 }]} showsVerticalScrollIndicator={false}>
        {/* Hero forecast card — mirrors the home HeroEnergyCard exactly:
            same #0f0a24 background, score-tinted border + outer glow, top row
            with label + selected score, chart filling the body, insight pill
            at the bottom. Sized with a fixed minHeight so it has the same big
            immersive presence the home card gets from `flex: 1` on home. */}
        <View style={[
          s.heroCard,
          {
            backgroundColor: "#0f0a24",
            borderColor: `${scoreColor}40`,
            shadowColor: scoreColor,
          },
        ]}>
          {/* Top row — "ENERGY FORECAST" label + DEMO badge + selected score */}
          <View style={s.heroTopRow}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
              <Text style={[s.heroLabel, { color: "rgba(255,255,255,0.45)" }]}>
                {t.forecastTitle?.toUpperCase?.() ?? "ENERGY FORECAST"}
              </Text>
              {showDemo && (
                <View style={[s.heroDemoBadge, { backgroundColor: C.bgCard2 ?? C.bgCard, borderColor: C.border }]}>
                  <Feather name="lock" size={8} color={C.textDim} />
                  <Text style={[s.heroDemoBadgeText, { color: C.textDim }]}>{t.fc_demo ?? "DEMO"}</Text>
                </View>
              )}
            </View>
            {sel && (
              <View style={{ flexDirection: "row", alignItems: "flex-end", gap: 2 }}>
                <Text style={[s.heroScore, { color: scoreColor }]}>{sel.score}</Text>
                <Text style={[s.heroScoreMax, { color: C.textDim }]}>/100</Text>
              </View>
            )}
          </View>

          {/* Chart — flex:1 so it fills the remaining card height, exactly like home */}
          <View style={{ flex: 1, minHeight: 240 }}>
            {days.length > 0 ? (
              <WeekChart
                days={days}
                scores={days.map(d => d.score)}
                selected={selected}
                onSelect={setSelected}
              />
            ) : (
              <View style={s.chartPlaceholder}>
                <Text style={[s.placeholderText, { color: C.textMuted }]}>
                  {loading ? t.loading : t.forecastError}
                </Text>
              </View>
            )}
          </View>

          {/* Insight pill — selected day's summary, styled like home's insightPill */}
          {sel && (
            <View style={{ flexDirection: "row", alignItems: "center" }}>
              <View style={[s.heroInsightPill, { backgroundColor: `${scoreColor}10`, borderColor: `${scoreColor}30` }]}>
                <Feather name="sun" size={11} color={scoreColor} />
                <Text style={[s.heroInsightText, { color: scoreColor }]} numberOfLines={1}>
                  {sel.date.toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short" })} · {sel.summary}
                </Text>
              </View>
            </View>
          )}
        </View>

        {/* Selected day detail */}
        {sel && (
          <>
            {/* Cosmic Risk Radar — focused per-day risk module with freemium gate.
                Sits between the hero chart and the supporting info so it's the
                first thing the user reads after seeing the day's score. */}
            <RiskRadar
              days={days}
              selected={selected}
              onSelect={setSelected}
              fullAccess={!showDemo}
            />

            {/* Day navigation row */}
            <View style={s.navRow}>
              <Pressable
                style={[s.navBtn, selected === 0 && s.navBtnDisabled]}
                onPress={() => { if (selected > 0) { setSelected(selected - 1); Haptics.selectionAsync(); } }}
              >
                <Feather name={I18nManager.isRTL ? "chevron-right" : "chevron-left"} size={16} color={selected === 0 ? C.textDim : C.text} />
                <Text style={[s.navLabel, { color: C.text }, selected === 0 && { color: C.textDim }]}>{t.prevDay}</Text>
              </Pressable>
              <View style={s.navDots}>
                {days.map((_, i) => (
                  <Pressable key={i} onPress={() => setSelected(i)}>
                    <View style={[s.navDot, { backgroundColor: C.border }, i === selected && s.navDotActive]} />
                  </Pressable>
                ))}
              </View>
              <Pressable
                style={[s.navBtn, selected === 6 && s.navBtnDisabled]}
                onPress={() => { if (selected < days.length-1) { setSelected(selected + 1); Haptics.selectionAsync(); } }}
              >
                <Text style={[s.navLabel, { color: C.text }, selected === 6 && { color: C.textDim }]}>{t.nextDay}</Text>
                <Feather name={I18nManager.isRTL ? "chevron-left" : "chevron-right"} size={16} color={selected === 6 ? C.textDim : C.text} />
              </Pressable>
            </View>
          </>
        )}

        {/* Demo unlock prompt */}
        {showDemo && (
          <Pressable style={s.unlockBanner} onPress={() => router.push("/onboarding")}>
            <Feather name="lock" size={14} color="#fbbf24" />
            <View style={{ flex: 1 }}>
              <Text style={s.unlockTitle}>{t.unlockForecastTitle}</Text>
              <Text style={s.unlockSub}>{t.unlockForecastSub}</Text>
            </View>
            <Feather name={I18nManager.isRTL ? "chevron-left" : "chevron-right"} size={14} color="#fbbf24" />
          </Pressable>
        )}
      </ScrollView>
    </View>
  );
}

const s = StyleSheet.create({
  root:    { flex: 1, backgroundColor: "#020d1a" },
  header: {
    flexDirection: "row", alignItems: "center",
    paddingHorizontal: 16, paddingBottom: 12, paddingTop: 12, gap: 10,
    borderBottomWidth: 1, borderBottomColor: "rgba(255,255,255,0.04)",
  },
  back:        { padding: 4 },
  headerTitle: { color: "#dde8f4", fontSize: 18, fontWeight: "700", flex: 1 },
  demoPill: {
    backgroundColor: "rgba(251,191,36,0.15)", borderRadius: 10,
    paddingHorizontal: 8, paddingVertical: 2, borderWidth: 1, borderColor: "rgba(251,191,36,0.3)",
  },
  demoPillText: { color: "#fbbf24", fontSize: 10, fontWeight: "600" },

  content: { padding: 16, gap: 14 },

  // ── Hero forecast card — dimensionally + visually identical to home HeroEnergyCard ──
  heroCard: {
    borderRadius: 16, borderWidth: 1,
    paddingHorizontal: 10, paddingTop: 10, paddingBottom: 8,
    overflow: "hidden", gap: 4,
    minHeight: 380,                           // big immersive presence (home gets this from flex:1)
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.28, shadowRadius: 24, elevation: 5,
  },
  heroTopRow: {
    flexDirection: "row", alignItems: "center",
    justifyContent: "space-between",
  },
  heroLabel:    { fontSize: 8.5, fontWeight: "700", letterSpacing: 2 },
  heroScore:    { fontSize: 28, fontWeight: "800", letterSpacing: -1, lineHeight: 32 },
  heroScoreMax: { fontSize: 12, fontWeight: "600", paddingBottom: 3 },
  heroDemoBadge: {
    flexDirection: "row", alignItems: "center", gap: 3,
    borderWidth: 1, paddingVertical: 2,
    paddingHorizontal: 6, borderRadius: 5,
  },
  heroDemoBadgeText: { fontSize: 7, fontWeight: "700", letterSpacing: 1.2 },
  heroInsightPill: {
    flexDirection: "row", alignItems: "center", gap: 5,
    borderWidth: 1, borderRadius: 7, paddingVertical: 4, paddingHorizontal: 8,
    flexShrink: 1, maxWidth: "100%",
  },
  heroInsightText: { fontSize: 10, fontWeight: "600", flexShrink: 1 },

  chartPlaceholder: { flex: 1, alignItems: "center", justifyContent: "center" },
  placeholderText: { color: "#1e3a5f" },

  navRow:    { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  navBtn:    { flexDirection: "row", alignItems: "center", gap: 4, padding: 8 },
  navBtnDisabled: { opacity: 0.3 },
  navLabel:  { color: "#dde8f4", fontSize: 12 },
  navDots:   { flexDirection: "row", gap: 6 },
  navDot:    { width: 6, height: 6, borderRadius: 3, backgroundColor: "#1e3a5f" },
  navDotActive: { backgroundColor: "#f59e0b", width: 16 },

  unlockBanner: {
    backgroundColor: "rgba(251,191,36,0.06)", borderRadius: 16,
    borderWidth: 1, borderColor: "rgba(251,191,36,0.2)",
    padding: 16, flexDirection: "row", gap: 12, alignItems: "center",
  },
  unlockTitle: { color: "#fbbf24", fontSize: 13, fontWeight: "600" },
  unlockSub:   { color: "#92704e", fontSize: 11 },

  // ── Cosmic Risk Radar ────────────────────────────────────────────────────
  riskCard: {
    borderRadius: 16, borderWidth: 1,
    padding: 14, gap: 10,
  },
  riskHeader: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
  },
  riskTitleRow:    { flexDirection: "row", alignItems: "center", gap: 6 },
  riskTitle:       { fontSize: 13, fontWeight: "700", letterSpacing: 0.4 },
  riskHeaderHint:  { fontSize: 10, fontWeight: "600", letterSpacing: 1 },

  // Safest / Riskiest day chips
  riskChipsRow:    { flexDirection: "row", gap: 8 },
  riskChip: {
    flex: 1, flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingVertical: 6, paddingHorizontal: 10, borderRadius: 8, borderWidth: 1,
  },
  riskChipLabel:   { fontSize: 9,  fontWeight: "800", letterSpacing: 1 },
  riskChipDay:     { fontSize: 11, fontWeight: "600" },

  // Gauge bar
  gaugeHeaderRow:  { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginTop: 4 },
  gaugeMicroLabel: { fontSize: 9,  fontWeight: "700", letterSpacing: 1.4 },
  gaugeLevelText:  { fontSize: 13, fontWeight: "800", letterSpacing: 0.6 },
  gaugeValueText:  { fontSize: 11, fontWeight: "600" },
  gaugeTrack: {
    flexDirection: "row", height: 8, borderRadius: 4, overflow: "visible", position: "relative",
  },
  gaugeSeg:        { flex: 1, height: 8 },
  gaugeMarker: {
    position: "absolute", top: -3, width: 14, height: 14, borderRadius: 7,
    transform: [{ translateX: -7 }],
    borderWidth: 2, borderColor: "#0f0a24",
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.7, shadowRadius: 6, elevation: 4,
  },
  gaugeScaleRow:   { flexDirection: "row", justifyContent: "space-between", marginTop: 2 },
  gaugeScaleText:  { fontSize: 9, fontWeight: "600", letterSpacing: 0.5 },

  // Free 1-line warning
  riskShortRow: {
    flexDirection: "row", alignItems: "center", gap: 8,
    paddingVertical: 8, paddingHorizontal: 10, borderRadius: 8, borderWidth: 1,
    marginTop: 2,
  },
  riskShortIcon:   { fontSize: 13 },
  riskShortText:   { flex: 1, fontSize: 12, fontWeight: "600", lineHeight: 16 },

  // Header right side (streak pill + day-of-7 hint)
  riskHeaderRight: { flexDirection: "row", alignItems: "center", gap: 8 },
  streakPill: {
    backgroundColor: "rgba(251,146,60,0.14)",
    borderWidth: 1, borderColor: "rgba(251,146,60,0.40)",
    paddingHorizontal: 7, paddingVertical: 2, borderRadius: 10,
  },
  streakPillText: { color: "#fb923c", fontSize: 10, fontWeight: "800", letterSpacing: 0.4 },

  // 24-hour breakdown rows (KYA RISK / DHYAN / AVOID / KARNA)
  breakdownHeader: {
    flexDirection: "row", alignItems: "center", gap: 6, marginTop: 4,
  },
  breakdownHeaderText: { fontSize: 10, fontWeight: "800", letterSpacing: 1.4 },
  breakdownRow: {
    flexDirection: "row", alignItems: "flex-start", gap: 10,
    padding: 10, borderRadius: 10, borderWidth: 1,
  },
  breakdownIconBox: {
    width: 28, height: 28, borderRadius: 8,
    alignItems: "center", justifyContent: "center", flexShrink: 0,
  },
  breakdownText:  { flex: 1, gap: 3 },
  breakdownLabel: { fontSize: 9,  fontWeight: "800", letterSpacing: 1.2 },
  breakdownBody:  { fontSize: 12, fontWeight: "500", lineHeight: 17 },

  // Mini upay row (kept from old design)
  riskRemedyRow: {
    flexDirection: "row", alignItems: "center", gap: 10,
    padding: 10, borderRadius: 10, borderWidth: 1,
  },
  riskRemedyIcon:  { fontSize: 18 },
  riskRemedyLabel: { fontSize: 9,  fontWeight: "800", letterSpacing: 1.4, marginBottom: 2 },
  riskRemedyText:  { fontSize: 12, fontWeight: "600", lineHeight: 16 },

  // Lucky grid (numbers, color, best/avoid time)
  luckyGrid:    { flexDirection: "row", gap: 8 },
  luckyTile: {
    flex: 1, borderRadius: 10, borderWidth: 1,
    paddingVertical: 10, paddingHorizontal: 10, gap: 8,
    minHeight: 64, justifyContent: "space-between",
  },
  luckyTileLabel: { fontSize: 9, fontWeight: "800", letterSpacing: 1.2 },

  luckyNumRow:  { flexDirection: "row", gap: 6, flexWrap: "wrap" },
  luckyNumPill: {
    minWidth: 28, paddingHorizontal: 6, paddingVertical: 3,
    borderRadius: 6, borderWidth: 1, alignItems: "center",
    backgroundColor: "rgba(251,191,36,0.10)",
  },
  luckyNumText: { fontSize: 12, fontWeight: "800", letterSpacing: 0.5 },

  luckyColorRow:    { flexDirection: "row", alignItems: "center", gap: 8 },
  luckyColorSwatch: {
    width: 20, height: 20, borderRadius: 10, borderWidth: 1,
  },
  luckyColorName:   { fontSize: 13, fontWeight: "700" },

  luckyTimeText: { fontSize: 12, fontWeight: "700", letterSpacing: 0.3 },

  // Locked card (paywall)
  riskLockedCard: {
    borderRadius: 10, borderWidth: 1, padding: 12, gap: 8,
  },
  riskLockedTop:    { flexDirection: "row", alignItems: "center", gap: 8 },
  riskLockedTitle:  { color: "#fbbf24", fontSize: 12, fontWeight: "700", flex: 1 },
  riskLockedSub:    { color: "#92704e", fontSize: 11, lineHeight: 15 },
  riskLockedHint: {
    flexDirection: "row", alignItems: "center",
    paddingVertical: 7, paddingHorizontal: 10,
    borderRadius: 8, borderWidth: 1,
  },
  riskLockedHintText: { fontSize: 11, fontWeight: "600" },
  riskLockedCta:      { flexDirection: "row", alignItems: "center", gap: 4, marginTop: 2, alignSelf: "flex-start" },
  riskLockedCtaText:  { color: "#fbbf24", fontSize: 10, fontWeight: "800", letterSpacing: 1.5 },
});
