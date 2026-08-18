# Build the EAC backend sidecar and place it where Tauri expects it.
#
# Usage (from repo root):
#   .\scripts\build_sidecar.ps1
#
# Prerequisites:
#   cd backend
#   python -m venv .venv
#   .venv\Scripts\pip install -e ".[dev]"
#   .venv\Scripts\pip install pyinstaller

$ErrorActionPreference = "Stop"
$RepoRoot  = Split-Path $PSScriptRoot -Parent
$BackendDir = Join-Path $RepoRoot "backend"
$OutDir     = Join-Path $RepoRoot "frontend\src-tauri\binaries"

$Python = Join-Path $BackendDir ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    Write-Error "Backend venv not found at $Python`nRun: cd backend; python -m venv .venv; pip install -e ."
}

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

Push-Location $BackendDir
try {
    & $Python -m PyInstaller eac-backend.spec --noconfirm --clean
    if ($LASTEXITCODE -ne 0) {
        Write-Error "PyInstaller failed with exit code $LASTEXITCODE"
    }
} finally {
    Pop-Location
}

# Tauri externalBin appends the target triple to the binary name at build time.
# At runtime the installed binary is plain "eac-backend.exe"; the triple is only
# needed during the Tauri build so it can locate the file in src-tauri/binaries/.
$Src  = Join-Path $BackendDir "dist\eac-backend.exe"
$Dest = Join-Path $OutDir "eac-backend-x86_64-pc-windows-msvc.exe"

if (-not (Test-Path $Src)) {
    Write-Error "Expected output not found: $Src"
}

Copy-Item -Force $Src $Dest
Write-Host "Sidecar built -> $Dest"
Write-Host ""

# Build the full Tauri installer, injecting externalBin via the release overlay
# so the path check only runs when the binary is actually present.
$FrontendDir = Join-Path $RepoRoot "frontend"
Push-Location $FrontendDir
try {
    Write-Host "Building Tauri installer…"
    & pnpm tauri build --config src-tauri/tauri.release.conf.json
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Tauri build failed with exit code $LASTEXITCODE"
    }
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "Installer: frontend\src-tauri\target\release\bundle\nsis\Enterprise AI Companion_0.1.0_x64-setup.exe"
