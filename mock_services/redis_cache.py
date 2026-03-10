"""Mock Redis client with in-memory dict + TTL simulation."""

import time
import json
from typing import Any, Optional


class MockRedisClient:
    """In-memory key-value store simulating Redis with TTL support."""

    def __init__(self):
        self._store: dict[str, dict] = {}  # key -> {"value": ..., "expires_at": float|None}

    def _is_expired(self, key: str) -> bool:
        """Check if a key has expired."""
        if key not in self._store:
            return True
        entry = self._store[key]
        if entry.get("expires_at") and time.time() > entry["expires_at"]:
            del self._store[key]
            return True
        return False

    def get(self, key: str) -> Optional[str]:
        """Get a value by key."""
        if self._is_expired(key):
            return None
        return self._store[key]["value"]

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set a key-value pair with optional TTL."""
        expires_at = time.time() + ttl_seconds if ttl_seconds else None
        if not isinstance(value, str):
            value = json.dumps(value)
        self._store[key] = {"value": value, "expires_at": expires_at}

    def delete(self, key: str) -> bool:
        """Delete a key."""
        if key in self._store:
            del self._store[key]
            return True
        return False

    def incr(self, key: str, ttl_seconds: Optional[int] = None) -> int:
        """Increment a counter. Creates it if it doesn't exist."""
        if self._is_expired(key):
            expires_at = time.time() + ttl_seconds if ttl_seconds else None
            self._store[key] = {"value": "1", "expires_at": expires_at}
            return 1
        current = int(self._store[key]["value"])
        current += 1
        self._store[key]["value"] = str(current)
        return current

    def exists(self, key: str) -> bool:
        """Check if a key exists and is not expired."""
        return not self._is_expired(key)

    def get_session(self, session_id: str) -> Optional[dict]:
        """Get a WhatsApp session state."""
        raw = self.get(f"session:{session_id}")
        if raw:
            return json.loads(raw)
        return None

    def set_session(self, session_id: str, state: dict, ttl: int = 259200) -> None:
        """Set a WhatsApp session state (default TTL 72h)."""
        self.set(f"session:{session_id}", json.dumps(state), ttl)

    def check_rate_limit(self, customer_id: str, channel: str) -> bool:
        """Check if rate limit exceeded (max 3 per channel per week).
        
        Returns True if within limit (OK to proceed).
        """
        key = f"rate_limit:{customer_id}:{channel}"
        count = self.incr(key, ttl_seconds=604800)  # 7 days TTL
        return count <= 3
