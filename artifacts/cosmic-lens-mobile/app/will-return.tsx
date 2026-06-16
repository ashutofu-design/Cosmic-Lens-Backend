import { Redirect, useLocalSearchParams } from "expo-router";
import React from "react";

export default function WillReturnScreen() {
  const params = useLocalSearchParams<{ partnerId?: string }>();
  const qs = new URLSearchParams();
  if (typeof params.partnerId === "string") qs.set("partnerId", params.partnerId);
  const href = qs.toString() ? `/love-reality?${qs.toString()}` : "/love-reality";
  return <Redirect href={href as never} />;
}
