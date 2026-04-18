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
import { API_BASE } from "@/lib/apiConfig";

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
  const [message,  setMessage]  = useState("Sitaare align ho rahe hain...");
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
      setErrMsg("Sitaaron ki gehri jaanch me samay zyada lag gaya. Punah prayaas karein.");
    }, HARD_TIMEOUT_MS);

    pollRef.current = setInterval(async () => {
      try {
        const r = await fetch(`${API_BASE}/api/partner-portrait/status/${taskId}`);
        if (!r.ok) {
          if (r.status === 404) {
            stopPolling();
            setPhase("error");
            setErrMsg("Task expire ho gaya. Punah shuru karein.");
          }
          return;
        }
        const body = (await r.json()) as StatusBody;

        // Progress should never go backwards
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
          setErrMsg(body.error || "Cosmic Portrait abhi taiyar nahi ho saka.");
        }
      } catch {
        // ignore transient network blips; next tick will retry
      }
    }, POLL_INTERVAL_MS);
  }, []);

  const onReveal = useCallback(async () => {
    if (!kundli) {
      Alert.alert(
        "Kundli zaroori hai",
        "Apni primary kundli pehle bana lein, fir Cosmic Portrait reveal karein.",
      );
      return;
    }
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});

    setPhase("loading");
    setProgress(2);
    setMessage("Aapki kundli sitaaron ke saath align ho rahi hai...");
    setErrMsg("");
    setImageUrl(null);
    setTraits(null);

    try {
      const body: any = {
        kundli,
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
        setErrMsg(j?.message || j?.error || `Sitaare abhi vyast hain (${resp.status})`);
        return;
      }

      const data = await resp.json();
      if (!data?.task_id) {
        setPhase("error");
        setErrMsg("Task ID nahi mila. Punah prayaas karein.");
        return;
      }
      startPolling(data.task_id);
    } catch (e: any) {
      setPhase("error");
      setErrMsg("Network slow hai. Internet check karke punah prayaas karein.");
    }
  }, [kundli, birth, userGender, user, startPolling]);

  const onReset = useCallback(() => {
    stopPolling();
    setPhase("idle");
    setProgress(0);
    setMessage("Sitaare align ho rahe hain...");
    setImageUrl(null);
    setTraits(null);
    setErrMsg("");
  }, []);

  // ── Render ────────────────────────────────────────────────────────────────
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
        <Text style={[s.headerTitle, { color: C.text }]}>Cosmic Portrait</Text>
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
              <Text style={[s.heroTitle, { color: C.text }]}>
                Aapka Future Life Partner
              </Text>
              <Text style={[s.heroSub, { color: C.textMid }]}>
                Aapki kundli ke 30+ shastriya rules se {userGender === "male" ? "uski" : "uska"}{" "}
                roop, swabhav aur direction reveal hoga — D1, D9 Navamsa, D3 Drekkana,
                D30 Trimsamsa, KP 7th cuspal sub-lord, Upapada Lagna, Darakaraka,
                Arudha A7, Vargottama aur Ashtakavarga ka samuchit vishleshan.
              </Text>

              {primary && (
                <View style={[s.kundliPill, { backgroundColor: C.bg, borderColor: C.border }]}>
                  <Feather name="user" size={12} color={C.accent} />
                  <Text style={{ color: C.text, fontSize: 12, fontWeight: "700" }}>
                    Primary kundli: {primary.name || "—"}
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
                <Text style={s.ctaBtnText}>Reveal My Future Partner</Text>
              </Pressable>

              {!kundli && (
                <Text style={[s.warnText, { color: C.textMid }]}>
                  Pehle apni primary kundli banayein. Profile → Add kundli.
                </Text>
              )}
            </View>

            <View style={[s.infoCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <Text style={[s.infoTitle, { color: C.text }]}>
                💎 Yeh kya batayega
              </Text>
              {[
                "Roop-rang: chehra, complexion, aankhein, baal, sharir",
                "Swabhav: vibe, gun, stree/purush ke takat",
                "Vyavsay ki disha (D10 + 7th lord)",
                "Aapse umar ka antar (chhota / barabar / bada)",
                "Disha jis or se aayega (East / North / etc.)",
                "Ashtakavarga 7th bindu — attraction strength",
              ].map((line, i) => (
                <View key={i} style={s.bulletRow}>
                  <Text style={{ color: "#9333ea", marginRight: 6 }}>✦</Text>
                  <Text style={{ color: C.textMid, fontSize: 13, flex: 1, lineHeight: 19 }}>
                    {line}
                  </Text>
                </View>
              ))}
              <Text style={[s.disclaimer, { color: C.textMid, borderColor: C.border }]}>
                * Yeh ek divya jhalak hai — shastriya signature ka kalatmak chitran.
                Vastavik vyakti se haru-bahu mel zaroori nahi. Vyaktitva, vibe aur
                disha shastriya rules par adhrit hain.
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

            <Text style={[s.loadingTitle, { color: C.text }]}>
              Cosmic Portrait taiyar ho raha hai
            </Text>

            {/* Big animated percentage */}
            <Text style={[s.percentText, { color: "#9333ea" }]}>
              {Math.round(progress)}%
            </Text>

            {/* Progress bar */}
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

            {/* Current step message */}
            <View style={s.msgRow}>
              <ActivityIndicator size="small" color="#9333ea" />
              <Text style={[s.msgText, { color: C.textMid }]}>
                {message}
              </Text>
            </View>

            <Text style={[s.tipText, { color: C.textMid }]}>
              Pls wait... Sitaare aapke jeevansaathi ki essence padh rahe hain.
              {"\n"}Lag-bhag 15-25 sec lagenge.
            </Text>

            <Pressable onPress={onReset} style={[s.cancelBtn, { borderColor: C.border }]}>
              <Text style={{ color: C.textMid, fontSize: 12, fontWeight: "700" }}>
                Cancel
              </Text>
            </Pressable>
          </View>
        )}

        {/* ─────────── DONE ─────────── */}
        {phase === "done" && (
          <>
            {/* The portrait */}
            <View style={[s.imageCard, { backgroundColor: C.bgCard, borderColor: "#9333ea" }]}>
              {imageUrl ? (
                <Image
                  source={{ uri: imageUrl }}
                  style={s.portraitImg}
                  resizeMode="cover"
                />
              ) : (
                <View style={[s.portraitImg, { alignItems: "center", justifyContent: "center" }]}>
                  <Text style={{ color: C.textMid }}>Image taiyar nahi ho saki.</Text>
                </View>
              )}
              <View style={s.imageBadge}>
                <Text style={{ color: "#fff", fontSize: 10, fontWeight: "800" }}>
                  ✨ COSMIC PORTRAIT — DIVYA JHALAK
                </Text>
              </View>
            </View>

            {/* Trait highlights */}
            {traits?.features && (
              <View style={[s.traitCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                <Text style={[s.cardTitle, { color: C.text }]}>
                  🌟 Roop-rang & Swabhav
                </Text>
                <TraitRow label="Chehra"      value={traits.features.face_shape}    C={C} />
                <TraitRow label="Complexion"  value={traits.features.complexion}    C={C} />
                <TraitRow label="Build"       value={traits.features.build}         C={C} />
                <TraitRow label="Aankhein"    value={traits.features.eyes}          C={C} />
                <TraitRow label="Bhauein"     value={traits.features.eyebrows}      C={C} />
                <TraitRow label="Naak"        value={traits.features.nose}          C={C} />
                <TraitRow label="Honth"       value={traits.features.lips}          C={C} />
                <TraitRow label="Baal"        value={traits.features.hair}          C={C} />
                <TraitRow label="Vibe"        value={traits.features.vibe}          C={C} />
                {traits.features.vargottama_amplified && (
                  <View style={[s.boostPill, { backgroundColor: "#10b98120", borderColor: "#10b981" }]}>
                    <Text style={{ color: "#10b981", fontSize: 11, fontWeight: "800" }}>
                      ✨ Vargottama amplified — features especially harmonious
                    </Text>
                  </View>
                )}
              </View>
            )}

            {/* Context */}
            {traits?.context && (
              <View style={[s.traitCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                <Text style={[s.cardTitle, { color: C.text }]}>
                  🧭 Practical Insights
                </Text>
                <TraitRow label="Umar"          value={traits.context.approx_age_difference}     C={C} />
                <TraitRow label="Disha"         value={traits.context.direction_from_birthplace} C={C} />
                <TraitRow label="Vyavsay hint"  value={traits.context.profession_hint}           C={C} />
                <TraitRow label="Attraction"    value={traits.context.ashtakavarga_strength}     C={C} />
              </View>
            )}

            {/* Classical refs */}
            {traits?.layers && (
              <View style={[s.traitCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                <Text style={[s.cardTitle, { color: C.text }]}>
                  📜 Shastriya Adhar
                </Text>
                <RefRow label="D1 7th house"         value={`${traits.layers.d1_7th_sign} (lord ${traits.layers.d1_7th_lord})`} C={C} />
                <RefRow label="D9 7th (Navamsa)"     value={`${traits.layers.d9_7th_sign} (lord ${traits.layers.d9_7th_lord})`} C={C} />
                <RefRow label="D3 Lagna (face)"      value={traits.layers.d3_lagna_sign} C={C} />
                <RefRow label="D30 Lagna (swabhav)"  value={traits.layers.d30_lagna_sign} C={C} />
                {traits.layers.kp_7th_sub_lord && (
                  <RefRow label="KP 7th sub-lord"    value={traits.layers.kp_7th_sub_lord} C={C} />
                )}
                <RefRow label="Upapada Lagna"        value={`${traits.layers.upapada_lagna_sign} (lord ${traits.layers.upapada_lagna_lord})`} C={C} />
                <RefRow label="Darakaraka"           value={traits.layers.darakaraka} C={C} />
                <RefRow label="A7 (Arudha 7th)"      value={`${traits.layers.a7_sign} (lord ${traits.layers.a7_lord})`} C={C} />
                <RefRow label="Karaka 7th"           value={`${traits.layers.karaka_planet} → ${traits.layers.karaka_7th_sign}`} C={C} />
                <RefRow label="7th lord nakshatra"   value={`${traits.layers.seventh_lord_nakshatra} (${traits.layers.seventh_lord_nakshatra_lord})`} C={C} />
                <RefRow label="Ashtakavarga 7th"     value={`${traits.layers.ashtakavarga_7th_bindus} bindus`} C={C} />
                {(traits.layers.vargottama_planets || []).length > 0 && (
                  <RefRow label="Vargottama"         value={(traits.layers.vargottama_planets || []).join(", ")} C={C} />
                )}
              </View>
            )}

            <Text style={[s.disclaimer, { color: C.textMid, borderColor: C.border, marginTop: 12 }]}>
              * Cosmic Portrait — divya jhalak. Yeh ek kalatmak vishleshan hai
              jo aapki kundli ke 7th house, D9 Navamsa, KP cusp aur Jaimini ke
              Upapada/Arudha sutron par adhrit hai. Vastavik chehre se haru-bahu
              mel ho ya na ho — vyaktitva, vibe aur disha sahi hogi.
            </Text>

            <Pressable
              onPress={onReset}
              style={[s.againBtn, { backgroundColor: "#9333ea" }]}
            >
              <Feather name="refresh-cw" size={16} color="#fff" />
              <Text style={s.ctaBtnText}>Reveal Again</Text>
            </Pressable>
          </>
        )}

        {/* ─────────── ERROR ─────────── */}
        {phase === "error" && (
          <View style={[s.errorCard, { backgroundColor: C.bgCard, borderColor: "#ef4444" }]}>
            <Text style={{ fontSize: 48, textAlign: "center" }}>⚠️</Text>
            <Text style={[s.errorTitle, { color: "#ef4444" }]}>
              Cosmic Portrait abhi taiyar nahi
            </Text>
            <Text style={{ color: C.textMid, fontSize: 13, textAlign: "center", marginTop: 8, lineHeight: 19 }}>
              {errMsg || "Sitaare abhi vyast hain. Kuch der baad punah prayaas karein."}
            </Text>
            <Pressable onPress={onReset} style={[s.againBtn, { backgroundColor: "#9333ea" }]}>
              <Feather name="refresh-cw" size={16} color="#fff" />
              <Text style={s.ctaBtnText}>Punah Prayaas Karein</Text>
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
    paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20,
    borderWidth: 1, marginTop: 14,
  },
  ctaBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8,
    paddingHorizontal: 24, paddingVertical: 14, borderRadius: 14,
    marginTop: 18, alignSelf: "stretch",
  },
  ctaBtnText: { color: "#fff", fontSize: 15, fontWeight: "800" },
  warnText:   { fontSize: 11, marginTop: 10, textAlign: "center", fontStyle: "italic" },

  infoCard: { borderRadius: 14, borderWidth: 1, padding: 16, marginTop: 14 },
  infoTitle:{ fontSize: 14, fontWeight: "800", marginBottom: 10 },
  bulletRow:{ flexDirection: "row", alignItems: "flex-start", marginBottom: 6 },
  disclaimer:{
    fontSize: 11, lineHeight: 16, marginTop: 12,
    fontStyle: "italic", paddingTop: 10, borderTopWidth: 1,
  },

  loadingCard: {
    borderRadius: 18, borderWidth: 1, padding: 30, alignItems: "center",
    marginTop: 20,
  },
  loadingTitle:{ fontSize: 18, fontWeight: "800", marginTop: 14, textAlign: "center" },
  percentText: { fontSize: 56, fontWeight: "900", marginTop: 8, letterSpacing: -2 },
  progressTrack:{
    width: "100%", height: 10, borderRadius: 6, marginTop: 4, overflow: "hidden",
  },
  progressFill: { height: "100%", borderRadius: 6 },
  msgRow: {
    flexDirection: "row", alignItems: "center", gap: 8, marginTop: 18,
  },
  msgText: { fontSize: 13, flex: 1, lineHeight: 18, fontWeight: "600" },
  tipText: {
    fontSize: 11, marginTop: 16, textAlign: "center", lineHeight: 16,
    fontStyle: "italic",
  },
  cancelBtn: {
    marginTop: 18, paddingHorizontal: 18, paddingVertical: 8,
    borderRadius: 8, borderWidth: 1,
  },

  imageCard: {
    borderRadius: 16, borderWidth: 2, overflow: "hidden", position: "relative",
  },
  portraitImg: { width: "100%", aspectRatio: 1, backgroundColor: "#000" },
  imageBadge: {
    position: "absolute", top: 10, right: 10,
    backgroundColor: "rgba(147,51,234,0.95)",
    paddingHorizontal: 10, paddingVertical: 5, borderRadius: 12,
  },

  traitCard: {
    borderRadius: 14, borderWidth: 1, padding: 16, marginTop: 14,
  },
  cardTitle: { fontSize: 15, fontWeight: "800", marginBottom: 12 },
  traitRow:  {
    flexDirection: "row", paddingVertical: 6, alignItems: "flex-start",
  },
  refRow: {
    flexDirection: "row", paddingVertical: 5, alignItems: "flex-start",
  },
  boostPill: {
    marginTop: 10, paddingHorizontal: 12, paddingVertical: 8,
    borderRadius: 10, borderWidth: 1, alignItems: "center",
  },

  errorCard: {
    borderRadius: 14, borderWidth: 1, padding: 22, marginTop: 30,
    alignItems: "center",
  },
  errorTitle: { fontSize: 16, fontWeight: "800", marginTop: 8, textAlign: "center" },

  againBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8,
    paddingHorizontal: 24, paddingVertical: 12, borderRadius: 12, marginTop: 18,
    alignSelf: "stretch",
  },
});
