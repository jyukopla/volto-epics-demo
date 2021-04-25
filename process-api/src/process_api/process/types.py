"""Process types."""
from __future__ import annotations

from process_api.camunda.types import State
from pydantic import AnyHttpUrl
from pydantic import BaseModel
from pydantic import Field
from typing import Any
from typing import Dict
from typing import List
from typing import Optional


Variables = Dict[str, Any]


class StartProcessInstance(BaseModel):
    """Start process."""

    processDefinitionKey: str = Field(title="Process definition key")
    variables: Optional[Variables] = Field(
        title="Optional payload variables", default_factory=dict
    )


class UserTask(BaseModel):
    """User task."""

    jsonld_id: AnyHttpUrl = Field(title="Task URL", alias="@id")

    id: str = Field(title="Task id")
    name: str = Field(title="Task name")
    description: Optional[str] = Field(title="Task description", default="")
    taskDefinitionKey: str = Field(title="Task definition key")
    form: Optional[Variables] = Field(title="Task form variables")
    variables: Optional[Variables] = Field(title="Task variables")
    completed: bool = Field(title="Task has been completed", default=False)


class CompleteUserTask(BaseModel):
    """Complete user task."""

    class Config:
        """Pydantic configuration."""

        schema_extra = {"example": {"variables": {"name": "value"}}}

    variables: Variables = Field(title="Form variables")


class Message(BaseModel):
    """Complete user task."""

    class Config:
        """Pydantic configuration."""

        schema_extra = {"example": {"variables": {"name": "value"}}}

    variables: Variables = Field(title="Message variables")


class ActivityInstance(BaseModel):
    """Activity instance."""

    id: str = Field(title="Activity id")
    type: str = Field(title="Activity type")
    name: str = Field(title="Activity name", default=None)
    incident: bool = Field(title="Has incident", default=False)


class ProcessInstance(BaseModel):
    """Process instance."""

    jsonld_id: AnyHttpUrl = Field(title="Process URL", alias="@id")

    id: str = Field(title="Process id")
    businessKey: str = Field(title="Business key")
    tasks: List[UserTask] = Field(title="User tasks", default_factory=list)
    variables: Variables = Field(title="Process variables")
    activities: List[ActivityInstance] = Field(
        title="Running activities", default_factory=list
    )
    state: State = Field(title="Process state")
    rootProcessInstanceId: Optional[str] = Field(title="Root Process id", default=None)


class ProcessDefinition(BaseModel):
    """Process definition."""

    id: str = Field(title="Unique process definition id")
    bpmn20Xml: str = Field(title="BPMN 2.0 XML")
