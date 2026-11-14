$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $root
Write-Host "AETHERION | Creating Python 3.11 virtual environment..."
py -3.11 -m venv .venv
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Virtual environment python not found: $python" }
& $python -m pip install --upgrade pip
& $python -m pip install -e (Join-Path $root "apps\server") -e (Join-Path $root "apps\desktop")
& $python -c "import aetherion_server, aetherion_desktop; print('AETHERION packages imported successfully.')"
Write-Host "Setup complete. Run scripts\start_server.ps1 in one PowerShell, then scripts\start_desktop.ps1 in another."
