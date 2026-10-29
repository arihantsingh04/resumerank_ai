import { CheckCircle2, FileText, UploadCloud, X } from "lucide-react";
import { motion } from "motion/react";
import { useId, useRef, useState, type DragEvent, type ReactNode } from "react";

const MAX_MB = 4;
const ACCEPT = ".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document";

export function validateFile(f: File): string | null {
  const name = f.name.toLowerCase();
  if (!name.endsWith(".pdf") && !name.endsWith(".docx")) return "Use a PDF or DOCX file.";
  if (f.size > MAX_MB * 1024 * 1024) return `That file is over ${MAX_MB} MB. Try exporting a smaller PDF.`;
  if (f.size === 0) return "That file is empty.";
  return null;
}

const fmtSize = (b: number) => (b > 1024 * 1024 ? `${(b / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(b / 1024))} KB`);

interface Props {
  label: string;
  hint: string;
  file: File | null;
  onFile: (f: File | null) => void;
  art: ReactNode;
  compact?: boolean;
}

/** Drag-and-drop or click-to-browse for one PDF/DOCX, with an illustrated empty state. */
export default function Dropzone({ label, hint, file, onFile, art, compact = false }: Props) {
  const input = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const errId = useId();

  const take = (f: File | undefined) => {
    if (!f) return;
    const problem = validateFile(f);
    setError(problem);
    if (!problem) onFile(f);
  };
  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setOver(false);
    take(e.dataTransfer.files[0]);
  };

  if (file) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 8 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ type: "spring", stiffness: 380, damping: 28 }}
        className="flex items-center gap-3 rounded-2xl border border-good/25 bg-good-wash/60 p-3.5"
      >
        <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-white text-ink shadow-sm">
          <FileText size={20} aria-hidden />
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate font-semibold">{file.name}</p>
          <p className="flex items-center gap-1 text-sm text-good">
            <motion.span initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 600, damping: 18, delay: 0.15 }} className="inline-flex"><CheckCircle2 size={14} aria-hidden /></motion.span> Ready · {fmtSize(file.size)}
          </p>
        </div>
        <button type="button" onClick={() => onFile(null)} className="grid size-10 place-items-center rounded-full text-mute transition-colors hover:bg-white hover:text-ink" aria-label={`Remove ${file.name}`}>
          <X size={18} aria-hidden />
        </button>
      </motion.div>
    );
  }

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        aria-label={`${label}. ${hint}`}
        aria-describedby={error ? errId : undefined}
        onClick={() => input.current?.click()}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), input.current?.click())}
        onDragOver={(e) => {
          e.preventDefault();
          setOver(true);
        }}
        onDragLeave={() => setOver(false)}
        onDrop={onDrop}
        className={`group relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed text-center transition-all duration-500 ease-[var(--ease-apple)] ${
          compact ? "px-5 py-6" : "px-6 py-8"
        } ${
          over
            ? "scale-[1.01] border-ink bg-tile shadow-[0_0_0_6px_rgb(18_18_18/0.05)]"
            : "border-line-2 bg-white/60 hover:-translate-y-0.5 hover:border-ink/40 hover:bg-white hover:shadow-[0_10px_30px_-18px_rgb(18_18_18/0.3)]"
        }`}
      >
        {!compact && <div className="mb-2 h-24 w-32">{art}</div>}
        <p className="flex items-center gap-2 font-bold">
          <UploadCloud size={18} className="text-ink transition-transform duration-200 group-hover:-translate-y-0.5" aria-hidden />
          {over ? "Drop it here" : label}
        </p>
        <p className="mt-1 text-sm text-mute">{hint}</p>
        <input
          ref={input}
          type="file"
          accept={ACCEPT}
          className="sr-only"
          tabIndex={-1}
          aria-hidden="true"
          onChange={(e) => {
            take(e.target.files?.[0]);
            e.target.value = "";
          }}
        />
      </div>
      {error && (
        <p id={errId} role="alert" className="mt-2 text-sm font-medium text-bad">
          {error}
        </p>
      )}
    </div>
  );
}
