TEST_COSTS = {
    "dns": 1.0,
    "ping": 2.0,
    "http": 3.0,
    "database": 4.0,
}


def get_test_cost(test: str) -> float:
    """Return the relative cost of running a diagnostic test."""
    return TEST_COSTS.get(test, 1.0)