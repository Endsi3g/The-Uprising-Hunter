param(
    [Parameter(Mandatory = $true)][string]$PromptPath,
    [string]$OutputMessagePath = "artifacts/qa/codex_last_message.txt",
    [string]$OutputJsonPath = "artifacts/qa/latest_autofix.json",
    [string]$Model = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RootDir = (Resolve-Path (Join-Path $PSScriptRoot "..\\..")).Path
$ResolvedPromptPath = (Resolve-Path $PromptPath).Path
$ResolvedOutputMessagePath = Join-Path $RootDir $OutputMessagePath
$ResolvedOutputJsonPath = Join-Path $RootDir $OutputJsonPath

New-Item -ItemType Directory -Path (Split-Path $ResolvedOutputMessagePath -Parent) -Force | Out-Null
New-Item -ItemType Directory -Path (Split-Path $ResolvedOutputJsonPath -Parent) -Force | Out-Null

$promptText = Get-Content $ResolvedPromptPath -Raw
$startedAt = (Get-Date).ToString("o")

$args = @("exec", "--full-auto", "--cd", $RootDir, "--output-last-message", $ResolvedOutputMessagePath)
if ($Model) {
    $args += @("--model", $Model)
}
$args += @($promptText)

& codex @args
$exitCode = $LASTEXITCODE
$finishedAt = (Get-Date).ToString("o")

$payload = @{
    started_at = $startedAt
    finished_at = $finishedAt
    ok = ($exitCode -eq 0)
    return_code = [int]$exitCode
    prompt_path = $ResolvedPromptPath
    output_message_path = $ResolvedOutputMessagePath
}

$payload | ConvertTo-Json -Depth 6 | Set-Content -Path $ResolvedOutputJsonPath -Encoding UTF8
Write-Host ($payload | ConvertTo-Json -Depth 6)

exit $exitCode
