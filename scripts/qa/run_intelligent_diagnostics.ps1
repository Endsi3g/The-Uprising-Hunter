param(
    [switch]$AutoFix,
    [switch]$SkipUnitTests,
    [switch]$SkipFrontendBuild,
    [switch]$SkipSmoke,
    [switch]$SkipScrape,
    [switch]$WriteArtifactsOnly,
    [string]$Model = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
$FrontendDir = Join-Path $RootDir "admin-dashboard"
$ArtifactsDir = Join-Path $RootDir "artifacts\\qa"
$CommandResultsPath = Join-Path $ArtifactsDir "command_results_latest.json"
$ScrapeResultsPath = Join-Path $ArtifactsDir "scrape_latest.json"
$AnalysisJsonPath = Join-Path $ArtifactsDir "latest_diagnostics.json"
$AnalysisMdPath = Join-Path $ArtifactsDir "latest_diagnostics.md"
$PromptPath = Join-Path $ArtifactsDir "codex_autofix_prompt.txt"
$AutofixPath = Join-Path $ArtifactsDir "latest_autofix.json"
$ValidatePath = Join-Path $ArtifactsDir "validate_after_fix.json"

New-Item -ItemType Directory -Path $ArtifactsDir -Force | Out-Null

function Write-Step([string]$Message) {
    if (-not $WriteArtifactsOnly) {
        Write-Host ""
        Write-Host "== $Message =="
    }
}

function Invoke-Step {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory
    )

    Write-Step $Name

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
    $stdoutTail = @($stdout -split "`r?`n" | Select-Object -Last 60)
    $stderrTail = @($stderr -split "`r?`n" | Select-Object -Last 60)

    if (-not $WriteArtifactsOnly) {
        foreach ($line in $stdoutTail) {
            if (-not [string]::IsNullOrWhiteSpace($line)) {
                Write-Host $line
            }
        }
        foreach ($line in $stderrTail) {
            if (-not [string]::IsNullOrWhiteSpace($line)) {
                Write-Host $line
            }
        }
    }

    return @{
        name = $Name
        command = "$FilePath $($Arguments -join ' ')"
        started_at = $started.ToString("o")
        finished_at = $finished.ToString("o")
        duration_seconds = $duration
        exit_code = [int]$process.ExitCode
        stdout_tail = $stdoutTail
        stderr_tail = $stderrTail
    }
}

$results = @()

if (-not $SkipUnitTests) {
    $results += Invoke-Step -Name "pytest" -FilePath "python" -Arguments @("-m", "pytest", "-q") -WorkingDirectory $RootDir
}
if (-not $SkipFrontendBuild) {
    $results += Invoke-Step -Name "frontend_build" -FilePath "npm.cmd" -Arguments @("run", "build") -WorkingDirectory $FrontendDir
}
if (-not $SkipSmoke) {
    $results += Invoke-Step -Name "localhost_smoke" -FilePath "powershell" -Arguments @("-ExecutionPolicy", "Bypass", "-File", (Join-Path $RootDir "test_localhost_all_features.ps1"), "-SkipUnitTests", "-SkipFrontendBuild") -WorkingDirectory $RootDir
}
if (-not $SkipScrape) {
    $results += Invoke-Step -Name "frontend_scrape" -FilePath "node" -Arguments @((Join-Path $RootDir "scripts\\qa\\scrape_frontend_errors.mjs"), "--output", $ScrapeResultsPath) -WorkingDirectory $RootDir
} else {
    @{
        generated_at = (Get-Date).ToString("o")
        issue_count = 0
        error_count = 0
        warning_count = 0
        issues = @()
    } | ConvertTo-Json -Depth 10 | Set-Content -Path $ScrapeResultsPath -Encoding UTF8
}

$commandPayload = @{
    generated_at = (Get-Date).ToString("o")
    commands = $results
}
$commandPayload | ConvertTo-Json -Depth 10 | Set-Content -Path $CommandResultsPath -Encoding UTF8

$analysisStep = Invoke-Step -Name "analyze_findings" -FilePath "python" -Arguments @(
    (Join-Path $RootDir "scripts\\qa\\analyze_findings.py"),
    "--commands",
    $CommandResultsPath,
    "--scrape",
    $ScrapeResultsPath,
    "--output-json",
    $AnalysisJsonPath,
    "--output-md",
    $AnalysisMdPath
) -WorkingDirectory $RootDir
$results += $analysisStep

$analysisExists = Test-Path $AnalysisJsonPath
if (-not $analysisExists) {
    $fallbackAnalysis = @{
        generated_at = (Get-Date).ToString("o")
        ok = $false
        error_count = 1
        warning_count = 0
        findings = @(
            @{
                kind = "command"
                name = "analyze_findings"
                severity = "error"
                message = "Failed to generate diagnostics analysis artifact."
            }
        )
        recommendations = @("Inspect scripts/qa/analyze_findings.py output and command results JSON.")
    }
    $fallbackAnalysis | ConvertTo-Json -Depth 10 | Set-Content -Path $AnalysisJsonPath -Encoding UTF8
}

$analysis = Get-Content -Path $AnalysisJsonPath -Raw | ConvertFrom-Json
$analysisOk = [bool]$analysis.ok

if ($AutoFix -and -not $analysisOk) {
    Invoke-Step -Name "build_codex_prompt" -FilePath "python" -Arguments @(
        (Join-Path $RootDir "scripts\\qa\\build_codex_prompt.py"),
        "--analysis",
        $AnalysisJsonPath,
        "--output",
        $PromptPath
    ) -WorkingDirectory $RootDir | Out-Null

    $autofixArgs = @(
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        (Join-Path $RootDir "scripts\\qa\\run_codex_autofix.ps1"),
        "-PromptPath",
        $PromptPath,
        "-OutputJsonPath",
        $AutofixPath
    )
    if ($Model) {
        $autofixArgs += @("-Model", $Model)
    }

    $results += Invoke-Step -Name "codex_autofix" -FilePath "powershell" -Arguments $autofixArgs -WorkingDirectory $RootDir
    $results += Invoke-Step -Name "validate_after_fix" -FilePath "powershell" -Arguments @("-ExecutionPolicy", "Bypass", "-File", (Join-Path $RootDir "scripts\\qa\\validate_after_fix.ps1"), "-OutputJsonPath", $ValidatePath) -WorkingDirectory $RootDir
} elseif ($AutoFix) {
    @{
        generated_at = (Get-Date).ToString("o")
        ok = $true
        detail = "AutoFix requested but diagnostics were already clean."
    } | ConvertTo-Json -Depth 10 | Set-Content -Path $AutofixPath -Encoding UTF8
}

$finalPayload = @{
    generated_at = (Get-Date).ToString("o")
    ok = $analysisOk
    auto_fix = [bool]$AutoFix
    artifacts = @{
        commands = $CommandResultsPath
        scrape = $ScrapeResultsPath
        diagnostics_json = $AnalysisJsonPath
        diagnostics_md = $AnalysisMdPath
        autofix_json = $AutofixPath
        validate_json = $ValidatePath
    }
    steps = $results
}

if (-not $WriteArtifactsOnly) {
    Write-Host ""
    Write-Host "Diagnostics artifact: $AnalysisJsonPath"
    Write-Host "Diagnostics markdown: $AnalysisMdPath"
    if ($AutoFix) {
        Write-Host "Autofix artifact: $AutofixPath"
    }
}

Write-Host ($finalPayload | ConvertTo-Json -Depth 10)

if ($analysisOk) {
    exit 0
}
exit 2
