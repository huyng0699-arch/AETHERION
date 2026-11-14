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
    if ($LASTEXITCODE -ne 0) { throw "NASA import incomplete: do not commit or claim 119 originals." }

    # Independent verification of the full collection's document count and hashes.
    $validation = @'
import hashlib, json, pathlib, sys
root = pathlib.Path("knowledge/nasa/cliff_119_2023")
manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
files = manifest["files"]
assert manifest["complete"] and manifest["downloaded_documents"] == 119 and len(files) == 119
assert len({i["source_url"] for i in files}) == 119
for entry in files:
    assert entry["status"] == "downloaded"
    p = root / entry["path"]
    assert p.is_file()
    data = p.read_bytes()
    assert len(data) == entry["bytes"]
    assert hashlib.sha256(data).hexdigest() == entry["sha256"]
    assert data.startswith((b"%PDF-", b"PK\x03\x04", b"\xd0\xcf\x11\xe0"))
print("Verified: 119 NASA-origin files, size and SHA-256 match")
'@
    $validation | & $python -
    if ($LASTEXITCODE -ne 0) { throw "Integrity check failed; refusing to push." }
    if ($NoPush) {
        Write-Host "Local originals verified, push skipped via -NoPush."
        return
    }

    $otherStaged = @(& git diff --cached --name-only | Where-Object { $_ -and ($_ -notlike 'knowledge/nasa/cliff_119_2023/*') })
    if ($otherStaged.Count -gt 0) {
        throw "Unrelated files were already staged; refusing to include them in this commit: $($otherStaged -join ', ')"
    }
    & git add -- "knowledge/nasa/cliff_119_2023/original/" "knowledge/nasa/cliff_119_2023/manifest.json"
    if ($LASTEXITCODE -ne 0) { throw "Git staging failed." }
    & git diff --cached --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-Host "All 119 verified originals are already committed."
        return
    }
    & git commit -m "Import 119 original NASA CliFF 2023 documents with SHA-256 manifest"
    if ($LASTEXITCODE -ne 0) { throw "Git commit failed." }
    & git push origin main
    if ($LASTEXITCODE -ne 0) { throw "Git push failed; local commit is preserved." }
    Write-Host "SUCCESS: 119 original NASA CliFF documents uploaded to AETHERION."
}
finally {
    Pop-Location
}
