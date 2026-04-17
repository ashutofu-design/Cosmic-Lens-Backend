import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router, useLocalSearchParams } from "expo-router";
import React, { useEffect, useRef, useState } from "react";
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
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { CosmicBg } from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";
import { useUser, type AuthUser } from "@/context/UserContext";

import { API_BASE, apiFetch } from "@/lib/apiConfig";

const OTP_LEN = 6;

export default function VerifyOtpScreen() {
  const insets = useSafeAreaInsets();
  const C      = useC();
  const isDark = C.isDark;
  const { setUser } = useUser();

  const params = useLocalSearchParams<{
    phone?:    string;
    cc?:       string;
    cooldown?: string;
    devOtp?:   string;
  }>();
  const phone    = String(params.phone || "");
  const cc       = String(params.cc    || "91");
  const initialCd = parseInt(String(params.cooldown || "60"), 10) || 60;
  const devOtp   = String(params.devOtp || "");

  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  // Per-digit state for the 6 boxes
  const [digits, setDigits] = useState<string[]>(Array(OTP_LEN).fill(""));
  const inputs = useRef<Array<TextInput | null>>(Array(OTP_LEN).fill(null));

  const [loading,    setLoading]    = useState(false);
  const [resending,  setResending]  = useState(false);
  const [error,      setError]      = useState("");
  const [info,       setInfo]       = useState("");
  const [cooldown,   setCooldown]   = useState(initialCd);

  const code = digits.join("");

  // Cooldown countdown
  useEffect(() => {
    if (cooldown <= 0) return;
    const t = setTimeout(() => setCooldown(c => c - 1), 1000);
    return () => clearTimeout(t);
  }, [cooldown]);

  // Auto-focus first box on mount
  useEffect(() => {
    const t = setTimeout(() => inputs.current[0]?.focus(), 200);
    return () => clearTimeout(t);
  }, []);

  // Auto-submit when full
  useEffect(() => {
    if (code.length === OTP_LEN && !loading) {
      submit(code);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [code]);

  function setDigitAt(i: number, v: string) {
    const clean = v.replace(/\D/g, "");
    setError("");
    if (clean.length === 0) {
      const next = [...digits]; next[i] = ""; setDigits(next);
      return;
    }
    // Pasted multi-char (e.g. user pastes "123456")
    if (clean.length > 1) {
      const chars = clean.slice(0, OTP_LEN).split("");
      const next  = Array(OTP_LEN).fill("").map((_, idx) => chars[idx] || "");
      setDigits(next);
      const lastFilled = Math.min(chars.length, OTP_LEN) - 1;
      inputs.current[Math.min(lastFilled + 1, OTP_LEN - 1)]?.focus();
      return;
    }
    const next = [...digits]; next[i] = clean[0]; setDigits(next);
    if (i < OTP_LEN - 1) inputs.current[i + 1]?.focus();
  }

  function handleKey(i: number, key: string) {
    if (key === "Backspace" && !digits[i] && i > 0) {
      inputs.current[i - 1]?.focus();
    }
  }

  async function submit(otp: string) {
    if (otp.length !== OTP_LEN) {
      setError(`${OTP_LEN}-digit OTP daalein`);
      return;
    }
    setLoading(true); setError("");
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    try {
      const res = await apiFetch(`${API_BASE}/api/auth/verify-otp`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ phone, country_code: cc, otp }),
      });
      const data = await res.json();
      if (!res.ok || data.ok === false) {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
        setError(data.error || "OTP verify nahi ho saka.");
        // Clear digits on hard fail (so user retypes)
        if ((data.error || "").toLowerCase().includes("naya otp")) {
          setDigits(Array(OTP_LEN).fill(""));
        }
        return;
      }
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      setUser(data as AuthUser);
      router.replace("/(tabs)");
    } catch {
      setError("Network error. Try again.");
    } finally {
      setLoading(false);
    }
  }

  async function resend() {
    if (cooldown > 0 || resending) return;
    setResending(true); setError(""); setInfo("");
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    try {
      const res = await apiFetch(`${API_BASE}/api/auth/send-otp`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ phone, country_code: cc }),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) {
        setError(data.error || "OTP resend nahi ho saka.");
        if (data.retry_after) setCooldown(data.retry_after);
        return;
      }
      setInfo("Naya OTP bhej diya gaya hai.");
      setCooldown(data.cooldown || 60);
      setDigits(Array(OTP_LEN).fill(""));
      inputs.current[0]?.focus();
    } catch {
      setError("Network error. Try again.");
    } finally {
      setResending(false);
    }
  }

  return (
    <CosmicBg>
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        keyboardVerticalOffset={Platform.OS === "ios" ? 0 : 20}
      >
        <ScrollView
          contentContainerStyle={[s.scroll, { paddingTop: topPad + 24, paddingBottom: botPad + 24 }]}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {/* Back */}
          <Pressable onPress={() => router.back()} style={s.backBtn} hitSlop={10}>
            <Feather name="arrow-left" size={20} color={C.text} />
            <Text style={[s.backText, { color: C.text }]}>Number badlein</Text>
          </Pressable>

          {/* Header */}
          <View style={s.header}>
            <View style={[s.iconCircle, {
              backgroundColor: isDark ? "rgba(245,158,11,0.12)" : "#FEF3C7",
              borderColor: isDark ? "rgba(245,158,11,0.4)" : "#FCD34D",
            }]}>
              <Feather name="message-circle" size={26} color={isDark ? "#f59e0b" : "#92400E"} />
            </View>
            <Text style={[s.title, { color: C.text }]}>OTP Verify Karein</Text>
            <Text style={[s.subtitle, { color: C.textMuted }]}>
              Hum ne <Text style={{ color: C.text, fontFamily: "Nunito_700Bold" }}>+{cc} {phone}</Text>
              {" "}par 6-digit code bheja hai.
            </Text>
          </View>

          {/* Dev-mode helper */}
          {!!devOtp && (
            <View style={[s.devBox, { borderColor: isDark ? "rgba(167,139,250,0.4)" : "#C4B5FD", backgroundColor: isDark ? "rgba(167,139,250,0.08)" : "#EDE9FE" }]}>
              <Feather name="info" size={13} color={isDark ? "#a78bfa" : "#5B21B6"} />
              <Text style={[s.devText, { color: isDark ? "#c4b5fd" : "#5B21B6" }]}>
                Dev mode OTP: <Text style={{ fontFamily: "Nunito_700Bold" }}>{devOtp}</Text>
              </Text>
            </View>
          )}

          {/* OTP boxes */}
          <View style={[s.card, {
            backgroundColor: C.bgCard,
            borderColor: C.border2,
            shadowColor: isDark ? "#7c3aed" : "#0F172A",
            shadowOpacity: isDark ? 0.18 : 0.12,
          }]}>
            <View style={s.boxRow}>
              {digits.map((d, i) => (
                <TextInput
                  key={i}
                  ref={el => { inputs.current[i] = el; }}
                  value={d}
                  onChangeText={v => setDigitAt(i, v)}
                  onKeyPress={e => handleKey(i, e.nativeEvent.key)}
                  keyboardType="number-pad"
                  maxLength={1}
                  selectTextOnFocus
                  textContentType="oneTimeCode"
                  autoComplete="sms-otp"
                  style={[s.box, {
                    backgroundColor: C.inputBg,
                    borderColor: error
                      ? "rgba(239,68,68,0.6)"
                      : d
                        ? (isDark ? "rgba(245,158,11,0.5)" : "#F59E0B")
                        : C.inputBorder,
                    color: C.text,
                  }]}
                />
              ))}
            </View>

            {!!error && (
              <View style={s.errorBox}>
                <Feather name="alert-circle" size={13} color="#f87171" />
                <Text style={s.errorText}>{error}</Text>
              </View>
            )}
            {!!info && !error && (
              <View style={s.errorBox}>
                <Feather name="check-circle" size={13} color="#22c55e" />
                <Text style={[s.errorText, { color: "#22c55e" }]}>{info}</Text>
              </View>
            )}

            {/* Manual verify (in case auto-submit needs retry) */}
            <Pressable
              onPress={() => submit(code)}
              disabled={loading || code.length !== OTP_LEN}
              style={({ pressed }) => [{ opacity: (loading || code.length !== OTP_LEN) ? 0.6 : pressed ? 0.85 : 1 }]}
            >
              <LinearGradient
                colors={[C.btnGradStart, C.btnGradEnd]}
                start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
                style={s.ctaBtn}
              >
                {loading
                  ? <ActivityIndicator size="small" color="#fff" />
                  : (
                    <>
                      <Feather name="check" size={16} color="#fff" />
                      <Text style={s.ctaText}>Verify Karein</Text>
                    </>
                  )
                }
              </LinearGradient>
            </Pressable>

            {/* Resend */}
            <View style={s.resendRow}>
              <Text style={[s.resendLabel, { color: C.textMuted }]}>OTP nahi mila?</Text>
              <Pressable
                onPress={resend}
                disabled={cooldown > 0 || resending}
                hitSlop={8}
              >
                {resending
                  ? <ActivityIndicator size="small" color={isDark ? "#f59e0b" : "#92400E"} />
                  : (
                    <Text style={[
                      s.resendBtn,
                      cooldown > 0
                        ? { color: C.textMuted }
                        : { color: isDark ? "#f59e0b" : "#92400E" }
                    ]}>
                      {cooldown > 0 ? `Resend in ${cooldown}s` : "Resend OTP"}
                    </Text>
                  )
                }
              </Pressable>
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </CosmicBg>
  );
}

const s = StyleSheet.create({
  scroll: { paddingHorizontal: 20, gap: 18, alignItems: "center" },

  backBtn: { flexDirection: "row", alignItems: "center", gap: 6, alignSelf: "flex-start" },
  backText:{ fontSize: 13, fontFamily: "Nunito_500Medium" },

  header: { alignItems: "center", gap: 10, marginTop: 8 },
  iconCircle: {
    width: 60, height: 60, borderRadius: 30, borderWidth: 1.5,
    alignItems: "center", justifyContent: "center",
  },
  title:    { fontSize: 22, fontFamily: "Nunito_700Bold" },
  subtitle: { fontSize: 13, fontFamily: "Nunito_400Regular", textAlign: "center", lineHeight: 19, paddingHorizontal: 16 },

  devBox: {
    flexDirection: "row", alignItems: "center", gap: 8,
    paddingVertical: 9, paddingHorizontal: 12,
    borderRadius: 10, borderWidth: 1,
    width: "100%", maxWidth: 380,
  },
  devText: { fontSize: 12, fontFamily: "Nunito_500Medium" },

  card: {
    width: "100%", maxWidth: 380,
    borderRadius: 20, padding: 20,
    borderWidth: 1, gap: 16,
    shadowOffset: { width: 0, height: 8 },
    shadowRadius: 24, elevation: 10,
  },
  boxRow: { flexDirection: "row", justifyContent: "space-between", gap: 8 },
  box: {
    flex: 1, height: 54, borderRadius: 12, borderWidth: 1.5,
    textAlign: "center", fontSize: 22, fontFamily: "Nunito_700Bold",
  },

  errorBox:  { flexDirection: "row", alignItems: "center", gap: 6 },
  errorText: { fontSize: 12, color: "#f87171", fontFamily: "Nunito_500Medium", flex: 1 },

  ctaBtn: {
    flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 8, paddingVertical: 14, borderRadius: 14,
  },
  ctaText: { fontSize: 14, color: "#fff", fontFamily: "Nunito_700Bold" },

  resendRow: { flexDirection: "row", justifyContent: "center", alignItems: "center", gap: 6, marginTop: 2 },
  resendLabel: { fontSize: 12, fontFamily: "Nunito_400Regular" },
  resendBtn:   { fontSize: 13, fontFamily: "Nunito_700Bold" },
});
