import type { KundliData } from "@/types";
import { SIGNS, SIGNS_SHORT } from "@/lib/planetPositionUtils";

export type D1ChartData = {
  lagnaSignIdx: number;
  lagnaFull: string;
  lagnaShort: string;
  ascendantDeg: number;
  planets: {
    name: string;
    house: number;
    retrograde?: boolean;
    longitude?: number;
  }[];
};

export function getD1ChartData(kundli: KundliData | null | undefined): D1ChartData | null {
  if (!kundli?.planets?.length) return null;
  const asc = kundli.ascendantDeg ?? 0;
  const lagnaSignIdx = ((Math.floor(asc / 30) % 12) + 12) % 12;
  const planets = kundli.planets.map(p => {
    const signIdx = Math.floor((p.longitude ?? 0) / 30) % 12;
    const house = p.house ?? (((signIdx - lagnaSignIdx + 12) % 12) + 1);
    return {
      name: p.name,
      house,
      retrograde: p.retrograde,
      longitude: p.longitude,
    };
  });
  return {
    lagnaSignIdx,
    lagnaFull: SIGNS[lagnaSignIdx],
    lagnaShort: SIGNS_SHORT[lagnaSignIdx],
    ascendantDeg: asc,
    planets,
  };
}
