Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ToolsDir = Join-Path $RepoRoot "tools"
$PythonDir = Join-Path $ToolsDir "python"
$PythonExe = Join-Path $PythonDir "python.exe"
$ZipPath = Join-Path $ToolsDir "python-3.12.8-embed-amd64.zip"
$PthPath = Join-Path $PythonDir "python312._pth"

if (Test-Path $PythonExe) {
    Write-Host "Python locale gia' disponibile: $PythonExe"
    exit 0
}

New-Item -ItemType Directory -Force -Path $ToolsDir | Out-Null

if (-not (Test-Path $ZipPath)) {
    $url = "https://www.python.org/ftp/python/3.12.8/python-3.12.8-embed-amd64.zip"
    Write-Host "Download Python embedded da $url"
    Invoke-WebRequest -Uri $url -OutFile $ZipPath
}

Write-Host "Estrazione Python embedded..."
Expand-Archive -Path $ZipPath -DestinationPath $PythonDir -Force

if (-not (Test-Path $PthPath)) {
    throw "File _pth non trovato: $PthPath"
}

$lines = Get-Content $PthPath
if ($lines -notcontains "E:\OS") {
    $lines += "E:\OS"
}
$lines = $lines | ForEach-Object {
    if ($_ -eq "#import site") { "import site" } else { $_ }
}
Set-Content -Path $PthPath -Value $lines -Encoding UTF8

if (-not (Test-Path $PythonExe)) {
    throw "Installazione Python fallita: $PythonExe non trovato"
}

Write-Host "Python installato: $PythonExe"
