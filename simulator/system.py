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
    """
    Simulate the application stack over several investigation steps.

    DB lock contention creates a cascading effect:
    lock wait -> waiting transactions -> connection pressure
    -> increased request latency.
    """

    if failure == "db_lock_contention":
        return [
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
                active_connections=28,
                max_connections=50,
                waiting_transactions=6,
                lock_wait_ms=400.0,
                request_latency_ms=500.0,
                connection_pool_usage_percent=56.0,
                healthy=True,
            ),
            SystemState(
                step=2,
                requests=100,
                workers=10,
                active_connections=40,
                max_connections=50,
                waiting_transactions=15,
                lock_wait_ms=1000.0,
                request_latency_ms=1300.0,
                connection_pool_usage_percent=80.0,
                healthy=False,
            ),
            SystemState(
                step=3,
                requests=100,
                workers=10,
                active_connections=48,
                max_connections=50,
                waiting_transactions=24,
                lock_wait_ms=1800.0,
                request_latency_ms=2200.0,
                connection_pool_usage_percent=96.0,
                healthy=False,
            ),
        ]

    return [
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
        )
    ]
def mitigate_system(state: SystemState) -> SystemState:
    """
    Simulate mitigation of database lock contention.

    The intervention reduces lock wait and releases pressure
    on the connection pool, allowing application latency to recover.
    """

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