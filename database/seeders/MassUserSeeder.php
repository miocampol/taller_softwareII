<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Str;

class MassUserSeeder extends Seeder
{
    public const DEFAULT_TOTAL = 1_500_000;

    public const CHUNK_SIZE = 2_000;

    public function run(?int $count = null, ?int $chunk = null): void
    {
        $total = $count ?? (int) env('MASS_USER_SEED_COUNT', self::DEFAULT_TOTAL);
        $chunkSize = $chunk ?? (int) env('MASS_USER_CHUNK_SIZE', self::CHUNK_SIZE);

        if ($total < 1 || $chunkSize < 1) {
            throw new \InvalidArgumentException('El total y el tamaño de lote deben ser mayores a 0.');
        }

        $batchToken = (string) Str::uuid();

        $passwordHash = '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi';
        $now = now()->toDateTimeString();
        $inserted = 0;

        $this->command?->info("Insertando {$total} usuarios en lotes de {$chunkSize}...");

        DB::disableQueryLog();

        for ($offset = 0; $offset < $total; $offset += $chunkSize) {
            $limit = min($chunkSize, $total - $offset);
            $rows = [];

            for ($i = 0; $i < $limit; $i++) {
                $sequence = $offset + $i + 1;
                $birthDate = $this->randomBirthDate();

                $rows[] = [
                    'name' => 'Usuario '.$sequence,
                    'email' => 'usuario'.$batchToken.'.'.$sequence.'@loadtest.local',
                    'birth_date' => $birthDate,
                    'email_verified_at' => $now,
                    'password' => $passwordHash,
                    'remember_token' => null,
                    'created_at' => $now,
                    'updated_at' => $now,
                ];
            }

            DB::table('users')->insert($rows);
            $inserted += $limit;

            if ($this->command && $inserted % 100_000 === 0) {
                $this->command->info("Progreso: {$inserted} / {$total}");
            }
        }

        $this->command?->info("Listo: {$inserted} usuarios insertados.");
    }

    private function randomBirthDate(): string
    {
        $min = strtotime('-80 years');
        $max = strtotime('-5 years');

        return date('Y-m-d', random_int($min, $max));
    }
}
