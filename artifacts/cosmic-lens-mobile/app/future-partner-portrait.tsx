import { Redirect } from "expo-router";

/** Feature removed — keep route so old links land on Relationship. */
export default function FuturePartnerPortraitRedirect() {
  return <Redirect href="/relationship" />;
}
