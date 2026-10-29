// Decorative inline SVGs for empty and loading states. All aria-hidden; meaning is in nearby text.

const Grad = ({ id }: { id: string }) => (
  <defs>
    <linearGradient id={id} x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stopColor="#121212" />
      <stop offset="1" stopColor="#FF4A24" />
    </linearGradient>
  </defs>
);

/** A resume sheet with a sparkle: "drop your resume here". */
export function ResumeArt({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 160 120" className={className} aria-hidden="true">
      <Grad id="ra" />
      <ellipse cx="80" cy="108" rx="46" ry="6" fill="#121212" opacity="0.08" />
      <g className="motion-safe:animate-float" style={{ transformBox: "fill-box", transformOrigin: "center" }}>
        <rect x="46" y="14" width="68" height="86" rx="10" fill="#fff" stroke="#D4D8E8" />
        <circle cx="62" cy="32" r="7" fill="url(#ra)" opacity="0.9" />
        <rect x="74" y="27" width="28" height="5" rx="2.5" fill="#E5E7F1" />
        <rect x="74" y="35" width="18" height="4" rx="2" fill="#F1F1F3" />
        <rect x="56" y="50" width="48" height="4" rx="2" fill="#E5E7F1" />
        <rect x="56" y="59" width="40" height="4" rx="2" fill="#E5E7F1" />
        <rect x="56" y="68" width="44" height="6" rx="3" fill="#FDE047" opacity="0.75" />
        <rect x="56" y="80" width="30" height="4" rx="2" fill="#E5E7F1" />
      </g>
      <path d="M126 22l3 7 7 3-7 3-3 7-3-7-7-3 7-3z" fill="url(#ra)" />
      <path d="M32 56l2 4.5 4.5 2-4.5 2-2 4.5-2-4.5-4.5-2 4.5-2z" fill="#FF4A24" opacity="0.6" />
    </svg>
  );
}

/** A briefcase with a target: "choose the job". */
export function JobArt({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 160 120" className={className} aria-hidden="true">
      <Grad id="ja" />
      <ellipse cx="80" cy="108" rx="46" ry="6" fill="#121212" opacity="0.08" />
      <rect x="40" y="38" width="80" height="60" rx="12" fill="#fff" stroke="#D4D8E8" />
      <path d="M64 38v-8a6 6 0 0 1 6-6h20a6 6 0 0 1 6 6v8" fill="none" stroke="#D4D8E8" strokeWidth="3" />
      <rect x="40" y="56" width="80" height="6" fill="#F1F1F3" />
      <circle cx="80" cy="70" r="16" fill="none" stroke="url(#ja)" strokeWidth="3" />
      <circle cx="80" cy="70" r="8" fill="none" stroke="url(#ja)" strokeWidth="3" opacity="0.6" />
      <circle cx="80" cy="70" r="3" fill="url(#ja)" />
      <path d="M124 26l3 7 7 3-7 3-3 7-3-7-7-3 7-3z" fill="url(#ja)" />
    </svg>
  );
}

/** Ghost report: score ring + bars. Shown before the first check. */
export function ReportArt({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 220 120" className={className} aria-hidden="true">
      <Grad id="rpa" />
      <circle cx="56" cy="60" r="34" fill="none" stroke="#E5E7F1" strokeWidth="10" />
      <circle cx="56" cy="60" r="34" fill="none" stroke="url(#rpa)" strokeWidth="10" strokeLinecap="round" strokeDasharray="150 214" transform="rotate(-90 56 60)" />
      <rect x="44" y="54" width="24" height="12" rx="4" fill="#F1F1F3" />
      {[30, 50, 70, 90].map((y, i) => (
        <g key={y}>
          <rect x="112" y={y - 4} width="88" height="8" rx="4" fill="#F1F1F3" />
          <rect x="112" y={y - 4} width={[70, 52, 80, 36][i]} height="8" rx="4" fill="url(#rpa)" opacity={0.85 - i * 0.15} />
        </g>
      ))}
    </svg>
  );
}

/** A document with a scanning beam, for the "checking…" state. */
export function ScanningArt({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 120 150" className={className} aria-hidden="true">
      <Grad id="sa" />
      <rect x="14" y="8" width="92" height="134" rx="12" fill="#fff" stroke="#D4D8E8" />
      {[28, 40, 52, 70, 82, 94, 112, 124].map((y, i) => (
        <rect key={y} x="28" y={y} width={[52, 64, 40, 60, 48, 64, 36, 56][i]} height="5" rx="2.5" fill="#E5E7F1" />
      ))}
      <g className="motion-safe:animate-scan">
        <rect x="18" y="16" width="84" height="3" rx="1.5" fill="url(#sa)" />
        <rect x="18" y="19" width="84" height="16" fill="url(#sa)" opacity="0.08" />
      </g>
    </svg>
  );
}
