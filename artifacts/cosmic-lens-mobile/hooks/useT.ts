import { useUser } from "@/context/UserContext";
import { getT, type UILang } from "@/lib/i18n";
import { getTE } from "@/lib/i18nExtended";
import { getTM } from "@/lib/i18nMore";
import { getTV } from "@/lib/i18nVastu";
import { vedicLang, type VLang } from "@/lib/i18nVedic";

export type T = ReturnType<typeof getT> & ReturnType<typeof getTE>
              & ReturnType<typeof getTM> & ReturnType<typeof getTV>
              & {
                /** Current UI language code (e.g. "en", "hn", "hi") */
                lang: UILang;
                /** Bucketed Vedic vocabulary lang ("en" | "hn" | "hi") */
                vlang: VLang;
              };

export function useT(): T {
  const { language } = useUser();
  return {
    ...getT(language),
    ...getTE(language),
    ...getTM(language),
    ...getTV(language),
    lang: language,
    vlang: vedicLang(language),
  } as T;
}
