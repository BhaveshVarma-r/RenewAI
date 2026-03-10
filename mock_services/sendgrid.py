"""Mock SendGrid email client."""

import os
import uuid
import hashlib
from datetime import datetime
from config.settings import LOGS_DIR, MOCK_EMAIL_OPEN_RATE


class MockSendGridClient:
    """Simulates SendGrid email service with delivery tracking."""

    def __init__(self):
        self._sent_emails: dict[str, dict] = {}
        self._email_dir = LOGS_DIR / "emails"
        self._email_dir.mkdir(parents=True, exist_ok=True)

    async def send_email(
        self,
        to: str,
        subject: str,
        html_body: str,
        language: str,
        policy_id: str,
    ) -> dict:
        """Send an email and save it to the logs directory."""
        message_id = f"sg-mock-{uuid.uuid4()}"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{policy_id}.html"

        # Build full HTML document
        full_html = f"""<!DOCTYPE html>
<html lang="{language}">
<head>
    <meta charset="UTF-8">
    <title>{subject}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #1a237e; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ padding: 20px; border: 1px solid #e0e0e0; }}
        .footer {{ background: #f5f5f5; padding: 15px; font-size: 12px; color: #666; border-radius: 0 0 8px 8px; }}
        .cta {{ background: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Suraksha Life Insurance</h1>
    </div>
    <div class="content">
        <p><strong>To:</strong> {to}</p>
        <p><strong>Subject:</strong> {subject}</p>
        <p><strong>Language:</strong> {language}</p>
        <p><strong>Policy ID:</strong> {policy_id}</p>
        <hr>
        {html_body}
    </div>
    <div class="footer">
        <p>Message ID: {message_id}</p>
        <p>Sent at: {datetime.now().isoformat()}</p>
    </div>
</body>
</html>"""

        # Save to file
        filepath = self._email_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(full_html)

        self._sent_emails[message_id] = {
            "to": to,
            "subject": subject,
            "language": language,
            "policy_id": policy_id,
            "sent_at": datetime.now().isoformat(),
            "filepath": str(filepath),
        }

        return {"message_id": message_id, "status": "delivered"}

    async def get_open_rate(self, message_id: str) -> dict:
        """Simulate open rate — deterministic 42% based on message_id hash."""
        seed = int(hashlib.md5(message_id.encode()).hexdigest(), 16)
        opened = (seed % 100) < int(MOCK_EMAIL_OPEN_RATE * 100)
        clicked = opened and (seed % 200) < 30  # ~15% click-through of opened
        opened_at = datetime.now().isoformat() if opened else None

        return {
            "opened": opened,
            "clicked": clicked,
            "opened_at": opened_at,
        }

    async def track_click(self, message_id: str) -> dict:
        """Track click events for a message."""
        seed = int(hashlib.md5(message_id.encode()).hexdigest(), 16)
        clicked = (seed % 200) < 30
        return {"clicked": clicked}
