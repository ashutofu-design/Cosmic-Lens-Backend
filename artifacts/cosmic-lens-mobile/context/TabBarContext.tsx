import React, { createContext, useContext, useMemo, useState } from "react";

/**
 * TabBarContext — lets a screen request a full-screen view by hiding the
 * bottom tab bar (Home / Lifemap / Ask / Future / More). Used by the Ask
 * chat so "Ask Anything" opens edge-to-edge like a dedicated chat app.
 *
 * NOTE: this controls the custom JS tab bar (Android / web / older iOS).
 * iOS 26 Liquid-Glass NativeTabs are rendered natively and are not hidden
 * by this flag.
 */
interface TabBarCtx {
  hidden: boolean;
  setHidden: (v: boolean) => void;
}

const TabBarContext = createContext<TabBarCtx>({
  hidden: false,
  setHidden: () => {},
});

export function TabBarProvider({ children }: { children: React.ReactNode }) {
  const [hidden, setHidden] = useState(false);
  const value = useMemo(() => ({ hidden, setHidden }), [hidden]);
  return <TabBarContext.Provider value={value}>{children}</TabBarContext.Provider>;
}

export function useTabBar() {
  return useContext(TabBarContext);
}
