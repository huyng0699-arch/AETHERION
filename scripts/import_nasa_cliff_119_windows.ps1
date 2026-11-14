# Windows runner: fetch the 119 original NASA CliFF documents and push only the originals.
# Run from any PowerShell folder: powershell -ExecutionPolicy Bypass -File .\scripts\import_nasa_cliff_119_windows.ps1
[CmdletBinding()]
param([switch]$NoPush)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Push-Location $repo
try {
    $remote = (& git remote get-url origin).Trim()
    if ($LASTEXITCODE -ne 0 -or $remote -notmatch '(^|[:/])huyng0699-arch/AETHERION(\.git)?$') {
        throw "Wrong repository: this script only supports huyng0699-arch/AETHERION."
    }
    $branch = (& git branch --show-current).Trim()
    if ($branch -ne 'main') { throw "Switch to the main branch before importing. Current: $branch" }

    # Prevent accidental loss of local changes. No reset, force push, or staging of other data.
    & git pull --ff-only origin main
    if ($LASTEXITCODE -ne 0) { throw "Fast-forward pull failed. Resolve local Git changes before continuing." }

    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3.11 -m venv .venv-nasa
    } else {
        & python -m venv .venv-nasa
    }
    if ($LASTEXITCODE -ne 0) { throw "Python virtual environment creation failed." }
    $python = Join-Path $repo ".venv-nasa\Scripts\python.exe"
    & $python -m pip install --disable-pip-version-check "requests>=2.32,<3" "beautifulsoup4>=4.12,<5"
    if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed." }

    & $python ".\scripts\fetch_nasa_cliff_119.py"
    $importExitCode = $LASTEXITCODE
    $manifestPath = "knowledge/nasa/cliff_119_2023/manifest.json"
    if (-not (Test-Path $manifestPath)) {
        throw "NASA source index could not be read; no manifest was created. No data will be pushed."
    }

    # Independently verify every successfully downloaded original, including partial batches.
    $validation = @'
import hashlib, json, pathlib, sys
root = pathlib.Path("knowledge/nasa/cliff_119_2023")
manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
files = manifest["files"]
count = 0
for entry in files:
    if entry["status"] != "downloaded":
        continue
    count += 1
    p = root / entry["path"]
    assert p.is_file()
    data = p.read_bytes()
    assert len(data) == entry["bytes"]
    assert hashlib.sha256(data).hexdigest() == entry["sha256"]
    assert data.startswith((b"%PDF-", b"PK\x03\x04", b"\xd0\xcf\x11\xe0"))
assert count == manifest["downloaded_documents"]
print(f"Verified: {count} downloaded NASA originals; PDF count: {manifest.get('downloaded_pdf_count', 0)}/119")
'@
    $validation | & $python -
    if ($LASTEXITCODE -ne 0) { throw "Integrity check failed; refusing to push." }
    $manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
    if ($NoPush) {
        Write-Host "NASA originals verified locally: $($manifest.downloaded_pdf_count)/119 PDFs; push skipped."
        return
    }

    $otherStaged = @(& git diff --cached --name-only | Where-Object { $_ -and ($_ -notlike 'knowledge/nasa/cliff_119_2023/*') })
    if ($otherStaged.Count -gt 0) {
        throw "Unrelated files were already staged; refusing to include them in this commit: $($otherStaged -join ', ')"
    }
    & git add -- "knowledge/nasa/cliff_119_2023/"
    if ($LASTEXITCODE -ne 0) { throw "Git staging failed." }
    & git diff --cached --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "No newly downloadable NASA originals. Verified PDFs: $($manifest.downloaded_pdf_count)/119."
        if (-not $manifest.complete) { throw "INCOMPLETE: verified originals are preserved. Fix NASA access and retry." }
        return
    }
    & git commit -m "Import NASA CliFF 2023 originals with SHA-256 provenance"
    if ($LASTEXITCODE -ne 0) { throw "Git commit failed." }
    & git push origin main
    if ($LASTEXITCODE -ne 0) { throw "Git push failed; local commit is preserved." }
    if (-not $manifest.complete -or $importExitCode -ne 0) {
        throw "PARTIAL: $($manifest.downloaded_pdf_count)/119 NASA PDF originals uploaded. Manifest lists missing files; retry when accessible."
    }
    Write-Host "SUCCESS: 119/119 original NASA CliFF PDFs uploaded to AETHERION."
}
finally {
    Pop-Location
}
