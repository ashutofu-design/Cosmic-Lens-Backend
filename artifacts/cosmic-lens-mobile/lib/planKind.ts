/** Shared plan-type keys for floor plan upload (home / shop / office / factory). */
export type PlanKind = "home" | "shop" | "office" | "factory";

export type PlanKindLabels = {
  title: string;
  hint: string;
  home: string;
  shop: string;
  office: string;
  factory: string;
};
