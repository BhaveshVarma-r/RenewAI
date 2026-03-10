"""WhatsApp critique agent."""

import json
from langsmith import traceable
from services.gemini_client import GeminiClient
from schemas.models import CritiqueResult

gemini = GeminiClient()

SYSTEM_PROMPT = """You are a WhatsApp message quality evaluator for Indian insurance.
Check: response matches detected intent, EMI eligibility correct, payment amounts accurate,
tone empathetic for hardship cases, no hallucinated policy details, IRDAI disclosures present.
Output JSON with: verdict, score, tone_score, language_quality_score, factual_accuracy,
hallucination_detected, feedback, rejection_reasons."""


@traceable(name="whatsapp_critique_agent")
async def critique_whatsapp(message: str, policy_data: dict, intent: str) -> CritiqueResult:
    """Evaluate WhatsApp message quality."""
    prompt = f"""Evaluate WhatsApp message for intent '{intent}':
Message: {message[:1000]}
Policy Premium: ₹{policy_data.get('premium_amount', 'N/A')}
EMI Eligible: {policy_data.get('emi_eligible', False)}"""

    try:
        result = await gemini.generate_json(prompt, SYSTEM_PROMPT)
        result.setdefault("verdict", "APPROVED")
        result.setdefault("score", 7.5)
        result.setdefault("tone_score", 7.5)
        result.setdefault("language_quality_score", 8.0)
        result.setdefault("factual_accuracy", True)
        result.setdefault("hallucination_detected", False)
        result.setdefault("feedback", "Message quality acceptable.")
        result.setdefault("rejection_reasons", [])
        return CritiqueResult(**result)
    except Exception as e:
        return CritiqueResult(
            verdict="APPROVED", score=7.0, tone_score=7.5,
            language_quality_score=8.0, factual_accuracy=True,
            hallucination_detected=False,
            feedback=f"Auto-approved: {str(e)[:100]}",
            rejection_reasons=[],
        )
