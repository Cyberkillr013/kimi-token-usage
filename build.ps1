$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $Python)) {
    python -m venv (Join-Path $ProjectRoot ".venv")
}

& $Python -m pip install --disable-pip-version-check -r (Join-Path $ProjectRoot "requirements-build.txt")
if ($LASTEXITCODE -ne 0) { throw "Failed to install build dependencies." }

$Icon = Join-Path $ProjectRoot "assets\token_widget.ico"
$CatAssets = Join-Path $ProjectRoot "assets\cats"
$BubbleAssets = Join-Path $ProjectRoot "assets\bubbles"
$VersionInfo = Join-Path $ProjectRoot "installer\version_info.txt"
$Source = Join-Path $ProjectRoot "src\token_widget.py"

& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --name "KimiTokenUsage" `
    --icon $Icon `
    --add-data "$Icon;." `
    --add-data "$CatAssets;cats" `
    --add-data "$BubbleAssets;bubbles" `
    --version-file $VersionInfo `
    --distpath (Join-Path $ProjectRoot "dist") `
    --workpath (Join-Path $ProjectRoot "build") `
    --specpath (Join-Path $ProjectRoot "build") `
    $Source
if ($LASTEXITCODE -ne 0) { throw "Failed to build KimiTokenUsage.exe." }

$ISCC = @(
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
    (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
    (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe")
) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

if (-not $ISCC) {
    $Command = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($Command) { $ISCC = $Command.Source }
}

if (-not $ISCC) {
    throw "Inno Setup 6 is required. Install it with: winget install --id JRSoftware.InnoSetup --exact"
}

& $ISCC (Join-Path $ProjectRoot "installer\installer.iss")
if ($LASTEXITCODE -ne 0) { throw "Failed to build the installer." }

Write-Output "Installer created at $ProjectRoot\release\KimiTokenUsage-Setup.exe"
