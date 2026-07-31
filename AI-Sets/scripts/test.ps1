<#
.SYNOPSIS
  Runs the fast test suite (unit + integration) with coverage.
  Live tests (real API) are excluded by default - see docs\05-testing-ai-code.md.

.USAGE
  .\scripts\test.ps1               # everything except live
  .\scripts\test.ps1 -Live         # only the live suite (needs ANTHROPIC_API_KEY)
  .\scripts\test.ps1 -Path tests\unit\test_llm_fake.py
#>

param(
    [switch]$Live,
    [string]$Path = "tests"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

$activateScript = Join-Path $root ".venv\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    . $activateScript
} else {
    Write-Host "No .venv found - run .\scripts\setup.ps1 first." -ForegroundColor Red
    exit 1
}

Push-Location $root
try {
    $env:PYTHONPATH = Join-Path $root "src"
    if ($Live) {
        & python -m pytest $Path -m "live" -v
    } else {
        & python -m pytest $Path --cov=src\aisets --cov-report=term-missing -v
    }
} finally {
    Pop-Location
}
