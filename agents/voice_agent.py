"""Voice agent — generates call scripts and simulates calls."""

import json
from langsmith import traceable
from services.gemini_client import GeminiClient
from schemas.models import PolicyData
from mock_services.exotel import MockExotelClient
from mock_services.razorpay import MockPaymentClient
from mock_services.redis_cache import MockRedisClient
from mock_services.vector_search import MockVectorSearch
from mock_services.bigquery import MockBigQueryClient
from middleware.distress_detector import DistressDetector
from config.language_prompts import voice_system_prompt, irdai_disclosure

gemini = GeminiClient()
exotel = MockExotelClient()
razorpay = MockPaymentClient()
redis_client = MockRedisClient()
bigquery = MockBigQueryClient()
distress_detector = DistressDetector()


@traceable(name="voice_agent")
async def make_renewal_call(state: dict, vector_search: MockVectorSearch) -> dict:
    """Generate call script and simulate a voice call."""
    policy_data = state.get("policy_data", {})
    if isinstance(policy_data, PolicyData):
        policy_data = policy_data.model_dump()

    phone = policy_data.get("contact_phone", "")
    policy_id = policy_data.get("policy_id", "")
    language = policy_data.get("language_preference", "english")
    risk_tier = policy_data.get("risk_tier", "medium")

    # Pre-call: check if already paid
    payment_status = redis_client.get(f"payment:{policy_id}")
    if payment_status == "paid":
        state["execution_result"] = {
            "channel": "voice", "call_id": None, "outcome": "already_paid",
            "converted": True, "escalated": False, "objections": [],
        }
        return state

    # Pre-call: check DND
    if exotel.check_dnd_status(phone):
        state["execution_result"] = {
            "channel": "voice", "call_id": None, "outcome": "dnd_blocked",
            "converted": False, "escalated": False, "objections": [],
        }
        state["current_step"] = "voice_dnd_blocked"
        return state

    # Get objection responses from vector search
    objections = await vector_search.similarity_search(f"{risk_tier} risk customer objections", k=3)
    objection_text = "\n".join(f"- If: '{o['objection']}' → Respond: '{o['response'][:80]}...'" for o in objections)

    system = voice_system_prompt.get(language, voice_system_prompt["english"])
    disclosure = irdai_disclosure.get(language, irdai_disclosure["english"])

    prompt = f"""Generate a call script for this renewal:
Customer: {policy_data.get('customer_name')}
Policy: {policy_id}
Premium: ₹{policy_data.get('premium_amount', 0):,.2f}
Due Date: {policy_data.get('due_date')}
Grace Period: {policy_data.get('grace_period_days')} days
Sum Assured: ₹{policy_data.get('sum_assured', 0):,.2f}
Risk: {risk_tier}
EMI Eligible: {policy_data.get('emi_eligible')}
Nominee: {policy_data.get('nominee_name')}

Objection Handling:
{objection_text}

Disclosure: {disclosure}

Include all 6 sections: Greeting, Policy Reminder, Consequences, Objection Handling, Payment Offer, Closing."""

    try:
        script = await gemini.generate_flash(prompt, system)
    except Exception:
        script = f"""GREETING: Good day, {policy_data.get('customer_name')}. This is a call from Suraksha Life Insurance.
POLICY REMINDER: Your policy {policy_id} premium of ₹{policy_data.get('premium_amount', 0):,.2f} is due on {policy_data.get('due_date')}.
CONSEQUENCES: Without payment, your ₹{policy_data.get('sum_assured', 0):,.2f} coverage may lapse.
PAYMENT: I can send you a payment link right now.
CLOSING: Thank you for your time. Grievance: 1800-XXX-XXXX. {disclosure}"""

    # Check script for distress keywords
    distress = distress_detector.check(script, language)

    # Make the call
    call_result = await exotel.make_call(phone, script, language, policy_id, risk_tier)

    # Check call transcript for distress
    transcript_distress = distress_detector.check(call_result.get("transcript", ""), language)

    escalated = False
    if transcript_distress["distress_detected"] and transcript_distress["severity"] == "high":
        escalated = True
    if call_result.get("outcome") == "objection" and len(call_result.get("objections_raised", [])) >= 3:
        escalated = True

    state["execution_result"] = {
        "channel": "voice",
        "call_id": call_result.get("call_id"),
        "outcome": call_result.get("outcome"),
        "converted": call_result.get("converted", False),
        "escalated": escalated,
        "objections": call_result.get("objections_raised", []),
        "duration_seconds": call_result.get("duration_seconds", 0),
        "script_preview": script[:300],
    }
    state["current_step"] = "voice_called"
    if escalated:
        state["escalation_flag"] = True
        state["escalation_reason"] = f"Voice: {call_result.get('outcome')} - {len(call_result.get('objections_raised', []))} objections"

    # Log to BigQuery analytics
    await bigquery.async_insert("customer_interactions", [{
        "trace_id": state.get("trace_id", ""),
        "policy_id": policy_id,
        "customer_id": policy_data.get("customer_id"),
        "channel": "voice",
        "interaction_type": "renewal_call",
        "outcome": call_result.get("outcome"),
        "converted": 1 if call_result.get("converted", False) else 0,
        "escalated": 1 if escalated else 0,
        "duration_seconds": call_result.get("duration_seconds", 0),
        "language": language,
        "risk_tier": risk_tier,
    }])

    return state
