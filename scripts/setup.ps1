# One-time local setup for Windows (PowerShell). Run from the repo root:
#   powershell -ExecutionPolicy Bypass -File scripts\setup.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$env:PIP_NO_CACHE_DIR = "1"   # keep the (often small) C: drive free

Write-Host "==> Backend virtual environment" -ForegroundColor Cyan
if (-not (Test-Path backend\.venv)) { python -m venv backend\.venv }
$py = "backend\.venv\Scripts\python.exe"
& $py -m pip install --upgrade pip
& $py -m pip install torch --index-url https://download.pytorch.org/whl/cpu
& $py -m pip install -r backend\requirements-dev.txt

Write-Host "==> .env" -ForegroundColor Cyan
if (-not (Test-Path .env)) {
  Copy-Item .env.example .env
  Write-Host "Created .env. Add GEMINI_API_KEY to enable AI coaching." -ForegroundColor Yellow
} else { Write-Host ".env already exists - left unchanged." }

Write-Host "==> Frontend packages" -ForegroundColor Cyan
Push-Location frontend
npm install --no-audit --no-fund --cache .npm-cache
Pop-Location

Write-Host "Done. Start the app with: powershell -File scripts\dev.ps1" -ForegroundColor Green
