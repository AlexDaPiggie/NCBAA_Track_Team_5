param([string]$OutputDirectory = 'dist')
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$taskPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) {
    throw 'Create the environment first: python -m venv .venv'
}
Push-Location frontend
try {
    & npm.cmd run build
    if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed' }
} finally { Pop-Location }
if (-not (Test-Path -LiteralPath 'backend/data/trained_forecast.json')) {
if (-not (Test-Path -LiteralPath 'backend/data/trained_forecast.json')) {
    & $taskPython -m backend.training
    if ($LASTEXITCODE -ne 0) { throw 'Training failed' }
}
}
& $taskPython -m PyInstaller --noconfirm --windowed --distpath $OutputDirectory --name ApronStaffingLab --add-data 'frontend/dist;frontend/dist' --add-data 'backend/data/trained_forecast.json;backend/data' --collect-all webview --hidden-import uvicorn.logging --hidden-import uvicorn.loops.auto --hidden-import uvicorn.protocols.http.auto --hidden-import uvicorn.protocols.websockets.auto --hidden-import uvicorn.lifespan.on desktop.py
if ($LASTEXITCODE -ne 0) { throw 'Desktop packaging failed' }
Write-Host "Ready: $OutputDirectory\ApronStaffingLab\ApronStaffingLab.exe"
