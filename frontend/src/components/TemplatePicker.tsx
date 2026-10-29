import { useQuery } from "@tanstack/react-query";
import { Check, RotateCw, Search } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { useMemo, useState } from "react";
import { ApiError, getTemplates } from "../lib/api";
import { spotlight } from "./Fx";
import { iconFor } from "../lib/icons";

interface Props {
  value: string | null;
  onChange: (id: string) => void;
}

/** Grid of role templates, searchable and filterable by category. Behaves as a radio group. */
export default function TemplatePicker({ value, onChange }: Props) {
  const { data, isLoading, error, refetch } = useQuery({ queryKey: ["templates"], queryFn: getTemplates, staleTime: Infinity });
  const [q, setQ] = useState("");
  const [cat, setCat] = useState("All");

  const categories = useMemo(() => ["All", ...new Set((data ?? []).map((t) => t.category))], [data]);
  const shown = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return (data ?? []).filter(
      (t) =>
        (cat === "All" || t.category === cat) &&
        (!needle || t.title.toLowerCase().includes(needle) || t.required_skills.some((s) => s.toLowerCase().includes(needle))),
    );
  }, [data, q, cat]);

  if (error) {
    return (
      <div className="rounded-2xl border border-line bg-white/60 p-6 text-center">
        <p className="font-semibold">Couldn't load role templates.</p>
        <p className="mt-1 text-sm text-mute">
          {error instanceof ApiError && error.status === 404
            ? "The API server is running an older version. Restart it with scripts\\dev.ps1, then try again."
            : "Upload or paste the job description instead, or try again."}
        </p>
        <button type="button" onClick={() => refetch()} className="btn-light mt-3">
          <RotateCw size={15} aria-hidden /> Try again
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="flex flex-col gap-2.5 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search size={16} className="pointer-events-none absolute top-1/2 left-3.5 -translate-y-1/2 text-mute" aria-hidden />
          <label htmlFor="tpl-search" className="sr-only">Search roles or skills</label>
          <input id="tpl-search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search roles or skills, e.g. Kotlin" className="field !py-2.5 pl-10" />
        </div>
      </div>
      <div className="no-scrollbar -mx-1 mt-3 flex gap-1.5 overflow-x-auto px-1 pb-1 [mask-image:linear-gradient(90deg,#000_90%,transparent)]" role="group" aria-label="Filter by category">
        {categories.map((c) => (
          <button
            key={c}
            type="button"
            onClick={() => setCat(c)}
            aria-pressed={cat === c}
            className={`chip min-h-9 border transition-colors ${cat === c ? "border-ink bg-ink text-white" : "border-line bg-white text-ink-2 hover:border-line-2 hover:text-ink"}`}
          >
            {c}
          </button>
        ))}
      </div>

      <div role="radiogroup" aria-label="Role templates" className="thin-scrollbar mt-3 grid max-h-[420px] gap-2.5 overflow-y-auto pr-1 sm:grid-cols-2">
        {isLoading &&
          Array.from({ length: 6 }, (_, i) => (
            <div key={i} className="rounded-2xl border border-line bg-white p-4">
              <div className="skeleton h-9 w-9" />
              <div className="skeleton mt-3 h-4 w-2/3" />
              <div className="skeleton mt-2 h-3 w-full" />
            </div>
          ))}
        {shown.map((t, i) => {
          const Icon = iconFor(t.icon);
          const selected = value === t.id;
          return (
            <motion.button
              key={t.id}
              type="button"
              role="radio"
              aria-checked={selected}
              onClick={() => onChange(t.id)}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: Math.min(i, 8) * 0.04, ease: [0.16, 1, 0.3, 1] }}
              whileHover={{ y: -4 }}
              whileTap={{ scale: 0.98 }}
              onPointerMove={spotlight}
              className={`group spotlight relative rounded-2xl border bg-white p-4 text-left transition-[border-color,box-shadow] duration-500 ${
                selected
                  ? "border-ink shadow-[0_0_0_3px_rgb(18_18_18/0.08)]"
                  : "border-line hover:border-line-2 hover:shadow-[0_10px_30px_-18px_rgb(18_18_18/0.3)]"
              }`}
            >
              <AnimatePresence>
              {selected && (
                <motion.span
                  initial={{ scale: 0, rotate: -45 }}
                  animate={{ scale: 1, rotate: 0 }}
                  exit={{ scale: 0, opacity: 0 }}
                  transition={{ type: "spring", stiffness: 500, damping: 22 }}
                  className="absolute top-3 right-3 grid size-6 place-items-center rounded-full bg-ink text-white"
                >
                  <Check size={14} strokeWidth={3} aria-hidden />
                </motion.span>
              )}
              </AnimatePresence>
              <span className={`tilt-icon grid size-10 place-items-center rounded-xl transition-colors ${selected ? "bg-gradient-to-b from-[#2b2b2e] to-ink text-white" : "bg-tile text-ink group-hover:bg-ink group-hover:text-white"}`}>
                <Icon size={19} aria-hidden />
              </span>
              <span className="mt-3 block pr-6 font-bold">{t.title}</span>
              <span className="mt-0.5 block text-xs font-semibold text-mute">{t.seniority}</span>
              <span className="mt-2.5 flex flex-wrap gap-1">
                {t.required_skills.slice(0, 3).map((s) => (
                  <span key={s} className="rounded-md bg-tile px-1.5 py-0.5 text-xs font-medium text-ink-2">{s}</span>
                ))}
                {t.required_skills.length > 3 && <span className="px-1 py-0.5 text-xs text-mute">+{t.required_skills.length - 3}</span>}
              </span>
            </motion.button>
          );
        })}
        {data && shown.length === 0 && (
          <div className="col-span-full rounded-2xl border border-dashed border-line-2 p-6 text-center">
            <p className="font-semibold">No roles match “{q}”.</p>
            <p className="mt-1 text-sm text-mute">Try a broader word, or paste the job description in the Paste text tab.</p>
          </div>
        )}
      </div>
    </div>
  );
}
