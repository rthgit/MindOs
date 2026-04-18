Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$PythonExe = Join-Path $RepoRoot "tools\python\python.exe"

function Assert-PathExists {
    param([string]$PathToCheck)
    if (-not (Test-Path $PathToCheck)) {
        throw "Path obbligatorio mancante: $PathToCheck"
    }
}

function Assert-Contains {
    param(
        [string]$FilePath,
        [string]$Needle
    )
    $content = Get-Content $FilePath -Raw
    if ($content -notmatch [regex]::Escape($Needle)) {
        throw "Contenuto obbligatorio non trovato in $FilePath : $Needle"
    }
}

if (-not (Test-Path $PythonExe)) {
    throw "Python locale non trovato: $PythonExe"
}

Write-Host "== Preflight: struttura repository =="
@(
    (Join-Path $RepoRoot "runtime.env.json"),
    (Join-Path $RepoRoot "core\orchestrator\engine.py"),
    (Join-Path $RepoRoot "core\memory\store.py"),
    (Join-Path $RepoRoot "core\plugin\registry.py"),
    (Join-Path $RepoRoot "surfaces\cli\main.py"),
    (Join-Path $RepoRoot "surfaces\desktop\shell.py"),
    (Join-Path $RepoRoot "surfaces\ide\view.py"),
    (Join-Path $RepoRoot "docs\contracts\interfaces.md"),
    (Join-Path $RepoRoot "docs\contracts\events.md"),
    (Join-Path $RepoRoot "tests\test_e2e_vertical_slice.py")
) | ForEach-Object { Assert-PathExists $_ }

Write-Host "== Preflight: contratti minimi =="
Assert-Contains -FilePath (Join-Path $RepoRoot "docs\contracts\interfaces.md") -Needle "SubmitIntent"
Assert-Contains -FilePath (Join-Path $RepoRoot "docs\contracts\interfaces.md") -Needle "DispatchExecution"
Assert-Contains -FilePath (Join-Path $RepoRoot "docs\contracts\interfaces.md") -Needle "AppendEvent"
Assert-Contains -FilePath (Join-Path $RepoRoot "docs\contracts\events.md") -Needle "IntentAccepted"
Assert-Contains -FilePath (Join-Path $RepoRoot "docs\contracts\events.md") -Needle "PlanCreated"
Assert-Contains -FilePath (Join-Path $RepoRoot "docs\contracts\events.md") -Needle "RunStarted"
Assert-Contains -FilePath (Join-Path $RepoRoot "docs\contracts\events.md") -Needle "RunFinished"

Write-Host "== Preflight: runtime env schema =="
$runtimeEnvPath = Join-Path $RepoRoot "runtime.env.json"
$runtimeEnv = Get-Content $runtimeEnvPath -Raw | ConvertFrom-Json
if ($null -eq $runtimeEnv.system_name -or [string]::IsNullOrWhiteSpace([string]$runtimeEnv.system_name)) {
    throw "runtime.env.json: system_name mancante"
}
if ($runtimeEnv.deterministic_mode -ne $true) {
    throw "runtime.env.json: deterministic_mode deve essere true"
}
if ($null -eq $runtimeEnv.allowed_capabilities -or $runtimeEnv.allowed_capabilities.Count -lt 1) {
    throw "runtime.env.json: allowed_capabilities vuoto"
}

Write-Host "== Preflight: smoke flow CLI -> IDE -> resume -> rollback =="
$tmpRoot = Join-Path $RepoRoot ".ci_tmp"
$tmpData = Join-Path $RepoRoot ".ci_runtime_data"
New-Item -ItemType Directory -Force -Path $tmpRoot | Out-Null
New-Item -ItemType Directory -Force -Path $tmpData | Out-Null

$ciEnvPath = Join-Path $tmpRoot "runtime.env.json"
@"
{
  "system_name": "MindOs-ci",
  "deterministic_mode": true,
  "data_dir": "$($tmpData -replace '\\', '\\\\')",
  "default_project": "ci-project",
  "allowed_capabilities": ["document.generate", "presentation.generate", "program.echo.execute", "program.python.execute"],
  "bootstrap_plugins": ["document.plugin.v1", "presentation.plugin.v1"],
  "program_registry_file": "",
  "policy": {
    "blocked_actions": [],
    "confirm_required_actions": ["delete", "destructive_write"],
    "confirm_required_capabilities": [],
    "acl": {
      "users": {
        "default": {
          "allowed_capabilities": ["document.generate", "presentation.generate", "program.echo.execute", "program.python.execute"],
          "denied_capabilities": [],
          "allowed_surfaces": ["cli", "ide", "desktop"]
        }
      }
    },
    "plugin_trust": {
      "require_integrity": true,
      "require_signature": true,
      "trusted_signers": ["core-team"],
      "revoked_signers": [],
      "signer_keys": {
        "core-team": "core-team-dev-key"
      }
    },
    "program_sandbox": {
      "max_timeout_sec": 30,
      "allow_real_execution": true,
      "allowed_capabilities_for_real_execution": ["program.echo.execute"]
    }
  }
}
"@ | Set-Content -Path $ciEnvPath -Encoding UTF8

$cliOutRaw = & $PythonExe -m surfaces.cli.main --env $ciEnvPath --user ci-user run --project ci-project --title "CI-Doc" --body "Pipeline check"
if ($LASTEXITCODE -ne 0) {
    throw "CLI run fallita"
}
$cliOut = $cliOutRaw | ConvertFrom-Json
if ($cliOut.status -ne "completed") {
    throw "CLI run status inatteso: $($cliOut.status)"
}
if (-not $cliOut.output.artifact) {
    throw "CLI run: artifact mancante"
}

$ideOutRaw = & $PythonExe -m surfaces.ide.view --env $ciEnvPath --user ci-user --project ci-project
if ($LASTEXITCODE -ne 0) {
    throw "IDE retrieval fallita"
}
$ideOut = $ideOutRaw | ConvertFrom-Json
if ($ideOut.latest_run.status -ne "completed") {
    throw "IDE latest_run status inatteso: $($ideOut.latest_run.status)"
}

$presentationRaw = & $PythonExe -m surfaces.cli.main --env $ciEnvPath --user ci-user run-presentation --project ci-project --title "CI Deck" --from-latest
if ($LASTEXITCODE -ne 0) {
    throw "Presentazione da latest context fallita"
}
$presentationOut = $presentationRaw | ConvertFrom-Json
if ($presentationOut.status -ne "completed") {
    throw "Presentazione status inatteso: $($presentationOut.status)"
}
if ($presentationOut.output.artifact_type -ne "presentation_outline") {
    throw "Presentazione artifact_type inatteso: $($presentationOut.output.artifact_type)"
}

$promoteRaw = & $PythonExe -m surfaces.cli.main --env $ciEnvPath --user ci-user promote --project ci-project --pattern-id ci_doc_pattern --title "CI-Doc" --body "Pipeline check"
if ($LASTEXITCODE -ne 0) {
    throw "Promote pattern fallito"
}
$promoteOut = $promoteRaw | ConvertFrom-Json
if ($promoteOut.status -ne "saved") {
    throw "Promote status inatteso: $($promoteOut.status)"
}

$createScheduleRaw = & $PythonExe -m surfaces.cli.main --env $ciEnvPath --user ci-user create-schedule --schedule-id ci_schedule_1 --pattern-id ci_doc_pattern --interval-seconds 60 --surface cli --start-at-epoch 100 --max-runs 1
if ($LASTEXITCODE -ne 0) {
    throw "Create schedule fallito"
}
$createScheduleOut = $createScheduleRaw | ConvertFrom-Json
if ($createScheduleOut.schedule_id -ne "ci_schedule_1") {
    throw "Create schedule output inatteso"
}

$tickRaw = & $PythonExe -m surfaces.cli.main --env $ciEnvPath --user ci-user tick-scheduler --now-epoch 100
if ($LASTEXITCODE -ne 0) {
    throw "Tick scheduler fallito"
}
$tickOut = $tickRaw | ConvertFrom-Json
if ($tickOut.executed.Count -lt 1) {
    throw "Tick scheduler: nessuna esecuzione effettuata"
}

$desktopRaw = & $PythonExe -m surfaces.desktop.shell --env $ciEnvPath --user ci-user --project ci-project --document-title "Desktop Doc" --document-body "Desktop body" --presentation-title "Desktop Deck"
if ($LASTEXITCODE -ne 0) {
    throw "Desktop unified workflow fallito"
}
$desktopOut = $desktopRaw | ConvertFrom-Json
if ($desktopOut.status -ne "completed") {
    throw "Desktop workflow status inatteso: $($desktopOut.status)"
}

$resumeRaw = & $PythonExe -m surfaces.cli.main --env $ciEnvPath resume --run-id $cliOut.run_id
if ($LASTEXITCODE -ne 0) {
    throw "Resume fallito"
}
$resumeOut = $resumeRaw | ConvertFrom-Json
if ($resumeOut.status -ne "completed") {
    throw "Resume status inatteso: $($resumeOut.status)"
}

$rollbackRaw = & $PythonExe -m surfaces.cli.main --env $ciEnvPath rollback --run-id $cliOut.run_id
if ($LASTEXITCODE -ne 0) {
    throw "Rollback fallito"
}
$rollbackOut = $rollbackRaw | ConvertFrom-Json
if ($rollbackOut.status -ne "rolled_back") {
    throw "Rollback status inatteso: $($rollbackOut.status)"
}

Write-Host "== Preflight: plugin manager cycle =="
$catalogRaw = & $PythonExe -m surfaces.cli.main --env $ciEnvPath plugin-catalog
if ($LASTEXITCODE -ne 0) {
    throw "Plugin catalog fallito"
}
$catalogOut = $catalogRaw | ConvertFrom-Json
if ($catalogOut.catalog.Count -lt 1) {
    throw "Plugin catalog vuoto"
}

$installRaw = & $PythonExe -m surfaces.cli.main --env $ciEnvPath plugin-install --plugin-id presentation.plugin.v1
if ($LASTEXITCODE -ne 0) {
    throw "Plugin install fallito"
}
$installOut = $installRaw | ConvertFrom-Json
if ($installOut.status -ne "installed") {
    throw "Plugin install status inatteso: $($installOut.status)"
}

$listRaw = & $PythonExe -m surfaces.cli.main --env $ciEnvPath plugin-list
if ($LASTEXITCODE -ne 0) {
    throw "Plugin list fallito"
}
$listOut = $listRaw | ConvertFrom-Json
if ($null -eq $listOut."document.plugin.v1") {
    throw "Plugin list: document.plugin.v1 mancante"
}

$upgradeRaw = & $PythonExe -m surfaces.cli.main --env $ciEnvPath plugin-upgrade --plugin-id document.plugin.v1
if ($LASTEXITCODE -ne 0) {
    throw "Plugin upgrade fallito"
}
$upgradeOut = $upgradeRaw | ConvertFrom-Json
if ($upgradeOut.status -ne "installed") {
    throw "Plugin upgrade status inatteso: $($upgradeOut.status)"
}

$removeRaw = & $PythonExe -m surfaces.cli.main --env $ciEnvPath plugin-remove --plugin-id presentation.plugin.v1
if ($LASTEXITCODE -ne 0) {
    throw "Plugin remove fallito"
}
$removeOut = $removeRaw | ConvertFrom-Json
if ($removeOut.status -notin @("removed", "not_installed")) {
    throw "Plugin remove status inatteso: $($removeOut.status)"
}

Write-Host "== Preflight: cross-platform program plugin cycle =="
$programCatalogRaw = & $PythonExe -m surfaces.cli.main --env $ciEnvPath program-catalog
if ($LASTEXITCODE -ne 0) {
    throw "Program catalog fallito"
}
$programCatalogOut = $programCatalogRaw | ConvertFrom-Json
if ($programCatalogOut.program_catalog.Count -lt 1) {
    throw "Program catalog vuoto"
}

$programInstallRaw = & $PythonExe -m surfaces.cli.main --env $ciEnvPath program-install --program-id shell.echo.program.v1
if ($LASTEXITCODE -ne 0) {
    throw "Program install fallito"
}
$programInstallOut = $programInstallRaw | ConvertFrom-Json
if ($programInstallOut.status -ne "installed") {
    throw "Program install status inatteso: $($programInstallOut.status)"
}

$programRunRaw = & $PythonExe -m surfaces.cli.main --env $ciEnvPath --user ci-user program-run --project ci-project --capability program.echo.execute --arg "CI Program" --dry-run
if ($LASTEXITCODE -ne 0) {
    throw "Program run fallito"
}
$programRunOut = $programRunRaw | ConvertFrom-Json
if ($programRunOut.status -ne "completed") {
    throw "Program run status inatteso: $($programRunOut.status)"
}

Write-Host "== Preflight completata con successo =="
