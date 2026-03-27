Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($env:SKIP_PDF_BUNDLE -eq "1") {
  Write-Host "[pdf-bundle] SKIP_PDF_BUNDLE=1 -> skip local PDF build"
  exit 0
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Set-Location $repoRoot

$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) {
  $cmd = @("py", "-3", (Join-Path $repoRoot "scripts\pdf_package\build_pdf_bundle.py"))
} else {
  $python = Get-Command python -ErrorAction SilentlyContinue
  if (-not $python) {
    throw "[pdf-bundle] python runtime not found (py/python)."
  }
  $cmd = @("python", (Join-Path $repoRoot "scripts\pdf_package\build_pdf_bundle.py"))
}

Write-Host "[pdf-bundle] building local bundle before push..."
& $cmd[0] $cmd[1..($cmd.Length-1)]
if ($LASTEXITCODE -ne 0) {
  throw "[pdf-bundle] build failed"
}

Write-Host "[pdf-bundle] done"
