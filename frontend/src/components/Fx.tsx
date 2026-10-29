/**
 * Micro-interaction building blocks (D-43): rolling labels, press ripples, the glowing primary CTA,
 * and a cursor spotlight for cards. Visual rules live in index.css ("SaaS motion layer").
 */
import { AnimatePresence, motion } from "motion/react";
import { useState, type ButtonHTMLAttributes, type PointerEvent, type ReactNode } from "react";
import { Link } from "react-router-dom";

/** Label that rolls up and is replaced by an identical copy on hover (parent needs `group`). */
export function RollText({ children }: { children: string }) {
  return (
    <span className="roll">
      <span>{children}</span>
      <span aria-hidden>{children}</span>
    </span>
  );
}

interface Ripple {
  id: number;
  x: number;
  y: number;
}

/** Ripples that spread from the press point. Returns the handler and the layer to render. */
export function useRipple() {
  const [ripples, setRipples] = useState<Ripple[]>([]);
  const onPointerDown = (e: PointerEvent<HTMLElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    const ripple = { id: performance.now(), x: e.clientX - r.left, y: e.clientY - r.top };
    setRipples((rs) => [...rs.slice(-2), ripple]);
  };
  const layer = (
    <span aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden rounded-[inherit]">
      <AnimatePresence>
        {ripples.map((rp) => (
          <motion.span
            key={rp.id}
            className="absolute size-10 rounded-full bg-white/35"
            style={{ left: rp.x - 20, top: rp.y - 20 }}
            initial={{ scale: 0, opacity: 0.6 }}
            animate={{ scale: 9, opacity: 0 }}
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
            onAnimationComplete={() => setRipples((rs) => rs.filter((x) => x.id !== rp.id))}
          />
        ))}
      </AnimatePresence>
    </span>
  );
  return { onPointerDown, layer };
}

/** Feed the cursor position to `.spotlight` cards as CSS variables. */
export function spotlight(e: PointerEvent<HTMLElement>) {
  const r = e.currentTarget.getBoundingClientRect();
  e.currentTarget.style.setProperty("--mx", `${e.clientX - r.left}px`);
  e.currentTarget.style.setProperty("--my", `${e.clientY - r.top}px`);
}

/** Swaps button content with a short vertical slide when `stateKey` changes. */
export function SwapLabel({ stateKey, children }: { stateKey: string; children: ReactNode }) {
  return (
    <span className="relative inline-flex overflow-hidden">
      <AnimatePresence mode="popLayout" initial={false}>
        <motion.span
          key={stateKey}
          className="inline-flex items-center gap-2"
          initial={{ y: "110%", opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: "-110%", opacity: 0 }}
          transition={{ duration: 0.42, ease: [0.65, 0, 0.35, 1] }}
        >
          {children}
        </motion.span>
      </AnimatePresence>
    </span>
  );
}

const BTN = "btn-dark group relative overflow-hidden";

/** Primary call-to-action link with orbiting gradient ring, breathing glow, ripple and rolling label. */
export function GlowLink({ to, label, icon, className = "" }: { to: string; label: string; icon?: ReactNode; className?: string }) {
  const { onPointerDown, layer } = useRipple();
  return (
    <span className="glow-ring" data-active="true">
      <span className="halo" aria-hidden />
      <Link to={to} onPointerDown={onPointerDown} className={`${BTN} nudge ${className}`}>
        {layer}
        <RollText>{label}</RollText>
        {icon}
      </Link>
    </span>
  );
}

/** Primary button with the same treatment; the ring only orbits while `active` (ready to press). */
export function GlowButton({
  active,
  busy,
  children,
  className = "",
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { active: boolean; busy?: boolean; children: ReactNode }) {
  const { onPointerDown, layer } = useRipple();
  return (
    <span className={`glow-ring ${className}`} data-active={active && !busy ? "true" : "false"}>
      <span className="halo" aria-hidden />
      <motion.button
        {...(rest as object)}
        onPointerDown={onPointerDown}
        whileTap={active && !busy ? { scale: 0.97 } : undefined}
        transition={{ type: "spring", stiffness: 420, damping: 26 }}
        className={`${BTN} nudge w-full ${busy ? "shimmer" : ""}`}
      >
        {layer}
        {children}
      </motion.button>
    </span>
  );
}
