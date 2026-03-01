"""Constitution endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from skaro_core.artifacts import ArtifactManager
from skaro_web.api.deps import broadcast, get_am
from skaro_web.api.schemas import ContentBody

router = APIRouter(prefix="/api/constitution", tags=["constitution"])


@router.get("")
async def get_constitution(am: ArtifactManager = Depends(get_am)):
    return {
        "content": am.read_constitution(),
        "has_constitution": am.has_constitution,
        "validation": am.validate_constitution(),
    }


@router.post("/validate")
async def validate_constitution(am: ArtifactManager = Depends(get_am)):
    result = am.validate_constitution()
    is_valid = all(result.values()) if result else False
    return {"success": True, "valid": is_valid, "checks": result}


@router.put("")
async def save_constitution(
    request: Request,
    payload: ContentBody,
    am: ArtifactManager = Depends(get_am),
):
    am.write_constitution(payload.content)
    await broadcast(request, {"event": "artifact:updated", "artifact": "constitution"})
    return {"success": True}
