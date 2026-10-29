import { ArrowRight } from "lucide-react";
import type { CSSProperties, ReactNode } from "react";
import { Link } from "react-router-dom";
import { RollText } from "./Fx";
import LogoMark from "./LogoMark";

export function Logo() {
  return (
    <Link to="/" className="group flex items-center gap-2.5 text-ink" aria-label="ResumeRank home">
      <span className="transition-transform duration-500 ease-[var(--ease-spring)] group-hover:-rotate-6 group-hover:scale-105">
        <LogoMark size={30} />
      </span>
      <span className="font-brand text-[1.32rem] leading-none font-extrabold tracking-[-0.045em] [font-variation-settings:'opsz'_96]">
        resumerank
      </span>
    </Link>
  );
}

export function Navbar({ cta = true }: { cta?: boolean }) {
  return (
    <header className="no-print sticky top-3 z-40 px-3 sm:px-6">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-4 rounded-[18px] border border-line bg-white/85 pr-2 pl-4 shadow-[0_1px_2px_rgb(18_18_18/0.04)] backdrop-blur-lg">
        <Logo />
        <nav aria-label="Main" className="hidden items-center gap-7 text-sm font-medium text-ink-2 md:flex">
          <a href="/#how" className="nav-link hover:text-ink">How it works</a>
          <a href="/#roles" className="nav-link hover:text-ink">Roles</a>
          <a href="/#privacy" className="nav-link hover:text-ink">Privacy</a>
        </nav>
        {cta ? (
          <Link to="/check" className="btn-dark group !min-h-10 !px-4 text-sm">
            <RollText>Check my resume</RollText>
          </Link>
        ) : (
          <Link to="/" className="rounded-full px-3 py-2 text-sm font-medium text-ink-2 hover:text-ink">
            Home
          </Link>
        )}
      </div>
    </header>
  );
}

export function Footer() {
  return (
    <footer className="no-print mx-auto mt-10 max-w-6xl px-4 pb-10 sm:px-6">
      <div className="flex flex-col items-start justify-between gap-3 border-t border-line pt-6 text-sm text-mute sm:flex-row sm:items-center">
        <Logo />
        <p>Resumes are read in memory and never stored. AI suggestions can be wrong, so use your judgement.</p>
      </div>
    </footer>
  );
}

/** Tilted glossy sticker with pulsing rings. Used as a call to action, not decoration. */
export function StickerLink({
  to,
  children,
  rotate = -12,
  className = "",
  size = "text-6xl sm:text-7xl",
}: {
  to: string;
  children: ReactNode;
  rotate?: number;
  className?: string;
  size?: string;
}) {
  return (
    <Link to={to} className={`group relative inline-grid place-items-center transition-transform duration-700 ease-[var(--ease-apple)] hover:scale-[1.04] active:scale-[0.98] ${className}`}>
      {/* Concentric soft rings (static) plus one slow pulse: square aspect so they stay circles. */}
      <span data-rings aria-hidden className="pointer-events-none absolute inset-0 grid place-items-center">
        {[0.7, 0.95, 1.2].map((s) => (
          // Ring wrappers carry the size; inner circles are what the intro scales (data-ring).
          <span key={s} className="absolute grid aspect-square place-items-center" style={{ width: `${s * 100}%` }}>
            <span data-ring className="size-full rounded-full border-[14px] border-orange/[0.09]" />
          </span>
        ))}
        <span className="absolute aspect-square w-[80%] rounded-full bg-orange/20 motion-safe:animate-pulse-ring" />
      </span>
      <span
        className={`sticker ${size} motion-safe:animate-wobble`}
        style={{ "--r": `${rotate}deg` } as CSSProperties}
      >
        {children}
        <span className="grid size-[0.62em] place-items-center rounded-full bg-white text-orange shadow-md">
          <ArrowRight className="size-[0.36em]" strokeWidth={3} aria-hidden />
        </span>
      </span>
    </Link>
  );
}
