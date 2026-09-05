PRISM — Adaptive Network Investigation

PRISM is an adaptive network and distributed-system investigation framework.

Instead of running a fixed sequence of diagnostic tests, PRISM maintains competing hypotheses about a failure and selects the next diagnostic based on the expected diagnostic value of the test.

The system is designed to answer:

What should we test next, and when do we have enough evidence to stop?

Core Idea

Traditional troubleshooting often follows a fixed sequence:

DNS
 ↓
Ping
 ↓
HTTP
 ↓
Diagnosis

PRISM treats troubleshooting as a sequential investigation:

Target
  ↓
Initial hypotheses
  ↓
Select most informative test
  ↓
Run diagnostic
  ↓
Collect evidence
  ↓
Update hypotheses
  ↓
Select next test
  ↓
Stop when sufficient evidence exists
  ↓
Diagnosis

This allows PRISM to avoid unnecessary diagnostic tests when earlier evidence already strongly supports a diagnosis.

Features

Adaptive diagnostic test selection

Competing failure hypotheses

Evidence-based hypothesis updates

DNS diagnostics

Network connectivity diagnostics

HTTP diagnostics

Database diagnostic simulation

Controlled failure scenarios

Failure replay

System-state timeline visualization

Investigation trace

Diagnostic cost tracking

FastAPI backend

React/Vite frontend

Deterministic evaluation benchmark

Architecture

                    ┌─────────────────────┐
                    │      React UI       │
                    │     Frontend        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      FastAPI        │
                    │      Backend        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Investigation     │
                    │      Engine         │
                    └──────────┬──────────┘
                               │
                 ┌─────────────┼─────────────┐
                 ▼             ▼             ▼
              Hypotheses    Decision      Evidence
                             Engine
                 │             │             │
                 └─────────────┼─────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     Diagnostics     │
                    ├─────────────────────┤
                    │ DNS                 │
                    │ Ping                │
                    │ HTTP                │
                    │ Database Simulator   │
                    └─────────────────────┘

Project Structure

C2C/
│
├── backend/
│   ├── diagnostics/
│   │   ├── dns.py
│   │   ├── http.py
│   │   └── ping.py
│   │
│   ├── engine/
│   │   ├── baseline.py
│   │   ├── costs.py
│   │   ├── decision.py
│   │   ├── hypotheses.py
│   │   └── investigator.py
│   │
│   ├── models/
│   │   └── schema.py
│   │
│   └── main.py
│
├── simulator/
│   ├── failures.py
│   ├── scenarios.py
│   ├── diagnostics.py
│   └── system.py
│
├── tests/
│   └── evaluate.py
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── ...
│
├── requirements.txt
├── README.md
└── .gitignore

Failure Scenarios

PRISM currently supports controlled scenarios including:

Healthy system

DNS failure

Network failure

HTTP failure

High latency

Database lock contention

The database lock-contention scenario currently uses a controlled simulator to generate database and application metrics.

Example simulated progression:

Healthy
  ↓
Lock contention begins
  ↓
Waiting transactions increase
  ↓
Connection pool pressure increases
  ↓
Application latency increases
  ↓
System becomes critical

Adaptive Investigation

PRISM assigns confidence values to competing hypotheses.

Example hypotheses include:

DNS failure
Network connectivity
Network latency
HTTP/service failure
Database connection exhaustion
Database lock contention
Healthy

After each diagnostic result, the investigator updates the hypothesis scores.

The decision engine then evaluates the available tests using a lightweight information-value heuristic and diagnostic cost.

The current implementation is intentionally lightweight and should be considered a heuristic rather than a mathematically rigorous expected-information-gain model.

Diagnostic Costs

The current relative diagnostic costs are:

Test

Cost

DNS

1

Ping

2

HTTP

3

Database

4

PRISM uses these costs when selecting the next diagnostic.

Real vs Simulated Diagnostics

PRISM currently combines real diagnostics with controlled simulation.

Real diagnostics

The following diagnostics can operate against real Internet targets:

DNS resolution

Ping

HTTP requests

Simulated diagnostics

The distributed-system failure scenarios are currently controlled simulations.

This provides deterministic and reproducible experiments for evaluating the investigation strategy.

The distinction is intentional:

Real Internet Diagnostics
        +
Controlled Failure Simulation
        ↓
Adaptive Investigation Engine

Failure Replay

PRISM can replay the simulated system state over successive investigation steps.

For database lock contention, the replay demonstrates the progression of:

Lock wait
   ↓
Waiting transactions
   ↓
Connection pool pressure
   ↓
Application request latency

Example:

Step

Lock Wait

Waiting Transactions

Pool Usage

Latency

0

5 ms

0

32%

100 ms

1

400 ms

6

56%

500 ms

2

1000 ms

15

80%

1300 ms

3

1800 ms

24

96%

2200 ms

The frontend provides an interactive replay interface for stepping through these states.

Evaluation

PRISM includes a deterministic benchmark comparing an adaptive investigation strategy with a fixed diagnostic strategy.

Current benchmark:

Scenario

Adaptive

Fixed

Healthy

3

3

DNS failure

1

3

Network failure

2

3

HTTP failure

3

3

High latency

2

3

Total

11

15

This represents a:

26.7% reduction in diagnostic tests

for the controlled benchmark.

Both strategies achieve 100% diagnosis accuracy in this benchmark.

These results should be interpreted as results from the controlled evaluation scenarios, not as a general claim about all network troubleshooting environments.

Running the Backend

From the project root:

.env\Scripts\Activate.ps1

Then:

uvicorn backend.main:app --reload

The backend runs at:

http://127.0.0.1:8000

API documentation:

http://127.0.0.1:8000/docs

Running the Frontend

Open another terminal:

cd frontend
npm install
npm run dev

The frontend runs at:

http://localhost:5173

API Endpoints

Health

GET /health

Real Investigation

POST /investigate

Runs diagnostics against the supplied target.

Simulated Investigation

POST /investigate/simulated

Runs an adaptive investigation against a controlled failure scenario.

Example:

{
  "target": "api.example.com",
  "failure": "db_lock_contention"
}

Simulated Replay

POST /replay/simulated

Returns the simulated system timeline for replay.

Technology Stack

Backend

Python

FastAPI

Pydantic

Requests

dnspython

Frontend

React

Vite

JavaScript

CSS

Investigation

Hypothesis-based reasoning

Shannon entropy

Information-value heuristic

Diagnostic cost model

Hackathon Demonstration

The primary demonstration focuses on:

Failure
   ↓
Adaptive Investigation
   ↓
Evidence Collection
   ↓
Diagnosis
   ↓
Failure Replay

The main scenario is database lock contention and its cascading effects on application performance.

The project demonstrates how an adaptive investigation layer can decide which diagnostic to execute next instead of blindly executing every available test.