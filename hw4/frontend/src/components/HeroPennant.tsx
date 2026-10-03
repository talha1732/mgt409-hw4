// A classic horizontal felt pennant for the home page hero.
export default function HeroPennant() {
  return (
    <svg viewBox="0 0 360 150" width="360" height="150" role="img" aria-label="Yale pennant">
      {/* wooden stick */}
      <rect x="0" y="0" width="12" height="150" rx="6" fill="#c49a5a" />
      <rect x="2" y="0" width="3" height="150" rx="1.5" fill="#dcb67a" />
      {/* felt body */}
      <path d="M12 8 L352 75 L12 142 Z" fill="#ffffff" />
      <path d="M12 16 L330 75 L12 134 Z" fill="#00356b" />
      {/* stitched band near the stick */}
      <rect x="12" y="16" width="34" height="118" fill="#c8102e" />
      <path d="M40 22 V128" stroke="#ffffff" strokeWidth="2" strokeDasharray="5 5" opacity="0.7" />
      <text
        x="160" y="92" textAnchor="middle" fill="#ffffff"
        fontFamily="Fraunces, Georgia, serif" fontWeight="800" fontSize="50" letterSpacing="6"
      >
        YALE
      </text>
      {/* tassels */}
      <path d="M352 75 l8 -4 M352 75 l8 4 M352 75 l9 0" stroke="#d4a62a" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  )
}
