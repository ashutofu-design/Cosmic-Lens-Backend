import type { BirthData } from "@/types";

/** Birth payload for Love Reality API — shared to avoid circular imports. */
export function packLovePerson(bd: BirthData, name?: string) {
  return {
    name: name || bd.name,
    day: bd.day,
    month: bd.month,
    year: bd.year,
    hour: bd.hour,
    minute: bd.minute,
    ampm: bd.ampm,
    lat: bd.lat,
    lon: bd.lon,
    tz: bd.tz,
    place: bd.place,
    gender: bd.gender,
  };
}
