from fastapi import WebSocketException, status

WebSocketBadTokenException = WebSocketException(
    code=status.WS_1008_POLICY_VIOLATION,
    reason="Authentication token is expired or incorrect",
)
