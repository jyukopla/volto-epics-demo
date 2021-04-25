"""FastAPI router."""
from fastapi.exceptions import HTTPException
from fastapi.routing import APIRouter
from process_api.camunda.types import CompleteTaskDto
from process_api.camunda.types import CorrelationMessageDto
from process_api.camunda.types import HistoricProcessInstanceDto
from process_api.camunda.types import HistoricTaskDto
from process_api.camunda.types import ProcessDefinitionDiagramDto
from process_api.camunda.types import ProcessInstanceWithVariablesDto
from process_api.camunda.types import StartProcessInstanceFormDto
from process_api.camunda.types import State
from process_api.camunda.types import ValueType
from process_api.camunda.types import VariableValueDto
from process_api.camunda.utils import camunda_session
from process_api.camunda.utils import get_external_tasks
from process_api.camunda.utils import get_historic_process_instance_variables
from process_api.camunda.utils import get_historic_user_task_variables
from process_api.camunda.utils import get_process_activity_instances
from process_api.camunda.utils import get_process_instance
from process_api.camunda.utils import get_process_instance_variables
from process_api.camunda.utils import get_process_instances_by_key
from process_api.camunda.utils import get_user_task_by_key
from process_api.camunda.utils import get_user_task_form_variable_values
from process_api.camunda.utils import get_user_task_variables
from process_api.camunda.utils import get_user_tasks_by_key
from process_api.config import settings
from process_api.events import emcee
from process_api.process.types import ActivityInstance
from process_api.process.types import CompleteUserTask
from process_api.process.types import Message
from process_api.process.types import ProcessDefinition
from process_api.process.types import ProcessInstance
from process_api.process.types import StartProcessInstance
from process_api.process.types import UserTask
from process_api.utils import as_dict
from process_api.utils import as_json
from process_api.utils import assert_status_code
from starlette.requests import Request
from starlette.responses import Response
from typing import Any
from typing import List
from typing import Optional
from typing import Union
from uuid import uuid4
import asyncio
import itertools
import pprint
import time


ENCRYPTED_VARIABLE_NAMES = [
    "password",
    "confirmedPassword",
]


router = APIRouter()


def get_type(value: Any) -> ValueType:
    """Infer Camunda variable type from variable."""
    if value is True or value is False:
        return ValueType.Boolean
    if isinstance(value, str):
        return ValueType.String
    if isinstance(value, float):
        return ValueType.Double
    if isinstance(value, int):
        return ValueType.Integer
    return ValueType.String


@router.post(
    "/process",
    status_code=201,
    response_model=ProcessInstance,
    summary="Start new process",
    tags=["Process"],
)
async def post_process(
    data: StartProcessInstance,
    request: Request,
    response: Response,
    wait: Optional[Union[int, float]] = 0,
    wait_for: Optional[str] = None,
) -> ProcessInstance:
    """Start new process."""
    async with camunda_session() as http:
        # Create
        key = data.processDefinitionKey
        url = f"{settings.CAMUNDA_API_PATH}/process-definition/key/{key}/submit-form"
        payload = StartProcessInstanceFormDto(
            businessKey=str(uuid4()),
            variables={
                name: VariableValueDto(value=value, type=get_type(value))
                for name, value in (data.variables or {}).items()
            },
        )
        post = await http.post(url, data=as_json(payload))
        await assert_status_code(post, code=(200,))

        # Get
        initial = ProcessInstanceWithVariablesDto(**await post.json())
        assert initial.id, "Process instance is missing 'id'."
        assert initial.businessKey, "Process instance is missing 'businessKey'."
        result = await get_process(
            instance_id=initial.id,
            business_key=initial.businessKey,
            request=request,
            wait=wait,
            wait_for=wait_for,
        )
        assert isinstance(result, ProcessInstance)

        # Redirect
        response.headers["Location"] = request.url_for(
            name=get_process.__name__,
            instance_id=result.id,
            business_key=result.businessKey,
        )

        # Return
        return result


async def wait_for_external_tasks(
    instances: List[HistoricProcessInstanceDto], wait_for: Union[int, float]
) -> Union[int, float]:
    """Wait for external tasks."""
    # Get external tasks
    get_external_tasks_tasks = [
        asyncio.create_task(get_external_tasks(instance.id))
        for instance in instances
        if instance.id
    ]
    await asyncio.wait(get_external_tasks_tasks)
    external_tasks = list(
        itertools.chain.from_iterable(
            [task.result() for task in get_external_tasks_tasks]
        )
    )
    start = time.time()
    keys = [
        f"{task.processInstanceId}:{task.topicName}"
        for task in external_tasks
        if task.topicName
    ]
    tasks = [asyncio.create_task(emcee.wait(key, timeout=wait_for)) for key in keys]
    if tasks:
        await asyncio.wait(tasks)
        wait_left = wait_for - (time.time() - start)
    else:
        wait_left = 0

    # If an externalTask was completed, retry for additional wait
    if wait_left > 0:
        results = [task.result() for task in tasks if task.done()]
        if True in results:
            return wait_left

    return -1


@router.get(
    "/process/{instance_id}/{business_key}",
    response_model=ProcessInstance,
    summary="Get process status",
    tags=["Process"],
)
async def get_process(
    instance_id: str,
    business_key: str,
    request: Request,
    wait: Optional[Union[int, float]] = 0,
    wait_for: Optional[str] = None,
) -> ProcessInstance:
    """Get process status."""
    # Try twice to get process status, because the process may move from running
    # to historical during while we are calling it...
    try:
        return await get_process_impl(
            instance_id=instance_id,
            business_key=business_key,
            request=request,
            wait=wait,
            wait_for=wait_for,
        )
    except HTTPException:
        return await get_process_impl(
            instance_id=instance_id,
            business_key=business_key,
            request=request,
            wait=wait,
            wait_for=wait_for,
        )


async def get_process_impl(
    instance_id: str,
    business_key: str,
    request: Request,
    wait: Optional[Union[int, float]] = 0,
    wait_for: Optional[str] = None,
) -> ProcessInstance:
    """Get process status."""
    # Get instance
    main_instance = None
    all_instances = await get_process_instances_by_key(business_key)
    for instance in all_instances:
        if instance.id == instance_id:
            main_instance = instance
            break
    if not main_instance:
        raise HTTPException(
            status_code=404,
            detail=f'Process instance with id "{instance_id}" and '
            f'business key "{business_key}" was not found.',
        )

    # Optionally wait for incomplete external tasks
    if wait and wait_for:
        await emcee.wait(f"{instance_id}:{wait_for}", timeout=wait)
    if wait:
        wait = await wait_for_external_tasks(all_instances, wait) - 0.1
        if wait > -1:
            result = await get_process(
                instance_id=instance_id,
                business_key=business_key,
                request=request,
                wait=wait,
            )
            assert isinstance(result, ProcessInstance)
            return result

    # Get user tasks and variables
    get_user_tasks_task, get_variables_task, get_activities_task = (
        asyncio.create_task(get_user_tasks_by_key(business_key)),
        asyncio.create_task(
            get_process_instance_variables(instance_id)
            if main_instance.state == State.ACTIVE
            else get_historic_process_instance_variables(instance_id)
        ),
        asyncio.create_task(
            get_process_activity_instances(instance_id, main_instance.state)
        ),
    )
    await asyncio.wait((get_user_tasks_task, get_variables_task, get_activities_task))
    user_tasks, variables, activities = (
        get_user_tasks_task.result(),
        get_variables_task.result(),
        get_activities_task.result(),
    )

    # Merge tasks with process
    result = as_dict(main_instance)
    result["tasks"] = [
        UserTask(
            **{
                "@id": request.url_for(
                    name=get_process_user_task.__name__,
                    instance_id=instance_id,
                    business_key=business_key,
                    task_definition_key=task.taskDefinitionKey,
                )
            },
            **as_dict(task),
        )
        for task in user_tasks
    ]
    result["activities"] = [
        ActivityInstance(
            id=activity.id,
            name=activity.activityName,
            type=activity.activityType,
            incident=bool(activity.incidents),
        )
        for activity in activities
    ]
    result["variables"] = {
        name: value.value for name, value in (variables or {}).items()
    }
    result = ProcessInstance(
        **{
            "@id": request.url_for(
                name=get_process.__name__,
                instance_id=instance_id,
                business_key=business_key,
            )
        },
        **result,
    )
    assert isinstance(result, ProcessInstance)

    # Return
    return result


@router.post(
    "/process/{instance_id}/{business_key}/message/{message_id}",
    status_code=302,
    response_model=ProcessInstance,
    summary="Post message",
    tags=["Process"],
)
async def post_message(
    data: Message,
    instance_id: str,
    business_key: str,
    message_id: str,
    request: Request,
    response: Response,
) -> None:
    """Get user task details."""
    # Get instance to check businessKey
    instance = await get_process_instance(instance_id)
    if instance.businessKey != business_key:
        raise HTTPException(
            status_code=404,
            detail=f'Process instance with id "{instance_id}" and '
            f'business key "{business_key}" was not found.',
        )

    async with camunda_session() as http:
        url = f"{settings.CAMUNDA_API_PATH}/message"

        # At first, try to correlate with the specific process instance
        message = CorrelationMessageDto(
            messageName=message_id,
            processInstanceId=instance_id,
            resultEnabled=False,
            processVariables={
                key: VariableValueDto(value=value, type=ValueType.String)
                for key, value in data.variables.items()
            },
        )
        post = await http.post(url, data=as_json(message))

        # On error, try to correlate with the rest of the process family by business key
        if post.status not in [204]:
            message = CorrelationMessageDto(
                messageName=message_id,
                businessKey=business_key,
                resultEnabled=False,
                processVariables={
                    key: VariableValueDto(value=value, type=ValueType.String)
                    for key, value in data.variables.items()
                },
            )
            post = await http.post(url, data=as_json(message))
            await assert_status_code(post, code=(204,), error_code=400)

    # Redirect
    response.headers["Location"] = (
        request.url_for(
            name=get_process.__name__,
            instance_id=instance_id,
            business_key=business_key,
        )
        + "?wait=1"
    )


@router.get(
    "/process/{instance_id}/{business_key}/tasks/{task_definition_key}",
    response_model=UserTask,
    summary="Get user task details",
    tags=["Process"],
)
async def get_process_user_task(
    instance_id: str, business_key: str, task_definition_key: str, request: Request
) -> UserTask:
    """Get user task details."""
    # Get instance to check businessKey
    instance = await get_process_instance(instance_id)
    if instance.businessKey != business_key:
        raise HTTPException(
            status_code=404,
            detail=f'Process instance with id "{instance_id}" and '
            f'business key "{business_key}" was not found.',
        )

    # Get
    task = await get_user_task_by_key(task_definition_key, business_key)

    # Simplify
    result = UserTask(
        **{
            "@id": request.url_for(
                name=get_process_user_task.__name__,
                instance_id=instance_id,
                business_key=business_key,
                task_definition_key=task.taskDefinitionKey,
            )
        },
        **as_dict(task),
    )

    assert task.id, "User task is missing 'id'."
    assert task.processInstanceId, "User task is missing 'processInstanceId'."
    if isinstance(task, HistoricTaskDto):
        variables = await get_historic_user_task_variables(task.processInstanceId)
        if result.variables is None:
            result.variables = {}
        result.variables.update(
            {name: value.value for name, value in variables.items()}
        )
        result.completed = True
    else:
        variables = await get_user_task_variables(task.id)
        if result.variables is None:
            result.variables = {}
        result.variables.update(
            {name: value.value for name, value in variables.items()}
        )
        result.form = await get_user_task_form_variable_values(task.id)

    # Return
    return result


@router.post(
    "/process/{instance_id}/{business_key}/tasks/{task_definition_key}",
    status_code=302,
    response_model=ProcessInstance,
    summary="Complete open user task",
    tags=["Process"],
)
async def post_user_task(
    instance_id: str,
    business_key: str,
    task_definition_key: str,
    request: Request,
    response: Response,
    data: Optional[CompleteUserTask] = None,
) -> None:
    """Complete open user task."""
    # Get instance to check businessKey
    instance = await get_process_instance(instance_id)
    if instance.businessKey != business_key:
        raise HTTPException(
            status_code=404,
            detail=f'Process instance with id "{instance_id}" and '
            f'business key "{business_key}" was not found.',
        )

    # Get
    task = await get_user_task_by_key(task_definition_key, instance.businessKey)
    assert task.id
    task_definition_key = task.id
    form = await get_user_task_form_variable_values(task.id)

    # Complete
    payload = CompleteTaskDto(
        variables={
            name: VariableValueDto(value=value, type=get_type(value))
            for name, value in data.variables.items()
            if name in form
        }
        if data
        else {},
    )

    url = f"{settings.CAMUNDA_API_PATH}/task/{task_definition_key}/submit-form"
    async with camunda_session() as http:
        post = await http.post(url, data=as_json(payload))
        if post.status != 204:
            pprint.pprint(await post.json())
        await assert_status_code(post, code=(204,), error_code=400)

    # Redirect
    response.headers["Location"] = (
        request.url_for(
            name=get_process.__name__,
            instance_id=instance_id,
            business_key=business_key,
        )
        + "?wait=1"
    )


@router.get(
    "/process/{instance_id}/{business_key}/definition",
    response_model=ProcessDefinition,
    summary="Get process definition",
    tags=["Process"],
)
async def get_definition(instance_id: str, business_key: str) -> ProcessDefinition:
    """Get process definition."""
    # Get instance to check businessKey
    instance = await get_process_instance(instance_id)
    if instance.businessKey != business_key:
        raise HTTPException(
            status_code=404,
            detail=f'Process instance with id "{instance_id}" and '
            f'business key "{business_key}" was not found.',
        )
    assert instance.processDefinitionId, "Process instance is missing 'definitionId'"

    async with camunda_session() as http:
        url = f"{settings.CAMUNDA_API_PATH}/process-definition/{instance.processDefinitionId}/xml"
        get = await http.get(url)
        await assert_status_code(get, code=(200,), error_code=404)
        result = ProcessDefinitionDiagramDto(**await get.json())
        return ProcessDefinition(**as_dict(result))


@router.delete(
    "/process/{instance_id}/{business_key}",
    response_model=ProcessInstance,
    summary="Terminate process",
    tags=["Process"],
)
async def delete_process(
    instance_id: str, business_key: str, request: Request,
) -> ProcessInstance:
    """Delete process instance."""
    try:
        async with camunda_session() as http:
            url = f"{settings.CAMUNDA_API_PATH}/process-instance/{instance_id}"
            delete = await http.delete(url)
            await assert_status_code(delete, code=(204,), error_code=404)
    except HTTPException:
        pass
    return await get_process_impl(
        instance_id=instance_id, business_key=business_key, request=request,
    )
