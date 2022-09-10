from fastapi import HTTPException, status

UsernameAlreadyTaken = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="User with given username already exists."
)

EmailAlreadyTaken = HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="User with given email already exists."
)


CredentialsException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

ExpiredTokenException = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Access token expired",
    headers={"WWW-Authenticate": "Bearer"},
)
