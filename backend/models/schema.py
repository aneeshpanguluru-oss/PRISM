from typing import Any, Optional
from pydantic import BaseModel


class DiagnosticResult(BaseModel):
    diagnostic: str
    target: str
    success: bool
    metrics: dict[str, Any]
    error: Optional[str] = None


class InvestigationReport(BaseModel):

    target: str

    tests_executed: list[str]

    evidence: list[DiagnosticResult]

    hypotheses: list[dict[str, Any]]

    final_diagnosis: Optional[str] = None

    reasoning: Optional[str] = None

    investigation_trace: list[dict[str, Any]] = []

    system_timeline: list[dict[str, Any]] = []