# ResumeRank — Design Decisions

> **One file to understand the whole project.** It covers what the product does, how each part works,
> and *why* it was built that way. Update it whenever a major decision changes. Decisions are numbered
> (`D-xx`) so code comments and PRs can reference them.

**Project brief (P_101):** an LLM-based resume screening system that screens resumes against job
descriptions and ranks them. It runs on an 8 GB laptop with Python, Sentence Transformers and FAISS.
Domain: Education / Cross-Industry AI tooling. LLM: **Google Gemini**.

**Product direction (v2, 2026-10-29):** a **job-seeker tool**. A student or early-career engineer checks
*their own* resume against a job description (JD) and learns what to fix. There is no login and nothing
is stored. Version 1 was a recruiter tool with accounts and a database; see §12 for why it changed.

---

## 1. Intent

Most BTech graduates send the same resume to every opening and never learn why they aren't
shortlisted. Keyword-only "ATS checkers" give a number but no reasons.

ResumeRank lets anyone:

1. **Drop in their resume** (PDF or DOCX).
2. **Pick the job**, in one of three ways:
   - a ready-made **role template** (Backend, Flutter, DevOps…)
   - an **uploaded JD** (PDF or DOCX)
   - **pasted JD text**
3. **Press "Check match"** and get a report in seconds with:
   - a match score
   - the skills found, each with the resume sentence that proves it
   - the skills missing, with how to add them
   - AI suggestions (keywords and bullet rewrites)
   - resume health checks

### Goals
- **One obvious path:** land, click "Check my resume", upload, pick a job, check, read the report.
- **Explainable:** every score traces to components and quoted resume evidence.
- **Private by design:** files are processed in memory and never written to disk or a database.
- **Runs on an 8 GB laptop** on CPU with a small disk footprint. Free-tier Gemini usage stays bounded
  and protected from abuse without logins.
- **Stateless backend:** it scales horizontally behind a load balancer with no shared database.
- **No secrets in git.**

### Non-goals
- No accounts, saved history or recruiter features (v1 features were removed, D-35).
- No OCR for scanned PDFs (flagged "no extractable text").
- No resume builder or editor. We advise; the user edits their own document.

### Anti-goals (failure even if it "works")
- **Storing someone's resume.** Not on disk, not in a database, not in logs.
- **A score with no reasons.**
- **One user burning the shared Gemini key** for everyone else.
- **A cluttered first screen** with more than one primary action.

---

## 2. Architecture at a glance

```
 ┌──────────────────────────────┐   multipart (resume + JD)  ┌─────────────────────────────────────┐
 │ React + TS + Vite + Tailwind │ ─────────────────────────▶ │ FastAPI  /api/v1                    │
 │  /        Landing            │                             │  api/       check, templates, health│
 │  /check   Checker + Report   │ ◀───────────────────────── │  services/  checker (orchestrator)  │
 └──────────────────────────────┘        Report JSON         │             ingestion · scoring     │
                                                             │             health · ai budget      │
                                                             └──────┬──────────────┬───────────────┘
                                                                    │              │
                                               Sentence-Transformers + FAISS    Gemini API
                                               (in memory, per request)         (≤ 2 calls/check)
```

**Layering (D-01):** routers validate input only. Services hold the logic and never import FastAPI.
External systems (embedding model, Gemini) sit behind small interfaces, so tests use fakes.

---

## 3. How a check works (the pipeline)

| Step | What happens | Where |
|---|---|---|
| 1. Guard | Per-IP rate limit (10 checks/min). Concurrency slot (max 4 checks at once, else 503 "busy") | `api/v1/check.py`, `container.py` |
| 2. Validate | Resume: `.pdf`/`.docx`, ≤ 4 MB, magic bytes, DOCX zip-bomb guard. JD: exactly one of template / file / text | `services/ingestion/files.py` |
| 3. Extract | Text extracted **in memory** (pypdf / python-docx). Under 50 chars means "No extractable text" | `services/ingestion/extract.py` |
| 4. Redact | Emails, phones, URLs and dates of birth are removed from the text sent to AI. The first-line name is scrubbed (D-09) | `services/ingestion/redact.py` |
| 5. Requirements | **Template:** curated requirements. **Custom JD:** Gemini extraction (cached by JD hash), falling back to a ~200-skill tech catalogue (D-37) | `services/requirements.py`, `services/scoring/skill_catalog.py` |
| 6. Embed + index | Resume chunks (about 120 words, overlapping) are embedded and put in a **per-request FAISS `IndexFlatIP`** | `services/vectorstore/memory_index.py` |
| 7. Stage-1 score | Semantic fit, skill coverage (literal, alias or semantic evidence), experience | `services/scoring/scorer.py` |
| 8. Health checks | Rule-based: length, contact info, sections, quantified wins, action verbs, weak phrases, links | `services/health.py` |
| 9. AI coaching | One Gemini call: score, strengths, gaps, suggestions, keywords to add, bullet rewrites. Skipped gracefully if there's no key or the budget is used up (D-36) | `services/llm/` |
| 10. Report | Final score = stage-1, blended 50/50 with the AI score when available, plus a verdict and rule-based tips | `services/checker.py` |

### Scoring details
- **Semantic score:** cosine similarity of the JD embedding (the mean of its chunk vectors) with the
  mean resume vector. Calibrated so that 0.15 maps to 0 and 0.65 maps to 100 (D-24).
- **Skill coverage:** each requirement is matched one of three ways:
  - `keyword`: the skill or an alias appears literally; the sentence is quoted.
  - `semantic`: FAISS finds a chunk with cosine ≥ 0.55.

  Required skills weigh 2×, nice-to-haves 1×. With no requirements the score is a neutral 50 (D-30).
- **Experience:** `min(years / min_years, 1) × 100`. Templates target 0–2 years, so freshers aren't
  punished. Years come from the largest "N years" statement in the resume (D-31).
- **Stage-1 formula:** `0.40·semantic + 0.45·skills + 0.15·experience`.
- **Verdict:** ≥ 75 Strong match · ≥ 60 Good match · ≥ 40 Fair match · below 40 Low match.

---

## 4. Decision log

| ID | Decision | Why | Alternatives rejected |
|---|---|---|---|
| D-01 | FastAPI backend + React/TS SPA, layered | Clean split, typed API, independent scaling | Streamlit |
| D-03 | `all-MiniLM-L6-v2` on **CPU-only PyTorch** | ~90 MB model, fast on CPU; CPU torch ≈ 200 MB vs 2.5 GB CUDA (low disk) | Bigger models, Gemini embeddings |
| D-04 | **FAISS `IndexFlatIP`, built in memory per request** over that resume's chunks | Brief requires FAISS; gives per-requirement evidence retrieval; nothing persisted | Persistent per-user indexes (v1), vector DB |
| D-05 | `google-genai` SDK, `response_json_schema` from Pydantic models, output validated and clamped | Schema-validated output, no fragile parsing | Free-text prompting |
| D-06 | **Graceful degradation**: full report without Gemini (rule-based tips replace AI suggestions) | Works offline / without key / over budget | Hard failure |
| D-07 | pypdf + python-docx, in memory | Permissive licences, pure Python | PyMuPDF (AGPL) |
| D-09 | Contact details are redacted and the first-line name scrubbed before any AI call | Minimise PII sent to a third party | Raw text to the LLM |
| D-11 | Gemini client: client-side RPM limiter; **at most 2 attempts per AI call, 20 s each**. An overloaded/timed-out primary model falls straight through to `GEMINI_FALLBACK_MODEL` (no retry loop). Daily-quota errors are detected from the full SDK error text, then AI is **paused until reset** | Measured live: `gemini-3.8-flash` returned 503/504 under high demand and the old 3×60 s retry loop made checks wait 2 minutes. Now worst case is about 40 s and typical is 6–15 s | Retrying the same model with backoff |
| D-12 | Prompt-injection defence: untrusted text fenced (fence sanitised until stable), declared as data, schema-forced output, no tools | Resumes/JDs are attacker-controllable | Trusting output |
| D-16 | Security headers, CORS allowlist, generic error envelope with request id, in-memory sliding-window rate limiter with bounded memory | Standard hardening | slowapi |
| D-17 | Never log resume/JD text; log ids, sizes and timings only | Privacy | — |
| D-19 | Model loaded once (singleton), warmed up at startup; CPU work runs in the threadpool (sync routes), never on the event loop | Responsive server | Per-request load |
| D-20 | Docker files included but optional (Docker not installed locally, low disk) | Deploy-ready without forcing Docker | Docker-only |
| D-21 | Tests use a hashing encoder + fake LLM; no network or model download | Fast, deterministic CI | Live API in tests |
| D-22 | Coaching tone: honest, specific, job-relevant only; ignore protected attributes; never invent experience the resume doesn't show | Responsible AI; trustworthy advice | — |
| D-24 | Semantic score calibrated with fixed bounds (0.15 → 0, 0.65 → 100) | MiniLM cosines bunch together; fixed bounds keep scores comparable | Raw cosine |
| D-30 | Skill evidence sources `keyword` (quoted from the exact resume **line**) / `semantic` (best FAISS chunk), shown in the UI | Literal mentions are the most trustworthy evidence; semantic catches paraphrase | Semantic only |
| D-31 | Years of experience from the largest "N years" statement | Cheap, no LLM needed | Neutral 50 always |
| D-33 | **UI v3, following the user's reference shots**: a white canvas with soft grey dotted tiles, near-black ink, Plus Jakarta Sans with headlines at weight 500 and tight tracking, and large light-weight numerals for stats and the score. Black pill buttons are the primary actions. Small solid-colour icon squares (orange, blue, pink, green, yellow, purple). Tilted glossy **stickers** are the bold move: the hero's orange "Check" sticker with pulsing concentric rings is itself the CTA, and verdicts appear as a tilted sticker. Glossy orbs sit inside headline type. The yellow highlighter is kept for resume evidence. Motion is limited to one hero moment (orbs pop, sticker sways, rings pulse) plus responses to clicks (tabs, accordions, carousel). Everything is static under `prefers-reduced-motion` | The user asked for the look of the referenced Dribbble shots. Only true facts are used: no invented user counts or testimonials. The carousel shows illustrative bullet rewrites and labels them as such | v2 gradient-glow look (rejected by the user as generic) |
| D-34 | Repo guard rails: `.gitignore`, pre-commit (blocks `.env`, private keys, `AIza…` keys), CI (ruff, pytest, eslint, build) | Secrets must never reach GitHub | — |
| D-35 | **Guest, stateless service: no accounts, DB, JWT, file storage or background queue** | User choice (v2); no PII retained means no breach surface; horizontally scalable | v1 accounts + SQLite + per-user indexes |
| D-36 | **Abuse protection without logins**: 10 checks/min per IP; **AI coaching limited to `AI_CHECKS_PER_IP_PER_DAY` (15) per IP** and a **global `GEMINI_DAILY_BUDGET` (400 calls/day)**; at most `MAX_CONCURRENT_CHECKS` (4) checks run at once (others get 503 "busy, retry") | Protects the shared key and the 8 GB laptop; ranking still works when AI is capped | CAPTCHA (friction), accounts (rejected by user) |
| D-37 | JD requirements: **templates curated by hand**. Custom JDs use the **~200-skill tech catalogue first**. Gemini extraction (LRU-cached by SHA-256) runs only when the catalogue finds fewer than 3 skills, which saves a 15 s AI call on most tech JDs. A skill counts as nice-to-have if its sentence says "nice to have / preferred / bonus / plus" | Templates cost zero AI calls; catalogue keeps custom JDs useful without a key | LLM-only extraction |
| D-38 | **14 entry-level BTech role templates** (0–2 years) in `backend/app/data/templates.py` | Target audience is students/new grads; adding a role means adding one dict | Templates in a DB |
| D-39 | **Resume health checks** are deterministic rules (length, contact, sections, numbers, action verbs, weak phrases, links) | Instant, free, explainable; complements AI advice | AI-only feedback |
| D-40 | "Download report" = print stylesheet → browser "Save as PDF" | No server-side rendering or storage | Server PDF generation |
| D-41 | Upload types: **PDF and DOCX only** for both resume and JD file (TXT dropped) | User requirement; fewer formats, simpler validation | TXT |
| D-42 | **Animation stack: GSAP + Motion**. GSAP (`gsap`, `@gsap/react`, ScrollTrigger, ScrollTo) handles timelines and scroll: the hero entrance (headline lines rise from a mask, orbs spring in, sticker drops in), scroll reveals (`useScrollReveal`), hero parallax, magnetic hover (`<Magnetic>`), the score count-up, bar fills and smooth auto-scroll. Motion (`motion/react`) handles in-place micro-interactions: the shared-layout tab highlight (`layoutId`), accordions (`AnimatePresence` height), template card hover/press/select, the file chip, button presses and the spring carousel (swipeable). All live in `src/lib/anim.tsx`; GSAP work runs inside `gsap.matchMedia('(prefers-reduced-motion: no-preference)')` and Motion respects the same setting. Vendor code is split into its own chunks (`react`, `gsap`, `motion`) | User asked for famous React animation libraries and smooth, Apple-like motion. Each library is used where it's strongest | Hand-rolled CSS keyframes (v3), a single library for everything |
| D-43 | **SaaS micro-interaction layer** (`components/Fx.tsx` + "SaaS motion layer" in `index.css`):
| D-44 | **First-load intro**: one GSAP timeline that starts after the fonts are ready. Order: navbar, headline words blur in one by one, orbs, the rings behind the sticker ripple outward, the sticker settles, the description, the CTA (its label blurs in, then its glow fades up). Easing is expo/power ease-out only (no elastic bounces). Hidden states are set in a layout effect, so nothing flashes before the intro. `gsap.ticker.lagSmoothing(0)` keeps timing on the real clock. **Reduced motion** (for example Windows "Animation effects" off) runs the same sequence as a pure fade and blur-in, with no movement, scale or parallax | The user asked for a smooth animated first load. Measurement found this PC has OS animation effects off, which had disabled all motion | Elastic bounces; skipping all animation under reduced motion |
| D-45 | **Self-hosted fonts** (`@fontsource-variable/plus-jakarta-sans`, `@fontsource-variable/bricolage-grotesque`) instead of Google Fonts | The render-blocking Google Fonts stylesheet delayed first paint to about 13 s in testing; self-hosted it is about 0.8 s. It also avoids sending visitors to Google, and the CSP is now `font-src 'self'` | Google Fonts link |
| D-46 | **Deploy target: Vercel, one project** (static `frontend/dist` + Python function `api/index.py` serving the FastAPI app at `/api/*`).
- **Embeddings:** run the **same `all-MiniLM-L6-v2` model through ONNX Runtime** (`LazyOnnxEncoder`: official ONNX export, tokenizer, mean pooling, L2 normalisation). This matches PyTorch with cosine > 0.999 (test `test_onnx_matches_sentence_transformers`). `EMBEDDING_BACKEND=auto` picks PyTorch when it is installed (laptop), otherwise ONNX.
- **Dependencies:** split into `requirements.txt` (server, no PyTorch, about 270 MB) and `requirements-local.txt` (adds sentence-transformers).
- **Vercel specifics:** writable data lives in `/tmp`; client IP comes from Vercel's `x-real-ip` (`TRUSTED_IP_HEADER`, only honoured when configured); uploads are capped at 4 MB per file (Vercel's 4.5 MB body cap).
- **Deploying:** `scripts/deploy-vercel.ps1` logs in, links the project, stores `GEMINI_API_KEY` as an encrypted env var and deploys. | The user wants Netlify/Vercel with minimum manual work. Netlify can't run Python. Vercel's Python limit is 500 MB and PyTorch alone exceeds it | Netlify + separate Python host (more manual steps), Gemini embeddings (would drop the brief's Sentence-Transformers model) |
- **Primary CTAs** (`GlowButton`, `GlowLink`) get an orbiting conic-gradient ring (CSS `@property --angle`) and a breathing radial halo, both only while ready to press, plus a press ripple from the click point. They also get state label swaps: Check match, then Checking… with a shimmer sweep, then Match ready.
- **Every dark button** gets a rolling label on hover (`RollText`).
- **Cards and tiles** get a cursor spotlight (`--mx/--my`), and feature icons a light sweep.
- **The rewrites carousel** is a coverflow: position = sin(angle), depth = cos(angle), which drives scale, opacity, tilt and z-order together.

Rules adapted from the Remotion SaaS-animation playbook: glows use multi-stop radial gradients, never `filter: blur` on animated shapes (blur warps); motion that starts from rest uses in-out easing (`--ease-inout`), because out-curves jolt after a hold; only transform, opacity and custom properties are animated. Remotion itself renders video, so it is not used in the live site | The user asked for that skill's style of button and landing-page animation | Remotion inside the web app (it's a video renderer) |

(IDs D-02, D-08, D-10, D-13–D-15, D-23, D-25–D-29 and D-32 belonged to the v1 recruiter design and are retired.)

---

## 5. API (v1 prefix `/api/v1`, JSON)

| Method & path | Purpose |
|---|---|
| `GET /health` | Liveness + whether AI is enabled |
| `GET /templates` | Role templates: `id, title, category, icon, summary, seniority, required_skills, nice_to_have_skills` |
| `GET /templates/{id}` | One template including full JD text |
| `POST /check` | multipart: `resume` (file) **+ exactly one of** `jd_template` (id) / `jd_file` (file) / `jd_text` (50–20,000 chars); optional `jd_title`. Returns the **Report** |

**Report** (`schemas/check.py`):
- **Score:** `score`, `verdict`, `breakdown{semantic, skills, experience, ai?}`
- **Job:** `job{title, source, template_id?}`
- **Skills:** `matched[]` / `missing[]` (each with `requirement, required, source, evidence, tip`)
- **Experience:** `years_experience`, `min_years`
- **Checks and tips:** `health[]{id, label, status: pass|warn|fail, detail}`, `tips[]`
- **AI:** `ai{status: ok|disabled|limited|error, summary, strengths[], gaps[], suggestions[]{title, detail},
  keywords_to_add[], bullet_rewrites[]{before, after}}`
- **Meta:** `meta{resume_words, ms}`

Errors use one envelope: `{"error": {"code", "message"}}`. The codes are `validation_error` (422),
`rate_limited` (429), `busy` (503) and `internal_error` (500, with a request id).

---

## 6. Frontend

| Route | Screen |
|---|---|
| `/` | **Landing:** hero headline, primary CTA **"Check my resume"**, floating sample-report card (animated score ring), 3-step "How it works" (a real sequence), role-chip marquee, privacy promise, closing CTA |
| `/check` | **Checker:** Step 1 "Your resume" dropzone · Step 2 "The job" tabs (Templates · Upload JD · Paste text) · sticky **"Check match"** CTA (disabled with a reason until ready) · **Report** below, with an illustrated empty state before the first check and an animated "scanning" state while it runs |

Micro-animations:
- staggered reveal on scroll
- score-ring stroke and count-up
- dropzone lift and drag pulse
- file chip slide-in
- template card hover lift and selected-check pop
- tab indicator slide
- CTA glow on hover
- scanning line while checking

All are disabled under `prefers-reduced-motion`. Mobile-first, from 375 px up, with a sticky bottom CTA
on small screens.

---

## 7. Repository layout

```
RESUME_SCREENING/
├── backend/
│   ├── app/
│   │   ├── main.py              # app factory, middleware, error envelope
│   │   ├── container.py         # composition root: settings, encoder, LLM, limiters, budget
│   │   ├── core/                # config, errors, logging, ratelimit
│   │   ├── api/v1/              # check.py, templates.py, misc.py
│   │   ├── schemas/check.py     # Report DTOs
│   │   ├── data/templates.py    # 14 role templates
│   │   └── services/
│   │       ├── checker.py       # orchestrates a check (§3)
│   │       ├── requirements.py  # JD → requirements (template / Gemini / catalogue)
│   │       ├── health.py        # resume health rules
│   │       ├── ai_budget.py     # per-IP + global daily AI limits
│   │       ├── ingestion/       # files, extract, redact, chunk
│   │       ├── embeddings/      # encoder
│   │       ├── vectorstore/     # per-request FAISS index
│   │       ├── scoring/         # scorer, skills (aliases), skill_catalog
│   │       └── llm/             # Gemini client, prompts, schemas
│   ├── eval/                    # synthetic resumes + JDs, ranking-quality script
│   ├── tests/
│   └── Dockerfile
├── frontend/                    # Vite + React + TS + Tailwind v4
├── scripts/                     # setup.ps1, dev.ps1 (Windows)
├── docker-compose.yml · .env.example · .gitignore · .pre-commit-config.yaml · .github/workflows/ci.yml
└── DESIGN_DECISIONS.md          # this file
```

---

## 8. Configuration (`.env`, never committed)

| Variable | Default | Notes |
|---|---|---|
| `GEMINI_API_KEY` | — | Optional (D-06). Free-tier inputs may be used by Google to improve products |
| `GEMINI_PARSE_MODEL` | `gemini-3.5-flash-lite` | JD requirement extraction |
| `GEMINI_RERANK_MODEL` | `gemini-3.5-flash-lite` | Coaching (fast and reliably available in testing) |
| `GEMINI_FALLBACK_MODEL` | `gemini-flash-latest` | Used when the primary model is busy |
| `GEMINI_RPM` | `10` | Client-side throttle |
| `GEMINI_DAILY_BUDGET` | `400` | Global AI calls/day (D-36) |
| `AI_CHECKS_PER_IP_PER_DAY` | `15` | Per-IP AI coaching cap (D-36) |
| `CHECKS_PER_MINUTE_PER_IP` | `10` | Rate limit |
| `MAX_CONCURRENT_CHECKS` | `4` | Laptop protection |
| `MAX_UPLOAD_MB` | `4` | Per file (Vercel body cap 4.5 MB) |
| `EMBEDDING_BACKEND` | `auto` | `torch` / `onnx` / `auto` (D-46) |
| `TRUSTED_IP_HEADER` | — | e.g. `x-real-ip` behind Vercel; empty = socket address |
| `ENV` | `development` | `production` disables `/docs`, adds HSTS |
| `CORS_ORIGINS` | `http://localhost:5173` | |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | |
| `DATA_DIR` | `./data` | Only the model cache lives here |
| `SEMANTIC_SIM_LOW` / `HIGH`, `SKILL_MATCH_THRESHOLD`, `LLM_BLEND` | `0.15` / `0.65`, `0.55`, `0.5` | Scoring knobs |

---

## 9. Security & privacy summary
- **No storage:** uploads are read into memory, processed and dropped. No database, no upload folder.
- **Nothing sensitive leaves the server or reaches the logs:** the Gemini key lives only in `.env` on
  the server, and resume and JD text is never logged.
- **Upload hardening:** an extension allowlist, magic-byte checks, a 4 MB cap, a DOCX decompression-bomb
  guard (50 MB uncompressed, 100:1 ratio) and a PDF page cap (30).
- **Abuse protection:** rate limits, a per-IP and a global AI budget, and a concurrency cap (D-36).
  nginx overwrites `X-Forwarded-For` so clients can't spoof IPs.
- **Standard hardening:** security headers (CSP, nosniff, DENY framing, no-referrer, HSTS in
  production) and prompt-injection fencing.

## 10. Scaling path
Because the backend is stateless, it scales by adding instances behind a load balancer. The only
per-instance state is the rate-limit and AI-budget counters. Move them to Redis when running more than
one instance, so the limits become global. For heavier CPU load, put embeddings in a separate worker
pool or switch to an ONNX-quantised model.

## 11. Measured results
- Backend tests: 82, about 12 s, with no network and no model download.
- Live check with real Gemini (template JD, 108-word resume): 6–28 s end to end, depending on Gemini load.
  Local scoring alone takes under 1 s once the model is warm.
- `python -m eval.run` ranks the synthetic resumes for each JD by checker score and reports Spearman ρ
  against labelled tiers. The pass bar is 0.6.

## 12. Changelog
- **2026-10-29 — v1:** a recruiter tool with accounts, SQLite, per-user FAISS indexes, background
  ingestion and top-K Gemini re-ranking. It was security-reviewed and hardened.
- **2026-10-29 — v2 pivot (user decision):** a job-seeker self-check.
  - **Removed:** accounts, JWT, the database, Alembic, uploads storage, the queue and the recruiter
    screens.
  - **Added:** stateless `/check`, 14 role templates, JD upload via PDF/DOCX, a skill catalogue, health
    checks, AI coaching and IP-based AI budgets.
  - **Redesigned:** the UI (light, gradient glows, micro-animations, illustrated empty states).
  - **Kept:** the ingestion, embedding, FAISS, scoring and Gemini client modules and their hardening.
- **2026-10-30 — Vercel deploy (D-46):**
  - **ONNX embedding backend:** the same model, with no PyTorch on the server.
  - **New files:** `api/index.py`, `vercel.json`, `.vercelignore`, `scripts/deploy-vercel.ps1`.
  - **Uploads:** 4 MB cap.
- **2026-10-30 — First production deploy:** live at <https://resumerank-psi.vercel.app>
  (project `resumerank`; `GEMINI_API_KEY` stored as a Vercel Secret, production only).
  - **Verified live:**
    - `/api/v1/health` returns `ai_enabled: true`, and all 14 templates load.
    - A real PDF check against the Backend template scored 81.5 "strong" with Gemini coaching `ok`, in 4.7 s warm (about 5.5 s on a cold start).
    - Security headers are present, and the error-log scan is clean.
  - **Fix: `requirements.txt`.** Vercel's installer can't follow `-r` includes, so the root `requirements.txt` is now a full copy of `backend/requirements.txt`. `test_vercel_requirements_mirror_server_requirements` fails if the two drift apart.
  - **Fix: ignore rules.** The ignore rule `data/` also matched the source package `backend/app/data/` (the role templates), so it was missing from both git and the Vercel bundle. Both ignore files now use the anchored `/data/` rule. Added `backend/app/data/__init__.py`.
  - **`.vercelignore`** now also excludes AI-assistant folders (`.claude/`, `.cursor/`, …), mirroring `.gitignore`.
  - **`vercel link`** appended `.env*` to `.gitignore`, which would have hidden `.env.example`. That line was removed; the existing rules already cover `.env` and `.env.local`.
  - **`scripts/deploy-vercel.ps1`** now uses the CLI 65 syntax: `env add --environment production --force --sensitive`.
  - **Verified:** the serverless-only install has no PyTorch (271 MB), and a real check gave a score identical to the PyTorch version.
- **2026-10-30 — First-load intro & fonts (D-44, D-45):** smooth blur-in intro with a reduced-motion fade variant. Fonts are self-hosted, cutting first paint from about 13 s to 0.8 s in testing. The nginx upload cap is lowered to 12 MB, matching 2 files.
- **2026-10-30 — SaaS micro-interactions (D-43):** glowing ready-state CTA ring, ripple, rolling labels, shimmer loading, label state swaps, card spotlight, icon light sweep, coverflow carousel.
- **2026-10-30 — Motion & flow:**
  - **Animation stack (D-42).** GSAP + Motion added.
  - **Check button placement.** "Check match" now sits directly under the resume drop area, and the old floating bar is gone.
  - **Auto-scroll.** The page scrolls to the scanning card while checking, then to the match score once the report mounts. Measured: the score card lands 88 px from the top, just under the navbar.
  - **New logo mark.** A lowercase "r" whose arm is a rising arrow, plus a rank dot, on a glossy orange tile.
- **2026-10-30 — Brand & mobile:**
  - **New logo.** The mark is a resume page with a folded corner and an orange rank badge (`LogoMark.tsx`, also the favicon). The wordmark "resumerank" is set in Bricolage Grotesque 800 (`--font-brand`).
  - **Mobile.** Grid panels may now shrink (`min-width: 0`), fixing horizontal overflow on phones. Job tabs use short labels on phones, and the tab highlight re-measures on resize and font load.
  - **`scripts/dev.ps1`** stops stale ResumeRank servers before starting, so the web app can't proxy to an older API version (that was the cause of a `/templates` 404).
- **2026-10-30 — UI v3 (user decision):** redesigned the landing, checker and report in the reference style (D-33). The landing now has: a stats + orb headline + sticker hero, a bento grid, a feature grid, a privacy panel with a role quick-start, a roles explorer (category tabs + accordion), and a bullet-rewrite carousel. Backend unchanged.
- **2026-10-29 — v2 live testing:**
  - **Model fallback (D-11).** Testing with the user's real key showed `gemini-3.8-flash` overloaded. Coaching now uses `gemini-3.5-flash-lite` with a fallback model, at most 2×20 s.
  - **Catalogue-first requirements (D-37).**
  - **Evidence quotes.** These now quote whole resume lines, so job-title lines no longer get merged into the bullet below.
