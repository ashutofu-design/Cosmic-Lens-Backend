/**
 * Mount once at app root: top gift-burst banner after new-user login
 * (first time they land past login / reveal / onboarding).
 */
import { router, usePathname } from "expo-router";
import React, { useCallback, useEffect, useState } from "react";

import { WelcomeBonusModal } from "@/components/WelcomeBonusModal";
import { useUser } from "@/context/UserContext";
import { hasActiveAskV1Wallet } from "@/lib/askV1PackCheckoutFlow";
import {
  markWelcomeBonusPending,
  markWelcomeBonusSeen,
  shouldShowWelcomeBonus,
  wasWelcomeBonusSeen,
} from "@/lib/welcomeBonus";

function isBlockedPath(path: string | null): boolean {
  if (!path) return true;
  const p = path.toLowerCase();
  return (
    p.includes("login") ||
    p.includes("welcome-reveal") ||
    p.includes("onboarding")
  );
}

export function WelcomeBonusHost() {
  const { user, language } = useUser();
  const pathname = usePathname();
  const [visible, setVisible] = useState(false);
  const isHindi = language === "hi" || language === "hn";

  useEffect(() => {
    let cancelled = false;
    const userId = user?.id;
    if (!userId || isBlockedPath(pathname)) {
      setVisible(false);
      return;
    }

    // Let first paint / tab settle, then celebrate.
    const timer = setTimeout(() => {
      void (async () => {
        try {
          let show = await shouldShowWelcomeBonus(userId);
          if (!show) {
            // Fallback: brand-new V1 free wallet (3/3) never celebrated —
            // covers missed is_new_user from backend.
            const seen = await wasWelcomeBonusSeen(userId);
            if (!seen) {
              const w = await hasActiveAskV1Wallet(user);
              const freshFree =
                Number(w.free_questions_used || 0) === 0 &&
                Number(w.free_questions_left || 0) === 3;
              if (freshFree) {
                await markWelcomeBonusPending(userId);
                show = true;
              }
            }
          }
          if (!cancelled && show) setVisible(true);
        } catch {
          /* non-fatal */
        }
      })();
    }, 900);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [user?.id, user, pathname]);

  const dismiss = useCallback(async () => {
    setVisible(false);
    if (user?.id) await markWelcomeBonusSeen(user.id);
  }, [user?.id]);

  const askNow = useCallback(async () => {
    setVisible(false);
    if (user?.id) await markWelcomeBonusSeen(user.id);
    router.push("/(tabs)/ask" as any);
  }, [user?.id]);

  return (
    <WelcomeBonusModal
      visible={visible}
      isHindi={isHindi}
      onClose={dismiss}
      onAskNow={askNow}
    />
  );
}
