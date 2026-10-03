// The Campus Customs pennant mark, used in the nav, hero and footer.
export default function Pennant({ size = 34, label = 'CC' }: { size?: number; label?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true" className="pennant">
      <path d="M6 8h52L32 56z" fill="#00356b" stroke="#fff" strokeWidth="2.5" strokeLinejoin="round" />
      <path d="M8 9.5h48l-2.6 5H10.6z" fill="#c8102e" />
      <text x="32" y="37" fontFamily="Fraunces, Georgia, serif" fontSize="20" fontWeight="800" fill="#fff" textAnchor="middle">
        {label}
      </text>
    </svg>
  )
}
