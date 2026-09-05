from simulator.diagnostics import (
    simulate_dns,
    simulate_ping,
    simulate_http,
)

from backend.models.schema import DiagnosticResult, InvestigationReport


class FixedInvestigator:
    """Run a fixed diagnostic sequence for comparison."""

    def run_simulated_investigation(
        self,
        target: str,
        failure: str | None = None
    ) -> InvestigationReport:
        """Always execute DNS, Ping, and HTTP in that order."""

        evidence: list[DiagnosticResult] = []

        # Fixed sequence: DNS → Ping → HTTP
        evidence.append(simulate_dns(target, failure))
        evidence.append(simulate_ping(target, failure))
        evidence.append(simulate_http(target, failure))

        # Determine diagnosis from the collected evidence.
        dns = next(
            result for result in evidence
            if result.diagnostic == "dns"
        )

        ping = next(
            result for result in evidence
            if result.diagnostic == "ping"
        )

        http = next(
            result for result in evidence
            if result.diagnostic == "http"
        )

        if not dns.success:
            final_diagnosis = "dns_failure"
            reasoning = "DNS resolution failed."

        elif not ping.success:
            final_diagnosis = "network_connectivity"
            reasoning = "Ping failed, suggesting the target is unreachable."

        elif not http.success:
            final_diagnosis = "service_or_http_failure"
            reasoning = "Network connectivity works but HTTP failed."

        elif (
            ping.metrics.get("average_latency_ms") is not None
            and ping.metrics.get("average_latency_ms") > 200
        ):
            final_diagnosis = "network_latency"
            reasoning = (
                f"Ping latency is high at "
                f"{ping.metrics.get('average_latency_ms')} ms."
            )

        else:
            final_diagnosis = "healthy"
            reasoning = (
                "DNS resolution, network connectivity, and "
                "HTTP service checks all succeeded."
            )

        return InvestigationReport(
            target=target,
            tests_executed=[
                result.diagnostic
                for result in evidence
            ],
            evidence=evidence,
            hypotheses=[],
            final_diagnosis=final_diagnosis,
            reasoning=reasoning,
        )