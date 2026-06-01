import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { router } from "expo-router";
import React, { useState } from "react";
import {
  ActivityIndicator,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from "react-native";
import Svg, { Circle, Defs, Ellipse, RadialGradient, Stop } from "react-native-svg";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { CosmicBg } from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";
import { useUser, type AuthUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";

import { API_BASE, apiFetch } from "@/lib/apiConfig";
import { FadeInView } from "@/components/motion/FadeInView";
import { ScalePressable } from "@/components/motion/ScalePressable";
import { verifyFirebaseIdToken } from "@/lib/authBackend";
import { signInWithGoogle } from "@/lib/firebaseAuth";
import { isFirebaseConfigured } from "@/lib/firebaseConfig";

export default function LoginScreen() {
  const insets  = useSafeAreaInsets();
  const C       = useC();
  const t       = useT();
  const { setUser, language } = useUser();

  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;
  const isDark = C.isDark;
  const isHindi = language === "hi" || language === "hn";

  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState("");

  async function finishLogin(u: AuthUser) {
    await setUser(u);
    router.replace("/welcome-reveal");
  }

  async function handleGoogleLogin() {
    if (!isFirebaseConfigured()) {
      setError(t.authNotConfigured);
      return;
    }
    setError("");
    setLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});

    try {
      const idToken = await signInWithGoogle();
      const u = await verifyFirebaseIdToken(idToken);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
      finishLogin(u);
    } catch (e: unknown) {
      const msg = String((e as Error)?.message || e || "");
      if (msg.includes("popup-closed-by-user") || msg.includes("cancelled")) {
        setError(isHindi ? "Login cancel ho gaya." : "Sign-in was cancelled.");
      } else if (msg.toLowerCase().includes("network")) {
        setError(t.errNetwork);
      } else {
        setError(msg || t.loginGenericError);
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleDemoLogin() {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});
    setError("");
    setLoading(true);
    try {
      const res = await apiFetch(`${API_BASE}/api/auth/demo`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      const data = await res.json();
      if (!res.ok || !data?.id) {
        setError(data?.error || t.loginGenericError);
        return;
      }
      finishLogin({
        id:      data.id,
        name:    data.name || "Demo User",
        email:   data.email || "demo@cosmic.local",
        api_key: data.api_key || "",
        is_pro:  !!data.is_pro,
      });
    } catch {
      setError(t.errNetwork);
    } finally {
      setLoading(false);
    }
  }

  return (
    <CosmicBg>
      <ScrollView
        contentContainerStyle={[s.scroll, { paddingTop: topPad + 36, paddingBottom: botPad + 24 }]}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        <FadeInView delay={0} style={s.logoWrap}>
          <View style={[s.logoCircle, {
            backgroundColor: isDark ? "#1a1330" : "#F1F5F9",
            borderColor: "rgba(245,158,11,0.45)",
            shadowColor: "#f59e0b",
          }]}>
            <Svg width={36} height={36} viewBox="0 0 38 38" fill="none">
              <Defs>
                <RadialGradient id="rg1" cx="35%" cy="35%" r="65%">
                  <Stop offset="0%" stopColor="#f59e0b" stopOpacity="0.95" />
                  <Stop offset="100%" stopColor="#7c3aed" />
                </RadialGradient>
              </Defs>
              <Circle cx={19} cy={19} r={17} stroke="#f59e0b" strokeWidth={1} strokeOpacity={0.4} strokeDasharray="4 3" />
              <Circle cx={19} cy={19} r={7}  fill="url(#rg1)" />
              <Ellipse cx={19} cy={19} rx={13} ry={4} stroke="#a78bfa" strokeWidth={1} strokeOpacity={0.7} fill="none" />
            </Svg>
          </View>
          <Text style={[s.title, { color: C.text }]}>Cosmic Lens</Text>
          <Text style={[s.subtitle, { color: C.textMuted }]}>
            {isHindi
              ? "Gmail se login karein — OTP ki zaroorat nahi"
              : "Sign in with Gmail — no OTP needed"}
          </Text>
        </FadeInView>

        <FadeInView delay={140}>
        <View style={[s.card, {
          backgroundColor: C.bgCard,
          borderColor: C.border2,
          shadowColor: isDark ? "#7c3aed" : "#0F172A",
          shadowOpacity: isDark ? 0.18 : 0.12,
        }]}>
          <Text style={[s.fieldLabel, { color: C.warningText }]}>
            {isHindi ? "GOOGLE ACCOUNT" : "GOOGLE ACCOUNT"}
          </Text>

          {!!error && (
            <View style={s.errorBox}>
              <Feather name="alert-circle" size={13} color="#f87171" />
              <Text style={s.errorText}>{error}</Text>
            </View>
          )}

          <Text style={[s.note, { color: C.textMuted }]}>
            {isHindi
              ? "Pehli baar login par account automatic ban jayega."
              : "First-time sign-in creates your account automatically."}
          </Text>

          <Pressable
            onPress={handleGoogleLogin}
            disabled={loading}
            style={({ pressed }) => [{ opacity: loading ? 0.6 : pressed ? 0.85 : 1 }]}
          >
            <View style={[s.googleBtn, {
              backgroundColor: isDark ? "#fff" : "#fff",
              borderColor: C.border,
            }]}>
              {loading
                ? <ActivityIndicator size="small" color="#4285F4" />
                : (
                  <>
                    <Text style={s.googleG}>G</Text>
                    <Text style={s.googleBtnText}>
                      {isHindi ? "Google se continue karein" : "Continue with Google"}
                    </Text>
                  </>
                )}
            </View>
          </Pressable>
        </View>
        </FadeInView>

        {__DEV__ && (
          <FadeInView delay={280} style={s.demoWrap}>
            <View style={s.divider}>
              <View style={[s.divLine, { backgroundColor: C.border }]} />
              <Text style={[s.divText, { color: C.textMuted }]}>{t.orDivider}</Text>
              <View style={[s.divLine, { backgroundColor: C.border }]} />
            </View>
            <Pressable
              onPress={handleDemoLogin}
              disabled={loading}
              style={({ pressed }) => [{ opacity: pressed ? 0.8 : 1, width: "100%", maxWidth: 380 }]}
            >
              <View style={[s.demoBtn, {
                borderColor: isDark ? "rgba(245,158,11,0.3)" : C.warningBorder,
                backgroundColor: isDark ? "rgba(245,158,11,0.06)" : C.warningBg,
              }]}>
                <Text style={{ fontSize: 14 }}>⚡</Text>
                <View style={{ flex: 1 }}>
                  <Text style={[s.demoBtnTitle, { color: isDark ? "#f59e0b" : "#92400E" }]}>{t.demoLogin}</Text>
                  <Text style={[s.demoBtnSub, { color: C.textMuted }]}>{t.demoLoginSub}</Text>
                </View>
              </View>
            </Pressable>
          </FadeInView>
        )}

        <FadeInView delay={360}>
        <Text style={[s.footer, { color: C.textMuted }]}>
          {t.termsAccept}{" "}
          <Text style={{ color: isDark ? "#f59e0b" : "#92400E" }}>{t.termsLink}</Text>
          {" & "}
          <Text style={{ color: isDark ? "#f59e0b" : "#92400E" }}>{t.privacyLink}</Text>
        </Text>
        </FadeInView>
      </ScrollView>
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  scroll:    { paddingHorizontal: 20, alignItems: "center", gap: 16 },
  logoWrap:  { alignItems: "center", marginBottom: 4, gap: 8 },
  logoCircle:{
    width: 72, height: 72, borderRadius: 36, borderWidth: 1.5,
    alignItems: "center", justifyContent: "center",
    shadowOffset: { width: 0, height: 0 }, shadowOpacity: 0.3, shadowRadius: 20, elevation: 8,
  },
  title:    { fontSize: 26, fontFamily: "Nunito_700Bold", letterSpacing: 0.4 },
  subtitle: { fontSize: 12, fontFamily: "Nunito_400Regular", textAlign: "center", paddingHorizontal: 24 },

  card: {
    width: "100%", maxWidth: 380, borderRadius: 24, padding: 22,
    borderWidth: 1, gap: 14,
    shadowColor: "#7c3aed",
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.22, shadowRadius: 28, elevation: 12,
  },
  fieldLabel: { fontSize: 11, fontFamily: "Nunito_800ExtraBold", letterSpacing: 2.4 },

  errorBox:  { flexDirection: "row", alignItems: "center", gap: 6, paddingHorizontal: 4 },
  errorText: { fontSize: 12, color: "#f87171", fontFamily: "Nunito_500Medium", flex: 1 },
  note: { fontSize: 11, fontFamily: "Nunito_400Regular", lineHeight: 16, paddingHorizontal: 2 },

  googleBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 12, paddingVertical: 14, paddingHorizontal: 16, borderRadius: 999, borderWidth: 1,
  },
  googleG: {
    fontSize: 18, fontFamily: "Nunito_700Bold", color: "#4285F4",
    width: 24, textAlign: "center",
  },
  googleBtnText: {
    fontSize: 15, fontFamily: "Nunito_700Bold", color: "#1f2937",
  },

  demoWrap: { width: "100%", maxWidth: 380, gap: 14, alignItems: "center", marginTop: 4 },
  divider:  { flexDirection: "row", alignItems: "center", gap: 10, width: "100%" },
  divLine:  { flex: 1, height: 1 },
  divText:  { fontSize: 11, fontFamily: "Nunito_500Medium" },
  demoBtn: {
    flexDirection: "row", alignItems: "center", gap: 12,
    paddingHorizontal: 14, paddingVertical: 13, borderRadius: 14, borderWidth: 1,
  },
  demoBtnTitle: { fontSize: 13, fontFamily: "Nunito_700Bold" },
  demoBtnSub:   { fontSize: 11, fontFamily: "Nunito_400Regular", marginTop: 1 },
  footer: { fontSize: 10.5, textAlign: "center", lineHeight: 16, marginTop: 6, paddingHorizontal: 20 },
});
