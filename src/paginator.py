"""Module with custom paginator classes."""

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import CompoundSelect
from sqlalchemy.sql.expression import Select

from src.schemas.base import PaginatedResponse

T = TypeVar("T", BaseModel, BaseModel)


@dataclass
class BasePaginator(ABC, Generic[T]):
    """Base class for paginator"""

    page: int
    page_size: int
    session: AsyncSession
    total_count: int | None = None
    total_pages: int | None = None

    @abstractmethod
    async def paginate(self, query: Select) -> Select:
        """Method where pagination takes place."""

    async def _response(self, query: Select) -> PaginatedResponse[T]:
        """Returns pydantic response model for paginated queries."""
        result = await self.session.execute(query)
        return PaginatedResponse.construct(
            results=result.scalars().all(),
            total_pages=self.total_pages,
            total_records=self.total_count,
            current_page=self.page,
            items_per_page=self.page_size,
        )

    async def get_paginated_response(self, query: Select | CompoundSelect):
        """Returns pydantic response with pagination applied."""
        query = await self.paginate(query)
        response = await self._response(query)
        return response


@dataclass
class LimitOffsetPaginator(BasePaginator[T]):
    """Paginator class based on limit & offset queries."""

    async def paginate(self, query: Select) -> Select:
        offset_size = (self.page - 1) * self.page_size
        total_count_query = select([func.count()]).select_from(query)
        self.total_count = (
            await self.session.execute(total_count_query)
        ).fetchone()[0]
        self.total_pages = math.ceil(self.total_count / self.page_size)
        return query.offset(offset_size).limit(self.page_size)
