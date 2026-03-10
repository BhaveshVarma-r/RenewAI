"""Mock Vertex AI propensity scorer."""


class MockPropensityScorer:
    """Simulates an ML model for lapse propensity scoring."""

    async def get_lapse_score(
        self,
        policy_id: str,
        payment_history: list[str],
        days_to_due: int,
        risk_tier: str,
        premium_amount: float,
    ) -> dict:
        """Calculate deterministic lapse propensity score.
        
        Scoring logic:
        - Base score from risk_tier
        - +0.1 per late/missed payment
        - +0.05 if days_to_due < 10
        - +0.03 if premium_amount > 50000
        - Capped at 0.99
        """
        base_scores = {
            "low": 0.1,
            "medium": 0.35,
            "high": 0.65,
            "critical": 0.85,
        }

        score = base_scores.get(risk_tier, 0.35)

        # Add penalty for late payments
        for payment in payment_history:
            if payment in ("late", "missed", "partial"):
                score += 0.1

        # Urgency penalty
        if days_to_due is not None and days_to_due < 10:
            score += 0.05

        # High premium risk
        if premium_amount > 50000:
            score += 0.03

        # Cap at 0.99
        score = min(score, 0.99)

        # Determine risk level from score
        if score < 0.25:
            risk_level = "low"
        elif score < 0.50:
            risk_level = "medium"
        elif score < 0.75:
            risk_level = "high"
        else:
            risk_level = "critical"

        # Build key factors
        key_factors = []
        if risk_tier in ("high", "critical"):
            key_factors.append(f"High base risk tier: {risk_tier}")
        late_count = sum(1 for p in payment_history if p in ("late", "missed", "partial"))
        if late_count > 0:
            key_factors.append(f"{late_count} late/missed payments in history")
        if days_to_due is not None and days_to_due < 10:
            key_factors.append(f"Only {days_to_due} days to due date")
        if premium_amount > 50000:
            key_factors.append(f"High premium amount: ₹{premium_amount:,.2f}")

        # Recommend channel based on score
        if score < 0.3:
            recommended_channel = "email"
        elif score < 0.6:
            recommended_channel = "whatsapp"
        else:
            recommended_channel = "voice"

        # Recommend time
        recommended_time = "evening" if score > 0.5 else "morning"

        # EMI recommended for scores > 0.4 and premium > 20000
        emi_recommended = score > 0.4 and premium_amount > 20000

        return {
            "lapse_probability": round(score, 4),
            "risk_level": risk_level,
            "key_factors": key_factors,
            "recommended_channel": recommended_channel,
            "recommended_time": recommended_time,
            "emi_recommended": emi_recommended,
        }
