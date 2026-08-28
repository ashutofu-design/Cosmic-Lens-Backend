import { CopyTextButton } from "./CopyTextButton";
import type { AdminChartPayload } from "./v3KundliPack";
import {
  POSITION_COLUMNS,
  buildPlanetPositionRows,
  formatPlanetPositionsCopyText,
} from "./v3PlanetPositions";

const PINK_HEAD = "#f49797";
const CARD = "#ffffff";
const TEXT = "#1f2937";

type Props = {
  open: boolean;
  loading: boolean;
  error: string | null;
  data: AdminChartPayload | null;
  onClose: () => void;
  onReload: () => void;
};

export function V3PositionsPanel({ open, loading, error, data, onClose, onReload }: Props) {
  if (!open) return null;

  const rows = buildPlanetPositionRows(data);
  const copyText = formatPlanetPositionsCopyText(data);

  return (
    <div
      style={{
        borderBottom: "1px solid var(--border, #2a2f3a)",
        background: "rgba(245,242,237,0.98)",
        color: TEXT,
        maxHeight: "min(52vh, 420px)",
        display: "flex",
        flexDirection: "column",
        minHeight: 0,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 10,
          padding: "10px 14px",
          borderBottom: "1px solid #e5e7eb",
          flexWrap: "wrap",
        }}
      >
        <div>
          <strong style={{ fontSize: 14 }}>Planetary Positions</strong>
          <div style={{ fontSize: 11, color: "#6b7280", marginTop: 2 }}>
            User D1 positions — Sign, Nakshatra, House, State, Status
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
          <CopyTextButton text={copyText} label="Copy All" copiedLabel="Copied!" />
          <button type="button" onClick={() => void onReload()} disabled={loading} style={{ fontSize: 12 }}>
            {loading ? "Loading…" : "Reload"}
          </button>
          <button type="button" onClick={onClose} style={{ fontSize: 12 }}>
            Close
          </button>
        </div>
      </div>

      <div style={{ flex: 1, minHeight: 0, overflow: "auto", padding: "10px 14px 14px" }}>
        {loading ? (
          <div style={{ color: "#6b7280", fontSize: 13 }}>Loading chart…</div>
        ) : error ? (
          <div style={{ color: "#b91c1c", fontSize: 13 }}>{error}</div>
        ) : rows.length === 0 ? (
          <div style={{ color: "#6b7280", fontSize: 13 }}>No planetary data for this user.</div>
        ) : (
          <div
            style={{
              borderRadius: 10,
              overflow: "auto",
              border: "1px solid #e5e7eb",
              WebkitOverflowScrolling: "touch",
            }}
          >
            <table
              style={{
                width: "100%",
                minWidth: 920,
                borderCollapse: "collapse",
                fontSize: 11,
                background: CARD,
              }}
            >
              <thead>
                <tr style={{ background: PINK_HEAD, color: "#fff" }}>
                  {POSITION_COLUMNS.map((c) => (
                    <th
                      key={c}
                      style={{
                        padding: "8px 6px",
                        fontWeight: 700,
                        textAlign: "center",
                        whiteSpace: "nowrap",
                        position: "sticky",
                        top: 0,
                        background: PINK_HEAD,
                        zIndex: 1,
                      }}
                    >
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={`${r.planet}-${i}`} style={{ background: i % 2 ? "#f9fafb" : CARD }}>
                    {[r.planet, r.sign, r.signLord, r.nakshatra, r.nakshLord, r.degree, r.retro, r.house, r.state, r.status].map(
                      (cell, j) => (
                        <td
                          key={j}
                          style={{
                            padding: "8px 6px",
                            textAlign: "center",
                            fontWeight: j === 0 ? 700 : 500,
                            borderTop: "1px solid #e5e7eb",
                            whiteSpace: "nowrap",
                          }}
                        >
                          {cell}
                        </td>
                      ),
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
