import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  ArrowRight,
  ChevronDown,
  FileSearch,
  FileText,
  Gauge,
  HeartPulse,
  LayoutGrid,
  Lock,
  Sparkles,
  TrendingUp,
  XCircle,
  Zap,
  type LucideIcon,
} from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useMemo, useRef, useState, type CSSProperties } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Footer, Navbar, StickerLink } from "../components/Brand";
import { GlowLink, RollText, spotlight } from "../components/Fx";
import { getTemplates } from "../lib/api";
import { Magnetic, gsap, useGSAP, useScrollReveal } from "../lib/anim";
import { iconFor } from "../lib/icons";
import type { TemplateSummary } from "../lib/types";

function Pill({ children }: { children: string }) {
  return (
    <span className="pill">
      <Sparkles size={13} aria-hidden /> {children}
    </span>
  );
}

/* ── Hero ──────────────────────────────────────────────────────── */

function Hero() {
  const ref = useRef<HTMLElement>(null);
  useGSAP(
    () => {
      const mm = gsap.matchMedia();
      // Full motion normally; with "reduce motion" on (e.g. Windows animation effects off) the same sequence
      // runs as a pure fade + blur-in: no sliding, scaling, rotation or parallax.
      mm.add({ full: "(prefers-reduced-motion: no-preference)", reduce: "(prefers-reduced-motion: reduce)" }, (ctx) => {
        const full = Boolean(ctx.conditions?.full);
        const m = (v: number) => (full ? v : 0); // movement amount, zeroed under reduced motion
        const s = (v: number) => (full ? v : 1); // scale amount, neutral under reduced motion
        const q = gsap.utils.selector(ref);
        const nav = document.querySelector("header");
        const blurIn = { autoAlpha: 1, y: 0, scale: 1, filter: "blur(0px)" };

        // Hide everything synchronously, before first paint (useGSAP runs as a layout effect),
        // so nothing flashes and then jumps.
        gsap.set(nav, { autoAlpha: 0, y: m(-18), filter: "blur(6px)" });
        gsap.set(q("[data-hero=pill]"), { autoAlpha: 0, y: m(14), filter: "blur(6px)" });
        gsap.set(q("[data-word]"), { autoAlpha: 0, y: m(36), filter: "blur(10px)" });
        gsap.set(q("[data-hero=orb]"), { autoAlpha: 0, scale: s(0.55), rotate: m(-40), filter: "blur(6px)" });
        gsap.set(q("[data-rings]"), { autoAlpha: 0, scale: s(0.35) });
        gsap.set(q("[data-ring]"), { scale: s(0.6) });
        gsap.set(q("[data-hero=sticker], [data-hero=sticker-m]"), { autoAlpha: 0, y: m(46), rotate: m(9), scale: s(0.86), filter: "blur(8px)" });
        gsap.set(q("[data-hero=text]"), { autoAlpha: 0, y: m(18), filter: "blur(6px)" });
        gsap.set(q("[data-hero=cta]"), { autoAlpha: 0, y: m(18), scale: s(0.94), filter: "blur(8px)" });
        gsap.set(q("[data-hero=cta] .roll > span:first-child"), { autoAlpha: 0, filter: "blur(6px)", y: m(6) });
        gsap.set(q("[data-hero=cta] .halo"), { opacity: 0 });
        gsap.set(q("[data-hero=link]"), { autoAlpha: 0, filter: "blur(6px)" });

        // GPU layer hints only while the intro runs (removed at the end to free memory).
        const animated = [nav, ...q("[data-word], [data-hero], [data-rings]")].filter(Boolean);
        gsap.set(animated, { willChange: "transform, opacity, filter" });

        // One continuous, overlapping sequence with soft ease-outs: no bounces, no hard stops.
        const tl = gsap.timeline({ paused: true, defaults: { ease: "expo.out", duration: 1.4 } });
        tl.to(nav, { ...blurIn, duration: 1.2, ease: "power3.out" }, 0)
          .to(q("[data-hero=pill]"), { ...blurIn, duration: 1.2 }, 0.15)
          .to(q("[data-word]"), { ...blurIn, duration: 1.6, stagger: 0.11 }, 0.25)
          .to(q("[data-hero=orb]"), { ...blurIn, rotate: 0, duration: 1.8, stagger: 0.12 }, 0.45)
          .to(q("[data-rings]"), { autoAlpha: 1, scale: 1, duration: 2.2 }, 0.6)
          .to(q("[data-ring]"), { scale: 1, duration: 2.4, stagger: 0.14 }, 0.6)
          .to(q("[data-hero=sticker], [data-hero=sticker-m]"), { ...blurIn, rotate: 0, duration: 1.9 }, 0.8)
          .to(q("[data-hero=text]"), { ...blurIn, duration: 1.4 }, 0.85)
          .to(q("[data-hero=cta]"), { ...blurIn, duration: 1.4 }, 1.0)
          .to(q("[data-hero=cta] .roll > span:first-child"), { autoAlpha: 1, filter: "blur(0px)", y: 0, duration: 1.1, clearProps: "transform" }, 1.25)
          .to(q("[data-hero=cta] .halo"), { opacity: 0.55, duration: 1.6, ease: "power2.inOut", clearProps: "opacity" }, 1.35)
          .to(q("[data-hero=link]"), { autoAlpha: 1, filter: "blur(0px)", duration: 1.2 }, 1.3)
          .set(animated, { clearProps: "filter,willChange" });

        // Start once the web fonts are ready so the headline never re-flows mid-animation.
        let started = false;
        const start = () => {
          if (!started) {
            started = true;
            tl.play();
          }
        };
        document.fonts?.ready.then(start);
        const fallback = window.setTimeout(start, 900);

        // Gentle parallax while scrolling past the hero (on wrappers, so it never fights the intro).
        if (full) gsap.to(q("[data-parallax]"), { y: -70, ease: "none", scrollTrigger: { trigger: ref.current, start: "top top", end: "bottom top", scrub: 0.8 } });
        if (full) gsap.to(q("[data-orb-icon]"), { rotate: 140, ease: "none", scrollTrigger: { trigger: ref.current, start: "top top", end: "bottom top", scrub: 1 } });
        return () => window.clearTimeout(fallback);
      });
      return () => mm.revert();
    },
    { scope: ref },
  );
  return (
    <section ref={ref} className="relative mx-auto max-w-6xl px-4 pt-16 sm:px-6 sm:pt-24">
      <div data-hero="sticker" className="absolute top-[21.5rem] right-6 hidden lg:block xl:right-14">
        <div data-parallax>
          <Magnetic strength={0.22}>
            <StickerLink to="/check" size="text-6xl xl:text-7xl">Check</StickerLink>
          </Magnetic>
        </div>
      </div>

      <span data-hero="pill" className="pill !bg-white">
        <span className="flex -space-x-1.5" aria-hidden>
          <span className="size-5 rounded-full border-2 border-white bg-orange" />
          <span className="size-5 rounded-full border-2 border-white bg-blue" />
          <span className="size-5 rounded-full border-2 border-white bg-pink" />
        </span>
        Free, private, no sign-up
      </span>
      <h1 className="mt-6 text-[clamp(3.4rem,10.5vw,8.4rem)] leading-[0.95] font-medium tracking-[-0.055em]">
        <span className="sr-only">Good resumes get hired</span>
        <span aria-hidden className="block">
          <span data-word className="inline-block whitespace-nowrap">
            g
            <span data-hero="orb" className="orb bg-gradient-to-b from-[#ff7ab8] to-pink">
              <span data-orb-icon className="grid place-items-center"><FileText className="size-[0.36em]" strokeWidth={2.5} /></span>
            </span>
            <span data-hero="orb" className="orb -ml-[0.12em] bg-gradient-to-b from-[#55baff] to-blue">
              <span data-orb-icon className="grid place-items-center"><Zap className="size-[0.38em]" strokeWidth={2.5} fill="currentColor" /></span>
            </span>
            d
          </span>{" "}
          <span data-word className="inline-block">resumes</span>
          <br />
          <span data-word className="inline-block">get</span>{" "}
          <span data-word className="inline-block">hired.</span>
        </span>
      </h1>

      <div className="mt-10 flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-xl">
          <p data-hero="text" className="text-lg leading-relaxed text-ink-2">
            Compare your resume with any job and see what's missing before a recruiter does.
          </p>
          <div className="mt-6 flex flex-wrap items-center gap-5">
            <span data-hero="cta" className="inline-block">
              <Magnetic strength={0.2}>
                <GlowLink to="/check" label="Check my resume" icon={<ArrowRight size={17} aria-hidden />} className="!min-h-12 !px-6 text-base" />
              </Magnetic>
            </span>
            <a data-hero="link" href="#how" className="nav-link text-sm font-medium text-ink-2 hover:text-ink">See how it works</a>
          </div>
        </div>
        <div data-hero="sticker-m" className="lg:hidden">
          <StickerLink to="/check" size="text-5xl" rotate={-8}>Check</StickerLink>
        </div>
      </div>
    </section>
  );
}

/* ── Bento ─────────────────────────────────────────────────────── */

function Bento({ roles }: { roles: TemplateSummary[] }) {
  const circles = roles.slice(0, 6);
  return (
    <section id="how" className="mx-auto max-w-6xl scroll-mt-24 px-4 pt-28 sm:px-6">
      <div className="reveal text-center">
        <Pill>How it works</Pill>
        <h2 className="mx-auto mt-4 max-w-3xl text-4xl sm:text-5xl">Everything you need before you apply</h2>
      </div>

      <div className="mt-12 grid gap-4 lg:grid-cols-2">
        <div onPointerMove={spotlight} className="tile spotlight reveal relative overflow-hidden p-6 sm:p-8" style={{ "--i": 1 } as CSSProperties}>
          <span className="icon-sq bg-orange"><LayoutGrid size={18} aria-hidden /></span>
          <h3 className="mt-5 max-w-xs text-2xl tracking-[-0.03em]">14 ready-made BTech role templates</h3>
          <p className="mt-2 max-w-xs text-sm text-mute">Backend, Flutter, DevOps, ML and more, written for freshers.</p>
          <Link to="/check" className="btn-dark group nudge mt-6 !min-h-10 text-sm"><RollText>Try a template</RollText> <ArrowRight size={15} aria-hidden /></Link>
          <div className="mt-8 grid grid-cols-3 gap-3 sm:absolute sm:right-6 sm:bottom-6 sm:mt-0 sm:w-[19rem]">
            {(circles.length ? circles : Array.from({ length: 6 }, () => null)).map((t, i) => {
              const Icon = t ? iconFor(t.icon) : LayoutGrid;
              return (
                <Link
                  key={t?.id ?? i}
                  to={t ? `/check?role=${t.id}` : "/check"}
                  aria-label={t ? `Check against ${t.title}` : "Check"}
                  className={`grid aspect-square place-items-center rounded-full bg-white shadow-[0_8px_24px_-14px_rgb(18_18_18/0.35)] transition-transform duration-700 ease-[var(--ease-apple)] hover:-translate-y-1.5 hover:scale-110 hover:rotate-6 ${i === 0 || i === 2 ? "sm:col-start-auto" : ""}`}
                >
                  {/* Icons blur in when the role list arrives instead of popping in. */}
                  <motion.span
                    key={t?.id ?? "placeholder"}
                    initial={{ opacity: 0, scale: 0.7, filter: "blur(8px)" }}
                    animate={{ opacity: t ? 1 : 0.25, scale: 1, filter: "blur(0px)" }}
                    transition={{ duration: 0.9, delay: i * 0.06, ease: [0.16, 1, 0.3, 1] }}
                    className="grid place-items-center"
                  >
                    <Icon className={`size-8 ${["text-orange", "text-blue", "text-ink", "text-purple", "text-pink", "text-green"][i]}`} strokeWidth={2} aria-hidden />
                  </motion.span>
                </Link>
              );
            })}
          </div>
        </div>

        <div className="grid gap-4">
          <div onPointerMove={spotlight} className="tile spotlight reveal flex flex-col gap-6 overflow-hidden p-6 sm:flex-row sm:items-end sm:p-8" style={{ "--i": 2 } as CSSProperties}>
            <div className="sm:w-40">
              <span className="icon-sq bg-blue"><FileSearch size={18} aria-hidden /></span>
              <p className="mt-10 text-sm text-ink-2">See which skills your resume actually proves</p>
            </div>
            <div className="panel flex-1 p-4 sm:-mr-10 sm:-mb-10">
              <div className="flex items-center justify-between rounded-xl border border-line p-3">
                <div>
                  <p className="text-xs text-mute">Skills found</p>
                  <p className="text-3xl font-medium tracking-[-0.04em]">8 of 12</p>
                </div>
                <span className="grid size-10 place-items-center rounded-full bg-tile"><Gauge size={18} aria-hidden /></span>
              </div>
              <ul className="mt-3 flex flex-col gap-2.5 text-sm">
                {[
                  ["FastAPI", "Found", "bg-green"],
                  ["Docker", "Missing", "bg-orange"],
                  ["PostgreSQL", "Found", "bg-green"],
                ].map(([s, label, c]) => (
                  <li key={s} className="flex items-center justify-between gap-2">
                    <span className="flex items-center gap-2"><span className={`size-1.5 rounded-full ${c}`} />{s}</span>
                    <span className={`pct ${c}`}>{label}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          <div onPointerMove={spotlight} className="tile spotlight reveal flex items-center justify-between gap-4 overflow-hidden p-6 sm:p-8" style={{ "--i": 3 } as CSSProperties}>
            <div className="max-w-[12rem]">
              <h3 className="text-2xl tracking-[-0.03em]">Fixes in seconds</h3>
              <p className="mt-2 text-sm text-mute">Clear suggestions and stronger bullet points, based on what you've actually done.</p>
            </div>
            <div className="-mr-12 flex items-center rounded-full bg-white/70 p-2 shadow-[0_10px_30px_-18px_rgb(18_18_18/0.5)]">
              <span className="orb !size-20 bg-gradient-to-b from-[#5bd27a] to-green text-3xl"><Sparkles className="size-8" aria-hidden /></span>
              <span className="orb -ml-2 !size-20 bg-gradient-to-b from-[#ffd666] to-yellow text-3xl"><FileText className="size-8" aria-hidden /></span>
              <span className="orb -ml-2 !size-20 bg-gradient-to-b from-[#55baff] to-blue text-3xl"><TrendingUp className="size-8" aria-hidden /></span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ── Features ──────────────────────────────────────────────────── */

const FEATURES: { icon: LucideIcon; color: string; title: string; text: string }[] = [
  { icon: Gauge, color: "bg-blue", title: "Match score", text: "One clear number for how well your resume fits the job." },
  { icon: FileSearch, color: "bg-pink", title: "Skill proof", text: "See the exact line in your resume that shows each skill." },
  { icon: XCircle, color: "bg-orange", title: "Missing skills", text: "Know which must-have skills recruiters won't find, and how to add them." },
  { icon: HeartPulse, color: "bg-yellow", title: "Resume health", text: "Quick checks for length, contact details, sections and measurable results." },
  { icon: Sparkles, color: "bg-green", title: "AI coach", text: "Specific tips and rewritten bullet points you can use right away." },
  { icon: Lock, color: "bg-purple", title: "Private by design", text: "No account needed. Your resume is never saved." },
];

function Features() {
  return (
    <section className="mx-auto max-w-6xl px-4 pt-28 sm:px-6">
      <h2 className="reveal text-[clamp(2.8rem,7.5vw,6rem)] leading-[0.98] tracking-[-0.055em]">
        Fix your resume in{" "}
        <span className="sticker sticker-blue !gap-0 align-middle !text-[0.8em] [--r:-4deg]">30s</span>
        <br />
        <span className="text-[#a6a6ab]">before you</span> apply
      </h2>
      <div className="mt-14 grid gap-x-10 gap-y-12 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map(({ icon: Icon, color, title, text }, i) => (
          <div key={title} className="group reveal" style={{ "--i": i % 3 } as CSSProperties}>
            <span className={`icon-sq tilt-icon ${color}`}><Icon size={17} aria-hidden /></span>
            <h3 className="mt-5 text-xl tracking-[-0.03em]">{title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-mute">{text}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ── Privacy panel ─────────────────────────────────────────────── */

function PrivacyPanel({ roles }: { roles: TemplateSummary[] }) {
  const navigate = useNavigate();
  const [role, setRole] = useState("");
  return (
    <section id="privacy" className="mx-auto max-w-6xl scroll-mt-24 px-4 pt-28 sm:px-6">
      <div onPointerMove={spotlight} className="tile spotlight reveal overflow-hidden p-6 sm:p-10">
        <div className="flex flex-col justify-between gap-6 lg:flex-row">
          <div>
            <Pill>Privacy</Pill>
            <h2 className="mt-4 max-w-lg text-4xl sm:text-5xl">Honest feedback before you hit apply</h2>
          </div>
          <p className="max-w-sm text-sm leading-relaxed text-mute lg:pt-12">
            Your resume is read, scored and forgotten. Contact details are removed before anything reaches the AI
            coach, and nothing is saved.
          </p>
        </div>
        <form
          className="mt-10 flex flex-col gap-4 border-t border-line pt-6 md:flex-row md:items-center md:justify-between"
          onSubmit={(e) => {
            e.preventDefault();
            navigate(role ? `/check?role=${role}` : "/check");
          }}
        >
          <p className="max-w-md text-xs leading-relaxed text-mute">
            Pick a role to start. You'll add your resume on the next screen.
          </p>
          <div className="flex w-full items-center gap-2 rounded-full border border-line bg-white p-1.5 md:w-auto">
            <label htmlFor="quick-role" className="sr-only">Role</label>
            <select id="quick-role" value={role} onChange={(e) => setRole(e.target.value)} className="min-w-0 flex-1 bg-transparent px-3 text-sm outline-none md:w-56">
              <option value="">Any role</option>
              {roles.map((t) => <option key={t.id} value={t.id}>{t.title}</option>)}
            </select>
            <button className="btn-dark group nudge !min-h-9 shrink-0 text-sm"><RollText>Check now</RollText> <ArrowRight size={14} aria-hidden /></button>
          </div>
        </form>
      </div>
    </section>
  );
}

/* ── Roles explorer ────────────────────────────────────────────── */

function Roles({ roles }: { roles: TemplateSummary[] }) {
  const categories = useMemo(() => [...new Set(roles.map((t) => t.category))], [roles]);
  const [cat, setCat] = useState<string | null>(null);
  const active = cat ?? categories[0];
  const inCat = roles.filter((t) => t.category === active);
  const [open, setOpen] = useState<string | null>(null);
  const openId = open && inCat.some((t) => t.id === open) ? open : inCat[0]?.id;

  return (
    <section id="roles" className="mx-auto grid max-w-6xl scroll-mt-24 gap-10 px-4 pt-28 sm:px-6 lg:grid-cols-[0.8fr_1.2fr]">
      <div className="reveal">
        <Pill>Roles</Pill>
        <h2 className="mt-4 text-4xl sm:text-5xl">Sharper feedback for every role</h2>
        <div role="tablist" aria-label="Role categories" className="mt-8 flex flex-col gap-2">
          {categories.map((c) => {
            const sel = c === active;
            return (
              <button
                key={c}
                role="tab"
                aria-selected={sel}
                onClick={() => setCat(c)}
                className={`flex min-h-11 items-center gap-2.5 rounded-xl border px-4 text-left text-sm font-medium transition-all duration-200 ${
                  sel ? "border-ink bg-gradient-to-b from-[#2b2b2e] to-ink text-white shadow-[0_8px_18px_-10px_rgb(18_18_18/0.7)]" : "border-line bg-white text-ink-2 hover:border-line-2"
                }`}
              >
                <LayoutGrid size={15} aria-hidden /> {c}
              </button>
            );
          })}
          {categories.length === 0 && Array.from({ length: 5 }, (_, i) => <span key={i} className="skeleton h-11" />)}
        </div>
      </div>

      <div className="reveal flex flex-col gap-3 lg:pt-24" role="tabpanel" style={{ "--i": 1 } as CSSProperties}>
        {inCat.map((t) => {
          const isOpen = t.id === openId;
          return (
            <div key={t.id} onPointerMove={spotlight} className={`spotlight rounded-2xl border border-line bg-white px-5 transition-shadow duration-500 ${isOpen ? "shadow-[0_10px_26px_-18px_rgb(18_18_18/0.4)]" : ""}`}>
              <button type="button" onClick={() => setOpen(isOpen ? "" : t.id)} aria-expanded={isOpen} className="flex min-h-14 w-full items-center justify-between gap-3 text-left font-medium">
                {t.title}
                <motion.span
                  animate={{ rotate: isOpen ? 180 : 0, backgroundColor: isOpen ? "#f4f4f5" : "rgba(244,244,245,0)" }}
                  transition={{ type: "spring", stiffness: 300, damping: 24 }}
                  className="grid size-8 place-items-center rounded-lg"
                >
                  <ChevronDown size={17} aria-hidden />
                </motion.span>
              </button>
              <AnimatePresence initial={false}>
                {isOpen && (
                  <motion.div
                    key="body"
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                    className="overflow-hidden"
                  >
                    <p className="pb-5 text-sm leading-relaxed text-mute">
                      {t.summary} Must-haves: {t.required_skills.join(", ")}.{" "}
                      <Link to={`/check?role=${t.id}`} className="font-semibold text-ink underline underline-offset-4">Check against this role</Link>
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </div>
    </section>
  );
}

/* ── Rewrites carousel ─────────────────────────────────────────── */

const REWRITES = [
  { role: "Backend Developer", before: "Worked on APIs for the college project.", after: "Built 12 REST APIs in FastAPI for a placement portal used by 800+ students." },
  { role: "Flutter Developer", before: "Made an app in Flutter.", after: "Shipped a Flutter expense tracker with Firebase sync; 1,200 Play Store installs." },
  { role: "DevOps Engineer", before: "Responsible for deployment.", after: "Automated deployments with GitHub Actions and Docker, cutting release time from 2 hours to 10 minutes." },
  { role: "Data Analyst", before: "Helped with reports in Excel.", after: "Built a Power BI dashboard tracking attendance for 3,000 students, used weekly by faculty." },
  { role: "QA / SDET Engineer", before: "Did testing of the website.", after: "Wrote 140 Playwright tests covering checkout, catching 9 regressions before release." },
];

function Rewrites() {
  const [i, setI] = useState(0);
  const go = (d: number) => setI((x) => (x + d + REWRITES.length) % REWRITES.length);
  return (
    <section className="mx-auto max-w-6xl overflow-hidden px-4 pt-28 sm:px-6" aria-roledescription="carousel" aria-label="Example bullet rewrites">
      <h2 className="reveal text-center text-[clamp(2.6rem,7vw,5.6rem)] leading-[1] tracking-[-0.055em]">
        Turn{" "}
        <span className="sticker sticker-blue !gap-0 align-middle !text-[0.75em] [--r:-5deg]">weak</span> bullets
        <br />
        into interviews
      </h2>

      <div className="relative mt-16 h-[22rem]" onKeyDown={(e) => (e.key === "ArrowRight" ? go(1) : e.key === "ArrowLeft" ? go(-1) : null)}>
        {REWRITES.map((r, k) => {
          let off = k - i;
          if (off > 2) off -= REWRITES.length;
          if (off < -2) off += REWRITES.length;
          const center = off === 0;
          // Coverflow: each card sits on an ellipse. sin(angle) gives horizontal position,
          // cos(angle) is depth (1 = front, -1 = back) and drives scale, opacity, tilt and z-order together.
          const angle = off * (Math.PI / 4.2);
          const front = (Math.cos(angle) + 1) / 2;
          return (
            <motion.article
              key={r.role}
              aria-hidden={!center}
              initial={false}
              animate={{
                x: `${Math.sin(angle) * 118}%`,
                y: (1 - front) * 40,
                rotate: off * 5,
                rotateY: -Math.sin(angle) * 22,
                scale: 0.72 + 0.28 * front,
                opacity: 0.25 + 0.75 * front,
              }}
              style={{ zIndex: Math.round(front * 10), transformPerspective: 1200 }}
              transition={{ type: "spring", stiffness: 170, damping: 24, mass: 0.9 }}
              drag={center ? "x" : false}
              dragConstraints={{ left: 0, right: 0 }}
              dragElastic={0.35}
              onDragEnd={(_, info) => {
                if (info.offset.x < -60) go(1);
                else if (info.offset.x > 60) go(-1);
              }}
              whileHover={center ? { y: -6 } : undefined}
              className={`absolute top-0 left-1/2 -ml-[8.5rem] w-[17rem] rounded-[22px] p-6 sm:-ml-[9.5rem] sm:w-[19rem] ${center ? "cursor-grab active:cursor-grabbing" : ""} ${
                center ? "bg-gradient-to-b from-[#2b2b2e] to-ink text-white shadow-[0_30px_60px_-30px_rgb(18_18_18/0.8)]" : "border border-line bg-tile text-ink"
              }`}
            >
              <p className={`text-xs font-semibold ${center ? "text-white/60" : "text-mute"}`}>{r.role}</p>
              <p className={`mt-4 text-sm line-through ${center ? "text-white/50 decoration-orange" : "text-mute"}`}>{r.before}</p>
              <p className="mt-3 text-lg leading-snug font-medium tracking-[-0.02em]">“{r.after}”</p>
              <p className={`mt-6 flex items-center gap-2 text-xs ${center ? "text-white/60" : "text-mute"}`}>
                <span className="icon-sq !size-7 !rounded-lg bg-green"><Sparkles size={13} aria-hidden /></span> AI coach rewrite
              </p>
            </motion.article>
          );
        })}
      </div>
      <div className="flex items-center justify-center gap-3">
        <button type="button" onClick={() => go(-1)} className="grid size-10 place-items-center rounded-full border border-line hover:border-line-2" aria-label="Previous example">
          <ArrowLeft size={16} aria-hidden />
        </button>
        <div className="flex gap-1.5">
          {REWRITES.map((r, k) => (
            <button key={r.role} type="button" onClick={() => setI(k)} aria-label={`Show ${r.role} example`} aria-current={k === i} className={`h-2 rounded-full transition-all duration-300 ${k === i ? "w-10 bg-ink-2" : "w-4 bg-line-2"}`} />
          ))}
        </div>
        <button type="button" onClick={() => go(1)} className="grid size-10 place-items-center rounded-full border border-line hover:border-line-2" aria-label="Next example">
          <ArrowRight size={16} aria-hidden />
        </button>
      </div>
      <p className="mt-4 text-center text-xs text-mute">Illustrative examples. Your rewrites are based only on what your resume says.</p>
    </section>
  );
}

export default function Landing() {
  const ref = useRef<HTMLDivElement>(null);
  const { data } = useQuery({ queryKey: ["templates"], queryFn: getTemplates, staleTime: Infinity });
  const roles = data ?? [];
  useScrollReveal(ref, [roles.length]);
  return (
    <div ref={ref} className="min-h-screen overflow-x-clip pt-3">
      <Navbar />
      <main>
        <Hero />
        <Bento roles={roles} />
        <Features />
        <PrivacyPanel roles={roles} />
        <Roles roles={roles} />
        <Rewrites />
        <section className="reveal mx-auto max-w-6xl px-4 pt-28 text-center sm:px-6">
          <h2 className="text-4xl sm:text-5xl">Ready when you are</h2>
          <p className="mx-auto mt-3 max-w-md text-mute">Drop in your resume and see your match in under a minute.</p>
          <span className="mt-8 inline-block">
            <Magnetic strength={0.2}>
              <GlowLink to="/check" label="Check my resume" icon={<ArrowRight size={17} aria-hidden />} className="!min-h-12 !px-7 text-base" />
            </Magnetic>
          </span>
        </section>
      </main>
      <Footer />
    </div>
  );
}
