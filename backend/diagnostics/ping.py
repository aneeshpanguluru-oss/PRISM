import platform
import subprocess
import re

from backend.models.schema import DiagnosticResult


def run_ping(host: str, count: int = 4) -> DiagnosticResult:
    """Run ping and return a structured diagnostic result."""

    system = platform.system().lower()

    if system == "windows":
        command = ["ping", "-n", str(count), host]
    else:
        command = ["ping", "-c", str(count), host]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=15
        )

        output = result.stdout
        reachable = result.returncode == 0

        packet_loss = None
        latency = None

        if system == "windows":
            match = re.search(r"(\d+)%\s*loss", output, re.IGNORECASE)
            if match:
                packet_loss = float(match.group(1))

            match = re.search(
                r"Average\s*=\s*(\d+)\s*ms",
                output,
                re.IGNORECASE
            )
            if match:
                latency = float(match.group(1))

        else:
            match = re.search(
                r"(\d+(?:\.\d+)?)%\s*packet loss",
                output,
                re.IGNORECASE
            )
            if match:
                packet_loss = float(match.group(1))

            match = re.search(r"=\s*[\d.]+/([\d.]+)/", output)
            if match:
                latency = float(match.group(1))

        return DiagnosticResult(
            diagnostic="ping",
            target=host,
            success=reachable,
            metrics={
                "packet_loss_percent": packet_loss,
                "average_latency_ms": latency
            },
            error=None if reachable else "Host unreachable"
        )

    except subprocess.TimeoutExpired:
        return DiagnosticResult(
            diagnostic="ping",
            target=host,
            success=False,
            metrics={
                "packet_loss_percent": 100.0,
                "average_latency_ms": None
            },
            error="Ping timed out"
        )

    except Exception as e:
        return DiagnosticResult(
            diagnostic="ping",
            target=host,
            success=False,
            metrics={},
            error=str(e)
        )