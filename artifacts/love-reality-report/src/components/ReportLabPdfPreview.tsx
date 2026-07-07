import { useEffect, useState } from "react";

type PreviewMeta = {
  pages?: number;
  couple?: string;
  report_id?: string;
  description?: string;
};

export function ReportLabPdfPreview({ phoneView }: { phoneView: boolean }) {
  const [meta, setMeta] = useState<PreviewMeta | null>(null);
  const [pdfReady, setPdfReady] = useState(false);
  const [pdfError, setPdfError] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetch("/preview-report-meta.json")
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (!cancelled && data) setMeta(data as PreviewMeta);
      })
      .catch(() => {});

    fetch("/preview-report.pdf", { method: "HEAD" })
      .then((r) => {
        if (!cancelled) {
          setPdfReady(r.ok);
          setPdfError(!r.ok);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setPdfReady(false);
          setPdfError(true);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const frameClass = phoneView ? "phone-pdf-frame" : "full-pdf-frame";

  return (
    <div className={`reportlab-pdf-stack ${phoneView ? "phone-pdf-view" : ""}`}>
      {meta ? (
        <p className="mb-1 text-center text-xs text-slate-600">
          <strong>{meta.couple}</strong>
          {meta.pages ? ` · ${meta.pages} pages` : null}
          {meta.report_id ? ` · ${meta.report_id}` : null}
        </p>
      ) : null}

      {pdfReady ? (
        <div className={`reportlab-pdf-frame-wrap ${frameClass}`}>
          <iframe
            title="Love Reality Pro PDF preview"
            className="reportlab-pdf-frame"
            src="/preview-report.pdf#view=FitH"
          />
        </div>
      ) : (
        <div className="mx-auto max-w-md rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-center text-sm text-amber-900">
          {pdfError ? (
            <>
              <p className="font-semibold">PDF abhi generate nahi hua</p>
              <p className="mt-1 text-xs leading-relaxed">
                Terminal mein chalao:{" "}
                <code className="rounded bg-white px-1">cd artifacts/love-reality-report && pnpm gen:pdf</code>
              </p>
            </>
          ) : (
            <p>PDF load ho raha hai…</p>
          )}
        </div>
      )}
    </div>
  );
}
