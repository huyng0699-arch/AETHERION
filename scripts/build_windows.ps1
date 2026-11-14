# AETHERION Desktop: real native Windows one-folder EXE build (not a clinical release).
# Creates a separate offline scientific library only from existing, attributed JSON.
# No patient data, local server database, credentials, cloud keys or model weights bundled.
[CmdletBinding()]
param(
    [string]$OutputDirectory = "dist",
    [switch]$SkipSmoke,
    [switch]$RequireLibrary
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $root
if ($env:OS -ne "Windows_NT") {
    throw "Native Windows EXE must be compiled on Windows, not Linux."
}

$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Missing Python venv; run scripts/setup_windows.ps1 first."
}
& $python -c "import PySide6, aetherion_desktop, aetherion_desktop.main; print('Native Desktop imports OK')"
if ($LASTEXITCODE -ne 0) { throw "Desktop import failed; aborting before package." }
& $python -c "import PyInstaller; print('PyInstaller', PyInstaller.__version__)"
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller missing. Install: .venv\Scripts\python.exe -m pip install pyinstaller"
}

$sourceEntry = Join-Path $root "apps\desktop\src\aetherion_desktop\main.py"
if (-not (Test-Path -LiteralPath $sourceEntry)) {
    throw "Missing actual native desktop entrypoint."
}
$launchDir = Join-Path $root "build\windows"
New-Item -ItemType Directory -Path $launchDir -Force | Out-Null
$launcher = Join-Path $launchDir "launch_aetherion_desktop.py"
$entrySource = @'
from aetherion_desktop.main import main

if __name__ == "__main__":
    raise SystemExit(main())
'@
Set-Content -LiteralPath $launcher -Encoding UTF8 -Value $entrySource

$dist = [IO.Path]::GetFullPath((Join-Path $root $OutputDirectory))
$work = Join-Path $root "build\windows\pyinstaller-work"
$spec = Join-Path $root "build\windows\pyinstaller-spec"
New-Item -ItemType Directory -Force -Path $dist, $work, $spec | Out-Null

# Build the optional *reference-only* database from verified record fields and
# on-disk media hashes, without inventing missing CliFF records.
$staging = Join-Path $root "build\windows\scientific"
New-Item -ItemType Directory -Force -Path $staging | Out-Null
$library = Join-Path $staging "AETHERION_NASA_CLIFF_119.sqlite"
$manifest = Join-Path $staging "medical-manifest.json"
if (Test-Path -LiteralPath $library) { Remove-Item -LiteralPath $library -Force }
if (Test-Path -LiteralPath $manifest) { Remove-Item -LiteralPath $manifest -Force }
& $python (Join-Path $root "scripts\build_offline_medical_library.py") --db $library --report $manifest
$libraryExit = $LASTEXITCODE
if ($libraryExit -ne 0) {
    if ($RequireLibrary) {
        throw "Offline CliFF library build failed; -RequireLibrary blocks incomplete packages."
    }
    Write-Warning "No usable CliFF SQLite generated; native EXE will report MISSING rather than invent articles."
}

$hazards = Join-Path $root "knowledge\nasa\hazards"
if (-not (Test-Path -LiteralPath (Join-Path $hazards "space_radiation.json"))) {
    throw "Local NASA hazards missing: scientific Explore view cannot be bundled."
}
$anatomy = Join-Path $root "knowledge\anatomy"
$arguments = @(
    "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir", "--windowed",
    "--name", "AETHERION-Desktop",
    "--distpath", $dist, "--workpath", $work, "--specpath", $spec,
    "--paths", (Join-Path $root "apps\desktop\src"),
    "--collect-data", "aetherion_desktop",
    "--collect-submodules", "aetherion_desktop",
    "--add-data", ("{0};{1}" -f $hazards, "knowledge/nasa/hazards")
)
if (Test-Path -LiteralPath (Join-Path $anatomy "approved_models.json")) {
    $arguments += @("--add-data", ("{0};{1}" -f $anatomy, "knowledge/anatomy"))
}
$arguments += $launcher
& $python @arguments
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed. No EXE can be claimed." }
$app = Join-Path $dist "AETHERION-Desktop"
$exe = Join-Path $app "AETHERION-Desktop.exe"
if (-not (Test-Path -LiteralPath $exe)) {
    throw "PyInstaller reported success but Windows EXE is absent."
}

# Sidecar is independent of PyInstaller's _internal/ folder. Both the index and
# the reader use the same read-only path in the packaged application.
$scienceOut = Join-Path $app "data\knowledge\nasa\cliff_119_2023"
New-Item -ItemType Directory -Force -Path $scienceOut | Out-Null
if ($libraryExit -eq 0 -and (Test-Path -LiteralPath $library) -and
    (Test-Path -LiteralPath $manifest)) {
    $info = Get-Content -LiteralPath $manifest -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($RequireLibrary -and $info.import_status -ne "COMPLETE") {
        throw ("CliFF library is only {0}/119; -RequireLibrary requires all 119 valid records." -f $info.imported_articles)
    }
    $actualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $library).Hash.ToLowerInvariant()
    if ($actualHash -ne [string]$info.sqlite_sha256) {
        throw "Scientific SQLite checksum mismatch; refused to bundle."
    }
    Copy-Item -LiteralPath $library -Destination (Join-Path $scienceOut (Split-Path -Leaf $library)) -Force
    Copy-Item -LiteralPath $manifest -Destination (Join-Path $scienceOut "medical-manifest.json") -Force
    Write-Host ("REAL CliFF reference records: {0}/119 ({1})" -f
        $info.imported_articles, $info.import_status)
} else {
    Write-Warning "Medical library absent; app remains usable for other native features."
}

$exeSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $exe).Hash.ToLowerInvariant()
$exeBytes = (Get-Item -LiteralPath $exe).Length
$gitSha = "UNKNOWN"
if (Test-Path -LiteralPath (Join-Path $root ".git")) {
    try {
        $prevErr = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        $rawSha = (& git -C $root rev-parse HEAD 2>$null | Out-String).Trim()
        $ErrorActionPreference = $prevErr
        if ($LASTEXITCODE -eq 0 -and $rawSha) { $gitSha = $rawSha }
    } catch { }
}
$evidence = [ordered]@{
    product = "AETHERION Desktop"
    kind = "WINDOWS_PYINSTALLER_ONEDIR_CANDIDATE"
    source_commit = $gitSha
    executable = "AETHERION-Desktop.exe"
    executable_sha256 = $exeSha
    executable_bytes = $exeBytes
    medical_library_bundled = ($libraryExit -eq 0)
    native_gui_smoke = "NOT_RUN"
    review = "PENDING"
    medical_device_certified = $false
}
$evidencePath = Join-Path $app "build-evidence.json"
$evidence | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $evidencePath -Encoding UTF8
Write-Host "EXE: $exe"
Write-Host "SHA256: $exeSha"
Write-Host "Build evidence: $evidencePath"

if (-not $SkipSmoke) {
    # A real Windows GUI handle, not an import test or a source-code assertion.
    $p = Start-Process -FilePath $exe -WorkingDirectory $app -PassThru
    try {
        $visible = $false
        for ($i = 0; $i -lt 45; $i++) {
            Start-Sleep -Milliseconds 650
            $p.Refresh()
            if ($p.HasExited) { break }
            if ($p.MainWindowHandle -ne [IntPtr]::Zero) { $visible = $true; break }
        }
        if (-not $visible) {
            $evidence.native_gui_smoke = "FAILED_OR_NO_INTERACTIVE_DESKTOP"
            $evidence | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $evidencePath -Encoding UTF8
            throw "Native window did not appear. EXE exists but has NOT passed Windows GUI boot."
        }
        $evidence.native_gui_smoke = "WINDOW_HANDLE_OBSERVED"
        # Capture ONLY the AETHERION window rectangle, not the entire desktop.
        # The PNG remains a local build artifact; it is not uploaded to a service.
        try {
            Add-Type -AssemblyName System.Drawing
            $win32 = @'
using System;
using System.Runtime.InteropServices;
public static class AetherionWindowRect {
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left, Top, Right, Bottom; }
    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT rectangle);
}
'@
            Add-Type -TypeDefinition $win32 -ErrorAction SilentlyContinue
            $rect = New-Object AetherionWindowRect+RECT
            if ([AetherionWindowRect]::GetWindowRect($p.MainWindowHandle, [ref]$rect)) {
                $w = [Math]::Min(3840, [Math]::Max(1, $rect.Right - $rect.Left))
                $h = [Math]::Min(2160, [Math]::Max(1, $rect.Bottom - $rect.Top))
                if ($w -gt 200 -and $h -gt 150) {
                    $bitmap = New-Object System.Drawing.Bitmap($w, $h)
                    $graphic = [System.Drawing.Graphics]::FromImage($bitmap)
                    try {
                        $graphic.CopyFromScreen($rect.Left, $rect.Top, 0, 0, $bitmap.Size)
                        $picture = Join-Path $app "windows-native-portal.png"
                        $bitmap.Save($picture, [System.Drawing.Imaging.ImageFormat]::Png)
                        $evidence.screenshot = "windows-native-portal.png"
                        Write-Host "Actual Windows screenshot (local only): $picture"
                    } finally {
                        $graphic.Dispose()
                        $bitmap.Dispose()
                    }
                }
            }
        } catch {
            Write-Warning ("Window was observed, but screenshot could not be captured: {0}" -f $_.Exception.Message)
        }
        $evidence | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $evidencePath -Encoding UTF8
        Write-Host "Windows GUI handle observed; inspect five Portal cards, language switch, offline state, then close the app."
        Write-Host "Window-handle evidence does NOT certify routes, medical content, or independent review."
    } finally {
        if ($null -ne $p) {
            $p.Refresh()
            if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
        }
    }
}
Write-Host "Desktop and server remain independently launched. Never distribute without checking licenses and provenance."
