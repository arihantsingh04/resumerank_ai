# Share the running app through a temporary public HTTPS link (Cloudflare quick tunnel).
#   1) Start the app first:   powershell -File scripts\dev.ps1
#   2) Then run:              powershell -File scripts\share.ps1
# Look for a line like  https://<random-words>.trycloudflare.com  and open it on any device.
# Anyone with the link can use the app (and your Gemini quota) while this window is open.
# Close this window or press Ctrl+C to shut the link down.
$root = Split-Path -Parent $PSScriptRoot
$exe = Join-Path $root ".tools\cloudflared.exe"

if (-not (Test-Path $exe)) {
  New-Item -ItemType Directory -Force (Split-Path $exe) | Out-Null
  Write-Host "Downloading cloudflared (one time, ~50 MB)..." -ForegroundColor Cyan
  Invoke-WebRequest "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile $exe -UseBasicParsing
}
$sig = Get-AuthenticodeSignature $exe
if ($sig.Status -ne "Valid" -or $sig.SignerCertificate.Subject -notmatch "Cloudflare") {
  Write-Host "cloudflared.exe is not validly signed by Cloudflare. Delete $exe and try again." -ForegroundColor Red
  exit 1
}
try {
  Invoke-WebRequest "http://localhost:5173/" -UseBasicParsing -TimeoutSec 5 | Out-Null
} catch {
  Write-Host "The app isn't running on http://localhost:5173. Start it with scripts\dev.ps1 first." -ForegroundColor Red
  exit 1
}

Write-Host "Opening a temporary public link. Copy the https://...trycloudflare.com address below." -ForegroundColor Green
Write-Host "Anyone with the link can use the app while this window is open. Ctrl+C to stop." -ForegroundColor Yellow
& $exe tunnel --no-autoupdate --url http://localhost:5173 --protocol http2
