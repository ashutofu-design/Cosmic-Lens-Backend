Bundled Noto Sans for multilingual Milan PDFs.

Populate this folder with:

  python scripts/download_noto_indic_for_milan_pdf.py

(run from repository root; script lives under artifacts/api-server/scripts/).

Expected filenames include NotoSansOriya-Regular.ttf, NotoSansDevanagari-Bold.ttf, etc.
See milan_pdf._INDIC_FONT_FAMILIES for the full candidate list.

Override: MILAN_NOTO_FONT_DIR or MILAN_NOTO_FONT_DIRS.
