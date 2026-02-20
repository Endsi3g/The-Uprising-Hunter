# ===================================================
#   The Uprising Hunter - Smart Launcher (PowerShell)
# ===================================================

$ErrorActionPreference = "Stop"
$LogFile = Join-Path $PSScriptRoot "startup_errors.log"

# ---------------------------------------------------
# 0. Cleanup / Reset
# ---------------------------------------------------
Write-Host "[INFO] Cleaning up previous sessions..." -ForegroundColor Cyan

# 1. Kill processes on ports 8000 and 3000
$Ports = 8000, 3000
foreach ($Port in $Ports) {
    Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | 
    Select-Object -ExpandProperty OwningProcess | 
    ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
}

# 2. Kill existing processes by window title
Get-Process | Where-Object { $_.MainWindowTitle -eq "The Uprising Hunter - Backend" -or $_.MainWindowTitle -eq "The Uprising Hunter - Frontend" } | Stop-Process -Force -ErrorAction SilentlyContinue

# Verify file unlock
Start-Sleep -Seconds 1
if (Test-Path $LogFile) {
    Remove-Item $LogFile -Force -ErrorAction SilentlyContinue
    if (Test-Path $LogFile) {
        Write-Host "[WARNING] Could not delete log file. It may be locked." -ForegroundColor Yellow
    }
}

"[" + (Get-Date).ToString("yyyy-MM-dd HH:mm:ss") + "] [INFO] Launcher started" | Out-File -FilePath $LogFile -Encoding UTF8 -Force

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Starting The Uprising Hunter (Backend + Frontend)" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host ""

# ---------------------------------------------------
# 1. Python Environment Setup
# ---------------------------------------------------
Write-Host "[STEP 1/4] Checking Python environment..." -ForegroundColor Yellow

if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "[INFO] Activating virtual environment..." -ForegroundColor Green
    & .venv\Scripts\Activate.ps1
}
else {
    Write-Host "[WARNING] .venv not found. Creating one..." -ForegroundColor Yellow
    try {
        Start-Process python -ArgumentList "-m venv .venv" -Wait -NoNewWindow -RedirectStandardError $LogFile
        Write-Host "[INFO] Virtual environment created. Activating..." -ForegroundColor Green
        & .venv\Scripts\Activate.ps1
        
        Write-Host "[INFO] Installing dependencies..." -ForegroundColor Cyan
        Start-Process python -ArgumentList "-m pip install --upgrade pip" -Wait -NoNewWindow -RedirectStandardError $LogFile
        if (Test-Path "requirements.txt") {
            Start-Process pip -ArgumentList "install -r requirements.txt" -Wait -NoNewWindow -RedirectStandardError $LogFile
            Write-Host "[SUCCESS] Python dependencies installed." -ForegroundColor Green
        }
    }
    catch {
        Write-Host "[ERROR] Failed to setup Python environment. Check startup_errors.log" -ForegroundColor Red
        "[" + (Get-Date).ToString("yyyy-MM-dd HH:mm:ss") + "] [ERROR] Python setup failed: $_" | Out-File -FilePath $LogFile -Append -Encoding UTF8
        Read-Host "Press Enter to exit..."
        exit 1
    }
}

# ---------------------------------------------------
# 2. Node.js Environment Setup
# ---------------------------------------------------
Write-Host "[STEP 2/4] Checking Node.js environment..." -ForegroundColor Yellow

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    if (Test-Path "C:\Program Files\nodejs\node.exe") {
        Write-Host "[INFO] Adding Node.js to session PATH..." -ForegroundColor Green
        $env:PATH = "C:\Program Files\nodejs;$env:PATH"
    }
    else {
        Write-Host "[ERROR] Node.js not found." -ForegroundColor Red
        "[" + (Get-Date).ToString("yyyy-MM-dd HH:mm:ss") + "] [ERROR] Node.js not found" | Out-File -FilePath $LogFile -Append -Encoding UTF8
        Read-Host "Press Enter to exit..."
        exit 1
    }
}

if (Test-Path "admin-dashboard\package.json") {
    if (-not (Test-Path "admin-dashboard\node_modules")) {
        Write-Host "[INFO] node_modules missing. Installing..." -ForegroundColor Cyan
        Push-Location "admin-dashboard"
        try {
            Start-Process npm -ArgumentList "install" -Wait -NoNewWindow -RedirectStandardError $LogFile
            Write-Host "[SUCCESS] Frontend dependencies installed." -ForegroundColor Green
        }
        catch {
            Write-Host "[ERROR] npm install failed." -ForegroundColor Red
            "[" + (Get-Date).ToString("yyyy-MM-dd HH:mm:ss") + "] [ERROR] npm install failed: $_" | Out-File -FilePath $LogFile -Append -Encoding UTF8
        }
        Pop-Location
    }
}

# ---------------------------------------------------
# 3. Start Backend
# ---------------------------------------------------
Write-Host "[STEP 3/4] Starting Backend (Port 8000)..." -ForegroundColor Green
Start-Process -FilePath "cmd" -ArgumentList "/k python -m uvicorn src.admin.app:app --port 8000 --reload 2>> `"$LogFile`"" -WindowStyle Normal

# ---------------------------------------------------
# 4. Start Frontend
# ---------------------------------------------------
Write-Host "[STEP 4/4] Starting Frontend (Port 3000)..." -ForegroundColor Green
Set-Location "admin-dashboard"
Start-Process -FilePath "cmd" -ArgumentList "/k npm run dev 2>> `"$LogFile`"" -WindowStyle Normal

Write-Host ""
Write-Host "[SUCCESS] Services launched!" -ForegroundColor Green
Write-Host "Errors (if any) are logged to: $LogFile" -ForegroundColor Gray
Write-Host "- Backend: http://localhost:8000"
Write-Host "- Frontend: http://localhost:3000"
Write-Host ""
Read-Host "Press Enter to exit this launcher..."
