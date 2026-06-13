export type MarriageBand = "Strong" | "Moderate" | "Strained";
export type CoupleBand = "Promising" | "Workable" | "High Effort";

export type SeventhInfluenceDetail = {
  planet: string;
  source: "occupant" | "aspect";
  natural: "benefic" | "malefic" | "neutral";
  rules_houses: number[];
  dusthana_rules: number[];
  good_rules: number[];
  lordship_tier: "dusthana_lord" | "mixed_lord" | "supportive_lord" | "neutral_lord";
  effect: string;
  score_delta: number;
  note: string;
  dignity_word?: string | null;
  combust?: boolean;
  retrograde?: boolean;
  is_yogakaraka?: boolean;
  functional?: string;
  orb_degrees?: number | null;
  orb_weight?: number;
};

export type MarriageD1Block = {
  seventh_house_sign: string;
  planets_in_seventh: string[];
  benefics_in_seventh: string[];
  malefics_in_seventh: string[];
  aspects_on_seventh: string[];
  seventh_occupant_details?: SeventhInfluenceDetail[];
  seventh_aspect_details?: SeventhInfluenceDetail[];
  seventh_lordship_summary?: string;
  seventh_influence_score_delta?: number;
  seventh_lord: string;
  seventh_lord_house: number | null;
  seventh_lord_sign: string | null;
  seventh_lord_dignity: string;
  seventh_lord_strength: string;
  seventh_lord_combust?: boolean;
  seventh_lord_retrograde?: boolean;
  seventh_empty?: { empty: boolean; score_delta: number; note: string | null };
  maraka_axis?: {
    second_lord: string;
    eighth_lord: string;
    second_occupants?: string[];
    eighth_occupants?: string[];
    note: string;
    notes: string[];
  };
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
  seventh_occupants?: string[];
  seventh_occupants_note?: string;
};

export type PartnerPlainCopy = {
  band_label: string;
  headline: string;
  positives: string[];
  watchouts: string[];
  pro_lock_teaser?: string;
  remedy_teaser?: string;
  pro_strip?: string;
  spouse_line?: string | null;
  long_term_line?: string | null;
  manglik_line?: string | null;
  timing_line?: string | null;
  friction?: string;
  remedy?: string;
  copy_tags?: string[];
};

export type CouplePlainCopy = {
  gap_teaser: string;
  pro_cta_line: string;
  alert_count?: number;
  locked_highlights?: string[];
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
    aspects?: string[];
    conjunctions?: string[];
    d9?: { sign: string | null; house: number | null; dignity: string } | null;
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
    aspects_on_ul_lord?: string[];
    ul_lord_conjunctions?: string[];
    aspects_on_ul_sign?: string[];
    depth_note?: string;
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
  manglik?: {
    has_dosh: boolean;
    effective: string;
    severity: string;
    sources: string[];
    cancellations: string[];
    note: string;
  };
  dasha_timeline?: {
    available: boolean;
    current?: {
      maha?: string | null;
      antar?: string | null;
      pratyantar?: string | null;
      start_date?: string | null;
      end_date?: string | null;
      note?: string;
    };
    stress_windows?: { range: string; maha: string; antar: string; note: string }[];
    reconnection_windows?: { range: string; maha: string; antar: string; note: string }[];
    why_now_hint?: string;
  };
  critical_alerts?: {
    count: number;
    locked: boolean;
    teaser: string;
    unlock_in?: string | null;
    detail?: { id: string; label: string }[];
  };
  relationship_signals_safe?: {
    affliction_weight: number;
    reconnection_yoga: boolean;
    separation_yoga: boolean;
    safe_notes: string[];
  };
  relationship_signals?: {
    affliction_weight: number;
    loyalty_risk_high: boolean;
    third_person_risk: boolean;
    separation_yoga: boolean;
    reconnection_yoga: boolean;
    venus_mars_conjunct: boolean;
    moon_in_8th: boolean;
    d9_seventh_lord_weak: boolean;
    seventh_lord_dusthana: boolean;
    saturn_on_7th: boolean;
    rahu_on_7th_axis: boolean;
    key_notes: string[];
  };
  gender_flags: string[];
  friction: string;
  remedy: string;
  strengths: string[];
  pressures: string[];
  plain_copy?: PartnerPlainCopy;
};

export type MarriageBasicsPayload = {
  engine: string;
  couple: {
    structural_score: number;
    structural_band: CoupleBand;
    future_verdict: string;
    d9_sync_note: string;
    d9_sync?: {
      available: boolean;
      score_0_10?: number | null;
      lagna_lord_relation?: string;
      seven_lord_relation?: string;
      notes?: string[];
    };
    synastry?: {
      available: boolean;
      score_0_10?: number | null;
      p1_7l?: string | null;
      p2_7l?: string | null;
      summary?: string;
      drivers?: string[];
      cautions?: string[];
      p1_7l_in_p2_house?: number | null;
      p2_7l_in_p1_house?: number | null;
      pada_yoni?: {
        available: boolean;
        p1_nak?: string;
        p1_pada?: number;
        p2_nak?: string;
        p2_pada?: number;
        pada_match?: string;
        pada_note?: string;
        yoni_score?: number;
        yoni_max?: number;
        yoni_label?: string;
        note?: string;
      };
    };
    manglik?: {
      p1_has_dosh: boolean;
      p2_has_dosh: boolean;
      p1_effective: string;
      p2_effective: string;
      mutual_cancellation: boolean;
      imbalance: boolean;
      note: string;
    };
    couple_signals?: {
      moon_mismatch: boolean;
      cross_rahu_venus: boolean;
      combined_affliction: number;
      synastry_notes: string[];
    };
    graha_maitri?: {
      available: boolean;
      relation?: string;
      p1_moon_lord?: string;
      p2_moon_lord?: string;
      note?: string;
    };
    dasha_timeline?: {
      p1?: MarriagePartnerBasics["dasha_timeline"];
      p2?: MarriagePartnerBasics["dasha_timeline"];
    };
    critical_alerts_total?: number;
    kp_couple?: {
      available: boolean;
      couple_verdict?: string;
      p1_verdict?: string;
      p2_verdict?: string;
    };
    plain_copy?: CouplePlainCopy;
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
