import { coerceUILang, type UILang } from "@/lib/i18n";
import { pickLoveBasicCopy } from "@/lib/loveRealityBasicLang";

function p(lang: UILang, en: string, hn: string, hi: string): string {
  return pickLoveBasicCopy(lang, en, hn, hi);
}

export type DoshaKey = "vata" | "pitta" | "kapha";

export function healthTridoshaCopy(lang: UILang) {
  const L = coerceUILang(lang);
  return {
    sectionTitle: p(L, "Tridosha Balance", "Tridosha Balance", "त्रिदोष संतुलन"),
    sectionSub: p(
      L,
      "Vata · Pitta · Kapha from your birth chart",
      "Chart se Vata · Pitta · Kapha",
      "जन्म कुंडली से वात · पित्त · कफ",
    ),
    labels: {
      vata: p(L, "Vata (Baat)", "Vata (Baat)", "वात (बात)"),
      pitta: p(L, "Pitta", "Pitta", "पित्त"),
      kapha: p(L, "Kapha (Cough)", "Kapha (Cough)", "कफ (कफ)"),
    } as Record<DoshaKey, string>,
    dominant: (name: string) =>
      p(L, `${name} dominant`, `${name} dominant`, `${name} प्रमुख`),
    states: {
      Balanced: p(L, "Balanced", "Balanced", "संतुलित"),
      Afflicted: p(L, "Afflicted", "Afflicted", "प्रभावित"),
      "Highly Critical": p(L, "Elevated", "Elevated", "अधिक"),
    } as Record<string, string>,
    careTitle: p(L, "Daily care tip", "Daily care tip", "दैनिक देखभाल"),
  };
}
