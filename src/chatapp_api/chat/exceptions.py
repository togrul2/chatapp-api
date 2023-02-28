"""Chat model related exceptions."""
from typing import Any

from fastapi import HTTPException, WebSocketException, status


class ChatNameTakenException(HTTPException):
    """Http exception indicating that chat name is already taken."""

    def __init__(self, headers: dict[str, Any] | None = None) -> None:
        super().__init__(
            status.HTTP_409_CONFLICT,
            "This chat name is already taken by another chat.",
            headers,
        )


class UserNotAdminException(HTTPException):
    """Http exception indicating that action is
    available only for chat admins."""

    def __init__(self, headers: dict[str, Any] | None = None) -> None:
        super().__init__(
            status.HTTP_403_FORBIDDEN,
            "This action is only available for chat admins.",
            headers,
        )


class UserNotOwnerException(HTTPException):
    """Http exception indicating that action is
    available only for chat owner."""

    def __init__(self, headers: dict[str, Any] | None = None) -> None:
        super().__init__(
            status.HTTP_403_FORBIDDEN,
            "This action is only available for chat owner.",
            headers,
        )


class UserNotMemberException(HTTPException):
    """Http exception indicating that action is
    available only for chat members."""

    def __init__(self, headers: dict[str, Any] | None = None) -> None:
        super().__init__(
            status.HTTP_403_FORBIDDEN,
            "This action is only available for chat members.",
            headers,
        )


class BadInviteTokenException(HTTPException):
    """Http exception indicating that invite token is
    either expired or invalid."""

    def __init__(self, headers: dict[str, Any] | None = None) -> None:
        super().__init__(
            status.HTTP_400_BAD_REQUEST,
            "Invite token is either invalid or expired.",
            headers,
        )


class WebSocketChatDoesNotExist(WebSocketException):
    """Http exception indicating that chat does not exist."""

    def __init__(self) -> None:
        super().__init__(
            code=status.WS_1008_POLICY_VIOLATION, reason="Chat does not exist"
        )


class AuthUserNotFoundWebSocketException(WebSocketException):
    def __init__(self) -> None:
        super().__init__(
            code=status.WS_1008_POLICY_VIOLATION, reason="Auth user not found."
        )


class TargetUserNotFoundWebSocketException(WebSocketException):
    def __init__(self) -> None:
        super().__init__(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Target user not found.",
        )
