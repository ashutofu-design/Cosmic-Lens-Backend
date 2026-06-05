import { useUser } from "@/context/UserContext";
import { coerceUILang, getT, type UILang } from "@/lib/i18n";
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
  const lang = coerceUILang(language);
  return {
    ...getT(lang),
    ...getTE(lang),
    ...getTM(lang),
    ...getTV(lang),
    lang,
    vlang: vedicLang(lang),
  } as T;
}
