"""
Mock Log Generator - Generates realistic application logs and pushes them to Loki.
Simulates a microservices environment with various error scenarios.
"""

import json
import time
import random
import requests
from datetime import datetime, timezone

LOKI_URL = "http://localhost:3100/loki/api/v1/push"

# Service definitions
SERVICES = ["api-gateway", "auth-service", "payment-service", "user-service", "order-service", "inventory-service"]

# Log templates by severity
LOG_TEMPLATES = {
    "INFO": [
        "Request processed successfully in {duration}ms",
        "Health check passed for {service}",
        "Connection pool stats: active={active}, idle={idle}",
        "Cache hit ratio: {ratio}%",
        "Successfully processed {count} messages from queue",
        "Deployment version {version} is healthy",
        "Database migration completed successfully",
        "User {user_id} logged in successfully",
    ],
    "WARNING": [
        "High memory usage detected: {memory}% on {service}",
        "Response time exceeded threshold: {duration}ms (threshold: 500ms)",
        "Connection pool nearing capacity: {active}/{max} connections used",
        "Disk usage at {disk}% on volume /data",
        "Rate limiting applied for client {client_id}: {count} requests/min",
        "Certificate for {domain} expires in {days} days",
        "Retry attempt {attempt}/3 for external API call to {endpoint}",
        "Queue depth exceeding warning threshold: {depth} messages pending",
    ],
    "ERROR": [
        "Database connection failed: ConnectionRefusedError - host={host} port={port}",
        "OutOfMemoryError: Java heap space - container {container_id} killed by OOM",
        "SSL/TLS handshake failed: certificate verify failed for {domain}",
        "Timeout waiting for response from {service}: exceeded {timeout}s deadline",
        "Disk full on /var/log: write failed with errno 28 (No space left on device)",
        "Authentication failed: invalid token for user {user_id} from IP {ip}",
        "Container {container_id} CrashLoopBackOff: restart count {restart_count}",
        "Connection reset by peer: {service} upstream unreachable at {host}:{port}",
        "Failed to process payment: gateway timeout from {gateway}",
        "Kubernetes pod {pod_name} evicted: insufficient memory on node {node}",
    ],
    "CRITICAL": [
        "ALERT: All replicas of {service} are down! Last healthy: {timestamp}",
        "Data corruption detected in table {table}: checksum mismatch on block {block}",
        "Security breach detected: unauthorized access from {ip} to {endpoint}",
        "Cascading failure: {service} dependency chain broken at {dependency}",
        "Database replication lag exceeded 60s: primary={primary}, replica={replica}",
    ],
}


def _fill_template(template: str) -> str:
    """Fill a log template with random realistic values."""
    replacements = {
        "{duration}": str(random.randint(50, 5000)),
        "{service}": random.choice(SERVICES),
        "{active}": str(random.randint(5, 95)),
        "{idle}": str(random.randint(1, 20)),
        "{max}": "100",
        "{ratio}": str(random.randint(40, 99)),
        "{count}": str(random.randint(1, 500)),
        "{version}": f"v{random.randint(1,5)}.{random.randint(0,9)}.{random.randint(0,20)}",
        "{user_id}": f"usr_{random.randint(1000,9999)}",
        "{memory}": str(random.randint(75, 99)),
        "{disk}": str(random.randint(80, 99)),
        "{client_id}": f"client_{random.randint(100,999)}",
        "{domain}": random.choice(["api.example.com", "auth.internal.io", "payments.prod.net"]),
        "{days}": str(random.randint(1, 14)),
        "{attempt}": str(random.randint(1, 3)),
        "{endpoint}": random.choice(["/api/v1/users", "/api/v1/orders", "/api/v1/payments", "/health"]),
        "{depth}": str(random.randint(1000, 50000)),
        "{host}": random.choice(["10.0.1.5", "10.0.2.12", "db-primary.internal", "redis-master.internal"]),
        "{port}": random.choice(["5432", "6379", "3306", "8080", "443"]),
        "{container_id}": f"ctr-{random.randint(100000,999999):06x}",
        "{timeout}": str(random.randint(5, 60)),
        "{ip}": f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
        "{restart_count}": str(random.randint(3, 50)),
        "{gateway}": random.choice(["stripe", "paypal", "square"]),
        "{pod_name}": f"{random.choice(SERVICES)}-{random.randint(1000,9999):04x}",
        "{node}": f"node-{random.randint(1,10)}",
        "{timestamp}": datetime.now(timezone.utc).isoformat(),
        "{table}": random.choice(["users", "orders", "payments", "sessions"]),
        "{block}": str(random.randint(1, 1000)),
        "{dependency}": random.choice(SERVICES),
        "{primary}": "db-primary.internal",
        "{replica}": f"db-replica-{random.randint(1,3)}.internal",
    }
    result = template
    for key, value in replacements.items():
        result = result.replace(key, value)
    return result


def generate_log_entry() -> dict:
    """Generate a single realistic log entry."""
    # Weighted severity distribution: mostly INFO, some warnings, fewer errors
    severity = random.choices(
        ["INFO", "WARNING", "ERROR", "CRITICAL"],
        weights=[50, 25, 20, 5],
        k=1,
    )[0]

    service = random.choice(SERVICES)
    template = random.choice(LOG_TEMPLATES[severity])
    message = _fill_template(template)

    return {
        "service": service,
        "level": severity,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def push_to_loki(entries: list[dict]) -> bool:
    """Push log entries to Loki via the HTTP API."""
    streams = {}

    for entry in entries:
        label_key = f'{entry["service"]}_{entry["level"]}'
        if label_key not in streams:
            streams[label_key] = {
                "stream": {
                    "job": "devops-mock-logs",
                    "service": entry["service"],
                    "level": entry["level"],
                },
                "values": [],
            }
        timestamp_ns = str(int(time.time() * 1e9))
        log_line = json.dumps({
            "level": entry["level"],
            "service": entry["service"],
            "message": entry["message"],
            "timestamp": entry["timestamp"],
        })
        streams[label_key]["values"].append([timestamp_ns, log_line])

    payload = {"streams": list(streams.values())}

    try:
        resp = requests.post(LOKI_URL, json=payload, timeout=5)
        resp.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Failed to push logs to Loki: {e}")
        return False


def run_generator(batch_size: int = 10, interval: float = 2.0, total_batches: int = 50):
    """Run the log generator, pushing batches of logs to Loki."""
    print(f"Starting mock log generator: {batch_size} logs every {interval}s for {total_batches} batches")
    print(f"Pushing to Loki at {LOKI_URL}")

    for batch_num in range(1, total_batches + 1):
        entries = [generate_log_entry() for _ in range(batch_size)]

        error_count = sum(1 for e in entries if e["level"] in ("ERROR", "CRITICAL"))
        warn_count = sum(1 for e in entries if e["level"] == "WARNING")

        success = push_to_loki(entries)
        status = "OK" if success else "FAILED"

        print(
            f"[Batch {batch_num}/{total_batches}] {status} | "
            f"Sent {len(entries)} logs ({error_count} errors, {warn_count} warnings)"
        )

        if batch_num < total_batches:
            time.sleep(interval)

    print("Log generation complete.")


if __name__ == "__main__":
    run_generator()
