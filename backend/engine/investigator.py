from urllib.parse import urlparse

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
        self.evidence.append(result)
        self._update_hypotheses()

    def _get_hostname(self, target: str) -> str:
        if target.startswith(("http://", "https://")):
            return urlparse(target).hostname or target

        return target.split("/")[0]

    def _is_database_target(self, target: str) -> bool:
        target = target.lower().strip()

        return (
            target.startswith("db://")
            or target.startswith("postgres://")
            or target.startswith("postgresql://")
        )

    def _database_target(self, target: str) -> str:
        if target.startswith("db://"):
            return target[5:]

        return target

    def _get_result(self, diagnostic: str):
        for result in reversed(self.evidence):
            if result.diagnostic == diagnostic:
                return result

        return None

    def _update_hypotheses(self):
        dns = self._get_result("dns")
        ping = self._get_result("ping")
        http = self._get_result("http")
        database = self._get_result("database")

        scores = {
            "dns_failure": 0.15,
            "network_connectivity": 0.15,
            "network_latency": 0.15,
            "service_or_http_failure": 0.15,
            "db_connection_exhaustion": 0.01,
            "db_lock_contention": 0.01,
            "healthy": 0.20,
        }

        if dns:
            if dns.success:
                scores["dns_failure"] *= 0.1
            else:
                scores["dns_failure"] *= 8.0
                scores["healthy"] *= 0.1

        if ping:
            latency = ping.metrics.get("average_latency_ms")

            if ping.success:
                scores["network_connectivity"] *= 0.1

                if latency is not None:
                    if latency > 500:
                        scores["network_latency"] *= 10.0
                        scores["healthy"] *= 0.3

                    elif latency > 200:
                        scores["network_latency"] *= 6.0
                        scores["healthy"] *= 0.5

                    elif latency > 100:
                        scores["network_latency"] *= 2.0

                    else:
                        scores["network_latency"] *= 0.2

            else:
                if http is None:
                    scores["network_connectivity"] *= 8.0
                    scores["network_latency"] *= 0.2
                    scores["healthy"] *= 0.1

        if http:
            status_code = http.metrics.get("status_code")
            response_time = http.metrics.get("response_time_ms")
            error = http.error or ""

            if status_code is not None:

                if 200 <= status_code < 400:
                    scores["network_connectivity"] *= 0.1

                    if response_time is not None:
                        if response_time > 5000:
                            scores["network_latency"] *= 8.0
                            scores["service_or_http_failure"] *= 0.5
                            scores["healthy"] *= 0.1

                        elif response_time > 2000:
                            scores["network_latency"] *= 5.0
                            scores["service_or_http_failure"] *= 0.5
                            scores["healthy"] *= 0.3

                        elif response_time > 500:
                            scores["network_latency"] *= 3.0
                            scores["service_or_http_failure"] *= 0.2
                            scores["healthy"] *= 0.7

                        else:
                            scores["network_latency"] *= 0.2
                            scores["service_or_http_failure"] *= 0.1

                elif 400 <= status_code < 500:
                    scores["network_connectivity"] *= 0.1
                    scores["service_or_http_failure"] *= 8.0
                    scores["healthy"] *= 0.1

                    if response_time is not None and response_time > 2000:
                        scores["service_or_http_failure"] *= 2.0

                elif 500 <= status_code < 600:
                    scores["network_connectivity"] *= 0.1
                    scores["service_or_http_failure"] *= 10.0
                    scores["healthy"] *= 0.1

            elif "timed out" in error.lower():
                scores["service_or_http_failure"] *= 5.0
                scores["network_latency"] *= 3.0
                scores["healthy"] *= 0.1

            elif "connection error" in error.lower():
                scores["network_connectivity"] *= 7.0
                scores["service_or_http_failure"] *= 2.0
                scores["healthy"] *= 0.1

            else:
                scores["service_or_http_failure"] *= 3.0

        if database:
            lock_wait = database.metrics.get("lock_wait_ms", 0)

            waiting_transactions = database.metrics.get(
                "waiting_transactions",
                0
            )

            lock_contention = database.metrics.get(
                "lock_contention",
                False
            )

            pool_usage = database.metrics.get(
                "connection_pool_usage_percent",
                0
            )

            real_lock_evidence = (
                lock_contention is True
                or lock_wait > 500
                or waiting_transactions > 0
            )

            if real_lock_evidence:
                scores["db_lock_contention"] *= 10.0

            if pool_usage > 90:
                scores["db_connection_exhaustion"] *= 4.0

            if (
                database.success
                and not real_lock_evidence
                and pool_usage <= 90
            ):
                scores["db_lock_contention"] *= 0.1
                scores["db_connection_exhaustion"] *= 0.1

            if not database.success:
                if real_lock_evidence:
                    scores["db_lock_contention"] *= 8.0

                if pool_usage > 90:
                    scores["db_connection_exhaustion"] *= 6.0

                if not real_lock_evidence and pool_usage <= 90:
                    scores["db_lock_contention"] *= 0.1
                    scores["db_connection_exhaustion"] *= 0.1

                scores["healthy"] *= 0.1

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

            lock_wait = metrics.get("lock_wait_ms", 0)

            waiting_transactions = metrics.get(
                "waiting_transactions",
                0
            )

            pool_usage = metrics.get(
                "connection_pool_usage_percent"
            )

            lock_contention = metrics.get(
                "lock_contention",
                False
            )

            if (
                lock_contention
                or lock_wait > 500
                or waiting_transactions > 0
            ):
                reasoning = (
                    f"Database lock contention was supported by "
                    f"database evidence: "
                    f"{waiting_transactions} waiting transaction(s), "
                    f"{lock_wait} ms lock wait."
                )

                if pool_usage is not None:
                    reasoning += (
                        f" Connection pool usage reached "
                        f"{pool_usage}%."
                    )

        elif final_diagnosis == "db_connection_exhaustion":
            if database_result:
                pool_usage = database_result.metrics.get(
                    "connection_pool_usage_percent",
                    0
                )

                reasoning = (
                    f"Database connection pressure was detected. "
                    f"Connection pool usage reached {pool_usage}%."
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

    def should_stop(self) -> bool:
        if not self.evidence:
            return False

        completed_tests = {
            result.diagnostic
            for result in self.evidence
        }

        database_result = self._get_result("database")

        if database_result:
            return True

        dns = self._get_result("dns")
        ping = self._get_result("ping")
        http = self._get_result("http")

        if dns and not dns.success:
            return True

        if http:
            status_code = http.metrics.get("status_code")

            if status_code is not None:
                if 500 <= status_code < 600:
                    return True

                if 400 <= status_code < 500:
                    return True

            if http.success:
                return True

        if ping:
            latency = ping.metrics.get("average_latency_ms")

            if latency is not None and latency > 200:
                return False

        if completed_tests >= {"dns", "ping", "http"}:
            return True

        return False

    def choose_next_test(self) -> str | None:
        if self.should_stop():
            return None

        completed_tests = {
            result.diagnostic
            for result in self.evidence
        }

        hypothesis_probabilities = {
            hypothesis.name: hypothesis.confidence
            for hypothesis in self.hypotheses
        }

        available_tests = [
            "dns",
            "ping",
            "http"
        ]

        if not self.evidence:
            available_tests = ["dns"]

        database_result = self._get_result("database")

        if database_result:
            return None

        scores = {
            test: calculate_test_value(
                test=test,
                completed_tests=completed_tests,
                hypotheses=hypothesis_probabilities,
            )
            for test in available_tests
        }

        scores = {
            test: score
            for test, score in scores.items()
            if test not in completed_tests and score > 0
        }

        if not scores:
            return None

        selected_test = max(
            scores,
            key=scores.get
        )

        ping = self._get_result("ping")
        http = self._get_result("http")

        if ping and not ping.success and not http:
            selected_test = "http"

        if ping and ping.success and not http:
            selected_test = "http"

        if selected_test == "ping":
            reason = (
                "DNS resolution succeeded. PING is selected to "
                "measure network reachability and round-trip latency "
                "before testing the application layer."
            )

        elif selected_test == "http":
            if ping and not ping.success:
                reason = (
                    "PING did not establish IP-level reachability. "
                    "HTTP is selected to determine whether the application "
                    "endpoint is reachable and to measure its response behavior."
                )

            elif ping and ping.success:
                reason = (
                    "Network-level evidence is available. HTTP is selected "
                    "to verify application-layer availability and response behavior."
                )

            else:
                reason = (
                    "DNS resolution is available. HTTP is selected to verify "
                    "application-layer availability and response behavior."
                )

        else:
            reason = (
                "DNS resolution provides the highest information "
                "value relative to test cost."
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

        self.reset()

        is_database = self._is_database_target(target)

        if is_database:
            database_target = self._database_target(target)

            result = check_database(database_target)

            self.add_evidence(result)

            return self._build_report(target)

        hostname = self._get_hostname(target)

        while True:
            next_test = self.choose_next_test()

            if next_test is None:
                break

            if next_test == "dns":
                result = run_dns_lookup(hostname)

            elif next_test == "ping":
                result = run_ping(hostname)

            elif next_test == "http":
                result = run_http_check(target)

            else:
                break

            self.add_evidence(result)

        return self._build_report(target)

    def run_simulated_investigation(
        self,
        target: str,
        failure: str | None = None
    ) -> InvestigationReport:

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

        if failure == "db_lock_contention":
            result = simulate_database(target, failure)
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
                "connection_pool_usage_percent": (
                    state.connection_pool_usage_percent
                ),
                "healthy": state.healthy,
            }
            for state in system_states
        ]

        return report

    def get_hypotheses(self) -> list[Hypothesis]:
        return sorted(
            self.hypotheses,
            key=lambda h: h.confidence,
            reverse=True
        )