$ErrorActionPreference = 'Stop'
Push-Location (Join-Path $PSScriptRoot '..')
try {
    $root = (Get-Location).Path
    $directory = Join-Path $root 'reports/generated/comparison'
    $before = Join-Path $directory 'before'
    if (Test-Path 'bootstrap/cache/config.php') {
        throw 'Clear the Laravel config cache before starting the isolated comparison: php artisan config:clear.'
    }
    if (-not (Test-Path (Join-Path $before 'vendor/autoload.php'))) {
        throw 'Run scripts/prepare-comparison.ps1 first.'
    }
    $phpPath = (Get-Command php).Source
    foreach ($port in @(8001, 8002)) {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $port)
        try { $listener.Start() } catch { throw "Port $port is occupied. No server was started." } finally { $listener.Stop() }
    }
    $savedDatabase = $env:DB_DATABASE
    $savedUrl = $env:DATABASE_URL
    $beforeProcess = $null
    $afterProcess = $null
    try {
        $env:DB_DATABASE = 'locust_lab_comparison'
        $env:DATABASE_URL = ''
        $arguments = @('-d', 'error_reporting=8191', '-S', '127.0.0.1:8001', '-t', '.', '../vendor/laravel/framework/src/Illuminate/Foundation/resources/server.php')
        $beforeProcess = Start-Process -FilePath $phpPath -ArgumentList $arguments -WorkingDirectory (Join-Path $before 'public') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $directory 'before.stdout.log') -RedirectStandardError (Join-Path $directory 'before.stderr.log') -PassThru
        $arguments[3] = '127.0.0.1:8002'
        $afterProcess = Start-Process -FilePath $phpPath -ArgumentList $arguments -WorkingDirectory (Join-Path $root 'public') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $directory 'after.stdout.log') -RedirectStandardError (Join-Path $directory 'after.stderr.log') -PassThru
    } catch {
        if ($beforeProcess -and -not $beforeProcess.HasExited) { Stop-Process -Id $beforeProcess.Id }
        throw
    } finally {
        $env:DB_DATABASE = $savedDatabase
        $env:DATABASE_URL = $savedUrl
    }
    @{ before = $beforeProcess.Id; after = $afterProcess.Id } | ConvertTo-Json | Set-Content (Join-Path $directory 'servers.json') -Encoding utf8
    Write-Host "BEFORE (afbb181): http://127.0.0.1:8001/api/users - PID $($beforeProcess.Id)"
    Write-Host "AFTER (current): http://127.0.0.1:8002/api/users?page=1&per_page=5 - PID $($afterProcess.Id)"
    Write-Host 'Both use locust_lab_comparison. Capture only GET requests here.'
} finally {
    Pop-Location
}
