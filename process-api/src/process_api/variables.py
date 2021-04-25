"""Camunda task variable helper functions."""
from fastapi.exceptions import HTTPException
from process_api.camunda.types import LockedExternalTaskDto
from process_api.camunda.types import ValueType
from process_api.camunda.types import VariableValueDto
from process_api.config import settings
from process_api.utils import assert_status_code
from process_api.utils import camunda_session
from typing import Any
from typing import List
import datetime
import json


def task_variable_str(task: LockedExternalTaskDto, name: str) -> str:
    """Return named str task variable or raise KeyError."""
    if task.variables is not None:
        value = task.variables[name].value
        if isinstance(value, str):
            return value
    raise KeyError(name)


def task_variable_int(task: LockedExternalTaskDto, name: str) -> int:
    """Return named int task variable or raise KeyError."""
    if task.variables is not None:
        value = task.variables[name].value
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
    raise KeyError(name)


def task_variable_bool(task: LockedExternalTaskDto, name: str) -> bool:
    """Return named bool task variable or raise KeyError."""
    if task.variables is not None:
        value = task.variables[name].value
        if isinstance(value, bool):
            return value
    raise KeyError(name)


def task_variable_date(task: LockedExternalTaskDto, name: str) -> datetime.date:
    """Return named date task variable or raise KeyError."""
    if task.variables is not None:
        value = task.variables[name].value
        if isinstance(value, str):
            return datetime.date(*(map(int, value.split("T")[0].split("-"))))
    raise KeyError(name)


def task_variable_datetime(task: LockedExternalTaskDto, name: str) -> datetime.datetime:
    """Return named date time task variable or raise KeyError."""
    if task.variables is not None:
        value = task.variables[name].value
        if isinstance(value, str):
            return datetime.datetime.fromisoformat(value.replace("Z", ""))
    raise KeyError(name)


async def task_variable_deserialized(
    task: LockedExternalTaskDto, name: str
) -> VariableValueDto:
    """Fetch deserialized task variable from task execution."""
    async with camunda_session() as http:
        url = f"{settings.CAMUNDA_API_PATH}/execution/{task.executionId}/localVariables/{name}"
        get = await http.get(url, params={"deserializeValues": "true"})
        await assert_status_code(get, (200,))
        return VariableValueDto(**await get.json())


async def task_variable_map(task: LockedExternalTaskDto, name: str) -> Any:
    """Return named map task variable parsed or raise KeyError."""
    try:
        if task.variables is not None:
            value = task.variables[name].value
            info = task.variables[name].valueInfo
            assert (
                task.variables[name].type == ValueType.Json
                or info
                and info.get("serializationDataFormat") == "application/json"
            ), f"Invalid map variable: {task.variables[name]}"
            if isinstance(value, str):
                return json.loads(value)
    except AssertionError as e:
        try:
            variable = await task_variable_deserialized(task, name)
        except HTTPException:
            raise KeyError(name) from e
        if isinstance(variable.value, dict):
            return variable.value
    raise KeyError(name)


async def task_variable_list(task: LockedExternalTaskDto, name: str) -> List[str]:
    """Return named string list task variable or raise KeyError."""
    try:
        if task.variables is not None:
            variable = task.variables[name]
            assert (
                variable is not None
                and isinstance(variable.value, str)
                and variable.type == "Object"
                and variable.valueInfo is not None
                and variable.valueInfo["serializationDataFormat"] == "application/json"
            ), f"Invalid list variable: {task.variables[name]}"
            value = task.variables[name].value
            return [str(x) for x in json.loads(value or "[]") or []]
    except AssertionError as e:
        try:
            variable = await task_variable_deserialized(task, name)
        except HTTPException:
            raise KeyError(name) from e
        if isinstance(variable.value, list):
            return variable.value
    raise KeyError(name)
