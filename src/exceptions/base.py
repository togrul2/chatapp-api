"""Base exceptions module."""
from fastapi import HTTPException, status

NotFound = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="Not found."
)
