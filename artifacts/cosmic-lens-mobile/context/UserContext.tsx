import AsyncStorage from "@react-native-async-storage/async-storage";
import { signOutFromFirebase } from "@/lib/firebaseAuth";
import { router } from "expo-router";
import { Alert, AppState, Platform, type AppStateStatus } from "react-native";
import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import type { BirthData, KundliData } from "@/types";
import { coerceUILang, type UILang } from "@/lib/i18n";
import { API_BASE, apiFetchWithTimeout, userAuthHeaders } from "@/lib/apiConfig";
import { clearAllLocalReports } from "@/lib/localReports";
import {
  clearApiKey,
  loadApiKey,
  saveApiKey,
  userWithoutApiKey,
} from "@/lib/secureApiKey";
import {
  attachPushReceivedHandler,
  presentReportReadyNotification,
  setupPushForUser,
} from "@/lib/notifications";
import {
  startReportAutoSync,
  stopReportAutoSync,
  subscribeNewReports,
} from "@/lib/reportAutoSync";
import { installUnreadReportsBridge } from "@/lib/unreadReportsBadge";
import { clearServerSyncCache, syncServerReportsForUser } from "@/lib/serverMyReports";

// ── ProfileEntry ────────────────────────────────────────────────────────────
export interface ProfileEntry {
  id: string;
  name: string;
  gender: string;
  relation?: string;
  birthData: BirthData;
  kundli: KundliData | null;
}

/** Romantic partner slots — must never be used as the native Ask chart. */
const PARTNER_RELATIONS = new Set([
  "husband", "wife", "boyfriend", "girlfriend",
  "fiance", "fiancee", "partner", "spouse",
]);

export function isPartnerProfile(profile: Pick<ProfileEntry, "relation"> | null | undefined): boolean {
  const rel = (profile?.relation ?? "").trim().toLowerCase();
  return rel !== "" && PARTNER_RELATIONS.has(rel);
}

/** Native (self) profile for Ask — never a partner slot, even if marked primary. */
export function resolveNativeAskProfile(
  profiles: ProfileEntry[],
  primaryProfileId: string | null,
): ProfileEntry | null {
  if (profiles.length === 0) return null;
  const flaggedPrimary =
    profiles.find((p) => p.id === primaryProfileId) ?? profiles[0] ?? null;
  if (
    flaggedPrimary &&
    !isPartnerProfile(flaggedPrimary) &&
    (flaggedPrimary.kundli?.planets?.length ?? 0) > 0
  ) {
    return flaggedPrimary;
  }
  const selfWithChart = profiles.find(
    (p) => !isPartnerProfile(p) && (p.kundli?.planets?.length ?? 0) > 0,
  );
  if (selfWithChart) return selfWithChart;
  if (flaggedPrimary && !isPartnerProfile(flaggedPrimary)) return flaggedPrimary;
  return profiles.find((p) => !isPartnerProfile(p)) ?? flaggedPrimary;
}

/** True when user must complete birth profile (post-login onboarding). */
export function needsProfileSetup(
  profiles: ProfileEntry[],
  primaryProfileId: string | null,
): boolean {
  if (profiles.length === 0) return true;
  const native = resolveNativeAskProfile(profiles, primaryProfileId);
  if (!native?.birthData?.place || native.birthData.lat == null) return true;
  if (!native.kundli?.planets?.length) return true;
  return false;
}

export interface SubscriptionInfo {
  plan:                "free" | "trial" | "basic" | "pro" | "elite";
  analysis_mode:       "basic" | "pro";
  is_pro:              boolean;
  is_basic_or_above:   boolean;
  trial_eligible:      boolean;
  trial_expires_at:    string | null;
  plan_expires_at:     string | null;
  limits: {
    questions_per_day: number;   // -1 = unlimited
    questions_used:    number;
    timeline_months:   number;
    profile_limit:     number;   // -1 = unlimited
  };
  prices: Record<string, number>;
  trial_days: number;
}

export interface AuthUser {
  id: number;
  /** Public app id e.g. COSMO100 — assigned at signup */
  cosmo_user_id?: string | null;
  name: string;
  /** Phone is the canonical identity since OTP migration. E.164 format e.g. "+919876543210". */
  phone?: string;
  country_code?: string;
  /** Legacy field — empty string for OTP-created accounts; kept for backward compat. */
  email: string;
  api_key: string;
  is_pro?: boolean;
  plan?: "free" | "trial" | "basic" | "pro" | "elite";
  plan_expiry?: string | null;
  subscription?: SubscriptionInfo;
  /** True after user saved display name once in Personal Details */
  personal_name_locked?: boolean;
  /** True after user saved mobile once in Personal Details */
  personal_phone_locked?: boolean;
}

type LangCode = UILang;

// ── Dosh result types ──────────────────────────────────────────────────────────
export interface DoshItem {
  key: string;
  name: string;
  name_hindi: string;
  icon: string;
  status: "Active" | "Mild" | "None";
  headline: string;
  description: string;
  remedies: string[];
  planet_note: string;
}

export interface DoshAnalysisResult {
  total_dosh: number;
  active_count: number;
  mild_count: number;
  none_count: number;
  dosh_list: DoshItem[];
}

// ── Context shape ────────────────────────────────────────────────────────────
interface UserContextType {
  user: AuthUser | null;

  // Single-profile compat (derived from primary)
  birthData: BirthData | null;
  kundli: KundliData | null;
  setBirthData: (d: BirthData | null) => void;
  setKundli: (k: KundliData | null) => void;

  // Multi-profile
  profiles: ProfileEntry[];
  primaryProfileId: string | null;
  addProfile: (entry: Omit<ProfileEntry, "id">) => ProfileEntry;
  updateProfile: (id: string, updates: Partial<Omit<ProfileEntry, "id">>) => void;
  deleteProfile: (id: string) => void;
  setPrimaryProfile: (id: string) => void;

  // Language
  language: LangCode;
  setLanguage: (l: LangCode) => void;
  isIndia: boolean;

  // Cloud sync
  syncKundliToCloud: (bd: BirthData, k: KundliData) => Promise<void>;
  /** Pull cloud profiles then push local — returns primary chart for Ask send. */
  syncProfilesNow: () => Promise<{ chart: KundliData | null; birth: BirthData | null }>;

  // Dosh Analysis (auto-computed for primary kundli)
  doshData: DoshAnalysisResult | null;
  doshLoading: boolean;

  // Other
  todayEnergy: number | null;
  moonData: { longitude: number; rashiIndex: number } | null;
  isLoading: boolean;
  setUser: (u: AuthUser | null) => void;
  setTodayEnergy: (e: number | null) => void;
  setMoonData: (m: { longitude: number; rashiIndex: number } | null) => void;
  logout: () => void;

  // Payment / subscription
  refreshUser: () => Promise<void>;
}

const UserContext = createContext<UserContextType | null>(null);

// ── Storage keys ──────────────────────────────────────────────────────────────
const KEYS = {
  user:       "cl_user_v2",
  profiles:   "cl_profiles_v2",
  primaryId:  "cl_primaryId_v2",
  language:   "cl_language",
  lastUserId: "cl_last_user_id",
  // legacy keys (for migration)
  birthData:  "cl_birthData",
  kundli:     "cl_kundli",
  legacyUser: "cl_user",
};

function clearLocalProfiles(
  setProfiles: (v: ProfileEntry[]) => void,
  setPrimaryId: (v: string | null) => void,
  profilesRef: React.MutableRefObject<ProfileEntry[]>,
  primaryIdRef: React.MutableRefObject<string | null>,
) {
  setProfiles([]);
  setPrimaryId(null);
  profilesRef.current = [];
  primaryIdRef.current = null;
  AsyncStorage.multiRemove([
    KEYS.profiles,
    KEYS.primaryId,
    KEYS.birthData,
    KEYS.kundli,
  ]).catch(() => {});
}

function uid() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

function isIndiaPlace(place: string) {
  const lower = (place ?? "").toLowerCase();
  return lower.includes("india") || lower.includes(", in") || lower.endsWith(",in");
}

// ── Provider ──────────────────────────────────────────────────────────────────
export function UserProvider({ children }: { children: React.ReactNode }) {
  const [user,        _setUser]        = useState<AuthUser | null>(null);
  const [profiles,    _setProfiles]    = useState<ProfileEntry[]>([]);
  const [primaryId,   _setPrimaryId]   = useState<string | null>(null);
  const [language,    _setLanguage]    = useState<LangCode>("en");
  const [todayEnergy, _setTodayEnergy] = useState<number | null>(null);
  const [moonData,    _setMoonData]    = useState<{ longitude: number; rashiIndex: number } | null>(null);
  const [isLoading,   setIsLoading]    = useState(true);
  const [doshData,    _setDoshData]    = useState<DoshAnalysisResult | null>(null);
  const [doshLoading, _setDoshLoading] = useState(false);
  const doshKundliRef = useRef<string | null>(null);

  // ── Load persisted data on mount ───────────────────────────────────────────
  useEffect(() => {
    (async () => {
      try {
        const [u, ps, pid, legacyBD, legacyK, legacyUser, lastUid] = await Promise.all([
          AsyncStorage.getItem(KEYS.user),
          AsyncStorage.getItem(KEYS.profiles),
          AsyncStorage.getItem(KEYS.primaryId),
          AsyncStorage.getItem(KEYS.birthData),
          AsyncStorage.getItem(KEYS.kundli),
          AsyncStorage.getItem(KEYS.legacyUser),
          AsyncStorage.getItem(KEYS.lastUserId),
        ]);

        // App always opens in English; user may switch language for this session only.
        const resolvedLang: LangCode = "en";
        _setLanguage(resolvedLang);

        // Load user — migrate legacy (name+email only) to new AuthUser format
        let hydratedUser: AuthUser | null = null;
        if (u) {
          const parsed = JSON.parse(u) as AuthUser;
          let apiKey = parsed.api_key ?? null;
          if (apiKey) {
            await saveApiKey(parsed.id, apiKey);
            await AsyncStorage.setItem(KEYS.user, JSON.stringify(userWithoutApiKey(parsed)));
          } else {
            apiKey = await loadApiKey(parsed.id);
          }
          if (apiKey) {
            hydratedUser = { ...parsed, api_key: apiKey };
          } else {
            hydratedUser = parsed;
          }
        } else if (legacyUser) {
          const old = JSON.parse(legacyUser);
          // Old format only had name/email — treat as guest
          if (!old.id) {
            // just a guest, don't restore
          }
        }

        // ── RTL boot enforcement (native only) ─────────────────────────────
        // Web: skip — reload loops leave the Expo spinner spinning forever.
        if (Platform.OS !== "web") {
          try {
            const { applyRTLForLang } = await import("@/lib/rtl");
            await applyRTLForLang(resolvedLang, { silent: true });
          } catch (err) {
            console.warn("[UserContext] boot RTL apply failed:", err);
          }
        }

        const storedLastId = lastUid ? parseInt(lastUid, 10) : null;
        const profileUserMismatch =
          hydratedUser != null &&
          storedLastId != null &&
          !Number.isNaN(storedLastId) &&
          storedLastId !== hydratedUser.id;

        let loadedProfiles: ProfileEntry[] = [];
        if (profileUserMismatch) {
          await AsyncStorage.multiRemove([KEYS.profiles, KEYS.primaryId, KEYS.birthData, KEYS.kundli]);
        } else if (ps) {
          loadedProfiles = JSON.parse(ps) as ProfileEntry[];
        } else if (legacyBD) {
          // Migrate legacy single-profile data
          const bd: BirthData = JSON.parse(legacyBD);
          const kd: KundliData | null = legacyK ? JSON.parse(legacyK) : null;
          const entry: ProfileEntry = {
            id: uid(), name: bd.name, gender: "",
            birthData: bd, kundli: kd,
          };
          loadedProfiles = [entry];
          await AsyncStorage.setItem(KEYS.profiles, JSON.stringify(loadedProfiles));
        }

        _setProfiles(loadedProfiles);

        const resolvedPid = pid && loadedProfiles.find(p => p.id === pid)
          ? pid
          : (loadedProfiles[0]?.id ?? null);
        _setPrimaryId(resolvedPid);
        if (resolvedPid) await AsyncStorage.setItem(KEYS.primaryId, resolvedPid);

        // No saved kundli → show Login first; onboarding only after fresh sign-in.
        if (hydratedUser && needsProfileSetup(loadedProfiles, resolvedPid)) {
          await AsyncStorage.removeItem(KEYS.user);
          hydratedUser = null;
        }

        if (hydratedUser) {
          _setUser(hydratedUser);
          userRef.current = hydratedUser;
          AsyncStorage.setItem(KEYS.lastUserId, String(hydratedUser.id)).catch(() => {});
        }

      } catch {}
      setIsLoading(false);
    })();
  }, []);

  // ── Cloud sync refs & helpers (must appear before handlers that use them) ──
  const userRef      = useRef<AuthUser | null>(null);
  const primaryIdRef = useRef<string | null>(null);
  const profilesRef  = useRef<ProfileEntry[]>([]);
  const syncTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => { userRef.current      = user;      }, [user]);
  useEffect(() => { primaryIdRef.current = primaryId; }, [primaryId]);
  useEffect(() => { profilesRef.current  = profiles;  }, [profiles]);

  const clearAppSession = useCallback((keepLastUserId: boolean) => {
    const prevId = userRef.current?.id;
    _setUser(null);
    userRef.current = null;
    clearLocalProfiles(_setProfiles, _setPrimaryId, profilesRef, primaryIdRef);
    _setTodayEnergy(null);
    _setMoonData(null);
    _setDoshData(null);
    doshKundliRef.current = null;
    if (syncTimerRef.current) {
      clearTimeout(syncTimerRef.current);
      syncTimerRef.current = null;
    }
    const removals: Promise<void>[] = [
      AsyncStorage.removeItem(KEYS.user),
      AsyncStorage.removeItem(KEYS.legacyUser),
      clearAllLocalReports(),
      clearServerSyncCache(),
    ];
    stopReportAutoSync();
    if (keepLastUserId && prevId != null) {
      removals.push(AsyncStorage.setItem(KEYS.lastUserId, String(prevId)));
    } else if (prevId != null) {
      removals.push(clearApiKey(prevId));
    }
    Promise.all(removals).catch(() => {});
  }, []);

  const invalidateDeletedAccount = useCallback(async () => {
    await signOutFromFirebase().catch(() => {});
    clearAppSession(true);
    try {
      router.replace("/login");
    } catch {
      /* navigation not ready */
    }
  }, [clearAppSession]);

  const pushProfilesToCloud = useCallback(async (list: ProfileEntry[], pid: string | null) => {
    const currentUser = userRef.current;
    if (!currentUser?.id || !currentUser?.api_key) return;
    try {
      const r = await fetch(`${API_BASE}/api/user/${currentUser.id}/profiles/sync`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...userAuthHeaders(currentUser),
        },
        body: JSON.stringify({
          profiles: list.map(p => ({
            id: p.id, name: p.name, gender: p.gender, relation: p.relation ?? "",
            birthData: p.birthData, kundli: p.kundli,
          })),
          primaryProfileId: pid,
        }),
      });
      if (r.status === 404 || r.status === 401) {
        await invalidateDeletedAccount();
      }
    } catch { /* silent — local is source of truth */ }
  }, [invalidateDeletedAccount]);

  const queueCloudSync = useCallback((list: ProfileEntry[], pid: string | null) => {
    if (syncTimerRef.current) clearTimeout(syncTimerRef.current);
    syncTimerRef.current = setTimeout(() => { pushProfilesToCloud(list, pid); }, 600);
  }, [pushProfilesToCloud]);

  const pullProfilesFromCloud = useCallback(async (u: AuthUser) => {
    if (!u?.id || !u?.api_key) return;
    try {
      const r = await apiFetchWithTimeout(`${API_BASE}/api/user/${u.id}/profiles`, {
        headers: userAuthHeaders(u),
      }, 8000);
      if (r.status === 404 || r.status === 401) {
        await invalidateDeletedAccount();
        return;
      }
      if (!r.ok) return;
      const data = await r.json();
      const cloudProfiles: ProfileEntry[] = (data?.profiles ?? []).map((p: any) => ({
        id: p.id, name: p.name ?? "", gender: p.gender ?? "",
        relation: p.relation ?? undefined,
        birthData: p.birthData, kundli: p.kundli ?? null,
      })).filter((p: ProfileEntry) => !!p.birthData);
      const cloudPrimary = data?.primaryProfileId ?? null;
      const local = profilesRef.current;

      if (cloudProfiles.length > 0) {
        const cloudIds = new Set(cloudProfiles.map((p) => p.id));
        const onlyOnDevice = local.filter((p) => !cloudIds.has(p.id));
        const mergedFromCloud = cloudProfiles.map((cp) => {
          const localMatch = local.find((lp) => lp.id === cp.id);
          const localChart = localMatch?.kundli;
          const cloudChart = cp.kundli;
          const localBirth = localMatch?.birthData;
          const cloudBirth = cp.birthData;
          const birthSame =
            localBirth &&
            cloudBirth &&
            localBirth.day === cloudBirth.day &&
            localBirth.month === cloudBirth.month &&
            localBirth.year === cloudBirth.year &&
            localBirth.hour === cloudBirth.hour &&
            localBirth.minute === cloudBirth.minute &&
            localBirth.ampm === cloudBirth.ampm;
          const keepLocalChart =
            (localChart?.planets?.length ?? 0) > 0 &&
            (!(cloudChart?.planets?.length ?? 0) || !birthSame);
          if (keepLocalChart) {
            return {
              ...cp,
              kundli: localChart,
              birthData: localMatch?.birthData ?? cp.birthData,
            };
          }
          return cp;
        });
        const merged =
          onlyOnDevice.length > 0 ? [...mergedFromCloud, ...onlyOnDevice] : mergedFromCloud;

        _setProfiles(merged);
        profilesRef.current = merged;
        AsyncStorage.setItem(KEYS.profiles, JSON.stringify(merged)).catch(() => {});

        const resolvedPid =
          cloudPrimary && merged.find((p) => p.id === cloudPrimary)
            ? cloudPrimary
            : primaryIdRef.current && merged.find((p) => p.id === primaryIdRef.current)
              ? primaryIdRef.current
              : merged[0].id;
        _setPrimaryId(resolvedPid);
        primaryIdRef.current = resolvedPid;
        AsyncStorage.setItem(KEYS.primaryId, resolvedPid).catch(() => {});

        if (onlyOnDevice.length > 0) {
          pushProfilesToCloud(merged, resolvedPid);
        }
      } else if (local.length > 0) {
        // Server empty but phone has profiles — upload; NEVER erase local here.
        pushProfilesToCloud(local, primaryIdRef.current);
      }
      // Both empty: nothing to do (account switch already cleared via setUser).
    } catch { /* silent */ }
  }, [pushProfilesToCloud, invalidateDeletedAccount]);

  const syncProfilesNow = useCallback(async (): Promise<{ chart: KundliData | null; birth: BirthData | null }> => {
    if (syncTimerRef.current) {
      clearTimeout(syncTimerRef.current);
      syncTimerRef.current = null;
    }
    const currentUser = userRef.current;
    // Push local first so cloud cannot overwrite a fresher on-device chart.
    await pushProfilesToCloud(profilesRef.current, primaryIdRef.current);
    if (currentUser?.id && currentUser?.api_key) {
      await pullProfilesFromCloud(currentUser);
    }
    const prof = resolveNativeAskProfile(profilesRef.current, primaryIdRef.current);
    return { chart: prof?.kundli ?? null, birth: prof?.birthData ?? null };
  }, [pushProfilesToCloud, pullProfilesFromCloud]);

  // ── Derived values ─────────────────────────────────────────────────────────
  const primaryProfile = profiles.find(p => p.id === primaryId) ?? profiles[0] ?? null;
  const nativeAskProfile = resolveNativeAskProfile(profiles, primaryId);
  const birthData = nativeAskProfile?.birthData ?? primaryProfile?.birthData ?? null;
  const kundli    = nativeAskProfile?.kundli ?? primaryProfile?.kundli ?? null;

  const isIndia = isIndiaPlace(birthData?.place ?? "") ||
                  (birthData?.country ?? "").toLowerCase() === "in";

  // ── Profile helpers ────────────────────────────────────────────────────────
  function saveProfiles(ps: ProfileEntry[]) {
    _setProfiles(ps);
    AsyncStorage.setItem(KEYS.profiles, JSON.stringify(ps)).catch(() => {});
  }

  // ── Compat: setBirthData updates primary profile ───────────────────────────
  const setBirthData = useCallback((d: BirthData | null) => {
    if (!d) return;
    _setProfiles(prev => {
      const pid = primaryId ?? prev[0]?.id ?? null;
      if (!pid) {
        const entry: ProfileEntry = { id: uid(), name: d.name, gender: "", birthData: d, kundli: null };
        const next = [entry];
        AsyncStorage.setItem(KEYS.profiles, JSON.stringify(next)).catch(() => {});
        AsyncStorage.setItem(KEYS.primaryId, entry.id).catch(() => {});
        _setPrimaryId(entry.id);
        return next;
      }
      const next = prev.map(p => p.id === pid ? { ...p, birthData: d, name: d.name } : p);
      AsyncStorage.setItem(KEYS.profiles, JSON.stringify(next)).catch(() => {});
      return next;
    });
  }, [primaryId]);

  // ── Compat: setKundli updates primary profile ──────────────────────────────
  const setKundli = useCallback((k: KundliData | null) => {
    _setProfiles(prev => {
      const pid = primaryId ?? prev[0]?.id ?? null;
      if (!pid) return prev;
      const next = prev.map(p => p.id === pid ? { ...p, kundli: k } : p);
      AsyncStorage.setItem(KEYS.profiles, JSON.stringify(next)).catch(() => {});
      return next;
    });
  }, [primaryId]);

  const addProfile = useCallback((entry: Omit<ProfileEntry, "id">): ProfileEntry => {
    const newEntry: ProfileEntry = { ...entry, id: uid() };
    _setProfiles(prev => {
      const next = [...prev, newEntry];
      AsyncStorage.setItem(KEYS.profiles, JSON.stringify(next)).catch(() => {});
      queueCloudSync(next, primaryIdRef.current);
      return next;
    });
    return newEntry;
  }, []);

  const updateProfile = useCallback((id: string, updates: Partial<Omit<ProfileEntry, "id">>) => {
    _setProfiles(prev => {
      const next = prev.map(p => p.id === id ? { ...p, ...updates } : p);
      AsyncStorage.setItem(KEYS.profiles, JSON.stringify(next)).catch(() => {});
      queueCloudSync(next, primaryIdRef.current);
      return next;
    });
  }, []);

  const deleteProfile = useCallback((id: string) => {
    _setProfiles(prev => {
      const next = prev.filter(p => p.id !== id);
      AsyncStorage.setItem(KEYS.profiles, JSON.stringify(next)).catch(() => {});
      let nextPrimary: string | null = primaryIdRef.current;
      _setPrimaryId(prevId => {
        if (prevId !== id) { nextPrimary = prevId; return prevId; }
        const fallback = next[0]?.id ?? null;
        if (fallback) AsyncStorage.setItem(KEYS.primaryId, fallback).catch(() => {});
        nextPrimary = fallback;
        return fallback;
      });
      queueCloudSync(next, nextPrimary);
      return next;
    });
  }, []);

  const setPrimaryProfile = useCallback((id: string) => {
    const target = profilesRef.current.find((p) => p.id === id);
    if (target && isPartnerProfile(target)) return;
    _setPrimaryId(id);
    primaryIdRef.current = id;
    AsyncStorage.setItem(KEYS.primaryId, id).catch(() => {});
    // CRITICAL (May 6 2026 fix): backend /api/ask{,/stream} loads kundli
    // from the legacy `kundlis` table, which is mirrored from the primary
    // profile by /api/user/<id>/profiles/sync. Local-only state change
    // would leave Ask answering for the OLD primary chart. FLUSH the
    // sync IMMEDIATELY (skip 600ms debounce) so the next /api/ask call
    // sees the correct chart with no race window.
    if (syncTimerRef.current) { clearTimeout(syncTimerRef.current); syncTimerRef.current = null; }
    pushProfilesToCloud(profilesRef.current, id);
  }, [pushProfilesToCloud]);

  const setUser = useCallback(async (u: AuthUser | null) => {
    if (u) {
      let switchedAccount = false;
      try {
        const stored = await AsyncStorage.getItem(KEYS.lastUserId);
        const prevId = stored ? parseInt(stored, 10) : userRef.current?.id ?? null;
        switchedAccount = prevId != null && !Number.isNaN(prevId) && prevId !== u.id;
      } catch { /* ignore */ }

      if (switchedAccount) {
        clearLocalProfiles(_setProfiles, _setPrimaryId, profilesRef, primaryIdRef);
      }

      _setUser(u);
      userRef.current = u;
      if (u.api_key) {
        await saveApiKey(u.id, u.api_key);
      }
      AsyncStorage.setItem(KEYS.user, JSON.stringify(userWithoutApiKey(u))).catch(() => {});
      AsyncStorage.setItem(KEYS.lastUserId, String(u.id)).catch(() => {});
      void pullProfilesFromCloud(u);
    } else {
      const prevId = userRef.current?.id;
      _setUser(null);
      userRef.current = null;
      AsyncStorage.removeItem(KEYS.user).catch(() => {});
      if (prevId != null) {
        void clearApiKey(prevId);
      }
    }
  }, [pullProfilesFromCloud]);

  const setLanguage = useCallback((l: LangCode | string) => {
    const resolved = coerceUILang(l);
    _setLanguage(resolved);
    import("@/lib/rtl")
      .then(({ applyRTLForLang }) => applyRTLForLang(resolved))
      .catch((err) => console.warn("[UserContext] RTL apply failed:", err));
  }, []);

  const setTodayEnergy = useCallback((e: number | null) => { _setTodayEnergy(e); }, []);
  const setMoonData    = useCallback((m: { longitude: number; rashiIndex: number } | null) => { _setMoonData(m); }, []);

  // ── Auto dosh analysis when primary kundli or UI language changes ───────────
  useEffect(() => {
    const primaryProfile = profiles.find(p => p.id === primaryId) ?? profiles[0] ?? null;
    const kundli = primaryProfile?.kundli ?? null;
    const currentUser = userRef.current;
    if (!kundli?.planets?.length || !currentUser?.id || !currentUser?.api_key) {
      _setDoshData(null);
      return;
    }

    const fp = JSON.stringify({
      p: kundli.planets.map(pl => `${pl.name}:${pl.house}`).sort(),
      lang: language,
    });
    if (fp === doshKundliRef.current) return;
    doshKundliRef.current = fp;

    _setDoshLoading(true);
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 30000);

    fetch(`${API_BASE}/api/dosh-analysis`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-User-Id": String(currentUser.id),
        "X-API-Key": currentUser.api_key,
      },
      body: JSON.stringify({
        planets: kundli.planets,
        nakshatra: kundli.nakshatra ?? "",
        lang: coerceUILang(language),
      }),
      signal: controller.signal,
    })
      .then(r => r.json())
      .then(data => { _setDoshData(data as DoshAnalysisResult); })
      .catch(() => { /* silent — dosh.tsx falls back to local calc */ })
      .finally(() => { clearTimeout(timer); _setDoshLoading(false); });

    return () => { clearTimeout(timer); controller.abort(); };
  }, [profiles, primaryId, language]);

  // ── Cloud sync (single-kundli legacy push for primary) ─────────────────────
  const syncKundliToCloud = useCallback(async (bd: BirthData, k: KundliData) => {
    const currentUser = userRef.current;
    if (!currentUser?.id || !currentUser?.api_key) return;
    const payload = {
      name: bd.name,
      dob:  `${String(bd.day).padStart(2,"0")}/${String(bd.month).padStart(2,"0")}/${bd.year}`,
      tob:  `${String(bd.hour).padStart(2,"0")}:${String(bd.minute).padStart(2,"0")} ${bd.ampm}`,
      pob:  bd.place,
      lat:  bd.lat,
      lon:  bd.lon,
      tz:   bd.tz,
      chart_data: k,
    };
    try {
      await fetch(`${API_BASE}/api/user/${currentUser.id}/kundli`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...userAuthHeaders(currentUser),
        },
        body: JSON.stringify(payload),
      });
    } catch { /* silent — local data is the source of truth */ }
  }, []);

  const logout = useCallback(() => {
    void signOutFromFirebase().catch(() => {});
    clearAppSession(true);
  }, [clearAppSession]);

  const refreshUser = useCallback(async () => {
    const currentUser = userRef.current;
    if (!currentUser?.id) return;
    try {
      const r = await fetch(`${API_BASE}/api/user/${currentUser.id}/kundli`, {
        headers: userAuthHeaders(currentUser),
      });
      if (r.status === 404 || r.status === 401) {
        await invalidateDeletedAccount();
        return;
      }
      if (!r.ok) return;
      const data = await r.json();
      if (data?.user) {
        const updated: AuthUser = { ...currentUser, ...data.user };
        if (updated.api_key) {
          await saveApiKey(updated.id, updated.api_key);
        }
        _setUser(updated);
        AsyncStorage.setItem(KEYS.user, JSON.stringify(userWithoutApiKey(updated))).catch(() => {});
      }
      await pullProfilesFromCloud(currentUser);
    } catch { /* silent */ }
  }, [pullProfilesFromCloud, invalidateDeletedAccount]);

  // On app start — if we hydrated a persisted user from AsyncStorage, pull cloud profiles once.
  const didInitialCloudPull = useRef(false);
  useEffect(() => {
    if (didInitialCloudPull.current) return;
    if (isLoading) return;
    if (!user?.id || !user?.api_key) return;
    didInitialCloudPull.current = true;
    void pullProfilesFromCloud(user);
  }, [isLoading, user, pullProfilesFromCloud]);

  // Admin deleted account → re-check when app returns to foreground (no periodic wipe).
  useEffect(() => {
    const onState = (state: AppStateStatus) => {
      if (state !== "active") return;
      const u = userRef.current;
      if (!u?.id || !u?.api_key) return;
      void pullProfilesFromCloud(u);
    };
    const sub = AppState.addEventListener?.("change", onState);
    return () => {
      try {
        sub?.remove?.();
      } catch {
        /* web may not return a subscription */
      }
    };
  }, [pullProfilesFromCloud]);

  // While app is open: poll session so admin hard-delete forces logout quickly.
  useEffect(() => {
    if (!user?.id || !user?.api_key) return;
    let cancelled = false;
    const check = async () => {
      const u = userRef.current;
      if (!u?.id || !u?.api_key || cancelled) return;
      try {
        const r = await apiFetchWithTimeout(
          `${API_BASE}/api/user/${u.id}/profiles`,
          { headers: userAuthHeaders(u) },
          8000,
        );
        if (cancelled) return;
        if (r.status === 401 || r.status === 404) {
          await invalidateDeletedAccount();
        }
      } catch {
        /* network blips — ignore */
      }
    };
    const id = setInterval(() => {
      void check();
    }, 20000);
    void check();
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [user?.id, user?.api_key, invalidateDeletedAccount]);

  // Coarse foreground-time analytics for the admin user inspector.
  useEffect(() => {
    if (!user?.id || !user?.api_key) return;

    let state: AppStateStatus = AppState.currentState || "active";
    let lastTickAt = Date.now();

    const sendUsage = (sessionStart = false) => {
      const u = userRef.current;
      if (!u?.id || !u?.api_key) return;
      const now = Date.now();
      const elapsedSeconds =
        state === "active" ? Math.max(0, Math.round((now - lastTickAt) / 1000)) : 0;
      lastTickAt = now;
      if (!sessionStart && elapsedSeconds < 1) return;
      void apiFetchWithTimeout(
        `${API_BASE}/api/user/${u.id}/app-usage`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-API-Key": u.api_key,
          },
          body: JSON.stringify({
            elapsed_seconds: elapsedSeconds,
            session_start: sessionStart,
          }),
        },
        8000,
      ).catch(() => {
        /* Analytics must never interrupt the user experience. */
      });
    };

    if (state === "active") sendUsage(true);
    const timer = setInterval(() => {
      if (state === "active") sendUsage(false);
    }, 60_000);
    const sub = AppState.addEventListener?.("change", (nextState) => {
      if (state === "active" && nextState !== "active") sendUsage(false);
      state = nextState;
      lastTickAt = Date.now();
      if (nextState === "active") sendUsage(true);
    });

    return () => {
      if (state === "active") sendUsage(false);
      clearInterval(timer);
      sub?.remove?.();
    };
  }, [user?.id, user?.api_key]);

  // Push token + auto-sync founder-delivered reports (no manual Fetch needed).
  useEffect(() => {
    if (!user?.id || !user?.api_key) {
      stopReportAutoSync();
      return;
    }
    void setupPushForUser(user.id, user.api_key);
    installUnreadReportsBridge();
    startReportAutoSync(user.id, user.api_key);
    const unsubscribeReports = subscribeNewReports((added) => {
      void presentReportReadyNotification(added).then((shown) => {
        // Android Expo Go cannot show push/local notification banners.
        // Keep a visible in-app fallback so report delivery is never silent.
        if (!shown && AppState.currentState === "active") {
          Alert.alert(
            "📄 Your report is ready",
            added === 1
              ? "Aapki report My Reports mein aa gayi hai."
              : `${added} reports My Reports mein aa gayi hain.`,
            [
              { text: "Later", style: "cancel" },
              { text: "Open My Reports", onPress: () => router.push("/my-reports" as any) },
            ],
          );
        }
      });
    });
    const pushSub = attachPushReceivedHandler((data) => {
      const screen = typeof data.screen === "string" ? data.screen : "";
      const kind = typeof data.kind === "string" ? data.kind : "";
      if (screen !== "/my-reports" && kind !== "love_reality_pro" && kind !== "report_ready") {
        return;
      }
      const u = userRef.current;
      if (!u?.id || !u.api_key) return;
      void syncServerReportsForUser({ userId: u.id, apiKey: u.api_key });
    });
    return () => {
      stopReportAutoSync();
      unsubscribeReports();
      try {
        pushSub?.remove?.();
      } catch {
        /* push unsupported */
      }
    };
  }, [user?.id, user?.api_key]);

  const value = useMemo(() => ({
      user, birthData, kundli, setBirthData, setKundli,
      profiles, primaryProfileId: primaryId,
      addProfile, updateProfile, deleteProfile, setPrimaryProfile,
      language, setLanguage, isIndia,
      syncKundliToCloud, syncProfilesNow,
      doshData, doshLoading,
      todayEnergy, moonData, isLoading,
      setUser, setTodayEnergy, setMoonData, logout,
      refreshUser,
    }), [
      user, birthData, kundli, setBirthData, setKundli,
      profiles, primaryId,
      addProfile, updateProfile, deleteProfile, setPrimaryProfile,
      language, setLanguage, isIndia,
      syncKundliToCloud, syncProfilesNow,
      doshData, doshLoading,
      todayEnergy, moonData, isLoading,
      setUser, setTodayEnergy, setMoonData, logout,
      refreshUser,
    ]);

  return (
    <UserContext.Provider value={value}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error("useUser must be used inside UserProvider");
  return ctx;
}
