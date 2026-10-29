import { useId } from "react";

/**
 * ResumeRank mark: a lowercase "r" whose arm becomes a rising arrow (your rank going up),
 * with a rank dot, on a glossy orange tile that matches the site's stickers.
 * Bold strokes on a 32-unit grid stay legible from 16px (favicon) to 40px.
 */
export default function LogoMark({ size = 30 }: { size?: number }) {
  const id = useId().replace(/:/g, "");
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true" className="shrink-0">
      <defs>
        <linearGradient id={`lm${id}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#FF7A52" />
          <stop offset="0.55" stopColor="#FF4A24" />
          <stop offset="1" stopColor="#E8380F" />
        </linearGradient>
      </defs>
      <rect width="32" height="32" rx="10" fill={`url(#lm${id})`} />
      <rect x="1.5" y="1.2" width="29" height="13" rx="8.5" fill="#fff" opacity="0.14" />
      <g fill="none" stroke="#fff" strokeWidth="3.3" strokeLinecap="round" strokeLinejoin="round">
        <path d="M10.5 24.5V14" />
        <path d="M10.5 18.2C11.6 13.1 15.2 10.3 21.8 9.1" />
        <path d="M17.6 7.9l4.5 1.1-1.2 4.4" />
      </g>
      <circle cx="21.6" cy="22.6" r="2.7" fill="#121212" />
    </svg>
  );
}
