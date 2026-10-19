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

        status_code = response.status_code

        if 200 <= status_code < 400:
            success = True
            error = None

        elif 400 <= status_code < 500:
            success = False
            error = f"HTTP {status_code} - Client or access error"

        elif 500 <= status_code < 600:
            success = False
            error = f"HTTP {status_code} - Server error"

        else:
            success = False
            error = f"HTTP {status_code}"

        return DiagnosticResult(
            diagnostic="http",
            target=url,
            success=success,
            metrics={
                "status_code": status_code,
                "response_time_ms": round(elapsed_ms, 2),
                "final_url": response.url
            },
            error=error
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