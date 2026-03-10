"""Human queue service — manages escalated cases."""

import json
import sqlite3
import uuid
from datetime import datetime
from typing import Optional
from config.settings import MOCK_DATA_DIR
from services.gemini_client import GeminiClient
from mock_services.cloud_sql_audit import MockAuditDB
from schemas.models import AuditLogEntry

gemini = GeminiClient()
audit_db = MockAuditDB()


class HumanQueueService:
    """SQLite-backed queue for human-escalated cases."""

    def __init__(self):
        self._db_path = MOCK_DATA_DIR / "human_queue_writable.db"
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(str(self._db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS human_queue (
                queue_id TEXT PRIMARY KEY,
                trace_id TEXT NOT NULL,
                policy_id TEXT NOT NULL,
                priority INTEGER DEFAULT 3,
                reason TEXT,
                context_briefing TEXT,
                status TEXT DEFAULT 'pending',
                assigned_to TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                resolved_at TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    async def add_to_queue(self, state: dict, reason: str) -> str:
        """Add a case to the human queue with auto-generated briefing."""
        queue_id = f"HQ-{uuid.uuid4().hex[:8].upper()}"
        trace_id = state.get("trace_id", "")
        policy_id = state.get("policy_id", "")
        policy_data = state.get("policy_data", {})

        # Determine priority from risk tier
        priority_map = {"critical": 1, "high": 2, "medium": 3, "low": 4}
        risk_tier = policy_data.get("risk_tier", "medium") if isinstance(policy_data, dict) else "medium"
        priority = priority_map.get(risk_tier, 3)
        if "distress" in reason.lower():
            priority = 1

        # Generate context briefing
        try:
            briefing_prompt = f"""Summarize this insurance renewal case for a human specialist:
Policy: {policy_data.get('policy_id', policy_id)}
Customer: {policy_data.get('customer_name', 'N/A')}
Premium: ₹{policy_data.get('premium_amount', 0):,.2f}
Risk: {risk_tier}
Escalation Reason: {reason}
Interaction History: {json.dumps(state.get('interaction_history', []), default=str)[:500]}
Be concise (max 200 words)."""
            briefing = await gemini.generate_flash(briefing_prompt, "Summarize concisely for a human specialist.")
        except Exception:
            briefing = f"Policy {policy_id} escalated: {reason}. Risk: {risk_tier}. Review required."

        conn = self._get_conn()
        conn.execute(
            "INSERT INTO human_queue (queue_id, trace_id, policy_id, priority, reason, context_briefing) VALUES (?, ?, ?, ?, ?, ?)",
            (queue_id, trace_id, policy_id, priority, reason, briefing),
        )
        conn.commit()
        conn.close()
        return queue_id

    def get_pending_cases(self) -> list[dict]:
        """Get all pending cases sorted by priority."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM human_queue WHERE status = 'pending' ORDER BY priority ASC, created_at ASC"
        ).fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_all_cases(self) -> list[dict]:
        """Get all cases."""
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM human_queue ORDER BY created_at DESC").fetchall()
        conn.close()
        return [dict(row) for row in rows]

    async def assign_case(self, queue_id: str, specialist_role: str = "renewal_specialist") -> dict:
        """Assign a case to a specialist."""
        conn = self._get_conn()
        conn.execute(
            "UPDATE human_queue SET status = 'assigned', assigned_to = ? WHERE queue_id = ?",
            (specialist_role, queue_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM human_queue WHERE queue_id = ?", (queue_id,)).fetchone()
        conn.close()
        return dict(row) if row else {}

    async def resolve_case(self, queue_id: str, resolution: str, notes: str) -> dict:
        """Resolve a human queue case."""
        conn = self._get_conn()
        conn.execute(
            "UPDATE human_queue SET status = 'resolved', resolved_at = datetime('now') WHERE queue_id = ?",
            (queue_id,),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM human_queue WHERE queue_id = ?", (queue_id,)).fetchone()
        conn.close()

        case = dict(row) if row else {}

        # Log resolution to audit
        audit_db.write_audit_log(AuditLogEntry(
            trace_id=case.get("trace_id", ""),
            step_sequence=99,
            agent_id="human_queue",
            policy_id=case.get("policy_id", ""),
            customer_id="",
            agent_input={"queue_id": queue_id, "resolution": resolution},
            agent_response={"status": "resolved", "notes": notes},
        ))

        return case
