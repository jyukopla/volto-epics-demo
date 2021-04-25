"""Health tasks."""
from datetime import datetime
from process_api.camunda.types import CompleteExternalTaskDto
from process_api.camunda.types import LockedExternalTaskDto
from process_api.camunda.types import VariableValueDto
from process_api.health.config import Topic
from process_api.health.state import state
from process_api.types import ExternalTaskComplete


async def heartbeat(task: LockedExternalTaskDto) -> ExternalTaskComplete:
    """Update health check timestamp."""
    state.heartbeat = datetime.utcnow().isoformat()
    return ExternalTaskComplete(
        task=task,
        response=CompleteExternalTaskDto(
            workerId=task.workerId,
            variables={
                "heartbeat": VariableValueDto(value=state.heartbeat, type="string"),
            },
        ),
    )


TASKS = {Topic.HEALTH_HEARTBEAT: heartbeat}
