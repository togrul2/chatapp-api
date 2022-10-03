"""Base schemas module."""
from pydantic import BaseModel


class DetailMessage(BaseModel):
    """Detail schema for error messages."""
    detail: str
