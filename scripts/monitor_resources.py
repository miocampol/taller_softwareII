"""Sample API/database processes. CPU 100% means one logical core."""

import argparse
import csv
import time
from datetime import datetime, timezone
from pathlib import Path

import psutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int, nargs="+", required=True)
    parser.add_argument("--seconds", type=int, required=True)
    parser.add_argument("--output", required=True)
    options = parser.parse_args()
    processes = [psutil.Process(pid) for pid in options.pid]
    for process in processes:
        process.cpu_percent()
    output = Path(options.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["timestamp_utc", "elapsed_seconds", "pid", "process", "cpu_percent", "rss_mb"])
        started = time.monotonic()
        while time.monotonic() - started < options.seconds:
            time.sleep(1)
            for process in processes:
                try:
                    writer.writerow([datetime.now(timezone.utc).isoformat(),
                                     round(time.monotonic() - started, 2), process.pid, process.name(),
                                     process.cpu_percent(), round(process.memory_info().rss / 1024 ** 2, 2)])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            stream.flush()


if __name__ == "__main__":
    main()
