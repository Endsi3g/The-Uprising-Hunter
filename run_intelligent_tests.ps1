param(
    [switch]$AutoFix,
    [switch]$SkipUnitTests,
    [switch]$SkipFrontendBuild,
    [switch]$SkipSmoke,
    [switch]$SkipScrape
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RootDir = $PSScriptRoot
$ScriptPath = Join-Path $RootDir "scripts\\qa\\run_intelligent_diagnostics.ps1"

& $ScriptPath `
    -AutoFix:$AutoFix `
    -SkipUnitTests:$SkipUnitTests `
    -SkipFrontendBuild:$SkipFrontendBuild `
    -SkipSmoke:$SkipSmoke `
    -SkipScrape:$SkipScrape
