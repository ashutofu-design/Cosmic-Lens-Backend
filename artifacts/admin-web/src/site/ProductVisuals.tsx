type FeatureKind =
  | "face"
  | "kundli"
  | "numerology"
  | "palmistry"
  | "relationship"
  | "love"
  | "career"
  | "dosh"
  | "timing"
  | "vastu"
  | "reports";

const PLANETS = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"];

export function AnalysisEngineVisual() {
  const stages = ["Birth details", "Planetary positions", "Dasha", "Houses", "Timing", "Guidance"];
  return (
    <div className="analysis-engine-visual">
      <div className="engine-chart">
        <span className="engine-chart-line engine-line-one" />
        <span className="engine-chart-line engine-line-two" />
        <span className="engine-chart-line engine-line-three" />
        <div className="engine-chart-core">
          <small>D1</small>
          <strong>Chart</strong>
        </div>
        {["D9", "Dasha", "Transit", "Houses", "Timing"].map((label, index) => (
          <span
            key={label}
            className={`engine-node engine-node-${index + 1}`}
            style={{ animationDelay: `${index * -1.2}s` }}
          >
            {label}
          </span>
        ))}
        {PLANETS.map((planet, index) => (
          <i
            key={planet}
            className="engine-planet"
            style={{
              left: `${50 + Math.cos((index / PLANETS.length) * Math.PI * 2) * 42}%`,
              top: `${50 + Math.sin((index / PLANETS.length) * Math.PI * 2) * 42}%`,
              animationDelay: `${index * -0.35}s`,
            }}
          >
            {planet}
          </i>
        ))}
      </div>
      <div className="engine-flow" aria-label="Chart analysis sequence">
        {stages.map((stage, index) => (
          <span key={stage} style={{ animationDelay: `${index * 0.65}s` }}>
            <i>{index + 1}</i>
            {stage}
          </span>
        ))}
      </div>
      <span className="product-preview-note">How Cosmic Lens grounds guidance in chart context</span>
    </div>
  );
}

export function FeatureVisual({ kind }: { kind: FeatureKind }) {
  switch (kind) {
    case "face":
      return <FaceScanVisual />;
    case "kundli":
      return <KundliVisual />;
    case "numerology":
      return <NumerologyVisual />;
    case "palmistry":
      return <PalmistryVisual />;
    case "relationship":
      return <MilanVisual compact />;
    case "love":
      return <LoveSignalsVisual />;
    case "career":
      return <CareerVisual />;
    case "dosh":
      return <DoshVisual />;
    case "timing":
      return <LifeMapVisual compact />;
    case "vastu":
      return <VastuVisual />;
    case "reports":
      return <ReportsVisual compact />;
  }
}

function KundliVisual() {
  return (
    <div className="feature-visual kundli-visual">
      <div className="kundli-large-chart">
        <span className="kundli-diagonal kundli-diagonal-a" />
        <span className="kundli-diagonal kundli-diagonal-b" />
        <span className="kundli-midline kundli-midline-a" />
        <span className="kundli-midline kundli-midline-b" />
        {[
          ["Su", "10%", "50%"],
          ["Mo", "50%", "10%"],
          ["Ju", "84%", "50%"],
          ["Ve", "50%", "86%"],
          ["Sa", "23%", "26%"],
          ["Ma", "74%", "74%"],
        ].map(([planet, left, top], index) => (
          <i key={planet} style={{ left, top, animationDelay: `${index * -0.7}s` }}>
            {planet}
          </i>
        ))}
        <strong>D1</strong>
      </div>
      <div className="kundli-position-list">
        <span><i className="dot-sun" /> Sun <b>10th house</b></span>
        <span><i className="dot-moon" /> Moon <b>4th house</b></span>
        <span><i className="dot-jupiter" /> Jupiter <b>11th house</b></span>
        <div className="kundli-dasha">
          <small>Active dasha</small>
          <strong>Jupiter · Venus</strong>
          <i><b /></i>
        </div>
      </div>
      <PreviewNote />
    </div>
  );
}

function LoveSignalsVisual() {
  return (
    <div className="feature-visual love-signal-visual">
      <div className="love-orbit">
        <span className="love-core"><i /><i /></span>
        <span className="love-ring love-ring-one" />
        <span className="love-ring love-ring-two" />
      </div>
      <div className="love-signal-list">
        {[
          ["Emotional bond", "Supportive"],
          ["Commitment", "Developing"],
          ["Communication", "Needs clarity"],
          ["Timing", "Window ahead"],
        ].map(([label, value], index) => (
          <span key={label} style={{ animationDelay: `${index * 0.25}s` }}>
            <small>{label}</small>
            <strong>{value}</strong>
            <i><b style={{ width: `${82 - index * 9}%` }} /></i>
          </span>
        ))}
      </div>
      <PreviewNote />
    </div>
  );
}

function CareerVisual() {
  return (
    <div className="feature-visual career-visual">
      <div className="career-chart">
        <span className="career-grid" />
        <svg viewBox="0 0 500 180" role="img" aria-label="Career timing preview">
          <defs>
            <linearGradient id="careerLine" x1="0" x2="1">
              <stop offset="0" stopColor="#67e8f9" stopOpacity=".35" />
              <stop offset=".55" stopColor="#a78bfa" />
              <stop offset="1" stopColor="#e8c872" />
            </linearGradient>
          </defs>
          <path className="career-path-shadow" d="M10 145 C90 132 98 105 160 116 S252 145 302 80 S400 42 490 24" />
          <path className="career-path" d="M10 145 C90 132 98 105 160 116 S252 145 302 80 S400 42 490 24" />
        </svg>
        <span className="career-marker marker-now"><i />Now</span>
        <span className="career-marker marker-window"><i />Opportunity window</span>
      </div>
      <div className="career-signals">
        <span><small>Career</small><strong>Transition building</strong></span>
        <span><small>Money</small><strong>Stable → expanding</strong></span>
        <span><small>Risk</small><strong>Review commitments</strong></span>
      </div>
      <PreviewNote />
    </div>
  );
}

function DoshVisual() {
  const rows = [
    ["Manglik", "Mild", "amber"],
    ["Kalsarp", "Not active", "green"],
    ["Pitra", "Review", "violet"],
    ["Guru Chandal", "Not active", "green"],
    ["Shani", "Active period", "cyan"],
  ];
  return (
    <div className="feature-visual dosh-visual">
      <div className="dosh-header"><span>Dosh analysis</span><small>Chart-based screening</small></div>
      <div className="dosh-list">
        {rows.map(([name, status, tone], index) => (
          <div key={name} style={{ animationDelay: `${index * 0.12}s` }}>
            <i className={`dosh-dot tone-${tone}`} />
            <strong>{name}</strong>
            <span>{status}</span>
          </div>
        ))}
      </div>
      <div className="dosh-context">
        <i />
        <p><small>Context matters</small>Strength, aspects and active period are read together.</p>
      </div>
      <PreviewNote />
    </div>
  );
}

export function LifeMapVisual({ compact = false }: { compact?: boolean }) {
  const events = [
    { label: "Past", detail: "Foundation", tone: "muted" },
    { label: "Present", detail: "Career decision", tone: "cyan" },
    { label: "Upcoming", detail: "Relationship window", tone: "violet" },
    { label: "Key window", detail: "Finance · property", tone: "gold" },
  ];
  return (
    <div className={`feature-visual life-map-visual${compact ? " is-compact" : ""}`}>
      <div className="life-map-track">
        <span className="life-track-base" />
        <span className="life-track-progress" />
        <i className="life-moving-planet">✦</i>
        {events.map((event, index) => (
          <div
            key={event.label}
            className={`life-map-event tone-${event.tone}`}
            style={{ left: `${8 + index * 28}%`, animationDelay: `${index * 0.3}s` }}
          >
            <i />
            <small>{event.label}</small>
            <strong>{event.detail}</strong>
          </div>
        ))}
      </div>
      {!compact ? (
        <div className="life-map-legend">
          <span>Career</span><span>Relationship</span><span>Finance</span><span>Major decisions</span>
        </div>
      ) : null}
      <PreviewNote />
    </div>
  );
}

export function MilanVisual({ compact = false }: { compact?: boolean }) {
  const signals = [
    ["Compatibility", "Supportive"],
    ["Communication", "Mixed → improving"],
    ["Commitment", "Strong potential"],
    ["Long-term stability", "Needs timing"],
  ];
  return (
    <div className={`feature-visual milan-visual${compact ? " is-compact" : ""}`}>
      <div className="milan-charts">
        <SimpleChart label="A" />
        <div className="milan-compare">
          <i /><i /><i />
          <span>Chart comparison</span>
        </div>
        <SimpleChart label="B" />
      </div>
      <div className="milan-signals">
        {signals.map(([label, result], index) => (
          <div key={label} style={{ animationDelay: `${index * 0.18}s` }}>
            <span>{label}</span>
            <strong>{result}</strong>
          </div>
        ))}
      </div>
      <PreviewNote />
    </div>
  );
}

function FaceScanVisual() {
  const layers = [
    ["Facial geometry", "Mapped"],
    ["Feature zones", "Scanning"],
    ["Vedic synthesis", "Preview"],
  ];
  return (
    <div className="feature-visual face-scan-visual">
      <div className="science-scan-header">
        <span><i /> Multi-layer scan</span>
        <strong>LAUNCHING SOON</strong>
      </div>
      <div className="face-scan-layout">
        <div className="face-scan-stage">
          <div className="face-view-tabs"><span className="is-active">Front</span><span>Left</span><span>Right</span></div>
          <svg className="face-map" viewBox="0 0 240 300" aria-label="Face geometry preview">
            <path className="face-outline" d="M120 22C72 22 49 59 53 116c3 48 17 105 67 137 50-32 64-89 67-137 4-57-19-94-67-94Z" />
            <path className="face-contour contour-a" d="M72 103c20-25 76-25 96 0M70 151c21 26 79 26 100 0M92 204c18 12 38 12 56 0" />
            <path className="face-contour contour-b" d="M120 49v170M65 129h110M81 78l78 141M159 78 81 219" />
            <path className="face-feature" d="M78 118c12-9 25-9 37 0-12 9-25 9-37 0Zm47 0c12-9 25-9 37 0-12 9-25 9-37 0ZM120 120l-9 50h18M98 189c14 9 30 9 44 0" />
            {[["78","118"],["115","118"],["125","118"],["162","118"],["120","70"],["120","170"],["98","189"],["142","189"],["120","231"]].map(([cx, cy]) => (
              <circle key={`${cx}-${cy}`} className="face-landmark" cx={cx} cy={cy} r="3" />
            ))}
          </svg>
          <span className="face-scan-line" />
          <span className="face-axis axis-x" />
          <span className="face-axis axis-y" />
        </div>
        <div className="science-layer-panel">
          <small>Analysis layers</small>
          {layers.map(([label, status], index) => (
            <div key={label}>
              <span><i>{index + 1}</i>{label}</span>
              <strong>{status}</strong>
              <b><i style={{ animationDelay: `${index * 0.45}s` }} /></b>
            </div>
          ))}
          <p>Front and profile imagery · Vedic + science fusion</p>
        </div>
      </div>
      <PreviewNote />
    </div>
  );
}

function NumerologyVisual() {
  const numbers = [
    ["Life Path", "8"],
    ["Destiny", "3"],
    ["Soul Urge", "6"],
    ["Name", "5"],
  ];
  return (
    <div className="feature-visual numerology-visual">
      <div className="numerology-matrix">
        <span className="number-orbit number-orbit-a" />
        <span className="number-orbit number-orbit-b" />
        <div className="master-number"><small>Core vibration</small><strong>8</strong><span>Power · Structure</span></div>
        {["1", "3", "5", "6", "8", "9"].map((number, index) => (
          <i key={number} className={`matrix-number matrix-number-${index + 1}`}>{number}</i>
        ))}
      </div>
      <div className="numerology-results">
        <div className="numerology-title"><span>Personal number system</span><i>CALCULATED</i></div>
        {numbers.map(([label, number], index) => (
          <div key={label} style={{ animationDelay: `${index * 0.15}s` }}>
            <span>{label}</span><strong>{number}</strong><i />
          </div>
        ))}
        <p>Pythagorean calculation · Name pattern analysis</p>
      </div>
      <PreviewNote />
    </div>
  );
}

function PalmistryVisual() {
  return (
    <div className="feature-visual palm-scan-visual">
      <div className="science-scan-header">
        <span><i /> Palm line mapping</span>
        <strong>CONCEPT PREVIEW</strong>
      </div>
      <div className="palm-scan-layout">
        <div className="palm-map-wrap">
          <svg className="palm-map" viewBox="0 0 260 340" aria-label="Palmistry concept preview">
            <path className="palm-outline" d="M93 316c-28-34-42-72-43-111l-2-54c0-12 7-20 16-20 8 0 14 6 17 16l5 25-5-96c-1-14 7-24 18-24 10 0 17 8 18 21l4 83 2-118c0-15 8-25 19-25 12 0 19 10 18 26l-2 116 8-101c1-14 10-22 20-20 10 1 16 11 14 25l-10 106 12-70c2-13 11-20 21-17 10 3 14 13 11 26l-17 96c-6 43-23 82-48 116Z" />
            <path className="palm-line palm-life" d="M93 164c-5 48 12 95 50 125" />
            <path className="palm-line palm-head" d="M78 183c38-17 78-13 115 10" />
            <path className="palm-line palm-heart" d="M77 145c42-20 82-14 123 11" />
            <path className="palm-line palm-fate" d="M139 294c-9-59-4-111 15-157" />
            {[["93","164"],["143","289"],["78","183"],["193","193"],["77","145"],["200","156"],["154","137"]].map(([cx, cy]) => (
              <circle key={`${cx}-${cy}`} className="palm-point" cx={cx} cy={cy} r="4" />
            ))}
          </svg>
          <span className="palm-scan-beam" />
        </div>
        <div className="palm-line-panel">
          {[
            ["Heart line", "Emotional pattern"],
            ["Head line", "Mental approach"],
            ["Life line", "Vitality pattern"],
            ["Fate line", "Direction"],
          ].map(([line, meaning], index) => (
            <div key={line}>
              <i style={{ animationDelay: `${index * -0.45}s` }} />
              <span><strong>{line}</strong><small>{meaning}</small></span>
            </div>
          ))}
          <p>Future experience concept · Not currently live</p>
        </div>
      </div>
      <PreviewNote />
    </div>
  );
}

function VastuVisual() {
  return (
    <div className="feature-visual vastu-visual">
      <div className="science-scan-header">
        <span><i /> AstroVastu Drishti</span>
        <strong>LIVE ROOM SCAN</strong>
      </div>
      <div className="vastu-plan">
        <span className="vastu-room room-nw">Bedroom</span>
        <span className="vastu-room room-ne">Study</span>
        <span className="vastu-room room-sw">Kitchen</span>
        <span className="vastu-room room-se">Living</span>
        <span className="vastu-center">Brahmasthan</span>
        <div className="vastu-sweep" />
      </div>
      <div className="vastu-compass">
        <span>N</span><span>E</span><span>S</span><span>W</span>
        <i />
      </div>
      <div className="vastu-note"><small>Direction signal</small><strong>North-East · supportive</strong></div>
      <div className="vastu-scan-status"><span>Floor plan</span><span>Directions</span><span>Room energy</span><span>Dasha layer</span></div>
      <PreviewNote />
    </div>
  );
}

export function ReportsVisual({ compact = false }: { compact?: boolean }) {
  const reports = [
    { name: "Kundli Milan" },
    { name: "Love Reality" },
    { name: "Numerology" },
    { name: "Face Reading", status: "Coming soon" },
    { name: "AstroVastu" },
  ];
  return (
    <div className={`feature-visual reports-visual${compact ? " is-compact" : ""}`}>
      <div className="report-stack">
        {reports.map((report, index) => (
          <article
            key={report.name}
            className={`report-page report-page-${index + 1}`}
          >
            <span className="report-brand">COSMIC LENS</span>
            <small>PERSONALIZED REPORT</small>
            <strong>{report.name}</strong>
            {report.status ? <em>{report.status}</em> : null}
            <div className="report-chart-mark"><i /><i /><i /></div>
            <p><i /><i /><i /></p>
          </article>
        ))}
      </div>
      <div className="report-tabs">
        {reports.map((report) => (
          <span key={report.name}>
            {report.name}
            {report.status ? " · Soon" : ""}
          </span>
        ))}
      </div>
      <PreviewNote />
    </div>
  );
}

function SimpleChart({ label }: { label: string }) {
  return (
    <div className="simple-chart">
      <span className="simple-chart-a" />
      <span className="simple-chart-b" />
      <span className="simple-chart-c" />
      <span className="simple-chart-d" />
      <strong>{label}</strong>
    </div>
  );
}

function PreviewNote() {
  return <span className="product-preview-note">Representative product preview</span>;
}
