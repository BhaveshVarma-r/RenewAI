"""Mock Razorpay payment client."""

import uuid
import hashlib
from datetime import datetime, timedelta
from config.settings import MOCK_PAYMENT_SUCCESS_RATE


class MockPaymentClient:
    """Simulates Razorpay payment gateway."""

    def __init__(self):
        self._payments: dict[str, dict] = {}

    async def create_payment_link(
        self,
        amount: float,
        policy_id: str,
        customer_name: str,
    ) -> dict:
        """Create a payment link for premium collection."""
        payment_id = f"pay-mock-{uuid.uuid4()}"
        link_uuid = str(uuid.uuid4())[:8]
        expires_at = (datetime.now() + timedelta(hours=24)).isoformat()

        payment_data = {
            "payment_id": payment_id,
            "payment_link": f"https://rzp.mock/pay/{link_uuid}",
            "upi_id": f"renewai.{policy_id}@upi",
            "expires_at": expires_at,
            "amount": amount,
            "customer_name": customer_name,
            "policy_id": policy_id,
            "created_at": datetime.now().isoformat(),
        }

        self._payments[payment_id] = payment_data

        return {
            "payment_id": payment_id,
            "payment_link": payment_data["payment_link"],
            "upi_id": payment_data["upi_id"],
            "expires_at": expires_at,
        }

    async def check_payment_status(self, payment_id: str) -> dict:
        """Check payment status — deterministic 35% paid simulation."""
        seed = int(hashlib.md5(payment_id.encode()).hexdigest(), 16)
        paid = (seed % 100) < int(MOCK_PAYMENT_SUCCESS_RATE * 100)
        payment = self._payments.get(payment_id, {})
        amount = payment.get("amount", 0.0)

        if paid:
            return {
                "status": "paid",
                "amount": amount,
                "paid_at": datetime.now().isoformat(),
            }
        else:
            # Check if expired
            expires_at = payment.get("expires_at", "")
            if expires_at:
                try:
                    exp_time = datetime.fromisoformat(expires_at)
                    if datetime.now() > exp_time:
                        return {"status": "expired", "amount": amount, "paid_at": None}
                except ValueError:
                    pass
            return {"status": "pending", "amount": amount, "paid_at": None}
