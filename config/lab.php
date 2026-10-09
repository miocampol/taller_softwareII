<?php

return [
    // Set to zero only in the controlled load-testing environment.
    'api_rate_limit' => (int) env('API_RATE_LIMIT', 60),
];
