"""Mock Gupshup WhatsApp client."""

import uuid
import sqlite3
import hashlib
import random
from datetime import datetime
from config.settings import MOCK_DATA_DIR


class MockGupshupClient:
    """Simulates Gupshup WhatsApp Business API."""

    def __init__(self):
        self._db_path = MOCK_DATA_DIR / "whatsapp_messages_writable.db"
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database for message storage."""
        conn = sqlite3.connect(str(self._db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS whatsapp_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                msg_id TEXT NOT NULL,
                phone TEXT NOT NULL,
                message TEXT NOT NULL,
                quick_replies TEXT,
                policy_id TEXT,
                direction TEXT DEFAULT 'outbound',
                status TEXT DEFAULT 'sent',
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
        conn.close()

    async def send_message(
        self,
        phone: str,
        message: str,
        quick_replies: list[str] | None = None,
        policy_id: str = "",
    ) -> dict:
        """Send a WhatsApp message."""
        msg_id = f"wa-mock-{uuid.uuid4()}"

        conn = sqlite3.connect(str(self._db_path))
        conn.execute(
            "INSERT INTO whatsapp_messages (msg_id, phone, message, quick_replies, policy_id) VALUES (?, ?, ?, ?, ?)",
            (msg_id, phone, message, str(quick_replies or []), policy_id),
        )
        conn.commit()
        conn.close()

        return {"msg_id": msg_id, "status": "sent"}

    async def send_payment_qr(
        self,
        phone: str,
        amount: float,
        policy_id: str,
        payment_link: str,
    ) -> dict:
        """Send a payment QR code via WhatsApp."""
        msg_id = f"wa-qr-{uuid.uuid4()}"

        conn = sqlite3.connect(str(self._db_path))
        conn.execute(
            "INSERT INTO whatsapp_messages (msg_id, phone, message, policy_id) VALUES (?, ?, ?, ?)",
            (msg_id, phone, f"[QR CODE] Amount: ₹{amount:.2f} | Link: {payment_link}", policy_id),
        )
        conn.commit()
        conn.close()

        return {"status": "sent", "qr_sent": True, "msg_id": msg_id}

    async def simulate_inbound_reply(self, phone: str, risk_tier: str) -> dict:
        """Simulate a customer reply based on risk tier probabilities."""
        # Deterministic seed from phone
        seed = int(hashlib.md5(phone.encode()).hexdigest(), 16) % 10000
        rng = random.Random(seed)

        weights = {
            "low": {"pay_intent": 60, "emi_request": 20, "receipt": 10, "no_response": 10},
            "medium": {"pay_intent": 30, "emi_request": 30, "hardship": 20, "no_response": 20},
            "high": {"pay_intent": 10, "emi_request": 20, "hardship": 40, "human_request": 30},
            "critical": {"pay_intent": 5, "emi_request": 10, "hardship": 30, "no_response": 55},
        }

        tier_weights = weights.get(risk_tier, weights["medium"])
        intents = list(tier_weights.keys())
        probs = list(tier_weights.values())
        intent = rng.choices(intents, weights=probs, k=1)[0]

        messages = {
            "pay_intent": "Haan, main payment kar dunga. Link bhejo.",
            "emi_request": "Kya EMI mein payment ho sakta hai?",
            "receipt": "Mujhe pichli payment ki receipt chahiye.",
            "no_response": "",
            "hardship": "Abhi bahut mushkil hai, paisa nahi hai.",
            "human_request": "Mujhe kisi se baat karni hai, please connect karo.",
        }

        sentiment_scores = {
            "pay_intent": 0.8,
            "emi_request": 0.5,
            "receipt": 0.6,
            "no_response": 0.0,
            "hardship": 0.2,
            "human_request": 0.3,
        }

        return {
            "intent": intent,
            "raw_message": messages.get(intent, ""),
            "sentiment_score": sentiment_scores.get(intent, 0.5),
        }
