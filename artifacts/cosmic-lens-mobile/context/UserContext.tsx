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

export interface AuthUser {
  id: number;
  name: string;
  email: string;
  api_key: string;
  is_pro?: boolean;
  plan?: "free" | "pro" | "elite";
  plan_expiry?: string | null;
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

        if (lang) _setLanguage(JSON.parse(lang));

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
      return next;
    });
    return newEntry;
  }, []);

  const updateProfile = useCallback((id: string, updates: Partial<Omit<ProfileEntry, "id">>) => {
    _setProfiles(prev => {
      const next = prev.map(p => p.id === id ? { ...p, ...updates } : p);
      AsyncStorage.setItem(KEYS.profiles, JSON.stringify(next)).catch(() => {});
      return next;
    });
  }, []);

  const deleteProfile = useCallback((id: string) => {
    _setProfiles(prev => {
      const next = prev.filter(p => p.id !== id);
      AsyncStorage.setItem(KEYS.profiles, JSON.stringify(next)).catch(() => {});
      _setPrimaryId(prevId => {
        if (prevId !== id) return prevId;
        const fallback = next[0]?.id ?? null;
        if (fallback) AsyncStorage.setItem(KEYS.primaryId, fallback).catch(() => {});
        return fallback;
      });
      return next;
    });
  }, []);

  const setPrimaryProfile = useCallback((id: string) => {
    _setPrimaryId(id);
    AsyncStorage.setItem(KEYS.primaryId, id).catch(() => {});
  }, []);

  const setUser = useCallback((u: AuthUser | null) => {
    _setUser(u);
    if (u) AsyncStorage.setItem(KEYS.user, JSON.stringify(u)).catch(() => {});
    else   AsyncStorage.removeItem(KEYS.user).catch(() => {});
  }, []);

  const setLanguage = useCallback((l: LangCode) => {
    _setLanguage(l);
    AsyncStorage.setItem(KEYS.language, JSON.stringify(l)).catch(() => {});
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

  // ── Cloud sync ─────────────────────────────────────────────────────────────
  const userRef = useRef<AuthUser | null>(null);
  useEffect(() => { userRef.current = user; }, [user]);

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
    _setUser(null); _setProfiles([]); _setPrimaryId(null);
    _setTodayEnergy(null); _setMoonData(null);
    _setDoshData(null); doshKundliRef.current = null;
    Promise.all(Object.values(KEYS).map(k => AsyncStorage.removeItem(k))).catch(() => {});
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
    } catch { /* silent */ }
  }, []);

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
