# One-command deploy of ResumeRank (website + API) to Vercel (D-46).
#   powershell -ExecutionPolicy Bypass -File scripts\deploy-vercel.ps1
# First run: a browser opens once so you can log in to Vercel. After that, re-running just redeploys.
# Your GEMINI_API_KEY is copied from .env into Vercel's encrypted environment settings (never printed,
# never uploaded as a file: .env is excluded by .vercelignore).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$project = "resumerank"

function Vercel { & npx --yes vercel@latest @args }

Write-Host "==> Checking Vercel login" -ForegroundColor Cyan
& npx --yes vercel@latest whoami *> $null
if ($LASTEXITCODE -ne 0) {
  Write-Host "A browser window will open: log in to Vercel (free Hobby account is fine)." -ForegroundColor Yellow
  Vercel login
}

if (-not (Test-Path ".vercel\project.json")) {
  Write-Host "==> Creating / linking Vercel project '$project'" -ForegroundColor Cyan
  Vercel link --yes --project $project
}

Write-Host "==> Setting GEMINI_API_KEY (from .env)" -ForegroundColor Cyan
$line = Get-Content ".env" -ErrorAction SilentlyContinue | Where-Object { $_ -match '^\s*GEMINI_API_KEY\s*=\s*\S+' } | Select-Object -First 1
if ($line) {
  $key = ($line -split "=", 2)[1].Trim().Trim('"')
  # stdin keeps the key off the command line; --force overwrites, --sensitive stores it as a Secret
  $key | & npx --yes vercel@latest env add GEMINI_API_KEY --environment production --force --sensitive --yes *> $null
  Remove-Variable key
  Write-Host "Gemini key stored in Vercel (encrypted)." -ForegroundColor Green
} else {
  Write-Host "No GEMINI_API_KEY in .env: the site will work without the AI coach." -ForegroundColor Yellow
}

Write-Host "==> Deploying to production" -ForegroundColor Cyan
Vercel deploy --prod --yes
Write-Host "Done. The production URL is printed above (https://$project-....vercel.app)." -ForegroundColor Green
