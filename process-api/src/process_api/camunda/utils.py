"""Camunda REST API helpers."""
from aiohttp import ClientResponse
from aiohttp import ClientTimeout
from asyncio import Future
from contextlib import asynccontextmanager
from dataclasses import fields
from enum import Enum
from fastapi.exceptions import HTTPException
from mimetypes import guess_type
from operator import itemgetter
from process_api.camunda.types import ActivityInstanceDto
from process_api.camunda.types import CorrelationMessageDto
from process_api.camunda.types import ExternalTaskDto
from process_api.camunda.types import HistoricProcessInstanceDto
from process_api.camunda.types import HistoricTaskDto
from process_api.camunda.types import LockedExternalTaskDto
from process_api.camunda.types import PatchVariablesDto
from process_api.camunda.types import ProcessInstanceWithVariablesDto
from process_api.camunda.types import State
from process_api.camunda.types import TaskDto
from process_api.camunda.types import ValueType
from process_api.camunda.types import VariableValueDto
from process_api.config import settings
from process_api.events import emcee
from process_api.utils import as_json
from process_api.utils import assert_status_code
from pydantic import BaseModel
from typing import Any
from typing import AsyncGenerator
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type
from typing import TypeVar
from typing import Union
import aiohttp
import asyncio
import base64
import datetime
import json
import re


T = TypeVar("T")

RE_RENDERED_FORM_VARIABLES = re.compile(r' name="([^"]+)"')


@asynccontextmanager
async def camunda_session(
    authorization: str = settings.CAMUNDA_API_AUTHORIZATION,
    content_type: Optional[str] = "application/json",
    accept: Optional[str] = "application/json",
) -> AsyncGenerator[aiohttp.ClientSession, None]:
    """Get aiohttp session with Camunda headers."""
    headers = {
        name: value
        for name, value in (
            {
                "Content-Type": content_type,
                "Accept": accept,
                "Authorization": authorization,
            }
            if authorization
            else {"Content-Type": content_type, "Accept": accept}
        ).items()
        if value
    }
    async with aiohttp.ClientSession(
        headers=headers,
        #       trust_env=True,
        timeout=ClientTimeout(total=settings.CAMUNDA_TIMEOUT),
    ) as session:
        yield session


async def set_variable_value(
    variable: VariableValueDto, fetch: Future[ClientResponse]
) -> VariableValueDto:
    """Set process instance variable."""
    response: ClientResponse = fetch.result()

    if response.status in (200,) and variable.type == ValueType.File:
        filename = (
            response.content_disposition.filename
            if response.content_disposition
            else None
        ) or "download"
        mime_type = guess_type(filename)[0] or "plain/text"
        if variable.valueInfo is not None:
            variable.valueInfo["filename"] = filename
            variable.valueInfo["mimetype"] = mime_type
        if filename.endswith("json.txt") and mime_type == "text/plain":
            variable.value = (await response.read()).decode("utf-8")
        elif filename.endswith(".txt") and mime_type == "text/plain":
            variable.value = await response.read()
        else:
            variable.value = f"data:{mime_type};base64,".encode("utf-8")
            variable.value += base64.b64encode(await response.read())

    elif response.status in (200,) and variable.type == ValueType.Json:
        variable.value = json.loads(
            VariableValueDto(**await response.json()).value or "null"
        )

    return variable


async def get_process_instance(instance_id: str) -> HistoricProcessInstanceDto:
    """Get process instance."""
    instance_url = f"{settings.CAMUNDA_API_PATH}/history/process-instance/{instance_id}"
    async with camunda_session() as http:
        get = await http.get(instance_url)
        await assert_status_code(get, code=(200,), error_code=404)
        instance = HistoricProcessInstanceDto(**await get.json())
        return instance


async def get_process_instance_and_variables(
    instance_id: str,
) -> Tuple[HistoricProcessInstanceDto, Dict[str, VariableValueDto]]:
    """Get process instance and variables."""
    get_instance_task, get_variables_task = (
        asyncio.create_task(get_process_instance(instance_id)),
        asyncio.create_task(get_process_instance_variables(instance_id)),
    )
    await asyncio.wait((get_instance_task, get_variables_task))
    get_instance, get_variables = (
        get_instance_task.result(),
        get_variables_task.result(),
    )
    return get_instance, get_variables


async def get_process_instances_by_key(
    business_key: str,
) -> List[HistoricProcessInstanceDto]:
    """Get process instances by business key."""
    url = f"{settings.CAMUNDA_API_PATH}/history/process-instance"
    async with camunda_session() as http:
        get = await http.get(url, params={"processInstanceBusinessKey": business_key})
        await assert_status_code(get, code=(200,), error_code=404)
        instances = [
            HistoricProcessInstanceDto(**instance) for instance in await get.json()
        ]
        return instances


class VariableFilteringExpressionOperator(str, Enum):
    """Historic process instance variable filtering expression operator."""

    eq = "eq"


class VariableFilteringExpression(BaseModel):
    """Historic process instance variable filtering expression."""

    key: str
    operator: VariableFilteringExpressionOperator
    value: str


async def get_process_instances_by_variables(
    process_definition_key: str,
    variables: List[VariableFilteringExpression],
    executed_activity_ids: Optional[List[str]] = None,
    finished_after: Optional[datetime.datetime] = None,
) -> List[HistoricProcessInstanceDto]:
    """Get process instances by business key."""
    # Restrict to instances that were finished after the given date.
    # Date format: yyyy-MM-dd'T'HH:mm:ss.SSSZ, e.g.,
    # 2013-01-23T14:42:45.000+0200.
    url = f"{settings.CAMUNDA_API_PATH}/history/process-instance"
    timespec = "milliseconds"
    params = (
        {
            "processDefinitionKey": process_definition_key,
            "executedActivityIdIn": ",".join(executed_activity_ids or []),
            "variables": ",".join(
                [
                    "_".join([variable.key, variable.operator, variable.value])
                    for variable in variables
                ]
            ),
            "finishedAfter": f"{finished_after.isoformat(timespec=timespec)}+0000",
        }
        if finished_after
        else {
            "processDefinitionKey": process_definition_key,
            "executedActivityIdIn": ",".join(executed_activity_ids or []),
            "variables": ",".join(
                [
                    "_".join([variable.key, variable.operator, variable.value])
                    for variable in variables
                ]
            ),
        }
    )
    async with camunda_session() as http:
        get = await http.get(url, params=params)
        await assert_status_code(get, code=(200,), error_code=404)
        instances = [
            HistoricProcessInstanceDto(**instance) for instance in await get.json()
        ]
        return instances


async def get_process_instance_variables(
    instance_id: str,
) -> Dict[str, VariableValueDto]:
    """Get process instance variables."""
    url = f"{settings.CAMUNDA_API_PATH}/process-instance/{instance_id}/variables"
    async with camunda_session() as http:
        get = await http.get(url, params={"deserializeValues": "false"})
        if get.status in (404, 500):
            return await get_historic_process_instance_variables(instance_id)
        await assert_status_code(get, code=(200,), error_code=404)
        variables = await update_file_variables(
            url,
            {
                key: VariableValueDto(**value)
                for key, value in (await get.json()).items()
            },
        )
        return variables


async def get_historic_process_instance_variables(
    instance_id: str,
) -> Dict[str, VariableValueDto]:
    """Get process instance variables."""
    url = f"{settings.CAMUNDA_API_PATH}/history/variable-instance"
    async with camunda_session() as http:
        get = await http.get(
            url, params={"processInstanceId": instance_id, "deserializeValues": "false"}
        )
        await assert_status_code(get, code=(200,), error_code=404)

        def json_expand(variable: VariableValueDto) -> VariableValueDto:
            """Parse JSON values."""
            if variable.type == ValueType.Json and variable.value:
                variable.value = json.loads(variable.value)
            return variable

        return {
            item["name"]: json_expand(VariableValueDto(**item))
            for item in sorted(await get.json(), key=itemgetter("createTime"))
        }


async def update_file_variables(
    variables_url: str, variables: Dict[str, VariableValueDto]
) -> Dict[str, VariableValueDto]:
    """Update variables with file variable values."""
    files = {}
    async with camunda_session() as http:
        for name in variables:
            if variables[name].type == ValueType.File:
                files[name] = asyncio.create_task(
                    http.get(
                        f"{variables_url}/{name}/data",
                        headers={"Accept": "application/octet-stream"},
                    )
                )
            elif variables[name].type == ValueType.Json:
                files[name] = asyncio.create_task(
                    http.get(
                        f"{variables_url}/{name}", params={"deserializeValue": "false"},
                    )
                )
        if files:
            await asyncio.wait(files.values())

        # Updated file variable
        for name, get_variable in files.items():
            variables[name] = await set_variable_value(variables[name], get_variable)

    return variables


async def get_instance_variables(
    instance_id: str, fetch_files: Optional[bool] = True,
) -> Dict[str, VariableValueDto]:
    """Get process instance variables."""
    instance_url = f"{settings.CAMUNDA_API_PATH}/process-instance/{instance_id}"

    async with camunda_session() as http:
        get_variables = await http.get(f"{instance_url}/variables")
        await assert_status_code(get_variables, code=(200,))
        variables = {
            key: VariableValueDto(**value)
            for key, value in (await get_variables.json()).items()
        }

        if not fetch_files:
            return variables

        files = {}

        for name in variables:
            if variables[name].type == ValueType.File:
                files[name] = asyncio.create_task(
                    http.get(
                        f"{instance_url}/variables/{name}/data",
                        headers={"Accept": "application/octet-stream"},
                    )
                )
            elif variables[name].type == ValueType.Json:
                files[name] = asyncio.create_task(
                    http.get(
                        f"{instance_url}/variables/{name}",
                        params={"deserializeValue": "false"},
                    )
                )
        if files:
            await asyncio.wait(files.values())

        for name, get_variable in files.items():
            variables[name] = await set_variable_value(variables[name], get_variable)

        return variables


async def get_instance_with_variables(
    instance_id: str,
) -> ProcessInstanceWithVariablesDto:
    """Get process instance with variables."""
    instance_url = f"{settings.CAMUNDA_API_PATH}/process-instance/{instance_id}"

    async with camunda_session() as http:
        # 2) Fetch instance and inline variables
        get_instance_task, get_variables_task = (
            asyncio.create_task(http.get(instance_url)),
            asyncio.create_task(http.get(f"{instance_url}/variables")),
        )
        await asyncio.wait([get_instance_task, get_variables_task])
        get_instance, get_variables = (
            get_instance_task.result(),
            get_variables_task.result(),
        )
        await assert_status_code(get_instance, code=(200,), error_code=404)
        instance = ProcessInstanceWithVariablesDto(**await get_instance.json())
        instance.variables = {
            key: VariableValueDto(**value)
            for key, value in (await get_variables.json()).items()
        }

        # 3) Fetch file variables
        files = {}
        for name in instance.variables:
            if instance.variables[name].type == ValueType.File:
                files[name] = asyncio.create_task(
                    http.get(
                        f"{instance_url}/variables/{name}/data",
                        headers={"Accept": "application/octet-stream"},
                    )
                )
            elif instance.variables[name].type == ValueType.Json:
                files[name] = asyncio.create_task(
                    http.get(
                        f"{instance_url}/variables/{name}",
                        params={"deserializeValue": "false"},
                    )
                )
        if files:
            await asyncio.wait(files.values())

        # 4) Updated file variable
        for name, get_variable in files.items():
            instance.variables[name] = await set_variable_value(
                instance.variables[name], get_variable
            )

        return instance


async def update_variables(
    instance_id: str, variables: Dict[str, VariableValueDto],
) -> None:
    """Update process instance variables."""
    async with camunda_session() as http:
        url = f"{settings.CAMUNDA_API_PATH}/process-instance/{instance_id}/variables"
        data = PatchVariablesDto(modifications=variables)
        post = await http.post(url, data=as_json(data))
        await assert_status_code(post, code=(204,), error_code=400)


async def post_message(
    instance_id: str,
    message_id: str,
    variables: Optional[Dict[str, VariableValueDto]] = None,
    wait_for: Optional[str] = None,
) -> None:
    """Post correlated message and optionally wait for a task to be processed."""
    async with camunda_session() as http:
        url = f"{settings.CAMUNDA_API_PATH}/message"
        data = CorrelationMessageDto(
            messageName=message_id,
            processInstanceId=instance_id,
            resultEnabled=False,
            processVariables=variables,
        )
        post = await http.post(url, data=as_json(data))
        if post.status in [204] and wait_for:
            await emcee.wait(wait_for)


def task_variables(task: LockedExternalTaskDto, klass: Type[T]) -> T:
    """Parse task variables into data class instance."""
    data = {}
    if task.variables:
        for field in fields(klass):
            if field.name in task.variables:
                data[field.name] = task.variables[field.name].value
    return klass(**data)  # type: ignore


async def get_external_tasks(instance_id: str,) -> List[ExternalTaskDto]:
    """Get open process instance external tasks."""
    url = f"{settings.CAMUNDA_API_PATH}/external-task"
    async with camunda_session() as http:
        get = await http.get(url, params={"processInstanceId": instance_id})
        if get.status in [200]:
            return list([ExternalTaskDto(**task) for task in await get.json()])
    return []


async def get_process_activity_instances(
    instance_id: str, state: Optional[State] = State.ACTIVE,
) -> List[ActivityInstanceDto]:
    """Get active process instance jobs."""
    if state == State.ACTIVE:
        url = f"{settings.CAMUNDA_API_PATH}/process-instance/{instance_id}/activity-instances"
        async with camunda_session() as http:
            get = await http.get(url)
            await assert_status_code(get, code=(200,), error_code=404)
            root = ActivityInstanceDto(**await get.json())
            return root.childActivityInstances or []
    return []


async def get_user_tasks_by_key(business_key: str) -> List[TaskDto]:
    """Get open user tasks by business key."""
    url = f"{settings.CAMUNDA_API_PATH}/task"
    async with camunda_session() as http:
        get = await http.get(url, params={"processInstanceBusinessKey": business_key})
        if get.status in [200]:
            return list([TaskDto(**task) for task in await get.json()])
    return []


async def get_user_task_form_variable_values(task_id: str) -> Dict[str, Any]:
    """Get all user task form variable."""
    variable_values: Dict[str, VariableValueDto] = {}
    async with camunda_session(content_type=None, accept=None) as http:
        url = f"{settings.CAMUNDA_API_PATH}/task/{task_id}/rendered-form"
        get = await http.get(url)
        await assert_status_code(get, code=(200, 404), error_code=404)
        if get.status == 200:
            html = await get.text()
            variable_names = set(
                RE_RENDERED_FORM_VARIABLES.findall(html) or []
            ).difference({"generatedForm"})
        else:
            variable_names = set()

    if variable_names:
        async with camunda_session() as http:
            url = f"{settings.CAMUNDA_API_PATH}/task/{task_id}/form-variables"
            get = await http.get(
                url, params={"variableNames": ",".join(variable_names)}
            )
            await assert_status_code(get, code=(200,), error_code=404)
            variable_values = {
                name: VariableValueDto(**value)
                for name, value in (await get.json()).items()
            }

    return {
        name: variable_values[name].value if name in variable_values else None
        for name in variable_names
        if name in variable_values
    }


async def get_user_task_variables(task_id: str) -> Dict[str, VariableValueDto]:
    """Get user task variables."""
    url = f"{settings.CAMUNDA_API_PATH}/task/{task_id}/variables"
    async with camunda_session() as http:
        get = await http.get(url, params={"deserializeValues": "false"})
        await assert_status_code(get, code=(200,), error_code=404)
        data = await get.json()
        variables = await update_file_variables(
            url, {key: VariableValueDto(**value) for key, value in data.items()},
        )
        return variables


async def get_historic_user_task_variables(
    instance_id: str,
) -> Dict[str, VariableValueDto]:
    """Get historic user task variables."""
    url = f"{settings.CAMUNDA_API_PATH}/history/variable-instance"
    async with camunda_session() as http:
        get = await http.get(
            url,
            params={
                "activityInstanceIdIn": instance_id,
                "deserializeValues": "false",
                "includeDeleted": "true",
            },
        )
        await assert_status_code(get, code=(200,), error_code=404)
        data = await get.json()

        def json_expand(variable: VariableValueDto) -> VariableValueDto:
            """Parse JSON values."""
            if variable.type == ValueType.Json and variable.value:
                variable.value = json.loads(variable.value)
            return variable

        return {
            item["name"]: json_expand(VariableValueDto(**item))
            for item in sorted(data, key=itemgetter("createTime"))
        }


async def get_user_task_by_key(
    task_definition_key: str, business_key: str
) -> Union[TaskDto, HistoricTaskDto]:
    """Get open task by business key."""
    url = f"{settings.CAMUNDA_API_PATH}/task"
    async with camunda_session() as http:
        get = await http.get(
            url,
            params={
                "processInstanceBusinessKey": business_key,
                "taskDefinitionKey": task_definition_key,
            },
        )
        await assert_status_code(get, code=(200,), error_code=404)
        for task in await get.json():
            return TaskDto(**task)
        return await get_historic_user_task_by_key(task_definition_key, business_key)


async def get_historic_user_task(
    task_definition_key: str, instance_id: Optional[str] = None
) -> HistoricTaskDto:
    """Get historic task."""
    url = f"{settings.CAMUNDA_API_PATH}/history/task"
    async with camunda_session() as http:
        get = await http.get(
            url,
            params={
                "processInstanceId": instance_id,
                "taskDefinitionKey": task_definition_key,
            },
        )
        await assert_status_code(get, code=(200,), error_code=404)
        for task in await get.json():
            return HistoricTaskDto(**task)
        raise HTTPException(
            status_code=404,
            detail=f'Task "{task_definition_key}" for "{instance_id}" not found.',
        )


async def get_historic_user_task_by_key(
    task_definition_key: str, business_key: str
) -> HistoricTaskDto:
    """Get historic task by business key."""
    url = f"{settings.CAMUNDA_API_PATH}/history/task"
    async with camunda_session() as http:
        get = await http.get(
            url,
            params={
                "processInstanceBusinessKey": business_key,
                "taskDefinitionKey": task_definition_key,
            },
        )
        await assert_status_code(get, code=(200,), error_code=404)
        for task in await get.json():
            return HistoricTaskDto(**task)
        raise HTTPException(
            status_code=404,
            detail=f'Task "{task_definition_key}" for "{business_key}" not found.',
        )


async def get_historic_user_tasks_by_keys(
    task_definition_keys: List[str], business_key: str
) -> List[HistoricTaskDto]:
    """Get historic tasks by task definition keys and business key."""
    url = f"{settings.CAMUNDA_API_PATH}/history/task"
    async with camunda_session() as http:
        get = await http.get(
            url,
            params={
                "processInstanceBusinessKey": business_key,
                "taskDefinitionKeyIn": ",".join(task_definition_keys),
            },
        )
        await assert_status_code(get, code=(200,), error_code=404)
        return [HistoricTaskDto(**task) for task in await get.json()]
