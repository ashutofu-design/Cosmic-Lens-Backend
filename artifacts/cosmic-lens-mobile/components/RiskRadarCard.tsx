import { Feather } from "@expo/vector-icons";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { router } from "expo-router";
import * as Haptics from "expo-haptics";
import React, { useEffect, useState } from "react";
import { I18nManager, Pressable, StyleSheet, Text, View } from "react-native";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { fetchDailyLucky, type DailyLucky } from "@/lib/luckyAPI";

export const MONTHS_SHORT = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
export const fmtDate = (d: Date) => `${d.getDate()} ${MONTHS_SHORT[d.getMonth()]}`;

export type RiskLevel = "low" | "med" | "high";
export interface LuckyColor { name: string; emoji: string; hex: string; }

export interface DayForecast {
  date: Date;
  score: number;
  moonLon: number;
  moonSign: string;
  phase: string;
  summary: string;
  riskLevel:    RiskLevel;
  riskScore:    number;
  riskShort:    string;
  riskCategory: string;
  riskDetail:   string;
  riskDhyan:    string;
  riskAvoid:    string;
  riskKarna:    string;
  riskRemedy:   string;
  luckyNumbers: number[];
  luckyColor:   LuckyColor;
  bestTime:     string;
  avoidTime:    string;
}

const RISK_BY_LEVEL: Record<RiskLevel, {
  shorts:  string[];
  details: { cat: string; detail: string; dhyan: string; avoid: string; karna: string; remedy: string; }[];
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
        detail: "Aaj misunderstandings hone ke chances zyada hain. Important messages double-check karein, clarity rakhein.",
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
        detail: "Aaj arguments aur disputes hone ke chances bahut zyada hain. Confrontations avoid karein — silence is power aaj.",
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

export function scoreToRiskScore(score: number): number {
  return Math.round(Math.max(0, Math.min(10, (100 - score) / 7)));
}
export function scoreToRiskLevel(rs: number): RiskLevel {
  if (rs <= 3) return "low";
  if (rs <= 6) return "med";
  return "high";
}

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
  "10:30 AM — 12:45 PM", "8:00 AM — 10:15 AM", "4:30 PM — 6:30 PM",
  "11:00 AM — 1:15 PM", "9:00 AM — 11:00 AM", "5:00 PM — 7:00 PM",
  "7:30 AM — 9:45 AM",
];
const AVOID_TIME_SLOTS = [
  "3:15 PM — 5:00 PM", "1:00 PM — 2:30 PM", "7:00 PM — 8:30 PM",
  "2:30 PM — 4:00 PM", "12:30 PM — 2:00 PM", "8:00 PM — 9:30 PM",
  "1:45 PM — 3:15 PM",
];

function dayHash(dateMs: number): number { return Math.floor(dateMs / 86400000); }

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
  return AVOID_TIME_SLOTS[(dayHash(dateMs) + 2) % AVOID_TIME_SLOTS.length];
}

export function computeRisk(score: number, _dayIdx: number, date: Date) {
  const riskScore = scoreToRiskScore(score);
  const level     = scoreToRiskLevel(riskScore);
  const bucket    = RISK_BY_LEVEL[level];
  const dateMs    = date.getTime();
  // Content is selected by date hash (not array index) so the same calendar
  // date always renders the same risk copy across screens (forecast CTA preview
  // vs dasha-risk full card). _dayIdx is kept in the signature for backwards
  // compatibility but no longer drives content selection.
  const dh        = dayHash(dateMs);
  const shortLine = bucket.shorts[dh % bucket.shorts.length];
  const det       = bucket.details[dh % bucket.details.length];
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

// ── Cosmic Risk Radar Card ──────────────────────────────────────────────────
//   The single consolidated 8-section card that bundles every "next-24-hours"
//   signal: gauge, week chips, 24-hour breakdown (4 quadrants), upay, lucky
//   numbers, lucky color, best-time, avoid-time. Streak counter at top-right
//   increments once per UTC day via AsyncStorage and only renders when ≥ 2.
//
//   Premium gating: when `fullAccess=false`, only Day 1 (selected=0) is
//   unlocked; Days 2-7 show the upgrade card with a "Day 1 free hai" inner
//   tap fallback that bounces the user back to the unlocked day.
const FREE_DAYS = 1;

export function RiskRadarCard({
  days, selected, onSelect, fullAccess,
}: {
  days: DayForecast[]; selected: number; onSelect: (i: number) => void; fullAccess: boolean;
}) {
  const C = useC();
  const { user, kundli } = useUser();

  // ── Personalised "Aaj Ka Shubh Ank" + "Aaj Ka Shubh Rang" ────────────
  // Fetched from /api/lucky/today using the user's mool ank + janma
  // nakshatra. NEVER falls back to fake values — when missing the hero tile
  // shows a friendly Hinglish prompt.
  const [dailyLucky, setDailyLucky] = useState<DailyLucky | null>(null);
  const [luckyError, setLuckyError] = useState<string | null>(null);
  const [luckyLoading, setLuckyLoading] = useState(false);

  useEffect(() => {
    if (!user?.id || !user?.api_key || !kundli) {
      setDailyLucky(null);
      setLuckyError(null);
      return;
    }
    let cancelled = false;
    setLuckyLoading(true);
    fetchDailyLucky(user.id, user.api_key)
      .then(res => {
        if (cancelled) return;
        if (res.ok) {
          setDailyLucky(res);
          setLuckyError(null);
        } else {
          setDailyLucky(null);
          setLuckyError(res.message);
        }
      })
      .finally(() => { if (!cancelled) setLuckyLoading(false); });
    return () => { cancelled = true; };
  }, [user?.id, user?.api_key, kundli]);

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

  let safestIdx = 0, riskiestIdx = 0;
  days.forEach((d, i) => {
    if (d.riskScore < days[safestIdx].riskScore)   safestIdx   = i;
    if (d.riskScore > days[riskiestIdx].riskScore) riskiestIdx = i;
  });

  const isLocked   = !fullAccess && selected >= FREE_DAYS;
  const levelColor =
    sel.riskLevel === "low" ? "#4ade80" :
    sel.riskLevel === "med" ? "#fbbf24" : "#ef4444";
  const levelLabel =
    sel.riskLevel === "low" ? "LOW" :
    sel.riskLevel === "med" ? "MEDIUM" : "HIGH";
  const markerPct  = `${(sel.riskScore / 10) * 100}%` as `${number}%`;

  return (
    <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border }]}>
      {/* Header */}
      <View style={s.head}>
        <View style={s.titleRow}>
          <Feather name="alert-triangle" size={13} color="#fbbf24" />
          <Text style={[s.title, { color: C.text }]}>Cosmic Risk Radar</Text>
        </View>
        <View style={s.headRight}>
          {streak >= 2 && (
            <View style={s.streakPill}>
              <Text style={s.streakPillText}>🔥 {streak}</Text>
            </View>
          )}
          <Text style={[s.headHint, { color: C.textDim }]}>Day {selected + 1} of 7</Text>
        </View>
      </View>

      {/* Week highlights */}
      <View style={s.chipsRow}>
        <Pressable
          onPress={() => { onSelect(safestIdx); Haptics.selectionAsync(); }}
          style={[s.chip, { backgroundColor: "rgba(74,222,128,0.10)", borderColor: "rgba(74,222,128,0.30)" }]}
        >
          <Text style={[s.chipLabel, { color: "#4ade80" }]}>SAFEST</Text>
          <Text style={[s.chipDay,   { color: C.text }]}>{fmtDate(days[safestIdx].date)}</Text>
        </Pressable>
        <Pressable
          onPress={() => { onSelect(riskiestIdx); Haptics.selectionAsync(); }}
          style={[s.chip, { backgroundColor: "rgba(239,68,68,0.10)", borderColor: "rgba(239,68,68,0.30)" }]}
        >
          <Text style={[s.chipLabel, { color: "#ef4444" }]}>CHALLENGING</Text>
          <Text style={[s.chipDay,   { color: C.text }]}>{fmtDate(days[riskiestIdx].date)}</Text>
        </Pressable>
      </View>

      {isLocked ? (
        <Pressable
          style={[s.lockedCard, { backgroundColor: "rgba(251,191,36,0.06)", borderColor: "rgba(251,191,36,0.30)" }]}
          onPress={() => router.push("/onboarding")}
        >
          <View style={s.lockedTop}>
            <Feather name="lock" size={14} color="#fbbf24" />
            <Text style={s.lockedTitle}>{fmtDate(sel.date)} ka radar locked</Text>
          </View>
          <Text style={s.lockedSub}>
            Aane wale dino ka full radar — risk level, kya karna/avoid karna,
            lucky numbers, best time aur upay — Premium se unlock karein.
          </Text>
          <Pressable
            onPress={(e) => { e.stopPropagation?.(); onSelect(0); Haptics.selectionAsync(); }}
            style={[s.lockedHint, { borderColor: C.border }]}
          >
            <Text style={[s.lockedHintText, { color: C.textMuted }]}>
              💡 Day 1 free hai — preview ke liye tap karein
            </Text>
          </Pressable>
          <View style={s.lockedCta}>
            <Text style={s.lockedCtaText}>UNLOCK PREMIUM</Text>
            <Feather name={I18nManager.isRTL ? "arrow-left" : "arrow-right"} size={11} color="#fbbf24" />
          </View>
        </Pressable>
      ) : (
        <>
          {/* Gauge */}
          <View style={s.gaugeHead}>
            <Text style={[s.gaugeMicro, { color: C.textMuted }]}>RISK LEVEL</Text>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
              <Text style={[s.gaugeLevel, { color: levelColor   }]}>{levelLabel}</Text>
              <Text style={[s.gaugeValue, { color: C.textMuted  }]}>{sel.riskScore}/10</Text>
            </View>
          </View>
          <View style={s.gaugeTrack}>
            <View style={[s.gaugeSeg, { backgroundColor: "rgba(74,222,128,0.22)",  borderTopLeftRadius: 4, borderBottomLeftRadius: 4 }]} />
            <View style={[s.gaugeSeg, { backgroundColor: "rgba(251,191,36,0.22)" }]} />
            <View style={[s.gaugeSeg, { backgroundColor: "rgba(239,68,68,0.22)",   borderTopRightRadius: 4, borderBottomRightRadius: 4 }]} />
            <View style={[s.gaugeMarker, { left: markerPct, backgroundColor: levelColor, shadowColor: levelColor }]} />
          </View>
          <View style={s.gaugeScale}>
            <Text style={[s.gaugeScaleText, { color: C.textDim }]}>Low</Text>
            <Text style={[s.gaugeScaleText, { color: C.textDim }]}>Med</Text>
            <Text style={[s.gaugeScaleText, { color: C.textDim }]}>High</Text>
          </View>

          {/* Generic warning */}
          <View style={[s.shortRow, { borderColor: C.border }]}>
            <Text style={s.shortIcon}>💬</Text>
            <Text style={[s.shortText, { color: C.text }]}>{sel.riskShort}</Text>
          </View>

          {/* 24-hour breakdown */}
          <View style={s.bdHead}>
            <Feather name="clock" size={11} color={C.textMuted} />
            <Text style={[s.bdHeadText, { color: C.textMuted }]}>
              {selected === 0 ? "AAJ KE 24 GHANTE" : `${fmtDate(sel.date).toUpperCase()} KE 24 GHANTE`}
            </Text>
          </View>

          <View style={[s.bdRow, { backgroundColor: `${levelColor}10`, borderColor: `${levelColor}30` }]}>
            <View style={[s.bdIconBox, { backgroundColor: `${levelColor}22` }]}>
              <Feather name="alert-triangle" size={14} color={levelColor} />
            </View>
            <View style={s.bdText}>
              <Text style={[s.bdLabel, { color: levelColor }]}>KYA RISK HAI</Text>
              <Text style={[s.bdBody,  { color: C.text     }]}>{sel.riskDetail}</Text>
            </View>
          </View>

          <View style={[s.bdRow, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <View style={[s.bdIconBox, { backgroundColor: "rgba(96,165,250,0.18)" }]}>
              <Feather name="eye" size={14} color="#60a5fa" />
            </View>
            <View style={s.bdText}>
              <Text style={[s.bdLabel, { color: "#60a5fa" }]}>KYA DHYAN RAKHNA HAI</Text>
              <Text style={[s.bdBody,  { color: C.text    }]}>{sel.riskDhyan}</Text>
            </View>
          </View>

          <View style={[s.bdRow, { backgroundColor: "rgba(239,68,68,0.08)", borderColor: "rgba(239,68,68,0.25)" }]}>
            <View style={[s.bdIconBox, { backgroundColor: "rgba(239,68,68,0.22)" }]}>
              <Feather name="x-circle" size={14} color="#ef4444" />
            </View>
            <View style={s.bdText}>
              <Text style={[s.bdLabel, { color: "#ef4444" }]}>KYA AVOID KARNA HAI</Text>
              <Text style={[s.bdBody,  { color: C.text    }]}>{sel.riskAvoid}</Text>
            </View>
          </View>

          <View style={[s.bdRow, { backgroundColor: "rgba(74,222,128,0.08)", borderColor: "rgba(74,222,128,0.25)" }]}>
            <View style={[s.bdIconBox, { backgroundColor: "rgba(74,222,128,0.22)" }]}>
              <Feather name="check-circle" size={14} color="#4ade80" />
            </View>
            <View style={s.bdText}>
              <Text style={[s.bdLabel, { color: "#4ade80" }]}>KYA KARNA HAI</Text>
              <Text style={[s.bdBody,  { color: C.text    }]}>{sel.riskKarna}</Text>
            </View>
          </View>

          {/* Mini upay */}
          <View style={[s.remedyRow, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <Text style={s.remedyIcon}>🪔</Text>
            <View style={{ flex: 1 }}>
              <Text style={[s.remedyLabel, { color: C.textMuted }]}>UPAY</Text>
              <Text style={[s.remedyText,  { color: C.text      }]}>{sel.riskRemedy}</Text>
            </View>
          </View>

          {/* ── Personalised "Aaj Ka Shubh Ank" + "Aaj Ka Shubh Rang" ───── */}
          {selected === 0 && dailyLucky ? (
            <View style={[s.shubhCard, {
              backgroundColor: `${dailyLucky.shubh_rang_hex}14`,
              borderColor: `${dailyLucky.shubh_rang_hex}55`,
            }]}>
              <View style={s.shubhRow}>
                <View style={s.shubhAnkBox}>
                  <Text style={[s.shubhMicro, { color: C.textMuted }]}>AAJ KA SHUBH ANK</Text>
                  <View style={[s.shubhAnkBadge, {
                    borderColor: dailyLucky.shubh_rang_hex,
                    backgroundColor: `${dailyLucky.shubh_rang_hex}22`,
                  }]}>
                    <Text style={[s.shubhAnkText, { color: C.text }]}>{dailyLucky.shubh_ank}</Text>
                  </View>
                </View>
                <View style={s.shubhDivider} />
                <View style={s.shubhRangBox}>
                  <Text style={[s.shubhMicro, { color: C.textMuted }]}>AAJ KA SHUBH RANG</Text>
                  <View style={s.shubhRangRow}>
                    <View style={[s.shubhSwatch, {
                      backgroundColor: dailyLucky.shubh_rang_hex,
                      borderColor: dailyLucky.shubh_rang_hex === "#f3f4f6"
                        ? "rgba(255,255,255,0.3)" : "transparent",
                    }]} />
                    <Text style={[s.shubhRangName, { color: C.text }]}>{dailyLucky.shubh_rang_name}</Text>
                  </View>
                </View>
              </View>
              <Text style={[s.shubhReason, { color: C.textMuted }]}>
                {dailyLucky.reasoning_hinglish}
              </Text>
              <Text style={[s.shubhFooter, { color: C.textDim }]}>
                Powered by Advanced Cosmic Intelligence
              </Text>
            </View>
          ) : selected === 0 && luckyLoading ? (
            <View style={[s.shubhCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <Text style={[s.shubhReason, { color: C.textMuted, textAlign: "center" }]}>
                Aapka shubh ank aur rang calculate ho raha hai…
              </Text>
            </View>
          ) : selected === 0 && (luckyError || !user || !kundli) ? (
            <Pressable
              onPress={() => router.push("/onboarding")}
              style={[s.shubhCard, { backgroundColor: C.bgCard, borderColor: C.border }]}
            >
              <Text style={[s.shubhMicro, { color: C.textMuted, marginBottom: 6 }]}>
                AAJ KA SHUBH ANK + RANG
              </Text>
              <Text style={[s.shubhReason, { color: C.text }]}>
                {!user || !kundli
                  ? "Apni kundli banayein — aapke janm ke nakshatra se aaj ka personal shubh ank aur rang dekhein."
                  : luckyError ?? "Lucky details abhi available nahi hain."}
              </Text>
              {(!user || !kundli) && (
                <Text style={[s.shubhFooter, { color: "#fbbf24", marginTop: 6 }]}>
                  KUNDLI BANAYEIN →
                </Text>
              )}
            </Pressable>
          ) : (
            <View style={[s.shubhCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <Text style={[s.shubhMicro, { color: C.textMuted, marginBottom: 4 }]}>
                AAJ KA SHUBH ANK + RANG
              </Text>
              <Text style={[s.shubhReason, { color: C.textMuted }]}>
                Personalised shubh ank aur rang sirf "Aaj" ke liye dikhte hain — Day 1 par tap karein.
              </Text>
            </View>
          )}

          <View style={s.luckyGrid}>
            <View style={[s.luckyTile, { backgroundColor: "rgba(74,222,128,0.08)", borderColor: "rgba(74,222,128,0.25)" }]}>
              <Text style={[s.luckyTileLabel, { color: "#4ade80" }]}>⏰ BEST TIME</Text>
              <Text style={[s.luckyTimeText, { color: C.text }]}>{sel.bestTime}</Text>
            </View>
            <View style={[s.luckyTile, { backgroundColor: "rgba(239,68,68,0.08)", borderColor: "rgba(239,68,68,0.25)" }]}>
              <Text style={[s.luckyTileLabel, { color: "#ef4444" }]}>🚫 AVOID TIME</Text>
              <Text style={[s.luckyTimeText, { color: C.text }]}>{sel.avoidTime}</Text>
            </View>
          </View>
        </>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  card: { borderRadius: 14, borderWidth: 1, padding: 14, gap: 12 },
  head: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  titleRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  title:    { fontSize: 14, fontWeight: "800", letterSpacing: 0.3 },
  headRight: { flexDirection: "row", alignItems: "center", gap: 8 },
  headHint:  { fontSize: 10, fontWeight: "600", letterSpacing: 1 },

  streakPill: {
    backgroundColor: "rgba(251,146,60,0.14)",
    borderWidth: 1, borderColor: "rgba(251,146,60,0.40)",
    paddingHorizontal: 7, paddingVertical: 2, borderRadius: 10,
  },
  streakPillText: { color: "#fb923c", fontSize: 10, fontWeight: "800", letterSpacing: 0.4 },

  chipsRow: { flexDirection: "row", gap: 8 },
  chip:     { flex: 1, borderRadius: 10, borderWidth: 1, paddingVertical: 8, paddingHorizontal: 10, gap: 2 },
  chipLabel:{ fontSize: 9, fontWeight: "800", letterSpacing: 1.2 },
  chipDay:  { fontSize: 12, fontWeight: "700" },

  gaugeHead: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  gaugeMicro:{ fontSize: 10, fontWeight: "800", letterSpacing: 1.4 },
  gaugeLevel:{ fontSize: 12, fontWeight: "800", letterSpacing: 1 },
  gaugeValue:{ fontSize: 11, fontWeight: "700" },
  gaugeTrack:{ flexDirection: "row", height: 8, borderRadius: 4, overflow: "visible", position: "relative" },
  gaugeSeg:  { flex: 1, height: 8 },
  gaugeMarker: {
    position: "absolute", top: -3, width: 14, height: 14, borderRadius: 7,
    marginLeft: -7, shadowOpacity: 0.8, shadowRadius: 6, shadowOffset: { width: 0, height: 0 }, elevation: 4,
  },
  gaugeScale: { flexDirection: "row", justifyContent: "space-between", marginTop: 2 },
  gaugeScaleText: { fontSize: 9, fontWeight: "600", letterSpacing: 1 },

  shortRow: {
    flexDirection: "row", alignItems: "center", gap: 8,
    paddingVertical: 8, paddingHorizontal: 10, borderRadius: 8, borderWidth: 1,
  },
  shortIcon: { fontSize: 13 },
  shortText: { flex: 1, fontSize: 12, fontWeight: "600", lineHeight: 16 },

  bdHead:     { flexDirection: "row", alignItems: "center", gap: 6, marginTop: 4 },
  bdHeadText: { fontSize: 10, fontWeight: "800", letterSpacing: 1.4 },
  bdRow: {
    flexDirection: "row", alignItems: "flex-start", gap: 10,
    padding: 10, borderRadius: 10, borderWidth: 1,
  },
  bdIconBox: {
    width: 28, height: 28, borderRadius: 8,
    alignItems: "center", justifyContent: "center", flexShrink: 0,
  },
  bdText:  { flex: 1, gap: 3 },
  bdLabel: { fontSize: 9,  fontWeight: "800", letterSpacing: 1.2 },
  bdBody:  { fontSize: 12, fontWeight: "500", lineHeight: 17 },

  remedyRow: {
    flexDirection: "row", alignItems: "center", gap: 10,
    padding: 10, borderRadius: 10, borderWidth: 1,
  },
  remedyIcon:  { fontSize: 18 },
  remedyLabel: { fontSize: 9,  fontWeight: "800", letterSpacing: 1.4, marginBottom: 2 },
  remedyText:  { fontSize: 12, fontWeight: "600", lineHeight: 16 },

  luckyGrid: { flexDirection: "row", gap: 8 },
  luckyTile: {
    flex: 1, borderRadius: 10, borderWidth: 1,
    paddingVertical: 10, paddingHorizontal: 10, gap: 8,
    minHeight: 64, justifyContent: "space-between",
  },
  luckyTileLabel: { fontSize: 9, fontWeight: "800", letterSpacing: 1.2 },
  luckyNumRow:    { flexDirection: "row", gap: 6, flexWrap: "wrap" },
  luckyNumPill: {
    minWidth: 28, paddingHorizontal: 6, paddingVertical: 3,
    borderRadius: 6, borderWidth: 1, alignItems: "center",
    backgroundColor: "rgba(251,191,36,0.10)",
  },
  luckyNumText: { fontSize: 12, fontWeight: "800", letterSpacing: 0.5 },
  luckyColorRow:    { flexDirection: "row", alignItems: "center", gap: 8 },
  luckyColorSwatch: { width: 20, height: 20, borderRadius: 10, borderWidth: 1 },
  luckyColorName:   { fontSize: 13, fontWeight: "700" },
  luckyTimeText:    { fontSize: 12, fontWeight: "700", letterSpacing: 0.3 },

  // ── Personalised "Aaj Ka Shubh Ank" + "Aaj Ka Shubh Rang" hero card ──
  shubhCard: {
    borderRadius: 12, borderWidth: 1, padding: 12, gap: 10,
  },
  shubhRow: {
    flexDirection: "row", alignItems: "stretch",
  },
  shubhAnkBox:  { flex: 1, alignItems: "flex-start", gap: 6 },
  shubhRangBox: { flex: 1, alignItems: "flex-start", gap: 6, paddingLeft: 12 },
  shubhDivider: { width: 1, backgroundColor: "rgba(255,255,255,0.10)" },
  shubhMicro:   { fontSize: 9, fontWeight: "800", letterSpacing: 1.2 },
  shubhAnkBadge: {
    width: 56, height: 56, borderRadius: 28, borderWidth: 2,
    alignItems: "center", justifyContent: "center",
  },
  shubhAnkText: { fontSize: 26, fontWeight: "900", letterSpacing: 0.5 },
  shubhRangRow: { flexDirection: "row", alignItems: "center", gap: 10, paddingTop: 6 },
  shubhSwatch:  { width: 36, height: 36, borderRadius: 18, borderWidth: 1 },
  shubhRangName:{ fontSize: 16, fontWeight: "800" },
  shubhReason:  { fontSize: 12, fontWeight: "500", lineHeight: 17 },
  shubhFooter:  { fontSize: 9, fontWeight: "700", letterSpacing: 1.2, textAlign: "right" },

  lockedCard:     { borderRadius: 10, borderWidth: 1, padding: 12, gap: 8 },
  lockedTop:      { flexDirection: "row", alignItems: "center", gap: 8 },
  lockedTitle:    { color: "#fbbf24", fontSize: 12, fontWeight: "700", flex: 1 },
  lockedSub:      { color: "#92704e", fontSize: 11, lineHeight: 15 },
  lockedHint: {
    flexDirection: "row", alignItems: "center",
    paddingVertical: 7, paddingHorizontal: 10,
    borderRadius: 8, borderWidth: 1,
  },
  lockedHintText: { fontSize: 11, fontWeight: "600" },
  lockedCta:      { flexDirection: "row", alignItems: "center", gap: 4, marginTop: 2, alignSelf: "flex-start" },
  lockedCtaText:  { color: "#fbbf24", fontSize: 10, fontWeight: "800", letterSpacing: 1.5 },
});
