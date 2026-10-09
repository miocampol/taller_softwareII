$ErrorActionPreference = 'Stop'
Push-Location (Join-Path $PSScriptRoot '..')
try {
    $root = (Get-Location).Path
    $baselineCommit = 'afbb181'
    $directory = Join-Path $root 'reports/generated/comparison'
    $before = Join-Path $directory 'before'
    $phpPath = (Get-Command php).Source
    if (-not (Test-Path 'vendor/autoload.php')) { throw 'Run composer install first.' }
    if (-not (Test-Path '.env')) { throw 'Configure .env first.' }
    $currentLock = git hash-object composer.lock
    $baselineLock = git rev-parse "${baselineCommit}:composer.lock"
    if ($LASTEXITCODE -ne 0 -or $currentLock -ne $baselineLock) {
        throw 'The baseline has different dependencies. Install its own locked dependencies before reusing this script.'
    }
    New-Item -ItemType Directory -Force -Path $before | Out-Null
    $archive = Join-Path $directory 'before.tar'
    git archive --format=tar "--output=$archive" $baselineCommit
    if ($LASTEXITCODE -ne 0) { throw 'Could not export baseline source.' }
    $windowsTar = Join-Path $env:SystemRoot 'System32/tar.exe'
    if (Test-Path $windowsTar) {
        & $windowsTar -xf $archive -C $before
    } else {
        tar --force-local -xf $archive -C $before
    }
    if ($LASTEXITCODE -ne 0) { throw 'Could not extract baseline source.' }
    if (-not (Test-Path (Join-Path $before 'vendor/autoload.php'))) {
        # A real copy keeps Composer's relative App paths inside the old source.
        Copy-Item -LiteralPath (Join-Path $root 'vendor') -Destination $before -Recurse
    }
    $envText = [IO.File]::ReadAllText((Join-Path $root '.env'))
    $envText = [regex]::Replace($envText, '(?m)^DB_DATABASE=.*$', 'DB_DATABASE=locust_lab_comparison')
    $envText = [regex]::Replace($envText, '(?m)^APP_DEBUG=.*$', 'APP_DEBUG=false')
    $envText = [regex]::Replace($envText, '(?m)^APP_URL=.*$', 'APP_URL=http://127.0.0.1:8001')
    [IO.File]::WriteAllText((Join-Path $before '.env'), $envText)
    & $phpPath -d error_reporting=8191 scripts/prepare-comparison.php
    if ($LASTEXITCODE -ne 0) { throw 'Could not prepare the comparison database.' }
    Write-Host 'Comparison prepared: 10000 rows. Main .env and locust_lab were preserved.'
    Write-Host 'Start both servers with scripts/start-comparison.ps1.'
} finally {
    Pop-Location
}
