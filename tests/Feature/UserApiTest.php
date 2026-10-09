<?php

namespace Tests\Feature;

use App\Models\User;
use Carbon\Carbon;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class UserApiTest extends TestCase
{
    use RefreshDatabase;

    public function test_get_endpoints_paginate_without_exposing_passwords(): void
    {
        User::factory()->count(5)->create(['birth_date' => '1990-01-01']);

        foreach (['/api/users', '/api/users/emails', '/api/users/over-twenty'] as $path) {
            $response = $this->getJson($path.'?page=2&per_page=2');
            $response->assertOk()->assertJsonPath('total', 5)
                ->assertJsonPath('current_page', 2)->assertJsonPath('per_page', 2)
                ->assertJsonCount(2, 'data');
            $this->assertSame([3, 4], array_column($response->json('data'), 'id'));
            $this->assertArrayNotHasKey('password', $response->json('data.0'));
        }

        $this->assertSame(['id', 'email'], array_keys($this->getJson('/api/users/emails')->json('data.0')));
    }

    public function test_pagination_defaults_limits_and_empty_pages(): void
    {
        User::factory()->count(51)->create();
        $this->getJson('/api/users')->assertJsonCount(50, 'data')->assertJsonPath('per_page', 50);
        $this->getJson('/api/users?per_page=200')->assertOk();
        $this->getJson('/api/users?page=100')->assertOk()->assertJsonCount(0, 'data');

        foreach (['/api/users', '/api/users/emails', '/api/users/over-twenty'] as $path) {
            foreach (['per_page=201', 'per_page=0', 'per_page=abc', 'page=0', 'page=-1', 'page=1.5'] as $query) {
                $this->getJson($path.'?'.$query)->assertUnprocessable();
            }
        }
    }

    public function test_age_filter_excludes_users_exactly_twenty_and_younger(): void
    {
        Carbon::setTestNow(Carbon::parse('2026-10-09 12:00:00'));
        try {
            User::factory()->create(['birth_date' => '2006-10-08']);
            User::factory()->create(['birth_date' => '2006-10-09']);
            User::factory()->create(['birth_date' => '2006-10-10']);
            $this->getJson('/api/users/over-twenty')->assertOk()
                ->assertJsonPath('cutoff_date', '2006-10-09')
                ->assertJsonPath('total', 1)->assertJsonCount(1, 'data');
        } finally {
            Carbon::setTestNow();
        }
    }

    public function test_bulk_creation_requires_three_unique_valid_users(): void
    {
        $users = collect(range(1, 3))->map(fn ($id) => [
            'name' => 'Test '.$id,
            'email' => 'test'.$id.'@example.com',
            'birth_date' => '1990-01-01',
        ])->all();

        $response = $this->postJson('/api/users/bulk', ['users' => $users]);
        $response->assertCreated()->assertJsonCount(3, 'users');
        $this->assertArrayNotHasKey('password', $response->json('users.0'));
        $this->postJson('/api/users/bulk', ['users' => $users])->assertUnprocessable();
        $this->postJson('/api/users/bulk', ['users' => array_slice($users, 0, 2)])->assertUnprocessable();
        $this->assertDatabaseCount('users', 3);
    }
}
