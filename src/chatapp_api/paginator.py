"""Module with custom paginator classes."""
import math
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import TypedDict
from urllib import parse

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import CompoundSelect
from sqlalchemy.sql.expression import Select

from src.chatapp_api.base.models import CustomBase


class PaginatedResponseDict(TypedDict):
    """Typed dict for response body of paginated GET endpoint."""

    results: Sequence[CustomBase] | Sequence[Row]
    total_pages: int
    total_records: int
    current_page: int
    items_per_page: int
    next_page: str | None
    prev_page: str | None


@dataclass
class BasePaginator(ABC):
    """Base class for paginator.
    This class must be inherited with
    implementation of _paginate() method."""

    session: AsyncSession
    page: int
    page_size: int
    request: Request
    total_count: int | None = field(init=False, default=None)
    total_pages: int | None = field(init=False, default=None)

    @abstractmethod
    def _paginate_query(
        self, query: Select | CompoundSelect
    ) -> Select | CompoundSelect:
        """Method where pagination takes place."""

    def _get_url_for_page(self, page: int) -> str | None:
        """Generates url for given page."""
        if self.total_pages is None:
            raise ValueError(
                "total_pages is none, calculate it before calling this method."
            )

        if page < 1 or page > self.total_pages:
            return None

        base_url = f"{self.request.url.scheme}://{self.request.url.hostname}"

        if self.request.url.port:
            base_url += f":{self.request.url.port}"

        query_params_string = parse.urlencode(
            {**self.request.query_params, "page": str(page)}
        )
        return f"{base_url}?{query_params_string}"

    async def _calculate_total_count(
        self, query: Select | CompoundSelect
    ) -> int:
        """Calculates total number of records in table."""
        return (
            await self.session.scalar(
                select(func.count()).select_from(query.subquery())
            )
        ) or 0

    def _response(
        self, results: Sequence[CustomBase] | Sequence[Row]
    ) -> PaginatedResponseDict:
        """Returns pydantic response model for paginated queries."""
        if self.total_count is None or self.total_pages is None:
            raise ValueError(
                "_response() called before _paginate() or"
                " _calculate_total_count(). Make sure you call them first."
            )

        return {
            "results": results,
            "total_pages": self.total_pages,
            "total_records": self.total_count,
            "current_page": self.page,
            "items_per_page": self.page_size,
            "prev_page": self._get_url_for_page(self.page - 1),
            "next_page": self._get_url_for_page(self.page + 1),
        }

    async def get_paginated_response_for_model(
        self, paginated_query: Select | CompoundSelect
    ) -> PaginatedResponseDict:
        """
        Returns pydantic response with pagination
        applied to query of orm model. Basically
        this method is for cases when scalar() | scalars()
        can be used where select() only takes model instance.

        Example:
            >>> from src.user.models import User
            >>> list_query = select(User)
            >>> response = self.get_paginated_response_for_model(list_query)
        """
        # Calculate total number of records
        self.total_count = await self._calculate_total_count(paginated_query)
        results = (
            await self.session.scalars(self._paginate_query(paginated_query))
        ).all()
        return self._response(results)

    async def get_paginated_response_for_rows(
        self, paginated_query: Select | CompoundSelect
    ) -> PaginatedResponseDict:
        """
        Returns pydantic response with pagination applied to query of Row.
        Basically this method is for cases when scalar() is not used
        and select() takes different fields.

        Example:
            >>> from src.chat.models import Chat, Membership
            >>> list_query = (
            >>>     select(Chat, func.count(Membership.id))
            >>>     .join(Membership).group_by(Chat.id))
            >>> response = self.get_paginated_response_for_rows(list_query)
        """
        self.total_count = await self._calculate_total_count(paginated_query)
        results = (
            await self.session.execute(self._paginate_query(paginated_query))
        ).all()
        return self._response(results)


@dataclass
class LimitOffsetPaginator(BasePaginator):
    """Limit offset implementation of pagination.
    Uses database limit & offset query parameters for paginating results."""

    def _paginate_query(
        self, query: Select | CompoundSelect
    ) -> Select | CompoundSelect:
        """Returns paginated query with limit/offset and
        sets total_pages attribute. If total_count attribute is None,
        raises ValueError, so it must be calculated and
        set before calling this method."""
        if self.total_count is None:
            raise ValueError(
                "_paginate() called before _calculate_total_count()."
            )

        self.total_pages = math.ceil(self.total_count / self.page_size)
        return query.offset((self.page - 1) * self.page_size).limit(
            self.page_size
        )
