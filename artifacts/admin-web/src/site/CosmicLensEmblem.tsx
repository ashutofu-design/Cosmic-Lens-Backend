/** Image-like SVG lens artwork: crisp, lightweight and animated through CSS. */
export function CosmicLensEmblem() {
  return (
    <div className="cosmic-lens-emblem" role="img" aria-label="Cosmic Lens">
      <svg viewBox="0 0 320 320" aria-hidden>
        <defs>
          <radialGradient id="lensGlass" cx="38%" cy="30%" r="70%">
            <stop offset="0" stopColor="#dffbff" stopOpacity=".72" />
            <stop offset=".18" stopColor="#67e8f9" stopOpacity=".2" />
            <stop offset=".52" stopColor="#7c3aed" stopOpacity=".22" />
            <stop offset=".82" stopColor="#100b25" stopOpacity=".86" />
            <stop offset="1" stopColor="#050713" />
          </radialGradient>
          <linearGradient id="lensRim" x1="30" y1="30" x2="290" y2="290">
            <stop offset="0" stopColor="#f5e3a7" />
            <stop offset=".28" stopColor="#a78bfa" />
            <stop offset=".58" stopColor="#67e8f9" />
            <stop offset="1" stopColor="#8b5cf6" />
          </linearGradient>
          <radialGradient id="lensCore" cx="50%" cy="45%" r="55%">
            <stop offset="0" stopColor="#ffffff" />
            <stop offset=".2" stopColor="#67e8f9" />
            <stop offset=".56" stopColor="#8b5cf6" />
            <stop offset="1" stopColor="#160c35" stopOpacity="0" />
          </radialGradient>
          <filter id="lensGlow" x="-60%" y="-60%" width="220%" height="220%">
            <feGaussianBlur stdDeviation="8" />
          </filter>
          <clipPath id="lensClip">
            <circle cx="160" cy="160" r="105" />
          </clipPath>
        </defs>

        <circle className="lens-ambient" cx="160" cy="160" r="128" fill="none" stroke="#a78bfa" strokeOpacity=".12" />
        <circle className="lens-orbit lens-orbit-outer" cx="160" cy="160" r="142" fill="none" stroke="url(#lensRim)" strokeOpacity=".3" strokeDasharray="2 14" />
        <circle className="lens-glow" cx="160" cy="160" r="106" fill="#7c3aed" opacity=".25" filter="url(#lensGlow)" />
        <circle cx="160" cy="160" r="118" fill="#080a16" stroke="url(#lensRim)" strokeWidth="3" />
        <circle cx="160" cy="160" r="108" fill="url(#lensGlass)" stroke="#fff" strokeOpacity=".13" />

        <g clipPath="url(#lensClip)">
          <ellipse className="lens-nebula lens-nebula-a" cx="128" cy="190" rx="95" ry="30" fill="#7c3aed" opacity=".18" transform="rotate(-26 128 190)" />
          <ellipse className="lens-nebula lens-nebula-b" cx="206" cy="118" rx="78" ry="20" fill="#67e8f9" opacity=".12" transform="rotate(-26 206 118)" />
          <path className="lens-chart-path" d="M50 190 C95 130 126 210 165 142 S235 98 276 148" fill="none" stroke="#67e8f9" strokeOpacity=".44" strokeWidth="1.2" />
          <circle cx="94" cy="158" r="2" fill="#f5e3a7" />
          <circle cx="132" cy="103" r="1.5" fill="#fff" />
          <circle cx="211" cy="184" r="2" fill="#a78bfa" />
          <circle cx="239" cy="127" r="1.5" fill="#67e8f9" />
          <circle cx="176" cy="79" r="1" fill="#fff" />
        </g>

        <circle className="lens-core-glow" cx="160" cy="160" r="48" fill="url(#lensCore)" opacity=".78" />
        <circle cx="160" cy="160" r="17" fill="#070914" stroke="#f5e3a7" strokeOpacity=".55" />
        <path d="M160 143 L164 156 L177 160 L164 164 L160 177 L156 164 L143 160 L156 156 Z" fill="#f5e3a7" />

        <g className="lens-orbit lens-orbit-inner">
          <ellipse cx="160" cy="160" rx="92" ry="42" fill="none" stroke="#fff" strokeOpacity=".18" transform="rotate(-28 160 160)" />
          <circle cx="79" cy="202" r="6" fill="#67e8f9" />
          <circle cx="79" cy="202" r="12" fill="#67e8f9" opacity=".15" />
        </g>

        <path className="lens-shine" d="M93 91 C121 61 170 51 205 70" fill="none" stroke="#fff" strokeWidth="8" strokeLinecap="round" strokeOpacity=".24" />
      </svg>
    </div>
  );
}
