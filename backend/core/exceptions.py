from typing import Any
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from backend.core.responses import error_response

class YGITError(Exception):
    def __init__(self, *, code: str, message: str, status_code: int = 400, metadata: dict[str, Any] | None = None) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.metadata = metadata or {}
        super().__init__(message)

class FeatureNotEnabledError(YGITError):
    def __init__(self, feature: str) -> None:
        super().__init__(code="FEATURE_NOT_ENABLED_IN_SKELETON", message=f"{feature} is contracted but not enabled in skeleton v0.1.0.", status_code=501, metadata={"feature": feature})

async def ygit_error_handler(request: Request, exc: YGITError):
    trace_id = getattr(request.state, "trace_id", None)
    return error_response(code=exc.code, message=exc.message, status_code=exc.status_code, meta={"trace_id": trace_id, **exc.metadata})

async def validation_error_handler(request: Request, exc: RequestValidationError):
    trace_id = getattr(request.state, "trace_id", None)
    fields = [{"field": ".".join(str(part) for part in error["loc"]), "message": str(error["msg"])} for error in exc.errors()]
    return error_response(code="VALIDATION_ERROR", message="Request validation failed.", fields=fields, status_code=422, meta={"trace_id": trace_id})

async def unhandled_exception_handler(request: Request, exc: Exception):
    trace_id = getattr(request.state, "trace_id", None)
    return error_response(code="INTERNAL_SERVER_ERROR", message="An unexpected server error occurred.", status_code=500, meta={"trace_id": trace_id})
