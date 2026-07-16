# Windows-only. Creates a build venv, installs the backend + PyInstaller,
# and freezes it into backend/dist/listening-backend/listening-backend.exe.
#
# This is the same recipe the GitHub Actions workflow
# (.github/workflows/build-app-win.yml) runs on a windows-latest runner --
# use this script for local iteration if you have a Windows machine handy.
$ErrorActionPreference = "Stop"

$BackendDir = Split-Path -Parent $PSScriptRoot
$VenvDir = Join-Path $BackendDir ".venv"
$PythonExe = Join-Path $VenvDir "Scripts\python.exe"

if (-not (Test-Path $VenvDir)) {
    python -m venv $VenvDir
}

& $PythonExe -m pip install --upgrade pip
& $PythonExe -m pip install -e "$BackendDir[build]"

Push-Location $BackendDir
try {
    & $PythonExe -m PyInstaller pyinstaller/listening_backend.spec --noconfirm
} finally {
    Pop-Location
}

Write-Host "Built: $BackendDir\dist\listening-backend\listening-backend.exe"
