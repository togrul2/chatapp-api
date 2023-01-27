"""Base exceptions module."""
from fastapi import HTTPException, status


def http_404_not_found(detail: str = "Not found."):
    """Raises http 404 not found exception.
    Optionally can have detail parameter which
    will be used in exception's constructor,
    if not given, default one will be used."""
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
