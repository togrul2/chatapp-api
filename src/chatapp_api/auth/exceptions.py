"""Module with auth related exceptions"""

from fastapi import HTTPException, WebSocketException, status


class WebSocketBadTokenException(WebSocketException):
    """Websocket exception for indicating expired or invalid access token."""

    def __init__(
        self,
    ) -> None:
        super().__init__(
            status.WS_1008_POLICY_VIOLATION,
            "Authentication token is expired or incorrect",
        )


class BadTokenException(HTTPException):
    """Http exception for indicating invalid
    or expired access or refresh tokens."""

    def __init__(self) -> None:
        super().__init__(
            status.HTTP_401_UNAUTHORIZED,
            "Token is either expired or invalid.",
            {"WWW-Authenticate": "Bearer"},
        )
