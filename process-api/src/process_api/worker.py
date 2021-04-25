"""Camunda external task worker."""
from aiohttp import ClientResponse
from aiohttp import ClientSession
from asyncio import FIRST_COMPLETED
from asyncio import Future
from asyncio import Lock
from datetime import datetime
from process_api.camunda.types import ExtendLockOnExternalTaskDto
from process_api.camunda.types import ExternalTaskBpmnError
from process_api.camunda.types import ExternalTaskFailureDto
from process_api.camunda.types import FetchExternalTasksDto
from process_api.camunda.types import FetchExternalTaskTopicDto
from process_api.camunda.types import LockedExternalTaskDto
from process_api.camunda.types import ValueType
from process_api.camunda.types import VariableValueDto
from process_api.config import settings
from process_api.events import emcee
from process_api.types import ExternalTaskComplete
from process_api.types import ExternalTaskFailure
from process_api.types import ExternalTaskHandler
from process_api.types import NoOp
from process_api.types import TOPIC
from process_api.utils import as_json
from process_api.utils import assert_status_code
from process_api.utils import camunda_session
from typing import Dict
from typing import Set
from typing import Union
import asyncio
import logging
import random
import traceback


logger = logging.getLogger(__name__)


async def executor(
    handler: ExternalTaskHandler, task: LockedExternalTaskDto
) -> Union[ExternalTaskComplete, ExternalTaskFailure]:
    """Execute task handler and convert exception into external task failure."""
    # noinspection PyBroadException
    try:
        result = await handler(task)

        # Return explicit failure from worker
        if isinstance(result, ExternalTaskFailure):
            return result

        # Return explicit lock extension from worker
        if isinstance(result.response, NoOp):
            return result

        # Clear status messages on successful completion
        variables = task.variables or {}
        for name in [
            key
            for key in ["errorCode", "errorMessage", "statusCode", "statusMessage"]
            if key in variables
        ]:
            if result.response.variables is None:
                result.response.variables = {}
            result.response.variables[name] = VariableValueDto(
                value="", type=ValueType.String
            )

        return result
    except Exception as e:  # pylint: disable=W0703
        logger.exception("Unexpected error: %s.", getattr(e, "detail", str(e)))
        response = ExternalTaskFailureDto(
            workerId=task.workerId,
            errorMessage=f'{getattr(e, "detail", str(e))}',
            errorDetails=traceback.format_exc(),
            retries=0,
            retryTimeout=0,
        )
        return ExternalTaskFailure(task=task, response=response)


MUTEX = Lock()


async def complete_task(
    http: ClientSession, result: ExternalTaskComplete,
) -> Union[ExternalTaskComplete, ExternalTaskFailure]:
    """Report external task as complete or as BPMN error."""
    assert result.task.topicName, "External task is missing 'topicName'."

    if not result.task.topicName.endswith(".heartbeat"):
        logger.info("Completing %s:%s.", result.task.topicName, result.task.id)

    if isinstance(result.response, ExternalTaskBpmnError):
        url = f"{settings.CAMUNDA_API_PATH}/external-task/{result.task.id}/bpmnError"
    else:
        url = f"{settings.CAMUNDA_API_PATH}/external-task/{result.task.id}/complete"

    async with MUTEX:
        response = await http.post(url, data=as_json(result.response))
    for retry in range(3):  # noqa: W016 Unused variable 'retry'
        if response.status not in [204, 404]:
            msg = await response.text()
            logger.error("Task completion failed: %s.", msg)
            return ExternalTaskFailure(
                task=result.task,
                response=ExternalTaskFailureDto(
                    workerId=result.task.workerId,
                    errorMessage="Task completion failed",
                    errorDetails=msg,
                    retries=0,
                    retryTimeout=0,
                ),
            )
        else:
            break

    if not result.task.topicName.endswith("heartbeat"):
        logger.debug("Completed %s.", response)

    return result


async def fail_task(
    http: ClientSession, result: ExternalTaskFailure,
) -> ExternalTaskFailure:
    """Report external task as failure."""
    logger.warning("Failing %s:%s.", result.task.topicName, result.task.id)

    url = f"{settings.CAMUNDA_API_PATH}/external-task/{result.task.id}/failure"

    async with MUTEX:
        response = await http.post(url, data=as_json(result.response))
    if response.status not in [204, 404]:
        logger.error("Unexpected error: %s", await response.text())

    if response.status not in [404] and not result.response.retryTimeout:
        url = f"{settings.CAMUNDA_API_PATH}/external-task/{result.task.id}/unlock"
        await http.post(url)

    logger.debug("Failed %s.", result.response)

    return result


def as_topic(topic: str) -> TOPIC:
    """Convert string to topic."""
    # Magic to allow extensible topics.
    for enum in TOPIC.__args__:  # type: ignore
        try:
            return enum(topic)  # type: ignore
        except ValueError:
            pass
    raise ValueError(f"'{topic}' is not a valid TOPIC")


async def extend_lock(
    http: ClientSession,
    pending: Set[
        Future[Union[ClientResponse, ExternalTaskComplete, ExternalTaskFailure]],
    ],
) -> None:
    """Extend external task worker lock."""
    for task in [t for t in pending if isinstance(t, asyncio.Task)]:
        task_id = task.get_name().rsplit(":", 1)[-1]
        url = f"{settings.CAMUNDA_API_PATH}/external-task/{task_id}/extendLock"
        await http.post(
            url,
            data=as_json(
                ExtendLockOnExternalTaskDto(
                    workerId=settings.APP_NAME,
                    newDuration=settings.CAMUNDA_LOCK_TTL * 1000,
                )
            ),
        )


async def fetch_and_lock_and_complete(
    http: ClientSession, handlers: Dict[TOPIC, ExternalTaskHandler],
) -> None:
    """Poll and process external task until connection fails."""

    poll_url = f"{settings.CAMUNDA_API_PATH}/external-task/fetchAndLock"
    poll_topics = as_json(
        FetchExternalTasksDto(
            workerId=settings.APP_NAME,
            maxTasks=10,
            asyncResponseTimeout=settings.CAMUNDA_POLL_TTL * 1000,
            topics=[
                FetchExternalTaskTopicDto(
                    topicName=topic,
                    lockDuration=settings.CAMUNDA_LOCK_TTL * 1000,
                    deserializeValues=False,
                )
                for topic in handlers
            ],
        )
    )

    pending: Set[
        Future[Union[ClientResponse, ExternalTaskComplete, ExternalTaskFailure]],
    ] = set()

    poll_task = asyncio.create_task(
        http.post(poll_url, data=poll_topics), name="fetchAndLock"
    )

    while True:
        poll_task = (
            asyncio.create_task(
                http.post(poll_url, data=poll_topics), name="fetchAndLock"
            )
            if poll_task.done()
            else poll_task
        )

        logger.debug(
            "Waiting for %s pending asyncio task%s: %s.",
            len(pending),
            "s" if len(pending) > 1 else "",
            [getattr(t, "get_name", lambda: "n/a")() for t in pending],
        )

        done, pending = await asyncio.wait(
            pending | {poll_task}, return_when=FIRST_COMPLETED
        )
        if pending and len(done) == 1 and poll_task.done():
            await extend_lock(http, pending)
        for future in done:
            result: Union[
                ClientResponse, ExternalTaskComplete, ExternalTaskFailure
            ] = future.result()

            if isinstance(result, ClientResponse):
                await assert_status_code(result, code=(200,))
                tasks = [
                    LockedExternalTaskDto(**x)
                    for x in await result.json()
                    if x.get("topicName") in handlers
                ]
                for task in tasks:
                    assert task.topicName, "External task is missing 'topicName'."
                    if not task.topicName.endswith(".heartbeat"):
                        logger.info("Scheduling %s:%s.", task.topicName, task.id)
                    topic_name = as_topic(task.topicName)
                    pending = pending | {
                        asyncio.create_task(
                            executor(handlers[topic_name], task),
                            name=f"{task.topicName}:{task.id}",
                        )
                    }

            if isinstance(result, ExternalTaskComplete):
                if not isinstance(result.response, NoOp):
                    await complete_task(http, result)
                    emcee.set(
                        f"{result.task.processInstanceId}:{result.task.topicName}"
                    )

            if isinstance(result, ExternalTaskFailure):
                await fail_task(http, result)
                emcee.set(f"{result.task.processInstanceId}:{result.task.topicName}")


async def external_task_worker(handlers: Dict[TOPIC, ExternalTaskHandler],) -> None:
    """Reconnecting external task worker."""
    retry_in_seconds = 0.0
    logger.info("External task worker started.")
    while True:
        restart_dt = datetime.utcnow()
        # noinspection PyBroadException
        try:
            async with camunda_session() as session:
                await fetch_and_lock_and_complete(session, handlers)
        except Exception as e:  # pylint: disable=W0703
            logger.exception(
                "External task worker disconnected: %s", getattr(e, "detail", str(e))
            )

        finally:
            exception_dt = datetime.utcnow()
            if (exception_dt - restart_dt).total_seconds() > 60:
                retry_in_seconds = 0
            logger.warning(
                "External task worker reconnecting in %s seconds.", retry_in_seconds
            )
            await asyncio.sleep(retry_in_seconds)
            if (exception_dt - restart_dt).total_seconds() < 10:
                retry_in_seconds = min(
                    (max(retry_in_seconds, 1)) * (1.0 + random.random()), 60
                )
