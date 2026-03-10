"""Mock Exotel voice call client."""

import uuid
import hashlib
import random
from datetime import datetime
from config.settings import LOGS_DIR


class MockExotelClient:
    """Simulates Exotel voice call API with DND checking."""

    def __init__(self):
        self._call_dir = LOGS_DIR / "calls"
        self._call_dir.mkdir(parents=True, exist_ok=True)

    def check_dnd_status(self, phone: str) -> bool:
        """Check if a phone number is on the DND registry.
        
        Returns True for ~5% of numbers (deterministic hash-based).
        """
        phone_hash = int(hashlib.md5(phone.encode()).hexdigest(), 16)
        return (phone_hash % 100) < 5

    async def make_call(
        self,
        phone: str,
        script: str,
        language: str,
        policy_id: str,
        risk_tier: str = "medium",
    ) -> dict:
        """Simulate making a voice call with the given script."""
        call_id = f"call-mock-{uuid.uuid4()}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Log full script to file
        filename = f"{timestamp}_{policy_id}.txt"
        filepath = self._call_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Call ID: {call_id}\n")
            f.write(f"Phone: {phone}\n")
            f.write(f"Language: {language}\n")
            f.write(f"Policy ID: {policy_id}\n")
            f.write(f"Risk Tier: {risk_tier}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write(f"\n{'='*60}\n")
            f.write(f"CALL SCRIPT\n{'='*60}\n\n")
            f.write(script)

        # Simulate outcome by risk_tier
        seed = int(hashlib.md5(f"{phone}_{policy_id}".encode()).hexdigest(), 16)
        rng = random.Random(seed)

        outcome_weights = {
            "low": {"converted": 70, "objection": 20, "no_answer": 10},
            "medium": {"converted": 45, "objection": 35, "no_answer": 20},
            "high": {"converted": 20, "objection": 40, "no_answer": 40},
            "critical": {"converted": 10, "objection": 30, "no_answer": 60},
        }

        weights = outcome_weights.get(risk_tier, outcome_weights["medium"])
        outcomes = list(weights.keys())
        probs = list(weights.values())
        outcome = rng.choices(outcomes, weights=probs, k=1)[0]

        objection_bank = [
            "Premium is too high",
            "I have another policy",
            "I don't need insurance anymore",
            "Financial difficulties",
            "Want to talk to agent",
            "Need more time to decide",
            "Not happy with the service",
        ]

        objections_raised = []
        if outcome == "objection":
            num_objections = rng.randint(1, 3)
            objections_raised = rng.sample(objection_bank, min(num_objections, len(objection_bank)))

        duration = {
            "converted": rng.randint(180, 420),
            "objection": rng.randint(120, 300),
            "no_answer": rng.randint(15, 60),
        }

        transcript_templates = {
            "converted": f"Agent: Good day, this is Suraksha Life Insurance calling about policy {policy_id}.\n"
                        f"Customer: Yes, I was expecting your call.\n"
                        f"Agent: [Delivers script]\n"
                        f"Customer: Okay, I'll make the payment. Please send me the link.\n"
                        f"Agent: Thank you! I'll send the payment link right away.\n",
            "objection": f"Agent: Good day, this is Suraksha Life Insurance calling about policy {policy_id}.\n"
                        f"Customer: Yes, what is it?\n"
                        f"Agent: [Delivers script]\n"
                        f"Customer: {'; '.join(objections_raised) if objections_raised else 'I need to think about it.'}\n"
                        f"Agent: I understand your concerns. Let me explain...\n",
            "no_answer": f"[Call to {phone} - No answer after {duration['no_answer']} seconds]\n"
                        f"[Voicemail left with renewal reminder]\n",
        }

        return {
            "call_id": call_id,
            "outcome": outcome,
            "duration_seconds": duration.get(outcome, 60),
            "objections_raised": objections_raised,
            "transcript": transcript_templates.get(outcome, ""),
            "converted": outcome == "converted",
        }
