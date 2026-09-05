from simulator.failures import (
    DNS_FAILURE,
    NETWORK_FAILURE,
    HTTP_FAILURE,
    HIGH_LATENCY,
    DB_LOCK_CONTENTION,
)


SCENARIOS = {
    "healthy": None,
    "dns_failure": DNS_FAILURE,
    "network_failure": NETWORK_FAILURE,
    "http_failure": HTTP_FAILURE,
    "high_latency": HIGH_LATENCY,
    "db_lock_contention": DB_LOCK_CONTENTION,
}


def get_scenario(name: str):
    """Return a simulated failure scenario."""

    if name not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {name}")

    return SCENARIOS[name]