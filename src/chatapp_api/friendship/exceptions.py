"""Friendship exceptions module."""
from typing import Any

from fastapi import HTTPException, status


class RequestAlreadySent(HTTPException):
    """Http exception indicating that friendship
    request to this user already exists."""

    def __init__(self, headers: dict[str, Any] | None = None) -> None:
        super().__init__(
            status.HTTP_409_CONFLICT,
            "You already have friendship request with this user.",
            headers,
        )


class RequestWithYourself(HTTPException):
    """Http exception indicating that friendship
    request can't be sent from user to himself."""

    def __init__(
        self,
        headers: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            status.HTTP_409_CONFLICT,
            "You can't send request to yourself.",
            headers,
        )
