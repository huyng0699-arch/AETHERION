param([string]$Python = '', [switch]$SkipBuild, [switch]$Verification)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $Python) {
    $venvPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
    $Python = if (Test-Path -LiteralPath $venvPython) { $venvPython } else { 'python' }
}
if (-not $SkipBuild) {
    Push-Location (Join-Path $projectRoot 'apps\mobile')
    try {
        if (-not (Test-Path 'node_modules\expo\package.json')) { npm ci --no-audit --no-fund; if ($LASTEXITCODE) { throw 'npm ci failed' } }
        npm run typecheck
        if ($LASTEXITCODE) { throw 'TypeScript failed' }
        npm run export:web
        if ($LASTEXITCODE) { throw 'Expo export failed' }
    } finally { Pop-Location }
}
$arguments = @((Join-Path $PSScriptRoot 'run_mobile_local.py'))
if ($Verification) { $arguments += '--verification' }
& $Python @arguments
exit $LASTEXITCODE
