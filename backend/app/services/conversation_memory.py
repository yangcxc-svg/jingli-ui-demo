from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Literal


Role = Literal["user", "assistant"]


@dataclass(frozen=True)
class ConversationMessage:
    role: Role
    content: str


class ConversationMemory:
    """Process-local conversation memory for the MVP.

    This keeps recent turns available while the backend process is running.
    It is intentionally small and can later be replaced by PostgreSQL-backed
    persistence behind the same service boundary.
    """

    _instance: "ConversationMemory | None" = None
    _instance_lock = threading.Lock()

    def __new__(cls) -> "ConversationMemory":
        with cls._instance_lock:
            if cls._instance is None:
                inst = super().__new__(cls)
                inst._messages = {}  # type: ignore[attr-defined]
                inst._lock = threading.Lock()  # type: ignore[attr-defined]
                cls._instance = inst
        return cls._instance

    _messages: dict[str, list[ConversationMessage]]
    _lock: threading.Lock

    def get_recent(
        self, conversation_id: str, *, max_messages: int = 16
    ) -> list[ConversationMessage]:
        with self._lock:
            return list(self._messages.get(conversation_id, [])[-max_messages:])

    def append_pair(
        self,
        conversation_id: str,
        *,
        user_message: str,
        assistant_message: str,
        max_messages: int = 16,
    ) -> None:
        if not user_message.strip() or not assistant_message.strip():
            return
        with self._lock:
            items = self._messages.setdefault(conversation_id, [])
            items.extend(
                [
                    ConversationMessage(role="user", content=user_message),
                    ConversationMessage(role="assistant", content=assistant_message),
                ]
            )
            if len(items) > max_messages:
                self._messages[conversation_id] = items[-max_messages:]
