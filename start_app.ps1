# ===================================================
#   The Uprising Hunter - Smart Launcher (PowerShell)
# ===================================================

$ErrorActionPreference = "Stop"
$LauncherLog = Join-Path $PSScriptRoot "startup_launcher.log"
$BackendLog = Join-Path $PSScriptRoot "startup_backend.log"
$FrontendLog = Join-Path $PSScriptRoot "startup_frontend.log"

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
Get-Process | Where-Object { $_.MainWindowTitle -match "The Uprising Hunter" } | Stop-Process -Force -ErrorAction SilentlyContinue

# Verify file unlock
Start-Sleep -Seconds 1
foreach ($file in @($LauncherLog, $BackendLog, $FrontendLog)) {
    if (Test-Path $file) {
        Remove-Item $file -Force -ErrorAction SilentlyContinue
    }
}

"[" + (Get-Date).ToString("yyyy-MM-dd HH:mm:ss") + "] [INFO] Launcher started" | Out-File -FilePath $LauncherLog -Encoding UTF8 -Force

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
    try {
        & .venv\Scripts\Activate.ps1
    }
    catch {
        Write-Host "[ERROR] Failed to activate virtual environment: $_" -ForegroundColor Red
        Write-Host "[TIP] Check your execution policy (Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass)" -ForegroundColor Gray
        "[" + (Get-Date).ToString("yyyy-MM-dd HH:mm:ss") + "] [ERROR] Failed to activate virtual environment: $_" | Out-File -FilePath $LauncherLog -Append -Encoding UTF8
        Read-Host "Press Enter to exit..."
        exit 1
    }
}
else {
    Write-Host "[WARNING] .venv not found. Creating one..." -ForegroundColor Yellow
    try {
        python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw "Failed to create virtual environment" }
        
        Write-Host "[INFO] Virtual environment created. Activating..." -ForegroundColor Green
        & .venv\Scripts\Activate.ps1
        
        Write-Host "[INFO] Installing dependencies..." -ForegroundColor Cyan
        python -m pip install --upgrade pip
        if ($LASTEXITCODE -ne 0) { throw "Failed to upgrade pip" }
        
        if (Test-Path "requirements.txt") {
            pip install -r requirements.txt
            if ($LASTEXITCODE -ne 0) { throw "Failed to install Python dependencies" }
            Write-Host "[SUCCESS] Python dependencies installed." -ForegroundColor Green
        }
    }
    catch {
        Write-Host "[ERROR] Failed to setup Python environment. Check $LauncherLog" -ForegroundColor Red
        "[" + (Get-Date).ToString("yyyy-MM-dd HH:mm:ss") + "] [ERROR] Python setup failed: $_" | Out-File -FilePath $LauncherLog -Append -Encoding UTF8
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
        "[" + (Get-Date).ToString("yyyy-MM-dd HH:mm:ss") + "] [ERROR] Node.js not found" | Out-File -FilePath $LauncherLog -Append -Encoding UTF8
        Read-Host "Press Enter to exit..."
        exit 1
    }
}

if (Test-Path "admin-dashboard\package.json") {
    if (-not (Test-Path "admin-dashboard\node_modules")) {
        Write-Host "[INFO] node_modules missing. Installing..." -ForegroundColor Cyan
        Push-Location "admin-dashboard"
        try {
            npm install
            if ($LASTEXITCODE -ne 0) { throw "npm install failed" }
            Write-Host "[SUCCESS] Frontend dependencies installed." -ForegroundColor Green
        }
        catch {
            Write-Host "[ERROR] npm install failed. Check $LauncherLog" -ForegroundColor Red
            "[" + (Get-Date).ToString("yyyy-MM-dd HH:mm:ss") + "] [ERROR] npm install failed: $_" | Out-File -FilePath $LauncherLog -Append -Encoding UTF8
            Pop-Location
            Read-Host "Press Enter to exit..."
            exit 1
        }
        Pop-Location
    }
}

# ---------------------------------------------------
# 3. Start Backend
# ---------------------------------------------------
Write-Host "[STEP 3/4] Starting Backend (Port 8000)..." -ForegroundColor Green
$BackendCmd = "python -m uvicorn src.admin.app:app --host 127.0.0.1 --port 8000 2> `"$BackendLog`""
Start-Process -FilePath "cmd" -ArgumentList "/k $BackendCmd" -WorkingDirectory $PSScriptRoot -WindowStyle Normal

# ---------------------------------------------------
# 4. Start Frontend
# ---------------------------------------------------
Write-Host "[STEP 4/4] Starting Frontend (Port 3000)..." -ForegroundColor Green
$FrontendCmd = "npm run dev 2> `"$FrontendLog`""
Start-Process -FilePath "cmd" -ArgumentList "/c cd admin-dashboard && $FrontendCmd" -WindowStyle Normal

Write-Host ""
Write-Host "[SUCCESS] Services launched!" -ForegroundColor Green
Write-Host "- Backend Log: $BackendLog" -ForegroundColor Gray
Write-Host "- Frontend Log: $FrontendLog" -ForegroundColor Gray
Write-Host "- Backend URL: http://localhost:8000"
Write-Host "- Frontend URL: http://localhost:3000"
Write-Host ""
Read-Host "Press Enter to exit this launcher..."
