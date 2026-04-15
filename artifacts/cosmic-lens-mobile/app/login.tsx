import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useRef, useState } from "react";
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
import { getT } from "@/lib/i18n";

import { API_BASE, apiFetch } from "@/lib/apiConfig";

type Method = "mobile" | "email";
type EmailTab = "login" | "signup";

export default function LoginScreen() {
  const insets  = useSafeAreaInsets();
  const C       = useC();
  const { setUser, language } = useUser();
  const tr = getT(language);

  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;
  const isDark = C.isDark;

  // ── Method selector ──────────────────────────────────────────────────────────
  const [method, setMethod] = useState<Method>("mobile");

  // ── Mobile state ─────────────────────────────────────────────────────────────
  const [mobile,        setMobile]        = useState("");
  const [mobileLoading, setMobileLoading] = useState(false);
  const [mobileError,   setMobileError]   = useState("");

  // ── Email state ───────────────────────────────────────────────────────────────
  const [emailTab,  setEmailTab]  = useState<EmailTab>("login");
  const [name,      setName]      = useState("");
  const [email,     setEmail]     = useState("");
  const [password,  setPassword]  = useState("");
  const [showPwd,   setShowPwd]   = useState(false);
  const [emailLoading, setEmailLoading] = useState(false);
  const [emailError,   setEmailError]   = useState("");

  const emailRef    = useRef<TextInput>(null);
  const passwordRef = useRef<TextInput>(null);

  function finishLogin(u: AuthUser) {
    setUser(u);
    router.replace("/(tabs)");
  }

  // ── Mobile submit ─────────────────────────────────────────────────────────────
  async function handleMobileSubmit() {
    const digits = mobile.replace(/\D/g, "");
    if (digits.length < 7) {
      setMobileError("Valid mobile number enter karein"); return;
    }
    setMobileError(""); setMobileLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    try {
      const res = await apiFetch(`${API_BASE}/api/auth/mobile`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mobile: digits }),
      });
      const data = await res.json();
      if (!res.ok) { setMobileError(data.error || "Kuch galat hua"); return; }
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      finishLogin(data as AuthUser);
    } catch {
      setMobileError("Network error. Connection check karein.");
    } finally {
      setMobileLoading(false);
    }
  }

  // ── Email submit ──────────────────────────────────────────────────────────────
  async function handleEmailSubmit() {
    const trimEmail = email.trim().toLowerCase();
    const trimPwd   = password.trim();
    if (emailTab === "signup" && !name.trim()) {
      setEmailError("Please enter your name."); return;
    }
    if (!trimEmail || !trimEmail.includes("@")) {
      setEmailError("Please enter a valid email address."); return;
    }
    if (trimPwd.length < 6) {
      setEmailError("Password must be at least 6 characters."); return;
    }
    setEmailError(""); setEmailLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    try {
      const endpoint = emailTab === "signup" ? "/api/auth/signup" : "/api/auth/login";
      const body: Record<string, string> = { email: trimEmail, password: trimPwd };
      if (emailTab === "signup") body.name = name.trim();
      const res = await apiFetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) { setEmailError(data.error || "Something went wrong."); return; }
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      finishLogin(data as AuthUser);
    } catch {
      setEmailError("Network error. Please check your connection.");
    } finally {
      setEmailLoading(false);
    }
  }

  // ── Demo login ────────────────────────────────────────────────────────────────
  function handleDemoLogin() {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    finishLogin({
      id: 0,
      name: "Demo User",
      email: "demo@cosmic.local",
      api_key: "",
      is_pro: false,
    });
  }

  function switchMethod(m: Method) {
    setMethod(m);
    setMobileError(""); setEmailError("");
    Haptics.selectionAsync();
  }

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
            <Text style={[s.subtitle, { color: C.textMuted }]}>{tr.loginSubtitle}</Text>
          </View>

          {/* ── Method selector: Mobile | Email ── */}
          <View style={[s.methodRow, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <Pressable
              style={[s.methodBtn, method === "mobile" && [s.methodBtnActive, { borderColor: "rgba(245,158,11,0.35)", backgroundColor: isDark ? "rgba(245,158,11,0.08)" : "rgba(245,158,11,0.06)" }]]}
              onPress={() => switchMethod("mobile")}
            >
              <Feather name="smartphone" size={15} color={method === "mobile" ? "#f59e0b" : C.textMuted} />
              <Text style={[s.methodLabel, { color: method === "mobile" ? "#f59e0b" : C.textMuted }]}>
                Mobile Number
              </Text>
            </Pressable>
            <Pressable
              style={[s.methodBtn, method === "email" && [s.methodBtnActive, { borderColor: "rgba(99,102,241,0.35)", backgroundColor: isDark ? "rgba(99,102,241,0.08)" : "rgba(99,102,241,0.06)" }]]}
              onPress={() => switchMethod("email")}
            >
              <Feather name="mail" size={15} color={method === "email" ? "#a78bfa" : C.textMuted} />
              <Text style={[s.methodLabel, { color: method === "email" ? "#a78bfa" : C.textMuted }]}>
                Email & Password
              </Text>
            </Pressable>
          </View>

          {/* ── MOBILE PANEL ── */}
          {method === "mobile" && (
            <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border2, shadowColor: isDark ? "#7c3aed" : "#0F172A", shadowOpacity: isDark ? 0.18 : 0.12 }]}>
              <Text style={[s.fieldLabel, { color: "rgba(245,158,11,0.85)" }]}>
                MOBILE NUMBER
              </Text>
              {/* Phone row with +91 prefix */}
              <View style={[
                s.phoneRow,
                { backgroundColor: C.inputBg, borderColor: mobileError ? "rgba(239,68,68,0.5)" : C.inputBorder }
              ]}>
                <View style={[s.phonePrefix, { borderRightColor: C.border }]}>
                  <Text style={[s.phonePrefixFlag]}>🇮🇳</Text>
                  <Text style={[s.phonePrefixCode, { color: C.textMid }]}>+91</Text>
                </View>
                <TextInput
                  style={[s.phoneInput, { color: C.text }]}
                  value={mobile}
                  onChangeText={v => { setMobile(v.replace(/\D/g, "").slice(0, 10)); setMobileError(""); }}
                  placeholder="10-digit number"
                  placeholderTextColor={isDark ? "#3d2b6b" : "#94A3B8"}
                  keyboardType="number-pad"
                  maxLength={10}
                  returnKeyType="done"
                  onSubmitEditing={handleMobileSubmit}
                />
                {mobile.length > 0 && (
                  <Pressable onPress={() => { setMobile(""); setMobileError(""); }} hitSlop={10}>
                    <Feather name="x-circle" size={16} color={C.textMuted} />
                  </Pressable>
                )}
              </View>

              {!!mobileError && (
                <View style={s.errorBox}>
                  <Feather name="alert-circle" size={13} color="#f87171" />
                  <Text style={s.errorText}>{mobileError}</Text>
                </View>
              )}

              <Text style={[s.mobileNote, { color: C.textMuted }]}>
                Pehli baar number daalne par account automatic ban jaayega. Dubara daalne par seedha login ho jaayega.
              </Text>

              <Pressable
                onPress={handleMobileSubmit}
                disabled={mobileLoading || mobile.replace(/\D/g, "").length < 7}
                style={({ pressed }) => [{ opacity: (mobileLoading || mobile.replace(/\D/g, "").length < 7) ? 0.6 : pressed ? 0.85 : 1 }]}
              >
                <LinearGradient
                  colors={[C.btnGradStart, C.btnGradEnd]}
                  start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
                  style={[s.ctaBtn, !isDark && { shadowColor: "#EA580C", shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.35, shadowRadius: 10, elevation: 6 }]}
                >
                  {mobileLoading
                    ? <ActivityIndicator size="small" color="#fff" />
                    : (
                      <>
                        <Feather name="arrow-right" size={16} color="#fff" />
                        <Text style={s.ctaText}>Continue</Text>
                      </>
                    )
                  }
                </LinearGradient>
              </Pressable>
            </View>
          )}

          {/* ── EMAIL PANEL ── */}
          {method === "email" && (
            <View style={{ width: "100%", maxWidth: 380, gap: 12 }}>
              {/* Login / Signup sub-tabs */}
              <View style={[s.subTabs, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                {(["login", "signup"] as EmailTab[]).map(t => (
                  <Pressable
                    key={t}
                    onPress={() => { setEmailTab(t); setEmailError(""); setName(""); setEmail(""); setPassword(""); Haptics.selectionAsync(); }}
                    style={[s.subTab, emailTab === t && s.subTabActive]}
                  >
                    <Text style={[s.subTabText, { color: emailTab === t ? "#a78bfa" : C.textMuted }]}>
                      {t === "login" ? tr.logIn : tr.createAccount}
                    </Text>
                  </Pressable>
                ))}
              </View>

              <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border2, shadowColor: isDark ? "#7c3aed" : "#0F172A", shadowOpacity: isDark ? 0.18 : 0.12 }]}>
                {emailTab === "signup" && (
                  <View style={s.fieldWrap}>
                    <Text style={[s.fieldLabel, { color: "rgba(245,158,11,0.85)" }]}>{tr.yourName.toUpperCase()}</Text>
                    <FieldInput
                      icon="user"
                      value={name}
                      onChangeText={v => { setName(v); setEmailError(""); }}
                      placeholder="Full name"
                      returnKeyType="next"
                      onSubmitEditing={() => emailRef.current?.focus()}
                      autoCapitalize="words"
                      isDark={isDark}
                      inputBg={C.inputBg}
                      textColor={C.text}
                    />
                  </View>
                )}

                <View style={s.fieldWrap}>
                  <Text style={[s.fieldLabel, { color: "rgba(245,158,11,0.85)" }]}>{tr.emailAddr.toUpperCase()}</Text>
                  <FieldInput
                    ref={emailRef}
                    icon="mail"
                    value={email}
                    onChangeText={v => { setEmail(v); setEmailError(""); }}
                    placeholder="you@example.com"
                    keyboardType="email-address"
                    autoCapitalize="none"
                    returnKeyType="next"
                    onSubmitEditing={() => passwordRef.current?.focus()}
                    isDark={isDark}
                    inputBg={C.inputBg}
                    textColor={C.text}
                  />
                </View>

                <View style={s.fieldWrap}>
                  <Text style={[s.fieldLabel, { color: "rgba(245,158,11,0.85)" }]}>{tr.password.toUpperCase()}</Text>
                  <FieldInput
                    ref={passwordRef}
                    icon="lock"
                    value={password}
                    onChangeText={v => { setPassword(v); setEmailError(""); }}
                    placeholder={emailTab === "signup" ? "Min. 6 characters" : "Enter your password"}
                    secureTextEntry={!showPwd}
                    returnKeyType="done"
                    onSubmitEditing={handleEmailSubmit}
                    rightIcon={showPwd ? "eye-off" : "eye"}
                    onRightIconPress={() => setShowPwd(p => !p)}
                    isDark={isDark}
                    inputBg={C.inputBg}
                    textColor={C.text}
                  />
                </View>

                {!!emailError && (
                  <View style={s.errorBox}>
                    <Feather name="alert-circle" size={13} color="#f87171" />
                    <Text style={s.errorText}>{emailError}</Text>
                  </View>
                )}

                <Pressable
                  onPress={handleEmailSubmit}
                  disabled={emailLoading}
                  style={({ pressed }) => [{ opacity: emailLoading ? 0.75 : pressed ? 0.85 : 1 }]}
                >
                  <LinearGradient
                    colors={["#7c3aed", "#a78bfa"]}
                    start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
                    style={s.ctaBtn}
                  >
                    {emailLoading
                      ? <ActivityIndicator size="small" color="#fff" />
                      : (
                        <>
                          <Feather name={emailTab === "login" ? "log-in" : "user-plus"} size={16} color="#fff" />
                          <Text style={s.ctaText}>
                            {emailTab === "login" ? tr.logIn : tr.createAccount}
                          </Text>
                        </>
                      )
                    }
                  </LinearGradient>
                </Pressable>
              </View>
            </View>
          )}

          {/* ── DEMO LOGIN ── */}
          <View style={[s.demoWrap]}>
            <View style={s.divider}>
              <View style={[s.divLine, { backgroundColor: C.border }]} />
              <Text style={[s.divText, { color: C.textMuted }]}>ya phir</Text>
              <View style={[s.divLine, { backgroundColor: C.border }]} />
            </View>

            <Pressable
              onPress={handleDemoLogin}
              style={({ pressed }) => [{ opacity: pressed ? 0.8 : 1, width: "100%", maxWidth: 380 }]}
            >
              <View style={[s.demoBtn, { borderColor: isDark ? "rgba(245,158,11,0.3)" : "rgba(217,119,6,0.25)", backgroundColor: isDark ? "rgba(245,158,11,0.06)" : "rgba(245,158,11,0.05)" }]}>
                <View style={s.demoIconWrap}>
                  <Text style={{ fontSize: 14 }}>⚡</Text>
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={[s.demoBtnTitle, { color: "#f59e0b" }]}>Demo Login</Text>
                  <Text style={[s.demoBtnSub, { color: C.textMuted }]}>Testing ke liye — seedha andar jayein</Text>
                </View>
                <Feather name="chevron-right" size={16} color="#f59e0b" />
              </View>
            </Pressable>

            <Text style={[s.guestCaption, { color: C.textDim }]}>{tr.guestNote}</Text>
          </View>

          {/* Footer */}
          <Text style={[s.footer, { color: C.textMuted }]}>
            By continuing, you agree to our{" "}
            <Text style={{ color: "#f59e0b" }}>Terms of Service</Text>
            {" "}and{" "}
            <Text style={{ color: "#f59e0b" }}>Privacy Policy</Text>
          </Text>
        </ScrollView>
      </KeyboardAvoidingView>
    </CosmicBg>
  );
}

// ── FieldInput helper ──────────────────────────────────────────────────────────
interface FieldInputProps {
  icon: React.ComponentProps<typeof Feather>["name"];
  value: string;
  onChangeText: (v: string) => void;
  placeholder: string;
  keyboardType?: any;
  autoCapitalize?: any;
  returnKeyType?: any;
  onSubmitEditing?: () => void;
  secureTextEntry?: boolean;
  rightIcon?: React.ComponentProps<typeof Feather>["name"];
  onRightIconPress?: () => void;
  isDark: boolean;
  inputBg: string;
  textColor: string;
}

const FieldInput = React.forwardRef<TextInput, FieldInputProps>(
  ({ icon, rightIcon, onRightIconPress, isDark, inputBg, textColor, ...props }, ref) => {
    const C = useC();
    const [focused, setFocused] = useState(false);
    return (
      <View style={[
        fi.row,
        { backgroundColor: C.inputBg },
        focused
          ? { borderColor: C.inputFocusBorder }
          : { borderColor: C.inputBorder },
        focused && { shadowColor: C.inputFocusBorder, shadowOffset: { width: 0, height: 0 }, shadowOpacity: 0.25, shadowRadius: 5 },
      ]}>
        <Feather name={icon} size={16} color={focused ? C.inputFocusBorder : C.textMuted} />
        <TextInput
          ref={ref}
          style={[fi.input, { color: textColor }]}
          placeholderTextColor={isDark ? "#3d2b6b" : "#94A3B8"}
          autoCorrect={false}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          {...props}
        />
        {rightIcon && (
          <Pressable onPress={onRightIconPress} hitSlop={10}>
            <Feather name={rightIcon} size={16} color={isDark ? "#7c6fa0" : "#64748B"} />
          </Pressable>
        )}
      </View>
    );
  }
);

const fi = StyleSheet.create({
  row: {
    flexDirection: "row", alignItems: "center", gap: 10,
    borderRadius: 12, borderWidth: 1,
    paddingHorizontal: 14, paddingVertical: 13,
  },
  rowFocused: { borderColor: "rgba(245,158,11,0.45)" },
  input: { flex: 1, fontSize: 14, fontFamily: "Nunito_500Medium", padding: 0, margin: 0 },
});

const s = StyleSheet.create({
  root: { flex: 1 },

  glowWrap: { position: "absolute", top: -80, left: "50%", marginLeft: -160, width: 320, height: 320, zIndex: 0 },
  glowWrap2: { position: "absolute", bottom: 0, right: -80, width: 320, height: 320, zIndex: 0 },
  glowCircle: { width: 320, height: 320, borderRadius: 160 },

  scroll: { paddingHorizontal: 20, alignItems: "center", gap: 16 },

  logoWrap: { alignItems: "center", marginBottom: 4, gap: 8 },
  logoCircle: {
    width: 72, height: 72, borderRadius: 36, borderWidth: 1.5,
    alignItems: "center", justifyContent: "center",
    shadowOffset: { width: 0, height: 0 }, shadowOpacity: 0.3, shadowRadius: 20, elevation: 8,
  },
  title: { fontSize: 26, fontFamily: "Nunito_700Bold", letterSpacing: 0.4 },
  subtitle: { fontSize: 12, fontFamily: "Nunito_400Regular", textAlign: "center" },

  // Method selector
  methodRow: {
    flexDirection: "row", width: "100%", maxWidth: 380,
    borderRadius: 16, padding: 4, borderWidth: 1, gap: 4,
  },
  methodBtn: {
    flex: 1, flexDirection: "row", alignItems: "center", justifyContent: "center",
    gap: 7, paddingVertical: 11, borderRadius: 12, borderWidth: 1, borderColor: "transparent",
  },
  methodBtnActive: { borderWidth: 1 },
  methodLabel: { fontSize: 13, fontFamily: "Nunito_600SemiBold" },

  // Sub-tabs (email login/signup)
  subTabs: {
    flexDirection: "row", width: "100%",
    borderRadius: 14, padding: 3, borderWidth: 1,
  },
  subTab: { flex: 1, paddingVertical: 9, borderRadius: 11, alignItems: "center" },
  subTabActive: { backgroundColor: "rgba(167,139,250,0.10)" },
  subTabText: { fontSize: 13, fontFamily: "Nunito_600SemiBold" },

  // Card
  card: {
    width: "100%", maxWidth: 380, borderRadius: 20, padding: 20,
    borderWidth: 1, gap: 14,
    shadowColor: "#7c3aed",
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.18, shadowRadius: 24, elevation: 10,
  },
  fieldWrap: { gap: 7 },
  fieldLabel: { fontSize: 10, fontFamily: "Nunito_700Bold", letterSpacing: 2 },

  // Phone input
  phoneRow: {
    flexDirection: "row", alignItems: "center",
    borderRadius: 12, borderWidth: 1, overflow: "hidden",
  },
  phonePrefix: {
    flexDirection: "row", alignItems: "center", gap: 5,
    paddingHorizontal: 12, paddingVertical: 13,
    borderRightWidth: 1,
  },
  phonePrefixFlag: { fontSize: 16 },
  phonePrefixCode: { fontSize: 14, fontFamily: "Nunito_600SemiBold" },
  phoneInput: {
    flex: 1, fontSize: 15, fontFamily: "Nunito_500Medium",
    padding: 0, paddingHorizontal: 12, paddingVertical: 13,
  },
  mobileNote: {
    fontSize: 11, fontFamily: "Nunito_400Regular",
    lineHeight: 17, textAlign: "center",
  },

  // Error
  errorBox: {
    flexDirection: "row", alignItems: "flex-start", gap: 8,
    backgroundColor: "rgba(239,68,68,0.08)",
    borderWidth: 1, borderColor: "rgba(239,68,68,0.22)",
    borderRadius: 10, paddingHorizontal: 12, paddingVertical: 10,
  },
  errorText: { fontSize: 12, fontFamily: "Nunito_500Medium", color: "#f87171", flex: 1 },

  // CTA button
  ctaBtn: {
    height: 50, borderRadius: 14,
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8,
    shadowColor: "#7c3aed",
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.4, shadowRadius: 16, elevation: 6,
  },
  ctaText: { fontSize: 15, fontFamily: "Nunito_700Bold", letterSpacing: 0.3, color: "#fff" },

  // Demo section
  demoWrap: {
    width: "100%", maxWidth: 380, gap: 12, alignItems: "center", marginTop: 4,
  },
  divider: { flexDirection: "row", alignItems: "center", gap: 12, width: "100%" },
  divLine: { flex: 1, height: 1 },
  divText: { fontSize: 11, fontFamily: "Nunito_400Regular" },
  demoBtn: {
    flexDirection: "row", alignItems: "center", gap: 12,
    paddingVertical: 14, paddingHorizontal: 16,
    borderRadius: 16, borderWidth: 1,
  },
  demoIconWrap: {
    width: 34, height: 34, borderRadius: 10,
    backgroundColor: "rgba(245,158,11,0.12)",
    alignItems: "center", justifyContent: "center",
  },
  demoBtnTitle: { fontSize: 14, fontFamily: "Nunito_700Bold" },
  demoBtnSub: { fontSize: 11, fontFamily: "Nunito_400Regular", marginTop: 1 },
  guestCaption: { fontSize: 11, fontFamily: "Nunito_400Regular", textAlign: "center" },

  // Footer
  footer: {
    fontSize: 11, fontFamily: "Nunito_400Regular",
    textAlign: "center", paddingHorizontal: 20, lineHeight: 18, marginTop: 4,
  },
});
