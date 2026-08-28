import "react-native-gesture-handler";
import "react-native-reanimated";

import {
  Nunito_400Regular,
  Nunito_500Medium,
  Nunito_600SemiBold,
  Nunito_700Bold,
  Nunito_800ExtraBold,
  useFonts,
} from "@expo-google-fonts/nunito";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Platform } from "react-native";
import { router, Stack } from "expo-router";
import * as SplashScreen from "expo-splash-screen";
import React, { useEffect } from "react";

import {
  attachPushReceivedHandler,
  attachTapHandler,
  configureForeground,
} from "@/lib/notifications";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { SafeAreaProvider } from "react-native-safe-area-context";

import "@/lib/unhandledRejectionLogger";
import { applyWebDocumentHeight } from "@/lib/webDocumentHeight";
import { AppKeyboardShell } from "@/components/AppKeyboardShell";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { WelcomeBonusHost } from "@/components/WelcomeBonusHost";
import { ZodiacBridge } from "@/components/ZodiacBridge";
import { ThemeProvider } from "@/context/ThemeContext";
import { UserProvider, useUser } from "@/context/UserContext";
import { getT } from "@/lib/i18n";

if (Platform.OS === "web") {
  applyWebDocumentHeight();
} else {
  SplashScreen.preventAutoHideAsync();
}

const WEB_ROOT_STYLE = { flex: 1, minHeight: "100vh", width: "100%" } as const;

const queryClient = new QueryClient();

function RootLayoutNav() {
  const { language } = useUser();
  const t = getT(language);
  return (
    <Stack
      screenOptions={{
        headerBackTitle: t.back,
        animation: Platform.OS === "android" ? "fade_from_bottom" : "slide_from_right",
        animationDuration: Platform.OS === "web" ? 280 : 200,
      }}
    >
      <Stack.Screen name="index"            options={{ headerShown: false }} />
      <Stack.Screen name="login"            options={{ headerShown: false }} />
      <Stack.Screen name="welcome-reveal"   options={{ headerShown: false, animation: "fade", animationDuration: 220 }} />
      <Stack.Screen name="onboarding"       options={{ headerShown: false }} />
      <Stack.Screen name="(tabs)"           options={{ headerShown: false }} />
      <Stack.Screen name="forecast"         options={{ headerShown: false }} />
      <Stack.Screen name="dasha-risk"       options={{ headerShown: false }} />
      <Stack.Screen name="planet-position"   options={{ headerShown: false }} />
      <Stack.Screen name="gemstones"         options={{ headerShown: false }} />
      <Stack.Screen name="gemstone-buy"      options={{ headerShown: false }} />
      <Stack.Screen name="divisional-charts" options={{ headerShown: false }} />
      <Stack.Screen name="varga-chart"         options={{ headerShown: false }} />
      <Stack.Screen name="profile-edit"     options={{ headerShown: false }} />
      <Stack.Screen name="dosh"             options={{ headerShown: false }} />
      <Stack.Screen name="kundli-milan"        options={{ headerShown: false }} />
      <Stack.Screen name="kundli-milan-result" options={{ headerShown: false }} />
      <Stack.Screen name="love-reality-pro" options={{ headerShown: false }} />
      <Stack.Screen name="love-reality-pro-report" options={{ headerShown: false }} />
      <Stack.Screen name="vastu"            options={{ headerShown: false }} />
      <Stack.Screen name="astrovastu"               options={{ headerShown: false }} />
      <Stack.Screen name="astrovastu-pro-options"   options={{ headerShown: false }} />
      <Stack.Screen name="astrovastu-basic"         options={{ headerShown: false }} />
      <Stack.Screen name="astrovastu-pro"           options={{ headerShown: false }} />
      <Stack.Screen name="business-vastu"           options={{ headerShown: false }} />
      <Stack.Screen name="birth-time-rectification" options={{ headerShown: false }} />
      <Stack.Screen name="instagram-answers" options={{ headerShown: false }} />
      <Stack.Screen name="my-reports"                options={{ headerShown: false }} />
      <Stack.Screen name="personalization"           options={{ headerShown: false }} />
      <Stack.Screen name="panchang"                  options={{ headerShown: false }} />
      <Stack.Screen name="talk-to-founder"           options={{ headerShown: false }} />
      <Stack.Screen name="help-support"              options={{ headerShown: false }} />
      <Stack.Screen name="refer-earn"                options={{ headerShown: false }} />
      <Stack.Screen name="cosmic-packs"              options={{ headerShown: false }} />
      <Stack.Screen name="palmistry"                 options={{ headerShown: false }} />
    </Stack>
  );
}

export default function RootLayout() {
  const [fontsLoaded, fontError] = useFonts({
    Nunito_400Regular,
    Nunito_500Medium,
    Nunito_600SemiBold,
    Nunito_700Bold,
    Nunito_800ExtraBold,
  });

  useEffect(() => {
    if (Platform.OS === "web") {
      applyWebDocumentHeight();
      SplashScreen.hideAsync().catch(() => {});
      return;
    }
    if (fontsLoaded || fontError) {
      SplashScreen.hideAsync();
    }
  }, [fontsLoaded, fontError]);

  // Push notifications: foreground display + tap-to-navigate (+ v3_ready dispatch)
  useEffect(() => {
    configureForeground();
    const sub = attachTapHandler((path) => router.push(path as any));
    const recv = attachPushReceivedHandler(() => {
      /* v3_ready dispatched inside notifications.ts */
    });
    return () => {
      try {
        sub?.remove?.();
      } catch {
        /* push unsupported on web / Expo Go Android */
      }
      try {
        recv?.remove?.();
      } catch {
        /* ignore */
      }
    };
  }, []);

  // Native: wait for fonts. Web: never return null — Google Fonts can hang
  // and a null tree is a blank page.
  if (Platform.OS !== "web" && !fontsLoaded && !fontError) return null;

  return (
    <SafeAreaProvider style={Platform.OS === "web" ? WEB_ROOT_STYLE : undefined}>
      <ErrorBoundary>
        <QueryClientProvider client={queryClient}>
          <ThemeProvider>
            <UserProvider>
              <ZodiacBridge />
              <GestureHandlerRootView
                style={Platform.OS === "web" ? WEB_ROOT_STYLE : { flex: 1 }}
              >
                <AppKeyboardShell>
                  <RootLayoutNav />
                  <WelcomeBonusHost />
                </AppKeyboardShell>
              </GestureHandlerRootView>
            </UserProvider>
          </ThemeProvider>
        </QueryClientProvider>
      </ErrorBoundary>
    </SafeAreaProvider>
  );
}
