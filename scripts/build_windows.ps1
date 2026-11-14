# Native Windows desktop build (developer candidate; not a signed or certified release).
# Run from an authenticated checkout on Windows with Python 3.11+ and installed dependencies.
[CmdletBinding()]
param(
    [string]$OutputDirectory = "dist",
    [switch]$SkipSmoke
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $root
if ($env:OS -ne "Windows_NT") { throw "Windows is required for native EXE packaging." }
$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Missing .venv Python. First run scripts/setup_windows.ps1."
}
& $python -c "import PySide6, aetherion_desktop, aetherion_desktop.main; print('Desktop imports OK')"
if ($LASTEXITCODE -ne 0) { throw "Desktop import failed; packaging aborted." }
& $python -c "import PyInstaller; print(PyInstaller.__version__)"
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller is not installed in .venv. Run: .venv\Scripts\python.exe -m pip install pyinstaller"
}
# Only the desktop client is packaged. Never embed the HTTP server, SQLite
# user records, credentials, downloaded model weights, or external medical assets.
$moduleEntry = Join-Path $root "apps\desktop\src\aetherion_desktop\main.py"
if (-not (Test-Path $moduleEntry)) { throw "Desktop entrypoint missing: $moduleEntry" }
# Package a module-importing launcher: main.py uses package-relative imports and
# cannot safely be executed as a bare script.
$launcher = Join-Path $root "build\aetherion_desktop_launcher.py"
New-Item -ItemType Directory -Force -Path (Split-Path $launcher) | Out-Null
Set-Content -Path $launcher -Encoding UTF8 -Value "from aetherion_desktop.main import main\nif __name__ == \"__main__\":\n    raise SystemExit(main())\n"
$entry = $launcher
$out = [IO.Path]::GetFullPath((Join-Path $root $OutputDirectory))
$work = Join-Path $root "build\pyinstaller-work"
$spec = Join-Path $root "build\pyinstaller-spec"
New-Item -ItemType Directory -Force -Path $out, $work, $spec | Out-Null
& $python -m PyInstaller --noconfirm --clean --onedir --windowed --name AETHERION-Desktop --distpath $out --workpath $work --specpath $spec --paths (Join-Path $root "apps\desktop\src") --collect-data aetherion_desktop --collect-submodules aetherion_desktop $entry
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed." }
$exe = Join-Path $out "AETHERION-Desktop\AETHERION-Desktop.exe"
if (-not (Test-Path $exe)) { throw "Build returned success but executable is missing: $exe" }
$hash = (Get-FileHash -Algorithm SHA256 -Path $exe).Hash
$size = (Get-Item $exe).Length
Write-Host "Candidate EXE: $exe"
Write-Host "EXE SHA256: $hash"
Write-Host "EXE bytes: $size"
Write-Host "NOTE: executable existence does not prove GUI launch, licensing, or offline readiness."
if (-not $SkipSmoke) {
    Write-Host "Opening candidate for manual cold-start verification; no automatic GUI PASS."
    Start-Process -FilePath $exe -WorkingDirectory (Split-Path $exe) | Out-Null
    Write-Host "Manually verify Portal 5 cards, VI/EN switching, top menu, offline behavior and exit."
}
Write-Host "Review included dependencies/licenses and bundled bytes before distribution."
