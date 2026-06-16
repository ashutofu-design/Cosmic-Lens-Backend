import { MILAN_KOOT_DISPLAY, type MilanKootKey } from "@/lib/milanKootDisplay";

export interface MilanKootItem {
  score: number;
  max: number;
  label: string;
  detail: string;
  bad: boolean;
}

type KootKey = MilanKootKey;

export interface MilanBasicResult {
  nadi: MilanKootItem;
  gana: MilanKootItem;
  bhakut: MilanKootItem;
  maitri: MilanKootItem;
  yoni: MilanKootItem;
  tara: MilanKootItem;
  vasya: MilanKootItem;
  varna: MilanKootItem;
  total: number;
  manglik: boolean;
}

export type CompatibilityGrade = {
  label: "Excellent" | "Strong" | "Average" | "Challenging";
  col: string;
};

export type KootRow = {
  key: string;
  label: string;
  classicalLabel: string;
  score: number;
  max: number;
  detail: string;
  bad: boolean;
  col: string;
  emoji: string;
  tagline: string;
};

export type MilanBasicReport = {
  grade: CompatibilityGrade;
  verdict: string;
  topStrength: string;
  biggestChallenge: string;
  astrologerNote: string;
  kootRows: KootRow[];
};

type BackendAnalysis = {
  compatibility_insight?: string;
  strengths?: string[];
  challenges?: string[];
  marriage_outlook?: string;
} | null;

function kootPct(item: MilanKootItem): number {
  return item.max > 0 ? item.score / item.max : 0;
}

export function gradeForTotal(total: number): CompatibilityGrade {
  if (total >= 32) return { label: "Excellent", col: "#22c55e" };
  if (total >= 27) return { label: "Strong", col: "#4ade80" };
  if (total >= 21) return { label: "Average", col: "#fbbf24" };
  return { label: "Challenging", col: "#ef4444" };
}

function verdictFor(r: MilanBasicResult): string {
  const commWeak = r.maitri.bad || kootPct(r.maitri) < 0.6;
  const familyWeak = r.bhakut.bad || kootPct(r.bhakut) < 0.5;
  const nadiWeak = r.nadi.bad;

  if (r.total >= 32) {
    return "This match reads strong on the classical sheet. Day-to-day marriage will still ask for patience around money talk and family load, but the foundation supports a lasting bond.";
  }
  if (r.total >= 27) {
    if (commWeak) {
      return "This match shows strong long-term potential but requires conscious communication to avoid misunderstandings.";
    }
    if (familyWeak) {
      return "The charts support a workable marriage, though family expectations and home-life rhythm will need honest alignment early on.";
    }
    return "A solid classical match — ordinary friction will appear, yet the overall pattern favours a stable partnership with mutual effort.";
  }
  if (r.total >= 21) {
    if (r.manglik) {
      return "The bond is workable on paper, but a Manglik imbalance and weaker koots mean remedies and plain conversation before marriage are worth taking seriously.";
    }
    if (commWeak) {
      return "Average compatibility with a clear communication gap — the marriage can hold if both sides name friction early instead of waiting for it to repeat.";
    }
    return "An average classical read — not a rejection, but a match where habits, timing, and family pressure will shape the outcome more than chemistry alone.";
  }
  if (nadiWeak || r.manglik) {
    return "The charts flag serious classical concerns — not impossible, but this match deserves a full Jyotish read and remedy planning before any commitment.";
  }
  return "A challenging score on the traditional scale — attraction may be real, yet long-term stability will need deliberate work and professional guidance.";
}

function pickTopStrength(r: MilanBasicResult, backend: BackendAnalysis): string {
  if (backend?.strengths?.[0]) return backend.strengths[0];

  const ranked = (["maitri", "gana", "yoni", "bhakut", "nadi", "tara", "vasya", "varna"] as KootKey[])
    .map(key => ({ key, pct: kootPct(r[key]), bad: r[key].bad }))
    .filter(x => !x.bad && x.pct >= 0.5)
    .sort((a, b) => b.pct - a.pct);

  const best = ranked[0]?.key;
  if (best === "maitri") {
    return "Your Emotional Bond runs warm — Moon-sign lords sit friendly, so you tend to read each other's mood faster than most couples on paper.";
  }
  if (best === "gana") {
    return `Personality Energy aligns (${r.gana.detail}) — temperaments after a long day annoy less, and apologies tend to land sooner.`;
  }
  if (best === "yoni") {
    return "Intimacy Match scores well — physical pull and day-to-day closeness develop without constant guesswork about pace.";
  }
  if (best === "bhakut") {
    return "Life Alignment is clear — Moon rashi spacing supports family welfare and eases the home-money loops this dimension flags when weak.";
  }
  if (best === "nadi") {
    return "Soul Sync differs between you — classical texts read this as healthier constitutional balance for stamina over the years.";
  }
  if (best === "tara") {
    return "Destiny Link is full — relocations, job shifts, and parents' health seasons land with less blind-side shock on your timeline.";
  }
  if (best === "vasya") {
    return "Attraction Power is strong — who leads small decisions and who follows settles without a long power struggle in ordinary weeks.";
  }
  if (best === "varna") {
    return "Spiritual Harmony matches — work and dharma energy flows without one partner constantly feeling 'behind' the other.";
  }
  return "No single koot dominates the win column, but shared respect and how you repair after friction will define what the sheet cannot score.";
}

function pickBiggestChallenge(r: MilanBasicResult, backend: BackendAnalysis): string {
  if (backend?.challenges?.[0]) return backend.challenges[0];

  if (r.manglik) {
    return "Only one partner reads Manglik on the chart — classical marriage texts treat this as a defining imbalance. Kumbh Vivah or Mangal Shanti before shaadi is the traditional mitigation families still book.";
  }

  const ranked = (["nadi", "gana", "bhakut", "maitri", "yoni", "tara", "vasya", "varna"] as KootKey[])
    .map(key => ({ key, pct: kootPct(r[key]), bad: r[key].bad }))
    .filter(x => x.bad || x.pct < 0.55)
    .sort((a, b) => {
      if (a.bad !== b.bad) return a.bad ? -1 : 1;
      return a.pct - b.pct;
    });

  const worst = ranked[0]?.key;
  if (worst === "nadi") {
    return `Soul Sync carries Nadi dosha — both share the same nadi (${r.nadi.detail}). Tradition links this to health load; families often discuss Maha Mrityunjaya Jaap before finalising.`;
  }
  if (worst === "gana") {
    return `Personality Energy clashes (${r.gana.detail}) — the same fight can mean opposite things to each of you. Who returns to the room first becomes real marriage work.`;
  }
  if (worst === "bhakut") {
    return "Life Alignment shows Bhakut dosha — money, in-laws, and household roles stay tense until expectations are spoken plainly.";
  }
  if (worst === "maitri") {
    return "Emotional Bond runs thin — Moon-sign lords sit cool. You can both be sincere and still hear the same sentence as an attack after a tiring day.";
  }
  if (worst === "yoni") {
    return "Intimacy Match is hostile — instinctive pace of touch and irritation mismatch. Small slights after work stack unless the first ten minutes home are handled with care.";
  }
  if (worst === "tara") {
    return "Destiny Link scores low — big life moves may feel mistimed. When you marry and how you plan transitions matters more than chemistry alone.";
  }
  return "No headline dosha stacks on the sheet, but low-scoring koots are usually where the same argument shape borrows its fuel in a long marriage.";
}

function buildAstrologerNote(
  r: MilanBasicResult,
  grade: CompatibilityGrade,
  backend: BackendAnalysis,
  p1Name?: string,
  p2Name?: string,
): string {
  const pct = Math.round((r.total / 36) * 100);
  const names = p1Name && p2Name ? `${p1Name} and ${p2Name}` : "This couple";
  const badKoots = MILAN_KOOT_DISPLAY.filter(d => r[d.key].bad).map(d => d.modernTitle);
  const strongKoots = MILAN_KOOT_DISPLAY.filter(d => kootPct(r[d.key]) >= 0.75 && !r[d.key].bad).map(d => d.modernTitle);

  if (backend?.compatibility_insight && backend.compatibility_insight.length > 80) {
    const insight = backend.compatibility_insight.trim();
    const outlook = backend.marriage_outlook?.trim();
    if (outlook && insight.length < 90) {
      const combined = `${insight} ${outlook}`;
      if (combined.length >= 80 && combined.length <= 130) return combined;
    }
    if (insight.length >= 80 && insight.length <= 130) return insight;
  }

  const parts: string[] = [];
  parts.push(
    `${names} score ${r.total} of 36 Gun Milan (${pct}%) — a ${grade.label.toLowerCase()} read on the classical scale.`,
  );

  if (strongKoots.length > 0) {
    parts.push(`${strongKoots.slice(0, 2).join(" and ")} support the bond.`);
  }

  if (badKoots.length > 0) {
    parts.push(`${badKoots.slice(0, 2).join(" and ")} need attention before vows.`);
  } else if (r.manglik) {
    parts.push("Manglik imbalance is the main flag families discuss with a pandit.");
  } else {
    parts.push("No major dosha headline, yet mid-band koots still shape daily friction.");
  }

  if (r.total >= 27) {
    parts.push("Marriage can work well with ordinary patience around money, in-laws, and tone after stress.");
  } else if (r.total >= 21) {
    parts.push("Shaadi is not ruled out, but remedies and honest pre-marriage talks carry more weight here.");
  } else {
    parts.push("A full chart read with dasha timing and remedies is advisable before commitment.");
  }

  let note = parts.join(" ");
  if (note.length > 120) {
    note = note.slice(0, 117).trimEnd() + "...";
  }
  while (note.length < 80 && backend?.marriage_outlook) {
    const extra = backend.marriage_outlook.slice(0, 120 - note.length - 1).trim();
    if (!extra) break;
    note = `${note} ${extra}`;
    if (note.length > 120) note = note.slice(0, 117).trimEnd() + "...";
  }
  return note;
}

export function buildMilanBasicReport(
  r: MilanBasicResult,
  backend?: BackendAnalysis,
  names?: { p1?: string; p2?: string },
): MilanBasicReport {
  const grade = gradeForTotal(r.total);
  const kootRows: KootRow[] = MILAN_KOOT_DISPLAY.map(def => ({
    key: def.key,
    label: def.modernTitle,
    classicalLabel: def.classicalLabel,
    score: r[def.key].score,
    max: r[def.key].max,
    detail: r[def.key].detail,
    bad: r[def.key].bad,
    col: def.color,
    emoji: def.emoji,
    tagline: def.tagline,
  }));

  return {
    grade,
    verdict: verdictFor(r),
    topStrength: pickTopStrength(r, backend ?? null),
    biggestChallenge: pickBiggestChallenge(r, backend ?? null),
    astrologerNote: buildAstrologerNote(r, grade, backend ?? null, names?.p1, names?.p2),
    kootRows,
  };
}

/** @deprecated Use buildMilanBasicReport */
export function buildMilanTrailerInsights(r: MilanBasicResult) {
  const report = buildMilanBasicReport(r);
  return {
    strengthBadge: { label: report.grade.label, col: report.grade.col, emoji: "✦" },
    snapshotVerdict: report.verdict,
    topStrengthTeaser: report.topStrength,
    biggestChallengeTeaser: report.biggestChallenge,
    futureSignalTeaser: "",
    attractionTeaser: "",
    hiddenFactors: [],
    hiddenFactorIntro: "",
    showHiddenFactors: false,
  };
}
