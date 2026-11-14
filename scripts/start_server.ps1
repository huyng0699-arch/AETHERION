$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Install first using scripts\setup_windows.ps1" }
Set-Location $root
& $python -m uvicorn aetherion_server.main:app --host 127.0.0.1 --port 8765
