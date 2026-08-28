import { useEffect, useMemo, useRef, useState } from "react";
import {
  fetchPalmistryExport,
  fetchPalmistryMediaUrl,
  fetchPalmistryOrder,
  savePalmistryCorrection,
  API_BASE,
} from "./api";
import "./palmistryWorkspace.css";
import {
  FINGERS,
  LAYERS,
  LINE_LABELS,
  MAJOR_LINES,
  MOUNTS,
  asDict,
  asList,
  caseStatus,
  completeness,
  confBand,
  masterOf,
  metricRows,
  num,
  pointsOf,
  qualityGate,
  resolveMajorLinePath,
  scanOf,
  str,
  type Dict,
  type LayerId,
} from "./palmistryWorkspaceModel";

const NAV = [
  "Header",
  "Images",
  "Audit",
  "Quality",
  "Palm Map",
  "Geometry",
  "Landmarks",
  "Major Lines",
  "Segments",
  "Minor Lines",
  "Mounts",
  "Fingers",
  "Fingertips",
  "Thumb",
  "Wrist",
  "Markings",
  "Intersections",
  "Line-to-Mount",
  "Left vs Right",
  "Dominant",
  "Detection",
  "Confidence",
  "Validation",
  "Corrections",
  "JSON",
  "Completeness",
  "Analysis Ready",
  "Interpretation",
];
const PRODUCTION_NAV = ["Header", "Images", "Palm Map", "Major Lines", "Mounts", "Left vs Right", "Validation"] as const;

const LINE_COLORS: Record<string, string> = {
  heart_line: "#ef4444",
  head_line: "#f59e0b",
  life_line: "#22c55e",
  fate_line: "#a855f7",
  sun_apollo_line: "#06b6d4",
  mercury_line: "#eab308",
  mars_support_line: "#fb7185",
};

function Kv({ k, v }: { k: string; v: unknown }) {
  return (
    <div className="paw-kv">
      <b>{k}</b>
      <span>{v == null || v === "" ? "—" : String(v)}</span>
    </div>
  );
}

function Badge({ value }: { value: string }) {
  const cls = /fail|retake|unreliable/i.test(value)
    ? "fail"
    : /warn|partial|ambiguous|moderate/i.test(value)
      ? "warn"
      : /pass|complete|high|verified|ok/i.test(value)
        ? "ok"
        : "info";
  return <span className={`paw-badge ${cls}`}>{value}</span>;
}

function JsonBlock({ value }: { value: unknown }) {
  return <pre className="paw-json">{JSON.stringify(value, null, 2)}</pre>;
}

function ProductionSummaryCard({ order, left, right }: { order: Dict; left: Dict; right: Dict }) {
  const overallStatus = str(order.overall_scan_status || order.status, "—");
  const overallConfidence = num(order.overall_confidence);
  const leftValidation = asDict(left.production_validation);
  const rightValidation = asDict(right.production_validation);
  return (
    <div className="paw-card">
      <h2>Production summary</h2>
      <div className="paw-grid">
        <Kv k="Overall scan status" v={overallStatus} />
        <Kv k="Overall confidence" v={overallConfidence == null ? "—" : `${Math.round(overallConfidence * 100)}%`} />
        <Kv k="Writing hand" v={order.writing_hand} />
        <Kv k="Validation version" v={order.validation_version || leftValidation.validation_version || rightValidation.validation_version} />
        <Kv k="Left status" v={leftValidation.status || "—"} />
        <Kv k="Left message" v={leftValidation.user_message || "—"} />
        <Kv k="Right status" v={rightValidation.status || "—"} />
        <Kv k="Right message" v={rightValidation.user_message || "—"} />
      </div>
    </div>
  );
}

export function PalmistryAnalysisWorkspace({
  orderId,
  onClose,
}: {
  orderId: string;
  onClose: () => void;
}) {
  const [order, setOrder] = useState<Dict>({});
  const [error, setError] = useState<string | null>(null);
  const [section, setSection] = useState("Header");
  const [hand, setHand] = useState<"left" | "right">("left");
  const [layers, setLayers] = useState<Record<LayerId, boolean>>(() =>
    Object.fromEntries(LAYERS.map((layer) => [layer.id, true])) as Record<LayerId, boolean>,
  );
  const [selected, setSelected] = useState<Dict | null>(null);
  const [imageLayer, setImageLayer] = useState<
    | "original"
    | "processed"
    | "annotated"
    | "normalized"
    | "contrast-enhanced"
    | "crease-enhanced"
    | "foreground-mask"
    | "background-removed"
    | "palm-segmented"
    | "edge-map"
    | "line-map"
    | "skeleton-map"
  >("original");
  const [media, setMedia] = useState<Record<string, string>>({});
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [rotate, setRotate] = useState(0);
  const [originalOnly, setOriginalOnly] = useState(false);
  const [overlayOnly, setOverlayOnly] = useState(false);
  const [viewMode, setViewMode] = useState<"full" | "original_only" | "original_plus_raw" | "raw_only">("full");
  const [jsonQuery, setJsonQuery] = useState("");
  const [note, setNote] = useState("");
  const [phase2, setPhase2] = useState<Dict | null>(null);
  const [uiMode, setUiMode] = useState<"production" | "debug">("production");
  const mapRef = useRef<HTMLDivElement | null>(null);

  const left = useMemo(() => scanOf(order, "left"), [order]);
  const right = useMemo(() => scanOf(order, "right"), [order]);
  const scan = hand === "left" ? left : right;
  const master = masterOf(scan);
  const strictRawMode = viewMode === "original_only" || viewMode === "original_plus_raw" || viewMode === "raw_only";

  useEffect(() => {
    let alive = true;
    fetchPalmistryOrder(orderId)
      .then((row) => {
        if (alive) setOrder(row);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Load failed"));
    return () => {
      alive = false;
    };
  }, [orderId]);

  useEffect(() => {
    const names = [
      "original",
      "processed",
      "annotated",
      "normalized",
      "contrast-enhanced",
      "crease-enhanced",
      "foreground-mask",
      "background-removed",
      "palm-segmented",
      "edge-map",
      "line-map",
      "skeleton-map",
    ];
    let alive = true;
    (async () => {
      const next: Record<string, string> = {};
      for (const side of ["left", "right"] as const) {
        for (const name of names) {
          const url = await fetchPalmistryMediaUrl(orderId, side, name);
          if (url) next[`${side}:${name}`] = url;
        }
      }
      if (alive) setMedia(next);
    })();
    return () => {
      alive = false;
    };
  }, [orderId]);

  const imgSrc =
    media[`${hand}:${imageLayer}`] ||
    media[`${hand}:original`] ||
    media[`${hand}:annotated`] ||
    "";

  function toggleLayer(id: LayerId) {
    setLayers((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  function applyViewMode(mode: "full" | "original_only" | "original_plus_raw" | "raw_only") {
    setViewMode(mode);
    setImageLayer("original");
    if (mode === "full") {
      setOriginalOnly(false);
      setOverlayOnly(false);
      setLayers(Object.fromEntries(LAYERS.map((layer) => [layer.id, true])) as Record<LayerId, boolean>);
      return;
    }
    if (mode === "original_only") {
      setOriginalOnly(true);
      setOverlayOnly(false);
      setLayers(
        Object.fromEntries(
          LAYERS.map((layer) => [layer.id, layer.id === "original_image"]),
        ) as Record<LayerId, boolean>,
      );
      return;
    }
    if (mode === "original_plus_raw") {
      setOriginalOnly(false);
      setOverlayOnly(false);
      setLayers(
        Object.fromEntries(
          LAYERS.map((layer) => [
            layer.id,
            ["original_image", "raw_crease_evidence", "crease_candidates"].includes(layer.id),
          ]),
        ) as Record<LayerId, boolean>,
      );
      return;
    }
    setOriginalOnly(false);
    setOverlayOnly(true);
    setLayers(
      Object.fromEntries(
        LAYERS.map((layer) => [layer.id, ["raw_crease_evidence", "crease_candidates"].includes(layer.id)]),
      ) as Record<LayerId, boolean>,
    );
  }

  async function correct(action: string) {
    try {
      const updated = await savePalmistryCorrection(orderId, {
        action,
        changed_by: "admin",
        reason: note,
        hand_side: hand,
        feature_path: selected?.path || selected?.kind,
        feature_id: selected?.id || selected?.name,
        machine_original: selected,
        human_corrected: { action, note },
      });
      setOrder((prev) => ({
        ...prev,
        correction_history: updated.correction_history,
        human_overlays: updated.human_overlays,
        status: updated.status,
      }));
      setNote("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Correction failed");
    }
  }

  async function downloadExport() {
    const pack = await fetchPalmistryExport(orderId);
    const blob = new Blob([JSON.stringify(pack, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `palmistry-${orderId}.json`;
    a.click();
  }

  async function loadPhase2() {
    const res = await fetch(`${API_BASE}/api/palm-reading/interpret-bilateral`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        left_palm_scan_result: stripMaster(left),
        right_palm_scan_result: stripMaster(right),
        writing_hand: order.writing_hand || "right",
      }),
    });
    setPhase2(await res.json());
  }

  const jsonText = JSON.stringify(order, null, 2);
  const jsonView = jsonQuery
    ? jsonText
        .split("\n")
        .filter((line) => line.toLowerCase().includes(jsonQuery.toLowerCase()))
        .join("\n")
    : jsonText;

  const leftComplete = completeness(left);
  const rightComplete = completeness(right);
  const status = caseStatus(order, left, right);
  const q = qualityGate(scan);
  const navItems = uiMode === "debug" ? NAV : PRODUCTION_NAV;

  return (
    <div className="paw">
      <header className="paw-top">
        <button type="button" onClick={onClose}>Close</button>
        <h1>Palmistry Analysis Data</h1>
        <span className="muted">{orderId}</span>
        <Badge value={status} />
        <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
          <button type="button" className={uiMode === "production" ? "primary" : ""} onClick={() => { setUiMode("production"); if (!PRODUCTION_NAV.includes(section as typeof PRODUCTION_NAV[number])) setSection("Header"); }}>
            Production View
          </button>
          <button type="button" className={uiMode === "debug" ? "primary" : ""} onClick={() => setUiMode("debug")}>
            Developer Debug
          </button>
          <button type="button" className="primary" onClick={() => void downloadExport()}>
            Export package
          </button>
        </div>
      </header>
      <nav className="paw-nav">
        {navItems.map((item) => (
          <button
            key={item}
            type="button"
            className={section === item ? "active" : ""}
            onClick={() => setSection(item)}
          >
            {item}
          </button>
        ))}
      </nav>
      <main className="paw-main">
        {error ? <div className="error">{error}</div> : null}
        {uiMode === "production" ? <ProductionSummaryCard order={order} left={left} right={right} /> : null}
        <div className="paw-actions">
          <button type="button" className={hand === "left" ? "primary" : ""} onClick={() => setHand("left")}>Left hand</button>
          <button type="button" className={hand === "right" ? "primary" : ""} onClick={() => setHand("right")}>Right hand</button>
        </div>

        {section === "Header" ? (
          <div className="paw-card">
            <h2>Case / person</h2>
            <div className="paw-grid">
              <Kv k="Case ID" v={order.order_id} />
              <Kv k="User ID" v={order.user_id} />
              <Kv k="User reference" v={order.cosmo_user_id || order.user_name} />
              <Kv k="Session / scan ID" v={order.session_id} />
              <Kv k="Scan date/time" v={order.created_at} />
              <Kv k="Left uploaded" v={Object.keys(left).length ? "yes" : "no"} />
              <Kv k="Right uploaded" v={Object.keys(right).length ? "yes" : "no"} />
              <Kv k="Dominant / writing hand" v={order.writing_hand} />
              <Kv k="Non-dominant" v={order.writing_hand === "left" ? "right" : "left"} />
              <Kv k="Scanner version" v={asDict(left.metadata).engine || order.extraction_engine} />
              <Kv k="Schema version" v={left.schema_version || order.extraction_schema} />
              <Kv k="Extraction engine" v={order.extraction_engine} />
              <Kv k="Master schema" v={order.master_schema} />
              <Kv k="Rule engine version" v={order.rule_engine_version} />
              <Kv k="Overall status" v={status} />
              <Kv k="Data completeness" v={`${Math.round((leftComplete.pct + rightComplete.pct) / 2)}%`} />
              <Kv k="Overall confidence" v={str(asDict(left.scan_confidence).overall) + " / " + str(asDict(right.scan_confidence).overall)} />
            </div>
          </div>
        ) : null}

        {section === "Images" ? (
          <div className="paw-split">
            {(["left", "right"] as const).map((side) => (
              <div className="paw-card" key={side}>
                <h3>{side.toUpperCase()} original</h3>
                <div className="paw-actions">
                  <button type="button" onClick={() => setImageLayer("original")}>Original</button>
                  <button type="button" onClick={() => setImageLayer("processed")}>Processed layer</button>
                  <button type="button" onClick={() => setImageLayer("normalized")}>Normalized</button>
                  <button type="button" onClick={() => setImageLayer("background-removed")}>Background removed</button>
                  <button type="button" onClick={() => setImageLayer("palm-segmented")}>Palm segmented</button>
                  <button type="button" onClick={() => setImageLayer("contrast-enhanced")}>Contrast</button>
                  <button type="button" onClick={() => setImageLayer("crease-enhanced")}>Crease</button>
                  <button type="button" onClick={() => setImageLayer("edge-map")}>Edge map</button>
                  <button type="button" onClick={() => setImageLayer("line-map")}>Line map</button>
                  <button type="button" onClick={() => setImageLayer("skeleton-map")}>Skeleton</button>
                  <button type="button" onClick={() => setImageLayer("annotated")}>Annotated</button>
                  <a href={media[`${side}:original`] || "#"} download={`${side}-original.png`}>Download original</a>
                </div>
                {media[`${side}:original`] ? (
                  <img src={media[`${side}:original`]} alt={`${side} original`} style={{ width: "100%", borderRadius: 12 }} />
                ) : (
                  <p className="muted">Original image not persisted yet. Coordinates remain in JSON.</p>
                )}
                <p className="muted">Processed/annotated are extra layers. Original is never replaced.</p>
              </div>
            ))}
          </div>
        ) : null}

        {uiMode === "debug" && section === "Audit" ? (
          <AuditCard order={order} left={left} right={right} />
        ) : null}

        {uiMode === "debug" && section === "Quality" ? (
          <div className="paw-card">
            <h2>{hand.toUpperCase()} image quality</h2>
            <Badge value={q.label} />
            <ul>{q.reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul>
            <div className="paw-grid">
              {metricRows(scan).map((row) => <Kv key={row.key} k={row.key} v={row.value} />)}
            </div>
          </div>
        ) : null}

        {section === "Palm Map" ? (
          <div className="paw-card">
            <h2>Interactive palm map — {hand}</h2>
            <div className="paw-actions">
              <button type="button" onClick={() => setZoom((z) => Math.min(4, z + 0.2))}>Zoom +</button>
              <button type="button" onClick={() => setZoom((z) => Math.max(0.4, z - 0.2))}>Zoom -</button>
              <button type="button" onClick={() => setRotate((r) => r + 90)}>Rotate</button>
              <button type="button" className={viewMode === "original_only" ? "primary" : ""} onClick={() => applyViewMode("original_only")}>
                Original only
              </button>
              <button type="button" className={viewMode === "original_plus_raw" ? "primary" : ""} onClick={() => applyViewMode("original_plus_raw")}>
                Original + Raw Crease
              </button>
              <button type="button" className={viewMode === "raw_only" ? "primary" : ""} onClick={() => applyViewMode("raw_only")}>
                Raw Crease Only
              </button>
              <button type="button" className={viewMode === "full" ? "primary" : ""} onClick={() => applyViewMode("full")}>
                Full Debug
              </button>
              <button type="button" onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); setRotate(0); }}>Reset</button>
              <button type="button" onClick={() => mapRef.current?.requestFullscreen()}>Fullscreen</button>
              <select value={imageLayer} onChange={(e) => setImageLayer(e.target.value as typeof imageLayer)} disabled={strictRawMode}>
                <option value="original">Original resolution</option>
                <option value="processed">Processed</option>
                <option value="normalized">Normalized</option>
                <option value="background-removed">Background removed</option>
                <option value="palm-segmented">Palm segmented</option>
                <option value="contrast-enhanced">Contrast enhanced</option>
                <option value="crease-enhanced">Crease enhanced</option>
                <option value="edge-map">Edge map</option>
                <option value="line-map">Line map</option>
                <option value="skeleton-map">Skeleton map</option>
                <option value="annotated">Annotated</option>
              </select>
            </div>
            <div className="paw-layers">
              {LAYERS.map((layer) => (
                <label key={layer.id}>
                  <input
                    type="checkbox"
                    checked={layers[layer.id]}
                    disabled={
                      strictRawMode &&
                      !["original_image", "raw_crease_evidence", "crease_candidates"].includes(layer.id)
                    }
                    onChange={() => toggleLayer(layer.id)}
                  />
                  {layer.label}
                </label>
              ))}
            </div>
            <div
              className="paw-map"
              ref={mapRef}
              onMouseDown={(event) => {
                const start = { x: event.clientX - pan.x, y: event.clientY - pan.y };
                const move = (ev: MouseEvent) => setPan({ x: ev.clientX - start.x, y: ev.clientY - start.y });
                const up = () => {
                  window.removeEventListener("mousemove", move);
                  window.removeEventListener("mouseup", up);
                };
                window.addEventListener("mousemove", move);
                window.addEventListener("mouseup", up);
              }}
            >
              <div style={{ transform: `translate(${pan.x}px,${pan.y}px) scale(${zoom}) rotate(${rotate}deg)`, transformOrigin: "center", width: "100%", height: "100%", position: "absolute" }}>
                {!overlayOnly && layers.original_image && imgSrc ? <img src={imgSrc} alt={`${hand} palm`} /> : null}
                {!originalOnly && layers.raw_crease_evidence && (media[`${hand}:line-map`] || media[`${hand}:edge-map`]) ? (
                  <img
                    src={media[`${hand}:line-map`] || media[`${hand}:edge-map`] || ""}
                    alt={`${hand} raw crease evidence`}
                    className="paw-evidence"
                  />
                ) : null}
                {!originalOnly ? (
                  <PalmOverlay
                    scan={scan}
                    master={master}
                    imageLayer={imageLayer}
                    layers={layers}
                    selected={selected}
                    onSelect={setSelected}
                  />
                ) : null}
              </div>
            </div>
            <TransformDebugCard scan={scan} imageLayer={imageLayer} rotate={rotate} />
            {viewMode === "original_plus_raw" ? (
              <p className="muted">
                Visual audit mode: original photo plus IMAGE_PIXELS crease evidence only. If highlighted paths do not sit on visible skin creases, mark this as <b>CREASE EXTRACTION FAILED</b>.
              </p>
            ) : null}
          </div>
        ) : null}

        {uiMode === "debug" && section === "Geometry" ? <GeometryCard scan={scan} /> : null}
        {uiMode === "debug" && section === "Landmarks" ? <LandmarkCard scan={scan} onSelect={setSelected} selected={selected} /> : null}
        {section === "Major Lines" ? <MajorLineCards scan={scan} master={master} onSelect={setSelected} /> : null}
        {uiMode === "debug" && section === "Segments" ? <SegmentCard master={master} onSelect={setSelected} /> : null}
        {uiMode === "debug" && section === "Minor Lines" ? <MinorCard master={master} scan={scan} /> : null}
        {section === "Mounts" ? <MountCard scan={scan} master={master} onSelect={setSelected} /> : null}
        {uiMode === "debug" && section === "Fingers" ? <FingerCard scan={scan} /> : null}
        {uiMode === "debug" && section === "Fingertips" ? <TipCard master={master} scan={scan} /> : null}
        {uiMode === "debug" && section === "Thumb" ? <ThumbCard scan={scan} /> : null}
        {uiMode === "debug" && section === "Wrist" ? <WristCard master={master} scan={scan} /> : null}
        {uiMode === "debug" && section === "Markings" ? <MarkingTable scan={scan} hand={hand} master={master} onSelect={setSelected} /> : null}
        {uiMode === "debug" && section === "Intersections" ? <RelationTable master={master} onSelect={setSelected} /> : null}
        {uiMode === "debug" && section === "Line-to-Mount" ? <LineMountCard master={master} scan={scan} /> : null}
        {section === "Left vs Right" ? <CompareCard left={left} right={right} comparison={asDict(order.bilateral_comparison)} /> : null}
        {uiMode === "debug" && section === "Dominant" ? (
          <div className="paw-card">
            <h2>Dominant / non-dominant — raw comparison only</h2>
            <p>Writing hand declared by user: {str(order.writing_hand)}. Phase 2 interpretation is not applied here.</p>
            <JsonBlock value={asDict(order.bilateral_comparison).dominant_hand_data} />
            <JsonBlock value={asDict(order.bilateral_comparison).non_dominant_hand_data} />
          </div>
        ) : null}
        {uiMode === "debug" && section === "Detection" ? <DetectionCard scan={scan} master={master} /> : null}
        {uiMode === "debug" && section === "Confidence" ? <ConfidenceCard scan={scan} master={master} /> : null}
        {section === "Validation" ? <ValidationCard scan={scan} order={order} /> : null}
        {uiMode === "debug" && section === "Corrections" ? (
          <div className="paw-card">
            <h2>Human verification history</h2>
            <p>Machine originals are preserved. Corrections append; they do not overwrite extraction JSON.</p>
            <JsonBlock value={order.correction_history || []} />
          </div>
        ) : null}
        {uiMode === "debug" && section === "JSON" ? (
          <div className="paw-card">
            <h2>Raw PalmScanResult</h2>
            <input value={jsonQuery} onChange={(e) => setJsonQuery(e.target.value)} placeholder="Search JSON" />
            <div className="paw-actions">
              <button type="button" onClick={() => navigator.clipboard.writeText(jsonText)}>Copy JSON</button>
              <button type="button" onClick={() => void downloadExport()}>Download export</button>
            </div>
            <pre className="paw-json">{jsonView}</pre>
          </div>
        ) : null}
        {uiMode === "debug" && section === "Completeness" ? (
          <div className="paw-split">
            {(["left", "right"] as const).map((side) => {
              const pack = completeness(side === "left" ? left : right);
              return (
                <div className="paw-card" key={side}>
                  <h3>{side.toUpperCase()} checklist — {pack.pct}%</h3>
                  {pack.items.map((item) => (
                    <div key={item.id}>{item.ok ? "✓" : "○"} {item.id}</div>
                  ))}
                </div>
              );
            })}
          </div>
        ) : null}
        {uiMode === "debug" && section === "Analysis Ready" ? (
          <AnalysisReady left={left} right={right} comparison={asDict(order.bilateral_comparison)} />
        ) : null}
        {uiMode === "debug" && section === "Interpretation" ? (
          <div className="paw-card">
            <h2>Phase 2 interpretation — separate from extraction</h2>
            <p>Raw measurements stay above. This block only loads traditional rule output on demand.</p>
            <button type="button" className="primary" onClick={() => void loadPhase2()}>Load Phase 2 interpretation</button>
            {phase2 ? <JsonBlock value={phase2} /> : <p className="muted">Not loaded. Extraction is unaffected.</p>}
          </div>
        ) : null}
      </main>
      {uiMode === "debug" ? <aside className="paw-side">
        <h3>Feature inspector</h3>
        {selected ? (
          <>
            <div className="paw-grid">
              <Kv k="What" v={str(selected.kind || selected.type || selected.name)} />
              <Kv k="Hand" v={hand} />
              <Kv k="ID" v={str(selected.id || selected.marking_id || selected.name)} />
              <Kv k="x" v={selected.x} />
              <Kv k="y" v={selected.y} />
              <Kv k="normalized x" v={selected.normalized_x ?? selected.x} />
              <Kv k="normalized y" v={selected.normalized_y ?? selected.y} />
              <Kv k="region" v={selected.region} />
              <Kv k="confidence" v={`${selected.confidence} (${confBand(selected.confidence)})`} />
              <Kv k="status" v={selected.status} />
              <Kv k="method" v={selected.method || selected.detection_method} />
            </div>
            <JsonBlock value={selected} />
            <textarea className="paw-note" value={note} onChange={(e) => setNote(e.target.value)} placeholder="Correction reason" />
            <div className="paw-actions">
              <button type="button" onClick={() => void correct("confirm")}>Confirm</button>
              <button type="button" onClick={() => void correct("reject")}>Reject</button>
              <button type="button" onClick={() => void correct("ambiguous")}>Ambiguous</button>
              <button type="button" onClick={() => void correct("correct")}>Correct / note</button>
            </div>
          </>
        ) : (
          <p className="muted">Click a landmark, line, mount, or marking on the map or in a table.</p>
        )}
      </aside> : null}
    </div>
  );
}

function stripMaster(scan: Dict): Dict {
  const copy = { ...scan };
  delete copy.master_extraction;
  delete copy.admin_session;
  return copy;
}

function PalmOverlay({
  scan,
  master,
  imageLayer,
  layers,
  selected,
  onSelect,
}: {
  scan: Dict;
  master: Dict;
  imageLayer: string;
  layers: Record<LayerId, boolean>;
  selected: Dict | null;
  onSelect: (value: Dict) => void;
}) {
  const landmarks = asList(scan.landmarks).map((item) => asDict(item));
  const lines = asDict(scan.major_lines);
  const mounts = asDict(scan.mounts);
  const segs = asDict(scan.segmentation);
  const markings = asList(asDict(scan.special_markings).candidates).map((item) => asDict(item));
  const micro = asList(master.line_micro_features).map((item) => asDict(item));
  const creaseCandidates = asList(asDict(scan.secondary_lines).crease_candidates).map((item) => asDict(item));
  const relationships = asList(master.line_relationships).map((item) => asDict(item));
  const geom = asDict(scan.palm_geometry);
  const center = asList(asDict(geom.center).normalized).map((item) => num(item) ?? 0);
  const acceptedCandidateIds = new Set(
    MAJOR_LINES
      .map((name) => str(asDict(lines[name]).source_candidate_id, ""))
      .filter((value) => value && value !== "—"),
  );
  const rejectedCandidates = creaseCandidates.filter((row) => {
    return str(row.audit_status) === "rejected";
  });
  const ambiguousCandidates = creaseCandidates.filter((row) => {
    return str(row.audit_status) === "ambiguous";
  });
  const unresolvedCandidates = creaseCandidates.filter((row) => {
    return str(row.audit_status) === "missed_or_unresolved";
  });
  const acceptedCandidates = creaseCandidates.filter((row) => {
    return str(row.audit_status) === "accepted";
  });

  function displayPoints(points: { x: number; y: number }[]) {
    return points
      .map((point) => mapPointToDisplay(scan, point, imageLayer))
      .filter((point): point is { x: number; y: number } => point != null);
  }

  function poly(points: { x: number; y: number }[], key: string, color: string, payload: Dict) {
    const shown = displayPoints(points);
    points = shown;
    if (points.length < 2) return null;
    const d = points.map((p, i) => `${i ? "L" : "M"} ${p.x * 1000} ${p.y * 1000}`).join(" ");
    const active = selected && (selected.name === payload.name || selected.id === payload.id);
    return (
      <path
        key={key}
        d={d}
        fill="none"
        stroke={color}
        strokeWidth={active ? 8 : 4}
        onClick={(e) => {
          e.stopPropagation();
          onSelect(payload);
        }}
      />
    );
  }

  return (
    <svg viewBox="0 0 1000 1000" preserveAspectRatio="xMidYMid meet">
      {layers.grid
        ? Array.from({ length: 10 }, (_, i) => (
            <g key={i} stroke="rgba(255,255,255,0.12)" strokeWidth="1">
              <line x1={i * 100} y1={0} x2={i * 100} y2={1000} />
              <line x1={0} y1={i * 100} x2={1000} y2={i * 100} />
            </g>
          ))
        : null}
      {layers.hand_boundary ? poly(pointsOf(asDict(segs.hand_boundary).polygon), "hand", "#94a3b8", { kind: "hand_boundary", ...asDict(segs.hand_boundary) }) : null}
      {layers.palm_boundary ? poly(pointsOf(asDict(segs.palm_region).polygon), "palm", "#e2e8f0", { kind: "palm_boundary", ...asDict(segs.palm_region) }) : null}
      {layers.wrist ? poly(pointsOf(asDict(segs.wrist).polygon), "wrist", "#67e8f9", { kind: "wrist", ...asDict(segs.wrist) }) : null}
      {layers.hand_geometry
        ? [
            poly(pointsOf(asDict(segs.hand_boundary).polygon), "hand-geometry-boundary", "#64748b", { kind: "hand_geometry", ...asDict(segs.hand_boundary) }),
            poly(pointsOf(asDict(segs.palm_region).polygon), "hand-geometry-palm", "#cbd5e1", { kind: "hand_geometry", ...asDict(segs.palm_region) }),
            poly(pointsOf(asDict(segs.wrist).polygon), "hand-geometry-wrist", "#38bdf8", { kind: "hand_geometry", ...asDict(segs.wrist) }),
          ]
        : null}
      {layers.palm_center && center.length === 2 ? (
        (() => {
          const point = mapPointToDisplay(scan, { x: center[0], y: center[1] }, imageLayer);
          return point ? <circle cx={point.x * 1000} cy={point.y * 1000} r="8" fill="#f8fafc" /> : null;
        })()
      ) : null}
      {layers.mounts
        ? Object.entries(mounts).map(([name, value]) =>
            poly(pointsOf(asDict(value).region_polygon), `mount-${name}`, "#c084fc", {
              kind: "mount",
              name,
              ...asDict(value),
            }),
          )
        : null}
      {layers.major_lines
        ? MAJOR_LINES.map((name) => {
            const linePath = resolveMajorLinePath(scan, name);
            if (linePath.length < 2) return null;
            return poly(linePath, name, LINE_COLORS[name] || "#fff", {
              kind: "major_line",
              name,
              ...asDict(lines[name]),
              path: linePath,
            });
          })
        : null}
      {layers.accepted_crease_paths
        ? acceptedCandidates.map((row, index) =>
            poly(pointsOf(row.path), `accepted-${index}`, "#22c55e", {
              kind: "accepted_crease_candidate",
              id: row.id || `accepted_${index}`,
              final_status: "accepted",
              ...row,
            }),
          )
        : null}
      {layers.crease_candidates
        ? creaseCandidates.map((row, index) =>
            poly(pointsOf(row.path), `crease-${index}`, "#f59e0b", {
              kind: "crease_candidate",
              id: row.id || `candidate_${index}`,
              ...row,
            }),
          )
        : null}
      {layers.rejected_candidates
        ? rejectedCandidates.map((row, index) =>
            poly(pointsOf(row.path), `rejected-${index}`, "#ef4444", {
              kind: "rejected_candidate",
              id: row.id || `rejected_${index}`,
              final_status: "rejected",
              ...row,
            }),
          )
        : null}
      {layers.rejected_candidates
        ? ambiguousCandidates.map((row, index) =>
            poly(pointsOf(row.path), `ambiguous-${index}`, "#facc15", {
              kind: "ambiguous_candidate",
              id: row.id || `ambiguous_${index}`,
              final_status: "ambiguous",
              ...row,
            }),
          )
        : null}
      {layers.rejected_candidates
        ? unresolvedCandidates.map((row, index) =>
            poly(pointsOf(row.path), `unresolved-${index}`, "#fb7185", {
              kind: "missed_or_unresolved_candidate",
              id: row.id || `unresolved_${index}`,
              final_status: "missed_or_unresolved",
              ...row,
            }),
          )
        : null}
      {layers.landmarks || layers.fingers || layers.thumb
        ? landmarks.map((lm) => {
            const raw = mapPointToDisplay(scan, { x: num(lm.x) || 0, y: num(lm.y) || 0 }, imageLayer);
            if (!raw) return null;
            const x = raw.x * 1000;
            const y = raw.y * 1000;
            const id = Number(lm.id);
            const isThumb = id >= 1 && id <= 4;
            const isFinger = id >= 5;
            if (isThumb && !layers.thumb && !layers.landmarks) return null;
            if (isFinger && !layers.fingers && !layers.landmarks) return null;
            if (!isThumb && !isFinger && !layers.landmarks) return null;
            return (
              <circle
                key={String(lm.id)}
                cx={x}
                cy={y}
                r={selected && selected.id === lm.id ? 10 : 5}
                fill="#4ade80"
                onClick={(e) => {
                  e.stopPropagation();
                  onSelect({ kind: "landmark", ...lm });
                }}
              />
            );
          })
        : null}
      {layers.hand_geometry
        ? [
            [0, 1, 2, 3, 4],
            [0, 5, 6, 7, 8],
            [0, 9, 10, 11, 12],
            [0, 13, 14, 15, 16],
            [0, 17, 18, 19, 20],
          ].map((chain, index) =>
            poly(
              displayPoints(
                chain
                  .map((id) => landmarks.find((row) => Number(row.id) === id))
                  .filter((item): item is Dict => Boolean(item))
                  .map((item) => ({ x: num(item.x) || 0, y: num(item.y) || 0 })),
              ),
              `geom-chain-${index}`,
              "#60a5fa",
              { kind: "hand_geometry_chain", chain },
            ),
          )
        : null}
      {layers.micro
        ? micro.map((item, i) => {
            const c = asDict(item.coordinates);
            const raw = mapPointToDisplay(scan, { x: num(c.x) || 0, y: num(c.y) || 0 }, imageLayer);
            if (!raw) return null;
            const x = raw.x * 1000;
            const y = raw.y * 1000;
            return (
              <rect
                key={`micro-${i}`}
                x={x - 6}
                y={y - 6}
                width="12"
                height="12"
                fill="#fbbf24"
                onClick={(e) => {
                  e.stopPropagation();
                  onSelect({ kind: "micro_feature", ...item });
                }}
              />
            );
          })
        : null}
      {layers.intersections
        ? relationships.map((item, i) => {
            const coords = asDict(item.coordinates);
            const mapped = mapPointToDisplay(scan, { x: num(coords.x) || 0, y: num(coords.y) || 0 }, imageLayer);
            if (num(coords.x) == null || num(coords.y) == null || !mapped) return null;
            const x = mapped.x * 1000;
            const y = mapped.y * 1000;
            return (
              <circle
                key={`intersection-${i}`}
                cx={x}
                cy={y}
                r={selected && selected.relationship === item.relationship ? 10 : 6}
                fill="#22d3ee"
                onClick={(e) => {
                  e.stopPropagation();
                  onSelect({ kind: "line_relationship", ...item, ...coords });
                }}
              />
            );
          })
        : null}
      {layers.markings
        ? markings.map((item, i) => {
            const coords = asList(item.coordinates);
            const point = asDict(coords[0] || item.location || item);
            const mapped = mapPointToDisplay(scan, { x: num(point.x) || 0, y: num(point.y) || 0 }, imageLayer);
            if (!mapped) return null;
            const x = mapped.x * 1000;
            const y = mapped.y * 1000;
            return (
              <polygon
                key={`mk-${i}`}
                points={`${x},${y - 8} ${x + 8},${y + 6} ${x - 8},${y + 6}`}
                fill="#fb7185"
                onClick={(e) => {
                  e.stopPropagation();
                  onSelect({ kind: "marking", ...item, x: point.x, y: point.y });
                }}
              />
            );
          })
        : null}
    </svg>
  );
}

function mapPointToDisplay(scan: Dict, point: { x: number; y: number }, imageLayer: string) {
  if (imageLayer !== "original") return point;
  const prep = asDict(scan.preprocessing);
  const stages = asDict(prep.stages);
  const resolution = asDict(stages.resolution_normalization);
  const perspective = asDict(stages.perspective_normalization);
  const inputSize = asList(resolution.input_size).map((item) => num(item) ?? 0);
  const outputSize = asList(resolution.output_size).map((item) => num(item) ?? 0);
  const scale = num(resolution.scale) ?? 1;
  const matrixRows = asList(perspective.homography).map((row) => asList(row).map((item) => num(item) ?? 0));
  if (inputSize.length !== 2 || outputSize.length !== 2 || matrixRows.length !== 3) {
    return point;
  }
  const widthOut = outputSize[0] || 1;
  const heightOut = outputSize[1] || 1;
  const widthIn = inputSize[0] || widthOut;
  const heightIn = inputSize[1] || heightOut;
  const matrix = matrixRows.map((row) => [row[0] || 0, row[1] || 0, row[2] || 0]);
  const det =
    matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[1][2] * matrix[2][1]) -
    matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[1][2] * matrix[2][0]) +
    matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[1][1] * matrix[2][0]);
  if (!Number.isFinite(det) || Math.abs(det) < 1e-9) return point;
  const inv = invert3x3(matrix);
  if (!inv) return point;
  const x = point.x * widthOut;
  const y = point.y * heightOut;
  const w = inv[2][0] * x + inv[2][1] * y + inv[2][2];
  if (!Number.isFinite(w) || Math.abs(w) < 1e-9) return point;
  const nx = (inv[0][0] * x + inv[0][1] * y + inv[0][2]) / w;
  const ny = (inv[1][0] * x + inv[1][1] * y + inv[1][2]) / w;
  const ox = nx / Math.max(scale, 1e-9);
  const oy = ny / Math.max(scale, 1e-9);
  return {
    x: Math.min(1, Math.max(0, ox / widthIn)),
    y: Math.min(1, Math.max(0, oy / heightIn)),
  };
}

function invert3x3(m: number[][]) {
  const det =
    m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1]) -
    m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0]) +
    m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0]);
  if (!Number.isFinite(det) || Math.abs(det) < 1e-9) return null;
  const invDet = 1 / det;
  return [
    [
      (m[1][1] * m[2][2] - m[1][2] * m[2][1]) * invDet,
      (m[0][2] * m[2][1] - m[0][1] * m[2][2]) * invDet,
      (m[0][1] * m[1][2] - m[0][2] * m[1][1]) * invDet,
    ],
    [
      (m[1][2] * m[2][0] - m[1][0] * m[2][2]) * invDet,
      (m[0][0] * m[2][2] - m[0][2] * m[2][0]) * invDet,
      (m[0][2] * m[1][0] - m[0][0] * m[1][2]) * invDet,
    ],
    [
      (m[1][0] * m[2][1] - m[1][1] * m[2][0]) * invDet,
      (m[0][1] * m[2][0] - m[0][0] * m[2][1]) * invDet,
      (m[0][0] * m[1][1] - m[0][1] * m[1][0]) * invDet,
    ],
  ];
}

function TransformDebugCard({ scan, imageLayer, rotate }: { scan: Dict; imageLayer: string; rotate: number }) {
  const prep = asDict(scan.preprocessing);
  const stages = asDict(prep.stages);
  const res = asDict(stages.resolution_normalization);
  const perspective = asDict(stages.perspective_normalization);
  const inputSize = asList(res.input_size);
  const outputSize = asList(res.output_size);
  const usingOriginal = imageLayer === "original";
  return (
    <div className="paw-card">
      <h3>Transform debug</h3>
      <div className="paw-grid">
        <Kv k="base layer" v={imageLayer} />
        <Kv k="original image dimensions" v={`${str(inputSize[0])} × ${str(inputSize[1])}`} />
        <Kv k="display dimensions" v={usingOriginal ? `${str(inputSize[0])} × ${str(inputSize[1])}` : `${str(outputSize[0])} × ${str(outputSize[1])}`} />
        <Kv k="scale X" v={res.scale ?? 1} />
        <Kv k="scale Y" v={res.scale ?? 1} />
        <Kv k="rotation" v={`${rotate}deg`} />
        <Kv k="crop offset" v="0, 0" />
        <Kv k="transform status" v={usingOriginal ? "inverse_homography_to_original" : "processed_space_identity"} />
        <Kv k="perspective status" v={perspective.status} />
      </div>
    </div>
  );
}

function GeometryCard({ scan }: { scan: Dict }) {
  const g = asDict(scan.palm_geometry);
  return (
    <div className="paw-card">
      <h2>Palm geometry — raw and normalized</h2>
      <div className="paw-grid">
        <Kv k="length raw px" v={asDict(g.length).raw_px} />
        <Kv k="length normalized" v={asDict(g.length).normalized} />
        <Kv k="width raw px" v={asDict(g.width).raw_px} />
        <Kv k="width normalized" v={asDict(g.width).normalized} />
        <Kv k="area raw" v={asDict(g.area).raw_px2} />
        <Kv k="area normalized" v={asDict(g.area).normalized} />
        <Kv k="perimeter raw" v={asDict(g.perimeter).raw_px} />
        <Kv k="perimeter normalized" v={asDict(g.perimeter).normalized} />
        <Kv k="aspect ratio" v={asDict(g.aspect_ratio).raw_ratio} />
        <Kv k="wrist width" v={asDict(g.wrist_width).raw_px} />
        <Kv k="palm center" v={JSON.stringify(asDict(g.center).normalized)} />
        <Kv k="palm axis" v={JSON.stringify(asDict(g.palm_axis))} />
        <Kv k="orientation" v={JSON.stringify(asDict(g.orientation))} />
        <Kv k="shape classification" v={asDict(g.overall_shape).classification} />
        <Kv k="shape confidence" v={asDict(g.overall_shape).confidence} />
      </div>
      <JsonBlock value={g} />
    </div>
  );
}

function LandmarkCard({ scan, onSelect, selected }: { scan: Dict; onSelect: (v: Dict) => void; selected: Dict | null }) {
  const rows = asList(scan.landmarks).map((item) => asDict(item));
  return (
    <div className="paw-card">
      <h2>Landmarks</h2>
      <table className="paw-table">
        <thead>
          <tr>
            <th>ID</th><th>name</th><th>x</th><th>y</th><th>nx</th><th>ny</th><th>px</th><th>py</th><th>conf</th><th>method</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={String(row.id)} className={selected && selected.id === row.id ? "active" : ""} onClick={() => onSelect({ kind: "landmark", ...row })}>
              <td>{str(row.id)}</td>
              <td>{str(row.name)}</td>
              <td>{str(row.x)}</td>
              <td>{str(row.y)}</td>
              <td>{str(row.normalized_x)}</td>
              <td>{str(row.normalized_y)}</td>
              <td>{str(row.x_px || row.x_pixel)}</td>
              <td>{str(row.y_px || row.y_pixel)}</td>
              <td>{str(row.confidence)} {confBand(row.confidence)}</td>
              <td>{str(row.coordinate_space || row.method)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MajorLineCards({ scan, master, onSelect }: { scan: Dict; master: Dict; onSelect: (v: Dict) => void }) {
  const lines = asDict(scan.major_lines);
  const micros = asList(master.line_micro_features).map((item) => asDict(item));
  return (
    <div>
      {MAJOR_LINES.map((name) => {
        const line = asDict(lines[name]);
        const kids = micros.filter((item) => item.parent_line === name);
        return (
          <div className="paw-card" key={name}>
            <h3>{LINE_LABELS[name]}</h3>
            <div className="paw-grid">
              <Kv k="detected" v={line.detected ?? line.status} />
              <Kv k="status" v={line.status} />
              <Kv k="confidence" v={`${line.confidence} (${confBand(line.confidence)})`} />
              <Kv k="methods" v={JSON.stringify(line.methods)} />
              <Kv k="source candidate" v={line.source_candidate_id} />
              <Kv k="source layer" v={line.source_layer} />
              <Kv k="classification confidence" v={line.classification_confidence} />
              <Kv k="start" v={JSON.stringify(line.start_point)} />
              <Kv k="end" v={JSON.stringify(line.end_point)} />
              <Kv k="length" v={line.length} />
              <Kv k="normalized length" v={line.normalized_length} />
              <Kv k="thickness" v={line.thickness} />
              <Kv k="visibility_strength" v={line.visibility_strength || line.clarity} />
              <Kv k="curvature" v={line.curvature} />
              <Kv k="direction" v={line.direction} />
              <Kv k="continuity" v={line.continuity} />
            </div>
            <p>Path coordinates (not simplified):</p>
            <JsonBlock value={resolveMajorLinePath(scan, name)} />
            <p>Path point count: {resolveMajorLinePath(scan, name).length}</p>
            <h4>Raw crease evidence</h4>
            <JsonBlock value={line.raw_crease_evidence || {}} />
            <button type="button" onClick={() => onSelect({ kind: "major_line", name, ...line })}>Inspect on map</button>
            <h4>Micro-features</h4>
            <table className="paw-table">
              <thead><tr><th>ID</th><th>type</th><th>x</th><th>y</th><th>size</th><th>parent</th><th>conf</th></tr></thead>
              <tbody>
                {kids.map((item) => (
                  <tr key={str(item.marking_id)} onClick={() => onSelect({ kind: "micro_feature", ...item })}>
                    <td>{str(item.marking_id)}</td>
                    <td>{str(item.type)}</td>
                    <td>{str(asDict(item.coordinates).x)}</td>
                    <td>{str(asDict(item.coordinates).y)}</td>
                    <td>{str(item.size)}</td>
                    <td>{str(item.parent_line)}</td>
                    <td>{str(item.confidence)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
      })}
    </div>
  );
}

function SegmentCard({ master, onSelect }: { master: Dict; onSelect: (v: Dict) => void }) {
  const segs = asDict(master.line_segments);
  return (
    <div>
      {Object.entries(segs).map(([name, value]) => (
        <div className="paw-card" key={name}>
          <h3>{LINE_LABELS[name] || name}</h3>
          {asList(value).map((item, index) => {
            const row = asDict(item);
            return (
              <div key={index}>
                <h4>Segment {index + 1}</h4>
                <div className="paw-grid">
                  <Kv k="visibility" v={row.visibility_strength} />
                  <Kv k="thickness" v={row.thickness} />
                  <Kv k="direction" v={row.direction} />
                  <Kv k="curvature" v={row.curvature} />
                  <Kv k="confidence" v={`${row.confidence} (${confBand(row.confidence)})`} />
                </div>
                <JsonBlock value={row.coordinates} />
                <button type="button" onClick={() => onSelect({ kind: "segment", name, ...row })}>Inspect</button>
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}

function MinorCard({ master, scan }: { master: Dict; scan: Dict }) {
  const minor = asDict(master.minor_lines);
  const union = asDict(scan.union_lines);
  return (
    <div className="paw-card">
      <h2>Minor / secondary lines</h2>
      <p>If the image cannot prove absence, status is not_detected / insufficient_visibility — never a fake “absent”.</p>
      {Object.entries(minor).map(([name, value]) => {
        const row = asDict(value);
        const label = row.status === "not_detected" ? "NOT VISIBLE" : row.status === "ambiguous" ? "AMBIGUOUS" : str(row.status);
        return (
          <div key={name} className="paw-card">
            <h3>{name} <Badge value={label} /></h3>
            <div className="paw-grid">
              <Kv k="confidence" v={row.confidence} />
              <Kv k="reason" v={row.reason} />
            </div>
            <JsonBlock value={row.candidates || []} />
          </div>
        );
      })}
      <h3>Union / relationship candidates</h3>
      <JsonBlock value={union} />
    </div>
  );
}

function MountCard({ scan, master, onSelect }: { scan: Dict; master: Dict; onSelect: (v: Dict) => void }) {
  const mounts = { ...asDict(scan.mounts), ...asDict(master.mounts) };
  return (
    <div>
      {MOUNTS.map((name) => {
        const row = asDict(mounts[name]);
        return (
          <div className="paw-card" key={name}>
            <h3>{name} — measurements only</h3>
            <div className="paw-grid">
              <Kv k="status" v={row.status} />
              <Kv k="area" v={row.area_normalized} />
              <Kv k="width" v={row.width_normalized} />
              <Kv k="line density" v={row.line_density} />
              <Kv k="texture" v={JSON.stringify(row.texture)} />
              <Kv k="prominence" v={JSON.stringify(row.prominence || row.prominence_estimate)} />
              <Kv k="boundary confidence" v={`${row.confidence} (${confBand(row.confidence)})`} />
            </div>
            <JsonBlock value={row.region_polygon || []} />
            <button type="button" onClick={() => onSelect({ kind: "mount", name, ...row })}>Inspect on map</button>
          </div>
        );
      })}
    </div>
  );
}

function FingerCard({ scan }: { scan: Dict }) {
  const fingers = asDict(scan.fingers);
  return (
    <div>
      {FINGERS.map((name) => {
        const row = asDict(fingers[name]);
        return (
          <div className="paw-card" key={name}>
            <h3>{name}</h3>
            <div className="paw-grid">
              <Kv k="length" v={row.length_normalized} />
              <Kv k="raw length px" v={row.raw_length_px} />
              <Kv k="width" v={row.width_normalized} />
              <Kv k="finger/palm ratio" v={row.finger_to_palm_ratio} />
              <Kv k="spacing" v={row.spacing_normalized} />
              <Kv k="straightness" v={row.straightness} />
              <Kv k="taper" v={row.taper} />
              <Kv k="relative length" v={row.relative_length} />
              <Kv k="phalanx lengths" v={JSON.stringify(row.phalanx_lengths_px || row.raw_segment_lengths_px)} />
              <Kv k="phalanx ratios" v={JSON.stringify(row.proportions)} />
              <Kv k="joints" v={JSON.stringify(row.joints)} />
              <Kv k="tip" v={JSON.stringify(row.tip_location)} />
              <Kv k="confidence" v={`${row.confidence} (${confBand(row.confidence)})`} />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function TipCard({ master, scan }: { master: Dict; scan: Dict }) {
  const tips = asDict(master.fingertips);
  return (
    <div className="paw-card">
      <h2>Fingertips</h2>
      {Object.entries(tips).map(([name, value]) => {
        const row = asDict(value);
        return (
          <div key={name}>
            <h3>{name}</h3>
            <div className="paw-grid">
              <Kv k="classification" v={row.classification} />
              <Kv k="status" v={row.status} />
              <Kv k="confidence" v={`${row.confidence} (${confBand(row.confidence)})`} />
              <Kv k="measurements" v={JSON.stringify(row.measurements)} />
            </div>
          </div>
        );
      })}
      <p className="muted">Unknown is kept when the still image cannot classify the tip.</p>
      <JsonBlock value={asDict(scan.fingers)} />
    </div>
  );
}

function ThumbCard({ scan }: { scan: Dict }) {
  const thumb = asDict(scan.thumb);
  return (
    <div className="paw-card">
      <h2>Thumb</h2>
      <div className="paw-grid">
        <Kv k="length" v={JSON.stringify(thumb.length)} />
        <Kv k="width" v={JSON.stringify(thumb.width)} />
        <Kv k="angle" v={JSON.stringify(thumb.spread_angle)} />
        <Kv k="opening angle" v={JSON.stringify(thumb.opening_angle)} />
        <Kv k="first phalanx" v={JSON.stringify(thumb.first_phalanx)} />
        <Kv k="second phalanx" v={JSON.stringify(thumb.second_phalanx)} />
        <Kv k="phalanx proportions" v={JSON.stringify(thumb.phalanx_proportions)} />
        <Kv k="tip shape" v={JSON.stringify(thumb.tip_shape)} />
        <Kv k="Venus connection" v={JSON.stringify(thumb.venus_connection)} />
        <Kv k="flexibility" v={JSON.stringify(thumb.flexibility)} />
        <Kv k="confidence" v={`${thumb.confidence} (${confBand(thumb.confidence)})`} />
      </div>
      <p>Flexibility from a static photo is UNKNOWN unless explicitly observed.</p>
    </div>
  );
}

function WristCard({ master, scan }: { master: Dict; scan: Dict }) {
  return (
    <div className="paw-card">
      <h2>Wrist / Rascette</h2>
      <JsonBlock value={master.wrist_rascette || asDict(scan.segmentation).wrist} />
    </div>
  );
}

function MarkingTable({
  scan, hand, master, onSelect,
}: { scan: Dict; hand: string; master: Dict; onSelect: (v: Dict) => void }) {
  const markings = asList(asDict(scan.special_markings).candidates).map((item) => asDict(item));
  const rels = asList(master.marking_relationships).map((item) => asDict(item));
  return (
    <div className="paw-card">
      <h2>Special markings</h2>
      <table className="paw-table">
        <thead>
          <tr>
            <th>ID</th><th>type</th><th>hand</th><th>region/mount</th><th>parent</th>
            <th>x</th><th>y</th><th>size</th><th>orientation</th><th>conf</th><th>method</th>
          </tr>
        </thead>
        <tbody>
          {markings.map((row, i) => {
            const point = asDict(asList(row.coordinates)[0] || row);
            const rel = rels[i] || {};
            return (
              <tr key={i} onClick={() => onSelect({ kind: "marking", ...row, x: point.x, y: point.y, region: rel.region })}>
                <td>{str(row.id || i)}</td>
                <td>{str(row.type)}</td>
                <td>{hand}</td>
                <td>{str(rel.region || row.region)}</td>
                <td>{str(row.parent_feature || row.parent_line)}</td>
                <td>{str(point.x)}</td>
                <td>{str(point.y)}</td>
                <td>{str(row.size)}</td>
                <td>{str(row.orientation)}</td>
                <td>{str(row.confidence)} {confBand(row.confidence)}</td>
                <td>{str(row.method || row.detector)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function RelationTable({ master, onSelect }: { master: Dict; onSelect: (v: Dict) => void }) {
  const rows = asList(master.line_relationships).map((item) => asDict(item));
  return (
    <div className="paw-card">
      <h2>Line intersections / relationships</h2>
      <table className="paw-table">
        <thead>
          <tr><th>relationship</th><th>x</th><th>y</th><th>distance</th><th>angle</th><th>intersects</th><th>conf</th></tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} onClick={() => onSelect({ kind: "relationship", ...row, ...(asDict(row.coordinates)) })}>
              <td>{str(row.relationship)}</td>
              <td>{str(asDict(row.coordinates).x)}</td>
              <td>{str(asDict(row.coordinates).y)}</td>
              <td>{str(row.distance)}</td>
              <td>{str(row.angle)}</td>
              <td>{String(row.intersects)}</td>
              <td>{str(row.confidence)} {confBand(row.confidence)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function LineMountCard({ master, scan }: { master: Dict; scan: Dict }) {
  const mounts = asDict(scan.mounts);
  const polys = Object.entries(mounts).map(([name, value]) => ({ name, poly: pointsOf(asDict(value).region_polygon) }));
  const lines = asDict(scan.major_lines);
  const rows = MAJOR_LINES.map((name) => {
    const path = resolveMajorLinePath(scan, name);
    const start = path[0];
    const end = path[path.length - 1];
    const startMount = polys.find((m) => start && pointIn(start, m.poly))?.name || "unknown";
    const endMount = polys.find((m) => end && pointIn(end, m.poly))?.name || "unknown";
    const crossed = polys.filter((m) => path.some((p) => pointIn(p, m.poly))).map((m) => m.name);
    return { name, startMount, endMount, crossed, confidence: asDict(lines[name]).confidence };
  });
  return (
    <div className="paw-card">
      <h2>Line-to-mount relationships (geometry, not meaning)</h2>
      <table className="paw-table">
        <thead><tr><th>line</th><th>begins in</th><th>crosses</th><th>terminates toward</th><th>conf</th></tr></thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.name}>
              <td>{LINE_LABELS[row.name]}</td>
              <td>{row.startMount}</td>
              <td>{row.crossed.join(", ") || "—"}</td>
              <td>{row.endMount}</td>
              <td>{str(row.confidence)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <JsonBlock value={master.marking_relationships || []} />
    </div>
  );
}

function pointIn(point: { x: number; y: number }, polygon: { x: number; y: number }[]) {
  if (polygon.length < 3) return false;
  let inside = false;
  for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
    const a = polygon[i];
    const b = polygon[j];
    const hit = (a.y > point.y) !== (b.y > point.y) && point.x < ((b.x - a.x) * (point.y - a.y)) / ((b.y - a.y) || 1e-9) + a.x;
    if (hit) inside = !inside;
  }
  return inside;
}

function CompareCard({ left, right, comparison }: { left: Dict; right: Dict; comparison: Dict }) {
  const rows = asList(comparison.comparisons).map((item) => asDict(item));
  return (
    <div className="paw-card">
      <h2>Left vs right — no interpretation</h2>
      <table className="paw-table">
        <thead><tr><th>feature</th><th>left</th><th>right</th><th>difference</th><th>conf</th></tr></thead>
        <tbody>
          {rows.map((row) => (
            <tr key={str(row.id)}>
              <td>{str(row.id)}</td>
              <td>{str(row.left_value)}</td>
              <td>{str(row.right_value)}</td>
              <td>{str(row.difference)}</td>
              <td>{str(row.confidence)} {confBand(row.confidence)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <JsonBlock value={{ left_geometry: left.palm_geometry, right_geometry: right.palm_geometry }} />
    </div>
  );
}

function DetectionCard({ scan, master }: { scan: Dict; master: Dict }) {
  const detector = asDict(master.detector_fusion);
  const secondary = asDict(scan.secondary_lines);
  const semantic = asDict(secondary.semantic_verification);
  const fateDetection = asDict(secondary.fate_line_detection);
  const fateLine = asDict(asDict(scan.major_lines).fate_line);
  const prep = asDict(scan.preprocessing);
  const stages = asDict(prep.stages);
  return (
    <div className="paw-card">
      <h2>Detection methods</h2>
      <div className="paw-grid">
        <Kv k="detection source" v="IMAGE_PIXELS" />
        <Kv k="hand landmark backend" v="MediaPipe Hands" />
        <Kv k="crease detector" v="OpenCV blackhat + Canny ridge fusion" />
        <Kv k="semantic naming" v={str(semantic.status)} />
        <Kv k="detector agreement" v={secondary.detector_agreement} />
        <Kv k="crease candidates" v={asList(secondary.crease_candidates).length} />
        <Kv k="accepted crease paths" v={asDict(secondary.audit).accepted_candidate_count} />
        <Kv k="semantic assignments" v={JSON.stringify(asDict(semantic.model_evidence).assigned_classes || [])} />
        <Kv k="accepted candidates" v={asDict(secondary.audit).accepted_candidate_count} />
        <Kv k="rejected candidates" v={asDict(secondary.audit).rejected_candidate_count} />
        <Kv k="ambiguous candidates" v={asDict(secondary.audit).ambiguous_candidate_count} />
        <Kv k="missed/unresolved" v={asDict(secondary.audit).missed_or_unresolved_candidate_count} />
      </div>
      <h3>Preprocessing stages</h3>
      <JsonBlock value={stages} />
      <h3>Crease detector methods</h3>
      <JsonBlock value={secondary.methods || {}} />
      <h3>Candidate audit buckets</h3>
      <JsonBlock value={secondary.audit || {}} />
      <h3>Detector fusion / provenance</h3>
      <JsonBlock value={detector || secondary} />
      <h3>Semantic verifier evidence</h3>
      <JsonBlock value={semantic} />
      <h3>Fate Line detection (image-first)</h3>
      <div className="paw-grid">
        <Kv k="validity" v={fateLine.validity ?? fateLine.status} />
        <Kv k="image support" v={fateLine.image_support} />
        <Kv k="coverage span" v={fateLine.coverage_span} />
        <Kv k="confidence" v={fateLine.confidence} />
        <Kv k="path points" v={fateLine.path_point_count ?? asList(fateLine.path).length} />
        <Kv k="stitching" v={fateDetection.stitching_applied ? "yes" : "no"} />
        <Kv k="source candidates" v={JSON.stringify(fateLine.source_candidate_ids || [])} />
      </div>
      <JsonBlock value={fateDetection.candidate_audit ? fateDetection : { status: "not_available" }} />
    </div>
  );
}

function ConfidenceCard({ scan, master }: { scan: Dict; master: Dict }) {
  const c = asDict(master.confidence);
  const scanC = asDict(scan.scan_confidence);
  const rows = [
    ["image", c.image ?? asDict(scan.quality).score],
    ["hand", c.hand],
    ["landmark", c.landmark],
    ["line", c.line],
    ["segment", c.segment],
    ["marking", c.marking],
    ["mount", c.mount],
    ["finger", scanC.fingers],
    ["thumb", asDict(scan.thumb).confidence],
    ["measurement", c.measurement],
    ["relationship", c.relationship],
    ["overall", c.overall ?? scanC.overall],
  ];
  return (
    <div className="paw-card">
      <h2>Confidence layers</h2>
      <table className="paw-table">
        <thead><tr><th>level</th><th>value</th><th>band</th></tr></thead>
        <tbody>
          {rows.map(([k, v]) => (
            <tr key={String(k)}><td>{k}</td><td>{str(v)}</td><td>{confBand(v)}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ValidationCard({ scan, order }: { scan: Dict; order: Dict }) {
  const v = asDict(scan.validation);
  const p = asDict(scan.production_validation);
  return (
    <div className="paw-card">
      <h2>Validation</h2>
      <div className="paw-grid">
        <Kv k="scan validation" v={v.status} />
        <Kv k="quality gate" v={v.quality_gate} />
        <Kv k="production status" v={p.status || "—"} />
        <Kv k="production message" v={p.user_message || "—"} />
        <Kv k="overall scan status" v={order.overall_scan_status || order.status || "—"} />
        <Kv k="overall confidence" v={order.overall_confidence == null ? "—" : `${Math.round(Number(order.overall_confidence) * 100)}%`} />
        <Kv k="retake required" v={String(v.retake_required)} />
        <Kv k="human overlays" v={Object.keys(asDict(order.human_overlays)).length} />
      </div>
      <JsonBlock value={{ validation_issues: v.issues || [], production_validation: p }} />
    </div>
  );
}

function AnalysisReady({ left, right, comparison }: { left: Dict; right: Dict; comparison: Dict }) {
  return (
    <div className="paw-card">
      <h2>Analysis-ready view</h2>
      <p>RAW EXTRACTION only. Traditional meanings are not applied on this page.</p>
      {(["left", "right"] as const).map((side) => {
        const scan = side === "left" ? left : right;
        return (
          <div key={side} className="paw-card">
            <h3>{side.toUpperCase()}</h3>
            <JsonBlock value={{
              palm_geometry: scan.palm_geometry,
              major_lines: scan.major_lines,
              minor_lines: masterOf(scan).minor_lines,
              mounts: scan.mounts,
              fingers: scan.fingers,
              thumb: scan.thumb,
              wrist: masterOf(scan).wrist_rascette,
              markings: scan.special_markings,
              intersections: masterOf(scan).line_relationships,
              confidence: masterOf(scan).confidence || scan.scan_confidence,
            }} />
          </div>
        );
      })}
      <h3>Bilateral differences</h3>
      <JsonBlock value={comparison} />
    </div>
  );
}

function AuditCard({ order, left, right }: { order: Dict; left: Dict; right: Dict }) {
  const scans = { left, right };
  return (
    <div>
      {(["left", "right"] as const).map((side) => {
        const scan = scans[side];
        const prep = asDict(scan.preprocessing);
        const seg = asDict(scan.segmentation);
        const hand = asDict(scan.hand);
        const secondary = asDict(scan.secondary_lines);
        const semantic = asDict(secondary.semantic_verification);
        const major = asDict(scan.major_lines);
        const majorDetected = MAJOR_LINES.filter((name) => asDict(major[name]).status === "detected").length;
        const mounts = asDict(scan.mounts);
        const mountDetected = Object.values(mounts).filter((item) => asDict(item).status === "detected").length;
        return (
          <div className="paw-card" key={side}>
            <h2>{side.toUpperCase()} pipeline audit</h2>
            <div className="paw-grid">
              <Kv k="session" v={order.session_id} />
              <Kv k="scan id" v={asDict(scan.metadata).scan_id} />
              <Kv k="writing hand" v={order.writing_hand} />
              <Kv k="detected hand side" v={hand.side || hand.handedness} />
              <Kv k="hand confidence" v={`${hand.confidence} (${confBand(hand.confidence)})`} />
              <Kv k="quality usable" v={String(asDict(scan.quality).usable)} />
              <Kv k="preprocess variants" v={JSON.stringify(prep.variants || [])} />
              <Kv k="landmarks" v={asList(scan.landmarks).length} />
              <Kv k="segmentation quality" v={asDict(scan.scan_confidence).contributions ? JSON.stringify(asDict(scan.scan_confidence).contributions) : "—"} />
              <Kv k="crease candidates" v={asList(secondary.crease_candidates).length} />
              <Kv k="accepted" v={asDict(secondary.audit).accepted_candidate_count} />
              <Kv k="rejected" v={asDict(secondary.audit).rejected_candidate_count} />
              <Kv k="ambiguous" v={asDict(secondary.audit).ambiguous_candidate_count} />
              <Kv k="missed/unresolved" v={asDict(secondary.audit).missed_or_unresolved_candidate_count} />
              <Kv k="semantic verification" v={semantic.status} />
              <Kv k="major lines detected" v={majorDetected} />
              <Kv k="mounts detected" v={mountDetected} />
              <Kv k="special markings" v={asList(asDict(scan.special_markings).candidates).length} />
              <Kv k="phase 2 eligible" v={String(asDict(scan.scan_confidence).phase_2_eligible)} />
              <Kv k="overall confidence" v={`${asDict(scan.scan_confidence).overall} (${confBand(asDict(scan.scan_confidence).overall)})`} />
            </div>
            <h3>What to validate visually</h3>
            <ul>
              <li>Palm boundary and visible palm should trace the real palm, not finger gaps/background.</li>
              <li>Landmarks should sit on wrist, joints, and fingertips at the correct image positions.</li>
              <li>Raw crease evidence should be inspected before any candidate or final line is trusted.</li>
              <li>Raw crease candidates should follow visible creases before semantic naming is trusted.</li>
              <li>Named major lines should overlap the strongest matching crease, not nearby texture.</li>
              <li>Rejected, ambiguous, and missed/unresolved candidates should be reviewed before adding palmistry meaning.</li>
              <li>Mount polygons should cover the intended anatomical region rather than arbitrary convex hull area.</li>
              <li>Markings and intersections should be reviewed against the original image before interpretation.</li>
            </ul>
            <h3>Segmentation summary</h3>
            <JsonBlock value={seg} />
          </div>
        );
      })}
      <div className="paw-card">
        <h2>Detection audit table</h2>
        <table className="paw-table">
          <thead>
            <tr>
              <th>hand</th>
              <th>feature</th>
              <th>source algorithm</th>
              <th>raw result</th>
              <th>final result</th>
              <th>confidence</th>
              <th>status</th>
            </tr>
          </thead>
          <tbody>
            {(["left", "right"] as const).flatMap((side) => {
              const scan = scans[side];
              const secondary = asDict(scan.secondary_lines);
              const methods = asDict(secondary.methods);
              const major = asDict(scan.major_lines);
              const rows = MAJOR_LINES.map((name) => {
                const line = asDict(major[name]);
                const candidateId = str(line.source_candidate_id, "");
                const candidate = asList(secondary.crease_candidates)
                  .map((item) => asDict(item))
                  .find((item) => str(item.id, "") === candidateId);
                return {
                  id: `${side}-${name}`,
                  hand: side,
                  feature: LINE_LABELS[name],
                  source: candidate
                    ? JSON.stringify(candidate.methods || methods)
                    : JSON.stringify(asDict(secondary.semantic_verification).model_evidence || methods),
                  raw: candidate
                    ? `candidate ${candidateId || "?"} · len ${str(candidate.normalized_length || candidate.arc_length_px)}`
                    : "no accepted raw candidate",
                  final: line.status === "detected"
                    ? `classified as ${name}`
                    : line.reason || line.status,
                  confidence: str(line.confidence),
                  status: str(line.status),
                };
              });
              const rejected = asList(secondary.crease_candidates)
                .map((item) => asDict(item))
                .filter((item) => str(item.audit_status) !== "accepted")
                .slice(0, 8)
                .map((item, index) => ({
                  id: `${side}-rejected-${index}`,
                  hand: side,
                  feature: `crease candidate ${str(item.id, index)}`,
                  source: JSON.stringify(item.methods || methods),
                  raw: `path ${asList(item.path).length} pts`,
                  final: item.audit_status === "missed_or_unresolved"
                    ? "visible candidate not resolved to a named line"
                    : "not promoted to named major line",
                  confidence: str(item.confidence),
                  status: str(item.audit_status || item.status || "rejected_or_unassigned"),
                }));
              return [...rows, ...rejected];
            }).map((row) => (
              <tr key={row.id}>
                <td>{row.hand}</td>
                <td>{row.feature}</td>
                <td>{row.source}</td>
                <td>{row.raw}</td>
                <td>{row.final}</td>
                <td>{row.confidence}</td>
                <td>{row.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
