<?php

// CLI comparison only. Refuse the unpaginated query on a large dataset.
require __DIR__.'/../vendor/autoload.php';
$app = require __DIR__.'/../bootstrap/app.php';
$app->make(Illuminate\Contracts\Console\Kernel::class)->bootstrap();

$mode = $argv[1] ?? 'page';
if (!in_array($mode, ['all', 'page'], true)) {
    fwrite(STDERR, "Usage: php scripts/benchmark-pagination.php all|page\n");
    exit(1);
}
$total = App\Models\User::count();
if ($mode === 'all' && $total > 11000) {
    fwrite(STDERR, "Unpaginated benchmark is limited to 11000 rows. Use a separate small dataset.\n");
    exit(1);
}
$started = microtime(true);
$result = $mode === 'all'
    ? App\Models\User::all()
    : App\Models\User::orderBy('id')->paginate(50);
$json = $result->toJson();
echo json_encode([
    'mode' => $mode,
    'dataset_rows' => $total,
    'returned_rows' => count($result),
    'elapsed_ms' => round((microtime(true) - $started) * 1000, 2),
    'peak_memory_mb' => round(memory_get_peak_usage(true) / 1024 / 1024, 2),
    'response_bytes' => strlen($json),
], JSON_PRETTY_PRINT).PHP_EOL;
