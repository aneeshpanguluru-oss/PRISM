from dataclasses import dataclass


@dataclass
class SystemState:
    step: int
    requests: int
    workers: int
    active_connections: int
    max_connections: int
    waiting_transactions: int
    lock_wait_ms: float
    request_latency_ms: float
    connection_pool_usage_percent: float
    healthy: bool


def simulate_system(failure: str | None = None) -> list[SystemState]:
    scenarios = {
        "dns_failure": [
            SystemState(0, 100, 10, 16, 50, 0, 5.0, 100.0, 32.0, True),
            SystemState(1, 100, 10, 22, 50, 2, 5.0, 300.0, 44.0, True),
            SystemState(2, 100, 10, 30, 50, 5, 5.0, 800.0, 60.0, False),
            SystemState(3, 100, 10, 42, 50, 10, 5.0, 1800.0, 84.0, False),
        ],
        "network_failure": [
            SystemState(0, 100, 10, 16, 50, 0, 5.0, 100.0, 32.0, True),
            SystemState(1, 85, 10, 24, 50, 3, 5.0, 350.0, 48.0, True),
            SystemState(2, 60, 10, 34, 50, 8, 5.0, 900.0, 68.0, False),
            SystemState(3, 30, 10, 45, 50, 16, 5.0, 2000.0, 90.0, False),
        ],
        "http_failure": [
            SystemState(0, 100, 10, 16, 50, 0, 5.0, 100.0, 32.0, True),
            SystemState(1, 100, 10, 24, 50, 4, 5.0, 300.0, 48.0, True),
            SystemState(2, 100, 10, 35, 50, 10, 5.0, 750.0, 70.0, False),
            SystemState(3, 100, 10, 44, 50, 18, 5.0, 1600.0, 88.0, False),
        ],
        "high_latency": [
            SystemState(0, 100, 10, 16, 50, 0, 5.0, 100.0, 32.0, True),
            SystemState(1, 100, 10, 22, 50, 2, 5.0, 400.0, 44.0, True),
            SystemState(2, 100, 10, 32, 50, 6, 5.0, 900.0, 64.0, False),
            SystemState(3, 100, 10, 43, 50, 12, 5.0, 1800.0, 86.0, False),
        ],
        "db_lock_contention": [
            SystemState(0, 100, 10, 16, 50, 0, 5.0, 100.0, 32.0, True),
            SystemState(1, 100, 10, 28, 50, 6, 400.0, 500.0, 56.0, True),
            SystemState(2, 100, 10, 40, 50, 15, 1000.0, 1300.0, 80.0, False),
            SystemState(3, 100, 10, 48, 50, 24, 1800.0, 2200.0, 96.0, False),
        ],
    }

    return scenarios.get(
        failure,
        [
            SystemState(
                step=0,
                requests=100,
                workers=10,
                active_connections=16,
                max_connections=50,
                waiting_transactions=0,
                lock_wait_ms=5.0,
                request_latency_ms=100.0,
                connection_pool_usage_percent=32.0,
                healthy=True,
            ),
            SystemState(
                step=1,
                requests=100,
                workers=10,
                active_connections=20,
                max_connections=50,
                waiting_transactions=1,
                lock_wait_ms=5.0,
                request_latency_ms=150.0,
                connection_pool_usage_percent=40.0,
                healthy=True,
            ),
            SystemState(
                step=2,
                requests=100,
                workers=10,
                active_connections=24,
                max_connections=50,
                waiting_transactions=2,
                lock_wait_ms=5.0,
                request_latency_ms=200.0,
                connection_pool_usage_percent=48.0,
                healthy=True,
            ),
            SystemState(
                step=3,
                requests=100,
                workers=10,
                active_connections=28,
                max_connections=50,
                waiting_transactions=3,
                lock_wait_ms=5.0,
                request_latency_ms=250.0,
                connection_pool_usage_percent=56.0,
                healthy=True,
            ),
        ],
    )


def mitigate_system(state: SystemState) -> SystemState:
    return SystemState(
        step=state.step + 1,
        requests=state.requests,
        workers=state.workers,
        active_connections=16,
        max_connections=state.max_connections,
        waiting_transactions=0,
        lock_wait_ms=5.0,
        request_latency_ms=100.0,
        connection_pool_usage_percent=32.0,
        healthy=True,
    )