"""Type definitions."""
from process_api.camunda.types import CompleteExternalTaskDto
from process_api.camunda.types import ExternalTaskBpmnError
from process_api.camunda.types import ExternalTaskFailureDto
from process_api.camunda.types import LockedExternalTaskDto
from process_api.health.config import Topic as health_topic
from process_api.portal.config import Topic as portal_topic
from pydantic import BaseModel
from typing import Any
from typing import Awaitable
from typing import Callable
from typing import Union


class NoOp(BaseModel):
    """Do nothing."""


class ExternalTaskComplete(BaseModel):
    """Completed external task and its response."""

    def __init__(self, **data: Any) -> None:
        """Init."""
        super().__init__(**data)
        if any(
            [
                isinstance(data.get("response"), NoOp),
                isinstance(data.get("response"), CompleteExternalTaskDto),
                isinstance(data.get("response"), ExternalTaskBpmnError),
            ]
        ):
            # https://github.com/samuelcolvin/pydantic/issues/1423
            self.response = data["response"]

    task: LockedExternalTaskDto
    response: Union[CompleteExternalTaskDto, ExternalTaskBpmnError]


class ExternalTaskFailure(BaseModel):
    """Failed external task and its response."""

    task: LockedExternalTaskDto
    response: ExternalTaskFailureDto


ExternalTaskHandler = Callable[
    [LockedExternalTaskDto], Awaitable[Union[ExternalTaskComplete, ExternalTaskFailure]]
]

# Union of all supported topics (enum)
TOPIC = Union[health_topic, portal_topic]
