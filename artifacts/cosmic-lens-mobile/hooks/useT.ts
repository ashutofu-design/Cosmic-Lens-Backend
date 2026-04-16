import { useUser } from "@/context/UserContext";
import { getT } from "@/lib/i18n";
import { getTE } from "@/lib/i18nExtended";

export type T = ReturnType<typeof getT> & ReturnType<typeof getTE>;

export function useT(): T {
  const { language } = useUser();
  return { ...getT(language), ...getTE(language) } as T;
}
