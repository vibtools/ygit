from __future__ import annotations

import asyncio
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from backend.core.ids import new_id


class JsonSessionStore(ABC):
    @abstractmethod
    async def set_json(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None: ...

    @abstractmethod
    async def get_json(self, key: str) -> dict[str, Any] | None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...


class MemoryJsonSessionStore(JsonSessionStore):
    """Development/test fallback only. Production must use Redis."""

    def __init__(self) -> None:
        self._data: dict[str, tuple[float, dict[str, Any]]] = {}
        self._lock = asyncio.Lock()

    async def set_json(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        async with self._lock:
            self._data[key] = (time.time() + ttl_seconds, dict(value))

    async def get_json(self, key: str) -> dict[str, Any] | None:
        async with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            expires_at, value = item
            if expires_at < time.time():
                self._data.pop(key, None)
                return None
            return dict(value)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._data.pop(key, None)


class RedisJsonSessionStore(JsonSessionStore):
    def __init__(self, redis_url: str) -> None:
        import redis.asyncio as redis

        self._client = redis.from_url(redis_url, decode_responses=True)

    async def set_json(self, key: str, value: dict[str, Any], ttl_seconds: int) -> None:
        await self._client.set(key, json.dumps(value, separators=(",", ":")), ex=ttl_seconds)

    async def get_json(self, key: str) -> dict[str, Any] | None:
        raw = await self._client.get(key)
        if raw is None:
            return None
        data = json.loads(raw)
        return data if isinstance(data, dict) else None

    async def delete(self, key: str) -> None:
        await self._client.delete(key)


@dataclass(slots=True)
class AuthSessionManager:
    store: JsonSessionStore
    session_ttl_seconds: int
    auth_flow_ttl_seconds: int

    def _flow_key(self, state: str) -> str:
        return f"auth_flow:{state}"

    def _session_key(self, session_id: str) -> str:
        return f"auth_session:{session_id}"

    async def create_login_flow(self, payload: dict[str, Any]) -> str:
        state = new_id("state")
        await self.store.set_json(
            self._flow_key(state),
            {**payload, "state": state, "created_at": int(time.time())},
            self.auth_flow_ttl_seconds,
        )
        return state

    async def pop_login_flow(self, state: str) -> dict[str, Any] | None:
        key = self._flow_key(state)
        payload = await self.store.get_json(key)
        await self.store.delete(key)
        return payload

    async def create_session(self, payload: dict[str, Any]) -> str:
        session_id = new_id("sess")
        now = int(time.time())
        await self.store.set_json(
            self._session_key(session_id),
            {**payload, "session_id": session_id, "created_at": now, "last_seen_at": now},
            self.session_ttl_seconds,
        )
        return session_id

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        payload = await self.store.get_json(self._session_key(session_id))
        if payload is None:
            return None
        payload["last_seen_at"] = int(time.time())
        await self.store.set_json(self._session_key(session_id), payload, self.session_ttl_seconds)
        return payload

    async def delete_session(self, session_id: str) -> None:
        await self.store.delete(self._session_key(session_id))
