export function BrandMark({ size = 40 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <rect width="64" height="64" rx="16" fill="#07101c" />
      <circle cx="32" cy="32" r="22" stroke="rgba(103,232,249,0.18)" strokeWidth="1.2" />
      <ellipse
        cx="32"
        cy="32"
        rx="24"
        ry="8"
        transform="rotate(-28 32 32)"
        stroke="rgba(165,243,252,0.35)"
        strokeWidth="1.4"
      />
      <ellipse
        cx="32"
        cy="32"
        rx="20"
        ry="6.5"
        transform="rotate(38 32 32)"
        stroke="#67e8f9"
        strokeWidth="2.2"
        opacity="0.95"
      />
      <circle cx="32" cy="32" r="9" fill="url(#clPlanetMark)" />
      <circle cx="35.2" cy="28.6" r="2.4" fill="rgba(255,255,255,0.55)" />
      <circle cx="14" cy="18" r="1.1" fill="#a5f3fc" />
      <circle cx="50" cy="16" r="0.8" fill="#fff" opacity="0.8" />
      <circle cx="48" cy="48" r="1" fill="#c4b5fd" />
      <defs>
        <radialGradient id="clPlanetMark" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(28 26) rotate(90) scale(16)">
          <stop stopColor="#a5f3fc" />
          <stop offset="1" stopColor="#22d3ee" />
        </radialGradient>
      </defs>
    </svg>
  );
}
