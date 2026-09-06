import time
import requests

from backend.models.schema import DiagnosticResult


def run_http_check(url: str) -> DiagnosticResult:
    """Check HTTP/HTTPS availability and return a structured result."""

    if not url.startswith(("http://", "https://")):
        if url in ("localhost", "127.0.0.1"):
            url = "http://" + url
        else:
            url = "https://" + url

    start_time = time.perf_counter()

    try:
        response = requests.get(
            url,
            timeout=10,
            allow_redirects=True
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return DiagnosticResult(
            diagnostic="http",
            target=url,
            success=response.ok,
            metrics={
                "status_code": response.status_code,
                "response_time_ms": round(elapsed_ms, 2),
                "final_url": response.url
            },
            error=None if response.ok else f"HTTP {response.status_code}"
        )

    except requests.exceptions.Timeout:
        return DiagnosticResult(
            diagnostic="http",
            target=url,
            success=False,
            metrics={},
            error="HTTP request timed out"
        )

    except requests.exceptions.ConnectionError as e:
        return DiagnosticResult(
            diagnostic="http",
            target=url,
            success=False,
            metrics={},
            error=f"Connection error: {e}"
        )

    except requests.exceptions.RequestException as e:
        return DiagnosticResult(
            diagnostic="http",
            target=url,
            success=False,
            metrics={},
            error=str(e)
        )