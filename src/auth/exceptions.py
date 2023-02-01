"""Module with auth related exceptions"""
from fastapi import HTTPException, WebSocketException, status

WebSocketBadTokenException = WebSocketException(
    code=status.WS_1008_POLICY_VIOLATION,
    reason="Authentication token is expired or incorrect",
)

BadTokenException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token is either expired or invalid.",
    headers={"WWW-Authenticate": "Bearer"},
)
