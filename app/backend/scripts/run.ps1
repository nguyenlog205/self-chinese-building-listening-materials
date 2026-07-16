# Creates the backend venv on first run, then launches the API server.
# Prints "READY <port>" to stdout once listening -- Electron's main process
# watches for this line.
$ErrorActionPreference = "Stop"

$BackendDir = Split-Path -Parent $PSScriptRoot
$VenvDir = Join-Path $BackendDir ".venv"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"

if (-not (Test-Path $VenvDir)) {
    Write-Host "Setting up backend virtual environment (first run only)..."
    python -m venv $VenvDir
    & $PythonExe -m pip install --upgrade pip
    & $PythonExe -m pip install -e $BackendDir
}

& $PythonExe -m listening_backend.main
