from simulator.diagnostics import (
    simulate_dns,
    simulate_ping,
    simulate_http,
    simulate_database,
)
from backend.diagnostics.database import check_database
from simulator.system import simulate_system
from backend.diagnostics.dns import run_dns_lookup
from backend.diagnostics.ping import run_ping
from backend.diagnostics.http import run_http_check
from backend.models.schema import DiagnosticResult, InvestigationReport
from backend.engine.hypotheses import Hypothesis, INITIAL_HYPOTHESES
from backend.engine.decision import calculate_test_value
from backend.engine.costs import get_test_cost
class Investigator:

    def __init__(self):
        self.evidence: list[DiagnosticResult] = []
        self.hypotheses: list[Hypothesis] = [
            Hypothesis(
                name=h.name,
                confidence=h.confidence,
                reason=h.reason
            )
            for h in INITIAL_HYPOTHESES
        ]
        self.investigation_trace: list[dict] = []

    def add_evidence(self, result: DiagnosticResult):
        """Add a diagnostic result and update hypotheses."""

        self.evidence.append(result)
        self._update_hypotheses()

    def _update_hypotheses(self):
        """Update hypothesis confidence from collected evidence."""

        dns = self._get_result("dns")
        ping = self._get_result("ping")
        http = self._get_result("http")
        database = self._get_result("database")

        scores = {
                "dns_failure": 0.15,
                "network_connectivity": 0.15,
                "network_latency": 0.15,
                "service_or_http_failure": 0.15,
                "db_connection_exhaustion": 0.10,
                "db_lock_contention": 0.10,
                "healthy": 0.20,
                }

        # DNS evidence
        if dns:
            if dns.success:
                scores["dns_failure"] *= 0.1
            else:
                scores["dns_failure"] *= 8.0

        # Ping evidence
        if ping:
            if not ping.success:
                scores["network_connectivity"] *= 8.0
                scores["network_latency"] *= 0.2
                scores["service_or_http_failure"] *= 0.2
                scores["healthy"] *= 0.1

            else:
                scores["network_connectivity"] *= 0.1

                latency = ping.metrics.get("average_latency_ms")

                if latency is not None and latency > 200:
                    scores["network_latency"] *= 8.0
                    scores["healthy"] *= 0.3
                else:
                    scores["network_latency"] *= 0.2

        # HTTP evidence
        if http:
            if not http.success:
                scores["service_or_http_failure"] *= 8.0
                scores["healthy"] *= 0.1
            else:
                scores["service_or_http_failure"] *= 0.1

                response_time = http.metrics.get("response_time_ms")

                if response_time is not None and response_time > 500:
                    scores["service_or_http_failure"] *= 2.0
                    if response_time is not None and response_time > 1000:
                        scores["db_lock_contention"] *= 3.0
                        scores["db_connection_exhaustion"] *= 2.0

                # Database evidence
        if database:
            if not database.success:
                lock_wait = database.metrics.get("lock_wait_ms", 0)
                waiting_transactions = database.metrics.get(
                    "waiting_transactions", 0
                )
                lock_contention = database.metrics.get(
                    "lock_contention", False
                )
                pool_usage = database.metrics.get(
                    "connection_pool_usage_percent", 0
                )

                # Real PostgreSQL lock evidence
                if lock_contention:
                    scores["db_lock_contention"] *= 10.0

                if lock_wait > 500:
                    scores["db_lock_contention"] *= 8.0

                if waiting_transactions > 0:
                    scores["db_lock_contention"] *= 4.0

                # Simulator-specific connection pool evidence
                if pool_usage > 90:
                    scores["db_connection_exhaustion"] *= 4.0
                    scores["db_lock_contention"] *= 2.0

                scores["healthy"] *= 0.1

            else:
                scores["db_lock_contention"] *= 0.2
                scores["db_connection_exhaustion"] *= 0.2

        # Normalize scores into probabilities.
        total = sum(scores.values())

        self.hypotheses = [
            Hypothesis(
                name=name,
                confidence=round(score / total, 3),
                reason=f"Evidence-adjusted confidence for {name}."
            )
            for name, score in scores.items()
        ]

    def _build_report(self, target: str) -> InvestigationReport:
        """Build a structured investigation report."""

        hypotheses = self.get_hypotheses()

        if hypotheses:
            final_diagnosis = hypotheses[0].name
            reasoning = hypotheses[0].reason
        else:
            final_diagnosis = "healthy"
            reasoning = (
                "DNS resolution, network connectivity, and "
                "HTTP service checks all succeeded."
            )

        # Build a causal explanation from observed database evidence.
        database_result = next(
            (
                result
                for result in self.evidence
                if result.diagnostic == "database"
            ),
            None
        )

        if final_diagnosis == "db_lock_contention" and database_result:
            metrics = database_result.metrics

            lock_wait = metrics.get("lock_wait_ms")
            waiting_transactions = metrics.get("waiting_transactions")

            pool_usage = metrics.get(
                "connection_pool_usage_percent"
            )

            if pool_usage is not None:
                reasoning = (
                    f"Database lock contention caused transactions to wait "
                    f"({waiting_transactions} waiting transactions, "
                    f"{lock_wait} ms lock wait). "
                    f"This increased connection pool usage to "
                    f"{pool_usage}%, contributing to increased "
                    f"application latency."
                )
            else:
                reasoning = (
                    f"PostgreSQL reported active lock contention with "
                    f"{waiting_transactions} waiting transaction(s) and "
                    f"{lock_wait} ms lock wait. "
                    f"The database contention is the strongest observed "
                    f"explanation for the failure."
                )

        return InvestigationReport(
            target=target,
            tests_executed=[
                result.diagnostic
                for result in self.evidence
            ],
            evidence=self.evidence,
            hypotheses=[
                {
                    "name": hypothesis.name,
                    "confidence": hypothesis.confidence,
                    "reason": hypothesis.reason
                }
                for hypothesis in hypotheses
            ],
            final_diagnosis=final_diagnosis,
            reasoning=reasoning,
            investigation_trace=self.investigation_trace
        )
    def reset(self):
        """Reset the investigation to the initial uncertain state."""

        self.evidence = []

        self.hypotheses = [
            Hypothesis(
                name=h.name,
                confidence=h.confidence,
                reason=h.reason
            )
            for h in INITIAL_HYPOTHESES
        ]

        self.investigation_trace = []
            
    def _get_result(self, diagnostic: str):
        """Find the latest result for a diagnostic."""

        for result in reversed(self.evidence):
            if result.diagnostic == diagnostic:
                return result

        return None

    def should_stop(self) -> bool:
        """Decide whether the current evidence is sufficient."""

        if not self.evidence:
            return False

        completed_tests = {
            result.diagnostic
            for result in self.evidence
        }

        available_tests = {"dns", "ping", "http", "database"}

        # Nothing else to investigate.
        if completed_tests >= available_tests:
            return True

        dns = self._get_result("dns")
        ping = self._get_result("ping")
        http = self._get_result("http")
        database = self._get_result("database")

        # DNS failure already explains why the target cannot
        # be reached at the application level.
        if dns and not dns.success:
            return True

        # Network failure already explains the connectivity problem.
        if ping and not ping.success:
            return True

        # HTTP failure requires no further test in our current
        # diagnostic model.
        if http and not http.success:
            return True
        # Database failure provides sufficient evidence for a database diagnosis.
        if database and not database.success:
            return True
        # High latency is already directly observable from ping.
        if ping:
            latency = ping.metrics.get("average_latency_ms")

            if latency is not None and latency > 200:
                return True

        return False

    def choose_next_test(self) -> str | None:
        """Choose the next diagnostic using information value per cost."""

        if self.should_stop():
            return None

        available_tests = ["dns", "ping", "http", "database"]

        completed_tests = {
            result.diagnostic
            for result in self.evidence
        }

        hypothesis_probabilities = {
            hypothesis.name: hypothesis.confidence
            for hypothesis in self.hypotheses
        }

        scores = {
            test: calculate_test_value(
                test=test,
                completed_tests=completed_tests,
                hypotheses=hypothesis_probabilities,
            )
            for test in available_tests
        }
        if "database" in completed_tests:
            scores["database"] = 0.0

        scores = {
            test: score
            for test, score in scores.items()
            if score > 0
        }

        if not scores:
            return None

        selected_test = max(scores, key=scores.get)

        # Generate a human-readable explanation for the decision.
        if not completed_tests:
            reason = (
                "No diagnostic evidence is available yet, so DNS "
                "provides the highest information value relative to cost."
            )

        elif selected_test == "ping":
            dns = self._get_result("dns")

            if dns and dns.success:
                reason = (
                    "DNS succeeded, reducing the likelihood of a DNS "
                    "failure. Network connectivity is therefore the "
                    "next most informative test."
                )
            else:
                reason = (
                    "Network connectivity provides the highest remaining "
                    "diagnostic value relative to test cost."
                )

        elif selected_test == "http":
            ping = self._get_result("ping")

            if ping and ping.success:
                latency = ping.metrics.get("average_latency_ms")

                if latency is not None and latency > 200:
                    reason = (
                        "Network connectivity is established, but latency "
                        "is elevated. HTTP verification provides the highest "
                        "remaining diagnostic value."
                    )
                else:
                    reason = (
                        "Network connectivity is established. HTTP "
                        "verification is the remaining application-layer "
                        "diagnostic."
                    )
            else:
                reason = (
                    "HTTP provides the highest remaining information value "
                    "relative to test cost."
                )

        elif selected_test == "dns":
            reason = (
                "DNS resolution provides the highest remaining "
                "information value relative to test cost."
            )

        else:
            reason = (
                "This diagnostic provides the highest information value "
                "relative to its execution cost."
            )

        self.investigation_trace.append({
            "step": len(self.investigation_trace) + 1,
            "available_tests": scores,
            "test_costs": {
                test: get_test_cost(test)
                for test in scores
            },
            "selected_test": selected_test,
            "reason": reason,
            "hypotheses": [
                {
                    "name": hypothesis.name,
                    "confidence": hypothesis.confidence,
                }
                for hypothesis in self.get_hypotheses()
            ],
        })
        return selected_test
    
    def run_investigation(
        self,
        target: str
    ) -> InvestigationReport:
        """Run an adaptive investigation using real diagnostics."""

        self.reset()

        while True:
            next_test = self.choose_next_test()

            if next_test is None:
                break

            if next_test == "dns":
                result = run_dns_lookup(target)

            elif next_test == "ping":
                result = run_ping(target)

            elif next_test == "http":
                result = run_http_check(target)
            elif next_test == "database":
                result = check_database(target)
            else:
                break

            self.add_evidence(result)

        return self._build_report(target)

    def run_simulated_investigation(
            self,
            target: str,
            failure: str | None = None
        ) -> InvestigationReport:
        """Run an adaptive investigation using simulated diagnostics."""

        self.reset()

        system_states = simulate_system(failure)

        while True:
            next_test = self.choose_next_test()

            if next_test is None:
                break

            if next_test == "dns":
                result = simulate_dns(target, failure)

            elif next_test == "ping":
                result = simulate_ping(target, failure)

            elif next_test == "http":
                result = simulate_http(target, failure)

            elif next_test == "database":
                result = simulate_database(target, failure)

            else:
                break

            self.add_evidence(result)

        report = self._build_report(target)

        report.system_timeline = [
            {
                "step": state.step,
                "requests": state.requests,
                "workers": state.workers,
                "active_connections": state.active_connections,
                "max_connections": state.max_connections,
                "waiting_transactions": state.waiting_transactions,
                "lock_wait_ms": state.lock_wait_ms,
                "request_latency_ms": state.request_latency_ms,
                "connection_pool_usage_percent": state.connection_pool_usage_percent,
                "healthy": state.healthy,
            }
            for state in system_states
        ]

        return report

    def get_hypotheses(self) -> list[Hypothesis]:
        """Return hypotheses sorted by confidence."""

        return sorted(
            self.hypotheses,
            key=lambda h: h.confidence,
            reverse=True
        )