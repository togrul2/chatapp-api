"""Chat model related exceptions."""
from fastapi import HTTPException, WebSocketException, status

WebSocketChatDoesNotExist = WebSocketException(
    code=status.WS_1008_POLICY_VIOLATION,
    reason="Chat does not exist",
)

ChatNameTakenException = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="This chat name is already taken by another chat.",
)

UserNotAdminException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="This action is only available for chat admins.",
)

UserNotOwnerException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="This action is only available for chat owner.",
)

UserNotMemberException = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="This action is only available for chat members.",
)
