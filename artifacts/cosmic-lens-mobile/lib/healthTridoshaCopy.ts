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
    forYouTitle: p(L, "For you", "Aapke liye", "आपके लिए"),
    riskyOrgansTitle: p(L, "Sensitive Body Areas", "Sensitive body zones", "संवेदनशील अंग"),
    riskyOrgansSub: p(
      L,
      "Areas that may need extra care from your chart",
      "Chart se zyada dhyan dene wale zones",
      "कुंडली से अधिक देखभाल वाले अंग",
    ),
    riskyOrgansEmpty: p(
      L,
      "No major sensitive zone flagged — routine seasonal care is enough.",
      "Koi bada sensitive zone nahi — regular care kaafi hai.",
      "कोई बड़ा संवेदनशील अंग नहीं — नियमित देखभाल पर्याप्त।",
    ),
    dominantRemedy: {
      vata: p(
        L,
        "Warm, oily meals and steady sleep — ease cold, dry food and late nights.",
        "Garam, tel wala khana aur fixed sleep rakho — thanda-sukha khana aur late nights kam karo.",
        "गर्म, तैलीय भोजन और नियमित नींद रखें — ठंडा-सूखा भोजन और देर रात कम करें।",
      ),
      pitta: p(
        L,
        "Cool, light meals — less spice, anger, and sun; stay well hydrated.",
        "Thanda, halka khana — masala, gussa aur dhoop kam; paani zyada piyo.",
        "ठंडा, हल्का भोजन — मसाला, क्रोध और धूप कम; पानी अधिक पिएं।",
      ),
      kapha: p(
        L,
        "Morning walk and light warm meals — cut sweets, dairy, and heavy fried food.",
        "Subah walk + halka garam khana — mithai, dairy aur bhari fried cheez kam.",
        "सुबह टहलें + हल्का गर्म भोजन — मिठाई, दूध और तला हुआ कम करें।",
      ),
    } as Record<DoshaKey, string>,
  };
}
