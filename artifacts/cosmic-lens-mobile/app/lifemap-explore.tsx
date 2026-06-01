import { Redirect } from "expo-router";

/** Deep link / back-compat: open Life Map tab on Explore segment. */
export default function LifeMapExploreRedirect() {
  return <Redirect href="/(tabs)/lifemap?mode=explore" />;
}
