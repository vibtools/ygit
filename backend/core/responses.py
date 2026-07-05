from typing import Any
from fastapi.responses import JSONResponse

def success_response(data: Any, *, meta: dict[str, Any] | None = None, status_code: int = 200) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"success": True, "data": data, "error": None, "meta": meta or {}})

def error_response(*, code: str, message: str, status_code: int = 400, fields: list[dict[str, str]] | None = None, meta: dict[str, Any] | None = None) -> JSONResponse:
    error: dict[str, Any] = {"code": code, "message": message}
    if fields is not None:
        error["fields"] = fields
    return JSONResponse(status_code=status_code, content={"success": False, "data": None, "error": error, "meta": meta or {}})
