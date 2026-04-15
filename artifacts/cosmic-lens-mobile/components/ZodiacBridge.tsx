import { useEffect } from "react";

import { useTheme } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { getZodiacAccent, getZodiacSign, DEFAULT_ACCENT } from "@/lib/zodiac";

/**
 * ZodiacBridge — zero-UI component.
 * Reads the primary profile's birth date from UserContext,
 * derives the zodiac sign + accent, and injects it into ThemeContext.
 * Must be rendered inside both ThemeProvider and UserProvider.
 */
export function ZodiacBridge() {
  const { birthData } = useUser();
  const { setZodiacAccent } = useTheme();

  useEffect(() => {
    if (birthData?.day && birthData?.month) {
      const sign   = getZodiacSign(birthData.day, birthData.month);
      const accent = getZodiacAccent(birthData.day, birthData.month);
      setZodiacAccent(sign, accent);
    } else {
      setZodiacAccent(null, DEFAULT_ACCENT);
    }
  }, [birthData?.day, birthData?.month, setZodiacAccent]);

  return null;
}
