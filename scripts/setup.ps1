<#
.SYNOPSIS
    One-shot setup for Enterprise AI Companion on a new machine.

.DESCRIPTION
    1. Creates backend/.env from backend/.env.example (if .env does not already exist).
    2. Installs Python backend dependencies via uv sync.
    3. Ensures the editable install .pth file is present in the venv so the
       package is importable without PYTHONPATH (required for Tauri dev-mode).
    4. Installs frontend Node dependencies via pnpm.

.EXAMPLE
    # From the repo root:
    .\scripts\setup.ps1
#>

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "`n=== Enterprise AI Companion — Setup ===" -ForegroundColor Cyan

# ── Step 1: .env ──────────────────────────────────────────────────────────────

$envFile     = Join-Path $Root "backend\.env"
$envExample  = Join-Path $Root "backend\.env.example"

if (-not (Test-Path $envFile)) {
    Copy-Item $envExample $envFile
    Write-Host "Created backend/.env from .env.example" -ForegroundColor Green
    Write-Host "  -> Open backend/.env and set EAC_APIM_ENDPOINT (required)." -ForegroundColor Yellow
} else {
    Write-Host "backend/.env already exists — skipping copy." -ForegroundColor DarkGray
}

# ── Step 2: Python deps (uv sync) ─────────────────────────────────────────────

Push-Location (Join-Path $Root "backend")

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "uv is not installed. Install it from https://docs.astral.sh/uv/ and re-run."
}

Write-Host "`nInstalling Python dependencies (uv sync)..." -ForegroundColor Cyan
uv sync
if ($LASTEXITCODE -ne 0) { Write-Error "uv sync failed." }

# ── Step 3: Editable install .pth ─────────────────────────────────────────────
#
# Tauri dev-mode runs: .venv\Scripts\python.exe -m enterprise_ai_companion
# Without PYTHONPATH the package is only importable when the editable-install
# .pth file exists in site-packages.  uv sync creates it on a clean machine,
# but can fail to recreate it on a machine with a corrupted prior venv.
# This step ensures the file is always present.

$sitePackages = & ".venv\Scripts\python.exe" -c "import site; print(site.getsitepackages()[0])"
$pthFile      = Join-Path $sitePackages "__editable__.enterprise-ai-companion-0.1.0.pth"
$srcPath      = Join-Path $Root "backend\src"

if (-not (Test-Path $pthFile)) {
    Write-Host "Editable install .pth missing — creating it..." -ForegroundColor Yellow
    Set-Content -Path $pthFile -Value $srcPath -Encoding UTF8 -NoNewline
    Write-Host "  Created: $pthFile" -ForegroundColor Green
} else {
    $existing = (Get-Content $pthFile -Raw).Trim()
    if ($existing -ne $srcPath) {
        Write-Host "Editable install .pth points to wrong path — updating..." -ForegroundColor Yellow
        Set-Content -Path $pthFile -Value $srcPath -Encoding UTF8 -NoNewline
        Write-Host "  Updated: $pthFile" -ForegroundColor Green
    } else {
        Write-Host "Editable install .pth OK." -ForegroundColor DarkGray
    }
}

# Verify import works.
$ok = & ".venv\Scripts\python.exe" -c "from enterprise_ai_companion.api.app import app; print('ok')" 2>&1
if ($ok -notmatch "ok") {
    Write-Warning "Backend import check failed: $ok"
    Write-Warning "You may need to run: cd backend && uv pip install -e ."
} else {
    Write-Host "Backend import check: OK" -ForegroundColor Green
}

Pop-Location

# ── Step 4: Frontend deps (pnpm) ──────────────────────────────────────────────

Push-Location (Join-Path $Root "frontend")

if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
    Write-Error "pnpm is not installed. Install it with: npm install -g pnpm"
}

Write-Host "`nInstalling frontend dependencies (pnpm install)..." -ForegroundColor Cyan
pnpm install
if ($LASTEXITCODE -ne 0) { Write-Error "pnpm install failed." }

Pop-Location

# ── Done ──────────────────────────────────────────────────────────────────────

Write-Host @"

=== Setup complete ===

Next steps:
  1. Open backend/.env and set EAC_APIM_ENDPOINT to the APIM gateway URL.
  2. Launch the app:  cd frontend && pnpm tauri dev
  3. Go to Settings -> Security and paste your APIM subscription key.
     The key is stored in Windows Credential Manager — it never touches the repo.

"@ -ForegroundColor Green
