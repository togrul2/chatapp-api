"""Module with custom paginator classes."""

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

from sqlalchemy.orm import Query

from schemas.base import PaginatedResponse

T = TypeVar("T", int, str)


@dataclass
class BasePaginator(ABC, Generic[T]):
    """Base class for paginator"""

    page: int
    page_size: int
    total_count: int | None = None
    total_pages: int | None = None

    @abstractmethod
    def paginate(self, query: Query) -> Query:
        """Method where pagination takes place."""

    def _response(self, query: Query) -> PaginatedResponse[T]:
        """Returns pydantic response model for paginated queries."""

        return PaginatedResponse.construct(
            results=query.all(),
            total_pages=self.total_pages,
            total_records=self.total_count,
            current_page=self.page,
            items_per_page=self.page_size,
        )

    def get_paginated_response(self, query: Query) -> PaginatedResponse[T]:
        """Returns pydantic response with pagination applied."""
        query = self.paginate(query)
        response = self._response(query)
        return response


@dataclass
class LimitOffsetPaginator(BasePaginator[T]):
    """Paginator class based on limit & offset queries."""

    def paginate(self, query: Query) -> Query:
        offset_size = (self.page - 1) * self.page_size
        self.total_count = query.count()
        self.total_pages = math.ceil(self.total_count / self.page_size)
        return query.offset(offset_size).limit(self.page_size)
