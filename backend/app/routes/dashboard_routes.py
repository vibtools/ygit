from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from backend.app.dependencies.auth import require_user

router = APIRouter(tags=["Dashboard"])

_ROOT = Path(__file__).resolve().parents[3]
_DASHBOARD_ROOT = _ROOT / "frontend" / "dashboard"
_ASSETS_ROOT = _DASHBOARD_ROOT / "assets"


@router.get("/dashboard", include_in_schema=False)
async def dashboard_index(user = Depends(require_user)) -> FileResponse:
    """Serve the authenticated dashboard client shell.

    Business logic stays in API/engine layers.
    """
    _ = user
    return FileResponse(_DASHBOARD_ROOT / "index.html", media_type="text/html")


@router.get("/dashboard/assets/{asset_path:path}", include_in_schema=False)
async def dashboard_asset(asset_path: str) -> FileResponse:
    """Serve dashboard static assets without exposing filesystem traversal."""
    candidate = (_ASSETS_ROOT / asset_path).resolve()
    try:
        candidate.relative_to(_ASSETS_ROOT.resolve())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Asset not found") from exc
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")
    media_type = "text/css" if candidate.suffix == ".css" else "application/javascript" if candidate.suffix == ".js" else None
    return FileResponse(candidate, media_type=media_type)
