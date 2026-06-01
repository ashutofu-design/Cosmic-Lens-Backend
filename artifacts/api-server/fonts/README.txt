Noto Sans fonts for Milan PDF (ReportLab).

Place TrueType files in the `noto/` subdirectory (preferred), or directly here.

Populate automatically (requires network):

  python scripts/download_noto_indic_for_milan_pdf.py

Production: keep MILAN_PDF_RELAX_NATIVE_FONT_REQUIREMENT unset so PDF generation
fails loud if fonts are missing, instead of emitting Helvetica tofu.
