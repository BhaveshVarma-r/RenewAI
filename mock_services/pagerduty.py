"""Mock PagerDuty alerting service."""

import json
import sqlite3
import uuid
from datetime import datetime
from config.settings import LOGS_DIR, MOCK_DATA_DIR


# ANSI color codes for console output
COLORS = {
    "critical": "\033[91m",  # Red
    "high": "\033[93m",      # Yellow
    "medium": "\033[94m",    # Blue
    "low": "\033[92m",       # Green
    "reset": "\033[0m",
}


class MockPagerDuty:
    """Simulates PagerDuty alerting with colored console output and persistence."""

    ALERT_TYPES = [
        "PII_LEAK", "MIS_SELLING", "DISTRESS_DETECTED",
        "COMPLIANCE_VIOLATION", "CRITIQUE_MAX_RETRIES", "SYSTEM_ERROR",
    ]

    def __init__(self):
        self._alert_dir = LOGS_DIR / "alerts"
        self._alert_dir.mkdir(parents=True, exist_ok=True)
        self._critical_db_path = MOCK_DATA_DIR / "critical_alerts_writable.db"
        self._init_critical_db()

    def _init_critical_db(self):
        """Initialize critical alerts database."""
        conn = sqlite3.connect(str(self._critical_db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS critical_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT NOT NULL,
                title TEXT NOT NULL,
                severity TEXT NOT NULL,
                details TEXT,
                source_agent TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
        conn.close()

    async def trigger_alert(
        self,
        title: str,
        severity: str = "medium",
        details: dict | None = None,
        source_agent: str = "unknown",
    ) -> dict:
        """Trigger an alert.
        
        Args:
            title: Alert title
            severity: critical | high | medium | low
            details: Additional alert details
            source_agent: Which agent triggered the alert
        """
        alert_id = f"alert-{uuid.uuid4()}"
        timestamp = datetime.now()

        # Print colored console output
        color = COLORS.get(severity, COLORS["reset"])
        reset = COLORS["reset"]
        print(f"\n{color}{'='*60}")
        print(f"🚨 PAGERDUTY ALERT [{severity.upper()}]")
        print(f"Title: {title}")
        print(f"Source: {source_agent}")
        print(f"Time: {timestamp.isoformat()}")
        if details:
            print(f"Details: {json.dumps(details, indent=2, default=str)}")
        print(f"{'='*60}{reset}\n")

        # Save to file
        alert_data = {
            "alert_id": alert_id,
            "title": title,
            "severity": severity,
            "details": details,
            "source_agent": source_agent,
            "created_at": timestamp.isoformat(),
        }

        filename = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_alert.json"
        filepath = self._alert_dir / filename
        with open(filepath, "w") as f:
            json.dump(alert_data, f, indent=2, default=str)

        # Critical alerts also go to SQLite
        if severity == "critical":
            conn = sqlite3.connect(str(self._critical_db_path))
            conn.execute(
                "INSERT INTO critical_alerts (alert_id, title, severity, details, source_agent) VALUES (?, ?, ?, ?, ?)",
                (alert_id, title, severity, json.dumps(details, default=str), source_agent),
            )
            conn.commit()
            conn.close()

        return {"alert_id": alert_id, "status": "triggered", "severity": severity}
