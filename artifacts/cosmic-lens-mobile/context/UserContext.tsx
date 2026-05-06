import AsyncStorage from "@react-native-async-storage/async-storage";
import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import type { BirthData, KundliData } from "@/types";
import type { UILang } from "@/lib/i18n";
import { API_BASE } from "@/lib/apiConfig";

// ── ProfileEntry ────────────────────────────────────────────────────────────
export interface ProfileEntry {
  id: string;
  name: string;
  gender: string;
  relation?: string;
  birthData: BirthData;
  kundli: KundliData | null;
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
  // legacy keys (for migration)
  birthData:  "cl_birthData",
  kundli:     "cl_kundli",
  legacyUser: "cl_user",
};

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

  // ── Load persisted data on mount ───────────────────────────────────────────
  useEffect(() => {
    (async () => {
      try {
        const [u, ps, pid, lang, legacyBD, legacyK, legacyUser] = await Promise.all([
          AsyncStorage.getItem(KEYS.user),
          AsyncStorage.getItem(KEYS.profiles),
          AsyncStorage.getItem(KEYS.primaryId),
          AsyncStorage.getItem(KEYS.language),
          AsyncStorage.getItem(KEYS.birthData),
          AsyncStorage.getItem(KEYS.kundli),
          AsyncStorage.getItem(KEYS.legacyUser),
        ]);

        // Load user — migrate legacy (name+email only) to new AuthUser format
        if (u) {
          _setUser(JSON.parse(u));
        } else if (legacyUser) {
          const old = JSON.parse(legacyUser);
          // Old format only had name/email — treat as guest
          if (!old.id) {
            // just a guest, don't restore
          }
        }

        let resolvedLang: LangCode = "en";
        if (lang) {
          try { resolvedLang = JSON.parse(lang) as LangCode; } catch {}
          _setLanguage(resolvedLang);
        }
        // ── RTL boot enforcement (runs once, post-hydration) ──────────────
        // If the saved language requires a different layout direction than
        // I18nManager currently reports, silently apply forceRTL + reload.
        // This mainly fires on the FIRST launch after the user previously
        // selected Arabic in a session that ended before reload completed.
        try {
          const { applyRTLForLang } = await import("@/lib/rtl");
          await applyRTLForLang(resolvedLang, { silent: true });
        } catch (err) {
          console.warn("[UserContext] boot RTL apply failed:", err);
        }

        let loadedProfiles: ProfileEntry[] = [];
        if (ps) {
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

  const pushProfilesToCloud = useCallback(async (list: ProfileEntry[], pid: string | null) => {
    const currentUser = userRef.current;
    if (!currentUser?.id || !currentUser?.api_key) return;
    try {
      await fetch(`${API_BASE}/api/user/${currentUser.id}/profiles/sync`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": currentUser.api_key },
        body: JSON.stringify({
          profiles: list.map(p => ({
            id: p.id, name: p.name, gender: p.gender, relation: p.relation ?? "",
            birthData: p.birthData, kundli: p.kundli,
          })),
          primaryProfileId: pid,
        }),
      });
    } catch { /* silent — local is source of truth */ }
  }, []);

  const queueCloudSync = useCallback((list: ProfileEntry[], pid: string | null) => {
    if (syncTimerRef.current) clearTimeout(syncTimerRef.current);
    syncTimerRef.current = setTimeout(() => { pushProfilesToCloud(list, pid); }, 600);
  }, [pushProfilesToCloud]);

  const pullProfilesFromCloud = useCallback(async (u: AuthUser) => {
    if (!u?.id || !u?.api_key) return;
    try {
      const r = await fetch(`${API_BASE}/api/user/${u.id}/profiles`, {
        headers: { "X-API-Key": u.api_key },
      });
      if (!r.ok) return;
      const data = await r.json();
      const cloudProfiles: ProfileEntry[] = (data?.profiles ?? []).map((p: any) => ({
        id: p.id, name: p.name ?? "", gender: p.gender ?? "",
        relation: p.relation ?? undefined,
        birthData: p.birthData, kundli: p.kundli ?? null,
      })).filter((p: ProfileEntry) => !!p.birthData);
      const cloudPrimary = data?.primaryProfileId ?? null;

      // Merge with local — cloud is authoritative if non-empty, else push local up
      if (cloudProfiles.length > 0) {
        _setProfiles(cloudProfiles);
        AsyncStorage.setItem(KEYS.profiles, JSON.stringify(cloudProfiles)).catch(() => {});
        const resolvedPid = cloudPrimary && cloudProfiles.find(p => p.id === cloudPrimary)
          ? cloudPrimary : cloudProfiles[0].id;
        _setPrimaryId(resolvedPid);
        AsyncStorage.setItem(KEYS.primaryId, resolvedPid).catch(() => {});
      } else if (profilesRef.current.length > 0) {
        // Cloud empty but local has profiles → push local up
        pushProfilesToCloud(profilesRef.current, primaryIdRef.current);
      }
    } catch { /* silent */ }
  }, [pushProfilesToCloud]);

  // ── Derived values ─────────────────────────────────────────────────────────
  const primaryProfile = profiles.find(p => p.id === primaryId) ?? profiles[0] ?? null;
  const birthData = primaryProfile?.birthData ?? null;
  const kundli    = primaryProfile?.kundli ?? null;

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

  const setUser = useCallback((u: AuthUser | null) => {
    _setUser(u);
    if (u) {
      AsyncStorage.setItem(KEYS.user, JSON.stringify(u)).catch(() => {});
      pullProfilesFromCloud(u);
    } else {
      AsyncStorage.removeItem(KEYS.user).catch(() => {});
    }
  }, [pullProfilesFromCloud]);

  const setLanguage = useCallback((l: LangCode) => {
    _setLanguage(l);
    AsyncStorage.setItem(KEYS.language, JSON.stringify(l)).catch(() => {});
    // ── RTL handling: when switching to/from an RTL language (e.g. Arabic),
    // apply I18nManager.forceRTL and prompt user to restart the app so
    // layout flips correctly. No-op if direction already matches.
    import("@/lib/rtl")
      .then(({ applyRTLForLang }) => applyRTLForLang(l))
      .catch((err) => console.warn("[UserContext] RTL apply failed:", err));
  }, []);

  const setTodayEnergy = useCallback((e: number | null) => { _setTodayEnergy(e); }, []);
  const setMoonData    = useCallback((m: { longitude: number; rashiIndex: number } | null) => { _setMoonData(m); }, []);

  // ── Auto dosh analysis when primary kundli changes ─────────────────────────
  const doshKundliRef = useRef<string | null>(null);
  useEffect(() => {
    const primaryProfile = profiles.find(p => p.id === primaryId) ?? profiles[0] ?? null;
    const kundli = primaryProfile?.kundli ?? null;
    if (!kundli?.planets?.length) { _setDoshData(null); return; }

    // Fingerprint kundli to avoid redundant fetches
    const fp = JSON.stringify(kundli.planets.map(p => `${p.name}:${p.house}`).sort());
    if (fp === doshKundliRef.current) return;
    doshKundliRef.current = fp;

    _setDoshLoading(true);
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 10000);

    fetch(`${API_BASE}/api/dosh-analysis`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ planets: kundli.planets, nakshatra: kundli.nakshatra ?? "" }),
      signal: controller.signal,
    })
      .then(r => r.json())
      .then(data => { _setDoshData(data as DoshAnalysisResult); })
      .catch(() => { /* silent — dosh.tsx falls back to local calc */ })
      .finally(() => { clearTimeout(timer); _setDoshLoading(false); });

    return () => { clearTimeout(timer); controller.abort(); };
  }, [profiles, primaryId]);

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
        headers: { "Content-Type": "application/json", "X-API-Key": currentUser.api_key },
        body: JSON.stringify(payload),
      });
    } catch { /* silent — local data is the source of truth */ }
  }, []);

  const logout = useCallback(() => {
    _setUser(null);
    _setTodayEnergy(null); _setMoonData(null);
    _setDoshData(null); doshKundliRef.current = null;
    // Only clear auth session — keep profiles/primaryId/birthData/kundli/language
    // so user doesn't have to re-enter kundli details after logging back in.
    Promise.all([
      AsyncStorage.removeItem(KEYS.user),
      AsyncStorage.removeItem(KEYS.legacyUser),
    ]).catch(() => {});
  }, []);

  const refreshUser = useCallback(async () => {
    const currentUser = userRef.current;
    if (!currentUser?.id) return;
    try {
      const r = await fetch(`${API_BASE}/api/user/${currentUser.id}/kundli`, {
        headers: { "X-API-Key": currentUser.api_key ?? "" },
      });
      if (!r.ok) return;
      const data = await r.json();
      if (data?.user) {
        const updated: AuthUser = { ...currentUser, ...data.user };
        _setUser(updated);
        AsyncStorage.setItem(KEYS.user, JSON.stringify(updated)).catch(() => {});
      }
      // Always pull multi-profile snapshot too
      pullProfilesFromCloud(currentUser);
    } catch { /* silent */ }
  }, [pullProfilesFromCloud]);

  // On app start — if we hydrated a persisted user from AsyncStorage, pull cloud profiles once.
  const didInitialCloudPull = useRef(false);
  useEffect(() => {
    if (didInitialCloudPull.current) return;
    if (isLoading) return;
    if (!user?.id || !user?.api_key) return;
    didInitialCloudPull.current = true;
    pullProfilesFromCloud(user);
  }, [isLoading, user, pullProfilesFromCloud]);

  return (
    <UserContext.Provider value={{
      user, birthData, kundli, setBirthData, setKundli,
      profiles, primaryProfileId: primaryId,
      addProfile, updateProfile, deleteProfile, setPrimaryProfile,
      language, setLanguage, isIndia,
      syncKundliToCloud,
      doshData, doshLoading,
      todayEnergy, moonData, isLoading,
      setUser, setTodayEnergy, setMoonData, logout,
      refreshUser,
    }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error("useUser must be used inside UserProvider");
  return ctx;
}
