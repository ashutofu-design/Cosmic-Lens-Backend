import { sampleReportData } from "../sampleData";

const REPORT_SECTIONS = [
  { emoji: "❤️", title: "Emotional Reality", hook: "What they truly feel — not just what they show" },
  { emoji: "🛡️", title: "Loyalty & Intentions", hook: "Real intent — loyal, tempted, or unsure" },
  { emoji: "💔", title: "Breakup / Critical Window", hook: "Survive together or break — and when risk peaks" },
  { emoji: "🔄", title: "Return or Move On", hook: "Wait, patch up, or walk away for good" },
  { emoji: "🔮", title: "Future Timeline", hook: "3 months, 12 months, and major turning points" },
  { emoji: "🚩", title: "Red Flags & Remedies", hook: "What to watch and what to do" },
] as const;

function FormField({ label, value }: { label: string; value: string | number }) {
  return (
    <label className="block">
      <span className="mb-1 block text-[11px] font-bold uppercase tracking-wide text-cosmic-700">
        {label}
      </span>
      <div className="rounded-lg border border-cosmic-200/60 bg-white px-3 py-2 text-sm leading-relaxed text-slate-800">
        {value}
      </div>
    </label>
  );
}

function FormTextArea({ label, value }: { label: string; value: string }) {
  return (
    <label className="block">
      <span className="mb-1 block text-[11px] font-bold uppercase tracking-wide text-cosmic-700">
        {label}
      </span>
      <div className="min-h-[72px] rounded-lg border border-cosmic-200/60 bg-white px-3 py-2 text-sm leading-relaxed text-slate-800 whitespace-pre-wrap">
        {value}
      </div>
    </label>
  );
}

export function ReportContentsForm() {
  const d = sampleReportData;

  return (
    <div className="mx-auto max-w-2xl px-3 pb-8">
      <div className="rounded-xl border border-cosmic-300/40 bg-white/95 p-4 shadow-sm">
        <h2 className="text-base font-bold text-cosmic-800">Report ke andar kya-kya hai (form view)</h2>
        <p className="mt-1 text-xs text-slate-600">
          Sample couple: {d.p1Name} & {d.p2Name} — saari sections readable form fields mein
        </p>

        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <FormField label="Report ID" value={d.reportId} />
          <FormField label="Cosmic Alignment Score" value={`${d.cosmicAlignmentScore}/100`} />
        </div>

        <div className="mt-3">
          <FormTextArea label="Relationship Summary" value={d.relationshipSummary} />
        </div>

        <div className="mt-4">
          <p className="mb-2 text-[11px] font-bold uppercase tracking-wide text-cosmic-700">
            Core Metrics
          </p>
          <div className="grid gap-2 sm:grid-cols-2">
            {Object.values(d.metrics).map((m) => (
              <FormField key={m.label} label={m.label} value={`${m.value} — ${m.interpretation}`} />
            ))}
          </div>
        </div>

        <div className="mt-4">
          <p className="mb-2 text-[11px] font-bold uppercase tracking-wide text-cosmic-700">
            What&apos;s Inside Your Report (6 sections)
          </p>
          <div className="space-y-2">
            {REPORT_SECTIONS.map((s) => (
              <div
                key={s.title}
                className="rounded-lg border border-cosmic-100 bg-cosmic-50/50 px-3 py-2"
              >
                <p className="text-sm font-semibold text-slate-800">
                  {s.emoji} {s.title}
                </p>
                <p className="text-xs text-slate-600">{s.hook}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-4 grid gap-3">
          <FormTextArea label="Snapshot" value={d.snapshot} />
          <FormTextArea label="AI Explanation" value={d.aiExplanation} />
        </div>

        <div className="mt-4">
          <p className="mb-2 text-[11px] font-bold uppercase tracking-wide text-cosmic-700">
            Deep Analysis (4 dimensions)
          </p>
          <div className="grid gap-2 sm:grid-cols-2">
            {Object.values(d.analysis).map((a) => (
              <FormTextArea
                key={a.title}
                label={`${a.title} (${a.score}/100)`}
                value={a.explanation}
              />
            ))}
          </div>
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div>
            <p className="mb-2 text-[11px] font-bold uppercase tracking-wide text-cosmic-700">
              Strengths
            </p>
            {d.strengths.map((s) => (
              <FormField key={s.label} label={s.label} value={`${s.value}/100`} />
            ))}
          </div>
          <div>
            <p className="mb-2 text-[11px] font-bold uppercase tracking-wide text-cosmic-700">
              Challenges
            </p>
            {d.challenges.map((c) => (
              <FormField key={c.label} label={c.label} value={`${c.value}/100`} />
            ))}
          </div>
        </div>

        <div className="mt-4">
          <FormTextArea label="Final Cosmic Verdict" value={d.verdict} />
        </div>

        <div className="mt-4">
          <p className="mb-2 text-[11px] font-bold uppercase tracking-wide text-cosmic-700">
            Recommendations
          </p>
          <ul className="space-y-2">
            {d.recommendations.map((r) => (
              <li
                key={r}
                className="rounded-lg border border-cosmic-200/60 bg-white px-3 py-2 text-sm text-slate-800"
              >
                • {r}
              </li>
            ))}
          </ul>
        </div>

        <div className="mt-4">
          <p className="mb-2 text-[11px] font-bold uppercase tracking-wide text-cosmic-700">
            Key Insights
          </p>
          <ul className="space-y-2">
            {d.keyInsights.map((k) => (
              <li
                key={k.text}
                className="rounded-lg border border-cosmic-200/60 bg-white px-3 py-2 text-sm text-slate-800"
              >
                ✦ {k.text}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
