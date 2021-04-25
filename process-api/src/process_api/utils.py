"""Utilities."""
from aiohttp import ClientResponse
from aiohttp import ClientTimeout
from contextlib import asynccontextmanager
from fastapi.exceptions import HTTPException
from process_api.config import settings
from pydantic import BaseModel
from pydantic.json import pydantic_encoder
from typing import Any
from typing import AsyncGenerator
from typing import Dict
from typing import Optional
from typing import Tuple
from urllib.parse import urlparse
from urllib.parse import urlunparse
import aiohttp
import dataclasses
import json
import re


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
        headers=headers, timeout=ClientTimeout(total=settings.CAMUNDA_TIMEOUT),
    ) as session:
        yield session


def as_dict(ob: Any) -> Dict[Any, Any]:
    """Convert "anything" dict."""
    return ob.dict() if isinstance(ob, BaseModel) else dataclasses.asdict(ob)


def as_json(ob: Any) -> str:
    """Convert "anything" to JSON str."""
    return (
        ob.json()
        if isinstance(ob, BaseModel)
        else json.dumps(ob, default=pydantic_encoder)
    )


def canonical_url(url: str) -> str:
    """Convert URL into canonical form."""
    parts = list(urlparse(url))
    parts[2] = re.sub("/+", "/", parts[2])
    return urlunparse(parts)


async def assert_status_code(
    response: ClientResponse,
    code: Tuple[int, ...] = (200, 201, 204),
    error_code: Optional[int] = None,
) -> ClientResponse:
    """Raise HTTPException for unexpected status codes."""
    if response.status not in code:
        if response.content_type == "application/json":
            error = await response.json()
        else:
            error = await response.text()
        if response.status == 404:
            raise HTTPException(status_code=error_code or 404, detail=error)
        raise HTTPException(status_code=error_code or 500, detail=error)
    return response
