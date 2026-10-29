from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import ContainerDep

router = APIRouter(tags=["misc"])


@router.get("/health")
def health(container: ContainerDep) -> dict:
    return {"status": "ok", "ai_enabled": container.llm is not None}
