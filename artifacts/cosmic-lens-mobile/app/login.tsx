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
import { verifyFirebaseIdToken } from "@/lib/authBackend";
import { signInWithGoogle } from "@/lib/firebaseAuth";
import { isFirebaseConfigured } from "@/lib/firebaseConfig";

const WEB_GLASS = Platform.OS === "web"
  ? ({
      backdropFilter: "blur(24px) saturate(160%)",
      WebkitBackdropFilter: "blur(24px) saturate(160%)",
    } as ViewStyle)
  : {};

function FrostedLoginCard({
  width,
  children,
}: {
  width: number;
  children: React.ReactNode;
}) {
  return (
    <View style={[s.cardShell, { width }]}>
      {Platform.OS !== "web" ? (
        <BlurView
          intensity={Platform.OS === "ios" ? 42 : 72}
          tint="dark"
          style={StyleSheet.absoluteFill}
        />
      ) : (
        <View style={[StyleSheet.absoluteFill, WEB_GLASS]} />
      )}
      <View style={s.cardGlassTint} />
      <LinearGradient
        colors={["rgba(255,255,255,0.14)", "rgba(255,255,255,0.02)", "transparent"]}
        start={{ x: 0, y: 0 }}
        end={{ x: 0, y: 1 }}
        style={s.cardShine}
      />
      <View style={s.cardInner}>{children}</View>
    </View>
  );
}

export default function LoginScreen() {
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  const t = useT();
  const { setUser, language } = useUser();

  const topPad = Platform.OS === "web" ? Math.max(insets.top, 12) : insets.top;
  const botPad = Platform.OS === "web" ? Math.max(insets.bottom, 24) : insets.bottom;
  const isHindi = language === "hi" || language === "hn";
  const cardW = Math.min(width - 36, 400);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

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
          { paddingTop: topPad + 20, paddingBottom: botPad + 12, paddingHorizontal: 18 },
        ]}
      >
        <View style={s.centerCol}>
          <FadeInView delay={0} style={s.brandBlock}>
            <Animated.Text
              style={[
                s.title,
                {
                  opacity: titleGlow.interpolate({
                    inputRange: [0.35, 0.85],
                    outputRange: [0.92, 1],
                  }),
                },
              ]}
            >
              Cosmic Lens
            </Animated.Text>
            <Text style={s.subtitle}>
              {isHindi
                ? "Gmail se login — OTP ki zarurat nahi"
                : "Sign in with Gmail — no OTP needed"}
            </Text>
            <View style={s.trustRow}>
              <Feather name="shield" size={11} color="#a78bfa" />
              <Text style={s.trustText}>
                {isHindi ? "Surakshit · Private · Vedic precision" : "Secure · Private · Vedic precision"}
              </Text>
            </View>
          </FadeInView>

          <FadeInView delay={120} style={{ width: cardW, alignItems: "center" }}>
            <FrostedLoginCard width={cardW}>
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
                disabled={loading}
                style={({ pressed }) => [
                  s.googleBtnWrap,
                  { opacity: loading ? 0.65 : pressed ? 0.9 : 1 },
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
            </FrostedLoginCard>
          </FadeInView>

          <FadeInView delay={240} style={s.footerBlock}>
            <View style={s.footerRule} />
            <Text style={s.footer}>
              {t.termsAccept}{" "}
              <Text style={s.footerLink}>{t.termsLink}</Text>
              {" & "}
              <Text style={s.footerLink}>{t.privacyLink}</Text>
            </Text>
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
    gap: 32,
  },
  brandBlock: {
    alignItems: "center",
    gap: 12,
    paddingHorizontal: 8,
  },
  title: {
    fontSize: 32,
    fontFamily: "Nunito_800ExtraBold",
    color: "#fafafa",
    letterSpacing: 1.2,
    textAlign: "center",
    textShadowColor: "rgba(167,139,250,0.45)",
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 18,
  },
  subtitle: {
    fontSize: 14,
    fontFamily: "Nunito_500Medium",
    color: "rgba(226,232,240,0.82)",
    textAlign: "center",
    lineHeight: 21,
    maxWidth: 320,
    letterSpacing: 0.2,
  },
  trustRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 7,
    marginTop: 2,
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 999,
    backgroundColor: "rgba(124,58,237,0.12)",
    borderWidth: 1,
    borderColor: "rgba(167,139,250,0.2)",
  },
  trustText: {
    fontSize: 11,
    fontFamily: "Nunito_600SemiBold",
    color: "rgba(196,181,253,0.95)",
    letterSpacing: 0.6,
  },
  cardShell: {
    borderRadius: 28,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.14)",
    shadowColor: "#7c3aed",
    shadowOffset: { width: 0, height: 16 },
    shadowOpacity: 0.35,
    shadowRadius: 32,
    elevation: 16,
  },
  cardGlassTint: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(10,6,24,0.52)",
  },
  cardShine: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    height: 56,
    zIndex: 1,
  },
  cardInner: {
    paddingVertical: 30,
    paddingHorizontal: 26,
    gap: 20,
    alignItems: "center",
    zIndex: 2,
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
    fontSize: 13,
    fontFamily: "Nunito_400Regular",
    color: "rgba(203,213,225,0.78)",
    textAlign: "center",
    lineHeight: 20,
    paddingHorizontal: 6,
    letterSpacing: 0.15,
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
    paddingVertical: 16,
    paddingHorizontal: 22,
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
  footerBlock: {
    alignItems: "center",
    gap: 14,
    paddingTop: 4,
    width: "100%",
    maxWidth: 360,
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
});
