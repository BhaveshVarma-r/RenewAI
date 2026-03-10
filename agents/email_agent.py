"""Email agent — generates and sends renewal emails."""

import json
import asyncio
from langsmith import traceable
from services.gemini_client import GeminiClient
from schemas.models import PolicyData, ExecutionPlan
from mock_services.sendgrid import MockSendGridClient
from mock_services.vector_search import MockVectorSearch
from mock_services.bigquery import MockBigQueryClient
from config.language_prompts import email_system_prompt, irdai_disclosure

gemini = GeminiClient()
sendgrid = MockSendGridClient()
bigquery = MockBigQueryClient()


@traceable(name="email_agent")
async def send_renewal_email(state: dict, vector_search: MockVectorSearch) -> dict:
    """Generate and send a personalized renewal email."""
    policy_data = state.get("policy_data", {})
    plan = state.get("execution_plan", {})
    if isinstance(policy_data, PolicyData):
        policy_data = policy_data.model_dump()
    if isinstance(plan, ExecutionPlan):
        plan = plan.model_dump()

    language = policy_data.get("language_preference", "english")
    risk_tier = policy_data.get("risk_tier", "medium")

    # Tone rules by risk level
    tone_map = {
        "low": "friendly and warm reminder",
        "medium": "caring concern with gentle urgency",
        "high": "urgent action required with empathy",
        "critical": "last chance with clear consequences",
    }
    tone = tone_map.get(risk_tier, "empathetic")

    # Get benefit points from vector search
    benefits = await vector_search.similarity_search(f"policy benefits {policy_data.get('policy_type', '')}", k=2)

    system = email_system_prompt.get(language, email_system_prompt["english"])
    disclosure_localized = irdai_disclosure.get(language, irdai_disclosure["english"])
    disclosure_english = irdai_disclosure.get("english", "")  # Always include English for compliance checking

    prompt = f"""Generate an HTML email body for this renewal:

Customer: {policy_data.get('customer_name')}
Policy ID: {policy_data.get('policy_id')}
Premium: ₹{policy_data.get('premium_amount', 0):,.2f}
Due Date: {policy_data.get('due_date')}
Grace Period: {policy_data.get('grace_period_days')} days
Sum Assured: ₹{policy_data.get('sum_assured', 0):,.2f}
Policy Type: {policy_data.get('policy_type')}
Nominee: {policy_data.get('nominee_name')}
EMI Eligible: {policy_data.get('emi_eligible')}
Risk Level: {risk_tier}
Tone: {tone}

MANDATORY FOOTER (include this exactly):
{disclosure_localized}

Use attractive HTML with:
- Professional header with Suraksha Life branding
- Clear premium amount and due date
- Benefits reminder
- Payment CTA button
- IRDAI disclosure footer"""

    try:
        html_body = await gemini.generate_flash(prompt, system)
    except Exception as e:
        html_body = ""
    
    # Strip closing HTML tags if present so we can append footer before </body> and </html>
    html_body = html_body.replace("</body>", "").replace("</html>", "")
    
    # Always append the mandatory IRDAI disclosure footer with BOTH localized AND English text for compliance checking
    footer_html = f"""
<hr style='margin-top: 40px; border: none; border-top: 1px solid #ddd;'>
<div style='font-size: 11px; color: #666; background-color: #f9f9f9; padding: 15px; margin-top: 20px; border-radius: 4px;'>
    <strong>Important Disclosure:</strong><br/>
    {disclosure_localized}
    <br/><br/>
    {disclosure_english}
</div>
</body>
</html>"""
    
    if not html_body:
        html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset='UTF-8'>
    <title>Policy Renewal</title>
</head>
<body>
<h2>Policy Renewal Reminder</h2>
<p>Dear {policy_data.get('customer_name')},</p>
<p>Your Suraksha Life Insurance policy <strong>{policy_data.get('policy_id')}</strong> premium of
<strong>₹{policy_data.get('premium_amount', 0):,.2f}</strong> is due on <strong>{policy_data.get('due_date')}</strong>.</p>
<p>Sum Assured: ₹{policy_data.get('sum_assured', 0):,.2f}</p>
<p><a href='#' style='background:#4CAF50;color:white;padding:12px 24px;text-decoration:none;border-radius:4px;'>Pay Now</a></p>
{footer_html}"""
    else:
        html_body += footer_html

    # Send email
    result = await sendgrid.send_email(
        to=policy_data.get("contact_email", ""),
        subject=f"Suraksha Life - Policy {policy_data.get('policy_id')} Renewal Reminder",
        html_body=html_body,
        language=language,
        policy_id=policy_data.get("policy_id", ""),
    )

    # Brief delay then check open rate
    await asyncio.sleep(0.5)
    open_result = await sendgrid.get_open_rate(result["message_id"])

    attempt = state.get("attempt_number", 1)
    execution_result = {
        "channel": "email",
        "message_id": result["message_id"],
        "opened": open_result["opened"],
        "clicked": open_result.get("clicked", False),
        "language": language,
        "attempt_number": attempt,
        "html_content": html_body,  # Include full HTML with IRDAI disclosure footer
        "converted": False,
    }

    state["execution_result"] = execution_result
    state["current_step"] = "email_sent"

    # Log to BigQuery analytics
    await bigquery.async_insert("customer_interactions", [{
        "trace_id": state.get("trace_id", ""),
        "policy_id": policy_data.get("policy_id"),
        "customer_id": policy_data.get("customer_id"),
        "channel": "email",
        "interaction_type": "renewal_reminder",
        "outcome": "delivered",
        "converted": 1 if execution_result.get("converted", False) else 0,
        "escalated": 0,
        "language": language,
        "risk_tier": risk_tier,
    }])

    return state
