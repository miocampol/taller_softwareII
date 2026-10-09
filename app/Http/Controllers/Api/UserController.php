<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Http\Requests\BulkStoreUsersRequest;
use App\Models\User;
use Carbon\Carbon;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;

class UserController extends Controller
{
    public function index(Request $request): JsonResponse
    {
        $perPage = $this->perPage($request);

        return response()->json(User::orderBy('id')->paginate($perPage)->withQueryString());
    }

    public function emails(Request $request): JsonResponse
    {
        $perPage = $this->perPage($request);

        return response()->json(User::select('id', 'email')->orderBy('id')->paginate($perPage)->withQueryString());
    }

    public function overTwenty(Request $request): JsonResponse
    {
        $perPage = $this->perPage($request);
        $cutoff = Carbon::now()->subYears(20)->startOfDay();

        $users = User::where('birth_date', '<', $cutoff->toDateString())
            ->orderBy('id')->paginate($perPage)->withQueryString();

        return response()->json(array_merge($users->toArray(), [
            'cutoff_date' => $cutoff->toDateString(),
        ]));
    }

    private function perPage(Request $request): int
    {
        $validated = $request->validate([
            'page' => ['sometimes', 'integer', 'min:1'],
            'per_page' => ['sometimes', 'integer', 'min:1', 'max:200'],
        ]);

        return (int) ($validated['per_page'] ?? 50);
    }

    public function bulkStore(BulkStoreUsersRequest $request): JsonResponse
    {
        $created = [];

        foreach ($request->validated()['users'] as $userData) {
            $created[] = User::create([
                'name' => $userData['name'],
                'email' => $userData['email'],
                'birth_date' => $userData['birth_date'],
                'password' => Hash::make($userData['password'] ?? 'password'),
            ]);
        }

        return response()->json([
            'message' => 'Se crearon 3 usuarios correctamente.',
            'users' => $created,
        ], 201);
    }
}
