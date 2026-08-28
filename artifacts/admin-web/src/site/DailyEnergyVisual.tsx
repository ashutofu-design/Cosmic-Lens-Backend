import type { CSSProperties } from "react";

const PLANET_ENERGY = [
  ["☉", "Surya", "Clarity"],
  ["☽", "Chandra", "Emotion"],
  ["♂", "Mangal", "Drive"],
  ["☿", "Budh", "Focus"],
  ["♃", "Guru", "Growth"],
  ["♀", "Shukra", "Harmony"],
  ["♄", "Shani", "Discipline"],
] as const;

const ENERGY_SIGNALS = [
  ["Focus", "Clear", 78],
  ["Emotional flow", "Steady", 64],
  ["Growth", "Active", 84],
  ["Decisions", "Measured", 70],
] as const;

export function DailyEnergyVisual() {
  const today = new Intl.DateTimeFormat("en-IN", {
    day: "2-digit",
    month: "short",
  }).format(new Date());

  return (
    <div className="daily-energy-visual">
      <div className="daily-energy-topbar">
        <span><i /> Live planetary synthesis</span>
        <strong>{today} · Today</strong>
      </div>

      <div className="daily-energy-stage">
        <div className="daily-energy-cosmos" aria-label="Animated planetary energy map">
          <span className="daily-energy-orbit orbit-one" />
          <span className="daily-energy-orbit orbit-two" />
          <span className="daily-energy-orbit orbit-three" />
          <div className="daily-energy-core">
            <small>Today’s</small>
            <strong>Energy</strong>
            <span>Balanced momentum</span>
          </div>
          {PLANET_ENERGY.map(([symbol, planet, energy], index) => (
            <span
              key={planet}
              className={`daily-energy-planet planet-energy-${index + 1}`}
              style={{ "--planet-index": index } as CSSProperties}
              title={`${planet}: ${energy}`}
            >
              <i>{symbol}</i>
              <b>{planet}</b>
            </span>
          ))}
          <span className="daily-energy-sweep" aria-hidden />
        </div>

        <div className="daily-energy-readings">
          <div className="daily-energy-reading-title">
            <span>Energy signals</span>
            <i>LIVE</i>
          </div>
          {ENERGY_SIGNALS.map(([name, status, value], index) => (
            <div className="daily-energy-reading" key={name}>
              <div>
                <span>{name}</span>
                <strong>{status}</strong>
              </div>
              <i>
                <span
                  style={
                    {
                      "--energy-width": `${value}%`,
                      "--energy-delay": `${index * 0.35}s`,
                    } as CSSProperties
                  }
                />
              </i>
            </div>
          ))}
          <p>
            Dasha context and current transits are read together to form your daily energy view.
          </p>
        </div>
      </div>

      <div className="daily-energy-footer">
        <span>D1 chart</span><i>+</i><span>Current transits</span><i>+</i><span>Active dasha</span>
        <small>Representative preview</small>
      </div>
    </div>
  );
}
