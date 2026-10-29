import { ClipboardType, FileUp, LayoutGrid, type LucideIcon } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useRef, type KeyboardEvent } from "react";
import Dropzone from "./Dropzone";
import { JobArt } from "./Illustrations";
import TemplatePicker from "./TemplatePicker";

export type JobMode = "template" | "file" | "text";

export interface JobState {
  mode: JobMode;
  templateId: string | null;
  file: File | null;
  text: string;
  title: string;
}

export const MIN_JD_CHARS = 50;

const TABS: { id: JobMode; label: string; short: string; icon: LucideIcon }[] = [
  { id: "template", label: "Role templates", short: "Templates", icon: LayoutGrid },
  { id: "file", label: "Upload JD", short: "Upload", icon: FileUp },
  { id: "text", label: "Paste text", short: "Paste", icon: ClipboardType },
];

/** Three ways to give the job: template, JD file, or pasted text. Tabs with a sliding indicator. */
export default function JobInput({ value, onChange }: { value: JobState; onChange: (v: JobState) => void }) {
  const refs = useRef<Record<JobMode, HTMLButtonElement | null>>({ template: null, file: null, text: null });

  const select = (mode: JobMode) => onChange({ ...value, mode });
  const onKey = (e: KeyboardEvent) => {
    const i = TABS.findIndex((t) => t.id === value.mode);
    const next = e.key === "ArrowRight" ? (i + 1) % TABS.length : e.key === "ArrowLeft" ? (i + TABS.length - 1) % TABS.length : -1;
    if (next >= 0) {
      e.preventDefault();
      select(TABS[next].id);
      refs.current[TABS[next].id]?.focus();
    }
  };
  const chars = value.text.trim().length;

  return (
    <div>
      <div role="tablist" aria-label="How to add the job" onKeyDown={onKey} className="relative flex rounded-full bg-tile p-1">
        {TABS.map(({ id, label, short, icon: Icon }) => (
          <button
            key={id}
            ref={(el) => {
              refs.current[id] = el;
            }}
            role="tab"
            type="button"
            id={`tab-${id}`}
            aria-selected={value.mode === id}
            aria-controls={`panel-${id}`}
            tabIndex={value.mode === id ? 0 : -1}
            onClick={() => select(id)}
            className={`relative isolate flex min-h-10 min-w-0 flex-1 items-center justify-center gap-1.5 rounded-full px-2 text-sm font-semibold transition-colors ${value.mode === id ? "text-ink" : "text-mute hover:text-ink-2"}`}
          >
            {value.mode === id && (
              // Shared-layout highlight: Motion glides it between tabs with a spring (no manual measuring).
              <motion.span
                layoutId="job-tab-pill"
                aria-hidden
                className="absolute inset-0 -z-10 rounded-full bg-white shadow-[0_1px_3px_rgb(18_18_18/0.12)]"
                transition={{ type: "spring", stiffness: 380, damping: 32 }}
              />
            )}
            <Icon size={15} aria-hidden className="hidden shrink-0 sm:block" /> <span className="truncate sm:hidden">{short}</span><span className="hidden truncate sm:inline">{label}</span>
          </button>
        ))}
      </div>

      <div id={`panel-${value.mode}`} role="tabpanel" aria-labelledby={`tab-${value.mode}`} className="mt-4">
        <AnimatePresence mode="wait" initial={false}>
        <motion.div
          key={value.mode}
          initial={{ opacity: 0, y: 10, filter: "blur(4px)" }}
          animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
          exit={{ opacity: 0, y: -6, filter: "blur(4px)" }}
          transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
        >
          {value.mode === "template" && <TemplatePicker value={value.templateId} onChange={(templateId) => onChange({ ...value, templateId })} />}
          {value.mode === "file" && (
            <Dropzone
              label="Upload the job description"
              hint="PDF or DOCX, up to 4 MB"
              file={value.file}
              onFile={(file) => onChange({ ...value, file })}
              art={<JobArt className="h-full w-full" />}
            />
          )}
          {value.mode === "text" && (
            <div className="flex flex-col gap-3">
              <div>
                <label htmlFor="jd-title" className="mb-1.5 block text-sm font-semibold text-ink-2">
                  Job title <span className="font-normal text-mute">(optional)</span>
                </label>
                <input id="jd-title" className="field" maxLength={80} value={value.title} onChange={(e) => onChange({ ...value, title: e.target.value })} placeholder="e.g. SDE Intern, Backend" />
              </div>
              <div>
                <label htmlFor="jd-text" className="mb-1.5 block text-sm font-semibold text-ink-2">Job description</label>
                <textarea
                  id="jd-text"
                  className="field min-h-52 resize-y leading-relaxed"
                  maxLength={20000}
                  value={value.text}
                  onChange={(e) => onChange({ ...value, text: e.target.value })}
                  placeholder="Paste the full job posting: responsibilities, requirements and nice-to-haves."
                  aria-describedby="jd-count"
                />
                <p id="jd-count" className={`mt-1 text-xs ${chars > 0 && chars < MIN_JD_CHARS ? "text-warn" : "text-mute"}`}>
                  {chars < MIN_JD_CHARS ? `${chars} / ${MIN_JD_CHARS} characters minimum` : `${chars.toLocaleString()} characters`}
                </p>
              </div>
            </div>
          )}
        </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
