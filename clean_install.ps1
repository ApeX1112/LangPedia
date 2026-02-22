<#
.SYNOPSIS
    Clean install script for LangPedia development environment.
.DESCRIPTION
    Removes any existing venv, creates a fresh Python virtual environment,
    installs all dependencies (including dev tools), sets up pre-commit hooks,
    and installs Studio (Next.js) dependencies.
#>

param(
    [switch]$SkipStudio,
    [switch]$SkipPreCommit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot

Write-Host ""
Write-Host "  LangPedia - Clean Install" -ForegroundColor Cyan
Write-Host ""

# Ensure all commands run from the project root, regardless of where the script was invoked
Push-Location $ProjectRoot
try {

    # ── Step 1: Clean existing venv ──────────────────────────────────────────
    $VenvPath = Join-Path $ProjectRoot ".venv-langpedia"
    if (Test-Path $VenvPath) {
        Write-Host "[1/5] Removing existing .venv-langpedia..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force $VenvPath
    }
    else {
        Write-Host "[1/5] No existing .venv-langpedia found, starting fresh." -ForegroundColor Green
    }

    # ── Step 2: Create virtual environment ───────────────────────────────────
    Write-Host "[2/5] Creating Python virtual environment..." -ForegroundColor Cyan
    python -m venv $VenvPath
    if (-not $?) { throw "Failed to create virtual environment." }

    # Activate venv
    $ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
    . $ActivateScript

    # ── Step 3: Install Python dependencies ──────────────────────────────────
    Write-Host "[3/5] Upgrading pip and installing project..." -ForegroundColor Cyan
    python -m pip install --upgrade pip --quiet
    python -m pip install -e ".[dev]" --quiet
    if (-not $?) { throw "Failed to install Python dependencies." }
    Write-Host "       Python dependencies installed." -ForegroundColor Green

    # ── Step 4: Pre-commit hooks ─────────────────────────────────────────────
    if (-not $SkipPreCommit) {
        Write-Host "[4/5] Installing pre-commit hooks..." -ForegroundColor Cyan
        pre-commit install
        if (-not $?) { throw "Failed to install pre-commit hooks." }
        Write-Host "       Pre-commit hooks installed." -ForegroundColor Green
    }
    else {
        Write-Host "[4/5] Skipping pre-commit hooks (--SkipPreCommit)." -ForegroundColor Yellow
    }

    # ── Step 5: Studio (Next.js) dependencies ────────────────────────────────
    if (-not $SkipStudio) {
        $StudioPath = Join-Path $ProjectRoot "studio"
        if (Test-Path (Join-Path $StudioPath "package.json")) {
            Write-Host "[5/5] Installing Studio (Next.js) dependencies..." -ForegroundColor Cyan
            Push-Location $StudioPath
            npm.cmd install --silent
            Pop-Location
            Write-Host "       Studio dependencies installed." -ForegroundColor Green
        }
        else {
            Write-Host "[5/5] Studio package.json not found, skipping." -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "[5/5] Skipping Studio install (--SkipStudio)." -ForegroundColor Yellow
    }

    # ── Done ─────────────────────────────────────────────────────────────────
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  Installation Complete!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "To activate the environment:" -ForegroundColor White
    Write-Host "  .\.venv-langpedia\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Quick commands:" -ForegroundColor White
    Write-Host "  pytest                        # Run tests" -ForegroundColor Yellow
    Write-Host "  pre-commit run --all-files    # Run linters" -ForegroundColor Yellow
    Write-Host "  uvicorn backend.app.api.main:app --reload  # Start backend" -ForegroundColor Yellow
    Write-Host "  cd studio && npm run dev      # Start Studio UI" -ForegroundColor Yellow
    Write-Host ""

}
finally {
    Pop-Location
}
