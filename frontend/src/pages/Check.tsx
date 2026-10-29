import { useMutation } from "@tanstack/react-query";
import { AlertCircle, ArrowRight, Check as CheckIcon, RotateCw } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import Dropzone from "../components/Dropzone";
import { GlowButton, RollText, SwapLabel } from "../components/Fx";
import { Footer, Navbar } from "../components/Brand";
import { ReportArt, ResumeArt, ScanningArt } from "../components/Illustrations";
import JobInput, { MIN_JD_CHARS, type JobState } from "../components/JobInput";
import ReportView from "../components/ReportView";
import { ApiError, checkResume, type JobSource } from "../lib/api";
import { scrollToElement } from "../lib/anim";

const EASE = [0.16, 1, 0.3, 1] as const;

const STAGES = ["Reading your resume…", "Matching skills to the job…", "Checking resume health…", "Writing suggestions…"];

function Scanning() {
  const [stage, setStage] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setStage((s) => Math.min(s + 1, STAGES.length - 1)), 1400);
    return () => clearInterval(t);
  }, []);
  return (
    <div className="panel flex flex-col items-center px-6 py-12 text-center" role="status" aria-live="polite">
      <ScanningArt className="h-36 w-28" />
      <p className="mt-5 text-lg font-bold">{STAGES[stage]}</p>
      <div className="mt-4 flex gap-1.5" aria-hidden>
        {STAGES.map((s, i) => (
          <span key={s} className={`h-1.5 rounded-full transition-all duration-700 ease-[var(--ease-apple)] ${i <= stage ? "w-8 bg-ink" : "w-4 bg-line"}`} />
        ))}
      </div>
    </div>
  );
}

function EmptyReport() {
  return (
    <div className="panel flex flex-col items-center gap-2 border-dashed px-6 py-12 text-center">
      <ReportArt className="h-28 w-52" />
      <h2 className="mt-3 text-xl font-bold">Your match report shows up here</h2>
      <p className="max-w-md text-ink-2">
        Add your resume and choose a job above. You'll get a score, the lines that prove each skill, what's missing,
        and a resume health check.
      </p>
    </div>
  );
}

function jobSource(job: JobState): JobSource | null {
  if (job.mode === "template") return job.templateId ? { kind: "template", templateId: job.templateId } : null;
  if (job.mode === "file") return job.file ? { kind: "file", file: job.file } : null;
  return job.text.trim().length >= MIN_JD_CHARS ? { kind: "text", text: job.text, title: job.title } : null;
}

export default function Check() {
  const [params] = useSearchParams();
  const [resume, setResume] = useState<File | null>(null);
  const [job, setJob] = useState<JobState>(() => ({
    mode: "template",
    templateId: params.get("role"),
    file: null,
    text: "",
    title: "",
  }));
  const resultRef = useRef<HTMLDivElement>(null);
  const check = useMutation({ mutationFn: ({ r, j }: { r: File; j: JobSource }) => checkResume(r, j) });

  const source = jobSource(job);
  const reason = useMemo(() => {
    if (!resume && !source) return "Add your resume and choose a job to continue";
    if (!resume) return "Add your resume to continue";
    if (source) return null;
    if (job.mode === "template") return "Pick a role template";
    if (job.mode === "file") return "Upload the job description";
    return `Paste at least ${MIN_JD_CHARS} characters of the job description`;
  }, [resume, source, job.mode]);

  // Auto-scroll: to the scanning card while checking, then to the match score when it arrives.
  useEffect(() => {
    if (check.status === "pending") scrollToElement(resultRef.current);
    // On success the report scrolls itself into view once it has mounted (see ReportView).
    if (check.status === "error") scrollToElement(resultRef.current);
  }, [check.status]);

  const run = () => {
    if (!resume || !source) return;
    check.mutate({ r: resume, j: source });
  };
  const reset = () => {
    check.reset();
    setJob((j) => ({ ...j, templateId: j.mode === "template" ? null : j.templateId }));
    scrollToElement(document.body, 0);
  };
  const error = check.error instanceof ApiError ? check.error : check.error ? new ApiError(0, "unknown", "Something went wrong. Try again.") : null;

  return (
    <div className="min-h-screen overflow-x-clip">
      <Navbar cta={false} />
      <main className="relative mx-auto max-w-6xl px-4 pt-8 pb-16 sm:px-6 sm:pt-12">

        <header className="no-print relative">
          <motion.h1 initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.9, ease: EASE }} className="text-4xl sm:text-6xl">Check your resume</motion.h1>
          <motion.p initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.9, delay: 0.08, ease: EASE }} className="mt-2 max-w-2xl text-ink-2">
            Two steps. Nothing is stored: your files are read in memory and discarded.
          </motion.p>
        </header>

        <div className="no-print relative mt-8 grid gap-5 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
          <motion.section initial={{ opacity: 0, y: 28 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 1, delay: 0.14, ease: EASE }} className="panel self-start p-5 sm:p-6" aria-labelledby="step1">
            <StepTitle n={1} id="step1" title="Your resume" done={!!resume} />
            <div className="mt-4">
              <Dropzone label="Drop your resume or browse" hint="PDF or DOCX, up to 4 MB" file={resume} onFile={setResume} art={<ResumeArt className="h-full w-full" />} />
            </div>
            <div className="no-print mt-4">
              <GlowButton
                type="button"
                onClick={run}
                disabled={!!reason || check.isPending}
                aria-describedby="cta-reason"
                active={!reason}
                busy={check.isPending}
                className="flex w-full"
              >
                <span className="flex min-h-12 w-full items-center justify-center text-base">
                  <SwapLabel stateKey={check.isPending ? "busy" : check.isSuccess ? "done" : "idle"}>
                    {check.isPending ? (
                      <>
                        <span className="size-4 animate-spin rounded-full border-2 border-white/30 border-t-white" aria-hidden /> Checking…
                      </>
                    ) : check.isSuccess ? (
                      <>
                        <CheckIcon size={18} strokeWidth={3} aria-hidden /> Match ready, check again
                      </>
                    ) : (
                      <>
                        <RollText>Check match</RollText> <ArrowRight size={18} aria-hidden />
                      </>
                    )}
                  </SwapLabel>
                </span>
              </GlowButton>
              <AnimatePresence mode="wait" initial={false}>
                <motion.p
                  key={reason ?? (check.isPending ? "pending" : "ready")}
                  id="cta-reason"
                  aria-live="polite"
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -4 }}
                  transition={{ duration: 0.25 }}
                  className="mt-2 text-center text-sm text-mute"
                >
                  {reason ?? (check.isPending ? "This usually takes a few seconds." : "Ready when you are.")}
                </motion.p>
              </AnimatePresence>
            </div>
            <ul className="mt-5 flex flex-col gap-1.5 border-t border-line pt-4 text-xs text-mute">
              <li>Use the same file you'd send to recruiters.</li>
              <li>Scanned images can't be read. Export a text PDF from Word or Google Docs.</li>
            </ul>
          </motion.section>

          <motion.section initial={{ opacity: 0, y: 28 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 1, delay: 0.22, ease: EASE }} className="panel p-5 sm:p-6" aria-labelledby="step2">
            <StepTitle n={2} id="step2" title="The job" done={!!source} />
            <div className="mt-4">
              <JobInput value={job} onChange={setJob} />
            </div>
          </motion.section>
        </div>

        <div ref={resultRef} className="relative mt-10 scroll-mt-20" aria-live="polite">
          <AnimatePresence mode="wait">
          {check.isPending && (
            <motion.div key="scan" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, scale: 0.98 }} transition={{ duration: 0.5, ease: EASE }}>
              <Scanning />
            </motion.div>
          )}
          {!check.isPending && error && (
            <motion.div key="err" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0, x: [0, -6, 6, -3, 0] }} transition={{ duration: 0.5 }} role="alert" className="panel flex flex-col items-start gap-3 border-bad/30 p-6 sm:flex-row sm:items-center">
              <AlertCircle size={22} className="shrink-0 text-bad" aria-hidden />
              <div className="flex-1">
                <p className="font-bold">We couldn't check that.</p>
                <p className="text-ink-2">{error.message}</p>
              </div>
              <button type="button" onClick={run} disabled={!!reason} className="btn-light">
                <RotateCw size={15} aria-hidden /> Try again
              </button>
            </motion.div>
          )}
          {!check.isPending && check.data && (
            <motion.div key="report" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }}>
              <ReportView report={check.data} onReset={reset} />
            </motion.div>
          )}
          {check.isIdle && (
            <motion.div key="empty" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.8, delay: 0.3, ease: EASE }}>
              <EmptyReport />
            </motion.div>
          )}
          </AnimatePresence>
        </div>
      </main>
      <Footer />
    </div>
  );
}

function StepTitle({ n, id, title, done }: { n: number; id: string; title: string; done: boolean }) {
  return (
    <h2 id={id} className="flex items-center gap-3 text-lg font-bold">
      <span
        className={`grid size-8 place-items-center rounded-full text-sm font-extrabold transition-all duration-300 ${
          done ? "bg-good text-white motion-safe:animate-pop" : "bg-tile text-ink"
        }`}
        aria-hidden
      >
        {done ? <CheckIcon size={16} strokeWidth={3} /> : n}
      </span>
      {title}
      <span className="sr-only">{done ? "(done)" : `(step ${n})`}</span>
    </h2>
  );
}
