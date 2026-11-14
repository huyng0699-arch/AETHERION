$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Install first using scripts\setup_windows.ps1" }
Set-Location $root

# First-run default is loopback only. Respect explicit user/environment URL.
if (-not $env:AETHERION_API_URL) {
    $env:AETHERION_API_URL = "http://127.0.0.1:8765"
}
if (-not $env:AETHERION_AUTOSTART_LOCAL_SERVER) {
    $env:AETHERION_AUTOSTART_LOCAL_SERVER = "1"
}
Write-Host "AETHERION Desktop | Server: $env:AETHERION_API_URL"
Write-Host "An unavailable default loopback Server will start inside the app (if installed)."
Write-Host "The independent SIMULATED crew SQLite will seed asynchronously at startup."
& $python -m aetherion_desktop
exit $LASTEXITCODE
