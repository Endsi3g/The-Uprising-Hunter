param(
    [string]$OutputJsonPath = "artifacts/qa/validate_after_fix.json"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
$FrontendDir = Join-Path $RootDir "admin-dashboard"
$ResolvedOutputJsonPath = Join-Path $RootDir $OutputJsonPath

New-Item -ItemType Directory -Path (Split-Path $ResolvedOutputJsonPath -Parent) -Force | Out-Null

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory
    )

    $started = Get-Date
    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName = $FilePath
    $psi.WorkingDirectory = $WorkingDirectory
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $escapedArgs = $Arguments | ForEach-Object {
        if ($_ -match '\s' -or $_ -match '"') {
            '"' + ($_ -replace '"', '\"') + '"'
        } else {
            $_
        }
    }
    $psi.Arguments = ($escapedArgs -join " ")

    $process = [System.Diagnostics.Process]::Start($psi)
    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()
    $finished = Get-Date
    $duration = [Math]::Round(($finished - $started).TotalSeconds, 3)
    return @{
        name = $Name
        exit_code = [int]$process.ExitCode
        duration_seconds = $duration
        stdout_tail = @($stdout -split "`r?`n" | Select-Object -Last 40)
        stderr_tail = @($stderr -split "`r?`n" | Select-Object -Last 40)
    }
}

$results = @()
$results += Invoke-Step -Name "pytest" -FilePath "python" -Arguments @("-m", "pytest", "-q") -WorkingDirectory $RootDir
$results += Invoke-Step -Name "frontend_build" -FilePath "npm.cmd" -Arguments @("run", "build") -WorkingDirectory $FrontendDir
$results += Invoke-Step -Name "localhost_smoke" -FilePath "powershell" -Arguments @("-ExecutionPolicy", "Bypass", "-File", (Join-Path $RootDir "test_localhost_all_features.ps1"), "-SkipUnitTests", "-SkipFrontendBuild") -WorkingDirectory $RootDir

$ok = $true
foreach ($step in $results) {
    if ([int]$step.exit_code -ne 0) {
        $ok = $false
    }
}

$payload = @{
    generated_at = (Get-Date).ToString("o")
    ok = $ok
    steps = $results
}

$payload | ConvertTo-Json -Depth 10 | Set-Content -Path $ResolvedOutputJsonPath -Encoding UTF8
Write-Host ($payload | ConvertTo-Json -Depth 10)

if ($ok) {
    exit 0
}
exit 2
