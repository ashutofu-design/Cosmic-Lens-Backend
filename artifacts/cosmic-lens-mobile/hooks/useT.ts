import { useUser } from "@/context/UserContext";
import { getT } from "@/lib/i18n";
import { getTE } from "@/lib/i18nExtended";
import { getTM } from "@/lib/i18nMore";
import { getTV } from "@/lib/i18nVastu";

export type T = ReturnType<typeof getT> & ReturnType<typeof getTE>
              & ReturnType<typeof getTM> & ReturnType<typeof getTV>;

export function useT(): T {
  const { language } = useUser();
  return {
    ...getT(language),
    ...getTE(language),
    ...getTM(language),
    ...getTV(language),
  } as T;
}
