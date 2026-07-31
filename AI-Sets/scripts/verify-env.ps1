<#
.SYNOPSIS
  Checks that your environment is ready to run the AI-Sets tutorial.
  This is the "Requirement 9 checklist" turned into a script - run it any
  time something feels broken, and again right after setup.
#>

$ErrorActionPreference = "Continue"
$root = Split-Path -Parent $PSScriptRoot
$fail = $false

function Check-Item {
    param([string]$Name, [bool]$Ok, [string]$FixHint)
    if ($Ok) {
        Write-Host "[OK]   $Name" -ForegroundColor Green
    } else {
        Write-Host "[FAIL] $Name" -ForegroundColor Red
        Write-Host "       Fix: $FixHint" -ForegroundColor Yellow
        $script:fail = $true
    }
}

Write-Host "== AI-Sets environment check ==" -ForegroundColor Cyan

# Python present
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
Check-Item "Python is on PATH" ($null -ne $pythonCmd) "Install Python 3.11+ and re-open PowerShell."

# venv present
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
Check-Item "Virtual environment exists (.venv)" (Test-Path $venvPython) "Run .\scripts\setup.ps1"

# Activate if we can
$activateScript = Join-Path $root ".venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) { . $activateScript }

# Packages importable
if (Test-Path $venvPython) {
    $importCheck = & $venvPython -c "import anthropic, pydantic, fastapi, httpx, rich, dotenv; print('OK')" 2>&1
    Check-Item "Core packages import correctly" ($importCheck -match "OK") "Run .\scripts\setup.ps1 again - a package install may have failed. Output: $importCheck"
}

# .env exists
$envFile = Join-Path $root ".env"
Check-Item ".env file exists" (Test-Path $envFile) "Copy .env.example to .env: Copy-Item .env.example .env"

# Sample data exists
$ticketsFile = Join-Path $root "data\tickets.json"
$logFile = Join-Path $root "data\app.log"
$dbFile = Join-Path $root "data\orders.db"
Check-Item "Sample data: data\tickets.json" (Test-Path $ticketsFile) "Run: python data\seed_data.py"
Check-Item "Sample data: data\app.log" (Test-Path $logFile) "Run: python data\seed_data.py"
Check-Item "Sample data: data\orders.db" (Test-Path $dbFile) "Run: python data\seed_data.py"

# LLM_BACKEND reported
if (Test-Path $envFile) {
    $backendLine = Get-Content $envFile | Where-Object { $_ -match "^LLM_BACKEND=" }
    Write-Host "Info: $backendLine (fake = offline/free, claude = real API calls)" -ForegroundColor Cyan
}

Write-Host ""
if ($fail) {
    Write-Host "== One or more checks FAILED. Fix the items above and re-run this script. ==" -ForegroundColor Red
    exit 1
} else {
    Write-Host "== All checks passed. You are ready. Try: .\scripts\run-example.ps1 01_skill_hello ==" -ForegroundColor Green
    exit 0
}
