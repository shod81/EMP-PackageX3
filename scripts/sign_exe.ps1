# Optional code-signing helper (requires signtool + cert in store)
param(
  [Parameter(Mandatory = $true)][string]$ExePath,
  [string]$TimestampUrl = "http://timestamp.digicert.com"
)
$ErrorActionPreference = "Stop"
if (-not (Get-Command signtool -ErrorAction SilentlyContinue)) {
  Write-Error "signtool.exe not found. Install Windows SDK / Signing Tools."
  exit 1
}
if (-not (Test-Path $ExePath)) {
  Write-Error "EXE nicht gefunden: $ExePath"
  exit 1
}
signtool sign /fd SHA256 /tr $TimestampUrl /td SHA256 /a $ExePath
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
signtool verify /pa $ExePath
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Signed: $ExePath"
