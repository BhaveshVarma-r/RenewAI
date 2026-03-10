"""Orchestrator agent — coordinates the entire renewal workflow."""

import json
from langsmith import traceable
from services.gemini_client import GeminiClient
from schemas.models import PolicyData, PropensityScore
from mock_services.crm import MockCRMClient
from mock_services.vertex_ai import MockPropensityScorer
from mock_services.cloud_sql_audit import MockAuditDB
from mock_services.bigquery import MockBigQueryClient
from schemas.models import AuditLogEntry

gemini = GeminiClient()
crm = MockCRMClient()
propensity_scorer = MockPropensityScorer()
audit_db = MockAuditDB()
bigquery = MockBigQueryClient()


CLASSIFY_SYSTEM = """You are an insurance renewal orchestrator. Given policy data and propensity scores,
determine the optimal communication strategy. Consider customer history, risk level, preferred
language and channel. Output JSON with: recommended_channel, urgency_level, key_considerations."""


@traceable(name="orchestrator_init")
async def init_node(state: dict) -> dict:
    """Load policy data and get propensity score."""
    policy_id = state.get("policy_id", "")
    policy = crm.get_policy(policy_id)
    if not policy:
        state["final_status"] = "policy_not_found"
        state["current_step"] = "error"
        return state

    state["policy_data"] = policy.model_dump()
    days_to_due = state.get("days_to_due")
    if not isinstance(days_to_due, int):
        days_to_due = 30 # Default to 30 if not an int

    score = await propensity_scorer.get_lapse_score(
        policy_id=policy_id,
        payment_history=list(policy.payment_history) if policy.payment_history is not None else [],
        days_to_due=days_to_due or 30,
        risk_tier=policy.risk_tier,
        premium_amount=policy.premium_amount,
    )
    state["propensity_score"] = score
    state["current_step"] = "initialized"

    audit_db.write_audit_log(AuditLogEntry(
        trace_id=state.get("trace_id", ""), step_sequence=1,
        agent_id="orchestrator", policy_id=policy_id,
        customer_id=policy.customer_id,
        agent_input={"action": "init", "policy_id": policy_id},
        agent_response={"status": "initialized", "risk_tier": policy.risk_tier},
    ))
    return state


@traceable(name="orchestrator_classify")
async def classify_node(state: dict) -> dict:
    """Classify risk and select communication strategy."""
    policy_data = state.get("policy_data", {})
    propensity = state.get("propensity_score", {})

    prompt = f"""Classify this renewal case:
Customer: {policy_data.get('customer_name')}
Risk: {policy_data.get('risk_tier')}
Lapse Probability: {propensity.get('lapse_probability', 0)}
Channel Preference: {policy_data.get('channel_preference')}
Language: {policy_data.get('language_preference')}
Days to Due: {state.get('days_to_due', 'N/A')}
Payment History: {str(policy_data.get('payment_history', []))}"""

    try:
        classification = await gemini.generate_json(prompt, CLASSIFY_SYSTEM)
        state["classification"] = classification
    except Exception:
        state["classification"] = {
            "recommended_channel": policy_data.get("channel_preference", "email"),
            "urgency_level": policy_data.get("risk_tier", "medium"),
        }

    state["current_step"] = "classified"
    return state


def route_to_channel(state: dict) -> str:
    """Route to the appropriate channel based on classification."""
    if state.get("escalation_flag"):
        return "escalate"

    plan = state.get("execution_plan", {})
    channel = plan.get("channel") if plan else None

    if not channel:
        trigger = state.get("trigger_type", "due_date")
        days = state.get("days_to_due") or 30

        if trigger == "inbound_message":
            channel = "whatsapp"
        elif trigger == "lapse_event":
            channel = "voice"
        elif days >= 45:
            channel = "email"
        elif days >= 25:
            channel = "whatsapp"
        else:
            channel = "voice"

    return channel if channel in ("email", "whatsapp", "voice") else "email"


def route_after_safety(state: dict) -> str:
    """Route after safety check."""
    if state.get("escalation_flag"):
        return "escalate"
    compliance = state.get("compliance_result", {})
    if isinstance(compliance, dict) and compliance.get("verdict") == "BLOCK":
        return "escalate"
    return "deliver"


@traceable(name="orchestrator_deliver")
async def deliver_node(state: dict) -> dict:
    """Final delivery and audit logging."""
    result = state.get("execution_result", {})
    trace_id = state.get("trace_id", "")
    policy_data = state.get("policy_data", {})

    audit_db.write_audit_log(AuditLogEntry(
        trace_id=trace_id, step_sequence=10,
        agent_id="orchestrator_deliver",
        policy_id=policy_data.get("policy_id", ""),
        customer_id=policy_data.get("customer_id", ""),
        agent_input={"action": "deliver"},
        agent_response=result,
        compliance_verdict=state.get("compliance_result", {}).get("verdict") if isinstance(state.get("compliance_result"), dict) else None,
    ))

    # Log to BigQuery analytics
    await bigquery.async_insert("customer_interactions", [{
        "trace_id": trace_id,
        "policy_id": policy_data.get("policy_id"),
        "customer_id": policy_data.get("customer_id"),
        "channel": result.get("channel", "unknown"),
        "interaction_type": state.get("trigger_type", "due_date"),
        "outcome": result.get("outcome", result.get("intent_detected", "completed")),
        "converted": 1 if result.get("converted") else 0,
        "escalated": 1 if result.get("escalated") or state.get("escalation_flag") else 0,
        "language": policy_data.get("language_preference"),
        "risk_tier": policy_data.get("risk_tier"),
    }])

    state["current_step"] = "delivered"
    return state


@traceable(name="orchestrator_escalate")
async def escalate_node(state: dict) -> dict:
    """Escalate to human queue."""
    state["current_step"] = "escalated"
    state["escalation_flag"] = True
    if not state.get("escalation_reason"):
        state["escalation_reason"] = "Automatic escalation from safety gate"
    
    # Log escalation to analytics
    policy_data = state.get("policy_data", {})
    trace_id = state.get("trace_id", "")
    await bigquery.async_insert("customer_interactions", [{
        "trace_id": trace_id,
        "policy_id": policy_data.get("policy_id"),
        "customer_id": policy_data.get("customer_id"),
        "channel": state.get("trigger_type", "due_date"),
        "interaction_type": "escalation",
        "outcome": state.get("escalation_reason"),
        "converted": 0,
        "escalated": 1,
        "language": policy_data.get("language_preference"),
        "risk_tier": policy_data.get("risk_tier"),
    }])
    
    return state


@traceable(name="orchestrator_complete")
async def complete_node(state: dict) -> dict:
    """Mark renewal as complete."""
    result = state.get("execution_result", {})
    if result.get("converted"):
        state["final_status"] = "converted"
    elif state.get("escalation_flag"):
        state["final_status"] = "escalated"
    else:
        state["final_status"] = "completed"

    state["current_step"] = "complete"
    return state
