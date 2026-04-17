/**
 * Cosmic Lens — Subscription helpers (client side).
 *
 * Single source of truth for plan-aware UI logic. Mirrors backend
 * subscription_helper.py — keep these in sync if backend pricing/limits change.
 */

import { useEffect, useMemo, useState, useCallback } from "react";
import { useUser, type SubscriptionInfo } from "@/context/UserContext";
import { API_BASE, apiFetch } from "@/lib/apiConfig";

// ── Pricing constants (backend authoritative; these are fallbacks) ───────────
export const PRICES = {
  basic_monthly: 199,
  basic_yearly:  1799,
  pro_monthly:   399,
  pro_yearly:    2999,
} as const;

export const TRIAL_DAYS = 7;

export type Plan = "free" | "trial" | "basic" | "pro";

// ── Default subscription (for logged-out users) ──────────────────────────────
const DEFAULT_SUB: SubscriptionInfo = {
  plan:              "free",
  analysis_mode:     "basic",
  is_pro:            false,
  is_basic_or_above: false,
  trial_eligible:    false,
  trial_expires_at:  null,
  plan_expires_at:   null,
  limits: {
    questions_per_day: 1,
    questions_used:    0,
    timeline_months:   0,
    profile_limit:     1,
  },
  prices: PRICES,
  trial_days: TRIAL_DAYS,
};

// ── Feature gates ────────────────────────────────────────────────────────────
export type FeatureKey =
  | "ask_unlimited"
  | "marriage_compat_full"
  | "love_reality_full"
  | "career_deep"
  | "health_deep"
  | "finance_deep"
  | "future_timeline_6m"
  | "dasha_deep"
  | "karmic_insights"
  | "pdf_report"
  | "kundli_milan"
  | "unlimited_profiles";

export const FEATURE_REQUIREMENT: Record<FeatureKey, "basic" | "pro"> = {
  ask_unlimited:        "pro",
  marriage_compat_full: "pro",
  love_reality_full:    "pro",
  career_deep:          "pro",
  health_deep:          "pro",
  finance_deep:         "pro",
  future_timeline_6m:   "pro",
  dasha_deep:           "pro",
  karmic_insights:      "pro",
  pdf_report:           "pro",
  kundli_milan:         "basic",
  unlimited_profiles:   "pro",
};

function planRank(plan: Plan | "elite"): number {
  switch (plan) {
    case "free":  return 0;
    case "trial": return 2;   // trial unlocks Basic-tier features (matches backend)
    case "basic": return 2;
    case "pro":   return 3;
    case "elite": return 3;
    default:      return 0;
  }
}

// ── Hook: usePlan ────────────────────────────────────────────────────────────
export function usePlan() {
  const { user } = useUser();
  const [sub, setSub] = useState<SubscriptionInfo>(
    user?.subscription ?? DEFAULT_SUB
  );

  // Refetch live status from server (canonical truth)
  const refresh = useCallback(async () => {
    if (!user?.id || !user?.api_key) {
      setSub(DEFAULT_SUB);
      return;
    }
    try {
      const r = await apiFetch(
        `${API_BASE}/api/subscription/status?user_id=${user.id}`,
        { method: "GET", headers: { "X-API-Key": user.api_key } }
      );
      if (r.ok) {
        const data = await r.json();
        setSub(data);
      }
    } catch {
      /* keep cached */
    }
  }, [user?.id, user?.api_key]);

  // Sync when user object changes
  useEffect(() => {
    if (user?.subscription) {
      setSub(user.subscription);
    } else if (user?.id) {
      refresh();
    } else {
      setSub(DEFAULT_SUB);
    }
  }, [user?.id, user?.subscription, refresh]);

  const plan: Plan = useMemo(() => {
    const p = sub.plan;
    if (p === "elite") return "pro";
    return p as Plan;
  }, [sub.plan]);

  // Feature unlock check
  const has = useCallback((feature: FeatureKey): boolean => {
    const required = FEATURE_REQUIREMENT[feature];
    return planRank(plan) >= planRank(required);
  }, [plan]);

  // Days remaining (trial OR paid plan)
  const daysRemaining = useMemo(() => {
    const iso = plan === "trial" ? sub.trial_expires_at : sub.plan_expires_at;
    if (!iso) return null;
    const ms = new Date(iso).getTime() - Date.now();
    return Math.max(0, Math.ceil(ms / 86400000));
  }, [plan, sub.trial_expires_at, sub.plan_expires_at]);

  return {
    plan,                                    // 'free' | 'trial' | 'basic' | 'pro'
    sub,                                     // full SubscriptionInfo
    isPro:            plan === "pro",
    isBasic:          plan === "basic",
    isTrial:          plan === "trial",
    isFree:           plan === "free",
    isBasicOrAbove:   sub.is_basic_or_above,
    analysisMode:     sub.analysis_mode,    // 'basic' | 'pro'
    questionLimit:    sub.limits.questions_per_day,
    questionsUsed:    sub.limits.questions_used,
    questionsLeft:    sub.limits.questions_per_day === -1
                        ? Infinity
                        : Math.max(0, sub.limits.questions_per_day - sub.limits.questions_used),
    timelineMonths:   sub.limits.timeline_months,
    profileLimit:     sub.limits.profile_limit,
    trialEligible:    sub.trial_eligible,
    daysRemaining,
    has,
    refresh,
  };
}

// ── Start trial (one-time per user) ─────────────────────────────────────────
export async function startTrial(userId: number, apiKey: string): Promise<{ ok: boolean; error?: string; subscription?: SubscriptionInfo }> {
  try {
    const r = await apiFetch(`${API_BASE}/api/subscription/start-trial`, {
      method: "POST",
      headers: { "X-API-Key": apiKey },
      body: JSON.stringify({ user_id: userId }),
    });
    const data = await r.json();
    if (!r.ok || !data.ok) {
      return { ok: false, error: data?.error || "Trial start failed" };
    }
    return { ok: true, subscription: data.subscription };
  } catch (e: any) {
    return { ok: false, error: e?.message || "Network error" };
  }
}

// ── Upgrade trigger copy (Hinglish) ─────────────────────────────────────────
export const UPGRADE_COPY = {
  askLimit:     "Aaj ka limit poora ho gaya. Pro upgrade karein for unlimited questions.",
  feature:      "Unlock deeper insights and complete analysis with Pro.",
  timeline:     "Sirf 1 month visible hai. Full 6 months timeline ke liye Pro upgrade karein.",
  trialExpired: "Aapka trial expire ho gaya. Continue karne ke liye Basic ya Pro choose karein.",
  basicLocked:  "Ye feature Basic plan se shuru hoti hai.",
  proLocked:    "Ye feature sirf Pro members ke liye hai.",
} as const;
