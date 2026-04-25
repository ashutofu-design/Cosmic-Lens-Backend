import { Feather } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useEffect, useState } from "react";
import {
  ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { CosmicBg } from "@/components/CosmicBg";
import { useUser } from "@/context/UserContext";
import { useT, type T } from "@/hooks/useT";
import { API_BASE, apiFetch } from "@/lib/apiConfig";

const PLANET_CLR: Record<string, string> = {
  Sun: "#f59e0b", Moon: "#94a3b8", Mars: "#ef4444", Mercury: "#10b981",
  Jupiter: "#facc15", Venus: "#ec4899", Saturn: "#a78bfa",
  Rahu: "#f97316", Ketu: "#fb923c",
};
const TREND_CLR: Record<string, string> = {
  up: "#22c55e", neutral: "#94a3b8", down: "#ef4444",
};
const AREA_ICON: Record<string, string> = {
  career: "💼", finance: "💰", health: "🌿",
  relationship: "💞", spirituality: "🕉️",
};

interface DashaInfo {
  planet: string; quality_tag: string; quality_score: number;
  owns_houses: number[]; sits_in_house: number | null;
  impact_by_area: Record<string, string[]>;
}
interface MonthCard {
  month_label: string; start: string; end: string;
  md: string; ad: string; pd: string;
  pd_start: string; pd_end: string; is_pd_change: boolean;
  month_score: number; overall: string;
  md_info: DashaInfo; ad_info: DashaInfo; pd_info: DashaInfo;
  outlook: { area: string; label: string; trend: "up" | "down" | "neutral";
             hits: string[]; summary: string }[];
  opportunities: string[];
  cautions: string[];
  remedy_focus: { planet: string; action: string };
}
interface FutureResponse {
  available: boolean;
  generated_at?: string;
  current_dasha?: { md: string; ad: string; pd: string;
                    ad_start: string; ad_end: string };
  months?: MonthCard[];
  error?: string;
  reason?: string;
}

function scoreColor(s: number): string {
  if (s >= 70) return "#22c55e";
  if (s >= 50) return "#fbbf24";
  return "#ef4444";
}

function localizeArea(area: string, t: T): string {
  switch (area) {
    case "career":       return t.smf_areaCareer;
    case "finance":      return t.smf_areaFinance;
    case "health":       return t.smf_areaHealth;
    case "relationship": return t.smf_areaRelationship;
    case "spirituality": return t.smf_areaSpirituality;
    default:             return area;
  }
}

export default function SixMonthFutureScreen() {
  const insets = useSafeAreaInsets();
  const { user, kundli } = useUser();
  const t = useT();
  const [data, setData] = useState<FutureResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!kundli) {
      setData({ available: false, reason: t.smf_kundliFirst });
      setLoading(false);
      return;
    }
    setLoading(true);
    apiFetch(`${API_BASE}/api/future-6months`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: user?.id, kundli }),
    })
      .then(r => r.json())
      .then((res: FutureResponse) => setData(res))
      .catch(e => setData({ available: false, error: String(e) }))
      .finally(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [kundli, user?.id]);

  return (
    <CosmicBg>
      {/* Header */}
      <View style={[s.topBar, { paddingTop: insets.top + 8 }]}>
        <Pressable onPress={() => router.back()} style={s.backBtn}>
          <View style={s.backCircle}>
            <Feather name="arrow-left" size={20} color="#e2e8f0" />
          </View>
        </Pressable>
        <Text style={s.title}>{t.smf_title}</Text>
        <View style={{ width: 36 }} />
      </View>

      <ScrollView
        contentContainerStyle={{ padding: 16, paddingTop: insets.top + 70, paddingBottom: 80 }}
        showsVerticalScrollIndicator={false}
      >
        {loading && (
          <View style={{ alignItems: "center", marginTop: 60 }}>
            <ActivityIndicator color="#a78bfa" />
            <Text style={{ color: "#94a3b8", marginTop: 12 }}>
              {t.smf_loadingMsg}
            </Text>
          </View>
        )}

        {!loading && data && !data.available && (
          <View style={s.errCard}>
            <Feather name="alert-circle" size={28} color="#f59e0b" />
            <Text style={{ color: "#fbbf24", marginTop: 8, fontWeight: "700" }}>
              {t.smf_unavailableTtl}
            </Text>
            <Text style={{ color: "#cbd5e1", marginTop: 6, textAlign: "center" }}>
              {data.reason || data.error || t.smf_tryAgain}
            </Text>
          </View>
        )}

        {!loading && data?.available && (
          <>
            {/* Current dasha summary */}
            {data.current_dasha && (
              <LinearGradient
                colors={["#1e1b4b", "#0f172a"]}
                style={s.headerCard}
              >
                <Text style={s.headerLabel}>{t.smf_activeChain}</Text>
                <View style={s.dashaRow}>
                  {(["md", "ad", "pd"] as const).map(k => {
                    const planet = data.current_dasha![k];
                    const label = k === "md" ? t.smf_lblMaha : k === "ad" ? t.smf_lblAntar : t.smf_lblPratyantar;
                    return (
                      <View key={k} style={s.dashaPill}>
                        <Text style={s.dashaPillLabel}>{label}</Text>
                        <Text style={[s.dashaPillPlanet, { color: PLANET_CLR[planet] || "#e2e8f0" }]}>
                          {planet}
                        </Text>
                      </View>
                    );
                  })}
                </View>
                <Text style={s.adWindow}>
                  {t.smf_adWindow}: {data.current_dasha.ad_start} → {data.current_dasha.ad_end}
                </Text>
              </LinearGradient>
            )}

            {/* Month cards */}
            {data.months?.map((m, i) => (
              <MonthCardView key={i} month={m} t={t} />
            ))}

            <Text style={{ color: "#64748b", textAlign: "center", marginTop: 14, fontSize: 11 }}>
              {t.smf_generated}: {data.generated_at?.replace("T", " ").slice(0, 16)} UTC
              {"\n"}{t.smf_pureEngine}
            </Text>
          </>
        )}
      </ScrollView>
    </CosmicBg>
  );
}

function MonthCardView({ month: m, t }: { month: MonthCard; t: T }) {
  const sc = scoreColor(m.month_score);

  return (
    <View style={s.monthCard}>
      {/* Header strip */}
      <View style={[s.monthHeader, { borderLeftColor: sc }]}>
        <View style={{ flex: 1 }}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
            <Text style={s.monthLabel}>{m.month_label}</Text>
            {m.is_pd_change && (
              <View style={s.pdChangeChip}>
                <Text style={s.pdChangeChipTxt}>{t.smf_pdShift}</Text>
              </View>
            )}
          </View>
          <Text style={s.monthRange}>{m.start.slice(5)} → {m.end.slice(5)}</Text>
        </View>
        <View style={{ alignItems: "flex-end" }}>
          <Text style={[s.monthScore, { color: sc }]}>{m.month_score}</Text>
          <Text style={[s.monthOverall, { color: sc }]}>{m.overall}</Text>
        </View>
      </View>

      {/* MD/AD/PD pills */}
      <View style={s.dashaTrioRow}>
        {([[t.smf_lblMD, m.md, m.md_info], [t.smf_lblAD, m.ad, m.ad_info],
           [t.smf_lblPD, m.pd, m.pd_info]] as const).map(([lbl, plnt, inf]) => (
          <View key={lbl} style={s.dashaTrio}>
            <Text style={s.dashaTrioLbl}>{lbl}</Text>
            <Text style={[s.dashaTrioPlnt, { color: PLANET_CLR[plnt] || "#e2e8f0" }]}>
              {plnt}
            </Text>
            <Text style={s.dashaTrioTag}>{inf?.quality_tag || "—"}</Text>
            {inf?.owns_houses?.length > 0 && (
              <Text style={s.dashaTrioRules}>
                {t.smf_rulesPrefix}: {inf.owns_houses.map(h => `${h}H`).join(", ")}
              </Text>
            )}
            {inf?.sits_in_house && (
              <Text style={s.dashaTrioSits}>
                {t.smf_sitsIn} {inf.sits_in_house}H
              </Text>
            )}
          </View>
        ))}
      </View>

      {/* PD window */}
      <Text style={s.pdWindow}>
        {t.smf_pdActiveWindow}: {m.pd_start} → {m.pd_end}
      </Text>

      {/* Life-area outlook */}
      {m.outlook?.length > 0 && (
        <View style={{ marginTop: 12 }}>
          <Text style={s.sectionH}>{t.smf_lifeAreas}</Text>
          {m.outlook.map((o, i) => (
            <View key={i} style={s.outlookRow}>
              <Text style={s.outlookIcon}>{AREA_ICON[o.area] || "•"}</Text>
              <View style={{ flex: 1 }}>
                <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
                  <Text style={[s.outlookLbl, { color: TREND_CLR[o.trend] }]}>
                    {localizeArea(o.area, t)}
                  </Text>
                  <Text style={[s.outlookTrend, { color: TREND_CLR[o.trend] }]}>
                    {o.trend.toUpperCase()}
                  </Text>
                </View>
                <Text style={s.outlookSum}>{o.summary}</Text>
                {o.hits?.length > 0 && (
                  <Text style={s.outlookHits}>
                    {t.smf_whyPrefix}: {o.hits.join(" · ")}
                  </Text>
                )}
              </View>
            </View>
          ))}
        </View>
      )}

      {/* Opportunities */}
      {m.opportunities?.length > 0 && (
        <View style={{ marginTop: 12 }}>
          <Text style={[s.sectionH, { color: "#22c55e" }]}>{t.smf_opportunities}</Text>
          {m.opportunities.map((o, i) => (
            <Text key={i} style={s.bullet}>• {o}</Text>
          ))}
        </View>
      )}

      {/* Cautions */}
      {m.cautions?.length > 0 && (
        <View style={{ marginTop: 12 }}>
          <Text style={[s.sectionH, { color: "#ef4444" }]}>{t.smf_cautions}</Text>
          {m.cautions.map((c, i) => (
            <Text key={i} style={s.bullet}>• {c}</Text>
          ))}
        </View>
      )}

      {/* Remedy of month */}
      {m.remedy_focus?.action && (
        <View style={s.remedyCard}>
          <Text style={s.remedyLbl}>
            {t.smf_remedyLabel} ({m.remedy_focus.planet}-{t.smf_remedyFocused})
          </Text>
          <Text style={s.remedyTxt}>{m.remedy_focus.action}</Text>
        </View>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  topBar: {
    position: "absolute", top: 0, left: 0, right: 0,
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: 14, zIndex: 10, height: 60,
  },
  backBtn: { padding: 4 },
  backCircle: {
    width: 36, height: 36, borderRadius: 18,
    backgroundColor: "rgba(15,23,42,0.7)",
    borderWidth: 1, borderColor: "rgba(167,139,250,0.3)",
    alignItems: "center", justifyContent: "center",
  },
  title: { color: "#e2e8f0", fontSize: 17, fontWeight: "700" },

  errCard: {
    backgroundColor: "#1e293b", padding: 24, borderRadius: 14,
    alignItems: "center", marginTop: 40,
  },

  headerCard: {
    borderRadius: 16, padding: 16, marginBottom: 16,
    borderWidth: 1, borderColor: "rgba(167,139,250,0.3)",
  },
  headerLabel: { color: "#a78bfa", fontSize: 12, fontWeight: "700",
                 textTransform: "uppercase", letterSpacing: 1, marginBottom: 10 },
  dashaRow: { flexDirection: "row", justifyContent: "space-around", gap: 8 },
  dashaPill: {
    flex: 1, backgroundColor: "rgba(15,23,42,0.6)", padding: 10,
    borderRadius: 10, alignItems: "center",
    borderWidth: 1, borderColor: "rgba(255,255,255,0.05)",
  },
  dashaPillLabel: { color: "#94a3b8", fontSize: 10, marginBottom: 2 },
  dashaPillPlanet: { fontSize: 16, fontWeight: "800" },
  adWindow: { color: "#cbd5e1", fontSize: 11, marginTop: 10, textAlign: "center" },

  monthCard: {
    backgroundColor: "rgba(15,23,42,0.85)", borderRadius: 14, padding: 14,
    marginBottom: 14, borderWidth: 1, borderColor: "rgba(167,139,250,0.15)",
  },
  monthHeader: {
    flexDirection: "row", alignItems: "center",
    paddingLeft: 10, borderLeftWidth: 4, marginBottom: 10,
  },
  monthLabel: { color: "#e2e8f0", fontSize: 16, fontWeight: "800" },
  monthRange: { color: "#94a3b8", fontSize: 11, marginTop: 2 },
  monthScore: { fontSize: 24, fontWeight: "800" },
  monthOverall: { fontSize: 11, fontWeight: "700" },
  pdChangeChip: {
    backgroundColor: "rgba(167,139,250,0.2)", paddingHorizontal: 6,
    paddingVertical: 2, borderRadius: 6,
  },
  pdChangeChipTxt: { color: "#c4b5fd", fontSize: 9, fontWeight: "700" },

  dashaTrioRow: { flexDirection: "row", gap: 6, marginBottom: 6 },
  dashaTrio: {
    flex: 1, backgroundColor: "rgba(30,41,59,0.6)", padding: 8,
    borderRadius: 8,
  },
  dashaTrioLbl: { color: "#64748b", fontSize: 9, fontWeight: "700" },
  dashaTrioPlnt: { fontSize: 14, fontWeight: "800", marginTop: 2 },
  dashaTrioTag: { color: "#94a3b8", fontSize: 9, marginTop: 2,
                  fontWeight: "700", textTransform: "uppercase" },
  dashaTrioRules: { color: "#cbd5e1", fontSize: 10, marginTop: 4 },
  dashaTrioSits: { color: "#a78bfa", fontSize: 10, marginTop: 1 },
  pdWindow: { color: "#94a3b8", fontSize: 10, fontStyle: "italic", marginTop: 4 },

  sectionH: {
    color: "#a78bfa", fontSize: 11, fontWeight: "700",
    textTransform: "uppercase", letterSpacing: 0.8, marginBottom: 8,
  },
  outlookRow: { flexDirection: "row", marginBottom: 10, gap: 8 },
  outlookIcon: { fontSize: 18 },
  outlookLbl: { fontSize: 13, fontWeight: "700", flex: 1 },
  outlookTrend: { fontSize: 10, fontWeight: "800" },
  outlookSum: { color: "#cbd5e1", fontSize: 12, marginTop: 2, lineHeight: 17 },
  outlookHits: { color: "#64748b", fontSize: 10, marginTop: 4, fontStyle: "italic" },

  bullet: { color: "#cbd5e1", fontSize: 12, marginBottom: 4, lineHeight: 17 },

  remedyCard: {
    backgroundColor: "rgba(245,158,11,0.1)", borderLeftWidth: 3,
    borderLeftColor: "#f59e0b", padding: 10, borderRadius: 8, marginTop: 12,
  },
  remedyLbl: { color: "#fbbf24", fontSize: 11, fontWeight: "700",
               textTransform: "uppercase", marginBottom: 4 },
  remedyTxt: { color: "#fde68a", fontSize: 12, lineHeight: 17 },
});
