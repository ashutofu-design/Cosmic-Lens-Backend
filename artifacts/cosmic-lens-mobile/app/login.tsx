import { Feather } from "@expo/vector-icons";
import { BlurView } from "expo-blur";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Animated,
  Easing,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  useWindowDimensions,
  View,
  type ViewStyle,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { GalaxyStarfield } from "@/components/GalaxyStarfield";
import { FadeInView } from "@/components/motion/FadeInView";
import { useC } from "@/context/ThemeContext";
import { useUser, type AuthUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import {
  demoLogin,
  isDemoLoginEnabled,
  verifyFirebaseIdToken,
} from "@/lib/authBackend";
import { signInWithGoogle } from "@/lib/firebaseAuth";
import { isFirebaseConfigured } from "@/lib/firebaseConfig";

const WEB_GLASS = Platform.OS === "web"
  ? ({
      backdropFilter: "blur(18px) saturate(145%)",
      WebkitBackdropFilter: "blur(18px) saturate(145%)",
      backgroundColor: "rgba(8,5,20,0.28)",
    } as ViewStyle)
  : {};

function FrostedLoginCard({
  width,
  compact,
  children,
}: {
  width: number;
  compact?: boolean;
  children: React.ReactNode;
}) {
  return (
    <View style={[s.cardShell, compact && s.cardShellCompact, { width }]}>
      {Platform.OS !== "web" ? (
        <BlurView
          intensity={Platform.OS === "ios" ? 28 : 48}
          tint="dark"
          style={StyleSheet.absoluteFill}
        />
      ) : (
        <View style={[StyleSheet.absoluteFill, WEB_GLASS]} />
      )}
      <View style={s.cardGlassTint} />
      <LinearGradient
        colors={["rgba(255,255,255,0.08)", "rgba(255,255,255,0.02)", "transparent"]}
        start={{ x: 0, y: 0 }}
        end={{ x: 0, y: 1 }}
        style={s.cardShine}
      />
      <LinearGradient
        colors={["transparent", "rgba(8,4,22,0.12)", "rgba(6,3,18,0.22)"]}
        start={{ x: 0.5, y: 0 }}
        end={{ x: 0.5, y: 1 }}
        style={s.cardReadabilityVeil}
        pointerEvents="none"
      />
      <View style={[s.cardInner, compact && s.cardInnerCompact]}>{children}</View>
    </View>
  );
}

export default function LoginScreen() {
  const insets = useSafeAreaInsets();
  const { width, height } = useWindowDimensions();
  const t = useT();
  const { setUser, language } = useUser();

  const compact = height < 720 || width < 360;
  const topPad = Platform.OS === "web" ? Math.max(insets.top, 12) : insets.top;
  const botPad = Platform.OS === "web" ? Math.max(insets.bottom, 24) : insets.bottom;
  const isHindi = language === "hi" || language === "hn";
  const cardW = Math.min(width - (compact ? 28 : 36), 400);
  const stackGap = compact ? 20 : 26;
  const brandGap = compact ? 7 : 9;

  const [loading, setLoading] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const [error, setError] = useState("");
  const showDemo = isDemoLoginEnabled();

  const titleGlow = useRef(new Animated.Value(0.4)).current;

  useEffect(() => {
    const title = Animated.loop(
      Animated.sequence([
        Animated.timing(titleGlow, {
          toValue: 0.85,
          duration: 3200,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(titleGlow, {
          toValue: 0.35,
          duration: 3200,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ]),
    );
    title.start();
    return () => title.stop();
  }, [titleGlow]);

  async function finishLogin(u: AuthUser) {
    await setUser(u);
    router.replace("/welcome-reveal");
  }

  async function handleDemoLogin() {
    setError("");
    setDemoLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});

    try {
      const u = await demoLogin();
      await setUser(u);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
      router.replace("/");
    } catch (e: unknown) {
      const msg = String((e as Error)?.message || e || "");
      setError(msg || (isHindi ? "Demo login fail." : "Demo login failed."));
    } finally {
      setDemoLoading(false);
    }
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

  return (
    <View style={s.root}>
      <GalaxyStarfield />

      <View
        style={[
          s.content,
          {
            paddingTop: topPad + (compact ? 6 : 10),
            paddingBottom: botPad + (compact ? 8 : 10),
            paddingHorizontal: compact ? 14 : 18,
          },
        ]}
      >
        <View style={[s.centerCol, { gap: stackGap }]}>
          <FadeInView delay={0} style={[s.brandBlock, { gap: brandGap }]}>
            <Animated.Text
              style={[
                s.title,
                compact && s.titleCompact,
                {
                  opacity: titleGlow.interpolate({
                    inputRange: [0.35, 0.85],
                    outputRange: [0.96, 1],
                  }),
                },
              ]}
            >
              Cosmic Lens
            </Animated.Text>
            <View style={[s.trustRow, compact && s.trustRowCompact]}>
              <Feather name="shield" size={compact ? 10 : 11} color="#a78bfa" />
              <Text style={[s.trustText, compact && s.trustTextCompact]}>
                Powered by Cosmic Intelligence Engine
              </Text>
            </View>
          </FadeInView>

          <FadeInView delay={120} style={{ width: cardW, alignItems: "center", marginTop: compact ? -2 : 0 }}>
            <FrostedLoginCard width={cardW} compact={compact}>
              {!!error && (
                <View style={s.errorBox}>
                  <Feather name="alert-circle" size={13} color="#f87171" />
                  <Text style={s.errorText}>{error}</Text>
                </View>
              )}

              <Text style={s.note}>
                {isHindi
                  ? "Pehli baar sign-in par account khud ban jayega."
                  : "Your account is created automatically on first sign-in."}
              </Text>

              <Pressable
                onPress={handleGoogleLogin}
                disabled={loading || demoLoading}
                style={({ pressed }) => [
                  s.googleBtnWrap,
                  { opacity: loading || demoLoading ? 0.65 : pressed ? 0.9 : 1 },
                ]}
              >
                <LinearGradient
                  colors={["#ffffff", "#f8fafc"]}
                  style={s.googleBtn}
                >
                  {loading ? (
                    <ActivityIndicator size="small" color="#4285F4" />
                  ) : (
                    <>
                      <View style={s.googleIconWrap}>
                        <Text style={s.googleG}>G</Text>
                      </View>
                      <Text style={s.googleBtnText}>
                        {isHindi ? "Google se continue karein" : "Continue with Google"}
                      </Text>
                    </>
                  )}
                </LinearGradient>
              </Pressable>

              {showDemo && (
                <>
                  <View style={s.orRow}>
                    <View style={s.orLine} />
                    <Text style={s.orText}>{isHindi ? "ya" : "or"}</Text>
                    <View style={s.orLine} />
                  </View>

                  <Pressable
                    onPress={handleDemoLogin}
                    disabled={loading || demoLoading}
                    style={({ pressed }) => [
                      s.demoBtn,
                      { opacity: loading || demoLoading ? 0.65 : pressed ? 0.88 : 1 },
                    ]}
                  >
                    {demoLoading ? (
                      <ActivityIndicator size="small" color="#fbbf24" />
                    ) : (
                      <>
                        <Feather name="zap" size={18} color="#fbbf24" />
                        <View style={{ flex: 1, alignItems: "center" }}>
                          <Text style={s.demoBtnTitle}>{t.demoLogin}</Text>
                          <Text style={s.demoBtnSub}>{t.demoLoginSub}</Text>
                        </View>
                        <Feather name="chevron-right" size={16} color="rgba(251,191,36,0.7)" />
                      </>
                    )}
                  </Pressable>
                </>
              )}
            </FrostedLoginCard>
          </FadeInView>

          <FadeInView delay={240} style={[s.footerBlock, compact && s.footerBlockCompact]}>
            <View style={s.footerRule} />
            <Text style={s.footer}>
              {t.termsAccept}{" "}
              <Text style={s.footerLink}>{t.termsLink}</Text>
              {" & "}
              <Text style={s.footerLink}>{t.privacyLink}</Text>
            </Text>
            {__DEV__ && Platform.OS !== "web" && (
              <Text style={s.devBundleHint}>
                Live bundle · login-v2 · Demo {showDemo ? "on" : "off"}
              </Text>
            )}
          </FadeInView>
        </View>
      </View>
    </View>
  );
}

const s = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: "#000000",
  },
  content: {
    flex: 1,
    zIndex: 2,
  },
  centerCol: {
    flex: 1,
    width: "100%",
    maxWidth: 440,
    alignSelf: "center",
    justifyContent: "center",
    alignItems: "center",
  },
  brandBlock: {
    alignItems: "center",
    paddingHorizontal: 8,
    width: "100%",
  },
  title: {
    fontSize: 34,
    lineHeight: 40,
    fontFamily: "Nunito_700Bold",
    color: "#FFFFFF",
    letterSpacing: 3.6,
    textAlign: "center",
    textShadowColor: "rgba(167,139,250,0.22)",
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 10,
    ...(Platform.OS === "android" ? { includeFontPadding: false } : {}),
  },
  titleCompact: {
    fontSize: 30,
    lineHeight: 36,
    letterSpacing: 2.8,
    textShadowRadius: 8,
    textShadowColor: "rgba(167,139,250,0.18)",
  },
  trustRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    maxWidth: 340,
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 999,
    backgroundColor: "rgba(124,58,237,0.12)",
    borderWidth: 1,
    borderColor: "rgba(167,139,250,0.2)",
  },
  trustRowCompact: {
    maxWidth: 300,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  trustText: {
    flexShrink: 1,
    fontSize: 10.5,
    fontFamily: "Nunito_600SemiBold",
    color: "rgba(196,181,253,0.95)",
    letterSpacing: 0.35,
    textAlign: "center",
  },
  trustTextCompact: {
    fontSize: 9.5,
    letterSpacing: 0.25,
  },
  cardShell: {
    borderRadius: 26,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.09)",
    shadowColor: "#7c3aed",
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.18,
    shadowRadius: 18,
    elevation: 8,
  },
  cardShellCompact: {
    borderRadius: 24,
    shadowOffset: { width: 0, height: 8 },
    shadowRadius: 14,
    shadowOpacity: 0.14,
  },
  cardGlassTint: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(12,7,28,0.34)",
  },
  cardReadabilityVeil: {
    ...StyleSheet.absoluteFillObject,
    zIndex: 1,
  },
  cardShine: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    height: 48,
    zIndex: 1,
  },
  cardInner: {
    paddingVertical: 22,
    paddingHorizontal: 22,
    gap: 14,
    alignItems: "center",
    zIndex: 2,
  },
  cardInnerCompact: {
    paddingVertical: 18,
    paddingHorizontal: 18,
    gap: 11,
  },
  errorBox: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    width: "100%",
    paddingHorizontal: 2,
  },
  errorText: {
    flex: 1,
    fontSize: 12,
    color: "#fca5a5",
    fontFamily: "Nunito_500Medium",
  },
  note: {
    fontSize: 12.5,
    fontFamily: "Nunito_400Regular",
    color: "rgba(226,232,240,0.9)",
    textAlign: "center",
    lineHeight: 18,
    paddingHorizontal: 4,
    letterSpacing: 0.12,
  },
  googleBtnWrap: {
    width: "100%",
    alignItems: "center",
  },
  googleBtn: {
    width: "100%",
    maxWidth: 328,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    minHeight: 48,
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.35)",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.22,
    shadowRadius: 14,
    elevation: 8,
  },
  googleIconWrap: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: "#fff",
    alignItems: "center",
    justifyContent: "center",
    shadowColor: "#4285F4",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 2,
  },
  googleG: {
    fontSize: 17,
    fontFamily: "Nunito_800ExtraBold",
    color: "#4285F4",
  },
  googleBtnText: {
    fontSize: 16,
    fontFamily: "Nunito_700Bold",
    color: "#0f172a",
    letterSpacing: 0.2,
  },
  orRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    width: "100%",
    paddingVertical: 0,
    marginVertical: -2,
  },
  orLine: {
    flex: 1,
    height: 1,
    backgroundColor: "rgba(255,255,255,0.1)",
  },
  orText: {
    fontSize: 11,
    fontFamily: "Nunito_600SemiBold",
    color: "rgba(203,213,225,0.88)",
    textTransform: "lowercase",
  },
  demoBtn: {
    width: "100%",
    maxWidth: 328,
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    minHeight: 48,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 16,
    borderWidth: 1.5,
    borderColor: "rgba(251,191,36,0.45)",
    backgroundColor: "rgba(251,191,36,0.1)",
  },
  demoBtnTitle: {
    fontSize: 15,
    fontFamily: "Nunito_700Bold",
    color: "#fde68a",
    letterSpacing: 0.3,
  },
  demoBtnSub: {
    fontSize: 11,
    fontFamily: "Nunito_500Medium",
    color: "rgba(251,191,36,0.75)",
    marginTop: 2,
  },
  footerBlock: {
    alignItems: "center",
    gap: 11,
    paddingTop: 2,
    width: "100%",
    maxWidth: 360,
  },
  footerBlockCompact: {
    gap: 9,
    paddingTop: 0,
  },
  footerRule: {
    width: 48,
    height: 1,
    backgroundColor: "rgba(167,139,250,0.35)",
    borderRadius: 1,
  },
  footer: {
    fontSize: 11.5,
    fontFamily: "Nunito_400Regular",
    color: "rgba(148,163,184,0.9)",
    textAlign: "center",
    lineHeight: 18,
    paddingHorizontal: 20,
    letterSpacing: 0.25,
  },
  footerLink: {
    color: "#fcd34d",
    fontFamily: "Nunito_700Bold",
  },
  devBundleHint: {
    marginTop: 8,
    fontSize: 9,
    fontFamily: "Nunito_400Regular",
    color: "rgba(100,116,139,0.75)",
    textAlign: "center",
  },
});
