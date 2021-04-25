"""Heartbeat types."""
from datetime import datetime
from pydantic import BaseModel
from pydantic import Field
from typing import Optional


class State(BaseModel):
    """Service health check state."""

    heartbeat: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class Heartbeat(BaseModel):
    """Health check response."""

    heartbeat: str = Field(
        None, description="UTC timestamp of the last recorded heartbeat.",
    )
