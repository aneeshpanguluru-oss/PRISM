from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal
from backend.engine.investigator import Investigator
from simulator.system import simulate_system, mitigate_system

app = FastAPI(
    title="Adaptive Network Investigation API",
    description="AI-assisted adaptive network diagnostics",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InvestigationRequest(BaseModel):
    target: str
    failure: Literal[
        "dns_failure",
        "network_failure",
        "http_failure",
        "high_latency",
        "db_lock_contention",
        None
    ] = None

@app.get("/")
def root():
    return {
        "message": "Adaptive Network Investigation API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/investigate/simulated")
def investigate_simulated(request: InvestigationRequest):
    investigator = Investigator()

    report = investigator.run_simulated_investigation(
        target=request.target,
        failure=request.failure
    )

    return report
@app.post("/investigate")

def investigate(request: InvestigationRequest):
    investigator = Investigator()

    report = investigator.run_investigation(
        target=request.target
    )

    return report
@app.post("/replay/simulated")
def replay_simulated(request: InvestigationRequest):
    timeline = simulate_system(request.failure)

    return {
        "target": request.target,
        "failure": request.failure,
        "timeline": [
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
            for state in timeline
        ]
    }