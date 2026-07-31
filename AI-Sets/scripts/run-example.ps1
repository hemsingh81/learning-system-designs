<#
.SYNOPSIS
  Runs one example script by name, with the venv active and PYTHONPATH set.

.USAGE
  .\scripts\run-example.ps1 01_skill_hello
  .\scripts\run-example.ps1 08_agent_first_loop.py    (extension is optional)
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$Name
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

if (-not $Name.EndsWith(".py")) { $Name = "$Name.py" }
$scriptPath = Join-Path $root "examples\$Name"

if (-not (Test-Path $scriptPath)) {
    Write-Host "ERROR: could not find $scriptPath" -ForegroundColor Red
    Write-Host "Available examples:"
    Get-ChildItem (Join-Path $root "examples") -Filter "*.py" | ForEach-Object { Write-Host "  $($_.Name)" }
    exit 1
}

Push-Location $root
try {
    $env:PYTHONPATH = Join-Path $root "src"
    & python $scriptPath
} finally {
    Pop-Location
}
