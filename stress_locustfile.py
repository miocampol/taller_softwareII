"""Six one-minute stages; use --config loadtests/stress.conf."""

import os

from locust import LoadTestShape
from locustfile import ApiUser  # Locust discovers the imported user class.


class StressShape(LoadTestShape):
    stage_seconds = int(os.environ.get("LOCUST_STAGE_SECONDS", "60"))
    if stage_seconds < 1:
        raise ValueError("LOCUST_STAGE_SECONDS must be positive")
    stages = [(index, users, rate)
              for index, (users, rate) in enumerate(
                  [(5, 5), (10, 5), (20, 10), (40, 10), (80, 20), (160, 40)], 1)]

    def tick(self):
        elapsed = self.get_run_time()
        for duration, users, spawn_rate in self.stages:
            if elapsed < duration * self.stage_seconds:
                return users, spawn_rate
        return None
