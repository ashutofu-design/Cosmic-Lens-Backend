import {
  Nunito_400Regular,
  Nunito_500Medium,
  Nunito_600SemiBold,
  Nunito_700Bold,
  useFonts,
} from "@expo-google-fonts/nunito";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Stack } from "expo-router";
import * as SplashScreen from "expo-splash-screen";
import React, { useEffect } from "react";
import { GestureHandlerRootView } from "react-native-gesture-handler";
import { KeyboardProvider } from "react-native-keyboard-controller";
import { SafeAreaProvider } from "react-native-safe-area-context";

import { ErrorBoundary } from "@/components/ErrorBoundary";
import { ZodiacBridge } from "@/components/ZodiacBridge";
import { ThemeProvider } from "@/context/ThemeContext";
import { UserProvider } from "@/context/UserContext";

SplashScreen.preventAutoHideAsync();

const queryClient = new QueryClient();

function RootLayoutNav() {
  return (
    <Stack screenOptions={{ headerBackTitle: "Back" }}>
      <Stack.Screen name="login"            options={{ headerShown: false }} />
      <Stack.Screen name="onboarding"       options={{ headerShown: false }} />
      <Stack.Screen name="(tabs)"           options={{ headerShown: false }} />
      <Stack.Screen name="forecast"         options={{ headerShown: false }} />
      <Stack.Screen name="planet-position"  options={{ headerShown: false }} />
      <Stack.Screen name="profile-edit"     options={{ headerShown: false }} />
      <Stack.Screen name="dosh"             options={{ headerShown: false }} />
      <Stack.Screen name="kundli-milan"     options={{ headerShown: false }} />
      <Stack.Screen name="vastu"            options={{ headerShown: false }} />
      <Stack.Screen name="astrovastu-basic" options={{ headerShown: false }} />
      <Stack.Screen name="astrovastu-pro"   options={{ headerShown: false }} />
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

  if (!fontsLoaded && !fontError) return null;

  return (
    <SafeAreaProvider>
      <ErrorBoundary>
        <QueryClientProvider client={queryClient}>
          <ThemeProvider>
            <UserProvider>
              <ZodiacBridge />
              <GestureHandlerRootView>
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
