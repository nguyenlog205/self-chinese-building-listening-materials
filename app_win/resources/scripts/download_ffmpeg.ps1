# Windows-only. Downloads a static ffmpeg build and extracts ffmpeg.exe into
# resources/ffmpeg/ so the installer can bundle it -- end users never need to
# install ffmpeg themselves. Not committed to git; fetched at build time.
$ErrorActionPreference = "Stop"

$ResourcesDir = Split-Path -Parent $PSScriptRoot
$FfmpegDir = Join-Path $ResourcesDir "ffmpeg"
$ExePath = Join-Path $FfmpegDir "ffmpeg.exe"

if (Test-Path $ExePath) {
    Write-Host "ffmpeg.exe already present, skipping download."
    exit 0
}

New-Item -ItemType Directory -Force -Path $FfmpegDir | Out-Null

$ZipUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
$ZipPath = Join-Path $env:TEMP "ffmpeg-essentials.zip"
$ExtractDir = Join-Path $env:TEMP "ffmpeg-extract"

Write-Host "Downloading ffmpeg from $ZipUrl ..."
Invoke-WebRequest -Uri $ZipUrl -OutFile $ZipPath

if (Test-Path $ExtractDir) { Remove-Item -Recurse -Force $ExtractDir }
Expand-Archive -Path $ZipPath -DestinationPath $ExtractDir

$FoundExe = Get-ChildItem -Path $ExtractDir -Recurse -Filter "ffmpeg.exe" | Select-Object -First 1
if (-not $FoundExe) {
    throw "ffmpeg.exe not found inside downloaded archive"
}
Copy-Item $FoundExe.FullName -Destination $ExePath -Force

Write-Host "ffmpeg.exe ready at $ExePath"
