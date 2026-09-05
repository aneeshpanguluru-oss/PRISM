from backend.models.schema import DiagnosticResult


def simulate_dns(target: str, failure=None) -> DiagnosticResult:
    if failure == "dns_failure":
        return DiagnosticResult(
            diagnostic="dns",
            target=target,
            success=False,
            metrics={
                "ip_addresses": [],
                "resolution_time_ms": 50.0
            },
            error="Simulated DNS failure"
        )

    return DiagnosticResult(
        diagnostic="dns",
        target=target,
        success=True,
        metrics={
            "ip_addresses": ["192.0.2.1"],
            "resolution_time_ms": 10.0
        }
    )


def simulate_ping(target: str, failure=None) -> DiagnosticResult:
    if failure == "network_failure":
        return DiagnosticResult(
            diagnostic="ping",
            target=target,
            success=False,
            metrics={
                "packet_loss_percent": 100.0,
                "average_latency_ms": None
            },
            error="Simulated network failure"
        )

    if failure == "high_latency":
        return DiagnosticResult(
            diagnostic="ping",
            target=target,
            success=True,
            metrics={
                "packet_loss_percent": 0.0,
                "average_latency_ms": 350.0
            }
        )

    return DiagnosticResult(
        diagnostic="ping",
        target=target,
        success=True,
        metrics={
            "packet_loss_percent": 0.0,
            "average_latency_ms": 30.0
        }
    )


def simulate_http(target: str, failure=None) -> DiagnosticResult:
    if failure == "db_lock_contention":
        return DiagnosticResult(
            diagnostic="http",
            target=target,
            success=True,
            metrics={
                "status_code": 200,
                "response_time_ms": 2200.0
            }
        )

    if failure == "http_failure":
        return DiagnosticResult(
            diagnostic="http",
            target=target,
            success=False,
            metrics={
                "status_code": 503,
                "response_time_ms": 100.0
            },
            error="Simulated HTTP 503"
        )

    return DiagnosticResult(
        diagnostic="http",
        target=target,
        success=True,
        metrics={
            "status_code": 200,
            "response_time_ms": 100.0
        }
    )


def simulate_database(target: str, failure=None) -> DiagnosticResult:
    if failure == "db_lock_contention":
        return DiagnosticResult(
            diagnostic="database",
            target=target,
            success=False,
            metrics={
                "lock_wait_ms": 1800.0,
                "waiting_transactions": 24,
                "connection_pool_usage_percent": 96.0,
                "active_connections": 48,
                "max_connections": 50
            },
            error="Simulated database lock contention"
        )

    return DiagnosticResult(
        diagnostic="database",
        target=target,
        success=True,
        metrics={
            "lock_wait_ms": 5.0,
            "waiting_transactions": 0,
            "connection_pool_usage_percent": 32.0,
            "active_connections": 16,
            "max_connections": 50
        }
    )