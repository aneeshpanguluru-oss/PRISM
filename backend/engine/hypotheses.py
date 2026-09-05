from dataclasses import dataclass


@dataclass
class Hypothesis:
    name: str
    confidence: float
    reason: str


INITIAL_HYPOTHESES = [
    Hypothesis(
        name="dns_failure",
        confidence=0.15,
        reason="DNS may be preventing the target from being resolved."
    ),
    Hypothesis(
        name="network_connectivity",
        confidence=0.15,
        reason="The target may be unreachable over the network."
    ),
    Hypothesis(
        name="network_latency",
        confidence=0.15,
        reason="The network may be reachable but experiencing high latency."
    ),
    Hypothesis(
        name="service_or_http_failure",
        confidence=0.15,
        reason="The network may work while the application service fails."
    ),
    Hypothesis(
        name="db_connection_exhaustion",
        confidence=0.10,
        reason="The application may be unable to obtain database connections because the connection pool is exhausted."
    ),
    Hypothesis(
        name="db_lock_contention",
        confidence=0.10,
        reason="Database transactions may be waiting on locks, causing increasing database latency and connection pool pressure."
    ),
    Hypothesis(
        name="healthy",
        confidence=0.20,
        reason="The target may be operating normally."
    ),
]