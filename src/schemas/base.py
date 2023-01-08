"""Base schemas module."""
from typing import Generic, TypeVar

from pydantic import BaseModel
from pydantic.generics import GenericModel


class DetailMessage(BaseModel):
    """Detail schema for error messages."""

    detail: str


T = TypeVar("T", int, str)


class PaginatedResponse(GenericModel, Generic[T]):
    """Pydantic model for validating paginatel list response."""

    results: list[T]
    total_pages: int
    total_records: int
    current_page: int
    items_per_page: int
