# AETHERION native Windows cold-start evidence collector (Q-0011).
# Run separately on real Windows 10 AND Windows 11; no result is pre-filled.
# Does not launch a server, access accounts, health data, or transmit evidence.
[CmdletBinding()]
param(
    [string]$ExePath = "dist\AETHERION-Desktop\AETHERION-Desktop.exe",
    [string]$EvidenceDirectory = "build\windows\coldstart-evidence",
    [ValidateRange(5, 120)][int]$TimeoutSeconds = 25,
    [switch]$KeepRunning
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $root
if ($env:OS -ne "Windows_NT") {
    throw "This probe requires a real interactive Windows 10/11 session."
}

$build = [Environment]::OSVersion.Version.Build
$osVersion = [Environment]::OSVersion.Version.ToString()
$label = if ($build -ge 22000) {
    "Windows11"
} elseif ($build -ge 10240) {
    "Windows10"
} else {
    throw ("Unsupported Windows build {0}; run on Windows 10 or 11." -f $build)
}
$exe = [IO.Path]::GetFullPath((Join-Path $root $ExePath))
if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) {
    throw ("Real PyInstaller EXE missing: {0}. Build first with scripts\build_windows.ps1." -f $exe)
}
if ([IO.Path]::GetExtension($exe).ToLowerInvariant() -ne ".exe") {
    throw "Cold-start target must be an actual .exe file."
}

$evidenceRoot = [IO.Path]::GetFullPath((Join-Path $root $EvidenceDirectory))
$packageFolder = [IO.Path]::GetDirectoryName($exe).TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
if ($evidenceRoot.StartsWith($packageFolder, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Evidence must be saved OUTSIDE the packaged EXE folder."
}
New-Item -ItemType Directory -Path $evidenceRoot -Force | Out-Null

$sourceSha = "UNKNOWN"
try {
    $sourceSha = (& git -C $root rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0) { $sourceSha = "UNKNOWN" }
} catch {
    $sourceSha = "UNKNOWN"
}

$timestamp = [DateTimeOffset]::UtcNow.ToString("yyyyMMddTHHmmssZ")
$evidencePath = Join-Path $evidenceRoot ("coldstart-{0}-{1}.json" -f $label, $timestamp)
$info = [ordered]@{
    schema_version = "1.0"
    product = "AETHERION Native Desktop"
    os_target = $label
    os_version = $osVersion
    os_build = $build
    architecture = [Environment]::GetEnvironmentVariable("PROCESSOR_ARCHITECTURE")
    source_commit = $sourceSha
    executable = $exe
    executable_size_bytes = (Get-Item -LiteralPath $exe).Length
    executable_sha256 = (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()
    started_at_utc = [DateTimeOffset]::UtcNow.ToString("o")
    observed_pid = $null
    observed_main_window_handle = $false
    elapsed_ms = $null
    status = "NOT_RUN"
    review = "PENDING"
    native_ui_verified = $false
    other_os_verified = $false
    medical_data_read = $false
    errors = @()
}

$process = $null
$watch = [System.Diagnostics.Stopwatch]::StartNew()
try {
    $info.status = "STARTING"
    $process = Start-Process -FilePath $exe -WorkingDirectory ([IO.Path]::GetDirectoryName($exe)) -PassThru
    $info.observed_pid = $process.Id
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        Start-Sleep -Milliseconds 350
        $process.Refresh()
        if ($process.HasExited) {
            $info.errors += ("Process exited before a native window appeared; exit code {0}." -f $process.ExitCode)
            break
        }
        if ($process.MainWindowHandle -ne [IntPtr]::Zero) {
            $info.observed_main_window_handle = $true
            break
        }
    }
    $watch.Stop()
    $info.elapsed_ms = $watch.ElapsedMilliseconds
    if ($info.observed_main_window_handle) {
        $info.status = "WINDOW_HANDLE_OBSERVED_NOT_UI_ACCEPTED"
        Write-Host "Native window handle observed on $label, build $build."
        Write-Host "Manually inspect Home, bilingual UI and navigation; this probe does NOT approve them."
    } else {
        $info.status = "FAILED_OR_NO_INTERACTIVE_WINDOW"
        if (@($info.errors).Count -eq 0) {
            $info.errors += "No main window handle within timeout."
        }
    }
} catch {
    $watch.Stop()
    $info.elapsed_ms = $watch.ElapsedMilliseconds
    $info.status = "FAILED_START"
    $info.errors += $_.Exception.Message
} finally {
    $info.finished_at_utc = [DateTimeOffset]::UtcNow.ToString("o")
    # Do not force-kill a GUI that might contain unsaved local changes.
    if (-not $KeepRunning -and $null -ne $process) {
        try {
            $process.Refresh()
            if (-not $process.HasExited) {
                $closed = $process.CloseMainWindow()
                if ($closed) {
                    if (-not $process.WaitForExit(4000)) {
                        $info.errors += "Application remains open; close it manually."
                    }
                } else {
                    $info.errors += "No safe close window; close the app manually."
                }
            }
        } catch {
            $info.errors += ("Automatic graceful close unavailable: {0}" -f $_.Exception.Message)
        }
    }
    $info | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $evidencePath -Encoding UTF8
    Write-Host "Evidence written locally: $evidencePath"
}
if (-not $info.observed_main_window_handle) {
    throw "Native cold-start probe failed. Inspect the evidence JSON. Do not mark Q-0011 DONE."
}
Write-Host "Required: run this SAME script again on the other Windows OS and obtain independent review."
