# Build EMP-PackageX3 Onedir.
# Requires uv (on PATH or as `python -m uv`); PyInstaller comes from the dev group.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

if (Get-Command uv -ErrorAction SilentlyContinue) {
    & uv sync --extra dev
    if ($LASTEXITCODE -ne 0) { Write-Error "uv sync fehlgeschlagen (exit $LASTEXITCODE)"; exit 1 }
    & uv run pyinstaller packaging/emp_packagex3.spec --noconfirm
    if ($LASTEXITCODE -ne 0) { Write-Error "pyinstaller fehlgeschlagen (exit $LASTEXITCODE)"; exit 1 }
} elseif (Test-Path "$PSScriptRoot\..\.venv\Scripts\pyinstaller.exe") {
    $pyinstaller = "$PSScriptRoot\..\.venv\Scripts\pyinstaller.exe"
    & $pyinstaller packaging/emp_packagex3.spec --noconfirm
    if ($LASTEXITCODE -ne 0) { Write-Error "pyinstaller fehlgeschlagen (exit $LASTEXITCODE)"; exit 1 }
} else {
    & python -m PyInstaller packaging/emp_packagex3.spec --noconfirm
    if ($LASTEXITCODE -ne 0) { Write-Error "pyinstaller fehlgeschlagen (exit $LASTEXITCODE)"; exit 1 }
}

Write-Host "Output: dist\EMP-PackageX3\"
