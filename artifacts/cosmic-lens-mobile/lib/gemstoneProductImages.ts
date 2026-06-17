import { ImageSourcePropType } from "react-native";

/** Bundled in app — works without API / offline. */
const LOCAL = {
  hero: require("@/assets/gemstones/pukhraj-hero.png"),
  cushion: require("@/assets/gemstones/pukhraj-cushion.png"),
  wear: require("@/assets/gemstones/pukhraj-wear.png"),
  lifestyle: require("@/assets/gemstones/pukhraj-lifestyle.png"),
} as const;

export type GemstoneGalleryItem = {
  id: string;
  source: ImageSourcePropType;
  caption?: string;
};

export const PUKHRAJ_GALLERY: GemstoneGalleryItem[] = [
  { id: "hero", source: LOCAL.hero, caption: "Certified Ceylon Pukhraj" },
  { id: "cushion", source: LOCAL.cushion, caption: "Natural colour & clarity" },
  { id: "wear", source: LOCAL.wear, caption: "How to wear" },
  { id: "lifestyle", source: LOCAL.lifestyle, caption: "Ring & pendant styling" },
];
