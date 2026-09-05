function ReplayPage({
  replay,
  replayStep,
  setReplayStep,
  onBack,
}) {
  if (!replay) {
    return (
      <div className="app">
        <main className="main">
          <section className="hero">
            <h2>Failure Replay</h2>
            <p>No replay data available.</p>

            <button onClick={onBack}>
              Back to Investigation
            </button>
          </section>
        </main>
      </div>
    );
  }

  const currentState = replay.timeline[replayStep];

  const status = [
    {
      title: "HEALTHY",
      description: "System operating normally.",
    },
    {
      title: "DEGRADED",
      description: "Database lock contention begins.",
    },
    {
      title: "CRITICAL",
      description:
        "Waiting transactions increase connection pressure.",
    },
    {
      title: "FAILURE",
      description:
        "Connection pool saturation drives severe application latency.",
    },
  ][replayStep];

  return (
    <div className="app">

      <header className="header">
        <div>
          <h1>PRISM</h1>
          <p>Failure Replay</p>
        </div>

        <div className="status">
          <span className="status-dot"></span>
          Replay Mode
        </div>
      </header>

      <main className="main">

        <section className="hero">

          <button
            className="replay-back-button"
            onClick={onBack}
          >
            ← Back to Investigation
          </button>

          <h2>Failure Replay</h2>

          <p>
            Replay how the failure propagated through the
            system over successive states.
          </p>

        </section>

        <section className="replay-page">

          <div className="replay-panel">

            <div className="replay-header">
              <strong>SYSTEM STATE</strong>

              <span>
                STEP {replayStep + 1} / {replay.timeline.length}
              </span>
            </div>

            <div className="replay-progress">

              {replay.timeline.map((_, index) => (
                <div
                  key={index}
                  className={`replay-progress-step ${
                    index === replayStep
                      ? "active"
                      : ""
                  } ${
                    index < replayStep
                      ? "completed"
                      : ""
                  }`}
                >
                  {index + 1}
                </div>
              ))}

            </div>

            <div className="replay-status">

              <strong>{status.title}</strong>

              <span>
                {status.description}
              </span>

            </div>

            <div className="replay-metrics">

              <div>
                <span>REQUEST LATENCY</span>
                <strong>
                  {currentState.request_latency_ms} ms
                </strong>
              </div>

              <div>
                <span>LOCK WAIT</span>
                <strong>
                  {currentState.lock_wait_ms} ms
                </strong>
              </div>

              <div>
                <span>WAITING TRANSACTIONS</span>
                <strong>
                  {currentState.waiting_transactions}
                </strong>
              </div>

              <div>
                <span>CONNECTION POOL</span>
                <strong>
                  {currentState.connection_pool_usage_percent}%
                </strong>
              </div>

            </div>

            <div className="replay-controls">

              <button
                onClick={() =>
                  setReplayStep(
                    Math.max(0, replayStep - 1)
                  )
                }
                disabled={replayStep === 0}
              >
                Previous
              </button>

              <button
                onClick={() =>
                  setReplayStep(
                    Math.min(
                      replay.timeline.length - 1,
                      replayStep + 1
                    )
                  )
                }
                disabled={
                  replayStep ===
                  replay.timeline.length - 1
                }
              >
                Next
              </button>

            </div>

          </div>

        </section>

      </main>

    </div>
  );
}

export default ReplayPage;