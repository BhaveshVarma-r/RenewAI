"""Pydantic v2 schemas for RenewAI system."""

from pydantic import BaseModel, Field
from typing import Literal, Optional, Any
from datetime import datetime
import uuid


class PolicyData(BaseModel):
    """Insurance policy data from CRM."""
    policy_id: str
    customer_id: str
    customer_name: str
    premium_amount: float
    due_date: str
    grace_period_days: int
    status: Literal["active", "grace_period", "lapsed", "cancelled"]
    risk_tier: Literal["low", "medium", "high", "critical"]
    language_preference: str
    channel_preference: Literal["email", "whatsapp", "voice"]
    contact_phone: str
    contact_email: str
    preferred_contact_time: Literal["morning", "afternoon", "evening", "weekend"]
    payment_history: list[str]
    agent_id: str = "AG001"
    policy_type: str = "term_life"
    sum_assured: float = 500000.0
    emi_eligible: bool = False
    lapse_date: Optional[str] = None
    days_since_lapse: Optional[int] = None
    nominee_name: str = "Not Specified"


class PropensityScore(BaseModel):
    """Lapse propensity score from ML model."""
    lapse_probability: float = Field(ge=0.0, le=1.0)
    risk_level: Literal["low", "medium", "high", "critical"]
    key_factors: list[str]
    recommended_channel: str
    recommended_time: str
    emi_recommended: bool


class ExecutionPlan(BaseModel):
    """Communication execution plan for a policy renewal."""
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    policy_id: str
    channel: Literal["email", "whatsapp", "voice"]
    language: str
    tone: Literal["empathetic", "urgent", "friendly", "formal", "concerned"]
    timing: str
    message_template: str
    emi_options: Optional[dict] = None
    objection_strategy: list[str] = []
    escalation_triggers: list[str] = []


class CritiqueResult(BaseModel):
    """Quality evaluation result from critique agent."""
    verdict: Literal["APPROVED", "REJECTED"]
    score: float = Field(ge=0.0, le=10.0)
    tone_score: float = Field(ge=0.0, le=10.0)
    language_quality_score: float = Field(ge=0.0, le=10.0)
    factual_accuracy: bool
    hallucination_detected: bool
    feedback: str
    rejection_reasons: list[str] = []


class ComplianceResult(BaseModel):
    """IRDAI compliance check result."""
    verdict: Literal["PASS", "FAIL", "BLOCK"]
    irdai_disclosure_present: bool = False
    opt_out_present: bool = False
    grievance_number_present: bool = False
    mis_selling_detected: bool = False
    pii_violations: list[str] = []
    trai_dnd_respected: bool = True
    violations: list[str] = []


class AuditLogEntry(BaseModel):
    """Immutable audit trail entry."""
    trace_id: str
    step_sequence: int
    agent_id: str
    policy_id: str
    customer_id: str
    agent_input: dict
    agent_response: dict
    evidence: Optional[dict] = None
    critique_result: Optional[CritiqueResult] = None
    critique_score: Optional[float] = None
    compliance_verdict: Optional[str] = None
    rag_sources: Optional[list[str]] = None
    model_version: str = "gemini-2.0-flash"
    pii_masked: bool = True


class SafetyGateResult(BaseModel):
    """Result from the safety gate middleware pipeline."""
    passed: bool
    masked_content: str
    compliance: Optional[ComplianceResult] = None
    violations: list[str] = []
    escalate_human: bool = False
    pii_findings: list[dict] = []


class OrchestratorState(BaseModel):
    """Main state for the LangGraph orchestrator."""
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    policy_id: str
    customer_id: str
    trigger_type: Literal["due_date", "inbound_message", "lapse_event"]
    days_to_due: Optional[int] = None
    policy_data: Optional[PolicyData] = None
    propensity_score: Optional[PropensityScore] = None
    current_step: str = "init"
    execution_plan: Optional[ExecutionPlan] = None
    plan_retry_count: int = 0
    execution_result: Optional[dict] = None
    critique_result: Optional[CritiqueResult] = None
    compliance_result: Optional[ComplianceResult] = None
    escalation_flag: bool = False
    escalation_reason: Optional[str] = None
    interaction_history: list[dict] = []
    final_status: Optional[str] = None


class PlannerLoopState(BaseModel):
    """State for the planner critique retry loop."""
    policy_data: PolicyData
    propensity_score: PropensityScore
    execution_plan: Optional[ExecutionPlan] = None
    critique: Optional[CritiqueResult] = None
    retry_count: int = 0
    feedback_history: list[str] = []
    escalation_flag: bool = False
    escalation_reason: Optional[str] = None


# ----- API Request/Response Models -----

class DueDateTriggerRequest(BaseModel):
    policy_id: str
    days_to_due: int


class InboundTriggerRequest(BaseModel):
    policy_id: str
    channel: str
    message: str
    phone: str


class LapseTriggerRequest(BaseModel):
    policy_id: str
    days_since_lapse: int


class QueueResolveRequest(BaseModel):
    resolution: str
    specialist_notes: str


class TriggerResponse(BaseModel):
    trace_id: str
    status: str
    result: Optional[dict] = None


class InboundResponse(BaseModel):
    trace_id: str
    response_sent: bool
    intent: str


class LapseResponse(BaseModel):
    trace_id: str
    revival_attempted: bool


class HealthResponse(BaseModel):
    status: str
    gemini: str
    langsmith: str
