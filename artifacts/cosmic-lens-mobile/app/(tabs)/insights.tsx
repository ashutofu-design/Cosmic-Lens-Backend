import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  Animated,
  Easing,
  Platform,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { CosmicBg } from "@/components/CosmicBg";
import { FadeInView, staggerDelay } from "@/components/motion/FadeInView";
import {
  LiveDashaProgress,
  LiveHeroGlow,
  LiveHourglass,
  LiveNowBadge,
  LivePlanetEmoji,
  LiveTrendArrow,
  pdElapsedPct,
} from "@/components/motion/FutureLiveMotion";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import {
  buildAreaRows,
  buildFocusList,
  buildMainInsight,
  buildPdSummary,
  buildPeriodMeaning,
  trendLabel,
} from "@/lib/futureTimelineCopy";
import { getT } from "@/lib/i18n";
import {
  computeProInsight,
  pName,
  type ProInsight,
  type Trend,
} from "@/lib/proInsightEngine";

const F = {
  regular: "Nunito_400Regular",
  medium:  "Nunito_500Medium",
  semi:    "Nunito_600SemiBold",
  bold:    "Nunito_700Bold",
  extra:   "Nunito_800ExtraBold",
} as const;

const PLANET_CLR: Record<string, string> = {
  Sun: "#f59e0b", Moon: "#94a3b8", Mars: "#ef4444", Mercury: "#10b981",
  Jupiter: "#facc15", Venus: "#ec4899", Saturn: "#a78bfa",
  Rahu: "#f59e0b", Ketu: "#fb923c",
};

const TREND_AREAS = [
  { key: "career" as const, icon: "💼", color: "#f59e0b" },
  { key: "relationship" as const, icon: "💞", color: "#ec4899" },
  { key: "finance" as const, icon: "💰", color: "#4ade80" },
];

function formatDate(d: Date | null): string {
  if (!d) return "";
  return `${d.toLocaleString("default", { month: "short" })} ${d.getDate()}, ${d.getFullYear()}`;
}

function fmtPDDate(d: Date): string {
  return `${String(d.getDate()).padStart(2, "0")}/${String(d.getMonth() + 1).padStart(2, "0")}/${d.getFullYear().toString().slice(2)}`;
}

function trendColor(trend: Trend): string {
  if (trend === "UP") return "#4ade80";
  if (trend === "DOWN") return "#ef4444";
  return "#fbbf24";
}

function PulsingSectionDot({ color }: { color: string }) {
  const pulse = useRef(new Animated.Value(0)).current;
  useEffect(() => {
    const anim = Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 1, duration: 1100, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 0, duration: 1100, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ]),
    );
    anim.start();
    return () => anim.stop();
  }, [pulse]);
  const scale = pulse.interpolate({ inputRange: [0, 1], outputRange: [1, 1.5] });
  const opacity = pulse.interpolate({ inputRange: [0, 1], outputRange: [0.6, 1] });
  return (
    <Animated.View style={[s.sectionDot, { backgroundColor: color, opacity, transform: [{ scale }] }]} />
  );
}

function SectionCard({
  title,
  children,
  accent,
}: {
  title: string;
  children: React.ReactNode;
  accent?: string;
}) {
  const C = useC();
  return (
    <View style={[s.sectionCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
      <View style={s.sectionHeader}>
        {accent ? <PulsingSectionDot color={accent} /> : null}
        <Text style={[s.sectionTitle, { color: C.isDark ? C.textMuted : "#334155" }]}>{title}</Text>
      </View>
      {children}
    </View>
  );
}

export default function InsightsScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const { kundli, moonData, language } = useUser();
  const t = getT(language);
  const androidSB = StatusBar.currentHeight ?? 24;
  const topPad = Platform.OS === "web" ? 67 : Platform.OS === "android" ? Math.max(insets.top, androidSB) : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;
  const showDemo = !kundli;

  const [insight, setInsight] = useState<ProInsight | null>(null);
  const [showTechnical, setShowTechnical] = useState(false);

  useEffect(() => {
    if (!kundli) return;
    const moonLon = moonData?.longitude ?? 0;
    setInsight(computeProInsight(kundli, moonLon));
  }, [kundli, moonData]);

  const copy = useMemo(() => {
    if (!insight) return null;
    return {
      periodMeaning: buildPeriodMeaning(insight, language),
      mainInsight: buildMainInsight(insight, language),
      areaRows: buildAreaRows(insight, language),
      focusTips: buildFocusList(insight, language),
      pdSummary: buildPdSummary(insight, language),
    };
  }, [insight, language]);

  const pdClr = insight ? PLANET_CLR[insight.pdPlanet] ?? "#f59e0b" : "#f59e0b";
  const pdPct = insight ? pdElapsedPct(insight.pdStart, insight.pdEnd) : 0;

  // Light mode: muted/dim shades are too faint to read — use darker slate.
  const bodyClr = C.isDark ? C.textMuted : "#334155";
  const dimClr = C.isDark ? C.textDim : "#475569";

  return (
    <CosmicBg>
      <ScrollView
        style={s.root}
        contentContainerStyle={[s.content, { paddingTop: topPad + 16, paddingBottom: botPad + 110 }]}
        showsVerticalScrollIndicator={false}
      >
        <FadeInView delay={0}>
          <View style={s.titleRow}>
            <Text style={[s.heading, { color: C.text }]}>{t.futureTitle}</Text>
            <LiveHourglass size={20} />
          </View>
          <Text style={[s.subtitle, { color: dimClr, opacity: C.isDark ? 0.7 : 1 }]}>{t.futureSubtitle}</Text>
        </FadeInView>

        {showDemo && (
          <FadeInView delay={70}>
            <Pressable
              style={[s.demoBanner, { backgroundColor: C.warningBg, borderColor: C.warningBorder }]}
              onPress={() => router.push("/onboarding")}
            >
              <Feather name="lock" size={12} color={C.warningText} />
              <Text style={[s.demoText, { color: C.warningText }]}>{t.futureDemoBanner}</Text>
              <Feather name="chevron-right" size={12} color={C.warningText} />
            </Pressable>
          </FadeInView>
        )}

        {showDemo && (
          <FadeInView delay={140}>
            <View style={[s.emptyState, { borderColor: C.border, backgroundColor: C.bgCard }]}>
              <Text style={s.emptyEmoji}>🪐</Text>
              <Text style={[s.emptyTitle, { color: C.text }]}>{t.kundliRequired}</Text>
              <Text style={[s.emptyBody, { color: dimClr }]}>{t.kundliRequiredSub}</Text>
              <Pressable
                style={[s.emptyBtn, { backgroundColor: C.accent }]}
                onPress={() => router.push("/onboarding")}
              >
                <Text style={s.emptyBtnText}>{t.createKundli}</Text>
              </Pressable>
            </View>
          </FadeInView>
        )}

        {!showDemo && insight && copy && (
          <>
            {/* Hero — current period */}
            <FadeInView delay={staggerDelay(1)}>
              <View style={[s.heroCard, { borderColor: C.border }]}>
                <LinearGradient
                  colors={["rgba(99,102,241,0.18)", "rgba(167,139,250,0.08)"]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                  style={StyleSheet.absoluteFill}
                />
                <LiveHeroGlow color="rgba(167,139,250,0.35)" />
                <View style={s.heroTopRow}>
                  <Text style={[s.heroLabel, { color: bodyClr }]}>{t.activeDashaPhase}</Text>
                  <LiveNowBadge label={t.ftLiveNow} color="#4ade80" />
                </View>
                <View style={s.heroPlanetRow}>
                  <LivePlanetEmoji planet={insight.mdPlanet} size={26} />
                  <Text style={[s.heroConnector, { color: C.textDim }]}>→</Text>
                  <LivePlanetEmoji planet={insight.adPlanet} size={26} />
                </View>
                <Text style={[s.heroPhase, { color: C.text }]}>
                  {pName(insight.mdPlanet)} Mahadasha · {pName(insight.adPlanet)} Antardasha
                </Text>
                {insight.adEnd && (
                  <Text style={[s.heroUntil, { color: dimClr }]}>
                    {t.ftUntil} {formatDate(insight.adEnd)}
                  </Text>
                )}
                <Text style={[s.heroTheme, { color: bodyClr }]}>{copy.periodMeaning}</Text>
              </View>
            </FadeInView>

            {/* Trend chips */}
            <FadeInView delay={staggerDelay(2)}>
              <Text style={[s.sectionLabel, { color: bodyClr }]}>{t.ftLifeAreas}</Text>
              <View style={s.chipRow}>
                {TREND_AREAS.map(area => {
                  const data = insight[area.key];
                  const clr = trendColor(data.trend);
                  const label = t[area.key];
                  return (
                    <View
                      key={area.key}
                      style={[s.trendChip, { backgroundColor: C.bgCard, borderColor: `${area.color}44` }]}
                    >
                      <Text style={s.chipIcon}>{area.icon}</Text>
                      <Text style={[s.chipLabel, { color: bodyClr }]}>{label}</Text>
                      <LiveTrendArrow trend={data.trend} color={clr} size={16} />
                      <Text style={[s.chipTrend, { color: clr }]}>{trendLabel(data.trend, language)}</Text>
                      <Text style={[s.chipScore, { color: dimClr }]}>{data.score}/100</Text>
                    </View>
                  );
                })}
              </View>
            </FadeInView>

            {/* Main insight */}
            <FadeInView delay={staggerDelay(3)}>
              <SectionCard title={t.ftPeriodMeaning} accent={C.accent}>
                <Text style={[s.bodyText, { color: C.text }]}>{copy.mainInsight}</Text>
              </SectionCard>
            </FadeInView>

            {/* Area breakdown */}
            <FadeInView delay={staggerDelay(4)}>
              <SectionCard title={t.ftAreaBreakdown} accent="#a78bfa">
                <View style={s.areaList}>
                  {copy.areaRows.map(row => (
                    <View key={row.label} style={[s.areaRow, { borderColor: C.border }]}>
                      <View style={s.areaTop}>
                        <Text style={s.areaIcon}>{row.icon}</Text>
                        <Text style={[s.areaLabel, { color: C.text }]}>{row.label}</Text>
                        <View style={s.areaTrendWrap}>
                          <LiveTrendArrow trend={row.trend} color={trendColor(row.trend)} size={14} />
                          <Text style={[s.areaTrend, { color: trendColor(row.trend) }]}>{row.score}</Text>
                        </View>
                      </View>
                      <Text style={[s.areaBody, { color: bodyClr }]}>{row.text}</Text>
                    </View>
                  ))}
                </View>
              </SectionCard>
            </FadeInView>

            {/* Current PD */}
            <FadeInView delay={staggerDelay(5)}>
              <View style={[s.pdCard, { backgroundColor: C.bgCard, borderColor: `${pdClr}55` }]}>
                <Text style={[s.sectionLabel, { color: pdClr, marginBottom: 6 }]}>{t.ftCurrentPd}</Text>
                <View style={s.pdTop}>
                  <LivePlanetEmoji planet={insight.pdPlanet} size={30} />
                  <View style={{ flex: 1 }}>
                    <Text style={[s.pdName, { color: pdClr }]}>{pName(insight.pdPlanet)}</Text>
                    {insight.pdStart && insight.pdEnd && (
                      <Text style={[s.pdDates, { color: dimClr }]}>
                        {formatDate(insight.pdStart)} — {formatDate(insight.pdEnd)}
                      </Text>
                    )}
                  </View>
                  <LiveNowBadge label="PD" color={pdClr} />
                </View>
                {insight.pdStart && insight.pdEnd && (
                  <View style={s.pdProgressWrap}>
                    <View style={s.pdProgressHead}>
                      <Text style={[s.pdProgressLbl, { color: dimClr }]}>{t.ftPdProgress}</Text>
                      <Text style={[s.pdProgressPct, { color: pdClr }]}>{Math.round(pdPct)}%</Text>
                    </View>
                    <LiveDashaProgress pct={pdPct} color={pdClr} trackColor={C.border} />
                  </View>
                )}
                <Text style={[s.pdBody, { color: bodyClr }]}>{copy.pdSummary}</Text>
              </View>
            </FadeInView>

            {/* Focus tips */}
            <FadeInView delay={staggerDelay(6)}>
              <SectionCard title={t.ftFocusNow} accent="#4ade80">
                <View style={s.tipList}>
                  {copy.focusTips.map((tip, i) => (
                    <View key={i} style={s.tipRow}>
                      <View style={[s.tipDot, { backgroundColor: "#4ade80" }]} />
                      <Text style={[s.tipText, { color: bodyClr }]}>{tip}</Text>
                    </View>
                  ))}
                </View>
              </SectionCard>
            </FadeInView>

            {/* Collapsed technical details */}
            <FadeInView delay={staggerDelay(7)}>
              <Pressable
                onPress={() => { setShowTechnical(v => !v); Haptics.selectionAsync(); }}
                style={s.techToggle}
              >
                <Text style={[s.techToggleText, { color: dimClr }]}>{t.ftTechnical}</Text>
                <Feather name={showTechnical ? "chevron-up" : "chevron-down"} size={16} color={dimClr} />
              </Pressable>

              {showTechnical && (
                <View style={[s.techCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                  <View style={s.dashaRow}>
                    {[
                      { lbl: "MD", planet: insight.mdPlanet, clr: "#4b6a86" },
                      { lbl: "AD", planet: insight.adPlanet, clr: "#7c6ed4" },
                      { lbl: "PD", planet: insight.pdPlanet, clr: "#f59e0b" },
                    ].map((d, i) => (
                      <React.Fragment key={d.lbl}>
                        <View style={s.dashaItem}>
                          <Text style={[s.dashaPlanetLbl, { color: d.clr }]}>{d.lbl}</Text>
                          <View style={[s.dashaPlanetDot, { backgroundColor: `${d.clr}25`, borderColor: `${d.clr}55` }]}>
                            <Text style={[s.dashaPlanetName, { color: d.clr }]}>{pName(d.planet)}</Text>
                          </View>
                        </View>
                        {i < 2 && <Feather name="chevron-right" size={14} color={C.textDim} style={{ marginTop: 14 }} />}
                      </React.Fragment>
                    ))}
                  </View>

                  {insight.upcomingPDs.length > 0 && (
                    <View style={s.pdSection}>
                      <Text style={[s.sectionLabel, { color: bodyClr, marginTop: 4 }]}>{t.upcomingPD}</Text>
                      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={s.pdRow}>
                        {insight.upcomingPDs.map((pd, i) => {
                          const clr = PLANET_CLR[pd.planet] ?? "#f59e0b";
                          const isActive = i === 0;
                          return (
                            <View
                              key={i}
                              style={[s.pdChip, { borderColor: `${clr}44`, backgroundColor: `${clr}10` }, isActive && { borderColor: clr }]}
                            >
                              {isActive && <View style={[s.pdActiveDot, { backgroundColor: clr }]} />}
                              <Text style={[s.pdChipPlanet, { color: clr }]}>{pName(pd.planet)}</Text>
                              <Text style={[s.pdChipDates, { color: bodyClr }]}>{fmtPDDate(pd.start)}</Text>
                              <Text style={[s.pdChipDatesTo, { color: dimClr }]}>–</Text>
                              <Text style={[s.pdChipDates, { color: bodyClr }]}>{fmtPDDate(pd.end)}</Text>
                            </View>
                          );
                        })}
                      </ScrollView>
                    </View>
                  )}
                </View>
              )}
            </FadeInView>
          </>
        )}
      </ScrollView>
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  root: { flex: 1 },
  content: { paddingHorizontal: 16, gap: 14 },
  heading: { fontSize: 22, fontFamily: F.extra },
  titleRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  subtitle: { fontSize: 13, fontFamily: F.medium, marginTop: 4, marginBottom: 4, opacity: 0.7 },

  demoBanner: {
    flexDirection: "row", alignItems: "center", gap: 8,
    borderRadius: 12, borderWidth: 1,
    paddingHorizontal: 14, paddingVertical: 10,
  },
  demoText: { fontSize: 11, fontFamily: F.semi, flex: 1 },

  emptyState: {
    borderRadius: 20, borderWidth: 1, padding: 28,
    alignItems: "center", gap: 10,
  },
  emptyEmoji: { fontSize: 42, lineHeight: 52 },
  emptyTitle: { fontSize: 17, fontFamily: F.extra },
  emptyBody: { fontSize: 13, fontFamily: F.medium, lineHeight: 20, textAlign: "center", opacity: 0.75 },
  emptyBtn: { marginTop: 6, paddingHorizontal: 24, paddingVertical: 11, borderRadius: 14 },
  emptyBtnText: { color: "#fff", fontSize: 14, fontFamily: F.extra },

  heroCard: { borderRadius: 18, borderWidth: 1, padding: 18, gap: 8, overflow: "hidden" },
  heroTopRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  heroLabel: { fontSize: 10, fontFamily: F.extra, letterSpacing: 1.2, textTransform: "uppercase" },
  heroPlanetRow: { flexDirection: "row", alignItems: "center", gap: 8, marginTop: 2 },
  heroConnector: { fontSize: 16, fontFamily: F.semi },
  heroPhase: { fontSize: 17, fontFamily: F.extra, lineHeight: 24 },
  heroUntil: { fontSize: 12, fontFamily: F.semi },
  heroTheme: { fontSize: 13, fontFamily: F.medium, lineHeight: 20, marginTop: 4 },

  sectionLabel: { fontSize: 11, fontFamily: F.extra, letterSpacing: 0.8, textTransform: "uppercase", paddingLeft: 2 },
  chipRow: { flexDirection: "row", gap: 8 },
  trendChip: {
    flex: 1, borderRadius: 14, borderWidth: 1, paddingVertical: 12, paddingHorizontal: 6,
    alignItems: "center", gap: 3,
  },
  chipIcon: { fontSize: 18 },
  chipLabel: { fontSize: 10, fontFamily: F.semi, textAlign: "center" },
  chipTrend: { fontSize: 9, fontFamily: F.bold, textAlign: "center" },
  chipScore: { fontSize: 9, fontFamily: F.semi },

  sectionCard: { borderRadius: 18, borderWidth: 1, padding: 16, gap: 10 },
  sectionHeader: { flexDirection: "row", alignItems: "center", gap: 8 },
  sectionDot: { width: 6, height: 6, borderRadius: 3 },
  sectionTitle: { fontSize: 11, fontFamily: F.extra, letterSpacing: 0.8, textTransform: "uppercase" },
  bodyText: { fontSize: 14, fontFamily: F.medium, lineHeight: 22 },

  areaList: { gap: 10 },
  areaRow: { borderTopWidth: 1, paddingTop: 10, gap: 6 },
  areaTop: { flexDirection: "row", alignItems: "center", gap: 8 },
  areaIcon: { fontSize: 16 },
  areaLabel: { flex: 1, fontSize: 14, fontFamily: F.bold },
  areaTrendWrap: { flexDirection: "row", alignItems: "center", gap: 4 },
  areaTrend: { fontSize: 13, fontFamily: F.extra },
  areaBody: { fontSize: 13, fontFamily: F.medium, lineHeight: 19, paddingLeft: 24 },

  pdCard: { borderRadius: 18, borderWidth: 1, padding: 16, gap: 8 },
  pdTop: { flexDirection: "row", alignItems: "center", gap: 12 },
  pdName: { fontSize: 16, fontFamily: F.extra },
  pdDates: { fontSize: 11, fontFamily: F.medium, marginTop: 2 },
  pdProgressWrap: { gap: 6, marginTop: 2 },
  pdProgressHead: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  pdProgressLbl: { fontSize: 10, fontFamily: F.extra, textTransform: "uppercase", letterSpacing: 0.6 },
  pdProgressPct: { fontSize: 12, fontFamily: F.extra },
  pdBody: { fontSize: 13, fontFamily: F.medium, lineHeight: 19 },

  tipList: { gap: 10 },
  tipRow: { flexDirection: "row", alignItems: "flex-start", gap: 10 },
  tipDot: { width: 6, height: 6, borderRadius: 3, marginTop: 7 },
  tipText: { flex: 1, fontSize: 13, fontFamily: F.medium, lineHeight: 19 },

  techToggle: {
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6,
    paddingVertical: 8,
  },
  techToggleText: { fontSize: 12, fontFamily: F.semi },

  techCard: { borderRadius: 18, borderWidth: 1, padding: 16, gap: 10, marginTop: -4 },
  dashaRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  dashaItem: { alignItems: "center", gap: 4, flex: 1 },
  dashaPlanetLbl: { fontSize: 10, fontFamily: F.extra, letterSpacing: 1 },
  dashaPlanetDot: { paddingHorizontal: 10, paddingVertical: 5, borderRadius: 12, borderWidth: 1 },
  dashaPlanetName: { fontSize: 13, fontFamily: F.semi },

  pdSection: { gap: 8 },
  pdRow: { gap: 8, paddingRight: 4 },
  pdChip: {
    borderRadius: 12, borderWidth: 1.5, paddingHorizontal: 12, paddingVertical: 10,
    gap: 2, alignItems: "center", minWidth: 80,
  },
  pdActiveDot: { width: 6, height: 6, borderRadius: 3, marginBottom: 2 },
  pdChipPlanet: { fontSize: 12, fontFamily: F.bold },
  pdChipDatesTo: { fontSize: 10, fontFamily: F.medium },
  pdChipDates: { fontSize: 10, fontFamily: F.medium },
});
