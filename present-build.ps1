# Run ONCE before your presentation (at home). Builds UI into backend/static.
$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

Write-Host "TORCH - preparing offline demo build..." -ForegroundColor Cyan

$py = "$Root\backend\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
  Write-Host "Creating Python venv..." -ForegroundColor Yellow
  Push-Location "$Root\backend"
  python -m venv .venv
  .\.venv\Scripts\pip install -r requirements.txt
  Pop-Location
}

if (-not (Test-Path "$Root\frontend\node_modules")) {
  Write-Host "Installing frontend packages (one time)..." -ForegroundColor Yellow
  Push-Location "$Root\frontend"
  npm install
  Pop-Location
}

Write-Host "Building frontend..." -ForegroundColor Yellow
Push-Location "$Root\frontend"
$env:VITE_API_BASE = ""
npm run build
Pop-Location

$static = "$Root\backend\static"
if (Test-Path $static) { Remove-Item $static -Recurse -Force }
Copy-Item "$Root\frontend\dist" $static -Recurse

Write-Host ""
Write-Host "Ready. At the venue run:  .\present.ps1" -ForegroundColor Green
Write-Host "Demo URL on that PC: http://127.0.0.1:8010" -ForegroundColor Green
