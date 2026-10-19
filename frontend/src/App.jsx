import { useState } from "react";
import "./App.css";
import ReplayPage from "./ReplayPage";

function App() {
  const [showReplay, setShowReplay] = useState(false);
  const [target, setTarget] = useState("");
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");
  const [scenario, setScenario] = useState("healthy");
  const [mode, setMode] = useState("simulated");
  const [replay, setReplay] = useState(null);
  const [replayStep, setReplayStep] = useState(0);
  const [replaying, setReplaying] = useState(false);

  const getTimelineStatus = (test) => {
    const evidence = report?.evidence?.find(
      (item) => item.diagnostic === test
    );

    if (!evidence) {
      return {
        type: "pending",
        label: "NOT EXECUTED",
        detail: "Test was not required.",
      };
    }

    if (!evidence.success) {
      return {
        type: "failure",
        label: "FAILURE DETECTED",
        detail: Object.entries(evidence.metrics)
          .map(([key, value]) => `${key}: ${value}`)
          .join(" • "),
      };
    }

    if (
      test === "ping" &&
      evidence.metrics.average_latency_ms > 200
    ) {
      return {
        type: "warning",
        label: "HIGH LATENCY",
        detail: `${evidence.metrics.average_latency_ms} ms`,
      };
    }

    return {
      type: "success",
      label: "PASSED",
      detail: Object.entries(evidence.metrics)
        .map(([key, value]) => `${key}: ${value}`)
        .join(" • "),
    };
  };

  const startInvestigation = async () => {
    if (!target.trim()) {
      setError("Enter a target first.");
      return;
    }

    setLoading(true);
    setError("");
    setReport(null);

    try {
      const response = await fetch(
        mode === "real"
          ? "http://127.0.0.1:8000/investigate"
          : "http://127.0.0.1:8000/investigate/simulated",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            target: target.trim(),
            ...(mode === "simulated" && {
              failure: scenario === "healthy" ? null : scenario,
            }),
          }),
        }
      );

      if (!response.ok) {
        throw new Error(
          `Backend returned HTTP ${response.status}`
        );
      }

      const data = await response.json();
      setReport(data);
    } catch (err) {
      console.error("Investigation error:", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const startReplay = async () => {
    if (!report) return;

    setReplaying(true);
    setReplay(null);
    setReplayStep(0);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/replay/simulated",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            target: report.target,
            failure: scenario === "healthy" ? null : scenario,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(
          `Replay backend returned HTTP ${response.status}`
        );
      }

      const data = await response.json();

      setReplay(data);
      setReplayStep(0);
    } catch (err) {
      console.error("Replay error:", err);
      setError(err.message);
    } finally {
      setReplaying(false);
    }
  };

  if (showReplay) {
    return (
      <ReplayPage
        replay={replay}
        replayStep={replayStep}
        setReplayStep={setReplayStep}
        onBack={() => setShowReplay(false)}
      />
    );
  }

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>PRISM</h1>
          <p>Adaptive Network Investigation</p>
        </div>

        <div className="status">
          <span className="status-dot"></span>
          Backend Ready
        </div>
      </header>

      <main className="main">
        <section className="hero">
          <h2>Investigate a Network Target</h2>

          <p>
            PRISM adaptively selects diagnostic tests based on
            evidence, competing hypotheses, and test cost.
          </p>

          <div className="target-box">
            <input
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              placeholder="Enter a domain or IP"
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  startInvestigation();
                }
              }}
            />

            <select
              value={mode}
              onChange={(e) => setMode(e.target.value)}
            >
              <option value="simulated">SIMULATED</option>
              <option value="real">REAL SYSTEM</option>
            </select>

            {mode === "simulated" && (
              <select
                value={scenario}
                onChange={(e) => setScenario(e.target.value)}
              >
                <option value="healthy">Healthy</option>
                <option value="dns_failure">DNS Failure</option>
                <option value="network_failure">
                  Network Failure
                </option>
                <option value="http_failure">
                  HTTP Failure
                </option>
                <option value="high_latency">
                  High Latency
                </option>
                <option value="db_lock_contention">
                  DB Lock Contention
                </option>
              </select>
            )}

            <button
              onClick={startInvestigation}
              disabled={loading}
            >
              {loading
                ? "Investigating..."
                : "Start Investigation"}
            </button>
          </div>

          {error && (
            <p
              style={{
                color: "#ff7b7b",
                marginTop: "15px",
              }}
            >
              {error}
            </p>
          )}
        </section>

        <section className="dashboard">
          {/* LEFT COLUMN */}
          <div className="card">
            <h3>Investigation</h3>

            {!report && !loading && (
              <div className="empty-state">
                <div className="large-icon">⌁</div>

                <p>No investigation running</p>

                <span>
                  Enter a target above to begin.
                </span>
              </div>
            )}

            {loading && (
              <div className="empty-state">
                <div className="large-icon">⌁</div>

                <p>Investigation in progress...</p>

                <span>
                  PRISM is selecting diagnostic tests.
                </span>
              </div>
            )}

            {report && (
              <div className="result-panel">
              {/* FINAL DIAGNOSIS */}
              <div className="diagnosis-box">
                <span className="result-label">
                  FINAL DIAGNOSIS
                </span>

                <h4>
                  {report.final_diagnosis.replaceAll("_", " ")}
                </h4>

                <p>{report.reasoning}</p>

                <div className="diagnosis-chain">
                  <span className="result-label">
                    CAUSAL CHAIN
                  </span>

                  <div className="chain">
                    <span className="chain-node">TARGET</span>

                    <span className="chain-arrow">→</span>

                    <span className="chain-node">NETWORK</span>

                    <span className="chain-arrow">→</span>

                    <span className="chain-node">APPLICATION</span>

                    <span className="chain-arrow">→</span>

                    <span className="chain-node">DATABASE</span>

                    <span className="chain-arrow">→</span>

                    <span className="chain-node final">
                      {report.final_diagnosis.replaceAll("_", " ")}
                    </span>
                  </div>
                </div>

                {mode === "simulated" && (
                  <button
                    className="replay-button"
                    onClick={async () => {
                      await startReplay();
                      setShowReplay(true);
                    }}
                    disabled={replaying}
                  >
                    {replaying
                      ? "Preparing Replay..."
                      : "Replay Failure"}
                  </button>
                )}
              </div>

                {/* TARGET + TEST SEQUENCE */}
                <div className="result-row">
                  <div>
                    <span className="result-label">
                      TARGET
                    </span>

                    <strong>{report.target}</strong>
                  </div>

                  <div>
                    <span className="result-label">
                      TESTS EXECUTED
                    </span>

                    <strong>
                      {report.tests_executed.join(" → ")}
                    </strong>
                  </div>
                </div>

                {/* EVIDENCE */}
                <div className="evidence-section">
                  <span className="result-label">
                    EVIDENCE
                  </span>

                  {report.evidence.map((result) => (
                    <div
                      className="evidence-card"
                      key={result.diagnostic}
                    >
                      <div className="evidence-header">
                        <strong>
                          {result.diagnostic.toUpperCase()}
                        </strong>

                        <span
                          className={
                            result.success
                              ? "evidence-success"
                              : "evidence-failure"
                          }
                        >
                          {result.success
                            ? "PASSED"
                            : "FAILED"}
                        </span>
                      </div>

                      <div className="evidence-metrics">
                        {Object.entries(result.metrics).map(
                          ([key, value]) => (
                            <div key={key}>
                              <span>
                                {key.replaceAll(
                                  "_",
                                  " "
                                )}
                              </span>

                              <strong>
                                {Array.isArray(value)
                                  ? value.join(", ")
                                  : String(value)}
                              </strong>
                            </div>
                          )
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {/* FAILURE PATH */}
                <div className="failure-path">
                  {/* TARGET */}
                  <div className="path-node">
                    <div className="path-icon">T</div>
                    <strong>TARGET</strong>
                    <span>{report.target}</span>
                  </div>

                  <div className="path-line"></div>

                  {/* DNS */}
                  <div
                    className={`path-node ${
                      report.tests_executed.includes("dns")
                        ? report.evidence.find(
                            (e) => e.diagnostic === "dns"
                          )?.success
                          ? "success"
                          : "failure"
                        : "skipped"
                    }`}
                  >
                    <div className="path-icon">D</div>
                    <strong>DNS</strong>

                    <span>
                      {report.tests_executed.includes("dns")
                        ? report.evidence.find(
                            (e) => e.diagnostic === "dns"
                          )?.success
                          ? "RESOLVED"
                          : "FAILED"
                        : "NOT TESTED"}
                    </span>
                  </div>

                  <div className="path-line"></div>

                  {/* HTTP */}
                  <div
                    className={`path-node ${
                      !report.tests_executed.includes("http")
                        ? "skipped"
                        : report.evidence.find(
                            (e) => e.diagnostic === "http"
                          )?.success
                          ? "success"
                          : "failure"
                    }`}
                  >
                    <div className="path-icon">H</div>
                    <strong>HTTP</strong>

                    <span>
                      {!report.tests_executed.includes("http")
                        ? "NOT TESTED"
                        : report.evidence.find(
                            (e) => e.diagnostic === "http"
                          )?.success
                          ? "HEALTHY"
                          : "FAILED"}
                    </span>
                  </div>

                  <div className="path-line"></div>

                  {/* DATABASE */}
                  <div
                    className={`path-node ${
                      !report.tests_executed.includes(
                        "database"
                      )
                        ? "skipped"
                        : report.evidence.find(
                            (e) =>
                              e.diagnostic ===
                              "database"
                          )?.success
                          ? "success"
                          : "failure"
                    }`}
                  >
                    <div className="path-icon">DB</div>
                    <strong>DATABASE</strong>

                    <span>
                      {!report.tests_executed.includes(
                        "database"
                      )
                        ? "NOT TESTED"
                        : report.evidence.find(
                            (e) =>
                              e.diagnostic ===
                              "database"
                          )?.success
                          ? "HEALTHY"
                          : report.evidence.find(
                              (e) =>
                                e.diagnostic ===
                                "database"
                            )?.metrics
                                ?.lock_contention
                          ? "LOCK CONTENTION"
                          : "FAILED"}
                    </span>
                  </div>
                </div>

                {/* INVESTIGATION TIMELINE */}
                <div className="timeline-section">
                  <span className="result-label">
                    INVESTIGATION TIMELINE
                  </span>

                  <div className="timeline">
                    {report.tests_executed.map(
                      (test, index) => {
                        const status =
                          getTimelineStatus(test);

                        return (
                          <div
                            className={`timeline-item ${status.type}`}
                            key={test}
                          >
                            <div className="timeline-marker">
                              {status.type === "failure"
                                ? "!"
                                : status.type ===
                                  "warning"
                                ? "!"
                                : index + 1}
                            </div>

                            <div className="timeline-content">
                              <strong>
                                {test.toUpperCase()}
                              </strong>

                              <span
                                className={`timeline-status ${status.type}`}
                              >
                                {status.label}
                              </span>

                              <span className="timeline-detail">
                                {status.detail}
                              </span>
                            </div>
                          </div>
                        );
                      }
                    )}

                    <div className="timeline-item final">
                      <div className="timeline-marker">
                        ✓
                      </div>

                      <div className="timeline-content">
                        <strong>
                          FAILURE LOCALIZED
                        </strong>

                        <span className="timeline-diagnosis">
                          {report.final_diagnosis.replaceAll(
                            "_",
                            " "
                          )}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* INVESTIGATION TRACE */}
                <div className="trace-section">
                  <span className="result-label">
                    INVESTIGATION TRACE
                  </span>

                  {report.investigation_trace.map(
                    (trace) => (
                      <div
                        className="trace-step"
                        key={trace.step}
                      >
                        <div className="trace-header">
                          <div className="trace-step-number">
                            STEP {trace.step}
                          </div>

                          <div className="trace-selected">
                            Selected:{" "}
                            <strong>
                              {trace.selected_test.toUpperCase()}
                            </strong>
                          </div>
                        </div>

                        <div className="trace-reason">
                          {trace.reason}
                        </div>

                        <div className="trace-tests">
                          {Object.entries(
                            trace.available_tests
                          ).map(
                            ([test, score]) => (
                              <div
                                className={
                                  test ===
                                  trace.selected_test
                                    ? "trace-test selected"
                                    : "trace-test"
                                }
                                key={test}
                              >
                                <span>
                                  {test.toUpperCase()}
                                </span>

                                <div className="trace-test-details">
                                  <strong>
                                    {score.toFixed(2)}
                                  </strong>

                                  <span>
                                    Cost:{" "}
                                    {trace.test_costs?.[
                                      test
                                    ] ?? "-"}
                                  </span>
                                </div>
                              </div>
                            )
                          )}
                        </div>
                      </div>
                    )
                  )}
                </div>
              </div>
            )}
          </div>

          {/* RIGHT COLUMN */}
          <div className="card">
            <h3>Current Hypotheses</h3>

            {report ? (
              report.hypotheses.map((hypothesis) => (
                <div
                  className="hypothesis"
                  key={hypothesis.name}
                >
                  <div>
                    <span>{hypothesis.name}</span>

                    <strong>
                      {Math.round(
                        hypothesis.confidence * 100
                      )}
                      %
                    </strong>
                  </div>

                  <div className="bar">
                    <div
                      className="fill"
                      style={{
                        width: `${
                          hypothesis.confidence * 100
                        }%`,
                      }}
                    ></div>
                  </div>
                </div>
              ))
            ) : (
              <>
                {[
                  ["DNS Failure", 20],
                  ["Network Connectivity", 20],
                  ["Network Latency", 20],
                  ["Service / HTTP Failure", 20],
                  ["Healthy", 20],
                ].map(([name, confidence]) => (
                  <div
                    className="hypothesis"
                    key={name}
                  >
                    <div>
                      <span>{name}</span>

                      <strong>
                        {confidence}%
                      </strong>
                    </div>

                    <div className="bar">
                      <div
                        className="fill"
                        style={{
                          width: `${confidence}%`,
                        }}
                      ></div>
                    </div>
                  </div>
                ))}
              </>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;