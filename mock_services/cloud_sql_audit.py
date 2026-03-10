"""Mock Cloud SQL audit database — append-only."""

import json
import sqlite3
from typing import Optional
from config.settings import MOCK_DATA_DIR
from schemas.models import AuditLogEntry


class MockAuditDB:
    """SQLite-backed audit log — append-only, no updates or deletes."""

    def __init__(self):
        self._db_path = MOCK_DATA_DIR / "audit_writable.db"
        self._init_db()

    def _init_db(self):
        """Initialize the audit database with proper schema."""
        conn = sqlite3.connect(str(self._db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trace_id TEXT NOT NULL,
                step_sequence INTEGER NOT NULL,
                agent_id TEXT NOT NULL,
                policy_id TEXT NOT NULL,
                customer_id TEXT NOT NULL,
                agent_input TEXT NOT NULL,
                agent_response TEXT NOT NULL,
                evidence TEXT,
                critique_result TEXT,
                critique_score REAL,
                compliance_verdict TEXT,
                rag_sources TEXT,
                model_version TEXT,
                pii_masked INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
        conn.close()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def write_audit_log(self, entry: AuditLogEntry) -> None:
        """Write an audit log entry (append-only)."""
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO agent_audit_log 
               (trace_id, step_sequence, agent_id, policy_id, customer_id,
                agent_input, agent_response, evidence, critique_result,
                critique_score, compliance_verdict, rag_sources, model_version, pii_masked)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry.trace_id,
                entry.step_sequence,
                entry.agent_id,
                entry.policy_id,
                entry.customer_id,
                json.dumps(entry.agent_input, default=str),
                json.dumps(entry.agent_response, default=str),
                json.dumps(entry.evidence, default=str) if entry.evidence else None,
                entry.critique_result.model_dump_json() if entry.critique_result else None,
                entry.critique_score,
                entry.compliance_verdict,
                json.dumps(entry.rag_sources) if entry.rag_sources else None,
                entry.model_version,
                1 if entry.pii_masked else 0,
            ),
        )
        conn.commit()
        conn.close()

    def get_trace(self, trace_id: str) -> list[dict]:
        """Get all audit entries for a trace."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM agent_audit_log WHERE trace_id = ? ORDER BY step_sequence",
            (trace_id,),
        ).fetchall()
        conn.close()
        return [self._row_to_dict(row) for row in rows]

    def get_policy_history(self, policy_id: str) -> list[dict]:
        """Get all interactions for a policy."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM agent_audit_log WHERE policy_id = ? ORDER BY created_at DESC",
            (policy_id,),
        ).fetchall()
        conn.close()
        return [self._row_to_dict(row) for row in rows]

    def get_recent_logs(self, limit: int = 100) -> list[dict]:
        """Get the most recent audit log entries."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM agent_audit_log ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        conn.close()
        return [self._row_to_dict(row) for row in rows]

    def _row_to_dict(self, row: sqlite3.Row) -> dict:
        """Convert a SQLite row to a dictionary."""
        d = dict(row)
        # Parse JSON fields
        for field in ("agent_input", "agent_response", "evidence", "critique_result", "rag_sources"):
            if d.get(field):
                try:
                    d[field] = json.loads(d[field])
                except (json.JSONDecodeError, TypeError):
                    pass
        return d
