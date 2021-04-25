"""Camunda Nomad Client."""
from fastapi.applications import FastAPI
from process_api.health.routes import router as health_router
from process_api.health.tasks import TASKS as health_tasks
from process_api.portal.tasks import TASKS as portal_tasks
from process_api.process.routes import router as process_router
from process_api.types import ExternalTaskHandler
from process_api.types import TOPIC
from process_api.worker import external_task_worker
from starlette.requests import Request
from starlette.responses import Response
from typing import Awaitable
from typing import Callable
from typing import Dict
import asyncio
import logging


logger = logging.getLogger(__name__)

app = FastAPI(
    title="Camunda Process API",
    description="Application specific process tracking and automation middleware API, which enables easy interaction with application specific business processes and orchestrate application specific integrations and automations with Camunda BPM.",
    version="1.0.0",
)


@app.on_event("startup")
async def startup_event() -> None:
    """Start external task worker on FastAPI startup."""
    tasks: Dict[TOPIC, ExternalTaskHandler] = {}
    tasks.update(health_tasks)  # type: ignore
    tasks.update(portal_tasks)  # type: ignore
    asyncio.ensure_future(external_task_worker(tasks))
    logger.info("Event loop: %s", asyncio.get_event_loop())


app.include_router(health_router)
app.include_router(process_router)


@app.middleware("http")
async def cache_headers(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Set cache headers."""
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, max-age=0"
    return response
