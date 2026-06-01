import { Redirect } from "expo-router";
import React from "react";
import { ActivityIndicator, View } from "react-native";

import { needsProfileSetup, useUser } from "@/context/UserContext";

/** Root `/` route — web and native both need this or the first screen stays blank. */
export default function IndexScreen() {
  const { user, profiles, primaryProfileId, isLoading } = useUser();

  if (isLoading) {
    return (
      <View style={{
        flex: 1,
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: "#0B1220",
      }}>
        <ActivityIndicator size="large" color="#f59e0b" />
      </View>
    );
  }

  if (!user) {
    return <Redirect href="/login" />;
  }

  if (needsProfileSetup(profiles, primaryProfileId)) {
    return <Redirect href="/onboarding" />;
  }

  return <Redirect href="/(tabs)" />;
}
