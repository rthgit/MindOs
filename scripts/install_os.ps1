Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$BootstrapScript = Join-Path $PSScriptRoot "bootstrap_python.ps1"
$PreflightScript = Join-Path $PSScriptRoot "preflight.ps1"
$CiScript = Join-Path $PSScriptRoot "ci_local.ps1"
$PythonExe = Join-Path $RepoRoot "tools\python\python.exe"
$RuntimeDir = Join-Path $RepoRoot ".runtime_data"
$HealthFile = Join-Path $RuntimeDir "install_health.json"

Write-Host "== Install OS: bootstrap runtime =="
& $BootstrapScript

if (-not (Test-Path $PythonExe)) {
    throw "Python locale non trovato dopo bootstrap: $PythonExe"
}

Write-Host "== Install OS: preflight =="
& $PreflightScript

Write-Host "== Install OS: full CI =="
& $CiScript

Write-Host "== Install OS: initialize runtime data =="
New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null
$health = @{
    status = "installed"
    timestamp_utc = [DateTime]::UtcNow.ToString("o")
    python = $PythonExe
    runtime_env = (Join-Path $RepoRoot "runtime.env.json")
}
$health | ConvertTo-Json -Depth 4 | Set-Content -Path $HealthFile -Encoding UTF8

Write-Host "== Install OS completed =="
