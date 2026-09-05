import socket
import time

from backend.models.schema import DiagnosticResult


def run_dns_lookup(host: str) -> DiagnosticResult:
    """Resolve a hostname and return a structured diagnostic result."""

    start_time = time.perf_counter()

    try:
        addresses = socket.getaddrinfo(host, None)

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        ip_addresses = sorted({
            address[4][0]
            for address in addresses
        })

        return DiagnosticResult(
            diagnostic="dns",
            target=host,
            success=True,
            metrics={
                "ip_addresses": ip_addresses,
                "resolution_time_ms": round(elapsed_ms, 2)
            }
        )

    except socket.gaierror as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return DiagnosticResult(
            diagnostic="dns",
            target=host,
            success=False,
            metrics={
                "ip_addresses": [],
                "resolution_time_ms": round(elapsed_ms, 2)
            },
            error=str(e)
        )

    except Exception as e:
        return DiagnosticResult(
            diagnostic="dns",
            target=host,
            success=False,
            metrics={},
            error=str(e)
        )