"""Service external tasks."""
from aiohttp import ClientTimeout
from contextlib import asynccontextmanager
from process_api.camunda.types import CompleteExternalTaskDto
from process_api.camunda.types import ExternalTaskBpmnError
from process_api.camunda.types import LockedExternalTaskDto
from process_api.config import settings
from process_api.portal.config import Topic
from process_api.types import ExternalTaskComplete
from process_api.utils import as_json
from process_api.variables import task_variable_datetime
from process_api.variables import task_variable_str
from typing import AsyncGenerator
import aiohttp
import base64
import json


@asynccontextmanager
async def plone_session() -> AsyncGenerator[aiohttp.ClientSession, None]:
    """Get aiohttp session with Plone headers."""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": "Basic "
        + base64.b64encode(
            f"{settings.PLONE_USERNAME}:{settings.PLONE_PASSWORD}".encode("utf-8")
        ).decode("utf-8"),
    }
    async with aiohttp.ClientSession(
        headers=headers,
        trust_env=False,  # NO_PROXY
        timeout=ClientTimeout(total=settings.AIOHTTP_TIMEOUT),
    ) as session:
        yield session


async def event_create(task: LockedExternalTaskDto,) -> ExternalTaskComplete:
    """Create portal_event."""
    title = task_variable_str(task, "title")
    description = task_variable_str(task, "description")
    start = task_variable_datetime(task, "start")
    end = task_variable_datetime(task, "end")

    payload = {
        "@type": "Event",
        "title": title,
        "description": description,
        "start": start,
        "end": end,
    }

    url = f"{settings.PLONE_API_PATH}/events"
    async with plone_session() as http:
        response = await http.post(url, data=as_json(payload))

        if response.status != 201:
            message = await response.json()
            message = message["message"] if "message" in message else message
            try:
                message = json.loads(message.replace("'", '"'))
            except json.decoder.JSONDecodeError:
                pass
            if isinstance(message, list):
                for error in message:
                    message = error["message"] if "message" in error else f"{error}"
                    break
            return ExternalTaskComplete(
                task=task,
                response=ExternalTaskBpmnError(
                    workerId=task.workerId,
                    errorCode="error",
                    errorMessage=f"{message}",
                ),
            )

        event = response.headers["Location"]
        await http.post(f"f{event}/@workflow/publish")

    return ExternalTaskComplete(
        task=task, response=CompleteExternalTaskDto(workerId=task.workerId),
    )


TASKS = {Topic.WPD_EVENT_CREATE: event_create}
