import { useState } from "react";
import { ProjectCatalog } from "./components/ProjectCatalog";
import { ReportContentsForm } from "./components/ReportContentsForm";
import { ReportLabPdfPreview } from "./components/ReportLabPdfPreview";
import { sampleReportData } from "./sampleData";

type ViewMode = "project" | "form" | "pdf";

export default function App() {
  const [phoneView, setPhoneView] = useState(true);
  const [viewMode, setViewMode] = useState<ViewMode>("project");

  const tabClass = (mode: ViewMode) =>
    `rounded-full px-3 py-1 text-xs font-semibold ${
      viewMode === mode ? "bg-cosmic-600 text-white" : "bg-slate-100 text-slate-600"
    }`;

  return (
    <div className="min-h-screen py-4 cosmic-bg">
      <div className="mx-auto mb-3 max-w-4xl px-3">
        <div className="rounded-lg border border-cosmic-300/40 bg-white/90 px-4 py-2.5 shadow-sm">
          <p className="text-sm font-semibold text-cosmic-800">
            Cosmic Lens — Project Explorer
          </p>
          <p className="mt-1 text-xs leading-relaxed text-slate-600">
            Pura project dekho: 70+ screens, saare forms, paid products, admin tabs.
            Love Reality report alag se Form / PDF view mein.
          </p>
          <div className="mt-2 flex flex-wrap items-center justify-center gap-2">
            <button type="button" onClick={() => setViewMode("project")} className={tabClass("project")}>
              Pura Project
            </button>
            <button type="button" onClick={() => setViewMode("form")} className={tabClass("form")}>
              Love Report Form
            </button>
            <button type="button" onClick={() => setViewMode("pdf")} className={tabClass("pdf")}>
              Love Report PDF
            </button>
            {viewMode === "pdf" ? (
              <>
                <button
                  type="button"
                  onClick={() => setPhoneView(true)}
                  className={`rounded-full px-3 py-1 text-xs font-semibold ${
                    phoneView ? "bg-cosmic-600 text-white" : "bg-slate-100 text-slate-600"
                  }`}
                >
                  Phone width
                </button>
                <button
                  type="button"
                  onClick={() => setPhoneView(false)}
                  className={`rounded-full px-3 py-1 text-xs font-semibold ${
                    !phoneView ? "bg-cosmic-600 text-white" : "bg-slate-100 text-slate-600"
                  }`}
                >
                  Full width
                </button>
              </>
            ) : null}
          </div>
        </div>
      </div>

      {viewMode === "project" ? (
        <ProjectCatalog />
      ) : viewMode === "form" ? (
        <ReportContentsForm />
      ) : (
        <ReportLabPdfPreview phoneView={phoneView} />
      )}

      {viewMode === "pdf" ? (
        <p className="mx-auto mt-4 max-w-md px-3 text-center text-xs text-slate-400">
          Sample couple: {sampleReportData.p1Name} & {sampleReportData.p2Name} ·{" "}
          <code className="rounded bg-white/80 px-1">pnpm gen:pdf</code> → refresh
        </p>
      ) : null}
    </div>
  );
}
