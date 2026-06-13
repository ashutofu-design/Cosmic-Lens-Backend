export type MarriageBand = "Strong" | "Moderate" | "Strained";
export type CoupleBand = "Promising" | "Workable" | "High Effort";

export type MarriageD1Block = {
  seventh_house_sign: string;
  planets_in_seventh: string[];
  benefics_in_seventh: string[];
  malefics_in_seventh: string[];
  aspects_on_seventh: string[];
  seventh_lord: string;
  seventh_lord_house: number | null;
  seventh_lord_sign: string | null;
  seventh_lord_dignity: string;
  seventh_lord_strength: string;
  lordship_houses: number[];
  lordship_note: string;
};

export type MarriageD9Block = {
  available: boolean;
  seventh_house_sign: string | null;
  seventh_lord: string | null;
  seventh_lord_sign: string | null;
  seventh_lord_house: number | null;
  maturity_0_10: number | null;
  band: string;
  venus_dignity?: string;
  jupiter_dignity?: string;
};

export type MarriagePartnerBasics = {
  name: string;
  gender: "male" | "female" | "unknown";
  readiness_score: number;
  readiness_band: MarriageBand;
  d1: MarriageD1Block;
  d9: MarriageD9Block;
  darakaraka: {
    planet: string | null;
    sign: string | null;
    house: number | null;
    dignity?: string;
    note: string;
  };
  upapada: {
    available: boolean;
    ul_sign: string | null;
    ul_lord: string | null;
    ul_lord_house_from_ul: number | null;
    stability: string;
    verdict: string | null;
    occupants_ul: string[];
  };
  kp: {
    available: boolean;
    verdict: string;
    commitment_depth: string;
    seven_csl: {
      star_lord?: string;
      sub_lord?: string;
      sub_sub_lord?: string;
    } | null;
    signified_houses: number[];
    promise_hits: number;
    negation_hits: number;
  };
  karaka: {
    primary: string;
    role: string;
    sign: string | null;
    house: number | null;
    dignity: string;
    strength: string;
    note: string;
  };
  gender_flags: string[];
  friction: string;
  remedy: string;
  strengths: string[];
  pressures: string[];
};

export type MarriageBasicsPayload = {
  engine: string;
  couple: {
    structural_score: number;
    structural_band: CoupleBand;
    future_verdict: string;
    d9_sync_note: string;
  };
  p1: MarriagePartnerBasics;
  p2: MarriagePartnerBasics;
};

export const COUPLE_BAND_COLORS: Record<CoupleBand, string> = {
  Promising: "#22c55e",
  Workable: "#fbbf24",
  "High Effort": "#ef4444",
};

export const READINESS_BAND_COLORS: Record<MarriageBand, string> = {
  Strong: "#22c55e",
  Moderate: "#fbbf24",
  Strained: "#ef4444",
};

export function bandColor(band: MarriageBand | CoupleBand): string {
  return (COUPLE_BAND_COLORS as Record<string, string>)[band]
    ?? (READINESS_BAND_COLORS as Record<string, string>)[band]
    ?? "#6366f1";
}
