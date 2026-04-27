"""In-memory conversation sessions (per session_id)."""

from __future__ import annotations

import os
import threading
import uuid
from dataclasses import dataclass, field
from typing import Any


def _max_history() -> int:
    try:
        return max(4, min(int(os.environ.get("PYX13_MAX_HISTORY", "40")), 200))
    except ValueError:
        return 40


@dataclass
class Session:
    messages: list[dict[str, str]] = field(default_factory=list)

    def append(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        cap = _max_history()
        if len(self.messages) > cap:
            self.messages = self.messages[-cap:]

    def snapshot(self) -> list[dict[str, str]]:
        return list(self.messages)


class SessionStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._by_id: dict[str, Session] = {}

    def get_or_create(self, session_id: str | None) -> tuple[str, Session]:
        sid = (session_id or "").strip() or str(uuid.uuid4())
        with self._lock:
            if sid not in self._by_id:
                self._by_id[sid] = Session()
            return sid, self._by_id[sid]

    def reset(self, session_id: str) -> bool:
        with self._lock:
            if session_id in self._by_id:
                self._by_id[session_id] = Session()
                return True
            return False

    def export(self, session_id: str) -> list[dict[str, Any]] | None:
        with self._lock:
            s = self._by_id.get(session_id)
            if not s:
                return None
            return s.snapshot()
