import type { Feather } from "@expo/vector-icons";
import type React from "react";

export type SpecRow = { label: string; value: string };
export type WearStep = { icon: React.ComponentProps<typeof Feather>["name"]; title: string; highlight?: string };
export type CareTip = { icon: React.ComponentProps<typeof Feather>["name"]; text: string };

export const PUKHRAJ_TRUST_BADGES = [
  { icon: "award" as const, label: "Lab Certified" },
  { icon: "shield" as const, label: "Natural & Untreated" },
  { icon: "globe" as const, label: "Ceylon Origin" },
  { icon: "truck" as const, label: "Insured Delivery" },
];

export const PUKHRAJ_SPECS: SpecRow[] = [
  { label: "Origin", value: "Sri Lanka (Ceylon)" },
  { label: "Planet", value: "Jupiter (Guru)" },
  { label: "Colour", value: "Yellow to golden-yellow" },
  { label: "Shape", value: "Octagonal / Cushion / Oval" },
  { label: "Cut", value: "Faceted" },
  { label: "Composition", value: "Natural" },
  { label: "Treatment", value: "Unheated & untreated" },
  { label: "Certificate", value: "Government / lab report included" },
];

export const PUKHRAJ_WEAR_STEPS: WearStep[] = [
  {
    icon: "droplet",
    title: "Purify in raw milk, honey & Ganga jal before wearing.",
    highlight: "Milk, honey & Ganga jal",
  },
  {
    icon: "music",
    title: "Chant ॐ ग्रां ग्रीं ग्रौं सः गुरुवे नमः — 108 times.",
    highlight: "108 times",
  },
  {
    icon: "clock",
    title: "Wear on Thursday morning, 5–7 AM (Shukla Paksha).",
    highlight: "Thursday · 5–7 AM",
  },
  {
    icon: "hand",
    title: "Set in gold on the index finger of the right hand.",
    highlight: "Index finger · right hand",
  },
];

export const PUKHRAJ_CARE_TIPS: CareTip[] = [
  { icon: "wind", text: "After wearing, wipe gently with a soft dry cloth." },
  { icon: "x-circle", text: "Remove before soap, perfume, sanitiser or detergent." },
  { icon: "alert-triangle", text: "Avoid scratches — take off during heavy work or sports." },
  { icon: "sun", text: "Recharge in mild sunlight or moonlight; selenite plate optional." },
];

export const PUKHRAJ_BENEFITS = [
  "Attracts wealth & financial stability",
  "Supports career growth & opportunities",
  "Promotes peace & emotional balance",
  "Strengthens Guru (Jupiter) in the chart",
];

export function gemstoneWhatsAppMessage(ratti: number): string {
  return (
    `Namaste 🙏 Cosmic Lens app se hoon. ` +
    `Ceylon Pukhraj ${ratti} Ratti ke real photos/videos aur certificate share karein. Dhanyavaad.`
  );
}

export const EMERALD_TRUST_BADGES = [
  { icon: "award" as const, label: "Lab Certified" },
  { icon: "shield" as const, label: "Natural & Untreated" },
  { icon: "globe" as const, label: "Zambia Origin" },
  { icon: "truck" as const, label: "Insured Delivery" },
];

export const EMERALD_SPECS: SpecRow[] = [
  { label: "Origin", value: "Zambia" },
  { label: "Planet", value: "Mercury (Budh)" },
  { label: "Colour", value: "Rich green" },
  { label: "Shape", value: "Oval / Cushion / Emerald-cut" },
  { label: "Cut", value: "Faceted" },
  { label: "Composition", value: "Natural" },
  { label: "Treatment", value: "Unheated & untreated" },
  { label: "Certificate", value: "Government / lab report included" },
];

export const EMERALD_WEAR_STEPS: WearStep[] = [
  {
    icon: "droplet",
    title: "Purify in raw milk, honey & Ganga jal before wearing.",
    highlight: "Milk, honey & Ganga jal",
  },
  {
    icon: "music",
    title: "Chant ॐ ब्रां ब्रीं ब्रौं सः बुधाय नमः — 108 times.",
    highlight: "108 times",
  },
  {
    icon: "clock",
    title: "Wear on Wednesday morning, 5–7 AM (Shukla Paksha).",
    highlight: "Wednesday · 5–7 AM",
  },
  {
    icon: "hand",
    title: "Set in gold or silver on the little finger of the right hand.",
    highlight: "Little finger · right hand",
  },
];

export const EMERALD_CARE_TIPS: CareTip[] = PUKHRAJ_CARE_TIPS;

export const EMERALD_BENEFITS = [
  "Sharpens intellect & communication",
  "Supports business, trade & finance",
  "Calms anxiety & overthinking",
  "Strengthens Budh (Mercury) in the chart",
];
