$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Install first using scripts\setup_windows.ps1" }
Set-Location $root
# Validate settings before launching an HTTP listener.
& $python -m aetherion_server.runtime_config --check
if ($LASTEXITCODE -ne 0) { throw "AETHERION configuration rejected. Server was not started." }

$listenAddress = if ($env:AETHERION_HOST) { $env:AETHERION_HOST.Trim() } else { "127.0.0.1" }
$listenPort = if ($env:AETHERION_PORT) { $env:AETHERION_PORT.Trim() } else { "8765" }
& $python -m uvicorn aetherion_server.main:app --host $listenAddress --port $listenPort
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
