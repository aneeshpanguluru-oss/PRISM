from backend.engine.investigator import Investigator
from backend.engine.baseline import FixedInvestigator


SCENARIOS = {
    "healthy": None,
    "dns_failure": "dns_failure",
    "network_failure": "network_failure",
    "http_failure": "http_failure",
    "high_latency": "high_latency",
}


def evaluate():
    adaptive = Investigator()
    fixed = FixedInvestigator()

    adaptive_tests = 0
    fixed_tests = 0
    adaptive_correct = 0
    fixed_correct = 0

    print("\nPRISM Evaluation")
    print("=" * 60)

    for scenario, failure in SCENARIOS.items():

        expected = {
            "healthy": "healthy",
            "dns_failure": "dns_failure",
            "network_failure": "network_connectivity",
            "http_failure": "service_or_http_failure",
            "high_latency": "network_latency",
        }[scenario]

        adaptive_report = adaptive.run_simulated_investigation(
            target="test.local",
            failure=failure,
        )

        fixed_report = fixed.run_simulated_investigation(
            target="test.local",
            failure=failure,
        )

        adaptive_count = len(adaptive_report.tests_executed)
        fixed_count = len(fixed_report.tests_executed)

        adaptive_tests += adaptive_count
        fixed_tests += fixed_count

        if adaptive_report.final_diagnosis == expected:
            adaptive_correct += 1

        if fixed_report.final_diagnosis == expected:
            fixed_correct += 1

        print(
            f"{scenario:18}"
            f" Adaptive={adaptive_count}"
            f" Fixed={fixed_count}"
            f" Diagnosis={adaptive_report.final_diagnosis}"
        )

    test_reduction = (
        (fixed_tests - adaptive_tests)
        / fixed_tests
        * 100
    )

    adaptive_accuracy = (
        adaptive_correct
        / len(SCENARIOS)
        * 100
    )

    fixed_accuracy = (
        fixed_correct
        / len(SCENARIOS)
        * 100
    )

    print("\n" + "=" * 60)
    print(f"Adaptive tests:       {adaptive_tests}")
    print(f"Fixed tests:          {fixed_tests}")
    print(f"Test reduction:       {test_reduction:.1f}%")
    print(f"Adaptive accuracy:    {adaptive_accuracy:.1f}%")
    print(f"Fixed accuracy:       {fixed_accuracy:.1f}%")


if __name__ == "__main__":
    evaluate()