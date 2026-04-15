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
import { useC } from "@/context/ThemeContext";
import { useUser, type AuthUser } from "@/context/UserContext";
import { getT } from "@/lib/i18n";

const API_BASE = `https://${process.env.EXPO_PUBLIC_DOMAIN}`;

type Tab = "login" | "signup";

export default function LoginScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const { setUser, language } = useUser();
  const tr = getT(language);

  const [tab,      setTab]      = useState<Tab>("login");
  const [name,     setName]     = useState("");
  const [email,    setEmail]    = useState("");
  const [password, setPassword] = useState("");
  const [showPwd,  setShowPwd]  = useState(false);
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState("");

  const emailRef    = useRef<TextInput>(null);
  const passwordRef = useRef<TextInput>(null);

  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;

  function finishLogin(u: AuthUser) {
    setUser(u);
    router.replace("/(tabs)");
  }

  async function handleSubmit() {
    const trimEmail = email.trim().toLowerCase();
    const trimPwd   = password.trim();

    if (tab === "signup" && !name.trim()) {
      setError("Please enter your name."); return;
    }
    if (!trimEmail || !trimEmail.includes("@")) {
      setError("Please enter a valid email address."); return;
    }
    if (trimPwd.length < 6) {
      setError("Password must be at least 6 characters."); return;
    }

    setError(""); setLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);

    try {
      const endpoint = tab === "signup" ? "/api/auth/signup" : "/api/auth/login";
      const body: Record<string, string> = { email: trimEmail, password: trimPwd };
      if (tab === "signup") body.name = name.trim();

      const res  = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();

      if (!res.ok) {
        setError(data.error || "Something went wrong. Please try again.");
        return;
      }

      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      finishLogin(data as AuthUser);
    } catch {
      setError("Network error. Please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  }

  function handleGuestContinue() {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    router.replace("/(tabs)");
  }

  function switchTab(t: Tab) {
    setTab(t); setError(""); setName(""); setEmail(""); setPassword("");
    Haptics.selectionAsync();
  }

  const isDark = C.isDark;

  return (
    <View style={[s.root, { backgroundColor: C.bg }]}>
      {/* Ambient glow — purple mist */}
      <View style={[s.glowWrap, { pointerEvents: "none" }]}>
        <View style={[s.glowCircle, { backgroundColor: isDark ? "rgba(139,92,246,0.10)" : "rgba(139,92,246,0.06)" }]} />
      </View>
      {/* Gold mist bottom */}
      <View style={[s.glowWrap2, { pointerEvents: "none" }]}>
        <View style={[s.glowCircle, { backgroundColor: isDark ? "rgba(245,158,11,0.06)" : "rgba(245,158,11,0.04)", borderRadius: 160 }]} />
      </View>

      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        keyboardVerticalOffset={Platform.OS === "ios" ? 0 : 20}
      >
        <ScrollView
          contentContainerStyle={[s.scroll, { paddingTop: topPad + 40, paddingBottom: botPad + 24 }]}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {/* ── Logo ── */}
          <View style={s.logoWrap}>
            <View style={[s.logoCircle, {
              backgroundColor: isDark ? "#1a1330" : "#f3ebff",
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

          {/* ── Tab switcher ── */}
          <View style={[s.tabs, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            {(["login", "signup"] as Tab[]).map(t => (
              <Pressable key={t} onPress={() => switchTab(t)} style={[s.tab, tab === t && s.tabActive]}>
                <Text style={[s.tabText, { color: tab === t ? "#f59e0b" : C.textMuted }]}>
                  {t === "login" ? tr.logIn : tr.createAccount}
                </Text>
              </Pressable>
            ))}
          </View>

          {/* ── Card ── */}
          <View style={[s.card, { backgroundColor: C.bgCard, borderColor: C.border2 }]}>

            {/* Name (signup only) */}
            {tab === "signup" && (
              <View style={s.fieldWrap}>
                <Text style={[s.fieldLabel, { color: "rgba(245,158,11,0.85)" }]}>{tr.yourName.toUpperCase()}</Text>
                <FieldInput
                  icon="user"
                  value={name}
                  onChangeText={v => { setName(v); setError(""); }}
                  placeholder="Full name"
                  returnKeyType="next"
                  onSubmitEditing={() => emailRef.current?.focus()}
                  autoCapitalize="words"
                  isDark={isDark}
                  inputBg={C.inputBg}
                />
              </View>
            )}

            {/* Email */}
            <View style={s.fieldWrap}>
              <Text style={[s.fieldLabel, { color: "rgba(245,158,11,0.85)" }]}>{tr.emailAddr.toUpperCase()}</Text>
              <FieldInput
                ref={emailRef}
                icon="mail"
                value={email}
                onChangeText={v => { setEmail(v); setError(""); }}
                placeholder="you@example.com"
                keyboardType="email-address"
                autoCapitalize="none"
                returnKeyType="next"
                onSubmitEditing={() => passwordRef.current?.focus()}
                isDark={isDark}
                inputBg={C.inputBg}
              />
            </View>

            {/* Password */}
            <View style={s.fieldWrap}>
              <Text style={[s.fieldLabel, { color: "rgba(245,158,11,0.85)" }]}>{tr.password.toUpperCase()}</Text>
              <FieldInput
                ref={passwordRef}
                icon="lock"
                value={password}
                onChangeText={v => { setPassword(v); setError(""); }}
                placeholder={tab === "signup" ? "Min. 6 characters" : "Enter your password"}
                secureTextEntry={!showPwd}
                returnKeyType="done"
                onSubmitEditing={handleSubmit}
                rightIcon={showPwd ? "eye-off" : "eye"}
                onRightIconPress={() => setShowPwd(p => !p)}
                isDark={isDark}
                inputBg={C.inputBg}
              />
            </View>

            {/* Error */}
            {!!error && (
              <View style={s.errorBox}>
                <Feather name="alert-circle" size={13} color="#f87171" />
                <Text style={s.errorText}>{error}</Text>
              </View>
            )}

            {/* Submit */}
            <Pressable
              onPress={handleSubmit}
              disabled={loading}
              style={({ pressed }) => [{ opacity: loading ? 0.75 : pressed ? 0.85 : 1 }]}
            >
              <LinearGradient
                colors={["#7c3aed", "#f59e0b"]}
                start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }}
                style={s.ctaBtn}
              >
                {loading
                  ? <ActivityIndicator size="small" color="#fff" />
                  : (
                    <>
                      <Feather name={tab === "login" ? "log-in" : "user-plus"} size={16} color="#fff" />
                      <Text style={s.ctaText}>
                        {tab === "login" ? tr.logIn : tr.createAccount}
                      </Text>
                    </>
                  )
                }
              </LinearGradient>
            </Pressable>
          </View>

          {/* ── Guest continue ── */}
          <View style={s.guestWrap}>
            <View style={[s.divider]}>
              <View style={[s.divLine, { backgroundColor: C.border }]} />
              <Text style={[s.divText, { color: C.textMuted }]}>or</Text>
              <View style={[s.divLine, { backgroundColor: C.border }]} />
            </View>
            <Pressable
              onPress={handleGuestContinue}
              style={({ pressed }) => [s.guestBtn, { borderColor: C.border2, backgroundColor: C.bgCard }, pressed && { opacity: 0.7 }]}
            >
              <Feather name="arrow-right" size={14} color={C.textMuted} />
              <Text style={[s.guestText, { color: C.textMuted }]}>{tr.continueGuest}</Text>
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
    </View>
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
}

const FieldInput = React.forwardRef<TextInput, FieldInputProps>(
  ({ icon, rightIcon, onRightIconPress, isDark, inputBg, ...props }, ref) => {
    const [focused, setFocused] = useState(false);
    return (
      <View style={[
        fi.row,
        { backgroundColor: inputBg },
        focused ? fi.rowFocused : { borderColor: isDark ? "rgba(139,92,246,0.18)" : "rgba(109,40,217,0.13)" },
      ]}>
        <Feather name={icon} size={16} color={focused ? "#f59e0b" : (isDark ? "#7c6fa0" : "#9f7aea")} />
        <TextInput
          ref={ref}
          style={[fi.input, { color: isDark ? "#f0e6ff" : "#1e0a3c" }]}
          placeholderTextColor={isDark ? "#3d2b6b" : "#b39ddb"}
          autoCorrect={false}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          {...props}
        />
        {rightIcon && (
          <Pressable onPress={onRightIconPress} hitSlop={10}>
            <Feather name={rightIcon} size={16} color={isDark ? "#7c6fa0" : "#9f7aea"} />
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
  rowFocused: {
    borderColor: "rgba(245,158,11,0.45)",
  },
  input: {
    flex: 1, fontSize: 14,
    fontFamily: "Nunito_500Medium",
    padding: 0, margin: 0,
  },
});

const s = StyleSheet.create({
  root: { flex: 1 },

  glowWrap: {
    position: "absolute", top: -80, left: "50%", marginLeft: -160,
    width: 320, height: 320, zIndex: 0,
  },
  glowWrap2: {
    position: "absolute", bottom: 0, right: -80,
    width: 320, height: 320, zIndex: 0,
  },
  glowCircle: { width: 320, height: 320, borderRadius: 160 },

  scroll: { paddingHorizontal: 20, alignItems: "center" },

  // Logo
  logoWrap: { alignItems: "center", marginBottom: 24, gap: 10 },
  logoCircle: {
    width: 76, height: 76, borderRadius: 38,
    borderWidth: 1.5,
    alignItems: "center", justifyContent: "center",
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.3, shadowRadius: 20, elevation: 8,
  },
  title: {
    fontSize: 26, fontFamily: "Nunito_700Bold",
    letterSpacing: 0.4,
  },
  subtitle: {
    fontSize: 12,
    fontFamily: "Nunito_400Regular", textAlign: "center",
  },

  // Tabs
  tabs: {
    flexDirection: "row", width: "100%", maxWidth: 380,
    borderRadius: 14, padding: 3, marginBottom: 16,
    borderWidth: 1,
  },
  tab: {
    flex: 1, paddingVertical: 10, borderRadius: 11,
    alignItems: "center",
  },
  tabActive: { backgroundColor: "rgba(245,158,11,0.10)" },
  tabText: { fontSize: 13, fontFamily: "Nunito_600SemiBold" },

  // Card
  card: {
    width: "100%", maxWidth: 380,
    borderRadius: 20, padding: 22,
    borderWidth: 1,
    gap: 14,
    shadowColor: "#7c3aed",
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.2, shadowRadius: 30, elevation: 12,
  },
  fieldWrap: { gap: 7 },
  fieldLabel: {
    fontSize: 10, fontFamily: "Nunito_700Bold",
    letterSpacing: 2,
  },

  // Error
  errorBox: {
    flexDirection: "row", alignItems: "flex-start", gap: 8,
    backgroundColor: "rgba(239,68,68,0.08)",
    borderWidth: 1, borderColor: "rgba(239,68,68,0.22)",
    borderRadius: 10, paddingHorizontal: 12, paddingVertical: 10,
  },
  errorText: { fontSize: 12, fontFamily: "Nunito_500Medium", color: "#f87171", flex: 1 },

  // CTA
  ctaBtn: {
    height: 50, borderRadius: 14,
    flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 8,
    shadowColor: "#7c3aed",
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.4, shadowRadius: 16, elevation: 6,
  },
  ctaText: {
    fontSize: 15, fontFamily: "Nunito_700Bold",
    letterSpacing: 0.3, color: "#fff",
  },

  // Guest
  guestWrap: {
    width: "100%", maxWidth: 380, marginTop: 22, gap: 12, alignItems: "center",
  },
  divider: { flexDirection: "row", alignItems: "center", gap: 12, width: "100%" },
  divLine: { flex: 1, height: 1 },
  divText: { fontSize: 11, fontFamily: "Nunito_400Regular" },
  guestBtn: {
    flexDirection: "row", alignItems: "center", gap: 8,
    paddingVertical: 10, paddingHorizontal: 20,
    borderRadius: 12, borderWidth: 1,
  },
  guestText: { fontSize: 13, fontFamily: "Nunito_600SemiBold" },
  guestCaption: {
    fontSize: 11, fontFamily: "Nunito_400Regular", textAlign: "center",
  },

  // Footer
  footer: {
    fontSize: 11, fontFamily: "Nunito_400Regular",
    textAlign: "center",
    marginTop: 20, paddingHorizontal: 20, lineHeight: 18,
  },
});
