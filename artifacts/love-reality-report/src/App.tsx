import { useState } from "react";
import { ReportContentsForm } from "./components/ReportContentsForm";
import { ReportLabPdfPreview } from "./components/ReportLabPdfPreview";
import { sampleReportData } from "./sampleData";

type ViewMode = "pdf" | "form";

export default function App() {
  const [phoneView, setPhoneView] = useState(true);
  const [showReactApprox, setShowReactApprox] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>("form");

  return (
    <div className="min-h-screen py-4 cosmic-bg">
      <div className="mx-auto mb-3 max-w-lg px-3">
        <div className="rounded-lg border border-cosmic-300/40 bg-white/90 px-4 py-2.5 shadow-sm">
          <p className="text-sm font-semibold text-cosmic-800">
            Love Reality Pro — pura report (local, no LLM)
          </p>
          <p className="mt-1 text-xs leading-relaxed text-slate-600">
            <strong>Saari ~14 sections</strong> — executive summary, deep analysis, blueprint,
            dasha, remedies, sab kuch. Production ReportLab PDF, fixed sample data.
            Andar scroll karo — bilkul phone jaisa.
          </p>
          <div className="mt-2 flex flex-wrap items-center justify-center gap-2">
            <button
              type="button"
              onClick={() => setViewMode("form")}
              className={`rounded-full px-3 py-1 text-xs font-semibold ${
                viewMode === "form" ? "bg-cosmic-600 text-white" : "bg-slate-100 text-slate-600"
              }`}
            >
              Form view
            </button>
            <button
              type="button"
              onClick={() => setViewMode("pdf")}
              className={`rounded-full px-3 py-1 text-xs font-semibold ${
                viewMode === "pdf" ? "bg-cosmic-600 text-white" : "bg-slate-100 text-slate-600"
              }`}
            >
              PDF preview
            </button>
            <button
              type="button"
              onClick={() => setPhoneView(true)}
              disabled={viewMode !== "pdf"}
              className={`rounded-full px-3 py-1 text-xs font-semibold ${
                phoneView && viewMode === "pdf"
                  ? "bg-cosmic-600 text-white"
                  : "bg-slate-100 text-slate-600 opacity-60"
              }`}
            >
              Phone width
            </button>
            <button
              type="button"
              onClick={() => setPhoneView(false)}
              disabled={viewMode !== "pdf"}
              className={`rounded-full px-3 py-1 text-xs font-semibold ${
                !phoneView && viewMode === "pdf"
                  ? "bg-cosmic-600 text-white"
                  : "bg-slate-100 text-slate-600 opacity-60"
              }`}
            >
              Full width
            </button>
            <button
              type="button"
              onClick={() => setShowReactApprox((v) => !v)}
              className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600"
            >
              {showReactApprox ? "Hide" : "Show"} React draft
            </button>
          </div>
          <p className="mt-2 text-xs text-slate-500">
            Layout change ke baad: <code className="rounded bg-slate-100 px-1">pnpm gen:pdf</code>
            {" "}→ refresh browser
          </p>
        </div>
      </div>

      {viewMode === "form" ? <ReportContentsForm /> : <ReportLabPdfPreview phoneView={phoneView} />}

      {showReactApprox ? (
        <div className="mx-auto mt-8 max-w-md px-3 text-center text-xs text-slate-400">
          React draft hidden by default — use ReportLab preview above for exact phone view.
          Sample couple: {sampleReportData.p1Name} & {sampleReportData.p2Name}
        </div>
      ) : null}
    </div>
  );
}
