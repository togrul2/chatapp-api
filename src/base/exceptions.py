"""Base exceptions module."""
from collections.abc import Mapping
from typing import Any

from fastapi import HTTPException, status


class Http404NotFoundException(HTTPException):
    """Raises http 404 not found exception.
    Optionally can have detail parameter which
    will be used in exception's constructor,
    if not given, default one will be used."""

    def __init__(
        self,
        detail: str = "Not found.",
        headers: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(
            status.HTTP_404_NOT_FOUND, detail=detail, headers=headers
        )
