param([int]$Port = 8000)

$ErrorActionPreference = 'Stop'
Push-Location (Join-Path $PSScriptRoot '..')
try {
    if (-not (Test-Path 'vendor/autoload.php')) { throw 'Run composer install first.' }
    if (-not (Test-Path '.env')) { throw 'Create .env and configure locust_lab first.' }
    $phpPath = (Get-Command php -ErrorAction Stop).Source
    $phpVersion = & $phpPath -r 'echo PHP_VERSION_ID;'
    if ([int]$phpVersion -lt 80200) { throw 'The current composer.lock requires PHP 8.2 or newer.' }
    Write-Host "API: http://127.0.0.1:$Port/api/users?page=1&per_page=50"
    Write-Host 'Local development server. Press Ctrl+C to stop.'
    Set-Location public
    & $phpPath -d error_reporting=8191 -S "127.0.0.1:$Port" -t . ../vendor/laravel/framework/src/Illuminate/Foundation/resources/server.php
    if ($LASTEXITCODE -ne 0) { throw 'The PHP server could not start. Check whether the port is in use.' }
} finally {
    Pop-Location
}
