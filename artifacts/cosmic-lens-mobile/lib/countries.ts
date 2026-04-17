export type Country = {
  code: string;
  name: string;
  dial: string;
  flag: string;
  minLen: number;
  maxLen: number;
};

export const COUNTRIES: Country[] = [
  { code: "IN", name: "India",          dial: "91",  flag: "🇮🇳", minLen: 10, maxLen: 10 },
  { code: "US", name: "United States",  dial: "1",   flag: "🇺🇸", minLen: 10, maxLen: 10 },
  { code: "CA", name: "Canada",         dial: "1",   flag: "🇨🇦", minLen: 10, maxLen: 10 },
  { code: "GB", name: "United Kingdom", dial: "44",  flag: "🇬🇧", minLen: 10, maxLen: 10 },
  { code: "AE", name: "UAE",            dial: "971", flag: "🇦🇪", minLen: 9,  maxLen: 9  },
  { code: "AU", name: "Australia",      dial: "61",  flag: "🇦🇺", minLen: 9,  maxLen: 9  },
  { code: "SG", name: "Singapore",      dial: "65",  flag: "🇸🇬", minLen: 8,  maxLen: 8  },
  { code: "MY", name: "Malaysia",       dial: "60",  flag: "🇲🇾", minLen: 9,  maxLen: 10 },
  { code: "NZ", name: "New Zealand",    dial: "64",  flag: "🇳🇿", minLen: 8,  maxLen: 10 },
  { code: "NP", name: "Nepal",          dial: "977", flag: "🇳🇵", minLen: 10, maxLen: 10 },
  { code: "BD", name: "Bangladesh",     dial: "880", flag: "🇧🇩", minLen: 10, maxLen: 10 },
  { code: "LK", name: "Sri Lanka",      dial: "94",  flag: "🇱🇰", minLen: 9,  maxLen: 9  },
  { code: "PK", name: "Pakistan",       dial: "92",  flag: "🇵🇰", minLen: 10, maxLen: 10 },
  { code: "SA", name: "Saudi Arabia",   dial: "966", flag: "🇸🇦", minLen: 9,  maxLen: 9  },
  { code: "QA", name: "Qatar",          dial: "974", flag: "🇶🇦", minLen: 8,  maxLen: 8  },
  { code: "KW", name: "Kuwait",         dial: "965", flag: "🇰🇼", minLen: 8,  maxLen: 8  },
  { code: "OM", name: "Oman",           dial: "968", flag: "🇴🇲", minLen: 8,  maxLen: 8  },
  { code: "BH", name: "Bahrain",        dial: "973", flag: "🇧🇭", minLen: 8,  maxLen: 8  },
  { code: "DE", name: "Germany",        dial: "49",  flag: "🇩🇪", minLen: 10, maxLen: 11 },
  { code: "FR", name: "France",         dial: "33",  flag: "🇫🇷", minLen: 9,  maxLen: 9  },
  { code: "IT", name: "Italy",          dial: "39",  flag: "🇮🇹", minLen: 9,  maxLen: 10 },
  { code: "ES", name: "Spain",          dial: "34",  flag: "🇪🇸", minLen: 9,  maxLen: 9  },
  { code: "NL", name: "Netherlands",    dial: "31",  flag: "🇳🇱", minLen: 9,  maxLen: 9  },
  { code: "SE", name: "Sweden",         dial: "46",  flag: "🇸🇪", minLen: 9,  maxLen: 9  },
  { code: "CH", name: "Switzerland",    dial: "41",  flag: "🇨🇭", minLen: 9,  maxLen: 9  },
  { code: "IE", name: "Ireland",        dial: "353", flag: "🇮🇪", minLen: 9,  maxLen: 9  },
  { code: "ZA", name: "South Africa",   dial: "27",  flag: "🇿🇦", minLen: 9,  maxLen: 9  },
  { code: "NG", name: "Nigeria",        dial: "234", flag: "🇳🇬", minLen: 10, maxLen: 10 },
  { code: "KE", name: "Kenya",          dial: "254", flag: "🇰🇪", minLen: 9,  maxLen: 9  },
  { code: "EG", name: "Egypt",          dial: "20",  flag: "🇪🇬", minLen: 10, maxLen: 10 },
  { code: "BR", name: "Brazil",         dial: "55",  flag: "🇧🇷", minLen: 10, maxLen: 11 },
  { code: "MX", name: "Mexico",         dial: "52",  flag: "🇲🇽", minLen: 10, maxLen: 10 },
  { code: "AR", name: "Argentina",      dial: "54",  flag: "🇦🇷", minLen: 10, maxLen: 11 },
  { code: "CN", name: "China",          dial: "86",  flag: "🇨🇳", minLen: 11, maxLen: 11 },
  { code: "JP", name: "Japan",          dial: "81",  flag: "🇯🇵", minLen: 10, maxLen: 11 },
  { code: "KR", name: "South Korea",    dial: "82",  flag: "🇰🇷", minLen: 9,  maxLen: 11 },
  { code: "TH", name: "Thailand",       dial: "66",  flag: "🇹🇭", minLen: 9,  maxLen: 9  },
  { code: "ID", name: "Indonesia",      dial: "62",  flag: "🇮🇩", minLen: 9,  maxLen: 12 },
  { code: "PH", name: "Philippines",    dial: "63",  flag: "🇵🇭", minLen: 10, maxLen: 10 },
  { code: "VN", name: "Vietnam",        dial: "84",  flag: "🇻🇳", minLen: 9,  maxLen: 10 },
  { code: "TR", name: "Turkey",         dial: "90",  flag: "🇹🇷", minLen: 10, maxLen: 10 },
  { code: "RU", name: "Russia",         dial: "7",   flag: "🇷🇺", minLen: 10, maxLen: 10 },
];

export const DEFAULT_COUNTRY: Country =
  COUNTRIES.find(c => c.code === "IN") ?? COUNTRIES[0];

export function findCountryByDial(dial: string): Country | undefined {
  return COUNTRIES.find(c => c.dial === dial);
}
