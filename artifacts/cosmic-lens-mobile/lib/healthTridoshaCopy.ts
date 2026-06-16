import { coerceUILang, type UILang } from "@/lib/i18n";
import { pickLoveBasicCopy } from "@/lib/loveRealityBasicLang";

function p(lang: UILang, en: string, hn: string, hi: string): string {
  return pickLoveBasicCopy(lang, en, hn, hi);
}

export type DoshaKey = "vata" | "pitta" | "kapha";
export type OrganZoneId =
  | "digestion"
  | "respiratory"
  | "joints_nerves"
  | "heart_circulation"
  | "mind_sleep"
  | "metabolism";
export type OrganZoneStatus = "high" | "moderate" | "stable";

export function healthTridoshaCopy(lang: UILang) {
  const L = coerceUILang(lang);
  return {
    sectionTitle: p(L, "Tridosha Balance", "Tridosha Balance", "त्रिदोष संतुलन"),
    labels: {
      vata: p(L, "Vata", "Vata", "वात"),
      pitta: p(L, "Pitta", "Pitta", "पित्त"),
      kapha: p(L, "Kapha", "Kapha", "कफ"),
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
    organHeatmapTitle: p(L, "Priority Body Zones", "Priority body zones", "प्राथमिकता वाले क्षेत्र"),
    organHeatmapSub: p(
      L,
      "Top 3 zones from your chart that need the most seasonal care.",
      "Chart ke top 3 zones jin par sabse zyada dhyan dena chahiye.",
      "कुंडली के वे 3 क्षेत्र जिन पर सबसे अधिक देखभाल चाहिए।",
    ),
    zoneLabels: {
      digestion: p(L, "Stomach & Digestion", "Pet aur digestion", "पेट और पाचन"),
      respiratory: p(L, "Lungs & Throat", "Saans aur gala", "फेफड़े और गला"),
      joints_nerves: p(L, "Joints & Nerves", "Joints aur nerves", "जोड़ और नसें"),
      heart_circulation: p(L, "Heart & Circulation", "Dil aur blood flow", "हृदय और रक्त प्रवाह"),
      mind_sleep: p(L, "Mind & Sleep", "Mann aur neend", "मन और नींद"),
      metabolism: p(L, "Metabolism & Liver", "Metabolism aur liver", "चयापचय और लीवर"),
    } as Record<OrganZoneId, string>,
    statusLabels: {
      high: p(L, "High sensitivity", "Zyada sensitivity", "अधिक संवेदनशील"),
      moderate: p(L, "Moderate", "Medium", "मध्यम"),
      stable: p(L, "Stable", "Stable", "स्थिर"),
    } as Record<OrganZoneStatus, string>,
    stableZonesNote: (count: number) =>
      count === 1
        ? p(
            L,
            "1 other zone is stable — routine care is enough.",
            "1 aur zone stable hai — regular care kaafi hai.",
            "1 और क्षेत्र स्थिर है — नियमित देखभाल पर्याप्त।",
          )
        : p(
            L,
            `${count} other zones are stable — routine care is enough.`,
            `${count} aur zones stable hain — regular care kaafi hai.`,
            `${count} और क्षेत्र स्थिर हैं — नियमित देखभाल पर्याप्त।`,
          ),
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
