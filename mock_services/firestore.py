"""Mock Firestore client backed by SQLite."""

import json
import sqlite3
from typing import Optional, Any
from config.settings import MOCK_DATA_DIR


class MockFirestoreClient:
    """SQLite-backed document store simulating Firestore."""

    def __init__(self):
        self._db_path = MOCK_DATA_DIR / "firestore_writable.db"
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database."""
        conn = sqlite3.connect(str(self._db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                collection TEXT NOT NULL,
                doc_id TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                PRIMARY KEY (collection, doc_id)
            )
        """)
        conn.commit()
        conn.close()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def set_document(self, collection: str, doc_id: str, data: dict) -> None:
        """Set a document (create or overwrite)."""
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO documents (collection, doc_id, data)
               VALUES (?, ?, ?)
               ON CONFLICT(collection, doc_id)
               DO UPDATE SET data = excluded.data, updated_at = datetime('now')""",
            (collection, doc_id, json.dumps(data, default=str)),
        )
        conn.commit()
        conn.close()

    def get_document(self, collection: str, doc_id: str) -> Optional[dict]:
        """Get a document by collection and ID."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT data FROM documents WHERE collection = ? AND doc_id = ?",
            (collection, doc_id),
        ).fetchone()
        conn.close()
        if row:
            return json.loads(row["data"])
        return None

    def update_document(self, collection: str, doc_id: str, updates: dict) -> bool:
        """Update specific fields of a document."""
        existing = self.get_document(collection, doc_id)
        if existing is None:
            return False
        existing.update(updates)
        self.set_document(collection, doc_id, existing)
        return True

    def query_collection(self, collection: str, filters: Optional[dict] = None) -> list[dict]:
        """Query all documents in a collection, optionally filtered."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT doc_id, data FROM documents WHERE collection = ?",
            (collection,),
        ).fetchall()
        conn.close()

        results = []
        for row in rows:
            doc = json.loads(row["data"])
            doc["_id"] = row["doc_id"]

            if filters:
                match = True
                for key, val in filters.items():
                    if doc.get(key) != val:
                        match = False
                        break
                if not match:
                    continue

            results.append(doc)

        return results

    def delete_document(self, collection: str, doc_id: str) -> bool:
        """Delete a document."""
        conn = self._get_conn()
        cursor = conn.execute(
            "DELETE FROM documents WHERE collection = ? AND doc_id = ?",
            (collection, doc_id),
        )
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted
