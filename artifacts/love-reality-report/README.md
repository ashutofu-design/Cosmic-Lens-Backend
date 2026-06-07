# Love Reality Pro — Premium Report Dashboard (React + Tailwind)

Dense A4 dashboard page for Love Reality Pro — designed for **90–95% page fill**, purple cosmic theme, glassmorphism cards, and Puppeteer PDF export.

## Dev preview

```bash
cd artifacts/love-reality-report
pnpm install
pnpm dev
```

Open http://127.0.0.1:5180

## Export PDF (Puppeteer)

```bash
pnpm build
pnpm export:pdf
# custom path:
pnpm export:pdf -- --out ./output/Aarav_Riya_Love_Reality.pdf
```

## Wire real API data

```tsx
import { LoveRealityProDashboard } from "./pages/LoveRealityProDashboard";
import { mapFromPdfContext } from "./types";

const data = mapFromPdfContext(pdfContext, p1, p2, {
  reportId: "LR-XXXX",
  generatedAt: new Date().toISOString(),
});

<LoveRealityProDashboard data={data} />
```

`mapFromPdfContext` accepts the same structure as `build_love_reality_pdf_v2_context()` from the Python API.

## Components

| Component | Role |
|-----------|------|
| `LoveRealityProDashboard` | Full A4 page layout |
| `CircularGauge` | Hero cosmic alignment score |
| `MetricCard` | Love / Breakup / Loyalty / Reunion |
| `MiniRing` | Analysis card scores |
| `GlassCard` | Glassmorphism container |
| `ReportHeader` / `ReportFooter` | Branding, verdict, QR |

## Production integration (later)

1. Build static HTML: `pnpm build`
2. Serve `dist/` or inject JSON into a template
3. Puppeteer `page.pdf()` with `printBackground: true`
4. Optionally replace ReportLab page 1 in `love_reality_pdf.py` with this renderer
