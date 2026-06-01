import { Redirect, useLocalSearchParams } from "expo-router";
import React from "react";

export default function WillReturnScreen() {
  const params = useLocalSearchParams<{ partnerId?: string }>();
  const qs = new URLSearchParams({ tool: "will-return" });
  if (typeof params.partnerId === "string") qs.set("partnerId", params.partnerId);
  return <Redirect href={`/love-reality?${qs.toString()}` as never} />;
}
