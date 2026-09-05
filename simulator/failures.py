from dataclasses import dataclass


@dataclass
class SimulatedFailure:
    name: str
    description: str


DNS_FAILURE = SimulatedFailure(
    name="dns_failure",
    description="DNS resolution fails."
)

NETWORK_FAILURE = SimulatedFailure(
    name="network_failure",
    description="Network connectivity fails."
)

HTTP_FAILURE = SimulatedFailure(
    name="http_failure",
    description="Network works but the HTTP service fails."
)

HIGH_LATENCY = SimulatedFailure(
    name="high_latency",
    description="Network connectivity works but latency is high."
)

DB_LOCK_CONTENTION = SimulatedFailure(
    name="db_lock_contention",
    description="Database lock contention causes transactions to wait, increasing connection pool pressure and request latency."
)