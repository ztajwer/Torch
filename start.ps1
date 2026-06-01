# TORCH — start backend + frontend
$Root = $PSScriptRoot
$ErrorActionPreference = "Stop"
Write-Host "Starting TORCH..." -ForegroundColor Cyan

$py = "$Root\backend\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
  Write-Host "Missing backend venv. Run once:" -ForegroundColor Red
  Write-Host "  cd backend; python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
  exit 1
}

$envFile = "$Root\.env"
if (-not (Test-Path $envFile)) {
  Copy-Item "$Root\.env.example" $envFile
  Write-Host "Created .env from .env.example — add your TORCH_GEMINI_API_KEY from https://aistudio.google.com/apikey" -ForegroundColor Yellow
} elseif (-not (Select-String -Path $envFile -Pattern 'TORCH_GEMINI_API_KEY=\s*\S+' -Quiet)) {
  Write-Host "Warning: TORCH_GEMINI_API_KEY is empty in .env — chat/search AI will use rule-based fallback only." -ForegroundColor Yellow
}

# Stop old servers
foreach ($port in 8000, 8001, 8010, 5173) {
  Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique |
    ForEach-Object { if ($_ -gt 0) { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue } }
}

Start-Sleep -Seconds 2

$backend = Start-Process -FilePath $py `
  -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8010" `
  -WorkingDirectory "$Root\backend" -PassThru -WindowStyle Normal

$backendOk = $false
for ($i = 0; $i -lt 30; $i++) {
  Start-Sleep -Seconds 1
  try {
    $h = Invoke-RestMethod -Uri "http://127.0.0.1:8010/health" -TimeoutSec 2
    if ($h.status -eq "ok") { $backendOk = $true; break }
  } catch { }
}
if (-not $backendOk) {
  Write-Host "Backend did not respond on http://127.0.0.1:8010/health — check the backend window for errors." -ForegroundColor Red
  exit 1
}

$frontend = Start-Process -FilePath "cmd.exe" `
  -ArgumentList "/c", "npm run dev" `
  -WorkingDirectory "$Root\frontend" -PassThru -WindowStyle Normal

Write-Host ""
Write-Host "Backend PID:  $($backend.Id)  -> http://127.0.0.1:8010 (healthy)" -ForegroundColor Green
Write-Host "Frontend PID: $($frontend.Id) -> http://127.0.0.1:5173" -ForegroundColor Green
Write-Host ""
Write-Host "Open: http://127.0.0.1:5173" -ForegroundColor Yellow
Write-Host "Search: iphone, ludo, laptop - live prices from Daraz, PriceOye, Telemart, Mega.pk" -ForegroundColor Yellow
