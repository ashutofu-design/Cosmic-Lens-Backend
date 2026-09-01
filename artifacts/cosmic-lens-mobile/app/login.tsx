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
  TextInput,
  useWindowDimensions,
  View,
  type ViewStyle,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { GalaxyStarfield } from "@/components/GalaxyStarfield";
import { FadeInView } from "@/components/motion/FadeInView";
import { useUser, type AuthUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import { verifyFirebaseIdToken } from "@/lib/authBackend";
import { confirmPhoneOtp, prepareLoginPhoneAuth, requestPhoneOtp, resetPhoneAuthAfterFailure, signInWithGoogle, supportsPhoneOtp, watchPhoneAutoSignIn } from "@/lib/firebaseAuth";
import { otpTrace, redactId, redactPhone } from "@/lib/phoneOtpTrace";
import { isFirebaseConfigured } from "@/lib/firebaseConfig";
import { markWelcomeBonusPending } from "@/lib/welcomeBonus";

const RESEND_COOLDOWN_SEC = 120; // 2 minutes before Resend OTP is enabled

function isWrongOtpError(e: unknown): boolean {
  const code = String((e as { code?: string })?.code || "").toLowerCase();
  const msg = String((e as Error)?.message || e || "").toLowerCase();
  return code.includes("invalid-verification-code") || msg.includes("invalid-verification-code");
}

function isSessionExpiredError(e: unknown): boolean {
  const code = String((e as { code?: string })?.code || "").toLowerCase();
  const msg = String((e as Error)?.message || e || "").toLowerCase();
  return (
    code.includes("session-expired") ||
    code.includes("code-expired") ||
    msg.includes("session-expired") ||
    msg.includes("sms code has expired") ||
    msg.includes("otp session expired")
  );
}

function formatResendWait(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

const WEB_GLASS = Platform.OS === "web"
  ? ({
      backdropFilter: "blur(22px) saturate(140%)",
      WebkitBackdropFilter: "blur(22px) saturate(140%)",
      backgroundColor: "rgba(6,4,14,0.42)",
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
      {Platform.OS === "ios" ? (
        <BlurView intensity={36} tint="dark" style={StyleSheet.absoluteFill} />
      ) : Platform.OS === "web" ? (
        <View style={[StyleSheet.absoluteFill, WEB_GLASS]} />
      ) : (
        <View style={[StyleSheet.absoluteFill, { backgroundColor: "rgba(10,8,20,0.92)" }]} />
      )}
      <View style={s.cardGlassTint} />
      <LinearGradient
        colors={["rgba(232,212,168,0.10)", "rgba(255,255,255,0.03)", "transparent"]}
        start={{ x: 0, y: 0 }}
        end={{ x: 0, y: 1 }}
        style={s.cardShine}
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
  const cardW = Math.min(width - (compact ? 32 : 40), 380);

  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [error, setError] = useState("");
  const [phoneDigits, setPhoneDigits] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const [otpSessionId, setOtpSessionId] = useState<string | null>(null);
  const [resendInSec, setResendInSec] = useState(0);
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [phoneAuthReady, setPhoneAuthReady] = useState(Platform.OS === "web");

  const titleGlow = useRef(new Animated.Value(0.4)).current;
  const lineWidth = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (Platform.OS === "web") return;
    let cancelled = false;
    void (async () => {
      try {
        await prepareLoginPhoneAuth();
        if (!cancelled) setPhoneAuthReady(true);
      } catch (e) {
        if (!cancelled) {
          setError(String((e as Error)?.message || e || "Auth setup failed"));
          setPhoneAuthReady(true);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (resendInSec <= 0) return;
    const id = setTimeout(() => setResendInSec((s) => Math.max(0, s - 1)), 1000);
    return () => clearTimeout(id);
  }, [resendInSec]);

  const completingRef = useRef(false);
  const verifyingRef = useRef(false);
  const sendOtpInFlightRef = useRef(false);
  const completePhoneLoginRef = useRef<(idToken: string) => Promise<void>>(async () => {});

  async function completePhoneLogin(idToken: string) {
    if (completingRef.current) return;
    completingRef.current = true;
    setLoading(true);
    setError("");
    try {
      const { user: u, isNewUser } = await verifyFirebaseIdToken(idToken);
      if (isNewUser) {
        await markWelcomeBonusPending(String(u.id));
      }
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
      await finishLogin(u);
    } catch (e: unknown) {
      completingRef.current = false;
      setError(formatOtpError(e));
      await resetPhoneAuthAfterFailure().catch(() => {});
      setOtpSessionId(null);
      setOtpCode("");
    } finally {
      setLoading(false);
    }
  }

  completePhoneLoginRef.current = completePhoneLogin;

  useEffect(() => {
    if (Platform.OS === "web" || !otpSessionId || phoneDigits.length !== 10) return;
    const phone = `+91${phoneDigits}`;
    const stop = watchPhoneAutoSignIn(phone, (idToken) => {
      void completePhoneLoginRef.current(idToken);
    });
    return stop;
  }, [otpSessionId, phoneDigits]);

  useEffect(() => {
    const title = Animated.loop(
      Animated.sequence([
        Animated.timing(titleGlow, {
          toValue: 0.9,
          duration: 3400,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(titleGlow, {
          toValue: 0.4,
          duration: 3400,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ]),
    );
    const line = Animated.timing(lineWidth, {
      toValue: 1,
      duration: 900,
      delay: 280,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: false,
    });
    title.start();
    line.start();
    return () => title.stop();
  }, [titleGlow, lineWidth]);

  async function finishLogin(u: AuthUser) {
    await setUser(u);
    router.replace("/welcome-reveal");
  }

  function ensureTermsAccepted(): boolean {
    if (termsAccepted) return true;
    setError(
      isHindi
        ? "Aage badhne se pehle Terms & Conditions accept karein."
        : "Accept Terms & Conditions before continuing.",
    );
    return false;
  }

  function phoneE164(): string {
    return `+91${phoneDigits}`;
  }

  async function handleGoogleLogin() {
    if (!ensureTermsAccepted()) return;
    if (!isFirebaseConfigured()) {
      setError(t.authNotConfigured);
      return;
    }
    setError("");
    setLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});

    try {
      const idToken = await signInWithGoogle();
      const { user: u, isNewUser } = await verifyFirebaseIdToken(idToken);
      if (isNewUser) {
        await markWelcomeBonusPending(String(u.id));
      }
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
      await finishLogin(u);
    } catch (e: unknown) {
      const msg = String((e as Error)?.message || e || "");
      if (msg.includes("popup-closed-by-user") || msg.includes("cancelled")) {
        setError(isHindi ? "Login cancel ho gaya." : "Sign-in was cancelled.");
      } else if (/Failed to fetch|Network request failed|network-request-failed/i.test(msg)) {
        setError(
          isHindi
            ? "API proxy nahi mila. Terminal band karke `npm run dev:web` chalao, phir http://localhost:18987 kholo."
            : "API proxy missing. Stop Metro, run npm run dev:web, then open http://localhost:18987",
        );
      } else if (msg.toLowerCase().includes("network")) {
        setError(t.errNetwork);
      } else {
        setError(msg || t.loginGenericError);
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleSendOtp() {
    if (!ensureTermsAccepted()) return;
    if (!phoneAuthReady) {
      setError(isHindi ? "Auth taiyar ho raha hai… thodi der wait karo." : "Preparing sign-in… please wait a moment.");
      return;
    }
    if (!supportsPhoneOtp()) {
      setError(isHindi ? "OTP is device/app only right now." : "OTP is currently available in the app/device flow only.");
      return;
    }
    if (phoneDigits.length !== 10) {
      setError(isHindi ? "Valid 10-digit mobile number dalo." : "Enter a valid 10-digit mobile number.");
      return;
    }
    if (sendOtpInFlightRef.current) return;
    setError("");
    setLoading(true);
    sendOtpInFlightRef.current = true;
    otpTrace("SEND_OTP", { phone: redactPhone(phoneE164()) });
    try {
      const { sessionId } = await requestPhoneOtp(phoneE164());
      completingRef.current = false;
      verifyingRef.current = false;
      setOtpSessionId(sessionId);
      setOtpCode("");
      setResendInSec(RESEND_COOLDOWN_SEC);
      otpTrace("SEND_OTP_DONE", { sessionId: redactId(sessionId), phone: redactPhone(phoneE164()) });
    } catch (e: unknown) {
      setError(formatOtpError(e));
      await resetPhoneAuthAfterFailure().catch(() => {});
      setOtpSessionId(null);
      setOtpCode("");
    } finally {
      sendOtpInFlightRef.current = false;
      setLoading(false);
    }
  }

  function formatOtpError(e: unknown): string {
    const msg = String((e as Error)?.message || e || "");
    const code = String((e as { code?: string })?.code || "");
    if (isSessionExpiredError(e)) {
      return isHindi
        ? "OTP session expire ho gayi. Resend OTP dabao aur dubara try karo."
        : "OTP session expired. Tap Resend OTP and try again.";
    }
    if (msg.includes("invalid-verification-code")) {
      return isHindi ? "Galat OTP. Dubara check karo ya Resend OTP." : "Wrong OTP. Check again or tap Resend OTP.";
    }
    if (/not found|no api route|firebase-verify/i.test(msg)) {
      return isHindi
        ? "Server login route issue. Thodi der baad try karo ya support se contact karo."
        : msg;
    }
    if (/network|connection|timeout|fetch/i.test(msg)) {
      return isHindi
        ? "Internet ya server slow hai. WiFi/data check karke dubara try karo."
        : msg || t.errNetwork;
    }
    return code ? `${msg} [${code}]` : msg || t.loginGenericError;
  }

  async function handleResendOtp() {
    if (!ensureTermsAccepted()) return;
    if (!otpSessionId || resendInSec > 0 || resending || loading) return;
    if (phoneDigits.length !== 10) {
      setError(isHindi ? "Valid 10-digit mobile number dalo." : "Enter a valid 10-digit mobile number.");
      return;
    }
    setError("");
    setResending(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light).catch(() => {});
    try {
      otpTrace("RESEND_OTP", { phone: redactPhone(phoneE164()) });
      const { sessionId } = await requestPhoneOtp(phoneE164(), { forceResend: true });
      completingRef.current = false;
      verifyingRef.current = false;
      setOtpSessionId(sessionId);
      setOtpCode("");
      setResendInSec(RESEND_COOLDOWN_SEC);
    } catch (e: unknown) {
      setError(formatOtpError(e));
    } finally {
      setResending(false);
    }
  }

  async function handleVerifyOtp() {
    if (!ensureTermsAccepted()) return;
    if (!otpSessionId) {
      setError(isHindi ? "Pehle OTP bhejein." : "Send OTP first.");
      return;
    }
    if (otpCode.trim().length < 6) {
      setError(isHindi ? "6-digit OTP dalo." : "Enter the 6-digit OTP.");
      return;
    }
    if (verifyingRef.current || completingRef.current) return;

    verifyingRef.current = true;
    setError("");
    setLoading(true);
    otpTrace("VERIFY_OTP_TAP", {
      sessionId: redactId(otpSessionId),
      phone: redactPhone(phoneE164()),
      otpLength: otpCode.trim().length,
    });
    try {
      const idToken = await confirmPhoneOtp(otpSessionId, otpCode.trim());
      await completePhoneLogin(idToken);
    } catch (e: unknown) {
      setError(formatOtpError(e));
      if (!isWrongOtpError(e) && !isSessionExpiredError(e)) {
        await resetPhoneAuthAfterFailure().catch(() => {});
        setOtpSessionId(null);
        setOtpCode("");
      }
    } finally {
      verifyingRef.current = false;
      if (!completingRef.current) setLoading(false);
    }
  }

  function handleOtpChange(raw: string) {
    setOtpCode(raw.replace(/\D/g, "").slice(0, 6));
  }

  return (
    <View style={s.root}>
      <GalaxyStarfield />
      <LinearGradient
        colors={["transparent", "rgba(0,0,0,0.35)", "rgba(0,0,0,0.72)"]}
        locations={[0.35, 0.7, 1]}
        style={StyleSheet.absoluteFill}
        pointerEvents="none"
      />

      <View
        style={[
          s.content,
          {
            paddingTop: topPad + (compact ? 18 : 28),
            paddingBottom: botPad + (compact ? 16 : 22),
            paddingHorizontal: compact ? 16 : 22,
          },
        ]}
      >
        <View style={s.centerCol}>
          {/* Brand — hero */}
          <FadeInView delay={0} style={[s.brandBlock, compact && s.brandBlockCompact]}>
            <Text style={s.brandEyebrow}>
              {isHindi ? "वैदिक · इंटेलिजेंस" : "VEDIC · INTELLIGENCE"}
            </Text>
            <Animated.Text
              style={[
                s.title,
                compact && s.titleCompact,
                {
                  opacity: titleGlow.interpolate({
                    inputRange: [0.4, 0.9],
                    outputRange: [0.94, 1],
                  }),
                },
              ]}
            >
              Cosmic Lens
            </Animated.Text>
            <Animated.View
              style={[
                s.brandRule,
                {
                  width: lineWidth.interpolate({
                    inputRange: [0, 1],
                    outputRange: [0, compact ? 56 : 72],
                  }),
                },
              ]}
            />
            <Text style={[s.powered, compact && s.poweredCompact]}>
              Powered by Cosmic Intelligence Engine
            </Text>
          </FadeInView>

          {/* Auth */}
          <FadeInView delay={140} style={{ width: cardW, marginTop: compact ? 28 : 36 }}>
            <FrostedLoginCard width={cardW} compact={compact}>
              {!!error && (
                <View style={s.errorBox}>
                  <Feather name="alert-circle" size={13} color="#f87171" />
                  <Text style={s.errorText}>{error}</Text>
                </View>
              )}

              <Text style={s.sectionLabel}>
                {isHindi ? "Mobile OTP" : "Mobile number"}
              </Text>

              <View style={s.phoneRow}>
                <View style={s.ccBox}>
                  <Text style={s.ccText}>+91</Text>
                </View>
                <TextInput
                  value={phoneDigits}
                  onChangeText={(v) => setPhoneDigits(v.replace(/\D/g, "").slice(0, 10))}
                  placeholder={isHindi ? "10 अंकों का मोबाइल" : "10-digit mobile"}
                  placeholderTextColor="rgba(148,163,184,0.55)"
                  keyboardType="phone-pad"
                  maxLength={10}
                  style={s.phoneInput}
                />
              </View>

              {otpSessionId ? (
                <TextInput
                  value={otpCode}
                  onChangeText={handleOtpChange}
                  placeholder={isHindi ? "6-digit OTP" : "6-digit OTP"}
                  placeholderTextColor="rgba(148,163,184,0.55)"
                  keyboardType="number-pad"
                  maxLength={6}
                  autoComplete="off"
                  textContentType={Platform.OS === "ios" ? "oneTimeCode" : "none"}
                  importantForAutofill="no"
                  style={s.otpInput}
                />
              ) : null}

              <Pressable
                onPress={otpSessionId ? handleVerifyOtp : handleSendOtp}
                disabled={loading || resending || !phoneAuthReady}
                style={({ pressed }) => [
                  s.primaryBtnWrap,
                  { opacity: loading || resending || !phoneAuthReady ? 0.65 : pressed ? 0.92 : 1 },
                ]}
              >
                <LinearGradient
                  colors={["#e8d4a8", "#c9a962"]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                  style={s.primaryBtn}
                >
                  {loading || !phoneAuthReady ? (
                    <ActivityIndicator size="small" color="#1a1520" />
                  ) : (
                    <Text style={s.primaryBtnText}>
                      {otpSessionId
                        ? (isHindi ? "OTP Verify" : "Verify OTP")
                        : (isHindi ? "OTP bhejein" : "Send OTP")}
                    </Text>
                  )}
                </LinearGradient>
              </Pressable>

              {loading && !otpSessionId ? (
                <Text style={s.sendOtpHint}>
                  {isHindi
                    ? "OTP bhej rahe hain… pehli baar 15–30 sec lag sakta hai."
                    : "Sending OTP… first time can take 15–30 seconds."}
                </Text>
              ) : null}

              {otpSessionId ? (
                <View style={s.resendRow}>
                  <Text style={s.resendHint}>
                    {isHindi ? "OTP nahi aaya?" : "Didn't get the OTP?"}
                  </Text>
                  <Pressable
                    onPress={handleResendOtp}
                    disabled={loading || resending || resendInSec > 0}
                    hitSlop={10}
                    style={({ pressed }) => [
                      s.resendWrap,
                      {
                        opacity:
                          loading || resending || resendInSec > 0
                            ? 0.7
                            : pressed
                              ? 0.85
                              : 1,
                      },
                    ]}
                  >
                    {resending ? (
                      <ActivityIndicator size="small" color="rgba(232,212,168,0.95)" />
                    ) : (
                      <Text
                        style={[
                          s.resendText,
                          resendInSec > 0 ? s.resendTextWait : s.resendTextActive,
                        ]}
                      >
                        {resendInSec > 0
                          ? `${t.resendIn} ${formatResendWait(resendInSec)}`
                          : t.resendOtp}
                      </Text>
                    )}
                  </Pressable>
                </View>
              ) : null}

              <View style={s.orRow}>
                <View style={s.orLine} />
                <Text style={s.orText}>{isHindi ? "ya" : "or"}</Text>
                <View style={s.orLine} />
              </View>

              <Pressable
                onPress={handleGoogleLogin}
                disabled={loading || resending}
                style={({ pressed }) => [
                  s.googleBtn,
                  { opacity: loading || resending ? 0.65 : pressed ? 0.9 : 1 },
                ]}
              >
                {loading || resending ? (
                  <ActivityIndicator size="small" color="#e2e8f0" />
                ) : (
                  <>
                    <View style={s.googleIconWrap}>
                      <Text style={s.googleG}>G</Text>
                    </View>
                    <Text style={s.googleBtnText}>
                      {isHindi ? "Google se continue" : "Continue with Google"}
                    </Text>
                  </>
                )}
              </Pressable>

              <Text style={s.note}>
                {isHindi
                  ? "Pehli baar sign-in par account khud ban jayega."
                  : "Account is created automatically on first sign-in."}
              </Text>

              <Pressable
                onPress={() => setTermsAccepted((v) => !v)}
                style={s.termsRow}
                hitSlop={6}
              >
                <View style={[s.checkbox, termsAccepted && s.checkboxActive]}>
                  {termsAccepted ? <Feather name="check" size={12} color="#1a1520" /> : null}
                </View>
                <Text style={s.termsText}>
                  {isHindi ? "Main " : "I agree to the "}
                  <Text style={s.link} onPress={() => router.push("/legal")}>
                    Terms
                  </Text>
                  {isHindi ? " & " : " & "}
                  <Text style={s.link} onPress={() => router.push("/legal")}>
                    Privacy Policy
                  </Text>
                </Text>
              </Pressable>
            </FrostedLoginCard>
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
    width: "100%",
    gap: 10,
    paddingHorizontal: 8,
  },
  brandBlockCompact: {
    gap: 8,
  },
  brandEyebrow: {
    fontSize: 10,
    fontFamily: "Nunito_600SemiBold",
    color: "rgba(232,212,168,0.72)",
    letterSpacing: 3.2,
    textAlign: "center",
  },
  title: {
    fontSize: 40,
    lineHeight: 46,
    fontFamily: "Nunito_800ExtraBold",
    color: "#FFFFFF",
    letterSpacing: 1.2,
    textAlign: "center",
    textShadowColor: "rgba(232,212,168,0.18)",
    textShadowOffset: { width: 0, height: 0 },
    textShadowRadius: 18,
    ...(Platform.OS === "android" ? { includeFontPadding: false } : {}),
  },
  titleCompact: {
    fontSize: 34,
    lineHeight: 40,
    letterSpacing: 0.8,
  },
  brandRule: {
    height: 1.5,
    backgroundColor: "rgba(232,212,168,0.55)",
    borderRadius: 1,
    marginTop: 2,
  },
  powered: {
    marginTop: 2,
    fontSize: 12,
    fontFamily: "Nunito_400Regular",
    color: "rgba(203,213,225,0.72)",
    letterSpacing: 0.4,
    textAlign: "center",
  },
  poweredCompact: {
    fontSize: 11,
  },
  cardShell: {
    borderRadius: 22,
    overflow: "hidden",
    borderWidth: 1,
    borderColor: "rgba(232,212,168,0.14)",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 16 },
    shadowOpacity: 0.45,
    shadowRadius: 28,
    elevation: 12,
  },
  cardShellCompact: {
    borderRadius: 20,
  },
  cardGlassTint: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(8,6,16,0.38)",
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
    paddingVertical: 24,
    paddingHorizontal: 22,
    gap: 14,
    zIndex: 2,
  },
  cardInnerCompact: {
    paddingVertical: 20,
    paddingHorizontal: 18,
    gap: 12,
  },
  errorBox: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    width: "100%",
    marginBottom: 2,
  },
  errorText: {
    flex: 1,
    fontSize: 12,
    color: "#fca5a5",
    fontFamily: "Nunito_500Medium",
  },
  sectionLabel: {
    fontSize: 11,
    fontFamily: "Nunito_600SemiBold",
    color: "rgba(232,212,168,0.7)",
    letterSpacing: 1.4,
    textTransform: "uppercase",
  },
  phoneRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    width: "100%",
  },
  ccBox: {
    minHeight: 50,
    paddingHorizontal: 14,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.10)",
    backgroundColor: "rgba(255,255,255,0.04)",
    alignItems: "center",
    justifyContent: "center",
  },
  ccText: {
    fontSize: 15,
    fontFamily: "Nunito_700Bold",
    color: "rgba(248,250,252,0.92)",
    letterSpacing: 0.5,
  },
  phoneInput: {
    flex: 1,
    minHeight: 50,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.10)",
    backgroundColor: "rgba(255,255,255,0.04)",
    paddingHorizontal: 14,
    color: "#fff",
    fontSize: 16,
    fontFamily: "Nunito_600SemiBold",
    letterSpacing: 1.2,
  },
  otpInput: {
    width: "100%",
    minHeight: 50,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "rgba(232,212,168,0.28)",
    backgroundColor: "rgba(255,255,255,0.05)",
    paddingHorizontal: 14,
    color: "#fff",
    fontSize: 18,
    fontFamily: "Nunito_700Bold",
    letterSpacing: 6,
    textAlign: "center",
  },
  resendRow: {
    width: "100%",
    alignItems: "center",
    gap: 4,
    marginTop: 4,
    marginBottom: 2,
    paddingVertical: 4,
  },
  resendHint: {
    fontSize: 12,
    fontFamily: "Nunito_500Medium",
    color: "rgba(148,163,184,0.85)",
    textAlign: "center",
  },
  sendOtpHint: {
    fontSize: 12,
    fontFamily: "Nunito_500Medium",
    color: "rgba(148,163,184,0.85)",
    textAlign: "center",
    marginTop: 8,
    paddingHorizontal: 8,
  },
  resendWrap: {
    alignSelf: "center",
    paddingVertical: 8,
    paddingHorizontal: 12,
    minHeight: 36,
    justifyContent: "center",
  },
  resendText: {
    fontSize: 14,
    fontFamily: "Nunito_700Bold",
    letterSpacing: 0.3,
    textAlign: "center",
  },
  resendTextWait: {
    color: "rgba(226,232,240,0.78)",
  },
  resendTextActive: {
    color: "#e8d4a8",
    textDecorationLine: "underline",
  },
  primaryBtnWrap: {
    width: "100%",
    marginTop: 2,
  },
  primaryBtn: {
    minHeight: 50,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
  },
  primaryBtnText: {
    color: "#1a1520",
    fontSize: 15,
    fontFamily: "Nunito_800ExtraBold",
    letterSpacing: 0.6,
  },
  orRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    width: "100%",
    marginVertical: 2,
  },
  orLine: {
    flex: 1,
    height: StyleSheet.hairlineWidth,
    backgroundColor: "rgba(255,255,255,0.14)",
  },
  orText: {
    fontSize: 11,
    fontFamily: "Nunito_500Medium",
    color: "rgba(148,163,184,0.75)",
    letterSpacing: 1,
    textTransform: "uppercase",
  },
  googleBtn: {
    width: "100%",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 12,
    minHeight: 50,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.14)",
    backgroundColor: "rgba(255,255,255,0.06)",
    paddingHorizontal: 16,
  },
  googleIconWrap: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: "#fff",
    alignItems: "center",
    justifyContent: "center",
  },
  googleG: {
    fontSize: 14,
    fontFamily: "Nunito_800ExtraBold",
    color: "#4285F4",
  },
  googleBtnText: {
    fontSize: 15,
    fontFamily: "Nunito_700Bold",
    color: "rgba(248,250,252,0.95)",
    letterSpacing: 0.2,
  },
  note: {
    fontSize: 11.5,
    fontFamily: "Nunito_400Regular",
    color: "rgba(148,163,184,0.7)",
    textAlign: "center",
    lineHeight: 16,
    marginTop: 2,
  },
  termsRow: {
    width: "100%",
    flexDirection: "row",
    alignItems: "flex-start",
    gap: 10,
    marginTop: 2,
  },
  checkbox: {
    width: 18,
    height: 18,
    borderRadius: 5,
    borderWidth: 1,
    borderColor: "rgba(232,212,168,0.45)",
    alignItems: "center",
    justifyContent: "center",
    marginTop: 1,
    backgroundColor: "transparent",
  },
  checkboxActive: {
    backgroundColor: "#e8d4a8",
    borderColor: "#e8d4a8",
  },
  termsText: {
    flex: 1,
    fontSize: 12,
    lineHeight: 18,
    color: "rgba(203,213,225,0.78)",
    fontFamily: "Nunito_400Regular",
  },
  link: {
    color: "#e8d4a8",
    fontFamily: "Nunito_700Bold",
  },
});
