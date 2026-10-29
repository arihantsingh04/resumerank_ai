/**
 * Animation toolkit (D-42). GSAP handles timelines, scroll-triggered reveals, parallax, magnetic hover
 * and smooth scrolling; Motion (motion/react) handles component-level micro-interactions in place.
 * Everything here no-ops under prefers-reduced-motion.
 */
import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { ScrollToPlugin } from "gsap/ScrollToPlugin";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useRef, type ReactNode, type RefObject } from "react";

gsap.registerPlugin(useGSAP, ScrollTrigger, ScrollToPlugin);
gsap.defaults({ ease: "expo.out", duration: 1 });
// Keep animations on the real clock: on a slow frame GSAP skips ahead instead of stretching the timeline,
// so intros always finish on time even on low-end laptops or busy CPUs.
gsap.ticker.lagSmoothing(0);

export { gsap, ScrollTrigger, useGSAP };

export const reducedMotion = () =>
  typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

/** Fade-lift-unblur every `.reveal` inside `scope` as it scrolls into view, in small staggered batches. */
export function useScrollReveal(scope: RefObject<HTMLElement | null>, deps: unknown[] = []) {
  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      // Reduced motion keeps the fade + blur-in but drops the upward movement.
      mm.add({ full: "(prefers-reduced-motion: no-preference)", reduce: "(prefers-reduced-motion: reduce)" }, (ctx) => {
        const full = Boolean(ctx.conditions?.full);
        const items = gsap.utils.toArray<HTMLElement>(".reveal:not([data-revealed])", scope.current);
        if (!items.length) return;
        gsap.set(items, { autoAlpha: 0, y: full ? 36 : 0, filter: "blur(8px)" });
        ScrollTrigger.batch(items, {
          start: "top 88%",
          once: true,
          onEnter: (batch) => {
            batch.forEach((el) => el.setAttribute("data-revealed", ""));
            gsap.to(batch, { autoAlpha: 1, y: 0, filter: "blur(0px)", duration: 1.15, stagger: 0.09, overwrite: true, clearProps: "filter" });
          },
        });
      });
      return () => mm.revert();
    },
    { scope, dependencies: deps },
  );
}

/** Smoothly scroll the window so `el` sits just under the floating navbar. */
export function scrollToElement(el: Element | null, offset = 88) {
  if (!el) return;
  if (reducedMotion()) {
    const y = el.getBoundingClientRect().top + window.scrollY - offset;
    window.scrollTo(0, y);
    return;
  }
  gsap.to(window, { duration: 1.1, ease: "power3.inOut", scrollTo: { y: el, offsetY: offset, autoKill: true } });
}

/** Magnetic hover: the child drifts toward the cursor and springs back on leave. */
export function Magnetic({ children, strength = 0.28, className = "" }: { children: ReactNode; strength?: number; className?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  useGSAP(
    () => {
      const el = ref.current;
      if (!el || reducedMotion() || !window.matchMedia("(hover: hover)").matches) return;
      const xTo = gsap.quickTo(el, "x", { duration: 0.6, ease: "power3.out" });
      const yTo = gsap.quickTo(el, "y", { duration: 0.6, ease: "power3.out" });
      const move = (e: PointerEvent) => {
        const r = el.getBoundingClientRect();
        xTo((e.clientX - (r.left + r.width / 2)) * strength);
        yTo((e.clientY - (r.top + r.height / 2)) * strength);
      };
      const leave = () => {
        gsap.to(el, { x: 0, y: 0, duration: 1.2, ease: "power3.out" });
      };
      el.addEventListener("pointermove", move);
      el.addEventListener("pointerleave", leave);
      return () => {
        el.removeEventListener("pointermove", move);
        el.removeEventListener("pointerleave", leave);
      };
    },
    { scope: ref },
  );
  return (
    <span ref={ref} className={`inline-block will-change-transform ${className}`}>
      {children}
    </span>
  );
}
