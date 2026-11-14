$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $root

# Prefer Python 3.11, but do not assume the Windows 'py' launcher is installed.
# Validate the interpreter by executing it: Windows Store aliases may exist without Python.
$candidates = @(
    @{ Command = "py"; Prefix = @("-3.11") },
    @{ Command = "python3.11"; Prefix = @() },
    @{ Command = "py"; Prefix = @("-3.12") },
    @{ Command = "python3.12"; Prefix = @() },
    @{ Command = "py"; Prefix = @("-3.13") },
    @{ Command = "python3.13"; Prefix = @() },
    @{ Command = "python"; Prefix = @() },
    @{ Command = "python3"; Prefix = @() }
)
$selected = $null
foreach ($candidate in $candidates) {
    if (-not (Get-Command $candidate.Command -ErrorAction SilentlyContinue)) { continue }
    try {
        $probeArgs = @($candidate.Prefix) + @("-c", "import sys; assert sys.version_info[:2] >= (3, 11) and sys.version_info[:2] < (3, 14); print(sys.executable)")
        $probeOutput = & $candidate.Command @probeArgs 2>$null
        if ($LASTEXITCODE -eq 0 -and $probeOutput) {
            $selected = $candidate
            Write-Host "AETHERION | Selected Python: $($probeOutput | Select-Object -Last 1)"
            break
        }
    } catch {
        # Try the next candidate rather than failing on a missing launcher/version.
    }
}
if ($null -eq $selected) {
    throw "No usable Python 3.11-3.13 interpreter found. Install Python from python.org, enable PATH, then rerun setup_windows.ps1."
}

Write-Host "AETHERION | Creating virtual environment..."
$venvArgs = @($selected.Prefix) + @("-m", "venv", ".venv")
& $selected.Command @venvArgs
if ($LASTEXITCODE -ne 0) { throw "Failed to create virtual environment." }

$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Virtual environment python not found: $python" }
& $python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Failed to upgrade pip." }
& $python -m pip install -e (Join-Path $root "apps\server") -e (Join-Path $root "apps\desktop")
if ($LASTEXITCODE -ne 0) { throw "Failed to install AETHERION packages." }
& $python -c "import aetherion_server, aetherion_desktop; print('AETHERION packages imported successfully.')"
if ($LASTEXITCODE -ne 0) { throw "Installed package import verification failed." }
Write-Host "Setup complete. Run scripts\start_server.ps1 in one PowerShell, then scripts\start_desktop.ps1 in another."
