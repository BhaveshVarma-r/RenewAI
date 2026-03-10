"""Mock BigQuery analytics client backed by SQLite."""

import json
import sqlite3
from datetime import datetime
from typing import Optional
from config.settings import MOCK_DATA_DIR


class MockBigQueryClient:
    """SQLite-backed analytics store simulating BigQuery."""

    def __init__(self):
        self._db_path = MOCK_DATA_DIR / "analytics_writable.db"
        self._init_db()

    def _init_db(self):
        """Initialize all analytics tables."""
        conn = sqlite3.connect(str(self._db_path))
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS customer_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trace_id TEXT,
                policy_id TEXT,
                customer_id TEXT,
                channel TEXT,
                interaction_type TEXT,
                outcome TEXT,
                converted INTEGER,
                escalated INTEGER,
                duration_seconds INTEGER,
                language TEXT,
                risk_tier TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS kpi_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                dimension TEXT,
                period TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS critique_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trace_id TEXT,
                agent_id TEXT,
                verdict TEXT,
                score REAL,
                tone_score REAL,
                language_quality_score REAL,
                hallucination_detected INTEGER,
                retry_count INTEGER,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS compliance_verdicts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trace_id TEXT,
                policy_id TEXT,
                verdict TEXT,
                violations TEXT,
                irdai_disclosure INTEGER,
                opt_out_present INTEGER,
                grievance_number INTEGER,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS channel_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel TEXT NOT NULL,
                total_attempts INTEGER DEFAULT 0,
                conversions INTEGER DEFAULT 0,
                escalations INTEGER DEFAULT 0,
                avg_critique_score REAL,
                period TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)
        conn.commit()
        conn.close()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    async def async_insert(self, table: str, rows: list[dict]) -> dict:
        """Insert rows into a table (simulates Pub/Sub async sync)."""
        conn = self._get_conn()
        for row in rows:
            columns = ", ".join(row.keys())
            placeholders = ", ".join(["?" for _ in row])
            values = [
                json.dumps(v, default=str) if isinstance(v, (dict, list)) else v
                for v in row.values()
            ]
            conn.execute(
                f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
                values,
            )
        conn.commit()
        conn.close()
        return {"inserted": len(rows), "table": table}

    def query(self, sql: str) -> list[dict]:
        """Execute a query and return results."""
        conn = self._get_conn()
        try:
            rows = conn.execute(sql).fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            return [{"error": str(e)}]
        finally:
            conn.close()

    async def get_kpi_summary(self) -> dict:
        """Get aggregated KPI metrics."""
        conn = self._get_conn()

        # Total interactions
        total = conn.execute("SELECT COUNT(*) as count FROM customer_interactions").fetchone()
        conversions = conn.execute("SELECT COUNT(*) as count FROM customer_interactions WHERE converted = 1").fetchone()
        escalations = conn.execute("SELECT COUNT(*) as count FROM customer_interactions WHERE escalated = 1").fetchone()

        total_count = total["count"] if total else 0
        conversion_count = conversions["count"] if conversions else 0
        escalation_count = escalations["count"] if escalations else 0

        # Channel breakdown
        channels = conn.execute("""
            SELECT channel,
                   COUNT(*) as attempts,
                   SUM(CASE WHEN converted = 1 THEN 1 ELSE 0 END) as conversions,
                   SUM(CASE WHEN escalated = 1 THEN 1 ELSE 0 END) as escalations
            FROM customer_interactions
            GROUP BY channel
        """).fetchall()

        # Critique stats
        critique_stats = conn.execute("""
            SELECT AVG(score) as avg_score,
                   SUM(CASE WHEN verdict = 'APPROVED' THEN 1 ELSE 0 END) as approved,
                   SUM(CASE WHEN verdict = 'REJECTED' THEN 1 ELSE 0 END) as rejected
            FROM critique_logs
        """).fetchone()

        conn.close()

        persistency_rate = (conversion_count / max(total_count, 1)) * 100
        escalation_rate = (escalation_count / max(total_count, 1)) * 100
        cost_per_renewal = 15.50 if conversion_count > 0 else 0  # Simulated

        return {
            "total_interactions": total_count,
            "conversions": conversion_count,
            "escalations": escalation_count,
            "persistency_rate": round(persistency_rate, 2),
            "escalation_rate": round(escalation_rate, 2),
            "cost_per_renewal": cost_per_renewal,
            "channel_performance": [dict(ch) for ch in channels],
            "critique_stats": {
                "avg_score": round(critique_stats["avg_score"] or 0, 2) if critique_stats else 0,
                "approved": critique_stats["approved"] if critique_stats else 0,
                "rejected": critique_stats["rejected"] if critique_stats else 0,
            },
            "timestamp": datetime.now().isoformat(),
        }
