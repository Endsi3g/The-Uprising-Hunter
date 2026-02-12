$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
$FrontendDir = Join-Path $RootDir "admin-dashboard"
$VenvDir = Join-Path $RootDir ".venv"
$PythonExe = Join-Path $VenvDir "Scripts\\python.exe"
$PidFile = Join-Path $PSScriptRoot ".localhost_pids.json"

Write-Host "[INFO] Root directory: $RootDir"

if (-not (Test-Path $PythonExe)) {
    Write-Host "[INFO] Creating Python virtual environment..."
    python -m venv $VenvDir
}

Write-Host "[INFO] Installing Python dependencies..."
& $PythonExe -m pip install -r (Join-Path $RootDir "requirements.txt")

if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
    Write-Host "[INFO] Installing frontend dependencies..."
    Push-Location $FrontendDir
    npm.cmd install
    Pop-Location
}

$EnvLocalPath = Join-Path $FrontendDir ".env.local"
@"
API_BASE_URL=http://localhost:8000
ADMIN_AUTH=admin:change-me
"@ | Set-Content $EnvLocalPath -Encoding UTF8
Write-Host "[INFO] Wrote $EnvLocalPath"

Write-Host "[INFO] Starting backend on :8000..."
$BackendProc = Start-Process `
    -FilePath $PythonExe `
    -ArgumentList @("-m", "uvicorn", "src.admin.app:app", "--reload", "--port", "8000") `
    -WorkingDirectory $RootDir `
    -PassThru

$BackendReady = $false
for ($i = 0; $i -lt 60; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:8000/healthz" -TimeoutSec 2 -UseBasicParsing
        if ($resp.StatusCode -eq 200) {
            $BackendReady = $true
            break
        }
    }
    catch {
        Start-Sleep -Seconds 1
    }
}

if (-not $BackendReady) {
    Write-Warning "Backend healthcheck failed on http://localhost:8000/healthz"
}

Write-Host "[INFO] Starting frontend on :3000..."
$NpmCmd = (Get-Command npm.cmd -ErrorAction Stop).Source
$FrontendProc = Start-Process `
    -FilePath $NpmCmd `
    -ArgumentList @("run", "dev", "--", "--port", "3000") `
    -WorkingDirectory $FrontendDir `
    -PassThru

@{
    backend_pid = $BackendProc.Id
    frontend_pid = $FrontendProc.Id
    started_at = (Get-Date).ToString("o")
} | ConvertTo-Json | Set-Content $PidFile -Encoding UTF8

Write-Host ""
Write-Host "=== LOCALHOST STACK STARTED ==="
Write-Host "Backend : http://localhost:8000"
Write-Host "Frontend: http://localhost:3000"
Write-Host "PID file: $PidFile"
Write-Host ""
Write-Host "Stop both services with:"
Write-Host ".\\scripts\\ops\\stop_localhost.ps1"

