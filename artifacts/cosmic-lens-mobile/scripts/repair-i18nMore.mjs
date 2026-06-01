import fs from "node:fs";
import path from "node:path";

const p = path.resolve("lib/i18nMore.ts");
let src = fs.readFileSync(p, "utf8");
const cut = src.indexOf("\nconst AR: Partial<MoreT> = {");
if (cut === -1) {
  console.error("AR block marker not found");
  process.exit(1);
}
src = src.slice(0, cut);
src += `

/**
 * Get the additional translation table for a language.
 */
export function getTM(lang) {
  switch (lang) {
    case "hn": return { ...EN, ...HN };
    case "hi": return { ...EN, ...HI };
    case "bn": return { ...EN, ...BN };
    case "mr": return { ...EN, ...MR };
    case "ta": return { ...EN, ...TA };
    case "te": return { ...EN, ...TE };
    case "gu": return { ...EN, ...GU };
    case "kn": return { ...EN, ...KN };
    case "ml": return { ...EN, ...ML };
    case "pa": return { ...EN, ...PA };
    case "or": return { ...EN, ...OR };
    case "as": return { ...EN, ...AS };
    case "zh": return { ...EN, ...ZH };
    case "es": return { ...EN, ...ES };
    default:   return EN;
  }
}
`;
fs.writeFileSync(p, src, "utf8");
console.log("repaired", p, "lines", src.split("\n").length);
