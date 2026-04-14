export interface BirthData {
  name: string;
  day: number;
  month: number;
  year: number;
  hour: number;
  minute: number;
  ampm: "AM" | "PM";
  place: string;
  lat: number;
  lon: number;
  tz: number;
  country?: string;
}

export interface PlanetInfo {
  name: string;
  house: number;
  longitude: number;
  degrees?: string;
  sign?: string;
  speed?: number;
  retrograde?: boolean;
  // legacy / computed
  degree?: number;
  rashi?: string;
  rashiIndex?: number;
  nakshatra?: string;
  nakshatraPada?: number;
}

export interface DashaData {
  planet: string;
  startDate: string;
  endDate: string;
  years?: number;
  subDashas?: DashaData[];
}

export interface KundliData {
  name: string;
  ascendant: string;
  ascendantDeg: number;
  nakshatra?: string;
  nakshatraPada?: number;
  nakshatraRuler?: string;
  moonSign?: string;
  moonLongitude?: number;
  sunSign?: string;
  dashaBalance?: number;
  dob?: string;
  time?: string;
  place?: string;
  currentDasha?: {
    maha: string;
    antar: string;
    startDate: string;
    endDate: string;
  };
  currentPhase?: {
    name: string;
    start: string;
    end: string;
  };
  planets: PlanetInfo[];
  dashas: DashaData[];
  calcVersion?: number;
  ashtakavarga?: Record<string, number[]>;
}

export interface MoonHistoryPoint {
  longitude: number;
  rashiIndex: number;
  label: string;
}
