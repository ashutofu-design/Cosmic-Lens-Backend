import { LinearGradient } from "expo-linear-gradient";
import React from "react";
import { StyleSheet, Text, View } from "react-native";
import { MILAN_KOOT_DISPLAY, type MilanKootKey } from "@/lib/milanKootDisplay";
import type { MilanResultScreenCopy } from "@/lib/milanResultCopyI18n";

const HIGHLIGHT_KEYS: MilanKootKey[] = ["nadi", "tara", "bhakut", "yoni"];

export type MilanGunKootScores = Record<
  MilanKootKey,
  { score: number; max: number }
>;

export function ashtakootToGunScores(r: {
  varna: { score: number; max: number };
  vasya: { score: number; max: number };
  tara: { score: number; max: number };
  yoni: { score: number; max: number };
  maitri: { score: number; max: number };
  gana: { score: number; max: number };
  bhakut: { score: number; max: number };
  nadi: { score: number; max: number };
}): MilanGunKootScores {
  return {
    varna: { score: r.varna.score, max: r.varna.max },
    vasya: { score: r.vasya.score, max: r.vasya.max },
    tara: { score: r.tara.score, max: r.tara.max },
    yoni: { score: r.yoni.score, max: r.yoni.max },
    maitri: { score: r.maitri.score, max: r.maitri.max },
    gana: { score: r.gana.score, max: r.gana.max },
    bhakut: { score: r.bhakut.score, max: r.bhakut.max },
    nadi: { score: r.nadi.score, max: r.nadi.max },
  };
}

/** Map `/api/kundli-milan` koots array → breakdown UI scores (server source of truth). */
export function kootsToGunScores(
  koots: { key: string; score: number; max: number }[] | null | undefined,
): MilanGunKootScores | null {
  if (!Array.isArray(koots) || koots.length === 0) return null;
  const byKey = Object.fromEntries(koots.map(k => [k.key, k]));
  const keys: MilanKootKey[] = [
    "varna", "vasya", "tara", "yoni", "maitri", "gana", "bhakut", "nadi",
  ];
  const scores = {} as MilanGunKootScores;
  for (const key of keys) {
    const item = byKey[key];
    if (!item) return null;
    scores[key] = { score: item.score, max: item.max };
  }
  return scores;
}

type RowView = {
  key: MilanKootKey;
  modernTitle: string;
  classicalLabel: string;
  emoji: string;
  color: string;
  score: number;
  max: number;
  pct: number;
};

function buildRows(scores: MilanGunKootScores, copy: MilanResultScreenCopy): RowView[] {
  return MILAN_KOOT_DISPLAY.map(def => {
    const item = scores[def.key];
    const score = item?.score ?? 0;
    const max = item?.max ?? 1;
    const pct = Math.round(Math.min(100, (score / max) * 100));
    const modernTitle = copy.kootTitles[def.key];
    const classicalLabel = copy.kootClassical[def.key];
    return { ...def, modernTitle, classicalLabel, score, max, pct };
  });
}

function gunGrade(total: number, copy: MilanResultScreenCopy): { label: string; col: string } {
  if (total >= 32) return { label: copy.gunGrades.excellent, col: "#38bdf8" };
  if (total >= 27) return { label: copy.gunGrades.veryGood, col: "#60a5fa" };
  if (total >= 21) return { label: copy.gunGrades.average, col: "#94a3b8" };
  if (total >= 18) return { label: copy.gunGrades.belowAvg, col: "#78909c" };
  return { label: copy.gunGrades.lowMatch, col: "#64748b" };
}

const GUN_ACCENT = "#38bdf8";

function GunBar({
  pct,
  color,
  isDark,
  locked,
}: {
  pct: number;
  color: string;
  isDark: boolean;
  locked: boolean;
}) {
  const width = locked ? 0 : `${pct}%`;
  return (
    <View
      style={[
        st.barTrack,
        { backgroundColor: isDark ? "rgba(255,255,255,0.07)" : "rgba(99,102,241,0.12)" },
      ]}
    >
      {!locked && pct > 0 ? (
        <LinearGradient
          colors={[color, `${color}99`]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={[st.barFill, { width: width as `${number}%` }]}
        />
      ) : null}
    </View>
  );
}

type Props = {
  scores: MilanGunKootScores | null;
  total: number | null;
  isDark: boolean;
  textColor: string;
  mutedColor: string;
  copy: MilanResultScreenCopy;
};

export function MilanGunBreakdown({ scores, total, isDark, textColor, mutedColor, copy }: Props) {
  const locked = !scores;
  const empty: MilanGunKootScores = {
    varna: { score: 0, max: 1 },
    vasya: { score: 0, max: 2 },
    tara: { score: 0, max: 3 },
    yoni: { score: 0, max: 4 },
    maitri: { score: 0, max: 5 },
    gana: { score: 0, max: 6 },
    bhakut: { score: 0, max: 7 },
    nadi: { score: 0, max: 8 },
  };
  const rows = buildRows(scores ?? empty, copy);
  const grade = total != null ? gunGrade(total, copy) : null;
  const highlightSet = new Set<string>(HIGHLIGHT_KEYS);

  const cardBg = isDark ? "rgba(14,116,144,0.06)" : "rgba(240,249,255,0.95)";
  const cardBorder = isDark ? "rgba(56,189,248,0.22)" : "rgba(14,165,233,0.18)";

  return (
    <View style={[st.card, { backgroundColor: cardBg, borderColor: cardBorder }]}>
      <View style={st.headRow}>
        <View style={{ flex: 1 }}>
          <View style={st.badgeRow}>
            <View style={[st.refBadge, { backgroundColor: isDark ? "rgba(56,189,248,0.14)" : "rgba(14,165,233,0.1)", borderColor: isDark ? "rgba(56,189,248,0.35)" : "rgba(14,165,233,0.25)" }]}>
              <Text style={[st.refBadgeTxt, { color: isDark ? "#7dd3fc" : "#0369a1" }]}>{copy.gunReference}</Text>
            </View>
          </View>
          <Text style={[st.sectionTitle, { color: textColor }]}>{copy.gunTitle}</Text>
          <Text style={[st.sectionSub, { color: mutedColor }]}>{copy.gunSubtitle}</Text>
        </View>
        {grade && total != null ? (
          <View style={[st.totalPill, { borderColor: `${grade.col}55`, backgroundColor: `${grade.col}18` }]}>
            <Text style={[st.totalNum, { color: grade.col }]}>{total}/36</Text>
            <Text style={[st.totalLbl, { color: grade.col }]}>{grade.label}</Text>
          </View>
        ) : null}
      </View>

      {!locked ? (
        <View style={st.highlightRow}>
          {rows
            .filter(r => highlightSet.has(r.key))
            .map(r => (
              <View
                key={r.key}
                style={[
                  st.highlightChip,
                  {
                    backgroundColor: isDark ? `${r.color}14` : `${r.color}10`,
                    borderColor: `${r.color}35`,
                  },
                ]}
              >
                <Text style={{ fontSize: 11 }}>{r.emoji}</Text>
                <Text style={[st.highlightTxt, { color: isDark ? GUN_ACCENT : "#0284c7" }]} numberOfLines={1}>
                  {r.pct}%
                </Text>
              </View>
            ))}
        </View>
      ) : (
        <Text style={[st.lockHint, { color: mutedColor }]}>{copy.gunLockHint}</Text>
      )}

      <View style={{ gap: 10, marginTop: 4 }}>
        {rows.map(row => (
          <View key={row.key} style={{ gap: 5 }}>
            <View style={st.rowTop}>
              <View style={st.rowLabel}>
                <Text style={{ fontSize: 13 }}>{row.emoji}</Text>
                <View style={{ flex: 1 }}>
                  <Text style={[st.rowTitle, { color: textColor }]}>{row.modernTitle}</Text>
                  <Text style={[st.rowClassical, { color: mutedColor }]}>{row.classicalLabel}</Text>
                </View>
              </View>
              <Text style={[st.rowPct, { color: locked ? mutedColor : isDark ? "#bae6fd" : "#0369a1" }]}>
                {locked ? "—" : `${row.pct}%`}
              </Text>
            </View>
            <GunBar pct={row.pct} color={GUN_ACCENT} isDark={isDark} locked={locked} />
          </View>
        ))}
      </View>
    </View>
  );
}

const st = StyleSheet.create({
  card: { borderRadius: 18, borderWidth: 1, padding: 14, gap: 10 },
  badgeRow: { flexDirection: "row", marginBottom: 4 },
  refBadge: { borderWidth: 1, borderRadius: 6, paddingHorizontal: 7, paddingVertical: 2 },
  refBadgeTxt: { fontSize: 8, fontFamily: "Nunito_800ExtraBold", letterSpacing: 0.8 },
  headRow: { flexDirection: "row", alignItems: "flex-start", gap: 10 },
  sectionTitle: { fontSize: 14, fontFamily: "Nunito_800ExtraBold", letterSpacing: 0.2 },
  sectionSub: { fontSize: 10, fontFamily: "Nunito_500Medium", marginTop: 2, lineHeight: 14 },
  totalPill: { borderWidth: 1, borderRadius: 12, paddingHorizontal: 10, paddingVertical: 6, alignItems: "center" },
  totalNum: { fontSize: 15, fontFamily: "Nunito_800ExtraBold" },
  totalLbl: { fontSize: 8, fontFamily: "Nunito_700Bold", letterSpacing: 0.4, marginTop: 1 },
  highlightRow: { flexDirection: "row", flexWrap: "wrap", gap: 6 },
  highlightChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  highlightTxt: { fontSize: 10, fontFamily: "Nunito_800ExtraBold" },
  lockHint: { fontSize: 10, fontFamily: "Nunito_500Medium", lineHeight: 15 },
  rowTop: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: 8 },
  rowLabel: { flexDirection: "row", alignItems: "center", gap: 8, flex: 1 },
  rowTitle: { fontSize: 12, fontFamily: "Nunito_700Bold" },
  rowClassical: { fontSize: 9, fontFamily: "Nunito_500Medium", marginTop: 1 },
  rowPct: { fontSize: 13, fontFamily: "Nunito_800ExtraBold", minWidth: 40, textAlign: "right" },
  barTrack: { height: 6, borderRadius: 3, overflow: "hidden" },
  barFill: { height: 6, borderRadius: 3 },
});
