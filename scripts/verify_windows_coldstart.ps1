# Run on an interactive Windows desktop after scripts/build_windows.ps1.
# This verifies the packaged artifact, not source imports or an offscreen Qt mock.
[CmdletBinding()]
param(
    [string]$PackageDirectory = "dist/AETHERION-Desktop",
    [string]$ExpectedSha256,
    [int]$TimeoutSeconds = 20,
    [string]$ReportPath = "build/windows/coldstart-evidence.json"
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
if ($env:OS -ne "Windows_NT") { throw "Real Windows desktop required; refusing non-Windows smoke." }
if ($TimeoutSeconds -lt 5 -or $TimeoutSeconds -gt 120) { throw "TimeoutSeconds must be 5..120." }
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$package = (Resolve-Path -LiteralPath (Join-Path $root $PackageDirectory)).Path
$exe = Join-Path $package "AETHERION-Desktop.exe"
$manifestPath = Join-Path $package "build-evidence.json"
if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) { throw "Packaged EXE missing: $exe" }
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) { throw "Build evidence missing: $manifestPath" }
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifest.kind -ne "WINDOWS_PYINSTALLER_ONEDIR_CANDIDATE") { throw "Unexpected build evidence kind." }
$hash = (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()
if ($hash -ne ([string]$manifest.executable_sha256).ToLowerInvariant()) {
    throw "EXE hash differs from build-evidence.json; refusing launch."
}
if ($ExpectedSha256 -and $hash -ne $ExpectedSha256.ToLowerInvariant()) {
    throw "EXE hash differs from independently supplied expected SHA-256."
}
# Use a new isolated folder to catch accidental reliance on repository source files.
$temporary = Join-Path ([IO.Path]::GetTempPath()) ("aetherion-coldstart-" + [guid]::NewGuid().ToString("N"))
$process = $null
$observed = $false
$reason = "WINDOW_NOT_OBSERVED"
$started = (Get-Date).ToUniversalTime().ToString("o")
try {
    New-Item -ItemType Directory -Path $temporary -Force | Out-Null
    Copy-Item -LiteralPath $package -Destination (Join-Path $temporary "package") -Recurse -Force
    $isolated = Join-Path $temporary "package"
    $isolatedExe = Join-Path $isolated "AETHERION-Desktop.exe"
    if ((Get-FileHash -LiteralPath $isolatedExe -Algorithm SHA256).Hash.ToLowerInvariant() -ne $hash) {
        throw "Isolated EXE copy checksum mismatch."
    }
    $process = Start-Process -FilePath $isolatedExe -WorkingDirectory $isolated -PassThru
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 400
        $process.Refresh()
        if ($process.HasExited) {
            $reason = "PROCESS_EXITED_EARLY"
            break
        }
        if ($process.MainWindowHandle -ne [IntPtr]::Zero) {
            $observed = $true
            $reason = "WINDOW_HANDLE_OBSERVED"
            break
        }
    }
} finally {
    if ($null -ne $process) {
        try {
            $process.Refresh()
            if (-not $process.HasExited) {
                $process.CloseMainWindow() | Out-Null
                if (-not $process.WaitForExit(3000)) {
                    Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
                    $process.WaitForExit(3000) | Out-Null
                }
            }
        } catch { Write-Warning ("Process cleanup: " + $_.Exception.Message) }
    }
    try { Remove-Item -LiteralPath $temporary -Recurse -Force -ErrorAction Stop }
    catch { Write-Warning ("Temporary folder cleanup blocked; remove manually: " + $temporary) }
}
$report = [ordered]@{
    kind = "NATIVE_WINDOWS_COLDSTART_CHECK"
    tested_utc = $started
    source_commit = [string]$manifest.source_commit
    exe_sha256 = $hash
    exe_bytes = (Get-Item -LiteralPath $exe).Length
    copied_to_isolated_temp = $true
    window_handle_observed = $observed
    result = $reason
    manual_vi_en_navigation = "NOT_TESTED"
    clean_machine_dependencies = "NOT_TESTED"
    independent_review = "PENDING"
}
$destination = [IO.Path]::GetFullPath((Join-Path $root $ReportPath))
New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
$report | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $destination -Encoding UTF8
Write-Host ("Cold-start result: " + $reason + "; SHA256: " + $hash)
Write-Host ("Evidence: " + $destination)
if (-not $observed) { throw "No interactive native window observed. Cold-start FAILED." }
Write-Host "A window handle is not proof of UI interaction, a clean machine, clinical validity, or release approval."
