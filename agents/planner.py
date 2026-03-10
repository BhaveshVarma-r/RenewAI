"""Planner agent — creates execution plans for renewal outreach."""

import json
from langsmith import traceable
from services.gemini_client import GeminiClient
from schemas.models import ExecutionPlan, OrchestratorState, PolicyData, PropensityScore
from mock_services.vector_search import MockVectorSearch
from config.language_prompts import email_system_prompt, whatsapp_system_prompt, voice_system_prompt

gemini = GeminiClient()


@traceable(name="planner_agent")
async def plan_renewal(state: dict, vector_search: MockVectorSearch) -> dict:
    """Create an execution plan for contacting a customer about renewal."""
    policy_data = state.get("policy_data")
    propensity = state.get("propensity_score")
    feedback = state.get("feedback_history", [])

    if isinstance(policy_data, dict):
        policy_data = PolicyData(**policy_data)
    if isinstance(propensity, dict):
        propensity = PropensityScore(**propensity)

    # Ensure feedback is a list
    if not isinstance(feedback, (list, tuple)):
        feedback = [] if feedback is None else [str(feedback)]

    # Get objection strategies from vector search
    objection_query = f"customer with {policy_data.risk_tier} risk, premium {policy_data.premium_amount}"
    objections = await vector_search.async_similarity_search(objection_query, k=3)
    objection_strategies = [o["response"][:100] for o in objections]

    # Determine channel
    channel = policy_data.channel_preference
    if propensity and propensity.recommended_channel:
        if propensity.risk_level in ("high", "critical"):
            channel = propensity.recommended_channel

    # Determine tone based on risk
    tone_map = {"low": "friendly", "medium": "empathetic", "high": "urgent", "critical": "concerned"}
    tone = tone_map.get(policy_data.risk_tier, "empathetic")

    # Build prompt with feedback if retrying
    feedback_text = ""
    if feedback and len(feedback) > 0:
        feedback_text = "\n\nPREVIOUS CRITIQUE FEEDBACK (must address these issues):\n" + "\n".join(f"- {str(f)}" for f in feedback)

    prompt = f"""Create a renewal communication plan for this customer:

Policy ID: {policy_data.policy_id}
Customer: {policy_data.customer_name}
Premium: ₹{policy_data.premium_amount:,.2f}
Due Date: {policy_data.due_date}
Grace Period: {policy_data.grace_period_days} days
Status: {policy_data.status}
Risk Tier: {policy_data.risk_tier}
Language: {policy_data.language_preference}
Preferred Channel: {channel}
Preferred Time: {policy_data.preferred_contact_time}
EMI Eligible: {policy_data.emi_eligible}
Sum Assured: ₹{policy_data.sum_assured:,.2f}
Payment History: {policy_data.payment_history}
Nominee: {policy_data.nominee_name}

Propensity Score: {propensity.lapse_probability if propensity else 'N/A'}
Key Risk Factors: {propensity.key_factors if propensity else []}

Objection Strategies Available:
{json.dumps(objection_strategies, indent=2)}
{feedback_text}

Output a JSON object with these exact fields:
- plan_id: a unique identifier string
- policy_id: "{policy_data.policy_id}"
- channel: "{channel}"
- language: "{policy_data.language_preference}"
- tone: "{tone}"
- timing: appropriate time description
- message_template: full message in {policy_data.language_preference} language
- emi_options: EMI details if eligible, null otherwise
- objection_strategy: list of strategy strings
- escalation_triggers: list of trigger conditions"""

    system = f"You are an insurance renewal planner. Create a detailed execution plan. The message must be in {policy_data.language_preference}. Be empathetic, clear about consequences of lapse, and offer solutions. Include IRDAI disclosures (AI identity, opt-out, grievance 1800-XXX-XXXX). Output JSON matching the schema exactly."

    try:
        result = await gemini.generate_json(prompt, system)
        # Ensure required fields
        result.setdefault("plan_id", f"plan-{policy_data.policy_id}")
        result.setdefault("policy_id", policy_data.policy_id)
        result.setdefault("channel", channel)
        result.setdefault("language", policy_data.language_preference)
        result.setdefault("tone", tone)
        result.setdefault("timing", policy_data.preferred_contact_time)
        result.setdefault("message_template", f"Renewal reminder for policy {policy_data.policy_id}")
        result.setdefault("objection_strategy", objection_strategies)
        result.setdefault("escalation_triggers", ["distress_detected", "3_failed_attempts"])

        plan = ExecutionPlan(**result)
        state["execution_plan"] = plan.model_dump()
        return state
    except Exception as e:
        # Fallback plan
        plan = ExecutionPlan(
            policy_id=policy_data.policy_id,
            channel=channel,
            language=policy_data.language_preference,
            tone=tone,
            timing=policy_data.preferred_contact_time,
            message_template=f"Dear {policy_data.customer_name}, your Suraksha Life policy {policy_data.policy_id} premium of ₹{policy_data.premium_amount:,.2f} is due on {policy_data.due_date}. Please renew to keep your ₹{policy_data.sum_assured:,.2f} coverage active. This is an AI-assisted communication. Reply STOP to opt out. Grievance: 1800-XXX-XXXX",
            objection_strategy=objection_strategies,
            escalation_triggers=["distress_detected", "3_failed_attempts"],
        )
        state["execution_plan"] = plan.model_dump()
        return state
