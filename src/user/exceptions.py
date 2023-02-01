"""User exceptions module."""
from fastapi import HTTPException, status

UsernameAlreadyTaken = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="User with given username already exists.",
)

EmailAlreadyTaken = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="User with given email already exists.",
)

BadCredentialsException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid username or password.",
    headers={"WWW-Authenticate": "Bearer"},
)

BadImageFileMIME = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Wrong file type, only jpeg and png files are allowed",
)
