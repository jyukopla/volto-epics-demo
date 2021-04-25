"""Process events."""
from asyncio import Task
from process_api.config import settings
from typing import Dict
from typing import Optional
from typing import Union
import asyncio


class MasterOfCeremonies:
    """Master of ceremonies to wait asynchronous process events."""

    events: Dict[str, asyncio.Event]
    attendees: Dict[str, int]

    def __init__(self) -> None:
        """Init."""
        self.events = {}
        self.attendees = {}
        self.history: Dict[str, bool] = {}

    async def wait(
        self, key: str, timeout: Union[int, float] = settings.EMCEE_TIMEOUT
    ) -> bool:
        """Wait for event to happen."""
        task: Optional[Task[bool]] = None
        if key in self.history:
            return True
        if key not in self.events:
            self.events[key] = asyncio.Event()
        try:
            self.attendees.setdefault(key, 0)
            self.attendees[key] += 1
            task = asyncio.create_task(self.events[key].wait())
            done, pending = await asyncio.wait({task}, timeout=timeout)
            assert not pending, f"Task {task} unexpectedly not done."
        except AssertionError:
            done = set()
        finally:
            if task and not task.done():
                task.cancel()
            del task
            self.attendees[key] -= 1
            if self.attendees[key] < 1:
                del self.attendees[key]
                del self.events[key]
        return bool(done)

    def set(self, key: str) -> None:
        """Notify all event attendees."""
        if key in self.events:
            self.events[key].set()
        self.history[key] = True
        asyncio.get_event_loop().call_later(
            settings.EMCEE_TIMEOUT, self.history.pop, key, None
        )


emcee = MasterOfCeremonies()

__all__ = ["emcee"]
