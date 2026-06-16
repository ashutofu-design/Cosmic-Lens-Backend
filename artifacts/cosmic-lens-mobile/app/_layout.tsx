import "react-native-gesture-handler";
import "react-native-reanimated";

import {
  Nunito_400Regular,
  Nunito_500Medium,
  Nunito_600SemiBold,
  Nunito_700Bold,
  useFonts,
} from "@expo-google-fonts/nunito";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Platform } from "react-native";
import { router, Stack } from "expo-router";
import * as SplashScreen from "expo-splash-screen";
import React, { useEffect } from "react";

import { attachTapHandler, configureForeground } from "@/lib/notifications";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { KeyboardProvider } from "react-native-keyboard-controller";
import { SafeAreaProvider } from "react-native-safe-area-context";

import "@/lib/unhandledRejectionLogger";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { ZodiacBridge } from "@/components/ZodiacBridge";
import { ThemeProvider } from "@/context/ThemeContext";
import { UserProvider, useUser } from "@/context/UserContext";
import { getT } from "@/lib/i18n";

SplashScreen.preventAutoHideAsync();

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
      <Stack.Screen name="my-reports"                options={{ headerShown: false }} />
      <Stack.Screen name="personalization"           options={{ headerShown: false }} />
      <Stack.Screen name="panchang"                  options={{ headerShown: false }} />
    </Stack>
  );
}

export default function RootLayout() {
  const [fontsLoaded, fontError] = useFonts({
    Nunito_400Regular,
    Nunito_500Medium,
    Nunito_600SemiBold,
    Nunito_700Bold,
  });

  useEffect(() => {
    if (fontsLoaded || fontError) {
      SplashScreen.hideAsync();
    }
  }, [fontsLoaded, fontError]);

  // Push notifications: foreground display + tap-to-navigate
  useEffect(() => {
    configureForeground();
    const sub = attachTapHandler((path) => router.push(path as any));
    return () => {
      try {
        sub?.remove?.();
      } catch {
        /* push unsupported on web / Expo Go Android */
      }
    };
  }, []);

  if (!fontsLoaded && !fontError) return null;

  return (
    <SafeAreaProvider>
      <ErrorBoundary>
        <QueryClientProvider client={queryClient}>
          <ThemeProvider>
            <UserProvider>
              <ZodiacBridge />
              <GestureHandlerRootView style={{ flex: 1 }}>
                <KeyboardProvider>
                  <RootLayoutNav />
                </KeyboardProvider>
              </GestureHandlerRootView>
            </UserProvider>
          </ThemeProvider>
        </QueryClientProvider>
      </ErrorBoundary>
    </SafeAreaProvider>
  );
}
