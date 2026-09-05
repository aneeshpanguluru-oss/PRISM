import math

from backend.engine.costs import get_test_cost


TEST_OUTCOMES = {
    "dns": ["success", "failure"],
    "ping": ["success", "failure"],
    "http": ["success", "failure"],
    "database": ["success", "failure"],
}


def entropy(probabilities: list[float]) -> float:
    """Calculate Shannon entropy for a probability distribution."""

    return -sum(
        p * math.log2(p)
        for p in probabilities
        if p > 0
    )


def calculate_test_value(
    test: str,
    completed_tests: set[str],
    hypotheses: dict[str, float],
) -> float:
    """
    Estimate diagnostic value using uncertainty reduction
    relative to the cost of the test.
    """

    if test in completed_tests:
        return 0.0

    if not hypotheses:
        return 0.0

    # Current uncertainty across competing hypotheses.
    probabilities = list(hypotheses.values())
    current_entropy = entropy(probabilities)

    # Map hypotheses to the diagnostic they are most associated with.
    hypothesis_test_map = {
        "dns_failure": "dns",
        "network_connectivity": "ping",
        "network_latency": "ping",
        "service_or_http_failure": "http",
        "db_connection_exhaustion": "database",
        "db_lock_contention": "database",
        "healthy": None,
    }

    # Estimate how strongly this test separates the hypotheses.
    relevant_probability = sum(
        probability
        for name, probability in hypotheses.items()
        if hypothesis_test_map.get(name) == test
    )

    # A diagnostic is most useful when the outcome can divide
    # the current uncertainty into meaningful alternatives.
    if test == "dns":
        outcome_balance = (
            4 * relevant_probability * (1 - relevant_probability)
        )

    elif test == "ping":
        outcome_balance = (
            4 * relevant_probability * (1 - relevant_probability)
        )

    elif test == "http":
        outcome_balance = (
        4 * relevant_probability * (1 - relevant_probability)
    )

    elif test == "database":
        outcome_balance = (4 * relevant_probability * (1 - relevant_probability))

    else:
        outcome_balance = 0.0

    # Combine current uncertainty with the diagnostic's
    # ability to distinguish competing explanations.
    information_gain = current_entropy * outcome_balance

    cost = get_test_cost(test)

    return information_gain / cost