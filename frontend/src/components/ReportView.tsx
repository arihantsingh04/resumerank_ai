import {
  AlertTriangle,
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronDown,
  Copy,
  Download,
  Lightbulb,
  RotateCcw,
  Sparkles,
  X,
  XCircle,
} from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useRef, useState, type CSSProperties } from "react";
import { gsap, reducedMotion, scrollToElement, useGSAP, useScrollReveal } from "../lib/anim";
import type { HealthStatus, Report, SkillResult, Verdict } from "../lib/types";

const VERDICT: Record<Verdict, { label: string; cls: string; sticker: string; line: string }> = {
  strong: { label: "Strong match", cls: "bg-good-wash text-good", sticker: "!bg-gradient-to-b !from-[#5bd27a] !to-green", line: "You're ready to apply. Polish the small gaps below." },
  good: { label: "Good match", cls: "bg-tile text-ink", sticker: "sticker-blue", line: "A solid fit. A few targeted edits will make it stronger." },
  fair: { label: "Fair match", cls: "bg-warn-wash text-warn", sticker: "!bg-gradient-to-b !from-[#ffd666] !to-[#f5a800] !text-ink", line: "Some overlap, but key requirements aren't visible yet." },
  low: { label: "Low match", cls: "bg-bad-wash text-bad", sticker: "", line: "This resume doesn't show most of what the job asks for." },
};

const delay = (i: number) => ({ "--i": i }) as CSSProperties;

function Bar({ label, value, i }: { label: string; value: number; i: number }) {
  const ref = useRef<HTMLDivElement>(null);
  useGSAP(
    () => {
      const fill = ref.current?.querySelector<HTMLElement>("[data-fill]");
      if (!fill) return;
      if (reducedMotion()) return void gsap.set(fill, { width: `${value}%` });
      gsap.fromTo(fill, { width: "0%" }, { width: `${value}%`, duration: 1.6, delay: 0.35 + i * 0.12, ease: "expo.out" });
    },
    { scope: ref, dependencies: [value, i] },
  );
  return (
    <div ref={ref}>
      <div className="flex justify-between text-sm">
        <span className="font-semibold text-ink-2">{label}</span>
        <span className="font-bold tabular-nums">{Math.round(value)}</span>
      </div>
      <div className="mt-1.5 h-2 rounded-full bg-tile-2" role="meter" aria-label={label} aria-valuenow={Math.round(value)} aria-valuemin={0} aria-valuemax={100}>
        <div data-fill className="h-full w-0 rounded-full bg-ink" />
      </div>
    </div>
  );
}

function MatchedRow({ m }: { m: SkillResult }) {
  return (
    <li className="-mx-2 rounded-xl px-2 py-3 transition-colors duration-300 hover:bg-tile/60">
      <div className="flex items-start gap-2.5">
        <CheckCircle2 size={18} className="mt-0.5 shrink-0 text-good" aria-label="Found" />
        <div className="min-w-0">
          <p className="font-semibold">
            {m.requirement}
            <span className={`chip ml-2 !py-0 !text-[0.7rem] ${m.required ? "bg-tile text-ink-2" : "bg-tile text-ink"}`}>{m.required ? "Required" : "Bonus"}</span>
          </p>
          {m.evidence && (
            <p className="mt-1 text-[0.95rem] leading-relaxed text-ink-2">
              “<span className="highlight text-ink">{m.evidence}</span>”
              {m.source === "semantic" && <span className="ml-1 text-xs text-mute">(similar wording)</span>}
            </p>
          )}
        </div>
      </div>
    </li>
  );
}

function MissingRow({ m }: { m: SkillResult }) {
  const [open, setOpen] = useState(false);
  return (
    <li className="-mx-2 rounded-xl px-2 py-3 transition-colors duration-300 hover:bg-tile/60">
      <button type="button" onClick={() => setOpen(!open)} aria-expanded={open} className="flex w-full items-start gap-2.5 text-left">
        <XCircle size={18} className={`mt-0.5 shrink-0 ${m.required ? "text-bad" : "text-mute"}`} aria-label="Not found" />
        <span className="flex-1 font-semibold">
          {m.requirement}
          <span className={`chip ml-2 !py-0 !text-[0.7rem] ${m.required ? "bg-bad-wash text-bad" : "bg-tile text-mute"}`}>{m.required ? "Required" : "Bonus"}</span>
        </span>
        <motion.span animate={{ rotate: open ? 180 : 0 }} transition={{ type: "spring", stiffness: 300, damping: 22 }} className="mt-0.5 text-mute">
          <ChevronDown size={18} aria-hidden />
        </motion.span>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.p
            key="tip"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
            className="overflow-hidden pl-7 text-sm leading-relaxed text-ink-2"
          >
            <span className="block pt-1.5">{m.tip}</span>
          </motion.p>
        )}
      </AnimatePresence>
    </li>
  );
}

const HEALTH_ICON: Record<HealthStatus, { icon: typeof Check; cls: string; sr: string }> = {
  pass: { icon: Check, cls: "bg-good-wash text-good", sr: "Passed" },
  warn: { icon: AlertTriangle, cls: "bg-warn-wash text-warn", sr: "Needs attention" },
  fail: { icon: X, cls: "bg-bad-wash text-bad", sr: "Failed" },
};

function CopyChip({ text }: { text: string }) {
  const [done, setDone] = useState(false);
  return (
    <button
      type="button"
      onClick={() => navigator.clipboard?.writeText(text).then(() => {
        setDone(true);
        setTimeout(() => setDone(false), 1200);
      })}
      className="chip min-h-8 border border-line bg-tile text-ink transition-transform hover:-translate-y-px"
      aria-label={`Copy ${text}`}
    >
      {text} {done ? <Check size={13} aria-hidden className="motion-safe:animate-pop" /> : <Copy size={12} aria-hidden className="opacity-60" />}
    </button>
  );
}

interface Props {
  report: Report;
  onReset: () => void;
}

export default function ReportView({ report: r, onReset }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  useScrollReveal(ref, [r]);
  const v = VERDICT[r.verdict];
  const scoreRef = useRef<HTMLSpanElement>(null);
  useGSAP(
    () => {
      const el = scoreRef.current;
      if (!el) return;
      // Bring the score into view as soon as the report exists (it mounts after the scanning card exits).
      scrollToElement(document.getElementById("report-score"));
      const target = Math.round(r.score);
      if (reducedMotion()) return void (el.textContent = String(target));
      const o = { v: 0 };
      gsap.to(o, { v: target, duration: 1.8, delay: 0.25, ease: "expo.out", onUpdate: () => {
          el.textContent = String(Math.round(o.v));
        } });
      gsap.from("[data-verdict]", { scale: 0.7, rotate: -16, y: 12, autoAlpha: 0, filter: "blur(10px)", duration: 1.4, delay: 0.7, ease: "expo.out", clearProps: "filter" });
    },
    { scope: ref, dependencies: [r.score] },
  );
  const req = [...r.matched, ...r.missing].filter((m) => m.required);
  const reqHit = req.filter((m) => m.source).length;
  const summary = r.ai.status === "ok" && r.ai.summary ? r.ai.summary : v.line;
  const passed = r.health.filter((h) => h.status === "pass").length;

  return (
    <div ref={ref} className="flex flex-col gap-5">
      {/* Score header: big light numerals + tilted verdict sticker (reference stats style) */}
      <section id="report-score" className="tile relative scroll-mt-24 overflow-hidden p-6 sm:p-10" aria-labelledby="report-title">
        <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
          <div className="min-w-0">
            <p className="text-sm text-mute">Match score for</p>
            <h2 id="report-title" className="mt-1 text-3xl tracking-[-0.04em] sm:text-4xl">{r.job.title}</h2>
            <div className="mt-6 flex flex-wrap items-end gap-x-6 gap-y-4">
              <p className="leading-none" aria-label={`Match score ${Math.round(r.score)} out of 100`}>
                <span className="text-[6.5rem] font-light tracking-[-0.07em] tabular-nums sm:text-[8rem]" aria-hidden ref={scoreRef}>0</span>
                <span className="ml-1 text-2xl font-light text-mute" aria-hidden>/100</span>
              </p>
              <span data-verdict className="mb-6 inline-block"><span className={`sticker ${v.sticker} text-2xl sm:text-3xl`} style={{ "--r": "-6deg" } as CSSProperties}>{v.label}</span></span>
            </div>
            <p className="mt-2 max-w-xl text-ink-2">{summary}</p>
            <p className="mt-3 text-sm text-mute">
              {req.length ? `${reqHit} of ${req.length} required skills found` : "No specific skills listed in this job"}
              {r.years_experience != null && `, ${r.years_experience} years of experience detected`}
            </p>
            <div className="no-print mt-6 flex flex-wrap gap-2">
              <button type="button" onClick={onReset} className="btn-dark nudge">
                <RotateCcw size={15} aria-hidden /> Check another job
              </button>
              <button type="button" onClick={() => window.print()} className="btn-light">
                <Download size={15} aria-hidden /> Download report
              </button>
            </div>
          </div>
          <div className="panel flex w-full flex-col gap-4 p-5 lg:w-80">
            <p className="text-sm font-semibold">How it adds up</p>
            <Bar label="Overall fit" value={r.breakdown.semantic} i={0} />
            <Bar label="Skill coverage" value={r.breakdown.skills} i={1} />
            <Bar label="Experience" value={r.breakdown.experience} i={2} />
            {r.breakdown.ai != null && <Bar label="AI review" value={r.breakdown.ai} i={3} />}
          </div>
        </div>
      </section>

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]">
        {/* Skills */}
        <section className="reveal panel p-5 sm:p-6" style={delay(1)} aria-labelledby="skills-h">
          <h3 id="skills-h" className="text-lg font-bold">Skills the job asks for</h3>
          <p className="mt-0.5 text-sm text-mute">Highlighted lines are where we found each skill in your resume.</p>
          {r.matched.length > 0 && (
            <>
              <p className="mt-4 text-sm font-bold text-good">Found · {r.matched.length}</p>
              <ul className="divide-y divide-line">{r.matched.map((m) => <MatchedRow key={m.requirement} m={m} />)}</ul>
            </>
          )}
          {r.missing.length > 0 && (
            <>
              <p className="mt-4 text-sm font-bold text-bad">Not found · {r.missing.length} <span className="font-medium text-mute">(tap for how to fix)</span></p>
              <ul className="divide-y divide-line">{r.missing.map((m) => <MissingRow key={m.requirement} m={m} />)}</ul>
            </>
          )}
          {r.matched.length + r.missing.length === 0 && (
            <p className="mt-4 rounded-xl bg-tile p-4 text-sm text-ink-2">This job description didn't list recognisable skills, so the score leans on overall fit. Try a role template for a sharper check.</p>
          )}
        </section>

        <div className="flex flex-col gap-5">
          {/* Health */}
          <section className="reveal panel p-5 sm:p-6" style={delay(2)} aria-labelledby="health-h">
            <div className="flex items-baseline justify-between">
              <h3 id="health-h" className="text-lg font-bold">Resume health</h3>
              <span className="text-sm font-semibold text-mute">{passed}/{r.health.length} passed</span>
            </div>
            <ul className="mt-3 flex flex-col gap-2.5">
              {r.health.map((h) => {
                const { icon: Icon, cls, sr } = HEALTH_ICON[h.status];
                return (
                  <li key={h.id} className="flex items-start gap-3">
                    <span className={`grid size-7 shrink-0 place-items-center rounded-full ${cls}`}>
                      <Icon size={14} strokeWidth={2.75} aria-label={sr} />
                    </span>
                    <div className="min-w-0">
                      <p className="text-sm font-semibold">{h.label}</p>
                      <p className="text-sm text-mute">{h.detail}</p>
                    </div>
                  </li>
                );
              })}
            </ul>
          </section>

          {/* Quick wins */}
          <section className="reveal panel p-5 sm:p-6" style={delay(3)} aria-labelledby="tips-h">
            <h3 id="tips-h" className="flex items-center gap-2 text-lg font-bold">
              <Lightbulb size={18} className="text-warn" aria-hidden /> Quick wins
            </h3>
            <ol className="mt-3 flex list-decimal flex-col gap-2 pl-5 text-sm text-ink-2 marker:font-bold marker:text-mute">
              {r.tips.map((t) => <li key={t}>{t}</li>)}
            </ol>
          </section>
        </div>
      </div>

      {/* AI coach */}
      <section className="reveal panel relative overflow-hidden p-5 sm:p-6" style={delay(4)} aria-labelledby="ai-h">
        <h3 id="ai-h" className="relative flex items-center gap-2 text-lg font-bold">
          <span className="grid size-8 place-items-center rounded-lg bg-gradient-to-b from-[#2b2b2e] to-ink text-white"><Sparkles size={16} aria-hidden /></span>
          AI coach
        </h3>
        {r.ai.status === "ok" ? (
          <div className="relative mt-4 flex flex-col gap-6">
            {r.ai.suggestions.length > 0 && (
              <div className="grid gap-3 sm:grid-cols-2">
                {r.ai.suggestions.map((s, i) => (
                  <div key={s.title} className="lift rounded-2xl border border-line bg-tile p-4" data-i={i}>
                    <p className="font-bold">{s.title}</p>
                    <p className="mt-1 text-sm text-ink-2">{s.detail}</p>
                  </div>
                ))}
              </div>
            )}
            {r.ai.keywords_to_add.length > 0 && (
              <div>
                <p className="text-sm font-bold">Keywords to work in <span className="font-medium text-mute">(only if they're true for you)</span></p>
                <div className="mt-2 flex flex-wrap gap-1.5">{r.ai.keywords_to_add.map((k) => <CopyChip key={k} text={k} />)}</div>
              </div>
            )}
            {r.ai.bullet_rewrites.length > 0 && (
              <div>
                <p className="text-sm font-bold">Stronger bullet points</p>
                <ul className="mt-2 flex flex-col gap-3">
                  {r.ai.bullet_rewrites.map((b) => (
                    <li key={b.before} className="grid items-center gap-2 rounded-2xl border border-line p-4 md:grid-cols-[1fr_auto_1fr]">
                      <p className="text-sm text-mute line-through decoration-orange/50">{b.before}</p>
                      <ArrowRight size={16} className="hidden text-ink md:block" aria-label="becomes" />
                      <p className="text-sm font-medium text-ink">{b.after}</p>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {(r.ai.strengths.length > 0 || r.ai.gaps.length > 0) && (
              <div className="grid gap-4 sm:grid-cols-2">
                {r.ai.strengths.length > 0 && (
                  <div>
                    <p className="text-sm font-bold text-good">What works</p>
                    <ul className="mt-1.5 list-disc space-y-1 pl-5 text-sm text-ink-2">{r.ai.strengths.map((s) => <li key={s}>{s}</li>)}</ul>
                  </div>
                )}
                {r.ai.gaps.length > 0 && (
                  <div>
                    <p className="text-sm font-bold text-bad">What's missing</p>
                    <ul className="mt-1.5 list-disc space-y-1 pl-5 text-sm text-ink-2">{r.ai.gaps.map((s) => <li key={s}>{s}</li>)}</ul>
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="relative mt-3 flex flex-col items-start gap-1 rounded-2xl border border-dashed border-line-2 bg-tile p-5">
            <p className="font-semibold">
              {r.ai.status === "limited" && "You've reached today's AI suggestions limit."}
              {r.ai.status === "error" && "AI suggestions are unavailable right now."}
              {r.ai.status === "disabled" && "AI suggestions aren't switched on for this server."}
            </p>
            <p className="text-sm text-ink-2">
              Your score, skills evidence and health checks above are complete. They're computed locally.
              {r.ai.status === "limited" && " AI suggestions come back tomorrow."}
              {r.ai.status === "error" && " Try the check again in a minute."}
              {r.ai.status === "disabled" && " Add a Gemini API key to the server's .env to enable them."}
            </p>
          </div>
        )}
      </section>

      <p className="reveal text-center text-xs text-mute" style={delay(5)}>
        Checked {r.meta.resume_words} words in {(r.meta.ms / 1000).toFixed(1)}s · Your resume wasn't stored · AI suggestions can be wrong
      </p>
    </div>
  );
}
