import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useEffect, useState } from "react";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import Svg, { Circle, Defs, Ellipse, RadialGradient, Stop } from "react-native-svg";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { CosmicBg } from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";
import { useUser, type AuthUser } from "@/context/UserContext";

import { API_BASE, apiFetch } from "@/lib/apiConfig";
import { sendPhoneOtp, resetPendingVerification } from "@/lib/firebaseAuth";
import { isFirebaseConfigured } from "@/lib/firebaseConfig";

export default function LoginScreen() {
  const insets  = useSafeAreaInsets();
  const C       = useC();
  const { setUser } = useUser();

  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;
  const isDark = C.isDark;

  const [mobile,  setMobile]  = useState("");
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState("");

  // Reset any stale verification handle whenever the user lands on the login
  // screen (e.g. they hit "Number badlein" on the verify screen).
  useEffect(() => {
    resetPendingVerification();
  }, []);

  function finishLogin(u: AuthUser) {
    setUser(u);
    router.replace("/(tabs)");
  }

  async function sendOtp() {
    const digits = mobile.replace(/\D/g, "");
    if (digits.length !== 10 || !"6789".includes(digits[0])) {
      setError("Sahi 10-digit mobile number daalein (6/7/8/9 se shuru)");
      return;
    }
    if (!isFirebaseConfigured()) {
      setError("Firebase setup pending. Admin se contact karein.");
      return;
    }

    setError(""); setLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});

    try {
      const e164 = `+91${digits}`;
      await sendPhoneOtp(e164);

      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
      router.push({
        pathname: "/verify-otp",
        params: {
          phone:    digits,
          cc:       "91",
          cooldown: "30",
        },
      });
    } catch (e: any) {
      const msg = String(e?.message || e || "OTP bhejne mein dikkat aayi.");
      // Normalise common Firebase error codes for non-technical users.
      if (msg.includes("auth/invalid-phone-number")) {
        setError("Mobile number invalid hai. Dobara check karein.");
      } else if (msg.includes("auth/too-many-requests")) {
        setError("Bahut zyada attempts. Thodi der baad try karein.");
      } else if (msg.includes("auth/quota-exceeded")) {
        setError("Aaj ka SMS quota khatam. Kal try karein.");
      } else if (msg.toLowerCase().includes("network")) {
        setError("Network error. Connection check karein.");
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleDemoLogin() {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});
    setError(""); setLoading(true);
    try {
      const res = await apiFetch(`${API_BASE}/api/auth/demo`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      const data = await res.json();
      if (!res.ok || !data?.id) {
        setError(data?.error || "Demo login failed. Try again.");
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
      setError("Network error. Connection check karein.");
    } finally {
      setLoading(false);
    }
  }

  const canContinue = mobile.replace(/\D/g, "").length === 10;

  return (
    <CosmicBg>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        keyboardVerticalOffset={Platform.OS === "ios" ? 0 : 20}
      >
        <ScrollView
          contentContainerStyle={[s.scroll, { paddingTop: topPad + 36, paddingBottom: botPad + 24 }]}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {/* ── Logo ── */}
          <View style={s.logoWrap}>
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
                <Circle cx={7}  cy={9}  r={1}   fill="#f59e0b" opacity={0.8} />
                <Circle cx={31} cy={9}  r={0.7} fill="#f59e0b" opacity={0.6} />
                <Circle cx={5}  cy={27} r={0.7} fill="#a78bfa" opacity={0.6} />
                <Circle cx={33} cy={26} r={1}   fill="#f59e0b" opacity={0.7} />
              </Svg>
            </View>
            <Text style={[s.title, { color: C.text }]}>Cosmic Lens</Text>
            <Text style={[s.subtitle, { color: C.textMuted }]}>
              Apna mobile number daalein, OTP se login karein
            </Text>
          </View>

          {/* ── PHONE PANEL ── */}
          <View style={[s.card, {
            backgroundColor: C.bgCard,
            borderColor: C.border2,
            shadowColor: isDark ? "#7c3aed" : "#0F172A",
            shadowOpacity: isDark ? 0.18 : 0.12,
          }]}>
            <Text style={[s.fieldLabel, { color: C.warningText }]}>MOBILE NUMBER</Text>
            <View style={[
              s.phoneRow,
              { backgroundColor: C.inputBg, borderColor: error ? "rgba(239,68,68,0.5)" : C.inputBorder }
            ]}>
              <View style={[s.phonePrefix, { borderRightColor: C.border }]}>
                <Text style={s.phonePrefixFlag}>🇮🇳</Text>
                <Text style={[s.phonePrefixCode, { color: C.textMid }]}>+91</Text>
              </View>
              <TextInput
                style={[s.phoneInput, { color: C.text }]}
                value={mobile}
                onChangeText={v => { setMobile(v.replace(/\D/g, "").slice(0, 10)); setError(""); }}
                placeholder="10-digit number"
                placeholderTextColor={isDark ? "#3d2b6b" : "#94A3B8"}
                keyboardType="number-pad"
                maxLength={10}
                returnKeyType="done"
                onSubmitEditing={sendOtp}
                autoFocus
              />
              {mobile.length > 0 && (
                <Pressable onPress={() => { setMobile(""); setError(""); }} hitSlop={10}>
                  <Feather name="x-circle" size={16} color={C.textMuted} />
                </Pressable>
              )}
            </View>

            {!!error && (
              <View style={s.errorBox}>
                <Feather name="alert-circle" size={13} color="#f87171" />
                <Text style={s.errorText}>{error}</Text>
              </View>
            )}

            <Text style={[s.note, { color: C.textMuted }]}>
              SMS se 6-digit OTP aayega. Pehli baar number daalne par account automatic ban jaayega.
            </Text>

            <Pressable
              onPress={sendOtp}
              disabled={loading || !canContinue}
              style={({ pressed }) => [{ opacity: (loading || !canContinue) ? 0.6 : pressed ? 0.85 : 1 }]}
            >
              <LinearGradient
                colors={[C.btnGradStart, C.btnGradEnd]}
                start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
                style={[s.ctaBtn, !isDark && { shadowColor: "#EA580C", shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.35, shadowRadius: 10, elevation: 6 }]}
              >
                {loading
                  ? <ActivityIndicator size="small" color="#fff" />
                  : (
                    <>
                      <Feather name="send" size={16} color="#fff" />
                      <Text style={s.ctaText}>OTP Bhejen</Text>
                    </>
                  )
                }
              </LinearGradient>
            </Pressable>
          </View>

          {/* ── DEMO LOGIN ── */}
          <View style={s.demoWrap}>
            <View style={s.divider}>
              <View style={[s.divLine, { backgroundColor: C.border }]} />
              <Text style={[s.divText, { color: C.textMuted }]}>ya phir</Text>
              <View style={[s.divLine, { backgroundColor: C.border }]} />
            </View>

            <Pressable
              onPress={handleDemoLogin}
              style={({ pressed }) => [{ opacity: pressed ? 0.8 : 1, width: "100%", maxWidth: 380 }]}
            >
              <View style={[s.demoBtn, {
                borderColor: isDark ? "rgba(245,158,11,0.3)" : C.warningBorder,
                backgroundColor: isDark ? "rgba(245,158,11,0.06)" : C.warningBg,
              }]}>
                <View style={s.demoIconWrap}>
                  <Text style={{ fontSize: 14 }}>⚡</Text>
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={[s.demoBtnTitle, { color: isDark ? "#f59e0b" : "#92400E" }]}>Demo Login</Text>
                  <Text style={[s.demoBtnSub, { color: C.textMuted }]}>Testing ke liye — seedha andar jayein</Text>
                </View>
                <Feather name="chevron-right" size={16} color={isDark ? "#f59e0b" : "#92400E"} />
              </View>
            </Pressable>
          </View>

          <Text style={[s.footer, { color: C.textMuted }]}>
            By continuing, you agree to our{" "}
            <Text style={{ color: isDark ? "#f59e0b" : "#92400E" }}>Terms of Service</Text>
            {" "}and{" "}
            <Text style={{ color: isDark ? "#f59e0b" : "#92400E" }}>Privacy Policy</Text>
          </Text>

          {/*
            Invisible reCAPTCHA mount point. Required by Firebase JS SDK on web
            for phone authentication. On native this div simply doesn't render.
            Using a hidden View with a raw HTML id via dangerouslySetInnerHTML
            keeps it cross-platform — react-native-web honours the `nativeID`.
          */}
          {Platform.OS === "web" && (
            <View nativeID="cosmic-recaptcha" style={{ height: 0, width: 0, opacity: 0 }} />
          )}
        </ScrollView>
      </KeyboardAvoidingView>
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
    width: "100%", maxWidth: 380, borderRadius: 20, padding: 20,
    borderWidth: 1, gap: 14,
    shadowColor: "#7c3aed",
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.18, shadowRadius: 24, elevation: 10,
  },
  fieldLabel: { fontSize: 10, fontFamily: "Nunito_700Bold", letterSpacing: 2 },

  phoneRow: { flexDirection: "row", alignItems: "center", borderRadius: 12, borderWidth: 1, overflow: "hidden" },
  phonePrefix: {
    flexDirection: "row", alignItems: "center", gap: 5,
    paddingHorizontal: 12, paddingVertical: 13,
    borderRightWidth: 1,
  },
  phonePrefixFlag: { fontSize: 16 },
  phonePrefixCode: { fontSize: 14, fontFamily: "Nunito_600SemiBold" },
  phoneInput: { flex: 1, fontSize: 15, paddingHorizontal: 12, fontFamily: "Nunito_500Medium" },

  errorBox:  { flexDirection: "row", alignItems: "center", gap: 6, paddingHorizontal: 4 },
  errorText: { fontSize: 12, color: "#f87171", fontFamily: "Nunito_500Medium", flex: 1 },

  note: { fontSize: 11, fontFamily: "Nunito_400Regular", lineHeight: 16, paddingHorizontal: 2 },

  ctaBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 8, paddingVertical: 14, borderRadius: 14,
  },
  ctaText: { fontSize: 14, color: "#fff", fontFamily: "Nunito_700Bold" },

  demoWrap: { width: "100%", maxWidth: 380, gap: 14, alignItems: "center", marginTop: 4 },
  divider:  { flexDirection: "row", alignItems: "center", gap: 10, width: "100%" },
  divLine:  { flex: 1, height: 1 },
  divText:  { fontSize: 11, fontFamily: "Nunito_500Medium" },

  demoBtn: {
    flexDirection: "row", alignItems: "center", gap: 12,
    paddingHorizontal: 14, paddingVertical: 13, borderRadius: 14, borderWidth: 1,
  },
  demoIconWrap: {
    width: 28, height: 28, borderRadius: 14,
    backgroundColor: "rgba(245,158,11,0.12)",
    alignItems: "center", justifyContent: "center",
  },
  demoBtnTitle: { fontSize: 13, fontFamily: "Nunito_700Bold" },
  demoBtnSub:   { fontSize: 11, fontFamily: "Nunito_400Regular", marginTop: 1 },

  footer: { fontSize: 10.5, textAlign: "center", lineHeight: 16, marginTop: 6, paddingHorizontal: 20 },
});
