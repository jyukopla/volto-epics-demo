"""Health configuration."""
from enum import Enum
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Settings."""

    HEALTH_HEARTBEAT_THRESHOLD: int = 60


class Topic(str, Enum):
    """External task topics."""

    HEALTH_HEARTBEAT = "process-api.heartbeat"
