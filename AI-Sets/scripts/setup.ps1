<#
.SYNOPSIS
  One-command setup for the AI-Sets tutorial on Windows.

.WHAT IT DOES
  1. Checks your Python version.
  2. Creates a virtual environment in .venv (if missing).
  3. Activates it for this script's session.
  4. Installs the project in editable mode (or falls back to requirements.txt).
  5. Copies .env.example to .env if you don't have one yet.
  6. Generates the sample data (data\*.json, data\orders.db, data\app.log).

.USAGE
  Open PowerShell in the repo root and run:
    .\scripts\setup.ps1

  If PowerShell blocks the script, run this once (safe, session-only):
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#>

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

Write-Host "== AI-Sets setup ==" -ForegroundColor Cyan
Write-Host "Project root: $root"

# 1. Python check
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "ERROR: 'python' was not found on PATH. Install Python 3.11+ from https://www.python.org/downloads/ and re-run this script." -ForegroundColor Red
    exit 1
}
$versionOutput = & python --version
Write-Host "Found: $versionOutput"

# 2. Create venv if missing
$venvPath = Join-Path $root ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment at .venv ..."
    & python -m venv $venvPath
} else {
    Write-Host "Virtual environment already exists at .venv"
}

# 3. Activate venv for this session
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
if (-not (Test-Path $activateScript)) {
    Write-Host "ERROR: could not find $activateScript. The venv may be corrupt - delete .venv and re-run." -ForegroundColor Red
    exit 1
}
. $activateScript
Write-Host "Virtual environment activated."

# 4. Install dependencies
Write-Host "Installing dependencies (this can take a minute the first time) ..."
& python -m pip install --upgrade pip --quiet
Push-Location $root
try {
    & python -m pip install -e ".[dev]"
} catch {
    Write-Host "Editable install failed, falling back to requirements.txt ..." -ForegroundColor Yellow
    & python -m pip install -r requirements.txt
}
Pop-Location

# 5. .env file
$envFile = Join-Path $root ".env"
$envExample = Join-Path $root ".env.example"
if (-not (Test-Path $envFile)) {
    Copy-Item $envExample $envFile
    Write-Host "Created .env from .env.example (LLM_BACKEND=fake by default - no API key needed)."
} else {
    Write-Host ".env already exists, leaving it alone."
}

# 6. Generate sample data
Write-Host "Generating sample data ..."
Push-Location $root
& python data\seed_data.py
Pop-Location

Write-Host ""
Write-Host "== Setup complete ==" -ForegroundColor Green
Write-Host "Next: run '.\scripts\verify-env.ps1' to confirm everything is wired up."
