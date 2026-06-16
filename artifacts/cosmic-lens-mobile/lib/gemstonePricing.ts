import type { GemstoneCatalogKey } from "@/lib/gemstoneCatalog";



/** Per-ratti pricing — update MRP & discounts here when you set new prices. */

export type GemstoneRattiPricing = {

  ratti: number;

  sku: string;

  mrpInr: number;

  selfDiscountInr: number;

  referralBuyerDiscountInr: number;

  referrerRewardInr: number;

  inStock: boolean;

};



export const CEYLON_PUKHRAJ_RATTI: GemstoneRattiPricing[] = [

  {

    ratti: 5,

    sku: "ceylon_pukhraj_5ratti",

    mrpInr: 47_999,

    selfDiscountInr: 2_000,

    referralBuyerDiscountInr: 1_000,

    referrerRewardInr: 2_500,

    inStock: true,

  },

  {

    ratti: 6,

    sku: "ceylon_pukhraj_6ratti",

    mrpInr: 58_000,

    selfDiscountInr: 2_500,

    referralBuyerDiscountInr: 1_500,

    referrerRewardInr: 3_000,

    inStock: true,

  },

  {

    ratti: 7,

    sku: "ceylon_pukhraj_7ratti",

    mrpInr: 86_000,

    selfDiscountInr: 3_000,

    referralBuyerDiscountInr: 2_000,

    referrerRewardInr: 3_500,

    inStock: true,

  },

  {

    ratti: 8,

    sku: "ceylon_pukhraj_8ratti",

    mrpInr: 98_000,

    selfDiscountInr: 3_500,

    referralBuyerDiscountInr: 2_500,

    referrerRewardInr: 4_000,

    inStock: true,

  },

  {

    ratti: 9,

    sku: "ceylon_pukhraj_9ratti",

    mrpInr: 110_000,

    selfDiscountInr: 4_000,

    referralBuyerDiscountInr: 3_000,

    referrerRewardInr: 4_500,

    inStock: true,

  },

  {

    ratti: 10,

    sku: "ceylon_pukhraj_10ratti",

    mrpInr: 123_000,

    selfDiscountInr: 4_500,

    referralBuyerDiscountInr: 3_500,

    referrerRewardInr: 5_000,

    inStock: true,

  },

];



export const CEYLON_PUKHRAJ_PRODUCT = {

  catalogId: "yellowsapphire" as GemstoneCatalogKey,

  label: "Ceylon Pukhraj (Yellow Sapphire)",

  subtitle: "Natural Ceylon · 5–10 Ratti · Certified",

};



export type GemstoneShopSku = {

  sku: string;

  catalogId: GemstoneCatalogKey;

  label: string;

  subtitle: string;

  mrpInr: number;

  inStock: boolean;

  ratti: number;

  selfDiscountInr: number;

  referralBuyerDiscountInr: number;

  referrerRewardInr: number;

};



export const GEMSTONE_SHOP: GemstoneShopSku[] = CEYLON_PUKHRAJ_RATTI.map(row => ({

  sku: row.sku,

  catalogId: CEYLON_PUKHRAJ_PRODUCT.catalogId,

  label: CEYLON_PUKHRAJ_PRODUCT.label,

  subtitle: `Natural Ceylon · ${row.ratti} Ratti · Certified`,

  mrpInr: row.mrpInr,

  inStock: row.inStock,

  ratti: row.ratti,

  selfDiscountInr: row.selfDiscountInr,

  referralBuyerDiscountInr: row.referralBuyerDiscountInr,

  referrerRewardInr: row.referrerRewardInr,

}));



export function getGemstoneSkuPricing(sku: string): GemstoneRattiPricing | undefined {

  return CEYLON_PUKHRAJ_RATTI.find(r => r.sku === sku);

}



export function getDefaultGemstoneSku(): string {

  return CEYLON_PUKHRAJ_RATTI.find(r => r.ratti === 6)?.sku

    ?? CEYLON_PUKHRAJ_RATTI[0]?.sku

    ?? "ceylon_pukhraj_6ratti";

}



export function selfPriceFor(row: GemstoneRattiPricing): number {

  return row.mrpInr - row.selfDiscountInr;

}



export function referralPriceFor(row: GemstoneRattiPricing): number {

  return row.mrpInr - row.referralBuyerDiscountInr;

}



export function lowestSelfPriceInr(): number {

  return Math.min(...CEYLON_PUKHRAJ_RATTI.filter(r => r.inStock).map(selfPriceFor));

}



export function formatInr(amount: number): string {

  return `₹${amount.toLocaleString("en-IN")}`;

}



export function referralCodeForUserId(userId: number): string {

  return `CL${userId}`;

}



export function normalizeReferralCode(raw: string): string {

  return raw.trim().toUpperCase();

}



export function isSelfReferral(buyerUserId: number, code: string): boolean {

  const norm = normalizeReferralCode(code);

  return norm === referralCodeForUserId(buyerUserId);

}


