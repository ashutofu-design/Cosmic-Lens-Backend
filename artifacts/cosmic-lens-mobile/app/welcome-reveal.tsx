import { router } from "expo-router";
import React, { useEffect } from "react";
import { ActivityIndicator, View } from "react-native";

import { PostLoginReveal } from "@/components/PostLoginReveal";
import { useUser } from "@/context/UserContext";

/** Full-screen cinematic intro after Google sign-in (before onboarding or home). */
export default function WelcomeRevealScreen() {
  const { user } = useUser();

  useEffect(() => {
    if (!user) router.replace("/login");
  }, [user]);

  if (!user) {
    return (
      <View style={{ flex: 1, backgroundColor: "#030712", alignItems: "center", justifyContent: "center" }}>
        <ActivityIndicator color="#f59e0b" />
      </View>
    );
  }

  const firstName = user.name?.trim().split(/\s+/)[0];

  return <PostLoginReveal userName={firstName} />;
}
