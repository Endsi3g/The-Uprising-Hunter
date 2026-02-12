$ErrorActionPreference = "SilentlyContinue"

$PidFile = Join-Path $PSScriptRoot ".localhost_pids.json"

function Stop-IfRunning([int]$Pid) {
    if ($Pid -le 0) { return }
    $proc = Get-Process -Id $Pid -ErrorAction SilentlyContinue
    if ($null -ne $proc) {
        Write-Host "[INFO] Stopping PID $Pid ($($proc.ProcessName))"
        Stop-Process -Id $Pid -Force
    }
}

if (Test-Path $PidFile) {
    try {
        $pids = Get-Content $PidFile | ConvertFrom-Json
        Stop-IfRunning -Pid ([int]$pids.backend_pid)
        Stop-IfRunning -Pid ([int]$pids.frontend_pid)
    }
    catch {
        Write-Warning "Unable to parse PID file: $PidFile"
    }
    Remove-Item $PidFile -Force
}

foreach ($port in @(8000, 3000)) {
    $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    foreach ($connection in $connections) {
        if ($connection.OwningProcess -gt 0) {
            Stop-IfRunning -Pid ([int]$connection.OwningProcess)
        }
    }
}

Write-Host "Localhost services stopped for ports 8000 and 3000."

