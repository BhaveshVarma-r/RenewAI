"""WhatsApp agent — multi-turn conversation handler."""

import json
from langsmith import traceable
from services.gemini_client import GeminiClient
from schemas.models import PolicyData
from mock_services.gupshup import MockGupshupClient
from mock_services.razorpay import MockPaymentClient
from mock_services.redis_cache import MockRedisClient
from mock_services.firestore import MockFirestoreClient
from mock_services.vector_search import MockVectorSearch
from mock_services.bigquery import MockBigQueryClient
from config.language_prompts import whatsapp_system_prompt, irdai_disclosure

gemini = GeminiClient()
gupshup = MockGupshupClient()
razorpay = MockPaymentClient()
redis_client = MockRedisClient()
firestore = MockFirestoreClient()
vector_search = MockVectorSearch()
bigquery = MockBigQueryClient()


@traceable(name="whatsapp_agent")
async def handle_whatsapp(state: dict) -> dict:
    """Handle WhatsApp renewal outreach and multi-turn conversation."""
    policy_data = state.get("policy_data", {})
    if isinstance(policy_data, PolicyData):
        policy_data = policy_data.model_dump()

    phone = policy_data.get("contact_phone", "")
    policy_id = policy_data.get("policy_id", "")
    language = policy_data.get("language_preference", "english")
    risk_tier = policy_data.get("risk_tier", "medium")
    customer_id = policy_data.get("customer_id", "")

    # Rate limit check
    if not redis_client.check_rate_limit(customer_id, "whatsapp"):
        state["execution_result"] = {
            "channel": "whatsapp", "intent_detected": "rate_limited",
            "messages_sent": 0, "converted": False, "escalated": False,
        }
        return state

    # Generate initial outreach message
    system = whatsapp_system_prompt.get(language, whatsapp_system_prompt["english"])
    disclosure = irdai_disclosure.get(language, irdai_disclosure["english"])

    prompt = f"""Send a renewal reminder to {policy_data.get('customer_name')}:
Policy: {policy_id}, Premium: ₹{policy_data.get('premium_amount', 0):,.2f}
Due: {policy_data.get('due_date')}, Sum Assured: ₹{policy_data.get('sum_assured', 0):,.2f}
Risk: {risk_tier}, EMI Eligible: {policy_data.get('emi_eligible')}
Include: {disclosure}"""

    try:
        message = await gemini.generate_flash(prompt, system)
    except Exception:
        message = f"Namaste {policy_data.get('customer_name')}, your Suraksha Life policy {policy_id} premium of ₹{policy_data.get('premium_amount', 0):,.2f} is due on {policy_data.get('due_date')}. Reply PAY to get payment link. {disclosure}"

    quick_replies = ["Pay Now", "EMI Options", "Talk to Agent", "Not Interested"]
    await gupshup.send_message(phone, message, quick_replies, policy_id)
    messages_sent = 1

    # Simulate customer reply
    reply = await gupshup.simulate_inbound_reply(phone, risk_tier)
    intent = reply["intent"]
    converted = False
    escalated = False

    # Handle each intent
    if intent == "pay_intent":
        payment = await razorpay.create_payment_link(
            policy_data.get("premium_amount", 0), policy_id,
            policy_data.get("customer_name", ""),
        )
        await gupshup.send_payment_qr(phone, policy_data.get("premium_amount", 0), policy_id, payment["payment_link"])
        status = await razorpay.check_payment_status(payment["payment_id"])
        converted = status.get("status") == "paid"
        messages_sent += 1

    elif intent == "emi_request":
        if policy_data.get("emi_eligible"):
            premium = policy_data.get("premium_amount", 0)
            emi_msg = f"EMI available! Monthly: ₹{premium/12:,.2f}, Quarterly: ₹{premium/4:,.2f}. Reply to choose."
            await gupshup.send_message(phone, emi_msg, ["Monthly", "Quarterly"], policy_id)
            messages_sent += 1
        else:
            await gupshup.send_message(phone, "EMI is not available for this policy. Full payment required.", [], policy_id)
            messages_sent += 1

    elif intent == "hardship":
        escalated = True
        await gupshup.send_message(phone, "I understand your situation. Connecting you with our specialist team.", [], policy_id)
        messages_sent += 1

    elif intent == "human_request":
        escalated = True
        await gupshup.send_message(phone, "Connecting you with a live agent. Please hold.", [], policy_id)
        messages_sent += 1

    elif intent == "receipt":
        await gupshup.send_message(phone, f"Receipt for policy {policy_id} has been sent to your email.", [], policy_id)
        messages_sent += 1

    elif intent == "no_response":
        pass  # Flag for voice followup

    # Store session
    redis_client.set_session(f"wa_{phone}", {"policy_id": policy_id, "intent": intent, "messages": messages_sent})

    # Store conversation history
    firestore.set_document("conversations", f"{policy_id}_{phone}", {
        "policy_id": policy_id, "phone": phone, "intent": intent,
        "messages_sent": messages_sent, "converted": converted,
    })

    state["execution_result"] = {
        "channel": "whatsapp",
        "intent_detected": intent,
        "messages_sent": messages_sent,
        "converted": converted,
        "escalated": escalated,
        "sentiment_score": reply.get("sentiment_score", 0.5),
    }
    state["current_step"] = "whatsapp_handled"
    if escalated:
        state["escalation_flag"] = True
        state["escalation_reason"] = f"WhatsApp: {intent}"

    # Log to BigQuery analytics
    await bigquery.async_insert("customer_interactions", [{
        "trace_id": state.get("trace_id", ""),
        "policy_id": policy_id,
        "customer_id": customer_id,
        "channel": "whatsapp",
        "interaction_type": "renewal_chat",
        "outcome": intent,
        "converted": 1 if converted else 0,
        "escalated": 1 if escalated else 0,
        "language": language,
        "risk_tier": risk_tier,
    }])

    return state