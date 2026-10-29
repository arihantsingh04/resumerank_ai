from __future__ import annotations

from fastapi import APIRouter, Response

from app.core.errors import NotFound
from app.data.templates import BY_ID, TEMPLATES
from app.schemas.check import TemplateDetail, TemplateSummary

router = APIRouter(prefix="/templates", tags=["templates"])
CACHE = "public, max-age=3600"


@router.get("", response_model=list[TemplateSummary])
def list_templates(response: Response):
    response.headers["Cache-Control"] = CACHE
    return TEMPLATES


@router.get("/{template_id}", response_model=TemplateDetail)
def get_template(template_id: str, response: Response):
    t = BY_ID.get(template_id)
    if t is None:
        raise NotFound("That role template doesn't exist.")
    response.headers["Cache-Control"] = CACHE
    return t
