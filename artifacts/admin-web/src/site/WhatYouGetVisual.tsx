import type { CSSProperties } from "react";

const LIFE_AREAS = [
  {
    name: "Relationship",
    signal: "Connection · Commitment · Timing",
    className: "relationship",
    icon: "♡",
  },
  {
    name: "Health",
    signal: "Energy · Balance · Vitality",
    className: "health",
    icon: "✦",
  },
  {
    name: "Wealth",
    signal: "Growth · Opportunity · Stability",
    className: "wealth",
    icon: "◇",
  },
  {
    name: "Career",
    signal: "Direction · Change · Progress",
    className: "career",
    icon: "↗",
  },
] as const;

export function WhatYouGetVisual() {
  return (
    <div className="life-areas-visual">
      <svg className="life-areas-paths" viewBox="0 0 640 500" aria-hidden>
        <path d="M320 250 C245 205 210 150 140 120" />
        <path d="M320 250 C395 205 430 150 500 120" />
        <path d="M320 250 C245 295 210 350 140 380" />
        <path d="M320 250 C395 295 430 350 500 380" />
        <circle cx="320" cy="250" r="115" />
        <circle cx="320" cy="250" r="168" />
      </svg>

      <div className="life-areas-core" aria-hidden>
        <span>Cosmic</span>
        <strong>V3</strong>
        <small>Life Analysis</small>
      </div>

      <div className="life-areas-grid">
        {LIFE_AREAS.map((area, index) => (
          <article
            key={area.name}
            className={`life-area-card life-area-${area.className}`}
            style={{ "--life-area-index": index } as CSSProperties}
          >
            <div className="life-area-card-top">
              <i>{area.icon}</i>
              <span>Analyzing</span>
            </div>
            <h3>{area.name}</h3>
            <p>{area.signal}</p>
            <div className="life-area-signal">
              <span /><span /><span /><span /><span />
            </div>
          </article>
        ))}
      </div>

      <div className="life-areas-scan" aria-hidden />
    </div>
  );
}
