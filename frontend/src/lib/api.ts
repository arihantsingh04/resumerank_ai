import type { Report, TemplateSummary } from "./types";

const BASE = "/api/v1";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function parse<T>(res: Response): Promise<T> {
  if (res.ok) return (await res.json()) as T;
  let code = "http_error";
  let message =
    res.status === 413
      ? "Those files are too large to send together. Keep the resume and JD file under 4 MB combined."
      : `Something went wrong (${res.status}). Try again.`;
  try {
    const data = await res.json();
    if (data?.error?.message) {
      code = data.error.code ?? code;
      message = data.error.message;
    }
  } catch {
    /* non-JSON body */
  }
  throw new ApiError(res.status, code, message);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, init);
  } catch {
    throw new ApiError(0, "network", "Can't reach ResumeRank. Check your connection and that the server is running.");
  }
  return parse<T>(res);
}

export const getTemplates = () => request<TemplateSummary[]>("/templates");

export type JobSource =
  | { kind: "template"; templateId: string }
  | { kind: "file"; file: File }
  | { kind: "text"; text: string; title?: string };

export function checkResume(resume: File, job: JobSource): Promise<Report> {
  const form = new FormData();
  form.append("resume", resume);
  if (job.kind === "template") form.append("jd_template", job.templateId);
  if (job.kind === "file") form.append("jd_file", job.file);
  if (job.kind === "text") {
    form.append("jd_text", job.text);
    if (job.title?.trim()) form.append("jd_title", job.title.trim());
  }
  return request<Report>("/check", { method: "POST", body: form });
}
