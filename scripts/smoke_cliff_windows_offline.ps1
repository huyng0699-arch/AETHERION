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
$auditScript = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), "aetherion_cliff_audit_$PID.py")
try {
    Set-Content -Encoding UTF8 -Path $auditScript -Value $pythonAudit
    $auditRaw = & $PythonPath $auditScript $LibraryPath
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
    $process = Start-Process -FilePath $PythonPath -ArgumentList $arguments -WorkingDirectory $root -PassThru -WindowStyle Hidden

    Add-Type -AssemblyName UIAutomationClient
    Add-Type -AssemblyName UIAutomationTypes
    $desktop = [System.Windows.Automation.AutomationElement]::RootElement
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $window = $null
    $trackedPids = @([int]$process.Id)
    while ((Get-Date) -lt $deadline) {
        Start-Sleep -Milliseconds 350
        $process.Refresh()
        if ($process.HasExited) { throw "Native desktop process exited before its window was ready" }
        $children = @(Get-CimInstance Win32_Process -Filter "ParentProcessId = $($process.Id)" -ErrorAction SilentlyContinue | ForEach-Object { [int]$_.ProcessId })
        $trackedPids = @([int]$process.Id) + $children
        $windows = $desktop.FindAll([System.Windows.Automation.TreeScope]::Children, [System.Windows.Automation.Condition]::TrueCondition)
        foreach ($candidate in $windows) {
            if (($trackedPids -contains [int]$candidate.Current.ProcessId) -and ($candidate.Current.Name -match "AETHERION")) {
                $window = $candidate
                break
            }
        }
        if ($null -ne $window) { break }
    }
    if ($null -eq $window) { throw "No AETHERION native top-level window appeared via Windows UI Automation" }
    $report.observed += "Native Qt window opened under process $($window.Current.ProcessId) (launcher $($process.Id)): $($window.Current.Name)."

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
    function Find-UiAnyName($parent, [string[]]$names, $controlType = $null) {
        foreach ($name in $names) {
            $cond = [System.Windows.Automation.PropertyCondition]::new(
                [System.Windows.Automation.AutomationElement]::NameProperty, $name
            )
            if ($null -ne $controlType) {
                $typeCond = [System.Windows.Automation.PropertyCondition]::new(
                    [System.Windows.Automation.AutomationElement]::ControlTypeProperty, $controlType
                )
                $cond = [System.Windows.Automation.AndCondition]::new($cond, $typeCond)
            }
            $found = $parent.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $cond)
            if ($null -ne $found) { return $found }
        }
        return $null
    }
    function Select-UiItem($element) {
        if ($null -eq $element) { return $false }
        try {
            $sel = $element.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern)
            if ($null -ne $sel) { $sel.Select(); return $true }
        } catch {}
        return $false
    }
    function Click-UiPoint([IntPtr]$rootHwnd, $element) {
        if ($null -eq $element) { throw "Cannot click null UIA element" }
        $rect = $element.Current.BoundingRectangle
        if ($rect.Width -le 0 -or $rect.Height -le 0) { throw "UIA element has empty BoundingRectangle" }
        $sx = [int][Math]::Round($rect.Left + ($rect.Width / 2.0))
        $sy = [int][Math]::Round($rect.Top + ($rect.Height / 2.0))
        $win32Click = @'
using System;
using System.Runtime.InteropServices;
public static class AetherionWinClick {
    [StructLayout(LayoutKind.Sequential)] public struct POINT { public int X, Y; }
    [DllImport("user32.dll")] public static extern bool ScreenToClient(IntPtr hWnd, ref POINT lpPoint);
    [DllImport("user32.dll")] public static extern IntPtr ChildWindowFromPointEx(IntPtr hwndParent, POINT pt, uint uFlags);
    [DllImport("user32.dll")] public static extern IntPtr SendMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
    public static void ClickScreenPoint(IntPtr rootHwnd, int x, int y) {
        POINT pt = new POINT { X = x, Y = y };
        ScreenToClient(rootHwnd, ref pt);
        IntPtr cur = rootHwnd;
        for (int i = 0; i < 6; i++) {
            IntPtr child = ChildWindowFromPointEx(cur, pt, 1);
            if (child == IntPtr.Zero || child == cur) break;
            POINT spt = new POINT { X = x, Y = y };
            ScreenToClient(child, ref spt);
            cur = child;
            pt = spt;
        }
        IntPtr lp = (IntPtr)((pt.Y << 16) | (pt.X & 0xFFFF));
        SendMessage(cur, 0x0201, (IntPtr)1, lp);
        SendMessage(cur, 0x0202, IntPtr.Zero, lp);
    }
}
'@
        Add-Type -TypeDefinition $win32Click -ErrorAction SilentlyContinue
        [AetherionWinClick]::ClickScreenPoint($rootHwnd, $sx, $sy)
    }
    $rootHwnd = [IntPtr]::new([int64]$window.Current.NativeWindowHandle)
    # Support Q-0485 Browse tree navigation ("Medical Library" / "Thư viện y khoa")
    # and legacy top-bar "Medical Library" button; a mere portal screenshot is never an article-read PASS.
    $libraryItem = Find-UiAnyName $window @("Medical Library", "Thư viện y khoa") ([System.Windows.Automation.ControlType]::TreeItem)
    if ($null -eq $libraryItem) {
        $libraryItem = Find-UiAnyName $window @("Medical Library", "Thư viện y khoa")
    }
    if ($null -eq $libraryItem) { throw "Medical Library navigation control is missing" }
    if ($libraryItem.Current.ControlType -eq [System.Windows.Automation.ControlType]::TreeItem) {
        Click-UiPoint $rootHwnd $libraryItem
    } else {
        Invoke-UiButton $libraryItem
    }
    Start-Sleep -Milliseconds 750
    $readerButton = Find-UiAnyName $window @(
        "Read imported article from local library",
        "Read selected article offline",
        "Đọc bài đã nhập từ thư viện cục bộ",
        "Đọc bài đã chọn ngoại tuyến"
    ) ([System.Windows.Automation.ControlType]::Button)
    if ($null -eq $readerButton) {
        throw "Native library page did not reveal the reader selection control"
    }
    $report.observed += "Medical Library navigation opened a native article-index view."

    $listItemType = [System.Windows.Automation.PropertyCondition]::new(
        [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
        [System.Windows.Automation.ControlType]::ListItem
    )
    $items = $window.FindAll([System.Windows.Automation.TreeScope]::Descendants, $listItemType)
    if ($items.Count -lt 1) { throw "No accessible imported article list item was visible" }
    $selectedOk = $false
    try {
        Click-UiPoint $rootHwnd $items.Item(0)
        $selectedOk = $true
    } catch { }
    if (-not $selectedOk) {
        $selectionPattern = $items.Item(0).GetCurrentPattern(
            [System.Windows.Automation.SelectionItemPattern]::Pattern
        )
        $selectionPattern.Select()
    }
    Start-Sleep -Milliseconds 250
    Invoke-UiButton $readerButton
    Start-Sleep -Milliseconds 650
    if ($null -eq (Find-UiAnyName $window @("Back to library", "Trở về thư viện"))) {
        throw "Selection did not open the native offline article reader"
    }
    $report.observed += "Selected a real imported article, opened reader, and detected Back to library."

    # Capture only the actual AETHERION window rectangle, using PrintWindow fallback if CopyFromScreen handle is restricted.
    Add-Type -AssemblyName System.Drawing
    $bounds = $window.Current.BoundingRectangle
    $width = [int][Math]::Ceiling($bounds.Width)
    $height = [int][Math]::Ceiling($bounds.Height)
    if ($width -lt 200 -or $height -lt 200) { throw "Qt native window has invalid screenshot bounds" }
    $bitmap = New-Object System.Drawing.Bitmap($width, $height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    try {
        try {
            $graphics.CopyFromScreen([int]$bounds.Left, [int]$bounds.Top, 0, 0, $bitmap.Size)
        } catch {
            $hwnd = [IntPtr]::new([int64]$window.Current.NativeWindowHandle)
            if ($hwnd -eq [IntPtr]::Zero) { throw }
            $winCapture = @'
using System;
using System.Runtime.InteropServices;
public static class AetherionPrintWindow {
    [DllImport("user32.dll", SetLastError = true)]
    public static extern bool PrintWindow(IntPtr hwnd, IntPtr hdcBlt, uint nFlags);
}
'@
            Add-Type -TypeDefinition $winCapture -ErrorAction SilentlyContinue
            $hdc = $graphics.GetHdc()
            try {
                if (-not [AetherionPrintWindow]::PrintWindow($hwnd, $hdc, 2)) {
                    [void][AetherionPrintWindow]::PrintWindow($hwnd, $hdc, 0)
                }
            } finally {
                $graphics.ReleaseHdc($hdc)
            }
        }
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
    Remove-Item -LiteralPath $auditScript -Force -ErrorAction SilentlyContinue
    $env:AETHERION_API_URL = $oldApi
    $env:AETHERION_CLIFF_LIBRARY_PATH = $oldCliff
    if ($null -ne $process -and -not $KeepWindowOpen) {
        try {
            $children = @(Get-CimInstance Win32_Process -Filter "ParentProcessId = $($process.Id)" -ErrorAction SilentlyContinue | ForEach-Object { [int]$_.ProcessId })
            foreach ($cid in $children) {
                Stop-Process -Id $cid -Force -ErrorAction SilentlyContinue
            }
        } catch { }
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
