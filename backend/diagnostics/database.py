import psycopg

from backend.models.schema import DiagnosticResult


def check_database(target: str) -> DiagnosticResult:
    """
    Inspect the local PostgreSQL database for active lock contention.

    Returns real PostgreSQL evidence that can be consumed by PRISM's
    investigation engine.
    """

    try:
        with psycopg.connect(
            "dbname=prism user=postgres host=localhost port=5432"
        ) as conn:

            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        count(*) FILTER (
                            WHERE wait_event_type = 'Lock'
                        ) AS waiting_sessions,
                        count(*) FILTER (
                            WHERE state = 'active'
                        ) AS active_sessions
                    FROM pg_stat_activity
                    WHERE datname = 'prism';
                    """
                )

                row = cur.fetchone()

                waiting_sessions = row[0] if row else 0
                active_sessions = row[1] if row else 0

                # Find the oldest currently waiting transaction.
                cur.execute(
                    """
                    SELECT
                        EXTRACT(
                            EPOCH FROM (clock_timestamp() - xact_start)
                        ) * 1000
                    FROM pg_stat_activity
                    WHERE datname = 'prism'
                      AND wait_event_type = 'Lock'
                      AND xact_start IS NOT NULL
                    ORDER BY xact_start
                    LIMIT 1;
                    """
                )

                wait_row = cur.fetchone()

                lock_wait_ms = (
                    float(wait_row[0])
                    if wait_row and wait_row[0] is not None
                    else 0.0
                )

        lock_contention = waiting_sessions > 0

        if lock_contention:
            return DiagnosticResult(
                diagnostic="database",
                target=target,
                success=False,
                metrics={
                    "lock_contention": True,
                    "waiting_transactions": waiting_sessions,
                    "waiting_sessions": waiting_sessions,
                    "active_sessions": active_sessions,
                    "lock_wait_ms": round(lock_wait_ms, 2),
                },
                error="PostgreSQL lock contention detected",
            )

        return DiagnosticResult(
            diagnostic="database",
            target=target,
            success=True,
            metrics={
                "lock_contention": False,
                "waiting_transactions": 0,
                "waiting_sessions": 0,
                "active_sessions": active_sessions,
                "lock_wait_ms": 0.0,
            },
        )

    except Exception as exc:
        return DiagnosticResult(
            diagnostic="database",
            target=target,
            success=False,
            metrics={},
            error=f"PostgreSQL connection failed: {exc}",
        )