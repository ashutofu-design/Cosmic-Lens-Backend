/** Format admin kundli chart JSON into a shareable V3 chat text pack. */

export type AdminChartPlanet = {
  name?: string;
  house?: number;
  sign?: string;
  rashi?: string;
  degrees?: string;
  degree?: number;
  longitude?: number;
  nakshatra?: string;
  nakshatraPada?: number;
  nakshatraRuler?: string;
  retrograde?: boolean;
};

export type AdminChartPayload = {
  ok: boolean;
  user_id: number;
  cosmo_user_id?: string;
  name?: string;
  birth?: {
    name?: string;
    gender?: string;
    dob?: string;
    time?: string;
    place?: string;
  };
  chart?: {
    name?: string;
    ascendant?: string;
    ascendantDeg?: number;
    moonSign?: string;
    sunSign?: string;
    nakshatra?: string;
    nakshatraPada?: number;
    nakshatraRuler?: string;
    dob?: string;
    time?: string;
    place?: string;
    currentDasha?: {
      maha?: string;
      antar?: string;
      pratyantar?: string;
      startDate?: string;
      endDate?: string;
      mahaStartDate?: string;
      mahaEndDate?: string;
      pratyantarStart?: string;
      pratyantarEnd?: string;
    };
    planets?: AdminChartPlanet[];
    dashas?: Array<{
      planet?: string;
      startDate?: string;
      endDate?: string;
      subDashas?: Array<{
        planet?: string;
        startDate?: string;
        endDate?: string;
        subDashas?: Array<{ planet?: string; startDate?: string; endDate?: string }>;
      }>;
    }>;
    divisionalCharts?: Record<
      string,
      {
        ascendant?: string;
        planets?: Array<{ name?: string; sign?: string; house?: number }>;
      }
    >;
    kp?: {
      planets?: Array<{
        name?: string;
        house?: number;
        sign?: string;
        nl?: string;
        sb?: string;
        ss?: string;
        degree?: string;
      }>;
      cusps?: Array<{
        house?: number;
        sign?: string;
        nl?: string;
        sb?: string;
        degree?: string;
      }>;
    };
  };
  error?: string;
  message?: string;
};

function line(label: string, value: string | number | undefined | null): string {
  const v = value == null || String(value).trim() === "" ? "—" : String(value).trim();
  return `${label}: ${v}`;
}

function planetLine(p: AdminChartPlanet): string {
  const sign = p.sign || p.rashi || "";
  const deg = p.degrees || (p.degree != null ? String(p.degree) : "");
  const nak = p.nakshatra
    ? `${p.nakshatra}${p.nakshatraPada ? ` (pada ${p.nakshatraPada})` : ""}`
    : "";
  const bits = [
    p.name || "?",
    p.house != null ? `H${p.house}` : "",
    sign,
    deg,
    nak,
    p.retrograde ? "R" : "",
  ].filter(Boolean);
  return bits.join(" · ");
}

function dashaTs(raw?: string | Date | null): number {
  if (raw == null || raw === "") return NaN;
  const t = +new Date(raw);
  return Number.isFinite(t) ? t : NaN;
}

/** Same rule as mobile kundli.tsx activeDashaIndex. */
export function activeDashaIndex(
  items: Array<{ startDate?: string | Date; endDate?: string | Date }>,
  now = Date.now(),
): number {
  const ai = items.findIndex((s) => {
    const a = dashaTs(s.startDate);
    const b = dashaTs(s.endDate);
    return Number.isFinite(a) && Number.isFinite(b) && a <= now && now < b;
  });
  return ai >= 0 ? ai : 0;
}

/**
 * Live MD/AD/(PD) from dashas tree — matches app "chal rahi dasha".
 * Falls back to stored currentDasha if tree missing.
 */
export function resolveLiveCurrentDasha(
  chart: NonNullable<AdminChartPayload["chart"]> | null | undefined,
): NonNullable<NonNullable<AdminChartPayload["chart"]>["currentDasha"]> | null {
  if (!chart) return null;
  const dashas = Array.isArray(chart.dashas) ? chart.dashas : [];
  const now = Date.now();

  if (dashas.length) {
    const mi = activeDashaIndex(dashas, now);
    const maha = dashas[mi];
    const antars = Array.isArray(maha?.subDashas) ? maha.subDashas! : [];
    const ai = antars.length ? activeDashaIndex(antars, now) : 0;
    const antar = antars[ai];

    let pratyantar: string | undefined;
    let pratyantarStart: string | undefined;
    let pratyantarEnd: string | undefined;
    const prats = Array.isArray(antar?.subDashas) ? antar.subDashas! : [];
    if (prats.length) {
      const pi = activeDashaIndex(prats, now);
      const pd = prats[pi];
      pratyantar = pd?.planet;
      pratyantarStart = pd?.startDate != null ? String(pd.startDate) : undefined;
      pratyantarEnd = pd?.endDate != null ? String(pd.endDate) : undefined;
    } else if (chart.currentDasha?.pratyantar) {
      pratyantar = chart.currentDasha.pratyantar;
      pratyantarStart = chart.currentDasha.pratyantarStart;
      pratyantarEnd = chart.currentDasha.pratyantarEnd;
    }

    return {
      maha: maha?.planet,
      antar: antar?.planet,
      pratyantar,
      startDate:
        antar?.startDate != null
          ? String(antar.startDate)
          : maha?.startDate != null
            ? String(maha.startDate)
            : undefined,
      endDate:
        antar?.endDate != null
          ? String(antar.endDate)
          : maha?.endDate != null
            ? String(maha.endDate)
            : undefined,
      mahaStartDate: maha?.startDate != null ? String(maha.startDate) : undefined,
      mahaEndDate: maha?.endDate != null ? String(maha.endDate) : undefined,
      pratyantarStart,
      pratyantarEnd,
    };
  }

  return chart.currentDasha || null;
}

export function liveDashaMahaIndex(
  chart: NonNullable<AdminChartPayload["chart"]> | null | undefined,
): number {
  const dashas = Array.isArray(chart?.dashas) ? chart!.dashas! : [];
  if (!dashas.length) return 0;
  return activeDashaIndex(dashas);
}

/** Compact text pack for sharing into V3 live chat (user can read it). */
export function formatKundliShareText(data: AdminChartPayload): string {
  const c = data.chart || {};
  const b = data.birth || {};
  const name = b.name || data.name || c.name || "User";
  const lines: string[] = [
    "════ KUNDLI PACK ════",
    line("Name", name),
  ];
  if (data.cosmo_user_id) lines.push(line("Cosmo ID", data.cosmo_user_id));
  if (b.gender) lines.push(line("Gender", b.gender));
  lines.push(line("DOB", b.dob || c.dob));
  lines.push(line("Time", b.time || c.time));
  lines.push(line("Place", b.place || c.place));
  lines.push("");
  lines.push("── Lagna / Moon / Sun ──");
  lines.push(line("Lagna", c.ascendant));
  lines.push(
    line(
      "Moon",
      [c.moonSign, c.nakshatra ? `${c.nakshatra}${c.nakshatraPada ? ` p${c.nakshatraPada}` : ""}` : ""]
        .filter(Boolean)
        .join(" · ") || undefined,
    ),
  );
  lines.push(line("Sun", c.sunSign));

  const cd = resolveLiveCurrentDasha(c);
  if (cd) {
    lines.push("");
    lines.push("── Current Dasha (live · same as app) ──");
    lines.push(line("Maha", cd.maha));
    lines.push(line("Antar", cd.antar));
    if (cd.pratyantar) lines.push(line("Pratyantar", cd.pratyantar));
    lines.push(line("From", cd.startDate));
    lines.push(line("To", cd.endDate));
    if (cd.pratyantarStart || cd.pratyantarEnd) {
      lines.push(line("PD From", cd.pratyantarStart));
      lines.push(line("PD To", cd.pratyantarEnd));
    }
  }

  const planets = Array.isArray(c.planets) ? c.planets : [];
  if (planets.length) {
    lines.push("");
    lines.push("── D1 Planets ──");
    for (const p of planets) lines.push(planetLine(p));
  }

  const d9 = c.divisionalCharts?.D9;
  if (d9) {
    lines.push("");
    lines.push("── D9 Navamsa ──");
    lines.push(line("D9 Lagna", d9.ascendant));
    for (const p of d9.planets || []) {
      lines.push(
        [p.name || "?", p.house != null ? `H${p.house}` : "", p.sign || ""]
          .filter(Boolean)
          .join(" · "),
      );
    }
  }

  // Other common divisionals if present
  for (const key of ["D10", "D7", "D12", "D60"] as const) {
    const div = c.divisionalCharts?.[key];
    if (!div) continue;
    lines.push("");
    lines.push(`── ${key} ──`);
    lines.push(line(`${key} Lagna`, div.ascendant));
    for (const p of (div.planets || []).slice(0, 12)) {
      lines.push(
        [p.name || "?", p.house != null ? `H${p.house}` : "", p.sign || ""]
          .filter(Boolean)
          .join(" · "),
      );
    }
  }

  const kpPlanets = c.kp?.planets;
  if (kpPlanets?.length) {
    lines.push("");
    lines.push("── KP Planets ──");
    for (const p of kpPlanets) {
      lines.push(
        [
          p.name || "?",
          p.house != null ? `H${p.house}` : "",
          p.sign || "",
          p.degree || "",
          p.nl ? `NL ${p.nl}` : "",
          p.sb ? `SB ${p.sb}` : "",
          p.ss ? `SS ${p.ss}` : "",
        ]
          .filter(Boolean)
          .join(" · "),
      );
    }
  }
  const cusps = c.kp?.cusps;
  if (cusps?.length) {
    lines.push("");
    lines.push("── KP Cusps ──");
    for (const cu of cusps) {
      lines.push(
        [
          `H${cu.house}`,
          cu.sign || "",
          cu.degree || "",
          cu.nl ? `NL ${cu.nl}` : "",
          cu.sb ? `SB ${cu.sb}` : "",
        ]
          .filter(Boolean)
          .join(" · "),
      );
    }
  }

  const dashas = Array.isArray(c.dashas) ? c.dashas.slice(0, 6) : [];
  if (dashas.length) {
    lines.push("");
    lines.push("── Maha Dasha (timeline) ──");
    for (const d of dashas) {
      lines.push(
        `${d.planet || "?"} · ${d.startDate || "?"} → ${d.endDate || "?"}`,
      );
    }
  }

  lines.push("");
  lines.push("(Shared from Cosmic Intelligence V3 admin)");
  return lines.join("\n");
}

const SIGN_NAMES = [
  "Aries",
  "Taurus",
  "Gemini",
  "Cancer",
  "Leo",
  "Virgo",
  "Libra",
  "Scorpio",
  "Sagittarius",
  "Capricorn",
  "Aquarius",
  "Pisces",
];

function signIdxLoose(raw?: string | null): number {
  if (!raw) return 0;
  const s = String(raw).trim().toLowerCase();
  const i = SIGN_NAMES.findIndex(
    (n) => n.toLowerCase() === s || s.startsWith(n.toLowerCase().slice(0, 3)),
  );
  return i >= 0 ? i : 0;
}

/** D1 / Lagna chart only — for Share from Lagna tab into V3 chat. */
export function formatD1ChartShareText(data: AdminChartPayload): string {
  const c = data.chart || {};
  const b = data.birth || {};
  const name = b.name || data.name || c.name || "User";
  const lagna = c.ascendant || "—";
  const lagnaIdx = signIdxLoose(c.ascendant);
  const planets = Array.isArray(c.planets) ? c.planets : [];

  const byHouse: Record<number, AdminChartPlanet[]> = {};
  for (let h = 1; h <= 12; h++) byHouse[h] = [];
  for (const p of planets) {
    let h = typeof p.house === "number" && p.house >= 1 && p.house <= 12 ? p.house : 0;
    if (!h) {
      const si = signIdxLoose(p.sign || p.rashi);
      h = ((si - lagnaIdx + 12) % 12) + 1;
    }
    byHouse[h].push(p);
  }

  const lines: string[] = [
    "════ D1 · LAGNA CHART ════",
    line("Name", name),
  ];
  if (data.cosmo_user_id) lines.push(line("Cosmo ID", data.cosmo_user_id));
  lines.push(line("DOB", b.dob || c.dob));
  lines.push(line("Time", b.time || c.time));
  lines.push(line("Place", b.place || c.place));
  lines.push(line("Lagna", lagna));
  lines.push(
    line(
      "Moon",
      [c.moonSign, c.nakshatra ? `${c.nakshatra}${c.nakshatraPada ? ` p${c.nakshatraPada}` : ""}` : ""]
        .filter(Boolean)
        .join(" · ") || undefined,
    ),
  );
  lines.push(line("Sun", c.sunSign));
  lines.push("");
  lines.push("── Houses (D1) ──");
  for (let h = 1; h <= 12; h++) {
    const sign = SIGN_NAMES[(lagnaIdx + h - 1) % 12];
    const occ = byHouse[h];
    const names =
      occ.length === 0
        ? "—"
        : occ
            .map((p) => {
              const bits = [p.name || "?"];
              if (p.degrees || p.degree != null) bits.push(String(p.degrees || p.degree));
              if (p.retrograde) bits.push("R");
              return bits.join(" ");
            })
            .join(", ");
    lines.push(`H${h} (${sign}): ${names}`);
  }
  lines.push("");
  lines.push("── Planets ──");
  for (const p of planets) lines.push(planetLine(p));
  lines.push("");
  lines.push("(D1 chart shared from Cosmic Intelligence V3 admin)");
  return lines.join("\n");
}
