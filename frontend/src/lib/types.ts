// Mirrors backend/app/schemas/check.py. Keep in sync.

export interface TemplateSummary {
  id: string;
  title: string;
  category: string;
  icon: string;
  summary: string;
  seniority: string;
  required_skills: string[];
  nice_to_have_skills: string[];
}

export interface SkillResult {
  requirement: string;
  required: boolean;
  source: "keyword" | "semantic" | null;
  evidence: string | null;
  similarity: number | null;
  tip: string | null;
}

export type Verdict = "strong" | "good" | "fair" | "low";
export type HealthStatus = "pass" | "warn" | "fail";

export interface HealthCheck {
  id: string;
  label: string;
  status: HealthStatus;
  detail: string;
}

export interface AIReport {
  status: "ok" | "disabled" | "limited" | "error";
  summary: string | null;
  strengths: string[];
  gaps: string[];
  suggestions: { title: string; detail: string }[];
  keywords_to_add: string[];
  bullet_rewrites: { before: string; after: string }[];
}

export interface Report {
  score: number;
  verdict: Verdict;
  breakdown: { semantic: number; skills: number; experience: number; ai: number | null };
  job: { title: string; source: "template" | "file" | "text"; template_id: string | null };
  matched: SkillResult[];
  missing: SkillResult[];
  years_experience: number | null;
  min_years: number | null;
  health: HealthCheck[];
  tips: string[];
  ai: AIReport;
  meta: { resume_words: number; ms: number; requirements_source: "template" | "ai" | "catalog" };
}
