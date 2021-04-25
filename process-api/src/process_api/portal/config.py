"""Service configuration."""
from enum import Enum
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Settings."""

    PLONE_API_PATH: str = "http://localhost:8080/Plone"
    PLONE_USERNAME: str = "admin"
    PLONE_PASSWORD: str = "admin"


class Topic(str, Enum):
    """External task topics."""

    WPD_EVENT_CREATE = "wpd.event.create"
