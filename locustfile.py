"""90% reads / 10% writes. Run with python -m locust -f locustfile.py."""

import logging
import random

from locust import HttpUser, between, events, task

from loadtests.contracts import bulk_payload, validate_bulk, validate_page


@events.init_command_line_parser.add_listener
def add_arguments(parser):
    parser.add_argument("--per-page", type=int, default=50, help="GET page size (1..200)")
    parser.add_argument("--page-count", type=int, default=10, help="Random pages to request (1..N)")
    parser.add_argument("--sla-p95-ms", type=float, default=1000, help="Per-operation p95 target")
    parser.add_argument("--sla-error-ratio", type=float, default=0.01, help="Maximum failure ratio")


@events.init.add_listener
def validate_options(environment, **kwargs):
    options = environment.parsed_options
    if not 1 <= options.per_page <= 200 or options.page_count < 1:
        raise ValueError("--per-page must be 1..200 and --page-count must be positive")
    if options.sla_p95_ms <= 0 or not 0 <= options.sla_error_ratio <= 1:
        raise ValueError("Invalid SLA thresholds")


@events.quitting.add_listener
def check_sla(environment, **kwargs):
    """Nonzero exit for no traffic, errors, or a per-operation latency breach."""
    options = environment.parsed_options
    total = environment.stats.total
    breached = total.num_requests == 0 or total.fail_ratio > options.sla_error_ratio
    expected = {('GET', '/api/users'), ('GET', '/api/users/emails'),
                ('GET', '/api/users/over-twenty'), ('POST', '/api/users/bulk')}
    observed = {(entry.method, entry.name) for entry in environment.stats.entries.values() if entry.num_requests}
    if expected - observed:
        logging.warning('Incomplete endpoint coverage: %s', sorted(expected - observed))
        breached = True
    for entry in environment.stats.entries.values():
        p95 = entry.get_response_time_percentile(0.95) or 0
        breached |= p95 > options.sla_p95_ms or entry.fail_ratio > options.sla_error_ratio
    if breached:
        environment.process_exit_code = 1


class ApiUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        self.client.headers.update({"Accept": "application/json"})

    def get_page(self, endpoint):
        options = self.environment.parsed_options
        page = random.randint(1, options.page_count)
        with self.client.get(endpoint, params={"page": page, "per_page": options.per_page},
                             name=endpoint, catch_response=True, timeout=30) as response:
            if response.status_code != 200:
                response.failure(f"Expected HTTP 200, received {response.status_code}")
                return
            try:
                error = validate_page(response.json(), endpoint, page, options.per_page)
            except ValueError:
                error = "Response is not valid JSON"
            if error:
                response.failure(error)

    @task(5)
    def users(self):
        self.get_page("/api/users")

    @task(3)
    def emails(self):
        self.get_page("/api/users/emails")

    @task(1)
    def over_twenty(self):
        self.get_page("/api/users/over-twenty")

    @task(1)
    def create_batch(self):
        payload = bulk_payload()
        with self.client.post("/api/users/bulk", json=payload, name="/api/users/bulk",
                              catch_response=True, timeout=30) as response:
            if response.status_code != 201:
                response.failure(f"Expected HTTP 201, received {response.status_code}")
                return
            try:
                error = validate_bulk(response.json(), payload)
            except ValueError:
                error = "Response is not valid JSON"
            if error:
                response.failure(error)
