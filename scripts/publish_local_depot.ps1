# Publish Onedir build into local/network App-Depot (EMP-PackageX3 updates).
# Not for Empirum PackageStore (Configurator$) - use UI deploy for that.
param(
    [string]$DepotPath = "$env:USERPROFILE\Documents\EMP-PackageX3-Depot",
    [string]$DistDir = ".\dist\EMP-PackageX3",
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

if (-not (Test-Path $DistDir)) {
    Write-Error "Build fehlt: $DistDir - zuerst .\scripts\build_onedir.ps1"
    exit 1
}

if (-not $Version) {
    $raw = & python -c "import sys; sys.path.insert(0,'src'); from emp_packagex3 import __version__; print(__version__)"
    if ($LASTEXITCODE -ne 0 -or -not $raw -or -not "$raw".Trim()) {
        Write-Error "Versionsermittlung fehlgeschlagen (python/Quellcode erreichbar?)"
        exit 1
    }
    $Version = "$raw".Trim()
}

New-Item -ItemType Directory -Force -Path $DepotPath | Out-Null
$zipName = "EMP-PackageX3-$Version.zip"
$zipPath = Join-Path $DepotPath $zipName

if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path (Join-Path $DistDir "*") -DestinationPath $zipPath -Force

$manifestSrc = ".\packaging\VERSION.json"
$manifest = Get-Content $manifestSrc -Raw | ConvertFrom-Json
$manifest.version = $Version
$manifest.download_url = $zipPath
$manifest.notes = "Lokales Depot-Publish $Version"
$manifestJson = $manifest | ConvertTo-Json

# Set-Content -Encoding utf8 writes a BOM under Windows PowerShell 5.1 which the
# app's update check cannot parse - write the manifest explicitly BOM-free.
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$manifestPath = Join-Path (Resolve-Path $DepotPath).Path "VERSION.json"
[System.IO.File]::WriteAllText($manifestPath, $manifestJson + "`n", $utf8NoBom)

Write-Host "Depot: $DepotPath"
Write-Host "ZIP:   $zipPath"
Write-Host "Manifest aktualisiert. In der App: Datei -> Auf Update pruefen..."
