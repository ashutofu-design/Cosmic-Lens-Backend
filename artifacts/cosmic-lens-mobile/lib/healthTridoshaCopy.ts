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
      "D1 prakriti · D9 immunity · KP 6th CSL",
      "D1 prakriti · D9 immunity · KP 6th CSL",
      "D1 प्रकृति · D9 रोग प्रतिरोध · KP 6वें भाव CSL",
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
      Elevated: p(L, "Elevated", "Elevated", "अधिक"),
    } as Record<string, string>,
    careTitle: p(L, "Daily care tip", "Daily care tip", "दैनिक देखभाल"),
  };
}
