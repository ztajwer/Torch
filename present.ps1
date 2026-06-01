# TORCH — 30-second presentation launcher (one URL, no Render)
# Run present-build.ps1 once at home first.
param(
  [switch]$Tunnel  # Optional: public URL via localtunnel (needs internet)
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

$py = "$Root\backend\.venv\Scripts\python.exe"
$static = "$Root\backend\static"

if (-not (Test-Path $py)) {
  Write-Host "First time only — run:  .\present-build.ps1" -ForegroundColor Red
  exit 1
}
if (-not (Test-Path "$static\index.html")) {
  Write-Host "UI not built yet — run:  .\present-build.ps1" -ForegroundColor Red
  exit 1
}

foreach ($port in 8000, 8001, 8010, 5173) {
  Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique |
    ForEach-Object { if ($_ -gt 0) { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue } }
}
Start-Sleep -Seconds 1

$env:TORCH_SERVE_STATIC = "true"
$env:TORCH_ENVIRONMENT = "production"

Write-Host "Starting TORCH demo on http://127.0.0.1:8010 ..." -ForegroundColor Cyan

$server = Start-Process -FilePath $py `
  -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8010" `
  -WorkingDirectory "$Root\backend" -PassThru -WindowStyle Normal

$ok = $false
for ($i = 0; $i -lt 25; $i++) {
  Start-Sleep -Seconds 1
  try {
    $h = Invoke-RestMethod -Uri "http://127.0.0.1:8010/health" -TimeoutSec 2
    if ($h.status -eq "ok") { $ok = $true; break }
  } catch { }
}
if (-not $ok) {
  Write-Host "Server failed to start — check the Python window." -ForegroundColor Red
  exit 1
}

Start-Process "http://127.0.0.1:8010"
Write-Host ""
Write-Host "TORCH is running." -ForegroundColor Green
Write-Host "  Open in browser:  http://127.0.0.1:8010" -ForegroundColor Yellow
Write-Host "  Demo search:      iphone   or   samsung   or   laptop" -ForegroundColor Yellow
Write-Host "  Keep the Python window open during your talk." -ForegroundColor DarkGray

if ($Tunnel) {
  Write-Host ""
  Write-Host "Starting public link (localtunnel)..." -ForegroundColor Cyan
  Write-Host "Copy the https://.... URL shown below — anyone can open it." -ForegroundColor Yellow
  Push-Location $Root
  npx --yes localtunnel --port 8010
}
