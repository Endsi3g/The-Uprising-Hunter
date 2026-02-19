$ErrorActionPreference = "Stop"

# Configuration paths
$MonitoringDir = Join-Path $PSScriptRoot "..\monitoring"
$PrometheusConfig = Join-Path $MonitoringDir "prometheus.yml"

# Check if docker is running
Try {
    docker info > $null 2>&1
}
Catch {
    Write-Error "Docker is not running. Please start Docker Desktop and try again."
    Exit 1
}

# 1. Set Service Role Key
Write-Host "Supabase Monitoring Setup" -ForegroundColor Cyan
Write-Host "-------------------------" -ForegroundColor Cyan
$ServiceRoleKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZyY2ZheGNrdnFvaml6d2hiYWFjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTQ2NDQ5OCwiZXhwIjoyMDg3MDQwNDk4fQ.QM5fBpQQtI74I3WxxQ_Yorygtwr1RlKXiD96qLSdokQ"

# 2. Update prometheus.yml
if (Test-Path $PrometheusConfig) {
    $ConfigContent = Get-Content $PrometheusConfig -Raw
    if ($ConfigContent -match "INSERT_SERVICE_ROLE_KEY_HERE") {
        $NewContent = $ConfigContent -replace "INSERT_SERVICE_ROLE_KEY_HERE", $ServiceRoleKey
        Set-Content -Path $PrometheusConfig -Value $NewContent
        Write-Host "✅ prometheus.yml updated with your key." -ForegroundColor Green
    }
    else {
        Write-Warning "Placeholder 'INSERT_SERVICE_ROLE_KEY_HERE' not found in prometheus.yml. Skipping replacement."
    }
}
else {
    Write-Error "prometheus.yml not found at $PrometheusConfig"
    Exit 1
}

# 3. Launch Docker Compose
Write-Host "🚀 Launching monitoring stack..." -ForegroundColor Cyan
Push-Location $MonitoringDir
try {
    docker-compose up -d
    Write-Host "✅ Monitoring stack started!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Acces dashboards:" -ForegroundColor Yellow
    Write-Host "   Grafana:    http://localhost:3001 (admin/admin)"
    Write-Host "   Prometheus: http://localhost:9090"
}
finally {
    Pop-Location
}
