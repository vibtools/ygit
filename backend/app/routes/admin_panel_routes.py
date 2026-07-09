from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from backend.app.dependencies.auth import require_admin

router = APIRouter(tags=["Admin Panel"])

_ROOT = Path(__file__).resolve().parents[3]
_ADMIN_ROOT = _ROOT / "frontend" / "admin"
_ASSETS_ROOT = _ADMIN_ROOT / "assets"


@router.get("/admin", include_in_schema=False)
async def admin_index(user = Depends(require_admin)) -> FileResponse:
    """Serve the authenticated Admin Operations Console shell.

    The Admin Panel is a presentation surface. Business and authorization
    decisions stay in the Auth Engine and protected /api/v1/admin endpoints.
    """
    _ = user
    return FileResponse(_ADMIN_ROOT / "index.html", media_type="text/html")


@router.get("/admin/assets/{asset_path:path}", include_in_schema=False)
async def admin_asset(asset_path: str) -> FileResponse:
    """Serve admin static assets without exposing filesystem traversal."""
    candidate = (_ASSETS_ROOT / asset_path).resolve()
    try:
        candidate.relative_to(_ASSETS_ROOT.resolve())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Asset not found") from exc
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="Asset not found")
    media_type = "text/css" if candidate.suffix == ".css" else "application/javascript" if candidate.suffix == ".js" else None
    return FileResponse(candidate, media_type=media_type)
