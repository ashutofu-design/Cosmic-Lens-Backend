#!/usr/bin/env python3
"""Trim Cosmic Lens i18n files to en / hn / hi only."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOBILE_LIB = ROOT / "artifacts" / "cosmic-lens-mobile" / "lib"


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines(keepends=True)


def write_lines(path: Path, lines: list[str]) -> None:
    path.write_text("".join(lines), encoding="utf-8")


def splice(path: Path, ranges: list[tuple[int, int]]) -> None:
    lines = read_lines(path)
    out: list[str] = []
    for start, end in ranges:
        out.extend(lines[start - 1 : end])
    write_lines(path, out)


def trim_i18n_ts() -> None:
    path = MOBILE_LIB / "i18n.ts"
    lines = read_lines(path)
    header = lines[:12]
    header[2] = "// COSMIC LENS — App-wide UI Translation (English, Hinglish, Hindi only)\n"
    header[6] = 'export type UILang = "en" | "hn" | "hi";\n'
    header[7] = "\n"
    header[8] = 'export const APP_LANG_CODES = ["en", "hn", "hi"] as const;\n'
    header[9] = "/** @deprecated use APP_LANG_CODES */ export const INDIA_LANG_CODES = APP_LANG_CODES;\n"
    header[10] = "/** @deprecated use APP_LANG_CODES */ export const GLOBAL_LANG_CODES = APP_LANG_CODES;\n"
    # Keep en/hn/hi blocks (lines 204-542 in original) + footer from 2896
    body = lines[203:542] + lines[2895:]
    # Fix uiDateLocale map
    for i, line in enumerate(body):
        if line.strip().startswith("const map:"):
            body[i] = "  const map: Partial<Record<UILang, string>> = {\n"
            body[i + 1] = '    hi: "hi-IN", hn: "hi-IN", en: "en-IN",\n'
            # remove old multi-line map until closing };
            j = i + 2
            while j < len(body) and "};" not in body[j]:
                body[j] = ""
                j += 1
            break
    write_lines(path, header + body)


def trim_i18n_extended() -> None:
    splice(MOBILE_LIB / "i18nExtended.ts", [(1, 446), (2297, 99999)])


def trim_i18n_content() -> None:
    path = MOBILE_LIB / "i18nContent.ts"
    lines = read_lines(path)
    head = lines[:3]
    head.append(
        'export type ContentLang = "en" | "hn" | "hi";\n'
    )
    head.append("type Dict = Record<string, string>;\n\n")
    head.append("const DICTS: Record<ContentLang, Dict> = {\n")
    dict_body = lines[7:571]
    if dict_body[-1].strip() == "},":
        dict_body[-1] = "};\n"
    tail = lines[4521:]
    write_lines(path, head + dict_body + ["\n"] + tail)


def trim_i18n_more() -> None:
    path = MOBILE_LIB / "i18nMore.ts"
    lines = read_lines(path)
    kept = lines[:6806]
    footer = (
        "\n/** Get additional strings — English, Hinglish, Hindi only. */\n"
        "export function getTM(lang: UILang): MoreT {\n"
        "  switch (lang) {\n"
        "    case \"hn\": return { ...EN, ...HN };\n"
        "    case \"hi\": return { ...EN, ...HI };\n"
        "    default:   return EN;\n"
        "  }\n"
        "}\n"
    )
    write_lines(path, kept + [footer])


def main() -> None:
    trim_i18n_ts()
    trim_i18n_extended()
    trim_i18n_content()
    trim_i18n_more()
    print("Trimmed i18n files to en/hn/hi.")


if __name__ == "__main__":
    main()
