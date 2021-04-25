"""Health routes."""
from datetime import datetime
from datetime import timedelta
from fastapi.exceptions import HTTPException
from fastapi.routing import APIRouter
from process_api.config import settings
from process_api.health.state import state
from process_api.health.types import Heartbeat


router = APIRouter()


@router.get(
    "/healthz", response_model=Heartbeat, summary="Service health status", tags=["Meta"]
)
async def healthz() -> Heartbeat:
    """Service health status."""
    now = datetime.utcnow()

    if (
        now - timedelta(seconds=settings.HEALTH_HEARTBEAT_THRESHOLD)
    ).isoformat() < state.heartbeat:
        return Heartbeat(heartbeat=state.heartbeat)

    age = (now - datetime.fromisoformat(state.heartbeat)).total_seconds()
    raise HTTPException(status_code=500, detail=f"No heartbeat for {age} seconds")
