# Q-0430: real Windows-only offline medical-library acceptance probe.
# Requires a prepared native PySide6 developer install and a genuine populated
# SQLite CliFF library; no mock NASA data or automatically fabricated evidence.
# This script cannot certify medical correctness, image licensing or network isolation.
[CmdletBinding()]
param(
    [string]$LibraryPath = "",
    [string]$PythonPath = "",
    [string]$EvidenceDir = "",
    [int]$TimeoutSeconds = 35,
    [switch]$KeepWindowOpen
)

$ErrorActionPreference = "Stop"
if ($env:OS -ne "Windows_NT") {
    throw "Q-0430 is a real Windows GUI acceptance check; refusing headless/non-Windows PASS."
}
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $PythonPath) {
    $PythonPath = Join-Path $root ".venv\Scripts\python.exe"
}
if (-not $LibraryPath) {
    $LibraryPath = Join-Path $root "knowledge\nasa\cliff_119_2023\AETHERION_NASA_CLIFF_119.sqlite"
}
if (-not $EvidenceDir) {
    $EvidenceDir = Join-Path $root "docs\qa\windows-cliff-evidence"
}
if (-not (Test-Path -PathType Leaf $PythonPath)) {
    throw "Native developer Python missing: $PythonPath (run scripts\setup_windows.ps1 first)"
}
if (-not (Test-Path -PathType Leaf $LibraryPath)) {
    throw "Real offline NASA CliFF SQLite file absent: $LibraryPath"
}
$LibraryPath = (Resolve-Path $LibraryPath).Path
$EvidenceDir = [System.IO.Path]::GetFullPath($EvidenceDir)
New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null
$stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$reportFile = Join-Path $EvidenceDir "q0430-$stamp.json"
$screenshotFile = Join-Path $EvidenceDir "q0430-$stamp.png"

$report = [ordered]@{
    quest = "Q-0430"
    timestamp_utc = (Get-Date).ToUniversalTime().ToString("o")
    status = "NOT_TESTED"
    library_path = $LibraryPath
    library_sha256 = (Get-FileHash -Algorithm SHA256 -Path $LibraryPath).Hash.ToLowerInvariant()
    observed = @()
    screenshot = $null
    screenshot_sha256 = $null
    git_commit = $null
    limitations = @(
        "GUI accessibility depends on real Qt Windows accessibility exposure.",
        "Loopback API is intentionally unavailable; this is not proof that all external network traffic is blocked.",
        "No clinical accuracy or image-license review is performed by this probe.",
        "Independent review is still required before status DONE."
    )
    error = $null
}
try {
    $gitHead = (& git -C $root rev-parse HEAD 2>$null)
    if ($LASTEXITCODE -eq 0) { $report.git_commit = ($gitHead | Select-Object -First 1).Trim() }
} catch { }

# A read-only SQLite query verifies that the selected file is an actual
# imported CliFF library, not an empty placeholder or another app's database.
$pythonAudit = @'
import hashlib, json, pathlib, sqlite3, sys
path = pathlib.Path(sys.argv[1]).resolve()
db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
try:
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA query_only=ON")
    integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
    kind = db.execute("SELECT value FROM library_info WHERE key='library_kind'").fetchone()
    articles = db.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    complete = db.execute("SELECT COUNT(*) FROM articles WHERE completeness_state='COMPLETE'").fetchone()[0]
    approved = db.execute("SELECT COUNT(*) FROM media WHERE usage_review='APPROVED'").fetchone()[0]
    examples = [dict(row) for row in db.execute(
        "SELECT article_id,display_title,completeness_state FROM articles ORDER BY slot LIMIT 3"
    )]
    print(json.dumps({"integrity": integrity, "kind": kind[0] if kind else None,
        "articles": articles, "complete_articles": complete,
        "rights_approved_image_rows": approved, "sample_articles": examples}))
finally:
    db.close()
'@
$oldApi = $env:AETHERION_API_URL
$oldCliff = $env:AETHERION_CLIFF_LIBRARY_PATH
$process = $null
try {
    $auditRaw = & $PythonPath -c $pythonAudit $LibraryPath
    if ($LASTEXITCODE -ne 0) { throw "Python failed to open the selected library read-only" }
    $audit = $auditRaw | Out-String | ConvertFrom-Json
    $report.sqlite_audit = $audit
    if ($audit.integrity -ne "ok" -or $audit.kind -ne "NASA_CLIFF_119_MEDICAL_REFERENCE") {
        throw "SQLite file fails integrity or authentic-library identity checks"
    }
    if ($audit.articles -lt 1) {
        throw "Library contains zero imported articles. Empty-state UI can be checked separately, but Q-0430 rich-content PASS is impossible."
    }
    $report.observed += "SQLite read-only integrity/identity passed, imported article count $($audit.articles)."

    # The app must open and provide local library content with its API unreachable.
    # Do NOT infer that internet access was blocked; inspect actual traffic separately.
    $env:AETHERION_CLIFF_LIBRARY_PATH = $LibraryPath
    $env:AETHERION_API_URL = "http://127.0.0.1:1"
    $arguments = '-c "from aetherion_desktop.main import main; raise SystemExit(main())"'
    $process = Start-Process -FilePath $PythonPath -ArgumentList $arguments -WorkingDirectory $root -PassThru

    Add-Type -AssemblyName UIAutomationClient
    Add-Type -AssemblyName UIAutomationTypes
    $desktop = [System.Windows.Automation.AutomationElement]::RootElement
    $processFilter = [System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::ProcessIdProperty, [int]$process.Id
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $window = $null
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 350
        $process.Refresh()
        if ($process.HasExited) { throw "Native desktop process exited before its window was ready" }
        $windows = $desktop.FindAll([System.Windows.Automation.TreeScope]::Children, $processFilter)
        foreach ($candidate in $windows) {
            if ($candidate.Current.Name -match "AETHERION") {
                $window = $candidate
                break
            }
        }
        if ($null -ne $window) { break }
    }
    if ($null -eq $window) { throw "No AETHERION native top-level window appeared via Windows UI Automation" }
    $report.observed += "Native Qt window opened under process $($process.Id): $($window.Current.Name)."

    function Find-UiName($parent, [string]$name) {
        $matcher = [System.Windows.Automation.PropertyCondition]::new(
            [System.Windows.Automation.AutomationElement]::NameProperty, $name
        )
        return $parent.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $matcher)
    }
    function Invoke-UiButton($element) {
        if ($null -eq $element) { throw "Expected native UIA button is missing" }
        $pattern = $element.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
        if ($null -eq $pattern) { throw "Native UIA element cannot be invoked" }
        $pattern.Invoke()
    }
    # Verify the real button; a mere screenshot of the portal is not an article-read PASS.
    $libraryButton = Find-UiName $window "Medical Library"
    Invoke-UiButton $libraryButton
    Start-Sleep -Milliseconds 750
    $readerButton = Find-UiName $window "Read imported article from local library"
    if ($null -eq $readerButton) {
        $readerButton = Find-UiName $window "Read selected article offline"
    }
    if ($null -eq $readerButton) {
        throw "Native library page did not reveal the reader selection control"
    }
    $report.observed += "Medical Library button opened a native article-index view."

    $listItemType = [System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
        [System.Windows.Automation.ControlType]::ListItem
    )
    $items = $window.FindAll([System.Windows.Automation.TreeScope]::Descendants, $listItemType)
    if ($items.Count -lt 1) { throw "No accessible imported article list item was visible" }
    $selectionPattern = $items.Item(0).GetCurrentPattern(
        [System.Windows.Automation.SelectionItemPattern]::Pattern
    )
    $selectionPattern.Select()
    Invoke-UiButton $readerButton
    Start-Sleep -Milliseconds 650
    if ($null -eq (Find-UiName $window "Back to library")) {
        throw "Selection did not open the native offline article reader"
    }
    $report.observed += "Selected a real imported article, opened reader, and detected Back to library."

    # Capture only the actual AETHERION window rectangle, not the full personal desktop.
    Add-Type -AssemblyName System.Drawing
    $bounds = $window.Current.BoundingRectangle
    $width = [int][Math]::Ceiling($bounds.Width)
    $height = [int][Math]::Ceiling($bounds.Height)
    if ($width -lt 200 -or $height -lt 200) { throw "Qt native window has invalid screenshot bounds" }
    $bitmap = New-Object System.Drawing.Bitmap($width, $height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    try {
        $graphics.CopyFromScreen([int]$bounds.Left, [int]$bounds.Top, 0, 0, $bitmap.Size)
        $bitmap.Save($screenshotFile, [System.Drawing.Imaging.ImageFormat]::Png)
    } finally {
        $graphics.Dispose()
        $bitmap.Dispose()
    }
    $report.screenshot = $screenshotFile
    $report.screenshot_sha256 = (Get-FileHash -Algorithm SHA256 -Path $screenshotFile).Hash.ToLowerInvariant()
    $report.observed += "Captured actual native-window pixels; SHA-256 recorded."
    # This indicates a functional PROBE, not a medical or Q-0430 release approval.
    $report.status = "WINDOWS_NATIVE_PROBE_PASSED_REVIEW_PENDING"
} catch {
    $report.status = "FAILED_OR_INCOMPLETE"
    $report.error = $_.Exception.Message
} finally {
    $env:AETHERION_API_URL = $oldApi
    $env:AETHERION_CLIFF_LIBRARY_PATH = $oldCliff
    if ($null -ne $process -and -not $KeepWindowOpen) {
        try { if (-not $process.HasExited) { Stop-Process -Id $process.Id -Force } } catch { }
    }
    $report | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -Path $reportFile
    Write-Host "Evidence report: $reportFile"
    if ($null -ne $report.screenshot) { Write-Host "Actual window screenshot: $($report.screenshot)" }
    Write-Host "Q-0430 probe status: $($report.status)"
}
if ($report.status -ne "WINDOWS_NATIVE_PROBE_PASSED_REVIEW_PENDING") {
    throw "Q-0430 probe did not pass: $($report.error)"
}
Write-Host "Native probe finished; independent reviewer must still inspect real screenshot, image/citation behavior, original sources and offline network trace."
