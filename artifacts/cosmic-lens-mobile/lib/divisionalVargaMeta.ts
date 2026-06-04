import type { VargaKey } from "@/lib/vargaCompute";

export const D1_CHART_META = {
  key: "D1" as const,
  label: "D1 · Lagna Kundli",
  hint: "Birth chart & life path",
};

export type ChartVargaParam = VargaKey | "D1";

export const DIVISIONAL_VARGAS: { key: VargaKey; label: string; hint: string }[] = [
  { key: "D9", label: "D9 Navamsa", hint: "Marriage & dharma" },
  { key: "D10", label: "D10 Dashamsha", hint: "Career & karma" },
  { key: "D7", label: "D7 Saptamsa", hint: "Children & progeny" },
  { key: "D2", label: "D2 Hora", hint: "Wealth" },
  { key: "D3", label: "D3 Drekkana", hint: "Siblings & courage" },
  { key: "D12", label: "D12 Dwadashamsha", hint: "Parents" },
  { key: "D30", label: "D30 Trimsamsa", hint: "Misfortunes" },
];

const KEYS = new Set(DIVISIONAL_VARGAS.map(v => v.key));

export function parseVargaParam(raw?: string | string[]): VargaKey {
  const s = (Array.isArray(raw) ? raw[0] : raw) || "D9";
  const up = s.toUpperCase() as VargaKey;
  return KEYS.has(up) ? up : "D9";
}

/** Route param for `/varga-chart` — includes D1 birth chart. */
export function parseChartVargaParam(raw?: string | string[]): ChartVargaParam {
  const s = (Array.isArray(raw) ? raw[0] : raw) || "D9";
  const up = s.toUpperCase();
  if (up === "D1") return "D1";
  return parseVargaParam(up);
}

export function chartVargaMeta(key: ChartVargaParam) {
  if (key === "D1") return D1_CHART_META;
  return DIVISIONAL_VARGAS.find(v => v.key === key) ?? DIVISIONAL_VARGAS[0];
}

export function vargaMeta(key: VargaKey) {
  return DIVISIONAL_VARGAS.find(v => v.key === key) ?? DIVISIONAL_VARGAS[0];
}
