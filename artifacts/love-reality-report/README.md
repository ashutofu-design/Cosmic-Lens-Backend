# Love Reality Pro — Local full PDF preview

**Pura report** locally dekho — **no LLM**, sample data + production ReportLab.

## Quick start

```bash
cd artifacts/love-reality-report
pnpm install
pnpm gen:pdf
pnpm dev:only
```

Open **http://127.0.0.1:5180** — PDF box ke andar scroll karo (saari ~14 sections, ~15+ PDF pages).

## Kya generate hota hai

| File | Kya hai |
|------|---------|
| `public/preview-report.pdf` | Pura Love Reality Pro PDF |
| `public/preview-report-meta.json` | Page count, couple name |

Script: `artifacts/api-server/scripts/gen_love_exec_preview_pdf.py`  
Renderer: `render_love_reality_pro_pdf()` — wahi jo phone par.

Layout change ke baad: `pnpm gen:pdf` → browser refresh.
