"""Settings and logging configuration."""
# https://pydantic-docs.helpmanual.io/usage/settings/

from process_api.health.config import Settings as health_settings
from process_api.portal.config import Settings as nomad_settings
import logging


class Settings(health_settings, nomad_settings):
    """Settings."""

    APP_NAME: str = __name__.split(".", 1)[0]

    CAMUNDA_API_PATH: str = "http://localhost:8081/engine-rest"
    CAMUNDA_API_AUTHORIZATION: str = ""
    CAMUNDA_TIMEOUT: int = 20
    CAMUNDA_POLL_TTL: int = 10
    CAMUNDA_LOCK_TTL: int = 60

    AIOHTTP_TIMEOUT: int = 10

    LOG_LEVEL: str = "DEBUG"

    EMCEE_TIMEOUT: int = 10


settings = Settings()

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s:%(lineno)d | %(message)s",
    "%d-%m-%Y %H:%M:%S",
)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(settings.LOG_LEVEL)

logger = logging.getLogger(__name__.split(".", 1)[0])
logger.addHandler(stream_handler)
logger.setLevel(settings.LOG_LEVEL)
logger.propagate = False

__all__ = ["settings"]
