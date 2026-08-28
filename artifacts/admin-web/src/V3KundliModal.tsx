import { useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import {
  NorthIndianChartWeb,
  PLANET_CLR,
  SIGN_LORDS,
  StyleToggle,
  renderDashaSharePngDataUrl,
  renderNorthIndianChartPngDataUrl,
  resolveSignIndex,
  shortPlanet,
  type ChartPlanet,
  type ChartStyle,
} from "./NorthIndianChartWeb";
import {
  AshtakavargaPanel,
  BirthChartSnapshot,
  JaiminiPanel,
  NavataraPanel,
  TransitPanel,
} from "./v3KundliAppSections";
import {
  liveDashaMahaIndex,
  resolveLiveCurrentDasha,
  type AdminChartPayload,
} from "./v3KundliPack";

type Tab =
  | "basic"
  | "lagna"
  | "navamsa"
  | "divisional"
  | "kp"
  | "ashtakavarga"
  | "navatara"
  | "jaimini"
  | "transit"
  | "dasha";

type Props = {
  open: boolean;
  loading: boolean;
  error: string | null;
  data: AdminChartPayload | null;
  sharing: boolean;
  onClose: () => void;
  /** Share diamond chart image (PNG data-URL) into V3 chat. */
  onShareImage: (dataUrl: string) => void;
  onReload: () => void;
};

const DIV_ORDER = [
  { key: "D2", label: "Hora" },
  { key: "D3", label: "Drekkana" },
  { key: "D4", label: "Chaturthamsa" },
  { key: "D7", label: "Saptamsa" },
  { key: "D9", label: "Navamsa" },
  { key: "D10", label: "Dasamsa" },
  { key: "D12", label: "Dwadasamsa" },
  { key: "D16", label: "Shodasamsa" },
  { key: "D20", label: "Vimsamsa" },
  { key: "D24", label: "Chaturvimsamsa" },
  { key: "D27", label: "Nakshatramsa" },
  { key: "D30", label: "Trimsamsa" },
  { key: "D40", label: "Khavedamsa" },
  { key: "D45", label: "Akshavedamsa" },
  { key: "D60", label: "Shashtiamsa" },
] as const;

const CREAM = "#f5f2ed";
const CARD = "#ffffff";
const PINK_HEAD = "#f49797";
const TEXT = "#1f2937";
const MUTED = "#6b7280";

const MONTHS_SHORT = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
] as const;

/** Always day → month → year. Input 2010-06-27 → 27-06-2010 */
function formatDateDMY(raw?: string | null): string {
  if (raw == null || String(raw).trim() === "") return "—";
  const s = String(raw).trim();

  // Already DD-MM-YYYY
  if (/^\d{2}-\d{2}-\d{4}$/.test(s)) return s;

  // Already DD-Mon-YYYY → convert to DD-MM-YYYY
  const monName = s.match(/^(\d{1,2})-([A-Za-z]{3})-(\d{4})$/);
  if (monName) {
    const mi = MONTHS_SHORT.findIndex((x) => x.toLowerCase() === monName[2].toLowerCase());
    if (mi >= 0) {
      return `${monName[1].padStart(2, "0")}-${String(mi + 1).padStart(2, "0")}-${monName[3]}`;
    }
  }

  // YYYY-MM-DD or YYYY-MM-DDTHH:mm:ss…
  let m = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/);
  if (m) {
    return `${m[3].padStart(2, "0")}-${m[2].padStart(2, "0")}-${m[1]}`;
  }

  // DD/MM/YYYY or DD-MM-YYYY (1–2 digit day/month)
  m = s.match(/^(\d{1,2})[\/\-.](\d{1,2})[\/\-.](\d{4})/);
  if (m) {
    return `${m[1].padStart(2, "0")}-${m[2].padStart(2, "0")}-${m[3]}`;
  }

  // 27 June 2010 / 27 Jun 2010
  m = s.match(/^(\d{1,2})\s+([A-Za-z]{3,9})\s+(\d{4})/);
  if (m) {
    const mi = MONTHS_SHORT.findIndex((x) => m![2].toLowerCase().startsWith(x.toLowerCase()));
    if (mi >= 0) {
      return `${m[1].padStart(2, "0")}-${String(mi + 1).padStart(2, "0")}-${m[3]}`;
    }
  }

  const d = new Date(s);
  if (!Number.isNaN(d.getTime())) {
    const dd = String(d.getUTCDate()).padStart(2, "0");
    const mm = String(d.getUTCMonth() + 1).padStart(2, "0");
    return `${dd}-${mm}-${d.getUTCFullYear()}`;
  }
  return s;
}

function DetailRow({
  label,
  value,
  zebra,
}: {
  label: string;
  value: string;
  zebra?: boolean;
}) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "minmax(0, 40%) minmax(0, 60%)",
        gap: 8,
        padding: "11px 12px",
        background: zebra ? "#f3f4f6" : CARD,
        borderBottom: "1px solid #e5e7eb",
        fontSize: 13,
        alignItems: "start",
      }}
    >
      <div style={{ color: MUTED, wordBreak: "break-word" }}>{label}</div>
      <div style={{ color: TEXT, fontWeight: 600, wordBreak: "break-word", textAlign: "right" }}>
        {value || "—"}
      </div>
    </div>
  );
}

function PinkTable({
  columns,
  rows,
}: {
  columns: string[];
  rows: (string | number | null | undefined)[][];
}) {
  return (
    <div
      style={{
        borderRadius: 10,
        overflow: "auto",
        border: "1px solid #e5e7eb",
        marginTop: 8,
        WebkitOverflowScrolling: "touch",
      }}
    >
      <table
        style={{
          width: "100%",
          minWidth: columns.length > 4 ? 480 : "100%",
          borderCollapse: "collapse",
          fontSize: 11,
        }}
      >
        <thead>
          <tr style={{ background: PINK_HEAD, color: "#fff" }}>
            {columns.map((c) => (
              <th
                key={c}
                style={{
                  padding: "9px 6px",
                  fontWeight: 700,
                  textAlign: "center",
                  whiteSpace: "nowrap",
                }}
              >
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} style={{ background: i % 2 ? "#f9fafb" : CARD }}>
              {r.map((cell, j) => (
                <td
                  key={j}
                  style={{
                    padding: "9px 6px",
                    textAlign: "center",
                    color: TEXT,
                    fontWeight: j === 0 ? 700 : 500,
                    borderTop: "1px solid #e5e7eb",
                    whiteSpace: "nowrap",
                  }}
                >
                  {cell == null || cell === "" ? "—" : String(cell)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const DASHA_GRID = "minmax(70px, 0.9fr) minmax(86px, 1fr) minmax(86px, 1fr) 18px";

function ShareDiamondButton({
  label,
  chartLabel,
  lagnaSign,
  planets,
  personName,
  sharing,
  loading,
  onShareImage,
}: {
  label: string;
  chartLabel: string;
  lagnaSign?: string | null;
  planets: ChartPlanet[];
  personName: string;
  sharing: boolean;
  loading: boolean;
  onShareImage: (dataUrl: string) => void;
}) {
  return (
    <>
      <button
        type="button"
        disabled={sharing || loading || !planets.length}
        onClick={() => {
          try {
            const dataUrl = renderNorthIndianChartPngDataUrl({
              lagnaSign,
              planets,
              title: `${personName} · ${chartLabel}`,
              caption: chartLabel,
              chartPx: 720,
            });
            onShareImage(dataUrl);
          } catch (e) {
            alert(e instanceof Error ? e.message : "Could not render chart image");
          }
        }}
        style={{
          width: "100%",
          marginTop: 14,
          padding: "12px 14px",
          borderRadius: 10,
          border: "1px solid #16a34a",
          background: "#15803d",
          color: "#fff",
          fontWeight: 800,
          fontSize: 14,
          cursor: sharing ? "wait" : "pointer",
        }}
      >
        {sharing ? "Sharing diamond chart…" : label}
      </button>
      <div
        style={{
          marginTop: 8,
          fontSize: 11,
          color: MUTED,
          textAlign: "center",
          lineHeight: 1.4,
        }}
      >
        Chat me sirf North Indian diamond chart image jayegi
      </div>
    </>
  );
}

export function V3KundliModal({
  open,
  loading,
  error,
  data,
  sharing,
  onClose,
  onShareImage,
  onReload,
}: Props) {
  const [tab, setTab] = useState<Tab>("basic");
  const [chartStyle, setChartStyle] = useState<ChartStyle>("north");
  const [divKey, setDivKey] = useState("D10");
  const [dashaMahaIdx, setDashaMahaIdx] = useState<number | null>(null);

  useEffect(() => {
    if (open) {
      setTab("basic");
      setChartStyle("north");
      setDashaMahaIdx(null);
    }
  }, [open]);

  const c = data?.chart;
  const b = data?.birth;
  const planets = Array.isArray(c?.planets) ? c!.planets! : [];
  const dashas = Array.isArray(c?.dashas) ? c!.dashas! : [];
  const liveDasha = useMemo(() => resolveLiveCurrentDasha(c), [c]);
  const liveMahaIdx = useMemo(() => liveDashaMahaIndex(c), [c]);
  const d9 = c?.divisionalCharts?.D9;
  const divMap = c?.divisionalCharts || {};
  const availableDivs = DIV_ORDER.filter((d) => divMap[d.key]?.planets?.length);
  const kpPlanets = c?.kp?.planets || [];
  const cusps = c?.kp?.cusps || [];

  useEffect(() => {
    if (availableDivs.length && !availableDivs.some((d) => d.key === divKey)) {
      setDivKey(availableDivs[0].key);
    }
  }, [availableDivs, divKey]);

  if (!open) return null;

  // Planet Position = Lagna / Navamsa / Divisional (charts only).
  // Rest mirrors app View Kundli: snapshot, KP, Ashtakavarga, Navatara, Jaimini, Transit, Dasha.
  const tabs: { id: Tab; label: string }[] = [
    { id: "basic", label: "Kundli" },
    { id: "lagna", label: "Lagna" },
    { id: "navamsa", label: "Navamsa" },
    { id: "divisional", label: "Divisional" },
    { id: "kp", label: "KP" },
    { id: "ashtakavarga", label: "Ashtakavarga" },
    { id: "navatara", label: "Navatara" },
    { id: "jaimini", label: "Jaimini" },
    { id: "transit", label: "Transit" },
    { id: "dasha", label: "Dasha" },
  ];

  const moonKp = kpPlanets.find((p) => (p.name || "").toLowerCase() === "moon");
  const ascCusp = cusps.find((cu) => Number(cu.house) === 1);
  const selectedDiv = divMap[divKey];
  const maha = dashaMahaIdx != null ? dashas[dashaMahaIdx] : null;
  const antars = maha?.subDashas || [];

  const modal = (
    <div
      role="dialog"
      aria-modal="true"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 2147483646,
        background: "rgba(0,0,0,0.55)",
        display: "flex",
        alignItems: "stretch",
        justifyContent: "center",
        padding: 0,
      }}
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: "100%",
          maxWidth: 520,
          height: "100%",
          maxHeight: "100dvh",
          overflow: "hidden",
          display: "flex",
          flexDirection: "column",
          borderRadius: 0,
          background: CREAM,
          boxShadow: "0 20px 60px rgba(0,0,0,0.45)",
          margin: "0 auto",
        }}
      >
        {/* Header */}
        <div
          style={{
            background: CARD,
            padding: "10px 10px",
            display: "flex",
            alignItems: "center",
            gap: 6,
            borderBottom: "1px solid #e5e7eb",
            flexShrink: 0,
          }}
        >
          <button
            type="button"
            onClick={onClose}
            style={{
              border: "none",
              background: "transparent",
              fontSize: 20,
              cursor: "pointer",
              color: TEXT,
              lineHeight: 1,
              padding: "4px 6px",
              flexShrink: 0,
            }}
            aria-label="Back"
          >
            ←
          </button>
          <div
            style={{
              flex: 1,
              textAlign: "center",
              fontWeight: 800,
              fontSize: 16,
              color: TEXT,
              minWidth: 0,
            }}
          >
            Kundli
          </div>
          <button
            type="button"
            onClick={onReload}
            disabled={loading}
            style={{ fontSize: 11, padding: "6px 8px", flexShrink: 0 }}
          >
            Reload
          </button>
        </div>

        {/* Primary tabs — side by side scroll */}
        <div
          style={{
            background: CARD,
            display: "flex",
            gap: 0,
            overflowX: "auto",
            borderBottom: "1px solid #e5e7eb",
            WebkitOverflowScrolling: "touch",
          }}
        >
          {tabs.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id)}
              style={{
                flex: "0 0 auto",
                border: "none",
                background: "transparent",
                padding: "12px 14px",
                fontWeight: tab === t.id ? 800 : 600,
                fontSize: 13,
                color: TEXT,
                cursor: "pointer",
                borderBottom: tab === t.id ? "2.5px solid #111" : "2.5px solid transparent",
                whiteSpace: "nowrap",
              }}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Body */}
        <div style={{ padding: 12, overflow: "auto", flex: 1, WebkitOverflowScrolling: "touch" }}>
          {loading ? (
            <div style={{ color: MUTED }}>Loading kundli…</div>
          ) : error ? (
            <div style={{ color: "#dc2626" }}>{error}</div>
          ) : !c ? (
            <div style={{ color: MUTED }}>No chart data.</div>
          ) : (
            <>
              {tab === "basic" ? (
                <div style={{ display: "grid", gap: 12 }}>
                  <BirthChartSnapshot chart={c} />

                  <div
                    style={{
                      background: CARD,
                      borderRadius: 14,
                      overflow: "hidden",
                      border: "1px solid #e5e7eb",
                    }}
                  >
                    <div
                      style={{
                        background: "#f5f3ff",
                        padding: "10px 14px",
                        borderBottom: "1px solid #e5e7eb",
                        fontWeight: 800,
                        fontSize: 11,
                        letterSpacing: 1,
                        color: "#7c3aed",
                      }}
                    >
                      BIRTH DETAILS
                    </div>
                    {[
                      ["Name", b?.name || data?.name || c.name || "—"],
                      ["Date of Birth", formatDateDMY(b?.dob || c.dob)],
                      ["Time", b?.time || c.time || "—"],
                      ["Place", b?.place || c.place || "—"],
                      ["Gender", b?.gender || "—"],
                      ["Cosmo ID", data?.cosmo_user_id || "—"],
                      ["Sun Sign", c.sunSign || "—"],
                      [
                        "Current Dasha",
                        liveDasha
                          ? [liveDasha.maha, liveDasha.antar, liveDasha.pratyantar]
                              .filter(Boolean)
                              .join(" / ")
                          : "—",
                      ],
                      [
                        "Dasha period",
                        liveDasha
                          ? `${formatDateDMY(liveDasha.startDate)} → ${formatDateDMY(liveDasha.endDate)}`
                          : "—",
                      ],
                    ].map(([label, value], i) => (
                      <DetailRow
                        key={label}
                        label={label}
                        value={String(value)}
                        zebra={i % 2 === 1}
                      />
                    ))}
                  </div>

                  <div
                    style={{
                      fontSize: 12,
                      color: MUTED,
                      lineHeight: 1.45,
                      padding: "8px 4px",
                    }}
                  >
                    Planet positions (D1 / Divisional) → Lagna · Navamsa · Divisional tabs. Full
                    dasha timeline → Dasha tab.
                  </div>
                </div>
              ) : null}

              {tab === "lagna" ? (
                <div>
                  <StyleToggle value={chartStyle} onChange={setChartStyle} />
                  <NorthIndianChartWeb
                    style={chartStyle}
                    lagnaSign={c.ascendant}
                    planets={planets}
                    caption="Lagna Chart"
                    showAsc
                    size={360}
                  />
                  <ShareDiamondButton
                    label="Share D1 diamond chart to chat"
                    chartLabel="D1 Lagna"
                    lagnaSign={c.ascendant}
                    planets={planets}
                    personName={b?.name || data?.name || c.name || "User"}
                    sharing={sharing}
                    loading={loading}
                    onShareImage={onShareImage}
                  />
                </div>
              ) : null}

              {tab === "navamsa" ? (
                d9 ? (
                  <div>
                    <StyleToggle value={chartStyle} onChange={setChartStyle} />
                    <NorthIndianChartWeb
                      style={chartStyle}
                      lagnaSign={d9.ascendant}
                      planets={d9.planets || []}
                      caption="Navamsa Chart"
                      showAsc
                      size={360}
                    />
                    <ShareDiamondButton
                      label="Share D9 Navamsa diamond to chat"
                      chartLabel="D9 Navamsa"
                      lagnaSign={d9.ascendant}
                      planets={d9.planets || []}
                      personName={b?.name || data?.name || c.name || "User"}
                      sharing={sharing}
                      loading={loading}
                      onShareImage={onShareImage}
                    />
                  </div>
                ) : (
                  <div style={{ color: MUTED }}>Navamsa (D9) not available.</div>
                )
              ) : null}

              {tab === "divisional" ? (
                availableDivs.length ? (
                  <div>
                    <StyleToggle value={chartStyle} onChange={setChartStyle} />
                    <div
                      style={{
                        display: "flex",
                        gap: 8,
                        overflowX: "auto",
                        marginBottom: 12,
                        paddingBottom: 4,
                      }}
                    >
                      {availableDivs.map((d) => (
                        <button
                          key={d.key}
                          type="button"
                          onClick={() => setDivKey(d.key)}
                          style={{
                            flex: "0 0 auto",
                            border: "none",
                            background: "transparent",
                            padding: "8px 10px",
                            fontWeight: divKey === d.key ? 800 : 600,
                            fontSize: 12,
                            color: TEXT,
                            borderBottom:
                              divKey === d.key ? "2.5px solid #111" : "2.5px solid transparent",
                            whiteSpace: "nowrap",
                            cursor: "pointer",
                          }}
                        >
                          {d.label}
                        </button>
                      ))}
                    </div>
                    <NorthIndianChartWeb
                      style={chartStyle}
                      lagnaSign={selectedDiv?.ascendant || c.ascendant}
                      planets={selectedDiv?.planets || []}
                      caption={`${availableDivs.find((d) => d.key === divKey)?.label || divKey} Chart`}
                      showAsc
                      size={360}
                    />
                    <ShareDiamondButton
                      label={`Share ${availableDivs.find((d) => d.key === divKey)?.label || divKey} diamond to chat`}
                      chartLabel={`${divKey} ${availableDivs.find((d) => d.key === divKey)?.label || ""}`.trim()}
                      lagnaSign={selectedDiv?.ascendant || c.ascendant}
                      planets={selectedDiv?.planets || []}
                      personName={b?.name || data?.name || c.name || "User"}
                      sharing={sharing}
                      loading={loading}
                      onShareImage={onShareImage}
                    />
                  </div>
                ) : (
                  <div style={{ color: MUTED }}>No divisional charts on this kundli.</div>
                )
              ) : null}

              {tab === "kp" ? (
                <div style={{ display: "grid", gap: 16, minWidth: 0 }}>
                  <NorthIndianChartWeb
                    style="north"
                    title="Bhav Chalit Chart"
                    lagnaSign={c.ascendant}
                    planets={
                      kpPlanets.length
                        ? kpPlanets.map((p) => ({
                            name: p.name,
                            house: p.house,
                            sign: p.sign,
                          }))
                        : planets
                    }
                    showAsc
                    size={360}
                  />

                  <div>
                    <div style={{ fontWeight: 800, fontSize: 15, color: TEXT, marginBottom: 4 }}>
                      Ruling Planets
                    </div>
                    <PinkTable
                      columns={["—", "Sign Lord", "Star Lord", "Sub Lord"]}
                      rows={[
                        [
                          "MO",
                          moonKp?.sign
                            ? SIGN_LORDS[resolveSignIndex(moonKp.sign)]
                            : c.moonSign
                              ? SIGN_LORDS[resolveSignIndex(c.moonSign)]
                              : "—",
                          moonKp?.nl || "—",
                          moonKp?.sb || "—",
                        ],
                        [
                          "ASC",
                          ascCusp?.sign
                            ? SIGN_LORDS[resolveSignIndex(ascCusp.sign)]
                            : c.ascendant
                              ? SIGN_LORDS[resolveSignIndex(c.ascendant)]
                              : "—",
                          ascCusp?.nl || "—",
                          ascCusp?.sb || "—",
                        ],
                      ]}
                    />
                  </div>

                  {kpPlanets.length ? (
                    <div>
                      <div style={{ fontWeight: 800, fontSize: 15, color: TEXT, marginBottom: 4 }}>
                        Planets
                      </div>
                      <PinkTable
                        columns={["Planet", "Cusp", "Sign", "Sign Lord", "Star Lord", "Sub Lord"]}
                        rows={kpPlanets.map((p) => [
                          shortPlanet(p.name),
                          p.house != null ? `H${p.house}` : "—",
                          p.sign || "—",
                          p.sign ? SIGN_LORDS[resolveSignIndex(p.sign)] : "—",
                          p.nl || "—",
                          p.sb || "—",
                        ])}
                      />
                    </div>
                  ) : null}

                  {cusps.length ? (
                    <div>
                      <div style={{ fontWeight: 800, fontSize: 15, color: TEXT, marginBottom: 4 }}>
                        Cusps
                      </div>
                      <PinkTable
                        columns={["House", "Sign", "Degree", "Star Lord", "Sub Lord"]}
                        rows={cusps.map((cu) => [
                          cu.house,
                          cu.sign || "—",
                          cu.degree || "—",
                          cu.nl || "—",
                          cu.sb || "—",
                        ])}
                      />
                    </div>
                  ) : null}
                </div>
              ) : null}

              {tab === "ashtakavarga" ? <AshtakavargaPanel chart={c} /> : null}
              {tab === "navatara" ? <NavataraPanel chart={c} /> : null}
              {tab === "jaimini" ? <JaiminiPanel chart={c} /> : null}
              {tab === "transit" ? <TransitPanel chart={c} active={tab === "transit"} /> : null}

              {tab === "dasha" ? (
                <div style={{ minWidth: 0 }}>
                  <div
                    style={{
                      fontWeight: 800,
                      fontSize: 11,
                      letterSpacing: 1,
                      color: "#7c3aed",
                      marginBottom: 10,
                    }}
                  >
                    DASHA TIMELINE
                  </div>
                  <div
                    style={{
                      fontWeight: 700,
                      fontSize: 13,
                      color: TEXT,
                      marginBottom: 10,
                      display: "flex",
                      alignItems: "center",
                      flexWrap: "wrap",
                      gap: 6,
                    }}
                  >
                    <span>
                      {maha
                        ? `MahaDasha > AntarDasha · ${shortPlanet(maha.planet)}`
                        : "MahaDasha"}
                    </span>
                    {maha ? (
                      <button
                        type="button"
                        onClick={() => setDashaMahaIdx(null)}
                        style={{
                          border: "none",
                          background: "transparent",
                          color: "#e11d48",
                          fontWeight: 700,
                          cursor: "pointer",
                          fontSize: 12,
                          padding: 0,
                        }}
                      >
                        ← All
                      </button>
                    ) : null}
                  </div>

                  {liveDasha ? (
                    <div
                      style={{
                        marginBottom: 12,
                        padding: "10px 12px",
                        borderRadius: 10,
                        background: "#fff1f2",
                        border: "1px solid #fecdd3",
                        fontSize: 13,
                        color: TEXT,
                      }}
                    >
                      <div style={{ fontWeight: 800, marginBottom: 4, color: "#be123c" }}>
                        Ab chal rahi (same as app)
                      </div>
                      <div>
                        MD:{" "}
                        <strong style={{ color: PLANET_CLR[liveDasha.maha || ""] || TEXT }}>
                          {liveDasha.maha || "—"}
                        </strong>
                        {" · AD: "}
                        <strong>{liveDasha.antar || "—"}</strong>
                        {liveDasha.pratyantar ? (
                          <>
                            {" · PD: "}
                            <strong>{liveDasha.pratyantar}</strong>
                          </>
                        ) : null}
                      </div>
                      <div style={{ color: MUTED, fontSize: 12, marginTop: 2 }}>
                        Antar: {formatDateDMY(liveDasha.startDate)} →{" "}
                        {formatDateDMY(liveDasha.endDate)}
                      </div>
                      {liveDasha.pratyantarStart || liveDasha.pratyantarEnd ? (
                        <div style={{ color: MUTED, fontSize: 12, marginTop: 2 }}>
                          Pratyantar: {formatDateDMY(liveDasha.pratyantarStart)} →{" "}
                          {formatDateDMY(liveDasha.pratyantarEnd)}
                        </div>
                      ) : null}
                    </div>
                  ) : null}

                  <div
                    style={{
                      background: CARD,
                      borderRadius: 12,
                      overflow: "hidden",
                      border: "1px solid #e5e7eb",
                      width: "100%",
                    }}
                  >
                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: DASHA_GRID,
                        columnGap: 6,
                        padding: "10px 10px",
                        background: "#f3f4f6",
                        fontWeight: 700,
                        fontSize: 11,
                        color: MUTED,
                        alignItems: "center",
                      }}
                    >
                      <div style={{ textAlign: "left" }}>Planet</div>
                      <div style={{ textAlign: "center" }}>Start Date</div>
                      <div style={{ textAlign: "center" }}>End Date</div>
                      <div />
                    </div>
                    {(maha && antars.length
                      ? antars.map((a) => ({
                          planet: `${shortPlanet(maha.planet)} - ${shortPlanet(a.planet)}`,
                          startDate: formatDateDMY(a.startDate),
                          endDate: formatDateDMY(a.endDate),
                          clickable: false as const,
                          idx: -1,
                          active:
                            shortPlanet(maha.planet) === shortPlanet(liveDasha?.maha) &&
                            shortPlanet(a.planet) === shortPlanet(liveDasha?.antar),
                        }))
                      : dashas.map((d, idx) => ({
                          planet: shortPlanet(d.planet),
                          startDate: formatDateDMY(d.startDate),
                          endDate: formatDateDMY(d.endDate),
                          clickable: !!(d.subDashas && d.subDashas.length),
                          idx,
                          active: idx === liveMahaIdx,
                        }))
                    ).map((row, i) => (
                      <button
                        key={`${row.planet}-${row.startDate}-${i}`}
                        type="button"
                        disabled={!row.clickable}
                        onClick={() => {
                          if (row.clickable && row.idx >= 0) setDashaMahaIdx(row.idx);
                        }}
                        style={{
                          display: "grid",
                          gridTemplateColumns: DASHA_GRID,
                          columnGap: 6,
                          width: "100%",
                          boxSizing: "border-box",
                          padding: "11px 10px",
                          border: "none",
                          borderTop: "1px solid #e5e7eb",
                          background: row.active
                            ? "#fef3c7"
                            : i % 2
                              ? "#f9fafb"
                              : CARD,
                          boxShadow: row.active ? "inset 3px 0 0 #e11d48" : undefined,
                          cursor: row.clickable ? "pointer" : "default",
                          fontSize: 12,
                          color: TEXT,
                          alignItems: "center",
                        }}
                      >
                        <div
                          style={{
                            fontWeight: 700,
                            textAlign: "left",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                          }}
                        >
                          {row.planet || "—"}
                        </div>
                        <div
                          style={{
                            textAlign: "center",
                            fontVariantNumeric: "tabular-nums",
                            whiteSpace: "nowrap",
                            fontSize: 11,
                            letterSpacing: 0.2,
                          }}
                        >
                          {row.startDate}
                        </div>
                        <div
                          style={{
                            textAlign: "center",
                            fontVariantNumeric: "tabular-nums",
                            whiteSpace: "nowrap",
                            fontSize: 11,
                            letterSpacing: 0.2,
                          }}
                        >
                          {row.endDate}
                        </div>
                        <div style={{ color: MUTED, textAlign: "center" }}>
                          {row.clickable ? ">" : ""}
                        </div>
                      </button>
                    ))}
                  </div>

                  <button
                    type="button"
                    disabled={sharing || loading || !dashas.length}
                    onClick={() => {
                      try {
                        const person = b?.name || data?.name || c.name || "User";
                        const sectionTitle = maha
                          ? `MahaDasha > AntarDasha · ${shortPlanet(maha.planet)}`
                          : "MahaDasha";
                        const shareRows =
                          maha && antars.length
                            ? antars.map((a) => ({
                                planet: `${shortPlanet(maha.planet)} - ${shortPlanet(a.planet)}`,
                                start: formatDateDMY(a.startDate),
                                end: formatDateDMY(a.endDate),
                                active:
                                  shortPlanet(maha.planet) === shortPlanet(liveDasha?.maha) &&
                                  shortPlanet(a.planet) === shortPlanet(liveDasha?.antar),
                              }))
                            : dashas.map((d, idx) => ({
                                planet: shortPlanet(d.planet),
                                start: formatDateDMY(d.startDate),
                                end: formatDateDMY(d.endDate),
                                active: idx === liveMahaIdx,
                              }));
                        const dataUrl = renderDashaSharePngDataUrl({
                          personName: person,
                          sectionTitle,
                          current: liveDasha
                            ? {
                                maha: liveDasha.maha,
                                antar: liveDasha.antar,
                                pratyantar: liveDasha.pratyantar,
                                start: formatDateDMY(liveDasha.startDate),
                                end: formatDateDMY(liveDasha.endDate),
                                pdStart: formatDateDMY(liveDasha.pratyantarStart),
                                pdEnd: formatDateDMY(liveDasha.pratyantarEnd),
                              }
                            : null,
                          rows: shareRows,
                        });
                        onShareImage(dataUrl);
                      } catch (e) {
                        alert(e instanceof Error ? e.message : "Could not render dasha image");
                      }
                    }}
                    style={{
                      width: "100%",
                      marginTop: 14,
                      padding: "12px 14px",
                      borderRadius: 10,
                      border: "1px solid #16a34a",
                      background: "#15803d",
                      color: "#fff",
                      fontWeight: 800,
                      fontSize: 14,
                      cursor: sharing ? "wait" : "pointer",
                    }}
                  >
                    {sharing
                      ? "Sharing dasha…"
                      : maha
                        ? "Share AntarDasha to chat"
                        : "Share Dasha to chat"}
                  </button>
                  <div
                    style={{
                      marginTop: 8,
                      fontSize: 11,
                      color: MUTED,
                      textAlign: "center",
                      lineHeight: 1.4,
                    }}
                  >
                    Chat me current dasha + timeline image jayegi (dates DD-MM-YYYY)
                  </div>
                </div>
              ) : null}
            </>
          )}
        </div>
      </div>
    </div>
  );

  return createPortal(modal, document.body);
}
