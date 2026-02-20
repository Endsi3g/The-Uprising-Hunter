# setup-env.ps1
# Script to automate Supabase environment variable extraction for the admin-dashboard

$FrontendDir = Join-Path $PSScriptRoot "..\admin-dashboard"
$EnvFile = Join-Path $FrontendDir ".env.local"

Write-Host "🔍 Attempting to extract Supabase credentials..." -ForegroundColor Yellow

try {
    # Run supabase status and capture output
    $Status = npx supabase status -o json | ConvertFrom-Json
    
    if ($Status) {
        $Url = $Status.api_url
        $AnonKey = $Status.anon_key
        
        $EnvContent = @"
NEXT_PUBLIC_SUPABASE_URL=$Url
NEXT_PUBLIC_SUPABASE_ANON_KEY=$AnonKey
"@
        
        Set-Content -Path $EnvFile -Value $EnvContent
        Write-Host "✅ Created .env.local with credentials from local Supabase." -ForegroundColor Green
        Write-Host "   URL: $Url"
    }
}
catch {
    Write-Warning "⚠️ Could not connect to local Supabase via CLI (is Docker running?)."
    
    if (-not (Test-Path $EnvFile)) {
        Write-Host "📝 Creating a template .env.local..." -ForegroundColor Yellow
        $Template = @"
# Supabase Configuration (Local Defaults)
NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-local-key-here
"@
        Set-Content -Path $EnvFile -Value $Template
        Write-Host "✅ Created template .env.local. Please update with your actual keys if different." -ForegroundColor Green
    }
    else {
        Write-Host "ℹ️ .env.local already exists. Skipping template creation." -ForegroundColor Gray
    }
}
