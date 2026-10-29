# ResumeRank

Check your resume against any job description in seconds (project P_101). Drop in a PDF or DOCX resume,
then pick a **BTech role template**, upload a JD (PDF/DOCX) or paste one. You get:

- a **match score** and verdict
- the **exact resume lines** that prove each skill (highlighted)
- the skills that are **missing**, with how to add them
- **resume health checks**: length, contact details, sections, measurable impact, action verbs
- an **AI coach** (Gemini): suggestions, keywords to add and stronger bullet points

No sign-up, and **nothing is stored**: files are read in memory and dropped. Scoring runs locally with
Sentence Transformers and FAISS on CPU, so it fits an 8 GB laptop. Gemini is optional.

**Live:** <https://resumerank-psi.vercel.app>

> **How it all works, and why:** see [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md), the single source of truth.

## Quick start (Windows)

Requirements: Python 3.11+ (3.13 tested), Node 20+ (22 tested).

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup.ps1   # venv, CPU PyTorch, deps, .env, npm
powershell -File scripts\dev.ps1                             # API on :8000, web app on :5173
```

Open http://localhost:5173 and click **Check my resume**. The first check downloads the embedding model
(~90 MB) into `data/models/`.

### Enable the AI coach

Put a key from https://aistudio.google.com/apikey in `.env`:

```
GEMINI_API_KEY=your-key-here
```

`.env` is git-ignored. Never put the key anywhere else. If the primary model is overloaded, ResumeRank
falls back to `GEMINI_FALLBACK_MODEL`, so a check never waits more than about 40 s on AI. Without a key,
or when the daily AI limits are reached, the report is still complete except for the AI coach section.

Free-tier caveat: Google may use free-tier inputs to improve its products.

### Open it on your phone (same Wi-Fi)

```powershell
powershell -File scripts\dev.ps1 -Lan     # prints http://<your-PC-IP>:5173
```

If the phone can't connect, allow the port once in an **admin** PowerShell. The rule only accepts devices on
your local network:

```powershell
New-NetFirewallRule -DisplayName "ResumeRank dev (5173)" -Direction Inbound -Protocol TCP -LocalPort 5173 -RemoteAddress LocalSubnet -Action Allow
# remove later with: Remove-NetFirewallRule -DisplayName "ResumeRank dev (5173)"
```

Only the web app is exposed. The API stays on `127.0.0.1` and is reached through the web app's `/api` proxy.

## Tests and quality checks

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest        # 86 tests; no network, no model download
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m eval.run      # ranking quality on synthetic resumes (Spearman rho per job)
cd ..\frontend; npm run lint; npm run build
```

## Project layout

```
backend/    FastAPI: POST /api/v1/check, GET /api/v1/templates; services: checker, ingestion, scoring, llm
frontend/   React + TypeScript + Vite + Tailwind: Landing (/) and Checker (/check)
scripts/    Windows setup / dev helpers
data/       model cache only (git-ignored); no user data is ever written
```

## Before pushing to GitHub

- `git status` must **not** list `.env`, `data/` or `node_modules/`. All are in `.gitignore`.
- Recommended: run `backend\.venv\Scripts\pre-commit install`. It blocks `.env` files, private keys and
  Google API keys from being committed.
- If a key is ever committed, **revoke it in Google AI Studio immediately**.

## Deploy to Vercel (website + API, one command)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\deploy-vercel.ps1
```

The first run opens a browser once so you can log in to Vercel (a free Hobby account works). The script then:
- creates the `resumerank` project
- copies `GEMINI_API_KEY` from `.env` into Vercel's encrypted settings
- deploys

Re-run the same command to redeploy.

How it fits on Vercel (DESIGN D-46):
- **Embeddings:** the API runs the same MiniLM model through ONNX Runtime instead of PyTorch. That is about 270 MB of dependencies, under Vercel's 500 MB Python limit.
- **Uploads:** each file is capped at 4 MB, because Vercel caps request bodies at 4.5 MB.
- **Cold starts:** the first check after the app has been idle takes longer (about 10-25 s) while the model downloads. After that, checks take under a second plus the AI coaching time.
- **Limits:** the per-IP rate limits and AI budget are tracked per server instance.

Netlify can't run the Python API. To use Netlify, host the backend elsewhere and see `frontend/public/_redirects`.

## Docker (optional)

`docker compose up --build`, then open http://localhost:8080. Put it behind HTTPS for real hosting.
The API is stateless, so you can run several containers. Move the per-IP limits to Redis first (DESIGN §10).
