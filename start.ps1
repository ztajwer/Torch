# TORCH — start backend + frontend
$Root = $PSScriptRoot
Write-Host "Starting TORCH..." -ForegroundColor Cyan

# Stop old servers
foreach ($port in 8000, 8001, 8010, 5173) {
  Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique |
    ForEach-Object { if ($_ -gt 0) { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue } }
}

Start-Sleep -Seconds 2

$backend = Start-Process -FilePath "$Root\backend\.venv\Scripts\python.exe" `
  -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8010" `
  -WorkingDirectory "$Root\backend" -PassThru -WindowStyle Normal

Start-Sleep -Seconds 3

$frontend = Start-Process -FilePath "cmd.exe" `
  -ArgumentList "/c", "npm run dev" `
  -WorkingDirectory "$Root\frontend" -PassThru -WindowStyle Normal

Write-Host ""
Write-Host "Backend PID:  $($backend.Id)  -> http://127.0.0.1:8010" -ForegroundColor Green
Write-Host "Frontend PID: $($frontend.Id) -> http://127.0.0.1:5173" -ForegroundColor Green
Write-Host ""
Write-Host "Open: http://127.0.0.1:5173" -ForegroundColor Yellow
Write-Host "Search: iphone, ludo, laptop - live prices from Daraz, PriceOye, Telemart, Mega.pk" -ForegroundColor Yellow
