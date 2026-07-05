from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field
from backend.core.ids import new_id

class EventEnvelope(BaseModel):
    event_id: str = Field(default_factory=lambda: new_id("evt"))
    event_name: str
    event_version: str = "1.0"
    actor_user_id: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    trace_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)
