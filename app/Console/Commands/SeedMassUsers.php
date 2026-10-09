<?php

namespace App\Console\Commands;

use Database\Seeders\MassUserSeeder;
use Illuminate\Console\Command;

class SeedMassUsers extends Command
{
    protected $signature = 'users:seed-mass
                            {--count=1500000 : Cantidad total de usuarios}
                            {--chunk=2000 : Tamaño de lote por inserción}';

    protected $description = 'Pobla la tabla users con datos masivos para pruebas de carga (Locust)';

    public function handle(): int
    {
        $count = filter_var($this->option('count'), FILTER_VALIDATE_INT, ['options' => ['min_range' => 1]]);
        $chunk = filter_var($this->option('chunk'), FILTER_VALIDATE_INT, ['options' => ['min_range' => 1]]);
        if ($count === false || $chunk === false) {
            $this->error('--count y --chunk deben ser enteros positivos.');

            return self::FAILURE;
        }

        $seeder = $this->laravel->make(MassUserSeeder::class);
        $seeder->setCommand($this);
        $seeder->run($count, $chunk);

        return self::SUCCESS;
    }
}
