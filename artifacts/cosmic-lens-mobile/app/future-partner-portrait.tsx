/**
 * Future Partner Portrait — Cosmic Portrait
 *
 * Uses the user's primary kundli to extract 30+ classical traits across
 * D1, D9, D3, D30, KP, Upapada Lagna, Darakaraka, Arudha A7, Vargottama,
 * and Ashtakavarga, then renders a soft watercolor portrait of their
 * future life partner. Server runs the full pipeline asynchronously and
 * we poll the progress every second to render a 0→100% loader.
 *
 * Branding: NEVER mentions AI / GPT / OpenAI. All copy cites classical
 * Vedic sources (BPHS, Phaladeepika, KP Reader, Jaimini Sutras).
 */

import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Animated,
  Easing,
  Image,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT, type T } from "@/hooks/useT";
import { API_BASE } from "@/lib/apiConfig";
import { fetchKundliFromAPI } from "@/lib/kundliAPI";

type Phase = "idle" | "loading" | "done" | "error";

type StatusBody = {
  task_id: string;
  progress: number;
  status: "queued" | "running" | "done" | "error";
  message: string;
  traits: any | null;
  image_url: string | null;
  error: string | null;
};

const POLL_INTERVAL_MS = 900;
const HARD_TIMEOUT_MS  = 90_000;

export default function FuturePartnerPortraitScreen() {
  const C       = useC();
  const t       = useT();
  const insets  = useSafeAreaInsets();
  const { user, profiles, primaryProfileId } = useUser();

  const primary = profiles.find(p => p.id === primaryProfileId) ?? profiles[0] ?? null;
  const kundli  = primary?.kundli ?? null;
  const birth   = primary?.birthData ?? null;

  // user_gender → backend computes opposite-gender partner. Default "male".
  const userGender = (() => {
    const g = (primary?.gender || "").toLowerCase();
    if (g.startsWith("f")) return "female";
    return "male";
  })();

  const [phase,    setPhase]    = useState<Phase>("idle");
  const [progress, setProgress] = useState(0);
  const [message,  setMessage]  = useState<string>(t.fpp_msgAlign);
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [traits,   setTraits]   = useState<any>(null);
  const [errMsg,   setErrMsg]   = useState<string>("");

  const pollRef    = useRef<ReturnType<typeof setInterval> | null>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const progressAnim = useRef(new Animated.Value(0)).current;
  const pulseAnim    = useRef(new Animated.Value(0)).current;

  // ── Smooth-animate the progress bar whenever progress changes ────────────
  useEffect(() => {
    Animated.timing(progressAnim, {
      toValue: progress,
      duration: 500,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: false,
    }).start();
  }, [progress, progressAnim]);

  // ── Pulse animation while loading ────────────────────────────────────────
  useEffect(() => {
    if (phase !== "loading") return;
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1, duration: 1200, useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 0, duration: 1200, useNativeDriver: true }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, [phase, pulseAnim]);

  // ── Cleanup on unmount ───────────────────────────────────────────────────
  useEffect(() => () => stopPolling(), []);

  function stopPolling() {
    if (pollRef.current)    { clearInterval(pollRef.current); pollRef.current = null; }
    if (timeoutRef.current) { clearTimeout(timeoutRef.current); timeoutRef.current = null; }
  }

  const startPolling = useCallback((taskId: string) => {
    stopPolling();

    timeoutRef.current = setTimeout(() => {
      stopPolling();
      setPhase("error");
      setErrMsg(t.fpp_errTimeout);
    }, HARD_TIMEOUT_MS);

    pollRef.current = setInterval(async () => {
      try {
        const r = await fetch(`${API_BASE}/api/partner-portrait/status/${taskId}`);
        if (!r.ok) {
          if (r.status === 404) {
            stopPolling();
            setPhase("error");
            setErrMsg(t.fpp_msgTaskExpire);
          }
          return;
        }
        const body = (await r.json()) as StatusBody;

        setProgress(prev => Math.max(prev, body.progress || 0));
        if (body.message) setMessage(body.message);

        if (body.status === "done") {
          stopPolling();
          setImageUrl(body.image_url);
          setTraits(body.traits);
          setProgress(100);
          setPhase("done");
          Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
        } else if (body.status === "error") {
          stopPolling();
          setPhase("error");
          setErrMsg(body.error || t.fpp_errPortraitFail);
        }
      } catch {
        // ignore transient network blips; next tick will retry
      }
    }, POLL_INTERVAL_MS);
  }, [t.fpp_errTimeout, t.fpp_msgTaskExpire, t.fpp_errPortraitFail]);

  const onReveal = useCallback(async () => {
    if (!birth) {
      Alert.alert(t.fpp_alertBirthTtl, t.fpp_alertBirthMsg);
      return;
    }
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});

    setPhase("loading");
    setProgress(2);
    setMessage(t.fpp_msgAlignFull);
    setErrMsg("");
    setImageUrl(null);
    setTraits(null);

    let kundliToUse = kundli;
    if (!kundliToUse) {
      try {
        setMessage(t.fpp_msgComputing);
        const auth = (user?.id && user?.api_key)
          ? { user_id: user.id, api_key: user.api_key }
          : null;
        kundliToUse = await fetchKundliFromAPI(birth, auth);
      } catch (e: any) {
        setPhase("error");
        setErrMsg(
          e?.message?.includes("quota")
            ? t.fpp_msgKundliQuota
            : t.fpp_msgKundliFail
        );
        return;
      }
    }

    try {
      const body: any = {
        kundli:      kundliToUse,
        birth_data:  birth,
        user_gender: userGender,
      };
      if (user?.id) body.user_id = user.id;

      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (user?.api_key) headers["X-API-Key"] = user.api_key;

      const resp = await fetch(`${API_BASE}/api/partner-portrait/start`, {
        method:  "POST",
        headers,
        body:    JSON.stringify(body),
      });

      if (!resp.ok) {
        const j = await resp.json().catch(() => ({}));
        setPhase("error");
        setErrMsg(j?.message || j?.error || `${t.fpp_msgStarsBusy} (${resp.status})`);
        return;
      }

      const data = await resp.json();
      if (!data?.task_id) {
        setPhase("error");
        setErrMsg(t.fpp_msgTaskIdMiss);
        return;
      }
      startPolling(data.task_id);
    } catch {
      setPhase("error");
      setErrMsg(t.fpp_msgNetSlow);
    }
  }, [
    kundli, birth, userGender, user, startPolling,
    t.fpp_alertBirthTtl, t.fpp_alertBirthMsg, t.fpp_msgAlignFull,
    t.fpp_msgComputing, t.fpp_msgKundliQuota, t.fpp_msgKundliFail,
    t.fpp_msgStarsBusy, t.fpp_msgTaskIdMiss, t.fpp_msgNetSlow,
  ]);

  const onReset = useCallback(() => {
    stopPolling();
    setPhase("idle");
    setProgress(0);
    setMessage(t.fpp_msgAlign);
    setImageUrl(null);
    setTraits(null);
    setErrMsg("");
  }, [t.fpp_msgAlign]);

  return (
    <View style={{ flex: 1, backgroundColor: C.bg }}>
      <StatusBar barStyle={C.isDark ? "light-content" : "dark-content"} />
      <CosmicBg />

      {/* Header */}
      <LinearGradient
        colors={[C.bgCard, C.bg]}
        style={[s.header, { paddingTop: insets.top + 10, borderBottomColor: C.border }]}
      >
        <Pressable hitSlop={12} onPress={() => router.back()}>
          <Feather name="arrow-left" size={22} color={C.text} />
        </Pressable>
        <Text style={[s.headerTitle, { color: C.text }]}>{t.fpp_headerTitle}</Text>
        <View style={{ width: 28 }} />
      </LinearGradient>

      <ScrollView
        contentContainerStyle={{ padding: 18, paddingBottom: insets.bottom + 50 }}
        showsVerticalScrollIndicator={false}
      >
        {/* ─────────── IDLE ─────────── */}
        {phase === "idle" && (
          <>
            <View style={[s.heroCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <Text style={{ fontSize: 56, textAlign: "center" }}>🔮</Text>
              <Text style={[s.heroTitle, { color: C.text }]}>{t.fpp_heroTitle}</Text>
              <Text style={[s.heroSub, { color: C.textMid }]}>
                {userGender === "male" ? t.fpp_heroSubMale : t.fpp_heroSubFemale}
              </Text>

              {primary && (
                <View style={[s.kundliPill, { backgroundColor: C.bg, borderColor: C.border }]}>
                  <Feather name="user" size={12} color={C.accent} />
                  <Text style={{ color: C.text, fontSize: 12, fontWeight: "700" }}>
                    {t.fpp_primaryKundli}: {primary.name || "—"}
                  </Text>
                </View>
              )}

              <Pressable
                onPress={onReveal}
                disabled={!kundli}
                style={({ pressed }) => [
                  s.ctaBtn,
                  {
                    backgroundColor: kundli ? "#9333ea" : C.border,
                    opacity: pressed ? 0.85 : 1,
                  },
                ]}
              >
                <Feather name="eye" size={18} color="#fff" />
                <Text style={s.ctaBtnText}>{t.fpp_btnReveal}</Text>
              </Pressable>

              {!kundli && (
                <Text style={[s.warnText, { color: C.textMid }]}>{t.fpp_warnNoKundli}</Text>
              )}
            </View>

            <View style={[s.infoCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <Text style={[s.infoTitle, { color: C.text }]}>{t.fpp_infoTitle}</Text>
              {[t.fpp_b1, t.fpp_b2, t.fpp_b3, t.fpp_b4, t.fpp_b5, t.fpp_b6].map((line, i) => (
                <View key={i} style={s.bulletRow}>
                  <Text style={{ color: "#9333ea", marginRight: 6 }}>✦</Text>
                  <Text style={{ color: C.textMid, fontSize: 13, flex: 1, lineHeight: 19 }}>
                    {line}
                  </Text>
                </View>
              ))}
              <Text style={[s.disclaimer, { color: C.textMid, borderColor: C.border }]}>
                {t.fpp_disclaimer1}
              </Text>
            </View>
          </>
        )}

        {/* ─────────── LOADING ─────────── */}
        {phase === "loading" && (
          <View style={[s.loadingCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <Animated.View
              style={{
                opacity: pulseAnim.interpolate({ inputRange: [0, 1], outputRange: [0.6, 1] }),
                transform: [{
                  scale: pulseAnim.interpolate({ inputRange: [0, 1], outputRange: [0.9, 1.1] }),
                }],
              }}
            >
              <Text style={{ fontSize: 72, textAlign: "center" }}>🔮</Text>
            </Animated.View>

            <Text style={[s.loadingTitle, { color: C.text }]}>{t.fpp_loadingTitle}</Text>

            <Text style={[s.percentText, { color: "#9333ea" }]}>
              {Math.round(progress)}%
            </Text>

            <View style={[s.progressTrack, { backgroundColor: C.border }]}>
              <Animated.View
                style={[
                  s.progressFill,
                  {
                    backgroundColor: "#9333ea",
                    width: progressAnim.interpolate({
                      inputRange:  [0, 100],
                      outputRange: ["0%", "100%"],
                    }),
                  },
                ]}
              />
            </View>

            <View style={s.msgRow}>
              <ActivityIndicator size="small" color="#9333ea" />
              <Text style={[s.msgText, { color: C.textMid }]}>{message}</Text>
            </View>

            <Text style={[s.tipText, { color: C.textMid }]}>{t.fpp_tipText}</Text>

            <Pressable onPress={onReset} style={[s.cancelBtn, { borderColor: C.border }]}>
              <Text style={{ color: C.textMid, fontSize: 12, fontWeight: "700" }}>
                {t.fpp_btnCancel}
              </Text>
            </Pressable>
          </View>
        )}

        {/* ─────────── DONE ─────────── */}
        {phase === "done" && (
          <>
            <View style={[s.imageCard, { backgroundColor: C.bgCard, borderColor: "#9333ea" }]}>
              {imageUrl ? (
                <Image source={{ uri: imageUrl }} style={s.portraitImg} resizeMode="cover" />
              ) : (
                <View style={[s.portraitImg, { alignItems: "center", justifyContent: "center" }]}>
                  <Text style={{ color: C.textMid }}>{t.fpp_imgFailed}</Text>
                </View>
              )}
              <View style={s.imageBadge}>
                <Text style={{ color: "#fff", fontSize: 10, fontWeight: "800" }}>
                  {t.fpp_imgBadge}
                </Text>
              </View>
            </View>

            {traits?.features && (
              <View style={[s.traitCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                <Text style={[s.cardTitle, { color: C.text }]}>{t.fpp_traitTitle}</Text>
                <TraitRow label={t.fpp_lblFace}       value={traits.features.face_shape} C={C} />
                <TraitRow label={t.fpp_lblComplexion} value={traits.features.complexion} C={C} />
                <TraitRow label={t.fpp_lblBuild}      value={traits.features.build}      C={C} />
                <TraitRow label={t.fpp_lblEyes}       value={traits.features.eyes}       C={C} />
                <TraitRow label={t.fpp_lblEyebrows}   value={traits.features.eyebrows}   C={C} />
                <TraitRow label={t.fpp_lblNose}       value={traits.features.nose}       C={C} />
                <TraitRow label={t.fpp_lblLips}       value={traits.features.lips}       C={C} />
                <TraitRow label={t.fpp_lblHair}       value={traits.features.hair}       C={C} />
                <TraitRow label={t.fpp_lblVibe}       value={traits.features.vibe}       C={C} />
                {traits.features.vargottama_amplified && (
                  <View style={[s.boostPill, { backgroundColor: "#10b98120", borderColor: "#10b981" }]}>
                    <Text style={{ color: "#10b981", fontSize: 11, fontWeight: "800" }}>
                      {t.fpp_vargottama}
                    </Text>
                  </View>
                )}
              </View>
            )}

            {traits?.context && (
              <View style={[s.traitCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                <Text style={[s.cardTitle, { color: C.text }]}>{t.fpp_practTitle}</Text>
                <TraitRow label={t.fpp_lblAge}        value={traits.context.approx_age_difference}     C={C} />
                <TraitRow label={t.fpp_lblDirection}  value={traits.context.direction_from_birthplace} C={C} />
                <TraitRow label={t.fpp_lblProfHint}   value={traits.context.profession_hint}           C={C} />
                <TraitRow label={t.fpp_lblAttraction} value={traits.context.ashtakavarga_strength}     C={C} />
              </View>
            )}

            {traits?.layers && (
              <View style={[s.traitCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                <Text style={[s.cardTitle, { color: C.text }]}>{t.fpp_classicalTtl}</Text>
                <RefRow label="D1 7th house"        value={`${traits.layers.d1_7th_sign} (lord ${traits.layers.d1_7th_lord})`} C={C} />
                <RefRow label="D9 7th (Navamsa)"    value={`${traits.layers.d9_7th_sign} (lord ${traits.layers.d9_7th_lord})`} C={C} />
                <RefRow label="D3 Lagna (face)"     value={traits.layers.d3_lagna_sign} C={C} />
                <RefRow label="D30 Lagna (swabhav)" value={traits.layers.d30_lagna_sign} C={C} />
                {traits.layers.kp_7th_sub_lord && (
                  <RefRow label="KP 7th sub-lord"   value={traits.layers.kp_7th_sub_lord} C={C} />
                )}
                <RefRow label="Upapada Lagna"       value={`${traits.layers.upapada_lagna_sign} (lord ${traits.layers.upapada_lagna_lord})`} C={C} />
                <RefRow label="Darakaraka"          value={traits.layers.darakaraka} C={C} />
                <RefRow label="A7 (Arudha 7th)"     value={`${traits.layers.a7_sign} (lord ${traits.layers.a7_lord})`} C={C} />
                <RefRow label="Karaka 7th"          value={`${traits.layers.karaka_planet} → ${traits.layers.karaka_7th_sign}`} C={C} />
                <RefRow label="7th lord nakshatra"  value={`${traits.layers.seventh_lord_nakshatra} (${traits.layers.seventh_lord_nakshatra_lord})`} C={C} />
                <RefRow label="Ashtakavarga 7th"    value={`${traits.layers.ashtakavarga_7th_bindus} bindus`} C={C} />
                {(traits.layers.vargottama_planets || []).length > 0 && (
                  <RefRow label="Vargottama"        value={(traits.layers.vargottama_planets || []).join(", ")} C={C} />
                )}
              </View>
            )}

            <Text style={[s.disclaimer, { color: C.textMid, borderColor: C.border, marginTop: 12 }]}>
              {t.fpp_disclaimer2}
            </Text>

            <Pressable onPress={onReset} style={[s.againBtn, { backgroundColor: "#9333ea" }]}>
              <Feather name="refresh-cw" size={16} color="#fff" />
              <Text style={s.ctaBtnText}>{t.fpp_btnRevealAgain}</Text>
            </Pressable>
          </>
        )}

        {/* ─────────── ERROR ─────────── */}
        {phase === "error" && (
          <View style={[s.errorCard, { backgroundColor: C.bgCard, borderColor: "#ef4444" }]}>
            <Text style={{ fontSize: 48, textAlign: "center" }}>⚠️</Text>
            <Text style={[s.errorTitle, { color: "#ef4444" }]}>{t.fpp_errTitle}</Text>
            <Text style={{ color: C.textMid, fontSize: 13, textAlign: "center", marginTop: 8, lineHeight: 19 }}>
              {errMsg || t.fpp_errDefault}
            </Text>
            <Pressable onPress={onReset} style={[s.againBtn, { backgroundColor: "#9333ea" }]}>
              <Feather name="refresh-cw" size={16} color="#fff" />
              <Text style={s.ctaBtnText}>{t.fpp_btnTryAgain}</Text>
            </Pressable>
          </View>
        )}
      </ScrollView>
    </View>
  );
}

// ── Sub-components ──────────────────────────────────────────────────────────
function TraitRow({ label, value, C }: { label: string; value: string; C: any }) {
  if (!value) return null;
  return (
    <View style={s.traitRow}>
      <Text style={{ color: C.textMid, fontSize: 12, fontWeight: "700", width: 96 }}>
        {label}
      </Text>
      <Text style={{ color: C.text, fontSize: 13, flex: 1, lineHeight: 18 }}>
        {value}
      </Text>
    </View>
  );
}

function RefRow({ label, value, C }: { label: string; value: string; C: any }) {
  if (!value) return null;
  return (
    <View style={s.refRow}>
      <Text style={{ color: C.textMid, fontSize: 11, fontWeight: "700", width: 130 }}>
        {label}
      </Text>
      <Text style={{ color: C.text, fontSize: 12, flex: 1, fontWeight: "600" }}>
        {value}
      </Text>
    </View>
  );
}

const s = StyleSheet.create({
  header: {
    flexDirection: "row", alignItems: "center", justifyContent: "space-between",
    paddingHorizontal: 16, paddingBottom: 12, borderBottomWidth: 1,
  },
  headerTitle: { fontSize: 17, fontWeight: "800" },

  heroCard: {
    borderRadius: 18, borderWidth: 1, padding: 22, alignItems: "center",
  },
  heroTitle:   { fontSize: 22, fontWeight: "900", marginTop: 10, textAlign: "center" },
  heroSub:     { fontSize: 13, lineHeight: 19, marginTop: 8, textAlign: "center" },
  kundliPill:  {
    flexDirection: "row", alignItems: "center", gap: 6,
    paddingHorizontal: 12, paddingVertical: 6,
    borderRadius: 999, borderWidth: 1, marginTop: 14,
  },
  ctaBtn: {
    flexDirection: "row", alignItems: "center", gap: 8,
    paddingHorizontal: 24, paddingVertical: 14,
    borderRadius: 12, marginTop: 18,
  },
  ctaBtnText: { color: "#fff", fontSize: 15, fontWeight: "800" },
  warnText:   { fontSize: 11, marginTop: 10, fontStyle: "italic", textAlign: "center" },

  infoCard: { borderRadius: 14, borderWidth: 1, padding: 16, marginTop: 14 },
  infoTitle:{ fontSize: 14, fontWeight: "800", marginBottom: 10 },
  bulletRow:{ flexDirection: "row", alignItems: "flex-start", marginVertical: 3 },
  disclaimer:{
    fontSize: 11, lineHeight: 16, fontStyle: "italic",
    paddingTop: 10, borderTopWidth: 1, marginTop: 12,
  },

  loadingCard: {
    borderRadius: 18, borderWidth: 1, padding: 26, alignItems: "center",
  },
  loadingTitle: { fontSize: 16, fontWeight: "800", marginTop: 18, textAlign: "center" },
  percentText:  { fontSize: 56, fontWeight: "900", marginTop: 14, letterSpacing: -2 },
  progressTrack:{
    width: "100%", height: 8, borderRadius: 4,
    marginTop: 18, overflow: "hidden",
  },
  progressFill: { height: "100%", borderRadius: 4 },
  msgRow: {
    flexDirection: "row", alignItems: "center", gap: 10,
    marginTop: 16, paddingHorizontal: 8,
  },
  msgText:  { fontSize: 13, flex: 1, lineHeight: 18 },
  tipText:  { fontSize: 11, marginTop: 18, textAlign: "center", fontStyle: "italic", lineHeight: 16 },
  cancelBtn:{
    paddingHorizontal: 20, paddingVertical: 8,
    borderRadius: 999, borderWidth: 1, marginTop: 18,
  },

  imageCard: {
    borderRadius: 18, borderWidth: 2, overflow: "hidden",
    marginBottom: 14, position: "relative",
  },
  portraitImg:{ width: "100%", aspectRatio: 1, backgroundColor: "#1a0033" },
  imageBadge: {
    position: "absolute", top: 10, right: 10,
    backgroundColor: "#9333ea", paddingHorizontal: 10, paddingVertical: 5,
    borderRadius: 999,
  },
  traitCard: { borderRadius: 14, borderWidth: 1, padding: 16, marginTop: 12 },
  cardTitle: { fontSize: 14, fontWeight: "800", marginBottom: 10 },
  traitRow:  { flexDirection: "row", alignItems: "flex-start", marginVertical: 4 },
  refRow:    { flexDirection: "row", alignItems: "flex-start", marginVertical: 3 },
  boostPill: {
    paddingHorizontal: 12, paddingVertical: 8,
    borderRadius: 8, borderWidth: 1, marginTop: 12,
  },
  againBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8,
    paddingVertical: 14, borderRadius: 12, marginTop: 18,
  },

  errorCard: { borderRadius: 18, borderWidth: 2, padding: 26, alignItems: "center" },
  errorTitle:{ fontSize: 16, fontWeight: "800", marginTop: 12, textAlign: "center" },
});
