<?php

// Never migrate or seed the main laboratory database from this script.
require __DIR__.'/../vendor/autoload.php';
$app = require __DIR__.'/../bootstrap/app.php';
$kernel = $app->make(Illuminate\Contracts\Console\Kernel::class);
$kernel->bootstrap();

$database = 'locust_lab_comparison';
config(['database.default' => 'mysql', 'database.connections.mysql.database' => null, 'database.connections.mysql.url' => null]);
Illuminate\Support\Facades\DB::purge('mysql');
Illuminate\Support\Facades\DB::statement('CREATE DATABASE IF NOT EXISTS `locust_lab_comparison` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci');
config(['database.connections.mysql.database' => $database]);
Illuminate\Support\Facades\DB::purge('mysql');
$actual = Illuminate\Support\Facades\DB::selectOne('SELECT DATABASE() AS name')->name;
if ($actual !== $database) {
    throw new RuntimeException('Refusing to modify an unexpected database.');
}
if ($kernel->call('migrate', ['--force' => true]) !== 0) {
    fwrite(STDERR, $kernel->output());
    exit(1);
}
$count = App\Models\User::count();
if ($count > 10000) {
    throw new RuntimeException('Comparison database has more than 10000 rows. No data was removed. Use only GET requests on this database.');
}
if ($count < 10000) {
    $app->make(Database\Seeders\MassUserSeeder::class)->run(10000 - $count, 2000);
}
echo json_encode(['database' => $actual, 'rows' => App\Models\User::count()], JSON_PRETTY_PRINT).PHP_EOL;
