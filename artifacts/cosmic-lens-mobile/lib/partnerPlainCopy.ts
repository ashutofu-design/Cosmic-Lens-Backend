import type { MarriageBand, MarriagePartnerBasics } from "@/lib/milanMarriageBasics";

export type PartnerPlainView = {
  bandLabel: string;
  headline: string;
  positives: string[];
  watchouts: string[];
  spouseLine: string | null;
  longTermLine: string | null;
  manglikLine: string | null;
  timingLine: string | null;
};

const BAND_LABEL: Record<MarriageBand, string> = {
  Strong: "Good foundation",
  Moderate: "Mixed signals",
  Strained: "Needs extra care",
};

const BAND_HEADLINE: Record<MarriageBand, string> = {
  Strong: "This chart supports marriage well — choices and timing still shape the outcome.",
  Moderate: "Marriage can work here, but some habits and patience will matter after wedding.",
  Strained: "Marriage is possible but will ask more effort — don't ignore friction early.",
};

const D9_PLAIN: Record<string, string> = {
  Supportive: "Long-term married life looks supportive — bond can grow stronger with years.",
  Mixed: "Long-term tone is mixed — early marriage and later years may feel different.",
  Weak: "Long-term married life may feel tested — remedies and realistic expectations help.",
};

/** Strip jargon from engine notes for Basic screen readers. */
export function simplifyNote(raw: string): string {
  return raw
    .replace(/\b7th lord\b/gi, "Marriage ruler")
    .replace(/\b7th house\b/gi, "marriage zone")
    .replace(/\b7th\b/g, "marriage")
    .replace(/\bdusthana\b/gi, "stress house")
    .replace(/\bcombust\b/gi, "weakened by Sun")
    .replace(/\bvakri\b/gi, "retrograde")
    .replace(/\bretrograde\b/gi, "retrograde (delays likely)")
    .replace(/\bUpapada\b/g, "Marriage manifest point")
    .replace(/\bKP 7th cusp\b/gi, "Precision marriage promise")
    .replace(/\bD9\b/g, "Inner chart")
    .replace(/\bD1\b/g, "Birth chart")
    .replace(/\bDarakaraka\b/gi, "Spouse-sign planet")
    .replace(/\bmaraka\b/gi, "family/longevity")
    .replace(/\bsignificator\b/gi, "life-sign planet")
    .replace(/\bshubh\b/gi, "supportive")
    .replace(/\bmalefic\b/gi, "hard planet")
    .replace(/\bbenefic\b/gi, "soft planet")
    .replace(/\baspects?\b/gi, "influences")
    .replace(/\boccupant\b/gi, "planet sitting there")
    .replace(/\blordship\b/gi, "rules houses")
    .replace(/\s+/g, " ")
    .trim();
}

function flagToPlain(flag: string): string {
  const f = flag.toLowerCase();
  if (f.includes("combust")) return "Marriage ruler is weakened by the Sun — promise fades unless you act consistently.";
  if (f.includes("retrograde")) return "Marriage ruler is retrograde — old patterns or delays in partnership are common.";
  if (f.includes("mangal dosh active")) return "Mangal dosh is active — match with partner's chart and remedies matter.";
  if (f.includes("mangal dosh reduced")) return "Mangal dosh is partly cancelled — still worth checking partner balance.";
  if (f.includes("separation yoga")) return "Chart shows distance/separation theme — conscious repair time is important.";
  if (f.includes("d9") && f.includes("weak")) return "Inner marriage chart is weak — long-term tone needs care.";
  if (f.includes("jupiter") && f.includes("pressure")) return "Husband-sign planet Jupiter is under pressure.";
  if (f.includes("venus") && f.includes("pressure")) return "Wife-sign planet Venus is under pressure.";
  if (f.includes("dusthana")) return "Marriage ruler sits in a difficult life area — bond tests patience.";
  if (f.includes("saturn") && f.includes("7th")) return "Saturn presses on marriage zone — delays or duty-heavy partnerships.";
  return simplifyNote(flag);
}

function marriageZoneLine(p: MarriagePartnerBasics): string {
  const { d1 } = p;
  const soft = d1.benefics_in_seventh.length;
  const hard = d1.malefics_in_seventh.length;
  const occ = d1.planets_in_seventh.length;

  if (occ === 0) {
    if (d1.seventh_empty?.note) return simplifyNote(d1.seventh_empty.note);
    return "Marriage zone has no planets sitting directly — outcome leans on your marriage ruler's strength.";
  }
  if (soft > 0 && hard === 0) {
    return `Supportive planets in your marriage zone (${d1.benefics_in_seventh.join(", ")}) — warmth and cooperation come easier.`;
  }
  if (hard > 0 && soft === 0) {
    return `Hard planets in your marriage zone (${d1.malefics_in_seventh.join(", ")}) — more arguments or delays unless you manage temper.`;
  }
  if (soft > 0 && hard > 0) {
    return "Both soft and hard planets mix in your marriage zone — good days and stressful days both likely.";
  }
  return "Planets in your marriage zone give mixed signals — daily communication decides the tone.";
}

function marriageRulerLine(p: MarriagePartnerBasics): string | null {
  const { d1 } = p;
  if (!d1.seventh_lord || d1.seventh_lord_house == null) return null;

  let line = "";
  if (d1.seventh_lord_strength === "strong") {
    line = `Marriage ruler ${d1.seventh_lord} is well placed — good base for commitment.`;
  } else if (d1.seventh_lord_strength === "weak") {
    line = `Marriage ruler ${d1.seventh_lord} is under stress — delays or tests in partnership are more likely.`;
  } else {
    line = `Marriage ruler ${d1.seventh_lord} is average — neither very easy nor very hard by itself.`;
  }

  const extras: string[] = [];
  if (d1.seventh_lord_combust) extras.push("weakened by Sun");
  if (d1.seventh_lord_retrograde) extras.push("retrograde delays");
  if (extras.length) line += ` (${extras.join(", ")})`;
  return line;
}

function spouseLine(p: MarriagePartnerBasics): string | null {
  const dk = p.darakaraka;
  const karaka = p.karaka;
  const parts: string[] = [];

  if (dk.planet && dk.house != null) {
    parts.push(`You may attract a ${dk.planet}-type partner (house ${dk.house} theme).`);
  } else if (dk.note && !dk.note.includes("unavailable")) {
    parts.push(simplifyNote(dk.note.split(".")[0] + "."));
  }

  if (karaka.note && !karaka.note.includes("unavailable")) {
    const role =
      p.gender === "male"
        ? "Wife-sign Venus"
        : p.gender === "female"
          ? "Husband-sign Jupiter"
          : karaka.role;
    if (karaka.strength === "strong") {
      parts.push(`${role} is well placed — spouse-related promise is supportive.`);
    } else if (karaka.strength === "weak") {
      parts.push(`${role} is under pressure — spouse theme needs conscious nurture.`);
    }
  }

  return parts.length ? parts.slice(0, 2).join(" ") : null;
}

function longTermLine(p: MarriagePartnerBasics): string | null {
  if (!p.d9.available) return null;
  return D9_PLAIN[p.d9.band] ?? `Inner marriage tone: ${p.d9.band.toLowerCase()}.`;
}

function manglikLine(p: MarriagePartnerBasics): string | null {
  const m = p.manglik;
  if (!m?.has_dosh) return null;
  if (m.note) return simplifyNote(m.note);
  if (m.effective === "active") return "Mangal dosh is active — fiery temper or timing delays; match with partner matters.";
  if (m.effective === "reduced") return "Mangal dosh is present but partly reduced — still check partner chart balance.";
  return null;
}

function timingLine(p: MarriagePartnerBasics): string | null {
  const d = p.dasha_timeline;
  if (!d?.available) return null;
  if (d.why_now_hint) return simplifyNote(d.why_now_hint);
  const cur = d.current?.note;
  if (cur) return simplifyNote(cur);
  const stress = d.stress_windows?.[0]?.note;
  if (stress) return simplifyNote(stress);
  const repair = d.reconnection_windows?.[0]?.note;
  if (repair) return simplifyNote(repair);
  return null;
}

function uniqueNonEmpty(items: string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const item of items) {
    const t = item.trim();
    if (!t || seen.has(t)) continue;
    seen.add(t);
    out.push(t);
  }
  return out;
}

export function buildPartnerPlainView(person: MarriagePartnerBasics): PartnerPlainView {
  const apiStrengths = (person.strengths ?? []).map(simplifyNote);
  const apiPressures = (person.pressures ?? []).map(simplifyNote);

  const positives = uniqueNonEmpty([
    ...apiStrengths,
    ...(person.readiness_band !== "Strained" ? [marriageZoneLine(person)] : []),
    ...(person.d1.seventh_lord_strength === "strong" ? [marriageRulerLine(person) ?? ""] : []),
    ...(person.kp.verdict === "STRONG" ? ["Precision marriage promise is strong — commitment can solidify well."] : []),
    ...(person.upapada.stability === "stable" ? ["Marriage manifest point looks stable — wedding can translate into real life steadily."] : []),
  ]).slice(0, 3);

  const watchouts = uniqueNonEmpty([
    ...apiPressures,
    ...(person.readiness_band === "Strained" ? [marriageZoneLine(person)] : []),
    ...(person.d1.seventh_lord_strength === "weak" ? [marriageRulerLine(person) ?? ""] : []),
    ...(person.gender_flags ?? []).map(flagToPlain),
    ...(person.kp.verdict === "WEAK" ? ["Marriage promise layer is weak — commitment may need extra time."] : []),
    ...(person.upapada.stability === "strained" ? ["Marriage manifest point shows strain — pace wedding decisions realistically."] : []),
  ]).slice(0, 3);

  return {
    bandLabel: BAND_LABEL[person.readiness_band],
    headline: BAND_HEADLINE[person.readiness_band],
    positives: positives.length ? positives : ["No major supportive flag missing — nurture trust daily."],
    watchouts: watchouts.length ? watchouts : ["No major red flag — still talk openly before big decisions."],
    spouseLine: spouseLine(person),
    longTermLine: longTermLine(person),
    manglikLine: manglikLine(person),
    timingLine: timingLine(person),
  };
}
