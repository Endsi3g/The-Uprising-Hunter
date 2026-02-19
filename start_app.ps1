Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Starting The Uprising Hunter (Backend + Frontend)" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

# Check for .venv
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Green
    & .venv\Scripts\Activate.ps1
}
else {
    Write-Host "[WARNING] .venv not found. Assuming global python or manual setup." -ForegroundColor Yellow
}

# Start Backend
Write-Host "[INFO] Starting The Uprising Hunter Backend (Port 8000)..." -ForegroundColor Green
Start-Process -FilePath "cmd" -ArgumentList "/k python -m uvicorn src.admin.app:app --port 8000 --reload" -WindowStyle Normal

# Start Frontend
Write-Host "[INFO] Starting Frontend Dashboard (Port 3000)..." -ForegroundColor Green
Set-Location "admin-dashboard"
Start-Process -FilePath "cmd" -ArgumentList "/k npm run dev" -WindowStyle Normal

Write-Host ""
Write-Host "[SUCCESS] Services started!" -ForegroundColor Green
Write-Host "- Backend: http://localhost:8000"
Write-Host "- Frontend: http://localhost:3000"
Write-Host ""
Write-Host "Close the new windows to stop the servers." -ForegroundColor Gray
Read-Host "Press Enter to exit this launcher..."
