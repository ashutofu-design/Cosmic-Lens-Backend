import { ImageSourcePropType } from "react-native";

import { API_BASE } from "@/lib/apiConfig";

function remote(name: string): ImageSourcePropType {
  return { uri: `${API_BASE}/gemstone_media/${name}` };
}

/** Real product photos — served from API / bundled in assets/gemstones after copy script. */
export type GemstoneGalleryItem = {
  id: string;
  source: ImageSourcePropType;
  caption?: string;
};

export const PUKHRAJ_GALLERY: GemstoneGalleryItem[] = [
  { id: "hero", source: remote("pukhraj-hero.png"), caption: "Certified Ceylon Pukhraj" },
  { id: "cushion", source: remote("pukhraj-cushion.png"), caption: "Natural colour & clarity" },
  { id: "wear", source: remote("pukhraj-wear.png"), caption: "How to wear" },
  { id: "lifestyle", source: remote("pukhraj-lifestyle.png"), caption: "Ring & pendant styling" },
];
