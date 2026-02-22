<#
.SYNOPSIS
    Run the LangPedia test suite.
.DESCRIPTION
    Activates the virtual environment (if present) and runs pytest.
    Designed to be called locally or from CI pipelines.
#>

param(
  [switch]$Verbose,
  [string]$Filter
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent

# Activate venv if it exists
$VenvActivate = Join-Path $ProjectRoot ".venv-langpedia\Scripts\Activate.ps1"
if (Test-Path $VenvActivate) {
  . $VenvActivate
}

# Build pytest arguments
$PytestArgs = @("-v", "--tb=short")
if ($Verbose) {
  $PytestArgs += "-s"
}
if ($Filter) {
  $PytestArgs += "-k"
  $PytestArgs += $Filter
}

Write-Host ""
Write-Host "Running LangPedia tests..." -ForegroundColor Cyan
Write-Host "pytest $($PytestArgs -join ' ')" -ForegroundColor DarkGray
Write-Host ""

Push-Location $ProjectRoot
pytest @PytestArgs
$code = $LASTEXITCODE
Pop-Location
exit $code
