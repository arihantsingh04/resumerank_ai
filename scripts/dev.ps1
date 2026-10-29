# Start the API (port 8000) and the web app (port 5173) in two windows.
#   powershell -File scripts\dev.ps1          # this PC only
#   powershell -File scripts\dev.ps1 -Lan     # also reachable from phones on the same Wi-Fi
# Any ResumeRank servers left running from an earlier session are stopped first, so the web app
# never talks to an old API version. The API always stays on 127.0.0.1; the web app proxies /api to it.
param([switch]$Lan)
$root = Split-Path -Parent $PSScriptRoot

$stale = Get-CimInstance Win32_Process | Where-Object {
  ($_.Name -in 'python.exe', 'uvicorn.exe' -and $_.CommandLine -like "*$root*uvicorn*") -or
  ($_.Name -eq 'node.exe' -and $_.CommandLine -like "*$root*vite*")
}
foreach ($p in $stale) {
  Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
}
if ($stale) { Write-Host "Stopped $(@($stale).Count) old ResumeRank server process(es)." -ForegroundColor Yellow; Start-Sleep -Seconds 1 }

$viteHost = if ($Lan) { "--host 0.0.0.0" } else { "" }
Start-Process powershell -WorkingDirectory "$root\backend" -ArgumentList "-NoExit", "-Command", ".\.venv\Scripts\uvicorn.exe app.main:create_app --factory --host 127.0.0.1 --port 8000"
Start-Process powershell -WorkingDirectory "$root\frontend" -ArgumentList "-NoExit", "-Command", "npx vite --port 5173 --strictPort $viteHost"

Write-Host "App: http://localhost:5173" -ForegroundColor Green
if ($Lan) {
  $ips = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' -and $_.PrefixOrigin -ne 'WellKnown' } | Select-Object -ExpandProperty IPAddress
  foreach ($ip in $ips) { Write-Host "On your phone (same Wi-Fi): http://${ip}:5173" -ForegroundColor Cyan }
  Write-Host "If the phone can't connect, allow port 5173 in Windows Firewall (see README)." -ForegroundColor Yellow
}
