from collections.abc import Awaitable, Callable
from uuid import uuid4
from fastapi import Request, Response

async def request_context_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    trace_id = request.headers.get("X-Trace-Id") or f"trace_{uuid4().hex}"
    request.state.trace_id = trace_id
    response = await call_next(request)
    response.headers["X-Trace-Id"] = trace_id
    return response
