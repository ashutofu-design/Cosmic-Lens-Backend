import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useRef, useState } from "react";
import {
  ActivityIndicator,
  Animated,
  Easing,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import Svg, {
  Circle,
  Defs,
  Ellipse,
  Path,
  RadialGradient,
  Stop,
} from "react-native-svg";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { useUser } from "@/context/UserContext";

export default function LoginScreen() {
  const insets = useSafeAreaInsets();
  const { setUser } = useUser();

  const [mobile, setMobile]       = useState("");
  const [otp, setOtp]             = useState("");
  const [otpSent, setOtpSent]     = useState(false);
  const [error, setError]         = useState("");
  const [loading, setLoading]     = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);

  const [mobileFocused, setMobileFocused] = useState(false);
  const [otpFocused, setOtpFocused]       = useState(false);

  // Spin animation for demo loading
  const spinAnim = useRef(new Animated.Value(0)).current;
  const startSpin = () => {
    spinAnim.setValue(0);
    Animated.loop(
      Animated.timing(spinAnim, { toValue: 1, duration: 800, easing: Easing.linear, useNativeDriver: true })
    ).start();
  };
  const stopSpin = () => spinAnim.stopAnimation();
  const spinDeg = spinAnim.interpolate({ inputRange: [0, 1], outputRange: ["0deg", "360deg"] });

  function finishLogin(user: { name: string; email: string }) {
    setUser(user);
    router.replace("/(tabs)");
  }

  async function handleSendOtp() {
    const clean = mobile.replace(/\D/g, "");
    if (clean.length < 10) { setError("Please enter a valid mobile number"); return; }
    setError(""); setLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    await delay(800);
    setOtpSent(true); setLoading(false);
  }

  async function handleVerifyOtp() {
    if (otp.length < 4) { setError("Please enter the OTP"); return; }
    setError(""); setLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    await delay(600);
    finishLogin({ name: "Mobile User", email: `+91${mobile.replace(/\D/g, "")}@mobile.cosmic` });
    setLoading(false);
  }

  async function handleDemoLogin() {
    setDemoLoading(true); startSpin();
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    await delay(700);
    stopSpin();
    finishLogin({ name: "Demo User", email: "demo@cosmiclens.app" });
    setDemoLoading(false);
  }

  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  return (
    <View style={styles.root}>
      {/* Ambient glow top */}
      <View style={[styles.glowWrap, { pointerEvents: "none" }]}>
        <View style={styles.glowCircle} />
      </View>

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        keyboardVerticalOffset={Platform.OS === "ios" ? 0 : 20}
      >
        <ScrollView
          contentContainerStyle={[styles.scroll, { paddingTop: topPad + 48, paddingBottom: botPad + 24 }]}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {/* ── Logo ── */}
          <View style={styles.logoWrap}>
            <View style={styles.logoCircle}>
              <Svg width={36} height={36} viewBox="0 0 38 38" fill="none">
                <Defs>
                  <RadialGradient id="pg2" cx="35%" cy="35%" r="65%">
                    <Stop offset="0%" stopColor="#00c6ff" stopOpacity="0.9" />
                    <Stop offset="100%" stopColor="#0a3a5c" />
                  </RadialGradient>
                </Defs>
                <Circle cx={19} cy={19} r={17} stroke="#00c6ff" strokeWidth={1} strokeOpacity={0.45} strokeDasharray="4 3" />
                <Circle cx={19} cy={19} r={7}  fill="url(#pg2)" />
                <Ellipse cx={19} cy={19} rx={13} ry={4} stroke="#00c6ff" strokeWidth={1} strokeOpacity={0.65} fill="none" />
                <Circle cx={7}  cy={9}  r={1}   fill="#00d4ff" opacity={0.8} />
                <Circle cx={31} cy={9}  r={0.7} fill="#00d4ff" opacity={0.6} />
                <Circle cx={5}  cy={27} r={0.7} fill="#00d4ff" opacity={0.5} />
                <Circle cx={33} cy={26} r={1}   fill="#00d4ff" opacity={0.7} />
              </Svg>
            </View>

            <Text style={styles.title}>Cosmic Lens</Text>

            <Text style={styles.subtitle}>Your personal Vedic astrology guide</Text>
          </View>

          {/* ── Card ── */}
          <View style={styles.card}>

            {/* Mobile label */}
            <View style={styles.fieldWrap}>
              <Text style={styles.fieldLabel}>MOBILE NUMBER</Text>

              {!otpSent ? (
                <View style={styles.mobileRow}>
                  {/* Country prefix */}
                  <View style={styles.prefix}>
                    <Text style={styles.prefixText}>🇮🇳 +91</Text>
                  </View>
                  <TextInput
                    style={[
                      styles.input,
                      { flex: 1, borderColor: mobileFocused ? "rgba(0,198,255,0.5)" : "rgba(255,255,255,0.1)" },
                    ]}
                    placeholder="10-digit number"
                    placeholderTextColor="#4b5563"
                    value={mobile}
                    onChangeText={t => { setMobile(t); setError(""); }}
                    keyboardType="phone-pad"
                    maxLength={10}
                    returnKeyType="done"
                    onFocus={() => setMobileFocused(true)}
                    onBlur={() => setMobileFocused(false)}
                    onSubmitEditing={handleSendOtp}
                  />
                </View>
              ) : (
                <View style={{ gap: 8 }}>
                  <View style={styles.otpInfo}>
                    <Text style={styles.otpInfoText}>OTP sent to +91 {mobile}</Text>
                  </View>
                  <TextInput
                    style={[
                      styles.input,
                      styles.otpInput,
                      { borderColor: otpFocused ? "rgba(0,198,255,0.5)" : "rgba(255,255,255,0.1)" },
                    ]}
                    placeholder="Enter OTP"
                    placeholderTextColor="#4b5563"
                    value={otp}
                    onChangeText={t => { setOtp(t); setError(""); }}
                    keyboardType="number-pad"
                    maxLength={6}
                    textAlign="center"
                    onFocus={() => setOtpFocused(true)}
                    onBlur={() => setOtpFocused(false)}
                    onSubmitEditing={handleVerifyOtp}
                  />
                </View>
              )}
            </View>

            {/* Error */}
            {!!error && (
              <View style={styles.errorBox}>
                <Text style={styles.errorText}>{error}</Text>
              </View>
            )}

            {/* CTA */}
            {!otpSent ? (
              <Pressable
                onPress={handleSendOtp}
                disabled={loading}
                style={({ pressed }) => [pressed && { opacity: 0.8 }]}
              >
                <LinearGradient
                  colors={loading ? ["rgba(0,198,255,0.15)", "rgba(0,198,255,0.15)"] : ["#00c6ff", "#00f2fe"]}
                  start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
                  style={[styles.ctaBtn, loading && styles.ctaBtnDisabled]}
                >
                  {loading
                    ? <ActivityIndicator size="small" color="#4b5563" />
                    : <Text style={[styles.ctaText, { color: "#020d1a" }]}>Send OTP</Text>
                  }
                </LinearGradient>
              </Pressable>
            ) : (
              <View style={{ gap: 8 }}>
                <Pressable
                  onPress={handleVerifyOtp}
                  disabled={loading}
                  style={({ pressed }) => [pressed && { opacity: 0.8 }]}
                >
                  <LinearGradient
                    colors={loading ? ["rgba(0,198,255,0.15)", "rgba(0,198,255,0.15)"] : ["#00c6ff", "#00f2fe"]}
                    start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
                    style={[styles.ctaBtn, loading && styles.ctaBtnDisabled]}
                  >
                    {loading
                      ? <ActivityIndicator size="small" color="#4b5563" />
                      : <Text style={[styles.ctaText, { color: "#020d1a" }]}>Verify & Login</Text>
                    }
                  </LinearGradient>
                </Pressable>
                <Pressable onPress={() => { setOtpSent(false); setOtp(""); setError(""); }}>
                  <Text style={styles.changeNum}>Change Number</Text>
                </Pressable>
              </View>
            )}

            {/* Divider */}
            <View style={styles.divider}>
              <View style={styles.divLine} />
              <Text style={styles.divText}>or</Text>
              <View style={styles.divLine} />
            </View>

            {/* Google button */}
            <Pressable
              style={({ pressed }) => [styles.googleBtn, pressed && { opacity: 0.75 }]}
              onPress={() => setError("Google login is not available on mobile yet")}
            >
              <GoogleGIcon />
              <Text style={styles.googleText}>Continue with Google</Text>
            </Pressable>
          </View>

          {/* ── Demo Login ── */}
          <View style={styles.demoWrap}>
            <View style={styles.divider}>
              <View style={[styles.divLine, { backgroundColor: "rgba(255,255,255,0.06)" }]} />
              <Text style={[styles.divText, { color: "#374151" }]}>For Demo</Text>
              <View style={[styles.divLine, { backgroundColor: "rgba(255,255,255,0.06)" }]} />
            </View>

            <Pressable
              onPress={handleDemoLogin}
              disabled={demoLoading}
              style={({ pressed }) => [pressed && { opacity: 0.8 }]}
            >
              <LinearGradient
                colors={
                  demoLoading
                    ? ["rgba(168,85,247,0.1)", "rgba(168,85,247,0.1)"]
                    : ["rgba(168,85,247,0.18)", "rgba(139,92,246,0.25)"]
                }
                start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }}
                style={styles.demoBtn}
              >
                {demoLoading ? (
                  <>
                    <Animated.View style={{ transform: [{ rotate: spinDeg }] }}>
                      <Feather name="loader" size={16} color="#6b7280" />
                    </Animated.View>
                    <Text style={[styles.demoText, { color: "#6b7280" }]}>Signing in...</Text>
                  </>
                ) : (
                  <>
                    <Feather name="zap" size={16} color="#c4b5fd" />
                    <Text style={styles.demoText}>Demo Login — Quick Access</Text>
                  </>
                )}
              </LinearGradient>
            </Pressable>

            <Text style={styles.demoCaption}>All features available in demo account</Text>
          </View>

          {/* Footer */}
          <Text style={styles.footer}>
            By continuing, you agree to our{" "}
            <Text style={{ color: "#00d4ff" }}>Terms of Service</Text>
            {" "}and{" "}
            <Text style={{ color: "#00d4ff" }}>Privacy Policy</Text>
          </Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </View>
  );
}

function GoogleGIcon() {
  return (
    <Svg width={20} height={20} viewBox="0 0 18 18" fill="none">
      <Path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.716v2.259h2.908c1.702-1.567 2.684-3.875 2.684-6.615Z" fill="#4285F4"/>
      <Path d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18Z" fill="#34A853"/>
      <Path d="M3.964 10.706A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.706V4.962H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.038l3.007-2.332Z" fill="#FBBC05"/>
      <Path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.962L3.964 7.294C4.672 5.163 6.656 3.58 9 3.58Z" fill="#EA4335"/>
    </Svg>
  );
}

function delay(ms: number) { return new Promise(r => setTimeout(r, ms)); }

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: "#020d1a",
  },
  glowWrap: {
    position: "absolute",
    top: -80,
    left: "50%",
    marginLeft: -160,
    width: 320,
    height: 320,
    zIndex: 0,
  },
  glowCircle: {
    width: 320, height: 320, borderRadius: 160,
    backgroundColor: "rgba(0,198,255,0.08)",
  },

  scroll: {
    paddingHorizontal: 20,
    alignItems: "center",
  },

  // Logo
  logoWrap: { alignItems: "center", marginBottom: 28, gap: 10 },
  logoCircle: {
    width: 76, height: 76, borderRadius: 38,
    backgroundColor: "#041424",
    borderWidth: 1.5, borderColor: "rgba(0,198,255,0.35)",
    alignItems: "center", justifyContent: "center",
    shadowColor: "#00c6ff", shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.25, shadowRadius: 20, elevation: 8,
  },
  title: {
    fontSize: 26, fontWeight: "800", letterSpacing: 0.5,
    color: "#e0f4ff",
  },
  subtitle: { fontSize: 12, color: "#6b7280", textAlign: "center" },

  // Card
  card: {
    width: "100%", maxWidth: 380,
    backgroundColor: "rgba(255,255,255,0.04)",
    borderRadius: 20, padding: 24,
    borderWidth: 1, borderColor: "rgba(255,255,255,0.08)",
    gap: 16,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.4, shadowRadius: 32, elevation: 12,
  },

  fieldWrap: { gap: 6 },
  fieldLabel: {
    fontSize: 10, fontWeight: "800", letterSpacing: 2.5,
    color: "rgba(0,198,255,0.8)",
  },

  mobileRow: { flexDirection: "row", gap: 8 },
  prefix: {
    height: 48, paddingHorizontal: 12, borderRadius: 12,
    backgroundColor: "rgba(255,255,255,0.07)",
    borderWidth: 1, borderColor: "rgba(255,255,255,0.12)",
    alignItems: "center", justifyContent: "center",
  },
  prefixText: { fontSize: 14, color: "#9ca3af", fontWeight: "500" },

  input: {
    height: 48, borderRadius: 12, paddingHorizontal: 16,
    backgroundColor: "rgba(255,255,255,0.05)",
    borderWidth: 1,
    color: "white", fontSize: 15,
  },
  otpInput: {
    height: 56, fontSize: 22, letterSpacing: 10,
    fontWeight: "700",
  },
  otpInfo: {
    paddingHorizontal: 12, paddingVertical: 8, borderRadius: 10,
    backgroundColor: "rgba(0,198,255,0.08)",
    borderWidth: 1, borderColor: "rgba(0,198,255,0.2)",
  },
  otpInfoText: { fontSize: 12, color: "#67e8f9" },

  errorBox: {
    paddingHorizontal: 16, paddingVertical: 10, borderRadius: 12,
    backgroundColor: "rgba(239,68,68,0.1)",
    borderWidth: 1, borderColor: "rgba(239,68,68,0.25)",
  },
  errorText: { fontSize: 12, color: "#f87171" },

  ctaBtn: {
    height: 50, borderRadius: 12,
    alignItems: "center", justifyContent: "center",
    shadowColor: "#00c6ff", shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.35, shadowRadius: 14, elevation: 6,
  },
  ctaBtnDisabled: {
    shadowOpacity: 0, elevation: 0,
    borderWidth: 1, borderColor: "rgba(0,198,255,0.2)",
  },
  ctaText: { fontSize: 14, fontWeight: "700", letterSpacing: 0.5 },

  changeNum: { fontSize: 12, color: "#6b7280", textAlign: "center", paddingVertical: 4 },

  divider: { flexDirection: "row", alignItems: "center", gap: 12 },
  divLine: { flex: 1, height: 1, backgroundColor: "rgba(255,255,255,0.08)" },
  divText: { fontSize: 12, color: "#4b5563" },

  googleBtn: {
    height: 50, borderRadius: 12,
    backgroundColor: "rgba(255,255,255,0.07)",
    borderWidth: 1, borderColor: "rgba(255,255,255,0.12)",
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 10,
    shadowColor: "#000", shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25, shadowRadius: 6, elevation: 3,
  },
  googleText: { fontSize: 14, fontWeight: "600", color: "#e5e7eb" },

  // Demo section
  demoWrap: {
    width: "100%", maxWidth: 380, marginTop: 20, gap: 12, alignItems: "center",
  },
  demoBtn: {
    width: "100%", maxWidth: 380, height: 52, borderRadius: 16,
    borderWidth: 1, borderColor: "rgba(168,85,247,0.35)",
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8,
    shadowColor: "rgba(168,85,247,1)", shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.22, shadowRadius: 18, elevation: 5,
  },
  demoText: { fontSize: 14, fontWeight: "700", color: "#c4b5fd", letterSpacing: 0.3 },
  demoCaption: { fontSize: 12, color: "#374151" },

  // Footer
  footer: {
    fontSize: 11, color: "#374151", textAlign: "center",
    marginTop: 20, paddingHorizontal: 16, lineHeight: 18,
  },
});
