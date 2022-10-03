"""Friendship exceptions module."""
from fastapi import HTTPException, status

RequestAlreadySent = HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail='You already have friendship request with this user.'
)

RequestWithYourself = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail='You can\'t send request to yourself.'
)
