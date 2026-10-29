from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.container import Container


def get_container(request: Request) -> Container:
    return request.app.state.container


ContainerDep = Annotated[Container, Depends(get_container)]


def client_ip(request: Request) -> str:
    header = request.app.state.container.settings.trusted_ip_header
    if header:
        value = request.headers.get(header, "").split(",")[0].strip()
        if value:
            return value[:64]
    return request.client.host if request.client else "unknown"
