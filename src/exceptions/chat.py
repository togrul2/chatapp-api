from fastapi import HTTPException, WebSocketException, status

WebSocketBadTokenException = WebSocketException(
    code=status.WS_1008_POLICY_VIOLATION,
    reason="Authentication token is expired or incorrect",
)

ChatNameTakenHTTPException = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="This chat name is already taken by another chat.",
)
