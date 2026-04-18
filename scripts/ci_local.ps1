Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$BootstrapScript = Join-Path $PSScriptRoot "bootstrap_python.ps1"
$PreflightScript = Join-Path $PSScriptRoot "preflight.ps1"
$PythonExe = Join-Path $RepoRoot "tools\python\python.exe"

Write-Host "== CI locale: bootstrap =="
& $BootstrapScript

if (-not (Test-Path $PythonExe)) {
    throw "Python locale non trovato: $PythonExe"
}

Write-Host "== CI locale: preflight =="
& $PreflightScript

Write-Host "== CI locale: test =="
& $PythonExe -m unittest discover -s (Join-Path $RepoRoot "tests") -p "test_*.py"

Write-Host "== CI locale completata con successo =="
