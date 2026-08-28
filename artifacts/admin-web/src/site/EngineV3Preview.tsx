import type { CSSProperties } from "react";

const ENGINE_LAYERS = [
  ["D1", "Birth chart"],
  ["D9", "Navamsha"],
  ["DA", "Dasha timing"],
  ["TR", "Live transits"],
] as const;

export function EngineV3Preview() {
  return (
    <div className="engine-v3-preview" aria-label="Cosmic Engine V3 preview">
      <div className="engine-v3-heading">
        <span className="engine-v3-pulse" />
        <div>
          <small>Inside the app</small>
          <strong>Cosmic Engine V3</strong>
        </div>
        <i>LIVE</i>
      </div>

      <div className="engine-v3-body">
        <div className="engine-v3-chart" aria-hidden>
          <span />
          <span />
          <span />
          <span />
          <b>V3</b>
        </div>
        <div className="engine-v3-layers">
          {ENGINE_LAYERS.map(([code, label], index) => (
            <div key={code} style={{ "--engine-delay": `${index * 0.7}s` } as CSSProperties}>
              <b>{code}</b>
              <span>{label}</span>
              <i />
            </div>
          ))}
        </div>
      </div>

      <div className="engine-v3-status">
        <span>12 houses</span>
        <span>9 planets</span>
        <span>Active periods</span>
      </div>
    </div>
  );
}
