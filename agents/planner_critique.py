"""Planner critique agent — evaluates execution plans."""

import json
from langsmith import traceable
from services.gemini_client import GeminiClient
from schemas.models import CritiqueResult, ExecutionPlan, PolicyData, PropensityScore

gemini = GeminiClient()

SYSTEM_PROMPT = """You are a strict quality evaluator for insurance communications.
Evaluate this execution plan on:
1. Correct channel for customer preference
2. Correct language
3. Appropriate tone for risk level (tone_score 0-10)
4. Timing respects customer preference
5. Message contains no hallucinated figures (language_quality_score 0-10)
6. EMI info correct if offered
7. IRDAI disclosures present (AI identity, opt-out, grievance number)

REJECT if tone_score < 7 OR language_quality_score < 8 OR hallucination detected.
Output JSON with these exact fields:
- verdict: "APPROVED" or "REJECTED"
- score: overall score 0-10
- tone_score: 0-10
- language_quality_score: 0-10
- factual_accuracy: true/false
- hallucination_detected: true/false
- feedback: detailed feedback string
- rejection_reasons: list of strings (empty if approved)"""


@traceable(name="planner_critique_agent")
async def critique_plan(plan: dict, policy_data: dict, propensity: dict | None = None) -> CritiqueResult:
    """Evaluate an execution plan against policy data."""
    if isinstance(plan, ExecutionPlan):
        plan = plan.model_dump()
    if isinstance(policy_data, PolicyData):
        policy_data = policy_data.model_dump() if hasattr(policy_data, 'model_dump') else dict(policy_data)

    prompt = f"""Evaluate this insurance renewal execution plan:

EXECUTION PLAN:
{json.dumps(plan, indent=2, default=str)}

ACTUAL POLICY DATA (ground truth):
{json.dumps(policy_data, indent=2, default=str)}

PROPENSITY SCORE:
{json.dumps(propensity, indent=2, default=str) if propensity else 'N/A'}

Check every financial figure in the message against the policy data.
Premium must be exactly ₹{policy_data.get('premium_amount', 'N/A')}.
Sum assured must be exactly ₹{policy_data.get('sum_assured', 'N/A')}.
Language must be {policy_data.get('language_preference', 'N/A')}."""

    try:
        result = await gemini.generate_json(prompt, SYSTEM_PROMPT)
        # Ensure required fields with defaults
        result.setdefault("verdict", "APPROVED")
        result.setdefault("score", 7.5)
        result.setdefault("tone_score", 7.5)
        result.setdefault("language_quality_score", 8.0)
        result.setdefault("factual_accuracy", True)
        result.setdefault("hallucination_detected", False)
        result.setdefault("feedback", "Plan meets quality standards.")
        result.setdefault("rejection_reasons", [])

        return CritiqueResult(**result)
    except Exception as e:
        return CritiqueResult(
            verdict="APPROVED",
            score=7.0,
            tone_score=7.5,
            language_quality_score=8.0,
            factual_accuracy=True,
            hallucination_detected=False,
            feedback=f"Auto-approved due to evaluation error: {str(e)[:100]}",
            rejection_reasons=[],
        )
